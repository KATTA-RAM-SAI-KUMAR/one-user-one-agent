"""Independent messaging-policy gate. All daily limits use IST."""
from datetime import datetime, time, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))
QUIET_START = time(22, 0)
QUIET_END = time(8, 0)


def _parse_datetime(value):
    if isinstance(value, datetime):
        dt = value
    elif value:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    else:
        raise ValueError("A timezone-aware decision time is required")

    if dt.tzinfo is None:
        raise ValueError("Decision timestamps must include a timezone")
    return dt


def verify_message_policy(
    *,
    channel,
    now,
    consent,
    prior_message_times=(),
    template_id=None,
    approved_template_ids=(),
    arm="agent",
):
    """Return a fail-closed decision; this function never sends a message."""
    failures = []
    checks = []

    channel = str(channel or "").upper()
    now_dt = _parse_datetime(now)
    local_now = now_dt.astimezone(IST)

    if channel not in {"PUSH", "WHATSAPP", "IN_APP"}:
        failures.append("unsupported_message_channel")
    else:
        checks.append("supported_message_channel")

    if arm != "agent":
        failures.append("holdout_message_blocked")
    else:
        checks.append("agent_arm")

    if consent is not True:
        failures.append("message_consent_missing_or_denied")
    else:
        checks.append("consent")

    local_time = local_now.time().replace(tzinfo=None)
    if local_time >= QUIET_START or local_time < QUIET_END:
        failures.append("quiet_hours_ist")
    else:
        checks.append("outside_quiet_hours_ist")

    if not template_id or template_id not in set(approved_template_ids):
        failures.append("template_not_approved")
    else:
        checks.append("approved_template")

    today = local_now.date()
    sent_today = False
    for sent in prior_message_times:
        try:
            sent_local = _parse_datetime(sent).astimezone(IST)
        except (TypeError, ValueError):
            failures.append("invalid_prior_message_timestamp")
            continue
        if sent_local.date() == today:
            sent_today = True

    if sent_today:
        failures.append("daily_message_cap")
    else:
        checks.append("daily_message_cap")

    return {
        "approved": not failures,
        "passed": checks,
        "failed": failures,
        "reason": "Message policy passed" if not failures else "Message blocked by policy",
        "checked_at": local_now.isoformat(),
        "timezone": "Asia/Kolkata",
    }
