# ExperimentSpec.v1

`ExperimentSpec.v1` is an immutable, offline planning record. It declares
pre-existing identities and projects planned matrix rows; it never schedules,
commands, persists, captures, unlocks truth, or authorizes an activity.

```text
immutable references -> ExperimentSpec validation -> structural freeze
                                       -> deterministic planned matrix
                                       -> later independent authorization/execution
```

Every reference is a SHA-256 identity. Required slots are explicitly `bound`,
`not_applicable`, or `unavailable_blocking`; the last state prevents execution
eligibility while retaining an inspectable structural freeze. Validation and all
matrix rows report `authorization_effect: none`.

The sole reference factor is `speed_reference_pct`: its frozen decision and
25/75 parameter revisions bind a specific 0--100 / 4--20 mA command profile
and its 8/16 mA derived parameter revisions. It is not electrical power, a
manufacturer recommendation, a universal compressor range, safety limit, or
efficiency limit. `capacity_reference_pct` is intentionally absent and must
remain blocked until separately evidenced.

Scenario, intervention, recovery, and truth policy references are opaque.
Rows retain the predeclared binding, phase, opaque identities, planned
disposition, and allowed-outcome policy only. Story 10.5 owns truth; Story
10.6 owns execution and actual outcomes. Current project-domain candidates
remain blocked where their immutable prerequisites are unavailable.
