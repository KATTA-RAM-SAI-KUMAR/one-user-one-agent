
"""Impact report with 95% confidence intervals for agent vs holdout."""

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


def wilson_interval(successes, total, z=1.96):
    """Calculate a two-sided 95% Wilson confidence interval for a rate."""
    if total <= 0:
        return None

    p = successes / total
    z2 = z * z
    denominator = 1 + z2 / total
    center = (p + z2 / (2 * total)) / denominator
    margin = (
        z
        * (p * (1 - p) / total + z2 / (4 * total * total)) ** 0.5
        / denominator
    )

    return [
        round(max(0.0, center - margin), 4),
        round(min(1.0, center + margin), 4),
    ]


def newcombe_difference_interval(
    a_successes, a_total, b_successes, b_total
):
    """Calculate a 95% Newcombe interval for rate A minus rate B."""
    if a_total <= 0 or b_total <= 0:
        return None

    a_rate = a_successes / a_total
    b_rate = b_successes / b_total

    a_ci = wilson_interval(a_successes, a_total)
    b_ci = wilson_interval(b_successes, b_total)

    low = a_rate - b_rate - (
        (a_rate - a_ci[0]) ** 2
        + (b_ci[1] - b_rate) ** 2
    ) ** 0.5

    high = a_rate - b_rate + (
        (a_ci[1] - a_rate) ** 2
        + (b_rate - b_ci[0]) ** 2
    ) ** 0.5

    return [
        round(max(-1.0, low), 4),
        round(min(1.0, high), 4),
    ]


def main():
    parser = argparse.ArgumentParser(
        description="Compare agent and holdout outcomes with confidence intervals."
    )
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
        row["user_id"]
        for row in triggers
        if row.get("user_id") in arms
    }

    decisions = read_jsonl(run / "decisions.jsonl")
    actions = read_jsonl(run / "actions.jsonl")
    outcomes = read_jsonl(run / "sim/outcome_events.jsonl")

    groups = {"agent": set(), "holdout": set()}

    for user in triggered_users:
        arm = arms[user]
        if arm in groups:
            groups[arm].add(user)

    action_users = {
        action["user_id"]
        for action in actions
        if action.get("user_id") in triggered_users
    }

    user_events = defaultdict(set)

    for event in outcomes:
        user = event.get("user_id")
        event_type = event.get("event")

        if user not in triggered_users:
            continue

        if event_type:
            user_events[user].add(event_type)

    report = {
        "scope": (
            "Preliminary event-level comparison; not goal success attribution"
        ),
        "seed": "oua-practice",
        "triggered_users": len(triggered_users),
        "decision_rows": len(decisions),
        "published_actions": len(actions),
        "users_receiving_actions": len(action_users),
        "arms": {},
    }

    metrics = (
        ("play_user_rate", "users_with_play_started", "play_started"),
        (
            "purchase_user_rate",
            "users_with_purchase_completed",
            "purchase_completed",
        ),
    )

    for arm, users in groups.items():
        denominator = len(users)

        arm_report = {
            "triggered_users": denominator,
            "users_receiving_actions": sum(
                user in action_users for user in users
            ),
        }

        for rate_key, count_key, event_name in metrics:
            successes = sum(
                event_name in user_events[user] for user in users
            )
            arm_report[count_key] = successes
            arm_report[rate_key] = (
                round(successes / denominator, 4)
                if denominator
                else None
            )

        report["arms"][arm] = arm_report

    agent = report["arms"]["agent"]
    holdout = report["arms"]["holdout"]

    report["descriptive_differences"] = {}
    report["confidence_intervals_95"] = {}

    for rate_key, count_key, _event_name in metrics:
        a = agent[rate_key]
        b = holdout[rate_key]
        a_count = agent[count_key]
        b_count = holdout[count_key]
        a_total = agent["triggered_users"]
        b_total = holdout["triggered_users"]

        difference = (
            round(a - b, 4)
            if a is not None and b is not None
            else None
        )

        difference_ci = newcombe_difference_interval(
            a_count, a_total, b_count, b_total
        )

        report["descriptive_differences"][rate_key] = difference
        report["confidence_intervals_95"][rate_key] = {
            "method": "Wilson score intervals; Newcombe difference interval",
            "confidence_level": 0.95,
            "agent_rate": wilson_interval(a_count, a_total),
            "holdout_rate": wilson_interval(b_count, b_total),
            "difference_agent_minus_holdout": difference_ci,
            "difference_excludes_zero": (
                difference_ci[0] > 0 or difference_ci[1] < 0
            ) if difference_ci else None,
            "interpretation": (
                "The 95% interval excludes zero."
                if difference_ci
                and (difference_ci[0] > 0 or difference_ci[1] < 0)
                else (
                    "The 95% interval includes zero; this analysis does "
                    "not show a clear difference between the rates."
                    if difference_ci
                    else "Insufficient data to calculate the interval."
                )
            ),
        }

    report["notes"] = [
        "Rates use unique triggered users as denominators.",
        "The outcomes are simulated and depend on the simulator seed.",
        "The difference is agent rate minus holdout rate.",
        "Confidence intervals quantify sampling uncertainty under the "
        "binary-outcome model; they do not correct bias or data-quality issues.",
        "These event-level metrics do not establish goal-specific success.",
        "Do not claim causal uplift without validating randomization, "
        "assignment integrity, outcome attribution, and holdout isolation.",
    ]

    output = run / "impact_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2))
    print(f"\nSaved: {output}")


if __name__ == "__main__":
    main()
