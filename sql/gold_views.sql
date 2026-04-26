CREATE OR REPLACE VIEW github_analytics.v_event_type_daily AS
SELECT event_day, event_type, SUM(event_count) AS event_count
FROM github_analytics.gold_event_type_daily
GROUP BY event_day, event_type;

CREATE OR REPLACE VIEW github_analytics.v_top_push_users_30d AS
SELECT actor_login, SUM(push_count) AS push_count
FROM github_analytics.gold_push_user_daily
WHERE event_day >= current_date - interval '30' day
GROUP BY actor_login
ORDER BY push_count DESC;

CREATE OR REPLACE VIEW github_analytics.v_top_pr_orgs_30d AS
SELECT org_login, SUM(pr_count) AS pr_count
FROM github_analytics.gold_pr_org_daily
WHERE event_day >= current_date - interval '30' day
GROUP BY org_login
ORDER BY pr_count DESC;

CREATE OR REPLACE VIEW github_analytics.v_top_pr_repos_30d AS
SELECT repo_name, SUM(pr_count) AS pr_count
FROM github_analytics.gold_pr_repo_daily
WHERE event_day >= current_date - interval '30' day
GROUP BY repo_name
ORDER BY pr_count DESC;
