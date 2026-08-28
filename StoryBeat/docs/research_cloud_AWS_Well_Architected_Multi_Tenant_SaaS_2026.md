# Research — AWS Well-Architected Framework for B2B SaaS Multi-Tenant Architecture

> **Agent:** framework-researcher · **Command:** `/cloud-architecture-researcher`
> **Research depth:** exhaustive · **Date compiled:** 2026-08-28
> **Target of record:** AWS Well-Architected Framework (current stable, 6 pillars) + AWS SaaS Lens
> **Audience:** Cloud/solution architects designing multi-tenant B2B SaaS on AWS.

---

## ⚠️ Version & Verification Notice (read first)

This document separates **verified-in-session** claims from **canonical-but-not-re-fetched** references. Do not treat the second class as confirmed.

| Claim class | Verified this session (WebFetch/WebSearch, 2026-08-28)? |
|---|---|
| The 6 WAF pillar names + set membership | ✅ Verified (framework pillars page) |
| SaaS Lens publication date = **April 4, 2023**, framed around **5** conceptual areas | ✅ Verified (SaaS Lens page) |
| Silo / Pool / **Bridge** tenant-isolation models | ✅ Verified (SaaS Lens search + bridge-model page reference) |
| Individual AWS service capabilities (RDS Multi-AZ, Secrets Manager, etc.) in Mandatory Patterns | 🟡 Canonical AWS URLs cited but **not re-opened this session** — verify before publishing |
| Cross-cloud equivalence map (GCP/Azure/OCI) | 🟡 Based on stable product-positioning knowledge — **treat as orientation, not contract** |

**Version-absolutism flag:** The request referenced "AWS WAF 2024." There is no single dated "2024" edition of the Well-Architected Framework — it is continuously revised. The **SaaS Lens** most relevant to multi-tenancy carries **publication date April 4, 2023** and predates the 6th (Sustainability) pillar; it addresses **five** conceptual areas. Where the SaaS Lens and the 6-pillar base framework diverge, the base framework (6 pillars) is authoritative for pillar structure, and the SaaS Lens is authoritative for multi-tenant patterns. `⚠️ Migration Note` tags mark this gap.

---

## 1. Framework Pillars — Multi-Tenant SaaS Context

The base framework defines **six** pillars (verified 2026-08-28): Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, Sustainability. The SaaS Lens (April 4, 2023) applies SaaS-specific best practices across five of these (Sustainability not yet incorporated at publication — `⚠️ Migration Note`).

### 1.1 Operational Excellence
- **SaaS lens:** Tenant-aware operations. Every log, metric, and trace must carry a **tenant context** (tenant ID injected at the identity/JWT layer) so operators can isolate a single tenant's health without scanning the whole fleet.
- Onboarding must be **fully automated** (no manual tenant provisioning) — tenant provisioning pipeline as code.
- Aggregate per-tenant operational metrics to detect **noisy-neighbor** and tier-SLA breaches.

### 1.2 Security
- **Tenant isolation is the defining security control of SaaS.** Isolation must be enforced at compute, data, and network layers, not just application logic.
- Use **dynamically-scoped IAM** (session policies / STS `AssumeRole` with tenant-scoped conditions, `dynamodb:LeadingKeys` for pool tables) so a tenant's runtime credentials cannot reach another tenant's data.
- Identity via a tenant-aware IdP (Amazon Cognito user pools per tenant, or federated).

### 1.3 Reliability
- Blast-radius containment: a failure or overload in one tenant must not cascade. Tier-based throttling and cell-based/shard architectures limit impact.
- Multi-AZ by default for stateful services; define per-tier RTO/RPO.

### 1.4 Performance Efficiency
- Pool resources for economies of scale; silo only where compliance or noisy-neighbor risk demands it.
- Right-size per tenant tier; autoscale on tenant-aggregate demand signals.

### 1.5 Cost Optimization
- **Per-tenant cost attribution** is mandatory — tag every resource and instrument shared resources with tenant-level metering so you know unit economics (cost-to-serve per tenant/tier).
- Pool model maximizes utilization; reserve silo for premium tiers that pay for it.

### 1.6 Sustainability (`⚠️ Migration Note`)
- 6th pillar (added to base framework Dec 2021); **not** covered by the April-2023 SaaS Lens's five conceptual areas. Apply base-framework guidance: maximize utilization through pooling, right-size, and prefer managed/serverless to shift efficiency responsibility to AWS.

### 1.7 SaaS Tenant-Isolation Models (SaaS Lens — verified)
| Model | Definition | When |
|---|---|---|
| **Silo** | Dedicated resources per tenant; shared identity/onboarding/ops plane. | Compliance, strong isolation, premium tier. |
| **Pool** | Tenants share scalable infrastructure. Classic multi-tenancy; best economies of scale. | Default for most B2B SaaS. |
| **Bridge** | Mix: silo the services that must be isolated, pool the rest. | Realistic decomposition — most mature SaaS lands here. |

---

## 2. Mandatory Patterns (✅ Always-Do)

> 🟡 Service-capability claims below cite canonical AWS URLs not re-opened in this session — verify each URL before publishing.

### Pattern 1 — Inject Tenant Context at the Identity Layer
- **Why (pillar):** Security, Operational Excellence.
- **Provider Service:** Amazon Cognito (user pools) + AWS STS / IAM session policies.
- **Architecture Decision:** Tenant ID is embedded as a custom claim in the JWT at authentication; downstream services derive tenant-scoped credentials via `AssumeRole` — never trust a tenant ID passed in the request body.
- **Verification:** Attempt cross-tenant access with a valid token for tenant A requesting tenant B's resource → must be denied at the IAM/policy layer, not just app code.
- **Trade-offs:** Adds token-exchange latency; requires disciplined role design.
- **Source:** https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/saas-lens.html (verified 2026-08-28)

### Pattern 2 — Pool Data with Row-Level Isolation Enforced by IAM
- **Why (pillar):** Security, Cost Optimization, Performance Efficiency.
- **Provider Service:** Amazon DynamoDB (with `dynamodb:LeadingKeys` condition) or Amazon RDS/Aurora with row-level security + partition key = tenant ID.
- **Architecture Decision:** In pool tables, the tenant ID is the partition/leading key and IAM condition keys prevent a session from reading rows outside its tenant.
- **Verification:** IAM policy simulator + integration test proving `LeadingKeys` blocks cross-tenant reads.
- **Trade-offs:** Pool tables need careful hot-partition management for large tenants.
- **Source:** https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/ (verified 2026-08-28); DynamoDB fine-grained access: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/specifying-conditions.html (🟡 canonical, not re-fetched)

### Pattern 3 — Stateful Services Multi-AZ by Default
- **Why (pillar):** Reliability.
- **Provider Service:** Amazon RDS Multi-AZ (or Aurora with multi-AZ replicas).
- **Architecture Decision:** All shared/stateful tenant data runs Multi-AZ with automated failover; no single-AZ production databases.
- **Verification:** Confirm `MultiAZ=true`; run a failover test and measure recovery against tier RTO.
- **Trade-offs:** ~2x standby cost; Multi-AZ is HA, not a substitute for cross-region DR or backups.
- **Source:** https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZ.html (🟡 canonical, not re-fetched)

### Pattern 4 — Externalize All Secrets, Rotate Automatically
- **Why (pillar):** Security, Operational Excellence.
- **Provider Service:** AWS Secrets Manager (per-tenant secrets where siloed; scoped by resource policy).
- **Architecture Decision:** No credentials in code, env vars, or images; enable automatic rotation; scope secret access by IAM to the owning tenant/service.
- **Verification:** Scan repos/images for secrets = zero; confirm rotation schedule enabled.
- **Trade-offs:** Per-secret cost and API call overhead; rotation Lambdas need maintenance.
- **Source:** https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html (🟡 canonical, not re-fetched)

### Pattern 5 — Tenant-Tagged Observability + Per-Tenant Cost Attribution
- **Why (pillar):** Operational Excellence, Cost Optimization.
- **Provider Service:** Amazon CloudWatch (embedded metric format with tenant dimension), AWS X-Ray, AWS Cost Explorer + cost allocation tags.
- **Architecture Decision:** Emit tenant ID as a metric dimension/log field and resource tag so both operational health and cost-to-serve are queryable per tenant/tier.
- **Verification:** Query a single tenant's error rate and monthly cost end-to-end.
- **Trade-offs:** High-cardinality tenant dimensions raise CloudWatch custom-metric cost — aggregate by tier where cardinality is large.
- **Source:** https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/saas-lens.html (verified 2026-08-28)

### Pattern 6 — Automated, Codified Tenant Onboarding
- **Why (pillar):** Operational Excellence, Reliability.
- **Provider Service:** AWS Step Functions + AWS CloudFormation/CDK (control-plane onboarding pipeline).
- **Architecture Decision:** Onboarding (identity, resource provisioning for silo tenants, tier config) is a repeatable, idempotent workflow — never manual.
- **Verification:** Provision a test tenant end-to-end with zero manual steps.
- **Trade-offs:** Upfront engineering investment in the control plane.
- **Source:** https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/saas-lens.html (verified 2026-08-28)

---

## 3. Architectural Decisions (⚠️ Ask-First)

### 3.1 Compute Model
| Option | Best for | Trade-offs |
|---|---|---|
| **AWS Lambda** | Spiky/unpredictable per-tenant load, fast onboarding, pay-per-use, small teams. | Cold starts; 15-min limit; per-tenant concurrency isolation needs reserved concurrency; harder for long/stateful workloads. |
| **Amazon ECS (Fargate)** | Steady containerized workloads, need long-running processes, portability. | Coarser scaling than Lambda; you manage task sizing; still serverless-ish (no node mgmt). |
| **Amazon EC2** | Specialized hardware, licensing, maximum control, sustained high utilization. | You own patching, scaling, HA; highest operational burden; weakest fit for lean SaaS. |

### 3.2 Data Architecture
| Option | Best for | Trade-offs |
|---|---|---|
| **Amazon RDS (PostgreSQL/MySQL)** | Relational, transactions, existing SQL skills; row-level tenant isolation. | Vertical scaling limits; provisioned capacity even when idle. |
| **Amazon DynamoDB** | Pool model at scale, predictable single-digit-ms access, tenant-as-partition-key, `LeadingKeys` isolation. | Access-pattern-first modeling; hot-partition risk for large tenants; limited ad-hoc query. |
| **Amazon Aurora Serverless v2** | Relational + variable/multi-tenant load needing autoscaling capacity (ACUs). | Cost at sustained high load can exceed provisioned; scaling granularity/behavior must be tested per workload. |

### 3.3 Messaging
| Option | Best for | Trade-offs |
|---|---|---|
| **Amazon SQS** | Decoupling, work queues, per-message processing, buffering noisy tenants. | No native ordering (except FIFO), no fan-out replay. |
| **Amazon Kinesis Data Streams** | High-throughput ordered streaming, per-tenant analytics/metering ingestion, replay. | Shard capacity planning; more ops overhead; cost at low volume. |
| **Amazon EventBridge** | Event-driven choreography, SaaS control-plane events, schema routing, partner/SaaS integrations. | Not for high-throughput streaming; at-least-once with eventual delivery. |

### 3.4 Account Strategy
| Option | Best for | Trade-offs |
|---|---|---|
| **Single account** | Early-stage, few tenants, pool-only. | Weak blast-radius/quota isolation; hard silo boundaries; noisy-neighbor at the account level. |
| **AWS Organizations (multi-account)** | Silo tenants / tiers, strong isolation, per-tenant quotas & billing, SCP guardrails. | Higher operational complexity; needs landing zone / Control Tower; automation mandatory. |

### 3.5 Region Strategy
| Option | Best for | Trade-offs |
|---|---|---|
| Single region | Simplicity, lowest cost, no cross-region latency. | No regional DR; data-residency limits. |
| Multi-region active-passive | DR/RTO requirements, compliance. | Replication cost/complexity; failover testing burden. |
| Multi-region active-active / data-residency sharding | Global B2B tenants, in-region data residency (EU/US separation). | Highest complexity; tenant-to-region routing at control plane; consistency challenges. |

---

## 4. Anti-Patterns (🚫 Never-Do)

### AP-1 — Tenant isolation in application code only
- ❌ **Wrong:** Single IAM role for all tenants; a `WHERE tenant_id = ?` filter in app code is the only guard against cross-tenant reads on an Amazon RDS pool table.
- ✅ **Correct:** Enforce isolation at the IAM/data layer — Amazon RDS row-level security or DynamoDB `dynamodb:LeadingKeys` with tenant-scoped STS sessions.
- **Pillar:** Security. **Risk:** Critical. **Detection:** Code review for shared roles; penetration test forging tenant IDs.

### AP-2 — Hardcoded secrets / shared static credentials
- ❌ **Wrong:** Database password baked into a container image env var, reused across all tenants.
- ✅ **Correct:** AWS Secrets Manager with automatic rotation and IAM-scoped access.
- **Pillar:** Security. **Risk:** Critical. **Detection:** Secret scanning (git-secrets/CI), image inspection.

### AP-3 — Single-AZ production database
- ❌ **Wrong:** Amazon RDS instance in one AZ serving all tenants, no standby.
- ✅ **Correct:** Amazon RDS Multi-AZ (or Aurora multi-AZ) with automated failover + tested backups.
- **Pillar:** Reliability. **Risk:** High. **Detection:** Config rule checking `MultiAZ=false` on prod DBs.

### AP-4 — No per-tenant cost/usage attribution
- ❌ **Wrong:** Untagged shared fleet; cost visible only as one blended AWS bill.
- ✅ **Correct:** Cost allocation tags + tenant-dimension metering (CloudWatch EMF / usage records) feeding Cost Explorer for cost-to-serve per tenant/tier.
- **Pillar:** Cost Optimization. **Risk:** High (business, not outage). **Detection:** Tag-policy compliance report; attempt to produce a per-tenant margin report.

### AP-5 — No noisy-neighbor throttling in the pool
- ❌ **Wrong:** One shared API with no per-tenant quotas; a single tenant's traffic starves all others (shared Lambda concurrency exhausted).
- ✅ **Correct:** Amazon API Gateway usage plans / per-tenant rate limits + Lambda reserved concurrency per tier.
- **Pillar:** Reliability, Performance Efficiency. **Risk:** High. **Detection:** Load test one tenant to saturation; observe others' latency.

### AP-6 — Manual tenant onboarding
- ❌ **Wrong:** Engineer clicks through the console to provision each new tenant's resources.
- ✅ **Correct:** Codified onboarding via AWS Step Functions + CloudFormation/CDK, idempotent and auditable.
- **Pillar:** Operational Excellence. **Risk:** Medium-High. **Detection:** Ask for the onboarding runbook — if it has manual steps, it's an anti-pattern.

---

## 5. Service Equivalence Map (orientation only — 🟡 not contract-grade)

| Service class | AWS | GCP | Azure | OCI |
|---|---|---|---|---|
| FaaS / serverless compute | Lambda | Cloud Functions / Cloud Run functions | Azure Functions | OCI Functions |
| Containers (serverless) | ECS on Fargate | Cloud Run | Container Apps | OCI Container Instances |
| VMs | EC2 | Compute Engine | Virtual Machines | OCI Compute |
| Managed relational DB | RDS | Cloud SQL | Azure Database for PostgreSQL/MySQL | OCI Database (Base DB / MySQL HeatWave) |
| Serverless relational | Aurora Serverless v2 | AlloyDB / Cloud SQL | Azure SQL Serverless | MySQL HeatWave (autoscale) |
| Managed NoSQL (key-value) | DynamoDB | Firestore / Bigtable | Cosmos DB | OCI NoSQL Database |
| Queue | SQS | Cloud Tasks / Pub/Sub | Storage Queues / Service Bus | OCI Queue |
| Streaming | Kinesis Data Streams | Pub/Sub (+ Dataflow) | Event Hubs | OCI Streaming |
| Event bus | EventBridge | Eventarc | Event Grid | OCI Events |
| Object storage | S3 | Cloud Storage | Blob Storage | OCI Object Storage |
| Secrets | Secrets Manager | Secret Manager | Key Vault | OCI Vault |
| Identity (CIAM) | Cognito | Identity Platform | Entra External ID (Azure AD B2C) | OCI IAM / Identity Domains |
| Observability | CloudWatch / X-Ray | Cloud Monitoring / Trace | Azure Monitor / App Insights | OCI Monitoring / APM |
| Multi-account governance | Organizations / Control Tower | Resource Manager / folders | Management Groups | Compartments / Tenancies |

> Equivalences are functional-positioning approximations from stable product knowledge; capabilities, isolation semantics, and limits differ. Verify against each provider's docs before any design decision.

---

## 6. Source Bibliography

**Verified in this session (WebFetch/WebSearch, access date 2026-08-28):**
- AWS Well-Architected Framework — The pillars of the framework: https://docs.aws.amazon.com/wellarchitected/latest/framework/the-pillars-of-the-framework.html
- AWS Well-Architected Framework — SaaS Lens (publication date April 4, 2023): https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/saas-lens.html
- AWS SaaS Lens — Bridge model (via search): https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/bridge-model.html
- AWS SaaS Lens PDF: https://docs.aws.amazon.com/pdfs/wellarchitected/latest/saas-lens/wellarchitected-saas-lens.pdf

**Canonical AWS URLs cited but NOT re-opened this session (🟡 verify before publishing):**
- AWS WAF whitepaper welcome: https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html
- DynamoDB fine-grained access (`LeadingKeys`): https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/specifying-conditions.html
- RDS Multi-AZ: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZ.html
- Secrets Manager: https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html
- SaaS Tenant Isolation Strategies (whitepaper): https://docs.aws.amazon.com/whitepapers/latest/saas-tenant-isolation-strategies/

---

## 7. Research Iteration Changelog

| # | Item | Action | Outcome |
|---|---|---|---|
| 1 | Pillar count/names | WebFetch pillars page | ✅ 6 pillars confirmed, exact names captured |
| 2 | SaaS Lens edition/date | WebFetch SaaS Lens page | ✅ April 4, 2023, five conceptual areas — version mismatch vs. "2024" flagged |
| 3 | Silo/Pool/Bridge models | WebSearch | ✅ Confirmed, bridge model canonical URL captured |
| 4 | Service-capability claims (§2) | Not re-fetched this session | ⚠️ IRRESOLVABLE without further fetches — marked 🟡; requires targeted WebFetch per URL before publishing |
| 5 | Cross-cloud equivalences (§5) | Not source-verified | ⚠️ Marked orientation-only; human/vendor-doc verification required |

---

## 8. Next Steps
1. Run targeted WebFetch on each 🟡 URL in §6 to promote §2 patterns and §5 map to verified status (`/cloud-architecture-researcher` gap-loop).
2. Run `/skill-best-practices-validator` on this file before it feeds `/skill-creator`.
3. Resolve the SaaS-Lens-vs-6-pillar Sustainability gap by checking for any SaaS Lens revision post-2023 (`document-revisions.md`).
