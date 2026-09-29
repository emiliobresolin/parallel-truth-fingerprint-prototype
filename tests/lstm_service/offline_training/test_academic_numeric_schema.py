"""Regression tests for the closed thesis-evaluation-v2 numeric schema."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from parallel_truth_fingerprint.lstm_service.offline_training.academic_numeric_schema import (
    V2_NUMERIC_RULES,
    V2_NUMERIC_SCHEMA_IDENTITY,
    V2_NUMERIC_SCHEMA_VERSION,
    v2_numeric_consumers,
    validate_v2_numeric_schema,
)
from parallel_truth_fingerprint.lstm_service.offline_training.academic_runner import (
    load_academic_config,
)
from scripts.build_academic_parameter_requirements import build


ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "configs" / "experiments" / "thesis-evaluation-v2.json"
REQUIREMENTS_PATH = (
    ROOT
    / "configs"
    / "experiments"
    / "thesis-evaluation-v2.parameter-requirements-v2.1.json"
)


def _raw_config() -> dict[str, object]:
    value = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


class AcademicNumericSchemaTests(unittest.TestCase):
    def test_committed_config_implements_the_explicit_205_slot_schema(self) -> None:
        config = load_academic_config(CONFIG_PATH)
        consumers = v2_numeric_consumers(config)

        self.assertEqual(len(V2_NUMERIC_RULES), 205)
        self.assertEqual(len(consumers), 205)
        self.assertEqual(len({pointer for pointer, _, _ in consumers}), 205)
        self.assertEqual(
            config["numeric_authority"]["numeric_schema_version"],  # type: ignore[index]
            V2_NUMERIC_SCHEMA_VERSION,
        )
        self.assertEqual(
            config["numeric_authority"]["numeric_schema_identity"],  # type: ignore[index]
            V2_NUMERIC_SCHEMA_IDENTITY,
        )

    def test_missing_default_boolean_string_and_unknown_number_fail_closed(self) -> None:
        cases: list[tuple[str, dict[str, object], str]] = []

        missing = deepcopy(_raw_config())
        del missing["datasets"]["lid-ds-2021"]["numeric_clip"]  # type: ignore[index]
        cases.append(("missing", missing, "missing numeric consumer"))

        boolean = deepcopy(_raw_config())
        boolean["statistical_protocol"]["bootstrap_replicates"] = True  # type: ignore[index]
        cases.append(("boolean", boolean, "Boolean/string coercion forbidden"))

        numeric_string = deepcopy(_raw_config())
        numeric_string["statistical_protocol"]["confidence_level"] = "0.95"  # type: ignore[index]
        cases.append(("numeric string", numeric_string, "numeric string is forbidden"))

        unknown = deepcopy(_raw_config())
        unknown["statistical_protocol"]["undeclared_default"] = 7  # type: ignore[index]
        cases.append(("unknown", unknown, "unknown numeric consumer"))

        for label, config, message in cases:
            with self.subTest(label=label), self.assertRaisesRegex(ValueError, message):
                validate_v2_numeric_schema(config)

    def test_inventory_is_bound_to_schema_and_contains_no_implicit_default(self) -> None:
        config = load_academic_config(CONFIG_PATH)
        generated = build(config)
        committed = json.loads(REQUIREMENTS_PATH.read_text(encoding="utf-8"))

        self.assertEqual(generated, committed)
        self.assertEqual(generated["numeric_consumer_count"], 205)
        self.assertEqual(
            generated["numeric_schema_identity"], V2_NUMERIC_SCHEMA_IDENTITY
        )
        locators = {slot["consumer_locator"] for slot in generated["slots"]}
        self.assertIn("/datasets/lid-ds-2021/numeric_clip", locators)
        self.assertIn(
            "/statistical_protocol/minimum_valid_bootstrap_fraction", locators
        )

    def test_number_consumers_never_round_through_binary_float(self) -> None:
        config = deepcopy(_raw_config())
        exact_integer = 9_007_199_254_740_993
        config["computational_budget"]["safety_factor"] = exact_integer  # type: ignore[index]

        consumers = {
            pointer: value for pointer, value, _ in v2_numeric_consumers(config)
        }

        self.assertEqual(
            consumers["/computational_budget/safety_factor"], str(exact_integer)
        )
        config["computational_budget"]["safety_factor"] = -0.0  # type: ignore[index]
        with self.assertRaisesRegex(ValueError, "finite JSON number"):
            validate_v2_numeric_schema(config)


if __name__ == "__main__":
    unittest.main()
