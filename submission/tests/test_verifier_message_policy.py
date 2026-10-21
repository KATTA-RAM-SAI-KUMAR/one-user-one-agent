import unittest
from datetime import datetime, timezone

from submission.src.verifier import verify_action


NOW = datetime(2026, 10, 21, 10, 0, tzinfo=timezone.utc)


class VerifierMessagePolicyTests(unittest.TestCase):
    def verify(self, *, action="PUSH", decision_override=None, **overrides):
        decision = {
            "action": action,
            "message_title": "Continue watching",
            "message_body": "Pick up where you left off.",
            "deeplink": "ott://title/title_1",
            "template_id": "approved_1",
            "now": NOW.isoformat(),
        }
        if decision_override is not None:
            decision = decision_override
        args = {
            "arm": "agent",
            "trigger_id": "trigger_1",
            "processed_trigger_ids": set(),
            "notifications_opt_in": True,
            "whatsapp_opt_in": True,
            "now": NOW.isoformat(),
            "approved_template_ids": {"approved_1"},
        }
        args.update(overrides)
        return verify_action(decision, **args)

    def test_approved_push_passes_policy(self):
        result = self.verify()
        self.assertTrue(result["approved"], result["failed"])

    def test_push_without_consent_is_rejected(self):
        result = self.verify(notifications_opt_in=False)
        self.assertFalse(result["approved"])
        self.assertIn("channel_consent", result["failed"])

    def test_unapproved_template_is_rejected(self):
        result = self.verify(approved_template_ids=set())
        self.assertFalse(result["approved"])
        self.assertIn(
            "message_policy:template_not_approved", result["failed"]
        )

    def test_quiet_hours_are_rejected(self):
        quiet_time = datetime(
            2026, 10, 21, 18, 0, tzinfo=timezone.utc
        ).isoformat()
        result = self.verify(now=quiet_time)
        self.assertFalse(result["approved"])
        self.assertIn("message_policy:quiet_hours_ist", result["failed"])

    def test_same_day_message_is_rejected(self):
        previous = datetime(
            2026, 10, 21, 4, 0, tzinfo=timezone.utc
        )
        result = self.verify(prior_message_times=[previous])
        self.assertFalse(result["approved"])
        self.assertIn("message_policy:daily_message_cap", result["failed"])

    def test_holdout_message_is_rejected(self):
        result = self.verify(arm="holdout")
        self.assertFalse(result["approved"])

    def test_missing_publish_time_fails_closed(self):
        result = self.verify(now=None)
        self.assertFalse(result["approved"])
        self.assertIn(
            "message_policy_unverifiable_publish_time", result["failed"]
        )

    def test_whatsapp_without_consent_is_rejected(self):
        result = self.verify(
            action="WHATSAPP", whatsapp_opt_in=False
        )
        self.assertFalse(result["approved"])
        self.assertIn("channel_consent", result["failed"])

    def test_in_app_without_explicit_consent_is_rejected(self):
        result = self.verify(
            action="IN_APP",
            decision_override={"action": "IN_APP", "template_id": "approved_1",
                               "now": NOW.isoformat()},
        )
        self.assertFalse(result["approved"])
        self.assertIn("channel_consent", result["failed"])


if __name__ == "__main__":
    unittest.main()
