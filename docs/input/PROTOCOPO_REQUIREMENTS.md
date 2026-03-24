# Requisitos do Protótipo

## Requisitos funcionais
- RF01: Simular 3 sensores de um compressor
- RF02: Cada edge deve coletar somente seu sensor local
- RF03: Cada edge deve publicar dados no MQTT
- RF04: Cada edge deve consumir dados dos outros edges
- RF05: O sistema deve manter uma visão compartilhada do compressor
- RF06: Deve existir consenso bizantino entre os edges
- RF07: O consenso deve produzir ranking de confiança e isso deve constar no pacote que vai pro bucket.
- RF08: Edge suspeito deve ser excluído da rodada
- RF09: Deve existir SCADA fake em OPC UA
- RF10: Deve existir comparação sensor por sensor com tolerância
- RF11: Deve gerar alerta quando SCADA divergir do físico consensado
- RF12: Deve persistir dados válidos em storage local (bucket)
- RF13: Deve existir treinamento LSTM com dados normais
- RF14: Deve gerar fingerprint do equipamento
- RF15: Deve gerar score e classe normal/anômalo
- RF16: Deve salvar modelo/fingerprint
- RF17: Deve detectar cenário de replay

## Requisitos não funcionais
- RNF01: Rodar localmente
- RNF02: Priorizar Python
- RNF03: Ser simples e demonstrável
- RNF04: Ter logs claros para apresentação
- RNF05: Ser modular
- RNF06: Permitir futura substituição do storage local por nuvem real