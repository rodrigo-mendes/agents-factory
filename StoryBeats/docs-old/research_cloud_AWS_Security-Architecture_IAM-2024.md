# AWS IAM — Security Architecture Knowledge Base

---

## Metadata

```yaml
Full_Name: "AWS Security Architecture — Identity & Access Management (IAM)"
Cloud_Provider: "AWS"
Architecture_Domain: "Security Architecture — Identity & Access Management"
Target_Edition: "AWS IAM 2024"
Architecture_Context: "Production workloads requiring secure identity and access management across single and multi-account AWS environments, with emphasis on least-privilege access, federation, and organizational guardrails"
Official_Source_URL: "https://docs.aws.amazon.com/IAM/latest/UserGuide/"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-05-28"
Currency_Threshold: "2027-05-28 — review required after this date due to IAM feature evolution"
```

---

## Executive Summary

AWS Identity and Access Management (IAM) is the foundational security control plane for all AWS services. It provides authentication (who you are) and authorization (what you can do) for every API call made to AWS — whether from the console, CLI, SDK, or service-to-service communication. IAM is globally available, eventually consistent, and offered at no additional charge. It supports seven distinct policy types (identity-based, resource-based, permissions boundaries, SCPs, RCPs, ACLs, and session policies) that compose through a well-defined evaluation logic to produce effective permissions. The architect's primary challenge is not granting access — it is constraining access precisely to what is needed, at scale, across organizational boundaries.

The 2024 edition introduced **Resource Control Policies (RCPs)** — a new organization-level policy type that applies permission guardrails to resources within member accounts, complementing the existing Service Control Policies (SCPs) that constrain principals. IAM Access Analyzer expanded with unused access analysis (detecting unused roles, access keys, and permissions), custom policy checks for CI/CD pipelines, and policy generation from CloudTrail activity. IAM Identity Center (successor to AWS SSO) solidified as the recommended workforce identity solution, with enhanced attribute-based access control (ABAC) support. IAM Roles Anywhere extended temporary credential delivery to workloads running outside AWS via X.509 certificates from customer PKIs.

The three most critical architecture guardrails for IAM are: (1) **all human users must authenticate via federation (IAM Identity Center or external IdP) using temporary credentials** — IAM users with long-term access keys are acceptable only for documented exceptions where federation is technically impossible; (2) **all workloads must use IAM roles for temporary credentials** — never embed access keys in application code, configuration files, or container images; (3) **every IAM policy must enforce least-privilege** — start with AWS managed policies for iteration speed, then refine to customer managed policies using IAM Access Analyzer policy generation based on actual CloudTrail access activity.

---

## Cloud Architecture Glossary

```
Term: Principal
Definition: An entity (AWS account root user, IAM user, IAM role, federated user, or service) that can make a request to perform an action on an AWS resource. Principals are authenticated by IAM before any authorization evaluation occurs.
Provider Docs Section: https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_principal.html
Architect Usage: Use the Principal element in trust policies and resource-based policies to define who can assume a role or access a resource. For identity-based policies, the principal is implicitly the entity the policy is attached to.
Common Confusion: A principal is NOT the same as an IAM user. Roles, federated users, and service principals are all principals. The AWS account root user is also a principal, distinct from any IAM user.

Term: IAM Role
Definition: An IAM identity with permission policies that determine what the identity can do in AWS. Unlike an IAM user, a role has no long-term credentials (no password, no access keys). Instead, when a principal assumes a role, AWS STS issues temporary security credentials (access key, secret key, session token) for the role session.
Provider Docs Section: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html
Architect Usage: Roles are the primary mechanism for granting access to AWS resources. Use roles for: EC2 instance profiles, Lambda execution roles, ECS task roles, cross-account access, federated user access, and service-to-service communication. Prefer roles over IAM users in all production architectures.
Common Confusion: A role is not "a user without a password." A role is assumable by multiple principals simultaneously, issues temporary credentials per session, and has a trust policy that controls who can assume it. IAM users have a 1:1 relationship with a human or workload.

Term: Trust Policy
Definition: A resource-based policy attached to an IAM role that defines which principals (users, roles, accounts, services) are allowed to assume that role. Without a valid trust policy, no entity can assume the role regardless of identity-based policies.
Provider Docs Section: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_terms-and-concepts.html
Architect Usage: Trust policies are the gatekeepers of role assumption. Always restrict the Principal element to specific accounts, roles, or services — never use wildcard (*) in production trust policies. Use conditions (aws:SourceAccount, aws:SourceArn, sts:ExternalId) to prevent the confused deputy problem.
Common Confusion: A trust policy only controls WHO can assume the role. It does NOT control what the role can do after assumption — that is determined by the role's permissions policies (identity-based policies attached to the role).

Term: Identity-Based Policy
Definition: A JSON permissions policy document attached to an IAM identity (user, group, or role) that grants or denies permissions for actions on resources. Can be managed (standalone, reusable across identities) or inline (embedded directly in a single identity).
Provider Docs Section: https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html
Architect Usage: Prefer customer managed policies over inline policies for reusability and central management. Use AWS managed policies for common use cases during initial development, then refine to least-privilege customer managed policies. Attach policies to roles (not users) for production workloads.
Common Confusion: Identity-based policies define what an identity CAN do. They do not override explicit denies from SCPs, RCPs, permissions boundaries, or resource-based policy denies. The effective permission is the intersection of all applicable policy types (except resource-based policies in certain same-account scenarios).

Term: Resource-Based Policy
Definition: A JSON policy document attached directly to an AWS resource (S3 bucket, SQS queue, KMS key, Lambda function, SNS topic, etc.) that specifies which principals can access the resource and under what conditions. Always inline — there are no managed resource-based policies.
Provider Docs Section: https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_identity-vs-resource.html
Architect Usage: Resource-based policies enable cross-account access without requiring the target account to create a role. In same-account scenarios, a resource-based policy grant is additive — it can grant access even if the identity-based policy does not explicitly allow the action. For cross-account access, both the resource-based policy AND the identity-based policy must allow the action (unless the resource-based policy directly references the principal).
Common Confusion: The IAM service itself only supports one resource-based policy type: the role trust policy. Other resource-based policies belong to their respective services (S3 bucket policies, KMS key policies, etc.) — they are not IAM policies, but they are evaluated by the IAM policy evaluation engine.

Term: Permissions Boundary
Definition: A managed policy used as a ceiling on the maximum permissions that identity-based policies can grant to an IAM entity (user or role). Permissions boundaries do not grant permissions — they only limit what can be granted by identity-based policies. The effective permissions are the intersection of identity-based policies and the permissions boundary.
Provider Docs Section: https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html
Architect Usage: Use permissions boundaries to delegate identity administration safely. Require that all roles/users created by delegated administrators have a specified permissions boundary attached. This enables decentralized team management without risking privilege escalation.
Common Confusion: A permissions boundary does NOT limit resource-based policies that specify the session ARN or user ARN directly. Implicit denies in permissions boundaries are not the same as explicit denies — resource-based policies can still grant access through certain code paths. Only explicit denies in permissions boundaries universally block access.

Term: Service Control Policy (SCP)
Definition: An AWS Organizations policy that defines the maximum permissions for IAM principals (users and roles) within member accounts. SCPs do not grant permissions — they only restrict what identity-based and resource-based policies can effectively grant to principals within the account.
Provider Docs Section: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html
Architect Usage: Use SCPs as preventive guardrails across your organization. Common patterns: deny access to unused regions, deny disabling CloudTrail/GuardDuty, deny creation of IAM users with console access, restrict specific service usage. SCPs affect all principals in the account including the root user (except for certain root-user-only actions).
Common Confusion: SCPs do NOT affect service-linked roles. SCPs apply to principals in member accounts only — they do not affect the management account. An SCP that denies an action will deny it even if an identity-based policy allows it. SCPs do not grant permissions — you still need identity-based policies.

Term: Resource Control Policy (RCP)
Definition: An AWS Organizations policy (introduced 2024) that defines the maximum permissions for resources within member accounts. RCPs restrict what identity-based and resource-based policies can grant to resources, regardless of the principal's account membership. They complement SCPs by controlling the resource side of the access equation.
Provider Docs Section: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_rcps.html
Architect Usage: Use RCPs to enforce resource-level controls across the organization — e.g., ensure S3 buckets cannot be made public, ensure KMS keys cannot be shared with untrusted accounts, ensure resources cannot grant access to principals outside the organization. RCPs apply to resources regardless of whether the accessing principal is inside or outside the organization.
Common Confusion: RCPs are NOT the same as SCPs. SCPs constrain what principals can do; RCPs constrain what resources can allow. A principal from outside the organization accessing a resource in a member account is affected by RCPs on that resource but NOT by SCPs (because SCPs only apply to principals within the org's accounts).

Term: IAM Access Analyzer
Definition: A service that analyzes resource policies, identity policies, and organizational policies to identify resources shared with external entities, unused access, and policy validation issues. Generates findings for public/cross-account access and produces least-privilege policy recommendations from CloudTrail access logs.
Provider Docs Section: https://docs.aws.amazon.com/IAM/latest/UserGuide/what-is-access-analyzer.html
Architect Usage: Enable Access Analyzer in every account and region. Use external access analyzers to detect unintended resource sharing. Use unused access analyzers to identify roles, access keys, and permissions that are no longer used. Integrate policy validation checks into CI/CD pipelines for infrastructure-as-code.
Common Confusion: IAM Access Analyzer is NOT a real-time blocker — it generates findings after the fact. For preventive controls, use SCPs/RCPs. Access Analyzer's external access analysis is free; unused access analysis and custom policy checks incur charges.

Term: IAM Identity Center (formerly AWS SSO)
Definition: The recommended AWS service for managing workforce access to multiple AWS accounts and applications. Provides centralized identity management with a built-in identity store or federation from external IdPs (Okta, Azure AD/Entra ID, OneLogin, etc.), and uses permission sets that map to IAM roles in target accounts.
Provider Docs Section: https://docs.aws.amazon.com/singlesignon/latest/userguide/what-is.html
Architect Usage: Use IAM Identity Center as the primary entry point for all human access to AWS accounts. Define permission sets (which become IAM roles in target accounts) and assign them to users/groups for specific accounts. This eliminates the need for IAM users with long-term credentials in member accounts.
Common Confusion: IAM Identity Center is NOT the same as IAM. Identity Center manages workforce identity and multi-account access. IAM manages fine-grained permissions within an account. Permission sets in Identity Center become IAM roles when provisioned to accounts — they follow standard IAM policy evaluation once assumed.

Term: IAM Roles Anywhere
Definition: A service that enables workloads running outside of AWS (on-premises servers, other cloud providers, CI/CD platforms) to obtain temporary AWS credentials by authenticating with X.509 certificates from a customer's public key infrastructure (PKI). Eliminates the need for long-term IAM access keys for external workloads.
Provider Docs Section: https://docs.aws.amazon.com/rolesanywhere/latest/userguide/introduction.html
Architect Usage: Use IAM Roles Anywhere for any workload running outside AWS that needs to call AWS APIs. Configure a trust anchor (CA certificate), create a profile mapping to an IAM role, and configure the workload to present its certificate to obtain temporary credentials. This replaces long-term access keys for hybrid/multi-cloud workloads.
Common Confusion: IAM Roles Anywhere is NOT the same as assuming a role via SAML/OIDC federation. It uses mutual TLS (X.509 certificates) rather than identity provider tokens. The certificates must chain to a trust anchor registered in IAM Roles Anywhere.

Term: Session Policy
Definition: An advanced policy passed as a parameter when programmatically creating a temporary session (via AssumeRole, AssumeRoleWithSAML, AssumeRoleWithWebIdentity, or GetFederationToken). Session policies limit the permissions for that specific session to the intersection of the identity-based policies and the session policy. They do not grant permissions on their own.
Provider Docs Section: https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html#policies_session
Architect Usage: Use session policies to create scoped-down sessions for specific operations — e.g., a deployment pipeline that assumes a broad role but passes a session policy limiting access to specific S3 buckets for that deployment. Useful for multi-tenant scenarios where the same role serves multiple tenants with different resource scopes.
Common Confusion: Session policies are NOT the same as permissions boundaries. Both limit effective permissions, but permissions boundaries are persistent (attached to the entity), while session policies are per-session (passed at assume time). A session policy's effective permissions are the intersection of the session policy AND the identity-based policy AND the permissions boundary (if set).

Term: Attribute-Based Access Control (ABAC)
Definition: An authorization strategy that uses attributes (tags) attached to principals and resources to define permissions dynamically. Instead of defining permissions per resource ARN, you define policies that grant access when the principal's tags match the resource's tags.
Provider Docs Section: https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction_attribute-based-access-control.html
Architect Usage: Use ABAC for environments with rapidly changing resources where maintaining explicit resource ARNs in policies is impractical. Define tag keys like Project, Team, Environment on both roles/users and resources. Write policies with conditions like aws:ResourceTag/Project = aws:PrincipalTag/Project. ABAC scales better than traditional RBAC for large, dynamic environments.
Common Confusion: ABAC does NOT replace IAM roles or policies — it is a strategy for writing conditions within policies. Both ABAC and RBAC (role-based access control) use IAM policies. ABAC requires disciplined tagging governance — untagged resources may be inaccessible or over-accessible depending on policy design.

Term: Policy Evaluation Logic
Definition: The algorithm AWS uses to determine whether a request is allowed or denied. The evaluation considers all applicable policy types (SCPs, RCPs, identity-based, resource-based, permissions boundaries, session policies, ACLs) and applies explicit deny > explicit allow > implicit deny ordering. Cross-account access requires allows from both the principal's account policies and the resource's account policies.
Provider Docs Section: https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html
Architect Usage: Understand that an explicit Deny in ANY applicable policy type overrides all Allows. Within a single account, resource-based policies that grant access to a specific principal ARN can provide access without a corresponding identity-based allow (for IAM users and session ARNs). Cross-account access requires explicit allows from both sides.
Common Confusion: The evaluation logic is NOT a simple union or intersection. Same-account and cross-account evaluations follow different code paths. Resource-based policies behave differently depending on whether they reference a user ARN, role ARN, or session ARN. This complexity is the #1 source of unexpected access denials in production.

Term: Confused Deputy Problem
Definition: A security vulnerability where a trusted service (the "deputy") is tricked by a less-privileged entity into performing actions on resources it should not have access to. In AWS, this typically occurs when a cross-account role's trust policy does not restrict the source of the request, allowing any customer of the trusted service to impersonate another customer.
Provider Docs Section: https://docs.aws.amazon.com/IAM/latest/UserGuide/confused-deputy.html
Architect Usage: Always use aws:SourceArn, aws:SourceAccount, or sts:ExternalId conditions in trust policies for cross-account roles. When granting a third-party service access to your resources, require an ExternalId in the trust policy to prevent other customers of that service from assuming your role.
Common Confusion: The confused deputy problem is NOT about credential theft — it is about authorization bypass through a legitimate intermediary. ExternalId is NOT a secret — it is a unique identifier that proves the caller is the expected customer of the third-party service. ExternalId should be unique per customer relationship, not per role.
```

---

## Architecture Guardrails

### ✅ Mandatory Patterns

**Federated Access for All Human Users**
- Pillar Alignment: Security — Identity Management (SEC02)
- Why: "Require human users to use federation with an identity provider to access AWS using temporary credentials" — AWS IAM Security Best Practices. Long-term credentials (passwords, access keys) are high-value theft targets, cannot be automatically rotated by the system, and create persistent access that outlives employment.
- AWS Services: IAM Identity Center, AWS STS, External IdPs (Okta, Azure AD/Entra ID, Ping, OneLogin)
- Architecture Decision:
  Configure IAM Identity Center as the centralized access portal for all AWS accounts. Connect to your enterprise IdP via SAML 2.0 or SCIM provisioning. Define permission sets that map to job functions. Assign permission sets to groups (not individual users) for specific accounts. Permission sets become IAM roles in target accounts with a maximum session duration of 1–12 hours.
- Verification:
  ```bash
  # Check for IAM users with console access (should be zero or minimal)
  aws iam generate-credential-report && aws iam get-credential-report --output text --query Content | base64 -d | grep -c "password_enabled.*true"
  # List IAM users with active access keys
  aws iam generate-credential-report && aws iam get-credential-report --output text --query Content | base64 -d | awk -F',' '$9=="true" || $14=="true" {print $1}'
  ```
- Trade-offs: Dependency on IdP availability (mitigate with emergency break-glass IAM user secured with hardware MFA); increased initial setup complexity; session duration limits may require re-authentication for long-running console sessions.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html

---

**IAM Roles for All Workloads (No Embedded Credentials)**
- Pillar Alignment: Security — Identity Management (SEC02)
- Why: "Require workloads to use temporary credentials with IAM roles to access AWS" — AWS IAM Security Best Practices. Embedded access keys in code, environment variables, or config files create persistent credentials that cannot be automatically rotated by AWS and are frequently leaked through source control, logs, or container image layers.
- AWS Services: IAM Roles, EC2 Instance Profiles, ECS Task Roles, Lambda Execution Roles, EKS Service Accounts (IRSA/Pod Identity), IAM Roles Anywhere
- Architecture Decision:
  Every compute workload (EC2, ECS, EKS, Lambda, CodeBuild, etc.) must use an IAM role for AWS API access. For EC2: attach instance profiles. For ECS: use task roles (not the EC2 instance role). For EKS: use IAM Roles for Service Accounts (IRSA) or EKS Pod Identity. For Lambda: execution roles. For external workloads: IAM Roles Anywhere with X.509 certificates. Each workload gets its own role with least-privilege permissions — never share roles across unrelated workloads.
- Verification:
  ```bash
  # Find IAM users with active access keys (potential workload credentials)
  aws iam list-users --query 'Users[*].UserName' --output text | xargs -I {} aws iam list-access-keys --user-name {} --query 'AccessKeyMetadata[?Status==`Active`].[UserName,AccessKeyId,CreateDate]' --output text
  # Verify EC2 instances have instance profiles
  aws ec2 describe-instances --query 'Reservations[*].Instances[?IamInstanceProfile==null].[InstanceId,State.Name]' --output text
  ```
- Trade-offs: Temporary credentials expire (default 1 hour for assumed roles, 6 hours for EC2 instance profiles), requiring SDK credential refresh logic (all AWS SDKs handle this automatically); more IAM roles to manage (mitigate with IaC and naming conventions).
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html

---

**Least-Privilege Permissions**
- Pillar Alignment: Security — Permissions Management (SEC03)
- Why: "Apply least-privilege permissions" — AWS IAM Security Best Practices. Overly broad permissions increase the blast radius of compromised credentials or application vulnerabilities. Every wildcard `*` in an Action or Resource element is a potential privilege escalation vector.
- AWS Services: IAM (Customer Managed Policies), IAM Access Analyzer (Policy Generation, Unused Access), CloudTrail
- Architecture Decision:
  Start with AWS managed policies for rapid iteration during development. Once workloads stabilize, use IAM Access Analyzer to generate least-privilege policies from actual CloudTrail access activity (90-day analysis window recommended). Replace managed policies with generated customer managed policies. Enable unused access analysis to detect permissions granted but never used. Integrate IAM Access Analyzer policy validation into CI/CD pipelines to catch overly permissive policies before deployment.
- Verification:
  ```bash
  # Check for policies with wildcard actions
  aws iam list-policies --scope Local --query 'Policies[*].Arn' --output text | xargs -I {} aws iam get-policy-version --policy-arn {} --version-id $(aws iam get-policy --policy-arn {} --query 'Policy.DefaultVersionId' --output text) --query 'PolicyVersion.Document' --output json | grep -l '"Action": "\*"'
  # Generate policy from access activity
  aws accessanalyzer start-policy-generation --policy-generation-details '{"principalArn":"arn:aws:iam::123456789012:role/MyRole"}' --cloud-trail-details '{"trails":[{"cloudTrailArn":"arn:aws:cloudtrail:us-east-1:123456789012:trail/my-trail","allRegions":true}],"accessRole":"arn:aws:iam::123456789012:role/AccessAnalyzerRole","startTime":"2024-01-01T00:00:00Z","endTime":"2024-04-01T00:00:00Z"}'
  ```
- Trade-offs: Generating least-privilege policies requires CloudTrail logging enabled and sufficient access activity history; newly deployed features may lack permissions if policy generation was based on pre-feature access patterns; ongoing maintenance as application capabilities evolve.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html

---

**MFA for All Human Access**
- Pillar Alignment: Security — Identity Management (SEC02)
- Why: "Require multi-factor authentication (MFA)" — AWS IAM Security Best Practices. MFA adds a second authentication factor that prevents credential-only compromise from resulting in unauthorized access. AWS recommends phishing-resistant MFA (FIDO2 passkeys/security keys) wherever possible.
- AWS Services: IAM MFA (FIDO2/passkeys, TOTP, hardware tokens), IAM Identity Center MFA
- Architecture Decision:
  Enforce MFA at the identity provider level for federated access via IAM Identity Center. For the break-glass root user and any remaining IAM users, require hardware MFA (YubiKey or similar FIDO2 device). Use IAM policy conditions (`aws:MultiFactorAuthPresent`, `aws:MultiFactorAuthAge`) to enforce MFA for sensitive operations even within an authenticated session. Configure IAM Identity Center to require MFA at every sign-in (not just "context-aware" mode) for production account access.
- Verification:
  ```bash
  # Check root user MFA status
  aws iam get-account-summary --query 'SummaryMap.AccountMFAEnabled'
  # List IAM users without MFA
  aws iam generate-credential-report && aws iam get-credential-report --output text --query Content | base64 -d | awk -F',' '$4=="true" && $8=="false" {print $1}'
  ```
- Trade-offs: Hardware MFA devices require procurement and physical distribution; TOTP (software) MFA is phishable but better than no MFA; FIDO2 requires browser/device support; MFA enforcement via policy conditions adds complexity to API-access patterns.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html

---

**Organizational Permission Guardrails (SCPs + RCPs)**
- Pillar Alignment: Security — Permissions Management (SEC03)
- Why: "Establish permissions guardrails across multiple accounts" — AWS IAM Security Best Practices. Without organizational guardrails, any administrator in a member account can grant any permission to any principal within that account. SCPs and RCPs provide preventive controls that cannot be overridden by account-level administrators.
- AWS Services: AWS Organizations (SCPs, RCPs), AWS Control Tower (Managed Guardrails)
- Architecture Decision:
  Enable all features in AWS Organizations. Apply baseline SCPs to all member accounts that: deny access to unused AWS regions, deny disabling CloudTrail/GuardDuty/SecurityHub, deny root user actions (except break-glass), deny creation of IAM users with console access, deny leaving the organization. Apply RCPs that: deny resource policies granting access to principals outside the organization, deny making S3 buckets public, deny KMS key sharing with external accounts. Use AWS Control Tower for managed guardrail deployment and drift detection.
- Verification:
  ```bash
  # List SCPs attached to organizational units
  aws organizations list-policies --filter SERVICE_CONTROL_POLICY --query 'Policies[*].[Name,Id]' --output table
  # List RCPs attached to organizational units
  aws organizations list-policies --filter RESOURCE_CONTROL_POLICY --query 'Policies[*].[Name,Id]' --output table
  ```
- Trade-offs: Overly restrictive SCPs can break legitimate workloads — always test in a sandbox OU first; SCPs do not affect the management account (never run workloads there); RCPs are a newer feature with limited service support — validate supported services before relying on them.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html

---

**Root User Credential Protection**
- Pillar Alignment: Security — Identity Management (SEC02)
- Why: "Follow best practices to protect your root user credentials" — AWS IAM Security Best Practices. The root user has unrestricted access to all resources in the account and cannot be constrained by SCPs for certain actions. Root user compromise is a total account takeover.
- AWS Services: IAM (Root User), AWS Organizations (Root User Management)
- Architecture Decision:
  Enable MFA on the root user with a hardware FIDO2 device (not TOTP). Do not create access keys for the root user. Store root user credentials (email + password + MFA device) in a physical safe or enterprise secrets vault with break-glass procedures. Use Organizations centralized root access management to perform root user tasks without signing in as root. Monitor root user activity via CloudTrail with CloudWatch Alarms for any root user API call. Restrict root-user-only tasks to account creation and the few documented scenarios that require root.
- Verification:
  ```bash
  # Verify root user has MFA enabled
  aws iam get-account-summary --query 'SummaryMap.AccountMFAEnabled'
  # Check for root user access keys (should be none)
  aws iam get-account-summary --query 'SummaryMap.AccountAccessKeysPresent'
  # CloudTrail filter for root user activity
  aws cloudtrail lookup-events --lookup-attributes AttributeKey=Username,AttributeValue=root --max-items 10
  ```
- Trade-offs: Physical hardware MFA creates a single point of failure (mitigate with backup MFA device registered to the account); break-glass procedures add latency to emergency response; centralized root management requires Organizations — not available for standalone accounts.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/root-user-best-practices.html

---

**One Role Per Workload (Role Isolation)**
- Pillar Alignment: Security — Permissions Management (SEC03)
- Why: Sharing IAM roles across unrelated workloads violates least-privilege by granting each workload the union of permissions needed by all workloads using that role. A compromise of any single workload using a shared role grants the attacker all permissions of all workloads.
- AWS Services: IAM Roles, EC2 Instance Profiles, ECS Task Roles, Lambda Execution Roles
- Architecture Decision:
  Create a dedicated IAM role for each distinct workload or microservice. Name roles using a consistent convention (e.g., `{app}-{environment}-{service}-role`). Each role's permissions policy should grant only the specific actions and resources needed by that workload. Use separate roles for different environments (dev, staging, production) even for the same workload. Tag roles with application metadata for governance and cost attribution.
- Verification:
  ```bash
  # Identify roles with overly broad policies (e.g., AdministratorAccess)
  aws iam list-roles --query 'Roles[*].RoleName' --output text | xargs -I {} sh -c 'aws iam list-attached-role-policies --role-name {} --query "AttachedPolicies[?PolicyArn==\`arn:aws:iam::aws:policy/AdministratorAccess\`].PolicyName" --output text | grep -q "." && echo {}'
  ```
- Trade-offs: More roles to manage (mitigate with IaC templates/modules); role session credential caching per-workload; IAM has a default limit of 1000 roles per account (request increase for microservice architectures).
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/permissions-management.html

---

### ⚠️ Architectural Decisions

**Identity Provider Strategy**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|------------|-----------|------------|-----------|
  | IAM Identity Center (built-in directory) | IAM Identity Center | Simplicity, no external IdP dependency | Enterprise identity lifecycle integration | Small teams, AWS-only workforce, no existing enterprise IdP |
  | IAM Identity Center (federated to external IdP) | IAM Identity Center + Okta/Azure AD/etc. | Centralized identity lifecycle, SSO across cloud + SaaS | Operational dependency on external IdP availability | Enterprise workforce with existing IdP, multi-cloud/multi-SaaS |
  | Direct SAML/OIDC federation to IAM | IAM Identity Providers + IAM Roles | No IAM Identity Center dependency, granular trust per role | No centralized permission set management, manual role-account mapping | Legacy architectures, single-account, specific compliance requirements |
  | IAM Users (long-term credentials) | IAM Users, Access Keys | Zero dependency on federation infrastructure | Security posture (persistent credentials), scalability, auditability | Only for documented exceptions (WordPress plugins, legacy tools without federation support) |

- Cost Profile: IAM Identity Center is free. External IdP licensing varies. IAM is free. Cost difference is operational — federated architectures reduce credential management burden.
- Lock-in Assessment: IAM Identity Center is AWS-specific but uses standard SAML/OIDC protocols. External IdPs are portable. IAM users with access keys are the most portable but least secure.
- Architect Instruction: "Ask which identity provider the organization already uses for workforce identity before designing the IAM access pattern."
- Source: https://docs.aws.amazon.com/singlesignon/latest/userguide/what-is.html

---

**Cross-Account Access Pattern**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|------------|-----------|------------|-----------|
  | Cross-account IAM roles | IAM Roles (trust policies) | Temporary credentials, auditable via CloudTrail, least-privilege per role | Requires role assumption in calling code | Service-to-service communication, CI/CD pipelines, centralized tooling accessing member accounts |
  | Resource-based policies | S3/SQS/SNS/KMS/Lambda policies | No role assumption needed, direct principal grant | Only works for services that support resource-based policies, harder to audit centrally | Sharing specific resources (S3 buckets, KMS keys) with specific accounts |
  | AWS RAM (Resource Access Manager) | AWS RAM | Managed sharing, Organization-level sharing, no policy authoring | Limited to supported resource types, less granular than policies | Sharing VPC subnets, Transit Gateways, Route 53 resolver rules, License Manager configurations |
  | Organizations delegated administration | AWS Organizations + Service delegation | Centralized service management from non-management account | Limited to services that support delegation | SecurityHub/GuardDuty/CloudFormation StackSets administration |

- Cost Profile: All options are free (IAM, resource policies, RAM). Operational cost differs — cross-account roles are most flexible but require more IaC.
- Lock-in Assessment: All patterns are AWS-specific. Cross-account roles use standard STS AssumeRole API — well-supported by all AWS SDKs and IaC tools.
- Architect Instruction: "Ask whether the cross-account access is for a human user, an automated workload, or a shared resource — the pattern differs for each."
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies-cross-account-resource-access.html

---

**Authorization Strategy (RBAC vs ABAC vs Hybrid)**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|------------|-----------|------------|-----------|
  | RBAC (Role-Based) | IAM Roles + Identity-based policies with explicit resource ARNs | Clarity, auditability, predictability | Policy proliferation as resources grow, manual updates for new resources | Stable environments with well-known resource sets, compliance requirements for explicit grants |
  | ABAC (Attribute-Based) | IAM Policies with tag conditions (aws:ResourceTag, aws:PrincipalTag) | Scalability, dynamic access as resources are created, fewer policies | Requires strict tag governance, harder to audit "who has access to what", tag propagation complexity | Rapidly growing environments, multi-team organizations, dynamic resource creation |
  | Hybrid (RBAC + ABAC) | IAM Roles (RBAC for role assignment) + Tag conditions (ABAC for resource scoping) | Balance of clarity and scalability | Complexity of managing both tag governance and role assignments | Most production environments — RBAC for job function assignment, ABAC for resource-level scoping within the role |

- Cost Profile: No cost difference. Operational cost: RBAC requires more policy updates; ABAC requires tag governance enforcement.
- Lock-in Assessment: Both are standard IAM patterns — no vendor lock-in implications. ABAC tag-condition syntax is AWS-specific but the concept is portable.
- Architect Instruction: "Ask how frequently new resources are created and whether tagging governance (enforcement + audit) is already in place before recommending ABAC."
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction_attribute-based-access-control.html

---

**Permissions Boundary vs SCP for Guardrails**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|------------|-----------|------------|-----------|
  | Service Control Policies (SCPs) | AWS Organizations | Organization-wide enforcement, cannot be circumvented by account admins | Requires Organizations, does not apply to management account, coarse granularity (entire account) | Preventing dangerous actions across all accounts (disable regions, protect security services) |
  | Resource Control Policies (RCPs) | AWS Organizations | Resource-level guardrails, prevents resources from granting access to external entities | Newer feature, limited service support, does not constrain principals directly | Preventing data exfiltration via resource policies (S3 public access, KMS external sharing) |
  | Permissions Boundaries | IAM | Per-entity enforcement, delegatable, scopes individual roles/users | Only applies to identity-based policy grants, does not prevent resource-based policy access | Delegated administration — allowing teams to create roles within defined limits |
  | IAM Policy Conditions | IAM | Fine-grained, per-action/resource scoping | Requires policy author discipline, no enforcement if conditions are omitted | Enforcing constraints within specific policies (e.g., require encryption, restrict regions) |

- Cost Profile: All free. Operational cost: SCPs require Organizations; permissions boundaries require consistent attachment enforcement.
- Lock-in Assessment: All are AWS-specific constructs with no direct equivalent on other providers (conceptual equivalents exist).
- Architect Instruction: "Ask whether the guardrail needs to apply organization-wide (SCP/RCP) or per-team/per-role (permissions boundary) before choosing the mechanism."
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html

---

### 🚫 Anti-Patterns

**Wildcard Actions and Resources in Production Policies**
- Risk Level: CRITICAL
- Why: Violates Security pillar — Permissions Management (SEC03). Policies with `"Action": "*"` or `"Resource": "*"` on sensitive services grant effectively unlimited access within that service, enabling privilege escalation, data exfiltration, and resource destruction.
- Instead: Use specific action names and resource ARNs. Start with AWS managed policies, then use IAM Access Analyzer policy generation to refine to actual actions/resources used by the workload over a 90-day CloudTrail window.
- Detection:
  ```bash
  # IAM Access Analyzer policy validation flags overly permissive policies
  aws accessanalyzer validate-policy --policy-document file://policy.json --policy-type IDENTITY_POLICY
  # Custom check: find policies with Action: *
  aws iam list-policies --scope Local --query 'Policies[*].Arn' --output text | xargs -I {} aws iam get-policy-version --policy-arn {} --version-id $(aws iam get-policy --policy-arn {} --query 'Policy.DefaultVersionId' --output text) --output json | jq 'select(.PolicyVersion.Document.Statement[].Action == "*")'
  ```
- Impact: Privilege escalation | Data breach | Resource destruction | Compliance violation
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html

---

**Long-Term Access Keys for Workloads Running on AWS**
- Risk Level: CRITICAL
- Why: Violates Security pillar — Identity Management (SEC02). IAM access keys are long-lived credentials that do not automatically rotate. Workloads running on AWS compute (EC2, ECS, Lambda, EKS) have native mechanisms for temporary credentials via IAM roles — using access keys instead creates unnecessary persistent credential exposure.
- Instead: Use IAM roles: EC2 instance profiles, ECS task roles, Lambda execution roles, EKS Pod Identity/IRSA. For workloads outside AWS, use IAM Roles Anywhere with X.509 certificates.
- Detection:
  ```bash
  # List access keys and their age
  aws iam generate-credential-report && aws iam get-credential-report --output text --query Content | base64 -d | awk -F',' 'NR>1 && $9=="true" {print $1, $10}'
  # Check for access keys older than 90 days
  aws iam generate-credential-report && aws iam get-credential-report --output text --query Content | base64 -d | awk -F',' 'NR>1 && $9=="true"' | while read line; do echo "$line" | awk -F',' '{print $1, $10}'; done
  ```
- Impact: Credential theft | Persistent unauthorized access | Data breach | Compliance violation (PCI-DSS, SOC2)
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html

---

**Shared IAM Roles Across Unrelated Workloads**
- Risk Level: HIGH
- Why: Violates least-privilege principle. A shared role grants each workload the union of all permissions required by all workloads using that role. Compromise of one workload grants the attacker access to resources of all other workloads sharing the role.
- Instead: Create one IAM role per workload/microservice with only the permissions that specific workload needs. Use IaC modules to standardize role creation patterns.
- Detection:
  ```bash
  # Identify roles used by multiple services (check instance profiles across multiple instances, task definitions referencing same role)
  aws iam list-instance-profiles --query 'InstanceProfiles[*].[InstanceProfileName,Roles[0].RoleName]' --output table
  ```
- Impact: Privilege escalation | Increased blast radius | Lateral movement after initial compromise
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/permissions-management.html

---

**Trust Policies Without Source Conditions (Confused Deputy)**
- Risk Level: HIGH
- Why: Trust policies that allow a service principal (e.g., `lambda.amazonaws.com`, `s3.amazonaws.com`) without conditions like `aws:SourceArn` or `aws:SourceAccount` allow any resource in any account using that service to assume the role. This is the confused deputy problem — a third party can trick the service into assuming your role on their behalf.
- Instead: Always include `aws:SourceArn` and/or `aws:SourceAccount` conditions in trust policies for service principals. For third-party cross-account roles, require `sts:ExternalId`.
- Detection:
  ```bash
  # Find roles with service principals in trust policy but no conditions
  aws iam list-roles --query 'Roles[*].[RoleName,AssumeRolePolicyDocument]' --output json | jq '.[] | select(.[1].Statement[].Principal.Service != null and (.[1].Statement[].Condition == null)) | .[0]'
  ```
- Impact: Unauthorized role assumption | Cross-account privilege escalation | Data breach via confused deputy
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/confused-deputy.html

---

**IAM Users With Console Access in Member Accounts**
- Risk Level: HIGH
- Why: IAM users with console passwords in member accounts bypass the centralized identity management provided by IAM Identity Center. They create shadow identities that are not governed by the organization's IdP lifecycle (joiners/movers/leavers), not subject to centralized MFA enforcement, and not visible in federated access logs.
- Instead: Use IAM Identity Center for all human console access. Enforce via SCP that denies `iam:CreateLoginProfile` and `iam:CreateUser` in member accounts (with exceptions for documented break-glass scenarios).
- Detection:
  ```bash
  # Count IAM users with console access per account
  aws iam generate-credential-report && aws iam get-credential-report --output text --query Content | base64 -d | awk -F',' 'NR>1 && $4=="true" {print $1}'
  # SCP to prevent creation
  # Deny: iam:CreateUser, iam:CreateLoginProfile (apply to member account OUs)
  ```
- Impact: Shadow identity proliferation | Bypass of MFA enforcement | Orphaned accounts after employee departure | Audit gap
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html

---

**Inline Policies at Scale**
- Risk Level: MEDIUM
- Why: Inline policies are embedded directly in a single user, group, or role. They cannot be reused, versioned, or centrally audited. At scale, inline policies create an ungovernable sprawl of permissions that are invisible to policy audit tools that query managed policies.
- Instead: Use customer managed policies for all non-trivial permissions. Reserve inline policies only for rare cases where a strict 1:1 relationship between policy and identity is intentionally desired and the policy must be deleted with the identity.
- Detection:
  ```bash
  # List roles with inline policies
  aws iam list-roles --query 'Roles[*].RoleName' --output text | xargs -I {} sh -c 'policies=$(aws iam list-role-policies --role-name {} --query "PolicyNames" --output text); [ -n "$policies" ] && echo "{}: $policies"'
  ```
- Impact: Policy governance gap | Audit failure | Unintended permission drift | Difficulty achieving least-privilege at scale
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_managed-vs-inline.html

---

**Disabled or Absent CloudTrail Logging**
- Risk Level: CRITICAL
- Why: CloudTrail is the audit log for ALL IAM API calls and resource access. Without CloudTrail, there is no way to detect unauthorized access, investigate security incidents, generate least-privilege policies via Access Analyzer, or satisfy compliance audit requirements (SOC2, PCI-DSS, HIPAA).
- Instead: Enable CloudTrail organization trail with management events in all regions. Store logs in a centralized security account S3 bucket with bucket policy preventing deletion. Enable CloudTrail Insights for anomaly detection. Configure CloudWatch Alarms for critical IAM events (root login, policy changes, role creation).
- Detection:
  ```bash
  # Verify CloudTrail is enabled in all regions
  aws cloudtrail describe-trails --query 'trailList[*].[Name,IsMultiRegionTrail,IsOrganizationTrail]' --output table
  aws cloudtrail get-trail-status --name <trail-name> --query 'IsLogging'
  ```
- Impact: Complete loss of audit trail | Inability to detect breaches | Compliance violation | Cannot generate least-privilege policies
- Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-getting-started.html

---

## Cloud-Native Design Patterns

**Least-Privilege Policy Lifecycle**
- Category: Security
- Problem: Applications evolve over time — new features require new AWS API calls, deprecated features leave unused permissions behind. Static policies drift from actual access requirements, either under-granting (breaking features) or over-granting (expanding blast radius).
- Solution on AWS:
  1. Deploy with AWS managed policies during development (fast iteration)
  2. Enable CloudTrail logging for the workload's role
  3. After 90 days of stable operation, run IAM Access Analyzer policy generation against the CloudTrail data
  4. Replace managed policies with generated customer managed policies
  5. Enable unused access analysis to continuously detect permission drift
  6. Integrate Access Analyzer policy validation into CI/CD pipeline to prevent re-introduction of overly broad permissions
- Services Used: IAM Access Analyzer (policy generation + unused access + policy validation), CloudTrail, IAM (customer managed policies)
- When to Apply: Every production workload after initial stabilization
- When NOT to Apply: Development/sandbox environments where rapid iteration requires broad permissions
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Security | Provably least-privilege based on actual access | Requires 90-day CloudTrail history before policy generation |
  | Operational | Automated policy authoring reduces manual errors | Must re-run generation when application features change |
  | Cost | Access Analyzer unused access analysis has per-analyzer-per-month charges | Nominal — offset by reduced incident response costs |

- Complements: Role Isolation, Permissions Boundaries, SCP guardrails
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/access-analyzer-policy-generation.html

---

**Delegated Administration with Permissions Boundaries**
- Category: Security
- Problem: In large organizations, a central IAM team cannot manage all roles for all application teams. Teams need autonomy to create and manage their own roles. But unrestricted IAM administration allows privilege escalation — a team could grant themselves administrator access or access another team's resources.
- Solution on AWS:
  1. Central team defines a permissions boundary policy (ceiling on what any team-created role can do)
  2. Central team grants application teams permission to create/manage roles ONLY IF they attach the specified permissions boundary
  3. Enforce via IAM condition: `"iam:PermissionsBoundary": "arn:aws:iam::ACCOUNT:policy/TeamBoundary"`
  4. Permissions boundary denies access to: other teams' resources, security services, IAM administration beyond self-management
  5. Teams can create roles with any permissions policies — but effective permissions are always capped by the boundary
- Services Used: IAM (Permissions Boundaries, Customer Managed Policies, IAM Conditions)
- When to Apply: Multi-team environments where teams need IAM self-service without centralized bottleneck
- When NOT to Apply: Small teams where a single IAM administrator can manage all roles; accounts with <10 roles
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Security | Prevents privilege escalation by delegated administrators | Complex policy evaluation path — harder to debug access denials |
  | Operational | Teams are self-service for IAM — no central team bottleneck | Central team must maintain boundary policies as services evolve |
  | Agility | Teams can iterate on permissions without waiting for approvals | Boundary too restrictive = teams blocked; too permissive = security gap |

- Complements: SCPs (organization-wide guardrails), ABAC (tag-based resource isolation between teams)
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html

---

**Cross-Account Role Chaining for CI/CD Pipelines**
- Category: Communication
- Problem: CI/CD pipelines need to deploy resources across multiple AWS accounts (dev, staging, production). The pipeline itself runs in a tools/shared-services account. Embedding per-account credentials in the pipeline is insecure and unscalable.
- Solution on AWS:
  1. Pipeline execution role in the tools account (e.g., CodeBuild service role)
  2. Deployment role in each target account with trust policy allowing the pipeline role to assume it
  3. Deployment role has only the permissions needed for deployment (e.g., CloudFormation, S3, Lambda)
  4. Pipeline assumes the target account deployment role via `sts:AssumeRole` before each deployment
  5. Use `aws:SourceArn` condition in trust policy to restrict which pipeline resources can assume the role
  6. Use session policies to further scope permissions to the specific deployment (e.g., specific stack name)
- Services Used: IAM Roles, AWS STS (AssumeRole), CodePipeline/CodeBuild, CloudFormation
- When to Apply: Any multi-account deployment automation
- When NOT to Apply: Single-account environments; manual deployments (use IAM Identity Center instead)
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Security | Temporary credentials per deployment, scoped to target account | Role chaining limits session to 1 hour maximum |
  | Auditability | Each AssumeRole is logged in CloudTrail in both accounts | More CloudTrail events to analyze during incident response |
  | Operational | No credential rotation needed — STS handles it | Trust policy maintenance across accounts (mitigate with IaC) |

- Complements: SCP guardrails on deployment roles, Permissions Boundaries for deployment scope
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_common-scenarios.html

---

**Tag-Based Access Control (ABAC) for Multi-Tenant Resource Isolation**
- Category: Data
- Problem: In multi-team or multi-tenant environments, each team's workloads must access only their own resources. With traditional RBAC, every new resource requires a policy update to add its ARN. This doesn't scale when resources are created dynamically (e.g., per-customer S3 prefixes, per-team DynamoDB tables).
- Solution on AWS:
  1. Define mandatory tags: `Team`, `Environment`, `Project` on all resources
  2. Enforce tagging via SCP or AWS Config rules (deny untagged resource creation)
  3. Assign matching tags to IAM roles: `aws:PrincipalTag/Team = engineering`
  4. Write policies with conditions: `"Condition": {"StringEquals": {"aws:ResourceTag/Team": "${aws:PrincipalTag/Team}"}}`
  5. New resources automatically accessible to the correct team if tagged correctly — no policy update needed
  6. Tag governance enforced via AWS Organizations Tag Policies and AWS Config conformance packs
- Services Used: IAM (Policy conditions, Principal tags), AWS Organizations (Tag Policies), AWS Config (Required tags rule)
- When to Apply: Organizations with >5 teams, dynamic resource creation, or multi-tenant architectures
- When NOT to Apply: Single-team environments; resources that cannot be tagged; environments without tag governance maturity
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Scalability | Zero policy updates for new resources — access governed by tags | Tag governance enforcement infrastructure required |
  | Security | Fine-grained isolation without policy sprawl | Incorrect tagging = access denial or over-access |
  | Operational | Self-service resource creation with automatic access scoping | Debugging tag-condition mismatches is harder than explicit ARN denials |

- Complements: Permissions Boundaries (cap maximum permissions), SCPs (enforce tagging), AWS Config (audit tag compliance)
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction_attribute-based-access-control.html

---

## Security Architecture

**Identity Management (Workforce Identity)**
- AWS Services: IAM Identity Center, AWS STS, IAM (Identity Providers for SAML/OIDC), AWS Directory Service
- Architecture:
  IAM Identity Center connects to enterprise IdP (via SAML 2.0 or SCIM) as the single entry point for all human AWS access. Users authenticate against the IdP, receive SAML assertions, and IAM Identity Center maps them to permission sets (which become IAM roles in target accounts). MFA is enforced at the IdP layer. Permission sets define maximum session duration (1–12 hours). Access assignments are group-based (not individual) for lifecycle management. Break-glass IAM users exist in a security account with hardware MFA, rotated quarterly, and monitored via CloudTrail alarms.
- Compliance Alignment: SOC2 CC6.1 (Logical Access), PCI-DSS 7.1 (Restrict access by business need), HIPAA §164.312(d) (Person authentication)
- Source: https://docs.aws.amazon.com/singlesignon/latest/userguide/what-is.html

---

**Identity Management (Workload Identity)**
- AWS Services: IAM Roles, EC2 Instance Profiles, ECS Task Roles, EKS Pod Identity (IRSA), Lambda Execution Roles, IAM Roles Anywhere, AWS STS
- Architecture:
  Every compute workload receives its own IAM role with least-privilege permissions. On-AWS workloads use native credential delivery mechanisms (instance metadata, container credential provider, environment variables injected by the compute service). Off-AWS workloads use IAM Roles Anywhere with X.509 certificates from the organization's PKI, configured with trust anchors and profiles. Service-to-service authentication uses IAM roles assumed via STS — no shared secrets, no API keys. Cross-account workload access uses role assumption with trust policies scoped by `aws:SourceArn`.
- Compliance Alignment: SOC2 CC6.2 (Credentials), PCI-DSS 8.2 (Unique identification), NIST 800-53 IA-5 (Authenticator management)
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html

---

**Permissions Management (Authorization)**
- AWS Services: IAM (Policies — identity-based, resource-based), Permissions Boundaries, AWS Organizations (SCPs, RCPs), IAM Access Analyzer
- Architecture:
  Authorization follows a defense-in-depth model with multiple policy layers. Organization level: SCPs prevent dangerous actions across all accounts; RCPs prevent resources from being shared externally. Account level: Permissions boundaries cap what delegated administrators can grant. Role level: Customer managed policies grant specific actions on specific resources with conditions. Resource level: Resource-based policies (S3 bucket policies, KMS key policies) define cross-account sharing explicitly. Validation: IAM Access Analyzer continuously monitors for public/cross-account access findings and unused permissions. CI/CD: Policy validation checks integrated into deployment pipelines reject overly permissive policies before they reach production.
- Compliance Alignment: SOC2 CC6.3 (Least privilege), PCI-DSS 7.2 (Access control systems), HIPAA §164.312(a)(1) (Access control)
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html

---

**Detection & Monitoring (IAM Activity)**
- AWS Services: CloudTrail, CloudWatch (Alarms, Log Insights), IAM Access Analyzer (Findings), GuardDuty, SecurityHub
- Architecture:
  CloudTrail logs all IAM API calls (management events) across all regions via organization trail. CloudWatch Alarms trigger on high-risk IAM events: root user login, policy changes (`Put*Policy`, `Attach*Policy`), role creation, access key creation, console login without MFA. IAM Access Analyzer generates findings for external access to resources and unused access (roles not used in 90 days, permissions not used in 90 days, access keys not used in 90 days). GuardDuty detects anomalous IAM activity: credential exfiltration, unusual API calls, impossible travel. SecurityHub aggregates findings from all sources with automated severity scoring.
- Compliance Alignment: SOC2 CC7.2 (Monitoring), PCI-DSS 10.2 (Audit trails), HIPAA §164.312(b) (Audit controls)
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/what-is-access-analyzer.html

---

## Operational Patterns

**IAM Credential Rotation and Hygiene**
- AWS Services: IAM (Credential Report, Access Advisor), IAM Access Analyzer (Unused Access), AWS Config (Rules), CloudWatch Events
- Cost Profile: Low — IAM and Config rules are minimal cost. Unused access analysis has per-analyzer charges.
- Automation:
  - AWS Config rule `iam-user-unused-credentials-check` (flag credentials unused for 90 days)
  - AWS Config rule `access-keys-rotated` (flag access keys older than 90 days)
  - IAM Access Analyzer unused access findings (roles unused 90+ days, permissions unused 90+ days)
  - Lambda function triggered by Config rule non-compliance to disable stale access keys automatically
  - Monthly credential report generation and review by security team
- Runbook Skeleton:
  1. Weekly: Review IAM Access Analyzer unused access findings
  2. Monthly: Generate and review IAM credential report
  3. On finding: Contact resource owner, confirm credential is unnecessary, disable (not delete) for 7 days, delete if no impact reported
  4. Quarterly: Review all IAM users — confirm each has documented justification for existence (vs. federation)
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html

---

**IAM Policy Change Management**
- AWS Services: CloudTrail, CloudWatch Events, AWS Config (Config Rules), CodePipeline, IAM Access Analyzer (Policy Validation)
- Cost Profile: Low — operational tooling costs only.
- Automation:
  - All IAM policy changes via Infrastructure-as-Code (CloudFormation/Terraform) — no console policy editing in production
  - IAM Access Analyzer policy validation integrated into CI/CD pipeline (fail build on SECURITY_WARNING findings)
  - CloudWatch Events rule on `PutRolePolicy`, `AttachRolePolicy`, `CreatePolicy` events → SNS notification to security team
  - AWS Config rule `iam-policy-no-statements-with-admin-access` (detect admin policy attachment)
  - Drift detection via CloudFormation/Terraform plan — alert on unexpected policy changes
- Runbook Skeleton:
  1. Developer submits IaC change with policy modification
  2. CI pipeline runs IAM Access Analyzer policy validation — blocks on security warnings
  3. Security review for any policy adding `*` actions, cross-account access, or sensitive service permissions
  4. Deployment to staging → validate application functionality with new permissions
  5. Deployment to production with CloudFormation change set review
  6. Post-deployment: Verify no IAM Access Analyzer findings generated
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/access-analyzer-policy-validation.html

---

**Break-Glass (Emergency Access) Procedure**
- RTO/RPO: RTO < 15 minutes (time to access break-glass credentials and authenticate)
- AWS Services: IAM (Break-glass IAM user), Hardware MFA, Secrets Manager or Physical Safe, CloudTrail, CloudWatch Alarms
- Cost Profile: Low — only the monitoring infrastructure. Break-glass user itself is free.
- Automation:
  - CloudWatch Alarm on ANY API call from break-glass IAM user → immediate PagerDuty/Slack alert
  - Automatic access key disable after 4-hour window (Lambda triggered by CloudWatch Events)
  - Post-incident: Forced password rotation on break-glass user
- Runbook Skeleton:
  1. Trigger: Identity provider is unavailable AND an AWS action requiring human access is urgent
  2. Retrieve break-glass credentials from physical safe / secrets vault (requires two-person authorization)
  3. Sign in to AWS console with break-glass IAM user + hardware MFA
  4. Perform minimum necessary actions to resolve the incident
  5. Sign out immediately after resolution
  6. Rotate break-glass credentials (password + access keys if used)
  7. Post-incident review: Document actions taken, verify via CloudTrail, assess if IdP resilience improvements are needed
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html

---

## Reference Architectures

**Multi-Account IAM Architecture (AWS Organizations)**
- Context: Enterprise workload requiring environment isolation, team autonomy, and centralized security governance
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Organization Management | AWS Organizations | Account hierarchy, SCP/RCP enforcement, consolidated billing |
  | Identity | IAM Identity Center | Centralized human access, permission set management, IdP federation |
  | Security Guardrails | SCPs | Preventive controls — deny dangerous actions in all member accounts |
  | Resource Guardrails | RCPs | Preventive controls — deny resource sharing with external entities |
  | Account Baseline | Control Tower | Automated account provisioning with security baseline (CloudTrail, Config, GuardDuty) |
  | Workload Identity | IAM Roles | Per-workload least-privilege roles in each account |
  | Cross-Account Access | IAM Roles (trust policies) | Deployment pipelines, centralized tooling, security scanning |
  | Audit | CloudTrail Organization Trail | Centralized logging of all IAM activity across all accounts |
  | Analysis | IAM Access Analyzer | Organization-level analyzer for external access + unused access findings |

- Key Decisions:
  - Management account: NO workloads, NO human day-to-day access (SCPs don't apply to it)
  - Security account: Hosts CloudTrail logs, SecurityHub delegated admin, break-glass users
  - Shared Services account: Hosts CI/CD pipelines, container registries, artifact storage
  - Workload accounts: One per environment per application (e.g., app1-dev, app1-prod)
  - Permission sets: Map to job functions (Admin, Developer, ReadOnly, SecurityAuditor) with account-specific assignments
- Scaling Path:
  Start with 4-5 accounts (Management, Security, Shared Services, Dev, Prod). Scale by adding workload accounts per team/application as the organization grows. Use account vending machine (Control Tower Account Factory) for self-service account creation with baseline guardrails.
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/organizations.html

---

**Zero-Trust Workload Identity Architecture**
- Context: Microservices architecture where services authenticate to each other and to AWS resources without network-level trust assumptions
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Workload Identity | IAM Roles (per-service) | Each microservice has unique identity with least-privilege AWS permissions |
  | Service-to-Service Auth | IAM (SigV4 signed requests) | Services authenticate to AWS APIs using role-derived temporary credentials |
  | Service Mesh Auth | App Mesh / VPC Lattice | Service-to-service mTLS authentication independent of network location |
  | API Authorization | API Gateway (IAM auth) | API-level authorization using IAM policies and resource policies |
  | Resource Access | Resource-based policies | Resources validate caller identity via IAM principal conditions |
  | Secret Distribution | Secrets Manager | Runtime secrets (DB passwords, API keys) delivered via IAM-authorized API calls |
  | Network Segmentation | VPC Security Groups | Defense-in-depth — network controls complement identity controls |

- Key Decisions:
  - Never rely solely on network location (VPC, security group) for authorization — always validate identity
  - Each microservice assumes its own IAM role — no shared roles between services
  - Inter-service calls authenticated via SigV4 (for AWS-native services) or mTLS (for custom services)
  - Secrets retrieved at runtime from Secrets Manager — never baked into container images or environment variables at build time
  - API Gateway uses IAM authorization (SigV4) for internal APIs, Cognito/JWT for external APIs
- Scaling Path:
  Start with per-service IAM roles + security groups. Add VPC Lattice or App Mesh for service-to-service mTLS as the service count grows. Implement ABAC with service tags for dynamic permission management across hundreds of services.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/identity-and-access-management.html

---

## Scenario Coverage

**Standard Case**: Multi-account production environment with 5-20 AWS accounts, engineering team of 20-100 people
- Approach: IAM Identity Center federated to corporate IdP (Okta/Azure AD) → Permission sets per job function → One IAM role per workload per account → SCPs for baseline guardrails → IAM Access Analyzer for continuous monitoring
- Key Decisions: Which IdP to federate with; which permission sets map to which job functions; how to structure account hierarchy (by team, by application, by environment, or combination)

**Edge Case**: Hybrid workloads running partially on-premises that need AWS API access
- Approach: IAM Roles Anywhere with organization's existing PKI → Certificate-based authentication → Temporary credentials issued per session → No long-term access keys stored on-premises
- If PKI is unavailable: STS AssumeRoleWithSAML via on-premises ADFS, or Systems Manager Hybrid Activations for server management use cases

**Anti-Pattern Case**: Developer asks for AdministratorAccess policy on their deployment role "to avoid permission errors"
- Clarification: "What specific AWS API actions is your deployment failing on? Let's add exactly those permissions rather than granting full admin access. Run the deployment with CloudTrail enabled, capture the Access Denied errors, and we'll build a policy with exactly the actions and resources needed."
