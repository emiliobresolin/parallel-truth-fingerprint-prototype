# MinIO - resumo dos artefatos (LIVE 2026-06-23)

Endpoint: `localhost:9000` (container `ptfp-minio`). Acesso: `minioadmin/minioadmin`.

## Buckets existentes apos as execucoes ao vivo

| bucket | objetos | conteudo |
| --- | ---: | --- |
| `sem-normal` | 16 | consenso valido, dataset de fingerprint |

> Os cenarios `quorum_loss` e `scada_divergence` **nao criaram bucket** porque a persistencia foi bloqueada a montante (sem quorum / divergencia SCADA). Isso e a evidencia direta de que apenas estado validado chega ao armazenamento.

## Classificacao dos artefatos

- **Consenso (`valid-consensus-artifacts/`)** - registro pos-consenso/pos-SCADA de cada ciclo valido. Amostra legivel: `sample-valid-consensus-artifact.(pretty.json|txt)`.
- **SCADA** - embutido em cada artefato de consenso, campo `scada_context.comparison_output`. Amostra: `sample-scada-comparison.(pretty.json|txt)`.
- **Dataset de fingerprint (`fingerprint-datasets/`)** - manifest `.manifest.json` + tensores `.windows.npz`, derivados dos artefatos validos. Gerado ao vivo nesta sessao a partir do bucket `sem-normal`.

## Uso no Seminario de Andamento

- Pilar de persistencia/descentralizacao -> `sample-valid-consensus-artifact.*` + `minio-listing.txt`.
- Pilar de comparacao fisico-logica -> `sample-scada-comparison.*` (e os cenarios).
- Pilar de dataset/fingerprint (integracao) -> `custom-dataset/live-custom-dataset.manifest.pretty.json`.
