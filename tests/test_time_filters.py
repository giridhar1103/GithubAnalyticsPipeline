from datetime import datetime, timezone

from api.app.time_filters import normalize_ts


def test_normalize_ts_removes_timezone():
    value = datetime(2026, 4, 26, 12, 0, tzinfo=timezone.utc)
    normalized = normalize_ts(value)
    assert normalized.tzinfo is None
    assert normalized.hour == 12
