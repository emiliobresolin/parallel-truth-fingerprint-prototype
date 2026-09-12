from __future__ import annotations

import hashlib
import unittest

from parallel_truth_fingerprint.consensus_v2.versioned_state import (
    V1_CONSENSUS_SCHEMA, V2_CONSENSUS_SCHEMA, ConsensusRoundEvidence, RestartQualification,
    RollbackEvidence, V2ToV1Projection, VersionedConsensusState, VersionedConsensusStateError,
    VersionedQuery, qualify_restart, resolve_versioned_query, versioned_state_id,
)


def ident(number: int) -> str:
    return "sha256:" + f"{number:064x}"


def state(version: str = "v2", key: str | None = None, body: bytes = b'{"opaque":"record"}') -> VersionedConsensusState:
    digest = "sha256:" + hashlib.sha256(body).hexdigest()
    key = key or f"consensus/{version}/round/{ident(1)}"
    schema = V2_CONSENSUS_SCHEMA if version == "v2" else V1_CONSENSUS_SCHEMA
    return VersionedConsensusState(version, schema, key, 7, ident(2), body, digest, versioned_state_id(version, schema, key, 7, ident(2), digest))


class VersionedStateTests(unittest.TestCase):
    def test_versions_have_non_conflicting_routes_and_exact_query_schema(self):
        one, two = state("v1"), state("v2")
        result = resolve_versioned_query(VersionedQuery("v2", V2_CONSENSUS_SCHEMA, two.storage_key), (one, two))
        self.assertEqual(result.state, two)
        self.assertEqual(result.schema_identity, V2_CONSENSUS_SCHEMA)
        self.assertEqual(resolve_versioned_query(VersionedQuery("v1", V1_CONSENSUS_SCHEMA, "consensus/v1/missing"), (one, two)).status, "missing")

    def test_unknown_version_and_cross_version_schema_fail_closed(self):
        with self.assertRaisesRegex(VersionedConsensusStateError, "VCQ_UNKNOWN_VERSION"):
            VersionedQuery("latest", V2_CONSENSUS_SCHEMA, "consensus/latest/a")
        with self.assertRaisesRegex(VersionedConsensusStateError, "VCS_SCHEMA_VERSION_MISMATCH"):
            VersionedConsensusState("v2", V1_CONSENSUS_SCHEMA, "consensus/v2/a", 0, ident(1), b"x", "sha256:" + hashlib.sha256(b"x").hexdigest(), ident(2))

    def test_projection_is_one_way_versioned_and_source_bound(self):
        source = state()
        fields = {"decision_id": ident(4)}
        payload = {"projection_schema": "ConsensusV2ToV1Projection.v1", "source_v2_state_id": source.state_id, "target_v1_schema_identity": V1_CONSENSUS_SCHEMA, "projected_fields": fields}
        projection_id = "sha256:" + hashlib.sha256(__import__("json").dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        projected = V2ToV1Projection(**payload, projection_id=projection_id)
        self.assertEqual(projected.source_v2_state_id, source.state_id)
        with self.assertRaisesRegex(VersionedConsensusStateError, "VCP_FIELDS"):
            V2ToV1Projection("ConsensusV2ToV1Projection.v1", source.state_id, V1_CONSENSUS_SCHEMA, {}, projection_id)

    def test_restart_requires_pinned_identities_and_exact_reconstruction(self):
        item = state()
        self.assertIsInstance(qualify_restart(ident(6), ident(7), (item,), (item,)), RestartQualification)
        with self.assertRaisesRegex(VersionedConsensusStateError, "VCR_REPLAY_MISMATCH"):
            qualify_restart(ident(6), ident(7), (item,), ())
        with self.assertRaisesRegex(VersionedConsensusStateError, "VCR_CODE_IDENTITY"):
            qualify_restart("main", ident(7), (), ())

    def test_reconstruction_and_rollback_only_accept_immutable_evidence(self):
        values = tuple(ident(i) for i in range(10, 19))
        evidence = ConsensusRoundEvidence(values[0], (values[1],), (values[1],), (), *values[2:])
        self.assertEqual(evidence.runtime_identity, values[5])
        data = {"authorization_id": ident(30), "from_version": "v2", "to_version": "v1", "prior_verified_state_id": state().state_id}
        rollback_id = "sha256:" + hashlib.sha256(__import__("json").dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self.assertEqual(RollbackEvidence(**data, rollback_id=rollback_id).to_version, "v1")
        with self.assertRaisesRegex(VersionedConsensusStateError, "VCRB_VERSION"):
            RollbackEvidence(data["authorization_id"], "v2", "v2", data["prior_verified_state_id"], rollback_id)
