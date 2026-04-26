import os
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import boto3
import requests
from prefect import flow, get_run_logger, task

from bronze_writer import write_bronze_parquet

GHARCHIVE_BASE_URL = os.getenv("GHARCHIVE_BASE_URL", "https://data.gharchive.org")
S3_BUCKET = os.getenv("S3_BUCKET", "<your_bucket_here>")
BRONZE_PREFIX = os.getenv("BRONZE_PREFIX", "bronze/gharchive")
RAW_PREFIX = os.getenv("RAW_PREFIX", "raw/gharchive")
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "150"))


def hour_stamp(value: datetime) -> str:
    return f"{value.strftime('%Y-%m-%d')}-{value.hour}"


def s3_keys_for_stamp(stamp: str) -> dict[str, str]:
    date_part = "-".join(stamp.split("-")[:3])
    hour_part = stamp.split("-")[3]
    base = f"{BRONZE_PREFIX}/date={date_part}/hour={hour_part}"
    return {
        "raw": f"{RAW_PREFIX}/date={date_part}/hour={hour_part}/{stamp}.json.gz",
        "parquet": f"{base}/part-000.parquet",
        "success": f"{base}/_SUCCESS",
    }


def s3_client():
    return boto3.client("s3")


def object_exists(bucket: str, key: str) -> bool:
    try:
        s3_client().head_object(Bucket=bucket, Key=key)
        return True
    except Exception:
        return False


@task(retries=3, retry_delay_seconds=30)
def download_hour(stamp: str, target_dir: str) -> str:
    logger = get_run_logger()
    url = f"{GHARCHIVE_BASE_URL}/{stamp}.json.gz"
    output_path = os.path.join(target_dir, f"{stamp}.json.gz")

    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        with open(output_path, "wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)

    logger.info("downloaded %s", url)
    return output_path


@task
def convert_to_parquet(raw_path: str, target_dir: str) -> dict:
    stamp = Path(raw_path).name.replace(".json.gz", "")
    parquet_path = os.path.join(target_dir, f"{stamp}.parquet")
    return write_bronze_parquet(raw_path, parquet_path)


@task(retries=3, retry_delay_seconds=15)
def upload_partition(stamp: str, raw_path: str, parquet_path: str, rows_written: int) -> None:
    keys = s3_keys_for_stamp(stamp)
    client = s3_client()
    client.upload_file(raw_path, S3_BUCKET, keys["raw"])
    client.upload_file(parquet_path, S3_BUCKET, keys["parquet"])
    client.put_object(
        Bucket=S3_BUCKET,
        Key=keys["success"],
        Body=f"rows={rows_written}\ningested_at={datetime.now(timezone.utc).isoformat()}\n",
    )


@task
def wait_until_available(stamp: str, max_wait_seconds: int = 3600) -> bool:
    logger = get_run_logger()
    deadline = time.time() + max_wait_seconds
    url = f"{GHARCHIVE_BASE_URL}/{stamp}.json.gz"
    while time.time() < deadline:
        response = requests.head(url, timeout=20)
        if response.status_code == 200:
            return True
        logger.info("%s not available yet", url)
        time.sleep(60)
    return False


@flow(name="gharchive-bronze-ingestion")
def bronze_ingestion_flow(start_from: str | None = None, hours_back: int = 6):
    logger = get_run_logger()
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    latest_complete_hour = now - timedelta(hours=1)

    if start_from:
        current = datetime.fromisoformat(start_from).replace(tzinfo=timezone.utc)
    else:
        current = latest_complete_hour - timedelta(hours=hours_back - 1)

    min_allowed = latest_complete_hour - timedelta(days=RETENTION_DAYS)
    current = max(current, min_allowed)

    with tempfile.TemporaryDirectory() as temp_dir:
        while current <= latest_complete_hour:
            stamp = hour_stamp(current)
            keys = s3_keys_for_stamp(stamp)

            if object_exists(S3_BUCKET, keys["success"]):
                logger.info("partition already exists for %s", stamp)
                current += timedelta(hours=1)
                continue

            if not wait_until_available(stamp):
                logger.warning("source file unavailable for %s", stamp)
                current += timedelta(hours=1)
                continue

            raw_path = download_hour(stamp, temp_dir)
            stats = convert_to_parquet(raw_path, temp_dir)
            upload_partition(stamp, raw_path, stats["output_file"], int(stats["rows_written"]))
            logger.info("processed %s rows=%s", stamp, stats["rows_written"])
            current += timedelta(hours=1)


if __name__ == "__main__":
    bronze_ingestion_flow()
