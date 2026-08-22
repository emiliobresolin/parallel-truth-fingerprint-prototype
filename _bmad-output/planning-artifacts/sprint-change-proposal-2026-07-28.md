---
type: sprint-change-proposal
date: 2026-07-28
status: approved-for-planning-g0a
approved_by: Emilio
approved_at: 2026-07-28
gate_status:
  G0a: PASS
  G0b: NOT_AUTHORIZED
change_classification: major
delivery_path: direct-adjustment
approval_scope: proposal-only
implementation_authorized: false
implementation_authorization_record: required-after-overlay-approval
official_retraining_allowed: false
triggered_by:
  - complete technical audit
  - user decisions recorded on 2026-07-28
documents_to_overlay_after_plan_approval:
  - prd.md
  - architecture.md
  - epics.md
  - requirements.md
  - scope.md
partially_supersedes:
  - course-correction-2026-05-21.md
  - prd-update-2026-05-21.md
  - architecture-update-2026-05-21.md
  - epics-update-2026-05-21.md
---

# Sprint Change Proposal — Validade Científica, Round-Trip OPC UA e Separação HIDS

## 1. Decisão executiva

Este plano propõe uma correção de curso aditiva, sem rollback geral e sem
integração de hardware industrial real.

O trabalho passa a ter três trilhas semanticamente separadas:

1. **Protótipo físico-lógico de laboratório:** sensores e compressor simulados;
   MQTT, CometBFT/ABCI, round-trip OPC UA, comparação e MinIO executados de
   verdade.
2. **Benchmark HIDS auxiliar:** ADFA-LD e, opcionalmente, LID-DS permanecem
   offline para validar classificação de sequências de syscalls, LSTM versus
   GRU, métricas e reprodutibilidade.
3. **Fingerprint cyber-físico futuro:** somente datasets industriais temporais
   semanticamente compatíveis, ou dados pareados produzidos pelo protótipo
   corrigido, poderão sustentar a alegação físico-operacional.

### Alegação acadêmica permitida após o recorte imediato

> O protótipo laboratorial demonstra aquisição simulada, comunicação MQTT
> real, replicação CometBFT/ABCI, avaliação distribuída das observações,
> comparação entre uma fonte física consensuada e uma fonte lógica
> independente lida por round-trip OPC UA real, além de persistência local
> verificável. Os resultados ADFA-LD/LID-DS são evidência auxiliar de HIDS e
> não constituem fingerprint físico do compressor.

### Decisões já confirmadas pelo pesquisador

- Implementar o round-trip OPC UA real de laboratório.
- Não integrar PLC, HART FSK, sensores ou SCADA industriais reais neste
  escopo.
- Manter ADFA-LD como benchmark HIDS auxiliar.
- Não usar ADFA-LD como prova do fingerprint físico-operacional.
- Planejar uma trilha posterior com datasets cyber-físicos públicos.
- Corrigir os problemas de validade científica antes de repetir treinamentos.

## 2. Motivo e classificação da mudança

A mudança é classificada como **Major** porque altera fronteiras arquiteturais,
alegações acadêmicas, critérios de aceite e a ordem do backlog. A rota proposta
é **Direct Adjustment**:

- preservar componentes reutilizáveis;
- corrigir contratos e integrações defeituosas;
- registrar os resultados anteriores como históricos e não conclusivos;
- substituir apenas as alegações e os caminhos incompatíveis;
- adicionar Epics 9–13 em um overlay append-only.

Não é necessário recomeçar o projeto. Também não é aceitável continuar apenas
com documentação, porque os defeitos atingem causalidade, liveness,
reprodutibilidade e validade das métricas.

## 3. Fronteira arquitetural proposta para aprovação

```text
                                PLANTA SIMULADA
                               /               \
                              /                 \
            RAMO FÍSICO REAL DE SOFTWARE        RAMO LÓGICO REAL DE SOFTWARE
              sensores -> Edges                   fake PLC / writer
                    -> MQTT                           -> OPC UA Server
                    -> CometBFT/ABCI                  -> OPC UA Client
                    -> estado consensuado             -> estado lógico observado
                              \                       /
                               \                     /
                                COMPARAÇÃO CORRELACIONADA
                                          |
                                 EVIDÊNCIA MINIO

 ADFA-LD/LID-DS -> trilha HIDS offline auxiliar -> sem promoção ao runtime físico

 Dataset industrial temporal -> trilha cyber-física futura -> gate próprio
```

### Invariantes

1. O fake PLC pode receber o mesmo `LabPlantSnapshot` que originou o ramo
   físico, mas nunca pode receber `ConsensusedValidState`. Uma mudança legítima
   da planta deve aparecer nos dois ramos; uma adulteração aplicada apenas no
   canal de aquisição físico não pode alterar o ramo lógico, e vice-versa.
2. O comparador recebe somente o snapshot reconstruído por uma sessão real
   `asyncua.Client`.
3. O servidor OPC UA executa em processo ou serviço distinto do consumidor.
4. Falha, timeout, snapshot não atômico, valor stale ou `Bad` quality no OPC UA bloqueiam a
   comparação e a persistência como artefato válido; não existe fallback em
   memória.
5. O runtime físico não importa, promove, carrega ou executa um modelo HIDS.
6. Um futuro modelo online exige o mesmo domínio e um contrato de features
   compatível com o runtime.

## 4. Revalidação dos pontos críticos

| Ponto | Decisão | Por que afeta a comprovação | Destino |
| --- | --- | --- | --- |
| SCADA derivado do próprio consenso | **MUST-FIX** | A comparação atual é circular e não prova independência físico × lógico | Epic 10 |
| Runtime não lê o servidor OPC UA | **MUST-FIX** | A fronteira industrial declarada é desviada por chamada em memória | Epic 10 |
| ABCI aceita entrada insuficiente e pode produzir `NaN` | **MUST-FIX** | Uma transação malformada pode quebrar liveness e AppHash | Epic 9 |
| IDs duplicados/desconhecidos e membership ambígua | **MUST-FIX** | A hipótese de até um Edge comprometido exige participantes conhecidos | Epic 9 |
| Estado Edge sem round/freshness e vínculo de origem | **MUST-FIX** | Observação antiga ou spoofed pode ser tratada como participação atual | Epic 9 |
| Falhas injetadas depois do MQTT | **MUST-FIX** | Os cenários atuais testam objetos Python adulterados, não o pipeline | Epic 9 |
| `quorum_loss` não representa indisponibilidade | **MUST-FIX** | Nome e evidência não correspondem ao fenômeno experimental | Epic 9 |
| Reset destrutivo a cada startup | **MUST-FIX** | Altura, estado e continuidade experimental são apagados | Epic 9 |
| MinIO sem durabilidade, imutabilidade e readback | **MUST-FIX** | Evidência pode desaparecer ou ser sobrescrita sem detecção | Epic 9 |
| Imagens não fixadas | **MUST-FIX** | O ambiente não é reproduzível entre execuções | Epic 9 |
| Split ADFA por janela/amostra e preprocessing global | **MUST-FIX** | Há risco de leakage entre treino, validação e teste | Epic 11 |
| Sweep seleciona hiperparâmetros pelo teste | **MUST-FIX** | O teste deixa de medir generalização independente | Epic 11 |
| Modelo “promovido” é refeito no carregamento | **MUST-FIX** | O runtime não usa exatamente o artefato avaliado | Epic 11/13 |
| ADFA promovido como fingerprint físico | **MUST-FIX de escopo** | Syscalls não representam temperatura, pressão, RPM ou HART | Epic 11 |
| Resultados e readiness antigos sobreafirmam validade | **MUST-FIX documental** | A evidência escrita não corresponde aos limites reais | Epics 9/11 |
| Três Edges lógicos no mesmo processo | **SHOULD, documentar** | É suficiente para o laboratório se a independência lógica for explícita | Epic 9 |
| TLS/PKI/IAM industrial, alta disponibilidade e WORM | **DEFER** | São hardening de produção, não premissas mínimas da hipótese | Trabalho futuro |
| PLC/HART físico e SCADA comercial | **DEFER** | O ambiente simulado é compatível com o protótipo acadêmico | Trabalho futuro |
| BBD/FABA executável | **DEFER** | Permanece inspiração conceitual; o algoritmo real deve ser descrito honestamente | Documentação |

## 5. Contratos arquiteturais propostos

### 5.1 `ConsensusRoundTxV2`

Campos mínimos:

- `schema_version`, `experiment_id`, `round_id`;
- `window_started_at`, `window_ended_at`;
- `membership_version` e `membership_hash`;
- participantes presentes e um estado único por participante;
- sensores obrigatórios, unidades, timestamps e valores finitos;
- identidade de origem verificável.

A membership autoritativa é `MembershipConfigV1`, persistida na configuração ou
no estado confiável da aplicação ABCI. A transação apenas referencia sua versão
e hash; ela nunca declara quem conta para o próprio quorum.

Para uma `MembershipConfigV1` de três Edges:

- dois ou três participantes conhecidos e frescos podem formar quorum;
- zero ou um participante resulta em `insufficient_participation`;
- duplicatas, desconhecidos, rodadas misturadas e números não finitos são
  rejeitados antes da heurística;
- o quorum é calculado contra a membership configurada, não contra um tamanho
  arbitrário recebido.

`CheckTx`, `ProcessProposal` e `FinalizeBlock` reutilizam a mesma validação
canônica. `FinalizeBlock` permanece defensivo e nunca permite `NaN`, panic ou
estado não serializável.

### 5.2 `ConsensusDecisionV2`

Campos mínimos:

- `validator_commit_status`;
- `edge_observation_validation_status`;
- `membership_version` e `membership_hash`;
- quorum esperado e participantes frescos recebidos;
- exclusões e causas estruturadas;
- estado válido ou causa estruturada de ausência.

Esse contrato separa a replicação/commit dos validadores CometBFT da heurística
de avaliação das observações Edge. BBD/FABA permanece referência conceitual e
não é apresentado como algoritmo executado.

### 5.3 `EdgeObservationV2`

Campos e regras mínimas:

- `experiment_id`, `round_id`, `sequence`, `publisher_id`;
- `observed_at`, `published_at`, sensor, unidade, PV, percentual e corrente;
- credencial individual e ACL por Edge em broker confiável de laboratório;
- `publisher_id` deve corresponder à credencial e ao tópico;
- QoS 1, `retain=false`, sessão limpa e resubscribe explícito após reconnect;
- deduplicação por `(publisher_id, round_id, sequence)`;
- deadline padrão de 2.000 ms após o fim da janela e skew futuro máximo de
  2.000 ms, congelados no manifesto antes da execução;
- coerência PV ↔ percentual ↔ 4–20 mA dentro de tolerância declarada.

Mensagens stale, futuras, duplicadas, fora de ordem, com origem divergente,
unidade errada, valor não finito ou incoerência física não alteram o estado
válido.

O threat model confia no broker e na rede local. HMAC, TLS e proteção contra
administrador do broker ficam fora deste recorte; devem ser reabertos se o
adversário de rede entrar na alegação.

### 5.4 `LabPlantSnapshotV1` e `ScadaLogicalSnapshotV1`

Campos mínimos:

- `sample_id`, `experiment_id`, `occurred_at`, `compressor_id`;
- temperatura, pressão e RPM com unidades;
- `source_id`, `scenario_mode` e indicador `simulated`;
- no snapshot lógico: `observed_at` e qualidade da fonte.

### 5.5 Address space OPC UA

NodeIds string estáveis:

- `Compressor1/Temperature`
- `Compressor1/Pressure`
- `Compressor1/Rpm`
- `Compressor1/ExperimentId`
- `Compressor1/SampleId`
- `Compressor1/ObservedAt`
- `Compressor1/Scenario`
- `Compressor1/SnapshotVersion`

O cliente registra endpoint, namespace, horário de início/fim da leitura,
source/server timestamps e `StatusCode` por nó em um `OpcUaReadReceiptV1`.

O writer usa `SnapshotVersion` como seqlock:

1. publica uma versão ímpar antes de alterar qualquer campo;
2. atualiza todos os nós do snapshot;
3. publica a próxima versão par somente depois de concluir.

Uma leitura é aceita somente quando:

- `ExperimentId` e `SampleId` correspondem exatamente ao snapshot físico
  preservado no estado consensuado;
- `SnapshotVersion` lido antes e depois dos demais nós é igual e par;
- todos os nós têm `Good` status;
- a diferença entre o timestamp de origem físico e lógico é no máximo 2.000
  ms, valor congelado no protocolo antes da execução.

Versão diferente, ID divergente, snapshot parcial ou skew acima do limite
invalidam toda a leitura, ainda que os valores numéricos coincidam.

### 5.6 `ExperimentRunManifestV1`

Campos mínimos:

- commit Git e lockfile;
- versões ou digests das imagens;
- configuração, membership, tolerâncias e seed;
- cenário e período da execução;
- IDs e hashes dos artefatos;
- política de reset;
- resultado dos quality gates.

## 6. Backlog proposto

Os Epics 7 e 8 permanecem no histórico. Este plano adiciona Epics 9–13 sem
renumerar o trabalho anterior.

### Epic 9 — Scientific Validity and Runtime Foundation

**Prioridade:** P0  
**Objetivo:** corrigir as premissas de causalidade, identidade, liveness,
reprodutibilidade e evidência que bloqueiam qualquer novo resultado oficial.

| Story | Entrega | Depends on | Critérios de aceite resumidos | Esforço |
| --- | --- | --- | --- | --- |
| 9.1 | Claims e threat model versionados | G0b | Separa arquitetura, integridade físico-lógica, HIDS e fingerprint físico; registra extrapolações proibidas e matriz cenário → componente comprometido → resultado esperado | S–M |
| 9.2 | Parâmetros e limites pré-registrados | 9.1 | Congela membership, quorum, normalização, limiares da heurística ABCI, tolerâncias SCADA e coerência física antes dos cenários; testa valores de fronteira e análise de sensibilidade; documenta que dois Edges coludidos não são tolerados | M |
| 9.3 | Validador canônico ABCI | 9.1–9.2 | `MembershipConfigV1` é externa à transação; testes cobrem 0/1, 2/3 e 3/3 participantes, membership autodeclarada, duplicata, ID desconhecido, sensor ausente, JSON inválido e `NaN`/Inf; `CheckTx`, `ProcessProposal` e `FinalizeBlock` decidem de forma consistente; uma válida posterior confirma sem perda de liveness | M |
| 9.4 | Estado Edge/MQTT round-scoped e autenticado | 9.1–9.2 | Mosquitto rejeita anônimo e escrita em tópico alheio; credencial/ACL, topic binding, QoS 1, `retain=false`, sessão/reconnect, deduplicação, TTL/skew e coerência física são testados em broker real | L |
| 9.5 | Cenários ponta a ponta honestos | 9.3–9.4 | `single_edge_byzantine` adultera antes do MQTT; `single_edge_unavailable` suprime publicação; `two_edges_unavailable` produz quorum insuficiente; `two_byzantine_inputs` permanece cenário distinto | M |
| 9.6 | Lifecycle não destrutivo | 9.3 | Startup preserva altura/AppHash/queries; reset é comando explícito, contido e auditado; dez ciclos de restart não perdem estado | M |
| 9.7 | MinIO verificável e ambiente fixado | 9.1 | Toda imagem usa digest imutável e builds locais registram hash de Dockerfile/context/lockfile; volume em `/data`, credenciais via configuração e versioning; mesmos bytes são idempotentes e bytes diferentes na mesma identidade são rejeitados antes do write; version-id, SHA-256 e readback são registrados, e um overwrite fora da API deve deixar a versão anterior recuperável; rodadas inválidas ficam fora do dataset válido | M |
| 9.8 | Evidence pack, gate aggregator e guard central | 9.1–9.7 | Um comando executa os P0, gera manifestos e retorna não zero para teste/evidência ausente; entrypoints oficiais de treino, sweep, avaliação, promoção e runtime legado consultam o guard antes de carregar dataset para `fit`, acessar locked test ou escrever artefatos; em bloqueio, registry, bucket e ponteiros permanecem byte a byte inalterados; dry-runs e auditorias read-only usam namespace isolado | M |

Decisão de segurança de laboratório:

- implementar identidade mínima real por Edge no MQTT;
- fornecer credenciais individuais por configuração de laboratório, sem
  versioná-las no repositório;
- documentar rede local controlada;
- declarar o broker e a rede local como parte confiável da base experimental;
- deixar HMAC, TLS corporativo, PKI, rotação automática e secret manager fora
  deste recorte.

A garantia MinIO deste recorte é **append-only aplicado pela aplicação +
versioning + tamper evidence por hash**. Ela não resiste a um administrador
malicioso com permissão para apagar versões. Object Lock/WORM e manifesto
assinado externamente permanecem trabalho futuro, e a alegação deve respeitar
esse limite.

### Epic 10 — OPC UA Laboratory Round-Trip

**Prioridade:** P0  
**Objetivo:** eliminar a circularidade e provar a fronteira OPC UA real sem
hardware industrial.

| Story | Entrega | Depends on | Critérios de aceite resumidos | Esforço |
| --- | --- | --- | --- | --- |
| 10.1 | Topologia e fake PLC independentes | G0b, 9.1–9.2 | O servidor executa separado do consumidor; o ramo lógico nasce de `LabPlantSnapshot`, nunca do consenso; o address space e a política de segurança de laboratório são explícitos | M |
| 10.2 | Writer lógico/scenario writer | 10.1 | Normal, offset, freeze e replay são aplicados antes da leitura, pelo ramo lógico; o writer não importa nem consulta consenso/comparação; usa seqlock, marcando versão ímpar antes das escritas e versão par ao concluir o snapshot | M |
| 10.3 | `asyncua.Client` independente e snapshot atômico | 10.1 | Reconstrói o estado somente por reads remotos e aceita apenas `SnapshotVersion` par e igual em double-read; timeout, disconnect, nó ausente, versão ímpar/divergente, ID divergente, skew, snapshot parcial, stale e `Bad` quality geram erro tipado | M |
| 10.4 | Wiring runtime → OPC → comparação | 10.1–10.3 | Um guard test falha se o runtime usar `_current_state`, node handle interno ou projeção do consenso; exige igualdade de `experiment_id/sample_id` e skew máximo de 2.000 ms | M |
| 10.5 | Matriz causal E2E | 10.4 | Mudança legítima da planta atualiza ambos os ramos; adulteração só no físico não muta o lógico; adulteração só no lógico não muta o físico; executa no mínimo 10 ciclos normais e 5 de offset, freeze, replay, snapshot misto e disconnect; qualquer leitura inválida gera zero persistência válida | M |
| 10.6 | Evidence pack OPC UA | 10.5 | Registra endpoint, NodeIds, versões, status, timestamps, snapshots antes/depois, round/sample IDs, decisão de comparação e resultado de persistência; agregador retorna não zero para expectativa ausente | S–M |

O caminho mínimo aceito é:

```text
PlantSimulator -> PhysicalBranch -> Edges/MQTT -> CometBFT/ABCI
PlantSimulator -> FakePlcWriter -> OPC UA Server -> OPC UA Client
estado consensuado + snapshot realmente lido -> comparação
```

### Epic 11 — Leakage-Safe ADFA-LD Auxiliary HIDS Benchmark

**Prioridade:** P1, depois dos gates P0  
**Objetivo:** manter ADFA-LD como benchmark auxiliar, corrigir o protocolo
experimental e repetir os resultados sem leakage.

| Story | Entrega | Depends on | Critérios de aceite resumidos | Esforço |
| --- | --- | --- | --- | --- |
| 11.1 | Separação HIDS/runtime e quarentena legada | G0b, 9.1, 9.8 | Runs usam `domain=HIDS`, `evidence_role=auxiliary`, `cyberphysical_claim=false` e `live_promotion_eligible=false`; o runtime ignora/rejeita ponteiros e modelos ADFA/LID existentes; startup prova que nenhum artefato HIDS é carregado; errata é append-only | S–M |
| 11.2 | Dataset card e `trace_id` | 11.1 | Archive, versão, checksum, citação, contagens e erros de parsing são registrados; cada trace mantém identidade antes de qualquer janela | M |
| 11.3 | Split 60/20/20 group-safe | 11.2 | Preserva o mandato externo 80/20: 80% development e 20% locked test por `trace_id`; development é dividido em 75% train e 25% validation, resultando 60/20/20; interseções são vazias e manifests byte-reproduzíveis | M |
| 11.4 | Preprocessing, windowing e agregação sem leakage | 11.3 | Vocabulário/scaler é fit apenas no train; janelas são geradas depois do split; caps/oversampling/class weights atuam só no train; para binary, a probabilidade de attack por trace é a média das janelas e threshold 0,5; para multiclass, usa média das probabilidades e `argmax`; a regra é congelada antes do test | M |
| 11.5 | Sweep somente por validação | 11.4 | LSTM e GRU usam o mesmo budget; ranking não lê o test; configuração é congelada antes da primeira leitura do locked test; cinco seeds por configuração final são pré-registrados | M |
| 11.6 | Artefato exato e verificável | 11.5 | Persiste pesos, label map, preprocessing, split, histórico e checksums; load nunca chama `fit`; labels recarregadas são idênticas e probabilidades têm `max_abs_diff <= 1e-6` no mesmo ambiente | M |
| 11.7 | Novo treinamento ADFA-LD | G-RETRAIN, 11.6 | Binary Normal × Attack é primário e seis classes é exploratório; cada seed acessa seu locked test uma única vez depois do freeze; relatório inclui média, desvio/IC, métricas por classe, FPR e matriz de confusão | M–L + compute |
| 11.8 | Relatório/dashboard honesto | 11.7 | Título e limitações dizem “benchmark HIDS auxiliar”; métricas ADFA não alimentam readiness de fingerprint físico e não aparecem como canal do compressor; PASS metodológico independe de atingir um F1 desejado | S–M |

O LID-DS continua disponível como segundo benchmark HIDS opcional. Ele deixa de
ser caminho crítico para a alegação físico-operacional.

Antes de `G-RETRAIN`, Story 11.2–11.3 pode ler o archive real somente pelo
entrypoint de auditoria read-only, para provenance, parsing, contagens, hashes e
construção/validação do split. Essa auditoria não chama `fit`, não calcula
métricas, não abre o locked test para modelagem e não escreve no registry
oficial. O gate bloqueia o primeiro treino, sweep ou avaliação oficial, não a
auditoria do dataset.

### Epic 12 — Cyber-Physical Dataset and Physical Fingerprint Track

**Prioridade de produto:** necessária para a alegação físico-operacional  
**Execução:** diferida para uma segunda autorização, após o baseline corrigido  
**Objetivo:** selecionar e avaliar dados realmente compatíveis com o fenômeno
industrial estudado.

| Story | Entrega | Depends on | Critérios de aceite resumidos |
| --- | --- | --- | --- |
| 12.1 | Rubrica e seleção de dataset | G0b, 9.1–9.2 | Exige séries temporais de processo, sensores/atuadores, ataques/falhas rotulados, agrupamento por run/equipamento, licença, provenance e compatibilidade de features |
| 12.2 | Protocolo de dados pareados | 12.1, G2 | Captura/representa canal físico, OPC UA lógico, consenso/quorum, regime e ground truth sob IDs e timestamps comuns |
| 12.3 | Pilot sem treino | 12.1–12.2 | Valida schema, clocks, unidades, missingness, labels e independência das fontes antes de definir a campanha |
| 12.4 | Protocolo ML cyber-físico pré-registrado | 12.1–12.3 | Congela tarefa, unidade de análise, variáveis, preprocessing, split/grouping, métricas primárias, seeds, espaço/budget de busca, regra de seleção, agregação temporal e failure criteria próprios do domínio; reutiliza a infraestrutura de gates de G3, nunca o protocolo HIDS |
| 12.5 | Campanha e partições imutáveis | G5a | A coleta cumpre o plano aprovado; split por run/equipamento/tempo é congelado; nenhuma janela cruza boundaries; locked test permanece inacessível ao tuner |
| 12.6 | Baselines e ablações | G5b | Compara regra simples e modelos temporais sob train-only preprocessing; ablações SCADA-only, physical+SCADA e physical+consensus+SCADA testam a contribuição da proposta |
| 12.7 | Avaliação físico-operacional | 12.6 | Reporta F1/recall/FPR, PR-AUC, detection delay, dispersão entre runs e failure analysis |
| 12.8 | Evidence package | 12.6–12.7 | Cada tabela/figura resolve até raw run IDs, manifests, hashes e scripts |

Um dataset público de outra planta pode comprovar capacidade em um domínio ICS,
mas não prova sozinho um fingerprint específico do compressor. Para essa
alegação, será necessário um dataset pareado do próprio protótipo ou uma fonte
externa semanticamente equivalente, com a limitação de simulação declarada.

### Epic 13 — Same-Domain Online Reintegration

**Status:** placeholder bloqueado; não detalhar nem implementar antes da
aceitação da Epic 12.

Escopo futuro mínimo:

- **13.1:** compatibilidade de schema/features e policy de promoção;
- **13.2:** carregamento de pesos verificáveis sem `fit`, inicialmente em
  shadow mode;
- **13.3:** paridade offline/online e medição de latência;
- **13.4:** dashboard por nível de evidência;
- **13.5:** rollback, quarentena/remoção do legado e decisão explícita antes de
  emitir alertas live.

## 7. Migração do backlog existente

Taxonomia:

- disposição de código: `RETAIN`, `AMEND`, `QUARANTINE` ou `DEFER`;
- disposição de evidência: `VALID_COMPONENT_ONLY`, `HISTORICAL_ONLY` ou
  `INVALID_FOR_FINAL_CLAIM`.

| Item anterior | Código | Evidência | Replacement story IDs | Estado final |
| --- | --- | --- | --- | --- |
| 3.1 fake OPC UA | AMEND | INVALID_FOR_FINAL_CLAIM | 10.1–10.6 | fonte independente + round-trip obrigatório |
| 3.2 comparação | RETAIN | VALID_COMPONENT_ONLY | 10.4–10.5 | lógica pura recebe snapshot OPC remoto |
| 3.3 outputs/alerts | AMEND | VALID_COMPONENT_ONLY | 10.4–10.6 | adiciona erros OPC tipados |
| 3.4 persistência | AMEND | INVALID_FOR_FINAL_CLAIM | 9.7, 10.5 | storage verificável e bloqueios corrigidos |
| 4.1 dataset físico | AMEND | VALID_COMPONENT_ONLY | 9.7, 12.2–12.5 | lineage futura; sem validade ML herdada |
| 4.2A dataset artifact | AMEND | VALID_COMPONENT_ONLY | 9.7, 12.5 | manifests e hashes novos |
| 4.2 autoencoder | QUARANTINE | HISTORICAL_ONLY | 12.6, 13.5 | demo legada, sem claim acadêmica |
| 4.3 inferência | QUARANTINE | HISTORICAL_ONLY | 12.6–12.7, 13.2–13.3 | substituição same-domain futura |
| 4.3A lifecycle | QUARANTINE | HISTORICAL_ONLY | 9.8, 13.2, 13.5 | runtime não treina |
| 4.4 replay ML | QUARANTINE | INVALID_FOR_FINAL_CLAIM | 10.5, 12.6–12.7 | replay OPC agora; ML só após Epic 12 |
| 4.5 cenários | AMEND | INVALID_FOR_FINAL_CLAIM | 9.5, 10.2, 10.5 | injeção antes do transporte |
| 6.1 readiness | AMEND | INVALID_FOR_FINAL_CLAIM | 11.8, 12.8 | separa HIDS auxiliar de físico |
| 6.5 replay rico | QUARANTINE | INVALID_FOR_FINAL_CLAIM | 10.5, 12.6–12.7 | sem claim ML atual |
| 7.1 scaffold/CLI | AMEND | VALID_COMPONENT_ONLY | 9.8, 11.1 | namespace e guard científico |
| 7.2 split 80/20 | AMEND | INVALID_FOR_FINAL_CLAIM | 11.3 | 60/20/20 group-safe |
| 7.3 history | AMEND | VALID_COMPONENT_ONLY | 9.8, 11.6 | manifests, hashes e pesos |
| 7.4 metrics | AMEND | VALID_COMPONENT_ONLY | 11.4, 11.7, 12.7 | agrega por trace e adiciona IC/PR-AUC/delay |
| 7.5 LSTM | RETAIN | VALID_COMPONENT_ONLY | 11.5–11.7 | modelo reutilizado, resultados não |
| 7.6 ADFA adapter | AMEND | INVALID_FOR_FINAL_CLAIM | 11.2–11.4 | preserva trace antes de windowing |
| 7.7 first ADFA run | AMEND | INVALID_FOR_FINAL_CLAIM | 11.7 | rerun após G-RETRAIN |
| 7.8 GRU baseline | RETAIN | INVALID_FOR_FINAL_CLAIM | 11.5–11.7 | comparação refeita sob mesmo protocolo |
| 7.9 ADFA sweep | AMEND | INVALID_FOR_FINAL_CLAIM | 11.5–11.7 | seleção passa a usar validation |
| 7.10 LID adapter | DEFER | VALID_COMPONENT_ONLY | futura extensão HIDS | fixture/adapter não é evidência física |
| 7.11 LID run | DEFER | INVALID_FOR_FINAL_CLAIM | futura extensão HIDS | fora do caminho crítico |
| 7.12 LID sweep | DEFER | INVALID_FOR_FINAL_CLAIM | futura extensão HIDS | fora do caminho crítico |
| 7.13 cross-benchmark | AMEND | INVALID_FOR_FINAL_CLAIM | 11.8, 12.7 | relatórios HIDS e físico separados |
| 8.1 promotion | QUARANTINE | HISTORICAL_ONLY | 11.1 | endorsement HIDS sem efeito live |
| 8.2 online inference | QUARANTINE | INVALID_FOR_FINAL_CLAIM | 13.1–13.3 | mismatch e refit proibidos |
| 8.3 autoencoder removal | AMEND | VALID_COMPONENT_ONLY | 11.1, 13.5 | quarentena agora, decisão final depois |
| 8.4 dashboard promoted run | AMEND | INVALID_FOR_FINAL_CLAIM | 11.8, 13.4 | painel HIDS separado |

Os seguintes registros recebem errata, sem apagar o histórico:

- `implementation-readiness-report-2026-05-21.md`;
- `evidence-gap-implementation-plan.md`;
- `docs/results-of-the-prototype.md`;
- artefatos de implementação 7.x/8.x que tratem o teste como seleção ou o
  ADFA como fingerprint físico.

## 8. Quality gates e congelamento de treinamento

### Estado atual

**FAIL — nenhum novo treinamento, sweep, promoção ou claim oficial está
autorizado.**

Dry-runs com dados sintéticos para testar código são permitidos se forem
marcados `non_evidence=true`, não escreverem no registry oficial e não alterarem
qualquer ponteiro de modelo.

### Infraestrutura dos gates

Story 9.8 implementa `GateManifestV1` e um agregador determinístico. Os
artefatos ficam em:

```text
_bmad-output/validation/gates/<git_sha>/<gate_id>/manifest.json
_bmad-output/validation/gates/<git_sha>/<gate_id>/raw/*
```

Todo manifesto registra:

- gate ID e estado;
- commit, influence closure de arquivos e hashes;
- lockfile, digests de todas as imagens e hashes de builds locais;
- dataset/split/protocolo quando aplicável;
- test IDs, comandos, exit codes e caminhos da evidência bruta;
- thresholds;
- `approved_by`, `approved_at` e SHA-256 do manifesto aprovado.

`scripts/evaluate_quality_gates.py --gate <id>` deve retornar código não zero
quando um P0 estiver ausente, skipped, `xfail`, flakey, sem artefato ou abaixo
do threshold. O approval record humano autoriza a transição, mas não substitui
os testes.

### Gates

| Gate | Depends on | Aprovadores/registro | Condição de PASS e evidence manifest | Desbloqueia |
| --- | --- | --- | --- | --- |
| G0a — Plan Approved | nenhum | research owner; status deste documento | Aprovação explícita desta proposta | somente overlays e ADRs; nenhum código |
| G0b — Implementation Authorized | G0a + overlays aprovados | research owner; `implementation-authorization-<date>.md` | Escopo/branch/gates autorizados explicitamente | implementação; treinamento continua congelado |
| G1 — Runtime Scientific Validity | G0b | technical reviewer + research owner; `G1/manifest.json` | Stories 9.1–9.8; `ABCI-P0`, `MQTT-P0`, `RESTART-P0`, `MINIO-P0` e `STACK-PIN-P0` completos | execução confiável do ramo físico |
| G2 — OPC UA Round-Trip Verified | G1 | technical reviewer + research owner; `G2/manifest.json` | Stories 10.1–10.6; `OPCUA-P0` comprova processo separado, snapshot estável e ausência de shortcut | claim arquitetural físico × lógico e piloto pareado |
| G3 — ML Protocol Ready | G0b + 9.1 + 9.8 | reproducibility reviewer + research owner; `G3/manifest.json` | Stories 11.1–11.6; auditoria ADFA read-only e isolada permitida; `ML-LEAK-P0`, `MODEL-PARITY-P0` e `HIDS-SCOPE-P0` verdes sem `fit` real nem uso do test para decisões | candidatura a retreino HIDS |
| G-RETRAIN — Official HIDS Retraining Authorized | G1 + G2 + G3 | research owner + methodological reviewer/advisor; `retraining-authorization.json` | Guard verifica hashes dos três gates, commit, protocolo, dataset e imagens antes do primeiro `fit`, sweep, avaliação ou write oficial com ADFA real | Story 11.7, exclusivamente HIDS auxiliar |
| G4 — HIDS Evidence Accepted | G-RETRAIN + 11.7 + 11.8 | reproducibility reviewer + research owner; `G4/manifest.json` | Cinco seeds, locked test, reload parity, métricas raw/agregadas e limitações completas; PASS metodológico não depende de F1 alto | publicação auxiliar; nunca runtime físico |
| G5a — Cyber-Physical Collection Ready | G1 + G2 + 12.1–12.4 | domain/method reviewer + research owner; `G5a/manifest.json` | Pilot, schema, labels, clocks, provenance, coverage plan e protocolo ML cyber-físico pré-registrados | somente campanha/coleta; zero treino |
| G5b — Cyber-Physical Dataset Locked | G5a + 12.5 | reproducibility reviewer + research owner; `G5b/manifest.json` | Raw/curated manifests e train/val/locked-test por run/equipamento/tempo estão imutáveis, sem overlap e vinculados ao protocolo 12.4 | Story 12.6 e treino cyber-físico |
| G6 — Physical Evidence Accepted | G5b + 12.6–12.8 | domain/method reviewer + research owner; `G6/manifest.json` | Locked test, baselines, ablações, failure analysis e lineage aceitos | detalhamento/execução da Epic 13 |
| G7 — Online Reintegration Verified | G6 + 13.1–13.5 | technical reviewer + research owner; `G7/manifest.json` | Pesos verificáveis, schema parity, shadow mode, latência, paridade e rollback testados | inferência física live |

A dependência de G1 e G2 em `G-RETRAIN` é uma decisão deliberada de governança
do milestone — não uma dependência técnica do HIDS. Ela implementa a decisão
do pesquisador de corrigir todos os pontos científicos críticos antes de
produzir novos números oficiais.

### Famílias de teste P0

| Test ID family | Gate | Evidência/threshold mínimo |
| --- | --- | --- |
| `ABCI-P0-*` | G1 | table-driven Go + rede real: entradas inválidas rejeitadas, válida posterior confirmada e três nós com mesma altura/AppHash |
| `MQTT-P0-*` | G1 | Mosquitto real: anonymous/cross-topic/stale/duplicate/out-of-order rejeitados; reconnect idempotente |
| `RESTART-P0-*` | G1 | dez restarts e `down/up` sem regressão de altura, AppHash ou queries |
| `MINIO-P0-*` | G1 | idempotência, colisão rejeitada, version-id, SHA readback, adulteração detectada e volume preservado |
| `STACK-PIN-P0-*` | G1 | nenhum `latest`/tag flutuante; todo serviço usa digest; build local registra Dockerfile/context/lockfile |
| `OPCUA-P0-*` | G2 | matriz planta legítima, falha só física, ataque só lógico, versão mista, ID/skew errado, stale, `Bad` e disconnect |
| `ML-LEAK-P0-*` | G3 | zero group overlap, fit train-only, zero acesso ao test no tuning e um acesso após freeze por seed |
| `MODEL-PARITY-P0-*` | G3/G4 | load sem `fit`, labels idênticas e `max_abs_diff <= 1e-6` no mesmo ambiente |
| `HIDS-SCOPE-P0-*` | G3/G4 | namespace/metadata auxiliares e rejeição de qualquer promoção ao slot físico |

### Regras do gate P0

- teste ausente, skipped, `xfail`, flakey ou sem evidência bruta conta como
  **FAIL**;
- uma mudança invalida apenas o gate cujo `influence_closure` inclui o
  arquivo/dado/ambiente/configuração alterado e todos os seus descendentes;
  mudanças fora dessa closure não reabrem gates independentes;
- métricas F1/accuracy isoladas nunca liberam promoção física;
- G4 HIDS não substitui G5a/G5b/G6 cyber-físicos.

## 9. Evidência mínima por claim

| Claim | Evidência mínima |
| --- | --- |
| Liveness e membership | Testes table-driven Go; membership confiável; bloco com inválidas seguido de válida; três nós na mesma altura/AppHash |
| Validade da heurística | Parâmetros pré-registrados, fronteiras, análise de sensibilidade e limites de colusão documentados |
| Freshness e origem Edge | Mosquitto real; rejeição de anônimo/spoof/stale/duplicata; cenário coerente atravessando MQTT |
| Continuidade | Altura, AppHash e queries preservados antes/depois de restart e `down/up` |
| Independência OPC UA | Processo servidor separado; mudança legítima da planta atualiza ambos; adulteração de um canal não muta o outro; snapshot versionado |
| Integridade da evidência | Volume persistente, append-only da aplicação, versioning, SHA-256, readback e detecção de adulteração dentro do threat model |
| HIDS sem leakage | Zero interseção de `trace_id`; preprocessing train-only; tuning sem acesso ao test; load sem `fit` |
| Limite semântico | Registry, relatório e dashboard impedem ADFA de satisfazer qualquer claim físico |

## 10. Ordem de execução recomendada

1. Aprovar somente este Sprint Change Proposal e fechar G0a.
2. Produzir overlays de PRD, arquitetura, requisitos, escopo e épicos, além dos
   ADRs.
3. Revisar os overlays; registrar autorização separada de implementação e
   fechar G0b.
4. Executar Epic 9 e fechar G1.
5. Executar Epic 10 e fechar G2.
6. Implementar Stories 11.1–11.6 e fechar G3, ainda sem retreinar.
7. Revisar e aprovar `retraining-authorization.json`.
8. Repetir ADFA-LD como HIDS auxiliar, fechar G4 e corrigir os relatórios.
9. Planejar/autorizar separadamente a Epic 12, usando G5a para coleta e G5b
   para treino.
10. Não executar Epic 13 antes de G6.

Trabalho independente dentro de uma mesma onda pode ser paralelizado, mas os
gates e a ordem de promoção não podem ser invertidos.

## 11. Impacto nos documentos

Após G0a, criar overlays datados para:

- PRD: revisar FR15–FR18 e FR24–FR29; adicionar contratos/gates de validade;
- arquitetura: registrar as três trilhas, a fonte lógica independente, o
  cliente OPC UA real e a proibição de HIDS no runtime físico;
- épicos: adicionar Epics 9–13 e a matriz de migração;
- requisitos e escopo: separar execução física-lógica, benchmark auxiliar e
  claim futuro;
- resultados: adicionar errata e remover conclusões que não sobrevivem à
  revalidação.

Esta proposta passa a controlar conflitos somente depois de G0a e apenas para
a elaboração dos overlays. Cada overlay identifica, por seção, o texto antigo
preservado, amendado ou superseded. O conjunto de overlays recebe um aceite
próprio antes de G0b; documentos-base não são modificados silenciosamente.

Cláusulas centrais do overlay de 2026-05-21:

- preservar a separação treino offline/runtime;
- reforçar histórico, métricas e provenance;
- superseder a simples divisão 80/20 por amostra;
- superseder integralmente a reintegração ADFA/LID ao runtime físico;
- superseder a afirmação de que Edge/MQTT, consenso, SCADA e MinIO não
  precisavam de mudanças.

## 12. Esforço e risco

| Bloco | Esforço | Risco principal |
| --- | --- | --- |
| Epic 9 | L | Mudanças cruzam Python, Go, MQTT e infraestrutura |
| Epic 10 | M–L | Concorrência, lifecycle e correlação temporal OPC UA |
| Epic 11 sem compute | M–L | Compatibilidade de artefatos e redesign do split |
| Rerun ADFA | M–L + compute | Métricas podem cair após remover leakage |
| Epic 12 | L | Seleção de domínio, qualidade/volume de dados e validade externa |
| Epic 13 | Não estimar antes de G6 | Contrato futuro ainda não está validado |

Estimativa honesta do recorte obrigatório até G4: **L**. A correção é
necessária para defender as alegações atuais; reduzir o esforço só é possível
reduzindo explicitamente as alegações.

## 13. Handoff e aprovação requerida

Esta proposta autoriza apenas planejamento. A aprovação desta proposta fecha
G0a e permite somente a geração de overlays/ADRs. Nenhum código, resultado ou
modelo pode ser alterado até um segundo aceite explícito, registrado em
`implementation-authorization-<date>.md`, fechar G0b.

Decisão solicitada:

- **Aprovar o plano:** gerar apenas overlays BMAD/ADRs; não iniciar código;
- **Aprovar com ajustes:** revisar este documento antes de executar;
- **Rejeitar:** manter o projeto atual, registrando formalmente as limitações e
  retirando as alegações afetadas.
