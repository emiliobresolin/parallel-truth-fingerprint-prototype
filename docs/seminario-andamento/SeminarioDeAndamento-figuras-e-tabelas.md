# Seminário de Andamento — Índice de Figuras e Tabelas

Mapa de cada figura e tabela usada em `SeminarioDeAndamento.md`, com origem e local sugerido no texto.

## Figuras

| Figura | Arquivo / Fonte | Origem | Local sugerido no texto | Observação |
| --- | --- | --- | --- | --- |
| Figura 1 — Ausência de mecanismo independente sensor↔SCADA | `assets/pep-figura-1-problema.png` | Extraída do PEP (`docs/input/...DOCUMENTO_ORIGINAL.pdf`, p. 8) | Seção I (Introdução) | Imagem real inserida |
| Figura 3 — Acesso do Edge ao SCADA via OPC UA | `assets/pep-figura-3-opcua-edge.png` | Extraída do PEP (p. 14) | Seção III (Pilar 4) | Imagem real inserida |
| Figura 4 — Arquitetura proposta (Fonte de Verdade Física Paralela) | `assets/pep-figura-4-arquitetura.png` | Extraída do PEP (p. 20) | Seção III (figura principal) | Imagem real inserida |
| Figura 5 — Fingerprint via LSTM (processamento em nuvem) | `assets/pep-figura-5-lstm.png` | Extraída do PEP (p. 27) | Seção III (Pilar 5) | Imagem real inserida |
| Figura 6 — Pipeline do protótipo atual | `assets/prototype-pipeline.mmd` (inline ```mermaid```) | Gerada nesta entrega | Seção IV | Renderiza no GitHub/visualizador Mermaid |
| Figura 7 — Fluxo dos cenários de validação | `assets/validation-scenarios-flow.mmd` (inline ```mermaid```) | Gerada nesta entrega | Seção V | Renderiza no GitHub/visualizador Mermaid |
| (Auxiliar) Pipeline de fingerprint | `assets/fingerprint-pipeline.mmd` | Gerada nesta entrega | Apoio à Seção VI-C | Não embutida; disponível como fonte |
| (Auxiliar) Matriz de confusão (visual) | `assets/confusion-matrix.md` | Relatório técnico §5.3 | Apoio à Seção VI-C | Tabela visual (PNG não gerado: sem matplotlib/headless browser) |

> Observação sobre PNG/SVG do Mermaid: a exportação automática não foi possível neste ambiente (mermaid-cli requer navegador headless ausente). As Figuras 6 e 7 estão **inline como blocos ```mermaid```** no `.md` e renderizam diretamente no GitHub e em visualizadores Mermaid. Os `.mmd` ficam como fonte editável em `assets/`.

## Tabelas

| Tabela | Fonte (arquivo) | Local sugerido no texto | Observação de proveniência |
| --- | --- | --- | --- |
| Tabela I — Comparação dos trabalhos relacionados | `tables/` (síntese do PEP §6.2) | Seção II | Versão resumida da tabela do PEP |
| Tabela II — Componentes do protótipo | `tables/infrastructure-components.md` | Seção IV | `docker ps` ao vivo 2026-06-23 |
| Tabela III — Cenários de validação | `tables/validation-scenarios.md` | Seção V | 3 execuções ao vivo |
| Tabela IV — Resumo do dataset custom | `tables/custom-dataset-summary.md` | Seção VI-B | Manifest regenerado ao vivo |
| Tabela V — Resultados ADFA-LD binário | `tables/adfa-ld-binary-results.md` | Seção VI-C | Sweep real (`embedding-adfa-ld-binary-sweep.md`) |
| Tabela VI — Matriz de confusão do campeão | `tables/confusion-matrix.md` | Seção VI-C | Relatório técnico §5.3 (run binário não no working tree) |
| Tabela VII — Cronograma | (novo, neste documento) | Seção IX | Marcos relativos M1–M6 |

### Tabelas disponíveis mas não embutidas no corpo (apoio)
| Tabela | Fonte | Uso |
| --- | --- | --- |
| ADFA-LD multiclasse | `tables/adfa-ld-multiclass-results.md` | citada em texto na Seção VI-C (melhor F1=0,5610) |
| ADFA-LD dataset (resumo) | `tables/adfa-ld-dataset-summary.md` | base numérica da Seção VI-C |
| Campeão (resumo do run) | `tables/champion-run-summary.md` | base da Seção VI-C |
| Métricas por classe | `tables/champion-class-metrics.md` | base da Tabela VI |
| Limitações do protótipo | `tables/prototype-limitations.md` | base da Seção VII |
