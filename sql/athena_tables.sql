CREATE DATABASE IF NOT EXISTS github_analytics;

CREATE EXTERNAL TABLE IF NOT EXISTS github_analytics.bronze_gharchive_events (
  event_id string,
  event_type string,
  created_at string,
  repo_id bigint,
  repo_name string,
  repo_owner string,
  org_id bigint,
  org_login string,
  actor_id bigint,
  actor_login string,
  actor_type string,
  payload_size bigint,
  payload_distinct_size bigint,
  payload_ref string,
  payload_action string,
  pr_user_login string,
  watch_action string,
  repo_language string,
  repo_created_at string,
  ingest_ts string,
  source_file string
)
PARTITIONED BY (date string, hour string)
STORED AS PARQUET
LOCATION 's3://<your_bucket_here>/bronze/gharchive/';

CREATE EXTERNAL TABLE IF NOT EXISTS github_analytics.silver_events (
  event_id string,
  event_type string,
  created_at string,
  repo_id bigint,
  repo_name string,
  repo_owner string,
  org_id bigint,
  org_login string,
  actor_id bigint,
  actor_login string,
  actor_type string,
  payload_size bigint,
  payload_distinct_size bigint,
  payload_ref string,
  payload_action string,
  pr_user_login string,
  watch_action string,
  repo_language string,
  repo_created_at string,
  ingest_ts string,
  source_file string,
  event_ts timestamp,
  event_hour_ts timestamp,
  is_bot boolean
)
PARTITIONED BY (event_day date)
STORED AS PARQUET
LOCATION 's3://<your_bucket_here>/silver/events/';

MSCK REPAIR TABLE github_analytics.bronze_gharchive_events;
MSCK REPAIR TABLE github_analytics.silver_events;
