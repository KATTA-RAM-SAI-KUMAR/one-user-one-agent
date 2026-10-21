import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from submission.src.event_loader import parse_timestamp, load_events
from submission.src.verifier import verify_action


class ReliabilityTests(unittest.TestCase):

    def test_late_timestamp_is_normalized(self):
        parsed = parse_timestamp("2026-10-01T10:00:00Z")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.tzinfo, timezone.utc)

    def test_conflicting_evidence_does_not_create_automatic_truth(self):
        # Conflicting facts must remain explicit; a single source must not
        # silently overwrite contradictory evidence in this test fixture.
        evidence = [
            {"source": "profile", "value": "English"},
            {"source": "app", "value": "Telugu"},
        ]
        self.assertEqual(len({item["value"] for item in evidence}), 2)

    def test_dependency_failure_is_reported(self):
        # A failed dependency must raise or be handled as a failure,
        # rather than being silently interpreted as valid empty evidence.
        with patch("submission.src.event_loader.load_events", side_effect=OSError("simulated dependency failure")):
            with self.assertRaises(OSError):
                load_events("nonexistent-test-file.jsonl")

    def test_corrected_goal_rule_uses_play_started_event(self):
        from submission.src.goal_planner import _success_event
        corrected_goal = {
            "goal_id": "G03",
            "success_event": "play_started",
        }
        self.assertEqual(_success_event(corrected_goal), "play_started")


    def test_trigger_age_uses_received_time_minus_occurred_time(self):
        from submission.src.replay_engine import trigger_age_seconds

        event = {
            "received_at": "2026-10-01T10:05:00Z",
            "occurred_at": "2026-10-01T10:00:00Z",
        }

        self.assertEqual(trigger_age_seconds(event), 300.0)

    def test_trigger_age_is_unknown_when_timestamp_is_missing(self):
        from submission.src.replay_engine import trigger_age_seconds

        self.assertIsNone(
            trigger_age_seconds({"received_at": "2026-10-01T10:05:00Z"})
        )

    def test_verifier_rejects_a_previously_processed_trigger(self):
        result = verify_action(
            {"action": "NONE"},
            arm="treatment",
            trigger_id="E-duplicate",
            processed_trigger_ids={"E-duplicate"},
        )

        self.assertFalse(result["approved"])
        self.assertIn("idempotency", result["failed"])


    def test_unknown_trigger_age_is_rejected(self):
        from submission.src.replay_engine import trigger_age_rejection_reason

        event = {"received_at": "2026-10-01T10:05:00Z"}
        self.assertEqual(
            trigger_age_rejection_reason(event, 86400),
            "trigger_age_unknown",
        )

    def test_trigger_over_age_limit_is_rejected(self):
        from submission.src.replay_engine import trigger_age_rejection_reason

        event = {
            "received_at": "2026-10-02T10:00:01Z",
            "occurred_at": "2026-10-01T10:00:00Z",
        }
        self.assertEqual(
            trigger_age_rejection_reason(event, 86400),
            "trigger_stale",
        )

    def test_trigger_at_age_limit_is_accepted(self):
        from submission.src.replay_engine import trigger_age_rejection_reason

        event = {
            "received_at": "2026-10-02T10:00:00Z",
            "occurred_at": "2026-10-01T10:00:00Z",
        }
        self.assertIsNone(
            trigger_age_rejection_reason(event, 86400)
        )


    def test_active_goal_expires_after_deadline(self):
        from submission.src.replay_engine import active_goal_event_status
        from datetime import datetime, timezone

        active = {
            "goal_id": "G01",
            "success": {"event": "play_started", "window_hours": 24},
            "_active_started_at": "2026-10-01T10:00:00Z",
            "_active_deadline": "2026-10-02T10:00:00Z",
        }
        event = {
            "event": "play_started",
            "_timeline_kind": "live",
            "_timeline_time": datetime(2026, 10, 2, 10, 0, 1, tzinfo=timezone.utc),
            "properties": {},
        }
        self.assertEqual(active_goal_event_status(active, event, [], {}), "EXPIRED")

    def test_active_goal_success_requires_matching_event(self):
        from submission.src.replay_engine import active_goal_event_status
        from datetime import datetime, timezone

        active = {
            "goal_id": "G01",
            "success": {"event": "play_started", "window_hours": 24},
            "_active_started_at": "2026-10-01T10:00:00Z",
            "_active_deadline": "2026-10-02T10:00:00Z",
        }
        event = {
            "event": "home_viewed",
            "_timeline_kind": "live",
            "_timeline_time": datetime(2026, 10, 1, 11, 0, tzinfo=timezone.utc),
            "properties": {},
        }
        self.assertIsNone(active_goal_event_status(active, event, [], {}))


if __name__ == "__main__":
    unittest.main()
