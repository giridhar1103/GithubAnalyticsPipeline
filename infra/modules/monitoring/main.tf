resource "aws_cloudwatch_log_group" "api" {
  name              = "/github-analytics/api"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "glue" {
  name              = "/github-analytics/glue"
  retention_in_days = 30
}

resource "aws_cloudwatch_metric_alarm" "api_5xx" {
  alarm_name          = "${var.project_name}-api-5xx"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "API5xxCount"
  namespace           = "GitHubAnalytics"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
}
