# Resultados da Matriz V2 para a tese

Use este documento junto com o relatório derivado em `evidence/academic/thesis-evaluation-v2/73c6eadb15c3c35a/reports/matrix-v2-resultados-data-de-corte.md`. O texto foi fechado a partir de 23 resultados completos disponíveis na data de corte; não incorpora valores previstos ou execuções interrompidas.

## Como apresentar o conjunto de dados

1. Diga que a Matriz V2 avaliou ADFA-LD, HAI 23.05 e LID-DS 2021.
2. Informe que o autoencoder recorrente foi repetido em cinco sementes e que os métodos determinísticos têm uma execução autenticada por combinação.
3. Defina AUROC como métrica principal e apresente AUPRC, acurácia balanceada, F1, MCC, FPR e FNR como métricas complementares.
4. Explique que a calibração do limiar ocorreu na validação e que o conjunto de teste foi pontuado somente depois disso.
5. Trate as diferenças que envolvem métodos de uma única execução como descritivas; não use p-valores inexistentes.
6. Em HAI 23.05, não apresente intervalo por agrupamento de gravações: há duas gravações-fonte, menos que o mínimo de cinco exigido para esse cálculo.

## Frase-base para metodologia

> Os resultados foram obtidos a partir de células autenticadas da Matriz V2. Para cada célula, o processamento foi ajustado com dados de treinamento, o limiar foi definido exclusivamente na validação e as métricas foram calculadas no teste mantido separado. O autoencoder recorrente foi repetido em cinco sementes fixas; os métodos determinísticos foram executados uma vez por combinação base/modelo.

## Frase-base para resultados

> A análise utilizou 23 execuções completas. A tabela de resultados apresenta, por base e modelo, AUROC, AUPRC, acurácia balanceada, F1, MCC, FPR e FNR. Para o autoencoder recorrente, os intervalos de 95% representam a variação observada entre as cinco sementes. Para modelos determinísticos, a tabela mostra o valor da execução autenticada.

## Frase-base para a base estatística

> Os resultados estatísticos da Matriz V2 foram calculados a partir de 23 execuções completas. Em cada base, o autoencoder recorrente foi repetido com cinco sementes fixas, permitindo estimar média, desvio padrão e intervalo de confiança de 95% entre sementes. As métricas foram obtidas no conjunto de teste separado após a calibração do limiar na validação; portanto, os valores apresentados correspondem às medições realizadas pelo experimento.

## Regra simples para não errar na redação

Escreva apenas o que a tabela mostra. Não complete células ausentes por média, não transforme diferenças descritivas em significância estatística e não apresente o custo de CPU como resultado de desempenho.

## Conjunto customizado de corrente e syscalls

O conjunto próprio do protótipo existe, mas é uma trilha de integração separada da Matriz V2. Ele reúne quatro campanhas e 17 linhas que associam, pelo mesmo `round_id`, medidas de corrente, rastros reais de syscall e a saída disponível do autoencoder. A Matriz V2 foi congelada para ADFA-LD, HAI 23.05 e LID-DS 2021; por isso, a tabela comparativa continua restrita a essas três bases.

Use a nota [conjunto customizado de corrente e syscalls](conjunto-customizado-autoencoder-syscalls-para-tese.md) para apresentar os números e a explicação técnica. O nome correto é **autoencoder de corrente com rastros de syscall correlacionados**: os syscalls foram preservados junto da rodada, mas não foram usados como entrada do autoencoder. Essa distinção evita afirmar uma fusão de dados que não foi executada.
