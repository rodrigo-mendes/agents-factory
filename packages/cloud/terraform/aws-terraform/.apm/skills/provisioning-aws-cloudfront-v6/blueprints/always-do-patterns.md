# Always-Do Patterns — provisioning-aws-cloudfront-v6

Index of the always-do blueprints, split by topic. Each pattern has complete HCL and cites its
official source (fetched 2026-10-22).

| # | Pattern | Blueprint |
|---|---|---|
| 1 | Terraform block (`~> 1.16`, `~> 6.69`), S3 backend `use_lockfile`, `aws.us_east_1` alias | [always-do-foundation](./always-do-foundation.md#1-terraform-block-and-providers) |
| 2 | Distribution with S3 origin, OAC, explicit TLS policy, explicit IPv6/price class | [always-do-foundation](./always-do-foundation.md#2-distribution-with-s3-origin-and-oac) |
| 3 | OAC and S3 bucket policy with `AWS:SourceArn` | [always-do-origins-policies](./always-do-origins-policies.md#3-oac-and-s3-bucket-policy) |
| 4 | Cache and response headers policies (no `forwarded_values`) | [always-do-origins-policies](./always-do-origins-policies.md#4-cache-origin-request-and-response-headers-policies) |
| 5 | Custom origin HTTPS-only and origin group | [always-do-origins-policies](./always-do-origins-policies.md#5-custom-origin-and-origin-group) |
| 6 | Functions, public key (newline), key group | [always-do-origins-policies](./always-do-origins-policies.md#6-functions-and-signed-urls) |
| 7 | Route 53 alias A and AAAA | [always-do-dns-logging](./always-do-dns-logging.md#7-route-53-alias-to-cloudfront) |
| 8 | Standard logging v2 in us-east-1 | [always-do-dns-logging](./always-do-dns-logging.md#8-standard-logging-v2) |
| 9 | Custom error responses (set both `response_code` and `response_page_path`) | [always-do-dns-logging](./always-do-dns-logging.md#9-custom-error-responses) |
