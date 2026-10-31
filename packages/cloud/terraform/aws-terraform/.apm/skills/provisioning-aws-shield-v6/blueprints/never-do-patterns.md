# Never-Do Patterns — provisioning-aws-shield-v6

Index of the never-do blueprints. Each entry has a `# WRONG` block, the documented reason with its
source (fetched 2026-10-23), and the correct alternative.

| Anti-pattern | Blueprint |
|---|---|
| `region` on an `aws_shield_*` resource (global service) | [never-do-shield](./never-do-shield.md#1-region-on-aws_shield_-resources) |
| NLB ARN as `resource_arn` | [never-do-shield](./never-do-shield.md#2-nlb-arn-as-resource_arn) |
| Health check on a Route 53 hosted-zone protection | [never-do-shield](./never-do-shield.md#3-health-check-on-a-hosted-zone-protection) |
| `members` / `resource_type` without the matching `pattern` | [never-do-shield](./never-do-shield.md#4-protection-group-arguments-without-the-matching-pattern) |
| S3 backend with `dynamodb_table` (deprecated) | [never-do-shield](./never-do-shield.md#5-s3-backend-with-dynamodb_table) |
| Pinning withdrawn provider 6.57.0 | [never-do-shield](./never-do-shield.md#6-pinning-version-6570) |
