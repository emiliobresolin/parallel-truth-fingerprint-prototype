"""Scenario-control helpers for Epic 4 Story 4.5."""

from __future__ import annotations

from dataclasses import dataclass, replace


NORMAL_SCENARIO = "normal"
SUPPORTED_DEMO_SCENARIOS = (
    "normal",
    "scada_replay",
    "scada_freeze",
    "scada_divergence",
    "single_edge_exclusion",
    "quorum_loss",
)
SCENARIO_OUTPUTS_NORMAL = (
    "consensus_alert",
    "persistence_stage",
    "fingerprint_lifecycle",
)
SCENARIO_OUTPUTS_REPLAY = (
    "consensus_alert",
    "persistence_stage",
    "replay_behavior",
    "fingerprint_inference",
)
SCENARIO_OUTPUTS_SCADA_BLOCKING = (
    "scada_divergence_alert",
    "persistence_stage",
)
SCENARIO_OUTPUTS_EDGE = (
    "consensus_alert",
    "persistence_stage",
    "fingerprint_lifecycle",
)
SCENARIO_OUTPUTS_SCADA_DIVERGENCE = (
    "scada_divergence_alert",
    "persistence_stage",
)
SCENARIO_OUTPUTS_QUORUM = (
    "consensus_alert",
    "persistence_stage",
)


@dataclass(frozen=True)
class RuntimeScenarioControlStage:
    """One cycle of explicit runtime scenario-control state."""

    configured_scenario: str
    active_scenario: str
    start_cycle: int
    active: bool
    fault_mode: str
    scada_mode: str
    scenario_label: str
    training_label: str
    training_eligible: bool
    training_eligibility_reason: str
    expected_output_channels: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "configured_scenario": self.configured_scenario,
            "active_scenario": self.active_scenario,
            "start_cycle": self.start_cycle,
            "active": self.active,
            "fault_mode": self.fault_mode,
            "scada_mode": self.scada_mode,
            "scenario_label": self.scenario_label,
            "training_label": self.training_label,
            "training_eligible": self.training_eligible,
            "training_eligibility_reason": self.training_eligibility_reason,
            "expected_output_channels": list(self.expected_output_channels),
        }


def resolve_runtime_scenario_control_stage(
    *,
    config,
    cycle_index: int,
) -> RuntimeScenarioControlStage:
    """Resolve the explicit scenario-control state for one runtime cycle."""

    configured_scenario, start_cycle = _resolve_configured_scenario(config)
    start_cycle = max(start_cycle, 1)

    if configured_scenario == NORMAL_SCENARIO:
        return RuntimeScenarioControlStage(
            configured_scenario=NORMAL_SCENARIO,
            active_scenario=NORMAL_SCENARIO,
            start_cycle=start_cycle,
            active=True,
            fault_mode="none",
            scada_mode="match",
            scenario_label="normal",
            training_label="normal",
            training_eligible=True,
            training_eligibility_reason="normal_validated_run",
            expected_output_channels=SCENARIO_OUTPUTS_NORMAL,
        )

    if cycle_index < start_cycle:
        return RuntimeScenarioControlStage(
            configured_scenario=configured_scenario,
            active_scenario=NORMAL_SCENARIO,
            start_cycle=start_cycle,
            active=False,
            fault_mode="none",
            scada_mode="match",
            scenario_label="normal",
            training_label="normal",
            training_eligible=True,
            training_eligibility_reason="normal_validated_run",
            expected_output_channels=SCENARIO_OUTPUTS_NORMAL,
        )

    if configured_scenario == "scada_replay":
        return RuntimeScenarioControlStage(
            configured_scenario=configured_scenario,
            active_scenario=configured_scenario,
            start_cycle=start_cycle,
            active=True,
            fault_mode="none",
            scada_mode="replay",
            scenario_label="scada_replay",
            training_label="non_normal",
            training_eligible=False,
            training_eligibility_reason="scada_replay",
            expected_output_channels=SCENARIO_OUTPUTS_REPLAY,
        )

    if configured_scenario == "scada_freeze":
        return RuntimeScenarioControlStage(
            configured_scenario=configured_scenario,
            active_scenario=configured_scenario,
            start_cycle=start_cycle,
            active=True,
            fault_mode="none",
            scada_mode="freeze",
            scenario_label="scada_freeze",
            training_label="non_normal",
            training_eligible=False,
            training_eligibility_reason="scada_freeze",
            expected_output_channels=SCENARIO_OUTPUTS_SCADA_BLOCKING,
        )

    if configured_scenario == "scada_divergence":
        return RuntimeScenarioControlStage(
            configured_scenario=configured_scenario,
            active_scenario=configured_scenario,
            start_cycle=start_cycle,
            active=True,
            fault_mode="none",
            scada_mode="offset",
            scenario_label="scada_divergence",
            training_label="non_normal",
            training_eligible=False,
            training_eligibility_reason="scada_divergence",
            expected_output_channels=SCENARIO_OUTPUTS_SCADA_DIVERGENCE,
        )

    if configured_scenario == "single_edge_exclusion":
        return RuntimeScenarioControlStage(
            configured_scenario=configured_scenario,
            active_scenario=configured_scenario,
            start_cycle=start_cycle,
            active=True,
            fault_mode="single_edge_exclusion",
            scada_mode="match",
            scenario_label="faulty_edge_exclusion",
            training_label="non_normal",
            training_eligible=False,
            training_eligibility_reason="faulty_edge_exclusion",
            expected_output_channels=SCENARIO_OUTPUTS_EDGE,
        )

    if configured_scenario == "quorum_loss":
        return RuntimeScenarioControlStage(
            configured_scenario=configured_scenario,
            active_scenario=configured_scenario,
            start_cycle=start_cycle,
            active=True,
            fault_mode="quorum_loss",
            scada_mode="match",
            scenario_label="quorum_loss",
            training_label="non_normal",
            training_eligible=False,
            training_eligibility_reason="scenario:quorum_loss",
            expected_output_channels=SCENARIO_OUTPUTS_QUORUM,
        )

    raise ValueError(f"Unsupported demo scenario '{configured_scenario}'.")


def apply_runtime_scenario_control(*, config, scenario_stage: RuntimeScenarioControlStage):
    """Return one cycle-local runtime config with scenario overrides applied."""

    return replace(
        config,
        demo_fault_mode=scenario_stage.fault_mode,
        demo_scada_mode=scenario_stage.scada_mode,
        demo_scada_start_cycle=scenario_stage.start_cycle if scenario_stage.scada_mode != "match" else 0,
    )


def _resolve_configured_scenario(config) -> tuple[str, int]:
    explicit_scenario = getattr(config, "demo_scenario_name", "").strip()
    explicit_start_cycle = getattr(config, "demo_scenario_start_cycle", 1)
    if explicit_scenario:
        return explicit_scenario, explicit_start_cycle

    scada_mode = getattr(config, "demo_scada_mode", "match")
    fault_mode = getattr(config, "demo_fault_mode", "none")
    if scada_mode in {"replay", "freeze"} and fault_mode != "none":
        raise ValueError(
            "Scenario control supports only one non-normal runtime scenario at a time."
        )
    if scada_mode == "replay":
        return "scada_replay", getattr(config, "demo_scada_start_cycle", 1)
    if scada_mode == "freeze":
        return "scada_freeze", getattr(config, "demo_scada_start_cycle", 1)
    if scada_mode == "offset":
        return "scada_divergence", getattr(config, "demo_scada_start_cycle", 1)
    if fault_mode != "none":
        return fault_mode, 1
    return NORMAL_SCENARIO, 1
