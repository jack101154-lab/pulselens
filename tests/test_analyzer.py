import unittest

from pulselens.analyzer import analyze, risk_level


class AnalyzerTest(unittest.TestCase):
    def test_positive_low_risk_can_be_amplified(self):
        result = analyze("Acme is reliable, secure, and helpful.", aliases=["Acme"], reach=100)
        self.assertGreater(result.sentiment, 0)
        self.assertIn(result.strategy, {"amplify", "neutral-watch"})

    def test_urgent_negative_reaches_high_risk(self):
        result = analyze(
            "Breaking data breach investigation: Acme is unsafe and customers are angry.",
            aliases=["Acme"],
            reach=100000,
            source_weight=1.5,
        )
        self.assertLess(result.sentiment, 0)
        self.assertGreaterEqual(result.risk_score, 60)
        self.assertIn(result.strategy, {"de-escalate", "crisis-response"})

    def test_risk_level_boundaries(self):
        self.assertEqual(risk_level(0), "low")
        self.assertEqual(risk_level(20), "guarded")
        self.assertEqual(risk_level(40), "elevated")
        self.assertEqual(risk_level(60), "high")
        self.assertEqual(risk_level(80), "critical")


if __name__ == "__main__":
    unittest.main()
