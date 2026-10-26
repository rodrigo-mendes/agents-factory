# Never-Do Patterns — provisioning-aws-waf-v6

Index of the never-do blueprints, split by topic. Each entry has a `# WRONG` block, the documented
reason with its source (fetched 2026-10-22), and the correct alternative.

| Anti-pattern | Blueprint |
|---|---|
| Inline `rule` mixed with separate rule resources, no `ignore_changes` | [never-do-web-acl](./never-do-web-acl.md#1-mixing-inline-rules-with-separate-rule-resources) |
| `action` on a rule-group statement | [never-do-web-acl](./never-do-web-acl.md#2-action-on-a-rule-group-statement) |
| `rule_json` with `rule`; wrong JSON argument name on rule groups | [never-do-web-acl](./never-do-web-acl.md#3-json-rules-and-drift) |
| `web_acl_id` and `scope` on `aws_wafv2_web_acl_rule` | [never-do-attachment-scope](./never-do-attachment-scope.md#4-wrong-arguments-on-aws_wafv2_web_acl_rule) |
| Association with a CloudFront distribution | [never-do-attachment-scope](./never-do-attachment-scope.md#5-association-with-cloudfront) |
| Association with an HTTP API stage | [never-do-attachment-scope](./never-do-attachment-scope.md#6-association-with-an-http-api) |
| CLOUDFRONT scope without us-east-1 | [never-do-attachment-scope](./never-do-attachment-scope.md#7-cloudfront-scope-in-the-wrong-region) |
| 1,500 WCU treated as the maximum | [never-do-limits-provider](./never-do-limits-provider.md#8-treating-1500-wcu-as-the-maximum) |
| Rate limit validation `>= 100` | [never-do-limits-provider](./never-do-limits-provider.md#9-rate-limit-minimum-of-100) |
| S3 backend `dynamodb_table`; pinning 6.57.0; backend-region claim | [never-do-limits-provider](./never-do-limits-provider.md#10-deprecated-backend-withdrawn-version-and-backend-region-claim) |
