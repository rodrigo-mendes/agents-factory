# Never-Do Patterns — provisioning-aws-route53-v6

Index of the never-do blueprints, split by topic. Each entry has a `# WRONG` block, the documented
reason with its source (fetched 2026-10-22), and the correct alternative.

| Anti-pattern | Blueprint |
|---|---|
| Inline `vpc` blocks mixed with `aws_route53_zone_association` | [never-do-zones-records](./never-do-zones-records.md#1-mixing-inline-vpc-blocks-with-aws_route53_zone_association) |
| Alias record with `ttl` or `records` | [never-do-zones-records](./never-do-zones-records.md#2-alias-record-with-ttl-or-records) |
| Routing policy without `set_identifier`, or two policies on one record | [never-do-zones-records](./never-do-zones-records.md#3-routing-policies-without-set_identifier-or-combined) |
| Partial `aws_route53_records_exclusive` | [never-do-zones-records](./never-do-zones-records.md#4-partial-aws_route53_records_exclusive) |
| Batch reads in drift-sensitive pipelines | [never-do-zones-records](./never-do-zones-records.md#5-batch-reads-in-drift-sensitive-pipelines) |
| `region` on global Route 53 resources | [never-do-region-logging-dnssec](./never-do-region-logging-dnssec.md#1-region-on-global-route-53-resources) |
| Query log group outside us-east-1 or on a private zone | [never-do-region-logging-dnssec](./never-do-region-logging-dnssec.md#2-query-log-log-group-outside-us-east-1-or-on-private-zone) |
| DNSSEC on a private zone or non-us-east-1 KMS key | [never-do-region-logging-dnssec](./never-do-region-logging-dnssec.md#3-dnssec-on-a-private-zone-or-with-a-non-us-east-1-kms-key) |
| Pinning withdrawn 6.57.0; S3 backend `dynamodb_table` | [never-do-region-logging-dnssec](./never-do-region-logging-dnssec.md#4-withdrawn-version-and-deprecated-backend-option) |
