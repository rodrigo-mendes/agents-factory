# Ask-First Decisions — AWS Well-Architected Framework

> Source: AWS WAF research file `research_aws_waf_2025.md`, accessed 2026-07-31.
> Framework edition: November 6, 2024 (current stable).

These 5 architectural crossroads have multiple valid answers. Confirm workload context
(SLA, team maturity, budget, data gravity, traffic pattern) before choosing.

---

## AF-1 — Compute model: Serverless vs. Containers vs. VMs

**Confirm before deciding**: traffic pattern (spiky vs. sustained), max runtime duration, team ops maturity, runtime requirements, and whether the workload is interruptible.

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| **AWS Lambda** (serverless) | Ops burden, scale-to-zero, cost at spiky/low traffic | Long-running/stateful work, cold starts, max runtime (15 min) | Event-driven APIs, glue code, unpredictable/bursty traffic |
| **Amazon ECS on AWS Fargate** | No node management, per-task isolation | Fine-grained node tuning, some cost vs. EC2 at steady high load | Containerized services wanting serverless containers |
| **Amazon EKS** | Kubernetes portability, ecosystem | Operational complexity, control-plane + ops skill cost | Multi-cloud/K8s standardization, complex orchestration |
| **Amazon EC2 Auto Scaling** | Full control, cheapest at sustained high utilization (with Savings Plans) | Highest ops burden (patching, AMIs, scaling) | Steady high-throughput, specialized instances (GPU), licensing constraints |

**Decision dimensions**:
- **Cost profile**: Lambda = per-request/GB-s (cheapest at low/spiky); Fargate = per vCPU/GB-hour; EC2 = per instance-hour (cheapest at sustained load with Savings Plans / Reserved Instances)
- **Scaling**: Lambda scales per-request automatically; Fargate/ECS/EKS scale tasks/pods; EC2 scales instances via EC2 Auto Scaling
- **Operational burden**: Lambda < Fargate < EKS ≈ EC2
- **Lock-in**: Lambda (high — event model/runtime specifics); Fargate (medium — OCI images portable); EKS (low — standard Kubernetes); EC2 (low — standard VMs)

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/design-principles.html — accessed 2026-07-31

---

## AF-2 — Primary datastore: Relational vs. NoSQL

**Confirm before deciding**: access patterns (ad-hoc queries vs. known key patterns), consistency requirements (strong vs. eventual), expected RPS/scale, and schema stability.

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| **Amazon Aurora** (MySQL/PostgreSQL) | Strong consistency, complex joins/transactions, familiar SQL | Horizontal write scaling beyond a point, per-hour cost | Relational domains, reporting, transactional integrity |
| **Amazon RDS** (Multi-AZ) | Managed standard engines, portability | Aurora's scaling/throughput features | Lift-and-shift of existing SQL engines |
| **Amazon DynamoDB** | Single-digit ms at any scale, serverless, per-request cost | Ad-hoc queries/joins, requires access-pattern modeling up front | High-scale key-value/document, multi-tenant SaaS with known access patterns |
| **Amazon ElastiCache** (Redis/Valkey) | Sub-ms caching/session store | Durability as a primary store | Caching, session state, leaderboards in front of a datastore |

**Decision dimensions**:
- **Cost profile**: DynamoDB on-demand = per-request (scales to zero at idle); Aurora/RDS = per instance-hour + storage; ElastiCache = per node-hour
- **Scaling**: DynamoDB scales horizontally transparently; Aurora scales reads via replicas (up to 15) + Aurora Serverless v2; RDS scales vertically + read replicas
- **Operational burden**: DynamoDB (lowest); Aurora/RDS (managed but tuning needed); ElastiCache (cluster management)
- **Lock-in**: DynamoDB (high — proprietary API); Aurora (medium — MySQL/PostgreSQL wire-compatible); RDS (low — standard engines); ElastiCache (low — Redis/Valkey compatible)

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/design-principles.html — accessed 2026-07-31

---

## AF-3 — Multi-tenant SaaS isolation: Pool vs. Silo vs. Bridge

**Confirm before deciding**: tenant count, compliance requirements (data residency, SOC 2, HIPAA), per-tenant SLA commitments, and cost envelope per tenant.

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| **Pool** (shared infra, tenant key in data) | Cost efficiency, simplest ops at scale | Blast-radius isolation, noisy-neighbor control | Many small tenants, cost-sensitive SaaS |
| **Silo** (dedicated resources/account per tenant) | Strong isolation, per-tenant compliance | Cost, per-tenant operational overhead | Regulated/enterprise tenants, strict data residency |
| **Bridge** (mixed: shared compute, isolated data) | Balance of cost and isolation | Added routing/tenancy complexity | Tiered SaaS (free pooled, enterprise siloed) |

**Decision dimensions**:
- **Cost profile**: Pool (lowest per-tenant), Silo (highest), Bridge (middle)
- **Scaling**: Pool scales best; Silo scales linearly with tenant count (account limits via AWS Organizations / Control Tower)
- **Operational burden**: Silo highest (per-tenant lifecycle management); Pool lowest; Bridge requires dual operational model
- **Compliance**: Silo = strongest isolation guarantees (separate account boundary); Pool = requires tenant-isolation controls at app layer

> ⚠️ **Partially verified**: Pool/Silo/Bridge terminology sourced from AWS SaaS Lens (ref: https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/saas-lens.html). Deep-verify the SaaS Lens before authoring a SaaS-specific deliverable.

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html — accessed 2026-07-31

---

## AF-4 — Data pipeline: Batch vs. Streaming vs. Serverless ETL

**Confirm before deciding**: latency SLA (batch/near-real-time/real-time streaming), data volume, schema evolution needs, and whether replayability/ordering is required.

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| **AWS Glue** (serverless Spark ETL) | Managed ETL, catalog integration, no cluster management | Real-time latency | Scheduled/batch transforms, data-lake curation |
| **Amazon Kinesis Data Streams** | Real-time ingestion, ordering, replay, AWS-native | AWS API lock-in, shard management | Event streaming, near-real-time analytics, AWS-centric |
| **Amazon Managed Streaming for Apache Kafka (MSK)** | Kafka compatibility, OSS ecosystem | Broker management overhead | Event streaming with Kafka ecosystem requirements |
| **Amazon EMR** | Big-data frameworks (Spark/Hadoop/Presto), tuning control | Ops overhead vs. serverless | Large-scale custom big-data processing |
| **AWS Lambda + Amazon S3 events** | Simple event-driven per-object transforms | Heavy/stateful processing, large payloads | Lightweight, per-object transformations |

**Decision dimensions**:
- **Cost profile**: Glue = per DPU-hour; Kinesis = per shard-hour/throughput; MSK = per broker-hour; EMR = per instance-hour; Lambda = per-invocation
- **Scaling**: Kinesis scales via shards / on-demand; Glue auto-scales DPUs; EMR scales cluster nodes
- **Operational burden**: Lambda/Glue lowest; MSK/EMR highest
- **Lock-in**: MSK (low — Apache Kafka compatible); Kinesis (high — AWS API); Glue (medium — Spark portable, catalog proprietary); EMR (low — OSS frameworks)

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/design-principles.html — accessed 2026-07-31

---

## AF-5 — Purchasing model: On-Demand vs. Savings Plans vs. Spot

**Confirm before deciding**: baseline vs. burst traffic profile, workload fault-tolerance (can instances be interrupted?), and planning horizon (1-yr vs. 3-yr commitment confidence).

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| **On-Demand** | Flexibility, no commitment | Highest unit price | Unpredictable/short-lived workloads, initial launch |
| **Compute Savings Plans / Reserved Instances** | Up to ~72% discount for 1-3 yr commitment | Flexibility, requires accurate capacity forecast | Steady-state baseline capacity with predictable load |
| **Amazon EC2 Spot Instances** | Up to ~90% discount | Can be interrupted (2-min notice) | Fault-tolerant, stateless, batch, and interruptible workloads |

**Decision dimensions**:
- **Cost profile**: Spot < Savings Plans/RI < On-Demand
- **Blend strategy**: EC2 Auto Scaling mixed-instances policy — baseline on Savings Plans/RI, burst on Spot, overflow on On-Demand
- **Operational burden**: Spot requires interruption handling (use Spot Instance Advisor + graceful drain); Savings Plans require commitment tracking
- **Lock-in**: Financial commitment (1-3 yr) only — no technical lock-in

> ⚠️ **Verify before quoting**: "up to ~72%" (Savings Plans) and "up to ~90%" (Spot) are AWS's commonly published maxima. Exact figures vary by instance type/term/Region — verify on current AWS pricing pages before a customer deliverable.

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/design-principles.html — accessed 2026-07-31
