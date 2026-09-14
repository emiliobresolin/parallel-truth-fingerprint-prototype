# Qualificação para execução viva — 2026-09-13

## Decisão

**Não iniciar a matriz de comparação nem publicar números nesta máquina.** O
preflight `scripts/qualify_live_run.py` retorna código `2`, isto é, falha
fechada. Nenhum dado de fixture, referência histórica ou ponteiro Git LFS pode
substituir os bytes oficiais ausentes.

## Evidência observada

| Item | Estado | Evidência/resultado |
| --- | --- | --- |
| MQTT e MinIO locais | Disponíveis | `ptfp-mqtt-broker` e `ptfp-minio` estavam ativos. |
| CometBFT + 3 ABCI | Disponíveis | A inicialização local deixou os três nós e três serviços ABCI ativos. |
| ADFA-LD | Presente localmente | Há uma cópia em `datasets/ADFA-LD`; sua origem deve continuar identificada como cópia histórica/mirror até que um inventário oficial seja pinado. |
| LID-DS 2021 | **Bloqueado** | O repositório oficial foi obtido em `datasets/LID-DS-2021`, mas ele contém o framework e um link de download, não os traces `.sc2` oficiais nem os papéis `normal`/`attack`. |
| HAI 23.05 | **Bloqueado** | O repositório oficial foi obtido em `datasets/HAI-23.05`, mas o checkout dos CSVs foi impedido pela cota Git LFS do proprietário. Os oito arquivos necessários estão ausentes/inacessíveis. |
| Autoencoder de runtime | Corrigido para uso seguro | `DEMO_DISABLE_RUNTIME_AUTOENCODER=true` é agora o padrão. O autoencoder legado não gera evidência acadêmica nem métricas de benchmark. |
| Sinal de instrumentação | Implementado como corrente | A rota `SignalObservation.v2`, transmissor, OPC UA v2 e contratos de comparação usam `raw_current`/`raw_current_ma` com unidade `mA`; valores de engenharia permanecem derivados e rastreáveis. |
| Compressor variável | Implementado | `DEMO_POWER` e o controle do dashboard alimentam `simulator.step(compressor_power=...)`; o valor é registrado no snapshot de cada ciclo. |
| Pipeline físico | Executável após o preflight | Sensores → três edges → MQTT → CometBFT/ABCI → OPC UA/SCADA → MinIO → dataset normal-only. |
| Syscalls de edge | Não qualificados nesta máquina | A captura Linux real requer ambiente Linux e a carga allowlisted; Windows não deve simular esse resultado como captura real. |

## Consequências para resultados

- Não há resultado medido novo para LID-DS ou HAI 23.05.
- Não há base para declarar uma matriz externa completa, nem para juntar HAI,
  LID, ADFA ou dados do compressor em uma única métrica.
- O dataset gerado pelo runtime é de dados físicos válidos e normais; ele não
  é um benchmark rotulado nem substituto para dados de syscall.
- Qualquer execução do pipeline local deve manter o autoencoder desativado e
  distinguir explicitamente dados simulados do compressor de dados oficiais.

## Próxima condição de liberação

1. Obter os CSVs oficiais HAI 23.05 pela publicação do próprio grupo no Kaggle.
   Ela exige autenticação local; execute `.venv\Scripts\kaggle.exe auth login`
   e depois `scripts\download_hai_official.ps1`. Isso baixa para
   `datasets\HAI-23.05-kaggle` sem registrar token no repositório.
2. Abrir o link `LID-DS 2021: download` no `README.md` do repositório oficial,
   baixar o arquivo público, extrair os traces em
   `datasets\LID-DS-2021-real` e registrar o escopo/cenário autorizado.
3. Adaptar/validar o layout contra esses bytes reais, executar novamente
   `scripts/qualify_live_run.py` e só então iniciar a matriz.
