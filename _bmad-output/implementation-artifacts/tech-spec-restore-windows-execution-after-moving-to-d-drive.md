---
title: 'Restore Windows execution after moving the repository to D drive'
type: 'chore'
created: '2026-09-13'
status: 'done'
baseline_commit: '27822d4'
context:
  - 'README.md'
  - '_bmad/bmm/config.yaml'
---

# Restore Windows execution after moving the repository to D drive

<frozen-after-approval reason="human-owned intent â€” do not modify unless human renegotiates">

## Intent

**Problem:** The repository was moved from an old `C:` location to `D:`, leaving a Python virtual environment whose Windows launchers embed the old path and operational commands that inconsistently target an empty `venv` directory instead of `.venv`. This prevents documented scripts and dependency tooling from running reliably.

**Approach:** Preserve all current source and BMAD changes, standardize active commands on a fresh project-local `.venv`, repair current workspace path references, synchronize every declared dependency group, and validate the application with imports, tests, preflight checks, and available infrastructure tooling.

## Boundaries & Constraints

**Always:** Preserve all existing uncommitted work; use repository-relative paths wherever possible; keep public datasets outside version control; retain a recoverable copy of the stale environment until verification completes; distinguish failures caused only by the still-downloading LID-DS data.

**Ask First:** Any change requiring deletion of non-environment user data, modification of historical immutable evidence, or credentials/external account access.

**Never:** Reset or discard existing Git changes; rewrite historical evidence solely to replace recorded old paths; commit datasets, secrets, virtual environments, generated containers, or package caches; claim the LID-DS workflow passed before the download and layout are complete.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|---------------|----------------------------|----------------|
| Moved workspace | Project is launched from the current `D:` root | Documented Python and PowerShell commands resolve `.venv` and repository-relative files | Fail with a clear setup instruction, never fall back to the former `C:` path |
| Stale virtual environment | Launchers embed the former workspace location | A newly synchronized `.venv` uses the current path and contains all declared extras | Preserve the old environment under ignored temporary storage until checks pass |
| LID-DS incomplete | `datasets/LID-DS-real` is absent or still incomplete | Non-LID checks run; LID qualification reports an honest data-only blocker | Do not manufacture, rename, or mutate partially downloaded dataset content |
| Infrastructure unavailable | Docker daemon or a service is stopped | Static/configuration checks still run and the precise external blocker is reported | Do not erase Docker volumes or unrelated containers |

</frozen-after-approval>

## Code Map

- `pyproject.toml` â€” authoritative Python version and dependency groups.
- `uv.lock` â€” reproducible dependency resolution used to rebuild `.venv`.
- `README.md` â€” primary Windows setup and execution commands, including one obsolete absolute `C:` path.
- `scripts/run_live_edge_capture.ps1` â€” active preflight currently points to `venv`.
- `scripts/download_hai_official.ps1` â€” active Kaggle launcher currently points to `venv`.
- `docs/manual-live-execution.md` â€” current operator runbook with `venv` commands.
- `_bmad/bmm/config.yaml` and `.agents/skills/` â€” local BMAD 6.2.0 installation and project configuration.
- `_bmad-output/implementation-artifacts/sprint-status.yaml` â€” active BMAD story location still records the former `C:` workspace.
- `src/parallel_truth_fingerprint/lstm_service/offline_training/benchmarks/lid_ds_2021.py` â€” required LID-DS layout and environment-variable contract.

## Tasks & Acceptance

**Execution:**
- [x] `README.md`, `docs/manual-live-execution.md`, `docs/live-qualification-2026-09-13.md` â€” replace active `venv` and absolute old-root commands with portable `.venv`/relative instructions.
- [x] `scripts/run_live_edge_capture.ps1`, `scripts/download_hai_official.ps1` â€” resolve `.venv` executables from the script-derived project root and emit actionable missing-environment errors.
- [x] `_bmad-output/implementation-artifacts/sprint-status.yaml` â€” update only the active BMAD `story_location` to the current `D:` repository.
- [x] `.venv` â€” preserve the stale moved environment, recreate it from `uv.lock`, and synchronize all declared extras so console launchers reference the current workspace.
- [x] Workspace/runtime â€” scan active files for functional old-drive references and run imports, dependency checks, unit tests, BMAD integrity checks, LID preflight, and Docker/Compose diagnostics.

**Acceptance Criteria:**
- Given the repository is on `D:`, when documented setup and runtime commands are resolved, then none requires the former workspace or the empty `venv` directory.
- Given a clean shell in the project root, when `.venv\Scripts\python.exe` imports the package and required dependency sets, then imports succeed and `pip check` reports no conflicts.
- Given the current source tree, when the unit-test suite runs with `PYTHONPATH=src`, then it passes or every residual failure is reported with evidence and separated from LID download incompleteness.
- Given the local BMAD installation, when its configuration and skill trees are checked, then required configuration and workflow files exist and remain usable from the new root.
- Given LID-DS is still downloading, when qualification runs, then it either recognizes a valid completed layout or fails closed with the exact missing data condition.

## Spec Change Log

## Verification

**Commands:**
- `py -m uv pip check --python .venv\Scripts\python.exe` â€” expected: no broken requirements.
- `$env:PYTHONPATH='src'; .venv\Scripts\python.exe -c "import parallel_truth_fingerprint"` â€” expected: package import succeeds from `D:`.
- `$env:PYTHONPATH='src'; .venv\Scripts\python.exe -m unittest discover -s tests` â€” expected: suite passes, excluding only explicitly documented external-data/service blockers.
- `.venv\Scripts\python.exe scripts\qualify_live_run.py` â€” expected: all local prerequisites pass or only incomplete official datasets/services are reported.
- `docker version` and `docker compose config` for project compose files â€” expected: client/daemon reachable and configurations parse with required environment supplied where applicable.
- `rg` scan of active configuration, scripts, and runbooks â€” expected: no functional reference to the old `C:` project root or `venv\Scripts` remains.
