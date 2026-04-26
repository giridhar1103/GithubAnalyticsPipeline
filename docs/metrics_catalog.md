# Metrics Catalog

The gold layer supports dashboard and warehouse metrics.

## Core Metrics

| Metric | Grain | Source |
| --- | --- | --- |
| Total events | preset | `event_type_daily`, `event_type_hourly` |
| Events by type | day, hour | `event_type_daily`, `event_type_hourly` |
| Push leaders | day, hour | `push_user_daily`, `push_user_hourly` |
| Pull request organizations | day, hour | `pr_org_daily`, `pr_org_hourly` |
| Pull request repositories | day, hour | `pr_repo_daily`, `pr_repo_hourly` |

## Extended Metrics

| Metric | Description |
| --- | --- |
| Repository daily activity | Event counts by repository and event type |
| Organization daily activity | Event counts grouped by organization |
| Actor daily activity | Event counts grouped by actor |
| Watch events by repository | Star activity by repository |
| Fork events by repository | Fork activity by repository |
| Issue events by repository | Issue activity by repository |
| Release events by repository | Release activity by repository |
| Create events by repository | Branch or tag creation activity |
| Delete events by repository | Branch or tag deletion activity |
| Repo language activity | Event counts grouped by repository language |
| Rolling 7 day activity | Moving activity window |
| Rolling 30 day activity | Moving activity window |
| Day over day change | Percent change by metric |
| Hour over hour change | Percent change by metric |
| Push to PR ratio | Push count divided by pull request count |

## Dashboard Presets

```text
1h
4h
24h
7d
30d
max
```

Short presets use hourly aggregates. Longer presets use daily aggregates.
