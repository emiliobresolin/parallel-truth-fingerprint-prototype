# Relatório breve: resultados atuais da Matrix V2 (protocolo V4)

## A ideia em palavras bem simples

Imagine que cada base de dados é uma caixa com exemplos normais e exemplos de ataque. O protótipo olha para cada exemplo, calcula uma pontuação de suspeita e tenta separar os dois grupos. Quanto melhor ele separa, melhores são os números.

Já existe um **piloto V4 completo**: 23 de 23 células executadas, sem falhas, consumindo aproximadamente **4,76 CPU-h**. Ele é suficiente para começar a redigir a tese como resultado **exploratório**. Exploratório quer dizer: é um ensaio controlado e reproduzível, mas ainda não é a rodada final de confirmação estatística.

## Os números principais do piloto

| Base | Variante com melhor AUROC no piloto | AUROC | AUPRC | Acurácia balanceada | Leitura simples |
| --- | --- | ---: | ---: | ---: | --- |
| ADFA | unigram | 0,565 | 0,673 | 0,530 | Separação fraca, só um pouco melhor que uma escolha aleatória. |
| HAI | PCA | 0,768 | 0,307 | 0,637 | Melhor resultado do piloto: há uma separação útil entre normal e ataque. |
| LID | PCA | 0,636 | 0,675 | 0,506 | O ranking de anomalias melhora, mas a decisão final ainda fica perto do acaso. |

### Resultados por variante

| Base | Unigram AUROC | PCA AUROC | Recorrente AUROC | Robusta AUROC |
| --- | ---: | ---: | ---: | ---: |
| ADFA | 0,565 | 0,516 | 0,557 | 0,413 |
| HAI | — | 0,768 | 0,722 | 0,715 |
| LID | 0,569 | 0,636 | 0,544 | 0,619 |

O traço `—` quer dizer que aquela combinação não faz parte da Matrix V4, e não que o programa falhou.

## Como ler os números

- **AUROC** vai de 0 a 1 e mede se os ataques tendem a receber uma pontuação mais suspeita que os exemplos normais. `0,5` é como chutar; quanto mais perto de `1`, melhor.
- **AUPRC** é especialmente útil quando existem poucos ataques. Ela mostra a qualidade ao encontrar ataques sem encher a resposta de alarmes falsos.
- **Acurácia balanceada** dá o mesmo peso a normal e ataque. Isso evita parecer bom apenas porque há muitos exemplos normais.
- A variante **recorrente** foi repetida com cinco sementes. Seus AUROCs médios foram: ADFA `0,557 ± 0,010`, HAI `0,722 ± 0,005` e LID `0,544 ± 0,022`. Em termos simples, HAI foi mais estável; LID oscilou mais entre repetições.

## O que já pode ser dito na tese

Uma forma segura de contar a história é esta:

> No piloto V4, o comportamento do detector variou entre as bases. HAI apresentou a melhor capacidade exploratória de discriminação, enquanto ADFA e LID ficaram mais próximos do nível aleatório em algumas variantes. Portanto, os resultados sugerem utilidade dependente do domínio e precisam ser interpretados com as limitações do protocolo piloto.

Isso descreve o que os dados mostram sem prometer que o método é universalmente melhor.

## A parte importante que ainda falta

A execução **confirmatória** não começou. O pré-teste encontrou uma trava correta no LID: depois de remover conteúdos duplicados entre papéis experimentais, havia **44 gravações válidas** para validação, mas o plano pedia **45**. Nenhuma célula confirmatória foi executada, o que evita misturar dados parecidos entre treino, validação e teste.

Logo, use os números acima como:

- resultados do **piloto V4**;
- evidência inicial e reproduzível para capítulos de experimento e discussão;
- não como resultado final confirmatório ou prova definitiva de superioridade.

## Onde encontrar o detalhamento completo

O quadro completo, com F1, MCC, intervalos das sementes, suporte das bases e identificadores de reprodução, está em `docs/thesis-v4-pilot-results.md`.

