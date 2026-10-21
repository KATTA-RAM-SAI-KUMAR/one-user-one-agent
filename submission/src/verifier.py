
"""Independent safety checks for proposed STAGE actions."""

from datetime import time, timedelta, timezone


IST = timezone(timedelta(hours=5, minutes=30))

FORBIDDEN_PUSH_PHRASES = (
    "last chance",
    "hurry",
    "only today",
    "free forever",
    "guaranteed",
)


def verify_action(
    decision,
    *,
    arm,
    trigger_id,
    processed_trigger_ids,
    notifications_opt_in=False,
    whatsapp_opt_in=False,
    prior_message_date=None,
    now=None,
    available_title_ids=None,
    title_dialects=None,
    content_slugs=None,
):
    """Return independent verification results; reject unsafe actions."""
    passed = []
    failed = []

    def check(name, condition):
        (passed if condition else failed).append(name)

    action = str(decision.get("action", "NONE")).upper()
    now = now or decision.get("now")

    check("holdout_isolation", arm != "holdout")
    check(
        "idempotency",
        trigger_id not in processed_trigger_ids,
    )

    if action in {"NONE", "NO_ACTION"}:
        return {
            "approved": not failed,
            "passed": passed,
            "failed": failed,
            "reason": (
                "Safe abstention" if not failed
                else "Holdout or duplicate trigger"
            ),
        }

    if arm == "holdout":
        return {
            "approved": False,
            "passed": passed,
            "failed": failed,
            "reason": "Holdout viewers must receive zero actions",
        }

    if action in {"PUSH", "WHATSAPP"}:
        consent = (
            notifications_opt_in
            if action == "PUSH"
            else whatsapp_opt_in
        )
        check("channel_consent", consent)

        local_now = None
        if now is not None:
            if isinstance(now, str):
                from submission.src.event_loader import parse_timestamp
                now = parse_timestamp(now)
            if now is not None:
                local_now = now.astimezone(IST)

        if local_now is not None:
            current_time = local_now.time().replace(tzinfo=None)
            quiet = current_time >= time(22, 0) or current_time < time(8, 0)
            check("quiet_hours", not quiet)

            if prior_message_date is not None:
                check(
                    "daily_frequency_cap",
                    prior_message_date != local_now.date().isoformat(),
                )
        else:
            failed.append("missing_verifiable_publish_time")

    if action == "PUSH":
        title = decision.get("message_title", "")
        body = decision.get("message_body", "")
        combined = f"{title} {body}".casefold()

        check("push_title_length", len(title) <= 40)
        check("push_body_length", len(body) <= 120)
        check(
            "honest_push_copy",
            not any(phrase in combined for phrase in FORBIDDEN_PUSH_PHRASES),
        )

        deeplink = decision.get("deeplink", "")
        check(
            "push_deeplink",
            deeplink.startswith("ott://title/")
            and bool(deeplink.removeprefix("ott://title/")),
        )

    if action == "HOME_PAGE":
        content = decision.get("content", [])
        rows = decision.get("rows", [])
        check("home_page_has_titles", bool(content))
        check("home_page_row_limit", len(rows) <= 6)
        check("home_page_has_valid_row", bool(rows))
        check(
            "home_page_row_size",
            all(3 <= len(row.get("title_ids", [])) <= 10 for row in rows),
        )

        if content_slugs is not None:
            slugs = [content_slugs.get(title) for title in content]
            check(
                "unique_content_slug",
                all(slug for slug in slugs) and len(slugs) == len(set(slugs)),
            )

        if available_title_ids is not None:
            check(
                "title_availability",
                all(title in available_title_ids for title in content),
            )

        dialect = decision.get("dialect", {}).get("used")
        if title_dialects is not None:
            check(
                "title_dialect",
                all(title_dialects.get(title) == dialect for title in content),
            )

    supported_actions = {
        "HOME_PAGE", "PUSH", "WHATSAPP", "IN_APP", "NONE", "NO_ACTION"
    }
    check("supported_action", action in supported_actions)

    return {
        "approved": not failed,
        "passed": passed,
        "failed": failed,
        "reason": "All checks passed" if not failed else "Action rejected",
    }
