# Evidence manifests v1

Story 9.6 defines data-only immutable manifest contracts. Their canonical contract set is
[`manifest-contract-set.v1.json`](evidence/manifests/v1/contracts/sha256-f0ecdc06e4012001e95a71732cafe60f513b614c7f7573f48a7db63d1cf906a3/manifest-contract-set.v1.json),
identified by `sha256:f0ecdc06e4012001e95a71732cafe60f513b614c7f7573f48a7db63d1cf906a3`.

All canonical records are UTF-8, compact sorted JSON with one LF. A record revision hashes
that representation after replacing only its self-ID with an empty string. Content SHA-256,
schema identity, serialized bytes hash, logical ID, and revision identity are distinct.

## Canonical identities and locators

All digests use lowercase `sha256:<64 hexadecimal characters>`. The identity preimage contains
every serialized field except the record's derived self-ID; a reference instead binds the target
revision ID and serialized-byte SHA-256. Creation timestamps are caller-supplied frozen values in
`YYYY-MM-DDTHH:MM:SS.ffffffZ` form. Serializers and validators never read a clock, working
directory, locale, environment, or filesystem metadata.

Formal locators are typed `repo:`, `object:`, or `oci:sha256:` identities. They reject aliases,
branches, tags, absolute/drive/UNC paths, dot or traversal segments, empty segments, control
characters, query/userinfo values, and mutable OCI tags. A locator is resolved only through an
injected qualified resolver; an opaque object key is never interpreted as a filesystem path.

Diagnostics have sorted rule IDs and field paths. Secret-bearing values are redacted; non-secret
facts use their SHA-256 representation, giving deterministic bounded diagnostics without a hidden
numeric truncation parameter.

Formal roots use typed immutable references and typed provenance edges. Detector-facing roots
must not traverse `truth.*` contracts. `latest`, branches, tags, traversal paths, query strings,
and unqualified locators are not formal identities. Alias resolution is a separate immutable
audit record tied to one injected resolver snapshot.

Run, bundle, and evaluation profiles are separate immutable references. An injected, registered
profile controls required binding slots, permitted not-applicable slots, and metric definitions;
caller-provided profile data never approves itself. Bundle modalities are only `physical` and
`syscall`; fusion is a same-run result kind for eligible PTFP-Custom-v1 support, never a third
detector or a cross-dataset result.

Artifact validation checks opaque content size and SHA-256, complete producer lineage, typed
provenance, registered source-use IDs, and closed audience access. With an injected dependency
resolver it validates the transitive closure, including cycles, divergent duplicate revision IDs,
missing targets, fixture/legacy promotion, and detector-facing truth taint.

Publication is manifest-last: write immutable subject bytes, read them back, write/read-back the
manifest, then conditionally create the immutable receipt. The receipt is the only completion
signal. This protocol proves client ordering only; Story 9.7 owns persistent-store qualification.
Before the receipt is created, the subject, manifest, and declared referenced closure are reread
from the same pinned snapshot. Orphaned immutable objects are inspectable but incomplete.

## Ownership boundary

| Owner | Responsibility |
| --- | --- |
| Story 9.6 | Generic contracts, pure graph validation, alias pre-resolution, and client-side publication ordering. |
| Story 9.7 | Qualification of a real persistent evidence store; this contract makes no durability or backend-atomicity claim. |
| Story 9.8 | Partition, freeze, truth-unlock, and activity-authorization records. |
| Later owning stories | Dataset/track requirement profiles, executable bundles, scores, metrics, and executed results. |
| Story 17B | Final claim-to-evidence packaging. |
| Epic 18 | Optional read-only presentation of published evidence. |

An identity, validation result, resolution record, or publication receipt always has
`authorization_effect: none`. It neither starts nor authorizes scientific, external, capture,
training, evaluation, deployment, or claim-publication activity.

These contracts do not train, infer, evaluate, publish claims, or grant authorization.
