# Inferencia online com modelo promovido - resumo (LIVE 2026-06-23)

**Resultado: SUCESSO.** O runtime carregou o modelo promovido a partir do ponteiro de
promocao e classificou uma janela de teste de ponta a ponta.

| Campo | Valor |
| --- | --- |
| promoted_run_id | `run-adfa-ld-gru-classifier-20260521T173524-3fc71cc1` |
| modelo | gru-classifier (re-treinado na carga - atalho documentado, gap G3) |
| label_names | ['Normal', 'Adduser', 'Hydra-FTP', 'Hydra-SSH', 'Java-Meterpreter', 'Web-Shell'] |
| sequence_length | 30 |
| feature_count | 1 |
| janela de entrada | zeros[30x1] synthetic probe window |
| classe prevista | **Normal** (id 0) |
| probabilidades | [0.347211, 0.027301, 0.170606, 0.228406, 0.089162, 0.137313] |

## Leitura honesta / ressalvas

1. **O modelo promovido no store LOCAL e o run multiclasse GRU de 2026-05-21**
   (`run-adfa-ld-gru-classifier-20260521T173524-3fc71cc1`), com 6 classes ADFA-LD. **Nao** e o campeao binario
   LSTM de 2026-06-02 (`run-adfa-ld-embed-binary-lstm-embedding-classifier-20260602T175338-3acfb039`)
   citado no relatorio tecnico. Aquela promocao binaria foi feita contra o MinIO
   (`--persist`) e o ponteiro nao esta presente no store local deste repositorio.
   O `index/latest.json` local aponta para o run GRU multiclasse.
2. A carga **re-treina** o modelo (atalho da Story 8.2, ~tempo de fit na carga). Os pesos
   reais nao sao persistidos ainda (gap G3 / "persistir pesos reais").
3. A janela de entrada usada e uma **sonda sintetica** (zeros de forma `seq x feat`), apenas
   para provar o caminho carga->classificacao. Nao e uma medicao fisico-operacional.
4. Portanto esta evidencia comprova **a integracao do canal de inferencia online**
   (ponteiro de promocao -> reconstrucao -> classificacao), e nao a metrica academica do
   fingerprint (essa esta em ADFA-LD binario, ver evidence/adfa-ld/).

> Saida bruta completa: `online-inference-output.txt`. Comando: `online-inference-command.txt`.
