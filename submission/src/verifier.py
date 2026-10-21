"""Independent safety checks for proposed STAGE actions."""

from datetime import datetime, time, timedelta, timezone

from .message_policy import verify_message_policy


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
    prior_message_times=(),
    approved_template_ids=(),
    now=None,
    available_title_ids=None,
    title_dialects=None,
    content_slugs=None,
):
    """Independently verify an action; reject unsafe or unverifiable messages."""
    passed = []
    failed = []

    def check(name, condition):
        (passed if condition else failed).append(name)

    action = str(decision.get("action", "NONE")).upper()
    # Fall back only when the caller omitted the argument; an explicit None
    # means the publish time is unavailable and message actions must fail closed.
    import inspect
    if "now" not in inspect.signature(verify_action).bind_partial(
        decision,
        arm=arm,
        trigger_id=trigger_id,
        processed_trigger_ids=processed_trigger_ids,
        notifications_opt_in=notifications_opt_in,
        whatsapp_opt_in=whatsapp_opt_in,
        prior_message_date=prior_message_date,
        now=now,
        available_title_ids=available_title_ids,
        title_dialects=title_dialects,
        content_slugs=content_slugs,
    ).arguments:
        now = decision.get("now")

    check("holdout_isolation", arm != "holdout")
    check("idempotency", trigger_id not in processed_trigger_ids)

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

    if action in {"PUSH", "WHATSAPP", "IN_APP"}:
        consent = (
            notifications_opt_in if action == "PUSH"
            else whatsapp_opt_in if action == "WHATSAPP"
            else decision.get("in_app_opt_in", False)
        )
        check("channel_consent", consent)

        parsed_now = None
        try:
            if isinstance(now, str):
                from .event_loader import parse_timestamp
                parsed_now = parse_timestamp(now)
            elif isinstance(now, datetime):
                parsed_now = now

            if parsed_now is None or parsed_now.tzinfo is None:
                raise ValueError("Missing timezone-aware publish time")

            history = list(prior_message_times or ())

            # Adapt the legacy local-date input for the shared policy check.
            if prior_message_date:
                previous_date = datetime.fromisoformat(
                    str(prior_message_date)
                ).date()
                history.append(
                    datetime.combine(
                        previous_date, time(12, 0), tzinfo=IST
                    )
                )

            policy = verify_message_policy(
                channel=action,
                now=parsed_now,
                consent=consent,
                prior_message_times=history,
                template_id=decision.get("template_id"),
                approved_template_ids=approved_template_ids,
                arm=arm,
            )

            passed.extend(
                f"message_policy:{name}" for name in policy["passed"]
            )
            failed.extend(
                f"message_policy:{name}" for name in policy["failed"]
            )

        except (TypeError, ValueError, OverflowError):
            failed.append("message_policy_unverifiable_publish_time")

    if action == "PUSH":
        title = decision.get("message_title", "")
        body = decision.get("message_body", "")
        combined = f"{title} {body}".casefold()

        check("push_title_length", len(title) <= 40)
        check("push_body_length", len(body) <= 120)
        check(
            "honest_push_copy",
            not any(
                phrase in combined
                for phrase in FORBIDDEN_PUSH_PHRASES
            ),
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
            all(
                3 <= len(row.get("title_ids", [])) <= 10
                for row in rows
            ),
        )

        if content_slugs is not None:
            slugs = [content_slugs.get(title) for title in content]
            check(
                "unique_content_slug",
                all(slug for slug in slugs)
                and len(slugs) == len(set(slugs)),
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
                all(
                    title_dialects.get(title) == dialect
                    for title in content
                ),
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

