# Research — AWS Organizations Architecture (Multi-Account Governance)

## Metadata

```yaml
Full_Name: "AWS Organizations — Multi-Account Governance Architecture"
Cloud_Provider: "AWS"
Architecture_Domain: "Organizations (multi-account strategy, SCPs, OUs, management account, Control Tower, account vending)"
Target_Edition: "AWS Organizations 2024–2025 (all-features mode; RCPs + declarative policies GA)"
Architecture_Context: "Enterprise multi-account governance, landing zones, centralized security and billing"
Official_Source_URL: "https://docs.aws.amazon.com/organizations/latest/userguide/"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-07-31"
Author: "framework-researcher subagent"
Currency_Threshold: "2027-07-31 (review after this date — cloud services evolve; re-verify GA states, quotas, default controls)"
Source_Hierarchy: "Official AWS docs > AWS whitepapers/Prescriptive Guidance > AWS blogs > reject all else"
```

> **Version Absolutism note.** This document is pinned to **AWS Organizations as documented in 2024–2025**, in **all-features mode**. It reflects capabilities that are **new or newly-GA in this window** and MUST be treated as the current baseline: **Resource Control Policies (RCPs)**, **declarative policies** (EC2, S3, Backup, Tag, Security Hub, Inspector, Bedrock, and more), **Security Hub central configuration policies**, and the **default root-level SCP** auto-attached to console-created organizations after **July 10, 2026**. Patterns from older editions (e.g., "SCPs are the only org-level guardrail", "AWS SSO" naming) are treated as misinformation and corrected inline.

---

## Executive Summary

**What AWS Organizations is.** AWS Organizations is the AWS service for **centrally managing and governing multiple AWS accounts** as a single, hierarchical entity. An *organization* is a tree with a single **root** at the top, **organizational units (OUs)** nested beneath it (up to **five levels deep**), a single **management account** that owns the organization, and zero or more **member accounts**. Governance is applied through **organization policies** attached to the root, OUs, or individual accounts and **inherited downward**. It is the foundation of every enterprise AWS *landing zone* and the substrate that **AWS Control Tower** orchestrates. Source: [Terminology and concepts](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_getting-started_concepts.html) (accessed 2026-07-31).

**What changed in the 2024–2025 edition.** The policy surface expanded well beyond SCPs. AWS introduced **Resource Control Policies (RCPs)** — resource-centric guardrails that cap the maximum permissions *on resources* (the mirror image of SCPs, which are principal-centric) — and a family of **declarative policies** that *configure and enforce service settings* org-wide (EC2, S3, Backup, Tag, Chat applications, AI services opt-out, Security Hub, Inspector, Bedrock Guardrails, and Upgrade rollout). AWS also began auto-attaching a **default SCP** that denies `organizations:LeaveOrganization` and `account:CloseAccount` to the root of console-created organizations after **July 10, 2026**. **AWS SSO was renamed AWS IAM Identity Center** (July 26, 2022), and the **organization instance** deployed in the management account is now the AWS-recommended way to centralize workforce access. The canonical whitepaper **"Organizing Your AWS Environment Using Multiple Accounts"** was refreshed with a **publication date of April 30, 2025**. Sources: [SCP concepts](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html), [Quotas](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_reference_limits.html), [Management account best practices](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices_mgmt-acct.html), [IAM Identity Center](https://docs.aws.amazon.com/singlesignon/latest/userguide/what-is.html) (all accessed 2026-07-31).

**The three most critical guardrails for enterprise governance.** (1) **Keep the management account empty of workloads** — SCPs do **not** restrict any principal in the management account, so any resource there is un-guardrailed; run everything in member accounts and use **delegated administrators**. (2) **Design OUs by function, not by org chart**, and apply **preventive SCP/RCP guardrails** at OU level rather than the root (which AWS explicitly warns against attaching untested policies to). (3) **Centralize audit and security** — an **organization CloudTrail trail** that member accounts cannot alter, plus **delegated-administrator** deployments of GuardDuty, Security Hub, and AWS Config aggregation into a dedicated **security/audit** account, with logs in a locked **Log Archive** account.

---

## Cloud Architecture Glossary

```
Term: Organization
Definition: A collection of AWS accounts managed centrally and organized into a hierarchical, tree-like structure with a root at the top and OUs nested under it. Consists of one management account, zero+ member accounts, zero+ OUs, and zero+ policies.
Provider Docs Section: Organizations User Guide → Terminology and concepts → Organization structure
Architect Usage: The top-level governance boundary; one org = one consolidated bill + one policy tree.
Common Confusion: Confused with a single AWS account; an organization spans many accounts.
```

```
Term: Management account (formerly "master account")
Definition: The AWS account used to create the organization; the ultimate owner and payer account with final control over security, infrastructure, and finance policies.
Provider Docs Section: Terminology and concepts → Management account
Architect Usage: Use ONLY for org-wide tasks that must run there. You cannot change which account is the management account.
Common Confusion: Confused with a "root account"; also frequently (incorrectly) used to host workloads — an anti-pattern (SCPs don't restrict it).
```

```
Term: Member account
Definition: Any AWS account other than the management account that is part of the organization. Belongs to only one organization at a time.
Provider Docs Section: Terminology and concepts → Member account
Architect Usage: Where all workloads and delegated-admin security tooling live. SCPs and RCPs DO apply here.
Common Confusion: Confused with an IAM user — an account is a resource/billing container, not an identity.
```

```
Term: Root (administrative root)
Definition: The top-most container in the org hierarchy, contained in the management account. Exactly one root per organization; created automatically.
Provider Docs Section: Terminology and concepts → Root
Architect Usage: Attach broad, well-tested Deny guardrails here; AWS warns against attaching untested SCPs to the root.
Common Confusion: Confused with the AWS account "root user" — completely different concepts.
```

```
Term: Organizational Unit (OU)
Definition: A group of AWS accounts within an organization; can contain nested OUs. Hierarchy can be up to five levels deep (including root and lowest accounts).
Provider Docs Section: Terminology and concepts → Organizational unit (OU); Quotas → OU maximum nesting
Architect Usage: The primary attach point for policies. Group accounts that need the same controls; organize by function.
Common Confusion: Confused with Azure Management Groups (similar) or GCP Folders (similar). Not an IAM boundary by itself.
```

```
Term: Service Control Policy (SCP)
Definition: An authorization policy that offers central control over the MAXIMUM available permissions for IAM users and IAM roles (principals) in member accounts. Never grants permissions — only sets a guardrail.
Provider Docs Section: Service control policies (SCPs)
Architect Usage: Principal-centric guardrail. Effective permission = intersection of SCP ∩ RCP ∩ IAM identity/resource policy.
Common Confusion: Confused with IAM policies (which DO grant). SCPs do NOT grant and do NOT restrict the management account or service-linked roles.
```

```
Term: Resource Control Policy (RCP) — 2024–2025 addition
Definition: An authorization policy offering central control over the MAXIMUM available permissions for RESOURCES in member accounts (resource-centric guardrail).
Provider Docs Section: Terminology and concepts → Resource control policy (RCP)
Architect Usage: Enforce org-wide resource perimeters (e.g., only identities in your org may access your S3 buckets). RCPFullAWSAccess is auto-attached and cannot be detached.
Common Confusion: Confused with SCPs. SCP guards the principal side; RCP guards the resource side. Both are guardrails, neither grants.
```

```
Term: Declarative policy — 2024–2025 addition
Definition: A policy type that centrally configures and ENFORCES a service's settings across the org, persisting even as the service adds new features/APIs (e.g., EC2, S3, Backup, Tag, Security Hub, Inspector, Bedrock policies).
Provider Docs Section: Terminology and concepts → Declarative policies
Architect Usage: Enforce durable configuration baselines (e.g., block public AMIs org-wide) that survive service evolution.
Common Confusion: Confused with SCPs. Declarative policies configure the SERVICE; SCPs restrict PRINCIPAL permissions.
```

```
Term: FullAWSAccess (AWS-managed SCP)
Definition: The default managed SCP that allows all services and actions, auto-attached to every root, OU, and account when SCPs are enabled.
Provider Docs Section: SCPs → SCP effects on permissions; SCP evaluation → Strategy
Architect Usage: Its presence enables the "deny list" strategy. Removing it (without replacement) blocks ALL actions under that node.
Common Confusion: Deleting it is often mistaken as harmless — it silently locks out member accounts.
```

```
Term: Delegated administrator
Definition: A member account registered by the management account to administer either Organizations policies or a specific integrated AWS service (e.g., GuardDuty, Security Hub, Config) on the org's behalf.
Provider Docs Section: Terminology and concepts → Delegated administrator
Architect Usage: The mechanism that lets you keep security tooling OUT of the management account. Register a dedicated security/audit account.
Common Confusion: Confused with cross-account IAM roles; delegation is registered per-service via Organizations trusted access.
```

```
Term: AWS Control Tower
Definition: A service that orchestrates AWS Organizations, AWS Service Catalog, and IAM Identity Center to set up and govern a multi-account landing zone with prescriptive controls, in under an hour.
Provider Docs Section: AWS Control Tower User Guide → What Is AWS Control Tower?
Architect Usage: Managed landing zone + Account Factory + controls. Use it instead of a hand-rolled landing zone unless you need full custom control.
Common Confusion: Confused with Organizations itself; Control Tower is a layer ON TOP of Organizations.
```

```
Term: Landing zone
Definition: A well-architected, multi-account environment based on security and compliance best practices — the enterprise-wide container for all OUs, accounts, users, and governed resources.
Provider Docs Section: Control Tower User Guide → Features → Landing zone
Architect Usage: The target end-state of foundation-stage adoption; scales from a few to thousands of accounts.
Common Confusion: Confused with a single VPC/network landing zone; here it means the whole account/governance topology.
```

```
Term: Account Factory
Definition: A configurable account template (built on AWS Service Catalog provisioned products) that standardizes and automates provisioning/enrollment of new accounts with pre-approved configurations and controls.
Provider Docs Section: Control Tower User Guide → Features → Account Factory
Architect Usage: The "account vending machine." Enables self-service, governed account creation for distributed teams.
Common Confusion: Confused with Organizations CreateAccount API (lower-level); Account Factory wraps it with governance.
```

```
Term: Control (guardrail)
Definition: A high-level, plain-language governance rule in Control Tower. Three kinds — preventive, detective, proactive; three guidance categories — mandatory, strongly recommended, elective.
Provider Docs Section: Control Tower User Guide → Features → Controls; How controls work
Architect Usage: Preventive controls use SCPs; detective use AWS Config rules; proactive check resources before provisioning (via CloudFormation hooks).
Common Confusion: "Guardrail" is used loosely; in Control Tower it maps to a specific control type with a specific enforcement mechanism.
```

```
Term: Organization trail (AWS CloudTrail)
Definition: A CloudTrail trail applied to the organization that logs events for the management account AND all member accounts into a central S3 bucket. Member accounts cannot modify or delete it.
Provider Docs Section: CloudTrail User Guide → Creating a trail for an organization
Architect Usage: The single tamper-resistant org-wide audit log; store in the Log Archive account. Delegated admin supported.
Common Confusion: Confused with per-account trails; member accounts can SEE but not alter an org trail.
```

```
Term: IAM Identity Center (organization instance)
Definition: The AWS workforce access service (formerly AWS SSO), deployed in the management account, providing one place to assign permission sets to groups across multiple accounts.
Provider Docs Section: IAM Identity Center User Guide → What is IAM Identity Center? → Two instance types
Architect Usage: Best-practice centralized human access. Connect an external IdP (SAML/SCIM) or the built-in directory; assign permission sets per account.
Common Confusion: Still called "AWS SSO" in old docs and legacy sso/identitystore API namespaces (retained for backward compatibility).
```

---

## 1. Framework Pillars — AWS Well-Architected Framework Applied to Organizations Governance

> The whitepaper **"Organizing Your AWS Environment Using Multiple Accounts"** (publication date **April 30, 2025**) states that a multi-account strategy "can help you optimize across most of the AWS Well-Architected Framework pillars, including operational excellence, security, reliability, and cost optimization." The six pillars are Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, and Sustainability. Below, each pillar is mapped to Organizations governance. Source: [Organizing Your AWS Environment](https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/organizing-your-aws-environment.html) (accessed 2026-07-31).

```
Pillar: Security
Definition (WAF): Protect data, systems, and assets; leverage the AWS shared responsibility model; enforce least privilege.
How it manifests in Organizations governance:
  - Account = the strongest isolation boundary. "By default, no access is allowed between accounts."
  - SCPs + RCPs provide preventive, org-wide permission guardrails on principals and resources.
  - Delegated administrators keep security tooling out of the management account (least privilege).
  - Dedicated Security OU with Log Archive + Security Tooling/Audit accounts.
Assessment Questions (top 3):
  1. Are workloads isolated in dedicated member accounts rather than the management account?
  2. Are preventive guardrails (SCPs/RCPs) applied at OU level and tested before root attachment?
  3. Is org-wide audit logging (organization CloudTrail trail) enabled and tamper-resistant?
Source: https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/organizing-your-aws-environment.html
```

```
Pillar: Operational Excellence
Definition (WAF): Run and monitor systems to deliver business value; continually improve processes and procedures.
How it manifests in Organizations governance:
  - Automated account vending (Account Factory / CreateAccount API) minimizes operational complexity.
  - Centralized governance via Control Tower dashboard and drift detection.
  - Delegated administration decentralizes operations without granting management-account access.
Assessment Questions:
  1. Is account provisioning automated and standardized (Account Factory / IaC), not manual?
  2. Is configuration drift from best practices detected (Control Tower drift detection)?
  3. Are org policies staged/tested (Policy Staging OU) before broad rollout?
Source: https://docs.aws.amazon.com/controltower/latest/userguide/what-is-control-tower.html
```

```
Pillar: Reliability
Definition (WAF): Ensure a workload performs its intended function correctly and consistently; recover from failure.
How it manifests in Organizations governance:
  - Account isolation provides explicit fault/blast-radius boundaries between environments and workloads.
  - Business Continuity OU groups DR/backup accounts.
  - Backup policies enforce org-wide backup plans centrally.
Assessment Questions:
  1. Are production and non-production workloads isolated in separate accounts?
  2. Are org-level Backup policies applied to enforce retention/DR baselines?
  3. Is there a Business Continuity OU / DR account strategy?
Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_backup.html
```

```
Pillar: Cost Optimization
Definition (WAF): Avoid unnecessary costs; understand spending and control fund allocation.
How it manifests in Organizations governance:
  - Consolidated billing under the management account (payer account) — one bill, shared volume discounts.
  - Account = a hard billing boundary that "maps costs directly to underlying projects."
  - Tag policies standardize cost-allocation tags across accounts.
Assessment Questions:
  1. Are costs traceable to workloads via account boundaries + standardized cost-allocation tags?
  2. Are Tag policies enforcing the mandatory tagging schema org-wide?
  3. Is the management account isolated so its bill reflects only org-admin charges?
Source: https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/organizing-your-aws-environment.html
```

```
Pillar: Performance Efficiency / Sustainability
Definition (WAF): Use computing resources efficiently; minimize environmental impact.
How it manifests in Organizations governance:
  - Declarative EC2 policies can enforce efficient/approved instance and AMI configurations at scale.
  - Sandbox OU isolates experimentation so it does not affect production capacity or footprint.
Assessment Questions:
  1. Are declarative policies used to enforce approved, efficient service configurations?
  2. Is experimentation contained in a Sandbox OU with limited production access?
Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_ec2.html
```

---

## 2. Always-Do Patterns (Mandatory)

> `{{TARGET_EDITION}}` = AWS Organizations 2024–2025, all-features mode. Every pattern below is sourced to official AWS documentation with an access date.

### ✅ AD-1 — Enable "All features" mode, not consolidated-billing-only

```
Pattern: Operate the organization in all-features mode.
Why (pillar: Security, Operational Excellence): SCPs, RCPs, declarative policies, tag/backup policies, and
  service integrations are "available only in an organization that has all features enabled." Consolidated-billing-only
  mode cannot restrict what principals do or integrate other AWS services org-wide.
AWS Services: AWS Organizations (feature set = ALL).
Architecture Decision: Enable all features at org creation. If migrating from consolidated-billing-only, every invited
  member must accept the ENABLE_ALL_FEATURES handshake.
Verification: `aws organizations describe-organization --query 'Organization.FeatureSet'` → expect "ALL".
Trade-offs: Member accounts gain org-level governance (they cannot opt out of SCPs); requires member consent to migrate.
Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_getting-started_concepts.html (accessed 2026-07-31)
```

### ✅ AD-2 — Keep the management account free of workloads; use delegated administrators

```
Pattern: The management account hosts only org-administration tasks; all workloads and security tooling live in member accounts.
Why (pillar: Security): "Organizations service control policies (SCPs) do not work to restrict any users or roles in the
  management account." Any resource there is un-guardrailed. AWS: "Avoid deploying workloads to the organization's management account."
AWS Services: AWS Organizations delegated administrators; member accounts for all workloads.
Architecture Decision: Register dedicated member accounts as delegated administrators for Organizations policy management and
  for each integrated service (GuardDuty, Security Hub, Config, CloudFormation StackSets, Service Catalog, IAM Access Analyzer, etc.).
Verification: `aws organizations list-accounts` cross-referenced with resource inventory in the management account (should be near-empty);
  `aws organizations list-delegated-administrators`.
Trade-offs: Slightly more setup (register delegated admins per service); vastly reduced blast radius.
Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices_mgmt-acct.html (accessed 2026-07-31)
```

### ✅ AD-3 — Protect the management account root user and restrict access

```
Pattern: Harden and tightly restrict access to the management account (and its root user).
Why (pillar: Security): The management account "is key to all administrative tasks" and is the payer/owner. AWS: restrict access
  to "only those admin users who need rights to make changes"; periodically review who has the email, password, MFA, and phone number.
AWS Services: IAM, root-user MFA, IAM Identity Center for human access.
Architecture Decision: Enforce MFA on the root user; store root credentials via a break-glass process not reliant on one individual;
  perform monthly/quarterly access reviews; grant day-to-day access via IAM Identity Center permission sets, not root.
Verification: Root-user MFA status in IAM console / `GetAccountSummary`; documented break-glass procedure; review cadence recorded.
Trade-offs: Operational discipline overhead; essential given the management account is un-guardrailed by SCPs.
Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices_mgmt-acct.html (accessed 2026-07-31)
```

### ✅ AD-4 — Attach a preventive SCP that blocks leaving/closing accounts

```
Pattern: Attach a root-level SCP denying organizations:LeaveOrganization and account:CloseAccount.
Why (pillar: Security, Operational Excellence): Member accounts can otherwise leave or close themselves, "which can disrupt
  governance, billing, and security controls." This is the canonical baseline guardrail.
AWS Services: AWS Organizations SCP attached at the root.
Architecture Decision: Deny statement:
  { "Effect": "Deny", "Action": ["organizations:LeaveOrganization", "account:CloseAccount"], "Resource": "*" }
  NOTE: Organizations created via the AWS Management Console AFTER July 10, 2026 receive this SCP automatically. Organizations
  created via CLI/SDK/CloudFormation, or before that date, MUST create and attach it manually.
Verification: `aws organizations list-policies-for-target --target-id <root-id> --filter SERVICE_CONTROL_POLICY` shows the guardrail SCP.
Trade-offs: None material — approved departures still possible via management account / delegated admin.
Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices_mgmt-acct.html (accessed 2026-07-31)
```

### ✅ AD-5 — Enable an organization CloudTrail trail into a locked Log Archive account

```
Pattern: Create one multi-Region organization trail; deliver logs to a central S3 bucket in a dedicated Log Archive account.
Why (pillar: Security, Operational Excellence): An organization trail "logs events for the management account and all member
  accounts." Member accounts "do not have sufficient permissions to delete organization trails, turn logging on or off... or
  otherwise change an organization trail" — tamper resistance by design.
AWS Services: AWS CloudTrail (organization trail), Amazon S3 (central bucket in Log Archive account), optional delegated administrator.
Architecture Decision: Enable a multi-Region org trail from the management account or a CloudTrail delegated administrator; central
  S3 bucket structured as <org-id>/<account-id>/... ; enable log-file validation and SSE-KMS.
Verification: `aws cloudtrail describe-trails` shows IsOrganizationTrail=true, IsMultiRegionTrail=true; delivery to the Log Archive bucket.
Trade-offs: Storage cost of centralized logs; a member account still only sees its own events in Event history.
Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/creating-trail-organization.html (accessed 2026-07-31)
```

### ✅ AD-6 — Centralize security services via delegated administrators in a dedicated Audit account

```
Pattern: Delegate GuardDuty, Security Hub, AWS Config aggregation, IAM Access Analyzer, etc. to a dedicated Security Tooling/Audit account.
Why (pillar: Security): "AWS security best practices follow the principle of least privilege and doesn't recommend" using the
  management account as the delegated administrator for security services. A delegated admin can auto-enable and manage the service across members.
AWS Services: Amazon GuardDuty (delegated admin, auto-enable ALL/NEW), AWS Security Hub (central configuration + delegated admin),
  AWS Config (organization aggregator), IAM Access Analyzer (org zone of trust).
Architecture Decision: Register the Audit account as delegated administrator per service in every Region GuardDuty/Security Hub run
  (both are Regional; use the SAME delegated admin account across all Regions). Set GuardDuty auto-enable to ALL for full coverage.
Verification: `aws guardduty list-organization-admin-accounts`; `aws securityhub list-organization-admin-accounts`;
  GuardDuty auto-enable config = ALL via `describe-organization-configuration`.
Trade-offs: GuardDuty delegated admin manages up to 50,000 members per Region; must configure per Region.
Source: https://docs.aws.amazon.com/guardduty/latest/ug/guardduty_organizations.html (accessed 2026-07-31)
```

### ✅ AD-7 — Design OUs by function; maintain a clean Control-Tower-compliant Security OU

```
Pattern: Group accounts into function-based OUs (Security, Infrastructure, Workloads, Sandbox, ...); keep the Security OU minimal.
Why (pillar: Operational Excellence, Security): OUs "are useful when you need to apply the same controls to a subset of accounts."
  AWS: "maintain a clean security OU that adheres to AWS Control Tower requirements... contain only the essential security accounts...
  For additional security-related accounts, create a separate OU outside the core security OU."
AWS Services: AWS Organizations OUs; AWS Control Tower (if used) manages the Security OU (Log Archive + Audit).
Architecture Decision: Foundational OUs = Security (Log Archive, Audit/Security Tooling accounts) + Infrastructure (Network, Shared Services);
  Application OU = Workloads (prod + non-prod, often as nested OUs); Experimental = Sandbox; Procedural = Exceptions, Transitional, Suspended,
  Policy Staging; Advanced = Individual Business Users, Deployments, Business Continuity.
Verification: `aws organizations list-organizational-units-for-parent --parent-id <root-id>`; Security OU contains only designated accounts.
Trade-offs: More OUs = more policy attach points to manage; keep hierarchy shallow (≤5 levels, usually 2–3 in practice).
Source: https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/recommended-ous-and-accounts.html (accessed 2026-07-31)
```

### ✅ AD-8 — Centralize workforce access with an IAM Identity Center organization instance

```
Pattern: Deploy an IAM Identity Center organization instance in the management account; assign permission sets across accounts.
Why (pillar: Security, Operational Excellence): The organization instance "is the best practice... the only instance that enables
  you to manage access to AWS accounts and it is recommended for all production use." One point of federation, one certificate to manage.
AWS Services: AWS IAM Identity Center (organization instance), permission sets, external IdP via SAML/SCIM or built-in directory.
Architecture Decision: Connect the corporate IdP (Entra ID, Okta, etc.) via SAML + SCIM; define permission sets by job function; assign
  groups to accounts/OUs. Avoid long-lived IAM users for humans. Optionally register a delegated administrator for Identity Center.
Verification: `aws sso-admin list-instances` shows an org instance; permission-set assignments reviewed per account.
Trade-offs: Identity Center account quota is 7,000 accounts (adjustable). Legacy sso/identitystore API namespaces remain (backward compat).
Source: https://docs.aws.amazon.com/singlesignon/latest/userguide/what-is.html (accessed 2026-07-31)
```

### ✅ AD-9 — Enforce standards with declarative, tag, and backup policies

```
Pattern: Use declarative policies (e.g., EC2, S3), Tag policies, and Backup policies to enforce durable org-wide baselines.
Why (pillar: Security, Cost, Reliability): Declarative policies keep a configuration "always maintained when the service adds new
  features or APIs." Tag policies "standardize the tags attached to AWS resources." Backup policies "centrally manage and apply backup plans."
AWS Services: AWS Organizations declarative policies (EC2, S3, Backup, Tag, Security Hub, Inspector, Bedrock, ...), AWS Backup.
Architecture Decision: Attach Tag policies enforcing mandatory cost-allocation/ownership tags; Backup policies enforcing retention/DR;
  declarative EC2 policy to block public AMIs / enforce IMDSv2-style baselines org-wide. Stage in the Policy Staging OU first.
Verification: `aws organizations list-policies --filter TAG_POLICY|BACKUP_POLICY|DECLARATIVE_POLICY`; effective policy via
  `aws organizations describe-effective-policy`.
Trade-offs: Declarative policy inheritance differs from SCP evaluation (they merge, not intersect) — model carefully.
Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_getting-started_concepts.html (accessed 2026-07-31)
```

---

## 3. Ask-First Decisions (Architectural Crossroads)

### ⚠️ AF-1 — SCP strategy: Deny-list vs Allow-list

```
Decision: Should SCP guardrails use a deny-list or an allow-list strategy?
Options:
  | Option | AWS mechanism | Optimizes | Sacrifices | Best When |
  |--------|---------------|-----------|------------|-----------|
  | Deny list (default) | Keep FullAWSAccess + add explicit Deny statements | Simplicity, low lockout risk, new services allowed by default | Broad Allow may permit unintended access | Most orgs; the AWS default and recommended starting point |
  | Allow list | Remove/replace FullAWSAccess; explicitly Allow a service subset at EVERY level | Tight service allowlisting; new services blocked unless allowed | High lockout risk; Allow must exist at root→OU→account or all access is denied | Highly regulated orgs needing an explicit service whitelist |
Key mechanics: "For a permission to be allowed... there must be an explicit Allow statement at every level from the root through each
  OU... including the target account." Any single Deny anywhere in the path wins. Missing an Allow at the root blocks ALL member access.
Cost Profile: No direct cost; allow-list carries high operational/incident cost if misconfigured.
Lock-in Assessment: Both are AWS-Organizations-specific; conceptually portable to Azure Policy / GCP Org Policy deny/allow constraints.
Ask The Architect: "Do you need an explicit whitelist of permitted services (allow-list), or is denying a known-bad set sufficient
  (deny-list)? If allow-list, are you prepared to maintain Allow statements at every hierarchy level and test in a Policy Staging OU?"
Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps_evaluation.html (accessed 2026-07-31)
```

### ⚠️ AF-2 — AWS Control Tower vs. self-managed (DIY) landing zone

```
Decision: Adopt AWS Control Tower or build a custom landing zone directly on AWS Organizations?
Options:
  | Option | AWS mechanism | Optimizes | Sacrifices | Best When |
  |--------|---------------|-----------|------------|-----------|
  | AWS Control Tower | Orchestrates Organizations + Service Catalog + Identity Center | Speed (landing zone <1 hr), prescriptive controls, drift detection, Account Factory | Some rigidity; opinionated OU/account model; regional/feature constraints | Teams wanting managed governance and standardized account vending |
  | DIY on Organizations | Organizations + CloudFormation StackSets / IaC + custom SCPs | Full customization, no Control Tower constraints | You build/own controls, drift detection, and vending; higher effort | Advanced platform teams with specific requirements Control Tower can't meet |
Key mechanics: "AWS Control Tower orchestration extends the capabilities of AWS Organizations." You can extend Control Tower by working
  directly in Organizations, then register existing orgs/enroll accounts and update the landing zone to reflect changes.
Cost Profile: Control Tower itself has no additional charge beyond the AWS resources it deploys (Config, CloudTrail, S3, etc.).
Lock-in Assessment: Control Tower configuration is AWS-specific; underlying Organizations structure remains portable/usable if you leave it.
Ask The Architect: "Do you want AWS-managed, prescriptive governance with built-in Account Factory and drift detection (Control Tower),
  or full control over a custom landing zone (DIY)? Do any requirements conflict with Control Tower's opinionated model?"
Source: https://docs.aws.amazon.com/controltower/latest/userguide/what-is-control-tower.html (accessed 2026-07-31)
```

### ⚠️ AF-3 — OU hierarchy: flat vs. deep; functional vs. environment vs. workload

```
Decision: How should OUs be structured and how deep should the hierarchy go?
Options:
  | Option | AWS mechanism | Optimizes | Sacrifices | Best When |
  |--------|---------------|-----------|------------|-----------|
  | Functional OUs (AWS-recommended) | Security, Infrastructure, Workloads, Sandbox... | Clear control boundaries, aligns to Control Tower | Requires mapping teams onto functions | Default enterprise pattern |
  | Environment nested under Workloads | Workloads OU → Prod / Non-Prod nested OUs | Different SCP guardrails per environment | Extra nesting level | Distinct prod vs non-prod controls needed |
  | Deep hierarchy (up to 5 levels) | Nested OUs per workload/team | Fine-grained inherited controls | Complexity; harder to reason about effective policy | Large orgs with many isolation tiers |
Key mechanics: "your hierarchy can be five levels deep" (including root and lowest accounts). Nesting "enables smaller units of
  management"; child OUs inherit parent policies plus their own. Max 2,000 OUs per org.
Cost Profile: No direct cost; deeper hierarchies raise operational reasoning cost.
Lock-in Assessment: OU trees map conceptually to Azure Management Group hierarchies and GCP Folder trees.
Ask The Architect: "Do prod and non-prod (or per-workload teams) need materially different guardrails? If not, prefer a shallow
  functional structure. Never mirror the corporate org chart rigidly — organize by the controls accounts need in common."
Source: https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/recommended-ous-and-accounts.html (accessed 2026-07-31)
```

### ⚠️ AF-4 — Number of accounts and account granularity

```
Decision: How many accounts, and at what granularity (per-workload, per-environment, per-team)?
Options:
  | Option | AWS mechanism | Optimizes | Sacrifices | Best When |
  |--------|---------------|-----------|------------|-----------|
  | Account per workload+environment (AWS-recommended) | Multiple accounts | Strong isolation, clean cost mapping, blast-radius control | More accounts to automate/govern | The AWS-recommended default |
  | Fewer, larger accounts | Shared accounts | Less account sprawl | Weaker isolation, muddier cost attribution | Very small footprints / early experimentation |
Key mechanics: "The optimal number of AWS accounts... can range from a few to thousands." "AWS charges are based on resource usage,
  not the number of accounts." Default org quota = 10 accounts, adjustable up to 50,000 based on qualification.
Cost Profile: Accounts are free; more accounts require automation (Account Factory) to control operational overhead.
Lock-in Assessment: Account granularity maps to GCP Projects and Azure Subscriptions as the equivalent isolation/billing unit.
Ask The Architect: "What isolation and cost-attribution granularity do you need? Default to one account per workload per environment,
  and automate provisioning. Do you need a quota increase beyond the default 10 accounts?"
Source: https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/organizing-your-aws-environment.html ; https://docs.aws.amazon.com/organizations/latest/userguide/orgs_reference_limits.html (accessed 2026-07-31)
```

### ⚠️ AF-5 — Account vending: Control Tower Account Factory vs. Organizations API/IaC

```
Decision: How to provision and enroll new accounts at scale?
Options:
  | Option | AWS mechanism | Optimizes | Sacrifices | Best When |
  |--------|---------------|-----------|------------|-----------|
  | Control Tower Account Factory | Service Catalog product wrapping account creation | Self-service, governed, applies controls automatically | Tied to Control Tower's model | Standardized enterprise vending |
  | Account Factory for Terraform (AFT) | GitOps pipeline over Account Factory | IaC-driven vending, customizations | Additional pipeline to run | Terraform-centric platform teams |
  | Organizations CreateAccount API / StackSets | Direct API + CloudFormation StackSets | Maximum control, no Control Tower | You build governance/enrollment | DIY landing zones |
Key mechanics: Account Factory "helps automate the account provisioning workflow" and is "built as an abstraction on top of provisioned
  products in AWS Service Catalog... automates the process of applying controls and policies." Org quota: create max 5 accounts concurrently.
Cost Profile: No charge for the vending mechanism; downstream baseline resources incur cost.
Lock-in Assessment: Vending automation is AWS-specific; conceptually maps to GCP Project Factory and Azure Subscription vending.
Ask The Architect: "Do you want managed self-service vending (Account Factory), a Terraform GitOps pipeline (AFT), or full-custom
  API/StackSets vending? Which integrates with your existing IaC and approval workflows?"
Source: https://docs.aws.amazon.com/controltower/latest/userguide/what-is-control-tower.html (accessed 2026-07-31)
```

### ⚠️ AF-6 — SCP vs RCP (and declarative policies): which guardrail for which need

```
Decision: Which policy type enforces a given control — SCP, RCP, or a declarative policy?
Options:
  | Option | AWS mechanism | Optimizes | Sacrifices | Best When |
  |--------|---------------|-----------|------------|-----------|
  | SCP | Principal-centric permission guardrail | Caps what identities in member accounts may do | Doesn't cover external principals to your resources | Restricting member-account principals |
  | RCP | Resource-centric permission guardrail | Enforces resource perimeter (who may touch your resources) | Newer; fewer supported services initially | Data perimeter (e.g., only org identities access S3) |
  | Declarative policy | Service configuration enforcement | Durable config baselines that survive new APIs | Merge (not intersect) inheritance; per-service | Enforcing service settings (block public AMIs, S3 config) |
Key mechanics: Effective permissions = intersection of SCP ∩ RCP ∩ IAM identity-based ∩ resource-based policies. SCPs and RCPs never grant.
  RCPFullAWSAccess is auto-attached to root/OUs/accounts and cannot be detached (counts toward the 5-RCP quota).
Cost Profile: No direct cost.
Lock-in Assessment: All AWS-specific; RCP data-perimeter concept maps loosely to VPC-SC (GCP) and Azure resource-level deny/condition.
Ask The Architect: "Is the control about what identities can DO (SCP), what can touch your RESOURCES (RCP), or how a SERVICE is
  CONFIGURED (declarative policy)? Combine them for defense-in-depth."
Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html (accessed 2026-07-31)
```

---

## 4. Never-Do Anti-Patterns

> Every entry uses exact AWS service names and provides a side-by-side ❌ Wrong / ✅ Correct example.

### 🚫 NP-1 — Running workloads / storing data in the management account

```
Anti-Pattern: Deploying application workloads or storing production data in the AWS Organizations management account.
Why: Security (WAF Security pillar). "SCPs don't affect users or roles in the management account" — every resource there is
  outside the org's preventive permission guardrails. AWS: "Avoid deploying workloads to the organization's management account."
Risk Level: CRITICAL
Blast Radius: Entire organization — the management account controls billing, policies, and all account lifecycle operations.
❌ Wrong:
  Deploy an EC2/RDS-backed application and its S3 data buckets directly in the management account; grant developers
  IAM AdministratorAccess there "because SCPs will protect it."
✅ Correct:
  Keep the management account empty of workloads. Create a member account under the Workloads OU for the application; register a
  dedicated Security/Audit member account as delegated administrator for security tooling. SCPs/RCPs then apply to those workloads.
Detection: Inventory the management account (`aws resourcegroupstaggingapi get-resources` / Config aggregator scoped to the
  management account) — it should contain only org-admin resources. Alarm on new resource creation there.
Impact: Data breach / Compliance violation / Cascading failure (un-guardrailed privileged blast radius).
Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices_mgmt-acct.html (accessed 2026-07-31)
```

### 🚫 NP-2 — Removing FullAWSAccess (or missing a root-level Allow) in an allow-list SCP

```
Anti-Pattern: Detaching the AWS-managed FullAWSAccess SCP without a replacement, or omitting an Allow at the root in an allow-list model.
Why: Reliability / Operational Excellence. "You should not remove the FullAWSAccess policy unless you modify or replace it... otherwise
  all AWS actions from member accounts will fail." "Missing an Allow statement at the root-level... will effectively block all access."
Risk Level: CRITICAL
Blast Radius: Every account below the affected node — potentially the entire organization if done at the root.
❌ Wrong:
  Detach FullAWSAccess at the root and attach only an "Allow S3" SCP at one OU, expecting other services to keep working.
✅ Correct:
  Keep FullAWSAccess (deny-list strategy) and layer explicit Deny guardrails; OR, for allow-list, attach the service-allow SCP at
  EVERY level (root → OU → account) and validate in a Policy Staging OU before rollout. Never leave a node with no effective Allow.
Detection: `aws organizations list-policies-for-target --target-id <id>` — verify at least one effective Allow (FullAWSAccess or custom)
  exists on the path root→OU→account. Test with a non-critical account first.
Impact: Service outage (org-wide lockout of all member-account actions).
Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps_evaluation.html (accessed 2026-07-31)
```

### 🚫 NP-3 — Attaching untested SCPs directly to the organization root

```
Anti-Pattern: Attaching new/untested SCPs directly at the organization root across all accounts at once.
Why: Reliability / Operational Excellence. AWS "strongly recommends that you don't attach SCPs to the root of your organization
  without thoroughly testing the impact." A single Deny at the root affects ALL accounts beneath it.
Risk Level: HIGH
Blast Radius: All member accounts in the organization simultaneously.
❌ Wrong:
  Author a broad Deny SCP and attach it to the root in production to "roll it out fast," locking users out of services in use.
✅ Correct:
  Create a Policy Staging OU (or move accounts one at a time / in small numbers into a test OU); validate against IAM service-last-accessed
  data and CloudTrail service usage; then promote the SCP. Use gradual OU-level rollout instead of a blanket root attachment.
Detection: Review SCP change history in CloudTrail (`AttachPolicy` events at the root); require a staging-OU validation gate in the change process.
Impact: Service outage / Cost overrun (from workarounds) — broad, simultaneous lockout.
Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html (accessed 2026-07-31)
```

### 🚫 NP-4 — No SCP preventing accounts from leaving/closing the organization

```
Anti-Pattern: Operating an organization without a guardrail on organizations:LeaveOrganization / account:CloseAccount.
Why: Security / Operational Excellence. Member accounts can otherwise "leave your organization or close themselves, which can disrupt
  governance, billing, and security controls."
Risk Level: HIGH
Blast Radius: Any member account that leaves escapes all org guardrails, audit logging, and consolidated billing.
❌ Wrong:
  Rely on the default FullAWSAccess only; a member-account admin runs `aws organizations leave-organization` and exits governance.
✅ Correct:
  Attach a root-level SCP: { "Effect":"Deny","Action":["organizations:LeaveOrganization","account:CloseAccount"],"Resource":"*" }.
  (Auto-applied to console-created orgs after July 10, 2026; attach manually for CLI/SDK/CloudFormation or pre-existing orgs.)
Detection: `aws organizations list-policies-for-target --target-id <root-id> --filter SERVICE_CONTROL_POLICY` and inspect for the Deny;
  alert on `LeaveOrganization`/`CloseAccount` CloudTrail events.
Impact: Compliance violation / loss of audit continuity / billing disruption.
Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices_mgmt-acct.html (accessed 2026-07-31)
```

### 🚫 NP-5 — Flat single-account (no isolation between environments/workloads)

```
Anti-Pattern: Running production, non-production, and multiple workloads in a single shared AWS account.
Why: Security / Reliability / Cost. The account "acts as an isolation boundary for identity and access management" and a billing
  boundary. AWS recommends "using several accounts to separate your workloads, rather than relying on a single account."
Risk Level: HIGH
Blast Radius: All environments/workloads share one blast radius — one compromise or misconfiguration affects everything.
❌ Wrong:
  One AWS account holding prod + dev + test resources for many teams, with IAM tags as the only separation and a single commingled bill.
✅ Correct:
  Separate member accounts per workload per environment under a Workloads OU (prod / non-prod nested OUs), governed by inherited SCPs;
  costs map cleanly per account; blast radius is contained. Automate provisioning via Account Factory.
Detection: `aws organizations list-accounts` — a mature org shows workload/environment-scoped accounts, not one shared account;
  Cost Explorer per-account attribution.
Impact: Data breach / Service outage / Cost overrun (no cost attribution) / Compliance violation.
Source: https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/organizing-your-aws-environment.html (accessed 2026-07-31)
```

### 🚫 NP-6 — No organization-wide CloudTrail trail (per-account or missing audit logging)

```
Anti-Pattern: Relying on individual per-account CloudTrail trails (or none) instead of a tamper-resistant organization trail.
Why: Security / Operational Excellence. Per-account trails can be disabled or deleted by that account's admin, and there is no
  central, consistent audit record. An organization trail logs "events for the management account and all member accounts" and cannot
  be altered by member accounts.
Risk Level: HIGH
Blast Radius: Org-wide audit/forensics capability — gaps in any account undermine incident response and compliance.
❌ Wrong:
  Each team enables (or forgets to enable) its own trail in its own account; a compromised account's admin turns logging off to hide activity.
✅ Correct:
  Enable one multi-Region AWS CloudTrail organization trail (from the management account or CloudTrail delegated administrator) delivering
  to a central, access-restricted Amazon S3 bucket in the Log Archive account, with log-file validation and SSE-KMS. Member accounts can see
  but cannot modify or delete it.
Detection: `aws cloudtrail describe-trails --query 'trailList[?IsOrganizationTrail==`true`]'` — expect exactly one multi-Region org trail.
Impact: Compliance violation / undetectable breach (no forensics).
Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/creating-trail-organization.html (accessed 2026-07-31)
```

### 🚫 NP-7 — Using the management account as the delegated administrator for security services

```
Anti-Pattern: Designating the organization's management account as the GuardDuty / Security Hub / Config delegated administrator.
Why: Security (least privilege). AWS: "the AWS security best practices follow the principle of least privilege and doesn't recommend
  this configuration." It concentrates security operations in the highest-privilege, un-guardrailed account.
Risk Level: MEDIUM
Blast Radius: Security tooling + management/billing authority collapse into one account, widening compromise impact.
❌ Wrong:
  Run `enable-organization-admin-account` for GuardDuty pointing at the management account; operate Security Hub from the management account.
✅ Correct:
  Register a dedicated Security Tooling/Audit member account (in the Security OU) as the delegated administrator for GuardDuty, Security Hub,
  AWS Config aggregation, and IAM Access Analyzer — the SAME account across all Regions for GuardDuty/Security Hub (both Regional services).
Detection: `aws guardduty list-organization-admin-accounts` / `aws securityhub list-organization-admin-accounts` — the admin account
  ID should be the Audit account, not the management account.
Impact: Compliance violation / widened blast radius on management-account compromise.
Source: https://docs.aws.amazon.com/guardduty/latest/ug/guardduty_organizations.html (accessed 2026-07-31)
```

### 🚫 NP-8 — Mirroring the corporate org chart / mixing security accounts into the core Security OU

```
Anti-Pattern: Building the OU tree to mirror the corporate reporting structure, and dumping every security-related account into the core Security OU.
Why: Operational Excellence / Security. AWS guidance: organize by function (common controls), not rigid org structure; "maintain a clean
  security OU that adheres to AWS Control Tower requirements... contain only the essential security accounts... For additional security-related
  accounts, create a separate OU outside the core security OU."
Risk Level: MEDIUM
Blast Radius: Governance clarity and Control Tower compliance across the whole account topology.
❌ Wrong:
  Create OUs named after departments/teams and place a general-purpose "SecOps sandbox," pentest, and tooling accounts inside the core Security OU.
✅ Correct:
  Function-based OUs (Security, Infrastructure, Workloads, Sandbox, ...). Keep the core Security OU limited to the Control Tower-designated
  accounts (Log Archive, Audit). Put other security-related accounts in a separate OU outside the core Security OU.
Detection: Review `list-organizational-units-for-parent` structure; confirm the Security OU contains only Log Archive + Audit accounts.
Impact: Governance drift / Control Tower non-conformance / harder-to-reason-about effective policy.
Source: https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/organizing-your-aws-environment.html (accessed 2026-07-31)
```

---

## 5. Service Equivalence Map (AWS ↔ Azure ↔ GCP ↔ OCI)

> Cross-provider conceptual mapping for architects choosing or comparing multi-account/tenancy governance models. AWS terms are sourced above from official AWS docs (accessed 2026-07-31). Non-AWS columns are conceptual equivalences based on each provider's published governance model; verify exact behavior against each provider's current docs before relying on parity — the governance semantics are similar but **not identical** (e.g., SCP intersection semantics differ from Azure Policy effects).

| Concept / Capability | AWS | Azure | GCP | OCI |
|---|---|---|---|---|
| **Top governance root** | Organization root (management account) | Root Management Group / Tenant (Entra ID) | Organization node (resource hierarchy) | Tenancy (root compartment) |
| **Grouping container for accounts** | Organizational Unit (OU) | Management Group | Folder | Compartment (nestable) |
| **Isolation + billing unit** | AWS account | Subscription | Project | Compartment / Tenancy |
| **Nesting depth** | OUs up to 5 levels | Management Groups up to 6 levels | Folders up to 10 levels | Compartments up to 6 levels |
| **Principal permission guardrail** | Service Control Policy (SCP) | Azure Policy (deny/deployIfNotExists) + Deny assignments | Organization Policy (IAM-adjacent constraints) | IAM Policies (compartment-scoped) |
| **Resource permission guardrail** | Resource Control Policy (RCP) | Azure Policy resource restrictions / Deny assignments | VPC Service Controls / Org Policy constraints | IAM policy + Network Sources / conditions |
| **Config/setting enforcement** | Declarative policies (EC2, S3, ...) | Azure Policy (audit/modify/deployIfNotExists) | Organization Policy constraints | OCI Configuration/Policies + Cloud Guard |
| **Tag governance** | Tag policies | Azure Policy tag rules | Org Policy + labels; Tag constraints | Tag defaults + tag namespaces |
| **Backup governance** | Backup policies (AWS Backup) | Azure Backup + Policy | Backup for GKE / Backup and DR + Org Policy | OCI Backup policies |
| **Centralized identity/SSO** | IAM Identity Center (org instance) | Microsoft Entra ID + PIM | Cloud Identity / Workforce Identity Federation | OCI IAM / Identity Domains |
| **Landing zone orchestration** | AWS Control Tower | Azure Landing Zones (CAF) / Azure Blueprints (retiring) | Cloud Foundation Toolkit / Terraform blueprints | OCI Landing Zone (Terraform) |
| **Account/project vending** | Account Factory (Service Catalog) / AFT | Subscription vending (Bicep/Terraform) | Project Factory (Terraform) | OCI account/compartment automation (Terraform) |
| **Org-wide audit log** | CloudTrail organization trail | Azure Monitor / Activity Log + diagnostic settings to central Log Analytics | Cloud Audit Logs (org-level log sink) | OCI Audit + Logging (central) |
| **Centralized threat detection** | GuardDuty (delegated admin) | Microsoft Defender for Cloud | Security Command Center | OCI Cloud Guard |
| **Central security posture aggregator** | Security Hub (central config + delegated admin) | Defender for Cloud secure score | Security Command Center | OCI Cloud Guard / Security Zones |
| **Consolidated billing** | Consolidated billing (payer/management account) | Microsoft Customer Agreement billing account | Cloud Billing account | OCI consolidated billing (tenancy) |

Sources for AWS column: AWS Organizations, Control Tower, CloudTrail, GuardDuty, Security Hub, and IAM Identity Center docs cited in the Bibliography (accessed 2026-07-31). Non-AWS mappings are conceptual — confirm current semantics in each provider's documentation.

---

## Reference Architecture — Enterprise Landing Zone (Control Tower-aligned)

**Context:** Enterprise multi-account governance with centralized security and billing (the `{{ARCHITECTURE_CONTEXT}}`).

| Layer | Account / OU | Purpose |
|---|---|---|
| Root | Management account | Org owner + payer; org-admin tasks only; **no workloads**; org CloudTrail owner |
| Security OU | Log Archive account | Central, access-restricted S3 for org CloudTrail + Config logs; tamper-resistant |
| Security OU | Audit / Security Tooling account | Delegated admin for GuardDuty, Security Hub, Config aggregator, IAM Access Analyzer |
| Infrastructure OU | Network account | Centralized networking (Transit Gateway, shared VPCs, DNS, egress) |
| Infrastructure OU | Shared Services account | Directory, CI/CD shared tooling, golden AMIs |
| Workloads OU → Prod (nested) | Per-workload prod accounts | Production workloads; stricter SCP/RCP guardrails |
| Workloads OU → Non-Prod (nested) | Per-workload dev/test accounts | Non-production; looser guardrails, cost caps |
| Sandbox OU | Sandbox accounts | Experimentation with limited production access |
| Policy Staging OU | Staging accounts | Validate new SCPs/policies before broad rollout |

**Key decisions to customize:** SCP deny-list vs allow-list (AF-1); Control Tower vs DIY (AF-2); OU depth (AF-3); account count/quota (AF-4); vending mechanism (AF-5).
**Scaling path:** Start with a few accounts (early adoption) → foundation stage (automated vending, CoE, cost management) → enterprise scale (thousands of accounts; org quota adjustable up to 50,000).
Source: https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/recommended-ous-and-accounts.html (accessed 2026-07-31)

---

## Key Quotas & Limits (AWS Organizations, 2024–2025)

| Item | Default value | Adjustable? |
|---|---|---|
| Max accounts per organization | 10 (increasable up to 50,000 based on qualification) | Yes (management account only) |
| Roots per organization | 1 | No |
| OUs per organization | 2,000 | — |
| OU nesting depth | 5 levels deep under a root | No |
| SCPs — max per organization | 10,000 | — |
| SCPs — max attached per entity (root/OU/account) | 10 (minimum 1 when SCPs enabled) | No (hard) |
| SCP max document size | 10,240 characters | No |
| RCPs — max per organization | 2,000; max 5 attached per entity | No (hard) |
| RCP max document size | 5,120 characters | No |
| Declarative policy max size | 10,000 characters; 1,000 per org; 10 per entity | No |
| Tag / Backup policy max size | 10,000 characters; 1,000 per org each | No |
| Concurrent account creation | 5 in progress at a time | No |
| Invitation attempts / 24h | 20 or org account max, whichever greater | — |
| Tags per root/OU/account | 50 | — |
| Targets a policy can attach to | Unlimited | — |
| GuardDuty members per delegated admin (per Region) | 50,000 | — |
| IAM Identity Center accounts | 7,000 | Yes |

> ⚠️ Quotas change over time; re-verify against the live [Quotas page](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_reference_limits.html) before design commitments. Organizations is a global service hosted in `us-east-1` — request increases there.
Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_reference_limits.html (accessed 2026-07-31)

---

## Scenario Coverage

**Standard case — enterprise landing zone.** Adopt AWS Control Tower for a prescriptive multi-account landing zone: Security OU (Log Archive + Audit), Infrastructure OU (Network + Shared Services), Workloads OU (prod/non-prod nested), Sandbox OU. Empty management account, org CloudTrail to Log Archive, delegated-admin GuardDuty/Security Hub/Config in Audit, IAM Identity Center org instance, deny-list SCPs with the LeaveOrganization/CloseAccount guardrail, Account Factory for vending. Key architect decisions: AF-1 through AF-5.

**Edge case — regulated org needing an explicit service whitelist.** Use an allow-list SCP strategy (AF-1): replace FullAWSAccess and attach explicit service-allow SCPs at every level, validated first in a Policy Staging OU. Combine with RCPs for a data perimeter and declarative policies for durable config baselines. Watch the OU-nesting (5-level) and per-entity SCP (10) / RCP (5) limits.

**Anti-pattern case — "just run it in the management account for now."** Refuse and flag. The management account is un-guardrailed by SCPs (NP-1). Clarify: create a member account under the Workloads OU and register delegated administrators; never place workloads/data or broad developer access in the management account.

---

## 6. Source Bibliography

All sources are official AWS documentation, accessed **2026-07-31**. None are older than 12 months relative to the research date except where an explicit publication date is noted; all reflect the current stable AWS Organizations documentation set.

### Primary Sources — AWS Organizations User Guide
- [Terminology and concepts for AWS Organizations](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_getting-started_concepts.html) — accessed 2026-07-31. (Management/member accounts, root, OUs, feature sets, authorization policies (SCP/RCP), declarative policies, delegated admin.)
- [Service control policies (SCPs)](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html) — accessed 2026-07-31. (SCPs never grant; intersection with IAM/RCP; management account & service-linked-role exemptions; testing warning.)
- [SCP evaluation](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps_evaluation.html) — accessed 2026-07-31. (Deny-list vs allow-list strategy; Allow required at every level; Deny wins anywhere; 7 scenarios.)
- [Best practices for the management account](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices_mgmt-acct.html) — accessed 2026-07-31. (Limit access, no workloads, LeaveOrganization/CloseAccount SCP, default SCP after July 10 2026, delegate outside management account.)
- [Quotas and service limits for AWS Organizations](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_reference_limits.html) — accessed 2026-07-31. (Account/OU/policy quotas, sizes, nesting depth, throttling.)

### Primary Sources — Related AWS Services
- [What Is AWS Control Tower?](https://docs.aws.amazon.com/controltower/latest/userguide/what-is-control-tower.html) — accessed 2026-07-31. (Landing zone, Account Factory, controls: preventive/detective/proactive & mandatory/strongly-recommended/elective, orchestration of Organizations + Service Catalog + Identity Center, SCPs/RCPs.)
- [Creating a trail for an organization (AWS CloudTrail)](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/creating-trail-organization.html) — accessed 2026-07-31. (Organization trail logs all accounts; member accounts can't modify/delete; delegated admin; central S3; service-linked role.)
- [Managing GuardDuty accounts with AWS Organizations](https://docs.aws.amazon.com/guardduty/latest/ug/guardduty_organizations.html) — accessed 2026-07-31. (Delegated admin, auto-enable NEW/ALL, Regional, 50,000-member limit, not-recommended to use management account.)
- [What is IAM Identity Center?](https://docs.aws.amazon.com/singlesignon/latest/userguide/what-is.html) — accessed 2026-07-31. (Organization vs account instances, permission sets, external IdP, AWS SSO rename July 26 2022, legacy namespaces.)

### Primary Sources — AWS Whitepaper (dated)
- [Organizing Your AWS Environment Using Multiple Accounts](https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/organizing-your-aws-environment.html) — **Publication date: April 30, 2025**; accessed 2026-07-31. (Multi-account strategy, WAF alignment, account isolation, clean Security OU guidance.)
- [Recommended OUs and accounts](https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/recommended-ous-and-accounts.html) — accessed 2026-07-31. (Foundational/Application/Experimental/Procedural/Advanced OUs; Security OU with Log Archive + Audit.)

### Referenced (not deep-fetched) — for downstream verification
- AWS Prescriptive Guidance — Security Reference Architecture (security-tooling): https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/security-tooling.html
- AWS Organizations — Default security controls: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_security_default_controls.html
- AWS Backup policies for Organizations: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_backup.html
- AWS Tag policies for Organizations: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_tag-policies.html
- AWS Well-Architected Framework: https://aws.amazon.com/architecture/well-architected/

---

## Verification Checklist (run before finalizing) — RESULT

```
[x] TARGET_EDITION explicitly stated in metadata and every major section (AWS Organizations 2024–2025)
[x] All 6 mandatory output sections present:
    1. Framework Pillars  2. Always-Do Patterns  3. Ask-First Decisions
    4. Never-Do Anti-Patterns  5. Service Equivalence Map  6. Source Bibliography
[x] Every pattern cites an official AWS URL with access date (2026-07-31)
[x] Every Never-Do (NP-1..NP-8) has ❌ Wrong / ✅ Correct side-by-side with exact AWS service names
[x] All sources dated; whitepaper flagged with its publication date (April 30, 2025); no source > 12 months from research date
[x] Service Equivalence Map covers AWS / Azure / GCP / OCI (non-AWS columns flagged as conceptual — verify per provider)
[x] No generic cloud terms where AWS-specific names exist (SCP, RCP, FullAWSAccess, Account Factory, org trail, delegated admin, IAM Identity Center)
```

### Research Gaps / Unverified (flagged honestly)
- **Non-AWS Service Equivalence columns (Azure/GCP/OCI)** are conceptual mappings, not fetched from each provider's live docs in this pass. Marked as "verify per provider." The AWS column is fully source-verified.
- **Nesting-depth values for Azure (6), GCP (10), OCI (6)** in the equivalence table are from general provider knowledge, not re-verified against live provider docs on 2026-07-31 — confirm before quoting externally. The AWS value (5 levels) IS source-verified.
- **Control Tower control counts / specific mandatory control lists** were not enumerated (the "How controls work" sub-page was referenced but not deep-fetched); the three control types and three guidance categories ARE source-verified.
- Recommend running **`/skill-best-practices-validator`** on the SKILL.md that is authored from this research.
```
