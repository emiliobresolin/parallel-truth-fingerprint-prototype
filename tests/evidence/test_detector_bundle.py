"""Focused non-domain tests for immutable physical DetectorBundle.v1."""
from __future__ import annotations

import unittest
from dataclasses import replace

from parallel_truth_fingerprint.contracts.detector_bundle import (
    DETECTOR_BUNDLE_SCHEMA, PHYSICAL_FEATURE_SCHEMA_VERSION,
    PHYSICAL_MODEL_CONTRACT_VERSION, BundleComponentHash, DetectorBundle,
    detector_bundle_identity,
)
from parallel_truth_fingerprint.evidence.detector_bundle import (
    DeclaredBundleEnvironment, assemble_detector_bundle, load_detector_bundle,
    validate_detector_bundle,
)


def digest(number: int) -> str:
    return "sha256:" + f"{number:064x}"


class DetectorBundleTests(unittest.TestCase):
    def bundle(self) -> DetectorBundle:
        ids = {name: digest(index) for index, name in enumerate((
            "architecture", "weights", "feature_schema", "preprocessing",
            "training_dataset", "training_split", "calibration_dataset",
            "calibration_split", "calibration_artifact", "threshold",
            "threshold_derivation", "profile_compatibility", "code",
            "dependency_lock", "runtime",
        ), 1)}
        return assemble_detector_bundle(DetectorBundle(
            DETECTOR_BUNDLE_SCHEMA, "lstm_ae", PHYSICAL_MODEL_CONTRACT_VERSION,
            ids["architecture"], ids["weights"], ids["feature_schema"], PHYSICAL_FEATURE_SCHEMA_VERSION,
            ("current", "pressure"), ids["preprocessing"], ids["training_dataset"], ids["training_split"],
            ids["calibration_dataset"], ids["calibration_split"], ids["calibration_artifact"],
            ids["threshold"], ids["threshold_derivation"], "higher_anomalous", ids["profile_compatibility"],
            ids["code"], ids["dependency_lock"], ids["runtime"],
            tuple(BundleComponentHash(name, ids[name], digest(100 + index)) for index, name in enumerate(sorted(ids))),
        ))

    def environment(self, bundle: DetectorBundle) -> DeclaredBundleEnvironment:
        return DeclaredBundleEnvironment(
            bundle.model_contract_version, bundle.feature_schema_id, bundle.feature_schema_version,
            bundle.ordered_feature_names, bundle.profile_compatibility_id, bundle.code_identity,
            bundle.dependency_lock_sha256, bundle.runtime_identity,
        )

    def resolver(self, bundle: DetectorBundle):
        entries = {item.artifact_id: item.serialized_sha256 for item in bundle.component_hashes}
        return entries.get

    def test_assembly_is_canonical_complete_and_inference_only(self) -> None:
        bundle = self.bundle()
        self.assertTrue(validate_detector_bundle(bundle).valid)
        self.assertTrue(bundle.bundle_id.startswith("sha256:"))
        self.assertNotIn("fit", " ".join(dir(__import__("parallel_truth_fingerprint.evidence.detector_bundle", fromlist=["*"]))))

    def test_every_identity_bearing_change_creates_a_new_identity(self) -> None:
        bundle = self.bundle()
        component_fields = {
            "architecture_id": "architecture", "weights_id": "weights", "feature_schema_id": "feature_schema",
            "preprocessing_state_id": "preprocessing", "training_dataset_id": "training_dataset",
            "training_split_id": "training_split", "calibration_dataset_id": "calibration_dataset",
            "calibration_split_id": "calibration_split", "calibration_artifact_id": "calibration_artifact",
            "threshold_id": "threshold", "threshold_derivation_id": "threshold_derivation",
            "profile_compatibility_id": "profile_compatibility", "code_identity": "code",
            "dependency_lock_sha256": "dependency_lock", "runtime_identity": "runtime",
        }
        for index, (field, component_name) in enumerate(component_fields.items(), 900):
            value = digest(index)
            changed = replace(bundle, **{field: value}, component_hashes=tuple(
                replace(item, artifact_id=value) if item.name == component_name else item
                for item in bundle.component_hashes
            ))
            self.assertNotEqual(bundle.bundle_id, assemble_detector_bundle(changed).bundle_id, field)
        for field, value in (("model_family", "gru_ae"), ("ordered_feature_names", ("pressure", "current")),
                             ("score_direction", "lower_anomalous"),
                             ("model_contract_version", "PhysicalDetectorModel.v3")):
            changed = replace(bundle, **{field: value})
            # An unsupported version is intentionally not assembled, but it
            # still changes the canonical address and is rejected structurally.
            self.assertNotEqual(bundle.bundle_id, detector_bundle_identity(changed), field)
            if field != "model_contract_version":
                self.assertNotEqual(bundle.bundle_id, assemble_detector_bundle(changed).bundle_id, field)
        self.assertEqual(bundle.bundle_id, assemble_detector_bundle(bundle).bundle_id)

    def test_load_verifies_all_components_and_declared_environment_atomically(self) -> None:
        bundle = self.bundle()
        loaded = load_detector_bundle(bundle, environment=self.environment(bundle), component_resolver=self.resolver(bundle))
        self.assertTrue(loaded.loaded)
        missing = load_detector_bundle(bundle, environment=self.environment(bundle), component_resolver=lambda _: None)
        self.assertFalse(missing.loaded)
        self.assertIn("DB13_COMPONENT_UNAVAILABLE", missing.diagnostic_codes)
        wrong = replace(self.environment(bundle), ordered_feature_names=("pressure", "current"))
        mismatch = load_detector_bundle(bundle, environment=wrong, component_resolver=self.resolver(bundle))
        self.assertFalse(mismatch.loaded)
        self.assertIn("DB13_ENVIRONMENT_FEATURE_ORDER_MISMATCH", mismatch.diagnostic_codes)

    def test_legacy_or_mixed_schema_and_mutable_component_are_explicitly_rejected(self) -> None:
        bundle = self.bundle()
        legacy = replace(bundle, model_contract_version="PhysicalDetectorModel.v1")
        self.assertIn("DB13_MODEL_CONTRACT_INCOMPATIBLE", validate_detector_bundle(legacy).diagnostic_codes)
        mixed = replace(bundle, feature_schema_version="PhysicalFeatureSchema.v1")
        self.assertIn("DB13_FEATURE_SCHEMA_INCOMPATIBLE", validate_detector_bundle(mixed).diagnostic_codes)
        stale = replace(bundle, component_hashes=tuple(
            replace(item, serialized_sha256="latest") if item.name == "weights" else item for item in bundle.component_hashes
        ))
        self.assertIn("DB13_COMPONENT_HASH_INVALID", validate_detector_bundle(stale).diagnostic_codes)

    def test_tampering_and_noncanonical_component_order_fail_closed(self) -> None:
        bundle = self.bundle()
        altered = replace(bundle, ordered_feature_names=("pressure", "current"))
        self.assertIn("DB13_BUNDLE_ID_MISMATCH", validate_detector_bundle(altered).diagnostic_codes)
        unsorted = replace(bundle, component_hashes=tuple(reversed(bundle.component_hashes)))
        self.assertIn("DB13_COMPONENT_ORDER_NONCANONICAL", validate_detector_bundle(unsorted).diagnostic_codes)


if __name__ == "__main__":
    unittest.main()
