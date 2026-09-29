# Conjunto customizado de corrente e syscalls: nota para a tese

## O que aconteceu com esses dados

O conjunto customizado existe e foi preservado. Ele não aparece na tabela principal da Matriz V2 porque a Matriz V2 foi congelada para três bases públicas: ADFA-LD, HAI 23.05 e LID-DS 2021. Essa decisão separou dois tipos de resultado: a comparação quantitativa entre benchmarks públicos e a evidência de integração do protótipo físico-operacional.

Não houve perda de arquivo. Há quatro campanhas próprias em `evidence/custom-dataset/`, com 17 linhas no total. Cada linha liga, pelo mesmo `round_id`, três coisas reais produzidas pelo protótipo: o vetor de medidas de corrente, os tokens de chamadas de sistema capturados no edge e, quando ele existe, o resultado do autoencoder em execução.

O nome correto para esse material é **autoencoder de corrente com rastros de syscall correlacionados**. Não é correto chamá-lo de modelo de fusão autoencoder mais syscall, porque os tokens de syscall foram guardados como rastros associados à mesma rodada, mas não foram usados como entrada do tensor do autoencoder. O autoencoder calculou o erro de reconstrução sobre as medidas de corrente.

## Números que podem ser apresentados

| Item | Resultado observado |
| --- | ---: |
| Campanhas próprias preservadas | 4 |
| Linhas sincronizadas de corrente e syscall | 17 |
| Linhas do cenário normal | 13 |
| Linhas de exclusão de edge | 4 |
| Linhas com saída persistida do autoencoder | 2 |
| Classificações anômalas do autoencoder | 0 |
| Linhas com sinalizador físico de falha, saturação ou partida fria | 0 |

As duas saídas do autoencoder pertencem à campanha V3. A linha `edgefault` teve escore `12,7424`, limiar `41,7693` e classificação normal. A linha normal teve escore `27,0096`, o mesmo limiar e também classificação normal. Esses valores mostram que a inferência do autoencoder foi executada e preservada, mas não representam 17 medições independentes do modelo.

O cenário `faulty_edge_exclusion` é uma condição de disponibilidade ou exclusão de edge. Ele não recebeu automaticamente o rótulo de anomalia física, pois os vetores físicos preservados não têm sinalizador de mau funcionamento, saturação ou partida fria. Portanto, transformar essas quatro linhas em ataques físicos para gerar uma métrica seria alterar o significado dos dados.

## Como usar na tese

O conjunto customizado deve aparecer em uma subseção própria, depois da apresentação da Matriz V2. A tabela acima comprova que o protótipo reuniu corrente, syscall e resultado do modelo no mesmo fluxo de execução. A comparação de AUROC, AUPRC, F1 e demais métricas fica restrita a ADFA-LD, HAI 23.05 e LID-DS 2021, pois são as três bases que possuem o desenho completo de avaliação da Matriz V2.

Texto pronto para a tese:

> Além dos benchmarks públicos, o protótipo registrou quatro campanhas próprias com 17 linhas sincronizadas. Cada linha preserva o vetor de corrente, os rastros de chamadas de sistema do edge e a associação com a rodada de execução. O autoencoder de corrente foi habilitado e duas inferências foram persistidas, ambas classificadas como normais. Esse resultado comprova o caminho de integração entre a coleta física, a captura de syscalls e a inferência. Como os rastros de syscall são correlacionados à rodada, mas não são a entrada do autoencoder, esse material é apresentado como resultado de integração e não como uma quarta comparação numérica junto aos benchmarks públicos.

## Rastreabilidade

- Escopo congelado da Matriz V2: `configs/experiments/thesis-evaluation-v2.frozen-v6.json`.
- Auditoria consolidada das quatro campanhas: `evidence/academic/thesis-evaluation-v2/73c6eadb15c3c35a/reports/pilot-custom-track-readiness.json`.
- Linhas brutas sincronizadas: `evidence/custom-dataset/*/current-syscall-windows.jsonl`.
- Estrutura que associa corrente, syscalls e resultado por rodada: `src/parallel_truth_fingerprint/evidence/custom_campaign.py`.
- Cálculo de erro de reconstrução do autoencoder: `src/parallel_truth_fingerprint/lstm_service/inference.py`.
- Registro legado de duas linhas, mantido apenas para rastreabilidade: `evidence/reports/cross-benchmark-comparison.md`.

Nenhuma linha ausente foi preenchida e nenhum rótulo foi alterado. Assim, a seção mostra exatamente o que o protótipo produziu e mantém separadas a evidência de integração e as métricas estatísticas da Matriz V2.
