<!-- Manifest real: evidence/custom-dataset/live-custom-dataset.manifest.pretty.json; tensores: live-custom-dataset.windows.npz (shape [13,2,27]). -->
| arquivo_dataset | origem | amostras_ou_janelas | sequence_length | stride | features | labels_disponiveis | uso_atual | limitacao |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fingerprint-datasets/training-dataset::...::seq-2 (gerado ao vivo) | bucket MinIO sem-normal (valid-consensus-artifacts) | 13 janelas (de 14 artefatos elegiveis) | 2 | 1 | 27 (9 por sensor x 3 sensores) | apenas 'normal' | demonstracao de integracao do pipeline (autoencoder/runtime) | normal-only, sem rotulo de ataque, abaixo do piso de adequacao (30 elegiveis/20 janelas); validation_level=runtime_valid_only |

> Manifest real: evidence/custom-dataset/live-custom-dataset.manifest.pretty.json; tensores: live-custom-dataset.windows.npz (shape [13,2,27]).
