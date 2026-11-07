# V1 golden fixtures

Identity-addressed contract replay corpus.

- `fixtures/`: payload bytes and fixture manifests.
- `requirements/`: requirement definitions.
- `catalogs/`: catalog revisions and expected outcomes.

Preserve existing identities; add revisions as separate artifacts. These are
contract oracles, not acquisition data. Validate with
`scripts/validate_v1_golden_fixtures.py`.
