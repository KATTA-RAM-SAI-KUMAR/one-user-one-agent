
"""Load and normalize STAGE events and viewer profiles."""

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def parse_timestamp(value):
    """Parse an ISO timestamp and normalize it to UTC."""
    if not value:
        return None

    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if result.tzinfo is None:
            result = result.replace(tzinfo=timezone.utc)
        return result.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def load_events(path):
    """Load JSONL events, deduplicate by event_id, and order by received_at."""
    events = []
    seen = set()
    duplicate_count = 0
    malformed_count = 0

    with Path(path).open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue

            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                malformed_count += 1
                continue

            event_id = event.get("event_id")

            if event_id is not None:
                if event_id in seen:
                    duplicate_count += 1
                    continue
                seen.add(event_id)

            event["_received_at_parsed"] = parse_timestamp(
                event.get("received_at")
            )
            events.append(event)

    events.sort(
        key=lambda event: (
            event["_received_at_parsed"] is None,
            event["_received_at_parsed"] or datetime.max.replace(
                tzinfo=timezone.utc
            ),
        )
    )

    return events, {
        "loaded_events": len(events),
        "duplicate_occurrences_skipped": duplicate_count,
        "malformed_lines_skipped": malformed_count,
    }


def load_profiles(path):
    """Load profile rows and retain duplicate-key conflicts."""
    profiles = {}
    conflicts = Counter()

    with Path(path).open("r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            user_id = row.get("user_id")
            if not user_id:
                continue

            if user_id in profiles:
                conflicts[user_id] += 1

            old = profiles.get(user_id)
            old_time = (
                parse_timestamp(old.get("updated_at")) if old else None
            )
            new_time = parse_timestamp(row.get("updated_at"))

            # Keep the row with the newest reliable updated_at.
            # Preserve the existing row if timestamps are tied or missing.
            if old is None or (
                new_time is not None
                and (old_time is None or new_time > old_time)
            ):
                profiles[user_id] = row

    return profiles, {
        "unique_profiles": len(profiles),
        "duplicate_profile_users": len(conflicts),
        "extra_duplicate_rows": sum(conflicts.values()),
    }


def resolve_viewer_facts(user_id, events, profiles):
    """Resolve basic viewer facts while retaining source conflicts."""
    profile = profiles.get(user_id, {})
    viewer_events = [
        event for event in events
        if event.get("user_id") == user_id
    ]

    facts = {}
    conflicts = []

    def record_fact(name, value, source, observed_at=None):
        facts[name] = {
            "value": value,
            "source": source,
            "observed_at": observed_at,
        }

    # Profile is a snapshot, not the final authority for all facts.
    if profile:
        for field in (
            "signup_at",
            "subscription_status",
            "plan_started_at",
            "plan_ends_at",
            "preferred_dialect",
            "preferred_language",
            "notifications_opt_in",
            "whatsapp_opt_in",
        ):
            if profile.get(field) not in (None, ""):
                record_fact(
                    field,
                    profile[field],
                    "profiles_snapshot.csv",
                    profile.get("updated_at"),
                )

    # Process server-received events in chronological order.
    for event in viewer_events:
        event_type = event.get("event_type")
        received_at = event.get("received_at")
        dialect = event.get("app_dialect")

        if dialect:
            previous = facts.get("app_dialect")
            if previous and previous["value"] != dialect:
                conflicts.append({
                    "fact": "app_dialect",
                    "previous": previous["value"],
                    "current": dialect,
                    "resolution": "latest received event",
                })
            record_fact("app_dialect", dialect, "event", received_at)

        if event_type == "signup_completed":
            record_fact("signup_completed", True, "event", received_at)

        elif event_type == "purchase_completed":
            record_fact(
                "subscription_status", "paid", "purchase_event", received_at
            )

        elif event_type == "subscription_renewed":
            record_fact(
                "subscription_status", "paid", "renewal_event", received_at
            )

        elif event_type == "subscription_lapsed":
            record_fact(
                "subscription_status", "lapsed", "lapse_event", received_at
            )

        elif event_type == "notification_opt_out":
            record_fact(
                "notifications_opt_in", False, "opt_out_event", received_at
            )

    return {
        "user_id": user_id,
        "facts": facts,
        "conflicts": conflicts,
        "event_count": len(viewer_events),
    }
