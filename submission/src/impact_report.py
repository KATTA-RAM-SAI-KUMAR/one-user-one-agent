
"""Preliminary randomized-arm outcome comparison."""

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def read_jsonl(path):
    with Path(path).open(encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pack", default="one_user_one_agent_pack")
    parser.add_argument("--run", default="sample_run")
    args = parser.parse_args()

    pack = Path(args.pack)
    run = Path(args.run)

    arms = {
        row["user_id"]: row["arm"]
        for row in read_csv(pack / "replay/arms.csv")
    }

    triggers = read_jsonl(pack / "replay/triggers.jsonl")
    triggered_users = {
        row["user_id"] for row in triggers
        if row.get("user_id") in arms
    }

    decisions = read_jsonl(run / "decisions.jsonl")
    actions = read_jsonl(run / "actions.jsonl")
    outcomes = read_jsonl(run / "sim/outcome_events.jsonl")

    groups = {
        "agent": set(),
        "holdout": set(),
    }

    for user in triggered_users:
        arm = arms[user]
        if arm in groups:
            groups[arm].add(user)

    action_users = {
        action["user_id"] for action in actions
        if action.get("user_id") in triggered_users
    }

    user_events = defaultdict(set)
    event_counts = defaultdict(int)

    for event in outcomes:
        user = event.get("user_id")
        event_type = event.get("event")

        if user not in triggered_users:
            continue

        event_counts[(arms[user], event_type)] += 1

        if event_type:
            user_events[user].add(event_type)

    report = {
        "scope": "Preliminary event-level comparison; not goal success attribution",
        "seed": "oua-practice",
        "triggered_users": len(triggered_users),
        "decision_rows": len(decisions),
        "published_actions": len(actions),
        "users_receiving_actions": len(action_users),
        "arms": {},
    }

    for arm, users in groups.items():
        denominator = len(users)
        played = sum(
            "play_started" in user_events[user] for user in users
        )
        purchased = sum(
            "purchase_completed" in user_events[user] for user in users
        )

        report["arms"][arm] = {
            "triggered_users": denominator,
            "users_with_play_started": played,
            "play_user_rate": round(played / denominator, 4)
            if denominator else None,
            "users_with_purchase_completed": purchased,
            "purchase_user_rate": round(purchased / denominator, 4)
            if denominator else None,
            "users_receiving_actions": sum(
                user in action_users for user in users
            ),
        }

    agent = report["arms"]["agent"]
    holdout = report["arms"]["holdout"]

    for metric in ("play_user_rate", "purchase_user_rate"):
        a = agent[metric]
        h = holdout[metric]
        report.setdefault("descriptive_differences", {})[metric] = (
            round(a - h, 4) if a is not None and h is not None else None
        )

    report["notes"] = [
        "Rates use unique triggered users as denominators.",
        "Outcome events are simulated and depend on the simulator seed.",
        "These metrics do not establish goal-specific success or causal uplift.",
        "Validate holdout isolation and goal attribution before final claims.",
    ]

    output = run / "impact_report.json"
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"\nSaved: {output}")


if __name__ == "__main__":
    main()
