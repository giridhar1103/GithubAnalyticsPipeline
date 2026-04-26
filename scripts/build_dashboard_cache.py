import argparse
import os
import shutil
from pathlib import Path

import duckdb


TABLES = [
    "event_type_daily",
    "event_type_hourly",
    "push_user_daily",
    "push_user_hourly",
    "pr_org_daily",
    "pr_org_hourly",
    "pr_repo_daily",
    "pr_repo_hourly",
]


def build_cache(bucket: str, database_path: str, region: str) -> None:
    target = Path(database_path)
    build = target.with_name("dashboard_build.duckdb")
    previous = target.with_name("dashboard_prev.duckdb")

    for path in [build, Path(f"{build}.wal")]:
        if path.exists():
            path.unlink()

    con = duckdb.connect(str(build))
    con.execute("INSTALL httpfs")
    con.execute("LOAD httpfs")
    con.execute(f"SET s3_region='{region}'")

    for table in TABLES:
        source = f"s3://{bucket}/gold/{table}/**/*.parquet"
        con.execute(
            f"""
            CREATE OR REPLACE TABLE {table} AS
            SELECT * FROM read_parquet('{source}', union_by_name=true)
            """
        )

    for table in TABLES:
        count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        if count == 0:
            raise RuntimeError(f"{table} is empty")

    con.execute("CHECKPOINT")
    con.close()

    if previous.exists():
        previous.unlink()
    if target.exists():
        shutil.move(str(target), str(previous))
    shutil.move(str(build), str(target))
    if previous.exists():
        previous.unlink()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--database-path", required=True)
    parser.add_argument("--region", default=os.getenv("AWS_REGION", "us-east-1"))
    args = parser.parse_args()
    build_cache(args.bucket, args.database_path, args.region)


if __name__ == "__main__":
    main()
