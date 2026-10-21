from __future__ import annotations

import json
import os
import time
import tempfile
from pathlib import Path
from typing import Any


class ViewerStateStore:
    """Atomic, file-backed storage for per-viewer replay state."""

    def __init__(self, directory: str | Path):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path(self, user_id: str) -> Path:
        safe_id = "".join(
            char for char in str(user_id)
            if char.isalnum() or char in "-_"
        )
        if not safe_id or safe_id != str(user_id):
            raise ValueError("Invalid user_id")
        return self.directory / f"{safe_id}.json"

    def get(self, user_id: str) -> dict[str, Any] | None:
        path = self._path(user_id)
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as file:
            value = json.load(file)
        if not isinstance(value, dict):
            raise ValueError(f"Invalid viewer state: {path}")
        return value

    def upsert(self, user_id: str, state: dict[str, Any]) -> None:
        path = self._path(user_id)
        payload = dict(state)
        payload["user_id"] = user_id

        fd, temporary_name = tempfile.mkstemp(
            prefix=f".{user_id}.",
            suffix=".tmp",
            dir=self.directory,
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as file:
                json.dump(payload, file, ensure_ascii=False, indent=2)
                file.write("\n")
                file.flush()
                os.fsync(file.fileno())
            for attempt in range(5):
                try:
                    os.replace(temporary_name, path)
                    break
                except PermissionError:
                    if attempt == 4:
                        raise
                    time.sleep(0.05 * (attempt + 1))
        except BaseException:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass
            raise

    def record_decision(
        self,
        user_id: str,
        decision: dict[str, Any],
    ) -> dict[str, Any]:
        state = self.get(user_id) or {
            "user_id": user_id,
            "decision_count": 0,
            "action_ids": [],
            "evidence_references": [],
            "processed_trigger_ids": [],
        }

        trigger_id = decision.get("trigger_event_id")
        processed = state["processed_trigger_ids"]

        if trigger_id and trigger_id in processed:
            return state

        state["decision_count"] += 1
        state["latest_decision_id"] = decision.get("decision_id")
        state["latest_trigger_event_id"] = trigger_id
        state["latest_trigger_type"] = decision.get("trigger_type")
        state["latest_reason"] = decision.get("reason")
        state["arm"] = decision.get("arm")
        state["active_goal"] = decision.get("goal") or decision.get("goal_id")

        if trigger_id:
            processed.append(trigger_id)

        for action_id in decision.get("action_ids", []):
            if action_id not in state["action_ids"]:
                state["action_ids"].append(action_id)

        evidence = decision.get("evidence_references", [])
        if not evidence:
            evidence = decision.get("evidence", [])
        for item in evidence:
            if item not in state["evidence_references"]:
                state["evidence_references"].append(item)

        self.upsert(user_id, state)
        return state
