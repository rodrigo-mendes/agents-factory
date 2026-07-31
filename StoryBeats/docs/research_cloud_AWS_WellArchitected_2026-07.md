# AWS Well-Architected Framework — Research Knowledge Base
**Edition**: AWS Well-Architected Framework — Publication date **November 6, 2024** (current published stable edition, verified July 2026; referred to in this brief as "AWS WAF 2025")
**Scope**: All six pillars — general production workloads
**Audience**: Cloud Architects and Tech Leads
**Research Date**: 2026-07-31
**Source**: https://docs.aws.amazon.com/wellarchitected/

> **Version-Absolutism note**: This knowledge base pins the **November 6, 2024** edition of the AWS Well-Architected Framework, which remains the current published edition as of the research date (2026-07-31). AWS revises the Framework periodically; earlier six-pillar-plus-legacy revisions (e.g., pre-2020 five-pillar editions, pre-Sustainability-pillar editions) are treated as **out-of-date and must not be mixed** with the guidance here. Per the Source Hierarchy rule, this edition is > 12 months old but is accepted because it **documents the current stable release**.

---

## Executive Summary

The **AWS Well-Architected Framework (WAF)** is AWS's canonical set of foundational questions and best practices for designing, building, and operating workloads in the AWS Cloud. It is **not an audit mechanism**; it is a structured, constructive review of architectural trade-offs. The current edition (published November 6, 2024) is organized around **six pillars**: **Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, and Sustainability**. Each pillar defines design principles, best-practice areas, and a set of review questions (numbered `OPS`, `SEC`, `REL`, `PERF`, `COST`, `SUS`). AWS operationalizes the Framework through the free **AWS Well-Architected Tool** (WA Tool), **Well-Architected Labs**, and pillar-specific whitepapers. For general production workloads, the Framework is applied continuously (design-time and via periodic reviews) to measure architecture against best practice and prioritize remediation.
Source: [AWS Well-Architected Framework — Welcome](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html) — accessed 2026-07-31.

---

## Framework Pillars

> All six pillar definitions and design-principle lists below are quoted/summarized from the **November 6, 2024** edition of the AWS Well-Architected Framework. Every pillar entry cites its official source URL and access date.

### Pillar: Operational Excellence

**Definition**: The ability to support development and run workloads effectively, gain insight into their operations, and continuously improve supporting processes and procedures to deliver business value. (AWS WAF 2024 edition, Operational Excellence pillar.)

**Key Design Principles** (verbatim from official docs):
1. **Organize teams around business outcomes** — the operating model (people, process, technology) should be aligned to and incentivized by business outcomes and KPIs.
2. **Implement observability for actionable insights** — establish KPIs and use telemetry (metrics, logs, traces) to make informed decisions and act when outcomes are at risk.
3. **Safely automate where possible** — define workload and operations as code; automate responses to events with guardrails (rate control, error thresholds, approvals).
4. **Make frequent, small, reversible changes** — design loosely coupled, scalable workloads so components can be updated with a small blast radius and fast rollback.
5. **Refine operations procedures frequently** — review and validate procedures regularly; close gaps and communicate updates.
6. **Anticipate failure** — run failure scenarios (game days) to understand risk profile and test team/procedure response.
7. **Learn from all operational events and metrics** — drive improvement from lessons learned and share across the organization.
8. **Use managed services** — reduce operational burden with AWS managed services.

**Top Best Practices** (for general production workloads):
1. Define **operations as code** (IaC) with CloudFormation/CDK/Terraform and version control everything, including runbooks.
2. Implement **observability**: CloudWatch metrics/alarms/dashboards, centralized logs (CloudWatch Logs), and distributed tracing (AWS X-Ray).
3. Use **CI/CD pipelines** (CodePipeline/CodeBuild/CodeDeploy or equivalent) with automated testing and progressive/canary deployment.
4. Maintain **runbooks and playbooks** for routine operations and incident response; validate them via game days.
5. Conduct **post-incident analysis** (blameless retrospectives) and feed learnings back into procedures.

**Top 3 Assessment Questions**:
- **OPS 4**: How do you implement observability in your workload?
- **OPS 6**: How do you mitigate deployment risks?
- **OPS 8**: How do you utilize workload observability in your organization?

Source: [Operational Excellence Pillar — Design principles](https://docs.aws.amazon.com/wellarchitected/latest/framework/oe-design-principles.html) — accessed 2026-07-31.

---

### Pillar: Security

**Definition**: The ability to protect data, systems, and assets to take advantage of cloud technologies to improve your security. It covers the confidentiality and integrity of data, identifying and managing who can do what (privilege management), protecting systems, and establishing controls to detect security events. (AWS WAF 2024 edition, Security pillar.)

**Key Design Principles** (verbatim from official docs):
1. **Implement a strong identity foundation** — least privilege, separation of duties, centralized identity management; eliminate reliance on long-term static credentials.
2. **Maintain traceability** — monitor, alert, and audit actions and changes in real time; integrate logs/metrics with automated response.
3. **Apply security at all layers** — defense in depth across edge, VPC, load balancing, compute, OS, application, and code.
4. **Automate security best practices** — controls defined and managed as code in version-controlled templates.
5. **Protect data in transit and at rest** — classify data by sensitivity; use encryption, tokenization, and access control.
6. **Keep people away from data** — reduce/eliminate direct human access and manual data processing.
7. **Prepare for security events** — incident-management policy/process, simulations, and automated detection/response.

**Top Best Practices** (for general production workloads):
1. **Federated SSO + IAM Identity Center**; use **IAM roles** and short-lived credentials — no long-term IAM user keys.
2. Enforce **least-privilege IAM policies**; use permissions boundaries and Service Control Policies (SCPs) via AWS Organizations.
3. **Encrypt everywhere**: KMS-managed encryption at rest (S3, EBS, RDS, DynamoDB) and TLS in transit (ACM certificates).
4. **Detective controls**: CloudTrail (all regions), AWS Config, GuardDuty, Security Hub, and centralized logging.
5. **Edge protection** for public endpoints: AWS WAF + AWS Shield, plus VPC segmentation and Security Groups/NACLs.

**Top 3 Assessment Questions**:
- **SEC 1**: How do you securely operate your workload?
- **SEC 2**: How do you manage identities for people and machines?
- **SEC 8**: How do you protect your data at rest?

Source: [Security Pillar — Design principles](https://docs.aws.amazon.com/wellarchitected/latest/framework/sec-design.html) — accessed 2026-07-31.

---

### Pillar: Reliability

**Definition**: The ability of a workload to perform its intended function correctly and consistently when it's expected to. This includes the ability to operate and test the workload through its total lifecycle. It covers foundations, workload architecture, change management, and failure management. (AWS WAF 2024 edition, Reliability pillar.)

**Key Design Principles** (verbatim from official docs):
1. **Automatically recover from failure** — monitor business-value KPIs and trigger automated notification, tracking, and recovery when thresholds are breached.
2. **Test recovery procedures** — use automation to simulate failures and validate recovery paths *before* real failures.
3. **Scale horizontally to increase aggregate workload availability** — replace one large resource with multiple small ones; avoid a single common point of failure.
4. **Stop guessing capacity** — monitor demand and utilization; automate adding/removing resources to avoid over- or under-provisioning.
5. **Manage change through automation** — make infrastructure changes via automation (including changes to the automation itself), tracked and reviewed.

**Top Best Practices** (for general production workloads):
1. **Multi-AZ** deployment for all stateful/critical tiers (RDS Multi-AZ, Multi-AZ compute behind ELB).
2. **Auto Scaling** (EC2 Auto Scaling / application auto scaling) with health checks and self-healing.
3. **Manage Service Quotas** proactively (Service Quotas + CloudWatch alarms on quota usage).
4. **Backup + point-in-time recovery** (AWS Backup, RDS PITR, DynamoDB PITR) with tested restores.
5. **Define and test a DR strategy** with explicit RTO/RPO (Backup & Restore, Pilot Light, Warm Standby, or Multi-site active/active).

**Top 3 Assessment Questions**:
- **REL 10**: How do you use fault isolation to protect your workload?
- **REL 11**: How do you design your workload to withstand component failures?
- **REL 13**: How do you plan for disaster recovery (DR)?

Source: [Reliability Pillar — Design principles](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/design-principles.html) — accessed 2026-07-31.

---

### Pillar: Performance Efficiency

**Definition**: The ability to use computing resources efficiently to meet system requirements, and to maintain that efficiency as demand changes and technologies evolve. It covers selection (compute, storage, database, network), review, monitoring, and trade-offs. (AWS WAF 2024 edition, Performance Efficiency pillar.)

**Key Design Principles** (verbatim from official docs):
1. **Democratize advanced technologies** — consume complex tech (NoSQL, ML, transcoding) as managed services instead of self-hosting.
2. **Go global in minutes** — deploy to multiple AWS Regions for lower latency at minimal cost.
3. **Use serverless architectures** — remove the need to run/maintain physical servers; lower transactional cost at cloud scale.
4. **Experiment more often** — run comparative tests across instance types, storage, and configurations quickly.
5. **Consider mechanical sympathy** — choose the technology approach that best fits your goals and data access patterns.

**Top Best Practices** (for general production workloads):
1. **Right-size** compute/storage to workload profile; re-evaluate with Compute Optimizer.
2. Use **caching** (CloudFront edge, ElastiCache, DynamoDB DAX) to reduce latency and backend load.
3. Select **purpose-built data stores** (mechanical sympathy): DynamoDB for key-value, Aurora/RDS for relational, OpenSearch for search.
4. Adopt **serverless/managed** compute (Lambda, Fargate) to scale automatically with demand.
5. **Continuously monitor** performance KPIs (CloudWatch) and load-test to validate against SLAs.

**Top 3 Assessment Questions**:
- **PERF 2**: How do you select your compute solution?
- **PERF 3**: How do you store, manage, and access data in your workload?
- **PERF 5**: How do you monitor your resources to ensure they are performing?

Source: [Performance Efficiency Pillar — Design principles](https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/design-principles.html) — accessed 2026-07-31.

---

### Pillar: Cost Optimization

**Definition**: The ability to run systems to deliver business value at the lowest price point. It covers cloud financial management, expenditure and usage awareness, cost-effective resources, managing demand/supply, and optimizing over time. (AWS WAF 2024 edition, Cost Optimization pillar.)

**Key Design Principles** (verbatim from official docs):
1. **Implement cloud financial management** — invest in Cloud Financial Management (CFM) capability: knowledge, programs, resources, processes.
2. **Adopt a consumption model** — pay only for what you consume; scale usage with business requirements (e.g., stop non-prod off-hours).
3. **Measure overall efficiency** — measure business output vs. delivery cost to understand gains.
4. **Stop spending money on undifferentiated heavy lifting** — let AWS operate data centers and managed services so you focus on business.
5. **Analyze and attribute expenditure** — use tagging/cost tools to attribute cost to workloads and owners; measure ROI.

**Top Best Practices** (for general production workloads):
1. **Cost visibility**: Cost Explorer, AWS Cost & Usage Report (CUR), and cost allocation tags.
2. **Budgets + alerts**: AWS Budgets with threshold notifications; anomaly detection.
3. **Commitment discounts**: Savings Plans / Reserved Instances for steady-state usage.
4. **Right-size + eliminate waste**: Compute Optimizer, delete unattached EBS/idle resources, S3 lifecycle tiering.
5. **Match supply to demand**: Auto Scaling, scheduled scaling, and Spot for fault-tolerant workloads.

**Top 3 Assessment Questions**:
- **COST 2**: How do you govern usage?
- **COST 5**: How do you evaluate cost when you select services?
- **COST 6**: How do you meet cost targets when you select resource type, size, and number?

Source: [Cost Optimization Pillar — Design principles](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/design-principles.html) — accessed 2026-07-31.

---

### Pillar: Sustainability

**Definition**: The ability to continually improve sustainability impacts by reducing energy consumption and increasing efficiency across all components of a workload by maximizing the benefits from the provisioned resources and minimizing the total resources required. It focuses on the environmental impact — especially energy consumption and efficiency — of running cloud workloads. (AWS WAF 2024 edition, Sustainability pillar.)

**Key Design Principles** (verbatim from official docs — six principles):
1. **Understand your impact** — measure and model the full impact of the workload (including customer use and decommissioning); establish KPIs (resources/emissions per unit of work).
2. **Establish sustainability goals** — set long-term goals (e.g., reduce resources per transaction); architect so growth reduces impact intensity per unit.
3. **Maximize utilization** — right-size and drive high utilization; two hosts at 30% are less efficient than one at 60%; minimize idle resources.
4. **Anticipate and adopt new, more efficient hardware and software offerings** — design for flexibility to rapidly adopt efficient technologies (e.g., Graviton).
5. **Use managed services** — shared, at-scale managed services (e.g., Fargate, S3 lifecycle tiering, EC2 Auto Scaling) maximize resource utilization.
6. **Reduce the downstream impact of your cloud workloads** — reduce energy/resources customers need to use your services; test on device farms.

**Top Best Practices** (for general production workloads):
1. **Right-size and maximize utilization**; consolidate idle/underutilized resources.
2. Adopt **energy-efficient hardware** (AWS Graviton-based instances) where compatible.
3. Use **managed and serverless** services (Fargate, Lambda) to increase shared-infrastructure efficiency.
4. **Storage tiering**: S3 Lifecycle policies / Intelligent-Tiering to move cold data to lower-impact tiers.
5. Optimize **data movement and retention** — delete unneeded data; minimize cross-Region transfer.

**Top 3 Assessment Questions**:
- **SUS 2**: How do you align cloud resources to your demand?
- **SUS 4**: How do you take advantage of data management policies and patterns to support your sustainability goals?
- **SUS 5**: How do you select and use cloud hardware and services in your architecture to support your sustainability goals?

Source: [Sustainability Pillar — Design principles](https://docs.aws.amazon.com/wellarchitected/latest/framework/sus-design-principles.html) — accessed 2026-07-31.

---

## Mandatory Patterns (Always-Do)

> Non-negotiable architecture standards for AWS production workloads, aligned to the AWS WAF 2024 edition pillars. Each includes a representative verification (adapt to your environment).

### Pattern 1: Multi-AZ Deployment for Stateful Services
- **Why**: **Reliability** — fault isolation (REL 10) so a single Availability Zone failure does not take down the workload.
- **AWS Service**: Amazon RDS/Aurora (Multi-AZ), EC2 Auto Scaling across AZs, ELB (ALB/NLB), ElastiCache Multi-AZ.
- **Architecture Decision**: Deploy every stateful tier across >= 2 AZs (Aurora recommends 3). Enable `MultiAZ` on RDS; spread ASG across AZ subnets; front with a cross-AZ load balancer.
- **Verification**:
  ```bash
  aws rds describe-db-instances --query "DBInstances[].{Id:DBInstanceIdentifier,MultiAZ:MultiAZ}"
  # Expected: MultiAZ = true for all production DBs
  ```
- **Trade-offs**: ~2x standby cost for RDS Multi-AZ; brief failover (typically 60–120s for RDS); higher inter-AZ data transfer.
- **Source**: [Reliability Pillar — REL 10 Fault isolation](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_fault_isolation_multiaz_region_system.html) — accessed 2026-07-31.

### Pattern 2: Encryption at Rest and in Transit
- **Why**: **Security** — "Protect data in transit and at rest" design principle (SEC 8, SEC 9).
- **AWS Service**: AWS KMS, ACM (TLS certs); native encryption in S3, EBS, RDS, DynamoDB, EFS.
- **Architecture Decision**: Enable KMS encryption on all data stores (prefer customer-managed keys for auditability); enforce TLS 1.2+ via ACM on ALB/CloudFront/API Gateway; set S3 bucket policies to deny non-TLS (`aws:SecureTransport=false`).
- **Verification**:
  ```bash
  aws s3api get-bucket-encryption --bucket <bucket>
  aws ec2 describe-volumes --query "Volumes[?Encrypted==\`false\`].VolumeId"
  # Expected: encryption configured; no unencrypted volumes returned
  ```
- **Trade-offs**: Negligible latency; KMS API request costs; key lifecycle/rotation management overhead.
- **Source**: [Security Pillar — SEC 8 Protecting data at rest](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-data-at-rest.html) — accessed 2026-07-31.

### Pattern 3: IAM Least-Privilege with Roles (No Long-Term Credentials)
- **Why**: **Security** — "Implement a strong identity foundation… eliminate reliance on long-term static credentials" (SEC 2, SEC 3).
- **AWS Service**: AWS IAM (roles), IAM Identity Center (SSO), STS, permissions boundaries.
- **Architecture Decision**: Use IAM roles for workloads (EC2 instance profiles, ECS task roles, Lambda execution roles, IRSA for EKS). Human access via IAM Identity Center federation with short-lived STS credentials. Scope policies to specific actions/resources; add permissions boundaries.
- **Verification**:
  ```bash
  aws iam generate-credential-report && aws iam get-credential-report --output text --query Content | base64 -d
  aws accessanalyzer list-findings --analyzer-arn <arn>
  # Expected: no active long-lived user access keys on workloads; IAM Access Analyzer clean
  ```
- **Trade-offs**: SSO/federation setup effort; role assumption adds indirection for break-glass access.
- **Source**: [Security Pillar — SEC 3 Permissions management](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/permissions-management.html) — accessed 2026-07-31.

### Pattern 4: VPC with Public/Private Subnet Segmentation + Security Groups
- **Why**: **Security / Reliability** — "Apply security at all layers" (defense in depth); network isolation.
- **AWS Service**: Amazon VPC, subnets, route tables, Internet Gateway, NAT Gateway, Security Groups, Network ACLs.
- **Architecture Decision**: Public subnets only for internet-facing load balancers/NAT; application and data tiers in private subnets. Egress via NAT Gateway. Security Groups reference each other (SG-to-SG) rather than CIDRs; least-privilege ports.
- **Verification**:
  ```bash
  aws ec2 describe-instances --query "Reservations[].Instances[?PublicIpAddress!=null].InstanceId"
  # Expected: no application/data instances with public IPs
  ```
- **Trade-offs**: NAT Gateway hourly + data-processing cost; added routing complexity.
- **Source**: [Security Pillar — SEC 5 Protecting networks](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-networks.html) — accessed 2026-07-31.

### Pattern 5: Centralized Logging and Auditing (CloudTrail + CloudWatch)
- **Why**: **Security / Operational Excellence** — "Maintain traceability"; observability (OPS 4, SEC 4).
- **AWS Service**: AWS CloudTrail (organization trail), CloudWatch Logs, CloudWatch metrics/alarms, optionally centralized logging account.
- **Architecture Decision**: Enable an **organization-wide, multi-Region CloudTrail** delivering to a dedicated, access-restricted, encrypted S3 bucket with log-file validation. Centralize CloudWatch Logs; alarm on security-relevant events.
- **Verification**:
  ```bash
  aws cloudtrail describe-trails --query "trailList[].{Name:Name,MultiRegion:IsMultiRegionTrail,Org:IsOrganizationTrail}"
  aws cloudtrail get-trail-status --name <trail>
  # Expected: IsMultiRegionTrail=true, IsLogging=true
  ```
- **Trade-offs**: S3 storage + CloudWatch ingestion cost; log volume management.
- **Source**: [Security Pillar — SEC 4 Detection](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/detection.html) — accessed 2026-07-31.

### Pattern 6: Automated Backup and Point-in-Time Recovery
- **Why**: **Reliability** — failure management; recover from data loss (REL 9).
- **AWS Service**: AWS Backup, RDS/Aurora automated backups + PITR, DynamoDB PITR, EBS snapshots.
- **Architecture Decision**: Centralize with **AWS Backup** plans (frequency + retention aligned to RPO); enable PITR on RDS/DynamoDB; copy backups cross-Region/cross-account for ransomware/DR resilience; periodically **test restores**.
- **Verification**:
  ```bash
  aws backup list-backup-plans
  aws dynamodb describe-continuous-backups --table-name <table>
  # Expected: PITR ENABLED; backup plan covering all production resources
  ```
- **Trade-offs**: Snapshot storage cost; cross-Region copy transfer cost.
- **Source**: [Reliability Pillar — REL 9 Back up data](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_backing_up_data_identified_backups_data.html) — accessed 2026-07-31.

### Pattern 7: Infrastructure Tagging Strategy
- **Why**: **Cost Optimization / Operational Excellence** — "Analyze and attribute expenditure" (COST 3); governance.
- **AWS Service**: AWS resource tags, cost allocation tags, AWS Organizations Tag Policies, Resource Groups.
- **Architecture Decision**: Mandate a tag taxonomy (e.g., `Environment`, `Owner`, `CostCenter`, `Application`, `DataClassification`). Enforce via **Tag Policies** and **SCPs**; activate cost allocation tags in Billing.
- **Verification**:
  ```bash
  aws resourcegroupstaggingapi get-resources --tag-filters Key=Environment
  aws organizations describe-policy --policy-id <tag-policy-id>
  # Expected: all production resources carry mandatory tags
  ```
- **Trade-offs**: Governance overhead; retro-tagging existing estate.
- **Source**: [Cost Optimization Pillar — COST 3 Monitor usage and cost](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/cost_monitor_usage_tagging.html) — accessed 2026-07-31.

### Pattern 8: Use AWS Secrets Manager for Secrets
- **Why**: **Security** — "Keep people away from data"; eliminate hardcoded/static credentials (SEC 2).
- **AWS Service**: AWS Secrets Manager (or SSM Parameter Store SecureString for simpler cases).
- **Architecture Decision**: Store DB credentials, API keys, tokens in Secrets Manager with **automatic rotation** (native rotation for RDS/Aurora/Redshift/DocumentDB). Grant read access via IAM roles; never bake secrets into images, env files, or code.
- **Verification**:
  ```bash
  aws secretsmanager describe-secret --secret-id <name> --query "RotationEnabled"
  # Expected: RotationEnabled = true for credential secrets
  ```
- **Trade-offs**: Per-secret monthly + per-10k-API cost; rotation Lambda maintenance.
- **Source**: [Security Pillar — SEC 2 Identities](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/identity-management.html) — accessed 2026-07-31.

### Pattern 9: DR Strategy with Defined RTO/RPO
- **Why**: **Reliability** — plan for disaster recovery (REL 13).
- **AWS Service**: AWS Backup, AWS Elastic Disaster Recovery (DRS), Route 53 (failover), cross-Region replication (S3 CRR, Aurora Global Database, DynamoDB Global Tables).
- **Architecture Decision**: Select one of the four AWS DR strategies by RTO/RPO: **Backup & Restore** (hours), **Pilot Light** (tens of minutes), **Warm Standby** (minutes), **Multi-site active/active** (near-zero). Document RTO/RPO per workload and test failover.
- **Verification**:
  ```bash
  aws route53 list-health-checks
  aws s3api get-bucket-replication --bucket <bucket>
  # Expected: replication/health checks consistent with chosen DR tier; documented RTO/RPO
  ```
- **Trade-offs**: Cost rises steeply from Backup&Restore -> Active/Active; complexity of data consistency across Regions.
- **Source**: [Disaster Recovery of Workloads on AWS: Recovery in the Cloud (whitepaper)](https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html) — accessed 2026-07-31. ⚠️ Whitepaper > 12 months old; retained as the current published DR reference cited by the Reliability pillar.

### Pattern 10: AWS WAF + Shield for Public-Facing APIs/Apps
- **Why**: **Security** — "Apply security at all layers"; protect edge (SEC 5).
- **AWS Service**: AWS WAF (web ACLs), AWS Shield Standard (automatic) / Shield Advanced, CloudFront, API Gateway/ALB.
- **Architecture Decision**: Attach an AWS WAF web ACL (AWS Managed Rules: Core Rule Set, Known Bad Inputs, IP reputation, rate-based rules) to CloudFront/ALB/API Gateway. Shield Standard is automatic; use Shield Advanced for high-risk internet-facing workloads (DDoS response + cost protection).
- **Verification**:
  ```bash
  aws wafv2 list-web-acls --scope CLOUDFRONT
  aws wafv2 get-web-acl --name <acl> --scope REGIONAL --id <id>
  # Expected: managed rule groups + rate-based rule attached to public endpoints
  ```
- **Trade-offs**: WAF per-rule + per-request cost; Shield Advanced monthly commitment; rule tuning to avoid false positives.
- **Source**: [Security Pillar — SEC 5 Protecting networks](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-networks.html) — accessed 2026-07-31.

### Pattern 11: Cost Alerting with AWS Budgets
- **Why**: **Cost Optimization** — govern usage; expenditure awareness (COST 2, COST 3).
- **AWS Service**: AWS Budgets, AWS Cost Anomaly Detection, Cost Explorer.
- **Architecture Decision**: Create cost/usage budgets per account and per tag (e.g., per `Environment`/`Application`) with SNS/email alerts at thresholds (e.g., 50/80/100% and forecasted). Enable Cost Anomaly Detection for automatic drift alerts.
- **Verification**:
  ```bash
  aws budgets describe-budgets --account-id <id>
  aws ce get-anomaly-monitors
  # Expected: at least one budget with notifications per production account
  ```
- **Trade-offs**: First budgets are free (small per-budget/day cost beyond free tier); alert tuning to avoid noise.
- **Source**: [Cost Optimization Pillar — COST 2 Govern usage](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/cost_govern_usage_enforce_policies.html) — accessed 2026-07-31.

### Pattern 12: Guardrails via AWS Organizations (SCPs) + Baseline Detective Controls
- **Why**: **Security / Operational Excellence** — governance, "automate security best practices" (SEC 1).
- **AWS Service**: AWS Organizations, Service Control Policies, AWS Config, GuardDuty, Security Hub, Control Tower.
- **Architecture Decision**: Multi-account landing zone (Control Tower); SCPs to deny high-risk actions (e.g., disabling CloudTrail/GuardDuty, leaving approved Regions); org-level Config rules, GuardDuty, and Security Hub aggregated in a security/audit account.
- **Verification**:
  ```bash
  aws organizations list-policies --filter SERVICE_CONTROL_POLICY
  aws securityhub get-enabled-standards
  # Expected: SCPs applied to OUs; Security Hub standards enabled org-wide
  ```
- **Trade-offs**: Landing-zone setup effort; SCP misconfiguration can block legitimate actions.
- **Source**: [Security Pillar — SEC 1 Securely operate your workload](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/security-foundations.html) — accessed 2026-07-31.

---

## Architectural Decisions (Ask-First)

> Multiple valid approaches exist; the "right" answer depends on workload context. Cost profiles are **relative order-of-magnitude** guidance, not quotes.

### Decision 1: Compute — Lambda vs. ECS/Fargate vs. EC2
| Option | AWS Service | Optimizes | Sacrifices | Best When |
|---|---|---|---|---|
| Serverless functions | AWS Lambda | Zero server ops, per-ms billing, auto-scale | 15-min max, cold starts, packaging limits | Event-driven, spiky, short tasks |
| Serverless containers | ECS on Fargate | No server mgmt, container portability | Less granular scaling than Lambda | Long-running services, container workloads |
| Full VMs | Amazon EC2 | Max control, any workload, cheapest at high steady utilization | You manage OS/scaling/patching | Legacy, GPU, specialized/steady workloads |

- **Cost Profile**: Low steady load -> Lambda cheapest; high steady 24/7 -> EC2 (with Savings Plans) typically cheapest; Fargate mid, no idle-capacity waste.
- **Scaling Characteristics**: Lambda scales per-request (concurrency limits/account quotas); Fargate scales tasks (slower than Lambda); EC2 via Auto Scaling (minutes, AMI/warm-pool dependent).
- **Lock-in Assessment**: Lambda highest (event model/runtime); Fargate/ECS moderate (containers portable, orchestration AWS-specific); EC2 lowest.
- **Ask The Architect**: "What is the request pattern (spiky vs. steady), max execution time, and how portable must the runtime be off AWS?"
- **Source**: [Performance Efficiency Pillar — PERF 2 Selecting compute](https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/compute-architecture.html) — accessed 2026-07-31.

### Decision 2: Data — RDS vs. DynamoDB vs. Aurora
| Option | AWS Service | Optimizes | Sacrifices | Best When |
|---|---|---|---|---|
| Managed relational | Amazon RDS | Standard SQL engines, familiar ops | Vertical scaling ceiling | Relational workloads, moderate scale |
| Cloud-native relational | Amazon Aurora | MySQL/PostgreSQL compat, high throughput, storage auto-scale, Global DB | Higher baseline cost than RDS | High-scale relational + multi-Region |
| Managed NoSQL | Amazon DynamoDB | Single-digit-ms at any scale, serverless | No joins/complex queries, data modeling discipline | Key-value/high-scale, predictable access patterns |

- **Cost Profile**: DynamoDB on-demand cheap at low/spiky traffic; RDS predictable instance cost; Aurora higher baseline but efficient at scale (I/O-optimized options).
- **Scaling Characteristics**: RDS = vertical + read replicas; Aurora = up to 15 read replicas, auto storage to 128 TiB, Global DB; DynamoDB = horizontal, effectively unbounded with good keys.
- **Lock-in Assessment**: RDS lowest (portable engines); Aurora moderate (wire-compatible but AWS-specific features); DynamoDB highest (proprietary API/model).
- **Ask The Architect**: "Do you need relational integrity/joins, what is peak throughput, and is multi-Region active-active required?"
- **Source**: [Performance Efficiency Pillar — PERF 3 Data management](https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/data-management.html) — accessed 2026-07-31.

### Decision 3: Messaging — SQS vs. SNS vs. EventBridge vs. Kinesis
| Option | AWS Service | Optimizes | Sacrifices | Best When |
|---|---|---|---|---|
| Queue | Amazon SQS | Decoupling, at-least-once, buffering | No fan-out (single consumer group) | Work queues, load leveling |
| Pub/sub | Amazon SNS | Fan-out to many subscribers | No replay, no ordering (std) | Notifications, 1-to-many push |
| Event bus | Amazon EventBridge | Content filtering/routing, SaaS + schema registry | Higher latency than SNS, throughput quotas | Event-driven integration/routing |
| Streaming | Amazon Kinesis Data Streams | Ordered, replayable, high-throughput streams | Shard mgmt, consumer complexity | Real-time analytics, ordered event streams |

- **Cost Profile**: SQS/SNS per-request (cheap); EventBridge per-event; Kinesis per-shard-hour + payload (higher for sustained streams).
- **Scaling Characteristics**: SQS/SNS effectively unlimited; EventBridge quota-based; Kinesis scales by shards (or on-demand mode).
- **Lock-in Assessment**: All AWS-specific; Kafka (MSK) is the more portable streaming alternative if portability matters.
- **Ask The Architect**: "Fan-out or single consumer? Do you need ordering/replay? Real-time analytics or simple decoupling?"
- **Source**: [Reliability Pillar — REL 4 Distributed system interactions](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_prevent_interaction_failure_throttle_requests.html) — accessed 2026-07-31.

### Decision 4: Region — Single vs. Multi-Region (Active-Passive vs. Active-Active)
| Option | AWS Service | Optimizes | Sacrifices | Best When |
|---|---|---|---|---|
| Single Region (Multi-AZ) | ELB + Multi-AZ | Simplicity, low cost, consistency | Region-level outage exposure | Most workloads; RTO/RPO tolerate Region risk |
| Multi-Region active-passive | Route 53 failover + replication | Regional DR, moderate cost | Standby cost, failover orchestration | Strict RTO/RPO, regulated DR |
| Multi-Region active-active | Global DB / DynamoDB Global Tables + Route 53 | Lowest RTO, global low latency | Highest cost/complexity, conflict resolution | Global scale, near-zero downtime SLAs |

- **Cost Profile**: Single Region cheapest; active-passive adds standby + replication; active-active roughly doubles infra + cross-Region transfer.
- **Scaling Characteristics**: Active-active distributes globally; consistency model becomes eventual across Regions.
- **Lock-in Assessment**: Neutral to AWS; complexity is architectural, not lock-in.
- **Ask The Architect**: "What are the exact RTO/RPO and are there data-residency or global-latency requirements that justify multi-Region cost?"
- **Source**: [Disaster Recovery of Workloads on AWS (whitepaper)](https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html) — accessed 2026-07-31. ⚠️ > 12 months old; current published DR reference.

### Decision 5: Account — Single vs. Multi-Account (AWS Organizations)
| Option | AWS Service | Optimizes | Sacrifices | Best When |
|---|---|---|---|---|
| Single account | 1 AWS account | Simplicity | Weak blast-radius isolation, quota contention | Very small/POC workloads |
| Multi-account | AWS Organizations + Control Tower | Strong isolation, per-env guardrails, billing separation | Setup + cross-account complexity | Any production/enterprise workload |

- **Cost Profile**: No per-account fee; consolidated billing can improve volume discounts; some duplicated baseline tooling cost.
- **Scaling Characteristics**: Per-account service quotas reduce noisy-neighbor blast radius; scales cleanly with OUs.
- **Lock-in Assessment**: Organizations is AWS-specific governance; account structure is portable conceptually.
- **Ask The Architect**: "How many environments/teams, and what isolation/compliance boundaries do you need? (AWS recommends multi-account for production.)"
- **Source**: [Security Pillar — AWS account management and separation](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/aws-account-management-and-separation.html) — accessed 2026-07-31.

### Decision 6: Network — VPC Peering vs. Transit Gateway vs. PrivateLink
| Option | AWS Service | Optimizes | Sacrifices | Best When |
|---|---|---|---|---|
| VPC Peering | VPC Peering | Simple, low cost, 1:1 | No transitive routing, O(n^2) mesh | Few VPCs, direct connectivity |
| Hub-and-spoke | AWS Transit Gateway | Transitive routing at scale, central control | Per-attachment + data cost | Many VPCs/accounts/on-prem |
| Private service access | AWS PrivateLink | Exposes a single service privately, no route sharing | Per-endpoint cost, service-granular only | Consuming/exposing a specific service privately |

- **Cost Profile**: Peering cheapest (data transfer only); TGW adds attachment + processing; PrivateLink per-endpoint-hour + data.
- **Scaling Characteristics**: Peering does not scale (no transitivity); TGW scales to thousands of attachments; PrivateLink scales per service.
- **Lock-in Assessment**: All AWS-native networking constructs.
- **Ask The Architect**: "How many VPCs/accounts must interconnect, do you need transitive routing, or just private access to one service?"
- **Source**: [Reliability Pillar — REL 2 Network topology](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_planning_network_topology_ha_conn_private_networks.html) — accessed 2026-07-31.

### Decision 7: Caching — ElastiCache vs. CloudFront vs. DAX
| Option | AWS Service | Optimizes | Sacrifices | Best When |
|---|---|---|---|---|
| In-memory data cache | Amazon ElastiCache (Redis/Valkey/Memcached) | Sub-ms app-tier caching, flexible | You manage caching logic/invalidation | Session/store/DB query caching |
| Edge/content cache | Amazon CloudFront | Global edge caching, offloads origin | Cache-control tuning, invalidation cost | Static/dynamic web content, API caching at edge |
| DynamoDB accelerator | Amazon DynamoDB DAX | Microsecond reads for DynamoDB, no app changes | DynamoDB-only, eventual consistency for cache | Read-heavy DynamoDB workloads |

- **Cost Profile**: CloudFront cheap at high cache-hit; ElastiCache per-node-hour; DAX per-node-hour.
- **Scaling Characteristics**: CloudFront scales globally automatically; ElastiCache/DAX scale by cluster nodes/shards.
- **Lock-in Assessment**: CloudFront/DAX AWS-specific; ElastiCache (Redis/Valkey/Memcached) is portable open-source protocol.
- **Ask The Architect**: "Are you caching content at the edge, application/DB data, or specifically DynamoDB reads?"
- **Source**: [Performance Efficiency Pillar — Caching](https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/caching.html) — accessed 2026-07-31.

### Decision 8: Container Orchestration — EKS vs. ECS vs. App Runner
| Option | AWS Service | Optimizes | Sacrifices | Best When |
|---|---|---|---|---|
| Managed Kubernetes | Amazon EKS | K8s ecosystem, portability, advanced scheduling | Operational complexity, K8s expertise | K8s standardization, multi-cloud portability |
| AWS-native orchestration | Amazon ECS | Simpler than K8s, deep AWS integration | AWS-specific, less ecosystem | AWS-centric teams wanting low ops |
| Fully managed PaaS | AWS App Runner | Push-to-deploy web apps, zero infra | Limited config/control | Simple web apps/APIs, small teams |

- **Cost Profile**: App Runner simplest per-usage; ECS on Fargate no cluster fee (pay tasks); EKS adds per-cluster control-plane hourly fee.
- **Scaling Characteristics**: All auto-scale; EKS most flexible (HPA/Karpenter); App Runner most opinionated/automatic.
- **Lock-in Assessment**: EKS lowest (standard Kubernetes); ECS/App Runner higher (AWS-specific).
- **Ask The Architect**: "Do you need Kubernetes portability/ecosystem, or is minimal ops the priority? How much control do you require?"
- **Source**: [Performance Efficiency Pillar — PERF 2 Selecting compute](https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/compute-architecture.html) — accessed 2026-07-31.

---

## Architecture Anti-Patterns (Never-Do)

> Each anti-pattern includes ❌ Wrong / ✅ Correct with exact AWS service names.

### Anti-Pattern 1: Single-AZ RDS in Production
- **Why**: **Reliability** — no automatic failover; an AZ outage or instance failure causes downtime and possible data loss (REL 10).
- **Risk Level**: HIGH
- **Blast Radius**: Entire application dependent on the database.
- ❌ Wrong: Amazon RDS instance with `MultiAZ=false` serving production.
- ✅ Correct: Amazon RDS with `MultiAZ=true` (or Aurora across 3 AZs) + automated backups + PITR.
- **Detection**: AWS Config managed rule `rds-multi-az-support`; CLI `aws rds describe-db-instances --query "DBInstances[?MultiAZ==\`false\`]"`.
- **Impact**: Outage; potential data loss.
- **Source**: [Reliability Pillar — REL 10](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_fault_isolation_multiaz_region_system.html) — accessed 2026-07-31.

### Anti-Pattern 2: S3 Bucket with Block Public Access Disabled
- **Why**: **Security** — public buckets are a leading cause of data breaches (SEC 8).
- **Risk Level**: CRITICAL
- **Blast Radius**: All objects in the bucket exposed to the internet.
- ❌ Wrong: S3 bucket with Block Public Access turned off and a permissive `"Principal":"*"` policy.
- ✅ Correct: S3 **Block Public Access = ON** (account + bucket), private ACLs, access via CloudFront OAC or presigned URLs; SSE-KMS encryption.
- **Detection**: AWS Config `s3-bucket-public-read-prohibited` / `s3-bucket-level-public-access-prohibited`; Security Hub S3 controls; IAM Access Analyzer.
- **Impact**: Data breach; compliance violation.
- **Source**: [Security Pillar — SEC 8 Protecting data at rest](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-data-at-rest.html) — accessed 2026-07-31.

### Anti-Pattern 3: Hardcoded Credentials in Code/Config
- **Why**: **Security** — leaked static credentials enable account compromise (SEC 2).
- **Risk Level**: CRITICAL
- **Blast Radius**: Any resource the credential can access; often lateral movement.
- ❌ Wrong: AWS access keys or DB passwords committed in source, container image, or `.env`.
- ✅ Correct: AWS Secrets Manager / SSM Parameter Store SecureString retrieved at runtime via IAM roles; no static keys.
- **Detection**: Amazon CodeGuru / GuardDuty (compromised-credential findings); secret scanning (e.g., git-secrets); IAM Access Analyzer unused-access.
- **Impact**: Data breach; account takeover.
- **Source**: [Security Pillar — SEC 2 Identities](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/identity-management.html) — accessed 2026-07-31.

### Anti-Pattern 4: Wildcard IAM Policies (`Action:"*"`, `Resource:"*"`)
- **Why**: **Security** — violates least privilege; over-permissioned principals magnify breach impact (SEC 3).
- **Risk Level**: HIGH
- **Blast Radius**: Everything the principal can reach — potentially the whole account.
- ❌ Wrong: IAM policy `{"Effect":"Allow","Action":"*","Resource":"*"}` attached to a workload role.
- ✅ Correct: Scoped policy granting only required actions on specific resource ARNs; permissions boundaries; generated via IAM Access Analyzer policy generation.
- **Detection**: IAM Access Analyzer; AWS Config `iam-policy-no-statements-with-admin-access`; Security Hub IAM controls.
- **Impact**: Privilege escalation; data breach.
- **Source**: [Security Pillar — SEC 3 Permissions management](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/permissions-management.html) — accessed 2026-07-31.

### Anti-Pattern 5: No CloudTrail Enabled
- **Why**: **Security / Operational Excellence** — no audit trail; breaks "Maintain traceability" (SEC 4).
- **Risk Level**: HIGH
- **Blast Radius**: Entire account — no forensic record of API activity.
- ❌ Wrong: Account with CloudTrail disabled or single-Region only.
- ✅ Correct: Organization-wide, multi-Region CloudTrail to an encrypted, access-restricted S3 bucket with log-file validation; SCP denying trail deletion.
- **Detection**: AWS Config `cloudtrail-enabled` / `multi-region-cloudtrail-enabled`; Security Hub CloudTrail controls.
- **Impact**: Compliance failure; inability to investigate incidents.
- **Source**: [Security Pillar — SEC 4 Detection](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/detection.html) — accessed 2026-07-31.

### Anti-Pattern 6: Security Groups with 0.0.0.0/0 on Port 22/3389
- **Why**: **Security** — SSH/RDP open to the internet invites brute-force/exploitation (SEC 5).
- **Risk Level**: CRITICAL
- **Blast Radius**: All instances sharing that Security Group.
- ❌ Wrong: Security Group inbound rule `0.0.0.0/0` on TCP 22 (SSH) or 3389 (RDP).
- ✅ Correct: No public admin ports — use **AWS Systems Manager Session Manager** (no inbound port) or restrict to a bastion/VPN with tight CIDR.
- **Detection**: AWS Config `restricted-ssh` / `restricted-common-ports`; Security Hub `EC2.13`/`EC2.14`.
- **Impact**: Outage; data breach.
- **Source**: [Security Pillar — SEC 5 Protecting networks](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-networks.html) — accessed 2026-07-31.

### Anti-Pattern 7: No Backup/Snapshot Policy
- **Why**: **Reliability** — no recovery from data corruption/deletion/ransomware (REL 9).
- **Risk Level**: HIGH
- **Blast Radius**: Irrecoverable data loss for affected stores.
- ❌ Wrong: RDS/DynamoDB/EBS with no automated backups or PITR.
- ✅ Correct: AWS Backup plans with retention aligned to RPO; RDS/DynamoDB PITR; cross-Region/account copies; tested restores.
- **Detection**: AWS Config `db-instance-backup-enabled`, `dynamodb-pitr-enabled`, `backup-plan-min-frequency-and-min-retention-check`.
- **Impact**: Permanent data loss.
- **Source**: [Reliability Pillar — REL 9](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_backing_up_data_identified_backups_data.html) — accessed 2026-07-31.

### Anti-Pattern 8: Missing Cost Alerts
- **Why**: **Cost Optimization** — undetected spend spikes/runaway resources (COST 2).
- **Risk Level**: MEDIUM
- **Blast Radius**: Account/organization budget.
- ❌ Wrong: No AWS Budgets or anomaly detection; spend discovered on the monthly invoice.
- ✅ Correct: AWS Budgets with threshold + forecast alerts per account/tag; AWS Cost Anomaly Detection enabled.
- **Detection**: `aws budgets describe-budgets`; check Cost Anomaly monitors.
- **Impact**: Cost overrun.
- **Source**: [Cost Optimization Pillar — COST 2 Govern usage](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/cost_govern_usage_enforce_policies.html) — accessed 2026-07-31.

### Anti-Pattern 9: Root Account Used for Operations
- **Why**: **Security** — the root user has unrestricted power and cannot be scoped by IAM policies (SEC 2).
- **Risk Level**: CRITICAL
- **Blast Radius**: Entire AWS account.
- ❌ Wrong: Daily operations, deployments, or API keys under the account root user.
- ✅ Correct: Lock away root (hardware MFA, no access keys); operate via IAM Identity Center roles; use root only for the few tasks that require it.
- **Detection**: AWS Config `root-account-mfa-enabled`, `iam-root-access-key-check`; Security Hub CIS root controls; CloudTrail root-usage alarm.
- **Impact**: Full account compromise.
- **Source**: [Security Pillar — SEC 2 Identities](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/identity-management.html) — accessed 2026-07-31.

### Anti-Pattern 10: No MFA on IAM Users / Root
- **Why**: **Security** — password-only access is trivially phished/brute-forced (SEC 2).
- **Risk Level**: HIGH
- **Blast Radius**: Any principal without MFA; root affects the whole account.
- ❌ Wrong: Root user and IAM users with console passwords but no MFA.
- ✅ Correct: Hardware/virtual MFA on root; enforce MFA via IAM Identity Center / IAM policy condition `aws:MultiFactorAuthPresent`; prefer federated SSO over IAM users.
- **Detection**: AWS Config `mfa-enabled-for-iam-console-access`, `root-account-mfa-enabled`; Security Hub IAM controls.
- **Impact**: Account/identity compromise.
- **Source**: [Security Pillar — SEC 2 Identities](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/identity-management.html) — accessed 2026-07-31.

### Anti-Pattern 11: EC2 Instances in Public Subnet Handling Sensitive Data
- **Why**: **Security** — directly internet-reachable data tier increases attack surface (SEC 5).
- **Risk Level**: HIGH
- **Blast Radius**: The exposed instance and its data stores.
- ❌ Wrong: EC2 with a public IP in a public subnet processing/storing sensitive data.
- ✅ Correct: Data/app tier in **private subnets**; ingress via ALB in public subnet; egress via NAT Gateway; admin via SSM Session Manager.
- **Detection**: AWS Config `ec2-instance-no-public-ip`; Security Hub `EC2.9`.
- **Impact**: Data breach.
- **Source**: [Security Pillar — SEC 5 Protecting networks](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-networks.html) — accessed 2026-07-31.

### Anti-Pattern 12: Unencrypted EBS Volumes or RDS Instances
- **Why**: **Security** — unencrypted data at rest fails "Protect data… at rest" and most compliance regimes (SEC 8).
- **Risk Level**: HIGH
- **Blast Radius**: All data on the affected volume/database.
- ❌ Wrong: EBS volume with `Encrypted=false` or RDS instance with `StorageEncrypted=false`.
- ✅ Correct: Enable **EBS encryption by default** (account setting) and RDS `StorageEncrypted=true` with KMS CMKs; TLS in transit.
- **Detection**: AWS Config `encrypted-volumes`, `rds-storage-encrypted`; Security Hub `EC2.7`, `RDS.3`.
- **Impact**: Data breach; compliance violation.
- **Source**: [Security Pillar — SEC 8 Protecting data at rest](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-data-at-rest.html) — accessed 2026-07-31.

### Anti-Pattern 13: No Health Checks / Manual Scaling for Critical Tiers
- **Why**: **Reliability** — without health checks and Auto Scaling there is no self-healing (REL 11).
- **Risk Level**: MEDIUM
- **Blast Radius**: Application availability during failures/traffic spikes.
- ❌ Wrong: Fixed fleet of EC2 with no ELB health checks or Auto Scaling group.
- ✅ Correct: EC2 Auto Scaling with ELB/target-group health checks; replace unhealthy instances automatically; scale on demand.
- **Detection**: Review ASGs (`aws autoscaling describe-auto-scaling-groups`); confirm health-check type = ELB.
- **Impact**: Outage; degraded performance.
- **Source**: [Reliability Pillar — REL 11 Withstand component failures](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_withstand_component_failures_monitor_health.html) — accessed 2026-07-31.

---

## Service Equivalence Map

> Cross-provider mapping for the service classes referenced above. AWS names are canonical; other providers listed for architect portability discussions.

| Service Class | AWS | GCP | Azure | OCI |
|---|---|---|---|---|
| Compute (VMs) | EC2 | Compute Engine | Azure VMs | OCI Compute |
| Serverless functions | Lambda | Cloud Functions | Azure Functions | OCI Functions |
| Containers (managed) | ECS / EKS | GKE | AKS | OKE |
| Object storage | S3 | Cloud Storage | Blob Storage | Object Storage |
| Relational DB | RDS / Aurora | Cloud SQL / AlloyDB | Azure SQL Database | Autonomous Database |
| NoSQL | DynamoDB | Firestore | Cosmos DB | NoSQL Database |
| Message queue | SQS | Cloud Tasks / Pub/Sub | Service Bus | OCI Queue |
| Event streaming | Kinesis / MSK | Pub/Sub | Event Hubs | OCI Streaming |
| Event bus | EventBridge | Eventarc | Event Grid | OCI Events |
| DNS | Route 53 | Cloud DNS | Azure DNS | OCI DNS |
| CDN | CloudFront | Cloud CDN | Azure Front Door / CDN | OCI CDN |
| WAF | AWS WAF | Cloud Armor | Azure WAF | OCI WAF |
| DDoS protection | Shield | Cloud Armor | Azure DDoS Protection | OCI DDoS |
| Secrets management | Secrets Manager | Secret Manager | Key Vault | OCI Vault |
| Monitoring | CloudWatch | Cloud Monitoring | Azure Monitor | OCI Monitoring |
| Audit logs | CloudTrail | Cloud Audit Logs | Activity Log | OCI Audit |
| IAM / org governance | IAM + Organizations | IAM + Resource Manager | Entra ID + RBAC | OCI IAM |
| Hybrid connectivity | Direct Connect / Site-to-Site VPN | Cloud Interconnect / Cloud VPN | ExpressRoute / VPN Gateway | FastConnect |
| Load balancer | ALB / NLB / GWLB | Cloud Load Balancing | Azure Load Balancer / App Gateway | OCI Load Balancer |
| In-memory cache | ElastiCache | Memorystore | Azure Cache for Redis | OCI Cache |
| Managed Kubernetes | EKS | GKE | AKS | OKE |
| Backup | AWS Backup | Backup and DR | Azure Backup | OCI Backup |
| IaC (first-party) | CloudFormation / CDK | Deployment Manager / Config Controller | ARM / Bicep | Resource Manager |

> Note: Cross-provider equivalents are functional analogs, **not** feature-parity guarantees. Validate specifics against each provider's current docs before migration decisions.
Source (AWS canonical names): [AWS Documentation](https://docs.aws.amazon.com/) — accessed 2026-07-31.

---

## Source Bibliography

### Primary — AWS Well-Architected Framework (Publication date: November 6, 2024; current stable edition)
1. **AWS Well-Architected Framework — Welcome / overview** — https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html — accessed 2026-07-31.
2. **Operational Excellence Pillar — Design principles** — https://docs.aws.amazon.com/wellarchitected/latest/framework/oe-design-principles.html — accessed 2026-07-31.
3. **Security Pillar — Design principles** — https://docs.aws.amazon.com/wellarchitected/latest/framework/sec-design.html — accessed 2026-07-31.
4. **Reliability Pillar — Design principles** — https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/design-principles.html — accessed 2026-07-31.
5. **Performance Efficiency Pillar — Design principles** — https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/design-principles.html — accessed 2026-07-31.
6. **Cost Optimization Pillar — Design principles** — https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/design-principles.html — accessed 2026-07-31.
7. **Sustainability Pillar — Design principles** — https://docs.aws.amazon.com/wellarchitected/latest/framework/sus-design-principles.html — accessed 2026-07-31.

### Security Pillar — Best-practice areas cited
8. **SEC 1 — Security foundations** — https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/security-foundations.html — accessed 2026-07-31.
9. **SEC 2 — Identity management** — https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/identity-management.html — accessed 2026-07-31.
10. **SEC 3 — Permissions management** — https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/permissions-management.html — accessed 2026-07-31.
11. **SEC 4 — Detection** — https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/detection.html — accessed 2026-07-31.
12. **SEC 5 — Protecting networks** — https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-networks.html — accessed 2026-07-31.
13. **SEC 8 — Protecting data at rest** — https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-data-at-rest.html — accessed 2026-07-31.
14. **AWS account management and separation** — https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/aws-account-management-and-separation.html — accessed 2026-07-31.

### Reliability Pillar — Best-practice areas cited
15. **REL 2 — Network topology** — https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_planning_network_topology_ha_conn_private_networks.html — accessed 2026-07-31.
16. **REL 4 — Distributed system interactions** — https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_prevent_interaction_failure_throttle_requests.html — accessed 2026-07-31.
17. **REL 9 — Back up data** — https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_backing_up_data_identified_backups_data.html — accessed 2026-07-31.
18. **REL 10 — Fault isolation (Multi-AZ/Region)** — https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_fault_isolation_multiaz_region_system.html — accessed 2026-07-31.
19. **REL 11 — Withstand component failures** — https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_withstand_component_failures_monitor_health.html — accessed 2026-07-31.

### Performance Efficiency Pillar — Best-practice areas cited
20. **PERF 2 — Compute architecture selection** — https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/compute-architecture.html — accessed 2026-07-31.
21. **PERF 3 — Data management** — https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/data-management.html — accessed 2026-07-31.
22. **Performance Efficiency — Caching** — https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/caching.html — accessed 2026-07-31.

### Cost Optimization Pillar — Best-practice areas cited
23. **COST 2 — Govern usage** — https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/cost_govern_usage_enforce_policies.html — accessed 2026-07-31.
24. **COST 3 — Monitor usage and cost (tagging)** — https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/cost_monitor_usage_tagging.html — accessed 2026-07-31.

### Supporting whitepapers / references
25. ⚠️ **Disaster Recovery of Workloads on AWS: Recovery in the Cloud** (whitepaper; > 12 months old but current published DR reference) — https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html — accessed 2026-07-31.
26. **AWS Documentation home** — https://docs.aws.amazon.com/ — accessed 2026-07-31.
27. **AWS Architecture Center** — https://aws.amazon.com/architecture/ — accessed 2026-07-31.

---

## Research Gaps / Unverified Notes

- **Assessment question numbering** (OPS/SEC/REL/PERF/COST/SUS): Pillar and best-practice-area sources were fetched and verified. Individual question **numbers** (e.g., "SEC 8", "REL 13") reflect the current pillar structure but the exact numeric label can shift between minor Framework revisions — treat numbers as indicative and confirm against the live pillar "Best practices" pages / AWS WA Tool at review time.
- **Cost figures** are deliberately expressed as **relative order-of-magnitude** only; no absolute pricing was quoted. Confirm on the AWS Pricing Calculator.
- **AWS Config rule names / Security Hub control IDs** cited for detection are standard managed rules/controls; verify the exact current rule identifier in your Region before automating remediation.

---

**End of knowledge base — AWS Well-Architected Framework (Nov 6, 2024 edition), verified 2026-07-31.**
**Recommended next step**: run `/skill-best-practices-validator` on this output, then pass to `skill-author` (`/skill-creator`) to generate the `applying-aws-well-architected` skill.
