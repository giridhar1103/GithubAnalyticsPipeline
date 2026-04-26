SELECT 'silver_event_count' AS check_name, COUNT(*) AS value
FROM github_analytics.silver_events
WHERE event_day = DATE '<process_date_here>';

SELECT 'null_event_type' AS check_name, COUNT(*) AS value
FROM github_analytics.silver_events
WHERE event_day = DATE '<process_date_here>'
  AND event_type IS NULL;

SELECT 'duplicate_event_ids' AS check_name, COUNT(*) - COUNT(DISTINCT event_id) AS value
FROM github_analytics.silver_events
WHERE event_day = DATE '<process_date_here>';

SELECT 'gold_event_type_reconciliation' AS check_name,
       silver.total_events - gold.total_events AS value
FROM (
  SELECT COUNT(*) AS total_events
  FROM github_analytics.silver_events
  WHERE event_day = DATE '<process_date_here>'
) silver
CROSS JOIN (
  SELECT SUM(event_count) AS total_events
  FROM github_analytics.gold_event_type_daily
  WHERE event_day = DATE '<process_date_here>'
) gold;
