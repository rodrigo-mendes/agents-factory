# Never Do Patterns — applying-aws-well-architected

Source: AWS Well-Architected Framework, November 6, 2024 edition (research date 2026-08-27).
Sources without a publish date below were accessed 2026-08-27.

---

## ND-1 — Long-Term Static Access Keys for Humans (CRITICAL)

**Why**: Static credentials never expire; a leaked key grants indefinite access. Violates Security design principle 1.
**Instead**: IAM Identity Center + STS temporary credentials. No human has an IAM user with access keys.
**Detection**: `aws iam generate-credential-report` — any `access_key_1_active` = true for a human user. Config rule `iam-user-no-policies-check`.
**Impact**: Data breach, compliance violation, full account takeover.
**Source**: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html

---

## ND-2 — Root User for Daily Operations (CRITICAL)

**Why**: Root has unrestricted access, cannot be scoped by IAM policies, and bypasses SCPs.
**Instead**: Lock root with a hardware MFA passkey, delete root access keys, use root only for the 4 tasks that require it (e.g., closing the account, changing support plan).
**Detection**: CloudTrail filter `userIdentity.type = Root`. Config rule `root-account-mfa-enabled`.
**Impact**: Full account takeover; no guardrail can limit root actions.
**Source**: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html

---

## ND-3 — Multiple Unrelated Workloads in One AWS Account (CRITICAL)

**Why**: An incident, quota exhaustion, or IAM misconfiguration in one workload affects all others; no SCP boundary is possible inside one account. Violates SEC01-BP01. IAM permission boundaries cannot replace account-level isolation.
**Instead**: One account per workload × environment under named OUs; Control Tower for account vending.
**Detection**: AWS Organizations — count accounts vs workload/environment combinations.
**Impact**: Blast radius amplification; compliance scope expansion; shared quota exhaustion.
**Source**: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_securely_operate_multi_accounts.html

---

## ND-4 — Single-AZ Production Deployment (CRITICAL)

**Why**: A single-AZ workload has 0% availability during an AZ failure. Violates Reliability design principle 3 (scale horizontally).
**Instead**: EC2 Auto Scaling across ≥2 AZs + ELB; RDS Multi-AZ; ElastiCache Multi-AZ; ECS/EKS tasks across AZs.
**Detection**: Auto Scaling group `AvailabilityZones` list length; RDS `MultiAZ` attribute.
**Impact**: Full workload outage during AZ failure (typically 15 min–4 hours historically, per research).
**Source**: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/use-fault-isolation-to-protect-your-workload.html

---

## ND-5 — No Disaster Recovery Plan (CRITICAL)

**Why**: Without a defined, tested DR strategy, recovery is ad hoc; MTTR without a runbook is measured in days. Violates REL13-BP01–05.
**Instead**: Define RTO/RPO SLAs, select a DR tier, implement with AWS Backup + Elastic Disaster Recovery + Route 53 ARC, test quarterly.
**Detection**: AWS Well-Architected Tool review — REL13 question set flagging no DR strategy.
**Impact**: Extended outage; potential total data loss; regulatory violation where retention rules apply.
**Source**: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_planning_for_recovery_disaster_recovery.html

---

## ND-6 — Manual Click-Ops Production Changes (CRITICAL)

**Why**: Console changes are not reproducible or version-controlled; drift compounds. Violates OE design principle 3.
**Instead**: CloudFormation/CDK in Git, deployed through CI/CD; Systems Manager Automation for runbooks.
**Detection**: CloudTrail — resource create/modify events not attributed to CloudFormation stack updates.
**Impact**: Configuration drift, failed audits, unrecoverable state, incident amplification.
**Source**: https://docs.aws.amazon.com/wellarchitected/latest/framework/oe-design-principles.html

---

## ND-7 — 100% On-Demand Pricing for Stable Compute (HIGH)

**Why**: Stable baselines on On-Demand forgo available 66–72% discounts. Violates COST07.
**Instead**: Compute Savings Plans for baseline (up to 66%); Spot for fault-tolerant burst (up to 90%); On-Demand only for unpredictable spikes.
**Detection**: Cost Optimization Hub — Savings Plans coverage and potential savings; Compute Optimizer.
**Impact**: Cost overrun; missed 40–66% savings on steady-state fleet.
**Source**: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/select-the-best-pricing-model.html

---

## ND-8 — Static Over-Provisioning Instead of Elastic Scaling (HIGH)

**Why**: Violates Cost Optimization (consumption model), Performance Efficiency (PE-AD-2 right-size) and Sustainability (SUS-AD-B). "Two hosts at 30% is less efficient than one at 60%."
**Instead**: EC2 Auto Scaling + CloudWatch KPI alarms; Lambda or Fargate; apply Compute Optimizer recommendations on a 14-day+ cycle.
**Detection**: Compute Optimizer "Over-provisioned" share; CloudWatch average CPU < 20% over 2 weeks on a fixed fleet.
**Impact**: Cost overrun; energy waste.
**Source**: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/design-principles-for-sustainability-in-the-cloud.html

---

## ND-9 — Shared NAT Gateway Across Availability Zones (HIGH)

**Why**: A single NAT gateway for all AZs is a cross-AZ single point of failure and adds cross-AZ data transfer cost.
**Instead**: One NAT gateway per AZ; route each AZ's private subnet 0.0.0.0/0 to the NAT in the same AZ.
**Detection**: VPC route tables — private subnets of multiple AZs sharing one NAT target.
**Impact**: Outage for all private subnets if the NAT's AZ fails.
**Source**: https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-basics.html
**Note**: Regional NAT gateway automatic multi-AZ expansion behavior is (unverified) — confirm before relying on it.

---

## ND-10 — NAT/IGW for S3 or DynamoDB from Private Subnets (MEDIUM)

**Why**: S3 and DynamoDB support free gateway VPC endpoints; NAT adds per-GB processing cost ($0.045/GB per research) and an unnecessary internet path.
**Instead**: Free S3 and DynamoDB gateway endpoints on all private route tables. Interface endpoints only for on-premises access via Direct Connect/VPN.
**Detection**:
```bash
aws ec2 describe-route-tables \
  --query 'RouteTables[*].Routes[?DestinationPrefixListId!=null].[DestinationPrefixListId,GatewayId]'
# Expected: pl-* routes to vpce-*, not nat-* or igw-*
```
**Source**: https://docs.aws.amazon.com/vpc/latest/privatelink/gateway-endpoints.html

---

## ND-11 — Spot Instances for Stateful or Uninterruptible Workloads (HIGH)

**Why**: Spot gives a 2-minute interruption notice; stateful workloads lose state.
**Instead**: On-Demand or Reserved Instances for stateful workloads; Spot only for fault-tolerant, stateless or checkpointed batch.
**Detection**: EC2 instances with Spot lifecycle running stateful services.
**Impact**: Data loss, transaction corruption, extended recovery.
**Source**: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/select-the-best-pricing-model.html
