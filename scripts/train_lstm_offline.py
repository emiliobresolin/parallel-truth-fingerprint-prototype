"""Thin wrapper around the offline training CLI.

Usage:
    venv\\Scripts\\python.exe scripts\\train_lstm_offline.py \\
        --benchmark dummy --model dummy \\
        --epochs 2 --batch-size 4 --learning-rate 0.01 \\
        --sequence-length 5 --seed 42

Real benchmarks (adfa-ld, lid-ds-2021) and the real LSTM classifier are
added by later stories. Story 7.1 only exercises the scaffold.
"""

from __future__ import annotations

from parallel_truth_fingerprint.lstm_service.offline_training.cli import main


if __name__ == "__main__":
    main()
