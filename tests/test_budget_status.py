import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aji.budget_status import summarize_budget


def budget(actual="0.001", currency="USD"):
    return {"BudgetName": "aji-project-dev",
            "BudgetLimit": {"Amount": "5.0", "Unit": currency},
            "CalculatedSpend": {"ActualSpend": {"Amount": actual, "Unit": currency}}}


def notifications():
    return [{"NotificationType": "ACTUAL", "ThresholdType": "ABSOLUTE_VALUE",
             "ComparisonOperator": "GREATER_THAN", "Threshold": amount}
            for amount in (3.0, 5.0)]


class BudgetStatusTests(unittest.TestCase):
    def test_reports_observed_tagged_spend_without_claiming_a_hard_limit(self):
        result = summarize_budget(budget(), notifications())

        self.assertEqual(result["status"], "BELOW_ALERT")
        self.assertEqual(result["observed_usd"], 0.001)
        self.assertEqual(result["alert_thresholds_usd"], [3.0, 5.0])
        self.assertEqual(result["limit_usd"], 5.0)
        self.assertEqual(result["coverage"], "tagged_project_only")
        self.assertTrue(result["costs_may_lag"])

    def test_alert_threshold_is_reported_even_before_aws_notification_delivery(self):
        result = summarize_budget(budget("3.5"), notifications())

        self.assertEqual(result["status"], "AT_OR_ABOVE_ALERT")
        self.assertEqual(result["highest_crossed_alert_usd"], 3.0)

    def test_wrong_currency_or_missing_actual_alerts_fails_closed(self):
        with self.assertRaises(ValueError):
            summarize_budget(budget(currency="MXN"), notifications())
        with self.assertRaises(ValueError):
            summarize_budget(budget(), [{"NotificationType": "FORECASTED",
                                         "ThresholdType": "PERCENTAGE",
                                         "Threshold": 80.0}])
        with self.assertRaises(ValueError):
            summarize_budget(budget(actual="NaN"), notifications())


if __name__ == "__main__":
    unittest.main()
