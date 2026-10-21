
import json
import tempfile
import unittest
from pathlib import Path

from submission.src.event_loader import load_events, parse_timestamp, resolve_viewer_facts


class EventLoaderTests(unittest.TestCase):

    def test_duplicate_events_are_skipped(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "events.jsonl"
            event = {
                "event_id": "E1",
                "user_id": "U1",
                "event_type": "app_open",
                "received_at": "2026-10-01T10:00:00Z",
            }
            path.write_text(
                json.dumps(event) + "\n" + json.dumps(event) + "\n",
                encoding="utf-8",
            )

            events, stats = load_events(path)

            self.assertEqual(len(events), 1)
            self.assertEqual(stats["duplicate_occurrences_skipped"], 1)

    def test_timestamps_normalize_to_utc(self):
        result = parse_timestamp("2026-10-01T15:30:00+05:30")
        self.assertEqual(result.isoformat(), "2026-10-01T10:00:00+00:00")

    def test_opt_out_overrides_profile_consent(self):
        profiles = {
            "U1": {
                "notifications_opt_in": "true",
                "preferred_dialect": "d1",
            }
        }
        events = [{
            "event_id": "E1",
            "user_id": "U1",
            "event_type": "notification_opt_out",
            "received_at": "2026-10-01T10:00:00Z",
        }]

        result = resolve_viewer_facts("U1", events, profiles)

        self.assertIs(
            result["facts"]["notifications_opt_in"]["value"], False
        )


    def test_latest_app_dialect_wins_and_conflict_is_recorded(self):
        profiles = {
            "U1": {"preferred_dialect": "English"}
        }
        events = [
            {
                "event_id": "E1",
                "user_id": "U1",
                "event_type": "app_open",
                "app_dialect": "Telugu",
                "received_at": "2026-10-01T10:00:00Z",
            },
            {
                "event_id": "E2",
                "user_id": "U1",
                "event_type": "app_open",
                "app_dialect": "Hindi",
                "received_at": "2026-10-01T11:00:00Z",
            },
        ]

        result = resolve_viewer_facts("U1", events, profiles)

        self.assertEqual(result["facts"]["app_dialect"]["value"], "Hindi")
        dialect_conflicts = [
            item for item in result["conflicts"]
            if item["fact"] == "app_dialect"
        ]
        self.assertEqual(len(dialect_conflicts), 1)
        self.assertEqual(dialect_conflicts[0]["previous"], "Telugu")
        self.assertEqual(dialect_conflicts[0]["current"], "Hindi")
        self.assertEqual(
            dialect_conflicts[0]["resolution"],
            "latest received event",
        )

    def test_app_dialect_is_separate_from_profile_preference(self):
        profiles = {
            "U1": {"preferred_dialect": "English"}
        }
        events = [{
            "event_id": "E1",
            "user_id": "U1",
            "event_type": "app_open",
            "app_dialect": "Telugu",
            "received_at": "2026-10-01T10:00:00Z",
        }]

        result = resolve_viewer_facts("U1", events, profiles)

        self.assertEqual(
            result["facts"]["preferred_dialect"]["value"], "English"
        )
        self.assertEqual(result["facts"]["app_dialect"]["value"], "Telugu")


if __name__ == "__main__":
    unittest.main()
