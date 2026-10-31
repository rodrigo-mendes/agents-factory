# Always-Do Patterns — provisioning-aws-waf-v6

Index of the always-do blueprints, split by topic. Each pattern has HCL and cites its official
source (fetched 2026-10-22).

| # | Pattern | Blueprint |
|---|---|---|
| 1 | Terraform block (`~> 1.16`, `~> 6.69`), S3 backend with `use_lockfile`, us-east-1 alias | [always-do-foundation](./always-do-foundation.md#1-terraform-block-and-providers) |
| 2 | Regional web ACL with a managed rule group in count mode | [always-do-foundation](./always-do-foundation.md#2-regional-web-acl) |
| 3 | CLOUDFRONT scope web ACL attached through `web_acl_id` | [always-do-foundation](./always-do-foundation.md#3-cloudfront-scope) |
| 4 | IP set and rule group with capacity headroom | [always-do-resources](./always-do-resources.md#4-ip-set-and-rule-group) |
| 5 | Rate-based rule (limit >= 10) | [always-do-resources](./always-do-resources.md#5-rate-based-rule) |
| 6 | Separate rules on a web ACL with `ignore_changes = [rule]` | [always-do-attach-logging](./always-do-attach-logging.md#6-separate-rules-on-a-web-acl) |
| 7 | Web ACL association for regional resources | [always-do-attach-logging](./always-do-attach-logging.md#7-web-acl-association) |
| 8 | Logging configuration with `aws-waf-logs-` destination | [always-do-attach-logging](./always-do-attach-logging.md#8-logging-configuration) |
