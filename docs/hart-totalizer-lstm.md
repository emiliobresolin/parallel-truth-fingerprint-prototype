# Campo HART complementar para a LSTM: Totalizador 1

Pesquisa e implementação autorizadas por Emilio em 31/10/2026. O objetivo é acrescentar um campo HART com significado operacional, preservando a entrada em corrente dos quatro instrumentos e a comparação com a configuração anterior.

## Fontes e campo escolhido

O manual oficial **Endress+Hauser BA01992D/06/EN/03.23-00**, p. 72–74, permite o totalizador como SV e identifica **Totalizador 1 como Device Variable 6**. As p. 103–104 descrevem a atribuição da vazão mássica e o modo de totalização; as p. 128–133 tratam de leitura e reset. Seleção do cenário: FIT-101, massa em kg, ar, sentido positivo, sem reset durante o episódio. [Manual oficial](https://bdih-download.endress.com/file/9bf358f8845b222e0c1c5d9b8b0573bf/BA01992DEN_0323-00.pdf), [cópia local](reference-archive/documents/EndressHauser_t-mass_F300_HART_BA01992DEN_0323-00.pdf).

O **ABB COMMANDER 200, IM/C200-RST**, introdução à totalização, p. impressa 13 / PDF p. 15, documenta a integração da vazão no tempo e as bases de tempo em segundos, minutos ou horas. Sustenta o princípio operacional e a conversão de unidade usados no acumulador emulado. [Fonte oficial](https://library.e.abb.com/public/65f6260d570a63de8025693d003066c7/IM_C200-RST_1.pdf), [cópia local](reference-archive/documents/ABB_IM_C200_RST_1_Totalizer.pdf).

As fontes sustentam a existência e o significado do totalizador. O esquema numérico de acumulação e o pré-processamento abaixo são escolhas declaradas do protótipo; não reproduzem firmware comercial.

## Comparação dos candidatos

| Campo | Documento / evidência local | Informação e encaminhamento |
|---|---|---|
| Corrente de malha | Contrato atual e manuais instrumentais | Manter as quatro séries de corrente |
| PV e percentual de faixa | Gerador atual e documentação HART já arquivada | No código atual são projeções da corrente; sua inclusão repetiria informação |
| SV de temperatura/pressão hoje emulada | `simulator.py`, função `_secondary_variable_from_loop_current` | Calculada da própria corrente; não usar como medição independente |
| Temperatura da eletrônica | Siemens A5E41864807-AC, p. 168, seção de mapeamento dinâmico | Campo documentado. Sua evolução temporal ainda não tem geração fundamentada no protótipo; não criar uma curva térmica para preencher a entrada |
| Diagnósticos de falha, saturação e partida | Campos já presentes nos payloads e schemas | Na coleta 606, os doze atributos ficaram em zero nas 690 observações de cada perfil. Preservar nos registros e conferir semântica no P14; não apresentá-los como informação variável aprendida nesse ensaio |
| Totalizador 1 | Manual t-mass F 300, localizadores acima | Selecionado como memória de massa acumulada; usar incrementos temporais além das correntes |
| Tags, timestamps, IDs e rótulos | Organização dos registros | Usar para rastreabilidade e conferência da cadência; excluir dos atributos numéricos do detector |

O manual Siemens consultado é [SITRANS TH100/TH320/TH420/TR320/TR420/TF320/TF420, A5E41864807-AC](https://cache.industry.siemens.com/dl/files/149/109793149/att_1053674/v1/A5E41864807-ACen_TH320420_TR320420_TF320420_HART_OI_en-US.pdf), [cópia local](reference-archive/documents/Siemens_SITRANS_TH320420_HART_OI_A5E41864807-AC_EN.pdf). A pesquisa não transfere suas especificações para instrumentos diferentes.

## Representação e geração

O totalizador é estado temporal do instrumento. Ele compartilha a origem física com a vazão; não constitui um quinto sensor ou uma medição estatisticamente independente. Uma leitura instantânea de corrente não determina o histórico acumulado, o que motiva avaliar sua informação complementar.

A emulação opcional acumula a vazão mássica interna em cada subpasso, antes do amortecimento/ruído do estágio de corrente:

```
M[k] = M[k-1] + max(q[k], 0) × dt / 3600
```

`q` está em kg/h, `dt` em segundos e `M` em kg. A divisão por 3600 converte segundos para horas. A vazão por subpasso é mantida constante para essa integração discreta. O modelo de processo preexistente continua sujeito à auditoria de dependências; a inclusão do contador não valida seus parâmetros físicos.

A observação transporta SV `Totalizer_1_Mass`, unidade kg. O código de unidade HART não será inventado: o envelope mantém `unit_code=None`, com a unidade textual e o identificador de variável na configuração explícita. A corrente continua em mA; a massa não é convertida em uma tolerância de consenso entre grandezas diferentes.

## Entrada temporal e proteção contra pistas artificiais

O contador absoluto fica preservado no payload e na persistência. A entrada proposta usa **incrementos de massa entre observações consecutivas do mesmo episódio**, divididos por uma massa de referência fixa:

```
delta_M = M[k] - M[k-1]
M_ref = configured_upper_flow_kg_h × nominal_interval_seconds / 3600
feature = delta_M / M_ref
```

A referência vem da configuração previamente fixada, sem ajuste pelos dados de teste. O valor configurado de 1.000 kg/h é do cenário emulado, não uma especificação universal do equipamento. Não entram no tensor o total absoluto, o tempo decorrido, as identidades ou os rótulos. A transformação conserva a informação de massa movimentada entre aquisições, em lugar de fornecer o nível crescente do contador como indicador de idade do registro.

Cada partição e episódio mantém seu próprio histórico. O replay reapresenta a sequência histórica de SV junto com a corrente. Os incrementos são calculados dentro de cada ramo e não cruzam a entrada do ataque. Os offsets 0 e 1 ficam como aquecimento em todas as condições e nos dois modelos comparados. Assim, uma queda do contador ao entrar no replay não se torna um sinal artificial exclusivo do ataque.

Na execução completa de protocolo proposto, as partições de 72/48/60 observações fornecem 70/46/58 janelas. Cada bloco de 30 observações fornece 28 janelas; cinco blocos fornecem 140 por condição e perfil. São 1.120 avaliações por método, sendo 560 normais e 560 de replay. Esses denominadores diferem do protocolo 606 e serão identificados nas tabelas.

## Caminho completo e comparação

O campo precisa atravessar observação, aquisição HART, replicação, vinculação da identidade da observação, seleção da fonte validada, SCADA, replay, persistência e preparação do tensor. Uma mudança apenas no SV deve afetar a concordância das cópias, mesmo se a corrente coincidir. O uso do hash de origem pelo consenso é distinto de interpretar fisicamente kg no aplicativo Go.

A entrada transacional atual valida os payloads antes da seleção por quórum. Um SV malformado, como valor não finito ou unidade incompatível, causa rejeição da rodada; não é substituído por zero. A divergência entre SVs válidos é tratada pela concordância das cópias e pelo quórum. Tolerar uma transação que contenha cópias malformadas exigiria revisar esse contrato de entrada, decisão separada da inclusão do campo. A qualificação existente com um validador parado tem seu próprio escopo operacional.

Modelo ampliado: duas amostras, cinco atributos por caminho (quatro correntes e um incremento de massa), dez atributos por instante. Controle de ablação: somente as quatro correntes por caminho, nas mesmas observações elegíveis e partições. Ambos usam a receita de treinamento previamente declarada e calibração normal separada. O escore relacional usa a divisão entre caminhos conforme a dimensão, sem assumir quatro atributos fixos.

Novos resultados terão protocolo, configuração e diretório próprios. A variação dos dados torna necessário avaliar a nova entrada em treinamento/calibração próprios; o comparativo não presume melhoria nem superioridade sobre os controles. Um aumento no número de atributos não substitui a análise da informação que eles contêm.

## Estado e condição de execução

A inclusão e a verificação técnica estão autorizadas. A coleta longa permanece condicionada ao fechamento das demais dependências experimentais já registradas no planejamento. A alteração opcional não substitui os resultados históricos nem reconstitui totalizadores para a semente 606. A dissertação será atualizada na etapa acordada de redação.

As cópias oficiais e seus hashes estão em `reference-archive/catalog/hart-totalizer-sources.v1.json`. Este registro documenta a seleção e a implementação. O resultado técnico é registrado separadamente em `output/dissertacao/professor_inputs/p14_hart_smoke.json`, após a verificação, preservando os hashes deste documento na versão executada.
