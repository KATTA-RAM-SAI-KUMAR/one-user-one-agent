
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


if __name__ == "__main__":
    unittest.main()
