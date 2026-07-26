<!-- Fonte: _bmad-output/implementation-artifacts/embedding-adfa-ld-multiclass-sweep.md. STATUS: executado, mas NENHUM run atinge o criterio D6 (melhor macro F1 = 0.5610). O D6 e satisfeito apenas no enquadramento binario; o multiclasse e analise complementar (gap G2). -->
| modelo | sequence_length | epocas | seed | embed_dim | hidden_units | batch | learning_rate | macro_f1 | accuracy | macro_precision | macro_recall | run_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LSTM | 80 | 18 | 42 | 64 | 64 | 256 | 0.001 | 0.561 | 0.7162 | 0.5637 | 0.6221 | run-adfa-ld-embed-lstm-embedding-classifier-20260602T181527-6cca4b2a |
| GRU | 80 | 18 | 42 | 64 | 64 | 256 | 0.001 | 0.5497 | 0.7235 | 0.5467 | 0.5886 | run-adfa-ld-embed-gru-embedding-classifier-20260602T182638-c5f96045 |
| LSTM | 50 | 18 | 42 | 64 | 64 | 256 | 0.001 | 0.4985 | 0.6667 | 0.4785 | 0.5695 | run-adfa-ld-embed-lstm-embedding-classifier-20260602T181201-69553ca3 |
| GRU | 120 | 18 | 42 | 64 | 64 | 256 | 0.001 | 0.4867 | 0.706 | 0.4957 | 0.5359 | run-adfa-ld-embed-gru-embedding-classifier-20260602T183145-c55d071b |
| LSTM | 120 | 18 | 42 | 64 | 64 | 256 | 0.001 | 0.4758 | 0.7053 | 0.4885 | 0.5266 | run-adfa-ld-embed-lstm-embedding-classifier-20260602T182021-0e27a06c |
| GRU | 50 | 18 | 42 | 64 | 64 | 256 | 0.001 | 0.4651 | 0.641 | 0.4577 | 0.5374 | run-adfa-ld-embed-gru-embedding-classifier-20260602T182243-084012c3 |

> Fonte: _bmad-output/implementation-artifacts/embedding-adfa-ld-multiclass-sweep.md. STATUS: executado, mas NENHUM run atinge o criterio D6 (melhor macro F1 = 0.5610). O D6 e satisfeito apenas no enquadramento binario; o multiclasse e analise complementar (gap G2).
