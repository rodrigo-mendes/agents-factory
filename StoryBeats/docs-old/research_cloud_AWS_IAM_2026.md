---
Full_Name: "AWS Identity and Access Management (IAM)"
Cloud_Provider: "AWS"
Architecture_Domain: "IAM / Security Architecture"
Target_Edition: "AWS IAM Best Practices — current (July 2026) + Well-Architected Security Pillar (SEC02 / SEC03)"
Architecture_Context: "General-purpose production AWS workloads on a multi-account AWS Organizations foundation (not specialized to one workload — see Agent Operation Notes for the Ask-First on ARCHITECTURE_CONTEXT and compliance scope)"
Official_Source_URL: "https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-07-31"
Currency_Threshold: "2027-07-31 (review by this date — IAM guidance evolves; AWS IAM docs are living/latest)"
---

# AWS IAM — Cloud Architecture Research Knowledge Base

> **Version Absolutism note.** AWS IAM is documented as a *living* (`latest`) service — there is no
> semantic version number. This research pins to the **AWS IAM Security Best Practices page as of
> 2026-07-31** and the **AWS Well-Architected Framework Security Pillar** identity-management (SEC02)
> and permissions-management (SEC03) best practices. Any guidance predating the 2024 "temporary
> credentials first / centralized root access" direction is treated as outdated and is flagged where
> it appears. All sources accessed **2026-07-31**.

---

## Executive Summary

AWS Identity and Access Management (IAM) is the control plane that governs *who* (human and machine
principals) can perform *which actions* on *which resources* under *which conditions* across an AWS
environment. In current AWS guidance, IAM is no longer centered on long-lived IAM users with access
keys. The official best-practices direction is **temporary credentials by default**: human users
federate through an identity provider via **AWS IAM Identity Center** (formerly AWS SSO), and
workloads assume **IAM roles** rather than holding static keys. IAM users with long-term access keys
are now an explicitly narrow exception list (WordPress-style plugins, third-party clients that cannot
use IAM Identity Center, AWS CodeCommit, Amazon Keyspaces).

The most consequential recent shifts captured in `{{TARGET_EDITION}}` (2024–2026): (1) **Centralized
root access management** through AWS Organizations — you can now *remove* root credentials from
member accounts entirely and perform the few root-only tasks via a privileged `AssumeRoot` session
from the management account; (2) **Resource control policies (RCPs)** joined service control policies
(SCPs) as an organization-wide guardrail — SCPs bound what *principals* can do, RCPs bound what
*resources* can grant; (3) **IAM Access Analyzer** matured into four analyzer types (external access,
internal access, unused access, plus policy validation / custom policy checks / policy generation),
making least-privilege a continuous, automated practice rather than a one-time review; and (4)
**phishing-resistant MFA** (passkeys, FIDO2 security keys) is now the recommended default, with MFA
mandatory for all root users within a 35-day grace period.

For a general production workload on a multi-account AWS Organizations foundation, the three most
critical IAM guardrails are: **(1)** lock away / centrally remove root credentials and require MFA on
every remaining root user; **(2)** eliminate long-term credentials — federate humans through IAM
Identity Center and give workloads IAM roles delivered by the compute service (EC2 instance profiles,
Lambda execution roles, EKS Pod Identity / IRSA, IAM Roles Anywhere for on-prem); and **(3)** enforce
organization-wide guardrails with SCPs + RCPs while continuously driving toward least privilege using
IAM Access Analyzer unused-access findings and policy generation. These map directly to Security
Pillar best practices SEC02-BP01/BP02/BP04 and SEC03-BP02/BP04/BP05.

---

## Framework Pillars

IAM is primarily a **Security** pillar concern, but touches Operational Excellence (credential
lifecycle automation) and Cost (Access Analyzer analyzer pricing). The Well-Architected Security
Pillar decomposes identity into two question areas, each with numbered best practices (BPs).

```
Pillar: Security — Identity and Access Management (SEC 2 & SEC 3)
Definition: "Grant your users and applications access to resources in your AWS accounts... ensure
  that the right people have access to the right resources under the right conditions." (Well-
  Architected Security Pillar, Identity and Access Management)
Key Design Principles:
  - Rely on a centralized identity provider; use temporary, least-privilege credentials.
  - Enforce strong sign-in (phishing-resistant MFA); store secrets securely; audit + rotate.
  - Grant least privilege, reduce permissions continuously, and bound with guardrails.
Applies To general production workloads:
  SEC02 (identity) governs how humans and workloads authenticate; SEC03 (permissions) governs what
  they are authorized to do once authenticated.
Assessment Questions (SEC02 / SEC03 best-practice list):
  SEC02-BP01 Use strong sign-in mechanisms
  SEC02-BP02 Use temporary credentials
  SEC02-BP03 Store and use secrets securely
  SEC02-BP04 Rely on a centralized identity provider
  SEC02-BP05 Audit and rotate credentials periodically
  SEC02-BP06 Employ user groups and attributes
  SEC03-BP01 Define access requirements
  SEC03-BP02 Grant least privilege access
  SEC03-BP03 Establish emergency access process
  SEC03-BP04 Reduce permissions continuously
  SEC03-BP05 Define permission guardrails for your organization
  SEC03-BP06 Manage access based on lifecycle
  SEC03-BP07 Analyze public and cross-account access
  SEC03-BP08 Share resources securely within your organization
  SEC03-BP09 Share resources securely with a third party
Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/identity-management.html
        https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/permissions-management.html
        (accessed 2026-07-31)
```

---

## Cloud Architecture Glossary

```
Term: Principal
Definition: A person or application authenticated as an IAM user, IAM role session, or federated
  identity that makes a request to AWS.
Provider Docs Section: IAM User Guide — JSON policy elements: Principal
Architect Usage: Every authorization decision resolves to a principal; SCPs/RCPs/permissions
  boundaries all constrain principals or resources relative to a principal.
Common Confusion: Confused with "identity" — a role is an identity but each role *session* is a
  distinct principal with temporary credentials.
```
```
Term: IAM Role
Definition: An IAM identity with permission policies but no long-term credentials; it is assumed to
  obtain temporary security credentials via AWS STS.
Provider Docs Section: IAM User Guide — Roles terms and concepts
Architect Usage: The default identity for workloads and (via federation) humans. Delivered
  automatically to EC2/Lambda/ECS/EKS compute.
Common Confusion: Confused with IAM user — users carry long-term passwords/access keys; roles do not.
```
```
Term: IAM Identity Center (formerly AWS SSO)
Definition: AWS service for centralized workforce access and permission-set assignment across many
  accounts, backed by its own identity store or an external IdP.
Provider Docs Section: AWS IAM Identity Center User Guide — What is IAM Identity Center
Architect Usage: The recommended front door for all human access in a multi-account org; replaces
  per-account IAM users.
Common Confusion: Confused with IAM itself — Identity Center provisions federated access *into* IAM
  roles; it does not replace IAM's authorization engine.
```
```
Term: AWS STS (Security Token Service)
Definition: Service that issues short-lived credentials via AssumeRole, AssumeRoleWithSAML,
  AssumeRoleWithWebIdentity, and (for root) AssumeRoot.
Provider Docs Section: AWS STS API Reference
Architect Usage: The mechanism behind every temporary-credential pattern; choose the AssumeRole*
  variant by the trust source (SAML vs OIDC/JWT vs certificate).
Common Confusion: Confused with IAM Identity Center — STS is the low-level token API; Identity Center
  is a higher-level workforce layer that ultimately calls STS.
```
```
Term: Service Control Policy (SCP)
Definition: An AWS Organizations policy that sets the maximum permissions for principals in member
  accounts/OUs. Does not grant permissions.
Provider Docs Section: AWS Organizations User Guide — SCPs
Architect Usage: Preventive guardrail — e.g., deny disabling CloudTrail, deny leaving Organizations,
  restrict Regions. Applied at org/OU/account scope.
Common Confusion: Confused with IAM policies (which grant) — SCPs only filter/limit and never grant.
```
```
Term: Resource Control Policy (RCP)
Definition: An AWS Organizations policy that sets the maximum access that resources across the org
  can grant (e.g., bounding resource-based policies). Does not grant permissions.
Provider Docs Section: AWS Organizations User Guide — RCPs
Architect Usage: Org-wide data-perimeter guardrail — e.g., enforce that S3 buckets cannot be shared
  outside the organization. Complements SCPs (principal-side) on the resource side.
Common Confusion: Confused with SCP — SCP bounds principals, RCP bounds resources.
```
```
Term: Permissions Boundary
Definition: A managed policy attached to an IAM user/role that caps the maximum permissions an
  identity-based policy can grant to that entity. Does not grant permissions.
Provider Docs Section: IAM User Guide — Permissions boundaries for IAM entities
Architect Usage: Delegation control — let developers create roles while guaranteeing they cannot
  escalate beyond the boundary.
Common Confusion: Confused with SCP — boundaries act *within* an account on a specific entity; SCPs
  act across accounts on all principals.
```
```
Term: Session Policy
Definition: An inline policy passed at AssumeRole/federation time that further limits the resulting
  session's permissions. Does not grant permissions.
Provider Docs Section: IAM User Guide — Session policies
Architect Usage: Narrow a broker/broker-issued session for a single task without editing the role.
Common Confusion: Confused with the role's own policy — session policies only intersect (reduce).
```
```
Term: ABAC (Attribute-Based Access Control)
Definition: Authorization based on matching tags (attributes) on principals and resources, evaluated
  via policy condition keys such as aws:PrincipalTag / aws:ResourceTag.
Provider Docs Section: IAM User Guide — ABAC for AWS
Architect Usage: Scales permissions without editing policies as resources grow; ideal for
  multi-team/multi-project isolation via a project tag.
Common Confusion: Confused with RBAC — RBAC uses many role/policy definitions; ABAC uses one policy
  plus tags.
```
```
Term: IAM Access Analyzer
Definition: IAM feature providing external-access, internal-access, and unused-access analyzers plus
  policy validation, custom policy checks, and policy generation.
Provider Docs Section: IAM User Guide — Using IAM Access Analyzer
Architect Usage: The engine for continuous least-privilege: find external sharing, prune unused
  roles/keys, and validate policies in CI/CD.
Common Confusion: Confused with GuardDuty (threat detection) — Access Analyzer reasons about policy
  intent, not runtime threats.
```
```
Term: Permissions Boundary vs Guardrail
Definition: Guardrail is the umbrella term for preventive controls (SCP, RCP, permissions boundary,
  session policy) that bound but never grant permissions.
Provider Docs Section: Security Reference Architecture — Organizations, accounts, and guardrails
Architect Usage: Effective permissions = intersection of identity/resource policies AND every
  applicable guardrail.
Common Confusion: Assuming a guardrail grants access — no guardrail grants; you still need an
  allow in an identity- or resource-based policy.
```
```
Term: AssumeRoot
Definition: An STS action that issues a short-lived privileged session to perform root-only tasks in
  a member account from the Organizations management account / delegated admin.
Provider Docs Section: AWS STS API Reference — AssumeRoot; IAM User Guide — Centrally manage root access
Architect Usage: Enables removing standing root credentials from member accounts while still
  performing rare root-only tasks.
Common Confusion: Confused with AssumeRole — AssumeRoot is scoped to a short list of privileged root
  tasks, not general role assumption.
```
```
Term: Identity-based vs Resource-based policy
Definition: Identity-based policies attach to users/groups/roles; resource-based policies attach to
  a resource (e.g., S3 bucket policy, KMS key policy) and name a principal.
Provider Docs Section: IAM User Guide — Identity-based vs resource-based policies
Architect Usage: Cross-account access requires an allow on both sides (identity in account A,
  resource policy in account B) unless within trusted org scope.
Common Confusion: Assuming an identity policy alone grants cross-account access — the resource policy
  must also allow it.
```
```
Term: Instance Profile / Execution Role
Definition: The mechanism by which AWS delivers a role's temporary credentials to compute — instance
  profile (EC2), execution role (Lambda), task role (ECS), Pod Identity / IRSA (EKS).
Provider Docs Section: IAM User Guide — best practices, "Require workloads to use temporary
  credentials with IAM roles"
Architect Usage: The canonical alternative to embedding access keys in a workload.
Common Confusion: Confused with hardcoded credentials — the SDK discovers these automatically; no
  keys are distributed.
```

---

## Architecture Guardrails

### ✅ Mandatory Patterns

The following are non-negotiable for production AWS workloads. Each maps to an official IAM
best-practice recommendation and/or a Security Pillar BP.

**Federate human users through a centralized identity provider (temporary credentials)**
- Pillar Alignment: Security — SEC02-BP04 (centralized IdP), SEC02-BP02 (temporary credentials)
- Why: "Require your human users to use temporary credentials when accessing AWS... we recommend
  that you use AWS IAM Identity Center to manage access to your accounts and permissions within those
  accounts." (IAM best practices — federation)
- AWS Services: AWS IAM Identity Center, AWS STS, external IdP (Okta/Entra ID/etc.) via SAML/OIDC
- Architecture Decision: Connect IAM Identity Center to your IdP (or use its built-in store); model
  access as permission sets mapped to groups; users assume roles for short sessions — no per-account
  IAM users.
- Verification: Confirm zero human IAM users with console passwords via IAM credential report;
  `aws iam generate-credential-report` then `aws iam get-credential-report`.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#bp-users-federation-idp
  (accessed 2026-07-31)

**Deliver IAM roles (not access keys) to workloads**
- Pillar Alignment: Security — SEC02-BP02
- Why: "there is no need to distribute long lived credentials for an IAM user to your workloads
  running on AWS." Compute services deliver role credentials automatically.
- AWS Services: EC2 instance profiles, Lambda execution roles, ECS task roles, EKS Pod Identity /
  IRSA; for outside-AWS workloads: IAM Roles Anywhere, `AssumeRoleWithSAML`, `AssumeRoleWithWebIdentity`
- Architecture Decision: Attach a least-privilege role to each workload; on-prem/CI use IAM Roles
  Anywhere (X.509 PKI) or OIDC federation instead of static keys.
- Verification: Inspect running compute for embedded keys; `aws iam list-access-keys` should show no
  keys for workload service accounts; scan repos with git-secrets / IAM Access Analyzer.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#bp-workloads-use-roles
  (accessed 2026-07-31)

**Require MFA — phishing-resistant where possible**
- Pillar Alignment: Security — SEC02-BP01 (strong sign-in)
- Why: "for scenarios in which you need an IAM user or root user... require MFA... We recommend that
  you use phishing-resistant MFA such as passkeys and security keys wherever possible."
- AWS Services: FIDO2 security keys / passkeys, hardware TOTP, virtual MFA; IAM Identity Center MFA
- Architecture Decision: Enforce MFA at the IdP / Identity Center for all human sign-in; register MFA
  for every root user (mandatory within 35 days of first console sign-in).
- Verification: Security Hub CSPM control IAM.4 (root MFA); AWS Config `root-account-mfa-enabled`;
  Trusted Advisor "MFA on Root Account".
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#enable-mfa-for-privileged-users
  (accessed 2026-07-31)

**Protect / centrally remove root user credentials**
- Pillar Alignment: Security — SEC02-BP01
- Why: "We strongly recommend you don't access the AWS account root user unless you have a task that
  requires root user credentials." For Organizations: "we recommend removing root user credentials
  from member accounts to help prevent unauthorized use."
- AWS Services: AWS Organizations (centralized root access management), AWS STS AssumeRoot, IAM
- Architecture Decision: Enable centralized root access; remove root password/keys/MFA from member
  accounts; perform rare root-only tasks via AssumeRoot from the management/delegated-admin account.
  Never create root access keys. Use a group email for the root address.
- Verification: AWS Config `iam-root-access-key-check`; Security Hub IAM controls; CloudTrail alert
  on `AssumeRoot` / root sign-in events via EventBridge → SNS or GuardDuty.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/root-user-best-practices.html
  (accessed 2026-07-31)

**Apply least-privilege permissions and reduce continuously**
- Pillar Alignment: Security — SEC03-BP02 (grant least privilege), SEC03-BP04 (reduce continuously)
- Why: "grant only the permissions required to perform a task... As your use case matures, you can
  work to reduce the permissions." Start from AWS managed policies, then move to tighter
  customer-managed policies.
- AWS Services: Customer-managed IAM policies, IAM Access Analyzer policy generation, IAM last
  accessed information, IAM Access Analyzer unused access analyzer
- Architecture Decision: Prefer customer-managed policies scoped to specific actions/resources/
  conditions; generate policies from CloudTrail activity; prune unused access on a schedule.
- Verification: IAM Access Analyzer unused-access findings; `aws accessanalyzer list-findings`;
  last-accessed report via `aws iam get-service-last-accessed-details`.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#grant-least-privilege
        https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#bp-gen-least-privilege-policies
  (accessed 2026-07-31)

**Establish organization-wide guardrails (SCPs + RCPs)**
- Pillar Alignment: Security — SEC03-BP05 (permission guardrails)
- Why: "use AWS Organizations service control policies (SCPs) to establish permissions guardrails to
  control access for all principals... use resource control policies (RCPs) to establish permissions
  guardrails to control access for AWS resources." Note: "No permissions are granted by SCPs and RCPs."
- AWS Services: AWS Organizations (SCPs, RCPs), applied at org/OU/account level
- Architecture Decision: Baseline SCPs (deny root actions in members, deny CloudTrail/Config
  tampering, restrict Regions, deny leaving org) + RCPs enforcing a data perimeter; still attach
  identity/resource policies to actually grant access.
- Verification: `aws organizations list-policies --filter SERVICE_CONTROL_POLICY` and
  `RESOURCE_CONTROL_POLICY`; validate effective permissions with the IAM policy simulator.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#bp-permissions-guardrails
  (accessed 2026-07-31)

**Validate every policy and verify external/cross-account access**
- Pillar Alignment: Security — SEC03-BP07 (analyze public/cross-account access)
- Why: IAM Access Analyzer "provides more than 100 policy checks" and "monitors supported resource
  types continuously and generates a finding for resources that allow public or cross-account access."
- AWS Services: IAM Access Analyzer (external access analyzer, policy validation, custom policy checks)
- Architecture Decision: Enable an org-level external-access analyzer per Region; wire policy
  validation + custom policy checks into IaC CI/CD to block policies that grant new/unintended access.
- Verification: `aws accessanalyzer validate-policy`; `aws accessanalyzer check-no-new-access`; review
  the Access Analyzer findings dashboard.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#bp-preview-access
        https://docs.aws.amazon.com/IAM/latest/UserGuide/what-is-access-analyzer.html
  (accessed 2026-07-31)

**Use conditions to constrain access (data perimeter)**
- Pillar Alignment: Security — SEC03-BP02
- Why: "You can grant access to actions and resources, but only if the access request meets specific
  conditions" — e.g., require TLS, restrict by source VPC/org ID/service.
- AWS Services: IAM policy `Condition` element (e.g., `aws:SecureTransport`, `aws:SourceVpc`,
  `aws:PrincipalOrgID`, `aws:ViaAWSService`)
- Architecture Decision: Add condition keys to enforce encryption-in-transit, network origin, and
  organization boundaries as part of a data perimeter.
- Verification: Policy review + Access Analyzer custom policy checks in CI; simulate with the IAM
  policy simulator.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#use-policy-conditions
  (accessed 2026-07-31)

### ⚠️ Architectural Decisions

**Human access model: IAM Identity Center vs SAML/OIDC federation into IAM roles vs IAM users**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | IAM Identity Center + external IdP | IAM Identity Center, STS | Central multi-account access, permission sets, MFA | Setup effort; another layer | Multi-account AWS Organizations (recommended default) |
  | Direct SAML/OIDC federation into IAM roles | IAM SAML/OIDC providers, STS | Simplicity for a single account | No central permission-set model | 1–2 accounts, existing IdP, minimal footprint |
  | IAM users with passwords/keys | IAM | Works with tools lacking federation | Long-term credentials to rotate/leak | Only the documented exception cases (see Never-Do) |

- Cost Profile: IAM and IAM Identity Center have no per-user charge; IAM Access Analyzer unused/
  internal analyzers are billed per role-or-resource analyzed per analyzer per month.
- Lock-in Assessment: Identity Center permission sets are AWS-specific but sit behind a standard
  SAML/OIDC IdP, so the IdP remains portable.
- Architect Instruction: "Ask which external IdP is authoritative (Entra ID / Okta / Ping) and
  whether the org is single- or multi-account, before choosing Identity Center vs direct federation."
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#bp-users-federation-idp
  (accessed 2026-07-31)

**Delegation model: Permissions boundaries vs central-only role creation**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Delegate role creation with a required permissions boundary | IAM permissions boundaries | Developer velocity, no central bottleneck | Boundary policy must be authored + enforced | Many teams needing self-service roles |
  | Central platform team creates all roles | IAM, IaC pipeline | Tight control, uniform review | Bottleneck, slower delivery | Small org or high-compliance environment |

- Cost Profile: No direct cost difference; operational cost differs (bottleneck vs governance
  tooling).
- Lock-in Assessment: Both are native IAM constructs; portable concepts, AWS-specific syntax.
- Architect Instruction: "Ask whether developers must self-serve IAM roles; if yes, mandate a
  permissions boundary + an SCP requiring the boundary on every created role."
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#bp-permissions-boundaries
  (accessed 2026-07-31)

**Authorization model at scale: RBAC (many policies) vs ABAC (tag-based)**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | RBAC — role/policy per job function | IAM managed policies | Explicit, auditable, simple mental model | Policy sprawl as teams/resources grow | Stable, small set of access patterns |
  | ABAC — tag-matching conditions | IAM condition keys (aws:PrincipalTag/ResourceTag) | Scales without editing policies; multi-tenant isolation | Requires disciplined, governed tagging | Many teams/projects/tenants with tag governance |

- Cost Profile: No direct IAM cost difference.
- Lock-in Assessment: ABAC condition keys are AWS-specific but the tagging concept is portable.
- Architect Instruction: "Ask whether a governed tagging standard exists (enforced via SCP/tag
  policies). ABAC without enforced tags becomes an access-control gap — default to RBAC if tagging
  is not governed."
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction_attribute-based-access-control.html
  (accessed 2026-07-31)

**Emergency/break-glass access (SEC03-BP03)**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Break-glass IAM role with strong monitoring | IAM role, CloudTrail, EventBridth alerts | Recovery during IdP/Identity Center outage | Must be tightly guarded + alerted | All production orgs need one |
  | Rely on root only | Root user | No extra setup | Root is the wrong tool; slow, high blast radius | Never as the primary plan |

- Cost Profile: Negligible.
- Lock-in Assessment: AWS-native.
- Architect Instruction: "Ask: what is the recovery path if the IdP or IAM Identity Center is
  unavailable? Define a monitored break-glass role, not ad-hoc root usage."
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_permissions_emergency_process.html
  (accessed 2026-07-31)

### 🚫 Anti-Patterns

**Long-term IAM access keys as the default credential**
- Risk Level: CRITICAL
- Why: Violates SEC02-BP02 (temporary credentials). Static keys leak in code, images, and logs and
  do not auto-rotate. Long-term keys are an explicit narrow exception, not the norm.
- ❌ Wrong: Application on EC2 reads `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` from an env var or
  `~/.aws/credentials` file baked into the AMI.
- ✅ Correct: EC2 instance profile (or Lambda execution / ECS task / EKS Pod Identity role) delivers
  auto-rotated temporary credentials the AWS SDK discovers automatically; for on-prem, IAM Roles
  Anywhere with X.509 certs.
- Detection: IAM credential report (`get-credential-report`); IAM Access Analyzer unused-access
  findings for access keys; git-secrets in CI.
- Impact: Data breach / account compromise via leaked credentials.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#bp-workloads-use-roles
  (accessed 2026-07-31)

**Root user access keys / daily root usage**
- Risk Level: CRITICAL
- Why: Root has unrestricted access including billing; keys cannot be permission-bounded and bypass
  most guardrails. "We strongly recommend that you do not create access keys for your root user."
- ❌ Wrong: Root user has an active access key used by a CI job; humans log in as root for routine
  admin.
- ✅ Correct: No root access keys exist; root credentials removed from member accounts via centralized
  root access; rare root-only tasks done via AssumeRoot from the management account; day-to-day admin
  via a federated administrator role.
- Detection: AWS Config `iam-root-access-key-check`; Security Hub IAM controls; CloudTrail/GuardDuty
  root-usage alerts.
- Impact: Full account takeover; irreversible actions.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/root-user-best-practices.html#ru-bp-access
  (accessed 2026-07-31)

**Wildcard `Action: "*"` / `Resource: "*"` in production identity policies**
- Risk Level: HIGH
- Why: Violates SEC03-BP02 (least privilege); grants far more than any task requires and enables
  privilege escalation.
- ❌ Wrong: Attaching a customer-managed policy with `{"Effect":"Allow","Action":"*","Resource":"*"}`
  to an application role "to make it work."
- ✅ Correct: Start from an AWS managed policy, then generate a least-privilege customer-managed
  policy from CloudTrail activity with IAM Access Analyzer policy generation; scope actions,
  resources, and conditions.
- Detection: IAM Access Analyzer policy validation (>100 checks) flags overly permissive statements;
  custom policy checks (`check-no-new-access`) in CI.
- Impact: Privilege escalation / large blast radius on compromise.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#best-practice-policy-validation
  (accessed 2026-07-31)

**No MFA on root or privileged users**
- Risk Level: CRITICAL
- Why: Violates SEC02-BP01. Password-only sign-in is phishable; AWS now mandates root MFA within 35
  days.
- ❌ Wrong: Root user and administrators sign in with password only, no MFA device registered.
- ✅ Correct: Phishing-resistant MFA (passkey/FIDO2 security key) on every root user (register up to 8
  devices) and enforced MFA at IAM Identity Center / IdP for all human sign-in.
- Detection: Security Hub control IAM.4; AWS Config `root-account-mfa-enabled`; Trusted Advisor "MFA
  on Root Account".
- Impact: Account compromise via credential phishing.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/root-user-best-practices.html#ru-bp-mfa
  (accessed 2026-07-31)

**Unintended public / cross-account resource sharing left unmonitored**
- Risk Level: HIGH
- Why: Violates SEC03-BP07. Resource-based policies (S3, KMS, Lambda, SQS, SNS, Secrets Manager, ECR,
  etc.) can silently expose data to external principals.
- ❌ Wrong: An S3 bucket policy or KMS key policy grants access to `"AWS": "*"` or an unknown external
  account, with no analyzer enabled.
- ✅ Correct: Enable an org-level IAM Access Analyzer external-access analyzer per Region; triage
  findings; add `aws:PrincipalOrgID` conditions / RCPs to enforce a data perimeter.
- Detection: IAM Access Analyzer external-access findings dashboard; `aws accessanalyzer list-findings`.
- Impact: Data exfiltration / compliance violation.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/what-is-access-analyzer.html#what-is-access-analyzer-resource-identification
  (accessed 2026-07-31)

**Treating SCPs/RCPs/boundaries as if they grant access**
- Risk Level: MEDIUM
- Why: "No permissions are granted by SCPs and RCPs." Misunderstanding effective-permission math
  leads to either broken access or a false sense of security.
- ❌ Wrong: Assuming attaching an SCP that "allows" a service actually grants principals access, and
  omitting the identity/resource policy.
- ✅ Correct: Grant via identity-based or resource-based policies; use SCP/RCP/boundary only to *cap*
  the maximum. Effective permission = intersection of all applicable policies.
- Detection: IAM policy simulator; Access Analyzer; review of effective-permissions results.
- Impact: Broken deployments or unintended standing access.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#bp-permissions-guardrails
  (accessed 2026-07-31)

**Stale, unused roles / keys / permissions never pruned**
- Risk Level: MEDIUM
- Why: Violates SEC03-BP04 (reduce permissions continuously). Unused access expands the attack
  surface silently.
- ❌ Wrong: Roles and access keys accumulate for years; no last-accessed review.
- ✅ Correct: Enable IAM Access Analyzer unused-access analyzer (flags unused roles, unused access
  keys, unused passwords, unused services/actions); schedule remediation using last-accessed data.
- Detection: IAM Access Analyzer unused-access findings; `aws iam get-service-last-accessed-details`.
- Impact: Enlarged blast radius; dormant credentials abused on compromise.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/what-is-access-analyzer.html#what-is-access-analyzer-unused-access-analysis
  (accessed 2026-07-31)

---

## Cloud-Native Design Patterns (IAM-relevant)

**Workload identity via role assumption**
- Category: Communication / Security
- Problem: Distributing credentials to workloads securely without static secrets.
- Solution on AWS: Compute service (EC2/Lambda/ECS/EKS) delivers a role's STS credentials; SDK
  discovers them from the instance/container metadata endpoint. Outside AWS: IAM Roles Anywhere
  (X.509), `AssumeRoleWithWebIdentity` (OIDC/JWT), or `AssumeRoleWithSAML`.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Security | No long-term secrets; auto-rotation | Requires trust config per source |
  | Portability | Standard OIDC/SAML for external | AWS-specific delivery for in-AWS compute |

- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#bp-workloads-use-roles
  (accessed 2026-07-31)

**Cross-account access via role trust + resource policy**
- Category: Communication
- Problem: A principal in account A must act on a resource in account B.
- Solution on AWS: Role in account B with a trust policy naming account A; identity policy in A
  allowing `sts:AssumeRole`; constrain with `aws:PrincipalOrgID` / ExternalId; for shared data,
  resource-based policy on the resource. Validate exposure with Access Analyzer.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Isolation | Accounts stay separate blast radii | More trust relationships to govern |
  | Auditability | Explicit AssumeRole events in CloudTrail | Two-sided policy to maintain |

- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/permissions-management.html
  (accessed 2026-07-31)

**ABAC for multi-tenant / multi-project isolation**
- Category: Scalability / Security
- Problem: Permissions must scale as teams and resources multiply without policy sprawl.
- Solution on AWS: Tag principals and resources with a governed `project`/`team` attribute; a single
  IAM policy uses `aws:PrincipalTag`/`aws:ResourceTag` matching to grant access to matching resources.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Maintenance | One policy, no per-resource edits | Requires enforced tag governance |
  | Risk | Automatic isolation | Missing/incorrect tags become gaps |

- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction_attribute-based-access-control.html
  (accessed 2026-07-31)

---

## Security Architecture

**Identity — centralized workforce access**
- AWS Services: IAM Identity Center (permission sets), external IdP via SAML/OIDC, STS
- Architecture: IdP authenticates humans → IAM Identity Center maps groups to permission sets →
  users assume account roles for short sessions. No standing human IAM users.
- Compliance Alignment: Supports SEC02-BP04 centralized identity; underpins access-review evidence
  for SOC2/ISO (structure only — not legal advice).
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/identity-management.html
  (accessed 2026-07-31)

**Permissions — least privilege lifecycle**
- AWS Services: Customer-managed policies, IAM Access Analyzer (policy generation + unused access),
  permissions boundaries, IAM last accessed
- Architecture: Start broad (AWS managed) → generate fine-grained policy from CloudTrail → attach
  customer-managed policy → continuously prune unused access → bound delegation with boundaries.
- Compliance Alignment: SEC03-BP02/BP04; produces evidence of least-privilege enforcement.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/permissions-management.html
  (accessed 2026-07-31)

**Guardrails — organization data perimeter**
- AWS Services: AWS Organizations SCPs (principal side) + RCPs (resource side), condition keys
  (`aws:PrincipalOrgID`, `aws:ResourceOrgID`, `aws:SourceVpc`, `aws:SecureTransport`)
- Architecture: SCPs deny high-risk/root actions and restrict Regions; RCPs prevent resources from
  granting access outside the org; conditions enforce network origin and encryption in transit.
- Compliance Alignment: SEC03-BP05; core of the AWS data-perimeter guidance.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#bp-permissions-guardrails
  (accessed 2026-07-31)

**Secrets — no embedded credentials**
- AWS Services: AWS Secrets Manager, AWS Systems Manager Parameter Store (SecureString), AWS KMS
- Architecture: Store any unavoidable secret in Secrets Manager with automatic rotation; grant the
  workload role `secretsmanager:GetSecretValue` scoped to the specific secret ARN; encrypt with a
  customer-managed KMS key. (SEC02-BP03)
- Compliance Alignment: SEC02-BP03 store and use secrets securely.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_identities_secrets.html
  (accessed 2026-07-31)

---

## Operational Patterns

**Continuous least-privilege review (FinOps-aware)**
- Operational Domain: Change Management / Governance
- AWS Services: IAM Access Analyzer (unused access analyzer), IAM last accessed, AWS Config
- Architecture: Org-level unused-access analyzer emits findings → ticketed remediation → policies
  regenerated from activity. Note: unused-access findings are Region-independent (one analyzer per
  org suffices), whereas external-access analyzers are per-Region.
- Cost Profile: Medium — unused/internal analyzers billed per role/resource per analyzer per month;
  right-size by scoping analyzers to the org rather than per-Region duplication for unused access.
- Automation: Automate finding ingestion + notifications; keep remediation as a reviewed decision.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/what-is-access-analyzer.html#what-is-access-analyzer-pricing
  (accessed 2026-07-31)

**Root usage monitoring and alerting**
- Operational Domain: Incident / Detection
- AWS Services: AWS CloudTrail (root sign-in + `AssumeRoot` privileged session events), Amazon
  EventBridge → Amazon SNS, Amazon GuardDuty (`Policy:IAMUser/RootCredentialUsage`)
- Architecture: CloudTrail records root and AssumeRoot events → EventBridge rule → SNS alert to
  security; GuardDuty raises a finding on root credential usage.
- Cost Profile: Low.
- Automation: Fully automatable alerting; response runbook to validate whether root usage was
  expected and escalate if not.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/root-user-best-practices.html#ru-bp-monitor
  (accessed 2026-07-31)

**Credential audit and rotation (SEC02-BP05)**
- Operational Domain: Governance
- AWS Services: IAM credential report, IAM access-key last-used, Secrets Manager rotation
- Architecture: Generate credential reports on a schedule; rotate/remove any unavoidable access keys
  using last-used data (e.g., when an employee leaves); enable automatic secret rotation.
- Cost Profile: Low.
- Automation: Automate report generation and rotation; retire keys that violate the temporary-
  credential default.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#update-access-keys
  (accessed 2026-07-31)

---

## Reference Architectures

**Multi-account IAM foundation (Organizations + Identity Center + Access Analyzer)**
- AWS Source: AWS Security Reference Architecture (Prescriptive Guidance) + IAM best practices
- Context: General production estate spanning many accounts under AWS Organizations.
- Services Composition:

  | Layer | Service | Purpose | Alternative |
  |-------|---------|---------|-------------|
  | Org root | AWS Organizations | Account hierarchy, SCPs, RCPs, centralized root access | — |
  | Human identity | IAM Identity Center + external IdP | Federated workforce access, permission sets, MFA | Direct SAML/OIDC per account |
  | Workload identity | IAM roles (instance profile / execution / task / Pod Identity), IAM Roles Anywhere | Temporary credentials to compute | OIDC federation |
  | Guardrails | SCPs + RCPs + permissions boundaries | Cap principal & resource permissions | — |
  | Assurance | IAM Access Analyzer (external/internal/unused), policy validation | Continuous least privilege & exposure detection | — |
  | Secrets | Secrets Manager + KMS | Rotate/encrypt unavoidable secrets | SSM Parameter Store SecureString |

- Key Decisions: Which IdP is authoritative; RBAC vs ABAC; whether developers self-serve roles (then
  mandate permissions boundaries); centralized-root-removal vs MFA-secured member root.
- Scaling Path: Add OUs and baseline SCPs/RCPs as account count grows; ABAC via governed tags to
  avoid policy sprawl; delegate Access Analyzer admin to a security account.
- Cost Baseline: Low for IAM/Identity Center/Organizations; medium for Access Analyzer unused/
  internal analyzers at scale.
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/organizations.html
  (accessed 2026-07-31)

---

## Service Equivalence Map

Identity & access equivalents across providers (for architects evaluating multi-cloud). Equivalence
does **not** imply feature parity — validate against each provider's current docs before deciding.

| Category | AWS | Google Cloud | Azure | Oracle Cloud (OCI) |
|----------|-----|-------------|-------|--------------------|
| Core IAM / authorization engine | IAM | Cloud IAM | Azure RBAC | IAM Policies |
| Workforce identity / SSO | IAM Identity Center | Workforce Identity Federation | Microsoft Entra ID | Identity Domains |
| Machine/workload identity | IAM roles, IAM Roles Anywhere | Workload Identity Federation / service accounts | Managed Identities / Workload Identity | Instance Principals / Dynamic Groups |
| Temporary credential broker | AWS STS | STS / token service | Entra token service | Security Token Service |
| Org-wide preventive guardrail (principals) | Organizations SCP | Organization Policies / IAM Deny policies | Azure Policy / Management Groups | Compartment Policies |
| Org-wide guardrail (resources / perimeter) | Organizations RCP | VPC Service Controls | Azure Policy / Private Link perimeter | Maximum Security Zones |
| Delegation cap | Permissions boundary | IAM Conditions / Deny policies | (no direct equivalent) | (no direct equivalent) |
| Attribute-based access | ABAC (tags) | IAM Conditions (tags/attributes) | ABAC (attributes) | Tag-based policies |
| Access analysis / least privilege | IAM Access Analyzer | Policy Analyzer / Recommender | Entra Access Reviews / PIM | Security Advisor / Cloud Guard |
| Secrets | Secrets Manager | Secret Manager | Key Vault | OCI Vault |
| Key management | AWS KMS | Cloud KMS | Key Vault | OCI Vault / Key Management |

> **⚠️ Important**: Service equivalence does NOT mean feature parity. Permissions boundaries (AWS)
> and RCP↔VPC Service Controls mappings are approximate; always validate against current provider
> documentation before an architecture decision.

---

## Provider Differentiators (AWS IAM)

```
Differentiator: Resource Control Policies (RCPs)
Category: Security
Unique Value: Org-wide guardrail that caps what *resources* can grant (data perimeter), complementing
  SCPs which cap what principals can do. A distinct two-sided guardrail model.
Architecture Impact: Enables enforcing "no resource in the org may be shared outside the org" centrally.
When to Leverage: Multi-account estates with strict data-perimeter requirements.
Caveat: RCPs grant nothing; they only reduce maximum resource access.
Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_rcps.html
  (accessed 2026-07-31)
```
```
Differentiator: Centralized root access management + AssumeRoot
Category: Security
Unique Value: Remove standing root credentials from every member account and perform rare root-only
  tasks via short-lived AssumeRoot sessions from the management account.
Architecture Impact: Eliminates the largest standing-credential risk across a multi-account org.
When to Leverage: Any AWS Organizations estate.
Caveat: AssumeRoot is limited to a defined list of privileged root tasks.
Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/root-user-best-practices.html#ru-bp-organizations
  (accessed 2026-07-31)
```
```
Differentiator: Permissions boundaries
Category: Security
Unique Value: A managed policy that caps the maximum permissions an identity policy can grant to a
  specific entity — enabling safe developer self-service role creation.
Architecture Impact: Decentralizes IAM without privilege escalation risk.
When to Leverage: Many-team orgs needing self-service IAM.
Caveat: Grants nothing on its own; must be paired with an SCP requiring the boundary.
Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html
  (accessed 2026-07-31)
```
```
Differentiator: IAM Access Analyzer (external + internal + unused + policy generation)
Category: Security
Unique Value: Logic-based (automated reasoning) analysis of policies for external exposure, internal
  access paths, unused access, plus policy generation from CloudTrail and >100 validation checks.
Architecture Impact: Makes least privilege continuous and CI/CD-enforceable.
When to Leverage: Every production org; wire custom policy checks into IaC pipelines.
Caveat: External-access analyzers are per-Region; unused/internal analyzers are billed per entity.
Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/what-is-access-analyzer.html
  (accessed 2026-07-31)
```

---

## Scenario Coverage

**Standard Case**: Multi-account production estate needing secure human + workload access.
- Approach: Organizations + IAM Identity Center (external IdP, phishing-resistant MFA) for humans;
  IAM roles for all workloads; baseline SCPs + RCPs; org-level IAM Access Analyzer; centralized root
  removal. No standing IAM users.
- Key Decisions: Authoritative IdP; RBAC vs ABAC; developer self-service (permissions boundaries);
  break-glass role design; per-Region external analyzers.

**Edge Case**: A workload genuinely cannot use IAM roles (e.g., a third-party client/plugin that
only supports static keys, or CodeCommit/Amazon Keyspaces service-specific credentials).
- Approach: Use the documented exception — an IAM user with least-privilege scope and long-term keys;
  audit with last-used data and rotate/remove promptly (SEC02-BP05); isolate to a dedicated,
  tightly-bounded principal; prefer service-specific credentials where the service offers them.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#update-access-keys
  (accessed 2026-07-31)

**Anti-Pattern Case**: A team asks to attach `AdministratorAccess` (or `Action:*`/`Resource:*`) to an
application role "to unblock a deploy."
- Clarification: Refuse the wildcard grant. Ask which specific actions/resources the workload needs;
  generate a least-privilege policy from CloudTrail via IAM Access Analyzer policy generation and
  validate it with policy validation / custom policy checks before attaching.

---

## Source Bibliography

### Primary Sources (Official AWS documentation — all accessed 2026-07-31; living/`latest` docs)
- IAM — Security best practices in IAM — https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html
- IAM — Root user best practices for your AWS account — https://docs.aws.amazon.com/IAM/latest/UserGuide/root-user-best-practices.html
- IAM — Using IAM Access Analyzer — https://docs.aws.amazon.com/IAM/latest/UserGuide/what-is-access-analyzer.html
- IAM — Permissions boundaries for IAM entities — https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html
- IAM — ABAC for AWS — https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction_attribute-based-access-control.html
- Well-Architected Security Pillar — Identity and access management — https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/identity-and-access-management.html
- Well-Architected Security Pillar — Identity management (SEC02-BP01…BP06) — https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/identity-management.html
- Well-Architected Security Pillar — Permissions management (SEC03-BP01…BP09) — https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/permissions-management.html
- AWS Organizations — Service control policies (SCPs) — https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html
- AWS Organizations — Resource control policies (RCPs) — https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_rcps.html
- AWS Prescriptive Guidance — Security Reference Architecture (Organizations, accounts, guardrails) — https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/organizations.html

### Validation / Supporting Sources
- IAM Identity Center — What is IAM Identity Center — https://docs.aws.amazon.com/singlesignon/latest/userguide/what-is.html
- AWS STS API Reference — AssumeRoot — https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRoot.html
- IAM Access Analyzer pricing — https://aws.amazon.com/iam/access-analyzer/pricing

> ⚠️ Currency: AWS IAM docs are living (`latest`) with no semantic version. Re-verify against the
> pages above by **2027-07-31**. No source used here is a dated blog older than 12 months; all
> primary material is current official documentation.

---

## Agent Operation Notes (for downstream skill authoring)

- **High confidence (autonomous)**: All Mandatory Patterns and Anti-Patterns above — each maps to an
  explicit official IAM best-practice recommendation or a Security Pillar BP with a live URL.
- **Ask-First that was NOT resolvable from the invocation** (surface to the user before authoring a
  prescriptive skill):
  1. **ARCHITECTURE_CONTEXT** — the invocation gave only "aws IAM". This research assumed a general
     multi-account production estate. Confirm the actual workload (SaaS multi-tenant? regulated
     finance? single account?) — it changes ABAC-vs-RBAC and break-glass guidance.
  2. **Compliance scope** — SOC2/HIPAA/PCI-DSS/GDPR-specific IAM controls were intentionally NOT
     added (compliance is organization-specific). Ask before adding compliance-specific constraints.
  3. **Single- vs multi-account** — several patterns (Identity Center, SCP/RCP, centralized root
     removal) assume AWS Organizations. Confirm before authoring.
- **Not covered (out of scope for this domain pass)**: detailed KMS key-policy design, VPC network
  IAM (endpoint policies), and full data-perimeter condition-key catalog — flag as follow-up research
  if the downstream skill needs them.
