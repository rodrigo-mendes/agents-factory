# Always-Do Patterns — provisioning-aws-route53-v6

Index of the always-do blueprints, split by topic. Each pattern has complete HCL and cites its
official source (fetched 2026-10-22).

| # | Pattern | Blueprint |
|---|---|---|
| 1 | Terraform block (`~> 1.16`, `~> 6.69`), S3 backend, `us_east_1` alias | [always-do-zones-records](./always-do-zones-records.md#1-terraform-block-and-providers) |
| 2 | Public and private zones, subdomain delegation | [always-do-zones-records](./always-do-zones-records.md#2-public-and-private-zones) |
| 3 | Records, alias records, long TXT values | [always-do-zones-records](./always-do-zones-records.md#3-records-and-alias-records) |
| 4 | Routing policies (failover, geolocation default) and health checks | [always-do-zones-records](./always-do-zones-records.md#4-routing-policies-and-health-checks) |
| 5 | Query logging (us-east-1 log group, resource policy, Route53.2) | [always-do-logging-dnssec](./always-do-logging-dnssec.md#5-query-logging) |
| 6 | DNSSEC (KMS ECC_NIST_P256 key, KSK, zone signing) | [always-do-logging-dnssec](./always-do-logging-dnssec.md#6-dnssec) |
| 7 | Delegation sets and Resolver (regional exception) | [always-do-logging-dnssec](./always-do-logging-dnssec.md#7-delegation-sets-and-resolver) |
