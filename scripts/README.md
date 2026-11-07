# Execution entry points

| Entry point | Function |
|---|---|
| `setup_windows.ps1` | Synchronize `.venv` from `uv.lock` |
| `init_cometbft_testnet.ps1` | Initialize the demo validator configuration |
| `start_consensus_stack.ps1`, `stop_consensus_stack.ps1` | Manage the demo consensus stack |
| `run_local_demo.py`, `run_local_dashboard.py` | Runtime and operator interface |
| `run_replay_evaluation.py` | Isolated collection, replay evaluation and syscall capture |
| `evaluate_hart_totalizer.py` | Instrumental LSTM and paired current-only evaluation |
| `evaluate_hart_multiseed.py` | Five training seeds on a frozen collection |
| `run_academic_experiments.py` | Public benchmark evaluation |
| `train_lstm_offline.py`, `train_lstm_sweep.py` | Offline classifier training and sweeps |
| `qualify_live_run.py` | Environment and input preflight |
| `validate_*.py` | Contract, parameter and provenance validation |

Run from the repository root. Python scripts use `src/`; inspect each CLI with
`--help`. Collection and model artifacts remain local.
