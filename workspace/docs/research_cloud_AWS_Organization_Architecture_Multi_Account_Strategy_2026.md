# AWS Organization Architecture — Multi-Account Strategy (AWS Organizations 2026)

> Anti-hallucination research base. Every pattern is sourced to official AWS documentation with an
> access date. Items that could not be confirmed against an official source are tagged
> `⚠️ unverified`. Do not treat this file as legal or compliance advice.

## Metadata

```yaml
Full_Name: "AWS Organization Architecture — Multi-Account Strategy"
Cloud_Provider: "AWS"
Architecture_Domain: "Organization Architecture - Multi-Account Strategy"
Target_Edition: "AWS Organizations 2026"
Architecture_Context: "Enterprise multi-account AWS environment with governance, security, and cost management requirements"
Official_Source_URL: "https://docs.aws.amazon.com/organizations/latest/userguide/"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-08-26"
Research_Depth: "exhaustive (5 parallel investigator agents)"
Currency_Threshold: "2027-08-26 — review after this date; Organizations ships new policy types frequently"
```

---

## Executive Summary

AWS Organizations is the foundation for any enterprise multi-account strategy on AWS. It provides a tree-shaped hierarchy (root → OUs → accounts) through which policies, billing, and governance propagate. As of 2026, AWS organizes its organizational policies into two principal categories: **Authorization policies** (Service Control Policies / SCPs and Resource Control Policies / RCPs) that act as permission guardrails, and **Declarative policies** (EC2, Backup, Tag, AI opt-out, Chatbot, Security Hub, Inspector, Bedrock, Shield Network Security Director, S3, and Upgrade rollout policies) that centrally configure and maintain desired service states. Any SKILL or architectural guidance still using the old "management policies" umbrella is misinformation — the 2026 documentation restructure sunsets that term.

**What changed in 2026 vs previous editions.** The most material 2026 change: organizations created via the AWS Management Console **after July 10, 2026** automatically receive a root SCP denying `organizations:LeaveOrganization` and `account:CloseAccount`, hardening the default posture. In July 2026, VPC Encryption Controls became available as a declarative policy type, enabling enforce-mode encryption settings across all existing and future VPCs. AWS Control Tower Landing Zone v4.0 (November 17, 2025) removed the mandatory Security OU requirement and made service integrations (AWS Config, CloudTrail, Security Roles, AWS Backup) individually optional — a significant flexibility increase. Resource Control Policies (RCPs) launched November 13, 2024 and are now a standard tool in the data-perimeter pattern.

**Three most critical guardrails for enterprise multi-account architecture.** (1) **Never run workloads or resources in the management account** — SCPs do not restrict the management account, and placing resources there permanently removes the coarse-grained guardrail layer. (2) **Delegate all security service administration to the Security Tooling (Audit) member account**, not the management account — this keeps the security control plane subject to SCP/RCP constraints. (3) **Implement the data perimeter using both SCPs (identity-centric) and RCPs (resource-centric)** — using only SCPs leaves a gap: external identities accessing your resources from outside your org are not constrained by SCPs, only by RCPs and resource-based policies.

---

## Framework Pillars

AWS Multi-Account Strategy aligns to the **AWS Well-Architected Framework** six-pillar model. Every guardrail and pattern in this research maps to at least one pillar. Edition: **AWS Organizations 2026**.

```
Pillar: Security
Definition (AWS WAF 2024): "The ability to protect data, systems, and assets to take advantage of
  cloud technologies to improve your security."
Key Design Principles: Implement a strong identity foundation; enable traceability; apply security
  at all layers; automate security best practices; protect data in transit and at rest; keep people
  away from data; prepare for security events.
Applies To Multi-Account: Organization-level guardrails (SCPs, RCPs) are the security-at-all-layers
  mechanism. Delegated admin to Security Tooling account enforces "keep people away from data."
Assessment Questions: Are SCPs enforced on all member OUs? Is an organization CloudTrail trail
  delivering logs to an immutable Log Archive account? Is the management account protected from
  workload resources?
Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html
```

```
Pillar: Operational Excellence
Definition (AWS WAF 2024): "The ability to support development and run workloads effectively, gain
  insight into their operations, and continuously improve supporting processes and procedures."
Key Design Principles: Perform operations as code; make frequent, small, reversible changes;
  refine operations procedures frequently; anticipate failure; learn from all operational events.
Applies To Multi-Account: Infrastructure-as-code account vending (AFT) and policy-as-code (SCPs/
  tag policies deployed via Policy Staging OU) embody operational excellence. Organization CloudTrail
  provides the insight layer.
Assessment Questions: Are new accounts provisioned via Account Factory or AFT (not manually)? Are
  SCP/policy changes tested in a Policy Staging OU before broad rollout? Is account lifecycle
  (provision → suspend → close) automated?
Source: https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/welcome.html
```

```
Pillar: Reliability
Definition (AWS WAF 2024): "The ability of a workload to perform its intended function correctly
  and consistently when it's expected to."
Key Design Principles: Automatically recover from failure; test recovery procedures; scale
  horizontally; stop guessing capacity; manage change through automation.
Applies To Multi-Account: Account-level blast-radius isolation is the primary reliability pattern —
  a failure in one account cannot propagate SCPs, quotas, or billing limits to other accounts.
  Service quota isolation per account supports independence of workloads.
Assessment Questions: Are production workloads isolated in dedicated accounts (not mixed with
  dev/test)? Is there a Business Continuity OU and DR strategy for critical workloads? Are Service
  Quota limits monitored per account?
Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html
```

```
Pillar: Performance Efficiency
Definition (AWS WAF 2024): "The ability to use computing resources efficiently to meet system
  requirements, and to maintain that efficiency as demand changes and technologies evolve."
Key Design Principles: Democratize advanced technologies; go global in minutes; use serverless
  architectures; experiment more often; consider mechanical sympathy.
Applies To Multi-Account: Service quota distribution across accounts prevents one workload from
  throttling another. Regional expansion (multi-Region org trail, multi-Region SCPs) supports
  "go global in minutes" for new accounts.
Assessment Questions: Are separate accounts used for workloads with different scaling characteristics?
  Are Service Quotas requested proactively (not reactively) per account?
Source: https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/welcome.html
```

```
Pillar: Cost Optimization
Definition (AWS WAF 2024): "The ability to run systems to deliver business value at the lowest
  price point."
Key Design Principles: Implement cloud financial management; adopt a consumption model; measure
  overall efficiency; stop spending money on undifferentiated heavy lifting; analyze and attribute
  expenditure.
Applies To Multi-Account: Consolidated billing with RI/SP sharing maximizes volume discounts. Tag
  policies enforce cost allocation tags org-wide. AWS Budgets per-OU and per-account provide
  "analyze and attribute expenditure" at scale. Cost Optimization Hub (delegated admin) surfaces
  cross-account savings opportunities.
Assessment Questions: Are cost allocation tags enforced via Tag Policies? Is Cost Anomaly Detection
  enabled? Are RI/SP sharing preferences configured intentionally (not defaulted)?
Source: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html
```

```
Pillar: Sustainability
Definition (AWS WAF 2024): "The ability to continually improve sustainability impacts by reducing
  energy consumption and increasing efficiency across all components of a workload."
Key Design Principles: Understand your impact; establish sustainability goals; maximize utilization;
  anticipate and adopt new, more efficient hardware and software offerings; use managed services;
  reduce the downstream impact of your cloud workloads.
Applies To Multi-Account: Rightsizing across accounts (surfaced by Cost Optimization Hub) directly
  reduces resource over-provisioning. Sandbox accounts with automated shutdown policies (via
  SCPs + EventBridge) prevent idle resource accumulation.
Assessment Questions: Are Sandbox/Development account budgets and auto-shutdown policies configured?
  Is Cost Optimization Hub's rightsizing analyzed for efficiency gains beyond cost?
Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/welcome.html
```

---

## Cloud Architecture Glossary

```
Term: Organization
Definition: A collection of AWS accounts managed centrally in a hierarchical tree with a single root
  at the top. Consists of one management account, zero or more member accounts, and zero or more OUs.
Provider Docs Section: orgs_getting-started_concepts.html
Architect Usage: The governance boundary; policies attached at any node flow down to all descendants.
Common Confusion: Confused with "AWS account". An organization contains multiple accounts; an
  account is the isolation boundary for IAM, quotas, and billing.
```

```
Term: Administrative root (root)
Definition: The top-most container in the org hierarchy, contained in the management account.
  Only ONE root exists per organization; auto-created when the org is created.
Provider Docs Section: orgs_getting-started_concepts.html
Architect Usage: The broadest attachment point for policies. AWS strongly recommends NOT attaching
  SCPs to the root without thorough testing — a deny here blocks all accounts org-wide.
Common Confusion: Confused with "root user". The org root is a structural container;
  the root user is the superuser of a specific AWS account.
```

```
Term: Organizational Unit (OU)
Definition: A group of AWS accounts within an organization that can contain other OUs. Accounts
  inherit policies from all parent OUs in the path from the root down to their OU.
Provider Docs Section: orgs_getting-started_concepts.html
Architect Usage: The primary policy-attachment granularity. Group accounts by common security/
  operational profile, not by org chart. Max nesting: 5 levels under root.
Common Confusion: Confused with IAM groups. OUs are hierarchical and hold accounts; IAM groups
  hold users and are flat.
```

```
Term: Management account
Definition: The AWS account used to create the organization. Acts as the ultimate owner and payer
  account. Cannot be changed. SCPs do NOT restrict its users/roles.
Provider Docs Section: orgs_getting-started_concepts.html
Architect Usage: Use only for org-level management tasks. Never deploy workload resources here.
  Limit access to the smallest possible set of highly trusted admins.
Common Confusion: Often incorrectly used as the delegated administrator account. AWS explicitly
  recommends delegating security service administration to a member Security Tooling account instead.
```

```
Term: Service Control Policy (SCP)
Definition: Authorization policy that sets maximum available permissions for IAM users and roles in
  member accounts. Principal-centric. Does NOT grant permissions; only restricts.
Provider Docs Section: orgs_manage_policies_scps.html
Architect Usage: Primary guardrail for what IAM principals in member accounts can do. Attach to OUs.
  Does not affect the management account or service-linked roles.
Common Confusion: Confused with IAM policies. SCPs are ceiling guards — they do not grant access;
  you still need IAM identity/resource policies to grant permissions within the SCP boundary.
```

```
Term: Resource Control Policy (RCP)
Definition: Authorization policy that sets maximum available permissions on resources in member
  accounts. Resource-centric. Launched November 13, 2024. Does NOT grant permissions; only restricts.
Provider Docs Section: orgs_manage_policies_rcps.html
Architect Usage: Use alongside SCPs to enforce data perimeter — prevents external identities (outside
  your org) from accessing your S3, STS, KMS, SQS, and Secrets Manager resources.
Common Confusion: Confused with S3 bucket policies or resource-based policies. RCPs are org-wide
  guardrails applied from Organizations, not individual resource policies.
```

```
Term: Declarative policy
Definition: An AWS Organizations policy type that centrally declares and maintains desired service
  configuration states. Unlike SCPs/RCPs (guardrails), declarative policies actively configure
  services and maintain the configuration as the service evolves.
Provider Docs Section: orgs_getting-started_concepts.html
Architect Usage: Use for EC2/EBS/VPC settings, Backup plans, Tag standardization, AI opt-out,
  Security Hub, Inspector, Bedrock guardrails. The service maintains compliance over time.
Common Confusion: Frequently called "management policies" in older AWS blogs — that term is
  deprecated as of 2025/2026 documentation restructure. The correct umbrella is "declarative policies."
```

```
Term: Delegated administrator
Definition: A member account authorized to perform management-like actions for a specific AWS service
  without needing direct management account access. Two types: (1) Organizations-level delegated
  admin (manage org policies), (2) Service-specific delegated admin (manage one integrated service).
Provider Docs Section: orgs_getting-started_concepts.html
Architect Usage: The primary pattern for reducing management account access surface. Register the
  Security Tooling account as delegated admin for GuardDuty, Security Hub, Config, IAM Access Analyzer,
  Macie, Detective, Audit Manager, Inspector, Firewall Manager, CloudTrail, Systems Manager.
Common Confusion: Confused with the management account. The delegated admin IS a member account and
  IS subject to SCP/RCP guardrails — this is its security advantage.
```

```
Term: Data perimeter
Definition: A set of coarse-grained permission guardrails ensuring only trusted identities access
  trusted resources from expected networks. Three axes: trusted identities, trusted resources,
  expected networks.
Provider Docs Section: access_policies_data-perimeters.html (IAM User Guide)
Architect Usage: Implement via SCPs (identity-centric), RCPs (resource-centric), and VPC endpoint
  policies (network-centric). Use condition keys aws:PrincipalOrgID, aws:ResourceOrgID, aws:SourceVpc.
Common Confusion: Confused with network perimeter only. A data perimeter spans IAM policy types and
  cannot be achieved with network controls alone.
```

```
Term: AWS Control Tower
Definition: An orchestration layer on top of AWS Organizations that provisions a governed landing
  zone, auto-creates foundational accounts (Log Archive, Audit), and applies controls (preventive,
  detective, proactive) at scale.
Provider Docs Section: how-control-tower-works.html
Architect Usage: Use as the baseline governance layer for any new AWS org. From v4.0 (Nov 2025),
  the Security OU is optional and service integrations are individually selectable.
Common Confusion: Confused with AWS Organizations. Control Tower uses Organizations as its foundation
  but adds account vending (Account Factory), controls library, and a management console.
```

```
Term: Landing Zone Accelerator (LZA)
Definition: An open-source CDK-based solution that extends Control Tower with deeper networking,
  security service orchestration, and multi-Region/partition support. Complementary to — not a
  replacement for — Control Tower.
Provider Docs Section: docs.aws.amazon.com/solutions/latest/landing-zone-accelerator-on-aws/
Architect Usage: Add LZA when Control Tower alone is insufficient: regulated workloads, GovCloud/
  Secret/Top Secret partitions, complex Transit Gateway topologies, or extensive Config/Security Hub
  customization.
Common Confusion: Confused with "Control Tower alternative." AWS explicitly positions them as
  complementary; LZA generates workload accounts via Control Tower Account Factory.
```

---

## Mandatory Patterns

**Pattern: Isolated Management Account — No Workloads**
- Pillar Alignment: Security (AWS Well-Architected)
- Why: SCPs do not apply to any IAM user or role in the management account. Any workload running there operates without the organization's primary guardrail layer. AWS states explicitly: "Because of the functionality and scope of influence the management account holds, we recommend that you limit access to this account" and "store all of your AWS resources in other AWS accounts in the organization and keep them out of the management account."
- AWS Services: AWS Organizations management account; IAM Identity Center for access control; delegated administrator pattern for all security services
- Architecture Decision:
  Use the management account exclusively for: creating org resources/OUs/policies, installing org-level automation tooling, consolidated billing, and break-glass access. All workload resources — databases, compute, data stores, application logic — must reside in member accounts governed by OUs with appropriate SCPs/RCPs.
- Verification:
  ```bash
  aws resourcegroupstaggingapi get-resources --region us-east-1 \
    --profile management-account-profile
  # Expected: zero or near-zero workload resources
  aws iam list-users --profile management-account-profile
  # Expected: no long-term IAM users (use IAM Identity Center instead)
  ```
- Trade-offs: Requires cross-account IAM roles for any automation that touches the management account; slightly more complex break-glass procedures.
- Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices_mgmt-acct.html (accessed 2026-08-26)

---

**Pattern: Root SCP Denying Account Departure and Closure**
- Pillar Alignment: Security
- Why: Without this SCP, any administrator in a member account with sufficient IAM permissions could remove their account from the org or close it, bypassing all governance. AWS recommends attaching at the root: `Deny organizations:LeaveOrganization` and `Deny account:CloseAccount`.
- AWS Services: AWS Organizations SCPs; applied at root to cover all member accounts
- Architecture Decision:
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "DenyLeaveOrg",
        "Effect": "Deny",
        "Action": ["organizations:LeaveOrganization", "account:CloseAccount"],
        "Resource": "*"
      }
    ]
  }
  ```
  > **2026 Note:** Organizations created via the AWS Management Console **after July 10, 2026** automatically receive this SCP at the root. Orgs created via CLI/SDK/CloudFormation or before that date must add it manually.
- Verification:
  ```bash
  aws organizations list-policies --filter SERVICE_CONTROL_POLICY \
    --query "Policies[*].{Name:Name,Id:Id}"
  aws organizations list-targets-for-policy --policy-id <policy-id>
  # Confirm root is a target
  ```
- Trade-offs: Closing an account now requires management-account-level action — adds a gate but this is the desired behavior.
- Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices_mgmt-acct.html (accessed 2026-08-26)

---

**Pattern: Delegated Security Service Administration to Security Tooling Account**
- Pillar Alignment: Security
- Why: Running security service administration from the management account unnecessarily expands its access surface and prevents SCP/RCP enforcement on the security admin surface itself. A member account (Security Tooling) that holds delegated admin roles IS subject to organizational guardrails.
- AWS Services: Security Tooling / Audit account in the Security OU; delegated administrator registration for: AWS CloudTrail (org trail), AWS Security Hub CSPM, Amazon GuardDuty, Amazon Detective, AWS Config, Amazon Macie, IAM Access Analyzer, AWS Firewall Manager, AWS Audit Manager, Amazon Inspector, AWS Security Incident Response, AWS Systems Manager, IAM Identity Center root access management
- Architecture Decision:
  Register a single dedicated "Security Tooling" member account as delegated administrator for all security services listed above. Ensure GuardDuty, Detective, and Security Hub CSPM share the same delegated admin account — misaligned delegated admin accounts break cross-service navigation (e.g., pivot from Security Hub finding into Detective). Exception: Amazon Security Lake delegates to the Log Archive account.
- Verification:
  ```bash
  aws organizations list-delegated-administrators \
    --service-principal guardduty.amazonaws.com
  aws organizations list-delegated-administrators \
    --service-principal securityhub.amazonaws.com
  # Confirm same account ID for both
  ```
- Trade-offs: One account holds high-security-service privilege; protect it with dedicated SCPs and the most restricted IAM Identity Center permission sets.
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/security-tooling.html (accessed 2026-08-26)

---

**Pattern: Centralized Log Archive with Immutable Storage**
- Pillar Alignment: Security, Operational Excellence
- Why: Logs are the forensic record. Centralizing in a dedicated account with immutable storage prevents tampering by any member account, even a compromised one.
- AWS Services: Log Archive account (Security OU); Amazon S3 with Object Lock (COMPLIANCE mode); AWS KMS customer-managed key (CMK); AWS CloudTrail organization trail; Amazon VPC Flow Logs; AWS Config delivery channel; Amazon CloudWatch Unified Data Experience (primary analytics); Amazon Security Lake (secondary)
- Architecture Decision:
  Configure a single S3 bucket in the Log Archive account. Enable: Object Lock (immutability), Versioning, SSE-KMS with a CMK, bucket policy restricting writes to the organization trail ARN only (prevents confused-deputy). Configure the org trail as multi-Region, capturing global-service events, with log file validation enabled. Set Config delivery channel to write to the same Log Archive S3 bucket. Limit Log Archive account access to automated/read-only roles — no human should routinely log in.
- Verification:
  ```bash
  aws s3api get-object-lock-configuration \
    --bucket <central-log-bucket> --profile log-archive
  # Expected: ObjectLockConfiguration.ObjectLockEnabled = Enabled
  aws cloudtrail get-trail-status --name <org-trail-name>
  # Expected: IsLogging = true, IsOrganizationTrail = true
  ```
- Trade-offs: Cross-account S3 writes require bucket policy grants; KMS CMK policy must allow CloudTrail principal; adds per-object storage cost vs unencrypted bucket.
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/log-archive.html (accessed 2026-08-26)

---

**Pattern: IAM Identity Center for All Human Access**
- Pillar Alignment: Security
- Why: Long-lived IAM users with static credentials are a primary attack vector in multi-account environments. IAM Identity Center issues temporary credentials scoped to permission sets, with centralized MFA enforcement.
- AWS Services: AWS IAM Identity Center; permission sets; AWS Organizations integration; SAML 2.0 / OIDC external IdP integration
- Architecture Decision:
  Enable IAM Identity Center in the management account; delegate administration to the Shared Services account. Create permission sets aligned to roles (ReadOnly, Developer, SecurityAdmin, OrgAdmin). For the management account specifically: assign individual users (not groups) to permission sets, because group membership can be escalated by group admins. Enforce MFA for all users. Use an external IdP (Okta, Azure AD) where available.
- Verification:
  ```bash
  aws sso-admin list-instances
  # Confirm IAM Identity Center is enabled
  aws iam list-users
  # In member accounts: Expected: zero IAM users (all access via Identity Center)
  ```
- Trade-offs: Requires browser-based AWS access portal or AWS CLI v2 `aws sso login`; no support for long-lived programmatic keys by design.
- Source: https://docs.aws.amazon.com/singlesignon/latest/userguide/delegated-admin.html (accessed 2026-08-26)

---

**Pattern: Management Account Root User Hardening**
- Pillar Alignment: Security
- Why: The management account root user has unlimited permissions over the entire organization and cannot be constrained by any policy. AWS now requires MFA registration for the management account root user (mandatory at first sign-in or within a 35-day grace period, rolled out 2025).
- AWS Services: IAM (root user); AWS MFA (hardware TOTP, FIDO2 passkey); AWS CloudTrail (root activity monitoring); Amazon GuardDuty (root credential usage finding); AWS Config rules `root-account-mfa-enabled`, `iam-root-access-key-check`
- Architecture Decision:
  Register at least 2 MFA devices (up to 8 allowed) for management account root. Do not create root access keys. Use a group email address for the root credential, not a personal mailbox. Split custody: password with one group, MFA with a different group. Monitor root usage via CloudTrail event filter on `userIdentity.type = Root`; alert via CloudWatch/EventBridge + SNS. Enable centralized root access management for member accounts — remove member-account root credentials entirely and perform privileged root-only member tasks via `sts:AssumeRoot` from the Security Tooling account.
- Verification:
  ```bash
  aws iam get-account-summary --query \
    "SummaryMap.{AccountMFAEnabled:AccountMFAEnabled,AccountAccessKeysPresent:AccountAccessKeysPresent}"
  # Expected: AccountMFAEnabled=1, AccountAccessKeysPresent=0
  ```
- Trade-offs: Multi-person custody adds friction to root access; this friction is the intended control.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/root-user-best-practices.html (accessed 2026-08-26)

---

## Architectural Decisions

**Decision: OU Structure Design**
- Options:

  | OU Category | OU Name | Purpose | When Needed |
  |---|---|---|---|
  | Foundational | Security OU | Log Archive + Audit/Security Tooling accounts | Always (even as optional in CT v4.0) |
  | Foundational | Infrastructure OU | Network, Shared Services, Backup accounts | Always for enterprise |
  | Application | Workloads OU | Business workload accounts (prod + non-prod) | Always |
  | Experimental | Sandbox OU | Free experimentation, disconnected from prod | When developers need isolated exploration |
  | Procedural | Exceptions OU | Non-standard policy deviations | Minimally, when unavoidable |
  | Procedural | Suspended OU | Deactivated/suspended accounts | Always — accounts held here before closure |
  | Procedural | Policy Staging OU | Test SCP/tag policy changes before rollout | Strongly recommended |
  | Procedural | Transitional OU | Landing zone for newly onboarded accounts | When migrating existing accounts |
  | Advanced | Deployments OU | CI/CD pipeline accounts | When CI/CD infrastructure needs isolation |
  | Advanced | Business Continuity OU | DR/air-gapped bunker accounts | Regulated/critical workloads |
  | Advanced | Individual Business Users OU | User/BU self-managed AWS accounts | When business units need direct access |

- Design Principles (per AWS Whitepaper, April 30, 2025):
  - Organize by function, not by org chart
  - Apply SCPs to OUs, not accounts; account-level SCPs only for exceptions
  - Avoid deep hierarchies (5 levels max; use only when benefit is clear)
  - Start small; expand as needs emerge
  - For non-production environments: choose Option A (single NonProd OU) when dev+test share access policies; choose Option B (separate Dev OU + Test OU) when they need different SCP profiles

- Cost Profile: No direct cost difference — OU structure affects operational complexity and audit scope, not AWS billing.
- Architect Instruction: "Ask the architect: Does the dev environment require meaningfully different SCPs than the test environment? If yes, create separate OUs. If not, a single NonProd OU reduces SCP maintenance overhead."
- Source: https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/recommended-ous-and-accounts.html (accessed 2026-08-26; publication date April 30, 2025)

---

**Decision: Multi-Account Networking Topology**
- Options:

  | Option | AWS Services | Optimizes | Sacrifices | Best When |
  |---|---|---|---|---|
  | Hub-spoke (Transit Gateway) | AWS Transit Gateway + AWS RAM | Centralized routing control; single on-prem attachment | Higher per-GB transit cost vs VPC peering; TGW route table complexity | >5 VPCs; hybrid connectivity needed; centralized inspection required |
  | VPC Sharing (Shared VPC) | Amazon VPC + AWS RAM | Fewer VPCs; no cross-AZ data transfer charges within same AZ | Reduced isolation; participants share subnet space | Teams co-located in same security posture; IPv4 address scarcity |
  | VPC Peering (mesh) | VPC Peering | No per-GB charge between VPCs in same AZ; simple | Does not scale (N² connections); no transitive routing | <5 VPCs with stable topology |
  | AWS PrivateLink (per-service) | AWS PrivateLink endpoint services | Strong per-service isolation; cross-account without VPC peering | Cost per endpoint; latency overhead | Exposing specific services cross-account; 3rd-party integrations |

- Cost Profile: Transit Gateway: $0.05/attachment-hour + $0.02/GB processed. VPC Sharing: no data transfer charges for same-AZ traffic between instances in shared subnet. PrivateLink: $0.01/hour per endpoint + $0.01/GB.
- Lock-in Assessment: All options use AWS-native services; Transit Gateway and PrivateLink have no direct equivalents in other clouds — migration requires re-architecting connectivity.
- Architect Instruction: "Ask the architect: Is centralized traffic inspection (firewall, IDS/IPS) required? If yes, Transit Gateway with an inspection VPC is the only scalable option. Is IPv4 address space constrained? If yes, evaluate VPC Sharing."
- Source: https://docs.aws.amazon.com/whitepapers/latest/building-scalable-secure-multi-vpc-network-infrastructure/transit-gateway.html (accessed 2026-08-26)

---

**Decision: Control Tower vs DIY Organizations vs LZA**
- Options:

  | Option | Effort | Flexibility | Compliance | Best When |
  |---|---|---|---|---|
  | AWS Control Tower | Low setup; managed | Moderate (v4.0 = high) | Built-in controls catalog | Standard enterprise; most use cases |
  | DIY AWS Organizations | High setup; manual | Maximum | Manual | Full customization required; non-standard patterns |
  | Control Tower + LZA | Medium setup; IaC-driven | Very high | Extended catalog + custom | Regulated/sovereign workloads; GovCloud/Secret/Top Secret |

- Cost Profile: Control Tower: no additional charge (pay for Config, CloudTrail, etc.). LZA: ~$430/month baseline (idle sandbox with Control Tower in us-east-1). DIY: pay only for underlying services but high engineering cost.
- Architect Instruction: "Ask the architect: Are you operating in GovCloud, Secret, or Top Secret regions, or do you have DoD compliance requirements? If yes, LZA is required. Are you starting from scratch with standard compliance needs? Control Tower is the recommended baseline."
- Source: https://docs.aws.amazon.com/solutions/latest/landing-zone-accelerator-on-aws/solution-overview.html (accessed 2026-08-26)

---

**Decision: RI and Savings Plans Discount Sharing Strategy**
- Options:

  | Sharing Mode | Behavior | Optimizes | Sacrifices | Best When |
  |---|---|---|---|---|
  | Organization-wide | Owner first; remainder shared org-wide | Total org savings | Individual BU cost accountability | Single-payer cost culture; centralized FinOps |
  | Prioritized Group Sharing | Owner first; then defined groups; then rest of org | BU-prioritized savings | Slightly more complex setup | Multiple BUs with separate RI budgets |
  | Restricted Group Sharing | Owner first; exclusively within group; no org spillover | BU isolation | Potential unused RI capacity | Chargeback model requiring strict BU cost isolation |

- Cost Profile: Disabling sharing can result in higher monthly bills if RIs purchased for shared use go unused by the owner. Sharing settings finalize at 23:59:59 UTC on the last day of each month.
- Architect Instruction: "Ask the architect: Does the organization use chargeback (BU charged exact AWS costs) or showback (BU sees costs but central IT pays)? Chargeback typically requires Restricted Group Sharing; showback can use Organization-wide sharing."
- Source: https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/ri-turn-off.html (accessed 2026-08-26)

---

## Anti-Patterns

**Anti-Pattern: Running Workloads in the Management Account**
- Risk Level: CRITICAL
- Why: SCPs — the primary policy guardrail in AWS Organizations — do not restrict any IAM user or role in the management account. Any workload there operates in a policy-free zone. Framework pillar: Security (AWS Well-Architected).
- Risk: A compromised workload in the management account gives an attacker full organizational control — they can modify SCPs, remove member accounts, or access billing data for all accounts.
- ❌ Wrong: Deploying an EC2 application, RDS database, or Lambda function in the management account; using the management account as a "general-purpose" AWS account.
- ✅ Correct: Create a dedicated member account per workload (or per workload group) within the Workloads OU. The management account holds only org-level automation and billing configuration.
- Detection:
  ```bash
  aws resourcegroupstaggingapi get-resources \
    --profile management-account-profile \
    --query "ResourceTagMappingList[*].ResourceARN"
  # Any compute/storage/database ARN here is a finding
  ```
- Impact: Loss of organizational governance; blast radius = entire org.
- Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices_mgmt-acct.html (accessed 2026-08-26)

---

**Anti-Pattern: No Organization CloudTrail Trail**
- Risk Level: CRITICAL
- Why: Without an organization trail, member accounts that don't individually configure CloudTrail have zero API audit logging. An attacker can operate undetected in any unlogged account. Framework pillar: Security, Operational Excellence.
- ❌ Wrong: Relying on account-level CloudTrail trails in each member account (inconsistently applied); no trail in the management account.
- ✅ Correct: Create one organization trail from the management account (or Security Tooling as delegated admin) covering all accounts and all Regions. Deliver to a central S3 bucket in the Log Archive account with Object Lock enabled. Enable log file validation and CMK encryption.
- Detection:
  ```bash
  aws cloudtrail describe-trails --include-shadow-trails false \
    --query "trailList[?IsOrganizationTrail==\`true\`]"
  # Expected: at least one result
  aws cloudtrail get-trail-status --name <trail-name> \
    --query "IsLogging"
  # Expected: true
  ```
- Impact: No forensic trail for incident response; compliance violation (SOC 2, PCI-DSS, HIPAA all require audit logging).
- Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/creating-trail-organization.html (accessed 2026-08-26)

---

**Anti-Pattern: SCP Allow-list without FullAWSAccess**
- Risk Level: HIGH
- Why: Removing the default `FullAWSAccess` managed SCP without replacing it with an explicit Allow-list blocks all IAM actions in affected accounts — including the actions needed to remediate the misconfiguration. AWS warns: "You should not remove the FullAWSAccess policy unless you modify or replace it with a separate policy with allowed actions." Framework pillar: Reliability, Operational Excellence.
- ❌ Wrong: Detaching `FullAWSAccess` from root/OU as a "restrictive baseline" without an explicit Allow list; applying a partial Allow-list and missing critical services.
- ✅ Correct: Use the deny-list strategy: keep `FullAWSAccess` attached at all OU levels; add targeted `Effect: Deny` statements for prohibited actions. Test policy changes in the Policy Staging OU before applying to production OUs.
- Detection:
  ```bash
  aws organizations list-policies-for-target \
    --target-id <root-or-ou-id> --filter SERVICE_CONTROL_POLICY \
    --query "Policies[?Name=='FullAWSAccess']"
  # Expected: result present at every OU level
  ```
- Impact: Complete service interruption for all workloads in the affected OU; potential inability to remediate without management account intervention.
- Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html (accessed 2026-08-26)

---

**Anti-Pattern: No RCP Data Perimeter (Resource-Side Gap)**
- Risk Level: HIGH
- Why: SCPs protect your member accounts' IAM principals from over-permissive actions. But they cannot block external principals (outside your org) from accessing your S3 buckets, KMS keys, SQS queues, or Secrets Manager secrets if those resources have permissive resource-based policies. RCPs fill this gap. Framework pillar: Security.
- ❌ Wrong: Relying solely on SCPs for data protection; assuming "nobody outside the org can access my S3" without an RCP enforcement layer.
- ✅ Correct: Attach an RCP at the organization root denying access from principals outside the org:
  ```json
  {
    "Effect": "Deny",
    "Action": "s3:*",
    "Resource": "*",
    "Condition": {
      "StringNotEqualsIfExists": {
        "aws:PrincipalOrgID": "<your-org-id>"
      },
      "BoolIfExists": {
        "aws:PrincipalIsAWSService": "false"
      }
    }
  }
  ```
  Preserve exceptions for AWS service principals using `aws:PrincipalIsAWSService`.
- Detection:
  ```bash
  aws organizations list-policies --filter RESOURCE_CONTROL_POLICY \
    --query "Policies[*].{Name:Name,Id:Id}"
  # Expected: at least one RCP beyond RCPFullAWSAccess
  ```
- Impact: External data exfiltration via confused-deputy or misconfigured resource policies; data perimeter incomplete.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_data-perimeters.html (accessed 2026-08-26)

---

**Anti-Pattern: Placing Security Services in the Wrong Delegated Admin Account**
- Risk Level: HIGH
- Why: GuardDuty, Detective, and Security Hub CSPM must share the same delegated administrator account. Misalignment breaks cross-service navigation (Security Hub finding → Detective investigation link fails). Audit Manager and Security Hub CSPM must also share the same account to collect Security Hub evidence. Framework pillar: Security, Operational Excellence.
- ❌ Wrong: Registering GuardDuty delegated admin in account A, Security Hub CSPM in account B, and Detective in account C — each managed independently.
- ✅ Correct: Register a single "Security Tooling" account as delegated administrator for GuardDuty, Security Hub CSPM, Amazon Detective, AWS Config, Amazon Macie, IAM Access Analyzer, AWS Firewall Manager, AWS Audit Manager, Amazon Inspector. Security Lake uses the Log Archive account as delegated admin (exception).
- Detection:
  ```bash
  for svc in guardduty.amazonaws.com securityhub.amazonaws.com \
    detective.amazonaws.com config.amazonaws.com; do
    echo -n "$svc: "
    aws organizations list-delegated-administrators \
      --service-principal $svc \
      --query "DelegatedAdministrators[0].Id" --output text
  done
  # Expected: same account ID for first three
  ```
- Impact: Broken security investigation workflows; evidence gaps in Audit Manager; duplicated or misrouted findings.
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/security-tooling.html (accessed 2026-08-26)

---

**Anti-Pattern: No Cost Alerting or Budget Alerts**
- Risk Level: MEDIUM
- Why: Without billing alerts, cost overruns from misconfiguration (open NAT gateways, forgotten data transfer, runaway auto-scaling) go undetected until the monthly bill arrives. Framework pillar: Cost Optimization.
- ❌ Wrong: No AWS Budgets configured; relying on monthly billing review to detect anomalies; no Cost Anomaly Detection enabled.
- ✅ Correct: Create AWS Budgets at the management account level for total org spend, per-OU spend (via cost categories), and per-service thresholds. Enable Cost Anomaly Detection with SNS notification. Use tag policies (Organizations) to enforce cost-allocation tags, ensuring granular Cost Explorer visibility.
- Detection:
  ```bash
  aws budgets describe-budgets --account-id <management-account-id> \
    --query "Budgets[*].{Name:BudgetName,Type:BudgetType}"
  # Expected: at least one budget configured
  ```
- Impact: Unexpected cost overruns; inability to chargeback to business units; regulatory findings for organizations requiring cost governance.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/cost_monitor_usage_config_tools.html (accessed 2026-08-26)

---

## Cloud-Native Design Patterns

**Pattern: Hub-Spoke Transit Gateway with Centralized Inspection**
- Category: Networking, Security
- Problem: How to route traffic between 10+ VPCs across multiple accounts while enforcing consistent security inspection without per-VPC firewall deployments.
- Solution on AWS: Deploy AWS Transit Gateway in the Network account; share via AWS RAM to all spoke accounts. Create an Inspection VPC in the Network account hosting AWS Network Firewall. Use Transit Gateway route tables to force east-west and egress traffic through the Inspection VPC before forwarding.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Routing Control | Single routing plane for all VPCs | TGW route table complexity increases with account count |
  | Security Inspection | One firewall deployment inspects all traffic | Inspection VPC is a potential bottleneck; size capacity carefully |
  | Cost | One Direct Connect/VPN attachment for entire org | $0.05/attachment-hour + $0.02/GB processed |
  | Operational | Centralized network operations team | Spoke teams depend on network team for connectivity changes |

- Source: https://aws.amazon.com/blogs/mt/scale-multi-account-architecture-aws-network-firewall-and-aws-control-tower/ (accessed 2026-08-26)

---

**Pattern: Centralized DNS with Route 53 Resolver**
- Category: Networking
- Problem: Hybrid and multi-account environments need consistent DNS resolution — on-premises hosts need to resolve AWS private hostnames and AWS services need to resolve on-premises hostnames.
- Solution on AWS: Deploy Route 53 Resolver inbound and outbound endpoints in a Shared Services VPC connected to on-premises via Direct Connect or VPN. Share the VPC via AWS RAM. Create Route 53 Profiles to distribute DNS configuration (private hosted zones, resolver rules) across VPCs without individual associations. Use conditional forwarding rules for on-premises domain resolution.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Centralization | Single DNS management point | Any outage in Shared Services VPC affects org-wide DNS |
  | PrivateLink | Endpoints resolve locally per PrivateLink requirements | Some services (EFS, PrivateLink) require per-account PHZ association |
  | Profiles | Route 53 Profiles eliminate per-VPC PHZ associations | Profiles are a newer feature; verify regional availability |

- Source: https://docs.aws.amazon.com/whitepapers/latest/hybrid-cloud-dns-options-for-vpc/scaling-dns-management-across-multiple-accounts-and-vpcs.html (accessed 2026-08-26)

---

**Pattern: Account Factory for Terraform (AFT) GitOps Account Vending**
- Category: Operational Excellence, Automation
- Problem: Manually provisioning new AWS accounts at scale is error-prone and inconsistent; each account needs baseline controls, tags, networking, and security configurations applied on creation.
- Solution on AWS: Deploy Account Factory for Terraform (AFT) with a dedicated AFT management account. Define an account request as a Terraform `.tf` file in the `aft-account-request` repository. A `git push` triggers a Step Functions pipeline that creates the account via Control Tower Account Factory, applies global customizations, then applies account-specific customizations. Supports HCP Terraform, Terraform Enterprise, and Terraform Community Edition.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Consistency | Every account gets identical baseline | Terraform state management complexity; AFT management account adds overhead |
  | Speed | Account provisioning automated via git | Initial AFT setup is non-trivial; requires Control Tower prerequisite |
  | Auditability | Git history = account provision audit trail | Requires GitOps discipline from platform team |

- Source: https://docs.aws.amazon.com/controltower/latest/userguide/aft-overview.html (accessed 2026-08-26)

---

**Pattern: Tag Policy Enforcement for Cost Allocation**
- Category: Cost Optimization, Operational Excellence
- Problem: Without standardized tags, cost allocation to business units, applications, and environments is impossible, and Cost Explorer becomes unreliable.
- Solution on AWS: Enable Tag Policies via AWS Organizations. Define required tag keys (`CostCenter`, `Environment`, `Application`, `Owner`) with approved value enumerations. Enable enforcement mode to block noncompliant tagging operations on specified resource types (EC2, RDS, S3). Activate cost allocation tags in the Billing console to surface tags in Cost Explorer and CUR. Use AWS Budgets scoped to tag-based cost categories for per-BU alerting.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Accuracy | Exact cost attribution by tag | Enforcement can break automated deployments if tags not pre-applied |
  | Governance | Prevents untagged resources from being created | Test enforcement in Policy Staging OU before org-wide rollout |
  | Visibility | Full Cost Explorer, CUR, Anomaly Detection support | Tag activation can take 24 hours to propagate |

- Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_tag-policies.html (accessed 2026-08-26)

---

## Security Architecture

**Domain: Data Perimeter Implementation**
- AWS Services: SCPs (identity-centric), RCPs (resource-centric), VPC endpoint policies (network-centric); condition keys `aws:PrincipalOrgID`, `aws:ResourceOrgID`, `aws:SourceVpc`, `aws:SourceVpce`, `aws:PrincipalIsAWSService`, `aws:ViaAWSService`
- Architecture: Implement all three perimeter axes:
  1. **Identity perimeter (RCP)**: Deny access to org resources from principals outside the org. Use `aws:PrincipalOrgID` condition. Exception: allow AWS service principals (`aws:PrincipalIsAWSService = true`) and cross-service calls (`aws:ViaAWSService = true`).
  2. **Resource perimeter (SCP)**: Deny access to resources owned outside the org from org principals. Use `aws:ResourceOrgID` condition.
  3. **Network perimeter (SCP + VPC endpoint policy)**: Deny access from networks outside approved VPCs and on-premises ranges. Use `aws:SourceVpc`, `aws:SourceVpce`, `aws:VpcSourceIp`.
  Apply starting with S3, STS, KMS, SQS, Secrets Manager (the five original RCP-supported services). Expand to additional services as RCP support grows.
- Compliance Alignment: CIS AWS Foundations Benchmark (data protection controls); AWS Security Reference Architecture data perimeter chapter; SOC 2 CC6 series (logical and physical access)
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_data-perimeters.html (accessed 2026-08-26)

---

**Domain: Preventive SCP Baseline (Deny-List)**
- AWS Services: AWS Organizations SCPs; attached to Security OU, Infrastructure OU, Workloads OU
- Architecture: Maintain `FullAWSAccess` attached at all levels. Apply additional Deny SCPs for:
  - Region restriction: deny actions in non-approved Regions (`aws:RequestedRegion` condition)
  - Root user restriction: deny all root user actions in member accounts (with narrow exceptions for root-only tasks)
  - Security service protection: deny `cloudtrail:StopLogging`, `guardduty:DeleteDetector`, `config:StopConfigurationRecorder`, `securityhub:DisableSecurityHub`
  - Privilege escalation prevention: deny `iam:CreateUser`, `iam:CreateAccessKey` (enforce IAM Identity Center-only access)
  - Leave/close protection: deny `organizations:LeaveOrganization`, `account:CloseAccount` (at root)
- Compliance Alignment: AWS Security Reference Architecture SCP recommendations; CIS Benchmark; NIST SP 800-53 AC controls
- Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps_examples.html (accessed 2026-08-26); https://github.com/aws-samples/service-control-policy-examples

---

**Domain: Control Tower Controls (Proactive + Detective)**
- AWS Services: AWS Control Tower; AWS Config rules (detective); AWS CloudFormation hooks (proactive); AWS Security Hub "Service-Managed Standard: AWS Control Tower"
- Architecture: Preventive controls (SCPs/RCPs) block non-compliant actions at the API level. Detective controls (Config rules) detect post-hoc drift and alert via Security Hub findings. Proactive controls (CloudFormation hooks) scan CloudFormation templates before provisioning — resources that fail proactive controls are not created. Apply all mandatory controls. Apply strongly recommended controls at the Workloads OU level. Test elective controls in the Policy Staging OU first. As of v4.0, mandatory controls are no longer applied by default — explicitly enable the controls required by your compliance profile.
- Compliance Alignment: Control Catalog maps 54 control objectives to 10 industry frameworks (Jun 2025 update). Controls map to: CIS, NIST, PCI-DSS, HIPAA, SOC 2, ISO 27001, and others.
- Source: https://docs.aws.amazon.com/controltower/latest/controlreference/control-behavior.html (accessed 2026-08-26)

---

## Operational Patterns

**Domain: RI and Savings Plans Governance**
- AWS Services: AWS Budgets; AWS Cost Explorer; Cost Optimization Hub (delegated admin = member account); AWS Organizations consolidated billing
- Cost Profile: Medium — requires dedicated FinOps function to manage purchasing cadence and track utilization.
- Automation: Use Cost Optimization Hub recommendations (delegated to a member FinOps account) to identify rightsizing and savings plan opportunities. Use Cost Anomaly Detection (SNS/email alerts) to detect unexpected usage spikes. Configure Budgets with SNS for threshold alerts at 80% and 100% of monthly target.
- Source: https://docs.aws.amazon.com/cost-management/latest/userguide/coh-delegated-admin.html (accessed 2026-08-26)

---

**Domain: Account Lifecycle Management**
- RTO/RPO: Account provisioning target: < 30 minutes via AFT; < 2 hours via manual Account Factory.
- AWS Services: AWS Control Tower Account Factory; Account Factory for Terraform (AFT); AWS Service Catalog; AWS Organizations CreateAccount API; Suspended OU; account closure (subject to minimum 4-day account age)
- Cost Profile: Low — no direct cost for account provisioning; operational cost in SCP/baseline maintenance per new account.
- Automation: Provision: AFT git-push pipeline. Suspend: move to Suspended OU (tightened SCPs applied via OU). Close: 4-day minimum age required; concurrent closures limited to 3 accounts.
- Source: https://docs.aws.amazon.com/controltower/latest/userguide/aft-overview.html (accessed 2026-08-26)

---

**Domain: Policy Change Management**
- AWS Services: Policy Staging OU; AWS Organizations (tag policies, SCPs, RCPs, declarative policies); AWS CloudTrail (policy change audit); AWS Config (config change tracking)
- Cost Profile: Low — operational discipline, minimal AWS service cost.
- Automation: Create a Policy Staging OU containing representative accounts from each target OU class. Attach the candidate SCP/RCP/tag policy to the Policy Staging OU only. Run integration tests. Then promote to target OUs incrementally (one OU at a time; monitor CloudWatch and Security Hub). Document all policy changes as change records linked to CloudTrail event IDs.
- Source: https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/recommended-ous-and-accounts.html (accessed 2026-08-26)

---

## Reference Architectures

**Architecture: Standard Enterprise Landing Zone**
- Context: New AWS organization; 50–5,000 accounts; standard commercial compliance requirements.
- Services Composition:

  | Layer | Account / Service | Purpose |
  |-------|-------------------|---------|
  | Org governance | Management account + AWS Organizations | Policy hierarchy; consolidated billing |
  | Identity | IAM Identity Center (Shared Services) | Federated human access; permission sets |
  | Security control plane | Security Tooling / Audit account | GuardDuty, Security Hub, Config, Macie, Inspector, Firewall Manager, Detective delegated admin |
  | Logging | Log Archive account | Immutable org trail S3; Config delivery; VPC Flow Logs |
  | Networking | Network account | Transit Gateway; centralized DNS; centralized egress + inspection VPC |
  | Shared services | Shared Services account | AMI sharing; Service Catalog; Route 53 Resolver endpoints; PrivateLink endpoints |
  | Backup | Backup account | AWS Backup delegated admin; cross-account backup vaults |
  | Workloads | Workloads OU (Prod/NonProd child OUs) | Business application accounts |
  | Experimentation | Sandbox OU | Developer free-form accounts; no prod connectivity |
  | Orchestration | AWS Control Tower | Account vending; controls library; drift detection |

- Key Decisions: Whether to use LZA for extended networking/compliance depth; whether Prod and NonProd workloads need separate OU-level SCPs; Transit Gateway vs VPC Sharing for the networking layer.
- Scaling Path: <50 accounts: start with Control Tower + manual Account Factory. 50–500 accounts: add AFT for automated account vending. >500 accounts: add LZA for declarative policy orchestration and complex networking topologies.
- Source: https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/ (April 30, 2025; accessed 2026-08-26)

---

**Architecture: Regulated Workloads (GovCloud / FedRAMP / DoD)**
- Context: US Government or DoD workloads requiring DISA CC SRG IL4/IL5 or FedRAMP High compliance; GovCloud (US) partition.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Foundation | Control Tower + LZA | LZA required for GovCloud/Secret/Top Secret partition support |
  | Network | AWS Transit Gateway (GovCloud) | GovCloud-region isolation; dedicated connectivity |
  | Logging | AWS CloudTrail + Amazon Security Lake | FIPS-compliant logging; Security Lake for centralized analytics |
  | Compliance | AWS Audit Manager + AWS Config | Evidence collection; compliance framework mapping |
  | Identity | IAM Identity Center with CAC/PIV | DoD PKI integration via external SAML IdP |

- Key Decisions: LZA is the required deployment mechanism for GovCloud and classified partitions. DISA CC SRG IL4/IL5 specifics: ⚠️ unverified in this research — verify against https://docs.aws.amazon.com/prescriptive-guidance/latest/secure-architecture-dod/lza-overview.html.
- Source: https://docs.aws.amazon.com/solutions/latest/landing-zone-accelerator-on-aws/solution-overview.html (accessed 2026-08-26)

---

## Service Equivalence Map

| Capability | AWS | Azure | GCP | OCI |
|---|---|---|---|---|
| Multi-account hierarchy | AWS Organizations (OUs) | Azure Management Groups | GCP Resource Hierarchy (Folders) | OCI Compartments |
| Policy guardrails (identity) | Service Control Policies (SCPs) | Azure Policy (Initiative) | Org Policy Constraints | OCI IAM Compartment Policies |
| Policy guardrails (resource) | Resource Control Policies (RCPs) | No direct equivalent | No direct equivalent | No direct equivalent |
| Landing zone orchestration | AWS Control Tower | Azure Landing Zone (Bicep/Terraform) | Google Cloud Landing Zone | OCI Landing Zone |
| Account vending | Account Factory / AFT | Azure subscription vending (Terraform) | GCP Project Factory | OCI Compartment provisioning |
| Centralized billing | Consolidated billing (Organizations) | Azure Enterprise Agreement / MCA | GCP Billing Account | OCI Cost Management |
| RI/Savings sharing | RI sharing, Savings Plans (consolidated) | Azure Reserved Instances (billing scope) | CUD at billing account | OCI Reserved Capacity (compartment) |
| Hub-spoke networking | AWS Transit Gateway | Azure Virtual WAN / Virtual Hub | Cloud Interconnect + Network Connectivity Center | OCI DRG + LPG |
| VPC / network isolation | Amazon VPC | Azure Virtual Network (VNet) | GCP VPC | OCI VCN |
| Cross-account service sharing | AWS Resource Access Manager (RAM) | Azure Shared Image Gallery / ARM | GCP Shared VPC | OCI Shared Compartments |
| Centralized secret management | AWS Secrets Manager | Azure Key Vault | GCP Secret Manager | OCI Vault |
| SIEM / threat detection | Amazon GuardDuty + Security Hub | Microsoft Defender for Cloud | Security Command Center | OCI Cloud Guard |
| Centralized IAM | IAM Identity Center (SSO) | Azure Entra ID (AAD) | Google Workspace / Cloud Identity | OCI Identity Domains |
| Compliance as code | AWS Config Conformance Packs | Azure Policy Initiative | Org Policy + Security Command Center | OCI Security Zones |
| Cost visibility | AWS Cost Explorer + AWS Budgets | Azure Cost Management | GCP Billing reports / Budget alerts | OCI Cost Analysis |

---

## Provider Differentiators

**AWS-unique: Resource Control Policies (RCPs)**
The resource-side authorization policy type that creates a permission ceiling on resources (not just principals). No equivalent exists in Azure, GCP, or OCI as of 2026-08-26. AWS is the only major provider that allows org-wide resource-centric guardrails enforced at the cloud-provider layer. Source: https://aws.amazon.com/blogs/aws/introducing-resource-control-policies-rcps-a-new-authorization-policy/ (Nov 13, 2024).

**AWS-unique: Declarative Policies (continuous configuration enforcement)**
AWS Declarative Policies maintain desired service configuration even as the service adds new features or APIs. The EC2/EBS/VPC declarative policy automatically covers new VPC encryption settings as AWS ships them — the policy doesn't need updating. This is architecturally distinct from a snapshot-in-time config rule. Source: https://aws.amazon.com/about-aws/whats-new/2024/12/aws-declarative-policies/ (Dec 2024).

**AWS-unique: AWS Control Tower Proactive Controls**
CloudFormation hook-based controls that prevent noncompliant resources from being provisioned — checked at template synthesis time, before any resource is created. GCP and Azure have policy enforcement at the API layer; the CloudFormation-hook integration is AWS-specific. Source: https://docs.aws.amazon.com/controltower/latest/controlreference/control-behavior.html (accessed 2026-08-26).

**AWS advantage: Breadth of Organizations-integrated services**
AWS Organizations integrates with 40+ services for delegated administration. The depth of the delegated admin pattern (single Security Tooling account administering GuardDuty, Security Hub, Config, Macie, Inspector, Detective, Firewall Manager, Audit Manager, IAM Access Analyzer simultaneously) is unmatched in Azure and GCP as of 2026.

**AWS advantage: LZA for classified partitions**
LZA natively supports GovCloud (US), Secret, and Top Secret AWS partitions — enabling consistent IaC-driven governance across commercial and classified environments. Azure and GCP have government cloud equivalents but no community-maintained open-source accelerator at this maturity level.

---

## Scenario Coverage

**Standard Case: New enterprise org with 20 initial accounts, target 200 in 2 years**
- Approach: Deploy Control Tower → provision Log Archive, Audit, Network, Shared Services accounts → configure IAM Identity Center with external IdP → set up AFT → establish foundational SCPs (deny root IAM users, deny non-approved regions, deny security service tampering) → attach org CloudTrail → configure Budgets and Cost Anomaly Detection.
- Key Decisions: Which Regions to allow (SCP `aws:RequestedRegion`); whether dev and test environments share an OU or need separate OUs with different SCPs; whether to use VPC Sharing (simpler, fewer VPCs) or Transit Gateway (more isolation, more cost) for networking.

**Edge Case: Migrating an existing standalone account into the org**
- Approach: Use Transitional OU as the landing zone for newly joined accounts. Apply a limited SCP (read-only restrictions) while assessing the account's existing resources. Do not use existing account email/root — create an IAM Identity Center permission set for access. After assessment, move to the appropriate Workloads OU. Note: account must be at least 4 days old before it can be closed; concurrent movements do not have this restriction.
- Key Decisions: Whether the account's existing resources violate the Workloads OU SCP; whether to remediate pre-existing IAM users before moving to governed OUs.

**Anti-Pattern Case: Customer wants to consolidate all development, test, and production in one AWS account for "simplicity"**
- Clarification: This is the canonical multi-account anti-pattern. Flag immediately: (1) SCPs cannot enforce environment isolation within a single account; (2) a production incident in a single-account model has unlimited blast radius; (3) IAM policies become the only isolation mechanism — IAM is not a substitute for account-level isolation. Recommend the AWS Whitepaper "Organizing Your AWS Environment Using Multiple Accounts" (April 30, 2025). At minimum, require separate Production and NonProd accounts as the starting point, with a Sandbox account for experimentation. Single-account environments that exist for budget reasons should at minimum have: separate VPCs per environment, strict IAM boundary policies, and CloudTrail logging to a separate account.

---

## Source Bibliography

All sources accessed **2026-08-26** unless otherwise noted.

| # | Source | URL | Date |
|---|--------|-----|------|
| 1 | AWS Organizations — Getting Started Concepts | https://docs.aws.amazon.com/organizations/latest/userguide/orgs_getting-started_concepts.html | Undated (stable) |
| 2 | AWS Organizations — Policies | https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies.html | Undated (stable) |
| 3 | AWS Organizations — SCPs | https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html | Undated (stable) |
| 4 | AWS Organizations — RCPs | https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_rcps.html | Undated (stable) |
| 5 | AWS Organizations — Management Account Best Practices | https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices_mgmt-acct.html | Undated (stable); July 10, 2026 auto-SCP noted |
| 6 | AWS Organizations — Service Limits | https://docs.aws.amazon.com/organizations/latest/userguide/orgs_reference_limits.html | Undated (stable) |
| 7 | AWS Whitepaper: Organizing Your AWS Environment Using Multiple Accounts | https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/ | **April 30, 2025** |
| 8 | AWS SRA — Security Tooling account | https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/security-tooling.html | Undated |
| 9 | AWS SRA — Log Archive account | https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/log-archive.html | Undated |
| 10 | AWS SRA — Management account | https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/management-account.html | Undated |
| 11 | AWS SRA — Best practices checklist | https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/checklist.html | Undated |
| 12 | IAM — Root user best practices | https://docs.aws.amazon.com/IAM/latest/UserGuide/root-user-best-practices.html | Undated |
| 13 | IAM — Data perimeters | https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_data-perimeters.html | Undated |
| 14 | IAM Identity Center — Delegated admin | https://docs.aws.amazon.com/singlesignon/latest/userguide/delegated-admin.html | Undated |
| 15 | AWS Control Tower — How it works | https://docs.aws.amazon.com/controltower/latest/userguide/how-control-tower-works.html | Undated |
| 16 | AWS Control Tower — Control behavior | https://docs.aws.amazon.com/controltower/latest/controlreference/control-behavior.html | Undated |
| 17 | AWS Control Tower — 2025 Release Notes | https://docs.aws.amazon.com/controltower/latest/userguide/2025-all.html | 2025 |
| 18 | AWS Control Tower — 2026 Release Notes | https://docs.aws.amazon.com/controltower/latest/userguide/2026-all.html | 2026 |
| 19 | AFT — Overview | https://docs.aws.amazon.com/controltower/latest/userguide/aft-overview.html | Undated; AFT v1.15.0 = July 28, 2025 |
| 20 | LZA — Solution Overview | https://docs.aws.amazon.com/solutions/latest/landing-zone-accelerator-on-aws/solution-overview.html | Undated |
| 21 | Consolidated Billing | https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/consolidated-billing.html | Undated |
| 22 | RI Discount Sharing | https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/ri-turn-off.html | Undated |
| 23 | Cost Optimization Hub — Delegated Admin | https://docs.aws.amazon.com/cost-management/latest/userguide/coh-delegated-admin.html | Undated; launched **August 2024** ⚠️ Source dated [2024-08]; core delegated admin pattern is stable but verify any new capability additions. |
| 24 | Account Tags — Cost Allocation | https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/account-tags-cost-allocation.html | What's New: **December 2025** |
| 25 | Tag Policies | https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_tag-policies.html | Undated |
| 26 | Networking — Transit Gateway | https://docs.aws.amazon.com/whitepapers/latest/building-scalable-secure-multi-vpc-network-infrastructure/transit-gateway.html | Undated |
| 27 | Networking — VPC Sharing | https://docs.aws.amazon.com/whitepapers/latest/building-scalable-secure-multi-vpc-network-infrastructure/amazon-vpc-sharing.html | Undated |
| 28 | DNS — Hybrid multi-account | https://docs.aws.amazon.com/whitepapers/latest/hybrid-cloud-dns-options-for-vpc/scaling-dns-management-across-multiple-accounts-and-vpcs.html | Undated |
| 29 | CloudTrail — Organization trails | https://docs.aws.amazon.com/awscloudtrail/latest/userguide/creating-trail-organization.html | Undated |
| 30 | CloudTrail — Security best practices | https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html | Undated |
| 31 | What's New — RCPs launch | https://aws.amazon.com/blogs/aws/introducing-resource-control-policies-rcps-a-new-authorization-policy/ | **November 13, 2024** ⚠️ Source dated [2024-11]; RCPs are GA and the launch blog describes the initial five supported services — verify current supported-service list at docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_rcps.html. |
| 32 | What's New — Declarative Policies GA | https://aws.amazon.com/about-aws/whats-new/2024/12/aws-declarative-policies/ | **December 2024** ⚠️ Source dated [2024-12]; declarative policy sub-types have expanded since launch (Bedrock, S3, Inspector, Security Hub, Shield NSD added after Dec 2024) — verify full list in current docs. |
| 33 | What's New — VPC Encryption Controls | https://aws.amazon.com/about-aws/whats-new/2026/07/vpc-encryption-controls-declarative-controls/ | **July 6, 2026** |
| 34 | What's New — Root MFA all account types | https://aws.amazon.com/about-aws/whats-new/2025/06/aws-iam-mfa-root-users-across-all-account-types/ | **June 2025** |
| 35 | SCP Examples | https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps_examples.html | Undated |
| 36 | SCP Examples GitHub repo | https://github.com/aws-samples/service-control-policy-examples | Community-maintained |
| 37 | Data Perimeter Examples GitHub repo | https://github.com/aws-samples/data-perimeter-policy-examples | Community-maintained |
| 38 | Well-Architected — Cost Monitoring Tools | https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/cost_monitor_usage_config_tools.html | Undated |
| 39 | Multi-Account Networking Prescriptive Guidance | https://docs.aws.amazon.com/prescriptive-guidance/latest/transitioning-to-multiple-aws-accounts/network-connectivity.html | Undated |

---

> **Research triangulation notes:**
> - Policy taxonomy restructure (Authorization vs Declarative replacing "Management Policies") confirmed by triangulating orgs_getting-started_concepts.html + orgs_manage_policies.html. Any skill or documentation using "management policies" as an umbrella is stale.
> - July 10, 2026 auto-SCP for console-created orgs: confirmed in both orgs_best-practices_mgmt-acct.html (agent 4) and ri-turn-off.html (agent 2). HIGH confidence.
> - Control Tower v4.0 Security OU as optional (Nov 17, 2025): confirmed via 2025 release notes. HIGH confidence.
> - LZA DoD IL4/IL5/CMMC specifics: ⚠️ unverified — cited in search results but prescriptive-guidance DoD page not directly fetched. Verify at https://docs.aws.amazon.com/prescriptive-guidance/latest/secure-architecture-dod/lza-overview.html before including in compliance-related SKILL.
> - AFT region exclusions (Spain, Zurich, Tel Aviv, UAE, Hyderabad): ⚠️ unverified — from search snippet only; verify at https://docs.aws.amazon.com/controltower/latest/userguide/aft-resources.html.
