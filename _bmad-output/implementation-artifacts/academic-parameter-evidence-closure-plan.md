# Academic ParameterEvidence Closure Plan

Date: 2026-09-21  
Scope: `thesis-evaluation-v2` academic offline evaluation only  
Status: candidate decision ledger; no authority is granted by this document

## Current gate

The closed-schema requirements inventory contains 205 numeric consumer slots and all 205 remain unresolved. Its identity is
`sha256:f1252521e4f0a9ff4b80e90961e71b5ac4cfa6b82b0841d5442dd34ccab24bbf`; it is bound to numeric schema `academic-v2-numeric-consumer-schema-v1` with identity `sha256:f72c2d4cece03829d7eb3989148042ad82d04a683273dba22c4558d5aacdfaaf`.
No `ParameterEvidence.v1` revision is created or bound by this plan.

Formal authority closure must not begin until the manual technical tests pass. The former 201-slot inferred inventory is historical and insufficient: the 205-slot inventory is now generated from an explicit typed schema and includes the formerly implicit LID preprocessing clip and bootstrap-validity criteria.

## Classification rule

Most values below are protocol choices, not facts supplied by a paper or dataset. The recommended authority class is consequently `preregistered_factor`, backed by a human-approved immutable `DecisionRecord.v1`. A value must not be labelled `direct`, `derived`, or `measured` merely because it is conventional or already appears in configuration.

A future record must bind the exact slot locator, value, unit, quantity kind, experiment/profile scope, rationale, approval and freeze time, limitations, and exact revision/content hashes. Dataset availability observations may support feasibility, but they do not themselves authorize a chosen cap, threshold, hyperparameter, or seed.

## Human decisions to present after technical verification

### 1. Compute-governance decision

- Candidate values: ask-first threshold `12 CPU-hour`; projection safety factor `2.0`.
- Justification: 12 CPU-hours is the explicit user-owned approval boundary; the factor is a conservative project choice rather than an empirically established constant.
- Impact: an incomplete projection always blocks; a complete projection above 12 CPU-hours requires a separate explicit authorization. A larger safety factor raises the projected cost but does not change scientific outcomes.
- Alternatives: retain `2.0`; choose a different documented conservative factor before pilot results; or derive a factor from independently retained timing evidence in a later protocol revision. A missing factor is not replaced by a default.

### 2. Frozen randomness and execution-schedule decision

- Candidate pilot seeds: `[101, 211, 307, 419, 523]`.
- Candidate confirmatory seeds: every integer from `10001` through `10050`, in that exact order.
- Candidate operational batch size: `10`, yielding five immutable positional batches.
- Other candidate seeds: ADFA partition `1729`; LID partition `2718`; HAI partition `3141`; validation-role split `424242`; bootstrap offset `1000003`; paired-comparison seed `99173`.
- Justification: seeds are arbitrary preregistered reproducibility controls. The five pilot trials estimate dispersion only; all 50 confirmatory seeds remain mandatory and non-adaptive.
- Impact: approving these values freezes schedule membership and order. Replacing a seed changes the config, inventory, plans and all downstream identities; it cannot be done in response to observed outcomes.
- Alternatives: approve the listed schedule, or generate a new schedule from an explicitly recorded seed-generation procedure before any v2 outcome is observed. Approval of the number 50 alone does not approve these exact 50 values.

### 3. Statistical-protocol decision

- Candidate values: confidence `0.95`; bootstrap replicates `2000`; minimum independent clusters `5`; minimum class-carrying clusters per class `5`; minimum valid mixed-label replicates `1900` and fraction `0.95`; target seed-level CI half-width `0.025`; stochastic planning minimum `10`; fixed maximum/schedule `50`; permutation replicates `20000`; curve maximum points `201`.
- Calibration candidates: target FPR `0.01`; normal quantile `0.99`; sensitivity quantiles `[0.90, 0.95, 0.975, 0.99, 0.995]`.
- Justification: these are planned precision, Monte Carlo, display and operating-point choices. They are not warranted by the Assis paper and must not be described as universally optimal.
- Impact: more resamples reduce Monte Carlo discreteness at higher cost; confidence and target half-width affect the disclosed uncapped repetition need but never shorten the fixed 50-seed schedule. With only two HAI test recordings, recording-cluster intervals remain undefined despite 50 training seeds.
- Alternatives: approve the candidates; increase resampling counts before outcomes for more Monte Carlo resolution; or adopt different confidence/operating targets in a new preregistered protocol. Lowering the five-cluster minimum merely to obtain an HAI interval is prohibited.

### 4. Validation-role decision

- Candidate values: early-stopping fraction `0.5`; minimum units per validation role `2`.
- Justification: the split separates model stopping from threshold calibration so the same validation observations do not perform both roles. The minimum of two is only a mechanical feasibility floor, not evidence of stable estimation.
- Impact: each role must pass support and disjointness checks; otherwise the affected dataset is blocked. A 50/50 split reduces the data available to each role.
- Alternatives: retain 50/50; freeze another ratio before outcomes; or increase the minimum where independent-unit supply permits. Reusing test truth is never an alternative.

### 5. Dataset allocation and support decisions

All values are counts of samples/independent units or allocation offsets, not repetition counts.

| Dataset | Pilot allocation | Confirmatory allocation | Minimum test support (pilot / confirmatory) | Consequence and alternative |
|---|---|---|---|---|
| ADFA-LD | train `250`, validation `100`, test-normal `100`, attack/class `30`; offsets all `0` | train `500`, validation `500`, test-normal `500`, attack/class `50`; offsets `250/100/100/30` | normal `50/400`; attack `100/200` | Preserves phase-disjoint normalized traces. If inventory is insufficient, reduce a frozen cap before outcomes or block; never reuse pilot units. |
| LID-DS-2021 | `6` archives for each of training, validation, test-normal and test-normal-and-attack; offsets all `0` | `45` for each role; offsets all `6` | normal `30/600`; attack `30/600` | The full confirmatory slice has not yet been manually audited. Approval must be conditional on preflight feasibility and disjointness; otherwise freeze smaller counts before outcomes or block. |
| HAI-23.05 | train-normal `360`, validation-normal `120`, test-total `800`; offsets all `0` | train-normal `500`, validation-normal `500`, test-total `1000`; offsets `360/120/800` | normal `700/850`; attack `20/50` | Row/block support does not create new recordings. Keep point estimates but mark cluster intervals undefined for the observed two recordings; acquire genuinely independent recordings in a future study for recording-level inference. |

The allocation decision must include the exact per-slot values in the requirements inventory, not only this compact table.

### 6. Window and preprocessing decisions

- ADFA-LD: sequence length `128`, stride `64`, maximum windows/unit `6`, aggregation `p95`, normal-validation fraction `0.5`, numeric clip `10.0`.
- LID-DS-2021: sequence length `128`, stride `128`, maximum windows/unit `8`, aggregation `max`.
- HAI-23.05: native block rows `128`, sequence length `128`, stride `128`, maximum windows/unit `1`, aggregation `max`, numeric clip `10.0`.
- Justification: these are frozen candidate representations used by the current leakage-safe protocol; there is no claim that they are externally mandated or globally optimal.
- Impact: changing them changes the detector input, support, cost and comparability, and therefore requires new config/inventory/plan identities. Overlapping windows never become independent inferential units.
- Alternatives: approve the candidates; preregister a pilot-only sensitivity analysis; or adopt different values in a new protocol before confirmatory outcomes. Post-result selection is prohibited.

### 7. Model and stopping decisions

- Shared categorical baseline where applicable: Laplace alpha `1.0`.
- Shared robust-distance candidates: hash bins `128` for ADFA/LID; maximum robust z `20.0` for all three datasets.
- PCA candidates: hash bins `128` for ADFA/LID; latent dimensions `16` for ADFA/LID and `24` for HAI.
- Recurrent candidates: epochs `12`, batch size `128`, hidden units `32`, latent units `16`, learning rate `0.001`, patience `3`, minimum delta `0.00001`; embedding dimensions `16` for ADFA/LID categorical sequences.
- Justification: these are protocol hyperparameters and stopping choices, not measured physical constants. Current evidence supports treating them only as human-frozen candidates, with no optimality claim.
- Impact: they determine capacity, runtime and early stopping. They must remain unchanged across the five confirmatory batches. Deterministic families run once; only the recurrent family receives the 50-seed schedule.
- Alternatives: approve the candidates; perform a separately preregistered pilot-only selection procedure with a fully nested validation design; or freeze a different architecture before confirmatory outcomes. Test-set tuning and between-batch adaptation are prohibited.

## Closure sequence

1. Receive passing manual technical-test output and retain its exact command/stdout/exit code.
2. Close the complete numeric schema so no executable default, Boolean or numeric string bypasses inventory.
3. Rebuild the deterministic requirements inventory; any schema/value change creates a new immutable path/hash and invalidates the current 205-slot identity.
4. Present the grouped decisions above to the human owner with the exact machine-expanded slot ledger. Record approval, rejection or requested alternative separately for each group; do not infer blanket approval.
5. Create immutable `DecisionRecord.v1` and `ParameterEvidence.v1` revisions only for approved values, with explicit limitations and prohibited interpretations.
6. Bind every slot in the required set and run the independent gate. Any unresolved, stale, scope-mismatched or hash-mismatched slot keeps v2 blocked.
7. Only after closure, proceed to preflight. A passing authority gate does not waive leakage, support, artifact-integrity, cost or HAI cluster limitations.
