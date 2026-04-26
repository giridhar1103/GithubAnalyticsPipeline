import gzip
import json
import os
import re
from datetime import datetime, timezone
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

HOUR_RE = re.compile(r"(\d{4}-\d{2}-\d{2})-(\d{1,2})")

SCHEMA = pa.schema(
    [
        pa.field("event_id", pa.string()),
        pa.field("event_type", pa.string()),
        pa.field("created_at", pa.string()),
        pa.field("repo_id", pa.int64()),
        pa.field("repo_name", pa.string()),
        pa.field("repo_owner", pa.string()),
        pa.field("org_id", pa.int64()),
        pa.field("org_login", pa.string()),
        pa.field("actor_id", pa.int64()),
        pa.field("actor_login", pa.string()),
        pa.field("actor_type", pa.string()),
        pa.field("payload_size", pa.int64()),
        pa.field("payload_distinct_size", pa.int64()),
        pa.field("payload_ref", pa.string()),
        pa.field("payload_action", pa.string()),
        pa.field("pr_user_login", pa.string()),
        pa.field("watch_action", pa.string()),
        pa.field("repo_language", pa.string()),
        pa.field("repo_created_at", pa.string()),
        pa.field("ingest_ts", pa.string()),
        pa.field("source_file", pa.string()),
    ]
)


def safe_get(data: dict[str, Any], path: str, default=None):
    current = data
    for key in path.split("."):
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def to_int(value) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def repo_owner(repo_name: str | None) -> str | None:
    if not repo_name or "/" not in repo_name:
        return None
    return repo_name.split("/", 1)[0]


def parse_hour_from_filename(path: str) -> tuple[str, str]:
    match = HOUR_RE.search(os.path.basename(path))
    if not match:
        raise ValueError(f"Cannot parse GHArchive hour from {path}")
    return match.group(1), match.group(2)


def event_to_row(event: dict[str, Any], source_file: str, ingest_ts: str) -> dict[str, Any]:
    event_type = event.get("type")
    repo_name = safe_get(event, "repo.name")
    return {
        "event_id": event.get("id"),
        "event_type": event_type,
        "created_at": event.get("created_at"),
        "repo_id": to_int(safe_get(event, "repo.id")),
        "repo_name": repo_name,
        "repo_owner": repo_owner(repo_name) or safe_get(event, "repo.owner"),
        "org_id": to_int(safe_get(event, "org.id")),
        "org_login": safe_get(event, "org.login"),
        "actor_id": to_int(safe_get(event, "actor.id")),
        "actor_login": safe_get(event, "actor.login"),
        "actor_type": safe_get(event, "actor.type"),
        "payload_size": to_int(safe_get(event, "payload.size")),
        "payload_distinct_size": to_int(safe_get(event, "payload.distinct_size")),
        "payload_ref": safe_get(event, "payload.ref"),
        "payload_action": safe_get(event, "payload.action"),
        "pr_user_login": safe_get(event, "payload.pull_request.user.login"),
        "watch_action": safe_get(event, "payload.action") if event_type == "WatchEvent" else None,
        "repo_language": safe_get(event, "repo.language"),
        "repo_created_at": safe_get(event, "repo.created_at"),
        "ingest_ts": ingest_ts,
        "source_file": source_file,
    }


def iter_events(path: str):
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def write_bronze_parquet(input_file: str, output_file: str, batch_size: int = 5000) -> dict[str, int | str]:
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    ingest_ts = datetime.now(timezone.utc).isoformat()
    source_file = os.path.basename(input_file)

    seen = set()
    batch = []
    writer = None
    rows_written = 0
    duplicates = 0

    try:
        for event in iter_events(input_file):
            event_id = event.get("id")
            if event_id in seen:
                duplicates += 1
                continue
            if event_id:
                seen.add(event_id)

            batch.append(event_to_row(event, source_file, ingest_ts))
            if len(batch) >= batch_size:
                table = pa.Table.from_pylist(batch, schema=SCHEMA)
                if writer is None:
                    writer = pq.ParquetWriter(output_file, SCHEMA, compression="zstd")
                writer.write_table(table)
                rows_written += len(batch)
                batch.clear()

        if batch:
            table = pa.Table.from_pylist(batch, schema=SCHEMA)
            if writer is None:
                writer = pq.ParquetWriter(output_file, SCHEMA, compression="zstd")
            writer.write_table(table)
            rows_written += len(batch)
    finally:
        if writer is not None:
            writer.close()

    return {
        "output_file": output_file,
        "rows_written": rows_written,
        "duplicates": duplicates,
    }
