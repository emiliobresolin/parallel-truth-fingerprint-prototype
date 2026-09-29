# Por que o experimento demora e o que cada etapa protege

## Resposta curta

O experimento demora porque não estamos apenas pedindo para um programa dizer “ataque” ou “normal” uma vez. Estamos construindo números que possam ser defendidos em uma tese: com dados separados, regras congeladas antes de ver o teste, repetições com sementes diferentes, verificação de origem e arquivos que permitem outra pessoa refazer a conta.

Pense em uma prova escolar. Um resultado rápido seria olhar a resposta de um colega e copiar. O resultado parece bom, mas não prova aprendizagem. A Matrix V2 faz o contrário: guarda a prova, não deixa treinar com as respostas e registra cada passo. Isso custa tempo de CPU, mas transforma um protótipo em evidência auditável.

## CPU-h não é o mesmo que horas no relógio

Uma **CPU-h** é uma unidade de trabalho: um núcleo de CPU trabalhando durante uma hora.

- 1 núcleo trabalhando por 1 hora = 1 CPU-h.
- 4 núcleos trabalhando por 1 hora = 4 CPU-h.
- Portanto, 4 CPU-h podem levar aproximadamente 1 hora no relógio se quatro núcleos trabalham em paralelo, ou 4 horas se apenas um núcleo trabalha.

O computador também precisa ler arquivos, esperar disco, montar dados e gravar evidências. Por isso o tempo no relógio nunca é exatamente igual ao total de CPU-h.

Há ainda outro “12” no projeto: o modelo recorrente pode treinar por até **12 épocas**. Isso significa até 12 passadas pelos dados de treino; **não são 12 horas**.

## O que significam 12 CPU-h, 437,72 CPU-h e 440 CPU-h

| Número | O que era | O que significa na prática |
| --- | --- | --- |
| 12 CPU-h | Teto antigo de orçamento da Matrix V2. | Era uma permissão máxima inicial, não uma previsão e nem tempo já gasto. Era pequeno demais para a confirmação completa. |
| 218,86 CPU-h | Previsão bruta de uma revisão anterior para a matriz confirmatória completa. | Soma estimada de treino, inferência, controles e pré-checagens, baseada nas medições do piloto daquele protocolo. |
| 437,72 CPU-h | A mesma previsão com fator de segurança de 2×. | É a estimativa conservadora: `218,86 × 2`. Ela ficou muito acima do teto antigo de 12 CPU-h, então o sistema corretamente não liberou a rodada completa. |
| 440 CPU-h | Teto atual aprovado para V4/V5. | É o limite máximo permitido. Não quer dizer que 440 horas já foram gastas ou que o sistema pode ultrapassá-lo. |
| 4,76 CPU-h | Custo autenticado do piloto V4 anterior. | Foi o primeiro ensaio de referência, com 23 células completas. |
| 4,10 CPU-h | Custo autenticado do novo piloto V5. | Foi necessário porque a configuração de confirmação mudou de forma controlada; terminou com 23/23 células, zero falhas e cerca de 1h21min no relógio. |
| 4,36 CPU-h | Custo autenticado do piloto V6. | O piloto V6 terminou com 23/23 células e zero falhas; ele mede a configuração final com a cota LID confirmatória de 40. |
| 174,25 CPU-h | Projeção bruta autenticada da confirmação V6 completa. | Inclui treino, inferência, overhead e as seis pré-checagens obrigatórias do protocolo de 158 células. |
| 348,50 CPU-h | Projeção V6 conservadora com fator de segurança 2×. | É o valor usado pelo gate; está abaixo do teto autorizado de 440 CPU-h. |

O número `437,72` está no preflight confirmatório anterior, em `evidence/academic/thesis-evaluation-v2/74de5e6a07aef678/confirmatory/preflight.json`. Ele é uma **previsão**, não uma fatura e não um resultado científico. Essa revisão também encontrou sobreposição observada no LID, portanto não era elegível para liberar a confirmação.

O limite atual é 440 CPU-h porque você autorizou esse teto. O pipeline usa fator de segurança `2,0`: se a previsão bruta for 200 CPU-h, ele considera aproximadamente 400 CPU-h para decidir se há margem. Se a pré-checagem V5 calcular mais de 440 CPU-h de forma conservadora, ela deve bloquear antes de iniciar a confirmação, em vez de gastar além do combinado.

Também existe uma projeção V4 menor, de 64,87 CPU-h brutas / 129,75 CPU-h conservadoras. Ela **não** deve ser usada para decidir o V5: o V4 parou no LID e deixou suas janelas como zero na projeção. A pré-checagem V5 completa é a fonte correta para o custo final, porque precisa incluir o LID inteiro.

## Por que a confirmação exige tanto trabalho

Existem três bases de dados e quatro tipos de detector em algumas delas. Os detectores determinísticos rodam uma vez por fase; o detector recorrente precisa repetir o treino com sementes diferentes.

Na confirmação V5 serão **158 células lógicas**:

| Tipo | Quantidade | Por quê |
| --- | ---: | --- |
| Modelos determinísticos | 8 | A mesma entrada produz a mesma saída; uma execução autenticada por base/modelo basta. |
| Modelo recorrente | 150 | São 3 bases × 50 sementes. Cada semente muda a inicialização e mostra se o resultado é estável ou apenas sorte. |
| Total | 158 | É a matriz fechada que será analisada somente quando estiver completa. |

Cada treino recorrente pode usar até 12 épocas, depois calcula pontuações no conjunto de teste e registra previsões, métricas, hashes e transações de evidência. Além do treino, o sistema faz leitura e auditoria dos dados, separa validação de calibração/early stopping e produz estatísticas. É por isso que “rodar 50 vezes” é muito mais caro do que rodar uma demo uma vez.

Além disso, há uma pré-checagem confirmatória independente e uma pré-checagem local em cada um dos cinco lotes. Elas repetem a verificação de identidades e fontes de propósito: se algum dado mudar no meio do caminho, a execução deve parar. Só o truth lock V5 inventaria 34.552 arquivos do LID; examinar e normalizar essa superfície é uma das razões de a primeira etapa levar bastante tempo.

Os lotes também são posicionais: o lote 2 só abre depois que todas as células do lote 1 forem autenticadas, e assim por diante. O sistema não permite executar lotes confirmatórios em paralelo ou pular sementes/modelos para “terminar logo”, porque isso abriria espaço para escolher apenas as partes favoráveis da matriz.

## Os quatro sentidos diferentes da palavra “teste”

É normal confundir estes testes porque todos recebem esse nome, mas eles fazem trabalhos diferentes:

| Tipo de teste | Pergunta que responde | Estado atual |
| --- | --- | --- |
| Testes de software | “O código implementa as regras corretamente?” | V5: 702 passaram, 15 foram ignorados e 194 subtestes passaram. |
| Pré-checagem de dados | “Os dados são oficiais, suficientes, separados e sem cópias vazando?” | Piloto V5 passou nas três bases; pré-checagem confirmatória V5 está em execução. |
| Piloto experimental | “O plano funciona e qual é a variabilidade inicial?” | V4: 23/23 completo; V5: 23/23 completo, zero falhas. |
| Confirmação estatística | “O padrão continua quando o plano congelado é executado por inteiro?” | Ainda faltam 158 células e o relatório final. |

Os testes de software não dizem que o detector é bom; eles dizem que o mecanismo de avaliação não quebrou. Os testes experimentais dizem como o detector se comporta nos dados.

## Por que existe pré-checagem antes de treinar

A pré-checagem é como conferir se as peças de um experimento de química estão limpas antes de misturá-las. Ela verifica, entre outras coisas:

1. **Origem dos dados:** ADFA-LD, HAI-23.05 e LID-DS-2021 devem vir da superfície oficial declarada.
2. **Integridade:** os arquivos e conteúdos usados recebem identidades criptográficas (hashes), para detectar mudanças.
3. **Separação de papéis:** treino, validação e teste não podem reutilizar a mesma unidade.
4. **Separação entre piloto e confirmação:** a confirmação não pode simplesmente repetir o mesmo conteúdo do piloto.
5. **Duplicatas de conteúdo:** no LID, não basta ter nomes de arquivo diferentes; o conteúdo que chega ao detector também precisa ser diferente.
6. **Suporte mínimo:** deve haver exemplos normais e ataques suficientes para que uma métrica tenha sentido.
7. **Papéis dentro da validação:** uma parte é usada para parar o treino cedo e outra para calibrar o limiar; elas não podem ser a mesma coisa.

Essa etapa demora principalmente porque o LID possui muitos arquivos/arquivos compactados e a avaliação precisa ler conteúdo suficiente para encontrar cópias e preservar a separação. É trabalho de proteção de validade, não tempo “perdido”.

## O que aconteceu com o V4 e por que apareceu o V5

O V4 executou seu piloto sem falhas. Porém, quando tentou montar a confirmação, a pré-checagem encontrou um problema real:

> No cenário `CVE-2012-2122` do LID, havia 44 gravações válidas e distintas disponíveis para validação, mas o plano exigia 45.

O pipeline bloqueou a execução. Isso foi uma coisa boa: ele preferiu parar a usar uma cópia parecida, misturar papéis ou inventar um dado que não existia.

A correção V5 é a menor possível:

- reduz a cota confirmatória do LID de 45 para 44 em **todos** os quatro papéis do LID;
- mantém os offsets do piloto, as sementes, os modelos, as métricas e as demais bases;
- preserva `15 cenários × 44 = 660` normais e 660 ataques no teste LID, acima do mínimo de 600 para cada classe;
- cria uma nova identidade de configuração, em vez de reescrever o V4.

Como uma cota de dados mudou, seria incorreto usar formalmente o piloto V4 como se ele tivesse sido feito com o V5. Os hashes de configuração impedem essa mistura. O V4 continua valioso como resultado de referência; o V5 cria uma linha limpa para a confirmação.

Na pré-checagem completa, a V5 encontrou um segundo limite real: `CVE-2020-23839` tinha somente 43 gravações de validação válidas e distintas para a cota de 44. Ela parou antes de treinar qualquer célula confirmatória. A V6 faz a correção única para 40 em todos os quatro papéis LID: `15 cenários × 40 = 600` normais e 600 ataques, exatamente o mínimo confirmatório já congelado. V6 preserva todas as sementes, modelos, métricas e regras estatísticas; muda apenas essa capacidade física e as evidências de governança que dela dependem.

## O que a Matrix V2 faz melhor que a V1

A V1 já tinha uma boa ideia de piloto, bases, sementes e métricas. A Matrix V2 transforma isso em um protocolo mais rígido e verificável.

| Tema | V1 | Matrix V2 / V4 / V5 |
| --- | --- | --- |
| Configuração numérica | Valores estavam em um arquivo de configuração. | Os 205 consumidores numéricos são inventariados, aprovados e ligados a evidência/decisão imutável. |
| Orçamento | Não havia o gate de orçamento V2 atual. | Há teto de CPU-h, fator de segurança e bloqueio antes de ultrapassar o teto. |
| Piloto versus confirmação | Havia fases e cotas, mas não havia `phase_allocation` com offsets; a confirmação ADFA estava configurada com cotas zero. | Há alocações por fase, offsets e auditoria observada de disjunção entre piloto e confirmação. |
| Duplicatas no LID | A proteção era menos específica para conteúdo visível pelo detector. | O V4/V5 compara identidades de conteúdo, não apenas nomes ou offsets de arquivo. |
| Validação | O limiar usava a partição de validação. | Validação é dividida em calibração e early stopping, com auditoria de independência. |
| Repetições do recorrente | V1 previa até 30 sementes confirmatórias. | V2/V5 fixa 50 sementes, em cinco lotes de 10, sem encurtar o plano ao ver resultados bons ou ruins. |
| Execução final | Não havia o mesmo ledger V2 de lotes e retenção de análise. | Cinco lotes confirmatórios, artefatos autenticados e resultados agregados retidos até a matriz inteira terminar. |
| Fontes e reprodutibilidade | Configuração e resultados eram a referência principal. | Configuração congelada, testes pós-congelamento, truth lock das fontes e hashes por célula permitem auditoria posterior. |

V1 deve ser tratado como diagnóstico histórico, e não como evidência elegível para a confirmação V2. V2 não torna automaticamente o detector mais inteligente. Ela torna a avaliação mais honesta: se o resultado for fraco, a tese poderá mostrar isso com confiança; se for forte, haverá uma trilha verificável explicando por quê.

## Que resultados já existem

O piloto V4 já oferece números de referência úteis para começar a escrever. Alguns AUROCs de referência são:

| Base | Variante | AUROC V4 | Leitura cuidadosa |
| --- | --- | ---: | --- |
| ADFA-LD | unigram | 0,565 | Separação fraca, pouco acima do acaso. |
| HAI-23.05 | PCA | 0,768 | Melhor separação observada no piloto. |
| LID-DS-2021 | PCA | 0,636 | Há sinal no ranking, mas a decisão final ainda precisa de cuidado. |

O relatório completo do piloto V4 está em `docs/thesis-v4-pilot-results.md`. Esses valores ajudam a formular a discussão, mas não devem ser misturados com a configuração V5.

O piloto V5 acabou com 23/23 células e zero falhas. Ele não foi criado para “escolher o melhor modelo”; ele autentica a nova configuração, mede tempo e permite que a confirmação use o mesmo protocolo limpo.

## O que a confirmação vai calcular

Quando as 158 células acabarem, o relatório final deverá apresentar:

- **AUROC** como métrica principal de ranking;
- **AUPRC**, útil quando ataques são menos frequentes;
- **acurácia balanceada**, **F1** e **MCC**;
- média, desvio padrão e intervalo de confiança t de 95% entre as 50 sementes do modelo recorrente;
- bootstrap clusterizado com 2.000 réplicas, apenas quando existir número suficiente de clusters independentes;
- teste de permutação com 20.000 réplicas e correção de Holm para comparações que realmente tiverem repetições estocásticas pareadas.

Há limites honestos que o relatório precisa manter:

- os baselines determinísticos não têm 50 sementes independentes; compará-los com o recorrente será **descritivo**, sem inventar p-valor;
- HAI possui somente dois clusters de teste, abaixo do mínimo de cinco para bootstrap clusterizado; o intervalo correspondente deve aparecer como indefinido, não como zero ou como uma falsa certeza;
- nenhuma métrica permite dizer que um modelo é “campeão universal” entre modalidades e bases diferentes.

Isso não diminui a tese. Mostrar claramente o que uma análise pode e não pode concluir é uma parte importante de ciência bem feita.

## Estado de corte para a tese (29/09/2026)

Esta seção substitui o estado operacional histórico registrado abaixo. A coleta usada para a redação foi encerrada por decisão do autor e utiliza o corpus V6 já concluído. Não há nova célula pendente para produzir as tabelas da tese.

| Item | Estado de corte | Uso na tese |
| --- | --- | --- |
| Corpus V6 | 23/23 células predefinidas concluídas, zero falhas, origem `official_native`, separação de grupos aprovada e teste cego preservado. | Fonte única dos números e tabelas. |
| Autoencoder recorrente | Cinco sementes por base: 101, 211, 307, 419 e 523. | Médias e IC95% entre sementes. |
| Métodos determinísticos | Uma execução autenticada por combinação base/modelo. | Valores diretos e comparações descritivas. |
| Continuação longa V6 | Interrompida antes de completar os cinco lotes. | Não entra nas tabelas nem recebe valor estimado. |
| Pacote de resultados | Gerado a partir dos artefatos completos e com manifesto SHA-256. | `reports/matrix-v2-resultados-data-de-corte.md`, CSV e tabela LaTeX. |

O relatório de referência para a escrita é `docs/matriz-v2-resultados-para-tese.md`. Ele explica como citar os números sem acrescentar resultados que não foram executados.

### Por que o corpus fechado já é uma base estatística

Os 23 resultados não são exemplos ou previsões: são medições obtidas no experimento. O autoencoder recorrente foi executado cinco vezes em cada base, com sementes independentes, o que permite calcular média, desvio padrão e IC95% t de Student para cada métrica. As células também preservam intervalos por unidade de teste por meio de 2.000 reamostragens nas condições em que há suporte independente suficiente.

Assim, a tese pode usar a formulação **“resultados estatísticos da Matriz V2 até a data de corte”**. A regra é simples: informar o `n` real de cada resultado, apresentar os intervalos existentes e não atribuir a uma comparação p-valores que não foram calculados. Isso não elimina a base estatística; apenas mantém cada conclusão no tamanho de amostra que foi realmente executado.

## Registro histórico anterior do estado operacional

Este é um retrato em 28/09/2026, após o bloqueio controlado da pré-checagem V5 e enquanto o piloto V6 está rodando:

| Etapa | Situação | Próximo resultado esperado |
| --- | --- | --- |
| Revisão V5 do LID | Concluída e congelada. | Manter V4 preservado e V5 como protocolo confirmatório. |
| Testes de software V5 | Concluídos com sucesso. | Evidência de que o pipeline está íntegro. |
| Truth lock das fontes | Concluído. | Provar que as fontes oficiais não mudaram antes da execução. |
| Piloto V5 | 23/23 concluído, 0 falhas, 4,10 CPU-h autenticadas. | Fornecer timing e matriz compatível para a confirmação. |
| Pré-checagem confirmatória V5 | Bloqueada corretamente por suporte: `CVE-2020-23839`/validação tinha 43 gravações válidas e distintas para uma cota de 44. Gastou 6.029,52 s de CPU; a projeção de 125,48 CPU-h conservadoras estava dentro de 440 CPU-h. Nenhuma célula confirmatória foi executada. | Preservar a V5 como evidência do bloqueio e não forçar dados duplicados. |
| Revisão V6 do LID | Congelada após a redução uniforme de 44 para 40 por cenário/papel. | Terminar o piloto V6 e confirmar, em nova pré-checagem, a disponibilidade integral de 600 normais e 600 ataques. |
| Piloto V6 | Concluído: 23/23 células, 0 falhas e 15.701,42 s de CPU (4,36 CPU-h). | Fornecer tempo autenticado e matriz compatível para a confirmação. |
| Pré-checagem confirmatória V6 | Aprovada: ADFA, HAI e LID passaram suporte, isolamento, validação e origem. Custou 6.620,97 s de CPU; a projeção é 174,25 CPU-h brutas / 348,50 conservadoras. | Autorizar os cinco lotes sem exceder 440 CPU-h. |
| Confirmação V6 | Lote 1 em execução. | Executar 158 células em cinco lotes: 38 no primeiro e 30 em cada um dos quatro seguintes, mantendo a ordem fixa e os gates locais. |
| Relatório final | Ainda não gerado. | Produzir tabelas, figuras, limites e análise estatística após a matriz completa. |

Se a pré-checagem V6 retornar `ready` e a previsão conservadora for até 440 CPU-h, a confirmação começa. Se ela bloquear por suporte, vazamento ou orçamento, não devemos forçar a execução: será necessário registrar o motivo e decidir uma nova mudança de desenho/orçamento.

Depois de uma configuração ser congelada, não é correto pular modelos, bases, sementes ou lotes porque o resultado ficou lento. Isso mudaria a pergunta respondida e invalidaria a comparação. A simplificação correta acontece antes do congelamento — foi exatamente o caso da redução uniforme do LID de 45 para 44 — e depois exige novo piloto compatível.

## Quais documentos e evidências sustentam esta explicação

- `configs/experiments/thesis-evaluation-v1.json`: configuração histórica V1.
- `configs/experiments/thesis-evaluation-v2.candidate-v5.json`: proposta V5 com a correção mínima do LID.
- `configs/experiments/thesis-evaluation-v2.approval-v5.json`: decisão registrada para continuar até a confirmação, com teto de 440 CPU-h.
- `configs/experiments/thesis-evaluation-v2.frozen-v5.json`: configuração que não pode ser alterada durante a confirmação.
- `evidence/academic/governance/thesis-evaluation-v2-test-lock-v5.json`: registro da bateria de testes pós-congelamento.
- `evidence/academic/governance/thesis-evaluation-v2-truth-lock-v5.json`: registro da superfície das fontes oficiais.
- `evidence/academic/thesis-evaluation-v2/23aa81cfb426dc4e/`: piloto V4 e o bloqueio confirmatório que revelou 44 em vez de 45.
- `evidence/academic/thesis-evaluation-v2/7798f410ddef6d68/`: piloto V5 autenticado e, depois, confirmação V5.
- `src/parallel_truth_fingerprint/lstm_service/offline_training/academic_protocol.py`: regras de partição, conteúdo, duplicatas e vazamento.
- `src/parallel_truth_fingerprint/lstm_service/offline_training/academic_runner.py`: gates, orçamento, lotes, integridade e relatórios.
- `docs/scientific-governance-v1.md`, `docs/evidence-manifests-v1.md` e `_bmad-output/implementation-artifacts/tech-spec-build-thesis-grade-experimental-evaluation-pipeline.md`: contratos e critérios que orientam o pipeline.
- `docs/thesis-v4-pilot-results.md`: tabelas completas dos resultados já disponíveis.

## A lógica em uma linha

`pergunta de pesquisa -> plano congelado -> dados separados -> piloto -> custo autenticado -> confirmação completa -> estatística com limites explícitos -> números para a tese`

Essa sequência é a razão de demorarmos mais agora e, ao mesmo tempo, a razão de os números finais terem muito mais valor na escrita e na banca.
