# DetectorBundle.v1

`DetectorBundle.v1` is a small, immutable physical-detector contract. Its
content address binds the model family and v2 model contract, architecture and
weights, the ordered v2 physical feature schema, preprocessing, training and
calibration datasets and splits, calibration artifact, frozen threshold and
derivation, score direction, profile compatibility, code, dependency lock,
runtime identity, and the serialized hash of every component.

The bundle contains opaque immutable identifiers only. It contains no truth,
labels, observations, fitted state, threshold value, alias, activation, or
authorization. Changing any identity-bearing field changes `bundle_id`.

`assemble_detector_bundle` is pure and only creates a canonical ID after
structural validation. `load_detector_bundle` is likewise pure: it compares an
explicit declared environment and injected component resolver with every pinned
component. Missing, stale, changed, or incompatible entries reject the entire
load. It never resolves `latest` and has no training, preprocessing-fit,
vocabulary-fit, calibration, or update operation.

Only `PhysicalDetectorModel.v2` with `PhysicalFeatureSchema.v2` is accepted;
all other version combinations, including v1 and mixed-scale artifacts, fail
closed with explicit diagnostic codes.
