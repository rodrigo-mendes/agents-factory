# Cloud Architecture Research — AWS Well-Architected Framework: Reliability Pillar

## Metadata
```yaml
Full_Name: "AWS Well-Architected Framework — Reliability Pillar"
Cloud_Provider: "AWS"
Architecture_Domain: "Well-Architected Framework — Reliability Pillar"
Target_Edition: "November 6, 2024 (current stable)"
Architecture_Context: "Multi-account production workloads on AWS"
Official_Source_URL: "https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-08-27"
Currency_Threshold: "2027-08-27"
```

> **Version Absolutism notice:** The Reliability Pillar whitepaper edition is November 6, 2024 (current stable). This research is valid until 2027-08-27. The AWS DR whitepaper (last updated 2022-04-01) is >12 months old but remains the current stable DR guidance — use with awareness that newer editions may exist.

## Executive Summary

The AWS Well-Architected Framework Reliability Pillar provides guidance to help customers apply best practices in the design, delivery, and maintenance of AWS environments. It defines reliability as the ability of a workload to perform its intended function correctly and consistently when expected, covering recovery from infrastructure or service disruptions, dynamic acquisition of computing resources, and mitigation of misconfigurations or transient network issues. The pillar is organized around four best-practice areas: Foundations, Workload Architecture, Change Management, and Failure Management.

The November 6, 2024 edition (current stable) preserves the five core design principles and the four best-practice areas established in prior editions. There is no retirement of major services in this edition; AWS Fault Injection Service (FIS), Amazon Application Recovery Controller (ARC), and AWS Elastic Disaster Recovery remain the current authoritative services for fault injection, traffic failover control, and managed server DR respectively. The guidance on DR strategies (Backup & Restore, Pilot Light, Warm Standby, Multi-Site Active/Active) is sourced from the companion DR whitepaper (last updated 2022-04-01 — current stable, >12 months, use with review awareness).

For multi-account production workloads on AWS, the three most critical architecture guardrails are: (1) deploy all workloads across multiple Availability Zones with automated failover — single-AZ deployment is a CRITICAL anti-pattern; (2) define and regularly test an explicit DR strategy with measured RTO/RPO objectives before a disaster occurs — untested and ad-hoc recovery are named anti-patterns in the whitepaper; and (3) never depend on control-plane operations during recovery — data-plane failover paths (e.g., Amazon Application Recovery Controller) must be pre-provisioned and exercised.

## Cloud Architecture Glossary

```
Term: Availability Zone (AZ)
Definition: One or more discrete data centers with redundant power, networking, and connectivity within a single AWS Region. AZs are physically separate, designed so that failures are isolated from other AZs.
Provider Docs Section: Reliability Pillar — Foundations; REL10-BP01
Architect Usage: Deploy across ≥2 AZs (≥3 preferred) for workload-level fault isolation. Use Auto Scaling groups and ELB spanning multiple AZs.
Common Confusion: Confused with AWS Region. A Region contains multiple AZs; AZ failure ≠ Region failure. A Region failure requires a multi-Region DR strategy.
```

```
Term: Recovery Time Objective (RTO)
Definition: The maximum acceptable delay between a service interruption and recovery of service. Defines how long the workload can be down.
Provider Docs Section: Reliability Pillar — REL13-BP01; DR whitepaper
Architect Usage: RTO is a business requirement, not a technical default. Derive it from business impact analysis. Select the DR strategy whose achievable RTO meets this target.
Common Confusion: Confused with RPO. RTO is about time to restore function; RPO is about acceptable data loss. Both must be defined independently.
```

```
Term: Recovery Point Objective (RPO)
Definition: The maximum acceptable amount of time since the last data recovery point. Defines how much data loss is tolerable.
Provider Docs Section: Reliability Pillar — REL13-BP01; DR whitepaper
Architect Usage: RPO drives backup frequency and replication strategy. Near-zero RPO requires continuous replication (e.g., Aurora Global Database <1s lag, DynamoDB global tables). Note: replication alone does not protect against data corruption or deletion — PITR and versioning must be added.
Common Confusion: Confused with RTO. RPO is about data loss; RTO is about downtime duration.
```

```
Term: Pilot Light
Definition: A DR strategy where a minimal version of the core infrastructure (the "pilot light") is always running in a secondary Region, with data continuously replicated. During a disaster, the environment is "turned on" (resources scaled up/activated) to handle production load.
Provider Docs Section: DR whitepaper — Disaster recovery options in the cloud
Architect Usage: Use when cost-consciousness is required but RTO of hours is unacceptable. Core infra must be pre-deployed; plan for the scale-up time in RTO calculation.
Common Confusion: Confused with Warm Standby. Pilot Light requires active scale-up during a DR event; Warm Standby already runs at reduced capacity and can immediately serve (reduced) traffic.
```

```
Term: Warm Standby
Definition: A DR strategy where a scaled-down but fully functional version of the production environment runs continuously in a secondary location. During a disaster, it is scaled up to full capacity.
Provider Docs Section: DR whitepaper — Disaster recovery options in the cloud
Architect Usage: Use for business-critical workloads requiring faster recovery than Pilot Light. Traffic can be routed immediately (at reduced capacity), then scaled up. RTO is typically minutes.
Common Confusion: Confused with Multi-Site Active/Active. Warm Standby is active/passive — the standby does not serve production traffic until a failover event.
```

```
Term: Multi-Site Active/Active
Definition: A DR strategy where the workload runs simultaneously in multiple Regions, each actively serving production traffic. Traffic is distributed across all sites at all times.
Provider Docs Section: DR whitepaper — Disaster recovery options in the cloud
Architect Usage: Use only for mission-critical or globally distributed workloads where near-zero RTO/RPO is required. Highest cost and complexity. Requires conflict resolution for data written simultaneously in multiple Regions.
Common Confusion: Confused with Multi-AZ deployment. Multi-AZ is within a single Region; Multi-Site Active/Active spans Regions.
```

```
Term: Service Quota (formerly Service Limit)
Definition: An upper bound on the number of AWS resources or operations that an AWS account can use in a given Region. Some quotas are soft (adjustable via request); some are hard (cannot be raised).
Provider Docs Section: Reliability Pillar — Foundations
Architect Usage: Monitor quota utilization via Service Quotas console and CloudWatch; request increases proactively before hitting limits. Account for quotas per account and per Region in DR planning — the DR Region must also have adequate quotas.
Common Confusion: Confused with IAM permissions. Quotas limit resource counts/rates; IAM controls access authorization. Both must be managed.
```

```
Term: Fault Isolation Boundary
Definition: A scope within which a failure is contained and prevented from propagating. AZs are a fundamental fault isolation boundary on AWS.
Provider Docs Section: Reliability Pillar — REL10-BP01 (Use fault isolation to protect your workload)
Architect Usage: Design the workload so that a failure within one boundary does not cascade across others. Use shuffle sharding, cell-based architecture, or AZ isolation to contain blast radius.
Common Confusion: Confused with security isolation. Fault isolation limits failure propagation; security isolation limits unauthorized access. Both are needed but serve different purposes.
```

```
Term: Control Plane vs Data Plane
Definition: The control plane manages and configures AWS resources (e.g., API calls to create/modify resources). The data plane serves runtime requests (e.g., EC2 instance processing, S3 object GET). Data planes are generally more available than control planes.
Provider Docs Section: Reliability Pillar — REL11-BP04
Architect Usage: During a DR event, rely exclusively on data-plane operations. Pre-provision all resources via IaC before a disaster. Avoid recovery runbooks that require control-plane API calls to create new resources during the event.
Common Confusion: Often architects assume AWS APIs are uniformly available. Control planes can degrade during major events; data planes are designed for higher availability.
```

```
Term: AWS Fault Injection Service (FIS)
Definition: A managed service for running controlled fault injection experiments on AWS workloads to validate resilience and recovery automation.
Provider Docs Section: Reliability Pillar — Failure Management (Design Principle 2: Test recovery procedures)
Architect Usage: Define FIS experiment templates for common failure scenarios (AZ impairment, instance termination, latency injection). Attach CloudWatch-based stop conditions to automatically halt experiments if real impact is detected.
Common Confusion: Confused with load/performance testing tools. FIS tests failure recovery, not throughput or latency under normal load.
```

```
Term: Amazon Application Recovery Controller (ARC)
Definition: A service that provides routing controls (data-plane API) for managing application traffic failover across Regions and AZs, independent of the AWS control plane.
Provider Docs Section: Reliability Pillar — REL13-BP02; REL11-BP04
Architect Usage: Use ARC routing controls in DR runbooks instead of DNS-only failover when strict RTO is required and control-plane independence is needed. ARC's data-plane API remains available even when the control plane is degraded.
Common Confusion: Confused with Amazon Route 53 health-check failover. Route 53 failover relies on DNS propagation (TTL delays); ARC routing controls shift traffic immediately at the data plane.
```

```
Term: AWS Elastic Disaster Recovery
Definition: A managed service that provides continuous block-level replication of servers to AWS for use in Pilot Light DR scenarios. Enables point-in-time recovery and fast failover.
Provider Docs Section: Reliability Pillar — REL13-BP02
Architect Usage: Use for lift-and-shift server-based DR where Pilot Light cost profile is acceptable. Replication is continuous; recovery launches pre-configured instances in the recovery Region.
Common Confusion: Confused with AWS Backup. AWS Backup is a centralized backup management service (backup & restore strategy); Elastic Disaster Recovery provides continuous replication closer to Pilot Light RTO/RPO targets.
```

```
Term: AWS Backup
Definition: A centralized managed service for automating and consolidating data backups across AWS services (EC2, EBS, RDS, DynamoDB, EFS, S3, etc.) with cross-Region and cross-account copy support.
Provider Docs Section: Reliability Pillar — REL09-BP01; Failure Management
Architect Usage: Use as the foundation of any backup & restore DR strategy. Enable cross-Region copy to the DR Region. Combine with S3 versioning and DynamoDB PITR for protection against data corruption/deletion — replication alone is insufficient.
Common Confusion: Confused with Amazon S3 replication. S3 CRR replicates objects but does not protect against deletion/corruption without versioning. AWS Backup provides point-in-time restore capability across multiple services.
```

## Architecture Guardrails

### ✅ Mandatory Patterns

**REL-AD-1 — Deploy across multiple Availability Zones**
- Pillar Alignment: Reliability — Fault Isolation (REL10-BP01); Design Principle 3 (Scale horizontally)
- Why: "AZs are physically separate with independent power/cooling." Distributing across AZs eliminates single points of failure at the infrastructure layer. REL10-BP01 mandates active/active across AZs.
- AWS Services: Amazon EC2 (multi-AZ placement), Elastic Load Balancing (cross-zone enabled), Amazon RDS Multi-AZ, EC2 Auto Scaling groups spanning multiple AZs
- Architecture Decision: Configure Auto Scaling groups to span ≥2 AZs (≥3 recommended). Enable cross-zone load balancing on ELB. Use RDS Multi-AZ with synchronous hot-standby failover. Distribute subnets across AZs in the VPC.
- Verification:
  - `aws autoscaling describe-auto-scaling-groups` — confirm AZ spread across ≥2 AZs
  - `aws rds describe-db-instances` — confirm `MultiAZ: true`
  - ELB: confirm cross-zone load balancing enabled in console or via `aws elbv2 describe-load-balancer-attributes`
- Trade-offs: Cross-AZ data-transfer costs; stateful replication complexity for session/cache layers.
- Source: REL10-BP01 https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/use-fault-isolation-to-protect-your-workload.html [triangulated with REL13-BP02]

**REL-AD-2 — Back up all critical data off-site**
- Pillar Alignment: Reliability — Failure Management (REL09-BP01); Design Principle 1 (Automatically recover from failure)
- Why: REL09-BP01 requires backing up all data or the ability to reproduce it from sources; backups must be copied to another Region to survive a regional event.
- AWS Services: AWS Backup (centralized), Amazon S3 versioning + Cross-Region Replication (CRR), Amazon EBS snapshots, RDS automated backups + PITR, DynamoDB PITR
- Architecture Decision: Enable AWS Backup plans with cross-Region copy to DR Region. Enable S3 versioning + CRR on buckets containing critical objects. Enable RDS automated backups with adequate retention period and PITR. Enable DynamoDB PITR. Combine replication with independent backups — replication alone does not protect against data corruption or deletion.
- Verification:
  - `aws backup list-backup-jobs` — confirm jobs completing successfully
  - `aws s3api get-bucket-versioning` — confirm versioning enabled
  - `aws rds describe-db-instances` — confirm `BackupRetentionPeriod` > 0
- Trade-offs: Storage and cross-region transfer costs; restore-time testing overhead.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/failure-management.html [triangulated with REL13-BP02]

**REL-AD-3 — Manage service quotas**
- Pillar Alignment: Reliability — Foundations; Design Principle 4 (Stop guessing capacity)
- Why: Unmanaged quota consumption causes throttling and capacity-driven outages. DR Regions must also have adequate quotas pre-provisioned — quota requests can take time to process.
- AWS Services: AWS Service Quotas, AWS Trusted Advisor (service limit checks), Amazon CloudWatch (quota usage alarms)
- Architecture Decision: Monitor quota utilization continuously via CloudWatch quota-usage metrics. Request increases proactively before reaching limits. Include quota planning in DR readiness reviews — the DR Region must have equivalent or sufficient quotas.
- Verification:
  - `aws service-quotas list-service-quotas --service-code <service>`
  - Trusted Advisor service-limits check in console
  - CloudWatch quota-usage metric alarms
- Trade-offs: Some quotas are hard limits that cannot be raised regardless of business justification.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/foundations.html

**REL-AD-4 — Elastic scaling to match demand**
- Pillar Alignment: Reliability — Change Management; Design Principle 4 (Stop guessing capacity)
- Why: Fixed capacity causes saturation outages under peak demand and wastes resources at low demand. The design principle mandates monitoring demand/utilization and automating resource adjustment.
- AWS Services: AWS Auto Scaling / EC2 Auto Scaling, Application Auto Scaling, Elastic Load Balancing, Amazon CloudWatch (KPI-based alarms driving scaling policies)
- Architecture Decision: Define scaling policies based on business-value KPIs (not just CPU), not raw infrastructure metrics alone. Design workload to adapt to demand changes without manual intervention. Validate scale-out behavior under load test before production.
- Verification:
  - Confirm ASG scaling policies exist and reference CloudWatch alarms on relevant KPIs
  - Load test to confirm scale-out triggers and instance-warm behavior
- Trade-offs: Scaling lag on sudden spikes; cold-start latency considerations for stateful or slow-booting workloads.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/change-management.html

**REL-AD-5 — Define and implement a tested DR strategy (RTO/RPO)**
- Pillar Alignment: Reliability — Failure Management (REL13-BP01 through REL13-BP05); Design Principle 2 (Test recovery procedures)
- Why: REL13-BP01 requires RTO/RPO to be derived from business need. REL13-BP02 requires selecting a strategy that meets those objectives. REL13-BP03 requires testing. REL13-BP04 requires managing configuration drift. REL13-BP05 requires automating recovery.
- AWS Services: AWS Backup, AWS Elastic Disaster Recovery, Amazon Route 53, Amazon Application Recovery Controller (ARC), AWS CloudFormation / StackSets, DynamoDB global tables, Aurora Global Database
- Architecture Decision: Define RTO/RPO from business impact analysis (REL13-BP01). Select DR strategy aligned to RTO/RPO and cost constraints (REL13-BP02). Use IaC (CloudFormation/StackSets) for all DR infrastructure to prevent configuration drift (REL13-BP04). Automate failover via ARC routing controls. Use data-plane operations only during recovery (REL11-BP04). Aurora Global Database: cross-Region replication latency <1s; promotion in <1 min even in complete regional outage.
- Verification:
  - Scheduled DR drills and game days with measured achieved RTO/RPO vs targets
  - Elastic Disaster Recovery drill reports
  - IaC drift detection (CloudFormation drift detection)
- Trade-offs: Cost and complexity increase from Backup & Restore toward Active/Active; over-engineering to lower RTO/RPO than the business requires wastes cost.
- Source: REL13-BP02 https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_planning_for_recovery_disaster_recovery.html [triangulated]

**REL-AD-6 — Test reliability via fault injection**
- Pillar Alignment: Reliability — Failure Management; Design Principle 2 (Test recovery procedures)
- Why: Design Principle 2 mandates simulating failures via automation to expose failure pathways before real failure occurs and to validate automated recovery.
- AWS Services: AWS Fault Injection Service (FIS), Amazon CloudWatch
- Architecture Decision: Create FIS experiment templates for representative failure scenarios (AZ impairment, instance termination, network latency). Attach CloudWatch-based stop conditions to each experiment to auto-halt if real impact is detected (blast-radius control). Recreate prior failure scenarios as regression experiments. Schedule game days via EventBridge.
- Verification:
  - FIS experiment templates exist and have been executed with results logged
  - Game-day runbooks documented
  - CloudWatch KPI alarms fire and automated recovery confirms workload self-heals within RTO
- Trade-offs: Requires safety guardrails and stop conditions; running against production without blast-radius controls risks uncontrolled impact. FIS charges per experiment action.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/failure-management.html [triangulated with Design Principle 2]

### ⚠️ Architectural Decisions

**Decision A — DR Strategy Selection**
- Options:

  | Option | AWS Service | RTO | RPO | Cost | Best When |
  |--------|-------------|-----|-----|------|-----------|
  | Backup & Restore | AWS Backup + IaC (CloudFormation) | Hours (PITR can lower RPO to ~5 min) | Hours | Lowest | Non-critical / cost-sensitive workloads |
  | Pilot Light | AWS Elastic Disaster Recovery + continuous data replication | Tens of minutes | Minutes | Low | Moderate criticality, cost-conscious |
  | Warm Standby | Scaled-down always-on stack in DR Region, cross-Region routing | Minutes | Seconds | Higher | Business-critical, faster recovery required |
  | Multi-Site Active/Active | Multi-Region + Route 53 + DynamoDB global tables / Aurora Global Database | Near zero | Near zero | Highest | Mission-critical / global low-latency |

- Cost Profile: Lowest (Backup & Restore — pay only for storage) to Highest (Active/Active — full duplicate running costs + cross-Region replication). Cost driver = standby resource running time + cross-Region data transfer.
- Lock-in Assessment: AWS-managed services (Elastic Disaster Recovery, ARC, Aurora Global Database) have AWS-specific APIs. DynamoDB global tables and Aurora Global Database are AWS-proprietary — migration to another provider requires re-architecture of data tier.
- Architect Instruction: "Ask what the business-defined RTO and RPO are when a DR strategy is being selected — do not select a strategy based on cost alone without confirming the business can accept the recovery objectives of that strategy."
- Source: REL13-BP02 https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_planning_for_recovery_disaster_recovery.html

**Decision B — Failover Routing / Orchestration**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | DNS failover | Amazon Route 53 health checks + failover routing | Simple to configure; broad applicability | DNS TTL propagation delay; relies on DNS clients respecting TTL | Basic active/passive; RTO of minutes acceptable |
  | Data-plane failover | Amazon Application Recovery Controller (ARC) routing controls | Control-plane-independent; highly available; immediate traffic shift | Additional setup/cost; requires ARC routing control cells | Strict RTO; must work even when control plane is degraded |
  | Managed replication + failover | AWS Elastic Disaster Recovery | Warm-standby-equivalent RPO/RTO at pilot-light cost; managed orchestration | Service-specific scope; not a general-purpose failover solution | Lift-and-shift / server-based DR scenarios |

- Cost Profile: Route 53 health checks — low (per health check/month). ARC — moderate (routing control cells per month). Elastic Disaster Recovery — based on replicated instance hours.
- Lock-in Assessment: ARC is AWS-specific. Route 53 is AWS-specific but DNS failover concept is portable; health check IPs are AWS-managed.
- Architect Instruction: "Ask whether the DR runbook requires creating or modifying resources during the failover event — if yes, flag REL11-BP04 (control-plane dependency risk) and evaluate ARC as the failover mechanism."
- Source: REL13-BP02

**Decision C — Cross-Region Data Synchronization**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Global multi-active DB | DynamoDB global tables | Near-zero RPO; automatic resync after partition | Eventual consistency; conflict resolution required for concurrent writes | Multi-Region active-active NoSQL workloads |
  | Global relational DB | Aurora Global Database | Fast cross-Region read (<1s replication lag); managed promotion in <1 min | Relational cost/complexity; writes to primary only (active/passive replication) | Multi-Region relational workloads; RPO <1s |
  | Object replication | Amazon S3 Cross-Region Replication + versioning | Durable object copies in DR Region; PITR-friendly when combined with versioning | Not protection against corruption/deletion unless versioning is also enabled | Object storage / data-lake DR |

- Cost Profile: DynamoDB global tables — replicated write unit costs; Aurora Global Database — instance + I/O costs in each Region; S3 CRR — per-GB replication cost.
- Lock-in Assessment: DynamoDB global tables and Aurora Global Database are AWS-proprietary managed services with no direct open-source equivalents. S3 CRR is S3-specific but object storage is broadly portable.
- Architect Instruction: "Ask whether the data tier requires multi-Region active-active writes or active-passive reads — this determines whether DynamoDB global tables (active-active) or Aurora Global Database (active-passive replication) is appropriate."
- Source: REL13-BP02

**Decision D — Single-Region (Multi-AZ) vs Multi-Region**
- Options:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | Multi-AZ, single Region | Lower cost/complexity; protects against AZ-level failure (fire, flood, power, hardware) | No protection against full-Region service disruption | Most workloads; data residency constrained to single Region |
  | Multi-Region | Protection against full-Region loss; global latency optimization | Highest cost and complexity; data residency must permit cross-Region | Region-loss RTO/RPO requirement; no single-Region residency constraint |

- Cost Profile: Multi-AZ adds cross-AZ data transfer costs (low). Multi-Region adds full duplicate running costs, cross-Region replication, and egress costs (high).
- Lock-in Assessment: Multi-Region architecture relies on AWS-specific global services (Route 53, ARC, Aurora Global Database, DynamoDB global tables).
- Architect Instruction: "Ask whether the business requires protection against a full AWS Region outage and whether data residency regulations permit cross-Region data transfer — both must be confirmed before proposing multi-Region."
- Source: REL13-BP02

### 🚫 Anti-Patterns

**REL-ND-1 — Single Points of Failure / Single-AZ Deployment**
- Risk Level: CRITICAL
- Why: Violates Design Principle 3 (Scale horizontally to increase aggregate workload availability) and REL10-BP01 (Use fault isolation to protect your workload). An AZ or component failure causes a complete outage with no automatic recovery path.
- Instead: EC2 Auto Scaling group spanning multiple AZs behind an Application Load Balancer with cross-zone load balancing enabled. Amazon RDS Multi-AZ with synchronous standby. ElastiCache with multi-AZ replication.
- Detection: `aws autoscaling describe-auto-scaling-groups` — confirm ≥2 AZs in `AvailabilityZones`. `aws rds describe-db-instances` — confirm `MultiAZ: true`. AWS Resilience Hub assessment for single-AZ findings.
- Impact: AZ failure = complete production outage with no automatic recovery.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/use-fault-isolation-to-protect-your-workload.html

**REL-ND-2 — No DR Plan / Ad-Hoc Recovery**
- Risk Level: CRITICAL
- Why: Named anti-patterns in REL13-BP02: "Having no plan for disaster recovery" and "Leaving the DR strategy ad-hoc when a disaster occurs." Without a pre-defined and tested plan, recovery objectives will not be met.
- Instead: Define RTO/RPO from business impact analysis (REL13-BP01). Implement AWS Backup and/or AWS Elastic Disaster Recovery. Document a DR runbook in IaC (CloudFormation). Schedule regular DR drills.
- Detection: Absence of DR runbook or IaC for DR infrastructure. No recorded DR drill results. No defined RTO/RPO targets documented.
- Impact: Recovery objectives missed; prolonged or incomplete recovery during a real disaster.
- Source: REL13-BP02 (Common anti-patterns section)

**REL-ND-3 — Control-Plane Dependency During Recovery**
- Risk Level: CRITICAL
- Why: Named anti-pattern in REL13-BP02 and REL11-BP04: "Dependency on control plane operations during recovery." The control plane may be degraded or unavailable during the exact event requiring recovery.
- Instead: Use data-plane operations only during DR (REL11-BP04). Pre-provision all resources via IaC before a disaster. Use Amazon Application Recovery Controller (ARC) data-plane API for traffic rerouting — ARC routing controls remain available even when the control plane is degraded.
- Detection: Review DR runbook for AWS API calls that create or modify resources during recovery (e.g., `CreateInstance`, `ModifyDBInstance`). Conduct DR drill under simulated control-plane impairment.
- Impact: Recovery blocked at the worst possible moment — control plane degradation may be caused by the same event requiring recovery.
- Source: REL13-BP02 + REL11-BP04

**REL-ND-4 — Replication Only (No PITR / Versioning)**
- Risk Level: HIGH
- Why: Verbatim from REL13-BP02: "Continuous data replication protects against some types of disaster, but not data corruption/destruction unless strategy also includes versioning or PITR." Corruption or accidental deletion is replicated to the DR copy, making both copies unusable.
- Instead: Combine continuous replication with independent backup mechanisms: AWS Backup with PITR, S3 versioning (preserves all object versions including deleted), DynamoDB PITR (enables restore to any point in time within retention window).
- Detection: Confirm S3 versioning is enabled on critical buckets. Confirm DynamoDB PITR is enabled. Confirm AWS Backup jobs produce independent restore points not derived from the replica.
- Impact: Data corruption or deletion events are replicated and unrecoverable — the DR strategy provides no protection against the most common data loss scenarios.
- Source: REL13-BP02

**REL-ND-5 — Fixed / Guessed Capacity**
- Risk Level: HIGH
- Why: Violates Design Principle 4 (Stop guessing capacity). Fixed provisioning causes saturation-driven outages during demand spikes and wastes cost during low-demand periods. Unmonitored quota consumption causes throttling at unpredictable thresholds.
- Instead: AWS Auto Scaling driven by CloudWatch KPI-based alarms. Monitor quota utilization via Service Quotas and Trusted Advisor; request increases proactively.
- Detection: CloudWatch utilization metrics showing sustained saturation. Throttling errors in application logs. Trusted Advisor service-limit warnings.
- Impact: Saturation-driven outages during demand peaks; wasted over-provisioning during low-demand periods; quota-driven throttling causing partial failures.
- Source: Reliability Design Principle 4 + Foundations https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/foundations.html

**REL-ND-6 — Never Testing Recovery**
- Risk Level: CRITICAL
- Why: Named anti-pattern in REL13-BP03: "Implementing inconsistent recovery procedures" and the DR strategy being "left untested." Design Principle 2 mandates testing recovery procedures via simulation before a real failure occurs.
- Instead: REL13-BP03 — test the DR implementation regularly. Use AWS Fault Injection Service (FIS) for failure simulation with stop conditions. Schedule game days. Record and compare achieved RTO/RPO to targets.
- Detection: No FIS experiment templates exist. No restore-test records. No DR drill records with measured RTO/RPO outcomes.
- Impact: Backups and failover mechanisms are silently broken or misconfigured — discovered only during a real disaster when the cost of failure is highest.
- Source: REL13-BP03 + https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/failure-management.html

## Cloud-Native Design Patterns

**Multi-AZ Active/Active with Auto Scaling**
- Category: Resilience
- Problem: Single-AZ deployments have no automatic recovery from AZ-level infrastructure failures (power, networking, hardware).
- Solution on AWS: EC2 Auto Scaling group spanning ≥2 AZs, Application Load Balancer with cross-zone load balancing, Amazon RDS Multi-AZ (synchronous standby), Auto Scaling policies driven by CloudWatch KPI alarms.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Availability | Survives AZ failure without manual intervention | Cross-AZ data transfer charges |
  | Scalability | Scales horizontally across AZs as demand grows | Stateful session/cache replication complexity |
  | Operability | Auto-replaces failed instances via ASG health checks | Slightly higher operational surface area to monitor |

- Source: REL10-BP01 https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/use-fault-isolation-to-protect-your-workload.html

**Tested DR with Automated Failover**
- Category: Resilience
- Problem: DR strategies are frequently documented but never exercised, resulting in silent failures discovered only during a real disaster.
- Solution on AWS: IaC (CloudFormation StackSets) for all DR infrastructure, AWS Backup with cross-Region copy, Amazon Application Recovery Controller (ARC) for data-plane failover, AWS Elastic Disaster Recovery for server-based workloads, AWS Fault Injection Service (FIS) for regular game days. Measure achieved RTO/RPO vs targets on every drill.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Reliability | Validates recovery before a real disaster; prevents configuration drift | DR drill engineering time; FIS experiment costs |
  | Confidence | Measured RTO/RPO data replaces assumptions | Requires prod-representative test environments |
  | Automation | Automated failover removes human-error risk during high-stress events | Requires pre-provisioned data-plane resources (ARC cells) |

- Source: REL13-BP03 https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_planning_for_recovery_disaster_recovery.html

## Security Architecture

**Backup Integrity and Access Control**
- AWS Services: AWS Backup, AWS Key Management Service (KMS), AWS Identity and Access Management (IAM), AWS Organizations Service Control Policies (SCPs)
- Architecture: Encrypt all backups at rest using AWS KMS customer-managed keys. Use separate KMS keys in the backup/DR account to prevent a compromised primary account from accessing backup decryption keys. Apply IAM least-privilege policies on backup vaults. Use AWS Organizations SCPs to prevent unauthorized deletion of backup vaults across member accounts. Enable AWS Backup Vault Lock to enforce WORM (write-once-read-many) on critical backup vaults, preventing deletion even by root.
- Compliance Alignment: Data integrity and availability controls relevant to SOC 2 (Availability/Integrity), ISO 27001 (A.12.3), and NIST 800-53 (CP-9 Information System Backup) — reference only, not legal advice.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/failure-management.html

## Operational Patterns

**Disaster Recovery Operations**
- RTO/RPO: Defined per strategy. Backup & Restore: RTO hours, RPO hours. Pilot Light: RTO tens of minutes, RPO minutes. Warm Standby: RTO minutes, RPO seconds. Multi-Site Active/Active: RTO near-zero, RPO near-zero. Aurora Global Database: cross-Region replication latency <1s; promote secondary in <1 min even in complete regional outage.
- AWS Services: AWS Backup, AWS Elastic Disaster Recovery, Amazon Route 53, Amazon Application Recovery Controller (ARC), DynamoDB global tables, Aurora Global Database, AWS CloudFormation StackSets
- Cost Profile: Low (Backup & Restore — storage only) → High (Multi-Site Active/Active — full duplicate running costs). Cost driver: standby resource running time + cross-Region replication and transfer.
- Automation: Use IaC (CloudFormation) for all DR infrastructure to prevent configuration drift (REL13-BP04). Automate failover via ARC routing controls (data-plane only — REL11-BP04). Automate restore validation after each backup job. Trigger DR drills on a scheduled cadence via EventBridge.
- Source: REL13-BP02 https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_planning_for_recovery_disaster_recovery.html

**Fault Injection Testing**
- RTO/RPO: N/A (testing discipline — validates that production RTO/RPO targets are achievable, not a production DR mechanism).
- AWS Services: AWS Fault Injection Service (FIS), Amazon CloudWatch, EC2 Auto Scaling
- Cost Profile: Low — FIS charges per experiment action. Main cost is engineering time for experiment design and game-day facilitation.
- Automation: Schedule game days via Amazon EventBridge. Attach FIS stop conditions linked to CloudWatch alarms to automatically halt experiments if real customer impact is detected. Document results and compare achieved recovery metrics to RTO/RPO targets.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/failure-management.html

## Reference Architectures

**Multi-AZ Highly Available Web Application**
- Context: Production web workloads requiring AZ-level resilience without multi-Region complexity.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | DNS | Amazon Route 53 | Health-check-aware DNS with failover routing policy |
  | Load balancing | Application Load Balancer (multi-AZ) | Distribute traffic; health checks per target group |
  | Compute | EC2 Auto Scaling group across ≥2 AZs | Horizontal scaling; automatic instance replacement on failure |
  | Database | Amazon RDS Multi-AZ | Synchronous standby in separate AZ; automatic failover |
  | Cache | Amazon ElastiCache (multi-AZ enabled) | Reduce DB load; multi-AZ replication for cache resilience |
  | Storage | Amazon S3 | Eleven 9s durability; multi-AZ by default |
  | Backup | AWS Backup | Centralized backup with cross-Region copy for RDS/EBS |

- Key Decisions: Number of AZs (2 vs 3 — 3 provides better fault domain distribution). RDS Multi-AZ DB instance vs DB cluster (cluster adds 2 readable standbys for read scalability). ElastiCache multi-AZ replication group vs single-node (always multi-AZ in production). Whether compliance requires cross-Region backup copy.
- Scaling Path: Start with 2 AZs; add a third for improved fault isolation. Promote to multi-Region by adding Aurora Global Database and Route 53 geolocation/latency routing. Add ARC routing controls when strict RTO requires control-plane-independent failover.
- Source: REL10-BP01 + AWS Solutions Library Containerized Web App Guidance

## Service Equivalence Map

*Not applicable — this research is AWS-specific. Cross-provider mapping is out of scope for single-provider reliability pillar guidance.*

## Provider Differentiators

**Amazon Application Recovery Controller (ARC)** — Provides data-plane-level traffic failover independent of the AWS control plane. This is unique in that ARC routing controls remain available even during major regional events where the control plane may be degraded. Directly addresses REL11-BP04 (the named anti-pattern of control-plane dependency during recovery).

**Aurora Global Database** — Delivers cross-Region replication with <1 second latency and managed secondary Region promotion in under 1 minute, even in a complete regional outage. This enables near-zero RPO for relational workloads that would otherwise require complex self-managed replication.

**AWS Fault Injection Service (FIS)** — Managed chaos engineering with built-in safety mechanisms (stop conditions linked to CloudWatch alarms). Enables systematic game-day execution without requiring self-managed tooling, directly implementing Design Principle 2 (Test recovery procedures via automation).

**AWS Resilience Hub** — Provides automated assessment of workload resilience against defined RTO/RPO targets, identifying gaps such as single-AZ deployments and missing backup configurations. Enables continuous DR posture monitoring without manual audit.

## Scenario Coverage

**Standard Case**: Production workload needing AZ resilience with RPO hours and RTO less than 1 hour
- Approach: Multi-AZ EC2 Auto Scaling + Application Load Balancer (cross-zone enabled) + Amazon RDS Multi-AZ + AWS Backup with cross-Region copy. Amazon Route 53 health checks with failover routing for DNS-level failover. CloudWatch KPI alarms driving ASG scaling policies.
- Key Decisions: RTO/RPO targets (must be defined from business impact analysis — do not assume defaults). Data classification to determine backup frequency and cross-Region copy requirement. Whether compliance mandates multi-Region data residency.

**Edge Case**: Near-zero RPO/RTO for mission-critical global workload
- Approach: Multi-Site Active/Active with DynamoDB global tables (for NoSQL) or Aurora Global Database (for relational, with <1s replication lag and <1 min promotion). Route 53 latency/failover routing to distribute traffic across Regions. Amazon Application Recovery Controller (ARC) routing controls for immediate, control-plane-independent traffic shifting. AWS Fault Injection Service (FIS) game days to validate recovery within RTO/RPO before a real event. All DR infrastructure defined in IaC (CloudFormation StackSets) to prevent configuration drift.

**Anti-Pattern Case**: Customer requests a single EC2 instance or single-AZ RDS for "cost savings" in production
- Clarification: Ask the defined RTO and RPO requirements. A single EC2 instance with no Auto Scaling group has no automatic instance recovery — manual intervention is required, with RTO measured in the time it takes an operator to respond. An RDS instance without Multi-AZ enabled has no automatic failover; a Multi-AZ RDS failover takes 60–120 seconds and requires Multi-AZ to be pre-enabled (it cannot be enabled during the outage). Present the quantified cost of downtime (based on the business's own RTO/RPO impact analysis) against the incremental cost of Multi-AZ and Auto Scaling. If the customer confirms they accept the RTO/RPO implications in writing, document the decision and the accepted risk — do not proceed silently.
