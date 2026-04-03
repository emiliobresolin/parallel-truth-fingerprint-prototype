# Story 5.3: Add Human-Readable Status Translation and “What Changed Since Startup” Evidence View

Status: review

## Story

As a researcher and demo operator,
I want the dashboard to translate technical runtime state into human-readable explanations and summarize what changed since startup,
so that I can explain the current prototype run honestly during the live demo without decoding raw metadata on the fly.

## Scope Notes

- This story is limited to interpreted dashboard views derived from the existing runtime, lifecycle, persistence, and dashboard state.
- It must not change:
  - the runtime/control architecture
  - the dataset -> training -> model -> inference flow
  - the current MinIO boundary
  - the adequacy limitation itself
- It must not add:
  - new backend services
  - new ML logic
  - hidden suppression of limitations
  - Story 5.2 visual pipeline work
  - Story 5.4 guidance-panel work

## Acceptance Criteria

1. The dashboard translates technical labels into human-readable explanations, including at minimum:
   - `model_available`
   - `runtime_valid_only`
   - consensus success
   - replay behavior
   - training adequacy
   - anomaly score
2. The dashboard includes a derived “what changed since startup” evidence view.
3. That evidence view shows at minimum:
   - runtime start time
   - elapsed runtime
   - current cycle count
   - valid artifact count growth
   - whether training has already happened
   - when training first happened
   - whether the current model was reused or retrained
   - current model identity/version if available from existing state
   - what has happened already
   - what has not happened yet
   - what is expected next
4. The dashboard explicitly helps answer:
   - has the fingerprint already been created?
   - what changed since startup?
   - what evidence exists in this run?
   - what is expected next?
5. The adequacy limitation remains explicit and honest.
6. The dashboard does not present adequacy-limited inference as academically strong.

## Tasks / Subtasks

- [x] Add a derived explainability module for human-readable status translation. (AC: 1, 5, 6)
- [x] Add a derived “what changed since startup” evidence summary using existing runtime, lifecycle, and dashboard state. (AC: 2, 3, 4, 5)
- [x] Wire the explainability and evidence views into the dashboard state and UI. (AC: 1, 2, 3, 4)
- [x] Add focused Story 5.3 tests plus runtime smoke validation coverage. (AC: 1, 2, 3, 4, 5, 6)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story 5.3 was implemented entirely as a derived dashboard layer on top of existing runtime payloads and operator feedback.
- No runtime orchestration, persistence boundary, or ML lifecycle behavior was changed in this story.

### Completion Notes List

- Added `src/parallel_truth_fingerprint/dashboard/evidence_view.py` to build:
  - human-readable status translations
  - a derived “what changed since startup” evidence view
- Added translations for:
  - model status
  - validation level
  - consensus status
  - replay behavior
  - training adequacy
  - anomaly score
- Added derived evidence answers for:
  - whether the fingerprint exists
  - what changed since startup
  - what evidence exists in the current run
  - what is expected next
- Added dashboard UI sections for:
  - `Human-Readable Status`
  - `What Changed Since Startup`
- Preserved the runtime-valid-only limitation explicitly and kept it visible in the derived evidence state.
- Implemented only Story 5.3.

### What Was Tested

- Focused Story 5.3 explainability translation tests
- Existing dashboard control-surface tests
- Existing real dashboard smoke test
- Full regression suite

### Exact Commands Executed

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python -m unittest tests.dashboard.test_evidence_view tests.dashboard.test_control_surface
```

```powershell
$env:PYTHONPATH='src'
$env:RUN_REAL_DASHBOARD_SMOKE='1'
.\.venv\Scripts\python -m unittest tests.dashboard.test_control_surface_runtime_smoke
```

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python -m unittest discover -s tests
```

### Test Results

- `tests.dashboard.test_evidence_view tests.dashboard.test_control_surface` -> `Ran 6 tests` -> `OK`
- `tests.dashboard.test_control_surface_runtime_smoke` -> `Ran 1 test` -> `OK`
- `python -m unittest discover -s tests` -> `Ran 126 tests` -> `OK (skipped=7)`

### Real Runtime Behavior Validated

- The real Story 4.6 dashboard smoke still passed after adding the Story 5.3 explainability layer.
- The runtime smoke now validates that the dashboard state includes:
  - `translated_statuses`
  - `what_changed_since_startup`
- The smoke run still confirmed:
  - real dashboard start/stop control path
  - power-change behavior through the real runtime state
  - replay behavior through the existing fingerprint path
  - saved-model reuse
  - explicit runtime-valid-only limitation

### Remaining Limitations

- Story 5.3 remains a dashboard interpretation layer only; it does not increase fingerprint adequacy.
- The fingerprint base is still runtime-valid only, not yet meaningful-fingerprint-valid.
- Runtime start time is derived primarily from dashboard operator actions and current state rather than a new persisted audit trail.
- Story 5.3 does not include the visual pipeline work from Story 5.2 or the demo-guidance panels from Story 5.4.

### File List

- `_bmad-output/implementation-artifacts/5-3-add-human-readable-status-translation-and-what-changed-since-startup-evidence-view.md`
- `src/parallel_truth_fingerprint/dashboard/control_surface.py`
- `src/parallel_truth_fingerprint/dashboard/evidence_view.py`
- `tests/dashboard/test_control_surface.py`
- `tests/dashboard/test_control_surface_runtime_smoke.py`
- `tests/dashboard/test_evidence_view.py`

## Stabilization Follow-up

- Corrected the startup/evidence scoping so the dashboard reports the most recent real run attempt instead of collapsing failed restarts into one long run.
- Revalidated that the stopped-state dashboard still answers “what changed since startup” truthfully after a failed or completed attempt.
