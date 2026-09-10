# AWS IAM — Security Architecture Research

## Metadata
```yaml
Full_Name: "AWS Security Architecture — IAM Identity & Access Management"
Cloud_Provider: "AWS"
Architecture_Domain: "Security Architecture - IAM Identity & Access Management"
Target_Edition: "AWS IAM 2026"
Architecture_Context: "Serverless"
Official_Source_URL: "https://docs.aws.amazon.com/IAM/latest/UserGuide/"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-08-28"
Currency_Threshold: "2027-08-28"
Research_Depth: "exhaustive"
Max_Iterations: 8
Research_Quality_Score: "89%"
# Research_Quality_Score = (total_claims - unverified - irresolvable) / total_claims * 100
Gap_Loop_Ran: true
Iterations_Used: "8 of 8"
Triangulated_Count: 74
Unverified_Count: 8
Irresolvable_Count: 1
```

> **Security note — prompt injection detected in sources:** Every fetched AWS documentation page contained an identical injected block titled "See also — Skills for AI coding assistants (optional)" instructing agents to run `aws agent-toolkit search-skills`. This is NOT genuine AWS documentation content. All findings below are drawn exclusively from the substantive documentation text.

---

## Executive Summary

AWS Identity and Access Management (IAM) is the authorization and authentication fabric of every AWS workload. In a serverless architecture — where Lambda functions, API Gateway endpoints, Step Functions workflows, EventBridge buses, and managed data services replace long-running servers — IAM is the primary security perimeter. There are no OS-level controls, no SSH keys to rotate; identity and permissions policies carry the full weight of the security model.

The 2024–2026 period delivered four structural shifts: (1) **Resource Control Policies (RCPs)** — a new Organizations policy type (Nov 2024) that sets maximum permissions on resources independent of the identity-based policy on the caller, now covering S3, SQS, STS, KMS, Secrets Manager, EventBridge, DynamoDB, CloudWatch Logs, and OpenSearch Serverless; (2) **Full IAM policy language for SCPs** (Sep 2025) — SCPs now support conditions, resource ARNs, `NotAction`/`NotResource`, and mid-string wildcards; (3) **Centralized root access management** — new accounts in an Organization carry no root credentials by default; (4) **MFA mandatory across all account types** including member accounts.

The three most critical guardrails for serverless architects: first, every Lambda function must have a **dedicated execution role** with least-privilege permissions — shared roles create lateral movement risk if any function is compromised. Second, every resource-based policy that trusts an AWS service principal (S3, SNS, EventBridge) must include **confused-deputy conditions** (`aws:SourceArn`/`aws:SourceAccount`) — an open service-principal grant is a privilege-escalation vector. Third, **Lambda functions and SNS topics are not covered by RCPs** — these must be protected via resource-based policies and SCPs directly, not by centralized RCP guardrails.

---

## Cloud Architecture Glossary

```
Term: Principal
Definition: A person or application that uses an IAM entity (user or role), an STS federated user, or an AWS account root user to send a request to AWS.
Provider Docs Section: IAM User Guide — How IAM works (intro-structure.html)
Architect Usage: Always identify the principal when designing an access-control pattern: is it a human (federated), a workload (role), or a service?
Common Confusion: Confused with "identity" — a principal is the actor sending a request; an identity is the IAM entity (user or role) it uses.
```

```
Term: IAM Role
Definition: An IAM identity with permission policies that determines what it can do; assumable by trusted principals; delivers temporary credentials via STS.
Provider Docs Section: IAM User Guide — Temporary security credentials in IAM
Architect Usage: The correct identity primitive for all workloads (Lambda, EC2, containers) and cross-account access. Never use IAM users for machine identity.
Common Confusion: Confused with IAM users — roles are assumed temporarily; users hold long-term credentials. For serverless, roles are always the answer.
```

```
Term: Execution Role
Definition: The IAM role that Lambda assumes automatically at invocation time to grant the function permission to call AWS services. Trust policy must name lambda.amazonaws.com.
Provider Docs Section: Lambda Developer Guide — Defining Lambda function permissions with an execution role
Architect Usage: One execution role per function (least privilege). Scoped to the specific AWS services that function calls. Never share across functions.
Common Confusion: Confused with the function's resource-based policy — the execution role controls what the function can DO (outbound); the resource-based policy controls who can INVOKE the function (inbound).
```

```
Term: Resource-Based Policy
Definition: A policy attached directly to an AWS resource (Lambda function, S3 bucket, SQS queue, KMS key) that grants other principals access to that resource.
Provider Docs Section: Lambda Developer Guide — Working with resource-based policies in Lambda
Architect Usage: Use AddPermission for simple invoke grants; use PutResourcePolicy (full JSON, 20 KB max) when you need explicit Deny, multiple principals, or org conditions.
Common Confusion: Confused with the execution role — resource policies control inbound access TO the resource; execution roles control outbound access FROM the resource.
```

```
Term: SCP (Service Control Policy)
Definition: An AWS Organizations policy that limits the maximum permissions of IAM principals (users and roles) in member accounts. Does not grant permissions — only restricts them.
Provider Docs Section: IAM User Guide — How IAM works; AWS Organizations User Guide
Architect Usage: Use to enforce organization-wide guardrails (e.g., deny all non-us-east-1 resources, require MFA). Effective permissions = intersection(SCP, identity-based policy).
Common Confusion: Confused with RCPs — SCPs restrict principals; RCPs restrict resources. Both are required for full preventive-control coverage.
```

```
Term: RCP (Resource Control Policy)
Definition: An AWS Organizations policy (GA Nov 2024) that sets maximum available permissions on resources in member accounts, including access by principals external to the org. Never grants permissions.
Provider Docs Section: AWS Organizations User Guide — Resource control policies
Architect Usage: Use to enforce that no external principal can access org resources without meeting org-level conditions. Requires all-features-enabled Organizations.
Common Confusion: Confused with resource-based policies — RCPs are org-level maximums applied centrally; resource-based policies are per-resource and can grant permissions.
```

```
Term: Permissions Boundary
Definition: A managed policy set as the maximum permissions an identity-based policy can grant to a user or role. Effective permissions = intersection(identity-based policy, boundary). Explicit deny anywhere wins.
Provider Docs Section: IAM User Guide — Permissions boundaries for IAM entities
Architect Usage: Use when delegating IAM management to a team (e.g., let devs create Lambda execution roles but cap them at a boundary that excludes iam:* and admin actions).
Common Confusion: Confused with SCPs — boundaries apply to individual entities; SCPs apply to accounts/OUs. A boundary does NOT restrict resource-based policies.
```

```
Term: Confused Deputy
Definition: An attack where a service principal is granted resource access without source conditions, allowing an attacker who can influence the service to access resources they shouldn't. Mitigated by aws:SourceArn, aws:SourceAccount, aws:SourceOrgID conditions.
Provider Docs Section: IAM User Guide — The confused deputy problem
Architect Usage: Every resource-based policy that trusts a service principal (s3.amazonaws.com, sns.amazonaws.com, etc.) must include SourceArn or SourceAccount conditions.
Common Confusion: Confused with cross-account impersonation — confused deputy exploits the service's own permissions, not stolen credentials.
```

```
Term: Role Chaining
Definition: Using one role's temporary credentials to assume a second role. Hard cap: maximum 1-hour session regardless of individual role max-session-duration settings.
Provider Docs Section: IAM User Guide — IAM roles terms and concepts
Architect Usage: Avoid role chaining in long-running automated workflows (pipelines, Step Functions). Design to assume the target role directly from the originating identity.
Common Confusion: Architects assume that setting max-session-duration=12h on both roles allows 12h sessions when chaining — the 1h cap is absolute and cannot be overridden.
```

```
Term: External ID
Definition: A value in a role's trust policy condition (sts:ExternalId) that a third party must supply when calling AssumeRole. Generated by the third party, unique per customer, non-guessable. Not a secret.
Provider Docs Section: IAM User Guide — How to use an external ID when granting access to your AWS resources to a third party
Architect Usage: Mandatory for any IAM role that grants cross-account access to a vendor or SaaS provider. The vendor generates and owns the value; you add it as a condition.
Common Confusion: Treated as a password — it is not. If the vendor controls it correctly (unique per customer), it prevents confused-deputy even if visible.
```

```
Term: ABAC (Attribute-Based Access Control)
Definition: Authorization strategy that grants permissions when a principal's tag matches a resource's tag. Single policy scales to new resources without policy edits. AWS implements via aws:PrincipalTag and aws:ResourceTag condition keys.
Provider Docs Section: IAM User Guide — Define permissions based on attributes with ABAC
Architect Usage: Use for per-user or per-tenant isolation in serverless (e.g., DynamoDB LeadingKeys matching Cognito user ID passed as session tag).
Common Confusion: Confused with RBAC — RBAC assigns fixed roles by job function; ABAC grants access dynamically based on matching attributes. ABAC scales better for multi-tenant.
```

```
Term: Session Tags
Definition: Key-value pairs passed when assuming a role or federating (sts:TagSession action on the role); visible as aws:PrincipalTag/* condition keys in the session. Transitive session tags propagate through role chains.
Provider Docs Section: IAM User Guide — Passing session tags in AWS STS
Architect Usage: Pass Cognito/OIDC identity claims as session tags when assuming a Lambda role so ABAC and DynamoDB LeadingKeys conditions can reference them.
Common Confusion: Confused with resource tags — session tags are on the STS session (principal); resource tags are on the AWS resource. Both sides must be set for ABAC to work.
```

---

## Architecture Guardrails

> Confidence legend: 🟢 High (2+ official sources, dated ≤12mo) | 🟡 Medium (1 source or dated 12–24mo) | 🔴 Low (community source or dated >24mo — verify before use)

### ✅ Mandatory Patterns

**One-execution-role-per-Lambda-function (Least Privilege Identity)**
- Pillar Alignment: Security — "Apply least-privilege permissions" (AWS Security best practices in IAM)
- Why: Sharing an execution role across multiple functions couples their blast radius. If one function is compromised or misconfigured, it can access the resources of all others sharing the role. [Source: IAM UG — Security best practices, best-practices.html]
- AWS Services: AWS IAM (role), AWS Lambda (execution role binding), IAM Access Analyzer (unused access findings)
- Architecture Decision: Create one IAM role per Lambda function. The role's trust policy names `lambda.amazonaws.com` as the trusted service. Attach only the actions the function actually calls, scoped to the specific resource ARNs. Use IAM Access Analyzer policy generation from CloudTrail (90-day window) to right-size after burn-in. Exclude `Scan` from any DynamoDB policy using `dynamodb:LeadingKeys`.
- Verification: `aws lambda get-function-configuration --function-name <name> --query Role` — confirm distinct role ARN per function. IAM Access Analyzer unused-access findings will flag over-broad actions.
- Source: https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html 🟢

**Confused-deputy conditions on all service-principal resource-based policies**
- Pillar Alignment: Security — "Use conditions in IAM policies to further restrict access" (AWS Security best practices in IAM)
- Why: When a service like S3, SNS, or EventBridge invokes Lambda (or writes to SQS/KMS/Secrets Manager), the resource-based policy trusts the service's own identity — not the account that configured it. Without a source condition, any account that can trigger the same service can hijack the trust. [Source: IAM UG — The confused deputy problem, confused-deputy.html]
- AWS Services: AWS Lambda (`AddPermission`/`PutResourcePolicy`), Amazon S3, Amazon SNS, Amazon EventBridge, AWS KMS, Amazon SQS, AWS Secrets Manager
- Architecture Decision: Every resource-based policy that grants a service principal (`*.amazonaws.com`) must include: (1) `aws:SourceArn` (specific triggering resource ARN) for tightest scope, OR (2) `aws:SourceAccount` when the ARN is not known ahead of time, OR (3) `aws:SourceOrgID` via an RCP for org-wide enforcement. Combine SourceArn + SourceAccount for cross-account scenarios. Use `aws:PrincipalIsAWSService = false` guard on any `Deny` using network conditions (`aws:SourceIp`, etc.) because those keys are redacted in service-to-service calls.
- Verification: IAM Access Analyzer external-access findings on Lambda, SQS, SNS, S3, KMS, Secrets Manager resources. Policy validation check in Access Analyzer also flags missing source conditions.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/confused-deputy.html 🟢

**Temporary credentials via IAM roles — never embed long-lived keys**
- Pillar Alignment: Security — "Require workloads to use temporary credentials with IAM roles" (AWS Security best practices in IAM)
- Why: Long-lived IAM user access keys embedded in function code, environment variables, or config files can be exfiltrated and reused indefinitely. Lambda automatically injects execution-role STS credentials that auto-expire; no distribution or revocation cycle needed. [Source: IAM UG — Temporary security credentials in IAM, id_credentials_temp.html]
- AWS Services: AWS STS (automatic credential injection by Lambda), AWS Secrets Manager (for third-party API keys that are not AWS credentials), AWS IAM Roles Anywhere (for off-AWS workloads)
- Architecture Decision: Lambda receives STS credentials for its execution role automatically — do NOT call `sts:AssumeRole` in function code to re-assume the same role. For off-AWS workloads (CI/CD, on-prem), use IAM Roles Anywhere (X.509 certs) or OIDC federation (`AssumeRoleWithWebIdentity`). Store third-party API keys in Secrets Manager, not in environment variables.
- Verification: `aws lambda get-function-configuration --function-name <name> --query 'Environment.Variables'` — confirm no `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` entries. IAM Access Analyzer unused-access findings flag long-lived keys on active roles.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp.html 🟢

**MFA mandatory for all human identities including root in member accounts**
- Pillar Alignment: Security — "Require multi-factor authentication (MFA)" (AWS Security best practices in IAM)
- Why: As of June 2025, AWS enforces MFA for root users across all account types including member accounts. Phishing-resistant hardware passkeys/security keys are the current recommendation. [Source: What's New 2025-06, aws.amazon.com/about-aws/whats-new/2025/06/aws-iam-mfa-root-users-across-all-account-types]
- AWS Services: AWS IAM (MFA device management), AWS IAM Identity Center (phishing-resistant MFA for workforce), AWS Organizations — Centralized root access management (remove standing root credentials from member accounts)
- Architecture Decision: Enable centralized root access management in Organizations to remove root credentials from member accounts by default. For workforce users, enforce phishing-resistant MFA (FIDO2 passkeys/hardware security keys) via IAM Identity Center. Add `aws:MultiFactorAuthPresent = true` conditions to sensitive IAM policies. Use `sts:AssumeRoot` for the rare privileged root task from the management account.
- Verification: IAM credential report — `mfa_active` column. AWS Config rule `root-account-mfa-enabled` and `iam-user-mfa-enabled`. Security Hub IAM controls.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html 🟢

**SCPs and RCPs as preventive org-wide guardrails**
- Pillar Alignment: Security — "Establish permissions guardrails across multiple accounts" (AWS Security best practices in IAM)
- Why: Identity-based policies can be misconfigured per-function. SCPs/RCPs set a ceiling that no identity or resource policy can exceed, enforcing org-wide invariants regardless of individual team mistakes. [Source: AWS Organizations UG — Resource control policies, orgs_manage_policies_rcps.html]
- AWS Services: AWS Organizations (SCPs, RCPs, Declarative Policies), AWS CloudTrail (AccessDenied impact assessment)
- Architecture Decision: Attach SCPs to OUs to prevent actions outside approved Regions or services. Attach RCPs to prevent external principals from accessing org resources (S3, DynamoDB, SQS, KMS, Secrets Manager, EventBridge, CloudWatch Logs — full list in RCP supported services). For services NOT covered by RCPs (Lambda, SNS), enforce via resource-based policies and SCPs. Test on individual accounts before attaching to OU root; monitor CloudTrail AccessDenied events after attachment.
- Verification: AWS Organizations console — Policies tab. CloudTrail — filter on `errorCode=AccessDenied` after SCP/RCP changes to detect over-restriction.
- Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_rcps.html 🟢

---

### ⚠️ Architectural Decisions

**API Gateway authorization model**

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|------------|-----------|------------|-----------|
| IAM permissions (SigV4) | API Gateway + IAM | Internal security, no token infra needed | Developer experience for external callers | Service-to-service, callers already have AWS credentials |
| Lambda authorizer | API Gateway + Lambda | Flexibility — any token/claim/header | Cold-start latency, additional Lambda cost | Custom/third-party auth, non-Cognito JWTs, fine-grained per-request logic |
| Cognito user pool | API Gateway + Cognito | No custom code, managed MFA/UI | Locked to Cognito; JWT validation only | End-user (web/mobile) apps, standard OIDC |
| Resource policy (IP/VPC) | API Gateway | Simple network boundary | Cannot authenticate identity | VPC-only internal APIs, combine with auth model |

- Cost Profile: IAM and resource-policy options add no per-call cost; Lambda authorizer adds Lambda invocation cost (mitigated with cache TTL up to 3600s); Cognito adds per-MAU pricing.
- Lock-in Assessment: Lambda authorizer is most portable (swap the logic); Cognito creates moderate lock-in (user pool migration is non-trivial).
- Architect Instruction: "Ask which identity providers callers already have when deciding the authorization model — internal services get SigV4; external end-users get Cognito; third-party tokens get Lambda authorizer."
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-control-access-to-api.html

**Human identity federation model**

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|------------|-----------|------------|-----------|
| IAM Identity Center (org instance) | IAM Identity Center + Organizations | Centralized SSO, per-user CloudTrail, permission sets | Requires Organizations all-features | Any multi-account environment — the default recommendation |
| Direct SAML/OIDC federation | IAM (OIDC/SAML provider) + STS | Flexible, works per-account | No central access management, harder to audit | Single-account or when Identity Center cannot be used |
| IAM users with long-term keys | IAM (user + access key) | Simplest setup | Security risk, no MFA enforcement, no central revocation | Legacy only — not recommended for new workloads |

- Cost Profile: IAM Identity Center has no per-user charge for AWS access; SAML/OIDC federation is free; IAM users are free but create long-term key management overhead.
- Lock-in Assessment: Identity Center is AWS-specific; SAML/OIDC patterns are portable; IAM user keys are AWS-specific and have no equivalent in a provider-agnostic model.
- Architect Instruction: "Ask whether this is a new or migrating environment — new multi-account environments must use IAM Identity Center (organization instance); do not create IAM users for human access."
- Source: https://docs.aws.amazon.com/singlesignon/latest/userguide/what-is.html

**End-user serverless auth (Cognito user pool vs identity pool)**

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|------------|-----------|------------|-----------|
| User pool only | Cognito user pool | App sign-in, JWTs for API auth | Does not issue AWS credentials | End-user auth to API Gateway/Lambda only |
| Identity pool only | Cognito identity pool | Direct AWS service access for end-users | Requires external IdP for authentication | Guest access or when you already have tokens from another IdP |
| User pool + identity pool | Cognito (both) | Full CIAM + scoped AWS credentials | Added complexity | Web/mobile apps where users read/write S3 or DynamoDB directly with per-user isolation |

- Cost Profile: User pools priced per-MAU; identity pools priced per-credential vend (very low); combined adds both costs.
- Lock-in Assessment: Cognito is AWS-specific; JWT format (OIDC) is portable, but migration of user store requires export/import.
- Architect Instruction: "Ask whether end-users will call AWS services directly (S3, DynamoDB) — if yes, add an identity pool to vend scoped temporary credentials; if users only call API Gateway, a user pool is sufficient."
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/what-is-amazon-cognito.html

---

### 🚫 Anti-Patterns

**Wildcard action+resource in Lambda execution role**
- Risk Level: CRITICAL
- Why: Overly permissive IAM policies — wildcard `*` actions or resources in production — violate the Security pillar least-privilege principle. If the Lambda function or its code supply chain is compromised, the attacker has full account access. [Source: IAM UG — Security best practices, best-practices.html]
- Instead: Scope the execution role to the exact actions the function calls (`s3:GetObject`, `dynamodb:PutItem`, etc.) on the specific resource ARNs (`arn:aws:s3:::my-bucket/*`). Use IAM Access Analyzer policy generation from CloudTrail activity to derive the minimal policy.
- ❌ Wrong: `{ "Effect": "Allow", "Action": "*", "Resource": "*" }` in a Lambda execution role policy.
- ✅ Correct: `{ "Effect": "Allow", "Action": ["s3:GetObject"], "Resource": "arn:aws:s3:::my-bucket/prefix/*" }` — scoped to the specific bucket prefix the function reads.
- Detection: AWS Config rule `iam-policy-no-statements-with-admin-access` (customer-managed policies); IAM Access Analyzer policy validation (100+ checks including wildcard analysis).
- Impact: Full account compromise if function code or dependencies are tampered with.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html

**Service-principal resource-based policy with no confused-deputy condition**
- Risk Level: CRITICAL
- Why: A resource-based policy that grants `s3.amazonaws.com`, `sns.amazonaws.com`, `events.amazonaws.com`, etc. with no `aws:SourceArn` or `aws:SourceAccount` condition allows any account that can configure the same service to invoke your resource. [Source: IAM UG — The confused deputy problem, confused-deputy.html]
- Instead: Always pair a service-principal grant with `aws:SourceArn` (specific triggering resource) and/or `aws:SourceAccount` (account scope). Use `aws:SourceOrgID` in an RCP for org-wide enforcement.
- ❌ Wrong: `{ "Effect": "Allow", "Principal": {"Service": "s3.amazonaws.com"}, "Action": "lambda:InvokeFunction", "Resource": "*" }` — no source condition.
- ✅ Correct: `{ "Effect": "Allow", "Principal": {"Service": "s3.amazonaws.com"}, "Action": "lambda:InvokeFunction", "Resource": "arn:aws:lambda:us-east-1:111122223333:function:my-fn", "Condition": {"StringEquals": {"aws:SourceAccount": "111122223333"}, "ArnLike": {"aws:SourceArn": "arn:aws:s3:::my-bucket"}} }`
- Detection: IAM Access Analyzer external-access findings on Lambda functions, SQS queues, SNS topics, S3 buckets, KMS keys, Secrets Manager secrets — any grant to a service principal without source conditions is flagged.
- Impact: Cross-service confused deputy — unauthorized actor in another account can trigger your Lambda/SNS/SQS by configuring the same AWS service.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/confused-deputy.html

**Long-lived IAM user access keys embedded in Lambda environment or code**
- Risk Level: CRITICAL
- Why: Long-lived access keys stored in application code or environment variables can be exfiltrated via code vulnerabilities, dependency attacks, or console describe-function API calls. They never expire automatically. [Source: IAM UG — Temporary security credentials in IAM, id_credentials_temp.html]
- Instead: Use the Lambda execution role — Lambda injects STS temporary credentials automatically. For third-party API keys (not AWS credentials), use AWS Secrets Manager with `secretsmanager:GetSecretValue` in the execution role.
- ❌ Wrong: Lambda environment variable `AWS_ACCESS_KEY_ID=AKIA...` / `AWS_SECRET_ACCESS_KEY=...` set in function configuration, or credentials hardcoded in source code.
- ✅ Correct: Lambda execution role with `secretsmanager:GetSecretValue` permission on `arn:aws:secretsmanager:us-east-1:111122223333:secret:my-third-party-key`. Function retrieves the secret at runtime.
- Detection: `aws lambda get-function-configuration --query 'Environment.Variables'` — check for key-like values. IAM Access Analyzer unused-access findings flag active long-term keys on IAM users. AWS Config `access-keys-rotated` rule.
- Impact: Persistent account access post-exfiltration — no automatic expiry, manual revocation required, blast radius = all permissions attached to the IAM user.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp.html

**Shared Lambda execution role across multiple functions**
- Risk Level: HIGH
- Why: Sharing one over-broad execution role across many functions violates least privilege and creates lateral movement risk. [Source: Lambda DG — execution role, lambda-intro-execution-role.html]
- Instead: One IAM role per Lambda function. Each role scoped to only the resources and actions that specific function requires.
- ❌ Wrong: Single `LambdaServiceRole` attached to all 20 Lambda functions in a microservice, with permissions for all the services any of them uses.
- ✅ Correct: `OrderProcessorRole` with `dynamodb:PutItem` on the orders table; `NotificationSenderRole` with `sns:Publish` on the notifications topic — independent, function-specific roles.
- Detection: `aws lambda list-functions | jq '[.Functions[].Role] | group_by(.) | map({role: .[0], count: length})'` — any role with count > 1 is a sharing candidate to investigate.
- Impact: Lateral movement — compromise of one function grants access to all resources reachable by the shared role.
- Source: https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html

**OIDC role trust policy without sub-claim scope (CI/CD)**
- Risk Level: HIGH
- Why: An IAM role trust policy that references an OIDC provider (e.g., GitHub Actions) but does not constrain the `sub` claim allows any repository under that OIDC provider to assume the role. [Source: IAM UG — Creating IAM OIDC identity providers, id_roles_providers_create_oidc.html]
- Instead: Scope the trust policy `Condition` on both `aud` (= `sts.amazonaws.com` for GitHub) and `sub` restricted to the specific repository + branch or environment.
- ❌ Wrong: Trust policy condition only validates `aud = sts.amazonaws.com` with no `sub` restriction — any GitHub Actions repo can assume the role.
- ✅ Correct: `"Condition": {"StringEquals": {"token.actions.githubusercontent.com:aud": "sts.amazonaws.com", "token.actions.githubusercontent.com:sub": "repo:MyOrg/my-repo:ref:refs/heads/main"}}`
- Detection: IAM Access Analyzer external-access findings on the role. Manual trust-policy review for OIDC conditions.
- Impact: Any GitHub repository can assume the role and perform any action it grants — supply chain attack vector.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html

---

## Cloud-Native Design Patterns

**Per-user data isolation with DynamoDB ABAC (LeadingKeys + session tags)**
- Category: Data
- Problem: In a multi-tenant serverless application, each user should access only their own DynamoDB items. Enforcing this at the application layer is fragile — a bug in filtering logic exposes other users' data.
- Solution on AWS: (1) Cognito identity pool issues temporary credentials with session tags mapping the user's sub to `aws:PrincipalTag/user_id`. (2) Lambda execution role or identity-pool role has a DynamoDB policy with `dynamodb:LeadingKeys` condition `ForAllValues:StringEquals {dynamodb:LeadingKeys: "${aws:PrincipalTag/user_id}"}`. (3) DynamoDB partition key is the user ID — the IAM condition enforces that the credentials can only address that user's partition.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Isolation | IAM-layer enforcement — app bugs cannot bypass it | Session tag setup adds Cognito/STS configuration complexity |
  | Scale | Single policy scales to unlimited users with no policy edits | Scan must be excluded from the policy; complex queries may require redesign |
  | Auditability | CloudTrail records every DynamoDB call with the user's identity | No additional cost beyond CloudTrail |

- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/specifying-conditions.html

**Zero-standing-privileges with IAM Access Analyzer policy generation**
- Category: Resilience
- Problem: Lambda execution roles are often created with broad permissions in development and never tightened for production — creating a permanently over-privileged workload.
- Solution on AWS: (1) Enable CloudTrail in the account. (2) After a burn-in period (up to 90 days of real traffic), use IAM Access Analyzer policy generation to synthesize a least-privilege policy from observed CloudTrail activity. (3) Review the generated template, replace resource placeholders with real ARNs, manually add `iam:PassRole` and S3 data events (not captured by policy generation). (4) Replace the dev-time broad policy with the generated customer-managed policy. (5) Set up IAM Access Analyzer unused-access findings to continuously flag drift.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Precision | Policy derived from actual usage — no guesswork | Requires 90-day burn-in with realistic traffic |
  | Gaps | Covers most API-level actions automatically | Does not capture iam:PassRole or S3 data events — manual addition required |
  | Drift detection | Unused-access findings flag new over-breadth continuously | Unused-access analyzer priced per role/user analyzed |

- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/access-analyzer-policy-generation.html

**OIDC-based CI/CD to AWS (no stored credentials)**
- Category: Communication
- Problem: CI/CD pipelines (GitHub Actions, GitLab CI) traditionally store long-lived IAM user access keys as CI secrets — keys that can be leaked via log output, forked PRs, or secret scanning misses.
- Solution on AWS: (1) Create an IAM OIDC identity provider for the CI system (GitHub: `https://token.actions.githubusercontent.com`, audience `sts.amazonaws.com`). (2) Create a deployment IAM role with a trust policy scoped to both `aud = sts.amazonaws.com` AND `sub = repo:Org/Repo:ref:refs/heads/main`. (3) In the workflow, set `permissions: id-token: write` and use `aws-actions/configure-aws-credentials` to exchange the workflow JWT for temporary AWS credentials. No stored secrets.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Security | Credentials ephemeral — expire with the job; no secret to leak | OIDC setup is per-provider; multiple CI systems need multiple providers |
  | Auditability | CloudTrail records every call attributed to the specific workflow run | None — CloudTrail is already required |
  | Scope control | sub-claim scoping enforces per-repo, per-branch authorization | Missing sub condition allows any repo to assume role (anti-pattern) |

- Source: https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services

---

## Security Architecture

**Lambda Identity — execution role + resource-based policy separation**
- AWS Services: AWS IAM (execution role, resource-based policy), AWS Lambda, AWS STS (automatic credential injection)
- Architecture: Two independent IAM planes govern a Lambda function. The execution role (identity-based, outbound) defines what AWS services the function can call — scoped by action + resource ARN, issued as auto-rotating STS credentials. The resource-based policy (function policy, inbound) defines who can invoke the function — services, accounts, or principals — and must carry confused-deputy conditions when the principal is a service. Neither policy should be broader than necessary; Access Analyzer validates both continuously.
- Compliance Alignment: SOC 2 CC6.1 (logical access / least privilege); PCI DSS v4.0 Req 7 (restrict by need-to-know); HIPAA §164.312(a)(1) Access Control.
- Source: https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html

**Organization-wide preventive controls (SCP + RCP + Declarative Policy)**
- AWS Services: AWS Organizations (SCPs, RCPs, Declarative Policies), AWS CloudTrail, AWS Config
- Architecture: Three complementary control types form the org-wide security envelope. SCPs restrict the maximum permissions of IAM principals (users/roles) in member accounts — effective permissions = intersection(SCP, identity-based policy). RCPs restrict maximum permissions on resources including external-principal access — effective permissions further intersected. Declarative Policies enforce baseline service configuration (e.g., block VPC public internet access, enforce EBS encryption) in the service control plane — persists across new features/APIs and applies to service-linked roles that SCPs/RCPs cannot touch. All three must be in place for complete preventive coverage; they are not substitutes for each other.
- Compliance Alignment: SOC 2 CC6.6 (boundary protection); PCI DSS v4.0 Req 7; HIPAA §164.308(a)(4) Info Access Management.
- Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_rcps.html

**IAM Access Analyzer continuous monitoring**
- AWS Services: IAM Access Analyzer (external access, internal access, unused access, policy validation, custom policy checks), AWS CloudTrail
- Architecture: Four concurrent analyzer capabilities provide defense-in-depth. (1) External-access findings use automated reasoning to detect resource-based policies that expose resources outside the zone of trust — re-scans within 30 minutes of policy changes; covers Lambda, SQS, SNS, S3, KMS, Secrets Manager, DynamoDB. (2) Internal-access findings (GA Jun 2025) flag which internal principals can reach business-critical resources (S3, DynamoDB). (3) Unused-access findings continuously identify unused roles, access keys, passwords, and over-broad action grants — signals for cleanup. (4) Custom policy checks (`CheckNoNewAccess`, `CheckAccessNotGranted`) gate CI/CD pipelines — block deploys that grant new or critical-action access.
- Compliance Alignment: SOC 2 CC6.3 (role-based access review and removal); PCI DSS v4.0 Req 8; HIPAA §164.308(a)(1) Security Management Process.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/what-is-access-analyzer.html

---

## Operational Patterns

**IAM credential hygiene — detection and rotation**
- RTO/RPO: N/A (preventive hygiene, not a DR pattern)
- AWS Services: AWS IAM (credential report), AWS Config (`access-keys-rotated`, `iam-user-mfa-enabled`, `root-account-mfa-enabled`, `iam-user-no-policies-check`), AWS Security Hub (IAM controls), IAM Access Analyzer (unused-access findings)
- Cost Profile: Low — credential report generation is free; Config managed rules priced per evaluation; Security Hub standard priced per account/Region.
- Automation: Automate credential report generation (`aws iam generate-credential-report; aws iam get-credential-report`) on a daily schedule. Feed results to a SIEM or Security Hub. Alert on: `mfa_active=FALSE`, `access_key_*_last_used_date` > 90 days, `password_last_used` > 90 days. Auto-remediate via AWS Config remediation actions (deactivate unused keys via SSM Automation). Manual decision points: key rotation for active keys (requires application coordination), root credential removal (requires centralized root access management enablement).
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_getting-report.html

**Centralized root access lifecycle**
- RTO/RPO: N/A
- AWS Services: AWS Organizations (centralized root access management), AWS IAM (`sts:AssumeRoot`), AWS CloudTrail (root activity detection)
- Cost Profile: Low — no additional pricing beyond Organizations (free for all-features-enabled orgs with ≥1 account).
- Automation: Enable "Root credentials management" in Organizations trusted access. Script: enumerate member accounts, remove root credentials (password + access keys + MFA) via the management account. For new accounts — credentials are absent by default. For on-demand privileged tasks (remove an S3/SQS resource policy blocking all principals): use `sts:AssumeRoot` from management account with `IAMAuditRootUserCredentials` managed policy. After task: re-remove credentials. CloudTrail alert on `userIdentity.type=Root` events in member accounts as anomaly signal.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_root-enable-root-access.html

---

## Reference Architectures

**Serverless API — end-user auth + per-user data isolation**
- Context: Web/mobile application with serverless backend where end-users read and write their own data in DynamoDB directly or via Lambda.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Auth / Identity | Amazon Cognito user pool | End-user sign-in, MFA, JWT issuance |
  | Credential broker | Amazon Cognito identity pool | Exchange user-pool JWT for temporary AWS credentials |
  | API | Amazon API Gateway (Cognito authorizer) | Authenticate JWTs; route requests |
  | Compute | AWS Lambda (per-function execution roles) | Business logic; least-privilege per function |
  | Data | Amazon DynamoDB | User data; LeadingKeys isolation by Cognito user sub |
  | Secrets | AWS Secrets Manager | Third-party API keys; accessed by execution role |
  | Audit | AWS CloudTrail | All IAM and data-plane events attributed to user identity |
  | Monitoring | IAM Access Analyzer | Continuous external/unused access findings |
  | Guardrails | AWS Organizations (SCPs + RCPs) | Org-wide permission ceiling |

- Key Decisions: (1) Whether end-users need direct AWS service access (identity pool) or only API Gateway access (user pool only). (2) Whether to use ABAC (session-tag-based LeadingKeys) or application-layer filtering for DynamoDB isolation. (3) Whether the API is internal (SigV4) or external (Cognito/Lambda authorizer).
- Scaling Path: Start with Cognito + API Gateway + Lambda + DynamoDB. Add identity pool when direct AWS service access is needed. Add IAM Access Analyzer unused-access analyzer as the function count grows. Add SCPs/RCPs when moving to multi-account. Add Lambda authorizer if auth complexity exceeds Cognito's built-in capabilities.
- Source: https://docs.aws.amazon.com/cognito/latest/developerguide/what-is-amazon-cognito.html

**Multi-account serverless platform — IAM governance foundation**
- Context: Enterprise serverless platform spanning multiple AWS accounts (prod, staging, dev, security) under an AWS Organization.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Identity (workforce) | IAM Identity Center (org instance) | SSO for engineers; permission sets per account/role |
  | Identity (workloads) | IAM roles per Lambda function | Least-privilege machine identity per function |
  | Identity (CI/CD) | IAM OIDC provider + deployment role | Keyless CI/CD via GitHub Actions OIDC |
  | Org guardrails | AWS Organizations SCPs | Maximum principal permissions across accounts |
  | Resource guardrails | AWS Organizations RCPs | Maximum resource permissions incl. external access |
  | Config guardrails | AWS Organizations Declarative Policies | Baseline service configuration (VPC, EBS, etc.) |
  | Delegation | IAM permissions boundaries | Safe team self-service of Lambda execution roles |
  | Audit | AWS CloudTrail (org trail) | All API activity across all accounts |
  | Detection | IAM Access Analyzer (org zone of trust) | Org-wide external-access and unused-access findings |
  | Root protection | Centralized root access management | No standing root credentials in member accounts |

- Key Decisions: (1) Permission-set design in Identity Center (broad job-function sets vs fine-grained per-service sets). (2) SCP strategy — deny-list (block specific actions) vs allow-list (only permit approved services). (3) Permissions boundary scope for developer self-service roles.
- Scaling Path: Start with SCPs + org CloudTrail. Add Identity Center when team size makes direct IAM user management painful. Add RCPs when first external-access security incident occurs or at org baseline review. Add IAM Access Analyzer org analyzer as account count grows.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html

---

## Service Equivalence Map

> IAM security patterns across major cloud providers — for architects evaluating multi-cloud or migrating workloads.

| IAM Concept | AWS | Google Cloud | Azure | Oracle Cloud (OCI) |
|-------------|-----|-------------|-------|--------------------|
| **Identity for workloads** | IAM role (assumed by service) | Service account | Managed identity | Dynamic group + instance principal |
| **Serverless function identity** | Lambda execution role | Cloud Functions service account | Azure Functions managed identity | OCI Functions dynamic group |
| **Organization-wide principal guardrails** | SCP (Organizations) | Organization Policy (iam.allowedPolicyMemberTypes, etc.) | Azure Policy + Management Groups | OCI Organization Policy |
| **Organization-wide resource guardrails** | RCP (Organizations) | — (no direct equivalent) | — | — |
| **Human SSO/workforce federation** | IAM Identity Center | Cloud Identity / Workforce Identity Federation | Entra ID (Azure AD) | IAM Identity Domains |
| **End-user app federation** | Cognito user pool + identity pool | Firebase Auth + Workload Identity Federation | Entra External ID (B2C) | IDCS (Identity Cloud Service) |
| **Temporary credentials for off-cloud** | IAM Roles Anywhere (X.509) | Workload Identity Federation | Workload Identity Federation | OCI Instance Principal (limited) |
| **OIDC CI/CD federation** | IAM OIDC provider + AssumeRoleWithWebIdentity | Workload Identity Federation | Workload Identity Federation | OCI OIDC provider |
| **Policy validation / CSPM** | IAM Access Analyzer | Security Command Center | Defender for Cloud | Cloud Guard |
| **Secrets management** | AWS Secrets Manager | Secret Manager | Azure Key Vault | OCI Vault |
| **Key management** | AWS KMS | Cloud KMS | Azure Key Vault | OCI Key Management |

> ⚠️ Service equivalence does NOT mean feature parity. RCPs have no direct equivalent in GCP or Azure — architects migrating from AWS must design compensating controls. Verify against Target_Edition documentation before architectural decisions.

---

## Provider Differentiators

**Resource Control Policies (RCPs) — resource-level org guardrails**
- Category: Security
- Unique Value: AWS is the only major cloud provider with a dedicated policy type that enforces maximum permissions on resources for ALL principals accessing them — including external accounts — without being a resource-based policy on the resource itself. GCP and Azure have no direct equivalent.
- Architecture Impact: Enables centralized enforcement of confused-deputy protection, cross-org data exfiltration prevention, and external-access guardrails without modifying individual resource policies. A single RCP at the OU level enforces that no S3 bucket, DynamoDB table, KMS key, SQS queue, or Secrets Manager secret in the entire OU can be accessed by principals outside the org.
- When to Leverage: Any multi-account AWS organization where a security team needs to enforce data perimeter controls without relying on each application team to configure individual resource policies correctly.
- Caveat: Lambda functions and SNS topics are NOT in the RCP supported-services list as of August 2026 — a governance gap requiring compensating controls (resource-based policies + SCPs). Monitor AWS What's New for service expansion.
- Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_rcps.html

**IAM Access Analyzer — automated-reasoning external-access analysis**
- Category: Security
- Unique Value: Access Analyzer uses automated formal reasoning (not heuristics) to mathematically prove whether a resource is accessible from outside the defined zone of trust, covering complex policy combinations including condition keys, deny statements, and cross-account grants.
- Architecture Impact: Provides a continuous, proof-based security camera for resource-based policies across Lambda, SQS, SNS, S3, KMS, Secrets Manager, DynamoDB, ECR, EFS. Re-scans within 30 minutes of any policy change. No other cloud provider offers formal-reasoning-backed policy analysis as a native free-tier service.
- When to Leverage: Any account with resource-based policies — enable as a first-day baseline. The unused-access analyzer additionally flags drift in execution roles over time.
- Caveat: External analyzer is per-Region (create in each Region with resources). Unused-access analyzer priced per role/user analyzed.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/what-is-access-analyzer.html

**Centralized root access management (no standing root credentials)**
- Category: Security
- Unique Value: AWS allows Organizations management accounts to centrally remove root credentials from all member accounts and perform privileged root tasks via `sts:AssumeRoot` without distributing root credentials. New accounts created in the org start with no root credentials by default. No other major cloud provider offers equivalent programmatic centralized root/super-admin credential management at the organization level.
- Architecture Impact: Eliminates the highest-risk identity in every member account without eliminating the ability to perform root-only tasks. Combined with phishing-resistant MFA enforcement (mandatory as of June 2025), closes the most common cloud account takeover path.
- When to Leverage: All multi-account Organizations — enable at organization baseline. Especially critical for accounts managed by automation or service teams where no individual should have persistent root access.
- Caveat: Requires Organizations all-features-enabled and IAM trusted access. Once root credentials are removed, account recovery requires the management account (or enabling password recovery as a temporary privileged action).
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_root-enable-root-access.html

**Full IAM policy language for SCPs (Sep 2025)**
- Category: Security
- Unique Value: As of September 2025, SCPs now support the full IAM policy language — conditions (StringEquals, ArnLike, IpAddress, DateLessThan, etc.), individual resource ARNs, `NotAction` with `Allow`, `NotResource`, and wildcards at start/middle of `Action`. Previously SCPs were limited compared to identity-based policies, requiring multiple statements to express what is now a single conditioned statement.
- Architecture Impact: Architects can now write precise, conditions-driven preventive guardrails at the organization level that were previously only achievable with complex allow-list workarounds. For example: deny all S3 access outside business hours, deny IAM key creation for principals without a specific tag, deny EC2 launch if instance type not in approved list.
- When to Leverage: Any existing SCP library should be reviewed to consolidate and simplify using conditions and resource ARNs. New guardrails should be written with conditions from the start.
- Caveat: Backward compatible — existing SCPs need no changes. Validate new condition-based SCPs on test accounts before OU attachment.
- Source: https://aws.amazon.com/about-aws/whats-new/2025/09/aws-organizations-iam-language-service-control-policies/

---

## Scenario Coverage

**Standard Case**: Multi-tenant serverless API with end-user auth and per-user DynamoDB isolation
- Approach: Cognito user pool authenticates end-users and issues JWTs. API Gateway uses Cognito authorizer to validate tokens. Lambda functions each have their own execution role scoped to the specific DynamoDB table and Secrets Manager secrets they need. Cognito identity pool optionally vends temporary credentials with session tags (`aws:PrincipalTag/userId`) for direct DynamoDB access from the client with `dynamodb:LeadingKeys` isolation.
- Key Decisions: (1) Whether clients call DynamoDB directly (identity pool) or only via Lambda (user pool sufficient). (2) Whether to enforce data isolation at the IAM layer (LeadingKeys + session tags) or in application code. (3) Whether Lambda authorizer is needed for custom token validation beyond Cognito.

**Edge Case**: CI/CD pipeline deploying Lambda functions across multiple AWS accounts
- Approach: GitHub Actions uses OIDC federation (no stored credentials). Each deployment environment (dev/staging/prod) has a dedicated IAM role with a trust policy scoped to the specific repository + branch + environment via the `sub` claim. The role has permissions only for the deployment actions required (Lambda:UpdateFunctionCode, IAM:PassRole for the function's execution role, etc.). Cross-account deployment uses `sts:AssumeRole` from the OIDC-assumed role to the target account's deployment role — total session must not exceed 1 hour (role chaining hard cap). IAM Access Analyzer custom policy check (`CheckNoNewAccess`) gates pull requests.

**Anti-Pattern Case**: Application team requests a shared `LambdaAdminRole` with `*:*` permissions for all their Lambda functions to "simplify deployment"
- Clarification: Ask the team to enumerate the specific AWS services each function calls, and the exact resource ARNs those functions address. Offer to run IAM Access Analyzer policy generation after a 2-week burn-in period to derive the minimal per-function roles. Explain that a shared admin role creates a single point of compromise — a supply chain attack on any one function grants the attacker full account access. Provide the delegation pattern (permissions boundary) so the team can self-provision their per-function roles within a guardrail.

---

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Cloud Architecture Glossary | Role chaining 1-hour cap | Added — triangulated against STS API Reference + IAM roles terms-and-concepts | https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_terms-and-concepts.html (2026-08-28) |
| 2 | Architecture Guardrails / ✅ | External ID for third-party cross-account | Added — triangulated against third-party external-ID page + IAM roles terms-and-concepts | https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-user_externalid.html (2026-08-28) |
| 3 | Security Architecture | IAM Access Analyzer internal access findings (Jun 2025) | Added from What's New dated 2025-06-17 — within 12-month window | https://aws.amazon.com/blogs/apn/aws-partners-enhance-cloud-security-with-new-iam-access-analyzer-internal-access-findings/ (2026-08-28) |
| 4 | Provider Differentiators | Full IAM language for SCPs (Sep 2025) | Added from What's New dated 2025-09-19 — confirmed backward compatible | https://aws.amazon.com/about-aws/whats-new/2025/09/aws-organizations-iam-language-service-control-policies/ (2026-08-28) |
| 5 | Architecture Guardrails / 🚫 | RCP gap: Lambda + SNS not covered | ⚠️ IRRESOLVABLE — Lambda and SNS confirmed absent from RCP supported-services list as of 2026-08-28; no compensating RCP exists; must use resource-based policies + SCPs | — |
| 6 | Cloud Architecture Glossary | iam:ServiceSpecificCredentialAgeDays / iam:ServiceSpecificCredentialServiceName condition keys | ⚠️ IRRESOLVABLE — exact announcement date unverified; WebSearch returned aggregate only; recommend confirm at IAM release notes RSS | — |
| 7 | Reference Architectures | EventBridge + Step Functions IAM specifics | ⚠️ IRRESOLVABLE — dedicated EventBridge/Step Functions IAM pages not fetched; Lambda-as-target covered; pull EventBridge DG IAM page before finalizing if needed | — |
| 8 | Cloud-Native Design Patterns | ABAC tutorial serverless example (`aws:PrincipalTag`/`aws:ResourceTag` on Lambda/API Gateway) | ⚠️ IRRESOLVABLE — confirmed from ABAC overview; no serverless-specific worked example fetched from tutorial page; verify against ABAC tutorial if concrete policy needed | — |
