# Data Quality

Data quality checks run at bronze, silver, and gold layers.

## Bronze Checks

Each hourly partition must satisfy:

- Source file downloaded successfully
- Parquet file exists
- Success marker exists
- Row count is recorded
- Required columns exist
- Duplicate event IDs are counted

Failed bronze partitions are reprocessed on the next run.

## Silver Checks

Silver validates the normalized event model:

- `event_id` is not null
- `event_type` is not null
- `event_ts` is parsed
- Duplicate event IDs are removed
- `event_day` matches the partition date

Bad records can be written to:

```text
s3://<your_bucket_here>/quarantine/silver_bad_rows/
```

## Gold Checks

Gold validates dashboard aggregates:

- Counts are non-negative
- Aggregate tables are not empty
- Latest event hour is within freshness SLA
- Daily event totals reconcile with silver event counts

Example reconciliation:

```sql
SELECT COUNT(*) FROM github_analytics.silver_events
WHERE event_day = DATE '<process_date_here>';

SELECT SUM(event_count) FROM github_analytics.gold_event_type_daily
WHERE event_day = DATE '<process_date_here>';
```

The values should match when all event types are included.
