# AWS Organizations — Multi-Account Architecture Knowledge Base

---

## Metadata

```yaml
Full_Name: "AWS Organizations — Multi-Account Architecture"
Cloud_Provider: "AWS"
Architecture_Domain: "Organization Architecture — Multi-Account Strategy"
Target_Edition: "AWS Organizations 2024"
Architecture_Context: "Enterprise multi-account environments requiring centralized governance, security guardrails, cost management, and workload isolation across organizational units"
Official_Source_URL: "https://docs.aws.amazon.com/organizations/latest/userguide/"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-05-28"
Currency_Threshold: "2027-05-28 — review required after this date due to Organizations feature evolution"
```

---

## Executive Summary

AWS Organizations is the foundational governance service for managing multiple AWS accounts as a single entity. It provides centralized account management, hierarchical organizational units (OUs), policy-based guardrails (SCPs, RCPs, declarative policies), consolidated billing, and integration with 200+ AWS services. Organizations is the control plane that enables the multi-account strategy recommended by the AWS Well-Architected Framework — where accounts serve as natural security, access, and billing boundaries. Every production AWS environment beyond a single account requires Organizations as the governance backbone.

The 2024 edition introduced **Resource Control Policies (RCPs)** — a new authorization policy type that applies resource-centric guardrails to member accounts, complementing the principal-centric SCPs. **Declarative policies** expanded significantly to include Amazon EC2 policies, Security Hub policies, Amazon Inspector policies, Amazon Bedrock policies, Amazon S3 policies, and AWS Shield Network Security Director policies. **Root access management** was introduced to centrally manage and remove root user credentials from member accounts — eliminating the need for per-account root user security. **Delegated administrator for Organizations** now allows member accounts to manage organization policies directly, reducing management account usage.

The three most critical architecture guardrails for Organizations are: (1) **never deploy workloads to the management account** — it is exempt from SCPs and its compromise grants control over the entire organization; (2) **use SCPs and RCPs as preventive guardrails attached to OUs** — not individual accounts — to enforce consistent security controls at scale; (3) **organize accounts by security and operational needs (function-based OUs), not by reporting structure** — separate production from non-production, isolate security tooling, and maintain foundational accounts (log archive, security tooling, network) independent of workload accounts.

---

## Cloud Architecture Glossary

```
Term: Organization
Definition: A collection of AWS accounts managed centrally and organized into a hierarchical tree structure with a root at the top and organizational units nested below. Each organization has one management account, zero or more member accounts, OUs, and policies. An organization enables all-features mode (recommended) or consolidated-billing-only mode.
Provider Docs Section: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_getting-started_concepts.html
Architect Usage: Create a single organization for all AWS accounts in the enterprise. Multiple organizations are rarely justified and create governance gaps. Use the all-features mode to enable SCPs, RCPs, and service integrations.
Common Confusion: An organization is NOT the same as an AWS account. An organization is a container of accounts. You cannot nest organizations within organizations — use OUs for hierarchy within a single organization.

Term: Management Account
Definition: The AWS account used to create the organization. It is the ultimate owner of the organization with final control over security, infrastructure, and finance policies. It is the payer account responsible for all consolidated charges. SCPs do NOT apply to the management account. You cannot change which account is the management account.
Provider Docs Section: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_getting-started_concepts.html
Architect Usage: Minimize resources and workloads in the management account. Use it only for organization-level operations (creating accounts, attaching policies, managing OUs). Delegate administration to member accounts wherever possible. Protect with hardware MFA on root user and break-glass IAM users.
Common Confusion: The management account is NOT exempt from RCPs on its resources (RCPs restrict what resources allow). It IS exempt from SCPs (which restrict principals). Declarative policies applied to the root DO apply to the management account. This creates an inconsistent control model that architects must understand precisely.

Term: Member Account
Definition: Any AWS account in the organization other than the management account. Member accounts can be created within the organization or invited from outside. SCPs apply to all principals within member accounts. A member account can belong to only one organization at a time.
Provider Docs Section: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_getting-started_concepts.html
Architect Usage: All workloads, shared services, security tooling, and infrastructure should reside in member accounts — never in the management account. Use dedicated accounts for security (log archive, security tooling), networking (transit gateway, DNS), and shared services (CI/CD, artifact registries).
Common Confusion: A member account is NOT less privileged than the management account for its own resources. Within its own boundary, a member account's administrators have full control — bounded only by SCPs/RCPs applied by the organization.

Term: Organizational Unit (OU)
Definition: A group of AWS accounts within an organization. OUs can contain other OUs, creating a hierarchy up to 5 levels deep (including root). Policies attached to an OU are inherited by all accounts and child OUs beneath it.
Provider Docs Section: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_getting-started_concepts.html
Architect Usage: Use OUs to group accounts by function and required controls — not by team or reporting structure. Apply SCPs/RCPs at the OU level for consistent governance. Recommended OUs: Security, Infrastructure, Workloads (with Prod/Non-Prod child OUs), Sandbox, Suspended, Policy Staging.
Common Confusion: OUs are NOT the same as resource groups or tags. OUs are governance constructs that determine policy inheritance. An account can be in only ONE OU at a time (it cannot be in multiple OUs simultaneously). Moving an account between OUs changes its effective policies immediately.

Term: Root (Administrative Root)
Definition: The top-most container in the organization hierarchy. The root is created automatically when you create an organization. All OUs and accounts exist under the root. Policies attached to the root apply to all OUs and member accounts (SCPs) or all entities including the management account (declarative policies).
Provider Docs Section: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_getting-started_concepts.html
Architect Usage: Attach organization-wide policies to the root for universal enforcement. The default SCP (FullAWSAccess) is attached to the root — if you remove it, all member accounts lose all permissions. Add deny-based SCPs to the root for organization-wide guardrails (e.g., deny unused regions, deny disabling CloudTrail).
Common Confusion: The administrative root is NOT the same as the root user of an account. The administrative root is a structural element of the organization hierarchy. The root user is the identity that owns an individual AWS account.

Term: Service Control Policy (SCP)
Definition: An authorization policy that defines the maximum permissions available to IAM principals (users and roles) in member accounts. SCPs do NOT grant permissions — they only restrict what identity-based and resource-based policies can effectively grant. SCPs use IAM policy syntax with Allow and Deny statements. The maximum SCP size is 5120 characters. Up to 5 SCPs can be attached per entity.
Provider Docs Section: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html
Architect Usage: Use deny-based SCPs for preventive guardrails: deny unused regions, deny disabling security services (CloudTrail, GuardDuty, Config), deny creation of IAM users with console access, deny public S3 bucket policies. Apply to OUs, not individual accounts. Test in a Policy Staging OU before production rollout.
Common Confusion: SCPs do NOT apply to the management account. SCPs do NOT affect service-linked roles. SCPs apply to ALL principals in member accounts including the root user (except certain root-user-only actions like closing an account). An SCP deny overrides all identity-based allows — there is no way to "bypass" an SCP from within the member account.

Term: Resource Control Policy (RCP)
Definition: An authorization policy (introduced 2024) that defines the maximum permissions available for resources in member accounts. RCPs restrict what resource-based policies can grant, regardless of the requesting principal's account. RCPs complement SCPs by controlling the resource side of the access equation. Maximum size: 5120 characters, up to 5 per entity.
Provider Docs Section: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_rcps.html
Architect Usage: Use RCPs to prevent data exfiltration by ensuring resources (S3 buckets, KMS keys, SQS queues) cannot grant access to principals outside the organization. RCPs enforce resource-level controls even when external principals attempt access — closing a gap that SCPs alone cannot address (SCPs only constrain principals within the org).
Common Confusion: RCPs are NOT the same as SCPs. SCPs constrain what principals can DO; RCPs constrain what resources can ALLOW. An external principal accessing a resource in a member account is affected by RCPs (which are on the resource) but NOT by SCPs (which are on principals inside the org). This is the key reason RCPs were introduced.

Term: Delegated Administrator
Definition: A member account designated by the management account to manage specific AWS services or Organizations policies on behalf of the organization. Two types exist: (1) Delegated administrator for Organizations — can manage and attach organization policies; (2) Delegated administrator for an AWS service — has administrative permissions for a specific integrated service.
Provider Docs Section: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_delegate_policies.html
Architect Usage: Register delegated administrators to reduce management account usage. Common delegations: Security Hub (to security tooling account), GuardDuty (to security tooling account), CloudFormation StackSets (to infrastructure account), IAM Access Analyzer (to security account). This follows the principle of least privilege for the management account.
Common Confusion: A delegated administrator does NOT have all management account privileges. It has administrative permissions only for its designated service. Different services can have different delegated administrator accounts. Not all services support delegated administration — verify per-service.

Term: Trusted Access
Definition: The mechanism by which an AWS service is authorized to perform operations across all accounts in the organization. When you enable trusted access for a service, Organizations creates a service-linked role in each member account that the service uses to perform cross-account operations.
Provider Docs Section: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_integrate_services.html
Architect Usage: Enable trusted access via the service's own console/API (not the Organizations console) to ensure proper initialization. Required for services like CloudTrail (organization trail), Config (aggregator), GuardDuty (organization detector), Security Hub (organization), and CloudFormation StackSets (service-managed).
Common Confusion: Trusted access is NOT the same as cross-account role assumption. Trusted access is a service-to-service integration at the organization level. It creates service-linked roles (which are exempt from SCPs). Enabling trusted access does NOT automatically configure the service — you still need to set up the service features.

Term: AWS Control Tower
Definition: A managed service that automates the setup and governance of a secure, multi-account AWS environment (landing zone) based on best practices established by AWS. It uses Organizations, SCPs, AWS Config rules, and IAM Identity Center to establish and enforce governance at scale. Control Tower provides pre-packaged controls (preventive, detective, proactive).
Provider Docs Section: https://docs.aws.amazon.com/controltower/latest/userguide/what-is-control-tower.html
Architect Usage: Use Control Tower as the implementation mechanism for your multi-account strategy. It provisions the recommended OU structure (Security, Sandbox), creates foundational accounts (Log Archive, Audit/Security Tooling), configures AWS Config and CloudTrail organization-wide, and provides a control catalog. Extend with customizations (Customizations for Control Tower — CfCT).
Common Confusion: Control Tower is NOT a replacement for Organizations — it is built ON TOP of Organizations. You cannot use Control Tower without Organizations. Control Tower manages a landing zone; Organizations manages the underlying account hierarchy and policies. Control Tower controls are implemented as SCPs, Config rules, or CloudFormation hooks.

Term: Consolidated Billing
Definition: A feature of Organizations that combines the billing from all member accounts into a single payer (the management account). All accounts in the organization share volume pricing discounts, Reserved Instance/Savings Plans benefits, and receive a single invoice.
Provider Docs Section: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_getting-started_concepts.html
Architect Usage: Consolidated billing is always active in an organization. Use it for volume discount optimization (S3, EC2, data transfer). Use cost allocation tags to track spending per account, team, and workload. Enable AWS Cost Explorer and set up billing alarms per account or OU. Consider dedicated billing accounts for chargeback models.
Common Confusion: Consolidated billing does NOT mean all accounts share the same payment method configuration. The management account is the payer, but individual accounts can still track their own costs. Reserved Instances and Savings Plans are shared across the organization by default — use RI/SP sharing preferences to control this.

Term: Root Access Management
Definition: A 2024 feature that enables the management account to centrally manage and remove root user credentials from member accounts. When enabled, newly created member accounts have no root user credentials by default (secure-by-default). The management account can perform privileged root-user tasks on member accounts without the member account needing root credentials.
Provider Docs Section: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_root-user.html#id_root-user-access-management
Architect Usage: Enable root access management to eliminate the attack surface of per-account root credentials. Use privileged sessions from the management account for emergency operations (fixing misconfigured S3 bucket policies, deleting misconfigured SQS resource policies, allowing root credential recovery for specific accounts when needed).
Common Confusion: Root access management does NOT remove the root user concept — it removes the credentials (password, access keys, MFA) for member account root users. The management account root user still exists and requires its own protection. This feature requires Organizations with all features enabled.

Term: Declarative Policy
Definition: An organization policy type that centrally configures and manages AWS service behavior across accounts. Unlike SCPs (which deny actions), declarative policies directly set configuration state. Types include: EC2 policies, Backup policies, Tag policies, Chat application policies, AI services opt-out policies, Security Hub policies, Inspector policies, Bedrock policies, S3 policies, and Upgrade rollout policies.
Provider Docs Section: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_declarative_policies.html
Architect Usage: Use declarative policies for configuration enforcement (not permission restriction). Tag policies enforce tagging standards. Backup policies enforce backup schedules. EC2 declarative policies enforce instance configuration. These complement SCPs/RCPs — use SCPs to deny actions, use declarative policies to enforce configuration state.
Common Confusion: Declarative policies DO support inheritance (child OUs inherit from parents) and DO apply to the management account when attached to root. They have different size limits (10,000 characters) and attachment limits (10 per entity) compared to SCPs/RCPs (5120 characters, 5 per entity). They are NOT authorization policies — they don't affect IAM evaluation logic.
```

---

## Architecture Guardrails

### ✅ Mandatory Patterns

**Single Organization for All Accounts**
- Pillar Alignment: Security — AWS Account Management and Separation (SEC01)
- Why: "We recommend creating a single organization and managing all your accounts within this organization" — AWS Organizations Best Practices. A single organization provides consistent policy enforcement, unified billing, cross-account service integration, and eliminates governance gaps between unmanaged accounts.
- AWS Services: AWS Organizations, AWS Control Tower, IAM Identity Center
- Architecture Decision:
  Create one organization with all-features enabled. All AWS accounts — production, non-production, sandbox, security, infrastructure — belong to this organization. Use OUs for hierarchical grouping. Never operate accounts outside the organization for production workloads.
- Verification:
  ```bash
  # List all accounts in the organization
  aws organizations list-accounts --query 'Accounts[*].[Id,Name,Status,JoinedMethod]' --output table
  # Verify all-features is enabled
  aws organizations describe-organization --query 'Organization.FeatureSet'
  ```
- Trade-offs: Single blast radius for organization-level misconfigurations (mitigate with delegated administration and separation of duties); management account becomes single point of governance control (mitigate with hardware MFA, break-glass procedures, and CloudTrail monitoring).
- Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices.html

---

**No Workloads in the Management Account**
- Pillar Alignment: Security — SEC01-BP01: Separate workloads using accounts
- Why: "We recommend that you limit access to an organization's management account... SCPs do not apply to the management account" — AWS Organizations Best Practices. The management account is exempt from SCPs, making any workload deployed there ungovernable by organizational guardrails. Its compromise grants control over the entire organization.
- AWS Services: AWS Organizations, AWS Control Tower, Delegated Administrators
- Architecture Decision:
  The management account contains ONLY: organization management configuration, break-glass IAM users with hardware MFA, billing configuration, and organization-level CloudTrail. All other workloads — including security tooling, CI/CD, shared services — reside in dedicated member accounts. Use delegated administrators for services that support it.
- Verification:
  ```bash
  # Check for unexpected resources in management account
  aws resourcegroupstaggingapi get-resources --query 'ResourceTagMappingList[*].ResourceARN' --output text | wc -l
  # List EC2 instances (should be zero)
  aws ec2 describe-instances --query 'Reservations[*].Instances[*].[InstanceId,State.Name]' --output table
  # List Lambda functions (should be minimal/zero)
  aws lambda list-functions --query 'Functions[*].FunctionName' --output text
  ```
- Trade-offs: Requires delegated administration setup for each integrated service; some services historically required management account operations (decreasing over time); increases the total number of accounts needed.
- Source: https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/design-principles-for-your-multi-account-strategy.html

---

**SCPs as Preventive Guardrails at the OU Level**
- Pillar Alignment: Security — Permissions Management (SEC03)
- Why: "Where feasible, we recommend that you apply security controls (for example, SCPs) to OUs instead of accounts so that you can more efficiently manage the distribution of controls" — AWS Multi-Account Strategy Design Principles. SCPs at the OU level ensure consistent enforcement as accounts are added or moved.
- AWS Services: AWS Organizations (SCPs), AWS Control Tower (Controls)
- Architecture Decision:
  Attach deny-based SCPs to OUs (not individual accounts) for: denying access to unused AWS regions, denying disabling of CloudTrail/Config/GuardDuty, denying creation of IAM users with console passwords, denying public S3 bucket access, denying leaving the organization. Use the default FullAWSAccess SCP at root and add explicit deny policies at appropriate OU levels. Test all SCPs in a Policy Staging OU before production deployment.
- Verification:
  ```bash
  # List SCPs attached to a specific OU
  aws organizations list-policies-for-target --target-id ou-xxxx-xxxxxxxx --filter SERVICE_CONTROL_POLICY --query 'Policies[*].[Name,Id]' --output table
  # View effective policies for an account
  aws organizations describe-effective-policy --policy-type SERVICE_CONTROL_POLICY --target-id 123456789012
  ```
- Trade-offs: SCP size limit (5120 chars) constrains policy complexity — may need multiple SCPs per OU; overly restrictive SCPs can block legitimate operations and are difficult to debug (no explicit "access denied by SCP" error message in standard IAM errors); SCP changes are eventually consistent and may take minutes to propagate.
- Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html

---

**Enable Root Access Management**
- Pillar Alignment: Security — Identity Management (SEC02)
- Why: "Enable root access management to help you monitor and remove root user credentials for member accounts. Root access management prevents recovery of root user credentials, improving account security" — AWS Organizations Best Practices 2024. Eliminates per-account root credential attack surface.
- AWS Services: AWS Organizations, IAM (Root Access Management)
- Architecture Decision:
  Enable root access management in the organization. Remove root user credentials from all member accounts. Newly created accounts will have no root credentials by default. Use privileged sessions from the management account for emergency root-level tasks (misconfigured bucket policies, misconfigured SQS policies, credential recovery).
- Verification:
  ```bash
  # Check if root access management is enabled
  aws iam list-organization-features
  # Check root credential status for member accounts
  aws iam get-account-summary --query 'SummaryMap.AccountMFAEnabled'
  ```
- Trade-offs: Dependency on management account availability for emergency root operations; requires clear operational runbooks for privileged session usage; teams lose ability to independently recover their account root access without management account intervention.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_root-user.html#id_root-user-access-management

---

**OU Structure Based on Function, Not Reporting**
- Pillar Alignment: Operational Excellence — OPS01 (Organization)
- Why: "We recommend that you organize accounts using OUs based on function, compliance requirements, or a common set of controls rather than mirroring your organization's reporting structure" — AWS Multi-Account Strategy. Reporting structures change frequently; security and operational requirements are more stable.
- AWS Services: AWS Organizations (OUs), AWS Control Tower (Landing Zone)
- Architecture Decision:
  Implement the AWS recommended OU structure:
  - **Security OU** (foundational): Log Archive account, Security Tooling account
  - **Infrastructure OU** (foundational): Network account (Transit Gateway, DNS), Shared Services account
  - **Workloads OU** (application): Child OUs for Prod and Non-Prod, one account per workload or small set of related workloads
  - **Sandbox OU** (experimental): Individual developer/team exploration accounts with aggressive cost controls
  - **Suspended OU** (procedural): Deactivated/quarantined accounts with deny-all SCP
  - **Policy Staging OU** (procedural): Test SCPs/RCPs before production rollout
- Verification:
  ```bash
  # List all OUs under root
  aws organizations list-roots --query 'Roots[0].Id' --output text | xargs -I {} aws organizations list-organizational-units-for-parent --parent-id {} --query 'OrganizationalUnits[*].[Name,Id]' --output table
  ```
- Trade-offs: More complex initial setup; requires clear account-to-OU mapping documentation; OU restructuring after initial deployment can disrupt policy inheritance; teams accustomed to "their own OU" may resist function-based grouping.
- Source: https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/recommended-ous-and-accounts.html

---

**Consolidated CloudTrail Organization Trail**
- Pillar Alignment: Security — Detection (SEC04)
- Why: An organization trail logs all API activity across all member accounts into a centralized, tamper-proof log archive. Member accounts cannot disable or modify the organization trail, ensuring audit completeness regardless of individual account administrator actions.
- AWS Services: AWS CloudTrail (Organization Trail), S3 (Log Archive bucket), KMS (encryption), CloudWatch Logs
- Architecture Decision:
  Create an organization trail from the management account (or delegated administrator). Route all logs to a dedicated Log Archive account's S3 bucket with: bucket policy denying deletion, KMS encryption with key policy restricting access to security team, S3 Object Lock (WORM) for compliance, lifecycle policies for tiered storage. Enable CloudTrail Lake for SQL-based analysis across the organization.
- Verification:
  ```bash
  # List organization trails
  aws cloudtrail describe-trails --query 'trailList[?IsOrganizationTrail==`true`].[Name,S3BucketName,IsMultiRegionTrail]' --output table
  # Verify trail is logging
  aws cloudtrail get-trail-status --name org-trail --query '[IsLogging,LatestDeliveryTime]'
  ```
- Trade-offs: S3 storage costs scale with organization activity; cross-region trails increase data transfer costs; CloudTrail Lake queries incur per-GB scanned charges; large organizations may generate TBs of logs monthly.
- Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/creating-trail-organization.html

---

### ⚠️ Architectural Decisions

**Account Strategy: Few Large Accounts vs Many Small Accounts**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | One account per workload | Organizations + Control Tower | Security isolation, blast radius containment, independent scaling | Operational simplicity, fewer cross-account integrations | Production workloads with independent teams, compliance-sensitive environments |
  | Shared accounts per environment | Organizations | Simplicity, reduced account management overhead | Security isolation, granular cost attribution | Early-stage startups, small teams, non-regulated workloads |
  | One account per microservice | Organizations + Account Factory | Maximum isolation, independent deployment | Extreme operational complexity, networking challenges | Large enterprises with mature platform teams, strict compliance |

- Cost Profile: AWS does not charge per account. Costs come from operational overhead (managing more accounts) and cross-account data transfer. More accounts = better volume discount aggregation via consolidated billing.
- Lock-in Assessment: Account structure is reversible but expensive to restructure. Moving workloads between accounts requires data migration, IAM reconfiguration, and networking changes. Plan OU structure carefully before account proliferation.
- Architect Instruction: "Ask 'How many independent teams will operate workloads, and what is the compliance boundary?' when deciding account-per-workload vs shared accounts"
- Source: https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/design-principles-for-your-multi-account-strategy.html

---

**Governance Model: Control Tower vs Custom Organizations Setup**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | AWS Control Tower | Control Tower + Organizations | Speed to governance, pre-built controls, Account Factory | Customization flexibility, fine-grained policy control | Organizations adopting AWS, standard governance needs, teams without deep Organizations expertise |
  | Custom Organizations Setup | Organizations + CloudFormation/Terraform | Full control over policies, custom OU structures, non-standard requirements | Time to implement, ongoing maintenance, requires deep expertise | Large enterprises with existing governance tools, non-standard compliance, organizations with mature platform engineering |
  | Control Tower + Customizations (CfCT) | Control Tower + CfCT pipeline | Balance of speed and customization, extensible | Complexity of two systems, CfCT learning curve | Organizations needing standard baseline plus custom extensions |

- Cost Profile: Control Tower is free (you pay for underlying services: Config rules, CloudTrail, S3). Custom setup requires engineering investment for automation.
- Lock-in Assessment: Control Tower can be deregistered but leaves artifacts (Config rules, SCPs, roles) that require cleanup. Custom Organizations setup is fully portable. CfCT adds a CodePipeline dependency.
- Architect Instruction: "Ask 'Does the organization have existing IaC for governance, and are there non-standard compliance requirements that Control Tower controls cannot satisfy?' when deciding governance model"
- Source: https://docs.aws.amazon.com/controltower/latest/userguide/what-is-control-tower.html

---

**Policy Strategy: SCPs Only vs SCPs + RCPs**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | SCPs Only | Organizations (SCPs) | Simplicity, well-understood model | Cannot prevent external principals from accessing org resources via resource policies | Internal-only workloads, no cross-account resource sharing with external parties |
  | SCPs + RCPs | Organizations (SCPs + RCPs) | Complete coverage — principal-side AND resource-side controls | Increased policy complexity, newer feature with less community experience | Organizations sharing resources externally, preventing data exfiltration, ensuring resources cannot grant access outside the org |

- Cost Profile: No additional cost — both are free features of Organizations.
- Lock-in Assessment: Both are Organizations-native. No portability concerns beyond AWS dependency.
- Architect Instruction: "Ask 'Do any workloads use resource-based policies to grant access to principals outside the organization?' when evaluating whether RCPs are needed"
- Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_rcps.html

---

### 🚫 Anti-Patterns

**Deploying Production Workloads in the Management Account**
- Risk Level: CRITICAL
- Why: The management account is exempt from SCPs — any workload deployed there operates without organizational guardrails. Compromise of the management account grants administrative control over the entire organization (creating/deleting accounts, modifying policies, removing members). Violates SEC01 — Separate workloads using accounts.
- Instead: Deploy all workloads in dedicated member accounts. Use delegated administrators for service management. Keep the management account minimal — only organization governance operations.
- Detection:
  ```bash
  # Check for compute resources in management account
  aws ec2 describe-instances --query 'Reservations[*].Instances[*].InstanceId' --output text
  aws lambda list-functions --query 'Functions[*].FunctionName' --output text
  aws ecs list-clusters --output text
  ```
- Impact: Full organization compromise if management account is breached; ungovernable workloads operating outside SCP boundaries; mixed billing that obscures governance costs from workload costs.
- Source: https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/design-principles-for-your-multi-account-strategy.html

---

**Single Account for All Environments (Prod + Dev + Staging)**
- Risk Level: HIGH
- Why: No security boundary between environments. A developer with access to deploy code in dev can potentially access production data. Blast radius of any misconfiguration spans all environments. Cost attribution between environments is impossible without granular tagging discipline. Violates SEC01 — "Separate production from non-production workloads."
- Instead: Use separate accounts for production and non-production. At minimum: one Production account and one Non-Production account per workload. Group under Workloads OU with appropriate child OUs (Prod OU, Non-Prod OU) for differentiated SCP policies.
- Detection:
  ```bash
  # Check if resources with "prod" and "dev" tags coexist in same account
  aws resourcegroupstaggingapi get-resources --tag-filters Key=Environment --query 'ResourceTagMappingList[*].Tags[?Key==`Environment`].Value' --output text | sort | uniq -c
  ```
- Impact: Cross-environment data exposure; accidental production changes from development activity; compliance violations (PCI-DSS, SOC2 require environment separation); impossible cost optimization per environment.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_securely_operate_multi_accounts.html

---

**Organizing OUs by Reporting Structure (Team/Department OUs)**
- Risk Level: MEDIUM
- Why: Organizational reporting structures change frequently (reorgs, acquisitions, team splits). OU-attached policies must be re-evaluated and potentially migrated with every reorg. Teams in the same department may have vastly different security requirements. This creates policy sprawl and inconsistent governance.
- Instead: Organize by function and required controls: Security OU, Infrastructure OU, Workloads OU (with Prod/Non-Prod children), Sandbox OU. Use tags (Team, Department, CostCenter) on accounts for organizational attribution without structural coupling.
- Detection: Review OU names — if they match department names (Marketing OU, Engineering OU, Finance OU) rather than functional names (Security OU, Workloads OU, Infrastructure OU), this anti-pattern is present.
- Impact: Governance drift during reorgs; inconsistent security controls across functionally similar workloads in different department OUs; increased SCP maintenance burden; difficulty applying uniform compliance controls.
- Source: https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/design-principles-for-your-multi-account-strategy.html

---

**Using Wildcard Allow SCPs Instead of Deny-Based SCPs**
- Risk Level: HIGH
- Why: SCPs that use explicit Allow statements (allowlisting services) are brittle — every new AWS service must be explicitly added to the SCP before accounts can use it. This blocks innovation and creates operational bottlenecks. The recommended pattern is to keep the default FullAWSAccess and add targeted Deny statements for guardrails.
- Instead: Maintain the default FullAWSAccess SCP. Add deny-based SCPs for specific guardrails: deny unused regions, deny disabling security services, deny specific high-risk actions. This approach is additive (new services work immediately) and targeted (only specific anti-patterns are blocked).
- Detection:
  ```bash
  # Check for SCPs that use Allow without the default FullAWSAccess
  aws organizations list-policies --filter SERVICE_CONTROL_POLICY --query 'Policies[*].[Name,Id]' --output text | while read name id; do
    aws organizations describe-policy --policy-id $id --query 'Policy.Content' --output text | grep -l '"Effect": "Allow"'
  done
  ```
- Impact: Blocked access to new AWS services; operational delays as teams wait for SCP updates; shadow IT as teams work around restrictions; innovation slowdown.
- Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps_strategies.html

---

**No Suspended OU for Deactivated Accounts**
- Risk Level: MEDIUM
- Why: Accounts that should be deactivated but remain in active OUs retain access to organization resources and may have running workloads incurring costs. Without a Suspended OU with a deny-all SCP, deactivated accounts cannot be effectively quarantined before final closure (which has a 90-day waiting period).
- Instead: Create a Suspended OU with an SCP that denies all actions (`"Effect": "Deny", "Action": "*", "Resource": "*"`). Move accounts to the Suspended OU immediately when they should be deactivated. After the waiting period, close the account. This prevents any activity while maintaining billing visibility.
- Detection: Check for accounts marked for deactivation that still reside in active workload OUs.
- Impact: Continued cost accrual from orphaned resources; potential security risk from unmonitored accounts; compliance gaps from ungoverned accounts.
- Source: https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/recommended-ous-and-accounts.html

---

## Cloud-Native Design Patterns

**Landing Zone Pattern**
- Category: Organization | Governance
- Problem: New AWS environments lack foundational governance — no account structure, no security baseline, no centralized logging, no identity federation. Each team creates ad-hoc accounts without consistent controls.
- Solution on AWS:
  Deploy a landing zone using AWS Control Tower (or custom automation) that provisions: the organization with recommended OU structure, foundational accounts (Log Archive, Security Tooling, Network), organization CloudTrail trail, AWS Config organization aggregator, IAM Identity Center with permission sets, and baseline SCPs. Use Account Factory (Control Tower) or Service Catalog / Terraform for account vending with pre-configured baselines.
- Services Used: AWS Organizations, AWS Control Tower, IAM Identity Center, CloudTrail, AWS Config, Service Catalog, CloudFormation StackSets
- When to Apply: Any organization moving beyond 2-3 AWS accounts; before first production workload deployment; when compliance requirements mandate centralized governance.
- When NOT to Apply: Single-account experimentation; personal learning environments; temporary proof-of-concepts that will be destroyed.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Security | Consistent baseline across all accounts | Initial investment in automation and policy design |
  | Agility | Self-service account provisioning | Governance overhead for policy changes |
  | Compliance | Auditable, repeatable infrastructure | Rigidity in non-standard requirements |

- Complements: Multi-Account Strategy, Hub-Spoke Networking, Centralized Logging
- Source: https://docs.aws.amazon.com/controltower/latest/userguide/what-is-control-tower.html

---

**Account Vending Pattern**
- Category: Organization | Automation
- Problem: Manual account creation is slow, inconsistent, and error-prone. Teams wait days/weeks for accounts. Accounts lack baseline security configuration. No repeatable process for account lifecycle.
- Solution on AWS:
  Implement automated account vending via Control Tower Account Factory, AWS Service Catalog, or custom pipelines (Step Functions + Organizations API). Each vended account receives: VPC with standard CIDR from IPAM, IAM roles for federation, CloudTrail and Config enabled, security baseline (GuardDuty, Security Hub enrolled), budget alerts, and tagging baseline. Account requests flow through an approval workflow (ServiceNow, Jira, or custom).
- Services Used: AWS Organizations (CreateAccount API), Control Tower Account Factory, Service Catalog, CloudFormation StackSets, Step Functions, IPAM
- When to Apply: Organizations with more than 10 accounts; teams requesting new accounts regularly; compliance requirements for consistent account baselines.
- When NOT to Apply: Organizations with fewer than 5 static accounts; environments where accounts are created once and never changed.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Speed | Minutes to provision vs days | Automation development and maintenance |
  | Consistency | Every account meets baseline | Less flexibility for one-off requirements |
  | Governance | Full audit trail of account creation | Approval workflow may slow urgent requests |

- Complements: Landing Zone, Infrastructure as Code, GitOps
- Source: https://docs.aws.amazon.com/controltower/latest/userguide/account-factory.html

---

**Guardrail Inheritance Pattern**
- Category: Security | Governance
- Problem: Applying security policies account-by-account doesn't scale. New accounts may miss critical guardrails. Policy updates require touching every account individually.
- Solution on AWS:
  Design an OU hierarchy where policies are attached at the appropriate OU level and inherited downward. Root-level SCPs enforce organization-wide invariants (deny unused regions, deny disabling audit). Workload OU SCPs enforce workload-specific constraints. Prod child OU has stricter policies than Non-Prod child OU. When an account is placed in an OU, it immediately inherits all policies from root through its OU path. Moving an account between OUs instantly changes its effective policies.
- Services Used: AWS Organizations (SCPs, RCPs, Declarative Policies), Control Tower (Controls)
- When to Apply: Any multi-account environment with differentiated security requirements between account groups.
- When NOT to Apply: Flat organizations with identical requirements for all accounts (rare in practice).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Scalability | New accounts auto-inherit correct policies | Policy debugging requires understanding inheritance chain |
  | Consistency | Impossible to have ungoverned accounts | Accidental OU moves can break workloads |
  | Maintainability | Change policy once, propagates everywhere | Deep hierarchies increase cognitive load |

- Complements: Landing Zone, SCP Strategy, Policy Staging OU
- Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_inheritance_auth.html

---

## Security Architecture

**Organization-Level Identity Governance**
- AWS Services: IAM Identity Center, Organizations (SCPs), IAM (Permissions Boundaries), AWS SSO
- Architecture:
  IAM Identity Center is deployed in the management account (or delegated administrator account) and federated to an external IdP (Okta, Entra ID, Ping). Permission sets define role-level access and are assigned to groups for specific accounts. SCPs at the OU level define the ceiling of what any principal can do. Permission boundaries on roles created by delegated administrators prevent privilege escalation. Break-glass IAM users exist only in the management account with hardware MFA.
- Compliance Alignment: SOC2 CC6.1 (Logical Access), HIPAA § 164.312(d) (Person or Entity Authentication), PCI-DSS Requirement 7 (Restrict access)
- Source: https://docs.aws.amazon.com/singlesignon/latest/userguide/what-is.html

---

**Cross-Account Security Monitoring**
- AWS Services: GuardDuty (organization detector), Security Hub (organization), IAM Access Analyzer (organization), AWS Config (organization aggregator), CloudTrail (organization trail)
- Architecture:
  Designate a Security Tooling account as delegated administrator for GuardDuty, Security Hub, IAM Access Analyzer, and Config. This account has read-only security visibility across all member accounts without requiring management account access. GuardDuty detects threats across accounts. Security Hub aggregates findings from GuardDuty, Config, Inspector, and third-party tools. Access Analyzer identifies external access paths and unused permissions. Config evaluates resource compliance against rules deployed via organization conformance packs.
- Compliance Alignment: SOC2 CC7.2 (System Monitoring), PCI-DSS Requirement 10 (Track and Monitor Access), HIPAA § 164.312(b) (Audit Controls)
- Source: https://docs.aws.amazon.com/securityhub/latest/userguide/designating-orgs-admin-account.html

---

**Data Perimeter with SCPs + RCPs**
- AWS Services: Organizations (SCPs, RCPs), IAM (identity policies), S3/KMS/SQS (resource policies)
- Architecture:
  Implement a three-layer data perimeter: (1) SCPs ensure principals within the org can only access resources within the org (deny actions on resources in accounts outside `aws:PrincipalOrgID`); (2) RCPs ensure resources within the org can only be accessed by principals within the org (deny access when `aws:PrincipalOrgID` doesn't match); (3) VPC Endpoints with condition keys restrict network-level access to AWS services from within VPCs only. This creates a comprehensive boundary preventing data exfiltration via both identity and resource paths.
- Compliance Alignment: SOC2 CC6.6 (Boundary Protection), PCI-DSS Requirement 1 (Network Segmentation), GDPR Art. 32 (Security of Processing)
- Source: https://docs.aws.amazon.com/whitepapers/latest/building-a-data-perimeter-on-aws/building-a-data-perimeter-on-aws.html

---

## Operational Patterns

**Organization Account Lifecycle Management**
- Operational Domain: Change Management
- AWS Services: Organizations (CreateAccount, CloseAccount), Control Tower (Account Factory), Service Catalog, Step Functions, CloudFormation StackSets
- Architecture:
  Account lifecycle: Request → Approval → Provision (vend account with baseline) → Operate (in active OU) → Decommission (move to Suspended OU, remove resources) → Close (after 90-day waiting period). Automate via Step Functions workflow triggered by Service Catalog or API. StackSets deploy baseline configurations. Tags track lifecycle stage, owner, and expiration date.
- Cost Profile: Low — Organizations and account creation are free. Cost is engineering time for automation.
- Automation: Account creation, baseline deployment, OU placement, and budget alert configuration should be fully automated. Account closure decision, data archival, and final approval are manual decision points.
- Runbook Skeleton:
  1. Receive account request with justification, owner, budget, OU target
  2. Approve based on governance criteria
  3. Execute account vending automation (CreateAccount → StackSets baseline → OU placement → Identity Center access)
  4. Notify requesting team with account details and access instructions
  5. Monitor account health via Config and Security Hub
  6. On decommission: quarantine in Suspended OU → archive data → close after 90 days
- Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_accounts.html

---

**SCP Change Management**
- Operational Domain: Change Management
- AWS Services: Organizations (SCPs), Policy Staging OU, CloudTrail, IAM Access Analyzer
- Architecture:
  SCP changes follow a staged rollout: Draft SCP → Validate syntax (Organizations policy validator) → Attach to Policy Staging OU with test accounts → Run automated tests against test accounts → Monitor for unintended denials via CloudTrail (look for AccessDenied events) → Promote to target OU after validation period. Use version control (Git) for all SCPs with PR-based review. IAM Access Analyzer custom policy checks validate policies in CI/CD pipelines.
- Cost Profile: Low — no additional service costs. Investment is in process and automation.
- Automation: SCP syntax validation, deployment to staging OU, and automated testing should be automated via CI/CD pipeline. Production promotion and rollback decisions are manual gates.
- Runbook Skeleton:
  1. Author SCP change in version control
  2. Peer review via pull request
  3. Automated validation (syntax check, Access Analyzer custom policy check)
  4. Deploy to Policy Staging OU
  5. Run integration tests from test accounts (verify expected operations succeed, verify guardrailed operations are denied)
  6. Monitor CloudTrail for unexpected AccessDenied events (48-hour observation window)
  7. Promote to production OU
  8. Monitor production CloudTrail for unintended impact
  9. Rollback procedure: detach SCP from OU (immediate effect)
- Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html

---

**FinOps at Organization Scale**
- Operational Domain: FinOps / Cost Optimization
- AWS Services: AWS Cost Explorer, AWS Budgets, Cost and Usage Reports (CUR), Cost Allocation Tags, Organizations (consolidated billing), Savings Plans, Reserved Instances
- Architecture:
  Enable cost allocation tags at the organization level (Environment, Team, Workload, CostCenter). Create AWS Budgets per account, per OU, and per tag combination with SNS alerts. Deploy Cost and Usage Reports to a dedicated analytics account with Athena for cross-organization cost analysis. Use Savings Plans and Reserved Instances shared across the organization via consolidated billing. Implement chargebacks via tag-based cost attribution. Sandbox accounts get aggressive budget alarms with automated shutdown (Lambda triggered by Budget action).
- Cost Profile: CUR storage and Athena queries incur nominal charges. Main cost is engineering time for dashboards and alerting.
- Automation: Budget alerts, cost anomaly detection (AWS Cost Anomaly Detection), and sandbox account auto-shutdown should be automated. Savings Plan purchases, RI modifications, and chargeback model decisions are manual.
- Runbook Skeleton:
  1. Review monthly Cost Explorer for trending and anomalies
  2. Investigate cost spikes per account/OU
  3. Right-size recommendations from Compute Optimizer
  4. Review Savings Plan/RI coverage and utilization
  5. Update budgets for next period
  6. Chargeback reporting to business units
- Source: https://docs.aws.amazon.com/cost-management/latest/userguide/ce-what-is.html

---

## Reference Architectures

**AWS Multi-Account Landing Zone**
- Context: Enterprise multi-account foundation for any workload type
- AWS Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/migration-aws-environment/welcome.html
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Governance | AWS Organizations | Account hierarchy, SCPs, RCPs |
  | Governance | AWS Control Tower | Automated landing zone, controls, Account Factory |
  | Identity | IAM Identity Center | Workforce federated access |
  | Security | GuardDuty + Security Hub | Threat detection and finding aggregation |
  | Audit | CloudTrail (Org Trail) | API activity logging across all accounts |
  | Compliance | AWS Config (Org) | Resource configuration compliance |
  | Networking | Transit Gateway | Hub-spoke connectivity between accounts |
  | Cost | Cost Explorer + Budgets | Organization-wide cost visibility |

- Key Decisions:
  - Control Tower vs custom governance automation
  - Number of foundational accounts (minimum: Log Archive + Security Tooling + Network)
  - OU depth (recommended: 2-3 levels max)
  - Account vending approach (Account Factory vs custom pipeline)
  - Network topology (Transit Gateway hub-spoke vs VPC peering for simple cases)
- Scaling Path:
  Start with Security OU + Workloads OU + Sandbox OU. Add Infrastructure OU when shared networking is needed. Add Deployments OU when CI/CD requires dedicated accounts. Expand Workloads OU with per-business-unit child OUs as the organization grows. Automate account vending when provisioning frequency exceeds manual capacity.
- Source: https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/recommended-ous-and-accounts.html

---

## Scenario Coverage

**Standard Case**: Enterprise adopting AWS with 5-50 initial workloads
- Approach: Deploy Control Tower landing zone with Security OU (Log Archive + Audit accounts), Infrastructure OU (Network + Shared Services accounts), Workloads OU (Prod + Non-Prod child OUs), and Sandbox OU. Federate identity via IAM Identity Center to corporate IdP. Deploy organization CloudTrail trail, Config aggregator, and GuardDuty organization detector. Apply baseline deny SCPs (unused regions, prevent disabling security services). Vend accounts via Account Factory.
- Key Decisions: Which workloads share accounts vs get dedicated accounts; VPC CIDR allocation strategy for non-overlapping ranges; permission set granularity (broad roles vs fine-grained per-service roles).

**Edge Case**: Acquisition integration — merging accounts from acquired company
- Approach: Invite acquired company's accounts into the organization. Place in Transitional OU initially (with permissive SCPs that allow current operations). Audit current posture with Config and Security Hub. Gradually align to organizational standards: apply baseline SCPs, enroll in GuardDuty, migrate identity to Identity Center. Move to appropriate Workloads OU once compliant. Use the 90-day transition period for SCP hardening.

**Anti-Pattern Case**: Team requests a standalone account outside the organization "for speed"
- Clarification: "What specific governance controls are blocking your work? Let's review the SCPs and Account Factory configuration to enable your use case within the organization rather than creating ungoverned accounts that will need retroactive compliance alignment."
