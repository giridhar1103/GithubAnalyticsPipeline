from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import HTTPException

Preset = Literal["1h", "4h", "24h", "7d", "30d", "max"]


def normalize_ts(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def resolve_range_from_clock(preset: Preset) -> tuple[datetime | None, datetime]:
    end_ts = datetime.now(timezone.utc)
    if preset == "1h":
        return normalize_ts(end_ts - timedelta(hours=1)), normalize_ts(end_ts)
    if preset == "4h":
        return normalize_ts(end_ts - timedelta(hours=4)), normalize_ts(end_ts)
    if preset == "24h":
        return normalize_ts(end_ts - timedelta(hours=24)), normalize_ts(end_ts)
    if preset == "7d":
        return normalize_ts(end_ts - timedelta(days=7)), normalize_ts(end_ts)
    if preset == "30d":
        return normalize_ts(end_ts - timedelta(days=30)), normalize_ts(end_ts)
    if preset == "max":
        return None, normalize_ts(end_ts)
    raise HTTPException(status_code=400, detail=f"Unsupported preset: {preset}")


def resolve_short_range_from_data(con, preset: Preset) -> tuple[datetime, datetime]:
    row = con.execute("SELECT max(event_hour_ts) FROM event_type_hourly").fetchone()
    latest_hour = row[0] if row else None
    if latest_hour is None:
        raise HTTPException(status_code=503, detail="Hourly aggregates are not available.")

    end_ts = latest_hour + timedelta(hours=1)
    if preset == "1h":
        return end_ts - timedelta(hours=1), end_ts
    if preset == "4h":
        return end_ts - timedelta(hours=4), end_ts
    if preset == "24h":
        return end_ts - timedelta(hours=24), end_ts
    raise HTTPException(status_code=400, detail=f"Unsupported short preset: {preset}")


def is_short_preset(preset: Preset) -> bool:
    return preset in {"1h", "4h", "24h"}
