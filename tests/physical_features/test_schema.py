from __future__ import annotations

import unittest

from parallel_truth_fingerprint.contracts.signal_observation import observation_content_id, parse_signal_observation
from parallel_truth_fingerprint.physical_features import (
    FeatureDefinition, FeatureSchemaError, OperatingContextValue,
    LegacyBaselineCatalogue,
    build_physical_features, register_physical_feature_schema,
    validate_physical_feature_schema,
)


def digest(number: int) -> str: return "sha256:" + f"{number:064x}"


def reference(number: int) -> dict[str, object]:
    return {"revision_id": digest(number), "serialized_sha256": digest(number + 1), "subject_sha256": None,
            "contract_id": "fixture", "contract_version": "v1", "locator": "fixture", "evidence_role": "fixture"}


def observation() -> object:
    uses = [{"role": "fixture", "target_revision_ref": reference(10), "target_bytes_hash": digest(12)}]
    derivation = {"direction": "current_to_normalized", "transform_revision_ref": reference(20),
                  "profile_revision_ref": reference(24), "input_representation": "raw_current",
                  "output_representation": "normalized_span", "parameter_uses": uses}
    payload: dict[str, object] = {
        "contract_id": "SignalObservation", "schema_version": 2, "schema_ref": reference(30),
        "record_role": "primary_per_edge", "audience_access_class": "detector_facing",
        "semantic_identity": {"modality": "fixture"},
        "experiment_id": digest(31), "run_id": digest(32), "round_id": digest(33), "edge_id": digest(34),
        "sensor_id": digest(35), "source_stream_id": digest(36), "source_boot_id": digest(37),
        "source_session_id": digest(38), "event_id": digest(39), "source_sequence": 1,
        "correlation": {"correlation_id": digest(40), "evidence_state": "unknown", "method": {"state": "unavailable", "reason": "fixture"}, "measured_uncertainty": {"state": "unavailable", "reason": "fixture"}},
        "source_timestamp": "2026-01-01T00:00:00.000000Z", "observed_timestamp": "2026-01-01T00:00:01.000000Z",
        "clock": {"source_clock_id": digest(41), "observed_clock_id": digest(42), "evidence_status": "unknown", "method": {"state": "unavailable", "reason": "fixture"}, "measured_offset": {"state": "unavailable", "reason": "fixture"}, "measured_uncertainty": {"state": "unavailable", "reason": "fixture"}, "qualification_policy": {"state": "unavailable", "reason": "fixture"}},
        "profile_binding": {"profile_id": digest(50), "profile_revision_ref": reference(51), "profile_canonical_bytes_hash": digest(53), "catalog_snapshot_ref": reference(54), "catalog_snapshot_hash": digest(56), "parameter_gate_result_ref": reference(57), "consumed_parameters": uses},
        "raw_current": {"state": "present", "value": "3.5", "unit": "mA"}, "diagnostics": [],
        "quality_trace": {"outcome": "in_range", "conversion_disposition": "convert", "applied_rule_ids": ["fixture"], "diagnostic_ids_used": [], "parameter_uses": uses},
        "normalized_span": {"state": "derived", "value": "-0.1", "quantity_kind": "normalized_span", "unit": "one", "derivation": derivation},
        "engineering_value": {"state": "derived", "value": "1", "quantity_kind": "fixture_quantity", "unit": "fixture_unit", "derivation": {**derivation, "direction": "current_to_engineering_or_reference", "output_representation": "engineering_value"}},
    }
    payload["observation_content_id"] = observation_content_id(payload)
    return parse_signal_observation(payload)


class PhysicalFeatureSchemaTests(unittest.TestCase):
    def feature(self, **changes: object) -> FeatureDefinition:
        data: dict[str, object] = {"name": "normalized_signal", "source_field": "normalized_span.value",
            "representation": "normalized_span", "unit": "one", "data_type": "canonical_decimal",
            "compatible_profile_ids": (digest(50),), "missingness_policy": "forbid",
            "parameter_evidence_references": (digest(60),), "preprocessing_id": digest(61)}
        data.update(changes)
        return FeatureDefinition(**data)  # type: ignore[arg-type]

    def schema(self, *features: FeatureDefinition):
        return register_physical_feature_schema(schema_id="compressor_current", version="v2", features=features or (self.feature(),))

    def test_registration_is_hashed_ordered_and_authority_validated(self) -> None:
        schema = self.schema()
        self.assertEqual(schema.schema_content_id, self.schema().schema_content_id)
        self.assertEqual(("normalized_signal",), tuple(item.name for item in schema.features))
        self.assertIs(validate_physical_feature_schema(schema, immutable_resolver=lambda _: True), schema)
        with self.assertRaises(FeatureSchemaError) as caught:
            validate_physical_feature_schema(schema, immutable_resolver=lambda _: False)
        self.assertEqual("PFS2_AUTHORITY", caught.exception.code)

    def test_canonical_observation_projection_never_reconverts(self) -> None:
        schema = self.schema(self.feature(), self.feature(name="current", source_field="raw_current.value", representation="raw_current", unit="mA"))
        row = build_physical_features(observation(), schema, immutable_resolver=lambda _: True)
        self.assertEqual(("normalized_signal", "current"), tuple(item.name for item in row.values))
        self.assertEqual(("-0.1", "3.5"), tuple(item.value for item in row.values))
        self.assertEqual((1.0, 2.0), row.tensor(frozen_preprocessor_id=digest(61), transform=lambda value: 1 if value.name == "normalized_signal" else 2))

    def test_profile_mix_missingness_and_unknown_source_fail_closed(self) -> None:
        with self.assertRaises(FeatureSchemaError) as caught:
            build_physical_features(observation(), self.schema(self.feature(compatible_profile_ids=(digest(77),))), immutable_resolver=lambda _: True)
        self.assertEqual("PFS2_PROFILE", caught.exception.code)
        with self.assertRaises(FeatureSchemaError) as caught:
            build_physical_features(observation(), self.schema(), immutable_resolver=lambda value: value != digest(50))
        self.assertEqual("PFS2_AUTHORITY", caught.exception.code)
        with self.assertRaises(FeatureSchemaError):
            self.feature(source_field="engineering_value.value", representation="normalized_span")
        unavailable = self.schema(self.feature(availability="unavailable", missingness_policy="explicit_unavailable"))
        row = build_physical_features(observation(), unavailable, immutable_resolver=lambda _: True)
        self.assertEqual("unavailable", row.values[0].availability)
        with self.assertRaises(FeatureSchemaError): row.tensor(frozen_preprocessor_id=digest(61), transform=lambda _: 0.0)

    def test_operating_context_has_frozen_authority_and_no_truth_role(self) -> None:
        feature = self.feature(name="speed_reference_pct", source_field="operating_context.speed_reference_pct", representation="operating_context", unit="percent", compatible_profile_ids=())
        schema = self.schema(feature)
        context = OperatingContextValue("speed_reference_pct", "25", "canonical_decimal", "percent", digest(70), (digest(71),))
        row = build_physical_features(observation(), schema, immutable_resolver=lambda _: True, operating_context={"speed_reference_pct": context})
        self.assertEqual("25", row.values[0].value)
        with self.assertRaises(FeatureSchemaError): self.feature(name="scenario_truth")
        with self.assertRaises(FeatureSchemaError):
            build_physical_features(observation(), schema, immutable_resolver=lambda value: value != digest(70), operating_context={"speed_reference_pct": context})

    def test_legacy_is_comparison_only(self) -> None:
        legacy = LegacyBaselineCatalogue("mixed_scale_autoencoder", "v1", digest(80))
        self.assertEqual("LEGACY_BASELINE", legacy.status)
        self.assertFalse(isinstance(legacy, type(self.schema())))


if __name__ == "__main__": unittest.main()
