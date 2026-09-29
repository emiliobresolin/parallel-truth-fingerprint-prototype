# Matriz V2 — resultados disponíveis na data de corte

Gerado em UTC: `2026-09-29T11:49:45.865766Z`  
Fonte dos dados: `evidence/academic/thesis-evaluation-v2/73c6eadb15c3c35a/pilot`  
Configuração: `sha256:73c6eadb15c3c35ac3dcbfa3b4ffa5df596914481746e01b351306b6dd93f6e7`

## Decisão de corte e escopo

Este pacote fecha a coleta de resultados para a redação da tese na data indicada acima. Ele utiliza somente os **23 registros completos, autenticados e verificados** do corpus V6. Todos os registros têm origem `official_native`, validação de separação entre grupos aprovada e teste cego preservado: o limiar foi definido na validação antes da pontuação do teste.

As tabelas não estimam, preenchem nem misturam execuções ausentes. Há `5` artefato(s) de uma execução interrompida fora deste conjunto; eles não são usados aqui. Assim, cada número abaixo pode ser rastreado a um arquivo de célula e à sua soma SHA-256 no manifesto.

## Base estatística da tese

Este corpus é a base estatística empírica da tese: os números são medições observadas nas execuções concluídas, não projeções. O autoencoder recorrente possui cinco repetições por base; para cada métrica, o relatório calcula média, desvio padrão e IC95% t de Student usando as sementes efetivamente executadas. As métricas de cada célula foram calculadas no teste mantido separado, depois que o limiar já estava congelado pela validação. Além disso, os artefatos de célula preservam reamostragem por unidade de teste com 2.000 repetições nas condições em que a unidade independente qualifica para esse cálculo.

Em outras palavras, a tese pode afirmar que apresenta **resultados estatísticos da Matriz V2 até a data de corte**. A inferência é sempre vinculada ao tamanho amostral executado: `n=5` para o autoencoder recorrente em cada base e `n=1` para cada método determinístico. A ausência de p-valor entre alguns métodos determinísticos não elimina as estatísticas existentes; ela apenas define que a comparação entre esses métodos deve permanecer descritiva.

## Desenho efetivamente executado

- Bases: ADFA-LD, HAI 23.05 e LID-DS 2021.
- Modelos: unigrama categórico quando aplicável, autoencoder PCA, distância robusta e autoencoder recorrente.
- Autoencoder recorrente: cinco execuções independentes por base, com sementes `101, 211, 307, 419, 523`.
- Modelos determinísticos: uma execução autenticada por combinação base/modelo.
- Métrica principal: AUROC. AUPRC, acurácia balanceada, F1, MCC, FPR e FNR complementam a leitura.

## Suporte de teste

| Base | Normais no teste | Ataques no teste | Total |
| --- | --- | --- | --- |
| ADFA-LD | 100 | 150 | 250 |
| HAI 23.05 | 759 | 41 | 800 |
| LID-DS 2021 | 90 | 90 | 180 |

## Tabela principal de resultados

| Base | Modelo | Execuções | AUROC | AUPRC | Acurácia balanceada | F1 | MCC | FPR média | FNR média |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ADFA-LD | Unigrama categórico | 1 | 0.5651 | 0.6730 | 0.5300 | 0.1463 | 0.1278 | 0.0200 | 0.9200 |
| ADFA-LD | Autoencoder PCA | 1 | 0.5161 | 0.5885 | 0.4900 | — | -0.1100 | 0.0200 | 1.0000 |
| ADFA-LD | Distância robusta | 1 | 0.4129 | 0.5183 | 0.4950 | — | -0.0776 | 0.0100 | 1.0000 |
| ADFA-LD | Autoencoder recorrente | 5 | 0.5575 [0.5455; 0.5694] | 0.6594 [0.6536; 0.6652] | 0.5193 [0.5090; 0.5296] | 0.1486 [0.1387; 0.1585] | 0.0782 [0.0330; 0.1234] | 0.0440 | 0.9173 |
| HAI 23.05 | Autoencoder PCA | 1 | 0.7677 | 0.3072 | 0.6371 | 0.3582 | 0.3410 | 0.0184 | 0.7073 |
| HAI 23.05 | Distância robusta | 1 | 0.7145 | 0.2942 | 0.6078 | 0.3396 | 0.3910 | 0.0040 | 0.7805 |
| HAI 23.05 | Autoencoder recorrente | 5 | 0.7225 [0.7158; 0.7292] | 0.3372 [0.3324; 0.3419] | 0.6543 [0.6496; 0.6589] | 0.3513 [0.3220; 0.3807] | 0.3181 [0.2837; 0.3525] | 0.0329 | 0.6585 |
| LID-DS 2021 | Unigrama categórico | 1 | 0.5693 | 0.5950 | 0.5056 | 0.0220 | 0.0747 | 0.0000 | 0.9889 |
| LID-DS 2021 | Autoencoder PCA | 1 | 0.6359 | 0.6748 | 0.5056 | 0.0220 | 0.0747 | 0.0000 | 0.9889 |
| LID-DS 2021 | Distância robusta | 1 | 0.6191 | 0.6620 | 0.5278 | 0.1053 | 0.1690 | 0.0000 | 0.9444 |
| LID-DS 2021 | Autoencoder recorrente | 5 | 0.5438 [0.5171; 0.5705] | 0.5602 [0.5357; 0.5847] | 0.5044 [0.4987; 0.5102] | 0.0291 [-0.0017; 0.0600] (n=3) | 0.0852 [0.0403; 0.1300] (n=3) | 0.0000 | 0.9911 |

**Leitura da tabela:** valores entre colchetes são IC95% calculados entre as sementes do autoencoder recorrente. Valores sem colchetes vêm de uma execução determinística. Quando uma métrica não é definida em alguma semente, a tabela informa o `n` efetivamente usado para ela. FPR e FNR são médias para manter a tabela legível; os valores por semente estão na tabela seguinte. Esses formatos não devem ser confundidos: os intervalos entre sementes descrevem variação de treinamento; os arquivos de célula também preservam intervalos por unidade de teste.

## Estatísticas de repetição do autoencoder recorrente

| Base | n | AUROC média ± DP | IC95% AUROC | AUPRC média ± DP | Acurácia balanceada média ± DP | F1 média ± DP |
| --- | --- | --- | --- | --- | --- | --- |
| ADFA-LD | 5 | 0.5575 ± 0.0096 | 0.5575 [0.5455; 0.5694] | 0.6594 ± 0.0047 | 0.5193 ± 0.0083 | 0.1486 ± 0.0080 |
| HAI 23.05 | 5 | 0.7225 ± 0.0054 | 0.7225 [0.7158; 0.7292] | 0.3372 ± 0.0038 | 0.6543 ± 0.0037 | 0.3513 ± 0.0236 |
| LID-DS 2021 | 5 | 0.5438 ± 0.0215 | 0.5438 [0.5171; 0.5705] | 0.5602 ± 0.0197 | 0.5044 ± 0.0046 | 0.0291 ± 0.0124 (n=3) |

Esta tabela mostra a estatística calculada diretamente das repetições concluídas. Média, desvio padrão e IC95% usam as sementes que foram efetivamente executadas em cada base.

## Resultado do autoencoder recorrente por semente

| Base | Semente | AUROC | AUPRC | Acurácia balanceada | F1 | FPR | FNR | Épocas |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ADFA-LD | 101 | 0.5617 | 0.6570 | 0.5150 | 0.1437 | 0.0500 | 0.9200 | 12 |
| ADFA-LD | 211 | 0.5474 | 0.6532 | 0.5250 | 0.1455 | 0.0300 | 0.9200 | 12 |
| ADFA-LD | 307 | 0.5702 | 0.6646 | 0.5067 | 0.1628 | 0.0800 | 0.9067 | 12 |
| ADFA-LD | 419 | 0.5483 | 0.6634 | 0.5250 | 0.1455 | 0.0300 | 0.9200 | 12 |
| ADFA-LD | 523 | 0.5599 | 0.6590 | 0.5250 | 0.1455 | 0.0300 | 0.9200 | 12 |
| HAI 23.05 | 101 | 0.7259 | 0.3345 | 0.6562 | 0.3636 | 0.0290 | 0.6585 | 12 |
| HAI 23.05 | 211 | 0.7143 | 0.3403 | 0.6529 | 0.3415 | 0.0356 | 0.6585 | 12 |
| HAI 23.05 | 307 | 0.7270 | 0.3359 | 0.6576 | 0.3733 | 0.0264 | 0.6585 | 12 |
| HAI 23.05 | 419 | 0.7257 | 0.3331 | 0.6562 | 0.3636 | 0.0290 | 0.6585 | 12 |
| HAI 23.05 | 523 | 0.7197 | 0.3420 | 0.6483 | 0.3146 | 0.0448 | 0.6585 | 12 |
| LID-DS 2021 | 101 | 0.5577 | 0.5722 | 0.5000 | — | 0.0000 | 1.0000 | 12 |
| LID-DS 2021 | 211 | 0.5135 | 0.5317 | 0.5000 | — | 0.0000 | 1.0000 | 12 |
| LID-DS 2021 | 307 | 0.5696 | 0.5842 | 0.5056 | 0.0220 | 0.0000 | 0.9889 | 12 |
| LID-DS 2021 | 419 | 0.5431 | 0.5573 | 0.5111 | 0.0435 | 0.0000 | 0.9778 | 12 |
| LID-DS 2021 | 523 | 0.5353 | 0.5557 | 0.5056 | 0.0220 | 0.0000 | 0.9889 | 12 |

## Diferenças descritivas de AUROC

| Base | Comparação | Diferença de AUROC | Leitura |
| --- | --- | --- | --- |
| ADFA-LD | Unigrama categórico vs. Autoencoder recorrente | 0.0076 | diferença descritiva; sem p-valor |
| ADFA-LD | Autoencoder PCA vs. Autoencoder recorrente | -0.0414 | diferença descritiva; sem p-valor |
| ADFA-LD | Autoencoder recorrente vs. Distância robusta | 0.1446 | diferença descritiva; sem p-valor |
| HAI 23.05 | Autoencoder PCA vs. Autoencoder recorrente | 0.0452 | diferença descritiva; sem p-valor |
| HAI 23.05 | Autoencoder recorrente vs. Distância robusta | 0.0080 | diferença descritiva; sem p-valor |
| LID-DS 2021 | Unigrama categórico vs. Autoencoder recorrente | 0.0255 | diferença descritiva; sem p-valor |
| LID-DS 2021 | Autoencoder PCA vs. Autoencoder recorrente | 0.0920 | diferença descritiva; sem p-valor |
| LID-DS 2021 | Autoencoder recorrente vs. Distância robusta | -0.0753 | diferença descritiva; sem p-valor |

Estas diferenças mostram o que foi observado no conjunto executado. Não há p-valor nesta tabela porque as comparações incluem modelos determinísticos com uma única execução e, portanto, não formam pares estocásticos repetidos equivalentes.

## Limites que precisam aparecer na tese

- Os intervalos do autoencoder recorrente medem apenas a variação entre sementes. Eles não substituem o intervalo calculado pelas unidades de teste de cada célula.
- Em HAI 23.05, os blocos temporais não sobrepostos foram preservados, mas há somente duas gravações-fonte; por isso não há intervalo por agrupamento de gravações nessa base.
- F1 pode ficar indefinido quando uma execução não produz verdadeiro positivo; o símbolo `—` preserva essa informação e não deve ser trocado por zero.
- Como o intervalo t entre sementes não é limitado ao intervalo matemático da métrica, uma extremidade pode ultrapassar 0 ou 1. Os valores são mantidos sem recorte para não alterar o cálculo original.

## Texto curto para a seção de resultados da tese

> A Matriz V2 reuniu 23 execuções completas nas bases ADFA-LD, HAI 23.05 e LID-DS 2021. O autoencoder recorrente foi executado cinco vezes por base, com sementes previamente registradas, enquanto os métodos determinísticos foram ajustados uma vez por combinação. A métrica principal foi AUROC, calculada no conjunto de teste após o congelamento do limiar com dados de validação.

> Nos resultados disponíveis na data de corte, o autoencoder recorrente apresentou AUROC médio de 0.5575 no ADFA-LD (IC95% 0.5455–0.5694), 0.7225 no HAI 23.05 (IC95% 0.7158–0.7292) e 0.5438 no LID-DS 2021 (IC95% 0.5171–0.5705). A tabela principal apresenta também AUPRC, acurácia balanceada, F1, MCC e as taxas de falso positivo e falso negativo para permitir a leitura conjunta de ordenação e operação no limiar calibrado.

> Os resultados devem ser interpretados no escopo das bases, das divisões e dos modelos efetivamente executados. As comparações com métodos determinísticos são apresentadas como diferenças descritivas, pois cada um deles possui uma única execução autenticada. Não se devem atribuir a este conjunto resultados de execuções que não foram concluídas.

## Nota de custo computacional

O corpus reportado consumiu `4.3615` CPU-h e `5.1265` horas de relógio na execução que o produziu. Esse valor é apenas contexto de processamento; não é uma métrica de qualidade do detector.

## Reprodutibilidade

Execute:

```powershell
 .venv\Scripts\python.exe scripts\build_thesis_result_cutoff.py
```

O comando relê as células-fonte, verifica inventário, estado, configuração, origem, separação de grupos e teste cego antes de reescrever as tabelas derivadas.
