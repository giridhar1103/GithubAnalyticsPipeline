import sys

from awsglue.utils import getResolvedOptions
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, date_trunc, lower, to_date, to_timestamp


args = getResolvedOptions(sys.argv, ["S3_BUCKET", "PROCESS_DATE"])

bucket = args["S3_BUCKET"]
process_date = args["PROCESS_DATE"]

spark = (
    SparkSession.builder.appName("github-analytics-bronze-to-silver")
    .config("spark.sql.sources.partitionOverwriteMode", "dynamic")
    .getOrCreate()
)

bronze_path = f"s3://{bucket}/bronze/gharchive/date={process_date}/"
silver_path = f"s3://{bucket}/silver/events/"

bronze = spark.read.parquet(bronze_path)

silver = (
    bronze.withColumn("event_ts", to_timestamp("created_at"))
    .withColumn("event_day", to_date("event_ts"))
    .withColumn("event_hour_ts", date_trunc("hour", col("event_ts")))
    .withColumn("is_bot", lower(col("actor_login")).contains("[bot]"))
    .filter(col("event_id").isNotNull())
    .filter(col("event_type").isNotNull())
    .filter(col("event_ts").isNotNull())
    .dropDuplicates(["event_id"])
)

(
    silver.write.mode("overwrite")
    .partitionBy("event_day")
    .parquet(silver_path)
)

spark.stop()
