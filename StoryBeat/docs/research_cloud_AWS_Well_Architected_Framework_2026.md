# AWS Well-Architected Framework — Cloud Architecture Research (2026)

> Anti-hallucination research base. Every fact is sourced to official AWS documentation
> (docs.aws.amazon.com, AWS Whitepapers, AWS Prescriptive Guidance) with an access or publish date.
> Sources older than 12 months are flagged ⚠️ >12mo but retained when they are the current stable
> edition. Items that could not be confirmed against an official source are tagged `[unverified]`.
> Do not treat this file as legal or compliance advice.

## Metadata

```yaml
Full_Name: "AWS Well-Architected Framework"
Cloud_Provider: "AWS"
Architecture_Domain: "Well-Architected Framework"
Target_Edition: "November 6, 2024 (current stable; no 2026 edition exists)"
Architecture_Context: "Multi-account production workloads on AWS"
Official_Source_URL: "https://docs.aws.amazon.com/wellarchitected/latest/framework/"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-08-27"
Currency_Threshold: "2027-08-27"
Research_Depth: "exhaustive"
```

> ⚠️ **Edition note:** No official "AWS WAF 2026" edition exists. The current stable edition is
> **November 6, 2024**, which refreshed 78 best practices across all six pillars. Treated as
> authoritative-current per Version Absolutism. Sources dated Nov 2024 are flagged ⚠️ >12mo but
> retained as current stable.

---

## Executive Summary

The AWS Well-Architected Framework (WAF) is the official multi-pillar design system for evaluating
and improving cloud architectures on AWS. The current stable edition (November 6, 2024) defines six
pillars: **Operational Excellence**, **Security**, **Reliability**, **Performance Efficiency**,
**Cost Optimization**, and **Sustainability**. The Nov 2024 update refreshed 78 best practices
across all pillars — the largest single refresh since Oct 2022 — published in 11 languages and
fully integrated into the AWS Well-Architected Tool in the AWS Console.
Source: https://aws.amazon.com/blogs/architecture/announcing-updates-to-the-aws-well-architected-framework-guidance-3/ (2024-11-06) ⚠️ >12mo, current stable

The three most impactful Nov 2024 changes are: (1) the Operational Excellence pillar expanded from
5 to 8 design principles, including a new principle for managed services and AI-assisted ops via
Amazon Q Business (OPS02-BP02); (2) a new Sustainability best practice SUS06-BP01 requiring teams
to cascade sustainability goals; and (3) Resource Control Policies (RCPs) launched Nov 13, 2024,
extending multi-account guardrails from identity-centric (SCPs) to resource-centric controls. In
the Cost Optimization space, Aurora Serverless v2 scale-to-zero reached GA in Nov 2024, and Cost
Optimization Hub gained Savings Plans/reservation preference analysis in May 2025.

The three most critical cross-pillar guardrails for any production workload are: (1) **multi-account
structure under AWS Organizations** (Security pillar SEC01, anchors all other pillars); (2)
**continuous detection via CloudTrail org trail + GuardDuty org-wide + Security Hub + AWS Config**
(SEC04, OE-AD-B); and (3) **multi-AZ deployment with tested DR strategy** (REL10, REL13). Any
architecture missing these three elements fails the Well-Architected review before reaching any
pillar-specific best practice.

---

## Cloud Architecture Glossary

```
Term: Well-Architected Framework (WAF)
Definition: AWS's multi-pillar framework of architectural best practices, design principles, and
  review questions for evaluating cloud workloads. Current edition: Nov 6, 2024, six pillars.
Provider Docs Section: https://docs.aws.amazon.com/wellarchitected/latest/framework/
Architect Usage: Use as structured review checklist via the AWS Well-Architected Tool; generates
  improvement plan and risk report per workload.
Common Confusion: Confused with AWS WAF (Web Application Firewall). They share the acronym but
  are unrelated services.
```

```
Term: Service Control Policy (SCP)
Definition: Organization policy that caps the maximum permissions available to IAM principals
  (users and roles) in member accounts. SCPs do not grant permissions; they act as guardrails.
  Not applied to the management account.
Provider Docs Section: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html
Architect Usage: Enforce security baselines across all member accounts (e.g., deny disabling
  CloudTrail, deny leaving the org). Apply at OU level for inheritance.
Common Confusion: Confused with IAM policies. SCPs set the ceiling; IAM policies determine the
  actual permissions within that ceiling.
```

```
Term: Resource Control Policy (RCP)
Definition: Organization policy that caps the maximum permissions for AWS resources, including
  access by external principals. Resource-centric complement to SCPs. Launched Nov 13, 2024.
  As of 2026-08-27 supports ~40 services. Not applied to the management account.
Provider Docs Section: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_rcps.html
Architect Usage: Enforce that S3 buckets, KMS keys, SQS queues, etc. cannot be accessed outside
  the organization even if bucket policies or resource policies attempt to allow it.
Common Confusion: Confused with SCPs. SCPs control what principals in your org can do; RCPs
  control what can be done to resources in your org (including by external identities).
```

```
Term: Control Tower Landing Zone
Definition: AWS-managed baseline multi-account environment. Creates Security OU (Log Archive +
  Audit accounts) and optional Sandbox OU using CloudFormation StackSets. Controls (formerly
  "guardrails") are Preventive (SCPs/RCPs), Detective (Config rules), or Proactive (CFN hooks).
Provider Docs Section: https://docs.aws.amazon.com/controltower/latest/userguide/how-control-tower-works.html
Architect Usage: Starting point for new AWS org setups. From Landing Zone v4.0, mandatory controls
  are NOT applied by default — verify version before assuming controls are active.
Common Confusion: Assumed to be fully secured out of the box. v4.0 changed mandatory control
  behavior; always verify active controls for your version.
```

```
Term: Operational Excellence — 8 Design Principles
Definition: The current Nov 2024 edition defines 8 OE design principles. Prior editions had 5.
  The 8 are: (1) Organize teams around business outcomes, (2) Implement observability for
  actionable insights, (3) Safely automate where possible, (4) Make frequent small reversible
  changes, (5) Refine operations procedures frequently, (6) Anticipate failure, (7) Learn from
  all operational events and metrics, (8) Use managed services.
Provider Docs Section: https://docs.aws.amazon.com/wellarchitected/latest/framework/oe-design-principles.html
Architect Usage: Use as evaluation checklist for operational maturity. Any team citing only 5
  principles is using a stale reference.
Common Confusion: Sources citing 5 OE principles are stale (pre-Nov 2024 editions). The
  expanded 8-principle model is the only valid reference.
```

```
Term: DR Strategy Tiers
Definition: Four active/passive and active/active disaster recovery strategies, ordered by cost
  and recovery speed: Backup & Restore (slowest/cheapest) → Pilot Light → Warm Standby →
  Multi-Site Active/Active (fastest/most expensive).
Provider Docs Section: https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html
Architect Usage: Select strategy based on RTO/RPO SLA. Aurora global DB achieves <1 s cross-Region
  replication lag and <1 min secondary promotion for near-Active/Active behavior at lower cost.
Common Confusion: "Pilot Light" is not the same as "Warm Standby." Pilot Light has core infra
  pre-deployed but not serving traffic; Warm Standby serves reduced-capacity traffic immediately.
```

```
Term: Transit Gateway (TGW)
Definition: Managed Regional hub that connects thousands of VPCs and on-premises networks via
  a single gateway. Supports transitive routing, segmentation via route tables, sharing via
  AWS RAM across org accounts. TGW Connect: BGP + GRE, up to 20 Gbps per attachment.
Provider Docs Section: https://docs.aws.amazon.com/whitepapers/latest/building-scalable-secure-multi-vpc-network-infrastructure/transit-gateway.html
Architect Usage: Use for hub-and-spoke at scale (multiple VPCs). Use VPC peering instead for
  small numbers of high-throughput VPC pairs (lower latency, no additional hop).
Common Confusion: TGW is HA by design within a Region; no additional TGW needed per Region for
  HA. VPC peering is not transitive — TGW is required for transitive routing.
```

```
Term: VPC Endpoint — Gateway vs Interface
Definition: Gateway endpoint: free, route-table target, supports only S3 and DynamoDB, not
  reachable from on-prem or peered VPCs. Interface endpoint (PrivateLink): ENI with private IP
  per subnet per AZ, billed hourly + data processing, supports most AWS services, reachable
  from on-prem via private DNS.
Provider Docs Section: https://docs.aws.amazon.com/vpc/latest/privatelink/concepts.html
Architect Usage: Always use gateway endpoint for S3 and DynamoDB from private subnets (free).
  Add interface endpoint only when on-premises access to S3/DynamoDB via Direct Connect/VPN
  is required.
Common Confusion: Architects install interface endpoints for S3/DynamoDB when a free gateway
  endpoint would suffice, adding unnecessary cost.
```

```
Term: NAT Gateway — Per-AZ Pattern
Definition: Each NAT gateway is AZ-specific and redundant within that AZ. Scales 5→100 Gbps,
  1M→10M pps. Public type requires EIP + IGW; Private type routes to other VPCs/on-prem.
Provider Docs Section: https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-basics.html
Architect Usage: Deploy one NAT gateway per AZ. Route each AZ's private subnet 0.0.0.0/0 to
  the NAT in the SAME AZ to avoid cross-AZ data transfer costs and AZ failure blast radius.
Common Confusion: Using a single shared NAT gateway across AZs (cost optimization) creates an
  AZ single point of failure for all private subnets.
```

```
Term: Savings Plans vs Reserved Instances
Definition: Compute Savings Plans: up to 66% discount, 1/3-yr hourly $ commitment, most
  flexible (any EC2 instance family/Region/OS). Instance Savings Plans: up to 72%, locked to
  instance family + Region. Reserved Instances: up to 72%, used for non-EC2 services (RDS,
  ElastiCache, Redshift, etc.).
Provider Docs Section: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/select-the-best-pricing-model.html
Architect Usage: Buy Savings Plans in the management account (no workloads) to maximize
  discount. Track potential-savings threshold (act when >20%) rather than targeting a fixed
  coverage percentage.
Common Confusion: Buying Savings Plans in workload accounts limits discount sharing across the
  org. Chasing a fixed coverage % leads to over-commitment during scaling.
```

---

## Architecture Guardrails

### ✅ Mandatory Patterns

**Multi-Account Workload Separation**
- Pillar Alignment: Security (SEC01-BP01); also anchors Reliability, Operational Excellence
- Why: Blast radius containment — a compromised or misconfigured account cannot affect other
  workloads. SCPs/RCPs applied at OU level enforce consistent guardrails without per-account
  configuration.
- AWS Services: AWS Organizations, Control Tower, Service Control Policies, Resource Control
  Policies, IAM Identity Center
- Architecture Decision: One AWS account per workload x environment (e.g., prod, staging, dev)
  under named OUs in the org. Security OU holds Log Archive + Audit accounts. Management account
  holds no workloads.
- Verification: AWS Organizations console — confirm OU structure matches recommended layout.
  Config rule `account-part-of-organizations` on all member accounts.
- Source: SEC01-BP01 https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_securely_operate_multi_accounts.html [triangulated]

**Federated Human Access via IAM Identity Center**
- Pillar Alignment: Security (design principle 1 — strong identity foundation)
- Why: Temporary STS credentials expire automatically, eliminating long-term credential exposure.
  Federated access via existing IdP means no per-user IAM users with access keys.
- AWS Services: IAM Identity Center, AWS STS, corporate IdP (SAML 2.0 / OIDC)
- Architecture Decision: All human access to AWS accounts via IAM Identity Center SSO with
  permission sets. Zero IAM users with long-term access keys for humans.
- Verification: IAM credential report — flag any IAM user with access keys and age > 0 days.
  Config rule `iam-user-no-policies-check`.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html + security pillar identity page [triangulated]

**IAM Roles for All Workload Identities**
- Pillar Alignment: Security (design principle 1)
- Why: Embedded access keys in code/config are a leading cause of credential leaks. IAM roles
  issue temporary credentials automatically via the instance metadata service or STS.
- AWS Services: IAM roles, EC2 instance profiles, Lambda execution roles, ECS task roles,
  EKS Pod Identity, IAM Roles Anywhere
- Architecture Decision: Never embed access keys in application code, environment variables, or
  AMIs. Assign IAM roles at the compute resource level.
- Verification: `aws iam list-access-keys` for all users; secret scanning in CI/CD pipelines
  (e.g., Amazon CodeGuru Security).
- Source: IAM best practices + security pillar [triangulated]

**Phishing-Resistant MFA for All IAM and Root Users**
- Pillar Alignment: Security (design principle 1)
- Why: SMS and TOTP MFA are vulnerable to SIM swap and phishing. FIDO2 passkeys/security keys
  require physical possession and are phishing-resistant.
- AWS Services: IAM (FIDO2 MFA registration), AWS Organizations (SCP to require MFA), root
  account lockdown procedure
- Architecture Decision: Register FIDO2 hardware security key on root account. Delete root
  access keys. Enable SCP denying API calls without MFA for sensitive actions.
- Verification: IAM console MFA status; Config rule `mfa-enabled-for-iam-console-access`.
- Source: IAM best practices + SEC design principle 1 [triangulated]

**Encryption at Rest with AWS KMS**
- Pillar Alignment: Security (SEC08-BP01/02 — protecting data at rest)
- Why: Unencrypted data at rest is accessible to anyone with storage-level access (e.g., snapshot
  copies, cross-account access, insider threat). KMS provides audit trail via CloudTrail.
- AWS Services: AWS KMS (CMK or AWS-managed keys), CloudTrail, CloudWatch Logs Insights,
  AWS Config rules
- Architecture Decision: Enable KMS encryption for all EBS volumes, S3 buckets, RDS instances,
  DynamoDB tables, and SQS queues. Audit key use via CloudTrail + CloudWatch Logs Insights.
- Verification: Config rules `encrypted-volumes`, `s3-bucket-server-side-encryption-enabled`,
  `rds-storage-encrypted`.
- Source: SEC08-BP01/02 https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-data-at-rest.html [triangulated]

**Continuous Detection Stack**
- Pillar Alignment: Security (SEC04-BP01–BP04 — detection)
- Why: Threats are often detected weeks after initial compromise. Continuous automated detection
  reduces mean time to detect (MTTD) to minutes.
- AWS Services: CloudTrail (org trail), Amazon GuardDuty (org-wide), AWS Security Hub,
  AWS Config
- Architecture Decision: Enable one CloudTrail org trail writing to S3 in Log Archive account.
  Enable GuardDuty organization-wide with delegated administrator in Security Tooling account.
  Aggregate findings in Security Hub. Config rules running in all accounts.
- Verification: Security Hub findings dashboard; GuardDuty coverage report; Config compliance
  aggregator in Security Tooling account.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/detection.html [triangulated]

**Multi-AZ Deployment for All Production Compute**
- Pillar Alignment: Reliability (REL10-BP01 — fault isolation)
- Why: A single AZ can fail independently. Multi-AZ deployment ensures that one AZ failure does
  not make the workload unavailable.
- AWS Services: EC2 Auto Scaling (multi-AZ), Application Load Balancer, RDS Multi-AZ, Aurora
  (automatic multi-AZ), ElastiCache Multi-AZ, ECS/EKS across AZs
- Architecture Decision: Span all stateless compute across ≥2 AZs behind an ELB. Enable Multi-AZ
  explicitly on RDS and ElastiCache (S3 and DynamoDB are Multi-AZ by default).
- Verification: EC2 Auto Scaling group AZ configuration; RDS Multi-AZ status in console.
- Source: REL10-BP01 https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/use-fault-isolation-to-protect-your-workload.html [triangulated]

**Centralized Backup for All Critical Data**
- Pillar Alignment: Reliability (REL09-BP01 — failure management)
- Why: Replication alone does not protect against logical corruption, ransomware, or accidental
  deletion. Point-in-time recovery and versioning provide independent recovery points.
- AWS Services: AWS Backup (centralized), S3 versioning + Cross-Region Replication, RDS PITR,
  DynamoDB PITR, EBS snapshots
- Architecture Decision: Configure AWS Backup plans covering all critical resources in all
  accounts. Enable S3 versioning and PITR on DynamoDB tables. Test restores on a regular
  schedule (at minimum quarterly).
- Verification: AWS Backup compliance report; test restore runbook execution record.
- Source: REL09-BP01 https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/failure-management.html [triangulated]

**Infrastructure as Code for All Resources**
- Pillar Alignment: Operational Excellence (OE-AD-A — design principle 3)
- Why: Manual console changes ("click-ops") are not reproducible, not auditable, and cannot be
  rolled back deterministically.
- AWS Services: AWS CloudFormation, AWS CDK, AWS Systems Manager, AWS Config, CodePipeline,
  CodeBuild, CodeDeploy
- Architecture Decision: All production infrastructure defined in CloudFormation/CDK, stored in
  version control, deployed via CI/CD pipeline. Systems Manager Automation for operational
  runbooks.
- Verification: CloudTrail events — flag `CreateBucket`, `RunInstances`, etc. not triggered by
  CloudFormation stack events. Config rule `cloudformation-stack-drift-detection-check`.
- Source: OE design principles https://docs.aws.amazon.com/wellarchitected/latest/framework/oe-design-principles.html (accessed 2026-08-27) [triangulated]

**Elastic Scaling to Match Demand**
- Pillar Alignment: Reliability (REL-AD-4), Performance Efficiency (PE-AD-3),
  Cost Optimization (CO-AD-1), Sustainability (SUS-AD-B)
- Why: Fixed capacity either over-provisions (cost/sustainability waste) or under-provisions
  (reliability failure). Elastic scaling is the unifying pattern across four pillars.
- AWS Services: EC2 Auto Scaling, Application Auto Scaling, ELB, CloudWatch alarms, Lambda,
  Fargate, Karpenter (EKS), Aurora Auto Scaling
- Architecture Decision: Define scaling policies based on business KPI metrics (not just CPU).
  Set minimum capacity for baseline availability. Set maximum capacity to cap cost.
- Verification: CloudWatch Auto Scaling activity log; test scale-out and scale-in events in
  lower environments.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/change-management.html + SUS02-BP01 [triangulated]

---

### ⚠️ Architectural Decisions

**DR Strategy Selection**

- Options:

  | Option | AWS Services | RTO | RPO | Cost | Best When |
  |--------|-------------|-----|-----|------|-----------|
  | Backup & Restore | AWS Backup, S3, CloudFormation | Hours–days | Hours | Lowest | Non-critical; budget constrained |
  | Pilot Light | AWS Backup + pre-deployed core infra + Elastic Disaster Recovery | 30 min–hours | Minutes | Low | Moderate criticality; cost-sensitive |
  | Warm Standby | AWS Backup + pre-deployed reduced-capacity stack + Route 53 | Minutes | Seconds–minutes | Higher | High criticality with cost ceiling |
  | Multi-Site Active/Active | Aurora global tables, DynamoDB global tables, Route 53 latency routing, ARC | Near-zero | Near-zero | Highest | Mission-critical; RTO/RPO <1 min |

- Cost Profile: Backup & Restore ~1x; Pilot Light ~1.5x; Warm Standby ~2x; Active/Active ~3–5x.
- Lock-in Assessment: Aurora Global DB and DynamoDB global tables are AWS-proprietary; plan
  migration cost before committing for Active/Active.
- Architect Instruction: "Ask what is the business cost of 1 hour of downtime and 1 hour of
  data loss when the RTO/RPO SLA is undefined."
- Source: https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html (2022-04-01 ⚠️ >12mo, current stable)

**Compute Type Selection per Component**

- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|------------|-----------|------------|-----------|
  | Serverless functions | Lambda | Cost (pay per invocation), operational overhead | Cold starts, max 15 min timeout | Event-driven, intermittent, stateless |
  | Containerized serverless | ECS Fargate / EKS Fargate | Balance: no server mgmt, flexible sizing | Higher base cost vs Lambda | Predictable container workloads |
  | Managed containers | ECS EC2 / EKS EC2 | Control, GPU, Spot discounts | Operational overhead | GPU ML, Spot-tolerant workloads |
  | Virtual machines | EC2 | Max flexibility, Spot 90% discount | Highest management overhead | Legacy lift-and-shift, HPC, Spot fleets |
  | Graviton (ARM) | M8g / C8g / R8g | 30% perf + 40% price-perf + 60% energy vs x86 | ARM compatibility testing | General-purpose; new greenfield workloads |

- Cost Profile: Lambda < Fargate < ECS/EKS EC2 (Spot) < EC2 On-Demand.
- Lock-in Assessment: Lambda and Fargate APIs are proprietary; Kubernetes workloads on EKS are
  more portable. Factor in migration cost.
- Architect Instruction: "Ask whether the workload is event-driven or long-running when selecting
  between Lambda and container-based compute."
- Source: PERF02-BP01 https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/ (accessed 2026-08-27)

**Pricing Model Mix for Stable + Variable Workloads**

- Options:

  | Option | Discount | Trade-off | Best When |
  |--------|----------|-----------|-----------|
  | On-Demand | 0% | Full flexibility | Unpredictable spikes; new workloads |
  | Spot | Up to 90% | 2-min interruption notice | Fault-tolerant, stateless, batch |
  | Compute Savings Plans | Up to 66% | 1/3-yr hourly $ commitment | Stable baseline compute |
  | Instance Savings Plans | Up to 72% | Locked to instance family + Region | Stable single-family workloads |
  | Reserved Instances | Up to 72% | Per-service commitment | RDS, ElastiCache, Redshift |

- Cost Profile: Recommended mix: Savings Plans for baseline + Spot for burst + On-Demand for
  unpredictable peaks.
- Lock-in Assessment: Savings Plans reduce flexibility to change instance families/Regions during
  commitment term. Evaluate workload maturity before committing.
- Architect Instruction: "Ask whether the workload has run for ≥3 months with stable CPU patterns
  before recommending a Savings Plan commitment."
- Source: COST07 https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/select-the-best-pricing-model.html (accessed 2026-08-27)

**Data Store Selection per Access Pattern**

- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|------------|-----------|------------|-----------|
  | Relational | Aurora / RDS | ACID, complex queries, joins | Horizontal write scaling | Transactional apps, reporting |
  | Key-value / NoSQL | DynamoDB | Single-digit ms at any scale | Query flexibility | High-throughput KV lookups |
  | In-memory cache | ElastiCache (Redis/Memcached) | Sub-ms reads | Durability (by default) | Session, leaderboard, hot data |
  | Object storage | S3 | Unlimited scale, low cost | Not a database | Unstructured data, media, backups |
  | Search | OpenSearch | Full-text, aggregations | Cost at scale | Log analytics, catalog search |

- Cost Profile: DynamoDB provisioned < DynamoDB on-demand < Aurora Serverless v2 < RDS
  Multi-AZ < ElastiCache Cluster.
- Architect Instruction: "Ask what the primary access pattern is (KV lookup, full-text search,
  relational join, or time-series) before selecting a data store."
- Source: PERF-AD-6 https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/ (accessed 2026-08-27) [triangulated]

---

### 🚫 Anti-Patterns

**Long-Term Static Access Keys for Humans**
- Risk Level: CRITICAL
- Why: Static credentials do not expire; a leaked key provides indefinite access. Violates Security
  pillar design principle 1 (strong identity foundation — eliminate long-term static credentials).
- Instead: IAM Identity Center + STS temporary credentials with automatic expiry. No human should
  have an IAM user with access keys.
- Detection: `aws iam generate-credential-report` — any `access_key_1_active` = true for a human
  user. Config rule `iam-user-no-policies-check`.
- Impact: Data breach, compliance violation, full account takeover.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html [triangulated]

**Root User Used for Daily Operations**
- Risk Level: CRITICAL
- Why: Root has unrestricted access to all services and cannot be scoped by IAM policies. Any
  action taken as root bypasses SCPs. Violates Security pillar design principle 1.
- Instead: Lock root with hardware MFA passkey, delete root access keys, use root only for the
  4 specific tasks that require it (e.g., closing the account, changing support plan).
- Detection: CloudTrail event filter `userIdentity.type = Root`. Config rule
  `root-account-mfa-enabled`.
- Impact: Full account takeover; no guardrail can limit root actions.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html [triangulated]

**Multiple Unrelated Workloads in One AWS Account**
- Risk Level: CRITICAL
- Why: A security incident, quota exhaustion, or IAM misconfiguration in one workload affects all
  others. No SCP boundary possible within a single account. Violates SEC01-BP01.
- Instead: One account per workload x environment under named OUs. Use Control Tower for
  automated account vending.
- Detection: AWS Organizations — count accounts vs workload/environment combinations.
- Impact: Blast radius amplification; compliance scope expansion; shared quota exhaustion.
- Source: SEC01-BP01 https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_securely_operate_multi_accounts.html [triangulated]

**Single-AZ Production Deployment**
- Risk Level: CRITICAL
- Why: AZ failures occur. A single-AZ workload has 0% availability during an AZ failure event.
  Violates Reliability pillar design principle 3 (scale horizontally to reduce single points of
  failure).
- Instead: EC2 Auto Scaling spanning ≥2 AZs + ELB. RDS Multi-AZ with synchronous replication.
  ElastiCache Multi-AZ. ECS/EKS tasks distributed across AZs.
- Detection: EC2 Auto Scaling group — check `AvailabilityZones` list length. RDS instance —
  check `MultiAZ` attribute.
- Impact: Full workload outage during AZ failure (typically 15 min–4 hours historically).
- Source: REL10-BP01 https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/use-fault-isolation-to-protect-your-workload.html [triangulated]

**No Disaster Recovery Plan**
- Risk Level: CRITICAL
- Why: Without a defined and tested DR strategy, recovery is ad-hoc. Mean time to recover (MTTR)
  under pressure with no runbook is measured in days. Violates REL13-BP01–05.
- Instead: Define RTO/RPO SLAs, select appropriate DR tier, implement with AWS Backup + Elastic
  Disaster Recovery + Route 53 ARC, and test quarterly.
- Detection: AWS Well-Architected Tool review — REL13 question set flagging no DR strategy.
- Impact: Extended outage; potential total data loss; regulatory violation if data retention
  rules apply.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_planning_for_recovery_disaster_recovery.html [triangulated]

**Manual Click-Ops Production Changes**
- Risk Level: CRITICAL
- Why: Console changes are not reproducible, not version-controlled, and not auditable beyond
  CloudTrail. Drift between environments compounds over time. Violates OE design principle 3.
- Instead: All infrastructure changes via CloudFormation/CDK committed to Git and deployed
  through a CI/CD pipeline. Systems Manager Automation for operational runbooks.
- Detection: CloudTrail — flag resource creation/modification events not attributed to
  CloudFormation stack updates.
- Impact: Configuration drift, failed audits, unrecoverable state, incident amplification.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/framework/oe-design-principles.html (accessed 2026-08-27) [triangulated]

**100% On-Demand Pricing for Stable Compute**
- Risk Level: HIGH
- Why: On-Demand is the highest unit price. Stable baseline workloads with predictable usage
  generate 0% discount vs available 66–72% savings. Violates COST07 consumption model principle.
- Instead: Compute Savings Plans for baseline (up to 66%). Spot instances for fault-tolerant
  burst (up to 90%). On-Demand only for unpredictable spikes.
- Detection: Cost Optimization Hub — "Savings Plans coverage" and "potential savings" reports.
  AWS Compute Optimizer — right-sizing recommendations.
- Impact: Cost overrun; missed 40–66% savings opportunity on steady-state fleet.
- Source: COST07 https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/select-the-best-pricing-model.html (accessed 2026-08-27)

**Static Over-Provisioning Instead of Elastic Scaling**
- Risk Level: HIGH
- Why: Violates Cost Optimization (consumption model), Performance Efficiency (PE-AD-2 right-size),
  and Sustainability (SUS-AD-B elastic scaling). "Two hosts at 30% is less efficient than one
  at 60%."
- Instead: EC2 Auto Scaling + CloudWatch KPI alarms. Lambda or Fargate for serverless.
  Compute Optimizer recommendations applied on a 14-day+ cycle.
- Detection: Compute Optimizer — % of instances in "Over-provisioned" category.
  CloudWatch — average CPU < 20% over 2 weeks on fixed-capacity fleet.
- Impact: Cost overrun; energy waste (sustainability violation); performance headroom
  wasted rather than eliminating under-utilized resources.
- Source: SUS design principle 3 https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/design-principles-for-sustainability-in-the-cloud.html (accessed 2026-08-27) [triangulated]

**Shared NAT Gateway Across Availability Zones**
- Risk Level: HIGH
- Why: All AZs routing through a single NAT gateway creates a cross-AZ single point of failure
  and adds cross-AZ data transfer costs. Violates Reliability pillar AZ isolation principle.
- Instead: One NAT gateway per AZ. Route each AZ's private subnet 0.0.0.0/0 to the NAT in the
  same AZ.
- Detection: VPC route tables — check whether multiple AZs' private subnets share a single
  NAT gateway target.
- Impact: Full outage for all private subnets if the NAT AZ fails. Cross-AZ data transfer cost.
- Source: https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-basics.html [triangulated]

**NAT/IGW for S3 or DynamoDB from Private Subnets**
- Risk Level: MEDIUM
- Why: S3 and DynamoDB support free gateway VPC endpoints. Routing through NAT adds per-GB data
  processing cost (NAT gateway: $0.045/GB) and adds internet-path risk unnecessarily.
- Instead: Free S3 and DynamoDB gateway endpoints on all private route tables.
- Detection: VPC route tables — check whether S3/DynamoDB traffic routes to `igw-` or `nat-`
  instead of `vpce-` (gateway type).
- Impact: Unnecessary data transfer cost; expanded network attack surface.
- Source: https://docs.aws.amazon.com/vpc/latest/privatelink/gateway-endpoints.html [triangulated]

**Spot Instances for Stateful or Uninterruptible Workloads**
- Risk Level: HIGH
- Why: Spot instances receive a 2-minute interruption notice before termination. Stateful workloads
  (e.g., databases, long-running transactions) lose state on interruption. Violates COST07 and
  Reliability pillar.
- Instead: On-Demand or Reserved Instances for stateful/uninterruptible workloads. Spot only for
  fault-tolerant, stateless, or checkpointed batch processing.
- Detection: EC2 instances with Spot lifecycle + RDS, stateful services attached.
- Impact: Data loss, transaction corruption, extended recovery.
- Source: COST07 https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/select-the-best-pricing-model.html (accessed 2026-08-27)

---

## Cloud-Native Design Patterns

**Event-Driven Architecture with Amazon EventBridge**
- Category: Communication / Scalability
- Problem: Tightly coupled synchronous service calls create cascading failures and limit
  independent scaling.
- Solution on AWS: EventBridge serverless event bus. Event rules route to up to 5 targets.
  EventBridge Pipes for point-to-point (source → target). Sources include AWS services,
  SaaS partners, and custom applications.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Coupling | Fully decoupled producers/consumers | Eventual consistency; harder to trace end-to-end |
  | Scalability | Auto-scales transparently | Fan-out complexity if >5 targets per rule needed |
  | Operability | Managed service; no infrastructure | Event schema discipline required |

- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-what-is.html
  + AWS Prescriptive Guidance publish-subscribe pattern [triangulated]

**Circuit Breaker Pattern**
- Category: Resilience
- Problem: A failing downstream service causes the caller to block and exhaust threads/connections,
  amplifying the failure.
- Solution on AWS: Step Functions (Express workflows) + DynamoDB CircuitStatus table with TTL
  (auto-reset) + Lambda (callee). States: CLOSED / OPEN / HALF-OPEN. OPEN = unexpired DynamoDB
  record → immediate FAIL. On failure → retry with exponential backoff + jitter → write
  ExpiryTimeStamp record to DynamoDB.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Resilience | Prevents cascade failures | Added latency for state check on each call |
  | Recovery | Auto-reset via DynamoDB TTL | Requires tuning of ExpiryTimeStamp per SLA |
  | Complexity | Managed Step Functions + DynamoDB | More complex than a library-level circuit breaker |

- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/circuit-breaker.html
  + Builders' Library (backoff + jitter) [triangulated]

**Queue-Based Load Leveling with Amazon SQS**
- Category: Scalability / Resilience
- Problem: Traffic spikes overwhelm downstream consumers, causing timeouts or data loss.
- Solution on AWS: Producers → SQS queue → consumers (EC2/Lambda). CloudWatch queue-depth alarm
  → EC2 Auto Scaling adds consumers. SQS buffers indefinitely (up to 14 days). Message retention:
  default 4 days, configurable 60 s–14 days.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Load | Absorbs any spike transparently | Adds latency (asynchronous processing) |
  | Durability | Messages retained up to 14 days | At-least-once delivery; consumers must be idempotent |
  | Cost | Pay per request; no provisioning | Cost grows linearly with message volume |

- Source: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html
  + Well-Architected HPC Lens Queue-Based Architecture + EC2 Auto Scaling SQS scaling guide [triangulated]

**CQRS (Command Query Responsibility Segregation)**
- Category: Data / Scalability
- Problem: A single data store optimized for writes is suboptimal for read-heavy query patterns
  (and vice versa), creating performance bottlenecks.
- Solution on AWS: Separate command (write) and query (read) data stores. Common implementations:
  (a) RDS + RDS read replicas; (b) DynamoDB (write) → DynamoDB Streams → Lambda → Aurora (read);
  (c) NoSQL both sides with stream-based sync.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Performance | Each store optimized for its pattern | Eventual consistency between write/read stores |
  | Scalability | Read replicas scale independently | Operational complexity of two data stores |
  | Flexibility | Polyglot persistence possible | Replication lag must be acceptable to the business |

- ⚠️ CQRS typically results in **eventual consistency** between command and query stores. Confirm
  this is acceptable before adopting the pattern.
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-data-persistence/cqrs-pattern.html
  [triangulated with AWS Database Blog]

---

## Security Architecture

**Identity and Access Management**
- AWS Services: IAM Identity Center, IAM roles, AWS STS, AWS Organizations (SCPs, RCPs)
- Architecture: Human access via Identity Center SSO + corporate IdP (SAML/OIDC) → permission
  sets → temporary STS credentials. Workloads use IAM roles (instance profiles, task roles, Pod
  Identity). SCPs cap principal permissions at OU level. RCPs cap resource access org-wide.
- Compliance Alignment: SEC01 (multi-account), SEC02 (identities), SEC03 (permissions) of the
  Security pillar; CIS AWS Foundations Benchmark v2.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/identity-management.html (accessed 2026-08-27)

**Data Protection**
- AWS Services: AWS KMS (CMK / AWS-managed keys), S3 SSE, EBS encryption, RDS encryption,
  ACM (TLS), AWS PrivateLink, CloudTrail
- Architecture: All data at rest encrypted with KMS. All data in transit via TLS 1.2+.
  KMS key usage audited via CloudTrail → CloudWatch Logs Insights. PrivateLink for
  service-to-service traffic avoiding public internet.
- Compliance Alignment: SEC08 (protecting data at rest), SEC09 (protecting data in transit).
  PCI-DSS Requirement 3/4; HIPAA encryption safe harbor.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-data-at-rest.html [triangulated]

**Threat Detection and Incident Response**
- AWS Services: CloudTrail (org trail), Amazon GuardDuty, AWS Security Hub, AWS Config,
  Amazon Detective, AWS Systems Manager Incident Manager, EventBridge
- Architecture: CloudTrail org trail → S3 (Log Archive account, immutable) → Security Hub
  aggregation → GuardDuty findings → EventBridge rules → Lambda automated remediation or
  SNS → Incident Manager. Detective for investigation graph. Config for compliance posture.
- Compliance Alignment: SEC04 (detection), SEC10 (incident response). SOC 2 CC7, ISO 27001
  A.16.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/detection.html [triangulated]

**Network Security**
- AWS Services: AWS WAF, AWS Shield (Standard/Advanced), AWS Network Firewall, Security Groups,
  Network ACLs, AWS PrivateLink, VPC Endpoints
- Architecture: Edge: CloudFront + WAF + Shield → ALB. Within VPC: Security Groups (stateful,
  instance-level) + NACLs (stateless, subnet-level). Data tier in isolated/private subnets only.
  Ingress via ALB/NLB, not direct EC2 exposure. PrivateLink for AWS service access without
  internet path.
- Compliance Alignment: SEC05 (network protection). NIST CSF PR.AC-5.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/network-protection.html (accessed 2026-08-27)

---

## Operational Patterns

**Disaster Recovery — Tested Strategy**
- RTO/RPO: Depends on selected tier (see Architectural Decisions — DR Strategy Selection table)
- AWS Services: AWS Backup, Elastic Disaster Recovery, Route 53 (ARC routing-control health
  checks), CloudFormation, Aurora Global DB, DynamoDB global tables
- Cost Profile: Low (Backup & Restore) → High (Multi-Site Active/Active)
- Automation: Automated failover via Route 53 health checks + ARC. Elastic Disaster Recovery
  replication daemon runs continuously on source servers. CloudFormation re-deploys compute tier
  from template. Test with FIS and quarterly game days.
- ⚠️ During recovery use data plane operations, not control plane — REL11-BP04. Control plane
  APIs may be degraded during Regional events.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_planning_for_recovery_disaster_recovery.html [triangulated]

**Service Quota Management**
- RTO/RPO: N/A (preventive)
- AWS Services: AWS Service Quotas, Trusted Advisor, CloudWatch alarms on quota utilization
- Cost Profile: Low (monitoring only; quota increases are free)
- Automation: CloudWatch alarm on quota utilization > 80% → SNS → team notification → automated
  quota increase request via Service Quotas API if business-critical.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/foundations.html

**Reliability Testing via Fault Injection**
- RTO/RPO: N/A (validation)
- AWS Services: AWS Fault Injection Service (FIS), CloudWatch, Systems Manager Automation
- Cost Profile: Low (experiment duration-based; typically minutes to hours)
- Automation: FIS experiment templates in version control. Run on schedule in staging;
  run quarterly in production during low-traffic windows.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/failure-management.html [triangulated]

**Observability Stack**
- RTO/RPO: N/A (enablement)
- AWS Services: Amazon CloudWatch (metrics, logs, alarms, dashboards), AWS X-Ray (tracing),
  CloudWatch Application Signals (APM), CloudTrail, Amazon Managed Grafana, Amazon Managed
  Prometheus
- Cost Profile: Medium (CloudWatch custom metrics and high-cardinality logs are the primary
  cost drivers)
- Automation: Automatic instrumentation via CloudWatch agent, AWS Distro for OpenTelemetry
  (ADOT), Container Insights for ECS/EKS. X-Ray SDK or ADOT for trace propagation.
- Source: OE design principles https://docs.aws.amazon.com/wellarchitected/latest/framework/oe-design-principles.html (accessed 2026-08-27)

**Sustainability Operations**
- RTO/RPO: N/A
- AWS Services: AWS Customer Carbon Footprint Tool, Compute Optimizer, Trusted Advisor,
  S3 Intelligent-Tiering, EC2 Auto Scaling, Instance Scheduler
- Cost Profile: Low to negative (optimization reduces cost)
- Automation: Compute Optimizer recommendations exported to EventBridge for team notification.
  Instance Scheduler for dev/test off-hours shutdown (~75% cost and energy savings).
  S3 Lifecycle rules applied automatically.
- Source: SUS06-BP01 https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/design-principles-for-sustainability-in-the-cloud.html (accessed 2026-08-27)

---

## Reference Architectures

**Three-Tier Highly-Available Web Application**
- Context: Traditional web/API workloads requiring SQL, stateful sessions, and high availability
  within a single Region.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | DNS | Route 53 | Latency/failover routing; health checks |
  | Edge | CloudFront + AWS WAF + Shield | CDN, DDoS protection, WAF rules |
  | Load Balancing | ALB (multi-AZ) | Layer-7 routing, SSL termination |
  | Compute | EC2 Auto Scaling / ECS Fargate (multi-AZ) | Stateless app tier; scales with demand |
  | Database | RDS Multi-AZ / Aurora | Relational data; automatic failover |
  | Cache | ElastiCache (multi-AZ) | Session store, hot data |
  | Object Store | S3 | Static assets, backups |

- Key Decisions: Multi-AZ must be explicitly enabled for RDS and ElastiCache (S3 and DynamoDB
  are Multi-AZ by default). Route 53 health checks with ELB + TTL ≤60 s for DNS failover.
  ELB is the single entry point — no direct EC2 exposure.
- Scaling Path: Single Region multi-AZ → add read replicas → Aurora Global DB for multi-Region
  → Active/Active with ARC.
- Source: REL10-BP01 https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_fault_isolation_multiaz_region_system.html
  + AWS Solutions Library Containerized Web App Guidance [triangulated]

**Serverless Web / API Application**
- Context: Event-driven, variable-traffic, API-first workloads requiring minimal operational
  overhead.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Frontend | CloudFront + S3 (SPA) | Static asset delivery; cache |
  | Auth | Amazon Cognito user pools | Authentication; JWT issuance |
  | API | API Gateway | REST/HTTP API; Cognito/JWT authorizer |
  | Compute | Lambda | Business logic; auto-scales to 0 |
  | Database | DynamoDB | Single-digit ms KV access |
  | Cache (opt) | ElastiCache / DAX | Hot path acceleration |
  | Event routing | EventBridge | Decoupled async processing |
  | Buffering | SQS | Spike absorption; at-least-once delivery |

- Key Decisions: Cognito user pools → JWT authorizer in API Gateway (no custom auth code).
  EventBridge for cross-service decoupling; SQS for load leveling before Lambda consumers.
  DynamoDB PITR enabled from day 1.
- Scaling Path: Single Region → DynamoDB global tables → CloudFront multi-Region origins →
  Route 53 latency routing for multi-Region active/active API.
- Source: Serverless Applications Lens https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/
  + API Gateway Cognito integration docs + Lambda refarch [triangulated]

**Multi-Account Landing Zone (Security Reference Architecture)**
- Context: Enterprise-scale AWS organization with multiple teams, workloads, and compliance
  requirements.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Org root | AWS Organizations | Account hierarchy; SCP/RCP attachment |
  | Baseline | Control Tower | Automated account vending; StackSets |
  | Identity | IAM Identity Center | SSO for all accounts |
  | Security OU | CloudTrail org trail → S3 (Log Archive) | Immutable audit log |
  | Security OU | GuardDuty + Security Hub + Config (delegated admin in Audit account) | Centralized threat detection |
  | Infrastructure OU | Transit Gateway (Network account) | Hub-and-spoke connectivity |
  | Workloads OU | One account per workload × env | Blast radius isolation |

- Key Decisions: Management account holds no workloads. SCPs/RCPs do not apply to the management
  account — enforce via separate preventive controls. From Control Tower v4.0, mandatory controls
  are not applied by default.
- Scaling Path: Start with Control Tower landing zone → add workload accounts via Account Factory
  → onboard to Security Hub as org-wide aggregator → add Network Firewall in Network account.
- Source: https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/recommended-ous-and-accounts.html
  + AWS SRA https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/architecture.html [triangulated]

---

## Scenario Coverage

**Standard Case: New greenfield production workload**
- Approach: Start with Control Tower landing zone (Security OU + Workloads OU). Create one
  account per environment (prod/staging/dev). Deploy three-tier or serverless architecture
  (choose based on compute pattern). Enable Compute Savings Plans after 3 months of stable
  baseline. Enable GuardDuty + Security Hub org-wide from day 1.
- Key Decisions: Compute type (EC2/Fargate/Lambda based on traffic pattern), DR tier (Backup &
  Restore for MVP; Warm Standby or better for production SLA), pricing model mix after
  baseline stabilizes.

**Standard Case: Existing single-account monolith migration**
- Approach: Phase 1 — enable detection stack (CloudTrail + GuardDuty) in existing account.
  Phase 2 — create Organization, migrate to multi-account via Control Tower Account Factory.
  Phase 3 — refactor monolith to service-oriented using strangler-fig with API Gateway + Lambda
  or Fargate. Phase 4 — apply WAF review pillar-by-pillar.
- Key Decisions: Prioritize Security (accounts + IAM) first, then Reliability (multi-AZ + backup),
  then cost optimization once architecture is stable.

**Edge Case: RTO < 1 minute with RPO < 30 seconds across Regions**
- Approach: Multi-Site Active/Active only. DynamoDB global tables (automatic multi-Region
  replication, typically <1 s lag) or Aurora Global Database (<1 s replication, <1 min
  secondary promotion). Route 53 latency routing + health checks + ARC routing-control for
  traffic steering. FIS experiments to validate actual RTO/RPO under failure.
- Clarification: Confirm business cost justification before Active/Active — 3–5x cost vs Backup
  & Restore. Verify Aurora Global DB secondary promotion is automated and tested.

**Edge Case: Sustainability-first architecture (regulated industry with carbon reporting)**
- Approach: SUS01 Region selection using Carbon Footprint Tool. All compute on Graviton4 (ARM)
  instances. Serverless-first (Lambda, Fargate, Aurora Serverless v2). S3 Intelligent-Tiering
  for all data stores. Instance Scheduler for all non-production environments. CloudWatch custom
  KPIs per unit of work. SUS06-BP01 cascaded team sustainability goals documented in OE runbook.
- Clarification: Ask whether the organization has a commitment to AWS Customer Carbon Footprint
  Tool reporting before designing custom per-unit KPI tracking.

**Anti-Pattern Case: Architect proposes deploying a self-managed Kubernetes cluster on EC2 with
static provisioned capacity for a new API workload with highly variable traffic**
- Clarification: Ask: (1) Is there a specific technical reason Kubernetes is required over ECS
  Fargate or EKS with Karpenter? (2) What is the expected traffic variability? Static provisioning
  for variable traffic violates both Performance Efficiency (PERF02-BP05) and Cost Optimization
  (CO-AD-1). Recommend EKS with Karpenter (auto-node provisioning) or ECS Fargate (no node
  management) with Application Auto Scaling. Flag static provisioning as SUS-ND-1, CO-ND-1, and
  PE-ND-2 anti-patterns.

**Anti-Pattern Case: Architect proposes using one AWS account for all environments (dev, staging,
production) with IAM boundaries for isolation**
- Clarification: IAM permission boundaries cannot replace account-level blast-radius isolation.
  A compromised IAM role, a service quota breach, or a misapplied Config rule in dev can affect
  production. Flag as SEC-ND-3 (CRITICAL). Require account separation under Organizations before
  any other WAF improvements. This is a mandatory prerequisite, not an optional improvement.

---

## Unverified Items

| Item | Section | Notes |
|------|---------|-------|
| Amazon Q Business (OE-AD-F) | Architecture Guardrails | OPS02-BP02 update: sourced from Nov 2024 OE update blog only. Verify against current OE pillar whitepaper before committing to a skill. |
| Regional NAT gateways for automatic multi-AZ expansion | Networking (Anti-Patterns) | Mentioned in AWS docs but specific behavior for automatic AZ expansion not triangulated to a second source. Confirm current behavior before production use. |
| CQRS eventual consistency guarantee specifics | Cloud-Native Design Patterns | Eventual consistency is a structural property of the pattern; specific lag and consistency guarantees depend on the implementation (e.g., DynamoDB Streams latency, Lambda processing time). Verify per use case. |
| DR whitepaper triangulation source (2021-04-05 blog) | Operational Patterns | Used only as secondary triangulation. The primary source is the 2022-04-01 DR whitepaper. The blog is >12mo and may not reflect current service limits. |

---

## Source Age Summary

All sources flagged ⚠️ >12mo below are the current stable editions with no newer official
replacement as of 2026-08-27:

| Source | Published | Status |
|--------|-----------|--------|
| WAF Nov 2024 update blog | 2024-11-06 | ⚠️ >12mo; current stable — no 2025/2026 edition |
| Performance efficiency pillar whitepaper | 2024-11-06 | ⚠️ >12mo; current stable |
| Cost optimization pillar whitepaper | 2024-06-27 | ⚠️ >12mo; current stable |
| DR whitepaper | 2022-04-01 | ⚠️ >12mo; current stable |
| DR Architecture blog (secondary) | 2021-04-05 | ⚠️ >12mo; secondary triangulation only |

Review this file after **2027-08-27** or when AWS announces a new WAF edition.
