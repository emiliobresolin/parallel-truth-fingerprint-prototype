# Official and Primary Reference Archive

This directory is the verification archive for the scientifically grounded
industrial-signal, syscall, anomaly-detection, and evaluation plan.

## Authority and storage policy

- Prefer standards bodies, government publications, manufacturer manuals,
  dataset-owner repositories, and peer-reviewed primary papers.
- Every adopted number must be classified as `direct`, `derived`, `measured`,
  `preregistered_factor`, or `mock` in `catalog/parameter-evidence.csv`.
- Publicly downloadable files are stored locally under `documents/` with the
  original URL, retrieval date, byte size, and SHA-256 in the source register.
- Paywalled or access-controlled standards are not copied. Their official
  landing pages, edition, and access limitation are recorded in the catalog.
- Vendor manuals are retained locally for academic verification but are not
  automatically redistribution-safe.
- Dataset archives remain outside Git under `datasets/` or object storage.
- The local PDF archive is ignored by Git to avoid repository bloat and
  accidental redistribution. The catalog and checksums remain versionable.
- A link or document establishes only the claims located in the catalog; it
  does not make unrelated project parameters official.

## Layout

```text
docs/reference-archive/
  README.md
  catalog/
    index.md
    parameter-evidence.csv
    decision-custom-reference-window-v1.yaml
    mock-admission-ptfp-signal-emulator-v1.yaml
    legacy-constant-quarantine-v1.csv
    checksums.sha256
  documents/       # local verification copies, ignored by Git
```

The canonical human-readable inventory is [catalog/index.md](catalog/index.md).
The three additional records separate researcher decisions, admitted mock
capability gaps, and legacy-only anonymous constants; none of them authorizes
runtime or experiment activity.
