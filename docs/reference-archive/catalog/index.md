# Source Register

Retrieval baseline: **2026-08-15**. Correct-course source update:
**2026-08-22**.

Status meanings:

- `local`: a verification copy is stored in `../documents/` and identified by
  `checksums.sha256`.
- `link-only`: the official source is an HTML/specification/repository page.
- `restricted`: the full standard is paywalled or access-controlled and is not
  copied without a license.
- `pending`: automated retrieval has not yet succeeded and must be performed
  manually from the official URL.

## Standards and official specifications

| Source ID | Document/version | Official source | Status | Project use |
|---|---|---|---|---|
| `std-iec-60381-1-1982` | IEC 60381-1 Ed. 2.0 (1982) | [IEC](https://webstore.iec.ch/en/publication/1948) | restricted | Industrial DC-current signals |
| `std-iec-60381-2-1978` | IEC 60381-2 Ed. 1.0 (1978) | [IEC](https://webstore.iec.ch/en/publication/1949) | restricted | Industrial DC-voltage signals and limitations |
| `std-isa-50-archived` | ANSI/ISA-50.00.01, archived 2024 | [ISA50](https://www.isa.org/standards-and-publications/isa-standards/isa-standards-committees/isa50), [archive](https://www.isa.org/standards-and-publications/isa-standards/archived-standards) | restricted | Historical 4-20 mA reference; not an active standard |
| `std-namur-ne43-2021` | NAMUR NE 43 revision notice (2021) | [NAMUR](https://www.namur.net/en/publications/news-archive/ne-43-has-been-revised.html) | restricted | Failure-current semantics; numerical use requires device manual |
| `std-iec-62443-3-2-2020` | IEC 62443-3-2 Ed. 1.0 (2020) | [IEC](https://webstore.iec.ch/en/publication/30727) | restricted | Zones, conduits, and risk assessment |
| `std-iec-61511-1-2017` | IEC 61511-1 Ed. 2.1 consolidated (2017) | [IEC](https://webstore.iec.ch/en/publication/61289) | restricted | Functional-safety boundary; no compliance claim |
| `std-jcgm-100-2008` | JCGM 100:2008, GUM | [BIPM PDF](https://www.bipm.org/documents/20126/2071204/JCGM_100_2008_E.pdf) | local | Type-B uncertainty and propagation |
| `std-mqtt-5-2019` | MQTT v5.0 OASIS Standard (2019) | [OASIS PDF](https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.pdf) | local | QoS, delivery, ordering, duplicates |
| `std-rfc5905-2010` | RFC 5905, NTPv4 | [RFC Editor](https://www.rfc-editor.org/info/rfc5905/) | local (official ASCII edition) | Clock synchronization evidence |
| `std-rfc3339-2002` | RFC 3339 timestamps | [RFC Editor](https://www.rfc-editor.org/rfc/rfc3339.html) | link-only | Timestamp serialization |
| `std-rfc8785-2020` | RFC 8785, JSON Canonicalization | [RFC Editor PDF](https://www.rfc-editor.org/rfc/rfc8785.pdf) | local | Stable JSON hashing/signing |
| `std-opcua-part4-10507` | OPC UA Part 4 v1.05.07 | [OPC Foundation](https://reference.opcfoundation.org/specs/OPC-10000-4/v1.05.07) | link-only | DataValue quality and timestamps |
| `std-opcua-part8-10507` | OPC UA Part 8 v1.05.07 | [OPC Foundation](https://reference.opcfoundation.org/specs/OPC-10000-8/v1.05.07) | link-only | AnalogItem, current/process values, ranges and units |
| `std-cloudevents-102` | CloudEvents v1.0.2 | [CNCF specification](https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/spec.md) | local | Envelope identity semantics only |
| `std-w3c-prov-dm-2013` | W3C PROV-DM | [W3C Recommendation](https://www.w3.org/TR/prov-dm/) | link-only | Artifact lineage entities/activities/agents |
| `std-otel-log-model-1600` | OpenTelemetry Log Data Model v1.60.0 | [OpenTelemetry tag](https://github.com/open-telemetry/opentelemetry-specification/tree/v1.60.0) | local | Source versus observed timestamps and trace context |
| `std-oci-image-111` | OCI Image Specification descriptor v1.1.1 | [OCI tag](https://github.com/opencontainers/image-spec/tree/v1.1.1) | local | Content identifiers, digest and size verification |

## Manufacturer and instrument documentation

| Source ID | Document/version | Official source | Status | Project use |
|---|---|---|---|---|
| `vendor-ni-scaling-2024` | NI 4-20 mA scaling guidance | [NI](https://knowledge.ni.com/KnowledgeArticleDetails?id=kA00Z000000PASfSAO) | link-only | Linear endpoint conversion |
| `vendor-rockwell-5034-um003-2025` | PointMax 5034 Analog I/O, 5034-UM003-EN-P | [Rockwell PDF](https://literature.rockwellautomation.com/idc/groups/literature/documents/um/5034-um003_-en-p.pdf) | local | 4/12/20 mA scaling and channel data |
| `vendor-siemens-sitrans-th-2025` | SITRANS TH320/TH420 FI01 (official Spanish edition archived) | [Siemens PDF](https://cache.industry.siemens.com/dl/files/161/109765161/att_1324085/v1/sitranst_th320_th420_fi01_es.pdf) | local | Normal/extended/fault current bands |
| `vendor-endress-ra33-2021` | Endress+Hauser RA33 BA00300K | [Endress PDF](https://bdih-download.endress.com/file/005056A5E3831EECA4FD81E28AFA37F3/BA00300KEN_0621-00.pdf) | local | Under/over-range and device-fault behavior |
| `vendor-electrosensors-fb420-datasheet-2025` | FB420 2.0 ES730 Rev I | [Electro-Sensors](https://www.electro-sensors.com/download_file/337/1274) | local | Real 4-20 mA RPM sensor and uncertainty |
| `vendor-electrosensors-fb420-manual` | FB420 v2.0 990-003401 Rev A | [Electro-Sensors PDF](https://www.electro-sensors.com/application/files/4817/1095/7949/FB420_v2.0_Standard_990-003401_Rev_A.pdf) | local | RPM endpoint configuration |
| `vendor-danfoss-cds803-design` | VLT CDS 803 Design Guide AJ330233902305 | [Danfoss PDF](https://assets.danfoss.com/documents/272571/AJ330233902305en-000301.pdf) | local | Compressor-drive 4-20 mA reference |
| `vendor-danfoss-cds803-programming-2021` | VLT CDS 803 Programming Guide AU356039245821 en-000201 / 130R0597 (2021.07) | [Danfoss PDF](https://assets.danfoss.com/documents/273384/AU356039245821en-000201.pdf) | local; 2,206,514 bytes; retrieved 2026-08-22 | Terminal 53 current and reference/feedback configuration; printed p. 54, Tables 60-63, parameters 6-12 through 6-15 |
| `vendor-siemens-sitrans-p200-2025` | SITRANS P200/P210/P220 FI 01 (2025) | [Siemens PDF](https://support.industry.siemens.com/cs/attachments/109765047/sitransp_p200_p210_p220_fi01_fr.pdf) | pending; official server denied automated archival on 2026-08-22 | Candidate 0-10 bar gauge-pressure, 4-20 mA two-wire profile; printed p. 1/7 selection table; dependent formal profile remains blocked until exact bytes are archived and hashed |
| `vendor-doe-compressed-air-sourcebook` | Compressed Air Sourcebook, 3rd ed. | [US DOE PDF](https://www.energy.gov/sites/prod/files/2016/03/f30/Improving%20Compressed%20Air%20Sourcebook%20version%203.pdf) | local | Compressor capacity/speed/power limitations |
| `vendor-fieldcomm-hart-guide-r71` | HART Application Guide Rev. 7.1 | [FieldComm PDF](https://www.fieldcommgroup.org/sites/default/files/imce_files/technology/documents/HART_ApplicationGuide_r7.1.pdf) | local | HART/4-20 mA relationship; prototype remains HART-inspired |

## Government and research-data guidance

| Source ID | Document/version | Official source | Status | Project use |
|---|---|---|---|---|
| `gov-nist-sp800-82r3-2023` | NIST SP 800-82 Rev. 3 | [NIST PDF](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-82r3.pdf) | local | OT architecture, availability, zones and flows |
| `gov-nist-ir8219-2020` | NIST IR 8219 | [NIST PDF](https://nvlpubs.nist.gov/nistpubs/ir/2020/NIST.IR.8219.pdf) | local | Passive behavioral anomaly detection for ICS |
| `gov-nist-ir8089-2015` | NIST IR 8089 | [NIST PDF](https://nvlpubs.nist.gov/nistpubs/ir/2015/NIST.IR.8089.pdf) | local | Realistic bounded ICS cybersecurity testbed |
| `gov-nist-sp1800-10-2022` | NIST SP 1800-10 | [NIST PDF](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.1800-10.pdf) | link-only (automated endpoint returned HTTP 404) | Manufacturing integrity example builds |
| `gov-nist-sp1339-2026` | NIST SP 1339 | [NIST PDF](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.1339.pdf) | local | OT backup and tested restoration |
| `gov-nist-rdaf2-2024` | NIST SP 1500-18 Rev. 2, RDaF 2.0 | [NIST PDF](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/1500-18/NIST.SP.1500-18r2.pdf) | local | Raw/derived data, versioning and provenance |
| `gov-nist-ai-rmf-2023` | NIST AI RMF 1.0 | [NIST PDF](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf) | local | Model documentation and TEVV |
| `gov-nist-ai-rmf-playbook` | NIST AI RMF Playbook | [NIST PDF](https://airc.nist.gov/docs/AI_RMF_Playbook.pdf) | local | Repeatable evaluation/documentation practices |
| `gov-nist-sp800-53r5` | NIST SP 800-53 Rev. 5 | [NIST PDF](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-53r5.pdf) | local | Least privilege, separation and audit protection |
| `gov-nist-sp800-218-2022` | NIST SP 800-218, SSDF | [NIST PDF](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-218.pdf) | local | Secure development, verification and documented releases |
| `gov-cisa-segmentation-2022` | Layering Network Security Through Segmentation | [CISA PDF](https://www.cisa.gov/sites/default/files/publications/layering-network-security-segmentation_infographic_508_0.pdf) | local | Supporting network-segmentation guidance |

## Dataset-owner and model primary sources

| Source ID | Document/version | Official source | Status | Project use |
|---|---|---|---|---|
| `dataset-adfa-official` | ADFA IDS datasets | [UNSW](https://research.unsw.edu.au/projects/adfa-ids-datasets) | link-only | Owner page, academic-use terms and dataset identity |
| `dataset-lid-official` | LID-DS official repository | [Leipzig/GitHub](https://github.com/LID-DS/LID-DS) | link-only | Official layouts, loader and GPL terms |
| `dataset-lid-paper-2023` | LID-DS 2021 evaluation paper | [Leipzig PDF](https://dbs.uni-leipzig.de/files/research/publications/2023-6/pdf/978-3-031-35190-7_6.pdf) | local | Official split/schema/evaluation semantics |
| `dataset-hai-official` | HAI official repository | [HAI GitHub](https://github.com/icsdataset/hai) | link-only | Versioned data and license caveat |
| `dataset-hai-manual-v4` | HAI Technical Details v4.0 | [HAI PDF](https://raw.githubusercontent.com/icsdataset/hai/master/hai_dataset_technical_details.pdf) | local | Tag ranges, layouts and scenario details |
| `paper-lstm-1997` | Hochreiter & Schmidhuber, LSTM | [MIT Press DOI page](https://direct.mit.edu/neco/article/9/8/1735/6109/Long-Short-Term-Memory), [author copy](https://www.bioinf.jku.at/publications/older/2604.pdf) | local (author copy; redistribution caveat) | LSTM design motivation, not superiority evidence |
| `paper-gru-2014` | Cho et al., GRU | [ACL PDF](https://aclanthology.org/D14-1179.pdf) | local | GRU primary paper |
| `paper-rnn-search-2015` | Jozefowicz et al. | [PMLR PDF](https://proceedings.mlr.press/v37/jozefowicz15.pdf) | local | No universal LSTM/GRU winner |
| `paper-deeplog-2017` | DeepLog | [University of Utah PDF](https://www2.cs.utah.edu/~lifeifei/papers/deeplog.pdf) | local (author copy; redistribution caveat) | Categorical event-sequence LSTM precedent |
| `paper-hai-2020` | HAI 1.0 | [USENIX PDF](https://www.usenix.org/system/files/cset20-paper-shin.pdf) | local | Dataset origin and evaluation context |
| `paper-lstm-ed-anomaly-2016` | Malhotra et al., LSTM encoder-decoder anomaly detector | [arXiv v2](https://arxiv.org/abs/1607.00148) | local | Sequence-autoencoder precedent; not universal threshold evidence |
| `metric-etapr` | eTaPR official implementation | [Official GitHub](https://github.com/wshw4ng/eTaPR) | link-only | Range/event-aware anomaly evaluation |

## Tooling and operational references

| Source ID | Official source | Status | Project use |
|---|---|---|---|
| `tool-docker-container-kernel` | [Docker: What is a container?](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-container/) | link-only | Containers are isolated processes that share the Linux kernel; establishes the capture boundary |
| `tool-docker-desktop-isolation` | [Docker Desktop container security](https://docs.docker.com/security/faqs/containers/) | link-only | On Windows, Linux containers run inside Docker Desktop's Linux VM; host-capture claims must name that boundary |
| `tool-linux-tracepoints` | [Linux kernel tracepoints](https://docs.kernel.org/trace/tracepoints.html) | link-only | Kernel hooks used for tracing/performance accounting |
| `tool-sysdig-container-capture` | [Official Sysdig repository](https://github.com/draios/sysdig) | link-only | Container-aware Linux system-event capture and immutable `.scap` traces |
| `tool-lid-recording-framework` | [Official LID-DS Docker/Sysdig recording framework](https://github.com/LID-DS/LID-DS/wiki/LID-DS-Recording-Framework%3A-Documentation-and-Installation) | link-only | Primary precedent for building scenario images and recording real syscalls with Sysdig |
| `tool-uv-locking` | [uv locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/) | link-only | Frozen dependency environment |
| `tool-docker-pin` | [Docker build best practices](https://docs.docker.com/build/building/best-practices/) | link-only | Pin mutable image tags by digest |
| `tool-oci-digest` | [OCI content descriptors](https://github.com/opencontainers/image-spec/blob/main/descriptor.md) | link-only | Content-addressed image/artifact identity |
| `tool-minio-versioning` | [MinIO versioning](https://min.io/docs/minio/kubernetes/upstream/administration/object-management/object-versioning.html) | link-only | Immutable-style artifact storage and capacity caution |
| `tool-minio-object-lock` | [MinIO object locking](https://min.io/docs/minio/windows/administration/object-management/object-retention.html) | link-only | Optional WORM evidence retention |
| `tool-pytorch-reproducibility` | [PyTorch reproducibility](https://docs.pytorch.org/docs/stable/notes/randomness) | link-only | Seeds/determinism limits and cost |
| `tool-sklearn-leakage` | [scikit-learn common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html) | link-only | Train-only preprocessing and no test leakage |
| `tool-falco-drops` | [Falco dropped syscall events](https://falco.org/docs/concepts/event-sources/kernel/dropped-events/) | link-only | Capture drop counters and run-quality policy |

## Caveats

- A locally stored manual or paper does not transfer redistribution rights.
- An official link is not proof that every number in the document applies to
  this compressor profile; the exact page/table/section belongs in
  `parameter-evidence.csv`.
- Repository pages and web specifications are intentionally indexed rather
  than copied when no stable public document or redistribution basis exists.
- `latest` URLs are never sufficient provenance without the retrieved file's
  document number and SHA-256.
- The Danfoss programming-guide source authorizes configurability and the
  documented defaults for parameters 6-12 and 6-13. It does not make the
  project-selected 0/100 reference configuration or 25%/75% experiment factors
  manufacturer recommendations.
