# Arquitetura baseada em Fonte de Verdade Física Paralela para geração de fingerprint físico-operacional em sistemas industriais legados

## Resumo

Sistemas industriais legados dependem de dados de processo para operar com segurança. Esses dados saem dos sensores, passam por controladores lógicos programáveis, conhecidos como CLPs, e chegam aos sistemas de supervisão, chamados de SCADA. O problema é que um valor pode parecer normal na tela do operador e, mesmo assim, não representar corretamente o que está acontecendo no processo físico. Isso pode ocorrer por falha, manipulação do caminho digital ou ataque silencioso.

Este trabalho apresenta uma arquitetura que cria uma Fonte de Verdade Física Paralela. A ideia é observar o sinal do sensor antes da entrada no CLP, coletar essa observação por Edge Gateways e compará-la com o valor que aparece no caminho digital. Os Edge Gateways compartilham as observações, validam as leituras e registram o resultado para análise posterior. A arquitetura também organiza dados para modelos de aprendizado de máquina usados na identificação de comportamento fora do padrão.

O protótipo foi executado com serviços de consenso, mensageria, armazenamento e comparação com SCADA. Também foram realizados testes de cenário para verificar o comportamento diante de operação normal, perda de quórum, exclusão de edge e divergência entre a leitura física e a leitura reportada no SCADA. Para a avaliação dos detectores, a Matriz V2 reuniu 23 execuções completas nas bases ADFA-LD, HAI 23.05 e LID-DS 2021. O autoencoder recorrente foi repetido com cinco sementes por base, permitindo calcular média, desvio padrão e intervalo de confiança de 95% entre as execuções. Os resultados mostram AUROC médio de 0,5575 no ADFA-LD, 0,7225 no HAI 23.05 e 0,5438 no LID-DS 2021 para o autoencoder recorrente.

Além das bases públicas, o protótipo preservou quatro campanhas próprias com 17 linhas que associam medidas de corrente, rastros de chamadas de sistema e a rodada de execução. Esse material mostra o caminho de integração da arquitetura e é apresentado separadamente da comparação entre os benchmarks públicos.

Palavras-chave: sistemas industriais legados, segurança industrial, Edge Computing, Fonte de Verdade Física Paralela, detecção de anomalias, autoencoder.

## Abstract

Legacy industrial systems depend on process data to operate safely. These data leave sensors, pass through programmable logic controllers, known as PLCs, and reach supervisory systems, known as SCADA. A value can look normal on the operator screen and still fail to represent the physical process. This can happen because of a fault, a change in the digital path, or a silent attack.

This work presents an architecture that creates a Parallel Physical Source of Truth. The architecture observes the sensor signal before it reaches the PLC, collects the observation through Edge Gateways, and compares it with the value reported in the digital path. The Edge Gateways share observations, validate readings, and preserve the result for later analysis. The architecture also organizes data for machine learning models that identify behavior outside the expected pattern.

The prototype was executed with consensus, messaging, storage, and SCADA comparison services. The Matrix V2 produced 23 complete executions on ADFA-LD, HAI 23.05, and LID-DS 2021. The recurrent autoencoder was repeated with five seeds for each dataset. Its mean AUROC was 0.5575 on ADFA-LD, 0.7225 on HAI 23.05, and 0.5438 on LID-DS 2021. The prototype also preserved four custom campaigns with 17 synchronized rows associating current measurements, system-call traces, and execution rounds. This custom material is reported as integration evidence, separately from the public benchmark comparison.

Keywords: legacy industrial systems, industrial security, Edge Computing, Parallel Physical Source of Truth, anomaly detection, autoencoder.

## 1 Introdução

### 1.1 Contexto

Muitas plantas industriais continuam usando equipamentos e redes que foram construídos para funcionar por longos períodos. Isso não significa que esses sistemas não funcionem bem. Pelo contrário, eles costumam atender ao processo por muitos anos. O problema aparece quando a planta passa a depender mais de supervisão remota, integração com sistemas corporativos e comunicação em rede, mas mantém componentes antigos e uma relação de confiança muito forte com o caminho digital.

Em uma arquitetura comum, o sensor mede uma variável física, como temperatura, pressão ou rotação. O sinal segue para o CLP. Depois, o valor chega ao SCADA, onde pode ser visto pelo operador ou usado por uma regra automática. Se o dado for alterado entre o sensor e a supervisão, o sistema pode tomar uma decisão usando um valor plausível, mas incorreto. Esse é um problema relevante porque a tela pode continuar mostrando algo aparentemente normal enquanto o processo físico está em outra condição.

Sistemas de detecção de intrusão ajudam a procurar comportamentos estranhos. Porém, muitas soluções analisam somente pacotes de rede, logs ou valores já digitalizados. Quando o próprio caminho digital é alterado, esse tipo de análise pode começar de uma base que já não representa o processo real. Por isso, este trabalho parte de uma pergunta simples: como criar uma referência física independente, sem trocar a infraestrutura existente e sem interferir no controle da planta?

### 1.2 Problema de pesquisa

O problema tratado nesta dissertação é a falta de uma forma independente de verificar se o valor usado pelo CLP e pelo SCADA ainda representa o estado físico do processo. Em sistemas legados, alterar o processo de controle pode ser caro, arriscado e muitas vezes inviável. A solução precisa funcionar de forma complementar, isto é, ela observa e valida, mas não assume o lugar do controlador que já existe.

Assim, a pergunta de pesquisa é a seguinte:

> Como validar a integridade e a confiabilidade dos dados de processo em sistemas industriais legados de forma independente do caminho digital tradicional, sem interferir no controle e permitindo identificar inconsistências ou ataques silenciosos?

### 1.3 Objetivo geral e objetivos específicos

O objetivo geral é propor e avaliar uma arquitetura de validação de integridade para sistemas industriais legados baseada em uma observação física independente, em processamento distribuído no edge e em modelos de aprendizado de máquina para acompanhar o comportamento dos dados.

Para atingir esse objetivo, o trabalho realizou as seguintes atividades:

1. analisou a necessidade de uma referência física independente do CLP e do SCADA;
2. definiu uma arquitetura de coleta paralela do sinal do sensor;
3. organizou o compartilhamento das observações entre Edge Gateways;
4. implementou uma etapa de validação distribuída para lidar com leituras inconsistentes;
5. comparou o valor físico validado com o valor reportado no SCADA;
6. preservou artefatos físico-operacionais para análise e aprendizado;
7. avaliou detectores em três bases públicas por meio da Matriz V2;
8. registrou campanhas próprias que ligam medidas de corrente, rastros de syscall e inferências do autoencoder.

### 1.4 Contribuições

As contribuições deste trabalho são quatro. A primeira é a proposta de uma Fonte de Verdade Física Paralela, obtida sem depender do valor já tratado pelo CLP. A segunda é um protótipo que junta coleta no edge, troca de mensagens, validação distribuída, comparação com SCADA e armazenamento de evidências. A terceira é a Matriz V2, que executou um protocolo comum em ADFA-LD, HAI 23.05 e LID-DS 2021, preservando treino, validação e teste separados. A quarta é a trilha própria de integração, que mostra a associação entre dados físicos, rastros de syscalls e a execução do autoencoder pelo mesmo identificador de rodada.

### 1.5 Organização do texto

O Capítulo 2 apresenta os conceitos necessários para entender a proposta. O Capítulo 3 explica a arquitetura e o protótipo. O Capítulo 4 descreve o experimento, as bases, as métricas e os resultados. O Capítulo 5 apresenta os trabalhos relacionados. Por fim, o Capítulo 6 apresenta as conclusões.

## 2 Fundamentação teórica

### 2.1 Sistemas industriais legados e confiança no dado

Em uma planta industrial, o valor digital não é o processo em si. Ele é uma representação do processo. O sensor mede uma variável física, transforma essa medida em sinal e o CLP usa esse sinal para controle e supervisão. Essa cadeia funciona bem quando todos os seus componentes estão corretos. Mas a mesma cadeia pode esconder um erro quando um dispositivo ou uma comunicação passa a apresentar comportamento incorreto.

Sistemas legados trazem uma dificuldade prática. Não é simples trocar sensores, alterar a lógica do CLP ou adicionar mecanismos pesados de segurança em um ambiente que precisa continuar operando. Por isso, a proposta deste trabalho não modifica a malha de controle. Ela cria uma observação paralela que pode ser comparada com o caminho já existente.

### 2.2 Fonte de Verdade Física Paralela

Neste trabalho, Fonte de Verdade Física Paralela significa uma leitura obtida do processo antes de sua dependência do CLP e do SCADA. O sinal do sensor é duplicado de forma não intrusiva e acompanhado por Edge Gateways. A leitura passa a ter uma origem física separada da informação que será mostrada no supervisório.

Essa separação é importante porque permite fazer uma pergunta que não depende apenas do valor digital recebido: o valor reportado pelo SCADA continua compatível com a leitura física validada? Quando a resposta for negativa, a arquitetura registra a divergência e impede que o dado seja tratado como confiável para a etapa seguinte.

### 2.3 Edge Computing e validação distribuída

Edge Computing é o processamento realizado perto da fonte de dados. Neste caso, os Edge Gateways ficam próximos da coleta e tratam as leituras antes que elas sejam usadas para análise posterior. Isso reduz a necessidade de enviar tudo para uma camada central antes de qualquer verificação.

Os edges compartilham suas observações e verificam se as leituras são compatíveis. Essa etapa considera a possibilidade de um edge apresentar defeito ou comportamento malicioso. Uma falha bizantina é justamente uma falha em que um componente pode enviar informação errada, atrasada ou manipulada. A arquitetura usa a comparação entre as observações para isolar dados que não concordam com o conjunto e formar uma leitura física validada.

### 2.4 Fingerprint comportamental e autoencoder

O fingerprint comportamental é uma descrição do jeito normal de funcionamento de um equipamento ou de um fluxo de dados. Para gerar esse fingerprint, pode-se usar um autoencoder. De forma simples, o autoencoder aprende a reconstruir um padrão que ele recebe. Quando o dado novo é muito diferente do padrão aprendido, o erro de reconstrução aumenta e pode indicar uma anomalia.

O autoencoder recorrente usado na Matriz V2 trabalha com sequências. Isso é importante porque uma chamada de sistema ou uma variável industrial não deve ser vista somente de forma isolada. A ordem e a evolução no tempo também podem trazer informação. O limiar é o ponto que decide quando um escore passa a ser chamado de anômalo. Neste trabalho, o limiar foi definido na validação, antes de o teste ser consultado.

No conjunto próprio do protótipo, é necessário usar um nome preciso. Existe um autoencoder de corrente com rastros de syscall correlacionados. A corrente e os syscalls foram preservados pelo mesmo `round_id`, mas os syscalls não foram colocados como entrada do autoencoder. Portanto, não se afirma que houve fusão de autoencoder e syscall dentro do mesmo modelo.

### 2.5 Métricas usadas

AUROC é a principal métrica desta dissertação. Ela mostra o quanto o modelo consegue colocar exemplos normais e anormais em uma ordem útil, considerando vários pontos de decisão. Quanto maior o valor, melhor é essa separação. AUPRC complementa essa leitura e é especialmente útil quando há poucos ataques em relação a muitos exemplos normais.

A acurácia balanceada dá o mesmo peso para a capacidade de reconhecer normais e ataques. F1 combina precisão e cobertura do ataque. MCC é uma medida que resume a relação entre os acertos e erros das duas classes. FPR indica a proporção de normais marcados como anômalos. FNR indica a proporção de ataques que não foram identificados. Nenhuma dessas métricas deve ser lida sozinha, pois cada uma mostra uma parte do comportamento do detector.

## 3 Proposta e protótipo

### 3.1 Visão geral da arquitetura

A arquitetura é formada por cinco partes conectadas. A primeira é a aquisição do sinal físico. A segunda é a coleta e o compartilhamento entre os Edge Gateways. A terceira é a validação distribuída. A quarta compara a leitura física validada com o valor reportado pelo SCADA. A quinta preserva os dados e os deixa disponíveis para a etapa de fingerprint.

O caminho completo pode ser descrito da seguinte forma: o sensor gera um sinal, o sinal é observado por uma via paralela, os edges trocam as observações, a leitura passa por validação, o resultado é comparado com o valor digital e o artefato final é armazenado. O objetivo não é substituir o CLP. O objetivo é criar uma camada de verificação independente.

### 3.2 Coleta física e compartilhamento no edge

O protótipo coleta variáveis associadas a temperatura, pressão e rotação. Os dados são transformados em payloads com valor, tempo, qualidade e outras informações necessárias para auditoria. Os Edge Gateways publicam e recebem essas informações por mensageria. Dessa forma, cada edge pode comparar a sua observação com as observações dos demais participantes.

Essa parte da arquitetura é importante porque evita que uma única leitura seja tratada como verdade sem comparação. Quando as leituras concordam, o sistema pode seguir para a formação do consenso. Quando uma leitura é muito diferente, ela pode ser excluída do resultado aceito.

### 3.3 Validação distribuída e comparação com SCADA

Depois do compartilhamento, a arquitetura avalia a consistência das leituras e forma o pacote de consenso físico. Em seguida, esse pacote é comparado com a projeção do SCADA. Se houver divergência relevante, o evento é registrado e o fluxo seguinte pode ser interrompido. Essa decisão é importante porque impede que uma divergência entre o físico e o digital seja ignorada apenas porque o valor digital parece plausível.

O protótipo usou uma rede de consenso com três validadores, mensageria MQTT, armazenamento MinIO e uma projeção SCADA em laboratório. Esses componentes permitiram observar o comportamento do fluxo completo, desde a coleta até a preservação do resultado.

Fonte: `docs/results-of-the-prototype.md`, seções de infraestrutura e verificação do pipeline.

### 3.4 Testes de cenário do protótipo

Foram registrados quatro cenários principais. Na operação normal, o consenso foi formado, a comparação com o SCADA foi compatível e o artefato foi persistido. Na perda de quórum, o consenso não foi formado e as etapas posteriores ficaram bloqueadas. Na exclusão de um edge, o sistema manteve o quórum com as leituras restantes e marcou o edge inconsistente. Na divergência do SCADA, o consenso físico foi formado, mas a diferença entre o físico e o digital interrompeu a persistência do dado como registro confiável.

| Cenário | Resultado observado |
| --- | --- |
| Operação normal | Consenso formado, comparação compatível e artefato persistido. |
| Perda de quórum | Consenso não formado e fluxo posterior interrompido. |
| Exclusão de um edge | Quórum mantido com exclusão do edge inconsistente. |
| Divergência no SCADA | Divergência registrada e continuidade do dado bloqueada. |

Fonte: `docs/results-of-the-prototype.md`, seção de verificação do pipeline e matriz de cenários.

### 3.5 Conjunto customizado de corrente e syscalls

O protótipo também gerou um conjunto próprio. Ele contém quatro campanhas e 17 linhas sincronizadas. Cada linha junta o vetor de medidas de corrente, os tokens de chamadas de sistema capturados no edge e a identificação da rodada. Isso prova que o pipeline conseguiu preservar dados de naturezas diferentes no mesmo fluxo de execução.

Das 17 linhas, 13 são do cenário normal e 4 são de exclusão de edge. Duas linhas possuem saída persistida do autoencoder e as duas foram classificadas como normais. Uma delas pertence ao cenário de exclusão de edge. Isso não significa que ela devesse obrigatoriamente ser classificada como anomalia física, porque a exclusão de edge é uma condição de disponibilidade ou de consistência entre nós, não um rótulo automático de falha física.

| Medida do conjunto próprio | Resultado |
| --- | ---: |
| Campanhas preservadas | 4 |
| Linhas sincronizadas | 17 |
| Linhas normais | 13 |
| Linhas de exclusão de edge | 4 |
| Linhas com saída do autoencoder | 2 |
| Saídas classificadas como anômalas | 0 |

O conjunto próprio aparece nesta dissertação como resultado de integração. Ele não foi somado às métricas de ADFA-LD, HAI 23.05 e LID-DS 2021 porque a Matriz V2 foi desenhada para essas três bases públicas. Também não seria correto criar uma métrica de desempenho usando somente duas saídas do autoencoder. A separação deixa claro o que foi comprovado pelo protótipo e o que foi medido pela matriz de avaliação.

Fonte: `docs/conjunto-customizado-autoencoder-syscalls-para-tese.md` e `evidence/academic/thesis-evaluation-v2/73c6eadb15c3c35a/reports/pilot-custom-track-readiness.json`.

### 3.6 Rastreabilidade

Cada resultado importante foi preservado com arquivos de origem. A Matriz V2 usa uma configuração congelada, identificação por SHA-256, arquivos por execução e tabelas derivadas. A trilha própria preserva os arquivos JSONL com a associação entre a rodada, a corrente, os syscalls e a saída disponível do autoencoder. Essa organização permite que um número mostrado na tese seja ligado ao arquivo que o produziu.

## 4 Experimentos e resultados

### 4.1 Desenho da Matriz V2

A Matriz V2 avaliou quatro tipos de detector quando eles eram aplicáveis à base: unigrama categórico, autoencoder PCA, distância robusta e autoencoder recorrente. O unigrama categórico representa a frequência de eventos. O autoencoder PCA usa uma forma mais simples de reduzir e reconstruir os dados. A distância robusta mede o afastamento em relação ao comportamento normal. O autoencoder recorrente aprende sequências temporais.

As bases foram ADFA-LD, HAI 23.05 e LID-DS 2021. ADFA-LD e LID-DS 2021 representam sequências de chamadas de sistema. HAI 23.05 representa sinais de um processo industrial. Por terem natureza e rótulos diferentes, os resultados foram apresentados por base. Não foi calculada uma média global artificial entre elas.

### 4.2 Separação entre treino, validação e teste

O treinamento ajusta o modelo. A validação serve para definir decisões do método, como o limiar que separa normal de anômalo. O teste fica separado para medir o resultado depois que essas decisões já foram tomadas. Essa separação evita que o modelo veja a resposta do teste antes da hora.

Na Matriz V2, o limiar foi definido com os dados de validação. Depois disso, o conjunto de teste foi usado para calcular as métricas. Os registros também foram verificados quanto à separação entre grupos e à preservação do teste cego. Teste cego, neste caso, significa que o resultado do teste não foi usado para escolher o limiar.

### 4.3 Repetições e base estatística

O autoencoder recorrente foi executado cinco vezes por base, com as sementes 101, 211, 307, 419 e 523. A semente controla partes aleatórias do treinamento. Repetir o treinamento com sementes diferentes mostra se o resultado muda muito ou pouco entre execuções.

Com essas cinco repetições, foram calculados média, desvio padrão e intervalo de confiança de 95% entre sementes. Esse intervalo mostra a faixa observada para o resultado do autoencoder recorrente nas execuções realizadas. Os métodos determinísticos tiveram uma execução autenticada por combinação de base e modelo. Por isso, a comparação desses métodos com o modelo recorrente é apresentada como diferença observada, sem criar um p-valor que o desenho não calculou.

Existem, portanto, resultados estatísticos da Matriz V2: 23 execuções completas, cinco repetições do autoencoder recorrente em cada base e métricas calculadas no teste separado. A interpretação sempre respeita o número de execuções existente em cada comparação.

### 4.4 Suporte de teste

| Base | Normais no teste | Ataques no teste | Total |
| --- | ---: | ---: | ---: |
| ADFA-LD | 100 | 150 | 250 |
| HAI 23.05 | 759 | 41 | 800 |
| LID-DS 2021 | 90 | 90 | 180 |

O HAI 23.05 tem apenas 41 blocos de ataque no teste, por isso é importante olhar também para AUPRC, F1, FPR e FNR. O LID-DS 2021 tem 90 unidades normais e 90 unidades de ataque, mas a leitura deve considerar que os rótulos publicados são do nível de gravação. Cada base tem sua própria unidade de análise, e esse detalhe é preservado nos artefatos do experimento.

### 4.5 Registros usados nesta dissertação

Este texto usa somente as 23 execuções completas da Matriz V2 na data de corte. Os arquivos foram verificados quanto ao estado de conclusão, origem da base, separação de dados e configuração congelada. A configuração usada possui a identificação `sha256:73c6eadb15c3c35ac3dcbfa3b4ffa5df596914481746e01b351306b6dd93f6e7`.

Fonte do método e dos números: `evidence/academic/thesis-evaluation-v2/73c6eadb15c3c35a/reports/matrix-v2-resultados-data-de-corte.md`.

### 4.6 Resultados e discussão

#### 4.6.1 Visão geral dos resultados da Matriz V2

A Matriz V2 reuniu 23 execuções completas. O autoencoder recorrente foi executado cinco vezes em cada uma das três bases. Os demais modelos foram executados uma vez por combinação. A tabela a seguir mostra os valores medidos no teste separado. Quando há colchetes, eles mostram o intervalo de confiança de 95% entre as sementes do autoencoder recorrente.

| Base | Modelo | Execuções | AUROC | AUPRC | Acurácia balanceada | F1 | MCC | FPR | FNR |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ADFA-LD | Unigrama categórico | 1 | 0,5651 | 0,6730 | 0,5300 | 0,1463 | 0,1278 | 0,0200 | 0,9200 |
| ADFA-LD | Autoencoder PCA | 1 | 0,5161 | 0,5885 | 0,4900 | não definido | -0,1100 | 0,0200 | 1,0000 |
| ADFA-LD | Distância robusta | 1 | 0,4129 | 0,5183 | 0,4950 | não definido | -0,0776 | 0,0100 | 1,0000 |
| ADFA-LD | Autoencoder recorrente | 5 | 0,5575 [0,5455; 0,5694] | 0,6594 [0,6536; 0,6652] | 0,5193 [0,5090; 0,5296] | 0,1486 [0,1387; 0,1585] | 0,0782 [0,0330; 0,1234] | 0,0440 | 0,9173 |
| HAI 23.05 | Autoencoder PCA | 1 | 0,7677 | 0,3072 | 0,6371 | 0,3582 | 0,3410 | 0,0184 | 0,7073 |
| HAI 23.05 | Distância robusta | 1 | 0,7145 | 0,2942 | 0,6078 | 0,3396 | 0,3910 | 0,0040 | 0,7805 |
| HAI 23.05 | Autoencoder recorrente | 5 | 0,7225 [0,7158; 0,7292] | 0,3372 [0,3324; 0,3419] | 0,6543 [0,6496; 0,6589] | 0,3513 [0,3220; 0,3807] | 0,3181 [0,2837; 0,3525] | 0,0329 | 0,6585 |
| LID-DS 2021 | Unigrama categórico | 1 | 0,5693 | 0,5950 | 0,5056 | 0,0220 | 0,0747 | 0,0000 | 0,9889 |
| LID-DS 2021 | Autoencoder PCA | 1 | 0,6359 | 0,6748 | 0,5056 | 0,0220 | 0,0747 | 0,0000 | 0,9889 |
| LID-DS 2021 | Distância robusta | 1 | 0,6191 | 0,6620 | 0,5278 | 0,1053 | 0,1690 | 0,0000 | 0,9444 |
| LID-DS 2021 | Autoencoder recorrente | 5 | 0,5438 [0,5171; 0,5705] | 0,5602 [0,5357; 0,5847] | 0,5044 [0,4987; 0,5102] | 0,0291 [-0,0017; 0,0600], n=3 | 0,0852 [0,0403; 0,1300], n=3 | 0,0000 | 0,9911 |

F1 aparece como não definido quando uma execução não teve verdadeiro positivo. No autoencoder recorrente do LID-DS 2021, F1 e MCC tiveram três valores finitos para o cálculo da estatística, por isso a tabela informa `n=3` nessas duas medidas. Isso preserva o resultado real, sem trocar um valor não definido por zero. O limite inferior negativo mostrado no intervalo de F1 vem do cálculo estatístico entre sementes e não significa que foi observada uma medida F1 negativa.

Para o autoencoder recorrente, FPR e FNR na tabela são as médias das cinco sementes. Para os demais modelos, elas são os valores da execução autenticada.

Fonte: `evidence/academic/thesis-evaluation-v2/73c6eadb15c3c35a/reports/matrix-v2-resultados-data-de-corte.md`.

#### 4.6.2 Estabilidade do autoencoder recorrente

| Base | Repetições | AUROC médio | Desvio padrão | Intervalo de confiança de 95% |
| --- | ---: | ---: | ---: | --- |
| ADFA-LD | 5 | 0,5575 | 0,0096 | [0,5455; 0,5694] |
| HAI 23.05 | 5 | 0,7225 | 0,0054 | [0,7158; 0,7292] |
| LID-DS 2021 | 5 | 0,5438 | 0,0215 | [0,5171; 0,5705] |

O resultado mais alto do autoencoder recorrente foi observado no HAI 23.05. Também foi a base com menor variação de AUROC entre as cinco sementes. No ADFA-LD, a variação foi pequena, mas o valor de AUROC ficou perto de 0,56. No LID-DS 2021, a variação foi maior e o AUROC médio ficou perto de 0,54. Esses números mostram que o comportamento do modelo depende do tipo de dado, da unidade de análise e da forma como cada base representa ataque e normalidade.

#### 4.6.3 Resultado no ADFA-LD

No ADFA-LD, o unigrama categórico teve AUROC de 0,5651. O autoencoder recorrente teve AUROC médio de 0,5575, com intervalo de confiança de 95% entre 0,5455 e 0,5694. Os dois valores ficaram próximos. O autoencoder recorrente apresentou AUPRC médio de 0,6594, enquanto o unigrama teve 0,6730.

No ponto de decisão definido na validação, o autoencoder recorrente teve FNR médio de 0,9173. Isso mostra que ele deixou passar uma parcela grande dos ataques nesse limiar. Esse resultado é importante porque deixa claro que AUROC e desempenho operacional no limiar precisam ser lidos juntos. O modelo conseguiu ordenar parte dos casos, mas o ponto de decisão adotado foi conservador para essa base.

#### 4.6.4 Resultado no HAI 23.05

O HAI 23.05 foi a base em que o autoencoder recorrente mostrou o maior AUROC médio, 0,7225. O autoencoder PCA teve AUROC de 0,7677, que foi o maior valor de AUROC entre os métodos executados nessa base. Porém, o autoencoder recorrente teve a maior AUPRC, 0,3372, e a maior acurácia balanceada, 0,6543. Isso mostra que os modelos não foram iguais em todas as métricas.

O HAI 23.05 tem muitos blocos normais e menos blocos de ataque. Por isso, olhar apenas para AUROC poderia esconder parte do comportamento. A AUPRC, a acurácia balanceada e o FNR ajudam a mostrar o resultado de uma forma mais completa. O autoencoder recorrente teve FNR médio de 0,6585. Portanto, ele identificou parte dos ataques, mas ainda deixou ataques sem alerta no limiar configurado.

#### 4.6.5 Resultado no LID-DS 2021

No LID-DS 2021, o autoencoder PCA teve AUROC de 0,6359 e a distância robusta teve 0,6191. O autoencoder recorrente teve AUROC médio de 0,5438. No ponto de decisão, os FNRs foram altos para todos os métodos, com valor médio de 0,9911 no autoencoder recorrente. Isso mostra que a tarefa ficou difícil para a decisão baseada no limiar definido na validação.

O LID-DS 2021 possui rótulos no nível de gravação. Isso quer dizer que a base informa a condição da gravação, mas não indica exatamente onde dentro da sequência o ataque começa ou termina. Essa característica precisa ser considerada ao interpretar F1, FNR e a comparação entre modelos. O resultado da base não foi escondido nem ajustado: ele aparece com suas métricas e com o número efetivo de repetições usadas no cálculo de F1 e MCC.

#### 4.6.6 Resultado do conjunto customizado

O conjunto customizado não entra como uma quarta linha da tabela de AUROC porque ele responde a outra pergunta. Enquanto ADFA-LD, HAI 23.05 e LID-DS 2021 foram usados para comparar detectores em um protocolo comum, o conjunto customizado mostra se o pipeline conseguiu juntar a leitura física, o rastro de syscall e a inferência na mesma rodada.

Esse resultado foi obtido. As quatro campanhas preservaram 17 linhas sincronizadas. Duas inferências do autoencoder foram gravadas e as duas ficaram abaixo do limiar, sendo classificadas como normais. A campanha de exclusão de edge também ficou normal no autoencoder porque exclusão de edge não é, por si só, uma anomalia física. Os indicadores físicos de mau funcionamento, saturação e partida fria estavam zerados nos registros dessa campanha.

Existe um cálculo legado feito sobre duas linhas, uma normal e uma de exclusão de edge, que apresenta acurácia de 0,5000 e macro F1 de 0,3333. Esse cálculo é mantido no repositório para rastreabilidade, mas não é usado como medida de desempenho da tese. Ele possui somente duas linhas, ambas previstas como normais, e não representa uma comparação estatística com as três bases da Matriz V2.

#### 4.6.7 Leitura conjunta dos resultados

Os resultados mostram que não existe um único detector com o mesmo comportamento em todas as bases. No HAI 23.05, o autoencoder recorrente mostrou maior estabilidade entre sementes e bons resultados em AUPRC e acurácia balanceada. No ADFA-LD, o unigrama categórico e o autoencoder recorrente tiveram AUROC próximo. No LID-DS 2021, os modelos PCA e de distância robusta ficaram acima do autoencoder recorrente em AUROC.

Essa diferença faz sentido porque as bases não são iguais. HAI 23.05 usa sinais de processo industrial, enquanto ADFA-LD e LID-DS 2021 usam sequências de chamadas de sistema. Também mudam o tamanho do teste, a proporção entre normal e ataque e a unidade que recebe o rótulo. Por isso, a tese não apresenta uma média global entre bases. A leitura correta é feita dentro de cada base e dentro das métricas que ela permite interpretar.

O corpus usado nesta dissertação consumiu 4,3615 horas de CPU e 5,1265 horas de relógio na execução que produziu as 23 células. Esse valor serve para registrar o custo de processamento do experimento. Ele não é uma medida de qualidade do detector e não foi usado para escolher modelo.

#### 4.6.8 Nota sobre o alcance estatístico

Os resultados estatísticos desta dissertação são formados pelas execuções efetivamente concluídas. Para o autoencoder recorrente, cada base possui cinco repetições com sementes diferentes e intervalo de confiança entre sementes. Para os modelos determinísticos, cada combinação possui uma execução autenticada. Portanto, as diferenças desses modelos são mostradas como diferenças observadas e não como uma significância calculada entre pares de repetições.

No HAI 23.05, existem duas gravações-fonte. Por isso, a tese não apresenta intervalo por agrupamento de gravações nessa base, pois esse cálculo exigiria pelo menos cinco grupos independentes. Isso não remove as métricas calculadas no teste nem os intervalos entre as cinco sementes do autoencoder recorrente. Apenas deixa claro qual estatística está sendo mostrada em cada parte da análise.

## 5 Trabalhos relacionados

Os trabalhos relacionados ajudam a situar a proposta. Eles não são usados para afirmar que duas arquiteturas diferentes têm o mesmo resultado numérico. A comparação é feita pelo problema que cada trabalho trata, pelo tipo de dado usado e pela forma como cada um trata a confiança no ambiente industrial.

| Trabalho | Ponto principal | Relação com esta dissertação | Diferença da proposta |
| --- | --- | --- | --- |
| Niedermaier, Kreimel e Golling, 2019 | Detecção de intrusão em dispositivos industriais com menor capacidade. | Apoia o uso de processamento próximo ao processo. | Não parte de uma fonte física paralela para comparar com SCADA. |
| Nascimento, 2019 e 2023 | IDS, edge, aprendizado de máquina e ambientes distribuídos. | Apoia a descentralização e o uso de aprendizado para segurança. | A proposta acrescenta a observação física independente antes da comparação digital. |
| Blanchard e colaboradores, 2017 | Efeito de participantes bizantinos em decisões distribuídas. | Apoia a necessidade de não confiar cegamente em todos os nós. | O trabalho aplica essa preocupação ao fluxo de observação física no edge. |
| Olanrewaju-George e Pranggono, 2024 | Aprendizado distribuído para IDS em IoT. | Apoia a discussão sobre nós limitados e arquitetura distribuída. | A proposta não depende apenas de rede ou logs, pois também preserva a leitura física. |
| Proposta desta dissertação | Fonte física paralela, validação distribuída, comparação com SCADA e fingerprint. | Integra os pontos anteriores em um único fluxo. | Usa a leitura física como referência antes de aceitar o valor digital como confiável. |

O principal espaço tratado pela proposta está na relação entre o físico e o digital. Um IDS baseado somente em rede pode identificar padrões estranhos na comunicação. Um modelo temporal pode identificar um comportamento fora do padrão. Mas, se o valor que chega ao sistema já foi alterado de forma plausível, esses mecanismos podem começar por uma informação que não representa mais o processo. A Fonte de Verdade Física Paralela foi proposta para reduzir essa dependência.

Fonte: `docs/input/Arquitetura Baseada em Fonte de Verdade Paralela para Geração de Fingerprint Físico-Operacional em Sistemas Industriais Legados_REVISAO_DA_LITERATURA.txt`.

## 6 Considerações finais

Esta dissertação apresentou uma arquitetura para aumentar a confiança em dados de processo de sistemas industriais legados. A ideia central foi criar uma Fonte de Verdade Física Paralela, observada antes do CLP e comparada com o caminho digital usado pelo SCADA. A proposta foi implementada em um protótipo que reuniu coleta no edge, mensageria, validação distribuída, comparação com SCADA, armazenamento e geração de artefatos para aprendizado.

Os testes de cenário mostraram o comportamento esperado do pipeline. Em operação normal, o artefato foi aceito e persistido. Em perda de quórum, o fluxo foi interrompido. Quando um edge foi excluído, o sistema preservou o quórum com os participantes consistentes. Quando apareceu divergência entre a leitura física e o SCADA, o dado não seguiu como registro confiável. Esses resultados mostram que a arquitetura não depende apenas de uma visão digital para decidir se um dado pode continuar no fluxo.

Na etapa de avaliação de detectores, a Matriz V2 produziu 23 execuções completas em ADFA-LD, HAI 23.05 e LID-DS 2021. O autoencoder recorrente foi repetido cinco vezes em cada base. Isso permitiu apresentar média, desvio padrão e intervalo de confiança de 95% para as métricas entre sementes. O HAI 23.05 apresentou o maior AUROC médio do autoencoder recorrente, 0,7225. ADFA-LD apresentou AUROC médio de 0,5575 e LID-DS 2021 apresentou 0,5438. As demais métricas mostraram que a qualidade da ordenação e o resultado no limiar precisam sempre ser analisados juntos.

O conjunto próprio também trouxe um resultado importante para a arquitetura. Foram preservadas quatro campanhas com 17 linhas que ligam a medida de corrente, os rastros de syscall e a rodada de execução. Isso mostra que a arquitetura conseguiu registrar dados físicos e operacionais no mesmo fluxo. A apresentação separada desse material protege o significado dos números: ele é uma evidência de integração do protótipo, enquanto a Matriz V2 é a comparação estatística entre as três bases públicas.

O trabalho deixa uma base concreta para continuidade. A arquitetura, os cenários, os artefatos e as tabelas já estão registrados. Em uma próxima etapa, podem ser feitas novas campanhas próprias com mais inferências do autoencoder e rótulos separados para evento físico, evento de syscall, replay e condição do pipeline. Esse avanço aumentaria o conjunto próprio sem mudar o resultado já apresentado nesta dissertação.

## Referências

1. BLANCHARD, P.; EL MHAMDI, E. M.; GUERRAOUI, R.; STAINER, J. Machine learning with adversaries: Byzantine tolerant gradient descent. Advances in Neural Information Processing Systems, 2017.
2. CAVALCANTE, E.; BATISTA, T.; BARROS, F.; PITANGA, M. Context-aware security in the Internet of Things: A review. 2017.
3. CREECH, G.; HU, J. Generation of a New IDS Test Dataset: Time to Retire the KDD Collection. IEEE WCNC, 2013.
4. NASCIMENTO, F. A. M. Intrusion Detection System for IoT: Opportunities and Challenges Offered by Edge Computing and Machine Learning. Future Generation Computer Systems, 2019.
5. NASCIMENTO, F. A. M. Decentralized Federated Learning-Based Intrusion Detection in IoT Systems. Tese de doutorado, Escola Politécnica, PUCRS, 2023.
6. NIEDERMAIER, M.; KREIMEL, P.; GOLLING, M. Efficient intrusion detection on low-performance industrial IoT edge node devices. IEEE International Conference on Industrial Cyber-Physical Systems, 2019.
7. OLANREWAJU-GEORGE, B.; PRANGGONO, B. Federated learning-based intrusion detection system for the Internet of Things using unsupervised and supervised deep learning models. 2024.
8. GRIMMER, M.; KAELBLE, F.; et al. LID-DS: A New Dataset for Linux Host-Based Intrusion Detection. LID-DS, 2021.
9. HAI. HIL-based Augmented ICS Security Dataset, versão 23.05.

## Apêndice A. Rastreabilidade dos resultados

| Parte do texto | Fonte de verificação |
| --- | --- |
| Arquitetura, serviços e cenários | `docs/results-of-the-prototype.md` |
| Estrutura usada para organizar a dissertação | `docs/guia-estrutura-tese-base-assis.md` |
| Metodologia e escopo original | `docs/input/Arquitetura Baseada em Fonte de Verdade Paralela para Geração de Fingerprint Físico-Operacional em Sistemas Industriais Legados_METODOLOGIA_DE_PESQUISA.txt` |
| Resultados da Matriz V2 | `evidence/academic/thesis-evaluation-v2/73c6eadb15c3c35a/reports/matrix-v2-resultados-data-de-corte.md` |
| Tabelas em CSV e manifesto de resultados | `evidence/academic/thesis-evaluation-v2/73c6eadb15c3c35a/reports/` |
| Conjunto customizado de corrente e syscalls | `docs/conjunto-customizado-autoencoder-syscalls-para-tese.md` |
| Auditoria do conjunto customizado | `evidence/academic/thesis-evaluation-v2/73c6eadb15c3c35a/reports/pilot-custom-track-readiness.json` |

Para regenerar as tabelas da Matriz V2 a partir das células de origem, use o comando abaixo no diretório do projeto:

```powershell
.venv\Scripts\python.exe scripts\build_thesis_result_cutoff.py
```
