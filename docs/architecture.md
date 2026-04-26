# Architecture

## Overview

The platform uses a Medallion architecture for GitHub event analytics. Raw hourly GHArchive files are converted into bronze Parquet partitions, cleaned into a silver event model, aggregated into gold dashboard tables, and served through a low-latency DuckDB cache behind a FastAPI service.

```text
GHArchive -> Prefect -> S3 Bronze -> Glue PySpark -> S3 Silver -> Glue PySpark -> S3 Gold -> Athena
                                                                                         |
                                                                                         v
                                                                                   DuckDB Cache
                                                                                         |
                                                                                         v
                                                                                      FastAPI
                                                                                         |
                                                                                         v
                                                                                    Dashboard
```

## Ingestion

The ingestion flow polls GHArchive for completed hourly files. Each file is downloaded, parsed, converted into Parquet, and uploaded to S3 with a success marker.

The success marker makes each partition idempotent. If a flow is retried, existing complete partitions are skipped.

## Storage

S3 stores all analytical data:

```text
raw/       Temporary source copies
bronze/    Normalized Parquet from GHArchive
silver/    Clean typed event records
gold/      Aggregates used by dashboards
duckdb/    Published dashboard cache files
```

## Transformation

Glue PySpark jobs handle distributed transformation:

1. `bronze_to_silver.py`
   - Parses timestamps.
   - Deduplicates by `event_id`.
   - Derives `event_day`, `event_hour_ts`, and `is_bot`.
   - Writes partitioned silver Parquet.

2. `silver_to_gold.py`
   - Builds event type counts.
   - Builds hourly and daily time series.
   - Builds top user, organization, and repository leaderboards.

## Warehouse

Athena queries the Glue Catalog tables directly from S3. It is used for validation, exploration, and backfills.

DuckDB is used as the serving cache for the API. The cache is built from gold Parquet files and atomically swapped into place so API readers never see a partial database.

## API

FastAPI exposes dashboard-ready JSON. It reads DuckDB in read-only mode and owns all SQL and time-window logic.

The frontend only knows API endpoints and presets. It does not know S3 paths, Glue tables, Athena SQL, or DuckDB internals.

## Deployment

The API runs as a Docker container on EC2. Nginx proxies public requests to the local container. Terraform provisions AWS resources and GitHub Actions builds and deploys the application.
