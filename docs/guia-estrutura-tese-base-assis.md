# Guia simples de estrutura para escrever a tese

Este guia usa apenas a **organização** da tese de Assis como inspiração. Não copia o conteúdo, os argumentos nem os resultados dela. Pense na tese como um livro: cada capítulo responde a uma pergunta diferente, e o leitor deve conseguir seguir a história sem se perder.

## Mapa bem curto

| Parte | Pergunta infantil | Função técnica |
| --- | --- | --- |
| Introdução | “Qual é o problema e por que importa?” | Define motivação, pergunta de pesquisa, objetivo e contribuições. |
| Fundamentação | “Quais peças precisamos conhecer?” | Explica conceitos, dados, métricas e técnicas usadas. |
| Proposta | “Qual foi a máquina construída?” | Descreve o método e o protótipo de forma reproduzível. |
| Experimentos | “Como testamos e o que aconteceu?” | Mostra protocolo, números, comparação e interpretação. |
| Trabalhos relacionados | “Quem já tentou algo parecido?” | Posiciona o trabalho diante da literatura. |
| Considerações finais | “O que aprendemos e o que falta?” | Responde à pergunta inicial, limita conclusões e aponta próximos passos. |

## Elementos antes do Capítulo 1

Organize as páginas iniciais exigidas pela sua instituição: capa, folha de rosto, resumo, abstract, listas de figuras/tabelas/siglas e sumário. Elas funcionam como a etiqueta e o índice de um brinquedo: dizem o que ele é e onde cada peça está.

## 1. Introdução

Esta é a porta de entrada. Ela deve dizer, em ordem simples:

1. qual problema de segurança ou detecção está sendo estudado;
2. por que esse problema vale a pena;
3. qual pergunta a tese tenta responder;
4. qual é o objetivo geral e quais são os objetivos específicos;
5. quais são as contribuições prometidas;
6. como o restante da tese está organizado.

Não coloque todos os detalhes técnicos aqui. A introdução apresenta o mapa; ela não é o lugar para despejar todos os resultados.

## 2. Fundamentação teórica

Aqui ficam as peças de Lego que o leitor precisa conhecer antes de ver sua construção. Separe em blocos pequenos, por exemplo:

- detecção de intrusão/anomalias e o domínio estudado;
- representação dos dados e pré-processamento;
- variantes do detector avaliadas;
- bases de dados e suas características;
- métricas: AUROC, AUPRC, acurácia balanceada, F1 e MCC;
- princípios de validação experimental, separação entre treino/validação/teste e controle de duplicatas.

Cada conceito deve aparecer porque será usado depois. Se uma peça não ajuda a entender o método ou o experimento, ela provavelmente não precisa estar aqui.

## 3. Proposta e protótipo

Este capítulo explica a sua “máquina”. O leitor deve conseguir entender o caminho completo do dado:

`dados brutos -> recorte/unidade experimental -> representação -> detector -> pontuação -> métrica`

Descreva a Matrix V2/V4 como um plano de testes: quais bases, quais variantes, quais papéis de treino/validação/teste, quais sementes e quais regras impedem vazamento de dados. Inclua diagramas, parâmetros congelados e pseudocódigo apenas quando ajudarem a reproduzir o trabalho.

## 4. Experimentos e resultados

Este é o capítulo dos números. Mantenha sempre a mesma sequência para cada experimento:

1. **o que foi testado**;
2. **como foi testado**: hardware, versão do código, dados, divisões e métricas;
3. **o que foi observado**: tabelas e figuras;
4. **o que o número significa**;
5. **o que o número não permite concluir**.

Para o estado atual do projeto, separe claramente “piloto V4” de uma futura rodada confirmatória. Chame os resultados atuais de exploratórios, informe que foram 23/23 células sem falhas e registre a limitação do pré-teste confirmatório no LID. Isso deixa a tese honesta e tecnicamente forte.

## 5. Trabalhos relacionados

Agora compare a ideia da tese com trabalhos anteriores. A estrutura mais fácil é uma tabela com colunas como: problema, tipo de dados, método, protocolo de avaliação, métricas, resultado principal e diferença para sua proposta.

Não transforme este capítulo em uma lista de resumos. Em cada grupo de trabalhos, explique qual espaço ainda estava aberto e como a sua tese tenta investigá-lo.

## 6. Considerações finais

Volte à pergunta da Introdução e responda usando somente o que os experimentos realmente sustentam. Depois, liste:

- contribuições entregues;
- principais resultados;
- limitações;
- ameaças à validade;
- trabalho futuro.

É como fechar uma história: diga o que foi descoberto, seja claro sobre o que ainda não se sabe e deixe o próximo passo bem visível.

## Referências e apêndices

As referências guardam todas as fontes citadas. Os apêndices podem guardar materiais que são importantes, mas interromperiam a leitura principal: configurações completas, tabelas longas, detalhes de execução, checklist de reprodutibilidade e resultados adicionais.

## Regra de ouro para não se perder

Cada promessa da Introdução deve reaparecer em algum experimento. Cada número do capítulo de resultados deve ter um método explicado antes. E cada conclusão deve apontar para uma tabela, figura ou análise que a sustente.

Essa cadeia simples evita a maior parte dos problemas de uma tese:

`pergunta -> método -> experimento -> evidência -> conclusão`

