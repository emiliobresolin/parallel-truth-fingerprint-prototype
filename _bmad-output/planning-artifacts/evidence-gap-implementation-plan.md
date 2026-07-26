# Evidence-Gap Implementation Plan (BMAD)

**Date:** 2026-06-02 · **Author agent:** BMAD implementation/validation/evidence agent
**Scope guardrail:** simplest solutions that preserve the academic essence; no scope
expansion beyond the current prototype.

This plan tracks evidence/implementation gaps identified while validating
[`docs/results-of-the-prototype.md`](../../docs/results-of-the-prototype.md). Items that
are **already satisfied** are listed at the bottom for traceability and are *not* gaps.

---

## G1 — LID-DS 2021 second benchmark has no real runs

- **Problem:** The advisor's D2 names a second benchmark (LID-DS 2021). The adapter and
  sweep config exist and pass fixture tests, but no real LID-DS run has ever executed
  (the dataset is not on the machine).
- **Why it matters academically:** D6 is satisfied on *one* benchmark (ADFA-LD); a
  second public benchmark strengthens generalisation claims and matches the Assis
  multi-dataset discipline.
- **Affected pillar:** Offline supervised fingerprint.
- **Likely root cause:** Dataset must be obtained out-of-band (large download); not done.
- **Minimal task:** Download LID-DS 2021 into `datasets/LID-DS-2021-real/` in the layout
  the adapter expects, then run `scripts/train_lstm_sweep.py` with a LID-DS embedding
  sweep config (mirror the ADFA-LD embedding configs).
- **Owner:** Dev (download + run) → QA/Test (verify metrics) → Documentation.
- **Acceptance criteria:** ≥5 persisted LID-DS runs (LSTM+GRU); metrics table added to
  the report; honest verdict vs the D6 bar.
- **Complexity:** Medium (mostly data + compute; code exists).
- **Priority:** Useful for December (June delivery already has one D6-passing benchmark).

## G2 — 6-class ADFA-LD framing is below the D6 bar

- **Problem:** The multiclass (6-class) framing does not reach macro F1 ≥ 0.85 (see
  report §5.3 for exact numbers). Only the binary anomaly framing clears D6.
- **Why it matters academically:** Distinguishing *attack family* is a stronger claim
  than binary anomaly detection; reviewers may ask for it.
- **Affected pillar:** Offline supervised fingerprint.
- **Likely root cause:** Severe per-family class imbalance + a single raw-syscall feature;
  6-way macro-F1 is intrinsically hard on ADFA-LD with a small model.
- **Minimal task (only if pursued):** richer features (syscall n-grams / frequency
  channels), larger embedding + 2 RNN layers, more epochs; or a hierarchical
  normal-vs-attack → family classifier. Keep it optional.
- **Owner:** Architect (decide framing) → Dev → QA/Test.
- **Acceptance criteria:** 6-class macro F1 ≥ 0.85 OR an explicit written decision that
  binary anomaly detection is the accepted academic framing for the prototype.
- **Complexity:** Large (uncertain ML outcome).
- **Priority:** Optional for June; useful for December. **Recommended:** accept the
  binary framing as the prototype's fingerprint claim (it matches the runtime question)
  and treat 6-class as exploratory.

## G3 — Online inferencer re-fits on load instead of persisting model weights

- **Problem:** `OnlineLstmInferencer.load` rebuilds and **re-fits** the promoted model on
  the recorded training split rather than loading saved weights (documented Epic 8
  shortcut).
- **Why it matters academically:** Re-fit reproduces the topology and split deterministically
  but is not bit-identical to the promoted run and adds load latency.
- **Affected pillar:** Offline supervised fingerprint (reintegration).
- **Likely root cause:** No model-weights persistence story was implemented.
- **Minimal task:** Persist Keras weights (`.weights.h5`) to MinIO alongside the run
  record; load them in `OnlineLstmInferencer` instead of re-fitting.
- **Owner:** Dev → QA/Test.
- **Acceptance criteria:** Inferencer loads weights without re-fit; predictions match the
  promoted run's test-set behaviour.
- **Complexity:** Medium.
- **Priority:** Useful for December.

## G4 — Promoted-run view is not wired into the live dashboard UI

- **Problem:** `build_promoted_run_dashboard_view` exists and is verified programmatically,
  but the dashboard control surface builds its store against the demo bucket
  (`valid-consensus-artifacts`), not the training-history bucket, so the panel is not
  actually rendered live.
- **Why it matters academically:** A visible dashboard panel makes the reintegration
  claim demonstrable to the examiner without a script.
- **Affected pillar:** Dashboard + offline fingerprint reintegration.
- **Likely root cause:** Story 8.4 delivered the helper, not the wiring.
- **Minimal task:** In the dashboard state builder, call
  `build_promoted_run_dashboard_view` with a store pointed at
  `fingerprint-training-history` and render a small card.
- **Owner:** Dev (dashboard) → QA/Test.
- **Acceptance criteria:** Dashboard shows the promoted run id + macro F1/accuracy live.
- **Complexity:** Small–Medium.
- **Priority:** Useful for December (nice-to-have for the June demo).

## G5 — "Dong Qing" third dataset unresolved

- **Problem:** A third dataset named informally by the advisor was never identified in
  the public literature.
- **Why it matters academically:** Open thread from the orientation meeting.
- **Affected pillar:** Offline supervised fingerprint (scope).
- **Likely root cause:** Ambiguous citation.
- **Minimal task:** Confirm the exact citation with the advisor in the next meeting.
- **Owner:** Documentation / student.
- **Acceptance criteria:** Citation confirmed or formally dropped.
- **Complexity:** Small. **Priority:** Optional.

## G6 — Invalid MinIO bucket names crash the runtime (operator-error hardening)

- **Problem:** During this validation, capturing a blocking scenario into a fresh bucket
  named with an **underscore** (`evidence-quorum_loss`) crashed the runtime with
  `S3Error: InvalidBucketName` from `list_json_objects` → `bucket_exists`. Renaming to a
  hyphenated, S3-valid bucket (`evidence-quorum-loss`) fixed it immediately.
- **Honest scope:** This is **operator error**, not a core defect. `list_json_objects`
  already guards a *valid-but-missing* bucket (it returns `()` cleanly — verified: the
  `normal` scenario created its bucket on first persist, blocking scenarios into valid
  bucket names worked). Only an **invalid name** propagates an S3 error. No code in this
  milestone touched this path.
- **Why it matters:** A live demo is brittle if the operator picks an S3-invalid bucket
  name; a one-line guard + a documented naming rule removes the foot-gun.
- **Affected pillar:** Persistence/storage robustness.
- **Minimal task:** Document the bucket-naming rule (no underscores; lowercase, hyphens)
  in the README; optionally validate the bucket name at `MinioStoreConfig` construction
  with a clear error.
- **Owner:** Documentation (rule) → Dev (optional validation).
- **Acceptance criteria:** README states the rule; optional early validation raises a
  clear message instead of a raw S3 error.
- **Complexity:** Small.
- **Priority:** Useful for June (low-effort demo hardening).

---

## Already satisfied (not gaps — traceability)

- **Decentralization, Byzantine consensus, SCADA comparison, persistence:** demonstrated
  live across `normal`, `quorum_loss`, `single_edge_exclusion`, `scada_divergence`
  (report §2.1).
- **D6 academic bar:** satisfied on the ADFA-LD binary framing — macro F1 0.9187 /
  accuracy 0.9229, 6 runs, LSTM-vs-GRU (report §5).
- **Promotion + dashboard-view payload:** champion promoted; payload verified (report §6a).
