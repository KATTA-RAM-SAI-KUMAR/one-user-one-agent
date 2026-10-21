import unittest
from datetime import datetime, timezone

from submission.src.goal_outcome_evaluator import evaluate_assignment

UTC = timezone.utc


def moment(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def make_assignment(goal_id="G01", start="2026-10-01T10:00:00Z"):
    return {
        "user_id": "USER-1",
        "arm": "agent",
        "goal_id": goal_id,
        "goal_started_at": moment(start),
        "action_ids": ["ACTION-1"],
    }


def make_goal(hours=24, event="play_started"):
    return {
        "goal_id": "G01",
        "name": "Test goal",
        "success": {"event": event, "window_hours": hours},
    }


def make_event(event_id, event_name, at, user_id="USER-1", properties=None):
    return {
        "event_id": event_id,
        "user_id": user_id,
        "event": event_name,
        "properties": properties or {},
        "_evaluation_time": moment(at),
    }


class GoalOutcomeEvaluatorTests(unittest.TestCase):
    def test_matching_event_within_deadline_succeeds(self):
        result = evaluate_assignment(
            make_assignment(),
            make_goal(),
            [make_event("E1", "play_started", "2026-10-01T11:00:00Z")],
            {},
            moment("2026-10-02T10:00:00Z"),
        )
        self.assertEqual(result["status"], "SUCCEEDED")
        self.assertEqual(result["evidence_event_ids"], ["E1"])

    def test_no_success_after_deadline_fails(self):
        result = evaluate_assignment(
            make_assignment(),
            make_goal(),
            [],
            {},
            moment("2026-10-03T10:00:00Z"),
        )
        self.assertEqual(result["status"], "FAILED")

    def test_before_deadline_without_success_is_inconclusive(self):
        result = evaluate_assignment(
            make_assignment(),
            make_goal(),
            [],
            {},
            moment("2026-10-01T12:00:00Z"),
        )
        self.assertEqual(result["status"], "INCONCLUSIVE")

    def test_event_after_deadline_does_not_count(self):
        result = evaluate_assignment(
            make_assignment(),
            make_goal(),
            [make_event("E-late", "play_started", "2026-10-02T10:00:01Z")],
            {},
            moment("2026-10-03T10:00:00Z"),
        )
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(result["evidence_event_ids"], [])

    def test_g03_requires_play_on_later_ist_calendar_day(self):
        assignment = make_assignment(
            "G03", "2026-10-01T20:00:00Z"
        )
        goal = {
            "goal_id": "G03",
            "name": "Return on a later day",
            "success": {"event": "app_open", "window_hours": 72},
        }
        result = evaluate_assignment(
            assignment,
            goal,
            [make_event("E-return", "play_started", "2026-10-02T19:00:00Z")],
            {},
            moment("2026-10-05T20:00:00Z"),
        )
        self.assertEqual(result["status"], "SUCCEEDED")
        self.assertEqual(result["success_event"], "play_started")


if __name__ == "__main__":
    unittest.main()
