from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile


_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "qualify_live_run.py"
_SPEC = importlib.util.spec_from_file_location("qualify_live_run", _SCRIPT)
assert _SPEC and _SPEC.loader
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)


class LiveRunPreflightTests(unittest.TestCase):
    def test_missing_official_bytes_blocks_execution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report = _MODULE.qualify(project_root=Path(directory))
        self.assertFalse(report["runtime_may_start"])
        self.assertIn("HAI_23_05_OFFICIAL_BYTES_UNAVAILABLE", report["blockers"])
        self.assertIn("LID_DS_2021_OFFICIAL_BYTES_UNAVAILABLE", report["blockers"])

    def test_complete_real_byte_layout_is_ready(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            hai = root / "datasets" / "HAI-23.05" / "hai-23.05"
            hai.mkdir(parents=True)
            for name in ("hai-train1.csv", "hai-train2.csv", "hai-train3.csv", "hai-train4.csv", "hai-test1.csv", "hai-test2.csv", "label-test1.csv", "label-test2.csv"):
                (hai / name).write_text("timestamp,value\n", encoding="utf-8")
            lid = root / "datasets" / "LID-DS-2021" / "scenario"
            (lid / "normal").mkdir(parents=True)
            (lid / "attack").mkdir()
            (lid / "normal" / "trace.sc2").write_text("1\n", encoding="utf-8")
            (lid / "attack" / "trace.sc2").write_text("2\n", encoding="utf-8")
            report = _MODULE.qualify(project_root=root)
        self.assertTrue(report["runtime_may_start"])

    def test_owner_kaggle_layout_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            hai = root / "datasets" / "HAI-23.05-kaggle" / "hai-23.05"
            hai.mkdir(parents=True)
            for name in ("hai-train1.csv", "hai-train2.csv", "hai-train3.csv", "hai-train4.csv", "hai-test1.csv", "hai-test2.csv", "label-test1.csv", "label-test2.csv"):
                (hai / name).write_text("timestamp,value\n", encoding="utf-8")
            lid = root / "datasets" / "LID-DS-2021" / "scenario"
            (lid / "normal").mkdir(parents=True)
            (lid / "attack").mkdir()
            (lid / "normal" / "trace.sc2").write_text("1\n", encoding="utf-8")
            (lid / "attack" / "trace.sc2").write_text("2\n", encoding="utf-8")
            report = _MODULE.qualify(project_root=root)
        self.assertTrue(report["runtime_may_start"])

    def test_complete_kaggle_hai_wins_over_incomplete_legacy_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "datasets" / "HAI-23.05" / "hai-23.05").mkdir(parents=True)
            hai = root / "datasets" / "HAI-23.05-kaggle" / "hai-23.05"
            hai.mkdir(parents=True)
            for name in ("hai-train1.csv", "hai-train2.csv", "hai-train3.csv", "hai-train4.csv", "hai-test1.csv", "hai-test2.csv", "label-test1.csv", "label-test2.csv"):
                (hai / name).write_text("timestamp,value\n", encoding="utf-8")
            lid = root / "datasets" / "LID-DS-2021" / "scenario"
            (lid / "normal").mkdir(parents=True)
            (lid / "attack").mkdir()
            (lid / "normal" / "trace.sc2").write_text("1\n", encoding="utf-8")
            (lid / "attack" / "trace.sc2").write_text("2\n", encoding="utf-8")
            report = _MODULE.qualify(project_root=root)
        self.assertTrue(report["runtime_may_start"])
        self.assertIn("HAI-23.05-kaggle", report["hai_23_05"]["root"])

    def test_split_lid_roles_do_not_authorize_execution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            hai = root / "datasets" / "HAI-23.05" / "hai-23.05"
            hai.mkdir(parents=True)
            for name in ("hai-train1.csv", "hai-train2.csv", "hai-train3.csv", "hai-train4.csv", "hai-test1.csv", "hai-test2.csv", "label-test1.csv", "label-test2.csv"):
                (hai / name).write_text("timestamp,value\n", encoding="utf-8")
            normal = root / "datasets" / "LID-DS-2021" / "scenario-a" / "normal"
            attack = root / "datasets" / "LID-DS-2021" / "scenario-b" / "attack"
            normal.mkdir(parents=True)
            attack.mkdir(parents=True)
            (normal / "trace.sc2").write_text("1\n", encoding="utf-8")
            (attack / "trace.sc2").write_text("2\n", encoding="utf-8")
            report = _MODULE.qualify(project_root=root)
        self.assertFalse(report["runtime_may_start"])
        self.assertIn("LID_DS_2021_OFFICIAL_BYTES_UNAVAILABLE", report["blockers"])

    def test_empty_or_lfs_lid_traces_do_not_authorize_execution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            hai = root / "datasets" / "HAI-23.05" / "hai-23.05"
            hai.mkdir(parents=True)
            for name in ("hai-train1.csv", "hai-train2.csv", "hai-train3.csv", "hai-train4.csv", "hai-test1.csv", "hai-test2.csv", "label-test1.csv", "label-test2.csv"):
                (hai / name).write_text("timestamp,value\n", encoding="utf-8")
            lid = root / "datasets" / "LID-DS-2021" / "scenario"
            (lid / "normal").mkdir(parents=True)
            (lid / "attack").mkdir()
            (lid / "normal" / "empty.sc2").write_bytes(b"")
            (lid / "attack" / "pointer.sc2").write_text(
                "version https://git-lfs.github.com/spec/v1\n", encoding="utf-8"
            )
            report = _MODULE.qualify(project_root=root)
        self.assertFalse(report["runtime_may_start"])
        self.assertIn("LID_DS_2021_OFFICIAL_BYTES_UNAVAILABLE", report["blockers"])

    def test_official_lid_archive_layout_is_accepted_without_expansion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            hai = root / "datasets" / "HAI-23.05" / "hai-23.05"
            hai.mkdir(parents=True)
            for name in (
                "hai-train1.csv", "hai-train2.csv", "hai-train3.csv", "hai-train4.csv",
                "hai-test1.csv", "hai-test2.csv", "label-test1.csv", "label-test2.csv",
            ):
                (hai / name).write_text("timestamp,value\n", encoding="utf-8")
            scenario = root / "datasets" / "LID-DS-2021-real" / "scenario"
            for role in ("training", "validation", "test/normal", "test/normal_and_attack"):
                archive = scenario / role / "recording.zip"
                archive.parent.mkdir(parents=True, exist_ok=True)
                with zipfile.ZipFile(archive, "w") as bundle:
                    bundle.writestr("recording.sc", "1 0 1 p 1 read >\n")
            report = _MODULE.qualify(project_root=root)
        self.assertTrue(report["runtime_may_start"])
        self.assertEqual(report["lid_ds_2021"]["trace_count"], 4)

    def test_current_domain_gate_is_required_and_accountable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report = _MODULE.qualify(project_root=Path(directory))
        self.assertEqual(
            report["current_domain_parameter_gate"]["accountability_outcome"],
            "accountable",
        )
        self.assertNotIn("CURRENT_DOMAIN_PARAMETER_GATE_BLOCKED", report["blockers"])


if __name__ == "__main__":
    unittest.main()
