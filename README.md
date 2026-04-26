# GitHub Analytics Pipeline

Cloud-native GitHub event analytics platform built on AWS. The system ingests GHArchive hourly event data, stores it in a Medallion data lake, builds analytical aggregates with Glue and PySpark, exposes low-latency dashboard APIs with FastAPI and DuckDB, and serves a React dashboard through a public API endpoint.

## Architecture

```text
GHArchive
  -> Prefect ingestion
  -> S3 bronze Parquet
  -> Glue Data Catalog
  -> Glue PySpark silver and gold jobs
  -> Athena analytical warehouse
  -> DuckDB dashboard cache
  -> FastAPI Docker service
  -> Nginx and AWS Load Balancer
  -> React dashboard
```

## What This Repository Contains

```text
api/                  FastAPI application and Docker image
glue_jobs/            PySpark ETL jobs for silver and gold layers
ingestion/            Prefect flow for GHArchive ingestion
infra/                Terraform for AWS infrastructure
scripts/              Operational scripts for dashboard cache refresh
sql/                  Athena DDL and analytical views
docs/                 Architecture and deployment documentation
.github/workflows/    CI, Docker build, and Terraform workflows
tests/                Unit tests for API and transformation helpers
```

## AWS Services Used

- S3 for bronze, silver, and gold Parquet datasets
- AWS Glue Data Catalog for table metadata
- AWS Glue PySpark jobs for distributed transforms
- Athena for serverless warehouse queries
- EC2 for the API runtime
- ECR for Docker images
- Application Load Balancer for public API traffic
- CloudWatch for logs, metrics, and alarms
- IAM for least-privilege access
- Route 53 and ACM for DNS and TLS

## Data Layers

### Bronze

Raw GHArchive events normalized into partitioned Parquet:

```text
s3://<bucket>/bronze/gharchive/date=YYYY-MM-DD/hour=H/part-000.parquet
```

### Silver

Typed, deduplicated, queryable event model:

```text
s3://<bucket>/silver/events/event_day=YYYY-MM-DD/hour=H/
```

### Gold

Dashboard-ready aggregate tables:

```text
s3://<bucket>/gold/event_type_daily/
s3://<bucket>/gold/event_type_hourly/
s3://<bucket>/gold/push_user_daily/
s3://<bucket>/gold/pr_org_daily/
s3://<bucket>/gold/pr_repo_daily/
```

## API Endpoints

```text
GET /health
GET /api/gh/summary?preset=7d
GET /api/gh/event-types?preset=7d
GET /api/gh/event-types-daily?preset=7d
GET /api/gh/top-push-users?preset=7d&limit=10
GET /api/gh/top-pr-orgs?preset=7d&limit=10
GET /api/gh/top-pr-repos?preset=7d&limit=10
```

Supported presets:

```text
1h, 4h, 24h, 7d, 30d, max
```

## Local API Development

```bash
cd api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DASHBOARD_DB_PATH=../data/dashboard.duckdb
export FRONTEND_ORIGINS=http://localhost:5173
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Docker

```bash
docker build -t github-analytics-api ./api
docker run --rm -p 8000:8000 \
  -e DASHBOARD_DB_PATH=/data/dashboard.duckdb \
  -e FRONTEND_ORIGINS=https://<your_frontend_domain_here> \
  -v $(pwd)/data:/data \
  github-analytics-api
```

## Terraform Deployment

```bash
cd infra/envs/prod
terraform init
terraform plan \
  -var="aws_region=us-east-1" \
  -var="project_name=github-analytics" \
  -var="domain_name=api.<your_domain_here>"
terraform apply
```

## Pipeline Execution

Run ingestion locally:

```bash
cd ingestion
pip install -r requirements.txt
export AWS_REGION=us-east-1
export S3_BUCKET=<your_bucket_here>
prefect deploy --all
prefect worker start --pool github-analytics
```

Run Glue jobs:

```bash
aws glue start-job-run \
  --job-name github-analytics-bronze-to-silver \
  --arguments '{"--S3_BUCKET":"<your_bucket_here>","--PROCESS_DATE":"2026-04-26"}'

aws glue start-job-run \
  --job-name github-analytics-silver-to-gold \
  --arguments '{"--S3_BUCKET":"<your_bucket_here>","--PROCESS_DATE":"2026-04-26"}'
```

Refresh the DuckDB dashboard cache:

```bash
python scripts/build_dashboard_cache.py \
  --bucket <your_bucket_here> \
  --database-path /opt/github-analytics/data/dashboard.duckdb
```

## Documentation

- [Architecture](docs/architecture.md)
- [Deployment Guide](docs/deployment.md)
- [Data Quality](docs/data_quality.md)
- [Metrics Catalog](docs/metrics_catalog.md)
- [Operations Runbook](docs/operations.md)
