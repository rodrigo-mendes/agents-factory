# Always-Do Patterns — provisioning-aws-step-functions-v6

Index of the always-do blueprints, split by topic. Each pattern has HCL and cites its page
(read 2026-10-23).

| # | Pattern | Blueprint |
|---|---|---|
| 1 | Terraform block (`~> 1.16`, `~> 6.69`) and S3 backend with `use_lockfile` | [always-do-foundation](./always-do-foundation.md#1-terraform-block-and-s3-backend) |
| 2 | Execution role: `states.amazonaws.com` trust, logging and X-Ray policies | [always-do-foundation](./always-do-foundation.md#2-iam-execution-role) |
| 3 | State machine with logging, tracing, `publish`, retry and timeouts | [always-do-state-machine](./always-do-state-machine.md#3-state-machine-with-logging-tracing-and-a-published-version) |
| 4 | Alias with weighted routing over versions | [always-do-state-machine](./always-do-state-machine.md#4-alias-with-weighted-routing) |
| 5 | Activity with tags | [always-do-state-machine](./always-do-state-machine.md#5-activity-with-tags) |
| 6 | Customer managed key encryption (role, key policy) | [always-do-encryption-testing](./always-do-encryption-testing.md#6-customer-managed-key-encryption) |
| 7 | `terraform test` with `mock_provider` and CI commands | [always-do-encryption-testing](./always-do-encryption-testing.md#7-terraform-test-and-ci) |
