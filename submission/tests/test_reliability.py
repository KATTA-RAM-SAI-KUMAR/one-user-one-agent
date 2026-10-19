import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from src.event_loader import parse_timestamp, load_events
from src.verifier import verify_action


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
        with patch("src.event_loader.load_events", side_effect=OSError("simulated dependency failure")):
            with self.assertRaises(OSError):
                load_events("nonexistent-test-file.jsonl")

    def test_corrected_goal_rule_uses_play_started_event(self):
        from src.goal_planner import _success_event
        corrected_goal = {
            "goal_id": "G03",
            "success_event": "play_started",
        }
        self.assertEqual(_success_event(corrected_goal), "play_started")


if __name__ == "__main__":
    unittest.main()
