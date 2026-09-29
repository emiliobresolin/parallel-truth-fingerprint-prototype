# Resultados do Piloto V4 para a Tese

## Status e uso permitido

Este é o piloto exploratório da Matrix V2/V4, executado com a configuração
congelada V4. Ele contém 23 das 23 células planejadas e não reteve falhas.
Os resultados servem para a seção de resultados preliminares, análise de
viabilidade e discussão metodológica. Eles não são resultados confirmatórios,
não sustentam uma escolha de "melhor" modelo e não substituem a matriz
confirmatória pré-registrada.

O LID-DS-2021 usa a seleção V4 corrigida: cópias de conteúdo são excluídas
entre fases e dentro da fase, entradas do modelo iguais em offsets distintos
são reconhecidas, e conteúdo igual com semântica de rótulo contraditória falha
fechado.

## Proveniência

- Configuração congelada: `configs/experiments/thesis-evaluation-v2.frozen-v4.json`
- Identidade da configuração: `sha256:23aa81cfb426dc4eb4d37b55c99a640d0bd7d93230d2b44dadb35b849b5782dd`
- Prévia do piloto: `evidence/academic/thesis-evaluation-v2/23aa81cfb426dc4e/pilot/preflight.json`
- Resumo autenticado: `evidence/academic/thesis-evaluation-v2/23aa81cfb426dc4e/pilot/run-summary.json`
- Células concluídas: 23/23; falhas: 0
- Custo de geração de evidência: 17 153,52 s de CPU (4,76 CPU-h)

## Suporte do piloto V4

| Base | Treino normal | Validação normal | Teste normal | Teste ataque |
|---|---:|---:|---:|---:|
| ADFA-LD | 250 | 100 | 100 | 150 |
| HAI-23.05 | 360 | 120 | 759 | 41 |
| LID-DS-2021 | 90 | 90 | 90 | 90 |

No LID-DS-2021, os 90 registros de treino, 90 de validação e 90 de cada
tipo de teste correspondem aos caps planejados (15 cenários x 6 registros por
papel), depois da exclusão e reposição de cópias de conteúdo.

## Métricas do piloto

Cada valor é a média da célula/execução disponível. Os modelos determinísticos
têm uma única execução; o autoencoder recorrente tem cinco sementes. `NA`
significa métrica indefinida para aquela célula.

| Base | Modelo | Ensaios | AUROC | AUPRC | Acurácia balanceada | F1 | MCC |
|---|---|---:|---:|---:|---:|---:|---:|
| ADFA-LD | Categorical unigram | 1 | 0,565 | 0,673 | 0,530 | 0,146 | 0,128 |
| ADFA-LD | PCA autoencoder | 1 | 0,516 | 0,589 | 0,490 | NA | -0,110 |
| ADFA-LD | Recurrent autoencoder | 5 | 0,557 | 0,659 | 0,519 | 0,149 | 0,078 |
| ADFA-LD | Robust distance | 1 | 0,413 | 0,518 | 0,495 | NA | -0,078 |
| HAI-23.05 | PCA autoencoder | 1 | 0,768 | 0,307 | 0,637 | 0,358 | 0,341 |
| HAI-23.05 | Recurrent autoencoder | 5 | 0,722 | 0,337 | 0,654 | 0,351 | 0,318 |
| HAI-23.05 | Robust distance | 1 | 0,715 | 0,294 | 0,608 | 0,340 | 0,391 |
| LID-DS-2021 | Categorical unigram | 1 | 0,569 | 0,595 | 0,506 | 0,022 | 0,075 |
| LID-DS-2021 | PCA autoencoder | 1 | 0,636 | 0,675 | 0,506 | 0,022 | 0,075 |
| LID-DS-2021 | Recurrent autoencoder | 5 | 0,544 | 0,560 | 0,504 | 0,029 | 0,085 |
| LID-DS-2021 | Robust distance | 1 | 0,619 | 0,662 | 0,528 | 0,105 | 0,169 |

## Variabilidade do modelo recorrente

| Base | AUROC médio | DP | IC 95% do piloto |
|---|---:|---:|---:|
| ADFA-LD | 0,557 | 0,010 | [0,546; 0,569] |
| HAI-23.05 | 0,722 | 0,005 | [0,716; 0,729] |
| LID-DS-2021 | 0,544 | 0,022 | [0,517; 0,571] |

## Formulação recomendada para a tese

> No piloto V4, composto por 23 células autenticadas e sem falhas, os
> desempenhos variaram substancialmente entre as bases. Em HAI-23.05, o PCA
> autoencoder apresentou AUROC de 0,768, enquanto o autoencoder recorrente
> obteve AUROC médio de 0,722 em cinco sementes. Em ADFA-LD e LID-DS-2021, os
> valores de AUROC permaneceram próximos de 0,5--0,6. Esses resultados são
> apresentados como evidência exploratória: a matriz confirmatória completa,
> com 50 sementes para os modelos estocásticos, permanece necessária para
> inferência, comparação e qualquer alegação de desempenho definitivo.
