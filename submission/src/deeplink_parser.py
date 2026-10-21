import re
from urllib.parse import urlparse


DEEPLINK_PATTERN = re.compile(
    r"^/([^/]+)/([^/]+)/title/([^/]+)$"
)


def parse_campaign_deeplink(value):
    """Parse ott://c/<campaign>/<dialect>/title/<title_id> safely."""
    if not isinstance(value, str):
        return None

    parsed = urlparse(value.strip())
    if parsed.scheme != "ott" or parsed.netloc != "c":
        return None

    match = DEEPLINK_PATTERN.match(parsed.path)
    if not match:
        return None

    campaign_id, dialect, title_id = match.groups()
    if not campaign_id or not dialect or not title_id:
        return None

    return {
        "campaign_id": campaign_id,
        "dialect": dialect,
        "title_id": title_id,
    }
