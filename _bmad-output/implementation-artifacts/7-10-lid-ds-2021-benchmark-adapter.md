# Story 7.10: LID-DS 2021 Benchmark Adapter

Status: review

## Story

As a researcher executing the second public benchmark of the offline track
(course-correction Decision D2 step 2), I want a LID-DS 2021 adapter that
loads the scenario-based syscall traces from a configurable local path,
builds fixed-length integer sequences using the same windowing rule as
the ADFA-LD adapter, and records the dataset provenance, so that Story
7.11 (first real LID-DS run) and Story 7.12 (LID-DS sweep) can use the
same harness without code changes.

## Scope Notes

- Implements `offline_training/benchmarks/lid_ds_2021.py` declared in
  `architecture-update-2026-05-21.md` §B.1 and listed in
  `epics-update-2026-05-21.md` Story 7.10.
- The adapter does NOT download LID-DS 2021. The user obtains it from the
  LID-DS GitHub repository (Database Systems group, Univ. Leipzig).
- Layout consumed by the adapter (per LID-DS 2021 convention):
  ```
  <root>/
    <scenario_a>/
      normal/<trace>.sc2
      attack/<trace>.sc2
    <scenario_b>/
      normal/<trace>.sc2
      attack/<trace>.sc2
    ...
  ```
- The .sc2 file format is one syscall integer per line (extra fields after
  the integer are tolerated and ignored).
- A small embedded fixture under
  `tests/lstm_service/offline_training/fixtures/lid_ds_2021_fixture/`
  exercises every code path without network access.

## Acceptance Criteria

1. A new module `offline_training/benchmarks/lid_ds_2021.py` exposes `LidDs2021Benchmark` registered under the name `"lid-ds-2021"`.
2. The adapter accepts a local root via `LidDs2021Benchmark(root_path=...)`. If `None`, reads `LID_DS_2021_PATH` from env. If neither set, `.load()` raises a clear `RuntimeError` with the obtain-and-unzip steps.
3. Each subdirectory under the root is a scenario; each scenario contains a `normal/` and an `attack/` subdir. Normal traces produce label `0`, attack traces produce a per-scenario label `1..N`. The full label space is `("Normal", <scenario_a_attack>, <scenario_b_attack>, ...)` in alphabetical scenario order.
4. Trace files are parsed line-by-line; each line yields the first integer token (the rest of the line is ignored). The same leading-window + zero-pad rule as ADFA-LD applies, with feature_count fixed to 1 and integer ids scaled by the dataset-wide max syscall id.
5. The returned `BenchmarkData.provenance` carries: `origin="LID-DS 2021"`, `year=2021`, `version` (root basename), `citation`, `feature_count=1`, `per_class_counts`, `max_syscall_id`, `scenarios` (alphabetical list).
6. A fixture under `tests/lstm_service/offline_training/fixtures/lid_ds_2021_fixture/` provides two scenarios with at least 2 normal + 1 attack trace each.
7. Unit tests cover: missing-path raises with actionable message, fixture loads with the expected label space and per-class counts, fixed-length window contract, scale-to-[0,1], provenance fields, registry retrieval via `load_benchmark("lid-ds-2021", ...)`.
8. Full regression remains green.

## Tasks / Subtasks

- [x] Build the fixture under `tests/lstm_service/offline_training/fixtures/lid_ds_2021_fixture/` with two scenarios (`cve_2017_7529`, `cve_2019_5736`). (AC: 6)
- [x] Implement `LidDs2021Benchmark` with leading-window + zero-pad + scale-to-[0,1]. (AC: 1, 2, 3, 4, 5)
- [x] Register the adapter under `"lid-ds-2021"` via side-effect import in `benchmarks/__init__.py`. (AC: 1)
- [x] Add unit tests (8) using the fixture. (AC: 7)
- [x] Run full suite; 196 tests pass. (AC: 8)
- [x] Update File List + Completion Notes.

### Debug Log References

- GREEN on first attempt. The adapter is a structural cousin of the ADFA-LD
  adapter, with two differences: scenarios are discovered dynamically from
  the directory layout, and the .sc2 line format tolerates "<id> <name>"
  rows by parsing the first whitespace-separated integer.

### Completion Notes List

- Scenario auto-discovery: each immediate subdirectory of the configured
  root that contains both `normal/` and `attack/` becomes a scenario.
  Scenarios are sorted alphabetically so the label space is deterministic.
- Label space = `("Normal", "<scenario_a>-attack", "<scenario_b>-attack", ...)`
  with integer ids `0`, `1`, `2`, ... in that order.
- Trace parser tolerates the two LID-DS line formats observed in the
  fixture and the wild: a bare integer per line, or `<integer> <name>`.
  Lines whose first token is not parseable as an integer are skipped.
- Full regression: 196 tests, OK (skipped=7).

### File List

- `_bmad-output/implementation-artifacts/7-10-lid-ds-2021-benchmark-adapter.md`
- `src/parallel_truth_fingerprint/lstm_service/offline_training/benchmarks/lid_ds_2021.py`
- `src/parallel_truth_fingerprint/lstm_service/offline_training/benchmarks/__init__.py`
- `tests/lstm_service/offline_training/test_lid_ds_2021.py`
- `tests/lstm_service/offline_training/fixtures/lid_ds_2021_fixture/cve_2017_7529/normal/trace-001.sc2`
- `tests/lstm_service/offline_training/fixtures/lid_ds_2021_fixture/cve_2017_7529/normal/trace-002.sc2`
- `tests/lstm_service/offline_training/fixtures/lid_ds_2021_fixture/cve_2017_7529/attack/trace-001.sc2`
- `tests/lstm_service/offline_training/fixtures/lid_ds_2021_fixture/cve_2017_7529/attack/trace-002.sc2`
- `tests/lstm_service/offline_training/fixtures/lid_ds_2021_fixture/cve_2019_5736/normal/trace-001.sc2`
- `tests/lstm_service/offline_training/fixtures/lid_ds_2021_fixture/cve_2019_5736/normal/trace-002.sc2`
- `tests/lstm_service/offline_training/fixtures/lid_ds_2021_fixture/cve_2019_5736/attack/trace-001.sc2`
- `tests/lstm_service/offline_training/fixtures/lid_ds_2021_fixture/cve_2019_5736/attack/trace-002.sc2`

## Dev Notes

- The LID-DS 2021 paper / framework: Grimmer et al., "LID-DS: A New Dataset
  for Linux Host-Based Intrusion Detection". Sources and dataset hosted at
  `github.com/LID-DS/LID-DS`.
- For Story 7.10 the windowing rule mirrors ADFA-LD (leading window,
  right-pad with zeros) so the cross-benchmark report (Story 7.13) does
  not have to normalize per-benchmark windowing.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 via BMAD dev-story workflow.

<!-- Dev Agent Record populated above. -->

