# Matriz de confusão — campeão binário ADFA-LD (LSTM, seq=80)

Split de teste: 1.634 janelas (1.041 Normal / 593 Attack).

|                 | pred Normal | pred Attack |
| --------------- | ----------: | ----------: |
| **true Normal** |         940 |         101 |
| **true Attack** |          25 |         568 |

- **macro F1 = 0.9187**, **accuracy = 0.9229**
- **recall de ataque = 0.958** — apenas 25 de 593 janelas de ataque foram perdidas (baixo falso-negativo, a propriedade mais importante para um fingerprint de intrusão)
- **FPR em normal = 4.2%** (101 de 1.041 janelas normais marcadas como ataque)

> Fonte: `docs/results-of-the-prototype.md` §5.3 (campeão `run-adfa-ld-embed-binary-lstm-embedding-classifier-20260602T175338-3acfb039`, verificado do registro persistido). Versão em dados: `tables/confusion-matrix.csv`.
