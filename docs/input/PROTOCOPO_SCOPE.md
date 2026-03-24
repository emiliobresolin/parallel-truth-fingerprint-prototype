# Escopo do Protótipo

## Objetivo
Construir uma prova de conceito simples e demonstrável de uma arquitetura para geração de fingerprint físico-operacional com fonte de verdade paralela em ambiente industrial simulado.

## O que deve ser real
- Descentralização entre edges
- Consenso bizantino entre edges
- Comparação com SCADA
- Geração de fingerprint com LSTM

## O que será simulado
- Sensores físicos
- Edge devices como hardware
- Ambiente industrial/fábrica
- Rede industrial real
- SCADA real
- Nuvem real

## Topologia mínima
- 3 sensores
- 3 edges
- 1 broker (Orion por exemplio) 
- 1 protocolo de comunicação com o broker: MQTT
- 1 servidor OPC UA fake
- 1 storage local estilo nuvem
- 1 serviço LSTM

## Critério de sucesso
O protótipo deve:
1. coletar dados simulados dos sensores
2. replicar os dados entre os edges via MQTT
3. realizar consenso bizantino entre edges
4. excluir edge suspeito na rodada
5. comparar estado consensado com SCADA
6. gerar alerta por divergência com SCADA
7. persistir dados válidos no storage
8. treinar LSTM com comportamento normal
9. gerar fingerprint e score/classificação
10. detectar pelo menos um cenário de replay/anomalia