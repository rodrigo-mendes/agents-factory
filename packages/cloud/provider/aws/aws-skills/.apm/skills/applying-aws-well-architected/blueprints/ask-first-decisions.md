# Ask First Decisions — applying-aws-well-architected

Source: AWS Well-Architected Framework, November 6, 2024 edition (research date 2026-08-27).
Never pick an option below without first asking the stated question.

---

## DEC-1 — DR Strategy Selection

**Ask**: "What is the business cost of 1 hour of downtime and 1 hour of data loss?" (when the RTO/RPO SLA is undefined)

| Option | AWS Services | RTO | RPO | Cost | Best When |
|--------|-------------|-----|-----|------|-----------|
| Backup & Restore | AWS Backup, S3, CloudFormation | Hours–days | Hours | Lowest (~1x) | Non-critical; budget constrained |
| Pilot Light | AWS Backup + pre-deployed core infra + Elastic Disaster Recovery | 30 min–hours | Minutes | Low (~1.5x) | Moderate criticality; cost-sensitive |
| Warm Standby | AWS Backup + reduced-capacity stack + Route 53 | Minutes | Seconds–minutes | Higher (~2x) | High criticality with cost ceiling |
| Multi-Site Active/Active | Aurora Global DB, DynamoDB global tables, Route 53 latency routing, ARC | Near-zero | Near-zero | Highest (~3–5x) | Mission-critical; RTO/RPO < 1 min |

- Pilot Light ≠ Warm Standby: Pilot Light has core infra pre-deployed but not serving traffic; Warm Standby serves reduced-capacity traffic immediately.
- Aurora Global DB: < 1 s cross-Region replication lag, < 1 min secondary promotion. DynamoDB global tables: typically < 1 s lag.
- Lock-in: Aurora Global DB and DynamoDB global tables are AWS-proprietary — plan migration cost before committing.
- During recovery use data plane operations, not control plane (REL11-BP04).

**Source**: https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html (2022-04-01, current stable)

---

## DEC-2 — Compute Type Selection per Component

**Ask**: "Is the workload event-driven or long-running, stateless or stateful?"

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|------------|-----------|------------|-----------|
| Serverless functions | Lambda | Pay per invocation, low ops overhead | Cold starts, 15 min max timeout | Event-driven, intermittent, stateless |
| Containerized serverless | ECS Fargate / EKS Fargate | No server management, flexible sizing | Higher base cost vs Lambda | Predictable container workloads |
| Managed containers | ECS EC2 / EKS EC2 | Control, GPU, Spot discounts | Operational overhead | GPU ML, Spot-tolerant workloads |
| Virtual machines | EC2 | Max flexibility, Spot up to 90% discount | Highest management overhead | Lift-and-shift, HPC, Spot fleets |
| Graviton (ARM) | M8g / C8g / R8g | 30% perf + 40% price-perf + 60% energy vs x86 | ARM compatibility testing | General-purpose; greenfield |

- Cost profile: Lambda < Fargate < ECS/EKS EC2 (Spot) < EC2 On-Demand.
- Lock-in: Lambda and Fargate APIs are proprietary; Kubernetes on EKS is more portable.

**Source**: PERF02-BP01 https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/ (pillar last updated 2024-11-06)

---

## DEC-3 — Pricing Model Mix for Stable vs Variable Workloads

**Ask**: "Has this workload run for ≥3 months with stable CPU patterns?" — only then recommend a Savings Plan commitment.

| Option | Discount | Trade-off | Best When |
|--------|----------|-----------|-----------|
| On-Demand | 0% | Full flexibility | Unpredictable spikes; new workloads |
| Spot | Up to 90% | 2-min interruption notice | Fault-tolerant, stateless, batch |
| Compute Savings Plans | Up to 66% | 1/3-yr hourly $ commitment | Stable baseline compute |
| Instance Savings Plans | Up to 72% | Locked to instance family + Region | Stable single-family workloads |
| Reserved Instances | Up to 72% | Per-service commitment | RDS, ElastiCache, Redshift |

- Recommended mix: Savings Plans for baseline + Spot for burst + On-Demand for unpredictable peaks.
- Buy Savings Plans in the management account (no workloads) so discounts share org-wide.
- Track potential-savings threshold (act when > 20%) rather than a fixed coverage percentage.

**Source**: COST07 https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/select-the-best-pricing-model.html (pillar last updated 2024-06-27)

---

## DEC-4 — Data Store Selection per Access Pattern

**Ask**: "What is the primary access pattern: KV lookup, full-text search, relational join, or time-series?"

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|------------|-----------|------------|-----------|
| Relational | Aurora / RDS | ACID, complex queries, joins | Horizontal write scaling | Transactional apps, reporting |
| Key-value / NoSQL | DynamoDB | Single-digit ms at any scale | Query flexibility | High-throughput KV lookups |
| In-memory cache | ElastiCache (Redis/Memcached) | Sub-ms reads | Durability (by default) | Session, leaderboard, hot data |
| Object storage | S3 | Unlimited scale, low cost | Not a database | Unstructured data, media, backups |
| Search | OpenSearch | Full-text, aggregations | Cost at scale | Log analytics, catalog search |

- Cost profile: DynamoDB provisioned < DynamoDB on-demand < Aurora Serverless v2 < RDS Multi-AZ < ElastiCache cluster.
- Time-series has no dedicated row in the research — store choice for time-series is (unverified).

**Source**: PERF-AD-6 https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/ (pillar last updated 2024-11-06)
