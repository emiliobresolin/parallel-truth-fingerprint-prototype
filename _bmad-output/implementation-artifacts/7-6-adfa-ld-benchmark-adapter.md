# Story 7.6: ADFA-LD Benchmark Adapter

Status: review

## Story

As a researcher executing the first real benchmark of the offline training
track (advisor action M2), I want an ADFA-LD adapter that loads the syscall
traces from a configurable local path, builds fixed-length integer sequences
ready for the supervised LSTM classifier, and records the dataset
provenance, so that Story 7.7 can run the first real training cycle on a
public, peer-reviewed benchmark.

## Scope Notes

- Implements `offline_training/benchmarks/adfa_ld.py` declared in
  `architecture-update-2026-05-21.md` §B.1 and listed in
  `epics-update-2026-05-21.md` Story 7.6.
- The adapter does NOT download ADFA-LD; the user must obtain it once
  from the official UNSW Canberra Cyber page. The adapter accepts a local
  path via env var `ADFA_LD_PATH` (or constructor argument).
- A small embedded fixture under `tests/.../fixtures/adfa_ld_fixture/`
  exercises every code path in the unit tests, so CI does not depend on
  the real download.
- Label space: 6 classes — `Normal`, `Adduser`, `Hydra-FTP`, `Hydra-SSH`,
  `Java-Meterpreter`, `Web-Shell`.

## Acceptance Criteria

1. A new module `offline_training/benchmarks/adfa_ld.py` exposes `AdfaLdBenchmark` registered under the name `"adfa-ld"`.
2. The adapter accepts a local dataset root via `AdfaLdBenchmark(root_path=...)`. If the constructor receives `None`, it reads `ADFA_LD_PATH` from the environment. If neither is set, calling `.load()` raises a clear `RuntimeError` instructing the user where to obtain the dataset.
3. Trace files contain whitespace-separated syscall integers. The adapter parses each file into a list of ints; then builds fixed-length windows of length `sequence_length` by sliding over the trace (one window per trace if shorter than `sequence_length` is padded with zeros at the right; one window per trace if longer, taking the first `sequence_length` syscalls — keeps Story 7.6 minimal and deterministic; sliding-window variants stay for Story 7.9 sweep config).
4. The integer syscall ids are scaled to floats by `id / max_syscall_id_seen_in_dataset` so the LSTM input feature is in `[0, 1]`. `feature_count` is fixed to 1 (each timestep is one syscall).
5. The returned `BenchmarkData` exposes label names in the canonical order `(Normal, Adduser, Hydra-FTP, Hydra-SSH, Java-Meterpreter, Web-Shell)`, with integer labels in that same order. `provenance` carries: `origin="ADFA-LD"`, `year=2013`, `version` (path basename), `citation`, `per_class_counts`, `max_syscall_id`.
6. A fixture under `tests/lstm_service/offline_training/fixtures/adfa_ld_fixture/` mirrors the real layout (`Training_Data_Master/`, `Validation_Data_Master/`, `Attack_Data_Master/<AttackName>/`) with at least 2 normal traces and 1 attack trace per attack subdirectory.
7. Unit tests cover: missing path raises with a clear message, fixture loads with all 6 classes present, per-class label counts, deterministic ordering, fixed-length window contract, scale-to-[0,1] guarantee, registry-level retrieval via `load_benchmark("adfa-ld", ...)`.
8. Full regression remains green.

## Tasks / Subtasks

- [x] Build the fixture under `tests/lstm_service/offline_training/fixtures/adfa_ld_fixture/` (4 normal + 10 attack traces across 5 attack classes). (AC: 6)
- [x] Implement `AdfaLdBenchmark` with leading-window + zero-pad + scale-to-[0,1]. (AC: 1, 2, 3, 4, 5)
- [x] Register the adapter under `"adfa-ld"` via side-effect import in `benchmarks/__init__.py`. (AC: 1)
- [x] Add unit tests using the fixture (10 tests). (AC: 7)
- [x] Run full suite; 178 tests pass. (AC: 8)
- [x] Update File List + Completion Notes.

## Dev Notes

- ADFA-LD reference: G. Creech, J. Hu. *Generation of a New IDS Test Dataset:
  Time to Retire the KDD Collection*. WCNC 2013. Dataset at UNSW Canberra
  Cyber. The official archive name is `ADFA-LD.zip` and unzips into
  three subdirectories `Training_Data_Master/`,
  `Validation_Data_Master/`, `Attack_Data_Master/`.
- Each attack subdirectory under `Attack_Data_Master/` is named after one
  of the six attack categories; the canonical 5 attack classes plus
  Normal give the 6-class label space.
- For Story 7.6 keep the windowing rule simple (first `sequence_length`
  syscalls per trace, right-pad shorter traces with 0). Story 7.9 sweep
  can introduce richer windowing if needed.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 via BMAD dev-story workflow.

### Debug Log References

- GREEN passed on first attempt once the side-effect import was added in
  `benchmarks/__init__.py`; no debugging cycles were required.

### Completion Notes List

- `AdfaLdBenchmark` reads from a configured root path (constructor arg or
  `ADFA_LD_PATH` env var). Missing configuration raises a clear runtime
  error pointing to the obtain-and-unzip steps documented in the module
  docstring.
- The adapter tolerates two folder-naming variants under
  `Attack_Data_Master/` (e.g. `Hydra_FTP` vs `Hydra-FTP`) so different
  distributions of the official ADFA-LD archive load without manual
  renaming.
- Windowing rule for Story 7.6: leading window of `sequence_length`
  syscalls per trace, right-padded with zeros if the trace is shorter.
  Story 7.9 may introduce sliding-window variants via the sweep config.
- Feature scaling: each syscall integer is divided by
  `max_syscall_id_seen_in_dataset` so the LSTM input lives in `[0, 1]`.
- Embedded fixture provides 4 normal traces + 10 attack traces (2 per
  attack class) so every code path is exercised by `unittest` without
  network access or the real archive.
- Full regression: 178 tests, OK (skipped=7).

### File List

- `_bmad-output/implementation-artifacts/7-6-adfa-ld-benchmark-adapter.md`
- `src/parallel_truth_fingerprint/lstm_service/offline_training/benchmarks/adfa_ld.py`
- `src/parallel_truth_fingerprint/lstm_service/offline_training/benchmarks/__init__.py`
- `tests/lstm_service/offline_training/test_adfa_ld.py`
- `tests/lstm_service/offline_training/fixtures/adfa_ld_fixture/Training_Data_Master/UTD-0001.txt`
- `tests/lstm_service/offline_training/fixtures/adfa_ld_fixture/Training_Data_Master/UTD-0002.txt`
- `tests/lstm_service/offline_training/fixtures/adfa_ld_fixture/Validation_Data_Master/UVD-0001.txt`
- `tests/lstm_service/offline_training/fixtures/adfa_ld_fixture/Validation_Data_Master/UVD-0002.txt`
- `tests/lstm_service/offline_training/fixtures/adfa_ld_fixture/Attack_Data_Master/Adduser/UAD-0001.txt`
- `tests/lstm_service/offline_training/fixtures/adfa_ld_fixture/Attack_Data_Master/Adduser/UAD-0002.txt`
- `tests/lstm_service/offline_training/fixtures/adfa_ld_fixture/Attack_Data_Master/Hydra_FTP/UFP-0001.txt`
- `tests/lstm_service/offline_training/fixtures/adfa_ld_fixture/Attack_Data_Master/Hydra_FTP/UFP-0002.txt`
- `tests/lstm_service/offline_training/fixtures/adfa_ld_fixture/Attack_Data_Master/Hydra_SSH/USH-0001.txt`
- `tests/lstm_service/offline_training/fixtures/adfa_ld_fixture/Attack_Data_Master/Hydra_SSH/USH-0002.txt`
- `tests/lstm_service/offline_training/fixtures/adfa_ld_fixture/Attack_Data_Master/Java_Meterpreter/UJM-0001.txt`
- `tests/lstm_service/offline_training/fixtures/adfa_ld_fixture/Attack_Data_Master/Java_Meterpreter/UJM-0002.txt`
- `tests/lstm_service/offline_training/fixtures/adfa_ld_fixture/Attack_Data_Master/Web_Shell/UWS-0001.txt`
- `tests/lstm_service/offline_training/fixtures/adfa_ld_fixture/Attack_Data_Master/Web_Shell/UWS-0002.txt`
