# Never-Do Patterns — provisioning-aws-cloudwatch-v6

Index of the never-do blueprints, split by topic. Each entry has a `# WRONG` block, the documented
reason with its source (fetched 2026-10-14), and the correct alternative.

| Anti-pattern | Blueprint |
|---|---|
| `DELIVERY` log class used for non-Lambda workloads | [never-do-logs §1](./never-do-logs.md#1-delivery-class-misuse) |
| `INFREQUENT_ACCESS` class with metric or subscription filters | [never-do-logs §2](./never-do-logs.md#2-infrequent_access-with-filters) |
| Changing `log_group_class` without destroy/recreate (immutable) | [never-do-logs §3](./never-do-logs.md#3-log-group-class-is-immutable) |
| Relying on argument omission to disable `deletion_protection_enabled` | [never-do-logs §4](./never-do-logs.md#4-omitting-deletion_protection_enabled) |
| Child metric alarm with empty `alarm_actions` (CloudWatch.15 trap) | [never-do-alarms §1](./never-do-alarms.md#1-child-alarm-with-empty-actions) |
| Heredoc `alarm_rule` with trailing newline | [never-do-alarms §2](./never-do-alarms.md#2-heredoc-alarm_rule) |
| `statistic` and `extended_statistic` both set on one alarm | [never-do-alarms §3](./never-do-alarms.md#3-statistic-and-extended_statistic-together) |
| Top-level metric params combined with `metric_query` blocks | [never-do-alarms §4](./never-do-alarms.md#4-metric_query-with-top-level-metric-params) |
