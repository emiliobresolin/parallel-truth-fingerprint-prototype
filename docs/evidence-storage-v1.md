# Evidence storage v1

Story 9.7 owns only the formal MinIO adapter and a narrow, single-node local qualification. Story 9.6 owns manifest structure and manifest-last publication; Story 9.8 owns partitions, freeze, truth unlock and activity authorization. Later stories own scientific execution/results; Epic 18 is optional presentation.

The formal adapter derives all keys itself: `formal/v1/<detector-facing|evaluator-restricted|public-reference>/<artifact|manifest|receipt|snapshot>/sha256-<lowercase digest>`. It never accepts a caller prefix, `latest`, a filesystem path, traversal or cross-role lookup. Prefix separation is structural classification, not IAM, encryption or authorization.

`python scripts/qualify_evidence_storage.py` is read-only preflight. A live sequence must additionally pass `--authorize-live`, an isolated Compose project and the dedicated bucket. It refuses to start a service, delete a bucket/volume, or run `down -v`; credentials are injected only by the operator and are never recorded. `compose.evidence.yml` requires an operator-provided immutable MinIO image digest and persists `/data` in a dedicated named volume.

The report binds image and Compose digests, endpoint identity without credentials, bucket, volume, namespace policy, runtime/dependency identities, versioning/object-lock observations, conditional-create probe, restart/recreation and closed-set restoration. Requalify after any identity drift. Boto3's public `put_object(IfNoneMatch="*")` path is used; MinIO compatibility remains blocked until the exact pinned pair has a live capability report.

Qualification proves only observed conditional create/read-back, scoped volume restart/recreation, and small exact-object restore at the recorded time. It does not prove WORM, privileged-admin protection, host/power-loss durability, media recovery, bit-rot detection, replication, HA, TLS, backup/DR, other backends, producer honesty, scientific validity, source authority, or any activity authorization.
