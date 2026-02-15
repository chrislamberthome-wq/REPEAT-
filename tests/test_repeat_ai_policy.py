from __future__ import annotations

import unittest

from repeat_ai.policy import Policy, evaluate_paths

class TestRepeatAiPolicy(unittest.TestCase):
    def test_policy_precedence_and_unmatched(self) -> None:
        policy = Policy(
            version="repeat-ai-policy-v1",
            deny=["/environment/**"],
            warn=["/response/**"],
            allow=["/response/body/output_text"],
            unmatched="warn",
        )

        paths = [
            "/environment/python",
            "/response/body/output_text",
            "/response/body/usage/total_tokens",
            "/request/body/input",
        ]

        res = evaluate_paths(paths, policy)

        self.assertEqual(res.counts.deny, 1)
        self.assertIn(("/environment/python", "DENY"), res.items)
        self.assertIn(("/response/body/output_text", "ALLOW"), res.items)
        self.assertIn(("/response/body/usage/total_tokens", "WARN"), res.items)
        self.assertIn(("/request/body/input", "WARN"), res.items)

if __name__ == "__main__":
    unittest.main()
