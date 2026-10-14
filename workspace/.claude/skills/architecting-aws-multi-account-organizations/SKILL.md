---
name: architecting-aws-multi-account-organizations
description: "Designs and governs enterprise AWS multi-account strategies using AWS Organizations 2026. Use when architecting a new AWS organization, designing OU hierarchies, implementing SCP/RCP guardrails, choosing a landing zone approach (Control Tower / LZA / DIY), or reviewing governance and data-perimeter patterns for a multi-account AWS environment."
---

## Function

Specialist in enterprise AWS multi-account governance for AWS Organizations 2026. Covers OU hierarchy design, authorization policies (SCPs, RCPs), declarative policies, landing zone patterns (Control Tower v4.0, AFT, LZA), centralized security service administration, data-perimeter implementation, and cost governance.

## Version Context

**Technology**: AWS Organizations — Multi-Account Strategy
**Target edition**: AWS Organizations 2026
**Research date**: 2026-08-26
**Currency threshold**: Review after 2027-08-26 — Organizations ships new declarative policy types frequently.
**Support status**: Active (GA)

**Material 2026 changes**:
- Organizations created via the AWS Console **after July 10, 2026** auto-receive a root SCP denying `organizations:LeaveOrganization` and `account:CloseAccount`.
- VPC Encryption Controls added as a declarative policy type (July 6, 2026).
- AWS Control Tower Landing Zone **v4.0** (November 17, 2025): Security OU is now optional; service integrations (Config, CloudTrail, Security Roles, Backup) are individually selectable.
- Resource Control Policies (RCPs) GA since November 13, 2024 — now a standard data-perimeter tool.
- Policy taxonomy restructured: correct umbrella terms are **Authorization policies** (SCPs + RCPs) and **Declarative policies**. The old term "management policies" is deprecated.

**Deprecated terminology**: "Management policies" (use "Declarative policies" instead).

> ⚠️ **CRITICAL — Agent Warning**
> This skill targets AWS Organizations 2026. Reject any pattern that references "management policies" as an umbrella term — that is a stale 2024 and earlier concept. Do not conflate SCPs (principal-centric guardrails) with RCPs (resource-centric guardrails); both are required for a complete data perimeter.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — 8 mandatory patterns with verification commands
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — 4 architectural decision matrices
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — 6 anti-patterns with detection commands
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 5 test scenarios (canonical, edge, misuse)
- **[Blueprints & Guardrails](#blueprints--guardrails)** — Three-tier summary (this file)
- **[Verification Loop](#verification-loop)** — AWS CLI checks for each guardrail
- **[Quick Reference](#quick-reference)** — Architecture layers at a glance
- **[External Resources](#external-resources)** — Official documentation links

---

## Blueprints & Guardrails

> **Domain Complexity**: Complex (security-critical, multi-layer governance). Pattern counts: 8 Always / 4 Ask First / 6 Never.
> Full code examples and decision matrices in the linked blueprint files.

### ✅ Always Do

For full code examples and verification commands, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**Summary of mandatory patterns**:

- **Isolated Management Account** — Deploy zero workload resources (EC2, RDS, Lambda, S3 data buckets) in the management account. SCPs do not apply to management-account IAM principals; any workload there operates without organizational guardrails. Use member accounts in governed OUs for all workloads.

- **Root SCP: Deny LeaveOrganization + CloseAccount** — Attach at the org root to prevent rogue account departures. Console-created orgs post-July 10, 2026 receive this automatically; CLI/SDK/CloudFormation-created orgs and all pre-July 10, 2026 orgs must add it manually.

- **Delegate Security Services to Security Tooling Account** — Register a single dedicated member account (Security Tooling / Audit) as delegated administrator for: GuardDuty, Security Hub CSPM, Amazon Detective, AWS Config, Amazon Macie, IAM Access Analyzer, AWS Firewall Manager, AWS Audit Manager, Amazon Inspector, AWS Security Incident Response, CloudTrail, Systems Manager. GuardDuty + Detective + Security Hub CSPM **must** share the same delegated admin account or cross-service navigation breaks. Exception: Security Lake delegates to the Log Archive account.

- **Centralized Log Archive with Immutable Storage** — One S3 bucket in the Log Archive account with Object Lock (COMPLIANCE mode), SSE-KMS with CMK, and Versioning. Feed: org CloudTrail trail (multi-Region, global-service events, log file validation on), Config delivery channel, VPC Flow Logs. Restrict bucket writes to the org trail ARN via bucket policy.

- **IAM Identity Center for All Human Access** — Enable IAM Identity Center in the management account; delegate administration to the Shared Services account. Zero long-lived IAM users in member accounts. Enforce MFA for all users. For the management account specifically: assign individual users (not groups) to permission sets.

- **Management Account Root User Hardening** — Register ≥ 2 MFA devices (FIDO2 passkey preferred). Zero root access keys. Group-email root credential with split custody (password group ≠ MFA group). Enable centralized root access management for member accounts to remove member-account root credentials entirely.

- **Data Perimeter: SCP + RCP + VPC Endpoint Policies** — Implement all three axes:
  1. Identity axis (RCP): deny non-org principals from accessing org resources (`aws:PrincipalOrgID`); preserve `aws:PrincipalIsAWSService` and `aws:ViaAWSService` exceptions.
  2. Resource axis (SCP): deny org principals from accessing resources outside the org (`aws:ResourceOrgID`).
  3. Network axis (SCP + VPC endpoint policy): restrict access to approved VPCs (`aws:SourceVpc`, `aws:SourceVpce`).

- **SCP Deny-List Strategy: Keep FullAWSAccess at All OU Levels** — Never remove the default `FullAWSAccess` managed SCP without an explicit Allow-list replacement. Use targeted `Effect: Deny` statements for prohibited actions on top of `FullAWSAccess`. Test all SCP changes in the Policy Staging OU before applying to production OUs.

### ⚠️ Ask First

For complete decision matrices with trade-off tables, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

**Summary of decision points**:

- **OU Structure Design** — Ask: "Does the dev environment require meaningfully different SCPs than test?" If yes, create separate Dev and Test OUs. If not, a single NonProd OU reduces maintenance. Always include: Security OU (Log Archive + Security Tooling), Infrastructure OU, Workloads OU (Prod/NonProd), Suspended OU, and Policy Staging OU. Sandbox OU when developers need isolated exploration.

- **Multi-Account Networking Topology** — Ask: "Is centralized traffic inspection (firewall, IDS/IPS) required?" If yes, Transit Gateway with an Inspection VPC is the only scalable option. Ask: "Is IPv4 address space constrained?" If yes, evaluate VPC Sharing. Default recommendation: Transit Gateway hub-spoke for >5 VPCs or any hybrid connectivity requirement.

- **Landing Zone Approach: Control Tower vs DIY vs LZA** — Ask: "Are you operating in GovCloud, Secret, or Top Secret regions, or require DoD compliance?" If yes, LZA is required. Ask: "Do you need full IaC customization beyond what Control Tower v4.0 offers?" If yes, evaluate LZA on top of Control Tower. Default for standard enterprise: Control Tower.

- **RI and Savings Plans Sharing Strategy** — Ask: "Does the organization use chargeback (BU charged exact AWS costs) or showback (BU sees costs but central IT pays)?" Chargeback → Restricted Group Sharing. Showback → Organization-wide sharing. Note: sharing settings finalize at 23:59:59 UTC on the last day of each month.

### 🚫 Never Do

For complete anti-patterns with detection commands, see [Never Do Patterns](./blueprints/never-do-patterns.md).

**Summary of prohibited patterns**:

| Anti-Pattern | Risk | Consequence |
|---|---|---|
| **Workloads in the management account** | CRITICAL | SCPs do not apply; compromised workload = full org takeover |
| **No organization CloudTrail trail** | CRITICAL | Zero API audit in unlogged accounts; compliance violation (SOC 2, PCI-DSS, HIPAA) |
| **SCP Allow-list without FullAWSAccess** | HIGH | Complete service interruption for all workloads in affected OU; potentially unrecoverable without management account |
| **No RCP data perimeter** | HIGH | External identities can access S3, KMS, SQS, Secrets Manager via misconfigured resource policies — SCPs cannot block this |
| **Security services in misaligned delegated admin accounts** | HIGH | Security Hub → Detective navigation broken; Audit Manager evidence gaps |
| **No cost alerting or budget alerts** | MEDIUM | Cost overruns discovered monthly; no chargeback/showback accuracy |

---

## Integration Patterns

For complete integration examples, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**Architecture layer integrations**:

- **AWS Organizations ↔ AWS Control Tower** — Control Tower is an orchestration layer on top of Organizations. Use Control Tower Account Factory (or AFT) for account vending; Organizations provides the policy hierarchy. v4.0 makes Security OU and service integrations individually optional.

- **AWS Organizations ↔ IAM Identity Center** — IAM Identity Center integrates with Organizations to assign permission sets across all member accounts from a single pane. Delegate IdC administration to the Shared Services account.

- **AWS Organizations ↔ AWS Config / CloudTrail** — Organization-level Config aggregator and org CloudTrail trail collect data from all member accounts automatically; delegated admin accounts manage them without management-account access.

- **SCPs ↔ RCPs (Data Perimeter)** — SCPs constrain what org IAM principals can do (identity-centric). RCPs constrain what can be done to org resources regardless of who the principal is (resource-centric). Both are required; neither alone closes the data perimeter gap.

**Common problems**:

- **Problem**: New account is not receiving SCP enforcement → **Solution**: Verify the account is in an OU (not directly under root without SCP); check `aws organizations list-policies-for-target --target-id <account-id>`.
- **Problem**: Security Hub finding does not link to Detective → **Solution**: Verify GuardDuty, Security Hub CSPM, and Detective share the same delegated admin account ID.
- **Problem**: AFT account provisioning fails → **Solution**: Confirm Control Tower is deployed and the AFT management account has the required IAM roles; verify AFT is not targeting an unsupported region (Spain, Zurich, Tel Aviv, UAE, Hyderabad — ⚠️ verify at AFT docs).

---

## Verification Loop

Run these checks to validate a multi-account environment against the mandatory guardrails.

### 1. Management Account Workload Isolation
```bash
aws resourcegroupstaggingapi get-resources \
  --profile management-account \
  --query "ResourceTagMappingList[*].ResourceARN"
# Expected: zero compute/storage/database ARNs
aws iam list-users --profile management-account
# Expected: no long-term IAM users
```

### 2. Root SCP Coverage
```bash
aws organizations list-policies --filter SERVICE_CONTROL_POLICY \
  --query "Policies[*].{Name:Name,Id:Id}"
# Find the deny-leave-org SCP, then confirm root is a target:
aws organizations list-targets-for-policy --policy-id <policy-id>
# Expected: root ID (r-xxxx) in targets
```

### 3. Delegated Admin Alignment
```bash
for svc in guardduty.amazonaws.com securityhub.amazonaws.com \
  detective.amazonaws.com config.amazonaws.com; do
  echo -n "$svc: "
  aws organizations list-delegated-administrators \
    --service-principal $svc \
    --query "DelegatedAdministrators[0].Id" --output text
done
# Expected: same account ID for GuardDuty, Security Hub, Detective
```

### 4. Log Archive Immutability
```bash
aws s3api get-object-lock-configuration \
  --bucket <central-log-bucket> --profile log-archive
# Expected: ObjectLockConfiguration.ObjectLockEnabled = Enabled
aws cloudtrail describe-trails --include-shadow-trails false \
  --query "trailList[?IsOrganizationTrail==\`true\`]"
# Expected: at least one organization trail
```

### 5. IAM Identity Center (No Long-Lived IAM Users)
```bash
aws sso-admin list-instances
# Expected: at least one Identity Center instance
aws iam list-users --profile <any-member-account>
# Expected: zero IAM users
```

### 6. RCP Data Perimeter
```bash
aws organizations list-policies --filter RESOURCE_CONTROL_POLICY \
  --query "Policies[*].{Name:Name,Id:Id}"
# Expected: at least one RCP beyond RCPFullAWSAccess
```

### 7. Cost Alerting
```bash
aws budgets describe-budgets --account-id <management-account-id> \
  --query "Budgets[*].{Name:BudgetName,Type:BudgetType}"
# Expected: at least one budget configured
```

**Troubleshooting**:
- SCP not applying → Check account is in an OU with SCP attached; management account is always exempt.
- RCP condition blocks AWS services → Add `"BoolIfExists": {"aws:PrincipalIsAWSService": "false"}` exception.
- Control Tower drift detected → Run re-register OU from Control Tower console; do not manually repair via Organizations.

---

## Quick Reference

**Standard Enterprise Landing Zone layers**:

| Layer | Account / Service | Purpose |
|---|---|---|
| Org governance | Management account + Organizations | Policy hierarchy; consolidated billing |
| Identity | IAM Identity Center (Shared Services) | Federated human access; permission sets |
| Security control plane | Security Tooling / Audit account | GuardDuty, Security Hub, Config, Detective, Macie delegated admin |
| Logging | Log Archive account | Immutable org trail S3; Config delivery; VPC Flow Logs |
| Networking | Network account | Transit Gateway; centralized DNS; centralized egress + inspection VPC |
| Shared services | Shared Services account | AMI sharing; Service Catalog; Route 53 Resolver; PrivateLink |
| Backup | Backup account | AWS Backup delegated admin; cross-account vaults |
| Workloads | Workloads OU | Business application accounts (Prod/NonProd child OUs) |
| Experimentation | Sandbox OU | Developer free-form accounts; no prod connectivity |
| Orchestration | AWS Control Tower | Account vending; controls library; drift detection |

**Critical limits**:

| Resource | Limit | Notes |
|---|---|---|
| OU nesting depth | 5 levels max under root | Use only when benefit is clear |
| Concurrent account closures | 3 per request | Minimum account age: 4 days |
| MFA devices per root user | Up to 8 | Register ≥ 2 |
| Delegated admins per service | 1 per service principal | GuardDuty/Security Hub/Detective must share the same account |

**Scaling path**:
- < 50 accounts: Control Tower + manual Account Factory
- 50–500 accounts: Add AFT for automated account vending
- > 500 accounts: Add LZA for declarative policy orchestration and complex networking

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/architecting-aws-multi-account-organizations/
├── SKILL.md                              ← This file (summary + guardrails)
└── blueprints/
    ├── always-do-patterns.md             ← ✅ 8 mandatory patterns with AWS CLI verification
    ├── ask-first-decisions.md            ← ⚠️ 4 decision matrices with trade-off tables
    ├── never-do-patterns.md              ← 🚫 6 anti-patterns with detection commands
    └── evaluation-scenarios.md           ← 5 test scenarios (canonical, edge, misuse)
```

---

## External Resources

### Official Documentation
- [AWS Organizations — Concepts](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_getting-started_concepts.html) — Root, OU, management account, SCP, RCP, declarative policy definitions
- [AWS Organizations — SCPs](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html) — SCP authoring, attachment, deny-list strategy
- [AWS Organizations — RCPs](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_rcps.html) — Resource Control Policies (GA November 13, 2024)
- [AWS Organizations — Management Account Best Practices](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices_mgmt-acct.html) — Management account isolation; July 10, 2026 auto-SCP
- [AWS Whitepaper: Organizing Your AWS Environment](https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/) — OU design, recommended OUs and accounts (April 30, 2025)

### Security Reference Architecture
- [AWS SRA — Security Tooling Account](https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/security-tooling.html)
- [AWS SRA — Log Archive Account](https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/log-archive.html)
- [IAM — Data Perimeters](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_data-perimeters.html)
- [IAM — Root User Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/root-user-best-practices.html)

### Landing Zone & Automation
- [AWS Control Tower — How It Works](https://docs.aws.amazon.com/controltower/latest/userguide/how-control-tower-works.html)
- [Account Factory for Terraform (AFT)](https://docs.aws.amazon.com/controltower/latest/userguide/aft-overview.html)
- [Landing Zone Accelerator (LZA)](https://docs.aws.amazon.com/solutions/latest/landing-zone-accelerator-on-aws/solution-overview.html)

### Community Resources (verified)
- [SCP Examples](https://github.com/aws-samples/service-control-policy-examples) — Community-maintained
- [Data Perimeter Policy Examples](https://github.com/aws-samples/data-perimeter-policy-examples) — Community-maintained
