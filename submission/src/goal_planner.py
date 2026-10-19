
"""Evidence-based, single-goal planner for STAGE."""

import json
from datetime import timedelta
from pathlib import Path

from src.event_loader import parse_timestamp


UNMEASURABLE_GOAL_IDS = {"G10"}


def load_goals(path):
    """Load goal rules without assuming a particular JSON layout."""
    with Path(path).open("r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for key in ("goals", "candidate_goals", "items"):
            if isinstance(data.get(key), list):
                return data[key]

    raise ValueError("Unrecognized goals.json structure")


def _goal_id(goal):
    return str(goal.get("id", goal.get("goal_id", "")))


def _success_event(goal):
    success = goal.get("success")
    if isinstance(success, dict):
        return success.get("event") or success.get("event_type")

    return (
        goal.get("success_event")
        or goal.get("success_event_type")
        or goal.get("success_signal")
    )


def _window_hours(goal):
    window = goal.get("window")
    if isinstance(window, dict):
        value = window.get("value")
        unit = str(window.get("unit", "days")).lower()

        if value is not None:
            multipliers = {
                "hour": 1, "hours": 1,
                "day": 24, "days": 24,
                "minute": 1 / 60, "minutes": 1 / 60,
            }
            if unit not in multipliers:
                return None
            return float(value) * multipliers[unit]

    for key in ("window_hours", "deadline_hours"):
        if goal.get(key) is not None:
            return float(goal[key])

    for key in ("window_days", "deadline_days"):
        if goal.get(key) is not None:
            return float(goal[key]) * 24

    return None


def plan_goal(goals, facts, evidence, started_at, active_goal=None):
    """
    Plan one goal only when eligibility is explicitly evidenced.

    `evidence` is a mapping from eligibility fact names to observed values.
    This function intentionally abstains when rule semantics are unknown.
    """
    if active_goal:
        return {
            "goal": active_goal,
            "reason": "Existing active goal retained",
        }

    start = parse_timestamp(started_at)
    if start is None:
        return {"goal": None, "reason": "Invalid or missing goal start time"}

    candidates = []

    for goal in goals:
        goal_id = _goal_id(goal)

        if not goal_id or goal_id in UNMEASURABLE_GOAL_IDS:
            continue

        success_event = _success_event(goal)
        hours = _window_hours(goal)

        if not success_event or hours is None or hours <= 0:
            continue

        # Require an explicit, pre-evaluated eligibility result.
        eligibility = evidence.get(goal_id)

        if not isinstance(eligibility, dict):
            continue

        if eligibility.get("eligible") is not True:
            continue

        references = eligibility.get("evidence", [])
        if not references:
            continue

        candidates.append({
            "id": goal_id,
            "deadline": (start + timedelta(hours=hours)).isoformat(),
            "success_event": success_event,
            "evidence": references,
            "assumptions": eligibility.get("assumptions", []),
            "rule_version": goal.get("version", "source"),
        })

    if not candidates:
        return {
            "goal": None,
            "reason": "No measurable goal has verified eligibility evidence",
        }

    # Deterministic choice: explicit priority, then goal ID.
    source_by_id = {_goal_id(g): g for g in goals}
    candidates.sort(
        key=lambda item: (
            -float(source_by_id[item["id"]].get("priority", 0)),
            item["id"],
        )
    )

    return {
        "goal": candidates[0],
        "reason": "Highest-priority measurable eligible goal",
    }
