from __future__ import annotations

import unittest

from parallel_truth_fingerprint.contracts.syscall_blind_scores import (
    SYSCALL_DETECTOR_SCORE_SCHEMA,
    SyscallBlindScore,
    SyscallDetectorScore,
    SyscallScoreDecision,
    finalize_syscall_detector_score,
)


class SyscallBlindScoreTests(unittest.TestCase):
    def test_score_without_value_is_blocked(self) -> None:
        digest = lambda char: "sha256:" + char * 64
        with self.assertRaises(ValueError):
            SyscallBlindScore(
                digest("a"), digest("b"), digest("c"), None, "scored", digest("d"), digest("e")
            ).validate()

    def test_full_detector_contract_remains_available_to_the_scoring_path(self) -> None:
        digest = lambda char: "sha256:" + char * 64
        score = SyscallDetectorScore(
            SYSCALL_DETECTOR_SCORE_SCHEMA, digest("a"), "window-1", digest("b"), "0.2", "0.2",
            "higher_is_anomalous", digest("c"), SyscallScoreDecision.NORMAL, None, digest("d"),
            digest("e"), digest("f"), digest("a"), digest("b"), digest("c"), digest("d"), None,
        )
        self.assertTrue(finalize_syscall_detector_score(score).score_id.startswith("sha256:"))


if __name__ == "__main__":
    unittest.main()
