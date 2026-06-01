import unittest

from pulselens.analyzer import analyze, risk_level, risk_type


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
        self.assertIn(result.risk_level, {"L3", "L4", "L5"})

    def test_risk_level_boundaries(self):
        self.assertEqual(risk_level(0), "L0")
        self.assertEqual(risk_level(21), "L1")
        self.assertEqual(risk_level(41), "L2")
        self.assertEqual(risk_level(61), "L3")
        self.assertEqual(risk_level(76), "L4")
        self.assertEqual(risk_level(91), "L5")

    def test_chinese_terms_and_risk_type(self):
        result = analyze("爆料：门店卫生糟糕，很多顾客投诉并要求退款。", reach=76000)
        self.assertLess(result.sentiment, 0)
        self.assertIn(result.risk_type, {"service", "reputation"})
        self.assertGreaterEqual(result.risk_score, 60)

    def test_privacy_risk_type(self):
        self.assertEqual(risk_type("有人泄露手机号和住址，涉及隐私风险。"), "privacy")


if __name__ == "__main__":
    unittest.main()
