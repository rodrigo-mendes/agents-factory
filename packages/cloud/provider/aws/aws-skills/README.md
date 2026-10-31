# aws-skills

Knowledge skills for **AWS cloud architecture** (2026 service editions; AWS Well-Architected
Framework Nov-2024 edition). 40 skills, each a `SKILL.md` + `blueprints/` migrated as-is from the
dated, official-source research base in `workspace/docs/`, `workspace/sdk_java/` and
`workspace/terraform/`.

These are **knowledge skills** (auto-invocable); the deliberate-action entry point and routing live
in the companion **`aws-architect`** package (advisory agent).

## Scope

| Group | Skills |
|---|---|
| Well-Architected | `applying-aws-well-architected`, the per-pillar `applying-aws-*` / `applying-waf-*` skills, `architecting-aws-security-pillar` |
| Serverless | `architecting-lambda-serverless-patterns`, `architecting-sam-serverless-patterns`, `designing-aws-api-gateway-serverless`, `orchestrating-aws-step-functions`, `architecting-eventbridge-eda`, `implementing-lambda-powertools-java` |
| Networking / edge | `designing-aws-vpc-networks`, `securing-vpc-network-access`, `configuring-aws-route53-dns`, `delivering-cloudfront-cdn`, `designing-multi-cloud-network-topology` |
| Security | `securing-aws-cognito`, `securing-aws-iam-serverless`, `securing-aws-secrets-certificates`, `securing-aws-waf-web-acls`, `protecting-workloads-ddos-shield` |
| Data / messaging / storage | `designing-dynamodb-nosql`, `architecting-aws-s3-storage`, `architecting-aws-sns-pubsub`, `architecting-aws-sqs-messaging`, `architecting-aws-ses-email` |
| Observability / audit | `monitoring-cloudwatch-observability`, `tracing-aws-xray`, `architecting-cloudtrail-audit-logging`, `auditing-aws-cloudtrail` |
| Cost | `managing-aws-costs`, `optimizing-aws-costs`, `applying-waf-cost-optimization` |
| SaaS / multi-account | `architecting-aws-saas-multitenant`, `architecting-aws-multi-account-organizations` |

## Known overlaps (flagged for review — G3 decision)

Several topics ship as more than one skill (migrated as-is to avoid losing work):

- Well-Architected pillars appear under both `applying-aws-*` and `applying-waf-*` naming.
- Cost has three skills: `managing-aws-costs`, `optimizing-aws-costs`, `applying-waf-cost-optimization`.
- CloudTrail has two: `architecting-cloudtrail-audit-logging`, `auditing-aws-cloudtrail`.

A later pass should pick one canonical skill per topic and merge/retire the rest.

## Dependencies

- `../factory-core`
