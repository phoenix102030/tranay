from datetime import datetime, timezone


def to_naive_tz(dt: datetime) -> datetime:
    return dt.astimezone(timezone.utc).replace(tzinfo=None)
