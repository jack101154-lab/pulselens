import unittest

from pulselens.topics import cluster_mentions, detect_topic


class TopicsTest(unittest.TestCase):
    def test_detects_data_security_topic(self):
        row = {
            "text": "Breaking data breach investigation after possible customer data leak.",
            "risk_type": "security",
        }
        self.assertEqual(detect_topic(row), "data-security")

    def test_clusters_mentions_by_topic(self):
        rows = [
            {"id": 1, "text": "客服处理投诉和退款太慢", "risk_type": "service", "risk_score": 72, "risk_level": "L3", "entity_name": "A"},
            {"id": 2, "text": "售后服务态度糟糕", "risk_type": "service", "risk_score": 66, "risk_level": "L3", "entity_name": "A"},
            {"id": 3, "text": "用户推荐新品，整体满意", "risk_type": "general", "risk_score": 20, "risk_level": "L0", "entity_name": "B"},
        ]
        clusters = cluster_mentions(rows)
        self.assertEqual(clusters[0]["topic"], "customer-service")
        self.assertEqual(clusters[0]["count"], 2)
        self.assertEqual(clusters[0]["max_risk"], 72)


if __name__ == "__main__":
    unittest.main()
