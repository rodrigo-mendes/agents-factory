---
name: aws-architecture-advisor
description: "Routes an AWS architecture question, design request, or review to the aws-architect advisory agent. Use when you need sourced, version-dated AWS architecture guidance — WAF pillar reviews, security hardening, serverless design, multi-account governance, networking, or cost optimization."
argument-hint: "<question or scope> (e.g. 'review my VPC design', 'design serverless event-driven API', 'assess WAF security posture')"
context: fork
agent: aws-architect
disable-model-invocation: true
---

# AWS Architecture Advisor

## Function

Routes AWS architecture questions and design requests to the `aws-architect` advisory agent.
The agent reasons over the 40 knowledge skills in `packages/aws-skills/.apm/skills/` and
returns sourced, version-dated guidance. It does not invent facts — every claim traces to an
official source recorded in a skill's `## Version Context` block.

## How the Agent Routes to the 40 AWS Skills

The `aws-architect` agent loads skills on demand based on the request domain. Skills are
referenced by name from `packages/aws-skills/.apm/skills/<name>/SKILL.md`. The full routing
table is in the agent body (`packages/aws-architect/.apm/agents/aws-architect.agent.md`).

### Available Knowledge Skills (40 total)

**WAF & Pillars**
- `applying-aws-well-architected` — six pillars, overall architecture assessment
- `applying-aws-operational-excellence` — OE design principles, IaC posture
- `applying-waf-operational-excellence-pillar` — OE pillar deep-dive
- `applying-aws-reliability-pillar` — DR, backup, fault tolerance
- `applying-waf-reliability-pillar` — Reliability pillar deep-dive
- `applying-aws-performance-efficiency` — compute selection, right-sizing, Graviton
- `applying-waf-cost-optimization` — pricing model mix, cost guardrails
- `applying-aws-sustainability-pillar` — energy efficiency, carbon footprint
- `applying-waf-sustainability-pillar` — Sustainability pillar deep-dive
- `applying-aws-serverless-well-architected-lens` — serverless WAF lens

**Security**
- `architecting-aws-security-pillar` — seven security areas, detection stack
- `securing-aws-iam-serverless` — IAM roles, SCPs/RCPs, confused-deputy, federation
- `securing-aws-cognito` — user pools, identity federation, OAuth 2.0
- `securing-aws-secrets-certificates` — Secrets Manager, ACM, rotation
- `securing-aws-waf-web-acls` — WAF web ACLs, managed rule groups
- `securing-vpc-network-access` — security groups, NACLs, VPC flow logs
- `protecting-workloads-ddos-shield` — Shield Advanced, DDoS protection

**Multi-Account & Governance**
- `architecting-aws-multi-account-organizations` — Organizations, Control Tower, landing zone
- `architecting-aws-saas-multitenant` — SaaS, multi-tenant isolation

**Networking**
- `designing-aws-vpc-networks` — VPC topology, subnets, NAT GW, Transit Gateway
- `configuring-aws-route53-dns` — DNS, latency routing, health checks
- `delivering-cloudfront-cdn` — CDN, edge caching, origin access
- `designing-multi-cloud-network-topology` — hybrid, multi-cloud connectivity

**Serverless & Event-Driven**
- `designing-aws-api-gateway-serverless` — API Gateway REST/HTTP, authorizers
- `architecting-lambda-serverless-patterns` — Lambda execution model, concurrency, SnapStart
- `architecting-sam-serverless-patterns` — SAM, CloudFormation extensions
- `implementing-lambda-powertools-java` — Powertools Java, structured logging, tracing
- `architecting-eventbridge-eda` — EventBridge, event buses, pipes
- `orchestrating-aws-step-functions` — Step Functions, state machines
- `architecting-aws-sqs-messaging` — SQS, dead-letter queues, FIFO
- `architecting-aws-sns-pubsub` — SNS, pub/sub, fan-out
- `architecting-aws-ses-email` — SES, email delivery, DKIM/DMARC

**Data**
- `designing-dynamodb-nosql` — DynamoDB, single-table design, GSI
- `architecting-aws-s3-storage` — S3, lifecycle, versioning, replication

**Observability & Audit**
- `monitoring-cloudwatch-observability` — CloudWatch, metrics, alarms, SLOs
- `architecting-cloudtrail-audit-logging` — CloudTrail, org trail, Log Archive
- `auditing-aws-cloudtrail` — CloudTrail audit, log analysis
- `tracing-aws-xray` — X-Ray, distributed tracing, ADOT

**Cost**
- `managing-aws-costs` — cost management, tagging, budgets
- `optimizing-aws-costs` — Compute Optimizer, right-sizing, Savings Plans

## Shared Knowledge Base

The agent also references:
- `workspace/aws/_family_facts_v2026.md` — 20 facts shared across ≥2 skills
- `workspace/aws/_family_rules_v2026.md` — 13 numbered testable policy rules

## Usage Examples

```
/aws-architecture-advisor review my three-tier VPC design for WAF Reliability and Security
/aws-architecture-advisor design a serverless event-driven order processing system
/aws-architecture-advisor assess our multi-account landing zone against WAF Security Pillar
/aws-architecture-advisor what RCP limits should I apply to prevent data exfiltration?
```

## Evaluation Scenarios

See [./blueprints/evaluation-scenarios.md](./blueprints/evaluation-scenarios.md) for 4 test
scenarios covering the canonical advisory workflow.
