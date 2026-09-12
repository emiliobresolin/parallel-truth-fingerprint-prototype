# Official and Primary Reference Archive

This directory is the verification archive for the scientifically grounded
industrial-signal, syscall, anomaly-detection, and evaluation plan.

## Authority and storage policy

- Prefer standards bodies, government publications, manufacturer manuals,
  dataset-owner repositories, and peer-reviewed primary papers.
- Every adopted number must be classified as `direct`, `derived`, `measured`,
  `preregistered_factor`, or `mock` in the machine authority
  `catalog/parameter-evidence.v1.json`.
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
    source-catalog.v1.json
    parameter-evidence.v1.json
    parameter-evidence.csv
    decision-custom-reference-window-v1.yaml
    mock-admission-ptfp-signal-emulator-v1.yaml
    legacy-constant-quarantine-v1.csv
    checksums.sha256
  documents/       # local verification copies, ignored by Git
```

The machine authority is
[catalog/source-catalog.v1.json](catalog/source-catalog.v1.json). It separates
the stable logical `source_id`, exact `source_revision_id`, observed byte-stream
`content_id`, retrieval observation `retrieval_id`, bounded source uses,
relations, and unresolved discrepancies. The human
[catalog/index.md](catalog/index.md) and
[catalog/checksums.sha256](catalog/checksums.sha256) files are deterministic
projections and must not be edited as independent authorities.

The sole machine authority for numeric accountability is
[catalog/parameter-evidence.v1.json](catalog/parameter-evidence.v1.json). The
CSV and YAML parameter, decision, mock-admission, and legacy-quarantine files
are frozen migration inputs and compatibility snapshots identified by their
preserved content hashes. They do not compete with the JSON authority and are
never read as runtime defaults. The JSON retains all 15 planning rows and 20
legacy quarantine rows without promoting blocked, conditional, candidate, or
legacy-only evidence.

Exact version and release authority belongs to `source_revision_id`. The
version/date fields retained on a logical source are immutable migration
baseline metadata and must match at least one revision; later editions append
new revision, content, retrieval, and use identities instead of rewriting the
baseline.

Run the read-only validator from the repository root with the package available
on Python's import path:

```powershell
.\.venv\Scripts\python.exe scripts\validate_source_catalog.py --check
.\.venv\Scripts\python.exe scripts\validate_source_catalog.py --check --archive-root docs\reference-archive\documents
.\.venv\Scripts\python.exe scripts\validate_source_catalog.py --catalog proposed.json --prior-catalog prior.json
.\.venv\Scripts\python.exe scripts\validate_parameter_evidence.py --catalog docs\reference-archive\catalog\parameter-evidence.v1.json --source-catalog docs\reference-archive\catalog\source-catalog.v1.json --consumer-inventory docs\reference-archive\catalog\parameter-evidence.v1.json --required-set docs\reference-archive\catalog\parameter-evidence.v1.json
```

The first command checks metadata and projection drift without requiring the
ignored archive. The second additionally verifies every declared local file as
an opaque stream against its size and SHA-256. The third checks append-only
identity preservation against an explicitly supplied prior catalog. None of
these commands writes files,
uses the network, downloads sources, infers rights, or authorizes activity.

Large, restricted, and dataset bytes remain outside Git. Local possession,
public access, an author copy, or a repository license never silently grants
redistribution rights to a different artifact. Unknown rights remain explicit.
The decision, mock-admission, parameter-evidence, and legacy-quarantine records
remain adjacent downstream inputs; catalog inclusion has
`authorization_effect: none` and does not authorize implementation, training,
capture, experiments, activation, or publication.

The parameter command returns `0` only for an accountable exact selection, `1`
for a well-formed blocked selection, and `2` for malformed input or usage. The
current planning baseline intentionally returns `1`: its inventory is
incomplete and its unresolved source, decision, derivation, and mock closures
remain visible. The command is read-only and never selects, repairs, downloads,
starts, trains, captures, executes, publishes, or activates anything.
