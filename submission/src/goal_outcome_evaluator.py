
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


UTC = timezone.utc
IST = timezone(timedelta(hours=5, minutes=30))

CORRECTED_GOALS = {
    "G03": {
        "event": "play_started",
        "condition": "on a later IST calendar day than the goal start",
    }
}

EXCLUDED_GOALS = {
    "G10": "The assignment defines no measurable success event."
}


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []

    if not path.exists():
        return records

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON at {path}:{line_number}: {exc}"
                ) from exc

            if isinstance(record, dict):
                records.append(record)

    return records


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def parse_time(value: Any) -> datetime | None:
    if not value:
        return None

    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    except (ValueError, TypeError):
        return None


def iso(value: datetime | None) -> str | None:
    if value is None:
        return None

    return value.astimezone(UTC).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )


def event_time(event: dict[str, Any]) -> datetime | None:
    # Use server receive time as the trusted timestamp.
    return (
        parse_time(event.get("received_at"))
        or parse_time(event.get("deliver_at"))
        or parse_time(event.get("at"))
    )


def load_goals(path: Path) -> dict[str, dict[str, Any]]:
    raw = read_json(path)
    goals = raw if isinstance(raw, list) else raw.get("goals", [])

    return {
        str(goal.get("goal_id") or goal.get("id")): goal
        for goal in goals
        if isinstance(goal, dict)
        and (goal.get("goal_id") or goal.get("id"))
    }


def load_catalogue(path: Path) -> dict[str, dict[str, Any]]:
    result = {}

    for row in read_csv(path):
        title_id = row.get("title_id", "").strip()
        if title_id:
            result[title_id] = row

    return result


def load_profiles(path: Path) -> dict[str, dict[str, str]]:
    """
    Resolve duplicate profile rows deterministically:
    newest updated_at, then snapshot_at.
    """
    selected = {}

    for row in read_csv(path):
        user_id = row.get("user_id", "").strip()
        if not user_id:
            continue

        current = selected.get(user_id)

        row_time = (
            parse_time(row.get("updated_at"))
            or parse_time(row.get("snapshot_at"))
            or datetime.min.replace(tzinfo=UTC)
        )

        current_time = (
            parse_time(current.get("updated_at"))
            or parse_time(current.get("snapshot_at"))
            or datetime.min.replace(tzinfo=UTC)
            if current
            else datetime.min.replace(tzinfo=UTC)
        )

        if current is None or row_time >= current_time:
            selected[user_id] = row

    return selected


def load_arms(path: Path) -> dict[str, str]:
    result = {}

    for row in read_csv(path):
        user_id = row.get("user_id", "").strip()
        arm = (
            row.get("arm")
            or row.get("assigned_arm")
            or row.get("experiment_arm")
            or ""
        ).strip().lower()

        if user_id and arm:
            result[user_id] = arm

    return result


def load_events(*paths: Path) -> list[dict[str, Any]]:
    """
    Load event files and deduplicate events by event_id.
    Records without event IDs are retained because they cannot be
    safely deduplicated using an identifier.
    """
    events = []
    seen_ids = set()

    for path in paths:
        for event in read_jsonl(path):
            event_id = event.get("event_id")

            if event_id:
                event_id = str(event_id)
                if event_id in seen_ids:
                    continue
                seen_ids.add(event_id)

            moment = event_time(event)
            if moment is None:
                continue

            event["_evaluation_time"] = moment
            events.append(event)

    events.sort(key=lambda e: (e["_evaluation_time"], str(e.get("event_id", ""))))
    return events


def get_properties(event: dict[str, Any]) -> dict[str, Any]:
    value = event.get("properties")
    return value if isinstance(value, dict) else {}


def goal_window_hours(goal: dict[str, Any]) -> float | None:
    success = goal.get("success") or {}

    if not isinstance(success, dict):
        return None

    hours = success.get("window_hours")
    if hours is not None:
        try:
            return float(hours)
        except (TypeError, ValueError):
            return None

    days = success.get("window_days")
    if days is not None:
        try:
            return float(days) * 24
        except (TypeError, ValueError):
            return None

    return None


def success_rule(
    goal_id: str,
    goal: dict[str, Any],
) -> tuple[str | None, str]:
    """
    Return the effective event and condition.

    G03 is corrected according to the supplied replay control event:
    an app open alone does not count as returning.
    """
    if goal_id in CORRECTED_GOALS:
        corrected = CORRECTED_GOALS[goal_id]
        return corrected["event"], corrected["condition"]

    success = goal.get("success") or {}
    if not isinstance(success, dict):
        return None, "invalid_success_rule"

    event_name = success.get("event")
    condition = str(success.get("condition") or "any")

    if not event_name:
        return None, condition

    return str(event_name), condition


def title_content_slug(
    event: dict[str, Any],
    catalogue: dict[str, dict[str, Any]],
) -> str | None:
    properties = get_properties(event)
    title_id = str(properties.get("title_id") or "")

    title = catalogue.get(title_id)
    if title:
        slug = title.get("content_slug")
        return str(slug) if slug else None

    # Some event sources may carry the slug directly.
    slug = properties.get("content_slug")
    return str(slug) if slug else None


def event_matches_goal(
    goal_id: str,
    goal: dict[str, Any],
    event: dict[str, Any],
    start: datetime,
    catalogue: dict[str, dict[str, Any]],
) -> bool:
    expected_event, condition = success_rule(goal_id, goal)

    if expected_event is None:
        return False

    if event.get("event") != expected_event:
        return False

    properties = get_properties(event)
    condition_lower = condition.lower()

    # A paid conversion must not count a free trial purchase.
    if goal_id in {"G04", "G05", "G06"}:
        if str(properties.get("is_trial", "")).lower() == "true":
            return False

    # G03: success must occur on a later IST calendar day.
    if goal_id == "G03":
        moment = event["_evaluation_time"]
        if moment.astimezone(IST).date() <= start.astimezone(IST).date():
            return False

    # G08: the play must be for a title released within 30 days
    # before the goal began.
    if goal_id == "G08":
        title_id = str(properties.get("title_id") or "")
        title = catalogue.get(title_id)

        if not title:
            return False

        release_date = parse_time(title.get("release_date"))
        if release_date is None:
            try:
                raw_date = str(title.get("release_date") or "")
                if raw_date:
                    release_date = datetime.fromisoformat(raw_date).replace(
                        tzinfo=UTC
                    )
            except ValueError:
                return False

        if release_date is None:
            return False

        age = start - release_date
        if age < timedelta(0) or age > timedelta(days=30):
            return False

    # G07: require the same series slug as the series started before
    # the goal. If that prior series cannot be established, do not claim success.
    if goal_id == "G07":
        current_slug = title_content_slug(event, catalogue)
        if not current_slug:
            return False

        # Prior matching-series evidence is added by the evaluator below
        # through the optional target_content_slug field.
        target_slug = goal.get("_target_content_slug")
        if not target_slug or current_slug != target_slug:
            return False

    # G09: three distinct IST play days are evaluated across all events
    # by the aggregate evaluator, not by one event in isolation.
    if goal_id == "G09":
        return False

    # G11: tv_app_open is not among the listed sample event types.
    # Only an actual event with that name can qualify.
    if goal_id == "G11":
        return True

    # G12 and ordinary event goals use the configured success event.
    if condition_lower in {"any", "any title", "any episode", "any paid plan"}:
        return True

    if goal_id in {"G04", "G05", "G06"}:
        return True

    return True


def find_g07_target(
    user_id: str,
    start: datetime,
    historical_events: list[dict[str, Any]],
    catalogue: dict[str, dict[str, Any]],
) -> str | None:
    """
    Conservative approximation: identify the most recent series played
    before the goal start. Full unfinished-episode state requires episode
    progress and episode catalogue analysis, so this does not claim that
    eligibility has been proven.
    """
    prior = [
        event
        for event in historical_events
        if event.get("user_id") == user_id
        and event.get("event") == "play_started"
        and event["_evaluation_time"] < start
    ]

    prior.sort(key=lambda e: e["_evaluation_time"], reverse=True)

    for event in prior:
        slug = title_content_slug(event, catalogue)
        if slug:
            return slug

    return None


def evaluate_assignment(
    assignment: dict[str, Any],
    goal: dict[str, Any],
    user_events: list[dict[str, Any]],
    catalogue: dict[str, dict[str, Any]],
    observed_until: datetime,
) -> dict[str, Any]:
    user_id = str(assignment["user_id"])
    assigned_goal_id = str(assignment["goal_id"])
    start = assignment["goal_started_at"]
    hours = goal_window_hours(goal)

    base = {
        "user_id": user_id,
        "arm": assignment["arm"],
        "goal_id": assigned_goal_id,
        "goal_name": goal.get("name"),
        "goal_started_at": iso(start),
        "action_ids": assignment.get("action_ids", []),
        "evidence_event_ids": [],
        "success_event": None,
        "success_at": None,
        "deadline": None,
        "status": "INCONCLUSIVE",
        "reason": "",
    }

    if assigned_goal_id in EXCLUDED_GOALS:
        base["reason"] = EXCLUDED_GOALS[assigned_goal_id]
        return base

    if hours is None or hours <= 0:
        base["reason"] = "No valid success window is configured."
        return base

    deadline = start + timedelta(hours=hours)
    base["deadline"] = iso(deadline)

    expected_event, condition = success_rule(assigned_goal_id, goal)

    if expected_event is None:
        base["reason"] = "No measurable success event is configured."
        return base

    if assigned_goal_id == "G07":
        goal["_target_content_slug"] = find_g07_target(
            user_id,
            start,
            user_events,
            catalogue,
        )

        if not goal["_target_content_slug"]:
            base["reason"] = (
                "Cannot establish a prior series slug; success not attributed."
            )
            return base

    # Use events in the actual goal window, never events before the goal start
    # or after its deadline. Server receive time is used consistently.
    candidates = [
        event
        for event in user_events
        if event.get("user_id") == user_id
        and start <= event["_evaluation_time"] <= deadline
    ]

    candidates.sort(key=lambda e: e["_evaluation_time"])

    # G09 requires play_started on three distinct IST calendar days.
    if assigned_goal_id == "G09":
        qualifying = [
            event
            for event in candidates
            if event.get("event") == "play_started"
        ]
        distinct_days = {
            event["_evaluation_time"].astimezone(IST).date().isoformat()
            for event in qualifying
        }

        if len(distinct_days) >= 3:
            chosen = qualifying[-1]
            base["status"] = "SUCCEEDED"
            base["success_event"] = "play_started_on_3_distinct_IST_days"
            base["success_at"] = iso(chosen["_evaluation_time"])
            base["evidence_event_ids"] = [
                str(event.get("event_id"))
                for event in qualifying
                if event.get("event_id")
            ]
            base["reason"] = (
                f"Observed play_started on {len(distinct_days)} distinct "
                "IST calendar days within the goal window."
            )
            return base

    # G03 uses the corrected success rule, and G08/G07 have specific
    # conditions enforced by event_matches_goal.
    for event in candidates:
        if event_matches_goal(
            assigned_goal_id,
            goal,
            event,
            start,
            catalogue,
        ):
            base["status"] = "SUCCEEDED"
            base["success_event"] = event.get("event")
            base["success_at"] = iso(event["_evaluation_time"])
            base["evidence_event_ids"] = (
                [str(event["event_id"])] if event.get("event_id") else []
            )
            base["reason"] = (
                f"Observed {expected_event} within the configured goal window; "
                f"condition: {condition}."
            )
            return base

    if observed_until >= deadline:
        base["status"] = "FAILED"
        base["reason"] = (
            f"No qualifying {expected_event} was observed by the deadline."
        )
    else:
        base["status"] = "INCONCLUSIVE"
        base["reason"] = (
            "The observation period ended before the goal deadline."
        )

    return base


def build_assignments(
    decisions: list[dict[str, Any]],
    actions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Use the first measurable goal assignment per user and arm.
    Repeated triggers must not silently restart a goal's deadline.
    """
    actions_by_decision: dict[str, list[str]] = defaultdict(list)

    for action in actions:
        decision_id = str(action.get("decision_id", ""))
        action_id = action.get("action_id")

        if decision_id and action_id:
            actions_by_decision[decision_id].append(str(action_id))

    assignments = []
    seen = set()

    for decision in sorted(
        decisions,
        key=lambda d: (
            parse_time(d.get("deliver_at"))
            or datetime.min.replace(tzinfo=UTC),
            str(d.get("decision_id", "")),
        ),
    ):
        user_id = str(decision.get("user_id", "")).strip()
        arm = str(decision.get("arm", "")).lower()
        goal_value = decision.get("goal")

        if not user_id or arm not in {"agent", "holdout"} or not goal_value:
            continue

        if isinstance(goal_value, dict):
            assigned_goal_id = str(
                goal_value.get("goal_id") or goal_value.get("id") or ""
            )
        else:
            assigned_goal_id = str(goal_value)

        start = parse_time(decision.get("deliver_at"))
        if not assigned_goal_id or start is None:
            continue

        key = (user_id, arm)
        if key in seen:
            continue

        seen.add(key)

        assignments.append(
            {
                "user_id": user_id,
                "arm": arm,
                "goal_id": assigned_goal_id,
                "goal_started_at": start,
                "action_ids": actions_by_decision.get(
                    str(decision.get("decision_id", "")), []
                ),
                "decision_id": decision.get("decision_id"),
            }
        )

    return assignments


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Attribute goal success using configured events and deadlines."
    )
    parser.add_argument(
        "--pack",
        default="one_user_one_agent_pack",
        help="Path to the assignment data pack.",
    )
    parser.add_argument(
        "--run",
        default="sample_run",
        help="Replay output directory.",
    )
    args = parser.parse_args()

    pack = Path(args.pack)
    run_dir = Path(args.run)

    decisions_path = run_dir / "decisions.jsonl"
    actions_path = run_dir / "actions.jsonl"
    simulated_events_path = run_dir / "sim" / "outcome_events.jsonl"

    for required in (
        pack / "config" / "goals.json",
        pack / "data" / "events.jsonl",
        pack / "data" / "catalogue.csv",
        decisions_path,
        actions_path,
        simulated_events_path,
    ):
        if not required.exists():
            raise SystemExit(f"Required file not found: {required}")

    goals = load_goals(pack / "config" / "goals.json")
    catalogue = load_catalogue(pack / "data" / "catalogue.csv")
    profiles = load_profiles(pack / "data" / "profiles_snapshot.csv")
    arms = load_arms(pack / "replay" / "arms.csv")

    decisions = read_jsonl(decisions_path)
    actions = read_jsonl(actions_path)

    events = load_events(
        pack / "data" / "events.jsonl",
        simulated_events_path,
    )

    # The assignment's replay may contain additional live events that arrived
    # during the decision stream.
    live_path = pack / "replay" / "live_events.jsonl"
    if live_path.exists():
        events = load_events(
            pack / "data" / "events.jsonl",
            live_path,
            simulated_events_path,
        )

    observed_until = max(
        (event["_evaluation_time"] for event in events),
        default=datetime.min.replace(tzinfo=UTC),
    )

    events_by_user: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        user_id = str(event.get("user_id", "")).strip()
        if user_id:
            events_by_user[user_id].append(event)

    assignments = build_assignments(decisions, actions)
    judgments = []

    for assignment in assignments:
        assigned_goal_id = assignment["goal_id"]

        if assigned_goal_id not in goals:
            judgments.append(
                {
                    "user_id": assignment["user_id"],
                    "arm": assignment["arm"],
                    "goal_id": assigned_goal_id,
                    "goal_started_at": iso(assignment["goal_started_at"]),
                    "status": "INCONCLUSIVE",
                    "reason": "Assigned goal ID is missing from goals.json.",
                    "evidence_event_ids": [],
                }
            )
            continue

        goal_copy = dict(goals[assigned_goal_id])

        judgments.append(
            evaluate_assignment(
                assignment=assignment,
                goal=goal_copy,
                user_events=events_by_user.get(assignment["user_id"], []),
                catalogue=catalogue,
                observed_until=observed_until,
            )
        )

    status_counts = Counter(row.get("status", "INCONCLUSIVE") for row in judgments)
    arm_counts: dict[str, dict[str, int]] = {}

    for arm in ("agent", "holdout"):
        rows = [row for row in judgments if row.get("arm") == arm]
        counts = Counter(row.get("status", "INCONCLUSIVE") for row in rows)

        arm_counts[arm] = {
            "assigned_goals": len(rows),
            "succeeded": counts.get("SUCCEEDED", 0),
            "failed": counts.get("FAILED", 0),
            "inconclusive": counts.get("INCONCLUSIVE", 0),
            "success_rate_among_all_assignments": round(
                counts.get("SUCCEEDED", 0) / len(rows), 4
            ) if rows else 0.0,
            "success_rate_among_judged": round(
                counts.get("SUCCEEDED", 0)
                / (counts.get("SUCCEEDED", 0) + counts.get("FAILED", 0)),
                4,
            ) if counts.get("SUCCEEDED", 0) + counts.get("FAILED", 0) else None,
        }

    report = {
        "report_type": "goal_specific_outcome_attribution",
        "goal_assignments_evaluated": len(judgments),
        "overall_status_counts": dict(status_counts),
        "arms": arm_counts,
        "excluded_goal_rules": EXCLUDED_GOALS,
        "corrections_applied": CORRECTED_GOALS,
        "methodology": [
            "First goal assignment per user and experiment arm is evaluated.",
            "The deadline starts at the assigned decision's deliver_at timestamp.",
            "Server received timestamps are used for event attribution.",
            "Events outside the goal window are not counted as success.",
            "G03 uses the corrected play_started event and a later IST calendar day.",
            "G09 requires plays on three distinct IST calendar days.",
            "G10 is excluded because it has no measurable success event.",
            "An expired goal without a qualifying event is FAILED.",
            "A goal whose deadline has not passed is INCONCLUSIVE if no success is observed.",
            "This is descriptive goal attribution, not proof that the intervention caused success.",
        ],
        "data_coverage": {
            "profile_rows_resolved": len(profiles),
            "experiment_arms_loaded": len(arms),
            "events_loaded_after_deduplication": len(events),
            "catalogue_titles_loaded": len(catalogue),
            "observed_until": iso(observed_until),
        },
    }

    run_dir.mkdir(parents=True, exist_ok=True)

    with (run_dir / "outcomes.jsonl").open("w", encoding="utf-8") as file:
        for judgment in judgments:
            file.write(json.dumps(judgment, ensure_ascii=False) + "\n")

    (run_dir / "goal_outcome_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nSaved: {run_dir / 'outcomes.jsonl'}")
    print(f"Saved: {run_dir / 'goal_outcome_report.json'}")


if __name__ == "__main__":
    main()
