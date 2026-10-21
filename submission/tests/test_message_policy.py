import unittest
from datetime import datetime, timezone

from submission.src.message_policy import verify_message_policy


class MessagePolicyTests(unittest.TestCase):
    def check(self, **overrides):
        args = {
            "channel": "PUSH",
            "now": datetime(2026, 10, 21, 10, 0, tzinfo=timezone.utc),
            "consent": True,
            "prior_message_times": [],
            "template_id": "approved_1",
            "approved_template_ids": {"approved_1"},
            "arm": "agent",
        }
        args.update(overrides)
        return verify_message_policy(**args)

    def test_approves_compliant_message(self):
        self.assertTrue(self.check()["approved"])

    def test_blocks_missing_consent(self):
        self.assertIn("message_consent_missing_or_denied",
                      self.check(consent=False)["failed"])

    def test_blocks_quiet_hours_in_ist(self):
        # 23:30 IST
        result = self.check(
            now=datetime(2026, 10, 21, 18, 0, tzinfo=timezone.utc)
        )
        self.assertIn("quiet_hours_ist", result["failed"])

    def test_blocks_second_message_same_ist_day(self):
        result = self.check(
            prior_message_times=[
                datetime(2026, 10, 21, 4, 0, tzinfo=timezone.utc)
            ]
        )
        self.assertIn("daily_message_cap", result["failed"])

    def test_blocks_unapproved_template(self):
        result = self.check(template_id="unapproved")
        self.assertIn("template_not_approved", result["failed"])

    def test_blocks_holdout(self):
        result = self.check(arm="holdout")
        self.assertIn("holdout_message_blocked", result["failed"])

    def test_fails_closed_on_naive_timestamp(self):
        with self.assertRaises(ValueError):
            self.check(now=datetime(2026, 10, 21, 10, 0))


if __name__ == "__main__":
    unittest.main()
