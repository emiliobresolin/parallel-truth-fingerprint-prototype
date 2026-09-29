# Deferred Work

## 2026-09-21 — academic pipeline review findings outside Iteration 3

These findings predate the fixed-50/five-batch change and require focused design work. They are not waived by the current review.

- Transactional artifact publication: make immutable writes concurrency-safe, prevent a non-cooperating editor from replacing newly approved inventory content in the final check/replace window, and commit prediction/cell artifacts as a recoverable pair so a crash cannot strand an orphan prediction.
- Raw-evidence reconstruction: persist validation-calibration unit IDs, truths, and scores; independently recompute threshold consistency, predictions, confusion/ranking/class/event metrics, curves, and bootstrap outputs from authenticated raw rows before admission.
- Numeric-schema closure: reject omitted numeric consumers, Boolean/numeric-string coercions, and execution defaults that lack inventory slots; define an explicit complete v2 numeric schema rather than inferring completeness only from present JSON leaves.
- Pilot-plan authentication: recompute repetition planning from authenticated pilot cell artifacts rather than trusting editable derived summary fields.
- Cluster-bootstrap design: require adequate class-carrying cluster support and a predeclared valid-replicate criterion for mixed-label clusters.
- Input-label validation: reject non-finite and fractional labels before integer conversion.
- Train-only categorical architecture: derive vocabulary/cardinality exclusively from train-fitted preprocessing metadata and route unseen validation/test IDs through a frozen unknown token.

The intentionally unresolved 201-slot `ParameterEvidence.v1` inventory is not a defect: human-approved authority closure remains a prerequisite to scientific execution.
