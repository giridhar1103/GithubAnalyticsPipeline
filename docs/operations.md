# Operations Runbook

## Check API Health

```bash
curl https://api.<your_domain_here>/health
```

## Check Latest Dashboard Data

```bash
duckdb /opt/github-analytics/data/dashboard.duckdb \
  "SELECT max(event_hour_ts) FROM event_type_hourly;"
```

## Restart API Container

```bash
docker restart github-analytics-api
```

## Refresh Dashboard Cache

```bash
python scripts/build_dashboard_cache.py \
  --bucket <your_bucket_here> \
  --database-path /opt/github-analytics/data/dashboard.duckdb \
  --region us-east-1
```

## Inspect Nginx

```bash
sudo nginx -t
sudo systemctl status nginx --no-pager
sudo tail -n 100 /var/log/nginx/error.log
```

## Inspect Glue Job

```bash
aws glue get-job-runs --job-name github-analytics-silver-to-gold
```

## Common Failures

### Dashboard Is Stale

1. Check bronze partition exists.
2. Check Glue silver job completed.
3. Check Glue gold job completed.
4. Run dashboard cache refresh.
5. Check API health.

### API Returns 500

1. Confirm `dashboard.duckdb` exists.
2. Confirm required tables exist.
3. Restart API container.
4. Check CloudWatch logs.

### Athena Shows No New Partitions

Run:

```sql
MSCK REPAIR TABLE github_analytics.bronze_gharchive_events;
MSCK REPAIR TABLE github_analytics.silver_events;
```
