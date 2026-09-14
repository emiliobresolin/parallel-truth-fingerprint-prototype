# Cross-Benchmark Comparative Report

This is a source-separated comparison matrix: each score is evaluated within its own dataset and label protocol. It must not be read as a cross-dataset accuracy claim.

## Champion runs per benchmark

| benchmark | model | run_id | macro_f1 | accuracy | macro_precision | macro_recall | parameter_count |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| hai-23.05 | lstm-classifier | run-hai-23.05-lstm-classifier-20260914T165229-dd571c76 | 0.3333 | 0.5000 | 0.2500 | 0.5000 | 71810 |
| lid-ds-2021 | lstm-classifier | run-lid-ds-2021-lstm-classifier-20260914T165610-be698260 | 0.0149 | 0.0606 | 0.0079 | 0.1250 | 50960 |
| adfa-ld | lstm-classifier | run-adfa-ld-lstm-classifier-20260914T164724-e8f6e32a | 0.0382 | 0.0605 | 0.1654 | 0.2135 | 50310 |
| custom-current-syscall | runtime-lstm-autoencoder+edge-syscalls | run-custom-current-syscall-runtime-autoencoder-20260914T170021-cfc12359 | 0.3333 | 0.5000 | 0.2500 | 0.5000 | 0 |

## Per-class metrics

### hai-23.05 -- lstm-classifier -- run-hai-23.05-lstm-classifier-20260914T165229-dd571c76

| class | precision | recall | f1 | support_train | support_test |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0 | 0.5000 | 1.0000 | 0.6667 | 40 | 10 |
| 1 | 0.0000 | 0.0000 | 0.0000 | 40 | 10 |

### lid-ds-2021 -- lstm-classifier -- run-lid-ds-2021-lstm-classifier-20260914T165610-be698260

| class | precision | recall | f1 | support_train | support_test |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0 | 0.0000 | 0.0000 | 0.0000 | 72 | 18 |
| 1 | 0.0000 | 0.0000 | 0.0000 | 1 | 1 |
| 2 | 0.0714 | 1.0000 | 0.1333 | 1 | 1 |
| 3 | 0.0556 | 1.0000 | 0.1053 | 1 | 1 |
| 4 | 0.0000 | 0.0000 | 0.0000 | 1 | 1 |
| 5 | 0.0000 | 0.0000 | 0.0000 | 1 | 1 |
| 6 | 0.0000 | 0.0000 | 0.0000 | 1 | 1 |
| 7 | 0.0000 | 0.0000 | 0.0000 | 1 | 1 |
| 8 | 0.0000 | 0.0000 | 0.0000 | 1 | 1 |
| 9 | 0.0000 | 0.0000 | 0.0000 | 1 | 1 |
| 10 | 0.0000 | 0.0000 | 0.0000 | 1 | 1 |
| 11 | 0.0000 | 0.0000 | 0.0000 | 1 | 1 |
| 12 | 0.0000 | 0.0000 | 0.0000 | 1 | 1 |
| 13 | 0.0000 | 0.0000 | 0.0000 | 1 | 1 |
| 14 | 0.0000 | 0.0000 | 0.0000 | 1 | 1 |
| 15 | 0.0000 | 0.0000 | 0.0000 | 1 | 1 |

### adfa-ld -- lstm-classifier -- run-adfa-ld-lstm-classifier-20260914T164724-e8f6e32a

| class | precision | recall | f1 | support_train | support_test |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0 | 0.8222 | 0.0355 | 0.0681 | 4164 | 1041 |
| 1 | 0.0283 | 0.5000 | 0.0536 | 73 | 18 |
| 2 | 0.1111 | 0.0312 | 0.0488 | 130 | 32 |
| 3 | 0.0306 | 0.7143 | 0.0586 | 141 | 35 |
| 4 | 0.0000 | 0.0000 | 0.0000 | 159 | 40 |
| 5 | 0.0000 | 0.0000 | 0.0000 | 94 | 24 |

### custom-current-syscall -- runtime-lstm-autoencoder+edge-syscalls -- run-custom-current-syscall-runtime-autoencoder-20260914T170021-cfc12359

| class | precision | recall | f1 | support_train | support_test |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0 | 0.5000 | 1.0000 | 0.6667 | 0 | 1 |
| 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 1 |


## Dataset provenance

- **hai-23.05** -- origin: HAI security dataset, year: 2023, version: `HAI-23.05`. citation: HIL-based Augmented ICS Security Dataset (HAI), 23.05 release.
- **lid-ds-2021** -- origin: LID-DS 2021, year: 2021, version: `2021`. citation: Grimmer, M., Kaelble, F., et al. 'LID-DS: A New Dataset for Linux Host-Based Intrusion Detection'. github.com/LID-DS/LID-DS, 2021 release.
- **adfa-ld** -- origin: ADFA-LD, year: 2013, version: `ADFA-LD`. citation: Creech, G., and Hu, J. 'Generation of a New IDS Test Dataset: Time to Retire the KDD Collection'. IEEE WCNC 2013.
- **custom-current-syscall** -- origin: PTFP synchronized live compressor campaign, year: 2026, version: `PTFP-Custom-current-syscall-v1`. citation: Locally captured runtime artifacts, 4-20 mA feature contract and Linux edge syscall traces.

