from __future__ import annotations

import unittest
from dataclasses import replace

from parallel_truth_fingerprint.contracts.linux_edge_workload import (
    ExecutionPath, LinuxEdgeWorkload, NetworkInteraction, ProcessDeclaration,
    StorageInteraction, WorkloadActivity, WorkloadEvidenceRole,
    WorkloadExecutionRequest, WorkloadRuntimeIdentity, linux_edge_workload_content_id,
)
from parallel_truth_fingerprint.evidence.linux_edge_workload import (
    validate_linux_edge_workload, validate_workload_execution,
)


def digest(number: int) -> str:
    return "sha256:" + f"{number:064x}"


def workload(**changes: object) -> LinuxEdgeWorkload:
    value = LinuxEdgeWorkload(
        schema_version="LinuxEdgeWorkload.v1", workload_id="", image_or_executable_identity=digest(1), entrypoint_identity=digest(2),
        expected_process_tree=(ProcessDeclaration("edge-main", digest(3), None), ProcessDeclaration("serializer", digest(4), "edge-main")),
        edge_role="edge", experiment_role="prototype", permission_identities=(digest(5),),
        network_interactions=(NetworkInteraction("mqtt", digest(6), digest(7)),), storage_interactions=(StorageInteraction("evidence", digest(8), digest(9)),),
        configuration_identity=digest(10), code_identity=digest(11), dependency_identity=digest(12), mock_admission_identity=digest(13),
        allowed_activities=(WorkloadActivity.SAFE_ACQUISITION, WorkloadActivity.SERIALIZATION, WorkloadActivity.MQTT, WorkloadActivity.CONSENSUS_INTERACTION, WorkloadActivity.EVIDENCE_WRITE),
        evidence_role=WorkloadEvidenceRole.HOST_CAPTURE, test_only=False,
        excluded_process_roles=("mosquitto", "minio", "cometbft", "abci", "collector", "unrelated_container"), workload_content_id="",
    )
    value = replace(value, **changes)
    content_id = linux_edge_workload_content_id(value)
    return replace(value, workload_id=content_id, workload_content_id=content_id)


def runtime() -> WorkloadRuntimeIdentity:
    return WorkloadRuntimeIdentity(*(digest(n) for n in range(20, 25)), (digest(25),), *(digest(n) for n in range(26, 32)))


class LinuxEdgeWorkloadTests(unittest.TestCase):
    def test_valid_authentic_allowlisted_workload_is_admitted(self) -> None:
        item = workload()
        request = WorkloadExecutionRequest(item, ExecutionPath.AUTHENTIC, runtime(), (WorkloadActivity.MQTT,))
        result = validate_workload_execution(request, authentic_reproduction_available=lambda _: True, mock_admission_valid=lambda *_: False)
        self.assertTrue(result.allowed)

    def test_manifest_fails_closed_for_identity_activity_and_exclusion_breaks(self) -> None:
        item = workload(permission_identities=("latest",), allowed_activities=("attack_tooling",), excluded_process_roles=("mosquitto",))
        result = validate_linux_edge_workload(item)
        self.assertFalse(result.allowed)
        self.assertTrue({"LWE1_PERMISSION_IDENTITY_INVALID", "LWE1_ACTIVITY_ALLOWLIST_INVALID", "LWE1_INFRASTRUCTURE_EXCLUSION_MISSING"}.issubset({item.rule_id for item in result.violations}))

    def test_mock_is_rejected_when_authentic_path_is_available(self) -> None:
        request = WorkloadExecutionRequest(workload(), ExecutionPath.MOCK, runtime(), (WorkloadActivity.MQTT,))
        result = validate_workload_execution(request, authentic_reproduction_available=lambda _: True, mock_admission_valid=lambda *_: True)
        self.assertIn("LWE1_MOCK_REJECTED_AUTHENTIC_AVAILABLE", {item.rule_id for item in result.violations})

    def test_mock_requires_exact_admission_when_authentic_unavailable(self) -> None:
        request = WorkloadExecutionRequest(workload(mock_admission_identity=None), ExecutionPath.MOCK, runtime(), (WorkloadActivity.MQTT,))
        result = validate_workload_execution(request, authentic_reproduction_available=lambda _: False, mock_admission_valid=lambda *_: True)
        self.assertIn("LWE1_MOCK_ADMISSION_REJECTED", {item.rule_id for item in result.violations})

    def test_fixture_replay_is_test_only_and_requested_actions_cannot_expand_scope(self) -> None:
        fixture = workload(evidence_role=WorkloadEvidenceRole.FIXTURE_REPLAY, test_only=False)
        self.assertIn("LWE1_FIXTURE_REPLAY_NOT_TEST_ONLY", {item.rule_id for item in validate_linux_edge_workload(fixture).violations})
        request = WorkloadExecutionRequest(workload(), ExecutionPath.AUTHENTIC, runtime(), ("control_action",))
        result = validate_workload_execution(request, authentic_reproduction_available=lambda _: True, mock_admission_valid=lambda *_: False)
        self.assertIn("LWE1_ACTIVITY_NOT_ALLOWLISTED", {item.rule_id for item in result.violations})

    def test_runtime_identity_must_be_complete_and_immutable(self) -> None:
        broken = replace(runtime(), kernel_identity="linux-latest")
        result = validate_workload_execution(WorkloadExecutionRequest(workload(), ExecutionPath.AUTHENTIC, broken, (WorkloadActivity.MQTT,)), authentic_reproduction_available=lambda _: True, mock_admission_valid=lambda *_: False)
        self.assertIn("LWE1_RUNTIME_IDENTITY_UNRESOLVED", {item.rule_id for item in result.violations})


if __name__ == "__main__":
    unittest.main()
