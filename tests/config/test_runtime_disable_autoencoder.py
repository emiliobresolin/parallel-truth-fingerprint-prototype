"""Story 8.3: DEMO_DISABLE_RUNTIME_AUTOENCODER env var parsing."""

from __future__ import annotations

import os
import unittest

from parallel_truth_fingerprint.config.runtime import load_runtime_demo_config


class DisableRuntimeAutoencoderTests(unittest.TestCase):
    def test_default_is_false_when_env_var_absent(self) -> None:
        previous = os.environ.pop("DEMO_DISABLE_RUNTIME_AUTOENCODER", None)
        try:
            config = load_runtime_demo_config()
            self.assertFalse(config.demo_disable_runtime_autoencoder)
        finally:
            if previous is not None:
                os.environ["DEMO_DISABLE_RUNTIME_AUTOENCODER"] = previous

    def test_truthy_values_set_switch(self) -> None:
        previous = os.environ.get("DEMO_DISABLE_RUNTIME_AUTOENCODER")
        try:
            for truthy in ("1", "true", "TRUE", "yes", "on"):
                os.environ["DEMO_DISABLE_RUNTIME_AUTOENCODER"] = truthy
                config = load_runtime_demo_config()
                self.assertTrue(
                    config.demo_disable_runtime_autoencoder,
                    f"Expected truthy parsing for {truthy!r}",
                )
        finally:
            if previous is None:
                os.environ.pop("DEMO_DISABLE_RUNTIME_AUTOENCODER", None)
            else:
                os.environ["DEMO_DISABLE_RUNTIME_AUTOENCODER"] = previous

    def test_falsy_values_keep_switch_false(self) -> None:
        previous = os.environ.get("DEMO_DISABLE_RUNTIME_AUTOENCODER")
        try:
            for falsy in ("0", "false", "no", "off", ""):
                os.environ["DEMO_DISABLE_RUNTIME_AUTOENCODER"] = falsy
                config = load_runtime_demo_config()
                self.assertFalse(
                    config.demo_disable_runtime_autoencoder,
                    f"Expected falsy parsing for {falsy!r}",
                )
        finally:
            if previous is None:
                os.environ.pop("DEMO_DISABLE_RUNTIME_AUTOENCODER", None)
            else:
                os.environ["DEMO_DISABLE_RUNTIME_AUTOENCODER"] = previous


if __name__ == "__main__":
    unittest.main()
