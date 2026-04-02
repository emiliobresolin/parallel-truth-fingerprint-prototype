"""Start the local Story 4.6 operator dashboard and control surface."""

from __future__ import annotations

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from parallel_truth_fingerprint.config.runtime import load_runtime_demo_config
from parallel_truth_fingerprint.dashboard import (
    LocalOperatorDashboardController,
    LocalOperatorDashboardServer,
)


def main() -> None:
    config = load_runtime_demo_config()
    controller = LocalOperatorDashboardController(config)
    server = LocalOperatorDashboardServer(
        controller,
        host=config.demo_dashboard_host,
        port=config.demo_dashboard_port,
    )
    try:
        print(f"Story 4.6 dashboard ready at {server.base_url}")
        print("Use the dashboard to start or stop the runtime and control scenarios.")
        server.start_in_background()
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\nDashboard stopped manually.")
    finally:
        server.stop()


if __name__ == "__main__":
    main()
