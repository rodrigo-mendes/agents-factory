---
name: architecting-aws-saas-multitenant
description: "Designs and validates multi-tenant B2B SaaS architectures on AWS using the Well-Architected Framework (6 pillars) and SaaS Lens. Use when selecting tenant-isolation models, choosing compute/data/messaging services, reviewing a SaaS design for security and cost, or enforcing per-tenant observability and onboarding patterns."
---

## Function

Specialist in multi-tenant B2B SaaS architecture on AWS, anchored to the AWS Well-Architected Framework (6 pillars, continuously revised) and the AWS SaaS Lens (published April 4, 2023).

## Version Context

**Framework**: AWS Well-Architected Framework — 6 pillars (continuously revised; verified 2026-08-28)
**SaaS Lens version**: April 4, 2023 (5 conceptual areas — Sustainability pillar not yet incorporated)
**Release date**: SaaS Lens: 2023-04-04; base framework: continuously revised
**Support status**: Active (base framework); SaaS Lens stable, pending Sustainability update

**Important notes for this version**:
- Base framework: 6 pillars — Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, Sustainability
- SaaS Lens covers 5 of the 6 pillars (Sustainability not covered at April-2023 publication)
- Three verified tenant-isolation models: Silo, Pool, Bridge
- "AWS WAF 2024" is not a distinct edition — the framework is continuously revised

**Sustainability gap**: Apply base-framework guidance directly (maximize pooling, right-size, prefer managed/serverless). No SaaS-specific Sustainability guidance exists yet in the Lens.

⚠️ **CRITICAL — Agent Warning**:
Apply SaaS Lens patterns only for the 5 pillars it covers.
For Sustainability, apply the base-framework pillar guidance directly.
Do not invent SaaS Lens guidance for Sustainability from memory.

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — ✅⚠️🚫 architecture guardrails
- **[Tenant Isolation Models](#tenant-isolation-models)** — Silo / Pool / Bridge decision table
- **[Architectural Decisions](#architectural-decisions)** — Compute, data, messaging, account, region
- **[Integration Patterns](#integration-patterns)** — Control-plane and cross-service connections
- **[Verification Loop](#verification-loop)** — Architecture review checklist
- **[Quick Reference](#quick-reference)** — Critical limits and service selection defaults
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 6 test cases
- **[External Resources](#external-resources)** — Official documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

- **Inject tenant context at the identity layer** — Embed tenant ID as a custom claim in the JWT at authentication (Amazon Cognito). Downstream services derive tenant-scoped STS credentials via `AssumeRole` with session policies. Never trust a tenant ID passed in the request body — IAM/policy layer must enforce isolation, not app code alone.

- **Pool data with row-level isolation enforced by IAM** — In pool tables, tenant ID is the partition/leading key. Use `dynamodb:LeadingKeys` IAM condition key (DynamoDB) or row-level security (RDS/Aurora). Prevents cross-tenant reads even if application-layer filtering is bypassed.

- **Run all stateful services Multi-AZ** — All shared/stateful tenant data must use Multi-AZ with automated failover (Amazon RDS Multi-AZ or Aurora multi-AZ replicas). No single-AZ production databases. Define per-tier RTO/RPO and test failover.

- **Externalize all secrets with automatic rotation** — No credentials in code, environment variables, container images, or configuration files. Use AWS Secrets Manager with rotation enabled; scope access by IAM to the owning tenant or service.

- **Emit tenant-tagged observability and per-tenant cost attribution** — Every log, metric, and trace carries tenant ID as a dimension/field (CloudWatch EMF, X-Ray). Tag every resource; use cost allocation tags + Cost Explorer to produce per-tenant/tier cost-to-serve. High-cardinality dimensions should aggregate by tier to control CloudWatch metric cost.

- **Automate tenant onboarding end-to-end** — Provision identity, resources (silo), and tier config via a repeatable idempotent workflow (AWS Step Functions + CloudFormation/CDK). Zero manual console steps in the onboarding path.

### ⚠️ Ask First

- **Compute model** — Lambda (spiky/unpredictable per-tenant load, pay-per-use, fast onboarding) vs. ECS Fargate (steady containerized workloads, long-running processes) vs. EC2 (specialized hardware, maximum control, sustained high utilization). Ask about tenant load profile and team operational capacity before choosing. See [Architectural Decisions](#architectural-decisions).

- **Data architecture** — RDS PostgreSQL/MySQL (relational, transactions, SQL skills) vs. DynamoDB (pool at scale, `LeadingKeys` isolation, single-digit-ms access) vs. Aurora Serverless v2 (relational + variable load autoscaling). Ask about access patterns and consistency requirements. See [Architectural Decisions](#architectural-decisions).

- **Messaging service** — SQS (decoupling, work queues, noisy-tenant buffering) vs. Kinesis Data Streams (high-throughput ordered streaming, metering ingestion, replay) vs. EventBridge (event-driven choreography, control-plane events, SaaS integrations). Ask about throughput, ordering, and replay needs.

- **Account strategy** — Single-account (early stage, pool-only, few tenants) vs. AWS Organizations multi-account (silo tenants/tiers, strong isolation, per-tenant quotas and billing, SCP guardrails). Ask about tenant tier isolation requirements and operational maturity.

- **Region strategy** — Single region (simplicity, lowest cost) vs. multi-region active-passive (DR/RTO compliance) vs. multi-region active-active / data-residency sharding (global B2B tenants, GDPR/data-residency requirements). Ask about data-residency mandates and RTO targets.

### 🚫 Never Do

| Anti-Pattern | Why Prohibited | Correct Alternative |
|---|---|---|
| Tenant isolation enforced only in application code | A `WHERE tenant_id = ?` filter is a single point of failure; any bypass (misconfigured query, injection) exposes all tenants. **Risk: Critical** | Enforce at the IAM/data layer: DynamoDB `LeadingKeys` condition or RDS row-level security with tenant-scoped STS sessions |
| Hardcoded secrets or shared static credentials | Password baked into a container image or shared across all tenants is catastrophic on any credential leak. **Risk: Critical** | AWS Secrets Manager with automatic rotation and IAM-scoped access |
| Single-AZ production database | AZ failure takes down all tenants sharing that DB with no automated recovery. **Risk: High** | Amazon RDS Multi-AZ or Aurora multi-AZ with automated failover and tested backups |
| No per-tenant cost or usage attribution | Untagged shared fleet makes unit economics invisible — impossible to price tiers or detect cost anomalies. **Risk: High (business)** | Cost allocation tags + tenant-dimension metering feeding Cost Explorer |
| No noisy-neighbor throttling in the pool | One tenant's traffic exhausts shared Lambda concurrency or API capacity, starving all others. **Risk: High** | API Gateway usage plans / per-tenant rate limits + Lambda reserved concurrency per tier |
| Manual tenant onboarding | Console clicks are error-prone, unauditable, and do not scale. **Risk: Medium-High** | Codified, idempotent onboarding via Step Functions + CloudFormation/CDK |

---

## Tenant Isolation Models

Verified source: AWS SaaS Lens (April 4, 2023) + bridge model page.

| Model | Definition | When to Use |
|---|---|---|
| **Silo** | Dedicated resources per tenant; shared identity/onboarding/ops control plane | Compliance requirements, strong isolation contractual SLA, premium tier willing to pay for it |
| **Pool** | Tenants share scalable infrastructure (IAM + data-layer isolation) | Default for most B2B SaaS; best economies of scale |
| **Bridge** | Silo the services that must be isolated; pool the rest | Realistic mature decomposition — most production SaaS lands here over time |

> Most production systems evolve toward **Bridge**: start Pool, silo services under regulatory or noisy-neighbor pressure.

---

## Architectural Decisions

### Compute Model
| Option | Best For | Trade-offs |
|---|---|---|
| **AWS Lambda** | Spiky/unpredictable per-tenant load, fast onboarding, pay-per-use, small teams | Cold starts; 15-min max; reserved concurrency needed for per-tenant isolation |
| **Amazon ECS (Fargate)** | Steady containerized workloads, long-running processes, portability | Coarser scaling; task sizing required; no node management |
| **Amazon EC2** | Specialized hardware, licensing, maximum control, sustained high utilization | Full patching/scaling/HA ownership; highest operational burden |

### Data Architecture
| Option | Best For | Trade-offs |
|---|---|---|
| **Amazon RDS (PostgreSQL/MySQL)** | Relational, transactions, SQL skills; row-level tenant isolation | Vertical scaling limits; provisioned cost even when idle |
| **Amazon DynamoDB** | Pool model at scale, `LeadingKeys` isolation, predictable single-digit-ms | Access-pattern-first modeling required; hot-partition risk for large tenants |
| **Amazon Aurora Serverless v2** | Relational + variable multi-tenant load needing ACU autoscaling | Cost at sustained load can exceed provisioned; scaling behavior must be tested |

### Messaging
| Option | Best For | Trade-offs |
|---|---|---|
| **Amazon SQS** | Decoupling, work queues, noisy-tenant buffering | No native ordering (except FIFO); no fan-out replay |
| **Amazon Kinesis Data Streams** | High-throughput ordered streaming, metering ingestion, replay | Shard capacity planning; cost at low volume |
| **Amazon EventBridge** | Control-plane event choreography, SaaS integrations, schema routing | Not for high-throughput streaming; at-least-once delivery |

### Account Strategy
| Option | Best For | Trade-offs |
|---|---|---|
| **Single account** | Early stage, few tenants, pool-only | Weak blast-radius/quota isolation; hard silo at account level |
| **AWS Organizations (multi-account)** | Silo tenants/tiers, strong isolation, per-tenant quotas and billing | Higher operational complexity; needs landing zone / Control Tower; automation mandatory |

### Region Strategy
| Option | Best For | Trade-offs |
|---|---|---|
| Single region | Simplicity, lowest cost, no cross-region latency | No regional DR; data-residency limits |
| Multi-region active-passive | DR/RTO requirements, compliance | Replication cost/complexity; failover testing burden |
| Multi-region active-active | Global B2B tenants, in-region data residency (EU/US) | Highest complexity; tenant-to-region routing; consistency challenges |

---

## Integration Patterns

**Control plane → Data plane**: Cognito authentication → STS `AssumeRole` with tenant-scoped session policy → tenant-scoped DynamoDB or RDS access. Tenant ID flows from JWT claim, not request body.

**Onboarding pipeline**: Step Functions orchestrates Cognito user pool creation (or user assignment), CloudFormation/CDK stack deploy (silo resources), tier-config injection, and event notification to downstream systems.

**Observability pipeline**: CloudWatch EMF with tenant ID dimension → CloudWatch metrics + Cost Explorer tags → per-tenant dashboard and alerting. X-Ray traces carry tenant ID annotation for cross-service correlation.

**Noisy-neighbor guard**: API Gateway usage plan per tenant/tier → Lambda reserved concurrency per tier → SQS per-tenant queue (buffer spiky tenants) → downstream processor.

**Common problems**:
- **Hot partition on pool DynamoDB table** → Use tenant ID as partition key only when tenant count is large; add sort key for access patterns. For large tenants consider silo table (Bridge model).
- **CloudWatch metric explosion from high cardinality** → Aggregate tenant dimension to tier level; reserve per-tenant granularity only for premium/silo tiers.
- **STS session token latency** → Cache tenant-scoped credentials for the session lifetime (up to 1 hour); refresh before expiry.

---

## Verification Loop

Architecture review checks (execute per design review, not build/deploy):

### 1. Tenant Isolation Check
```
For each data store: verify tenant ID is partition/leading key AND an IAM condition key enforces it.
For each API endpoint: verify tenant context is derived from verified JWT claim, not request body parameter.
Action: IAM policy simulator cross-tenant access test + integration test forging tenant IDs → all must deny.
```

### 2. Secrets and Credentials Check
```
Scan all repositories, container images, and CloudFormation/CDK for hardcoded credentials.
Verify Secrets Manager rotation schedule enabled for all DB credentials and API keys.
Action: git-secrets CI scan + AWS Config rule for Secrets Manager rotation enabled.
```

### 3. Reliability Baseline Check
```
Verify MultiAZ=true on all production RDS instances.
Verify Lambda reserved concurrency set per tier.
Verify API Gateway usage plans configured per tenant/tier.
Action: AWS Config rule checking MultiAZ=false on prod DBs → zero findings expected.
```

### 4. Observability and Cost Attribution Check
```
Verify tenant ID present as dimension in CloudWatch metrics and as X-Ray annotation.
Verify cost allocation tags applied to all resources.
Action: Produce a per-tenant error rate query and a per-tenant monthly cost report — both must return data.
```

### 5. Onboarding Automation Check
```
Provision a test tenant end-to-end using the onboarding pipeline.
Verify zero manual console steps required.
Action: Audit onboarding runbook — any manual step is a defect.
```

**Troubleshooting**:
- Cross-tenant access not blocked by IAM → Check session policy conditions; `dynamodb:LeadingKeys` must reference `${aws:PrincipalTag/TenantId}`
- Cost Explorer shows no per-tenant breakdown → Verify cost allocation tags are activated in Billing console and applied at resource creation
- Onboarding idempotency failures → Step Functions workflow must handle re-run: check if-already-exists guards in CDK/CloudFormation

---

## Quick Reference

**Tenant isolation decision**: Default Pool → add Bridge when compliance or noisy-neighbor demands silo for a specific service → Silo only for premium/regulated tiers.

**Data service default**: DynamoDB for pool-model stateless microservices; RDS/Aurora for relational/transactional; Aurora Serverless v2 for variable-load relational.

**Critical limits and defaults**:

| Resource | Limit / Default | Scope |
|---|---|---|
| STS session credentials | Max 1 hour (default); cache and refresh before expiry | Per-tenant IAM session |
| Lambda reserved concurrency | Set per tier; total account concurrency is a shared quota | Per-tier isolation |
| CloudWatch custom metrics | High cardinality (per-tenant) raises cost; aggregate by tier if tenant count > 1000 | Observability cost control |
| DynamoDB partition throughput | Hot-partition risk if one tenant >> others; Bridge model for outliers | Pool table scalability |
| Multi-AZ RDS | ~2x standby cost; HA, not cross-region DR or backup substitute | Reliability baseline |
| AWS Organizations | Automation mandatory; landing zone / Control Tower recommended | Multi-account governance |

**SaaS Lens conceptual areas** (5 of 6 pillars): Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization. Apply base-framework guidance for Sustainability.

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/architecting-aws-saas-multitenant/
├── SKILL.md                              <- This file (guardrails + decision tables)
└── blueprints/
    └── evaluation-scenarios.md           <- 6 test cases for skill-evaluator
```

---

## External Resources

### Verified (WebFetch/WebSearch, 2026-08-28)
- [AWS Well-Architected Framework — Pillars](https://docs.aws.amazon.com/wellarchitected/latest/framework/the-pillars-of-the-framework.html) — 6 pillars confirmed
- [AWS SaaS Lens](https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/saas-lens.html) — April 4, 2023; 5 conceptual areas
- [AWS SaaS Lens — Bridge Model](https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/bridge-model.html) — Verified isolation model
- [AWS SaaS Lens PDF](https://docs.aws.amazon.com/pdfs/wellarchitected/latest/saas-lens/wellarchitected-saas-lens.pdf) — Full SaaS Lens document

### Canonical (cited; verify before publishing — 🟡 not re-fetched in session)
- [AWS WAF Welcome](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html)
- [DynamoDB Fine-Grained Access (LeadingKeys)](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/specifying-conditions.html)
- [Amazon RDS Multi-AZ](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZ.html)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html)
- [SaaS Tenant Isolation Strategies Whitepaper](https://docs.aws.amazon.com/whitepapers/latest/saas-tenant-isolation-strategies/)
