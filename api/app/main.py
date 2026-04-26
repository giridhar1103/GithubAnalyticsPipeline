from collections import defaultdict
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.db import dashboard_connection
from app.models import (
    EventTypeRow,
    EventTypeSeriesResponse,
    EventTypeSeriesRow,
    EventTypesResponse,
    SummaryResponse,
    TopPROrgRow,
    TopPROrgsResponse,
    TopPRRepoRow,
    TopPRReposResponse,
    TopPushUserRow,
    TopPushUsersResponse,
)
from app.settings import get_settings
from app.time_filters import Preset, is_short_preset, resolve_range_from_clock, resolve_short_range_from_data

app = FastAPI(title="GitHub Analytics API", version="1.0.0")

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)


def resolve_range(con, preset: Preset) -> tuple[datetime | None, datetime]:
    if is_short_preset(preset):
        return resolve_short_range_from_data(con, preset)
    return resolve_range_from_clock(preset)


@app.get("/health")
def health_check():
    try:
        with dashboard_connection() as con:
            con.execute("SELECT 1").fetchone()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"database error: {exc}") from exc
    return {"status": "ok"}


@app.get("/api/gh/summary", response_model=SummaryResponse)
def summary(preset: Preset = Query(default="7d")):
    with dashboard_connection() as con:
        start_ts, end_ts = resolve_range(con, preset)
        if start_ts is None:
            row = con.execute("SELECT COALESCE(SUM(event_count), 0) FROM event_type_daily").fetchone()
        elif is_short_preset(preset):
            row = con.execute(
                """
                SELECT COALESCE(SUM(event_count), 0)
                FROM event_type_hourly
                WHERE event_hour_ts >= ? AND event_hour_ts < ?
                """,
                [start_ts, end_ts],
            ).fetchone()
        else:
            row = con.execute(
                """
                SELECT COALESCE(SUM(event_count), 0)
                FROM event_type_daily
                WHERE event_day >= ? AND event_day <= ?
                """,
                [start_ts.date(), end_ts.date()],
            ).fetchone()

    return SummaryResponse(
        preset=preset,
        start_ts=start_ts,
        end_ts=end_ts,
        total_events=int(row[0] or 0),
    )


@app.get("/api/gh/event-types", response_model=EventTypesResponse)
def event_types(preset: Preset = Query(default="7d")):
    with dashboard_connection() as con:
        start_ts, end_ts = resolve_range(con, preset)
        if start_ts is None:
            rows = con.execute(
                """
                SELECT event_type, SUM(event_count) AS event_count
                FROM event_type_daily
                GROUP BY event_type
                ORDER BY event_count DESC
                """
            ).fetchall()
        elif is_short_preset(preset):
            rows = con.execute(
                """
                SELECT event_type, SUM(event_count) AS event_count
                FROM event_type_hourly
                WHERE event_hour_ts >= ? AND event_hour_ts < ?
                GROUP BY event_type
                ORDER BY event_count DESC
                """,
                [start_ts, end_ts],
            ).fetchall()
        else:
            rows = con.execute(
                """
                SELECT event_type, SUM(event_count) AS event_count
                FROM event_type_daily
                WHERE event_day >= ? AND event_day <= ?
                GROUP BY event_type
                ORDER BY event_count DESC
                """,
                [start_ts.date(), end_ts.date()],
            ).fetchall()

    return EventTypesResponse(
        preset=preset,
        start_ts=start_ts,
        end_ts=end_ts,
        rows=[EventTypeRow(event_type=row[0], event_count=int(row[1])) for row in rows],
    )


@app.get("/api/gh/event-types-daily", response_model=EventTypeSeriesResponse)
def event_types_daily(preset: Preset = Query(default="7d")):
    with dashboard_connection() as con:
        start_ts, end_ts = resolve_range(con, preset)
        if is_short_preset(preset):
            rows = con.execute(
                """
                SELECT event_hour_ts, event_type, SUM(event_count) AS event_count
                FROM event_type_hourly
                WHERE event_hour_ts >= ? AND event_hour_ts < ?
                GROUP BY event_hour_ts, event_type
                ORDER BY event_hour_ts, event_count DESC
                """,
                [start_ts, end_ts],
            ).fetchall()
        elif start_ts is None:
            rows = con.execute(
                """
                SELECT event_day, event_type, SUM(event_count) AS event_count
                FROM event_type_daily
                GROUP BY event_day, event_type
                ORDER BY event_day, event_count DESC
                """
            ).fetchall()
        else:
            rows = con.execute(
                """
                SELECT event_day, event_type, SUM(event_count) AS event_count
                FROM event_type_daily
                WHERE event_day >= ? AND event_day <= ?
                GROUP BY event_day, event_type
                ORDER BY event_day, event_count DESC
                """,
                [start_ts.date(), end_ts.date()],
            ).fetchall()

    return EventTypeSeriesResponse(
        preset=preset,
        start_ts=start_ts,
        end_ts=end_ts,
        rows=[
            EventTypeSeriesRow(
                bucket=row[0].isoformat() if hasattr(row[0], "isoformat") else str(row[0]),
                event_type=row[1],
                event_count=int(row[2]),
            )
            for row in rows
        ],
    )


def ranked_rows(con, table: str, key_col: str, metric_col: str, preset: Preset, limit: int):
    start_ts, end_ts = resolve_range(con, preset)
    if start_ts is None:
        rows = con.execute(
            f"""
            SELECT {key_col}, SUM({metric_col}) AS metric
            FROM {table}_daily
            GROUP BY {key_col}
            ORDER BY metric DESC
            LIMIT ?
            """,
            [limit],
        ).fetchall()
    elif is_short_preset(preset):
        rows = con.execute(
            f"""
            SELECT {key_col}, SUM({metric_col}) AS metric
            FROM {table}_hourly
            WHERE event_hour_ts >= ? AND event_hour_ts < ?
            GROUP BY {key_col}
            ORDER BY metric DESC
            LIMIT ?
            """,
            [start_ts, end_ts, limit],
        ).fetchall()
    else:
        daily_rows = con.execute(
            f"""
            SELECT {key_col}, SUM({metric_col}) AS metric
            FROM {table}_daily
            WHERE event_day >= ? AND event_day <= ?
            GROUP BY {key_col}
            """,
            [start_ts.date(), end_ts.date()],
        ).fetchall()
        totals = defaultdict(int)
        for key, metric in daily_rows:
            totals[key] += int(metric or 0)
        rows = sorted(totals.items(), key=lambda item: item[1], reverse=True)[:limit]
    return start_ts, end_ts, rows


@app.get("/api/gh/top-push-users", response_model=TopPushUsersResponse)
def top_push_users(preset: Preset = Query(default="7d"), limit: int = Query(default=10, ge=1, le=50)):
    with dashboard_connection() as con:
        start_ts, end_ts, rows = ranked_rows(con, "push_user", "actor_login", "push_count", preset, limit)
    return TopPushUsersResponse(
        preset=preset,
        start_ts=start_ts,
        end_ts=end_ts,
        rows=[TopPushUserRow(actor_login=row[0], push_count=int(row[1])) for row in rows],
    )


@app.get("/api/gh/top-pr-orgs", response_model=TopPROrgsResponse)
def top_pr_orgs(preset: Preset = Query(default="7d"), limit: int = Query(default=10, ge=1, le=50)):
    with dashboard_connection() as con:
        start_ts, end_ts, rows = ranked_rows(con, "pr_org", "org_login", "pr_count", preset, limit)
    return TopPROrgsResponse(
        preset=preset,
        start_ts=start_ts,
        end_ts=end_ts,
        rows=[TopPROrgRow(org_login=row[0], pr_count=int(row[1])) for row in rows],
    )


@app.get("/api/gh/top-pr-repos", response_model=TopPRReposResponse)
def top_pr_repos(preset: Preset = Query(default="7d"), limit: int = Query(default=10, ge=1, le=50)):
    with dashboard_connection() as con:
        start_ts, end_ts, rows = ranked_rows(con, "pr_repo", "repo_name", "pr_count", preset, limit)
    return TopPRReposResponse(
        preset=preset,
        start_ts=start_ts,
        end_ts=end_ts,
        rows=[TopPRRepoRow(repo_name=row[0], pr_count=int(row[1])) for row in rows],
    )
