from __future__ import annotations

import json
import platform
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from parallel_truth_fingerprint.contracts.v1_baseline import (
    BaselineEntry,
    DirtyOverlay,
    RepositoryIdentity,
    V1BaselineManifest,
)
from parallel_truth_fingerprint.evidence.v1_baseline import (
    SCIENTIFIC_STATUSES,
    VERIFICATION_STATUSES,
    BaselineError,
    DEFAULT_EXPECTED_INVENTORY,
    build_manifest,
    canonical_json_bytes,
    collect_repository_identity,
    manifest_with_identity,
    normalize_local_locator,
    publish_manifest,
    redact_configuration,
    resolve_entry,
    sha256_file_stable,
    validate_manifest,
)


class V1BaselineTest(unittest.TestCase):
    def _entry(self, **overrides: object) -> BaselineEntry:
        values: dict[str, object] = {
            "entry_id": "code:sample",
            "category": "code",
            "role": "source",
            "version": None,
            "locator": "src/sample.py",
            "byte_size": 3,
            "sha256": "sha256:" + "a" * 64,
            "verification_status": "verified",
            "scientific_status": "IMPLEMENTED_RUNTIME_EVIDENCE",
            "limitation": None,
        }
        values.update(overrides)
        return BaselineEntry(**values)  # type: ignore[arg-type]

    def _manifest(self, entries: tuple[BaselineEntry, ...] | None = None) -> V1BaselineManifest:
        return V1BaselineManifest(
            schema_version="V1BaselineManifest.v1",
            baseline_id=None,
            observed_at="2026-08-31T00:00:00Z",
            repository=RepositoryIdentity(
                head="sha1:" + "b" * 40,
                branch="main",
                status_sha256="sha256:" + "c" * 64,
                status_verification="verified",
                ignored_status_sha256="sha256:" + "d" * 64,
                ignored_status_verification="verified",
                dirty_overlays=(),
            ),
            entries=entries or (self._entry(),),
            authorization_effect="none",
        )

    def _materialized_manifest(self, project_root: Path) -> V1BaselineManifest:
        source = project_root / "src" / "sample.py"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(b"one")
        digest, status = sha256_file_stable(source)
        self.assertEqual(status, "verified")
        draft = self._manifest((self._entry(sha256=digest),))
        return manifest_with_identity(
            replace(draft, repository=collect_repository_identity(project_root))
        )

    def _publishable_manifest(
        self, project_root: Path, manifest: V1BaselineManifest
    ) -> V1BaselineManifest:
        final = manifest_with_identity(
            replace(
                manifest,
                baseline_id=None,
                repository=collect_repository_identity(project_root),
            )
        )
        publish_manifest(project_root, final)
        return final

    def test_contract_tokens_are_closed(self) -> None:
        self.assertEqual(
            VERIFICATION_STATUSES,
            frozenset({"verified", "missing", "mutable", "corrupt", "unverifiable"}),
        )
        self.assertEqual(
            SCIENTIFIC_STATUSES,
            frozenset(
                {
                    "IMPLEMENTED_RUNTIME_EVIDENCE",
                    "FIXTURE",
                    "PUBLISHED_REFERENCE",
                    "MEASURED_RESULT",
                    "EXPERIMENTAL_FINGERPRINT_BASELINE",
                    "LEGACY_BASELINE",
                }
            ),
        )

    def test_canonical_identity_is_stable_and_changes_with_bytes(self) -> None:
        first = manifest_with_identity(self._manifest())
        second = manifest_with_identity(self._manifest())
        changed = manifest_with_identity(
            self._manifest((self._entry(byte_size=4),))
        )
        self.assertEqual(first.baseline_id, second.baseline_id)
        self.assertEqual(canonical_json_bytes(first.to_identity_dict()), canonical_json_bytes(second.to_identity_dict()))
        self.assertNotEqual(first.baseline_id, changed.baseline_id)

    def test_validation_rejects_unknown_tokens_and_duplicate_entries(self) -> None:
        with self.assertRaises(BaselineError):
            validate_manifest(self._manifest((self._entry(verification_status="unknown"),)))
        with self.assertRaises(BaselineError):
            validate_manifest(self._manifest((self._entry(), self._entry())))

    def test_redaction_never_exposes_secret_values_or_their_digest(self) -> None:
        view = redact_configuration(
            {
                "host": "localhost",
                "password": "secret-canary-value",
                "nested": {"api_token": "secret-canary-token", "port": 1883},
            },
            allowed_keys={"host", "nested", "port"},
        )
        rendered = canonical_json_bytes(view).decode("utf-8")
        self.assertIn("localhost", rendered)
        self.assertNotIn("secret-canary-value", rendered)
        self.assertNotIn("secret-canary-token", rendered)
        self.assertNotIn("password", rendered)
        self.assertNotIn("api_token", rendered)

    def test_locator_rejects_escape_and_symlink_escape(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "root"
            outside = Path(raw) / "outside.txt"
            root.mkdir()
            outside.write_text("x", encoding="utf-8")
            with self.assertRaises(BaselineError):
                normalize_local_locator(root, outside)
            link = root / "escape"
            try:
                link.symlink_to(outside)
            except OSError:
                self.skipTest("symlink creation unavailable")
            with self.assertRaises(BaselineError):
                normalize_local_locator(root, link)

    def test_hash_detects_mutation_during_read(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "sample.bin"
            path.write_bytes(b"abc")
            with patch("parallel_truth_fingerprint.evidence.v1_baseline._file_signature") as signature:
                signature.side_effect = [(1, 1, 3, 1), (1, 1, 4, 2)]
                digest, status = sha256_file_stable(path)
            self.assertIsNone(digest)
            self.assertEqual(status, "mutable")

    def test_build_manifest_reports_missing_without_substitution(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            manifest = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"code": ("missing.py",)},
            )
        self.assertEqual(manifest.entries[0].verification_status, "missing")
        self.assertIsNone(manifest.entries[0].sha256)

    def test_build_manifest_excludes_secret_files_without_reading_or_hashing(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            secret_file = root / ".env"
            secret_file.write_text("PASSWORD=secret-canary-value", encoding="utf-8")
            manifest = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"configuration": (".env",)},
            )
        entry = manifest.entries[0]
        self.assertEqual(entry.verification_status, "unverifiable")
        self.assertIsNone(entry.sha256)
        self.assertNotIn("secret-canary-value", canonical_json_bytes(manifest.to_dict()).decode("utf-8"))

    def test_configuration_identity_ignores_secret_values_but_tracks_approved_values(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            config = root / ".env.example"
            config.write_text(
                "DEMO_POWER=65.0\nMINIO_SECRET_KEY=secret-canary-one\n",
                encoding="utf-8",
            )
            first = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"configuration": (".env.example",)},
            )
            config.write_text(
                "DEMO_POWER=65.0\nMINIO_SECRET_KEY=secret-canary-two\n",
                encoding="utf-8",
            )
            secret_changed = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"configuration": (".env.example",)},
            )
            config.write_text(
                "DEMO_POWER=66.0\nMINIO_SECRET_KEY=secret-canary-two\n",
                encoding="utf-8",
            )
            approved_changed = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"configuration": (".env.example",)},
            )
        self.assertEqual(first.entries[0].sha256, secret_changed.entries[0].sha256)
        self.assertNotEqual(first.entries[0].sha256, approved_changed.entries[0].sha256)
        rendered = canonical_json_bytes(first.to_dict()).decode("utf-8")
        self.assertNotIn("secret-canary-one", rendered)
        self.assertNotIn("MINIO_SECRET_KEY", rendered)

    def test_configuration_identity_redacts_credentials_in_an_approved_url_field(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            config = root / ".env.example"
            config.write_text(
                "COMETBFT_RPC_URL=http://alice:secret-url-canary@localhost:26657\n",
                encoding="utf-8",
            )
            manifest = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"configuration": (".env.example",)},
            )
            config.write_text(
                "COMETBFT_RPC_URL=http://bob:another-secret-url-canary@localhost:26657\n",
                encoding="utf-8",
            )
            changed_credentials = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"configuration": (".env.example",)},
            )
        rendered = canonical_json_bytes(manifest.to_dict()).decode("utf-8")
        self.assertNotIn("alice", rendered)
        self.assertNotIn("secret-url-canary", rendered)
        self.assertEqual(manifest.entries[0].sha256, changed_credentials.entries[0].sha256)

    def test_directory_digest_is_deterministic_and_excludes_derived_cache(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / "src"
            source.mkdir()
            (source / "module.py").write_bytes(b"source")
            cache = source / "__pycache__"
            cache.mkdir()
            (cache / "module.pyc").write_bytes(b"derived-one")
            first = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"code": ("src",)},
            )
            (cache / "module.pyc").write_bytes(b"derived-two")
            second = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"code": ("src",)},
            )
            self.assertEqual(first.entries[0].sha256, second.entries[0].sha256)
            first = self._publishable_manifest(root, first)
            self.assertEqual(resolve_entry(first, root, "code:src"), root / "src")

    def test_directory_with_secret_file_is_unverifiable_without_hashing_the_secret(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / "src"
            source.mkdir()
            (source / ".env").write_text("PASSWORD=secret-directory-canary", encoding="utf-8")
            manifest = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"code": ("src",)},
            )
        entry = manifest.entries[0]
        self.assertEqual(entry.verification_status, "unverifiable")
        self.assertIsNone(entry.sha256)
        self.assertNotIn("secret-directory-canary", canonical_json_bytes(manifest.to_dict()).decode("utf-8"))

    def test_default_inventory_keeps_external_storage_unavailable_without_contacting_it(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            manifest = build_manifest(
                project_root=Path(raw),
                observed_at="2026-08-31T00:00:00Z",
            )
        external = [entry for entry in manifest.entries if entry.category == "external_storage"]
        self.assertEqual(len(external), 5)
        self.assertTrue(all(entry.verification_status == "unverifiable" for entry in external))
        self.assertTrue(all(entry.locator and entry.locator.startswith("minio://") for entry in external))

    def test_default_inventory_covers_runtime_known_absences_and_real_pointer_path(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            manifest = build_manifest(
                project_root=Path(raw),
                observed_at="2026-08-31T00:00:00Z",
            )
        by_id = {entry.entry_id: entry for entry in manifest.entries}
        self.assertIn("runtime_identity:python", by_id)
        self.assertEqual(by_id["runtime_identity:python"].version, platform.python_version())
        self.assertIn(
            "mutable_pointer:_bmad-output/local-store/fingerprint-training-history/"
            "fingerprint-training-history/index/latest.json",
            by_id,
        )
        known_absences = [entry for entry in manifest.entries if entry.category == "known_absence"]
        self.assertGreaterEqual(len(known_absences), 3)
        self.assertTrue(all(entry.verification_status == "missing" for entry in known_absences))

    def test_directory_inventory_emits_exact_resolvable_child_entries(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            dataset = root / "dataset"
            dataset.mkdir()
            (dataset / "b.txt").write_bytes(b"b")
            (dataset / "a.txt").write_bytes(b"a")
            manifest = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"datasets": ("dataset",)},
            )
            children = [
                entry for entry in manifest.entries
                if entry.entry_id.startswith("datasets:dataset#child:")
            ]
            self.assertEqual([entry.locator for entry in children], ["dataset/a.txt", "dataset/b.txt"])
            manifest = self._publishable_manifest(root, manifest)
            self.assertEqual(
                resolve_entry(manifest, root, "datasets:dataset#child:a.txt"),
                dataset / "a.txt",
            )

    def test_runtime_observations_are_not_promoted_to_measured_results(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            observations = root / "evidence"
            observations.mkdir()
            (observations / "command.txt").write_text("demo", encoding="utf-8")
            manifest = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"runtime_observations": ("evidence",)},
            )
        self.assertTrue(
            all(entry.scientific_status == "IMPLEMENTED_RUNTIME_EVIDENCE" for entry in manifest.entries)
        )
        self.assertTrue(all(entry.role == "runtime_observation" for entry in manifest.entries))

    def test_compose_image_tags_are_mutable_and_digest_declarations_are_not_runtime_proof(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            compose = root / "compose.local.yml"
            compose.write_text(
                "services:\n  tagged:\n    image: example/service:latest\n"
                "  pinned:\n    image: example/service@sha256:" + "a" * 64 + "\n",
                encoding="utf-8",
            )
            manifest = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"configuration": ("compose.local.yml",)},
                include_declared_runtime=True,
            )
        images = [entry for entry in manifest.entries if entry.category == "image_reference"]
        self.assertEqual([entry.verification_status for entry in images], ["mutable", "unverifiable"])
        self.assertEqual(images[0].version, "example/service:latest")
        self.assertIn("not inspected", images[1].limitation or "")

    def test_mutable_pointer_never_becomes_resolvable_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            pointer = root / "history" / "latest.json"
            pointer.parent.mkdir()
            pointer.write_text('{"target":"run-a"}', encoding="utf-8")
            manifest = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"mutable_pointer": ("history/latest.json",)},
            )
            self.assertEqual(manifest.entries[0].verification_status, "mutable")
            self.assertEqual(manifest.entries[0].observed_target, "run-a")
            with self.assertRaises(BaselineError):
                resolve_entry(manifest, root, manifest.entries[0].entry_id)

    def test_mutable_pointer_records_a_safe_exact_target_without_resolving_it(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            pointer = root / "history" / "latest.json"
            pointer.parent.mkdir()
            pointer.write_text('{"run_id":"runs/run-202605-example"}', encoding="utf-8")
            manifest = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"mutable_pointer": ("history/latest.json",)},
            )
        self.assertEqual(manifest.entries[0].observed_target, "runs/run-202605-example")

    def test_mutable_pointer_rejects_windows_absolute_target(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            pointer = root / "history" / "latest.json"
            pointer.parent.mkdir()
            pointer.write_text('{"target":"C:\\\\outside"}', encoding="utf-8")
            manifest = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"mutable_pointer": ("history/latest.json",)},
            )
        self.assertIsNone(manifest.entries[0].observed_target)

    def test_invalid_mutable_pointer_json_is_classified_as_corrupt(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            pointer = root / "history" / "latest.json"
            pointer.parent.mkdir()
            pointer.write_text('{"target":', encoding="utf-8")
            manifest = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"mutable_pointer": ("history/latest.json",)},
            )
        entry = manifest.entries[0]
        self.assertEqual(entry.verification_status, "corrupt")
        self.assertIsNone(entry.sha256)
        self.assertIn("invalid JSON", entry.limitation or "")

    def test_validation_rejects_scientific_role_or_category_misclassification(self) -> None:
        with self.assertRaises(BaselineError):
            validate_manifest(
                self._manifest(
                    (
                        self._entry(
                            category="legacy_baseline",
                            role="historical_detector",
                            scientific_status="MEASURED_RESULT",
                        ),
                    )
                )
            )
        with self.assertRaises(BaselineError):
            validate_manifest(
                self._manifest((self._entry(role="final_physical_detector"),))
            )
        with self.assertRaises(BaselineError):
            validate_manifest(
                self._manifest(
                    (
                        self._entry(
                            category="code",
                            role="historical_evidence",
                            scientific_status="EXPERIMENTAL_FINGERPRINT_BASELINE",
                        ),
                    )
                )
            )

    def test_expected_mqtt_contract_uses_the_actual_source_tree_path(self) -> None:
        self.assertIn(
            "src/parallel_truth_fingerprint/edge_nodes/common/mqtt_io.py",
            DEFAULT_EXPECTED_INVENTORY["contracts"],
        )

    def test_git_identity_separates_secret_untracked_overlay_without_hashing_it(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            tracked = root / "tracked.txt"
            tracked.write_text("tracked", encoding="utf-8")
            responses = {
                ("rev-parse", "--verify", "HEAD"): b"a" * 40 + b"\n",
                ("branch", "--show-current"): b"main\n",
                ("status", "--porcelain=v1", "--untracked-files=all", "-z"): b" M tracked.txt\0",
                (
                    "status",
                    "--porcelain=v1",
                    "--ignored=matching",
                    "--untracked-files=all",
                    "-z",
                ): b" M tracked.txt\0?? .env\0",
            }

            def fake_git(_root: Path, *arguments: str) -> tuple[bytes, str]:
                return responses[arguments], "verified"

            with patch("parallel_truth_fingerprint.evidence.v1_baseline._run_git", fake_git):
                identity = collect_repository_identity(root)
        overlays = {overlay.locator: overlay for overlay in identity.dirty_overlays}
        self.assertEqual(overlays["tracked.txt"].verification_status, "verified")
        secret_overlay = next(
            overlay for overlay in identity.dirty_overlays if overlay.locator.startswith("[REDACTED_SECRET_PATH]")
        )
        self.assertEqual(secret_overlay.verification_status, "unverifiable")
        self.assertIsNone(secret_overlay.sha256)

    def test_git_identity_requests_file_level_untracked_entries_and_records_origins(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            untracked = root / "new" / "sample.txt"
            untracked.parent.mkdir()
            untracked.write_text("one", encoding="utf-8")
            calls: list[tuple[str, ...]] = []

            def fake_git(_root: Path, *arguments: str) -> tuple[bytes, str]:
                calls.append(arguments)
                if arguments[:2] == ("rev-parse", "--verify"):
                    return b"a" * 40 + b"\n", "verified"
                if arguments[:2] == ("branch", "--show-current"):
                    return b"main\n", "verified"
                if "--ignored=matching" in arguments:
                    return (
                        b"?? new/sample.txt\0"
                        b"!! datasets/trace.txt\0"
                        b"?? _bmad-output/planning-artifacts/new-plan.md\0",
                        "verified",
                    )
                return b"?? new/sample.txt\0", "verified"

            with patch("parallel_truth_fingerprint.evidence.v1_baseline._run_git", fake_git):
                identity = collect_repository_identity(root)
        self.assertTrue(any("--untracked-files=all" in call for call in calls))
        overlays = {overlay.locator: overlay for overlay in identity.dirty_overlays}
        self.assertEqual(overlays["new/sample.txt"].origin, "untracked")
        self.assertEqual(overlays["datasets/trace.txt"].origin, "ignored_evidence")
        self.assertIsNotNone(overlays["new/sample.txt"].sha256)
        self.assertEqual(
            overlays["_bmad-output/planning-artifacts/new-plan.md"].origin,
            "excluded_post_v1",
        )
        self.assertIsNone(overlays["_bmad-output/planning-artifacts/new-plan.md"].sha256)

    def test_secret_bearing_ancestor_is_not_hashed_or_serialized(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            secret_dir = root / "dataset" / "private_keys"
            secret_dir.mkdir(parents=True)
            (secret_dir / "data.bin").write_bytes(b"secret-ancestor-canary")
            manifest = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"datasets": ("dataset",)},
            )
        rendered = canonical_json_bytes(manifest.to_dict()).decode("utf-8")
        self.assertNotIn("secret-ancestor-canary", rendered)
        self.assertNotIn("private_keys", rendered)
        self.assertEqual(manifest.entries[0].verification_status, "unverifiable")

    def test_compose_identity_tracks_safe_topology_but_not_secret_values(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            compose = root / "compose.local.yml"
            compose.write_text(
                "services:\n  app:\n    image: example/app:1\n"
                "    environment:\n      API_TOKEN: secret-one\n"
                "    ports:\n      - '8000:8000'\n",
                encoding="utf-8",
            )
            first = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"configuration": ("compose.local.yml",)},
            )
            compose.write_text(
                "services:\n  app:\n    image: example/app:1\n"
                "    environment:\n      API_TOKEN: secret-two\n"
                "    ports:\n      - '8000:8000'\n",
                encoding="utf-8",
            )
            secret_changed = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"configuration": ("compose.local.yml",)},
            )
            compose.write_text(
                "services:\n  app:\n    image: example/app:1\n"
                "    environment:\n      API_TOKEN: secret-two\n"
                "    ports:\n      - '9000:9000'\n",
                encoding="utf-8",
            )
            topology_changed = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"configuration": ("compose.local.yml",)},
            )
        self.assertEqual(first.entries[0].sha256, secret_changed.entries[0].sha256)
        self.assertNotEqual(first.entries[0].sha256, topology_changed.entries[0].sha256)
        self.assertNotIn("secret-one", canonical_json_bytes(first.to_dict()).decode("utf-8"))

    def test_compose_identity_redacts_list_style_secret_environment_values(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            compose = root / "compose.local.yml"
            compose.write_text(
                "services:\n  app:\n    environment:\n"
                "      - API_TOKEN=secret-list-one\n      - SAFE_MODE=true\n",
                encoding="utf-8",
            )
            first = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"configuration": ("compose.local.yml",)},
            )
            compose.write_text(
                "services:\n  app:\n    environment:\n"
                "      - API_TOKEN=secret-list-two\n      - SAFE_MODE=true\n",
                encoding="utf-8",
            )
            second = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"configuration": ("compose.local.yml",)},
            )
        self.assertEqual(first.entries[0].sha256, second.entries[0].sha256)
        self.assertNotIn("secret-list-one", canonical_json_bytes(first.to_dict()).decode("utf-8"))

    def test_validation_rejects_invalid_structure_and_missing_limitations(self) -> None:
        with self.assertRaises(BaselineError):
            validate_manifest(self._manifest((self._entry(sha256="garbage"),)))
        with self.assertRaises(BaselineError):
            validate_manifest(self._manifest((self._entry(byte_size=-1),)))
        with self.assertRaises(BaselineError):
            validate_manifest(
                self._manifest(
                    (
                        self._entry(
                            verification_status="missing",
                            byte_size=None,
                            sha256=None,
                            limitation=None,
                        ),
                    )
                )
            )

    def test_missing_inventory_locator_cannot_escape_project_root(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            with self.assertRaises(BaselineError):
                build_manifest(
                    project_root=Path(raw),
                    observed_at="2026-08-31T00:00:00Z",
                    expected_inventory={"code": ("../outside",)},
                )

    def test_evidence_root_requires_an_explicit_allowed_scientific_category(self) -> None:
        from scripts import freeze_v1_baseline as cli

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            evidence = root / "dataset"
            evidence.mkdir()
            self.assertEqual(
                cli.parse_evidence_root(f"datasets={evidence}", root),
                ("datasets", "dataset"),
            )
            with self.assertRaises(BaselineError):
                cli.parse_evidence_root(str(evidence), root)
            with self.assertRaises(BaselineError):
                cli.parse_evidence_root(f"code={evidence}", root)

    def test_cli_summary_includes_safe_limitation_text(self) -> None:
        from scripts import freeze_v1_baseline as cli

        manifest = manifest_with_identity(
            self._manifest(
                (
                    self._entry(
                        verification_status="missing",
                        byte_size=None,
                        sha256=None,
                        limitation="expected item is absent",
                    ),
                )
            )
        )
        rendered = "\n".join(cli.format_summary(manifest))
        self.assertIn("expected item is absent", rendered)

    def test_resolver_fails_closed_for_mutable_or_changed_entries(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / "src" / "sample.py"
            source.parent.mkdir()
            source.write_bytes(b"one")
            digest, status = sha256_file_stable(source)
            self.assertEqual(status, "verified")
            manifest = manifest_with_identity(
                self._manifest(
                    (
                        self._entry(
                            locator="src/sample.py",
                            byte_size=3,
                            sha256=digest,
                        ),
                    )
                )
            )
            manifest = self._publishable_manifest(root, manifest)
            self.assertEqual(resolve_entry(manifest, root, "code:sample"), source)
            source.write_bytes(b"two")
            with self.assertRaises(BaselineError):
                resolve_entry(manifest, root, "code:sample")
            mutable = manifest_with_identity(
                self._manifest(
                    (
                        self._entry(
                            verification_status="mutable",
                            sha256=None,
                            limitation="mutable evidence cannot be resolved",
                        ),
                    )
                )
            )
            with self.assertRaises(BaselineError):
                resolve_entry(mutable, root, "code:sample")

    def test_publish_is_manifest_last_and_never_overwrites(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            project_root = root / "project"
            manifest = self._materialized_manifest(project_root)
            output_root = project_root / "_bmad-output" / "evidence-artifacts" / "v1-baselines"
            first = publish_manifest(project_root, manifest)
            self.assertTrue(first.is_file())
            payload = json.loads(first.read_text(encoding="utf-8"))
            self.assertEqual(payload["baseline_id"], manifest.baseline_id)
            self.assertEqual(publish_manifest(project_root, manifest), first)
            changed = manifest_with_identity(self._manifest((self._entry(byte_size=4, sha256=manifest.entries[0].sha256),)))
            target = output_root / f"sha256-{(changed.baseline_id or '').removeprefix('sha256:')}"
            self.assertNotEqual(first, target)
            self.assertFalse(any(path.name == "latest" for path in output_root.rglob("*")))

    def test_publish_rejects_incomplete_or_different_existing_identity(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            project_root = root / "project"
            manifest = self._materialized_manifest(project_root)
            output_root = project_root / "_bmad-output" / "evidence-artifacts" / "v1-baselines"
            incomplete = output_root / f"sha256-{(manifest.baseline_id or '').removeprefix('sha256:')}"
            incomplete.mkdir(parents=True)
            with self.assertRaises(BaselineError):
                publish_manifest(project_root, manifest)

    def test_publish_revalidates_entries_before_finalization(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            project_root = root / "project"
            manifest = self._materialized_manifest(project_root)
            (project_root / "src" / "sample.py").write_bytes(b"changed")
            with self.assertRaises(BaselineError):
                publish_manifest(project_root, manifest)

    def test_collection_validation_and_resolution_have_no_runtime_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / "src" / "sample.py"
            source.parent.mkdir(parents=True)
            source.write_bytes(b"one")

            def snapshot() -> dict[str, bytes]:
                return {
                    path.relative_to(root).as_posix(): path.read_bytes()
                    for path in sorted(root.rglob("*"))
                    if path.is_file()
                }

            before = snapshot()
            manifest = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"code": ("src/sample.py",)},
            )
            validate_manifest(manifest)
            after_collection = snapshot()
            self.assertEqual(before, after_collection)
            manifest = self._publishable_manifest(root, manifest)
            before_resolution = snapshot()
            self.assertEqual(resolve_entry(manifest, root, "code:src/sample.py"), source)
            after_resolution = snapshot()

        self.assertEqual(before_resolution, after_resolution)

    def test_canonical_json_rejects_nan(self) -> None:
        with self.assertRaises(ValueError):
            canonical_json_bytes({"value": float("nan")})

    def test_manifest_authorization_effect_is_none(self) -> None:
        with self.assertRaises(BaselineError):
            validate_manifest(
                V1BaselineManifest(
                    **{**self._manifest().to_dict(), "authorization_effect": "implementation"}
                )
            )

    def test_default_inventory_includes_all_existing_result_tables(self) -> None:
        expected = set(DEFAULT_EXPECTED_INVENTORY["recorded_results"])
        self.assertTrue(
            {
                "docs/seminario-andamento/tables/champion-class-metrics.csv",
                "docs/seminario-andamento/tables/adfa-ld-dataset-summary.csv",
                "docs/seminario-andamento/tables/custom-dataset-summary.csv",
            }.issubset(expected)
        )

    def test_unresolved_recorded_result_is_not_promoted_to_measured(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            result = root / "result.csv"
            result.write_text("metric,value\naccuracy,1.0\n", encoding="utf-8")
            manifest = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"recorded_results": ("result.csv",)},
            )
        self.assertEqual(manifest.entries[0].scientific_status, "LEGACY_BASELINE")
        self.assertEqual(manifest.entries[0].role, "historical_result")
        self.assertIsNone(manifest.entries[0].evidence_origin)
        self.assertIn("not admitted as a measured result", manifest.entries[0].limitation or "")

    def test_compose_identity_excludes_unapproved_environment_keys(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            compose = root / "compose.local.yml"
            compose.write_text(
                "services:\n  app:\n    image: example/app:1\n"
                "    environment:\n      SESSION: opaque-one-92\n",
                encoding="utf-8",
            )
            first = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"configuration": ("compose.local.yml",)},
            )
            compose.write_text(
                "services:\n  app:\n    image: example/app:1\n"
                "    environment:\n      SESSION: opaque-two-47\n",
                encoding="utf-8",
            )
            second = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"configuration": ("compose.local.yml",)},
            )
        self.assertEqual(first.entries[0].sha256, second.entries[0].sha256)
        self.assertNotIn("opaque-one-92", canonical_json_bytes(first.to_dict()).decode("utf-8"))

    def test_mutable_pointer_rejects_secret_bearing_url_target(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            pointer = root / "latest.json"
            pointer.write_text(
                '{"target":"https://alice:secret-pointer-canary@example.invalid/run"}',
                encoding="utf-8",
            )
            manifest = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"mutable_pointer": ("latest.json",)},
            )
        self.assertEqual(manifest.entries[0].verification_status, "corrupt")
        self.assertIsNone(manifest.entries[0].observed_target)
        self.assertNotIn("secret-pointer-canary", canonical_json_bytes(manifest.to_dict()).decode("utf-8"))

    def test_configuration_identity_cannot_resolve_to_raw_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            config = root / ".env.example"
            config.write_text("DEMO_POWER=65\nPASSWORD=raw-secret\n", encoding="utf-8")
            manifest = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"configuration": (".env.example",)},
            )
            with self.assertRaises(BaselineError):
                resolve_entry(manifest, root, manifest.entries[0].entry_id)

    def test_legacy_directory_does_not_promote_latest_pointer_child(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            history = root / "history"
            history.mkdir()
            (history / "run.json").write_text('{"run":"a"}', encoding="utf-8")
            (history / "latest.json").write_text('{"target":"run.json"}', encoding="utf-8")
            manifest = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={
                    "legacy_baseline": ("history",),
                    "mutable_pointer": ("history/latest.json",),
                },
            )
        latest_entries = [entry for entry in manifest.entries if entry.locator == "history/latest.json"]
        self.assertEqual(len(latest_entries), 1)
        self.assertEqual(latest_entries[0].verification_status, "mutable")

    def test_publish_revalidates_repository_identity(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project_root = Path(raw) / "project"
            manifest = self._materialized_manifest(project_root)
            changed = replace(manifest.repository, branch="changed-after-collection")
            with patch(
                "parallel_truth_fingerprint.evidence.v1_baseline.collect_repository_identity",
                return_value=changed,
            ):
                with self.assertRaises(BaselineError):
                    publish_manifest(project_root, manifest)

    def test_ignored_derived_root_is_never_recursively_hashed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            derived = root / ".venv"
            derived.mkdir()
            (derived / "package.bin").write_bytes(b"must-not-be-hashed")

            def fake_git(_root: Path, *arguments: str) -> tuple[bytes, str]:
                if arguments[:2] == ("rev-parse", "--verify"):
                    return b"a" * 40 + b"\n", "verified"
                if arguments[:2] == ("branch", "--show-current"):
                    return b"main\n", "verified"
                if "--ignored=matching" in arguments:
                    return b"!! .venv/\0", "verified"
                return b"", "verified"

            with (
                patch("parallel_truth_fingerprint.evidence.v1_baseline._run_git", fake_git),
                patch(
                    "parallel_truth_fingerprint.evidence.v1_baseline.sha256_file_stable",
                    side_effect=AssertionError("derived root content was hashed"),
                ),
            ):
                identity = collect_repository_identity(root)
        overlay = identity.dirty_overlays[0]
        self.assertEqual(overlay.verification_status, "unverifiable")
        self.assertIsNone(overlay.sha256)

    def test_git_rename_secret_source_is_redacted_and_status_digest_is_stable(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "public.txt").write_text("public", encoding="utf-8")

            def collect(secret_name: str) -> RepositoryIdentity:
                def fake_git(_root: Path, *arguments: str) -> tuple[bytes, str]:
                    if arguments[:2] == ("rev-parse", "--verify"):
                        return b"a" * 40 + b"\n", "verified"
                    if arguments[:2] == ("branch", "--show-current"):
                        return b"main\n", "verified"
                    status = f"R  public.txt\0{secret_name}\0".encode()
                    return status, "verified"

                with patch("parallel_truth_fingerprint.evidence.v1_baseline._run_git", fake_git):
                    return collect_repository_identity(root)

            first = collect("private_token_one.txt")
            second = collect("private_token_two.txt")
        originals = [item for item in first.dirty_overlays if item.status_code.endswith(":original")]
        self.assertTrue(originals[0].locator.startswith("[REDACTED_SECRET_PATH]"))
        self.assertEqual(first.status_sha256, second.status_sha256)

    def test_publish_rejects_output_symlink_escape(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            project_root = root / "project"
            project_root.mkdir()
            outside = root / "outside"
            outside.mkdir()
            output_link = project_root / "_bmad-output"
            try:
                output_link.symlink_to(outside, target_is_directory=True)
            except OSError:
                self.skipTest("directory symlink creation unavailable")
            manifest = self._materialized_manifest(project_root)
            with patch(
                "parallel_truth_fingerprint.evidence.v1_baseline.collect_repository_identity",
                return_value=manifest.repository,
            ):
                with self.assertRaises(BaselineError):
                    publish_manifest(project_root, manifest)
        self.assertFalse(any(outside.rglob("baseline-manifest.v1.json")))

    def test_validation_rejects_non_utc_observation_time(self) -> None:
        with self.assertRaises(BaselineError):
            validate_manifest(replace(self._manifest(), observed_at="2026-08-31 00:00:00"))
        with self.assertRaises(BaselineError):
            validate_manifest(replace(self._manifest(), observed_at="2026-02-30T00:00:00Z"))

    def test_malformed_container_digest_is_not_reported_as_digest_pinned(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            compose = root / "compose.local.yml"
            compose.write_text(
                "services:\n  app:\n    image: example/app@sha256:not-a-digest\n",
                encoding="utf-8",
            )
            manifest = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"configuration": ("compose.local.yml",)},
                include_declared_runtime=True,
            )
        image = next(entry for entry in manifest.entries if entry.category == "image_reference")
        self.assertIn("invalid digest", image.limitation or "")

    def test_non_regular_mutable_pointer_is_unverifiable(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            pointer = root / "latest.json"
            pointer.mkdir()
            manifest = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"mutable_pointer": ("latest.json",)},
            )
        self.assertEqual(manifest.entries[0].verification_status, "unverifiable")
        self.assertIn("regular file", manifest.entries[0].limitation or "")

    def test_mutable_pointer_identity_ignores_non_allowlisted_secret_fields(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            pointer = root / "latest.json"
            pointer.write_text(
                '{"target":"runs/run-a.json","password":"opaque-one-92"}',
                encoding="utf-8",
            )
            first = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"mutable_pointer": ("latest.json",)},
            )
            pointer.write_text(
                '{"target":"runs/run-a.json","password":"opaque-two-47"}',
                encoding="utf-8",
            )
            second = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"mutable_pointer": ("latest.json",)},
            )
        self.assertEqual(first.entries[0].sha256, second.entries[0].sha256)
        self.assertNotIn("opaque-one-92", canonical_json_bytes(first.to_dict()).decode("utf-8"))

    def test_existing_final_manifest_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            project_root = root / "project"
            manifest = self._materialized_manifest(project_root)
            digest = (manifest.baseline_id or "").removeprefix("sha256:")
            target = (
                project_root
                / "_bmad-output/evidence-artifacts/v1-baselines"
                / f"sha256-{digest}/baseline-manifest.v1.json"
            )
            target.parent.mkdir(parents=True)
            external = root / "external.json"
            external.write_bytes(canonical_json_bytes(manifest.to_dict()))
            try:
                target.symlink_to(external)
            except OSError:
                self.skipTest("file symlink creation unavailable")
            with self.assertRaises(BaselineError):
                publish_manifest(project_root, manifest)

    def test_compose_identity_excludes_credential_bearing_scalar_values(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            compose = root / "compose.local.yml"
            compose.write_text(
                "services:\n  app:\n    build: https://alice:opaque-one-92@example.invalid/repo\n",
                encoding="utf-8",
            )
            first = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"configuration": ("compose.local.yml",)},
            )
            compose.write_text(
                "services:\n  app:\n    build: https://bob:opaque-two-47@example.invalid/repo\n",
                encoding="utf-8",
            )
            second = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"configuration": ("compose.local.yml",)},
            )
        self.assertEqual(first.entries[0].sha256, second.entries[0].sha256)

    def test_git_branch_and_post_v1_secret_path_are_redacted(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)

            def fake_git(_root: Path, *arguments: str) -> tuple[bytes, str]:
                if arguments[:2] == ("rev-parse", "--verify"):
                    return b"a" * 40 + b"\n", "verified"
                if arguments[:2] == ("branch", "--show-current"):
                    return b"feature/private_token_canary\n", "verified"
                return (
                    b"?? _bmad-output/planning-artifacts/private_token_canary.md\0",
                    "verified",
                )

            with patch("parallel_truth_fingerprint.evidence.v1_baseline._run_git", fake_git):
                identity = collect_repository_identity(root)
        rendered = canonical_json_bytes(identity.to_dict()).decode("utf-8")
        self.assertNotIn("private_token_canary", rendered)
        self.assertTrue(identity.branch and identity.branch.startswith("[REDACTED_SECRET_PATH]"))
        self.assertEqual(identity.dirty_overlays[0].origin, "excluded_post_v1")

    def test_known_absence_that_exists_never_becomes_verified(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "unexpected.bin").write_bytes(b"now-present")
            manifest = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"known_absence": ("unexpected.bin",)},
            )
        self.assertEqual(manifest.entries[0].verification_status, "unverifiable")
        self.assertIsNone(manifest.entries[0].sha256)
        self.assertIn("expected absent", manifest.entries[0].limitation or "")

    def test_dirty_configuration_overlay_uses_redacted_identity(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            compose = root / "compose.local.yml"

            def fake_git(_root: Path, *arguments: str) -> tuple[bytes, str]:
                if arguments[:2] == ("rev-parse", "--verify"):
                    return b"a" * 40 + b"\n", "verified"
                if arguments[:2] == ("branch", "--show-current"):
                    return b"main\n", "verified"
                return b" M compose.local.yml\0", "verified"

            compose.write_text(
                "services:\n  app:\n    environment:\n      SESSION: opaque-one-92\n",
                encoding="utf-8",
            )
            with patch("parallel_truth_fingerprint.evidence.v1_baseline._run_git", fake_git):
                first = collect_repository_identity(root)
            compose.write_text(
                "services:\n  app:\n    environment:\n      SESSION: opaque-two-47\n",
                encoding="utf-8",
            )
            with patch("parallel_truth_fingerprint.evidence.v1_baseline._run_git", fake_git):
                second = collect_repository_identity(root)
        self.assertEqual(first.dirty_overlays[0].sha256, second.dirty_overlays[0].sha256)

    def test_git_status_fallback_preserves_overlays_when_ignored_query_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "tracked.txt").write_text("tracked", encoding="utf-8")

            def fake_git(_root: Path, *arguments: str) -> tuple[bytes | None, str]:
                if arguments[:2] == ("rev-parse", "--verify"):
                    return b"a" * 40 + b"\n", "verified"
                if arguments[:2] == ("branch", "--show-current"):
                    return b"main\n", "verified"
                if "--ignored=matching" in arguments:
                    return None, "unverifiable"
                return b" M tracked.txt\0", "verified"

            with patch("parallel_truth_fingerprint.evidence.v1_baseline._run_git", fake_git):
                identity = collect_repository_identity(root)
        self.assertEqual([item.locator for item in identity.dirty_overlays], ["tracked.txt"])
        self.assertEqual(identity.dirty_overlays[0].verification_status, "verified")

    def test_fixture_origin_is_populated_and_contradictions_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "fixture.txt").write_text("fixture", encoding="utf-8")
            manifest = build_manifest(
                project_root=root,
                observed_at="2026-08-31T00:00:00Z",
                expected_inventory={"fixtures": ("fixture.txt",)},
            )
        self.assertEqual(manifest.entries[0].evidence_origin, "test_fixture")
        contradictory = replace(manifest.entries[0], evidence_origin="official_native")
        with self.assertRaises(BaselineError):
            validate_manifest(self._manifest((contradictory,)))

    def test_publication_link_failure_removes_incomplete_final_directory(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project_root = Path(raw) / "project"
            manifest = self._materialized_manifest(project_root)
            digest = (manifest.baseline_id or "").removeprefix("sha256:")
            final_directory = (
                project_root
                / "_bmad-output/evidence-artifacts/v1-baselines"
                / f"sha256-{digest}"
            )
            with patch("parallel_truth_fingerprint.evidence.v1_baseline.os.link", side_effect=OSError("no link")):
                with self.assertRaises(BaselineError):
                    publish_manifest(project_root, manifest)
            self.assertFalse(final_directory.exists())

    def test_cli_summary_includes_repository_and_overlay_limitations(self) -> None:
        from scripts import freeze_v1_baseline as cli

        repository = RepositoryIdentity(
            head=None,
            branch=None,
            status_sha256=None,
            status_verification="unverifiable",
            ignored_status_sha256=None,
            ignored_status_verification="unverifiable",
            dirty_overlays=(
                DirtyOverlay(
                    locator="[REDACTED_SECRET_PATH]/1",
                    status_code="??",
                    byte_size=None,
                    sha256=None,
                    verification_status="unverifiable",
                    limitation="secret overlay excluded",
                    origin="untracked",
                ),
            ),
        )
        manifest = manifest_with_identity(replace(self._manifest(), repository=repository))
        rendered = "\n".join(cli.format_summary(manifest))
        self.assertIn("repository_status:unverifiable", rendered)
        self.assertIn("ignored_status:unverifiable", rendered)
        self.assertIn("secret overlay excluded", rendered)

    def test_missing_entry_rejects_fabricated_identity_metadata(self) -> None:
        for overrides in (
            {"byte_size": 3},
            {"observed_target": "invented-target"},
        ):
            entry = self._entry(
                verification_status="missing",
                sha256=None,
                limitation="expected item is absent",
                **overrides,
            )
            with self.subTest(overrides=overrides):
                with self.assertRaises(BaselineError):
                    validate_manifest(self._manifest((entry,)))

    def test_common_credential_file_names_are_excluded_without_hashing(self) -> None:
        for secret_name in (".npmrc", ".pypirc", "auth.json", "id_rsa", "key.pem"):
            with self.subTest(secret_name=secret_name), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                secret = root / secret_name
                secret.write_text("opaque-credential-canary", encoding="utf-8")
                manifest = build_manifest(
                    project_root=root,
                    observed_at="2026-08-31T00:00:00Z",
                    expected_inventory={"code": (secret_name,)},
                )
                self.assertEqual(manifest.entries[0].verification_status, "unverifiable")
                self.assertIsNone(manifest.entries[0].sha256)
                self.assertNotIn(
                    "opaque-credential-canary",
                    canonical_json_bytes(manifest.to_dict()).decode("utf-8"),
                )

    def test_result_inventory_includes_validation_and_markdown_companions(self) -> None:
        stems = {
            "adfa-ld-binary-results",
            "adfa-ld-multiclass-results",
            "champion-run-summary",
            "confusion-matrix",
            "champion-class-metrics",
            "adfa-ld-dataset-summary",
            "custom-dataset-summary",
            "validation-scenarios",
        }
        expected = set(DEFAULT_EXPECTED_INVENTORY["recorded_results"])
        required = {
            f"docs/seminario-andamento/tables/{stem}.{suffix}"
            for stem in stems
            for suffix in ("csv", "md")
        }
        self.assertTrue(required.issubset(expected))

    def test_resolver_requires_the_published_manifest_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project_root = Path(raw) / "project"
            manifest = self._materialized_manifest(project_root)
            with self.assertRaises(BaselineError):
                resolve_entry(manifest, project_root, "code:sample")
            publish_manifest(project_root, manifest)
            self.assertEqual(
                resolve_entry(manifest, project_root, "code:sample"),
                project_root / "src/sample.py",
            )

    def test_identical_publication_rerun_precedes_repository_revalidation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project_root = Path(raw) / "project"
            manifest = self._materialized_manifest(project_root)
            first = publish_manifest(project_root, manifest)
            changed_repository = replace(manifest.repository, branch="changed-after-publication")
            with patch(
                "parallel_truth_fingerprint.evidence.v1_baseline.collect_repository_identity",
                return_value=changed_repository,
            ):
                self.assertEqual(publish_manifest(project_root, manifest), first)


if __name__ == "__main__":
    unittest.main()
