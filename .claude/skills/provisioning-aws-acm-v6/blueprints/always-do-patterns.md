# Always-Do Patterns — provisioning-aws-acm-v6

Index of the always-do blueprints, split by topic. Each pattern has HCL (snippets; placeholders
where noted) and cites its source (fetched 2026-10-22).

| # | Pattern | Blueprint |
|---|---|---|
| 1 | Terraform block (`~> 1.16`, `~> 6.69`) | [always-do-public-certificates](./always-do-public-certificates.md#1-terraform-block-and-provider-constraint) |
| 2 | Public certificate, DNS validation via `aws_route53_record` `for_each`, validation resource, tags | [always-do-public-certificates](./always-do-public-certificates.md#2-public-certificate-with-dns-validation) |
| 3 | CloudFront certificate in `us-east-1` (alias or `region`) | [always-do-public-certificates](./always-do-public-certificates.md#3-cloudfront-certificates-in-us-east-1) |
| 4 | Imported certificate with `private_key_wo` | [always-do-import-private-lookup](./always-do-import-private-lookup.md#4-imported-certificate-with-private_key_wo) |
| 5 | Private CA-issued certificate with `early_renewal_duration` | [always-do-import-private-lookup](./always-do-import-private-lookup.md#5-private-ca-issued-certificate) |
| 6 | Data source lookup | [always-do-import-private-lookup](./always-do-import-private-lookup.md#6-data-source-lookup) |
| 7 | Importing an existing certificate into state | [always-do-import-private-lookup](./always-do-import-private-lookup.md#7-importing-an-existing-certificate) |
