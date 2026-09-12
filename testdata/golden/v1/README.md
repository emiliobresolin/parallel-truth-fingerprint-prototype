# V1 golden fixture corpus

This append-only corpus preserves reviewed contract-replay oracles. It is not a dataset,
measurement, model result, or scientific-validity claim. `authorization_effect` is always `none`.
The current catalog is honestly blocked because no published Story 9.1 baseline manifest is present.
The implemented Story 9.5 catalog identity is `sha256:9e954bd3291f34079e3b8a370d0f9496417a01b834b83333d8c8d1d5cf34d144`; older identity-addressed revisions remain append-only.

| Requirement | Group | Reader | Origin | Legacy outcome | Gate outcome | Comparison |
|---|---|---|---|---|---|---|
| `consensus.committed.exclusion` | `core` | `go.consensus.v1` | `non_domain_sentinel` | `accepted` | `unverifiable` | `semantic_exact` |
| `consensus.committed.failed` | `core` | `go.consensus.v1` | `non_domain_sentinel` | `accepted` | `unverifiable` | `semantic_exact` |
| `consensus.committed.success` | `core` | `go.consensus.v1` | `non_domain_sentinel` | `accepted` | `unverifiable` | `semantic_exact` |
| `consensus.divergence` | `core` | `go.consensus.v1` | `non_domain_sentinel` | `accepted` | `unverifiable` | `semantic_exact` |
| `consensus.go.transaction` | `core` | `go.consensus.v1` | `non_domain_sentinel` | `accepted` | `unverifiable` | `semantic_exact` |
| `consensus.ordering` | `core` | `python.consensus.v1` | `non_domain_sentinel` | `accepted` | `unverifiable` | `semantic_exact` |
| `consensus.python.transaction` | `core` | `python.consensus.v1` | `non_domain_sentinel` | `accepted` | `unverifiable` | `semantic_exact` |
| `consensus.query.found` | `core` | `go.consensus.v1` | `non_domain_sentinel` | `accepted` | `unverifiable` | `semantic_exact` |
| `consensus.query.missing` | `core` | `go.consensus.v1` | `non_domain_sentinel` | `rejected` | `rejected` | `semantic_exact` |
| `dashboard.read_model` | `optional_dashboard` | `python.json.v1` | `non_domain_sentinel` | `accepted` | `unverifiable` | `semantic_exact` |
| `detector.input.extra` | `core` | `detector.schema.v1` | `non_domain_sentinel` | `rejected` | `rejected` | `semantic_exact` |
| `detector.input.missing` | `core` | `detector.schema.v1` | `non_domain_sentinel` | `rejected` | `rejected` | `semantic_exact` |
| `detector.input.permuted` | `core` | `detector.schema.v1` | `non_domain_sentinel` | `rejected` | `rejected` | `semantic_exact` |
| `detector.input.schema` | `core` | `detector.schema.v1` | `non_domain_sentinel` | `accepted` | `unverifiable` | `semantic_exact` |
| `detector.input.v2_only` | `core` | `detector.schema.v1` | `non_domain_sentinel` | `rejected` | `rejected` | `semantic_exact` |
| `detector.output.recorded` | `core` | `python.json.v1` | `non_domain_sentinel` | `accepted` | `unverifiable` | `semantic_exact` |
| `detector.value.nonfinite` | `core` | `detector.schema.v1` | `non_domain_sentinel` | `accepted` | `rejected` | `semantic_exact` |
| `manifest.artifact` | `core` | `manifest.json.v1` | `non_domain_sentinel` | `accepted` | `unverifiable` | `semantic_exact` |
| `manifest.dataset` | `core` | `manifest.json.v1` | `non_domain_sentinel` | `accepted` | `unverifiable` | `semantic_exact` |
| `manifest.schema_mismatch` | `core` | `manifest.json.v1` | `non_domain_sentinel` | `accepted` | `rejected` | `semantic_exact` |
| `mqtt.payload.basic` | `core` | `python.json.v1` | `non_domain_sentinel` | `accepted` | `unverifiable` | `semantic_exact` |
| `mqtt.payload.duplicate_key` | `core` | `python.json.v1` | `non_domain_sentinel` | `accepted` | `rejected` | `semantic_exact` |
| `mqtt.payload.malformed` | `core` | `python.json.v1` | `non_domain_sentinel` | `rejected` | `rejected` | `semantic_exact` |
| `mqtt.payload.non_utf8` | `core` | `python.json.v1` | `non_domain_sentinel` | `rejected` | `rejected` | `semantic_exact` |
| `mqtt.payload.optional_sv` | `core` | `mqtt.raw-hart.v1` | `non_domain_sentinel` | `accepted` | `unverifiable` | `semantic_exact` |
| `mqtt.payload.truncated` | `core` | `python.json.v1` | `non_domain_sentinel` | `rejected` | `rejected` | `semantic_exact` |
| `mqtt.topic` | `core` | `opaque.bytes.v1` | `non_domain_sentinel` | `accepted` | `unverifiable` | `byte_exact` |
| `mqtt.version.missing` | `core` | `python.json.v1` | `non_domain_sentinel` | `accepted` | `unverifiable` | `semantic_exact` |
| `mqtt.version.unknown` | `core` | `python.json.v1` | `non_domain_sentinel` | `accepted` | `rejected` | `semantic_exact` |
| `persistence.object.content` | `core` | `persistence.json.v1` | `non_domain_sentinel` | `accepted` | `unverifiable` | `semantic_exact` |
| `persistence.object.corrupt` | `core` | `persistence.json.v1` | `non_domain_sentinel` | `rejected` | `rejected` | `semantic_exact` |
| `persistence.object.key` | `core` | `opaque.bytes.v1` | `non_domain_sentinel` | `accepted` | `unverifiable` | `byte_exact` |
| `persistence.object.missing` | `core` | `persistence.json.v1` | `non_domain_sentinel` | `not_invoked` | `rejected` | `semantic_exact` |
