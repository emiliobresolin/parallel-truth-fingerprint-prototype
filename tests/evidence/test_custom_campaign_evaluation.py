from __future__ import annotations

import json
from pathlib import Path
import tempfile

from parallel_truth_fingerprint.evidence.custom_campaign_evaluation import (
    build_custom_campaign_evaluation,
)


def _row(*, campaign: str, round_id: str, label: str, classification: str) -> dict[str, object]:
    return {
        "campaign_id": campaign,
        "round_id": round_id,
        "scenario_label": label,
        "autoencoder_results": [{"round_ids": [round_id], "classification": classification}],
    }


def test_builds_source_separated_custom_record() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        normal = root / "normal.jsonl"
        fault = root / "fault.jsonl"
        normal.write_text(json.dumps(_row(campaign="normal", round_id="r1", label="normal", classification="normal")) + "\n", encoding="utf-8")
        fault.write_text(json.dumps(_row(campaign="fault", round_id="r2", label="faulty_edge_exclusion", classification="anomalous")) + "\n", encoding="utf-8")
        record = build_custom_campaign_evaluation((normal, fault))
    assert record.dataset_name == "custom-current-syscall"
    assert record.label_names == ("Normal", "NonNormalScenario")
    assert record.metrics["accuracy"] == 1.0
    assert record.dataset_provenance["row_count"] == 2
