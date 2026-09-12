from __future__ import annotations

import unittest
from dataclasses import replace

from decimal import Decimal

from parallel_truth_fingerprint.contracts.instrument_profile import (
    InstrumentProfile, TransformBinding, parse_instrument_profile,
)
from parallel_truth_fingerprint.evidence.instrument_profiles import (
    admit_instrument_profile, check_command_conformance, convert_admitted_profile,
    evaluate_measurement_quality,
)


class InstrumentProfileTests(unittest.TestCase):
    def profile(self, *, role: str = "measurement_transmitter") -> InstrumentProfile:
        profile = InstrumentProfile(
            "InstrumentProfile.v1", "instrument-profile-sentinel", role, "sentinel", "model",
            (), "temperature", "degC", ("sha256:" + "a" * 64,), ("source:sentinel",),
            "sha256:" + "b" * 64, "sha256:" + "c" * 64,
            tuple(TransformBinding(direction, "sha256:" + marker * 64, (), ()) for direction, marker in (
                ("current_to_normalized", "d"), ("current_to_engineering_or_reference", "e"),
                ("engineering_or_reference_to_current", "f"))), (),
            (("configuration_mode", "current"), ("quantity_kind", "temperature"), ("unit", "degC")), (), None, "", "none",
        )
        return replace(profile, content_sha256=profile.computed_content_sha256())

    def test_blocked_profile_cannot_be_admitted_with_unresolved_source(self) -> None:
        profile = self.profile()
        result = admit_instrument_profile(profile, registry_snapshot_id="sha256:" + "0" * 64, source_use_resolves=lambda _: False,
                                          parameter_gate_accountable=lambda *_: True)
        self.assertFalse(result.admitted)
        self.assertIsNone(result.handle)
        self.assertEqual("IPV1_SOURCE_USE_LOCATOR", result.violations[0].rule_id)

    def test_admitted_handle_is_required_for_exact_conversion(self) -> None:
        profile = self.profile()
        admission = admit_instrument_profile(profile, registry_snapshot_id="sha256:" + "0" * 64,
                                             source_use_resolves=lambda _: True, parameter_gate_accountable=lambda *_: True)
        self.assertTrue(admission.admitted)
        transforms = {
            "current_to_normalized": lambda value: value / Decimal("20"),
            "current_to_engineering_or_reference": lambda value: value * Decimal("2"),
            "engineering_or_reference_to_current": lambda value: value / Decimal("2"),
        }
        result = convert_admitted_profile(admission.handle, profile, "current_to_engineering_or_reference", Decimal("8"), transforms=transforms)
        self.assertEqual(Decimal("16"), result.value)
        forged = replace(admission.handle, profile_content_sha256="sha256:" + "9" * 64)
        self.assertEqual("IPV1_CONTENT_HASH", convert_admitted_profile(forged, profile, "current_to_normalized", Decimal("8"), transforms=transforms).violations[0].rule_id)

    def test_quality_is_exclusive_and_precedes_conversion(self) -> None:
        profile = self.profile()
        handle = admit_instrument_profile(profile, registry_snapshot_id="sha256:" + "0" * 64, source_use_resolves=lambda _: True, parameter_gate_accountable=lambda *_: True).handle
        missing = evaluate_measurement_quality(handle, profile, None, (), ordered_rules=(("raw-missing", "missing", lambda value, _: value is None),))
        self.assertEqual(("missing", "no_numeric_value"), (missing.quality, missing.conversion_disposition))
        overlap = evaluate_measurement_quality(handle, profile, Decimal("4"), (), ordered_rules=(("a", "in_range", lambda *_: True), ("b", "fault", lambda *_: True)))
        self.assertEqual(("uncertain", "IPV1_QUALITY_COVERAGE"), (overlap.quality, overlap.applied_rule_ids[0]))

    def test_command_conformance_never_returns_measurement_quality(self) -> None:
        profile = self.profile(role="command_input")
        handle = admit_instrument_profile(profile, registry_snapshot_id="sha256:" + "0" * 64, source_use_resolves=lambda _: True, parameter_gate_accountable=lambda *_: True).handle
        good = check_command_conformance(handle, profile, configuration_mode="current", requested_quantity="temperature", requested_unit="degC", requested_direction="engineering_or_reference_to_current")
        self.assertEqual(("conformant", "convert"), (good.status, good.conversion_disposition))
        self.assertEqual("blocked", check_command_conformance(handle, profile, configuration_mode="voltage", requested_quantity="temperature", requested_unit="degC", requested_direction="engineering_or_reference_to_current").status)

    def test_strict_parser_rejects_extra_field(self) -> None:
        payload = self.profile().to_dict()
        payload["unexpected"] = "x"
        with self.assertRaisesRegex(ValueError, "IPV1_SCHEMA_VERSION_TOKEN"):
            parse_instrument_profile(payload)


if __name__ == "__main__":
    unittest.main()
