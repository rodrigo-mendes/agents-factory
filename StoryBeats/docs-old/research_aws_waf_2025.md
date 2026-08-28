# Research — AWS Well-Architected Framework (AWS WAF 2025)

> **Cloud architecture knowledge base — hallucination-proof, version-absolute.**
> Produced by `framework-researcher` following workflow P0–P5.

## Version Context (Version Absolutism)

| Attribute | Value |
|---|---|
| **Cloud provider** | AWS |
| **Architecture domain** | Well-Architected Framework (WAF) |
| **Target edition** | AWS Well-Architected Framework — **publication date November 6, 2024** (current stable at access date) |
| **Architecture context** | General-purpose production workloads: multi-tenant SaaS, web APIs, data pipelines |
| **Primary audience** | Cloud Architects and Tech Leads |
| **Pillars** | 6 — Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, Sustainability |
| **Primary source of truth** | https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html |
| **Access date (all sources)** | **2026-07-31** |

> ⚠️ **Source-age note.** The Framework whitepaper carries **publication date November 6, 2024** (verified on the official `welcome.html` page). At the 2026-07-31 access date this is ~20 months old, which exceeds the 12-month freshness bar. It is **retained** under the explicit exception in the Source Hierarchy rule — *"reject sources > 12 months old **unless they are the current stable**."* The `.../latest/...` URLs resolve to this edition, confirming it is the current stable revision. Re-verify against the [Document revisions](https://docs.aws.amazon.com/wellarchitected/latest/framework/document-revisions.html) page before reuse.
>
> **Sustainability** was added as the 6th pillar in the December 2021 revision and remains part of the current edition; treat any 5-pillar guidance (pre-Dec 2021) as **outdated / misinformation** for AWS WAF 2025.

---

## 1. Framework Pillars

The AWS Well-Architected Framework is built on **six pillars**. Official pillar definitions (Table 1, *Definitions* page) and the official **design principles** for each pillar are reproduced below, each grounded in a dated official source.

### 1.1 Operational Excellence

> **Official definition:** "The ability to support development and run workloads effectively, gain insight into their operations, and to continuously improve supporting processes and procedures to deliver business value." — *Definitions*, AWS WAF (Nov 6, 2024).

**Design principles (verbatim, official):**
1. **Organize teams around business outcomes** — a business-aligned operating model with leadership investment in a CloudOps transformation; goals and operational KPIs aligned at all levels.
2. **Implement observability for actionable insights** — establish KPIs and use observability telemetry to decide and act when business outcomes are at risk.
3. **Safely automate where possible** — define workload and operations as code; apply automation safety via guardrails (rate control, error thresholds, approvals).
4. **Make frequent, small, reversible changes** — scalable, loosely coupled workloads; smaller incremental changes reduce blast radius and speed reversal.
5. **Refine operations procedures frequently** — evolve operations as workloads evolve; hold regular reviews and validate procedures.
6. **Anticipate failure** — drive failure scenarios to understand risk profile; test procedures and team response against simulated failures.
7. **Learn from all operational events and metrics** — drive improvement through lessons learned; share across the organization.
8. **Use managed services** — reduce operational burden by using AWS managed services where possible.

**Source:** https://docs.aws.amazon.com/wellarchitected/latest/framework/oe-design-principles.html — accessed 2026-07-31.

### 1.2 Security

> **Official definition:** "The security pillar describes how to take advantage of cloud technologies to protect data, systems, and assets in a way that can improve your security posture." — *Definitions*, AWS WAF (Nov 6, 2024).

**Design principles (verbatim, official):**
1. **Implement a strong identity foundation** — least privilege, separation of duties, centralize identity management, eliminate reliance on long-term static credentials.
2. **Maintain traceability** — monitor, alert, and audit actions/changes in real time; integrate log and metric collection to auto-investigate and act.
3. **Apply security at all layers** — defense in depth with multiple controls (edge, VPC, load balancing, every instance/compute service, OS, application, code).
4. **Automate security best practices** — software-based security mechanisms defined and managed as code in version-controlled templates.
5. **Protect data in transit and at rest** — classify data by sensitivity; use encryption, tokenization, and access control.
6. **Keep people away from data** — reduce or eliminate direct access or manual processing of data.
7. **Prepare for security events** — incident management/investigation policy and processes; run response simulations; use automation for detection, investigation, recovery.

**Source:** https://docs.aws.amazon.com/wellarchitected/latest/framework/sec-design.html — accessed 2026-07-31.

### 1.3 Reliability

> **Official definition:** "The reliability pillar encompasses the ability of a workload to perform its intended function correctly and consistently when it's expected to. This includes the ability to operate and test the workload through its total lifecycle." — *Definitions*, AWS WAF (Nov 6, 2024).

**Design principles (verbatim, official):**
1. **Automatically recover from failure** — monitor KPIs (business value, not just technical), run automation when thresholds are breached; anticipate and remediate before failures occur.
2. **Test recovery procedures** — use automation to simulate failures and validate recovery paths *before* real failures.
3. **Scale horizontally to increase aggregate workload availability** — replace one large resource with multiple small ones; avoid a common point of failure.
4. **Stop guessing capacity** — monitor demand/utilization and automate adding/removing resources; manage service quotas and constraints.
5. **Manage change through automation** — infrastructure changes made via automation, tracked and reviewed.

**Source:** https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/design-principles.html — accessed 2026-07-31.

### 1.4 Performance Efficiency

> **Official definition:** "The ability to use computing resources efficiently to meet system requirements, and to maintain that efficiency as demand changes and technologies evolve." — *Definitions*, AWS WAF (Nov 6, 2024).

**Design principles (verbatim, official):**
1. **Democratize advanced technologies** — consume complex technologies (NoSQL, media transcoding, ML) as a service rather than self-hosting.
2. **Go global in minutes** — deploy across multiple AWS Regions for lower latency at minimal cost.
3. **Use serverless architectures** — remove the need to run/maintain physical servers for compute activities.
4. **Experiment more often** — run comparative testing across instance types, storage, configurations.
5. **Consider mechanical sympathy** — choose the technology approach that aligns best with your goals and data access patterns.

**Source:** https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/design-principles.html — accessed 2026-07-31.

### 1.5 Cost Optimization

> **Official definition:** "The ability to run systems to deliver business value at the lowest price point." — *Definitions*, AWS WAF (Nov 6, 2024).

**Design principles (verbatim, official):**
1. **Implement Cloud Financial Management** — invest in capability (knowledge, programs, resources, processes) to become a cost-efficient organization.
2. **Adopt a consumption model** — pay only for resources consumed; scale with business need (e.g., stop dev/test outside working hours).
3. **Measure overall efficiency** — measure business output vs. cost of delivery.
4. **Stop spending money on undifferentiated heavy lifting** — let AWS manage data center operations and managed services.
5. **Analyze and attribute expenditure** — accurately identify cost/usage; attribute to revenue streams and workload owners.

**Source:** https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/design-principles.html — accessed 2026-07-31.

### 1.6 Sustainability

> **Official definition:** "The ability to continually improve sustainability impacts by reducing energy consumption and increasing efficiency across all components of a workload by maximizing the benefits from the provisioned resources and minimizing the total resources required." — *Definitions*, AWS WAF (Nov 6, 2024).

**Design principles (verbatim, official):**
1. **Understand your impact** — measure and model current/future impact; establish KPIs per unit of work.
2. **Establish sustainability goals** — long-term goals (e.g., reduce compute/storage per transaction); architect so growth reduces impact intensity.
3. **Maximize utilization** — right-size workloads; eliminate/minimize idle resources (two hosts at 30% are less efficient than one at 60%).
4. **Anticipate and adopt new, more efficient hardware and software offerings** — design for flexibility to adopt efficient technologies rapidly.
5. **Use managed services** — share services across a broad customer base to maximize resource utilization (e.g., AWS Fargate, Amazon S3 Lifecycle, Amazon EC2 Auto Scaling).
6. **Reduce the downstream impact of your cloud workloads** — reduce energy/resources customers need to use your services.

**Source:** https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/design-principles-for-sustainability-in-the-cloud.html — accessed 2026-07-31.

---

## 2. Always-Do Patterns

Mandatory architecture standards for AWS production workloads (multi-tenant SaaS, web APIs, data pipelines). Each pattern uses **exact AWS service names** and aligns to one or more pillars.

### AD-1 — Centralize identity and eliminate long-term static credentials

| Field | Detail |
|---|---|
| **Why (pillar)** | Security — "Implement a strong identity foundation" design principle. |
| **AWS services** | **AWS IAM Identity Center** (workforce SSO), **IAM roles** + **IAM Roles Anywhere**, **Amazon Cognito** (application end-users), **AWS Security Token Service (AWS STS)** for temporary credentials. |
| **Architecture decision** | Human access via IAM Identity Center federation; workload access via **IAM roles** (instance profiles, IRSA on **Amazon EKS**, task roles on **Amazon ECS**). Never embed IAM user access keys in code or AMIs. |
| **Verification** | `aws iam list-users` should show near-zero long-lived users; **IAM Access Analyzer** unused-access findings = 0; **AWS Config** rule `iam-user-no-policies-check` / `access-keys-rotated` compliant. |
| **Trade-offs** | Federation setup adds initial complexity and an IdP dependency; temporary credentials require SDK/role-assumption plumbing. |
| **Source** | https://docs.aws.amazon.com/wellarchitected/latest/framework/sec-design.html — accessed 2026-07-31 |

### AD-2 — Encrypt data at rest and in transit by default

| Field | Detail |
|---|---|
| **Why (pillar)** | Security — "Protect data in transit and at rest". |
| **AWS services** | **AWS KMS** (customer-managed keys), **Amazon S3** default encryption (SSE-KMS), **Amazon RDS**/**Amazon Aurora** storage encryption, **Amazon EBS** encryption-by-default, **AWS Certificate Manager (ACM)** for TLS, **Amazon DynamoDB** encryption at rest. |
| **Architecture decision** | Enable account-level EBS encryption-by-default and S3 default encryption; terminate TLS at **Elastic Load Balancing (ALB/NLB)** or **Amazon CloudFront** with ACM certificates; enforce TLS ≥ 1.2. |
| **Verification** | AWS Config rules `encrypted-volumes`, `s3-bucket-server-side-encryption-enabled`, `rds-storage-encrypted` compliant; ELB security policy = `ELBSecurityPolicy-TLS13-*`. |
| **Trade-offs** | KMS request costs and key-management overhead; envelope encryption adds minor latency. |
| **Source** | https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html — accessed 2026-07-31 |

### AD-3 — Design for Multi-AZ high availability

| Field | Detail |
|---|---|
| **Why (pillar)** | Reliability — "Scale horizontally to increase aggregate workload availability". |
| **AWS services** | **Amazon RDS Multi-AZ** (or **Amazon Aurora** with multiple Availability Zones), **Amazon EC2 Auto Scaling** across ≥ 2 AZs, **Elastic Load Balancing**, **Amazon EKS**/**Amazon ECS** across AZs, **Amazon S3** (11 9s durability, multi-AZ by design). |
| **Architecture decision** | Deploy every stateful and stateless tier across at least two (preferably three) Availability Zones in a Region; use **Amazon RDS Multi-AZ** for automatic failover of the database tier. |
| **Verification** | RDS instance `MultiAZ = true`; Auto Scaling group spans ≥ 2 subnets in distinct AZs; run a failover game day (reboot-with-failover) and confirm recovery within RTO. |
| **Trade-offs** | Multi-AZ roughly doubles standby compute/storage cost for RDS; cross-AZ data transfer charges apply. |
| **Source** | https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/design-principles.html — accessed 2026-07-31 |

### AD-4 — Manage infrastructure and operations as code

| Field | Detail |
|---|---|
| **Why (pillar)** | Operational Excellence — "Safely automate where possible"; Security — "Automate security best practices". |
| **AWS services** | **AWS CloudFormation** / **AWS CDK**, **AWS Systems Manager** (patching, runbooks/Automation documents), **AWS CodePipeline** + **AWS CodeBuild**, **AWS Config** for drift/compliance. |
| **Architecture decision** | All infrastructure defined in version-controlled templates; changes flow through CI/CD with automated tests; no console ("ClickOps") changes in production. |
| **Verification** | CloudFormation drift detection reports no drift; every prod change traces to a merged commit + pipeline execution; AWS Config timeline shows IaC-driven changes only. |
| **Trade-offs** | Upfront authoring effort and a learning curve; emergency break-glass paths must be governed and audited. |
| **Source** | https://docs.aws.amazon.com/wellarchitected/latest/framework/oe-design-principles.html — accessed 2026-07-31 |

### AD-5 — Implement observability (metrics, logs, traces) with actionable alarms

| Field | Detail |
|---|---|
| **Why (pillar)** | Operational Excellence — "Implement observability for actionable insights". |
| **AWS services** | **Amazon CloudWatch** (metrics, Logs, alarms, dashboards), **AWS X-Ray** (distributed tracing), **Amazon Managed Service for Prometheus** + **Amazon Managed Grafana** (containerized workloads), **AWS CloudTrail** (API audit). |
| **Architecture decision** | Emit structured logs to **Amazon CloudWatch Logs**; define business-KPI alarms (not just CPU); enable **AWS X-Ray** tracing across API → service → data tiers. |
| **Verification** | Each critical user journey has ≥ 1 CloudWatch alarm tied to a KPI; CloudTrail enabled in all Regions with log-file validation; alarms route to a notification/on-call path (e.g., Amazon SNS → incident tool). |
| **Trade-offs** | Log ingestion/retention and custom-metric costs grow with volume; high-cardinality metrics need budgeting. |
| **Source** | https://docs.aws.amazon.com/wellarchitected/latest/framework/oe-design-principles.html — accessed 2026-07-31 |

### AD-6 — Store secrets in a managed secrets service, not in code or environment files

| Field | Detail |
|---|---|
| **Why (pillar)** | Security — "Keep people away from data" + "Implement a strong identity foundation". |
| **AWS services** | **AWS Secrets Manager** (with automatic rotation), **AWS Systems Manager Parameter Store** (SecureString) for lower-sensitivity config, **AWS KMS** for encryption. |
| **Architecture decision** | Applications fetch secrets at runtime via IAM-scoped calls to **AWS Secrets Manager**; enable automatic rotation for database credentials; never commit secrets to Git or bake into container images. |
| **Verification** | Secret scanning (e.g., in CodeBuild/GitHub) shows no committed secrets; Secrets Manager rotation `RotationEnabled = true` on DB secrets; IAM policies scope `secretsmanager:GetSecretValue` to specific ARNs. |
| **Trade-offs** | Secrets Manager per-secret monthly cost + API calls; rotation Lambda functions add maintenance (Parameter Store is cheaper but lacks native rotation). |
| **Source** | https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html — accessed 2026-07-31 |

### AD-7 — Establish multi-account governance and guardrails

| Field | Detail |
|---|---|
| **Why (pillar)** | Security + Operational Excellence — separation of duties, blast-radius isolation. |
| **AWS services** | **AWS Organizations** (with **Service Control Policies**), **AWS Control Tower**, **AWS IAM Identity Center**, **AWS CloudTrail** organization trail, centralized **Amazon S3** log archive account. |
| **Architecture decision** | Separate accounts per environment (prod/non-prod) and per workload; enforce guardrails with **Service Control Policies**; centralize logging and security tooling in dedicated accounts. |
| **Verification** | SCPs deny disabling CloudTrail/GuardDuty; Control Tower shows no non-compliant accounts; each production workload isolated in its own account/OU. |
| **Trade-offs** | Cross-account networking and IAM complexity; more accounts to operate (offset by Control Tower automation). |
| **Source** | https://docs.aws.amazon.com/wellarchitected/latest/framework/sec-design.html — accessed 2026-07-31 |

### AD-8 — Set budgets, cost allocation tags, and right-sizing reviews

| Field | Detail |
|---|---|
| **Why (pillar)** | Cost Optimization — "Analyze and attribute expenditure"; Sustainability — "Maximize utilization". |
| **AWS services** | **AWS Budgets**, **AWS Cost Explorer**, **AWS Cost and Usage Report (CUR)**, **AWS Compute Optimizer**, **AWS Trusted Advisor**, cost-allocation tags. |
| **Architecture decision** | Apply mandatory cost-allocation tags (owner, environment, workload); create **AWS Budgets** alerts per account/workload; review **AWS Compute Optimizer** recommendations quarterly and right-size. |
| **Verification** | > 95% of spend covered by cost-allocation tags; each account has an active AWS Budget with alert thresholds; Compute Optimizer over-provisioned findings actioned. |
| **Trade-offs** | Tagging discipline requires enforcement (tag policies); right-sizing needs performance validation before applying. |
| **Source** | https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/design-principles.html — accessed 2026-07-31 |

---

## 3. Ask-First Decisions

Architectural crossroads with multiple valid answers. Confirm the workload's context (SLA, team maturity, budget, data gravity) before choosing.

### AF-1 — Compute model: Serverless vs. Containers vs. VMs

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| **AWS Lambda** (serverless) | Ops burden, scale-to-zero, cost at spiky/low traffic | Long-running/stateful work, cold starts, max runtime (15 min) | Event-driven APIs, glue code, unpredictable/bursty traffic |
| **Amazon ECS on AWS Fargate** | No node management, per-task isolation | Fine-grained node tuning, some cost vs. EC2 at steady high load | Containerized services wanting serverless containers |
| **Amazon EKS** | Kubernetes portability, ecosystem | Operational complexity, control-plane + ops skill cost | Multi-cloud/K8s standardization, complex orchestration |
| **Amazon EC2 Auto Scaling** | Full control, cheapest at sustained high utilization (with Savings Plans) | Highest ops burden (patching, AMIs, scaling) | Steady high-throughput, specialized instances (GPU), licensing constraints |

- **Cost profile:** Lambda = per-request/GB-s (cheapest at low/spiky); Fargate = per vCPU/GB-hour; EC2 = per instance-hour (cheapest at sustained load with **Savings Plans**/Reserved).
- **Scaling characteristics:** Lambda scales per-request automatically; Fargate/ECS/EKS scale tasks/pods; EC2 scales instances via **EC2 Auto Scaling**.
- **Operational burden:** Lambda < Fargate < EKS ≈ EC2.
- **Lock-in assessment:** Lambda (high — event model/runtime specifics); Fargate (medium — task defs, but OCI images portable); EKS (low — standard Kubernetes); EC2 (low — standard VMs).
- **Source:** https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/design-principles.html — accessed 2026-07-31

### AF-2 — Primary datastore: Relational vs. NoSQL

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| **Amazon Aurora** (MySQL/PostgreSQL) | Strong consistency, complex joins/transactions, familiar SQL | Horizontal write scaling beyond a point, per-hour cost | Relational domains, reporting, transactional integrity |
| **Amazon RDS** (Multi-AZ) | Managed standard engines, portability | Aurora's scaling/throughput features | Lift-and-shift of existing SQL engines |
| **Amazon DynamoDB** | Single-digit ms at any scale, serverless, per-request cost | Ad-hoc queries/joins, requires access-pattern modeling | High-scale key-value/document, multi-tenant SaaS with known access patterns |
| **Amazon ElastiCache** (Redis/Valkey) | Sub-ms caching/session store | Durability as a primary store | Caching, session state, leaderboards in front of a datastore |

- **Cost profile:** DynamoDB on-demand = per-request (scales to zero cost at idle); Aurora/RDS = per instance-hour + storage; ElastiCache = per node-hour.
- **Scaling characteristics:** DynamoDB scales horizontally transparently; Aurora scales reads via replicas (up to 15) and **Aurora Serverless v2** for capacity; RDS scales vertically + read replicas.
- **Operational burden:** DynamoDB (lowest); Aurora/RDS (managed but tuning needed); ElastiCache (cluster management).
- **Lock-in assessment:** DynamoDB (high — proprietary API); Aurora (medium — wire-compatible with MySQL/PostgreSQL); RDS (low — standard engines); ElastiCache (low — Redis/Valkey compatible).
- **Source:** https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/design-principles.html — accessed 2026-07-31

### AF-3 — Multi-tenant SaaS isolation: Pool vs. Silo vs. Bridge

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| **Pool** (shared infra, tenant key in data) | Cost efficiency, simplest ops at scale | Blast-radius isolation, noisy-neighbor control | Many small tenants, cost-sensitive SaaS |
| **Silo** (dedicated resources/account per tenant) | Strong isolation, per-tenant compliance | Cost, per-tenant operational overhead | Regulated/enterprise tenants, strict data residency |
| **Bridge** (mixed: shared compute, isolated data) | Balance of cost and isolation | Added routing/tenancy complexity | Tiered SaaS (free pooled, enterprise siloed) |

- **Cost profile:** Pool (lowest per-tenant), Silo (highest), Bridge (middle).
- **Scaling characteristics:** Pool scales best; Silo scales linearly with tenant count (account limits via **AWS Organizations**).
- **Operational burden:** Silo highest (per-tenant lifecycle); Pool lowest.
- **Lock-in assessment:** Architectural, not vendor — but **AWS Organizations**/**Control Tower** simplify Silo.
- **Source:** https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html — accessed 2026-07-31 (isolation guidance detailed in AWS SaaS Lens; see bibliography)

### AF-4 — Data pipeline: Batch vs. Streaming vs. Serverless ETL

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| **AWS Glue** (serverless Spark ETL) | Managed ETL, catalog integration | Real-time latency | Scheduled/batch transforms, data-lake curation |
| **Amazon Kinesis Data Streams** / **Amazon Managed Streaming for Apache Kafka (MSK)** | Real-time ingestion, ordering, replay | Operational/model complexity | Event streaming, near-real-time analytics |
| **Amazon EMR** | Big-data frameworks (Spark/Hadoop/Presto), tuning control | Ops overhead vs. serverless | Large-scale custom big-data processing |
| **AWS Lambda + Amazon S3 events** | Simple event-driven transforms | Heavy/stateful processing | Lightweight, per-object transformations |

- **Cost profile:** Glue = per DPU-hour; Kinesis = per shard-hour/throughput; MSK = per broker-hour; EMR = per instance-hour; Lambda = per-invocation.
- **Scaling characteristics:** Kinesis scales via shards / on-demand; Glue auto-scales DPUs; EMR scales cluster nodes.
- **Operational burden:** Lambda/Glue lowest; MSK/EMR highest.
- **Lock-in assessment:** MSK (low — Apache Kafka compatible); Kinesis (high — AWS API); Glue (medium — Spark portable, catalog proprietary); EMR (low — OSS frameworks).
- **Source:** https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/design-principles.html — accessed 2026-07-31

### AF-5 — Purchasing model: On-Demand vs. Savings Plans vs. Spot

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| **On-Demand** | Flexibility, no commitment | Highest unit price | Unpredictable/short-lived workloads |
| **Compute Savings Plans / Reserved Instances** | Up to ~72% discount for 1–3 yr commit | Flexibility, requires forecast | Steady-state baseline capacity |
| **Amazon EC2 Spot Instances** | Up to ~90% discount | Can be interrupted (2-min notice) | Fault-tolerant, stateless, batch, and interruptible workloads |

- **Cost profile:** Spot < Savings Plans/RI < On-Demand.
- **Scaling characteristics:** Blend via **EC2 Auto Scaling** mixed-instances (baseline on Savings Plans, burst on Spot).
- **Operational burden:** Spot requires interruption handling; Savings Plans require commitment tracking.
- **Lock-in assessment:** Financial commitment (1–3 yr), not technical.
- **Source:** https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/design-principles.html — accessed 2026-07-31

---

## 4. Never-Do Anti-Patterns

Each entry has side-by-side ❌ Wrong / ✅ Correct using exact AWS service names.

### ND-1 — Long-lived IAM user access keys in application code

- **Risk level:** Critical · **Blast radius:** Account-wide (leaked key = full API access within its policy)
- **Detection:** **IAM Access Analyzer**, **AWS Config** `access-keys-rotated`, secret scanners, **Amazon GuardDuty** `UnauthorizedAccess` findings.
- **Impact:** Credential leakage → data exfiltration, resource hijacking (e.g., crypto-mining), no automatic rotation.

```text
❌ Wrong
  App config: AWS_ACCESS_KEY_ID=AKIA...  AWS_SECRET_ACCESS_KEY=...
  (IAM user access key committed / baked into AMI or container image)

✅ Correct
  Attach an IAM role to the compute (EC2 instance profile / ECS task role /
  EKS IRSA). SDK obtains temporary credentials via AWS STS automatically.
  Secrets (DB creds) retrieved at runtime from AWS Secrets Manager.
```
- **Source:** https://docs.aws.amazon.com/wellarchitected/latest/framework/sec-design.html — accessed 2026-07-31

### ND-2 — Single-AZ production deployment / single point of failure

- **Risk level:** High · **Blast radius:** Entire workload (one AZ event = full outage)
- **Detection:** **AWS Trusted Advisor** fault-tolerance checks; architecture review; RDS `MultiAZ = false`.
- **Impact:** AZ impairment causes total downtime; violates the Reliability "scale horizontally" principle.

```text
❌ Wrong
  Amazon RDS single-AZ + one Amazon EC2 instance in one subnet/AZ.

✅ Correct
  Amazon RDS Multi-AZ (or Amazon Aurora across 3 AZs) +
  Amazon EC2 Auto Scaling across >=2 AZs behind Elastic Load Balancing.
```
- **Source:** https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/design-principles.html — accessed 2026-07-31

### ND-3 — Public S3 bucket / overly permissive access

- **Risk level:** Critical · **Blast radius:** All objects in the bucket (potential mass data breach)
- **Detection:** **Amazon S3 Block Public Access** status, **AWS Config** `s3-bucket-public-read-prohibited`, **IAM Access Analyzer** external-access findings, **Amazon Macie** for sensitive data.
- **Impact:** Public exposure of PII/customer data; a leading cause of cloud data breaches.

```text
❌ Wrong
  S3 bucket with Block Public Access disabled and a bucket policy
  granting Principal "*" s3:GetObject.

✅ Correct
  Enable S3 Block Public Access (account + bucket). Serve public content
  via Amazon CloudFront with Origin Access Control. Scope bucket policies
  to specific IAM principals; encrypt with SSE-KMS.
```
- **Source:** https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html — accessed 2026-07-31

### ND-4 — Unencrypted data at rest / in transit

- **Risk level:** High · **Blast radius:** All data in the affected store
- **Detection:** **AWS Config** `encrypted-volumes`, `rds-storage-encrypted`, `s3-bucket-server-side-encryption-enabled`; ELB listener TLS policy audit.
- **Impact:** Data readable if storage/media compromised; compliance failures (PCI DSS, HIPAA, GDPR).

```text
❌ Wrong
  Amazon EBS volume unencrypted; ALB listener on HTTP :80 only;
  Amazon RDS with StorageEncrypted=false.

✅ Correct
  EBS encryption-by-default with AWS KMS; ALB HTTPS listener with an
  AWS Certificate Manager cert (redirect 80->443); RDS StorageEncrypted=true.
```
- **Source:** https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html — accessed 2026-07-31

### ND-5 — Manual "ClickOps" changes in production

- **Risk level:** Medium-High · **Blast radius:** Any resource changed out-of-band
- **Detection:** **AWS CloudFormation** drift detection; **AWS Config** change timeline; **AWS CloudTrail** console-origin events.
- **Impact:** Configuration drift, non-reproducible environments, failed disaster recovery, undocumented changes.

```text
❌ Wrong
  Operator edits a security group / scales RDS in the AWS Console
  directly in production, bypassing IaC.

✅ Correct
  Change the AWS CloudFormation / AWS CDK template, PR review, deploy via
  AWS CodePipeline. Governed break-glass role for emergencies, fully
  logged in AWS CloudTrail and reconciled back into IaC.
```
- **Source:** https://docs.aws.amazon.com/wellarchitected/latest/framework/oe-design-principles.html — accessed 2026-07-31

### ND-6 — No cost guardrails (untagged, unbudgeted spend)

- **Risk level:** Medium (business) · **Blast radius:** Account/organization billing
- **Detection:** **AWS Cost Explorer** anomaly detection, **AWS Budgets** alerts absent, tag-coverage report.
- **Impact:** Runaway spend, no cost attribution, undetected idle/over-provisioned resources; violates Cost Optimization + Sustainability.

```text
❌ Wrong
  No AWS Budgets, no cost-allocation tags, oversized always-on
  Amazon EC2 instances in dev running 24/7.

✅ Correct
  Mandatory cost-allocation tags (tag policies via AWS Organizations),
  AWS Budgets alerts per account, AWS Instance Scheduler to stop dev
  out-of-hours, quarterly AWS Compute Optimizer right-sizing.
```
- **Source:** https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/design-principles.html — accessed 2026-07-31

### ND-7 — Disabling or not centralizing audit logging

- **Risk level:** High · **Blast radius:** Whole account/organization (loss of forensic capability)
- **Detection:** **AWS CloudTrail** status, **AWS Security Hub** foundational checks, SCP presence preventing CloudTrail disable.
- **Impact:** No traceability of API actions; breach investigations impossible; violates Security "Maintain traceability".

```text
❌ Wrong
  AWS CloudTrail disabled or per-account only, logs in the same account
  they audit, no log-file validation.

✅ Correct
  AWS Organizations organization trail -> centralized, immutable Amazon S3
  log-archive account (Object Lock), log-file validation on, monitored by
  Amazon GuardDuty and AWS Security Hub. SCP denies disabling CloudTrail.
```
- **Source:** https://docs.aws.amazon.com/wellarchitected/latest/framework/sec-design.html — accessed 2026-07-31

---

## 5. Service Equivalence Map (AWS → GCP / Azure / OCI)

> Cross-cloud equivalents for the service classes referenced above. Equivalences are approximate (feature parity varies); AWS names are authoritative for this knowledge base.

| Service class | AWS | Google Cloud (GCP) | Microsoft Azure | Oracle Cloud (OCI) |
|---|---|---|---|---|
| Serverless functions | AWS Lambda | Cloud Functions / Cloud Run functions | Azure Functions | OCI Functions |
| Serverless containers | AWS Fargate (ECS/EKS) | Cloud Run | Azure Container Apps / ACI | OCI Container Instances |
| Managed Kubernetes | Amazon EKS | Google Kubernetes Engine (GKE) | Azure Kubernetes Service (AKS) | OKE (Container Engine for Kubernetes) |
| Virtual machines / autoscale | Amazon EC2 + EC2 Auto Scaling | Compute Engine + MIGs | Azure Virtual Machines + VMSS | OCI Compute + Instance Pools |
| Object storage | Amazon S3 | Cloud Storage | Azure Blob Storage | OCI Object Storage |
| Block storage | Amazon EBS | Persistent Disk / Hyperdisk | Azure Managed Disks | OCI Block Volume |
| Relational (managed) | Amazon RDS / Amazon Aurora | Cloud SQL / AlloyDB / Spanner | Azure SQL Database / Azure Database for PostgreSQL/MySQL | OCI Autonomous Database / MySQL HeatWave |
| NoSQL key-value/document | Amazon DynamoDB | Firestore / Bigtable | Azure Cosmos DB | OCI NoSQL Database |
| In-memory cache | Amazon ElastiCache (Redis/Valkey) | Memorystore | Azure Cache for Redis | OCI Cache (Redis) |
| Load balancing | Elastic Load Balancing (ALB/NLB) | Cloud Load Balancing | Azure Load Balancer / Application Gateway | OCI Load Balancer |
| CDN | Amazon CloudFront | Cloud CDN | Azure Front Door / CDN | OCI CDN |
| Identity / IAM | AWS IAM + IAM Identity Center | Cloud IAM | Microsoft Entra ID | OCI IAM |
| App end-user identity | Amazon Cognito | Identity Platform / Firebase Auth | Azure AD B2C (Entra External ID) | OCI IAM Identity Domains |
| Key management | AWS KMS | Cloud KMS | Azure Key Vault | OCI Vault / KMS |
| Secrets management | AWS Secrets Manager | Secret Manager | Azure Key Vault (secrets) | OCI Vault (secrets) |
| Monitoring / logs | Amazon CloudWatch | Cloud Monitoring / Cloud Logging | Azure Monitor | OCI Observability & Monitoring / Logging |
| Distributed tracing | AWS X-Ray | Cloud Trace | Azure Monitor Application Insights | OCI APM |
| API audit log | AWS CloudTrail | Cloud Audit Logs | Azure Monitor Activity Log | OCI Audit |
| IaC (first-party) | AWS CloudFormation / AWS CDK | Cloud Deployment Manager / Config Controller | Azure Resource Manager / Bicep | OCI Resource Manager |
| Streaming | Amazon Kinesis / Amazon MSK | Pub/Sub / Managed Service for Kafka | Azure Event Hubs | OCI Streaming |
| ETL / big data | AWS Glue / Amazon EMR | Dataflow / Dataproc | Azure Data Factory / Synapse / HDInsight | OCI Data Integration / Big Data Service |
| Multi-account governance | AWS Organizations / AWS Control Tower | Resource Manager (folders/orgs) | Azure Management Groups / Landing Zones | OCI Compartments / Tenancy |
| Threat detection | Amazon GuardDuty | Security Command Center | Microsoft Defender for Cloud | OCI Cloud Guard |
| Security posture (CSPM) | AWS Security Hub | Security Command Center | Microsoft Defender for Cloud | OCI Cloud Guard / Security Zones |
| Cost management | AWS Cost Explorer / AWS Budgets | Cloud Billing / FinOps Hub | Microsoft Cost Management | OCI Cost Analysis / Budgets |
| Right-sizing | AWS Compute Optimizer | Recommender | Azure Advisor | OCI Advisor |
| Certificates / TLS | AWS Certificate Manager (ACM) | Certificate Manager | Azure Key Vault certificates | OCI Certificates |

> **Note:** Cross-cloud mappings above are engineering common-knowledge equivalences for architect orientation, **not** claims from the AWS WAF document. Validate specific feature parity against each provider's official documentation before a migration decision.

---

## 6. Source Bibliography

All sources are official AWS documentation (`docs.aws.amazon.com` / `aws.amazon.com`). **Access date for all: 2026-07-31.**

### Primary sources (AWS Well-Architected Framework — publication date November 6, 2024)

| # | Title | URL | Notes |
|---|---|---|---|
| 1 | AWS WAF — Welcome / Introduction | https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html | Publication date **Nov 6, 2024** confirmed on page |
| 2 | AWS WAF — The pillars of the framework | https://docs.aws.amazon.com/wellarchitected/latest/framework/the-pillars-of-the-framework.html | Lists all 6 pillars |
| 3 | AWS WAF — Definitions (pillar definitions, Table 1) | https://docs.aws.amazon.com/wellarchitected/latest/framework/definitions.html | Verbatim pillar definitions |
| 4 | Operational Excellence — Design principles | https://docs.aws.amazon.com/wellarchitected/latest/framework/oe-design-principles.html | 8 principles, verbatim |
| 5 | Security — Design principles | https://docs.aws.amazon.com/wellarchitected/latest/framework/sec-design.html | 7 principles, verbatim |
| 6 | Reliability — Design principles | https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/design-principles.html | 5 principles, verbatim |
| 7 | Performance Efficiency — Design principles | https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/design-principles.html | 5 principles, verbatim |
| 8 | Cost Optimization — Design principles | https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/design-principles.html | 5 principles, verbatim |
| 9 | Sustainability — Design principles for sustainability in the cloud | https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/design-principles-for-sustainability-in-the-cloud.html | 6 principles, verbatim |

### Pillar whitepapers (referenced for Always-Do / Never-Do)

| # | Title | URL |
|---|---|---|
| 10 | Security Pillar — whitepaper home | https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html |
| 11 | Reliability Pillar — whitepaper home | https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html |
| 12 | Operational Excellence Pillar — whitepaper home | https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/welcome.html |
| 13 | Performance Efficiency Pillar — whitepaper home | https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/welcome.html |
| 14 | Cost Optimization Pillar — whitepaper home | https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html |
| 15 | Sustainability Pillar — whitepaper home | https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/sustainability-pillar.html |

### Supporting official references

| # | Title | URL | Notes |
|---|---|---|---|
| 16 | AWS Well-Architected (homepage) | https://aws.amazon.com/architecture/well-architected/ | Program overview, lenses, WA Tool |
| 17 | AWS Well-Architected — Document revisions | https://docs.aws.amazon.com/wellarchitected/latest/framework/document-revisions.html | Verify current revision before reuse |
| 18 | AWS Prescriptive Guidance | https://aws.amazon.com/prescriptive-guidance/ | Patterns, guides, strategies |
| 19 | AWS SaaS Lens (multi-tenant isolation — AF-3) | https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/saas-lens.html | Pool/Silo/Bridge isolation models |

---

## Research Gaps / Unverified Items

- **AF-3 isolation depth (Pool/Silo/Bridge):** The specific Pool/Silo/Bridge tiering terminology is documented in the **AWS SaaS Lens** (ref #19), which was not fetched page-by-page in this pass. Verified conceptually against Framework guidance; deep-verify against the SaaS Lens before authoring a SaaS-specific skill. Marked **partially verified**.
- **Cross-cloud equivalence map (Section 5):** Reflects engineering common knowledge, **not** AWS WAF claims. Treated as orientation only; **unverified** against each non-AWS provider's docs.
- **Discount percentages (AF-5):** "up to ~72%" (Savings Plans) and "up to ~90%" (Spot) are AWS's commonly published maxima; exact figures vary by instance/term/Region — verify on the current AWS pricing pages before quoting in a customer deliverable. Marked **verify-before-quote**.
- **Framework edition age:** Retained the Nov 6, 2024 edition as current stable (see Version Context note). If AWS has published a newer revision after the 2026-07-31 access date, re-run against ref #17.

## Completion Checklist

- [x] P0 meta-skill loaded and confirmed (`researching-technical-frameworks/SKILL.md`).
- [x] All 6 pillars with official definitions + verbatim design principles (dated sources).
- [x] Always-Do patterns (8) with Why/Services/Decision/Verification/Trade-offs/Source.
- [x] Ask-First decisions (5) with options tables, cost/scaling/ops-burden/lock-in.
- [x] Never-Do anti-patterns (7) with side-by-side ❌/✅, Risk/Blast Radius/Detection/Impact/Source.
- [x] Service Equivalence Map (AWS → GCP / Azure / OCI).
- [x] Source Bibliography with URLs + access date (2026-07-31).
- [x] Exact AWS service names used throughout (no generic terms).
- [x] Source-age exception flagged (⚠️) for the Nov 6, 2024 edition.
- [ ] **Recommended next:** run `/skill-best-practices-validator` on any skill authored from this research.
