from datetime import datetime

from pydantic import BaseModel


class SummaryResponse(BaseModel):
    preset: str
    start_ts: datetime | None
    end_ts: datetime
    total_events: int


class EventTypeRow(BaseModel):
    event_type: str
    event_count: int


class EventTypesResponse(BaseModel):
    preset: str
    start_ts: datetime | None
    end_ts: datetime
    rows: list[EventTypeRow]


class EventTypeSeriesRow(BaseModel):
    bucket: str
    event_type: str
    event_count: int


class EventTypeSeriesResponse(BaseModel):
    preset: str
    start_ts: datetime | None
    end_ts: datetime
    rows: list[EventTypeSeriesRow]


class TopPushUserRow(BaseModel):
    actor_login: str
    push_count: int


class TopPushUsersResponse(BaseModel):
    preset: str
    start_ts: datetime | None
    end_ts: datetime
    rows: list[TopPushUserRow]


class TopPROrgRow(BaseModel):
    org_login: str
    pr_count: int


class TopPROrgsResponse(BaseModel):
    preset: str
    start_ts: datetime | None
    end_ts: datetime
    rows: list[TopPROrgRow]


class TopPRRepoRow(BaseModel):
    repo_name: str
    pr_count: int


class TopPRReposResponse(BaseModel):
    preset: str
    start_ts: datetime | None
    end_ts: datetime
    rows: list[TopPRRepoRow]
