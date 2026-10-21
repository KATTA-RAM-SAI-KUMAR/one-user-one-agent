import tempfile
import unittest
from pathlib import Path

from submission.src.state_store import ViewerStateStore


class ViewerStateStoreTests(unittest.TestCase):
    def test_state_persists_between_store_instances(self):
        with tempfile.TemporaryDirectory() as directory:
            first = ViewerStateStore(directory)
            first.upsert("U-001", {"decision_count": 1, "arm": "agent"})

            second = ViewerStateStore(directory)
            state = second.get("U-001")

            self.assertEqual(state["decision_count"], 1)
            self.assertEqual(state["arm"], "agent")
            self.assertEqual(state["user_id"], "U-001")

    def test_duplicate_trigger_is_not_counted_twice(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ViewerStateStore(directory)
            decision = {
                "decision_id": "D-001",
                "trigger_event_id": "E-001",
                "trigger_type": "play_started",
                "reason": "test",
                "arm": "agent",
                "goal_id": "G01",
                "action_ids": ["A-001"],
            }

            store.record_decision("U-001", decision)
            store.record_decision("U-001", decision)
            state = store.get("U-001")

            self.assertEqual(state["decision_count"], 1)
            self.assertEqual(state["action_ids"], ["A-001"])
            self.assertEqual(state["processed_trigger_ids"], ["E-001"])

    def test_invalid_user_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ViewerStateStore(directory)
            with self.assertRaises(ValueError):
                store.upsert("../outside", {"decision_count": 1})




    def test_selected_goal_is_persisted(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ViewerStateStore(directory)
            decision = {
                "decision_id": "D-1",
                "trigger_event_id": "E-1",
                "trigger_type": "app_open",
                "goal": "G03",
                "reason": "Eligible measurable goal",
                "arm": "agent",
                "action_ids": [],
                "evidence": ["measurable_success_event:play_started"],
            }

            state = store.record_decision("USER-1", decision)

            self.assertEqual(state["active_goal"], "G03")
            self.assertEqual(store.get("USER-1")["active_goal"], "G03")


if __name__ == "__main__":
    unittest.main()
