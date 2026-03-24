# Arquitetura do Protótipo

## Componentes

### Sensor Simulators
Três simuladores de sensores de um compressor:
- TemperatureSensor1
- PressureSensor1
- RPMSensor1

### Edge Collectors
Cada edge coleta apenas um sensor local:
- Edge1 -> temperatura
- Edge2 -> pressão
- Edge3 -> rotação

### MQTT + Broker
Canal de publicação e consumo entre edges.

### Edge State Replication
Cada edge publica sua leitura e consome as leituras dos outros, formando uma visão compartilhada do compressor.

### Byzantine Consensus Service
Executado logicamente em cada edge, avaliando ranking de confiança dos edges e removendo edge suspeito da rodada.

### OPC UA Fake SCADA
Servidor OPC UA simples representando a árvore do SCADA.

### Comparison Service
Compara os dados consensados com os dados do SCADA fake usando tolerância configurável.

### Storage Layer
Storage local simulando nuvem, preferencialmente com MinIO local.

### LSTM Service
Consome dados válidos armazenados, treina com comportamento normal, gera fingerprint e detecta anomalias.

## Fluxo resumido
1. Sensor simulado gera leitura
2. Edge local coleta
3. Edge publica no broker via MQTT
4. Todos os edges consomem todos os dados
5. Consenso bizantino calcula confiança
6. Estado consolidado válido é definido
7. Comparação com SCADA é executada
8. Alertas são emitidos se houver divergência
9. Dados válidos vão para o storage
10. LSTM treina/infere fingerprint
11. Alertas de anomalia são emitidos