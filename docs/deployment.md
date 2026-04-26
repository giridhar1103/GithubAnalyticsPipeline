# Deployment Guide

## Prerequisites

- AWS account
- AWS CLI configured
- Terraform 1.6 or newer
- Docker
- Python 3.12
- Prefect account or local Prefect server
- Domain name for the API

## 1. Configure AWS

```bash
aws configure
```

Use an IAM user or role with permission to create:

```text
S3
IAM
Glue
EC2
CloudWatch
ECR
Security Groups
```

## 2. Create Infrastructure

```bash
cd infra/envs/prod
terraform init
terraform plan \
  -var="aws_region=us-east-1" \
  -var="project_name=github-analytics" \
  -var="api_image=<aws_account_id>.dkr.ecr.us-east-1.amazonaws.com/github-analytics-api:latest"
terraform apply
```

## 3. Upload Glue Job Scripts

```bash
aws s3 cp glue_jobs/bronze_to_silver.py s3://<your_bucket_here>/jobs/bronze_to_silver.py
aws s3 cp glue_jobs/silver_to_gold.py s3://<your_bucket_here>/jobs/silver_to_gold.py
```

## 4. Register Athena Tables

Open Athena and run:

```text
sql/athena_tables.sql
sql/gold_views.sql
```

Replace:

```text
<your_bucket_here>
```

with the data lake bucket name from Terraform output.

## 5. Deploy Prefect Ingestion

```bash
cd ingestion
pip install -r requirements.txt
export S3_BUCKET=<your_bucket_here>
prefect deploy --all
prefect worker start --pool github-analytics
```

## 6. Run Glue Jobs

```bash
aws glue start-job-run \
  --job-name github-analytics-bronze-to-silver \
  --arguments '{"--S3_BUCKET":"<your_bucket_here>","--PROCESS_DATE":"2026-04-26"}'

aws glue start-job-run \
  --job-name github-analytics-silver-to-gold \
  --arguments '{"--S3_BUCKET":"<your_bucket_here>","--PROCESS_DATE":"2026-04-26"}'
```

## 7. Build API Image

```bash
aws ecr create-repository --repository-name github-analytics-api
aws ecr get-login-password --region us-east-1 | docker login \
  --username AWS \
  --password-stdin <aws_account_id>.dkr.ecr.us-east-1.amazonaws.com

docker build -t github-analytics-api ./api
docker tag github-analytics-api:latest \
  <aws_account_id>.dkr.ecr.us-east-1.amazonaws.com/github-analytics-api:latest
docker push <aws_account_id>.dkr.ecr.us-east-1.amazonaws.com/github-analytics-api:latest
```

## 8. Refresh Dashboard Cache

On the API instance:

```bash
python scripts/build_dashboard_cache.py \
  --bucket <your_bucket_here> \
  --database-path /opt/github-analytics/data/dashboard.duckdb \
  --region us-east-1
```

## 9. Validate API

```bash
curl http://<ec2_public_dns>/health
curl http://<ec2_public_dns>/api/gh/summary?preset=7d
```

After DNS and TLS are configured:

```bash
curl https://api.<your_domain_here>/health
```

## 10. Frontend Environment

Set the frontend build variable:

```text
VITE_API_BASE=https://api.<your_domain_here>
```

The dashboard frontend calls the API directly from the browser.
