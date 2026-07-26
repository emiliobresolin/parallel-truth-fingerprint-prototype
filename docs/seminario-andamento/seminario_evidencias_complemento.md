# Auditoria factual complementar do prototipo

Escopo: este complemento audita apenas os pontos adicionais pedidos. Nao altera codigo, configuracao, datasets, modelos, logs nem documentos existentes. As evidencias abaixo citam arquivos e intervalos de linhas sempre que a afirmacao depende de artefato local. Onde a justificativa nao aparece nos artefatos auditados, a resposta e: **NÃO DOCUMENTADO**.

## 1. Formulas do simulador

### 1.1 Constantes de faixa

O perfil padrao do compressor usa:

- potencia/compressor_power: `P_min = 0.0`, `P_max = 100.0`;
- temperatura: `T_min = 48.0`, `T_max = 95.0`;
- pressao: `Pr_min = 1.8`, `Pr_max = 8.5`;
- rpm: `R_min = 1200.0`, `R_max = 4200.0`;
- `base_noise_floor = 0.15`.

Evidencia: `src/parallel_truth_fingerprint/config/ranges.py:26-33`.

### 1.2 Funcoes auxiliares

A funcao de clamp e:

```text
clamp(x, [min, max]) = max(min, min(x, max))
```

Evidencia: `src/parallel_truth_fingerprint/sensor_simulation/behavior_model.py:10-13`.

A normalizacao do estado operacional e:

```text
n(P) =
  0, se P_max == P_min
  (clamp(P, compressor_power_range) - P_min) / (P_max - P_min), caso contrario
```

Evidencia: `src/parallel_truth_fingerprint/sensor_simulation/behavior_model.py:16-27`.

O padrao temporal e:

```text
time_pattern(k, period, phase_shift) = sin((k / period) + phase_shift)
```

Evidencia: `src/parallel_truth_fingerprint/sensor_simulation/behavior_model.py:36-39`.

### 1.3 Temperatura esperada

Para passo `k` e potencia efetiva `P`:

```text
state_ratio   = n(P)
lagged_ratio  = n(P - 8.0 * sin((k / 8.5) + 0.1))
temperature_ratio = 0.55 * state_ratio + 0.45 * lagged_ratio

temperature_expected =
  T_min
  + (T_max - T_min) * temperature_ratio
  + 1.8 * sin(k / 4.0)

temperature_expected_final = clamp(temperature_expected, [T_min, T_max])
```

Evidencia: `src/parallel_truth_fingerprint/sensor_simulation/behavior_model.py:49-67` e retorno com clamp em `src/parallel_truth_fingerprint/sensor_simulation/behavior_model.py:79-82`.

### 1.4 Pressao esperada

```text
pressure_ratio = 0.72 * state_ratio + 0.28 * lagged_ratio

pressure_expected =
  Pr_min
  + (Pr_max - Pr_min) * pressure_ratio
  + 0.15 * sin((k / 5.0) + 0.4)

pressure_expected_final = clamp(pressure_expected, [Pr_min, Pr_max])
```

Evidencia: `src/parallel_truth_fingerprint/sensor_simulation/behavior_model.py:59-72` e retorno com clamp em `src/parallel_truth_fingerprint/sensor_simulation/behavior_model.py:79-82`.

### 1.5 RPM esperado

```text
leading_ratio = n(P + 6.0 * sin((k / 6.0) + 0.2))
rpm_ratio = 0.88 * state_ratio + 0.12 * leading_ratio

rpm_expected =
  R_min
  + (R_max - R_min) * rpm_ratio
  + 45.0 * sin((k / 3.5) + 0.7)

rpm_expected_final = clamp(rpm_expected, [R_min, R_max])
```

Evidencia: `src/parallel_truth_fingerprint/sensor_simulation/behavior_model.py:54-57`, `src/parallel_truth_fingerprint/sensor_simulation/behavior_model.py:61-77` e retorno com clamp em `src/parallel_truth_fingerprint/sensor_simulation/behavior_model.py:79-82`.

### 1.6 Controle, vieses e nivel de ruido

Antes do ruido, o simulador calcula:

```text
P_effective = clamp(P_requested + operating_state_offset, compressor_power_range)

temperature_biased = temperature_expected_final + temperature_bias
pressure_biased    = pressure_expected_final + pressure_bias
rpm_biased         = rpm_expected_final + rpm_bias
```

Evidencia: `src/parallel_truth_fingerprint/sensor_simulation/simulator.py:150-174`.

A funcao `temperature_driven_noise_level()` calcula o ruido usando a temperatura como se ela fosse o campo normalizado de potencia de um perfil temporario:

```text
temperature_ratio_for_noise =
  (clamp(temperature, [T_min, T_max]) - T_min) / (T_max - T_min)

noise_level =
  base_noise_floor
  + temperature_ratio_for_noise * 0.85 * noise_multiplier
```

Evidencia: `src/parallel_truth_fingerprint/sensor_simulation/behavior_model.py:86-104`.

O valor `base_noise_floor = 0.15` participa dessa formula de `noise_level`. Evidencia: constante em `src/parallel_truth_fingerprint/config/ranges.py:26-33` e uso em `src/parallel_truth_fingerprint/sensor_simulation/behavior_model.py:93-104`.

### 1.7 Ruido aplicado a cada sensor

Para cada sensor, o sorteio e uniforme em `[-1.0, 1.0]`, nao gaussiano:

```text
U_T, U_Pr, U_R ~ Uniform(-1.0, 1.0)

temperature_observed =
  round(clamp(temperature_biased + U_T * noise_level * 5.0, [T_min, T_max]), 3)

pressure_observed =
  round(clamp(pressure_biased + U_Pr * noise_level * 0.35, [Pr_min, Pr_max]), 3)

rpm_observed =
  round(clamp(rpm_biased + U_R * noise_level * 60.0, [R_min, R_max]), 3)
```

Evidencia: `src/parallel_truth_fingerprint/sensor_simulation/simulator.py:222-252`.

Amplitude maxima do termo aleatorio antes do clamp:

- temperatura: `+/- noise_level * 5.0`;
- pressao: `+/- noise_level * 0.35`;
- rpm: `+/- noise_level * 60.0`.

Evidencia: `src/parallel_truth_fingerprint/sensor_simulation/simulator.py:228-247`.

### 1.8 Campos derivados no payload Edge

O simulador salva `metadata["noise_level"] = round(noise_level, 4)` no snapshot. Evidencia: `src/parallel_truth_fingerprint/sensor_simulation/simulator.py:180-188`.

O Edge grava no payload:

```text
noise_floor = round(float(reading.metadata.get("noise_level", 0.0)), 3)
```

Ou seja, `noise_floor` no payload nao e o `base_noise_floor`; e o `noise_level` do simulador, arredondado. Evidencia: `src/parallel_truth_fingerprint/edge_nodes/common/acquisition.py:174-185`.

O `rate_of_change_dtdt` e:

```text
rate_of_change_dtdt =
  0.0, se nao houver pv anterior
  round(pv_value_atual - pv_value_anterior, 3), caso contrario
```

Evidencia: `src/parallel_truth_fingerprint/edge_nodes/common/acquisition.py:174-185`.

O `local_stability_score` e:

```text
local_stability_score =
  round(max(0.0, 1.0 - min(0.95, abs(rate_of_change_dtdt) * 0.015 + noise_floor * 0.1)), 3)
```

Evidencia: `src/parallel_truth_fingerprint/edge_nodes/common/acquisition.py:105-107` e uso em `src/parallel_truth_fingerprint/edge_nodes/common/acquisition.py:181-185`.

O `pv_percent_range` e:

```text
span = sensor_max - sensor_min
pv_percent_range =
  0.0, se span <= 0
  round(((pv_value - sensor_min) / span) * 100.0, 3), caso contrario
```

Evidencia: `src/parallel_truth_fingerprint/sensor_simulation/simulator.py:75-79` e atribuicao em `src/parallel_truth_fingerprint/sensor_simulation/simulator.py:260-283`.

A corrente simulada de 4 a 20 mA e:

```text
loop_current_ma = round(4.0 + 16.0 * (pv_percent_range / 100.0), 3)
```

Evidencia: `src/parallel_truth_fingerprint/sensor_simulation/simulator.py:82-83` e atribuicao em `src/parallel_truth_fingerprint/sensor_simulation/simulator.py:260-283`.

### 1.9 Respostas diretas sobre ruido

a) O ruido depende diretamente da temperatura usada em `temperature_driven_noise_level()`, e depende da potencia apenas indiretamente porque a potencia entra no calculo da temperatura esperada. O ruido tambem depende diretamente de `noise_multiplier` e de `base_noise_floor`. Evidencia: cadeia de potencia para valores esperados em `src/parallel_truth_fingerprint/sensor_simulation/behavior_model.py:49-77`, vies de temperatura em `src/parallel_truth_fingerprint/sensor_simulation/simulator.py:163-173`, formula de ruido em `src/parallel_truth_fingerprint/sensor_simulation/behavior_model.py:86-104`.

b) Cadeia causal exata:

```text
compressor_power/operating_state_pct
-> P_effective
-> state_ratio, lagged_ratio, leading_ratio
-> temperature_expected
-> temperature_biased
-> temperature_driven_noise_level(temperature_biased)
-> ruido uniforme aplicado aos tres sensores
-> metadata.noise_level
-> payload.physics_metrics.noise_floor
```

Evidencia: `src/parallel_truth_fingerprint/sensor_simulation/simulator.py:150-188`, `src/parallel_truth_fingerprint/sensor_simulation/behavior_model.py:49-104`, `src/parallel_truth_fingerprint/edge_nodes/common/acquisition.py:174-185`.

c) A distribuicao do ruido e uniforme, por `self._rng.uniform(-1.0, 1.0)`. Evidencia: `src/parallel_truth_fingerprint/sensor_simulation/simulator.py:228-247`.

d) A amplitude de ruido e `+/- 5.0 * noise_level` para temperatura, `+/- 0.35 * noise_level` para pressao e `+/- 60.0 * noise_level` para rpm. Evidencia: `src/parallel_truth_fingerprint/sensor_simulation/simulator.py:228-247`.

e) `base_noise_floor = 0.15` participa da formula `noise_level = base_noise_floor + temperature_ratio * 0.85 * noise_multiplier`. Evidencia: `src/parallel_truth_fingerprint/config/ranges.py:26-33` e `src/parallel_truth_fingerprint/sensor_simulation/behavior_model.py:86-104`.

f) Exemplo numerico sem executar nova simulacao, usando `compressor_power = 65`, `step_index = 0`, sem vies e `noise_multiplier = 1.0`:

```text
state_ratio = 0.65
lagged_ratio = (65 - 8*sin(0.1)) / 100 = 0.6420133267
leading_ratio = (65 + 6*sin(0.2)) / 100 = 0.6619201598

temperature_ratio = 0.55*0.65 + 0.45*0.6420133267 = 0.6464059970
temperature_expected = 48 + 47*0.6464059970 + 1.8*sin(0) = 78.381081859 degC

pressure_ratio = 0.72*0.65 + 0.28*0.6420133267 = 0.6477637315
pressure_expected = 1.8 + 6.7*0.6477637315 + 0.15*sin(0.4) = 6.198628031 bar

rpm_ratio = 0.88*0.65 + 0.12*0.6619201598 = 0.6514304192
rpm_expected = 1200 + 3000*0.6514304192 + 45*sin(0.7) = 3183.707700 rpm

noise_level = 0.15 + ((78.381081859 - 48) / 47) * 0.85 = 0.699445097

amplitudes:
temperature +/- 3.497225485 degC
pressure    +/- 0.244805784 bar
rpm         +/- 41.9667058 rpm
```

Evidencia das formulas: `src/parallel_truth_fingerprint/sensor_simulation/behavior_model.py:49-104`, faixas em `src/parallel_truth_fingerprint/config/ranges.py:26-33`, amplitudes em `src/parallel_truth_fingerprint/sensor_simulation/simulator.py:228-247`. O sorteio especifico de ruido nao e calculavel sem conhecer os tres valores aleatorios uniformes usados no passo.

## 2. Score de confianca e exclusao

### 2.1 Distancia normalizada entre dois Edges

As escalas de normalizacao sao:

```text
temperature_scale = 20.0
pressure_scale = 3.0
rpm_scale = 600.0
```

Evidencia: Python em `src/parallel_truth_fingerprint/consensus/trust_model.py:26-32`; ABCI Go em `abci/consensus_app/internal/app/app.go:17-31`.

Para dois Edges `A` e `B`, a distancia normalizada e:

```text
d(A, B) =
  ( abs(T_A - T_B) / 20.0
  + abs(Pr_A - Pr_B) / 3.0
  + abs(R_A - R_B) / 600.0 ) / 3
```

Evidencia: Python em `src/parallel_truth_fingerprint/consensus/trust_model.py:39-49`; ABCI Go em `abci/consensus_app/internal/app/app.go:381-402`.

### 2.2 overall_normalized_deviation

Para um Edge `E`, com pares `Peers(E)`:

```text
overall_normalized_deviation(E) =
  round(mean(d(E, peer) for peer in Peers(E)), 3)
```

Evidencia: Python em `src/parallel_truth_fingerprint/consensus/trust_model.py:109-119`; ABCI Go em `abci/consensus_app/internal/app/app.go:284-294`.

### 2.3 Score de confianca

```text
score(E) = round(1.0 / (1.0 + overall_normalized_deviation(E)), 3)
```

Evidencia: Python em `src/parallel_truth_fingerprint/consensus/trust_model.py:114-120`; ABCI Go em `abci/consensus_app/internal/app/app.go:293-295`.

Intervalo possivel: como as distancias absolutas normalizadas sao `>= 0`, o score fica em `(0, 1]` antes do arredondamento; `1.0` ocorre quando o desvio e zero, e valores proximos de `0` indicam desvio normalizado muito alto. Evidencia da nao negatividade pela formula de distancia absoluta em `src/parallel_truth_fingerprint/consensus/trust_model.py:43-49` e da formula do score em `src/parallel_truth_fingerprint/consensus/trust_model.py:114-120`.

### 2.4 Thresholds e exclusao

O threshold `0.35` e usado para contar pares compativeis:

```text
compatible_peer_count(E) =
  count(peer for peer in Peers(E) if d(E, peer) <= 0.35)
```

Evidencia: Python em `src/parallel_truth_fingerprint/consensus/trust_model.py:109-113`; ABCI Go em `abci/consensus_app/internal/app/app.go:284-291`.

O quorum e maioria estrita:

```text
quorum = floor(participant_count / 2) + 1
```

Evidencia: Python em `src/parallel_truth_fingerprint/consensus/quorum.py:4-9`; ABCI Go em `abci/consensus_app/internal/app/app.go:239`.

Regra completa de exclusao:

```text
se compatible_peer_count(E) + 1 < quorum:
    excluir E
    se overall_normalized_deviation(E) >= 0.75:
        reason = suspected_byzantine_behavior
    senao:
        reason = inconsistent_view
```

Evidencia: Python em `src/parallel_truth_fingerprint/consensus/trust_model.py:133-156`; ABCI Go em `abci/consensus_app/internal/app/app.go:307-333`.

Confirmacao: o threshold `0.75` nao decide se o Edge sera excluido. A exclusao ja foi decidida por `compatible_peer_count + 1 < quorum`; o `0.75` so classifica o texto do motivo entre `suspected_byzantine_behavior` e `inconsistent_view`. Evidencia: Python em `src/parallel_truth_fingerprint/consensus/trust_model.py:133-138`; ABCI Go em `abci/consensus_app/internal/app/app.go:307-311`.

### 2.5 Formacao do estado consensado

Depois das exclusoes, o sistema monta `validEdges` como participantes nao excluidos. Se `len(validEdges) >= quorum`, o status vira `success` e o estado consensado e a media aritmetica, por sensor, dos valores dos Edges validos, arredondada a 3 casas. Se `len(validEdges) < quorum`, o status fica `failed_consensus` e nao ha estado consensado. Evidencia: `abci/consensus_app/internal/app/app.go:346-364` e media por sensor em `abci/consensus_app/internal/app/app.go:405-421`.

### 2.6 Explicacao numerica do quorum_loss

No modo `quorum_loss`, o runtime marca como faltosos `edge-2` e `edge-3`. Evidencia: default em `scripts/run_local_demo.py:121-128` e log da execucao em `logs/sem-quorum-loss.terminal.txt:35-39`.

Os offsets aplicados sao opostos:

```text
edge-2: temperature +40.0, pressure +3.4, rpm +1490.0
edge-3: temperature -60.0, pressure -5.0, rpm -2300.0
```

Evidencia: `scripts/run_local_demo.py:148-180`.

O log detalhado da rodada mostra:

- `edge-1`: `score=0.298`, `compatible_peers=0`, `overall_dev=2.353`;
- `edge-2`: `score=0.233`, `compatible_peers=0`, `overall_dev=3.289`;
- `edge-3`: `score=0.210`, `compatible_peers=0`, `overall_dev=3.769`.

Evidencia: `logs/sem-quorum-loss.log:620-630`, `docs/seminario-andamento/evidence/scenarios/quorum_loss/consensus-payload.pretty.json:270-300` e `docs/seminario-andamento/evidence/scenarios/quorum_loss/consensus-payload.pretty.json:349-413`.

Calculos:

```text
edge-1 vs edge-2:
d12 = (40/20 + 3.4/3 + 1490/600) / 3
    = (2.000 + 1.133 + 2.483) / 3
    = 1.872

edge-1 vs edge-3:
d13 = (60/20 + 5.0/3 + 2300/600) / 3
    = (3.000 + 1.667 + 3.833) / 3
    = 2.833

overall(edge-1) = round((1.872 + 2.833) / 2, 3) = 2.353
score(edge-1) = round(1 / (1 + 2.353), 3) = 0.298
```

Evidencia dos deltas por sensor para `edge-1`: `docs/seminario-andamento/evidence/scenarios/quorum_loss/consensus-payload.pretty.json:309-345`; escalas em `src/parallel_truth_fingerprint/consensus/trust_model.py:26-32`; formula em `src/parallel_truth_fingerprint/consensus/trust_model.py:39-49` e `src/parallel_truth_fingerprint/consensus/trust_model.py:114-120`.

```text
edge-2 vs edge-1:
d21 = 1.872

edge-2 vs edge-3:
d23 = (100/20 + 8.4/3 + 3790/600) / 3
    = (5.000 + 2.800 + 6.317) / 3
    = 4.706

overall(edge-2) = round((1.872 + 4.706) / 2, 3) = 3.289
score(edge-2) = round(1 / (1 + 3.289), 3) = 0.233
```

Evidencia dos deltas por sensor para `edge-2`: `docs/seminario-andamento/evidence/scenarios/quorum_loss/consensus-payload.pretty.json:349-407`.

```text
edge-3 vs edge-1:
d31 = 2.833

edge-3 vs edge-2:
d32 = 4.706

overall(edge-3) = round((2.833 + 4.706) / 2, 3) = 3.769
score(edge-3) = round(1 / (1 + 3.769), 3) = 0.210
```

Evidencia dos scores e desvios: `logs/sem-quorum-loss.log:620-630` e `docs/seminario-andamento/evidence/scenarios/quorum_loss/consensus-payload.pretty.json:409-413`.

O `edge-1` tambem foi excluido porque, embora nao tenha recebido offset direto, ficou sem nenhum peer compativel: `compatible_peer_count = 0`. Com tres participantes, `quorum = 2`; logo `0 + 1 < 2` e verdadeiro. Evidencia: regra em `src/parallel_truth_fingerprint/consensus/trust_model.py:109-138`, quorum em `src/parallel_truth_fingerprint/consensus/quorum.py:4-9`, resultado em `docs/seminario-andamento/evidence/scenarios/quorum_loss/consensus-payload.pretty.json:1-35`.

## 3. Tempo, ciclos e janelas

### 3.1 Janela de consenso

`window_ended_at` e o timestamp da ultima aquisicao local. `window_started_at` e calculado como `window_ended_at - timedelta(minutes=1)`. Portanto a duracao nominal da janela de consenso e 60 segundos. Evidencia: `src/parallel_truth_fingerprint/edge_nodes/common/acquisition.py:349-363`.

Na execucao `quorum_loss`, o payload mostra:

```text
window_started_at = 2026-06-23T19:19:09.763877+00:00
window_ended_at   = 2026-06-23T19:20:09.763877+00:00
```

Evidencia: `logs/sem-quorum-loss.log:628-630` e `docs/seminario-andamento/evidence/scenarios/quorum_loss/consensus-payload.pretty.json:37-40`.

### 3.2 Ciclo do runtime e passos do simulador

Os defaults de runtime sao:

```text
DEMO_STEPS = 3
DEMO_CYCLE_INTERVAL_SECONDS = 10
DEMO_FINGERPRINT_SEQUENCE_LENGTH = 2
```

Evidencia: `src/parallel_truth_fingerprint/config/runtime.py:63-70`.

Dentro de um ciclo de demo, o runtime executa `config.demo_steps` passos; em cada passo chama `simulator.step(...)`, faz aquisicao/publicacao por Edge e dorme `0.2` segundo. Depois ainda dorme `1.0` segundo antes de montar a entrada de consenso. Evidencia: `scripts/run_local_demo.py:1124-1136`.

Na execucao de 2026-06-23, o terminal registrou `interval_seconds=2.0` nos ciclos. Evidencia: `logs/sem-quorum-loss.terminal.txt:12-18` e `logs/sem-quorum-loss.terminal.txt:35-40`.

Explicacao: `DEMO_CYCLE_INTERVAL_SECONDS=2` controla a cadencia entre ciclos do runtime; nao controla a duracao nominal da identidade da rodada de consenso. A janela de consenso e metadado calculado sempre como 1 minuto antes da ultima aquisicao. Evidencia: cadencia em `logs/sem-quorum-loss.terminal.txt:15` e `logs/sem-quorum-loss.terminal.txt:39`; janela em `src/parallel_truth_fingerprint/edge_nodes/common/acquisition.py:355-363`.

### 3.3 Diferenca entre os tres tipos de janela

- Ciclo do runtime: iteracao operacional do `run_local_demo.py`, com passos do simulador, aquisicao, MQTT, consenso, SCADA, persistencia e fingerprint. Evidencia: `scripts/run_local_demo.py:1124-1145` e fluxo descrito em `README.md:190-200`.
- Janela de consenso: intervalo nominal `[window_started_at, window_ended_at]`, sempre ancorado na ultima aquisicao e retrocedido em 1 minuto. Evidencia: `src/parallel_truth_fingerprint/edge_nodes/common/acquisition.py:349-363`.
- Janela do dataset: sequencia de artefatos elegiveis ordenados cronologicamente, com `sequence_length` registros adjacentes na lista ordenada. Evidencia: ordenacao em `src/parallel_truth_fingerprint/lstm_service/dataset_builder.py:52-67` e montagem das janelas em `src/parallel_truth_fingerprint/lstm_service/dataset_builder.py:151-175`.

### 3.4 Regularidade, lacunas e manifest live

O builder nao exige intervalos regulares entre artefatos: ele carrega artefatos elegiveis, extrai `round_identity["window_ended_at"]`, ordena por `(timestamp, artifact_key)` e construi janelas por fatias adjacentes da lista. Evidencia: `src/parallel_truth_fingerprint/lstm_service/dataset_builder.py:33-79` e `src/parallel_truth_fingerprint/lstm_service/dataset_builder.py:151-175`.

Nao ha `max_gap`, validacao de continuidade nem rejeicao de lacunas na montagem das janelas. Evidencia: o algoritmo em `src/parallel_truth_fingerprint/lstm_service/dataset_builder.py:151-175` apenas verifica `len(eligible_records) < sequence_length` e itera `start_index`.

Sim, uma janela pode unir artefatos separados por varios minutos, desde que eles sejam adjacentes na lista ordenada de artefatos elegiveis. Evidencia: `src/parallel_truth_fingerprint/lstm_service/dataset_builder.py:62-67` e `src/parallel_truth_fingerprint/lstm_service/dataset_builder.py:161-170`.

No manifest live auditado, os artefatos selecionados incluem:

```text
valid-consensus-artifacts/round-20260623191948013076.json
valid-consensus-artifacts/round-20260623193124938936.json
```

Evidencia: `docs/seminario-andamento/evidence/custom-dataset/live-custom-dataset.manifest.pretty.json:41-45`.

Pelos `round_id`s, esses dois fins de janela correspondem a `2026-06-23 19:19:48.013076` e `2026-06-23 19:31:24.938936`; a diferenca e `696.925860` segundos. O proprio manifest informa `sequence_length = 2`, `stride = 1`, `window_count = 13` e tensor `[13, 2, 27]`. Evidencia: manifest em `docs/seminario-andamento/evidence/custom-dataset/live-custom-dataset.manifest.pretty.json:1-11` e `docs/seminario-andamento/evidence/custom-dataset/live-custom-dataset.manifest.pretty.json:58-64`.

Confirmacao: uma das 13 janelas atravessa essa lacuna. Como `sequence_length = 2` e o builder monta janelas por pares adjacentes, a janela iniciada no segundo artefato selecionado une `round-20260623191948013076` e `round-20260623193124938936`. Evidencia: artefatos adjacentes em `docs/seminario-andamento/evidence/custom-dataset/live-custom-dataset.manifest.pretty.json:42-44` e regra `window_id = window::<primeiro>::<ultimo>` em `src/parallel_truth_fingerprint/lstm_service/dataset_builder.py:161-170`.

`sequence_length = 2` e `stride = 1` aparecem como defaults/parametros do prototipo, nao como valores justificados experimentalmente. Evidencia: default runtime `DEFAULT_RUNTIME_SEQUENCE_LENGTH = 2` em `src/parallel_truth_fingerprint/lstm_service/lifecycle.py:23-27`, env default `DEMO_FINGERPRINT_SEQUENCE_LENGTH = 2` em `src/parallel_truth_fingerprint/config/runtime.py:63-70`, `DEFAULT_WINDOW_STRIDE = 1` em `src/parallel_truth_fingerprint/lstm_service/dataset_artifacts.py:19-23` e manifest em `docs/seminario-andamento/evidence/custom-dataset/live-custom-dataset.manifest.pretty.json:9-11`. Justificativa experimental: **NÃO DOCUMENTADO**.

Os pisos `30` artefatos elegiveis e `20` janelas tambem sao constantes default de adequacao, nao uma calibracao experimental documentada. Evidencia: `DEFAULT_MIN_ELIGIBLE_ARTIFACT_COUNT = 30` e `DEFAULT_MIN_WINDOW_COUNT = 20` em `src/parallel_truth_fingerprint/lstm_service/dataset_artifacts.py:19-31`; avaliacao `runtime_valid_only` abaixo do piso em `src/parallel_truth_fingerprint/lstm_service/dataset_artifacts.py:35-58`; manifest live em `docs/seminario-andamento/evidence/custom-dataset/live-custom-dataset.manifest.pretty.json:66-76`. Justificativa experimental: **NÃO DOCUMENTADO**.

## 4. Tolerancias do SCADA

### 4.1 Regra implementada

As tolerancias padrao sao:

```text
temperature = 2.0 degC
pressure = 0.35 bar
rpm = 120.0 rpm
```

Evidencia: `src/parallel_truth_fingerprint/comparison/service.py:23-29`.

A decisao por sensor e:

```text
absolute_difference = round(abs(physical_value - scada_value), 3)
within_tolerance = absolute_difference <= tolerance
```

Evidencia: `src/parallel_truth_fingerprint/comparison/service.py:68-82`.

O codigo declara que a tolerancia configuravel e a unica regra de decisao e que evidencia contextual nao altera o resultado. Evidencia: `src/parallel_truth_fingerprint/comparison/service.py:49-54`; story de implementacao em `_bmad-output/implementation-artifacts/3-2-implement-sensor-by-sensor-scada-comparison-on-consensused-valid-payloads.md:13-20` e `_bmad-output/implementation-artifacts/3-2-implement-sensor-by-sensor-scada-comparison-on-consensused-valid-payloads.md:28-39`.

Os testes validam comportamento dentro/fora de tolerancia e evidencia contextual sem alterar decisao; eles usam tolerancias configuradas no teste, mas nao justificam os valores default `2.0`, `0.35`, `120.0`. Evidencia: `tests/comparison/test_service.py:46-84` e `tests/comparison/test_service.py:86-162`.

### 4.2 Origem/calibracao

Nao encontrei nos artefatos auditados comentario, teste, documento ou mensagem de commit que calibre `2.0 degC`, `0.35 bar` e `120 rpm` por instrumento, fundo de escala ou experimento. O codigo chama esses valores de "Prototype-scaled configurable tolerance values by sensor". Evidencia: `src/parallel_truth_fingerprint/comparison/service.py:23-29`.

Classificacao factual: sao constantes configuraveis do prototipo. Calibracao por instrumento: **NÃO DOCUMENTADO**. Derivacao por fundo de escala: **NÃO DOCUMENTADO**. Justificativa experimental especifica: **NÃO DOCUMENTADO**.

### 4.3 Porcentagem em relacao ao span simulado

Usando os spans do simulador:

```text
temperature span = 95.0 - 48.0 = 47.0 degC
2.0 / 47.0 * 100 = 4.255%

pressure span = 8.5 - 1.8 = 6.7 bar
0.35 / 6.7 * 100 = 5.224%

rpm span = 4200.0 - 1200.0 = 3000.0 rpm
120.0 / 3000.0 * 100 = 4.000%
```

Evidencia das faixas: `src/parallel_truth_fingerprint/config/ranges.py:26-33`; evidencia das tolerancias: `src/parallel_truth_fingerprint/comparison/service.py:23-29`.

Ressalva: essas porcentagens sao apenas calculos posteriores. O codigo nao diz que elas foram o criterio de escolha. Evidencia: regra e comentario do servico em `src/parallel_truth_fingerprint/comparison/service.py:23-29` e `src/parallel_truth_fingerprint/comparison/service.py:49-54`.

Frase academica segura: "As tolerancias SCADA sao parametros laboratoriais configuraveis do prototipo, expressos nas unidades fisicas de cada sensor e aplicados por comparacao absoluta; no estado atual, nao ha calibracao documentada por instrumento, processo industrial real ou fundo de escala."

## 5. ADFA-LD e possivel vazamento

### 5.1 Ordem do fluxo

As janelas ADFA-LD embedding sao geradas no adaptador antes do split: `load()` carrega traces, cria `windows` e `window_labels`, e retorna `BenchmarkData(sequences=tuple(windows), labels=tuple(window_labels))`. Evidencia: `src/parallel_truth_fingerprint/lstm_service/offline_training/benchmarks/adfa_ld_embedding.py:79-149`.

O runner depois chama `stratified_train_test_split(data.sequences, data.labels, train_ratio=0.8, seed=seed)`. Evidencia: `src/parallel_truth_fingerprint/lstm_service/offline_training/training/run.py:73-79`.

Resposta objetiva: as janelas sao geradas antes da divisao treino/teste. Evidencia: `src/parallel_truth_fingerprint/lstm_service/offline_training/benchmarks/adfa_ld_embedding.py:98-123` e `src/parallel_truth_fingerprint/lstm_service/offline_training/training/run.py:73-79`.

### 5.2 Trace ID e agrupamento

Cada janela retornada carrega apenas a sequencia e o label; nao ha `trace_id` no objeto retornado por `BenchmarkData`. Evidencia: construcao de `windows`/`window_labels` em `src/parallel_truth_fingerprint/lstm_service/offline_training/benchmarks/adfa_ld_embedding.py:98-123` e campos retornados em `src/parallel_truth_fingerprint/lstm_service/offline_training/benchmarks/adfa_ld_embedding.py:119-149`.

O split estratificado usa somente `sequences`, `labels`, indices por classe e seed; nao usa `trace_id`, grupos ou `GroupShuffleSplit`. Evidencia: `src/parallel_truth_fingerprint/lstm_service/offline_training/splits.py:35-61`, `src/parallel_truth_fingerprint/lstm_service/offline_training/splits.py:75-123`.

Janelas do mesmo trace podem aparecer em treino e teste porque o agrupamento por trace e perdido antes do split. Se janelas do mesmo trace forem sobrepostas, o fluxo atual nao impede que uma sobreposta fique em treino e outra em teste. Evidencia: geracao de ate `max_windows_per_trace` janelas por trace em `src/parallel_truth_fingerprint/lstm_service/offline_training/benchmarks/adfa_ld_embedding.py:71-77` e `src/parallel_truth_fingerprint/lstm_service/offline_training/benchmarks/adfa_ld_embedding.py:100-113`; split por indice de janela em `src/parallel_truth_fingerprint/lstm_service/offline_training/splits.py:75-110`.

Isso e confirmado pelo fluxo atual como ausencia de controle por trace/grupo. A ocorrencia concreta de pares sobrepostos especificos no run campeao nao e rastreavel no working tree porque o artefato JSON do run binario nao esta presente localmente. Evidencia da ausencia local do JSON campeao: `docs/seminario-andamento/tables/champion-run-summary.md:1-6`. Evidencia do fluxo sem grupos: `src/parallel_truth_fingerprint/lstm_service/offline_training/splits.py:75-110`.

Teste que impeça esse vazamento: **NÃO DOCUMENTADO**. Os testes auditados do embedding verificam registro, labels, tokens, proveniencia, stride, tail coverage e cap por classe; nao verificam split por trace/grupo. Evidencia: `tests/lstm_service/offline_training/test_adfa_ld_embedding.py:1-6`, `tests/lstm_service/offline_training/test_adfa_ld_embedding.py:30-80` e `tests/lstm_service/offline_training/test_adfa_ld_embedding.py:82-114`.

### 5.3 Leitura correta das metricas

E correto chamar `macro F1 = 0.9187` e `accuracy = 0.9229` de resultado preliminar. Evidencia dos valores do campeao: `docs/seminario-andamento/tables/adfa-ld-binary-results.md:1-11`, `_bmad-output/implementation-artifacts/embedding-adfa-ld-binary-sweep.md:1-8`, `docs/seminario-andamento/tables/champion-run-summary.md:1-6` e `docs/results-of-the-prototype.md:263-275`.

Ressalva obrigatoria: essas metricas pertencem ao ADFA-LD binario, que e um dataset publico de syscalls de host, nao dado fisico-operacional industrial; alem disso, o fluxo atual gera janelas antes do split e nao preserva `trace_id`, entao existe risco metodologico de vazamento entre treino e teste. Evidencia de dominio ADFA-LD e limitacao: `docs/seminario-andamento/evidence/adfa-ld/adfa-ld-analysis.md:20-33` e `docs/seminario-andamento/evidence/adfa-ld/adfa-ld-analysis.md:64-70`; evidencia do fluxo de janelas antes do split: `src/parallel_truth_fingerprint/lstm_service/offline_training/benchmarks/adfa_ld_embedding.py:98-123` e `src/parallel_truth_fingerprint/lstm_service/offline_training/training/run.py:73-79`.

Correcao metodologica adequada: dividir por trace antes do janelamento ou preservar `trace_id` e usar um split por grupo equivalente a `GroupShuffleSplit`, para garantir que todas as janelas de um mesmo trace fiquem no mesmo lado do split. Evidencia do problema a corrigir: falta de `trace_id` no retorno em `src/parallel_truth_fingerprint/lstm_service/offline_training/benchmarks/adfa_ld_embedding.py:119-149` e split por indices/labels em `src/parallel_truth_fingerprint/lstm_service/offline_training/splits.py:75-123`.

### 5.4 Quantidades do run campeao

O dataset ADFA-LD real carregado tem `5.951 traces`: `5.205` normais e `746` ataques. Evidencia: `docs/seminario-andamento/evidence/adfa-ld/adfa-ld-analysis.md:29-33` e `docs/results-of-the-prototype.md:203-204`.

Para o campeao `adfa-ld-embed-binary`, `sequence_length = 80`, seed `42`, modelo LSTM embedding, 18 epocas, batch 256, learning rate 0.001. Evidencia: `docs/seminario-andamento/tables/adfa-ld-binary-results.md:1-4`, `scripts/sweeps/adfa_ld_embedding_binary_sweep.json:1-17`, `docs/results-of-the-prototype.md:230-237` e `docs/results-of-the-prototype.md:263-267`.

Contagem reproduzida nesta auditoria sem treinamento, apenas carregando o adaptador `adfa-ld-embed-binary` com `sequence_length=80`:

```text
total de janelas = 8172
Normal total = 5205
Attack total = 2967
treino = 6538 janelas: Normal 4164, Attack 2374
teste = 1634 janelas: Normal 1041, Attack 593
```

Evidencia do mecanismo que produz e registra `window_count`: `src/parallel_truth_fingerprint/lstm_service/offline_training/benchmarks/adfa_ld_embedding.py:98-149`; evidencia do split 80/20 estratificado: `src/parallel_truth_fingerprint/lstm_service/offline_training/splits.py:54-61` e `src/parallel_truth_fingerprint/lstm_service/offline_training/splits.py:90-123`; evidencia do split de teste do campeao: `docs/results-of-the-prototype.md:274-284` e `docs/seminario-andamento/tables/champion-class-metrics.md:1-7`.

Como `5.951` traces resultaram em `1.634` janelas de teste: o adaptador gera uma janela por trace normal e ate quatro janelas por trace de ataque; no carregamento auditado para `sequence_length=80`, isso produz `8.172` janelas. O split estratificado 80/20 separa `1.634` janelas para teste (`1.041` Normal e `593` Attack). Evidencia da politica de janelamento: `src/parallel_truth_fingerprint/lstm_service/offline_training/benchmarks/adfa_ld_embedding.py:71-77`, `src/parallel_truth_fingerprint/lstm_service/offline_training/benchmarks/adfa_ld_embedding.py:100-113` e `src/parallel_truth_fingerprint/lstm_service/offline_training/benchmarks/adfa_ld_embedding.py:158-190`; evidencia do split: `src/parallel_truth_fingerprint/lstm_service/offline_training/splits.py:90-123`; evidencia do teste do campeao: `docs/results-of-the-prototype.md:274-284`.

### 5.5 Hiperparametros e treinamento

- Optimizer: Adam com `learning_rate`. Evidencia: `src/parallel_truth_fingerprint/lstm_service/offline_training/models/embedding_classifiers.py:126-130`.
- Loss: `sparse_categorical_crossentropy`. Evidencia: `src/parallel_truth_fingerprint/lstm_service/offline_training/models/embedding_classifiers.py:126-130`.
- Ativacao de saida: `Dense(..., activation="softmax")`. Evidencia: `src/parallel_truth_fingerprint/lstm_service/offline_training/models/embedding_classifiers.py:118-120`.
- Ativacoes internas da LSTM/GRU: **NÃO DOCUMENTADO** no codigo local; as camadas sao instanciadas sem parametros `activation`/`recurrent_activation`. Evidencia: `src/parallel_truth_fingerprint/lstm_service/offline_training/models/embedding_classifiers.py:96-115`.
- Dropout: `0.3` no sweep campeao. Evidencia: default em `src/parallel_truth_fingerprint/lstm_service/offline_training/models/embedding_classifiers.py:45-49` e config em `scripts/sweeps/adfa_ld_embedding_binary_sweep.json:6-12`.
- Batch: `256`. Evidencia: `scripts/sweeps/adfa_ld_embedding_binary_sweep.json:13-17` e `docs/seminario-andamento/tables/adfa-ld-binary-results.md:1-4`.
- Learning rate: `0.001`. Evidencia: `scripts/sweeps/adfa_ld_embedding_binary_sweep.json:13-17` e `docs/seminario-andamento/tables/adfa-ld-binary-results.md:1-4`.
- Epocas: `18`. Evidencia: `scripts/sweeps/adfa_ld_embedding_binary_sweep.json:1-5` e `docs/seminario-andamento/tables/adfa-ld-binary-results.md:1-4`.
- Parametros treinaveis do campeao: `65.922`. Evidencia: `docs/seminario-andamento/tables/champion-run-summary.md:1-6`, `docs/seminario-andamento/evidence/adfa-ld/adfa-ld-analysis.md:51-55` e `docs/results-of-the-prototype.md:263-267`.
- Pesos de classe: inverso da frequencia, `weight(c) = n_samples / (n_classes * n_samples_of_c)`, passado como `class_weight` ao `fit`. Evidencia: `src/parallel_truth_fingerprint/lstm_service/offline_training/models/lstm_classifier.py:89-101` e formula em `src/parallel_truth_fingerprint/lstm_service/offline_training/models/lstm_classifier.py:123-137`; heranca do embedding em `src/parallel_truth_fingerprint/lstm_service/offline_training/models/embedding_classifiers.py:16-18` e `src/parallel_truth_fingerprint/lstm_service/offline_training/models/embedding_classifiers.py:52-58`.
- Validacao separada: **NÃO DOCUMENTADO**. O `fit` recebe apenas `x_train`, `y_train`, `epochs`, `batch_size`, `verbose` e `class_weight`; depois o teste e predito separadamente. Evidencia: chamada em `src/parallel_truth_fingerprint/lstm_service/offline_training/training/run.py:90-103` e `fit` em `src/parallel_truth_fingerprint/lstm_service/offline_training/models/lstm_classifier.py:94-101`.
- Early stopping: **NÃO DOCUMENTADO**. Nao ha `callbacks` no `fit` usado pelo classificador. Evidencia: `src/parallel_truth_fingerprint/lstm_service/offline_training/models/lstm_classifier.py:94-101`.
- Numero de seeds independentes: uma seed (`42`) no sweep binario; repeticoes independentes por seeds diferentes: **NÃO DOCUMENTADO**. Evidencia: `scripts/sweeps/adfa_ld_embedding_binary_sweep.json:1-17` e iteracao da grade sem eixo de seed em `src/parallel_truth_fingerprint/lstm_service/offline_training/training/sweep.py:46-96`.

## 6. Evolucao de FABA/BBD para CometBFT/ABCI

### 6.1 O que a proposta original dizia

A arquitetura proposta original listava validacao distribuida tolerante a falhas bizantinas como `BBD/FABA`. Evidencia: `docs/input/Arquitetura Baseada em Fonte de Verdade Paralela para Geração de Fingerprint Físico-Operacional em Sistemas Industriais Legados_ARQUITETURA_PROPOSTA.txt:10-16`.

O texto original dizia que cada Edge executaria mecanismo baseado em `BBD/FABA`, classificando nos como valido/suspeito/bizantino, e justificava FABA como estatistico, iterativo e leve. Evidencia: `docs/input/Arquitetura Baseada em Fonte de Verdade Paralela para Geração de Fingerprint Físico-Operacional em Sistemas Industriais Legados_ARQUITETURA_PROPOSTA.txt:106-132`.

### 6.2 O que o prototipo implementa

O PRD declara que, no prototipo, a implementacao real de consenso e CometBFT mais uma aplicacao ABCI em Go; BBD/FABA permanece inspiracao conceitual/teorica, nao biblioteca literal de runtime. Evidencia: `_bmad-output/planning-artifacts/prd.md:54-68`.

Os epicos repetem a mesma fronteira: CometBFT + Go ABCI e real no prototipo; BBD/FABA e conceitual salvo reaprovacao explicita. Evidencia: `_bmad-output/planning-artifacts/epics.md:94-99` e `_bmad-output/planning-artifacts/epics.md:136-140`.

A story de consenso tambem fixa que o caminho real e CometBFT + Go ABCI e que BBD/FABA deve ser usado apenas como base conceitual, sem alegar que seja a biblioteca literal de runtime. Evidencia: `_bmad-output/implementation-artifacts/2-2-implement-byzantine-style-consensus-evaluation.md:18-20`, `_bmad-output/implementation-artifacts/2-2-implement-byzantine-style-consensus-evaluation.md:53-66` e `_bmad-output/implementation-artifacts/2-2-implement-byzantine-style-consensus-evaluation.md:118-120`.

Motivo historico documentado para substituir ou nao implementar literalmente FABA/BBD: **NÃO DOCUMENTADO**. O que esta documentado e a fronteira de realidade do prototipo, nao uma decisao arquitetural retrospectiva completa. Evidencia: `_bmad-output/planning-artifacts/prd.md:54-68` e `_bmad-output/implementation-artifacts/2-2-implement-byzantine-style-consensus-evaluation.md:53-66`.

Motivo da escolha de CometBFT/ABCI alem de ser o caminho real aprovado do prototipo: **NÃO DOCUMENTADO**. Evidencia: o README descreve o papel da stack, mas nao apresenta comparativo de escolha em `README.md:128-132` e `README.md:305-312`.

### 6.3 Relacao entre CometBFT e ABCI

O README define:

- CometBFT e a camada BFT real;
- a aplicacao Go ABCI calcula o resultado deterministico de confianca/exclusao;
- a camada Python submete a rodada e le de volta o estado commitado.

Evidencia: `README.md:128-132`.

O runtime submete a rodada ao CometBFT, consulta a rodada commitada e entao mapeia o estado commitado para contratos locais. Evidencia: `scripts/run_local_demo.py:1135-1145`, cliente RPC em `src/parallel_truth_fingerprint/consensus/cometbft_client.py:60-91` e mapper em `src/parallel_truth_fingerprint/consensus/cometbft_mapper.py:28-120`.

A aplicacao ABCI valida transacoes em `CheckTx`, processa a rodada em `FinalizeBlock`, calcula app hash, persiste em `Commit` e responde consultas em `Query`. Evidencia: `abci/consensus_app/internal/app/app.go:70-95`, `abci/consensus_app/internal/app/app.go:109-161` e `abci/consensus_app/internal/app/app.go:164-190`.

### 6.4 Propriedades fornecidas por cada camada

Propriedades localmente evidenciadas do CometBFT no prototipo:

- camada BFT real que ordena/commita rodadas;
- receipt com `height`, `tx_hash`, `check_tx_code`, `deliver_tx_code`;
- fonte de verdade do resultado commitado lido pela camada Python.

Evidencia: `README.md:128-132`, `README.md:305-312`, `docs/seminario-andamento/tables/infrastructure-components.md:1-5`, `src/parallel_truth_fingerprint/consensus/cometbft_client.py:14-23` e `src/parallel_truth_fingerprint/consensus/cometbft_client.py:60-91`.

Propriedades detalhadas de seguranca/liveness do CometBFT, alem dessa descricao local: **NÃO DOCUMENTADO** no repositorio. Evidencia local disponivel limita-se a `README.md:128-132`, `README.md:305-312` e `docs/seminario-andamento/tables/infrastructure-components.md:1-5`.

Propriedades implementadas pela ABCI:

- distancia normalizada por sensor;
- score de confianca;
- contagem de peers compativeis;
- exclusao por falta de quorum compativel;
- classificacao textual do motivo com threshold `0.75`;
- estado consensado por media dos Edges validos quando ha quorum.

Evidencia: `abci/consensus_app/internal/app/app.go:17-31`, `abci/consensus_app/internal/app/app.go:225-365` e `abci/consensus_app/internal/app/app.go:381-421`.

### 6.5 Tres validadores e mesmo poder de voto

O `compose.consensus.yml` instancia tres nos CometBFT (`node0`, `node1`, `node2`) e tres apps ABCI (`abci-node0`, `abci-node1`, `abci-node2`). Evidencia: `compose.consensus.yml:1-99`.

O script de inicializacao chama `cometbft testnet --v 3`, ou seja, gera uma testnet com tres validadores. Evidencia: `scripts/init_cometbft_testnet.ps1:46-52`.

O genesis local existente mostra tres validadores (`node0`, `node1`, `node2`) com `power = "1"` para cada um. Evidencia: `.cometbft/testnet/node0/config/genesis.json:30-57`.

Limite real de falhas dos tres validadores com mesmo poder de voto segundo documentacao local do repositorio: **NÃO DOCUMENTADO**. O repositorio evidencia a topologia `3 x power 1`, mas nao documenta formalmente o calculo de tolerancia de falhas de validadores CometBFT nem deve-se inferir isso como justificativa sem fonte apropriada. Evidencia da topologia: `compose.consensus.yml:47-99`, `scripts/init_cometbft_testnet.ps1:46-52` e `.cometbft/testnet/node0/config/genesis.json:30-57`.

## 7. Tabela final para uso no seminario

| Questao | Resposta comprovada | Evidencia | Pode entrar no seminario? | Ressalva obrigatoria |
| --- | --- | --- | --- | --- |
| Formula do ruido | `noise_level = base_noise_floor + temperature_ratio_for_noise * 0.85 * noise_multiplier`; ruido aplicado com `Uniform(-1,1)` e amplitudes `5.0`, `0.35`, `60.0`. | `src/parallel_truth_fingerprint/sensor_simulation/behavior_model.py:86-104`; `src/parallel_truth_fingerprint/sensor_simulation/simulator.py:222-252`; `src/parallel_truth_fingerprint/config/ranges.py:26-33`. | Sim | Dizer que depende diretamente da temperatura enviesada e indiretamente da potencia. |
| Formula do score | `score = round(1 / (1 + overall_normalized_deviation), 3)`, com `overall` como media das distancias normalizadas aos peers. | `src/parallel_truth_fingerprint/consensus/trust_model.py:109-120`; `abci/consensus_app/internal/app/app.go:284-295`. | Sim | Score nao e probabilidade; e indice heuristico normalizado do prototipo. |
| Exclusao no `quorum_loss` | Todos os Edges foram excluidos porque cada um teve `compatible_peer_count=0`; para `N=3`, quorum=2, entao `0+1<2`. | `logs/sem-quorum-loss.log:620-630`; `docs/seminario-andamento/evidence/scenarios/quorum_loss/consensus-payload.pretty.json:1-35`; `src/parallel_truth_fingerprint/consensus/trust_model.py:109-138`. | Sim | Explicar que `edge-1` nao foi injetado como faltoso, mas ficou isolado por discordar dos dois peers modificados. |
| Threshold `0.75` | Nao decide exclusao; so decide o texto do motivo depois que a exclusao ja foi disparada pela regra de quorum compativel. | `src/parallel_truth_fingerprint/consensus/trust_model.py:133-138`; `abci/consensus_app/internal/app/app.go:307-311`. | Sim | Nao apresentar `0.75` como limiar de exclusao. |
| Janela de 60 segundos | `window_started_at = window_ended_at - timedelta(minutes=1)`. | `src/parallel_truth_fingerprint/edge_nodes/common/acquisition.py:349-363`; `docs/seminario-andamento/evidence/scenarios/quorum_loss/consensus-payload.pretty.json:37-40`. | Sim | Separar janela nominal de consenso da cadencia real do runtime. |
| `DEMO_CYCLE_INTERVAL_SECONDS=2` | O log registra ciclo com `interval_seconds=2.0`, mas isso e cadencia entre ciclos, nao tamanho da janela de consenso. | `logs/sem-quorum-loss.terminal.txt:12-18` e `logs/sem-quorum-loss.terminal.txt:35-40`; `scripts/run_local_demo.py:1124-1136`. | Sim | Usar datas/tempos absolutos da execucao de 2026-06-23. |
| Lacuna de `696.925860` segundos | O manifest tem artefatos adjacentes `19:19:48.013076` e `19:31:24.938936`; com `sequence_length=2`, uma janela cruza a lacuna. | `docs/seminario-andamento/evidence/custom-dataset/live-custom-dataset.manifest.pretty.json:41-64`; `src/parallel_truth_fingerprint/lstm_service/dataset_builder.py:151-175`. | Sim | Dizer que o builder nao valida continuidade temporal. |
| `sequence_length=2`, `stride=1` | Sao defaults/parametros do prototipo. Justificativa experimental: **NÃO DOCUMENTADO**. | `src/parallel_truth_fingerprint/lstm_service/lifecycle.py:23-27`; `src/parallel_truth_fingerprint/config/runtime.py:63-70`; `src/parallel_truth_fingerprint/lstm_service/dataset_artifacts.py:19-23`; `docs/seminario-andamento/evidence/custom-dataset/live-custom-dataset.manifest.pretty.json:9-11`. | Sim, como limitacao | Nao vender como escolha calibrada. |
| Pisos 30/20 | Sao defaults de adequacao, nao calibracao experimental documentada. | `src/parallel_truth_fingerprint/lstm_service/dataset_artifacts.py:19-58`; `docs/seminario-andamento/evidence/custom-dataset/live-custom-dataset.manifest.pretty.json:66-76`. | Sim, como criterio interno | Chamar de piso default do prototipo. |
| Tolerancias SCADA | `2.0 degC`, `0.35 bar`, `120 rpm`; regra `absolute_difference <= tolerance`. | `src/parallel_truth_fingerprint/comparison/service.py:23-29` e `src/parallel_truth_fingerprint/comparison/service.py:68-82`. | Sim | Calibracao por instrumento/fundo de escala: **NÃO DOCUMENTADO**. |
| Percentual das tolerancias | Temperatura `4.255%`, pressao `5.224%`, rpm `4.000%` do span simulado. | `src/parallel_truth_fingerprint/config/ranges.py:26-33`; `src/parallel_truth_fingerprint/comparison/service.py:23-29`. | Sim, apenas como calculo | Nao apresentar a porcentagem como criterio de escolha. |
| Vazamento ADFA-LD | Fluxo gera janelas antes do split e nao preserva `trace_id`; risco metodologico confirmado pelo fluxo. | `src/parallel_truth_fingerprint/lstm_service/offline_training/benchmarks/adfa_ld_embedding.py:98-149`; `src/parallel_truth_fingerprint/lstm_service/offline_training/splits.py:75-123`; `src/parallel_truth_fingerprint/lstm_service/offline_training/training/run.py:73-79`. | Sim, como ressalva | Chamar metricas de preliminares e informar que split por trace/grupo deve ser corrigido. |
| Metricas ADFA-LD | Campeao LSTM seq=80: macro F1 `0.9187`, accuracy `0.9229`, `65.922` parametros; teste com `1.634` janelas. | `docs/seminario-andamento/tables/adfa-ld-binary-results.md:1-11`; `docs/seminario-andamento/tables/champion-run-summary.md:1-6`; `docs/results-of-the-prototype.md:263-284`. | Sim | ADFA-LD e syscall de host, nao dado fisico-operacional industrial. |
| FABA/BBD versus CometBFT/ABCI | FABA/BBD e inspiracao conceitual; runtime real e CometBFT + Go ABCI. Motivo historico da substituicao: **NÃO DOCUMENTADO**. | `_bmad-output/planning-artifacts/prd.md:54-68`; `_bmad-output/planning-artifacts/epics.md:94-99` e `_bmad-output/planning-artifacts/epics.md:136-140`; `_bmad-output/implementation-artifacts/2-2-implement-byzantine-style-consensus-evaluation.md:53-66`. | Sim | Nao criar justificativa retrospectiva. |
| Propriedades CometBFT/ABCI | CometBFT ordena/commita e retorna height/hash/codes; ABCI calcula confianca, exclusao e estado valido. | `README.md:128-132`; `src/parallel_truth_fingerprint/consensus/cometbft_client.py:14-23` e `src/parallel_truth_fingerprint/consensus/cometbft_client.py:60-91`; `abci/consensus_app/internal/app/app.go:225-421`. | Sim | Limite formal de falha dos validadores CometBFT: **NÃO DOCUMENTADO** no repo. |
| Tres validadores mesmo poder | Topologia local tem 3 validadores e genesis local mostra `power="1"` para node0/node1/node2. | `compose.consensus.yml:47-99`; `init_cometbft_testnet.ps1:46-52`; `.cometbft/testnet/node0/config/genesis.json:30-57`. | Sim, como topologia | Nao declarar tolerancia formal de falhas sem fonte CometBFT externa ou decisao documentada. |
