import sys

from awsglue.utils import getResolvedOptions
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, date_trunc


args = getResolvedOptions(sys.argv, ["S3_BUCKET", "PROCESS_DATE"])

bucket = args["S3_BUCKET"]
process_date = args["PROCESS_DATE"]

spark = (
    SparkSession.builder.appName("github-analytics-silver-to-gold")
    .config("spark.sql.sources.partitionOverwriteMode", "dynamic")
    .getOrCreate()
)

silver_path = f"s3://{bucket}/silver/events/"
gold_path = f"s3://{bucket}/gold"

events = spark.read.parquet(silver_path).filter(col("event_day") == process_date)

event_type_daily = (
    events.groupBy("event_day", "event_type")
    .agg(count("*").alias("event_count"))
)

event_type_hourly = (
    events.groupBy(date_trunc("hour", col("event_ts")).alias("event_hour_ts"), "event_type")
    .agg(count("*").alias("event_count"))
)

push_user_daily = (
    events.filter(col("event_type") == "PushEvent")
    .filter(~col("is_bot"))
    .filter(col("actor_login").isNotNull())
    .groupBy("event_day", "actor_login")
    .agg(count("*").alias("push_count"))
)

push_user_hourly = (
    events.filter(col("event_type") == "PushEvent")
    .filter(~col("is_bot"))
    .filter(col("actor_login").isNotNull())
    .groupBy(date_trunc("hour", col("event_ts")).alias("event_hour_ts"), "actor_login")
    .agg(count("*").alias("push_count"))
)

pr_org_daily = (
    events.filter(col("event_type") == "PullRequestEvent")
    .filter(col("org_login").isNotNull())
    .groupBy("event_day", "org_login")
    .agg(count("*").alias("pr_count"))
)

pr_org_hourly = (
    events.filter(col("event_type") == "PullRequestEvent")
    .filter(col("org_login").isNotNull())
    .groupBy(date_trunc("hour", col("event_ts")).alias("event_hour_ts"), "org_login")
    .agg(count("*").alias("pr_count"))
)

pr_repo_daily = (
    events.filter(col("event_type") == "PullRequestEvent")
    .filter(col("repo_name").isNotNull())
    .groupBy("event_day", "repo_name")
    .agg(count("*").alias("pr_count"))
)

pr_repo_hourly = (
    events.filter(col("event_type") == "PullRequestEvent")
    .filter(col("repo_name").isNotNull())
    .groupBy(date_trunc("hour", col("event_ts")).alias("event_hour_ts"), "repo_name")
    .agg(count("*").alias("pr_count"))
)

tables = {
    "event_type_daily": event_type_daily,
    "event_type_hourly": event_type_hourly,
    "push_user_daily": push_user_daily,
    "push_user_hourly": push_user_hourly,
    "pr_org_daily": pr_org_daily,
    "pr_org_hourly": pr_org_hourly,
    "pr_repo_daily": pr_repo_daily,
    "pr_repo_hourly": pr_repo_hourly,
}

for table_name, dataframe in tables.items():
    dataframe.write.mode("overwrite").parquet(f"{gold_path}/{table_name}/event_day={process_date}")

spark.stop()
