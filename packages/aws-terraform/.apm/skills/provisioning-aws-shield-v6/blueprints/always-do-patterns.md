# Always-Do Patterns — provisioning-aws-shield-v6

Index of the always-do blueprints, split by topic. Each pattern has complete HCL and cites its
official source (fetched 2026-10-23).

| # | Pattern | Blueprint |
|---|---|---|
| 1 | Terraform block (`~> 1.16`, `~> 6.69`), S3 backend, Shield Advanced subscription | [always-do-subscription-protection](./always-do-subscription-protection.md#1-terraform-block-and-subscription) |
| 2 | Protections (CloudFront, ALB, NLB via EIP allocation ARN) | [always-do-subscription-protection](./always-do-subscription-protection.md#2-protections) |
| 3 | Protection groups (`ARBITRARY`, `BY_RESOURCE_TYPE`) | [always-do-subscription-protection](./always-do-subscription-protection.md#3-protection-groups) |
| 4 | Health check association | [always-do-detection-response](./always-do-detection-response.md#4-health-check-association) |
| 5 | SRT access role and log bucket | [always-do-detection-response](./always-do-detection-response.md#5-srt-access) |
| 6 | Proactive engagement (when approved) | [always-do-detection-response](./always-do-detection-response.md#6-proactive-engagement-when-approved) |
