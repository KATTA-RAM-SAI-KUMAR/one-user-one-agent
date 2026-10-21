
import unittest

from src.goal_planner import plan_goal
from src.verifier import verify_action


class PlannerVerifierTests(unittest.TestCase):

    def test_planner_abstains_without_evidence(self):
        result = plan_goal(
            goals=[{
                "id": "G01",
                "success_event": "episode_completed",
                "window_days": 3,
            }],
            facts={},
            evidence={},
            started_at="2026-10-01T10:00:00Z",
        )
        self.assertIsNone(result["goal"])

    def test_holdout_action_is_rejected(self):
        result = verify_action(
            {"action": "PUSH"},
            arm="holdout",
            trigger_id="E1",
            processed_trigger_ids=set(),
            notifications_opt_in=True,
        )
        self.assertFalse(result["approved"])

    def test_duplicate_trigger_is_rejected(self):
        result = verify_action(
            {"action": "HOME_PAGE"},
            arm="agent",
            trigger_id="E1",
            processed_trigger_ids={"E1"},
        )
        self.assertFalse(result["approved"])

    def test_unavailable_home_page_title_is_rejected(self):
        result = verify_action(
            {
                "action": "HOME_PAGE",
                "content": ["TITLE_1"],
                "rows": [{"title_ids": ["TITLE_1", "TITLE_2", "TITLE_3"]}],
                "dialect": {"used": "te"},
            },
            arm="agent",
            trigger_id="E2",
            processed_trigger_ids=set(),
            available_title_ids={"TITLE_2", "TITLE_3"},
        )
        self.assertFalse(result["approved"])
        self.assertIn("title_availability", result["failed"])

    def test_dialect_mismatch_is_rejected(self):
        result = verify_action(
            {
                "action": "HOME_PAGE",
                "content": ["TITLE_1", "TITLE_2", "TITLE_3"],
                "rows": [{"title_ids": ["TITLE_1", "TITLE_2", "TITLE_3"]}],
                "dialect": {"used": "te"},
            },
            arm="agent",
            trigger_id="E3",
            processed_trigger_ids=set(),
            available_title_ids={"TITLE_1", "TITLE_2", "TITLE_3"},
            title_dialects={
                "TITLE_1": "te",
                "TITLE_2": "hi",
                "TITLE_3": "te",
            },
        )
        self.assertFalse(result["approved"])
        self.assertIn("title_dialect", result["failed"])

    def test_push_without_consent_is_rejected(self):
        result = verify_action(
            {
                "action": "PUSH",
                "message_title": "New episode",
                "message_body": "Continue watching your show",
                "deeplink": "ott://title/TITLE_1",
            },
            arm="agent",
            trigger_id="E4",
            processed_trigger_ids=set(),
            notifications_opt_in=False,
            now="2026-10-19T12:00:00+05:30",
        )
        self.assertFalse(result["approved"])
        self.assertIn("channel_consent", result["failed"])


if __name__ == "__main__":
    unittest.main()
