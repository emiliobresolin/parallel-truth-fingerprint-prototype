# Physical Evidence Qualification v2

`PhysicalEvidenceQualificationResult.v1` is an offline, public, non-authorizing G2 report. It reconstructs only caller-supplied immutable public closure identities: the final run manifest and receipt, frozen specification/partition/boundary/gap and policy closure, and canonical `SignalObservation.v2` records. It never starts a run, repairs a record, accesses a repository, resolves restricted bytes, or publishes.

The gate retains the actual run status and every negative check. A missing final receipt is `incomplete`; an unresolved immutable closure, missing projection path, unknown modality, or missing/inapplicable tolerance is `blocked`; an invalid observation, failed public-boundary isolation, differing projection, or non-complete run is `not_qualified`. Only a complete run with every supplied check passing is `qualified` and therefore reports the narrow `PHYSICAL_EVIDENCE_QUALIFIED`/G2 condition.

Signal records are reparsed through the v2 canonical contract, then checked for exact experiment/run/stream and observation closure membership. No current is clipped, imputed, normalized, substituted, merged, or reordered. Batch/live feature parity compares supplied canonical outputs and exact ordered feature and input-closure identities; tolerance is an opaque, separately admitted immutable reference and is never invented here.

Public-boundary inspection uses the declared immutable semantic/provenance/audience map only. It rejects direct or declared transitive truth taint and does not inspect restricted bytes, locators, counts, or timing. This is not a claim to detect undeclared covert channels.

The result is not `DATASET_QUALIFIED`, G8/G9, a real-plant or synchronization claim, detector readiness, training/consensus permission, truth unlock/join, fusion, deployment, dashboard work, or scientific-publication authorization. Any durable manifest-last publication remains a separately authorized Story 9.6/9.7 concern.
