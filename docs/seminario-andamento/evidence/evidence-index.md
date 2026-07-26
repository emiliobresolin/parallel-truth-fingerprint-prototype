# Índice de Evidências — Seminário de Andamento

> Gerado em 2026-06-23. **Forte** = evidência ao vivo/quantitativa reproduzível nesta sessão.
> **Parcial** = real, mas com ressalva de domínio/proveniência. **Pendente** = não executado/ausente.
> Provenância padrão dos cenários e MinIO: execução **ao vivo 2026-06-23** contra a stack real
> (3× CometBFT v0.39.0 + 3× ABCI Go + MQTT + MinIO em containers locais), pelo caminho oficial
> `scripts/run_local_demo.py` (sem bypass).

## A. Mapa e índice
| Artefato | Caminho | Como foi gerado | Seção do Seminário | Confiabilidade | Força |
| --- | --- | --- | --- | --- | --- |
| Mapa do projeto | `evidence/project-map.md` | inspeção do repo + README | Implementação / Protótipo | alta | Forte |
| Este índice | `evidence/evidence-index.md` | enumeração da pasta | (apoio) | alta | Forte |

## B. Cenários de validação (ao vivo) — Parte 2
Comando exato por cenário em `evidence/scenarios/<cenario>/command.txt`.
| Artefato | Caminho | Seção do Seminário | Confiabilidade | Força |
| --- | --- | --- | --- | --- |
| normal — resumo | `evidence/scenarios/normal/scenario-summary.md` | Resultados: pipeline completo | ao vivo; consenso success + persistência | Forte |
| normal — terminal | `evidence/scenarios/normal/terminal-output.txt` | Resultados | saída bruta do runtime | Forte |
| normal — consenso | `evidence/scenarios/normal/consensus-payload.(pretty.json\|txt)` | Arquitetura: consenso BFT | tx_hash/height reais | Forte |
| normal — SCADA | `evidence/scenarios/normal/scada-comparison.(pretty.json\|txt)` | Comparação físico-lógica | match nos 3 sensores | Forte |
| normal — MinIO | `evidence/scenarios/normal/minio-artifact.(pretty.json\|txt)` | Persistência | objeto persistido real | Forte |
| quorum_loss — resumo/consenso | `evidence/scenarios/quorum_loss/*` | Consenso bizantino / quórum | 3 edges excluídos, downstream bloqueado | Forte |
| quorum_loss — ausências | `evidence/scenarios/quorum_loss/missing-artifact.txt` | Consenso bizantino | explica bucket não criado | Forte |
| scada_divergence — resumo/consenso/SCADA | `evidence/scenarios/scada_divergence/*` | Comparação físico-lógica | divergência nos 3 sensores, bloqueio | Forte |
| scada_divergence — ausências | `evidence/scenarios/scada_divergence/missing-artifact.txt` | Comparação físico-lógica | explica bloqueio de persistência | Forte |

## C. MinIO (ao vivo) — Parte 3
| Artefato | Caminho | Seção do Seminário | Confiabilidade | Força |
| --- | --- | --- | --- | --- |
| Listagem dos buckets | `evidence/minio/minio-listing.txt` | Persistência / Arquitetura | ao vivo (`list_objects`) | Forte |
| Resumo dos artefatos | `evidence/minio/minio-artifacts-summary.md` | Persistência | classificação dos objetos | Forte |
| Amostra consenso válido | `evidence/minio/sample-valid-consensus-artifact.(pretty.json\|txt)` | Persistência | objeto real do bucket | Forte |
| Amostra comparação SCADA | `evidence/minio/sample-scada-comparison.(pretty.json\|txt)` | Comparação físico-lógica | extraído do artefato real | Forte |

## D. Dataset custom / físico-operacional — Parte 5
| Artefato | Caminho | Seção do Seminário | Confiabilidade | Força |
| --- | --- | --- | --- | --- |
| Análise do dataset custom | `evidence/custom-dataset/custom-dataset-analysis.md` | Dataset / fingerprint (integração) | regenerado ao vivo | Forte (integração) |
| Manifest live | `evidence/custom-dataset/live-custom-dataset.manifest.pretty.json` | Dataset / fingerprint | manifest real (13 janelas, 27 feats) | Forte |
| Tensores live | `evidence/custom-dataset/live-custom-dataset.windows.npz` | Dataset / fingerprint | npz real [13,2,27] | Forte |
| Inspeção npz/adequação | `evidence/custom-dataset/_npz-inspection.json` | Limitações | adequacy_met=false | Forte |

> Ressalva: dataset **normal-only**, sem rótulo de ataque, abaixo do piso de adequação → **não** suporta métrica supervisionada. O `fingerprint-datasets.zip` do relatório **não está** no working tree (regenerado aqui).

## E. ADFA-LD e fingerprint supervisionado — Parte 6 + tabelas (Parte 4)
| Artefato | Caminho | Seção do Seminário | Confiabilidade | Força |
| --- | --- | --- | --- | --- |
| Análise ADFA-LD | `evidence/adfa-ld/adfa-ld-analysis.md` | Resultados: fingerprint | sweeps reais + relatório | Forte (com ressalva de domínio) |
| Sweep binário | `tables/adfa-ld-binary-results.(md\|csv)` | Resultados | `embedding-adfa-ld-binary-sweep.md` | Forte |
| Sweep multiclasse | `tables/adfa-ld-multiclass-results.(md\|csv)` | Resultados (complementar) | `…multiclass-sweep.md` | Parcial (não passa D6) |
| Dataset ADFA-LD | `tables/adfa-ld-dataset-summary.(md\|csv)` | Metodologia/dados | relatório §5.2 | Forte |
| Campeão | `tables/champion-run-summary.(md\|csv)` | Resultados | relatório §5.3/§6 | Forte* |
| Métricas por classe | `tables/champion-class-metrics.(md\|csv)` | Resultados | relatório §5.3 | Forte* |
| Matriz de confusão | `tables/confusion-matrix.(md\|csv)` + `assets/confusion-matrix.md` | Resultados | relatório §5.3 | Forte* |

> *Números do campeão binário vêm do relatório técnico (`docs/results-of-the-prototype.md`); o JSON do run binário **não** está no working tree (foi persistido no MinIO durante o sweep de 2026-06-02). Os runs presentes em `_bmad-output/local-store` são os multiclasse de 2026-05-21.

## F. Inferência online — Parte 7
| Artefato | Caminho | Seção do Seminário | Confiabilidade | Força |
| --- | --- | --- | --- | --- |
| Resumo inferência online | `evidence/online-inference/online-inference-summary.md` | Reintegração / fingerprint | ao vivo 2026-06-23 | Forte (integração) |
| Saída bruta | `evidence/online-inference/online-inference-output.txt` | Reintegração | terminal real | Forte |
| Resultado JSON | `evidence/online-inference/online-inference-output.pretty.json` | Reintegração | classe prevista=Normal | Forte |
| Comando | `evidence/online-inference/online-inference-command.txt` | Reprodutibilidade | — | Forte |

> Ressalva: o modelo promovido **local** é o GRU **multiclasse** de 2026-05-21, **não** o campeão binário de 2026-06-02; e a carga **re-treina** (gap G3). Prova a integração do canal online, não a métrica acadêmica.

## G. Tabelas de contexto — Parte 4
| Artefato | Caminho | Seção do Seminário | Confiabilidade | Força |
| --- | --- | --- | --- | --- |
| Componentes de infraestrutura | `tables/infrastructure-components.(md\|csv)` | Implementação | `docker ps` ao vivo | Forte |
| Cenários de validação | `tables/validation-scenarios.(md\|csv)` | Resultados | 3 runs ao vivo | Forte |
| Dataset custom (resumo) | `tables/custom-dataset-summary.(md\|csv)` | Dataset | manifest live | Forte |
| Limitações | `tables/prototype-limitations.(md\|csv)` | Limitações / próximos passos | relatório + sessão | Forte |

## H. Figuras auxiliares — Parte 8
| Artefato | Caminho | Seção do Seminário | Confiabilidade | Força |
| --- | --- | --- | --- | --- |
| Pipeline do protótipo (Mermaid) | `assets/prototype-pipeline.mmd` | Arquitetura | diagrama | Forte |
| Fluxo dos cenários (Mermaid) | `assets/validation-scenarios-flow.mmd` | Resultados | diagrama | Forte |
| Pipeline de fingerprint (Mermaid) | `assets/fingerprint-pipeline.mmd` | Fingerprint | diagrama | Forte |
| Matriz de confusão (tabela visual) | `assets/confusion-matrix.md` | Resultados | relatório §5.3 | Forte* |

> Export PNG/SVG do Mermaid **não foi possível** nesta sessão (mermaid-cli requer navegador headless, ausente). Os `.mmd` renderizam em qualquer visualizador Mermaid / GitHub.

## Pendências (não cobertas como evidência forte nesta entrega)
- **replay/freeze**: cenário previsto, sem captura bruta estável nesta sessão (Pendente).
- **single_edge_exclusion**: existe no runtime, não executado como resultado principal (Pendente).
- **Test suite**: não executada/anexada nesta sessão (Pendente).
- **Campeão binário no runtime local / pesos persistidos**: ponteiro local aponta para o GRU multiclasse; re-fit na carga (Parcial).
- **Dataset físico-operacional rotulado**: ainda a construir (ver custom-dataset-analysis §12).
