---
name: governing-aws-organizations
description: "Designs and enforces AWS Organizations multi-account governance (all-features mode, 2024-2025). Use when architecting landing zones, OU hierarchies, SCP/RCP/declarative policy guardrails, delegated-admin security tooling, or account vending strategies for enterprise AWS environments."
---

## Function

Specialist in AWS Organizations multi-account governance for the **2024-2025 all-features edition**, covering OU design, SCP/RCP/declarative policy guardrails, management-account hygiene, centralized security service delegation, and account vending.

---

## Version Context

**Technology**: AWS Organizations — Multi-Account Governance Architecture
**Target edition**: 2024-2025 (all-features mode)
**Research date**: 2026-07-31
**Review by**: 2027-07-31
**Service scope**: Global service hosted in `us-east-1`

**Key additions in this edition**:
- **Resource Control Policies (RCPs)** — resource-centric guardrails (GA); `RCPFullAWSAccess` is auto-attached at root/OU/account and cannot be detached; counts toward the 5-RCP-per-entity hard limit
- **Declarative policies** (GA) — EC2, S3, Backup, Tag, Security Hub, Inspector, Bedrock, AI services opt-out; enforce durable service configurations that survive new APIs
- **Default root SCP** — auto-attached to console-created organizations AFTER July 10, 2026; denies `organizations:LeaveOrganization` and `account:CloseAccount`; orgs created via CLI/SDK/CloudFormation and any pre-existing org MUST attach this guardrail manually
- **Security Hub central configuration policies** — org-wide, delegated-admin managed

**Terminology corrections** (reject old patterns):
- "master account" → **management account**
- "AWS SSO" → **AWS IAM Identity Center** (renamed July 26, 2022; legacy `sso`/`identitystore` API namespaces retained for backward compatibility)
- "SCPs are the only org-level guardrail" → misinformation; SCP + RCP + declarative policies form the current guardrail surface

> CRITICAL — Agent Warning: Patterns from pre-2024 editions are treated as misinformation. Apply 2024-2025 patterns exclusively.

---

## Quick Navigation

- **[Always-Do Patterns](./blueprints/always-do-patterns.md)** — AD-1 through AD-9: mandatory architectural guardrails with CLI verification
- **[Ask-First Decisions](./blueprints/ask-first-decisions.md)** — AF-1 through AF-6: architectural crossroads with tradeoff matrices
- **[Never-Do Anti-Patterns](./blueprints/never-do-patterns.md)** — NP-1 through NP-8: prohibited patterns with side-by-side wrong/correct examples
- **[Reference Architecture](./blueprints/reference-architecture.md)** — Enterprise landing zone topology, quota table, and scaling path
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 5 test cases: canonical, edge, and misuse
- **[Verification Loop](#verification-loop)** — AWS CLI validation commands
- **[Quick Reference](#quick-reference)** — Critical limits at a glance

---

## Blueprints & Guardrails

### ✅ Always Do

Full patterns with CLI verification commands in [Always-Do Patterns](./blueprints/always-do-patterns.md).

| # | Pattern | WAF Pillars | Risk if omitted |
|---|---------|-------------|-----------------|
| AD-1 | Enable **all-features mode** (not consolidated-billing-only) | Security, OpEx | SCPs/RCPs/declarative policies unavailable |
| AD-2 | **Management account empty of workloads**; use delegated administrators for every security service | Security | Un-guardrailed blast radius (SCPs do not restrict mgmt account) |
| AD-3 | **Harden management account root user**: MFA enforced, break-glass process, quarterly access review | Security | Highest-privilege, un-guardrailed account compromised |
| AD-4 | **Root-level SCP denying `organizations:LeaveOrganization` and `account:CloseAccount`** | Security, OpEx | Member accounts escape governance, billing, and audit |
| AD-5 | **Organization CloudTrail trail** (multi-Region) → central S3 in Log Archive account; log-file validation + SSE-KMS | Security, OpEx | No tamper-resistant org-wide audit record |
| AD-6 | **Delegate GuardDuty, Security Hub, Config, IAM Access Analyzer** to dedicated Audit account (same account across all Regions) | Security | Security tooling in un-guardrailed management account |
| AD-7 | **Function-based OU design** (Security, Infrastructure, Workloads, Sandbox, ...); keep core Security OU = Log Archive + Audit accounts only | OpEx, Security | Policy confusion; Control Tower non-conformance |
| AD-8 | **IAM Identity Center organization instance** for all human workforce access; connect corporate IdP via SAML/SCIM | Security, OpEx | Long-lived IAM users; no centralized federation or audit |
| AD-9 | **Declarative, Tag, and Backup policies** attached to enforce durable org-wide baselines; stage in Policy Staging OU first | Security, Cost, Reliability | Service config drift; untagged resources; backup gaps |

### ⚠️ Ask First

Full decision matrices in [Ask-First Decisions](./blueprints/ask-first-decisions.md).

- **AF-1 — SCP strategy: Deny-list vs Allow-list** — Deny-list (keep `FullAWSAccess` + add explicit Deny) is the AWS default and recommended starting point. Allow-list requires an explicit Allow at EVERY level (root → OU → account); a missing Allow at root locks out all member accounts. Ask: "Do you need an explicit service whitelist?"
- **AF-2 — AWS Control Tower vs. DIY landing zone** — Control Tower is managed + prescriptive (landing zone in < 1 hr, Account Factory, drift detection). DIY gives full control but requires owning controls, vending, and drift detection. Ask: "Do any requirements conflict with Control Tower's opinionated model?"
- **AF-3 — OU hierarchy depth and structure** — Functional OUs (AWS-recommended) vs. environment-nested (Prod/Non-Prod under Workloads) vs. deep hierarchy (up to 5 levels). Ask: "Do prod and non-prod need materially different guardrails?"
- **AF-4 — Account granularity** — Default: one account per workload per environment (strong isolation, clean cost mapping). Default quota = 10 accounts; request increase for any real-scale deployment. Ask: "What isolation and cost-attribution granularity do you need? Do you need a quota increase?"
- **AF-5 — Account vending mechanism** — Account Factory (managed), Account Factory for Terraform/AFT (GitOps), or direct Organizations API + CloudFormation StackSets (DIY). Ask: "Which integrates with your existing IaC and approval workflows?"
- **AF-6 — SCP vs RCP vs declarative policy** — SCP = principal permission guardrail; RCP = resource perimeter (who may access your resources); declarative policy = service configuration enforcement. Effective permission = SCP ∩ RCP ∩ IAM policies. Ask: "Is this about what identities can DO (SCP), what can touch your RESOURCES (RCP), or how a SERVICE is CONFIGURED (declarative)?"

### 🚫 Never Do

Full anti-patterns with wrong / correct examples in [Never-Do Anti-Patterns](./blueprints/never-do-patterns.md).

| # | Anti-Pattern | Risk Level | Impact |
|---|-------------|------------|--------|
| NP-1 | **Workloads or production data in the management account** | CRITICAL | Un-guardrailed blast radius; data breach; compliance failure |
| NP-2 | **Removing `FullAWSAccess` without a replacement Allow at the root** | CRITICAL | Org-wide lockout of ALL member-account actions |
| NP-3 | **Attaching untested SCPs directly to the organization root** | HIGH | Simultaneous lockout of all member accounts |
| NP-4 | **No SCP blocking `LeaveOrganization`/`CloseAccount`** | HIGH | Member accounts escape governance, billing, and audit continuity |
| NP-5 | **Single shared account for all workloads/environments** | HIGH | No blast-radius isolation; no cost attribution; compliance violation |
| NP-6 | **Per-account CloudTrail only (no org trail)** | HIGH | Audit gaps; member admins can disable logging to hide activity |
| NP-7 | **Management account designated as delegated admin for security services** | MEDIUM | Least-privilege violation; widens blast radius on compromise |
| NP-8 | **Mirroring corporate org chart in OUs; polluting core Security OU with extra accounts** | MEDIUM | Governance drift; Control Tower non-conformance |

---

## Integration Patterns

See full topology in [Reference Architecture](./blueprints/reference-architecture.md).

**AWS Organizations integrates with**:
- **AWS CloudTrail** — Organization trail logs all accounts; member accounts cannot modify or delete it
- **AWS Control Tower** — Orchestrates Organizations + Service Catalog + IAM Identity Center for a managed landing zone
- **Amazon GuardDuty** — Delegated-admin auto-enable ALL; Regional service; 50,000 member limit per Region
- **AWS Security Hub** — Central configuration policies + delegated admin; same account across all Regions
- **AWS Config** — Organization aggregator in the Audit account; delegated admin supported
- **IAM Identity Center** — Organization instance (in management account); permission sets across member accounts
- **AWS Backup** — Backup policies centrally enforced through Organizations policy inheritance

**Common failure modes**:
- **Problem**: SCP blocks service-linked-role actions, breaking Config/GuardDuty integration → **Solution**: Verify trusted-access enablement per service (`aws organizations enable-aws-service-access`); service-linked roles are exempt from SCP restrictions but trusted access must be enabled
- **Problem**: GuardDuty auto-enable = NEW misses existing accounts → **Solution**: Set auto-enable = ALL via `update-organization-configuration`; bulk-enroll existing members
- **Problem**: IAM Identity Center account limit hit at scale → **Solution**: Request quota increase (default 7,000; adjustable)

---

## Verification Loop

Run after every governance design or change:

### 1. All-Features Mode
```bash
aws organizations describe-organization --query 'Organization.FeatureSet'
# Expected: "ALL"
```

### 2. Root-Level Guardrail SCPs
```bash
ROOT_ID=$(aws organizations list-roots --query 'Roots[0].Id' --output text)
aws organizations list-policies-for-target \
  --target-id "$ROOT_ID" \
  --filter SERVICE_CONTROL_POLICY \
  --query 'Policies[].Name'
# Expected: includes the LeaveOrganization/CloseAccount deny SCP
# (auto-present for console-created orgs after July 10, 2026; attach manually otherwise)
```

### 3. Organization CloudTrail Trail
```bash
aws cloudtrail describe-trails \
  --query 'trailList[?IsOrganizationTrail==`true`].[Name,IsMultiRegionTrail,S3BucketName]'
# Expected: one row with IsOrganizationTrail=true, IsMultiRegionTrail=true
```

### 4. Delegated Administrators
```bash
aws organizations list-delegated-administrators \
  --query 'DelegatedAdministrators[].Id'
aws guardduty list-organization-admin-accounts
aws securityhub list-organization-admin-accounts
# Expected: admin account = Audit account, NOT the management account
```

### 5. Management Account Resource Inventory
```bash
aws resourcegroupstaggingapi get-resources \
  --query 'ResourceTagMappingList[].ResourceARN'
# Expected: near-empty; only org-admin resources (not application workloads)
```

**Troubleshooting**:
- `AccessDenied` on `describe-organization` → Run from management account or a delegated-admin account
- GuardDuty not auto-enabled on new accounts → Auto-enable was NEW; change to ALL and bulk-enroll existing members
- Unexpected SCP evaluation → Use IAM Policy Simulator + `get-service-last-accessed-details` from CloudTrail to diagnose

---

## Quick Reference

**Essential CLI commands**:
```bash
aws organizations describe-organization                          # Verify FeatureSet = ALL
aws organizations list-roots                                     # Get root ID
aws organizations list-organizational-units-for-parent --parent-id <root-id>
aws organizations list-policies --filter SERVICE_CONTROL_POLICY
aws organizations list-policies --filter RESOURCE_CONTROL_POLICY
aws organizations describe-effective-policy --policy-type TAG_POLICY
aws organizations list-delegated-administrators
aws cloudtrail describe-trails --query 'trailList[?IsOrganizationTrail]'
aws sso-admin list-instances                                     # Identity Center org instance
```

**Critical limits (AWS Organizations 2024-2025)**:

| Resource | Default / Hard Limit | Adjustable |
|----------|---------------------|-----------|
| Max accounts per org | 10 default; up to 50,000 based on qualification | Yes (mgmt acct only) |
| Roots per org | 1 | No |
| OUs per org | 2,000 | — |
| OU nesting depth | 5 levels under root | No (hard) |
| SCPs per org | 10,000 | — |
| SCPs attached per entity | 10 (min 1 when SCPs enabled) | No (hard) |
| SCP max document size | 10,240 characters | No |
| RCPs attached per entity | 5 (`RCPFullAWSAccess` counts) | No (hard) |
| RCP max document size | 5,120 characters | No |
| Declarative policies per org | 1,000; 10 per entity | No |
| Concurrent account creation | 5 in progress | No |
| IAM Identity Center accounts | 7,000 | Yes |
| GuardDuty members per delegated admin (per Region) | 50,000 | — |

> Re-verify live limits at [AWS Organizations Quotas](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_reference_limits.html) before design commitments. Request increases in `us-east-1`.

---

## Blueprints Directory Structure

```
.claude/skills/governing-aws-organizations/
├── SKILL.md                              <- This file (summary + guardrails)
└── blueprints/
    ├── always-do-patterns.md             <- AD-1 to AD-9: mandatory patterns with CLI verification
    ├── ask-first-decisions.md            <- AF-1 to AF-6: decision matrices with tradeoff tables
    ├── never-do-patterns.md              <- NP-1 to NP-8: anti-patterns with wrong/correct examples
    ├── reference-architecture.md         <- Enterprise landing zone topology + quota table
    └── evaluation-scenarios.md           <- 5 test cases (canonical, edge, misuse)
```

---

## External Resources

### Official AWS Documentation (all accessed 2026-07-31)
- [Terminology and concepts — AWS Organizations](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_getting-started_concepts.html)
- [Service control policies (SCPs)](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html)
- [SCP evaluation — deny-list vs allow-list](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps_evaluation.html)
- [Best practices for the management account](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices_mgmt-acct.html)
- [Quotas and service limits](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_reference_limits.html)
- [What Is AWS Control Tower?](https://docs.aws.amazon.com/controltower/latest/userguide/what-is-control-tower.html)
- [Creating a trail for an organization (CloudTrail)](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/creating-trail-organization.html)
- [Managing GuardDuty accounts with Organizations](https://docs.aws.amazon.com/guardduty/latest/ug/guardduty_organizations.html)
- [What is IAM Identity Center?](https://docs.aws.amazon.com/singlesignon/latest/userguide/what-is.html)

### Whitepaper (dated)
- [Organizing Your AWS Environment Using Multiple Accounts](https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/organizing-your-aws-environment.html) — **Publication date: April 30, 2025**; accessed 2026-07-31
- [Recommended OUs and accounts](https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/recommended-ous-and-accounts.html) — accessed 2026-07-31
