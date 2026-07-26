# Auditoria factual do prototipo para o Seminario de Andamento

Escopo: auditoria do workspace em `C:\Users\emili\OneDrive\Área de Trabalho\Projetos\parallel-truth-fingerprint-prototype\parallel-truth-fingerprint-prototype`. Este arquivo e o unico artefato criado por esta auditoria. Nao foram alterados codigo, configuracoes, datasets, modelos, MinIO ou logs.

## 1. Metodo e estado do repositorio

- Estado auditado: branch `main`, commit `ff685ffb94906974399f56154039ee79f890a40b`. Evidencia: comando `git rev-parse --abbrev-ref HEAD` e `git rev-parse HEAD`, executado nesta auditoria.
- A arvore ja estava suja antes da criacao deste relatorio, com alteracoes e arquivos nao versionados em `logs/`, `scripts/`, `src/`, `tests/`, `_bmad-output/` e `docs/seminario-andamento/`. Evidencia: `git status --short --branch`, executado antes deste arquivo ser criado.
- Python local e do `.venv`: `Python 3.14.5`. Evidencia: `python --version` e `.\.venv\Scripts\python.exe --version`.
- Docker local: Docker `29.5.2`, Docker Compose `v5.1.4`. Evidencia: `docker --version` e `docker compose version`.
- Dependencias declaradas: Python `>=3.14`, `asyncua>=1.1,<2`, `minio>=7.2,<8`, `numpy>=2,<3`, extra `runtime-demo` com `paho-mqtt>=2.1,<3`, extra `ml-training` com `keras>=3,<4` e `torch>=2,<3`. Evidencia: `pyproject.toml:4-9`.
- Nao rodei treinamentos longos. A auditoria e documental e estatica, com leitura de codigo, logs e artefatos existentes. Evidencia: este relatorio nao referencia novos artefatos de treinamento criados nesta sessao.

Atalhos para paths longos usados neste relatorio:

- `ARQ_PROP`: `docs/input/Arquitetura Baseada em Fonte de Verdade Paralela para Geração de Fingerprint Físico-Operacional em Sistemas Industriais Legados_ARQUITETURA_PROPOSTA.txt`.
- `FUND_TEOR`: `docs/input/Arquitetura Baseada em Fonte de Verdade Paralela para Geração de Fingerprint Físico-Operacional em Sistemas Industriais Legados_FUNDAMENTACAO_TEORICA.txt`.
- `INTRO`: `docs/input/Arquitetura Baseada em Fonte de Verdade Paralela para Geração de Fingerprint Físico-Operacional em Sistemas Industriais Legados_INTRODUÇÃO.txt`.

Vocabulário controlado de estado usado abaixo:

- IMPLEMENTADO E TESTADO: ha implementacao e evidencia de teste unitario, smoke ou execucao ao vivo.
- IMPLEMENTADO, MAS SEM EVIDÊNCIA DE TESTE: ha codigo, mas nao encontrei teste ou execucao correspondente.
- SOMENTE DOCUMENTADO: aparece em texto, proposta, tabela ou figura, mas nao encontrei implementacao.
- PLANEJADO: aparece como futuro, gap ou limitacao, sem implementacao atual.

## 2. Veredito executivo

| Item | Estado | Evidencia |
| --- | --- | --- |
| Pipeline local sensor -> edge -> MQTT -> consenso -> SCADA -> MinIO | IMPLEMENTADO E TESTADO | `scripts/run_local_demo.py:1102`, `docs/seminario-andamento/evidence/scenarios/normal/scenario-summary.md:1-37`, `logs/sem-normal.terminal.txt:1-48` |
| Simulador de compressor e sensores | IMPLEMENTADO E TESTADO | `src/parallel_truth_fingerprint/sensor_simulation/simulator.py:105-291`, `tests/sensor_simulation/test_simulator.py:7` |
| Payload HART-style | IMPLEMENTADO E TESTADO | `src/parallel_truth_fingerprint/contracts/raw_hart_payload.py:13-62`, `src/parallel_truth_fingerprint/edge_nodes/common/acquisition.py:191`, `tests/edge_nodes/test_acquisition_services.py:9-41` |
| Comunicacao MQTT entre edges | IMPLEMENTADO E TESTADO | `src/parallel_truth_fingerprint/edge_nodes/common/mqtt_io.py:123-205`, `tests/edge_nodes/test_mqtt_replication.py:91-103`, `compose.local.yml:2-6` |
| Consenso em CometBFT + ABCI Go | IMPLEMENTADO E TESTADO | `abci/consensus_app/internal/app/app.go:219-405`, `docs/seminario-andamento/evidence/scenarios/normal/scenario-summary.md:11-16`, `logs/sem-quorum-loss.terminal.txt:8-48` |
| BBD/FABA como algoritmo executado | SOMENTE DOCUMENTADO | Proposto em `ARQ_PROP:105-130`; nao ha ocorrencia de `FABA`, `BBD` ou `BBZ` em `src/`, `abci/` ou `tests/` na busca `rg -n "FABA|BBD|BBZ" src abci tests` |
| SCADA OPC UA fake | IMPLEMENTADO E TESTADO | `src/parallel_truth_fingerprint/scada/opcua_service.py:40-418`, `tests/scada/test_opcua_service.py:40-143` |
| SCADA real de planta, CLP real, instrumentacao real HART/Profibus | SOMENTE DOCUMENTADO | `docs/seminario-andamento/tables/prototype-limitations.md:11`, `ARQ_PROP:20-39` |
| Persistencia MinIO de artefatos validos | IMPLEMENTADO E TESTADO | `src/parallel_truth_fingerprint/persistence/service.py:31-139`, `docs/seminario-andamento/evidence/minio/minio-listing.txt:4-20` |
| Dataset proprio fisico-operacional | IMPLEMENTADO E TESTADO | `src/parallel_truth_fingerprint/lstm_service/dataset_builder.py:62-151`, `docs/seminario-andamento/evidence/custom-dataset/custom-dataset-analysis.md:4-59` |
| Dataset proprio com ataques e metricas F1/accuracy | PLANEJADO | `docs/seminario-andamento/evidence/custom-dataset/custom-dataset-analysis.md:65-78`, `docs/seminario-andamento/tables/prototype-limitations.md:4-5` |
| ADFA-LD binario com macro F1 0.9187 e accuracy 0.9229 | IMPLEMENTADO E TESTADO | `_bmad-output/implementation-artifacts/embedding-adfa-ld-binary-sweep.md:1-8`, `docs/seminario-andamento/tables/adfa-ld-binary-results.md:1-11` |
| ADFA-LD multiclasse aprovando D6 | IMPLEMENTADO E TESTADO, resultado negativo | `docs/seminario-andamento/tables/adfa-ld-multiclass-results.md:1-11` |
| Inferencia online local com campeao binario | PLANEJADO | `docs/seminario-andamento/tables/prototype-limitations.md:7-8`, `docs/seminario-andamento/evidence/online-inference/online-inference-summary.md` |

## 3. Fluxo tradicional e fluxo do prototipo

Fluxo tradicional correto para os slides:

1. Sensor ou instrumento de campo.
2. Sinal fisico, por exemplo 4-20 mA, HART, Profibus PA ou fieldbus.
3. CLP, tambem escrito como PLC em material em ingles.
4. Rede industrial e protocolos de controle ou supervisao.
5. SCADA ou HMI.

Evidencia documental: `FUND_TEOR:24-47` cita sensores/instrumentos, CLPs, 4-20 mA, HART, PROFIBUS-PA, Fieldbus, Modbus TCP, DNP3, OPC UA e SCADA. `INTRO:18-42` descreve CLP e SCADA/HMI como intermediarios do mundo fisico para o digital.

Fluxo implementado no prototipo:

1. `CompressorSimulator` gera temperatura, pressao e rpm. Evidencia: `src/parallel_truth_fingerprint/sensor_simulation/simulator.py:105-291`.
2. Cada edge adquire uma variavel local e constroi payload HART-style. Evidencia: `src/parallel_truth_fingerprint/edge_nodes/common/acquisition.py:65-191`.
3. Edges publicam e consomem observacoes via MQTT real ou relay passivo. Evidencia: `src/parallel_truth_fingerprint/edge_nodes/common/mqtt_io.py:123-205`.
4. O estado replicado de cada edge e enviado ao consenso CometBFT + ABCI. Evidencia: `src/parallel_truth_fingerprint/consensus/cometbft_client.py`, `abci/consensus_app/internal/app/app.go:219-405`.
5. O estado fisico consensado e comparado contra uma camada SCADA OPC UA fake. Evidencia: `src/parallel_truth_fingerprint/scada/opcua_service.py:40-418`, `src/parallel_truth_fingerprint/comparison/service.py:24-81`.
6. Se consenso e SCADA passam, o artefato e salvo no MinIO. Evidencia: `src/parallel_truth_fingerprint/persistence/service.py:31-139`.

Correcao necessaria: nao dizer que ha CLP real, splitter real, HART real, Profibus real ou SCADA industrial real. O prototipo simula sensores/planta/SCADA e usa infraestrutura real de laboratorio para MQTT, CometBFT, ABCI e MinIO. Evidencia: `docs/seminario-andamento/tables/infrastructure-components.md:4-15` e `docs/seminario-andamento/tables/prototype-limitations.md:11`.

## 4. Cinco pilares da proposta

| Pilar da proposta | Estado no prototipo | Evidencia |
| --- | --- | --- |
| 1. Duplicacao fisica nao intrusiva do sinal do sensor | SOMENTE DOCUMENTADO para hardware real; IMPLEMENTADO E TESTADO como simulacao | Pilar definido em `ARQ_PROP:11-16` e `ARQ_PROP:20-39`; simulacao em `src/parallel_truth_fingerprint/sensor_simulation/simulator.py:105-291` |
| 2. Coleta e descentralizacao das leituras fisicas via Edge Computing | IMPLEMENTADO E TESTADO | `src/parallel_truth_fingerprint/edge_nodes/common/acquisition.py:65-349`, `tests/edge_nodes/test_acquisition_services.py:9`, `tests/edge_nodes/test_mqtt_replication.py:91-103` |
| 3. Validacao distribuida tolerante a falhas bizantinas | IMPLEMENTADO E TESTADO, mas nao com BBD/FABA literal | Proposta BBD/FABA em `ARQ_PROP:105-130`; implementacao CometBFT/ABCI em `abci/consensus_app/internal/app/app.go:219-405`; logs em `docs/seminario-andamento/evidence/scenarios/quorum_loss/scenario-summary.md:11-25` |
| 4. Comparacao entre verdade fisica validada e dados logicos da rede industrial | IMPLEMENTADO E TESTADO com SCADA fake OPC UA, nao com rede industrial real | Proposta em `ARQ_PROP:239-250`; implementacao em `src/parallel_truth_fingerprint/comparison/service.py:24-81`; execucao em `logs/sem-scada-divergence.terminal.txt:16-45` |
| 5. Aprendizado profundo para fingerprint fisico-comportamental | IMPLEMENTADO E TESTADO em duas trilhas diferentes, com limitacoes | Dataset proprio runtime em `docs/seminario-andamento/evidence/custom-dataset/custom-dataset-analysis.md:29-59`; ADFA-LD offline em `docs/seminario-andamento/tables/adfa-ld-binary-results.md:1-11`; runtime autoencoder desabilitado no resultado principal em `logs/sem-normal.terminal.txt:21-23` |

## 5. Simulador, sensores e amostragem

O processo simulado e um compressor `compressor-1` com `compressor_power` de 0 a 100, temperatura de 48 a 95, pressao de 1.8 a 8.5, rpm de 1200 a 4200 e `base_noise_floor=0.15`. Evidencia: `src/parallel_truth_fingerprint/config/ranges.py:26`.

As variaveis implementadas sao temperatura, pressao e rpm. Evidencia: `SENSOR_TRANSMITTER_META` em `src/parallel_truth_fingerprint/sensor_simulation/simulator.py:86` e `SUPPORTED_SCADA_SENSORS` em `src/parallel_truth_fingerprint/scada/opcua_service.py:21`.

O modelo fisico e deterministico com seed quando o seed e fornecido. A execucao local usa `CompressorSimulator(seed=101)`. Evidencia: `src/parallel_truth_fingerprint/sensor_simulation/simulator.py:105-142` e `scripts/run_local_demo.py:883-886`.

Relacao operacional:

- `expected_sensor_values()` deriva temperatura, pressao e rpm da potencia normalizada, com defasagens e padroes senoidais. Evidencia: `src/parallel_truth_fingerprint/sensor_simulation/behavior_model.py:42-85`.
- `temperature_driven_noise_level()` aumenta o ruido conforme a temperatura cresce. Evidencia: `src/parallel_truth_fingerprint/sensor_simulation/behavior_model.py:86`.
- `_apply_noise()` aplica ruido por sensor e arredonda para 3 casas. Evidencia: `src/parallel_truth_fingerprint/sensor_simulation/simulator.py:222`.
- `_loop_current_from_percent()` calcula corrente 4-20 mA simulada como `4 + 16 * percent/100`. Evidencia: `src/parallel_truth_fingerprint/sensor_simulation/simulator.py:82`.
- Variavel secundaria existe para temperatura e pressao, mas nao para rpm. Evidencia: `src/parallel_truth_fingerprint/sensor_simulation/simulator.py:291`.

Amostragem documentada:

- O runtime tem `DEMO_STEPS=3` por ciclo e intervalo padrao `DEMO_CYCLE_INTERVAL_SECONDS=10`. Evidencia: `src/parallel_truth_fingerprint/config/runtime.py:63-65`.
- O README documenta os mesmos defaults. Evidencia: `README.md:148-150`.
- Frequencia fisica real de sensor, frequencia HART real, tempo de ciclo de CLP real e taxa de amostragem industrial real: NÃO DOCUMENTADO.

## 6. Edge gateways, payload e MQTT

Mapeamento dos edges:

| Edge | Sensor local | Tag | Gateway |
| --- | --- | --- | --- |
| `edge-1` | `temperature` | `TIT-101` | `GW-EDGE-01` |
| `edge-2` | `pressure` | `PIT-101` | `GW-EDGE-02` |
| `edge-3` | `rpm` | `RIT-101` | `GW-EDGE-03` |

Evidencia: `EDGE_DEVICE_CONFIGS` em `src/parallel_truth_fingerprint/edge_nodes/common/acquisition.py:65`.

O payload local e HART-style, nao HART real. Ele inclui `protocol="HART"`, `gateway_id`, timestamp, `device`, `process` e `diagnostics`. Evidencia: `src/parallel_truth_fingerprint/contracts/raw_hart_payload.py:13-62` e construcao em `src/parallel_truth_fingerprint/edge_nodes/common/acquisition.py:129-191`.

Cada edge publica a propria observacao e consome observacoes dos pares. Evidencia: `publish_local_observation()` em `src/parallel_truth_fingerprint/edge_nodes/common/acquisition.py:273`, `consume_peer_observation()` em `src/parallel_truth_fingerprint/edge_nodes/common/acquisition.py:306`.

O estado replicado antes do consenso e explicitamente nao validado. Evidencia: `EdgeLocalReplicatedStateContract.is_validated=False` e rejeicao de `is_validated=True` em `src/parallel_truth_fingerprint/contracts/edge_local_replicated_state.py:12-22`.

MQTT real:

- Broker: Eclipse Mosquitto em `compose.local.yml:2-6`.
- Porta: `1883:1883`, evidencia em `compose.local.yml:6`.
- Configuracao Mosquitto: `listener 1883` e `allow_anonymous true`, evidencia em `docs/infrastructure/mosquitto.conf:1-2`.
- Topico padrao: `edges/observations`, evidencia em `src/parallel_truth_fingerprint/config/runtime.py:55` e `README.md:141`.
- Topico efetivo por publisher: `RealMqttTransport.publish()` envia para `{topic}/{publisher_id}`. Evidencia: `src/parallel_truth_fingerprint/edge_nodes/common/mqtt_io.py:199-202`.

MQTT QoS, retain, TLS, autenticacao, ids persistentes e politica de retry: NÃO DOCUMENTADO no codigo de transporte, porque `publish()` e `subscribe()` sao chamados sem parametros de QoS ou retain. Evidencia: `src/parallel_truth_fingerprint/edge_nodes/common/mqtt_io.py:164-202`.

## 7. Consenso, quorum e tolerancia bizantina

O consenso usado no runtime e CometBFT com aplicacao ABCI em Go. Evidencia: `compose.consensus.yml:48-98`, `abci/consensus_app/go.mod:3-8`, `abci/consensus_app/internal/app/app.go:219-405`.

Ha 3 validadores CometBFT e 3 servicos ABCI. Evidencia: servicos `abci-node0`, `abci-node1`, `abci-node2` e `cometbft-node0`, `cometbft-node1`, `cometbft-node2` em `compose.consensus.yml:2-98`.

As portas RPC expostas sao 26657, 26667 e 26677. Evidencia: `compose.consensus.yml:62`, `:80`, `:98`.

O runtime vivo registrou CometBFT `node_version=0.39.0`. Evidencia: `docs/seminario-andamento/evidence/scenarios/normal/scenario-summary.md:13`, `docs/seminario-andamento/evidence/scenarios/quorum_loss/scenario-summary.md:13`, `docs/seminario-andamento/evidence/scenarios/scada_divergence/scenario-summary.md:13`.

O quorum e maioria simples: `(participant_count // 2) + 1`. Para 3 participantes, quorum requerido e 2. Evidencia: `src/parallel_truth_fingerprint/consensus/quorum.py:4`; logs em `logs/sem-normal.terminal.txt:12` e `logs/sem-quorum-loss.terminal.txt:12`.

Modelo de confianca implementado:

- Escalas: temperatura 20.0, pressao 3.0, rpm 600.0. Evidencia Python: `src/parallel_truth_fingerprint/consensus/trust_model.py:26`; Go: `abci/consensus_app/internal/app/app.go:27`.
- Threshold de consistencia par a par: 0.35. Evidencia Python: `src/parallel_truth_fingerprint/consensus/trust_model.py:31`; Go: `abci/consensus_app/internal/app/app.go:23`.
- Threshold para `suspected_byzantine_behavior`: 0.75. Evidencia Python: `src/parallel_truth_fingerprint/consensus/trust_model.py:32`; Go: `abci/consensus_app/internal/app/app.go:24`.
- A distancia normalizada e media das diferencas absolutas por sensor divididas pelas escalas. Evidencia Python: `src/parallel_truth_fingerprint/consensus/trust_model.py:44-52`; Go: `abci/consensus_app/internal/app/app.go:381-405`.
- Um edge e excluido quando `compatible_peer_count + 1 < quorum`. Evidencia Python: `src/parallel_truth_fingerprint/consensus/trust_model.py:109-151`; Go: `abci/consensus_app/internal/app/app.go:289-317`.
- O estado valido e a media dos valores dos edges nao excluidos, arredondada a 3 casas. Evidencia Go: `abci/consensus_app/internal/app/app.go:405`.

Correcao necessaria: o texto original do PEP fala em BBD/FABA, MAD e correlacao temporal de curto prazo. Evidencia: `ARQ_PROP:105-120`. O codigo atual nao implementa FABA literal, MAD ou correlacao temporal no consenso. Evidencia de ausencia: busca `rg -n "FABA|BBD|BBZ|MAD|median|Krum" src abci tests` nao encontrou ocorrencias; implementacao real esta nos thresholds par a par citados acima.

## 8. SCADA e comparacao fisico-logica

A camada SCADA implementada e `FakeOpcUaScadaService`, descrita no codigo como fake SCADA local. Evidencia: `src/parallel_truth_fingerprint/scada/opcua_service.py:1`, `:40-46`.

Ela expoe temperatura, pressao e rpm via OPC UA quando `asyncua` esta disponivel. Evidencia: `src/parallel_truth_fingerprint/scada/opcua_service.py:197-257`.

Modos suportados: `match`, `offset`, `freeze`, `replay`. Evidencia: `src/parallel_truth_fingerprint/scada/opcua_service.py:27`.

No modo normal `match`, o SCADA projetado replica o valor fisico consensado. Evidencia: `project_state()` em `src/parallel_truth_fingerprint/scada/opcua_service.py:146-166`; log normal com diffs 0.0 em `logs/sem-normal.terminal.txt:18` e `:42`.

Ruido e quantizacao no SCADA normal: nao ha novo ruido SCADA em `match`; o SCADA recebe o valor fisico ja arredondado/consensado. Evidencia: `src/parallel_truth_fingerprint/scada/opcua_service.py:146-166` e `logs/sem-normal.terminal.txt:18`. Ruido existe no simulador antes do consenso. Evidencia: `src/parallel_truth_fingerprint/sensor_simulation/simulator.py:222`.

Tolerancias da comparacao:

- Temperatura: 2.0.
- Pressao: 0.35.
- RPM: 120.0.

Evidencia: `ScadaToleranceProfile` em `src/parallel_truth_fingerprint/comparison/service.py:24-29`.

A regra de comparacao e `absolute_difference <= tolerance`. Evidencia: `src/parallel_truth_fingerprint/comparison/service.py:73-81`.

No cenario `scada_divergence`, o consenso passa, mas a comparacao bloqueia downstream por divergencia em temperatura, pressao e rpm. Evidencia: `logs/sem-scada-divergence.terminal.txt:16-45` e `docs/seminario-andamento/evidence/scenarios/scada_divergence/scenario-summary.md:18-26`.

OPC UA real de planta, Modbus TCP real, DNP3 real, EtherNet/IP real, PROFINET real e REST industrial real: SOMENTE DOCUMENTADO. Evidencia documental: `ARQ_PROP:239-250`. Evidencia de implementacao encontrada apenas para fake OPC UA: `src/parallel_truth_fingerprint/scada/opcua_service.py:40-418`.

## 9. Persistencia em MinIO

MinIO e real no ambiente local de laboratorio. Evidencia: `compose.local.yml:11-20` e `docs/seminario-andamento/tables/infrastructure-components.md:7`.

Imagem MinIO nao esta pinada por versao, usa `minio/minio:latest`. Evidencia: `compose.local.yml:12`.

Credenciais default: `minioadmin/minioadmin`. Evidencia: `compose.local.yml:16-17` e `README.md:144-145`.

Portas: API 9000 e console 9001. Evidencia: `compose.local.yml:14`, `:19-20`.

Persistencia so ocorre se o consenso final for `success` e houver `consensused_valid_state`. Evidencia: `src/parallel_truth_fingerprint/persistence/service.py:31-56`.

O objeto salvo usa chave `valid-consensus-artifacts/{round_id}.json`. Evidencia: `src/parallel_truth_fingerprint/persistence/service.py:56`.

O artefato inclui `round_identity`, `consensus_context`, `validated_state`, `dataset_context`, `scada_context` e `diagnostics`. Evidencia: `src/parallel_truth_fingerprint/persistence/service.py:59-139` e amostra em `docs/seminario-andamento/evidence/minio/sample-valid-consensus-artifact.pretty.json:1-519`.

Evidencia viva MinIO de 2026-06-23:

- Bucket `sem-normal` com 16 objetos. Evidencia: `docs/seminario-andamento/evidence/minio/minio-listing.txt:4`.
- 14 objetos em `valid-consensus-artifacts/`. Evidencia: `docs/seminario-andamento/evidence/minio/minio-listing.txt:7-20`.
- 1 manifest e 1 NPZ em `fingerprint-datasets/`. Evidencia: `docs/seminario-andamento/evidence/minio/minio-listing.txt:5-6`.
- `quorum_loss` e `scada_divergence` nao criaram bucket porque a persistencia foi bloqueada antes. Evidencia: `docs/seminario-andamento/evidence/minio/minio-artifacts-summary.md:9-17`.

## 10. Dataset fisico-operacional proprio

O dataset proprio e gerado a partir dos artefatos validos persistidos no MinIO, nao a partir de um arquivo estatico versionado. Evidencia: `src/parallel_truth_fingerprint/lstm_service/dataset_builder.py:62-82`, `src/parallel_truth_fingerprint/lstm_service/dataset_artifacts.py:61-228`, `docs/seminario-andamento/evidence/custom-dataset/custom-dataset-analysis.md:4-20`.

Criterios de elegibilidade:

- `final_consensus_status == "success"`.
- `training_label == "normal"`.
- `training_eligible == true`.
- `has_scada_divergence == false`.

Evidencia: `src/parallel_truth_fingerprint/lstm_service/dataset_builder.py:82-105` e descricao em `docs/seminario-andamento/evidence/custom-dataset/custom-dataset-analysis.md:44-45`.

Ordem temporal: artefatos elegiveis sao ordenados por timestamp e `artifact_key`. Evidencia: `src/parallel_truth_fingerprint/lstm_service/dataset_builder.py:62`.

Janela temporal: sequencia padrao de 2 ciclos e stride 1. Evidencia: `src/parallel_truth_fingerprint/lstm_service/lifecycle.py:25`, `src/parallel_truth_fingerprint/lstm_service/dataset_artifacts.py:20`.

Formula operacional: se existem `N` artefatos elegiveis e `sequence_length=2`, o numero de janelas e `N - 2 + 1`, quando `N >= 2`. Evidencia: `_build_windows()` em `src/parallel_truth_fingerprint/lstm_service/dataset_builder.py:151`.

Features:

- 9 features por sensor: `pv`, `loop_current_ma`, `pv_percent_range`, `noise_floor`, `rate_of_change_dtdt`, `local_stability_score`, `field_device_malfunction`, `loop_current_saturated`, `cold_start`.
- 3 sensores: pressao, rpm e temperatura, em ordem alfabetica de chave no payload.
- Total: 27 features.

Evidencia: `src/parallel_truth_fingerprint/lstm_service/dataset_builder.py:105-151` e `docs/seminario-andamento/evidence/custom-dataset/custom-dataset-analysis.md:29-35`.

Resultado vivo de 2026-06-23:

- 14 artefatos elegiveis.
- 13 janelas.
- Tensor shape `[13, 2, 27]`.
- `validation_level = runtime_valid_only`.
- Piso padrao de adequacao: 30 artefatos elegiveis e 20 janelas.

Evidencia: `docs/seminario-andamento/evidence/custom-dataset/custom-dataset-analysis.md:29-59`, `docs/seminario-andamento/evidence/custom-dataset/live-custom-dataset.manifest.pretty.json:60-67`, `src/parallel_truth_fingerprint/lstm_service/dataset_artifacts.py:22-31`.

Correcao necessaria: nao dizer que o dataset proprio ja sustenta F1/accuracy supervisionado. Ele e normal-only, pequeno e `runtime_valid_only`. Evidencia: `docs/seminario-andamento/tables/prototype-limitations.md:4-5`.

## 11. Fingerprint: trilhas runtime e offline

Ha duas trilhas distintas:

1. Runtime autoencoder sobre dataset proprio fisico-operacional.
2. Treinamento offline supervisionado sobre ADFA-LD.

Evidencia: README diferencia runtime/demo e trilha offline em `README.md:58-63`, `README.md:319-421`; runtime em `src/parallel_truth_fingerprint/lstm_service/lifecycle.py:67-111`; offline em `src/parallel_truth_fingerprint/lstm_service/offline_training/training/run.py:58-129`.

Runtime:

- Modelo runtime e LSTM autoencoder Keras com backend torch, loss MSE. Evidencia: `src/parallel_truth_fingerprint/lstm_service/trainer.py:25-138`.
- Threshold de inferencia runtime e baseado em erro de reconstrucao. Evidencia: `src/parallel_truth_fingerprint/lstm_service/inference.py:20-39`.
- Nos cenarios principais de 2026-06-23, o autoencoder runtime estava desabilitado. Evidencia: `logs/sem-normal.terminal.txt:21-23`, `logs/sem-quorum-loss.terminal.txt:21-23`, `logs/sem-scada-divergence.terminal.txt:21-23`.

Offline ADFA-LD:

- Classificadores LSTM e GRU supervisionados existem. Evidencia: `src/parallel_truth_fingerprint/lstm_service/offline_training/models/lstm_classifier.py:29-123`, `src/parallel_truth_fingerprint/lstm_service/offline_training/models/gru_classifier.py:28-99`.
- Classificadores com embedding existem. Evidencia: `src/parallel_truth_fingerprint/lstm_service/offline_training/models/embedding_classifiers.py:1-147`.
- O backend e Keras 3 com torch backend, nao PyTorch nativo puro. Evidencia: `README.md:58`, `README.md:361`, `pyproject.toml:8-9`.

Correcao necessaria: nao misturar a metrica ADFA-LD binaria com o dataset proprio. A metrica D6 vem do ADFA-LD, e o dataset proprio mostra integracao de pipeline. Evidencia: `docs/seminario-andamento/evidence/adfa-ld/adfa-ld-analysis.md:7-13` e `docs/seminario-andamento/evidence/custom-dataset/custom-dataset-analysis.md:65-78`.

## 12. ADFA-LD: dados, arquitetura e split

Dataset local presente:

- `datasets/ADFA-LD/`.
- `datasets/ADFA-LD.zip`.
- Subpastas `Attack_Data_Master`, `Training_Data_Master`, `Validation_Data_Master`.

Evidencia: listagem auditada de `datasets/`; documentacao em `docs/seminario-andamento/evidence/adfa-ld/adfa-ld-analysis.md:20-22`.

Volume documentado:

- 5.951 traces.
- 5.205 normais.
- 746 ataques em 5 familias.
- Maior syscall id: 340.

Evidencia: `docs/seminario-andamento/evidence/adfa-ld/adfa-ld-analysis.md:33`, `_bmad-output/implementation-artifacts/real-data-evidence-2026-05-21.md:21-30`.

Classes:

- Binario: `Normal` vs `Attack`.
- Multiclasse: `Normal`, `Adduser`, `Hydra-FTP`, `Hydra-SSH`, `Java-Meterpreter`, `Web-Shell`.

Evidencia: `docs/seminario-andamento/evidence/adfa-ld/adfa-ld-analysis.md:30-33`, `src/parallel_truth_fingerprint/lstm_service/offline_training/benchmarks/adfa_ld.py:38-71`.

Correcao de linguagem: existem 6 classes totais no multiclasse, mas 5 familias de ataque. Evidencia: mesmos caminhos acima.

Adaptadores:

- `adfa-ld`: uma janela por trace, feature unica, valores normalizados por maior syscall id. Evidencia: `src/parallel_truth_fingerprint/lstm_service/offline_training/benchmarks/adfa_ld.py:85-150`, `:227`.
- `adfa-ld-embed`: janelas deslizantes, tokens brutos de syscall carregados como floats para embedding. Evidencia: `src/parallel_truth_fingerprint/lstm_service/offline_training/benchmarks/adfa_ld_embedding.py:1-18`, `:79-136`, `:196-198`.
- `adfa-ld-embed-binary`: colapsa ataques em `Attack`. Evidencia: `src/parallel_truth_fingerprint/lstm_service/offline_training/benchmarks/adfa_ld_embedding.py:96`, `:198`.

Split e treino:

- Split estratificado 80/20, seed 42 nos sweeps reportados. Evidencia: `src/parallel_truth_fingerprint/lstm_service/offline_training/training/run.py:77-78`, `src/parallel_truth_fingerprint/lstm_service/offline_training/splits.py:35-122`, tabelas em `docs/seminario-andamento/tables/adfa-ld-binary-results.md:2-9`.
- Pesos de classe por frequencia inversa. Evidencia: `_balanced_class_weights()` em `src/parallel_truth_fingerprint/lstm_service/offline_training/models/lstm_classifier.py:123` e uso em `lstm_classifier.py:93`, `gru_classifier.py:87`.
- Nao ha validacao separada nem early stopping no runner reportado. Evidencia: `execute_training_run()` chama `model.fit()` e depois prediz no teste em `src/parallel_truth_fingerprint/lstm_service/offline_training/training/run.py:77-129`; parametros persistidos indicam `epochs_executed=epochs`.
- Medida anti-vazamento por trace para o adaptador com sliding windows: NÃO DOCUMENTADO. Evidencia: o split e aplicado em `data.sequences, data.labels` apos o adaptador gerar sequencias, em `src/parallel_truth_fingerprint/lstm_service/offline_training/training/run.py:77-78`.

## 13. ADFA-LD: metricas que podem entrar no seminario

Resultado D6 defendivel apenas para enquadramento binario `Normal` vs `Attack`:

| Modelo | Seq | Epocas | Seed | Macro F1 | Accuracy | Evidencia |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| LSTM embedding | 80 | 18 | 42 | 0.9187 | 0.9229 | `_bmad-output/implementation-artifacts/embedding-adfa-ld-binary-sweep.md:1-8` |

Tabela completa binaria: `docs/seminario-andamento/tables/adfa-ld-binary-results.md:1-11`.

Resultado multiclasse:

- Melhor run: LSTM embedding, sequence length 80, macro F1 0.5610, accuracy 0.7162.
- Nenhum run multiclasse atinge D6.

Evidencia: `docs/seminario-andamento/tables/adfa-ld-multiclass-results.md:1-11`.

Matriz de confusao do campeao binario:

| Verdade | Pred Normal | Pred Attack |
| --- | ---: | ---: |
| Normal | 940 | 101 |
| Attack | 25 | 568 |

Evidencia: `docs/seminario-andamento/tables/confusion-matrix.md:1-7`, `docs/results-of-the-prototype.md:275-282`.

Leitura para deteccao de ataque como positivo:

- TP = 568.
- FN = 25.
- TN = 940.
- FP = 101.
- Recall de ataque = 568 / 593 = 0.9578.
- FNR de ataque = 25 / 593 = 0.0422.
- FPR de ataque = 101 / 1041 = 0.0970.

Evidencia: matriz acima e metricas por classe em `docs/seminario-andamento/tables/champion-class-metrics.md:1-7`.

Conflito documental a corrigir: `docs/seminario-andamento/tables/confusion-matrix.md:1` diz "FPR em normal = 4.2%", mas a matriz mostra 101 normais classificados como ataque, que para ataque como classe positiva corresponde a FPR 9.70%. A tabela por classe mostra `Normal` com FPR 0.0422 e `Attack` com FPR 0.0970 em `docs/seminario-andamento/tables/champion-class-metrics.md:4-5`. O slide deve explicitar qual classe e tratada como positiva.

## 14. Cenarios de validacao

Resultado principal vivo de 2026-06-23:

| Cenario | Estado | Resultado factual | Evidencia |
| --- | --- | --- | --- |
| `normal` | IMPLEMENTADO E TESTADO | consenso `success`, 3/3 validos, SCADA match, persistencia no bucket `sem-normal` | `docs/seminario-andamento/evidence/scenarios/normal/scenario-summary.md:1-37`, `logs/sem-normal.terminal.txt:1-48` |
| `quorum_loss` | IMPLEMENTADO E TESTADO | consenso `failed_consensus`, 3 edges excluidos, comparacao e persistencia bloqueadas por `no_quorum_reached` | `docs/seminario-andamento/evidence/scenarios/quorum_loss/scenario-summary.md:1-37`, `logs/sem-quorum-loss.terminal.txt:1-48` |
| `scada_divergence` | IMPLEMENTADO E TESTADO | consenso `success`, SCADA divergente em 3 sensores, persistencia bloqueada por `scada_divergence_detected` | `docs/seminario-andamento/evidence/scenarios/scada_divergence/scenario-summary.md:1-38`, `logs/sem-scada-divergence.terminal.txt:1-48` |

Tabela oficial dos tres cenarios principais: `docs/seminario-andamento/tables/validation-scenarios.md:1-8`.

Cenarios implementados no codigo:

- `normal`.
- `scada_replay`.
- `scada_freeze`.
- `scada_divergence`.
- `single_edge_exclusion`.
- `quorum_loss`.

Evidencia: `SUPPORTED_DEMO_SCENARIOS` e blocos de configuracao em `src/parallel_truth_fingerprint/scenario_control/runtime.py:9-224`.

Evidencia auxiliar:

- `single_edge_exclusion` tem execucao de 2026-06-02, consenso `success`, 2 edges validos e `edge-3` excluido. Evidencia: `_bmad-output/results-evidence/single_edge_exclusion.txt:1-48`.
- `scada_replay` tem execucao de 2026-06-02 com `replay_behavior=completed`, classificacoes anomalo/anomalo/normal nos ciclos ativos, mas usa modelo runtime `runtime_valid_only`. Evidencia: `_bmad-output/results-evidence/scada_replay.txt:1-96`.
- `scada_freeze` existe no codigo e em testes unitarios de SCADA, mas nao encontrei log vivo principal. Evidencia de codigo: `src/parallel_truth_fingerprint/scenario_control/runtime.py:134-144`; evidencia de teste: `tests/scada/test_opcua_service.py:40-143`; evidencia principal ausente: `docs/seminario-andamento/tables/validation-scenarios.md:1-8` e limitacao em `docs/seminario-andamento/tables/prototype-limitations.md:10`.
- Drift gradual como cenario runtime dedicado: NÃO DOCUMENTADO. Ha teste de pequeno drift no modelo de consenso, mas nao ha `DEMO_SCENARIO=drift`. Evidencia de cenario suportado: `src/parallel_truth_fingerprint/scenario_control/runtime.py:9-224`.

## 15. Protocolos e tecnologias

| Tecnologia | Estado | Evidencia |
| --- | --- | --- |
| 4-20 mA | IMPLEMENTADO E TESTADO como formula simulada, nao hardware | `src/parallel_truth_fingerprint/sensor_simulation/simulator.py:82`, sample em `docs/seminario-andamento/evidence/minio/sample-valid-consensus-artifact.pretty.json:245-345` |
| HART | IMPLEMENTADO E TESTADO como payload digital HART-style, nao stack HART real | `src/parallel_truth_fingerprint/contracts/raw_hart_payload.py:13-62`, `src/parallel_truth_fingerprint/edge_nodes/common/acquisition.py:191`, `tests/edge_nodes/test_acquisition_services.py:41` |
| Profibus PA | SOMENTE DOCUMENTADO | `ARQ_PROP:35-39`; sem implementacao encontrada em `src/` |
| MQTT | IMPLEMENTADO E TESTADO | `src/parallel_truth_fingerprint/edge_nodes/common/mqtt_io.py:123-205`, `compose.local.yml:2-6`, `tests/edge_nodes/test_mqtt_replication.py:91-103` |
| OPC UA | IMPLEMENTADO E TESTADO como servidor fake local | `src/parallel_truth_fingerprint/scada/opcua_service.py:40-418`, `tests/scada/test_opcua_service.py:143` |
| Modbus TCP/RTU | SOMENTE DOCUMENTADO | `ARQ_PROP:243-248`; sem implementacao encontrada em `src/` |
| APIs REST industriais | SOMENTE DOCUMENTADO | `ARQ_PROP:243-248`; nao ha API REST industrial implementada |
| CometBFT HTTP RPC | IMPLEMENTADO E TESTADO | `src/parallel_truth_fingerprint/consensus/cometbft_client.py`, `logs/sem-normal.terminal.txt:8-20` |
| MinIO | IMPLEMENTADO E TESTADO | `src/parallel_truth_fingerprint/persistence/artifact_store.py:22-69`, `docs/seminario-andamento/evidence/minio/minio-listing.txt:4-20` |

Por que HART/Profibus aparecem na proposta: o PEP posiciona a coleta antes do CLP, em paralelo ao loop, e cita HART para PV/diagnosticos e Profibus PA por sniffing de telegrama. Evidencia: `ARQ_PROP:20-39`. Correcao: no prototipo atual, isso e simulado ou documentado, nao instrumentacao real.

## 16. Estrutura dos artefatos JSON

Artefato normal completo, amostra real: `docs/seminario-andamento/evidence/minio/sample-valid-consensus-artifact.pretty.json:1-519`.

Estrutura completa de campos do artefato normal persistido:

```json
{
  "artifact_key": "valid-consensus-artifacts/<round_id>.json",
  "persisted_at": "<iso_datetime>",
  "artifact_identity": {
    "type": "valid_consensus_artifact",
    "version": "2.0",
    "record_id": "valid-consensus-artifact::<artifact_key>"
  },
  "round_identity": {
    "round_id": "<round_id>",
    "window_started_at": "<iso_datetime>",
    "window_ended_at": "<iso_datetime>"
  },
  "consensus_context": {
    "final_consensus_status": "success",
    "participants": ["edge-1", "edge-2", "edge-3"],
    "quorum_required": 2,
    "source_edges": ["edge-1", "edge-2", "edge-3"],
    "trust_ranking": [],
    "exclusions": [],
    "trust_evidence": []
  },
  "validated_state": {
    "state_type": "consensused_valid_state",
    "source_edges": ["edge-1", "edge-2", "edge-3"],
    "sensor_values": {
      "pressure": 0.0,
      "rpm": 0.0,
      "temperature": 0.0
    },
    "structured_payload_snapshot": {
      "selected_source_edge_id": "edge-1",
      "payloads_by_sensor": {
        "temperature": {
          "protocol": "HART",
          "gateway_id": "GW-EDGE-01",
          "timestamp": "<iso_datetime>",
          "device": {
            "manufacturer_id": 26,
            "device_type": 33,
            "device_id": "<device_id>",
            "tag": "TIT-101"
          },
          "process": {
            "pv": {
              "name": "Process_Temperature",
              "value": 0.0,
              "unit": "degC",
              "unit_code": 32
            },
            "sv": {
              "name": "Sensor_Body_Temperature",
              "value": 0.0,
              "unit": "degC",
              "unit_code": 32
            },
            "loop_current_ma": 0.0,
            "pv_percent_range": 0.0,
            "physics_metrics": {
              "sensor_name": "temperature",
              "operating_state": 0.0,
              "expected_value": 0.0,
              "noise_floor": 0.0,
              "rate_of_change_dtdt": 0.0,
              "local_stability_score": 0.0
            }
          },
          "diagnostics": {
            "field_device_malfunction": false,
            "configuration_changed": false,
            "cold_start": false,
            "more_status_available": false,
            "loop_current_saturated": false
          }
        },
        "pressure": {
          "protocol": "HART",
          "gateway_id": "GW-EDGE-02",
          "timestamp": "<iso_datetime>",
          "device": {},
          "process": {},
          "diagnostics": {}
        },
        "rpm": {
          "protocol": "HART",
          "gateway_id": "GW-EDGE-03",
          "timestamp": "<iso_datetime>",
          "device": {},
          "process": {},
          "diagnostics": {}
        }
      }
    }
  },
  "dataset_context": {
    "scenario_label": "normal",
    "training_label": "normal",
    "training_eligible": true,
    "training_eligibility_reason": "normal_operation"
  },
  "scada_context": {
    "scada_state": {
      "source_round_id": "<round_id>",
      "sensor_values": {},
      "behavioral_sensor_values": {},
      "mode": "match",
      "behavioral_source_round_id": "<round_id>"
    },
    "comparison_output": {
      "round_identity": {},
      "scada_source_round_id": "<round_id>",
      "all_within_tolerance": true,
      "sensor_outputs": []
    },
    "divergence_alert": null
  },
  "diagnostics": {
    "final_consensus_status": "success",
    "has_scada_divergence": false,
    "divergent_sensors": [],
    "participants": ["edge-1", "edge-2", "edge-3"],
    "persisted_record_type": "valid_consensus_artifact"
  }
}
```

Observacao: o bloco acima e a estrutura de campos. O JSON real com valores completos, incluindo listas completas de ranking, evidencia de confianca, payloads de pressao/rpm e comparacoes SCADA, esta em `docs/seminario-andamento/evidence/minio/sample-valid-consensus-artifact.pretty.json:1-519`.

Payload HART-style completo de uma leitura local esta definido por contrato em `src/parallel_truth_fingerprint/contracts/raw_hart_payload.py:13-62` e materializado nos payloads do artefato em `docs/seminario-andamento/evidence/minio/sample-valid-consensus-artifact.pretty.json:245-345`.

## 17. Correcoes recomendadas para o Seminario

1. Trocar "o prototipo valida HART/Profibus real" por "o prototipo simula payload HART-style e documenta o caminho para HART/Profibus real". Evidencia: `src/parallel_truth_fingerprint/contracts/raw_hart_payload.py:13-62`, `ARQ_PROP:35-39`, `docs/seminario-andamento/tables/prototype-limitations.md:11`.
2. Trocar "usa FABA/BBD" por "a proposta conceitual cita BBD/FABA, mas o prototipo executa consenso CometBFT/ABCI com modelo deterministico de distancia normalizada e quorum 2 de 3". Evidencia: `ARQ_PROP:105-130`, `abci/consensus_app/internal/app/app.go:219-405`.
3. Trocar "SCADA real" por "SCADA fake local via OPC UA". Evidencia: `src/parallel_truth_fingerprint/scada/opcua_service.py:1-46`, `docs/seminario-andamento/tables/infrastructure-components.md:10`.
4. Trocar "dataset proprio treina o modelo supervisionado" por "dataset proprio e gerado end-to-end, mas ainda e normal-only e runtime_valid_only; metricas supervisionadas usam ADFA-LD". Evidencia: `docs/seminario-andamento/evidence/custom-dataset/custom-dataset-analysis.md:29-78`, `docs/seminario-andamento/evidence/adfa-ld/adfa-ld-analysis.md:7-13`.
5. Trocar "ADFA-LD multiclasse atinge D6" por "ADFA-LD binario atinge D6; multiclasse nao atinge". Evidencia: `docs/seminario-andamento/tables/adfa-ld-binary-results.md:1-11`, `docs/seminario-andamento/tables/adfa-ld-multiclass-results.md:1-11`.
6. Explicitar que 5.951 sao traces ADFA-LD e 1.634 sao janelas de teste do campeao binario, nao o mesmo denominador. Evidencia: `docs/seminario-andamento/evidence/adfa-ld/adfa-ld-analysis.md:33`, `docs/results-of-the-prototype.md:275-282`.
7. Corrigir FPR/FNR no slide de matriz: para ataque como positivo, FPR e 9.70% e FNR e 4.22%. Evidencia: `docs/seminario-andamento/tables/confusion-matrix.md:1-7`, `docs/seminario-andamento/tables/champion-class-metrics.md:4-5`.
8. Marcar `single_edge_exclusion` e `scada_replay` como evidencias auxiliares de 2026-06-02, nao como os tres cenarios principais de 2026-06-23. Evidencia: `docs/seminario-andamento/tables/validation-scenarios.md:1-8`, `_bmad-output/results-evidence/single_edge_exclusion.txt:1-48`, `_bmad-output/results-evidence/scada_replay.txt:1-96`.
9. Marcar `scada_freeze` como implementado em codigo e teste unitario, mas sem log principal vivo nesta entrega. Evidencia: `src/parallel_truth_fingerprint/scenario_control/runtime.py:134-144`, `tests/scada/test_opcua_service.py:40-143`, `docs/seminario-andamento/tables/prototype-limitations.md:10`.
10. Marcar drift gradual como trabalho futuro ou nao documentado como cenario runtime. Evidencia: ausencia em `SUPPORTED_DEMO_SCENARIOS` de `src/parallel_truth_fingerprint/scenario_control/runtime.py:9-224`.

## 18. Itens explicitamente nao documentados

- Frequencia real de amostragem de sensores industriais: NÃO DOCUMENTADO.
- Hardware, marca e modelo de sensores reais: NÃO DOCUMENTADO.
- CLP/PLC real, ladder logic, tags reais de CLP ou servidor real de CLP: NÃO DOCUMENTADO.
- QoS MQTT, retain, TLS, autenticacao e retry: NÃO DOCUMENTADO.
- Versao exata das imagens `minio/minio:latest` e `cometbft/cometbft:latest` no arquivo compose: NÃO DOCUMENTADO no compose. O runtime vivo registrou CometBFT `0.39.0` nos logs de 2026-06-23.
- Medida anti-vazamento por trace para janelas ADFA-LD embedding: NÃO DOCUMENTADO.
- Validacao em planta industrial real: NÃO DOCUMENTADO e listado como limitacao. Evidencia: `docs/seminario-andamento/tables/prototype-limitations.md:11`.

## 19. Frase curta segura para o slide de conclusao

Frase factual:

"O prototipo demonstrou, em laboratorio local, um pipeline end-to-end com sensores simulados, edges Python, MQTT, consenso real CometBFT/ABCI, comparacao contra SCADA fake OPC UA e persistencia MinIO. Tres cenarios principais foram executados ao vivo em 2026-06-23: normal, quorum_loss e scada_divergence. A etapa de fingerprint supervisionado foi avaliada separadamente no ADFA-LD binario, com macro F1 0.9187 e accuracy 0.9229; o dataset fisico-operacional proprio ja e gerado pelo pipeline, mas ainda e normal-only, pequeno e runtime_valid_only."

Evidencia: `docs/seminario-andamento/evidence/scenarios/normal/scenario-summary.md:1-37`, `docs/seminario-andamento/evidence/scenarios/quorum_loss/scenario-summary.md:1-37`, `docs/seminario-andamento/evidence/scenarios/scada_divergence/scenario-summary.md:1-38`, `docs/seminario-andamento/tables/adfa-ld-binary-results.md:1-11`, `docs/seminario-andamento/evidence/custom-dataset/custom-dataset-analysis.md:29-78`.
