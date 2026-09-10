---
name: securing-aws-iam-serverless
description: "Applies AWS IAM security architecture patterns for serverless workloads (Lambda, API Gateway, EventBridge, Step Functions) targeting AWS IAM 2026. Use when designing or reviewing IAM identity, permissions, execution roles, confused-deputy protection, org-wide guardrails, or identity federation for serverless architectures on AWS."
---

## Function

Specialist in AWS IAM security architecture for serverless workloads — execution roles, resource-based policies, confused-deputy prevention, org-wide guardrails (SCPs/RCPs/Declarative Policies), identity federation, and continuous access analysis.

## Version Context

**Technology**: AWS IAM — Identity & Access Management
**Target version**: AWS IAM 2026
**Research date**: 2026-08-28
**Support status**: Active

**Key changes (2024–2026)**:
- **Resource Control Policies (RCPs)** — GA Nov 2024; sets max permissions on resources for ALL principals (including external); covers S3, SQS, STS, KMS, Secrets Manager, EventBridge, DynamoDB, CloudWatch Logs. **Lambda + SNS are NOT covered.**
- **Full IAM policy language for SCPs** — Sep 2025; conditions, resource ARNs, `NotAction`/`NotResource`, mid-string wildcards now supported in SCPs
- **Centralized root access management** — new org member accounts start with no root credentials by default
- **MFA mandatory across all account types** — including member accounts, enforced Jun 2025; phishing-resistant hardware passkeys recommended
- **IAM Access Analyzer internal-access findings** — GA Jun 2025; flags which internal principals can reach business-critical resources

**Deprecated**: IAM users for machine identity (always use roles). IAM users for human access in multi-account (migrate to IAM Identity Center).

⚠️ **CRITICAL — Agent Warning**:
This skill targets AWS IAM 2026 patterns. RCP coverage does NOT include Lambda or SNS as of August 2026 — compensate with resource-based policies + SCPs. Reject any pre-2024 pattern that shares execution roles, omits confused-deputy conditions, or stores AWS credentials in Lambda environment variables.

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — ✅⚠️🚫 operational patterns
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 6 test scenarios
- **[Policy Patterns](./blueprints/policy-patterns.md)** — Full IAM policy JSON: ❌ wrong / ✅ correct
- **[Integration Patterns](#integration-patterns)** — Lambda, Cognito, OIDC CI/CD, Organizations wiring
- **[Verification Loop](#verification-loop)** — AWS CLI validation commands
- **[Quick Reference](#quick-reference)** — Critical limits and decision checklist

---

## Blueprints & Guardrails

### ✅ Always Do

For full IAM policy JSON examples, see [Policy Patterns](./blueprints/policy-patterns.md).

**One execution role per Lambda function (least-privilege identity)**
Create one IAM role per Lambda function. Trust policy must name `lambda.amazonaws.com` as the only trusted service. Permissions scoped to exact actions (`s3:GetObject`, `dynamodb:PutItem`) on specific resource ARNs. Sharing a role across functions couples blast radius — a compromise of one function gains access to every resource the shared role permits. Use IAM Access Analyzer policy generation from 90-day CloudTrail activity to right-size roles after a burn-in period.

**Confused-deputy conditions on every service-principal resource-based policy**
Any resource-based policy granting a service principal (`*.amazonaws.com`) must include `aws:SourceArn` (specific triggering resource — tightest scope) and/or `aws:SourceAccount`. Use `aws:SourceOrgID` via RCP for org-wide enforcement. Combine SourceArn + SourceAccount for cross-account scenarios. Add `aws:PrincipalIsAWSService = false` guard on any Deny that uses `aws:SourceIp` because IP condition keys are redacted in service-to-service calls.

**Use Lambda execution-role STS credentials — never embed AWS access keys**
Lambda automatically injects STS temporary credentials for its execution role. Do NOT call `sts:AssumeRole` inside function code to re-assume the same role. For third-party API keys (non-AWS), store in Secrets Manager and grant `secretsmanager:GetSecretValue` in the execution role. Never set `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` in environment variables.

**MFA mandatory for all human identities and root in member accounts**
Enable centralized root access management in Organizations to remove root credentials from member accounts by default. Enforce phishing-resistant MFA (FIDO2 passkeys/hardware security keys) for workforce users via IAM Identity Center. Add `aws:MultiFactorAuthPresent = true` conditions to sensitive IAM policies. Use `sts:AssumeRoot` only for rare root-only tasks from the management account.

**SCPs + RCPs + Declarative Policies as complementary org-wide preventive guardrails**
SCPs restrict maximum permissions of IAM principals in member accounts. RCPs restrict maximum permissions on resources including external-principal access. Declarative Policies enforce baseline service configuration and apply to service-linked roles that SCPs/RCPs cannot touch. All three are required for full preventive coverage — they are not substitutes. Test SCP/RCP changes on an isolated account and monitor CloudTrail `AccessDenied` events after attachment.

**IAM Access Analyzer enabled in every Region with resources**
Enable an external-access analyzer per Region — it re-scans within 30 minutes of any policy change using formal automated reasoning (not heuristics). Enable unused-access analyzer to continuously flag drift in execution roles. Integrate `CheckNoNewAccess` / `CheckAccessNotGranted` custom policy checks in CI/CD pipelines to gate deploys that introduce new access grants.

### ⚠️ Ask First

**API Gateway authorization model**
Ask which identity providers callers already have before deciding:

| Option | When to Use | Key Trade-off |
|--------|------------|---------------|
| IAM SigV4 | Internal service-to-service; callers have AWS credentials | No extra cost; poor DX for external callers |
| Cognito user pool authorizer | External end-users (web/mobile), standard OIDC | No custom code; managed MFA/UI; locked to Cognito |
| Lambda authorizer | Third-party/custom tokens, fine-grained per-request logic | Most flexible; adds cold-start latency + Lambda cost (cache TTL 0–3600s) |
| Resource policy (IP/VPC) | VPC-only internal APIs; combine with one of the above | Network boundary only; no identity authentication |

**Human identity federation model**
Ask whether this is a new or migrating environment:
- New multi-account environment → IAM Identity Center (org instance) is the default. Per-user CloudTrail, centralized permission sets, no per-user charge.
- Cannot use Identity Center (single-account or legacy) → Direct SAML/OIDC federation (portable; harder to audit centrally).
- Legacy only → IAM users with long-term keys. Not recommended for new workloads — no central revocation, manual MFA enforcement.

**End-user serverless auth: Cognito user pool vs identity pool**
Ask whether end-users will call AWS services directly (S3, DynamoDB):
- Users call only API Gateway → Cognito user pool is sufficient (JWTs for API auth).
- Users access AWS services directly → Add Cognito identity pool to vend scoped temporary credentials with session tags (`aws:PrincipalTag/userId`) for `dynamodb:LeadingKeys` per-user data isolation.

**Permissions boundary for developer self-service IAM**
Ask whether development teams create their own Lambda execution roles:
- If yes → Set a permissions boundary (managed policy) capping the maximum permissions any team-created role can hold (exclude `iam:*`, admin). Teams self-service within the boundary; they cannot escape it.
- If no → Central platform team manages all execution roles; simpler governance but slower deployment velocity.

### 🚫 Never Do

For full ❌ wrong / ✅ correct IAM policy JSON, see [Policy Patterns](./blueprints/policy-patterns.md).

**Never use wildcard action+resource in a Lambda execution role**
`{ "Effect": "Allow", "Action": "*", "Resource": "*" }` in production violates least privilege. A supply-chain attack on any dependency grants the attacker full account access. Impact: full account compromise.
✅ Instead: Scope to exact actions on specific resource ARNs. Run IAM Access Analyzer policy generation after 90-day burn-in.

**Never grant a service principal without confused-deputy conditions**
`"Principal": {"Service": "s3.amazonaws.com"}` with no `aws:SourceArn` or `aws:SourceAccount` allows any AWS account configuring the same service to invoke your resource. Impact: cross-service privilege escalation from another account.
✅ Instead: Always include `aws:SourceAccount`; add `aws:SourceArn` for tightest scope. See [Policy Patterns](./blueprints/policy-patterns.md).

**Never embed AWS access keys in Lambda environment variables or source code**
`AWS_ACCESS_KEY_ID=AKIA...` in environment configuration never auto-expires, can be retrieved via `get-function-configuration`, and creates persistent blast radius post-exfiltration. Impact: persistent account access with no automatic expiry.
✅ Instead: Use the execution role (automatic STS injection). For third-party keys, use Secrets Manager.

**Never share one execution role across multiple Lambda functions**
A single `LambdaServiceRole` shared by many functions means compromising any one function grants access to every resource all functions use. Impact: lateral movement across the entire service.
✅ Instead: One role per function, scoped to that function's ARNs only. Detect sharing:
```bash
aws lambda list-functions | jq '[.Functions[].Role] | group_by(.) | map({role: .[0], count: length}) | .[] | select(.count > 1)'
```

**Never create an OIDC trust policy without constraining the `sub` claim**
A GitHub Actions trust policy that validates only `aud = sts.amazonaws.com` allows ANY GitHub repository to assume the role. Impact: supply-chain attack — any public repo assumes your deployment role.
✅ Instead: Scope `Condition` to both `aud` AND `sub` restricted to the specific repo + branch/environment (e.g., `repo:MyOrg/my-repo:ref:refs/heads/main`).

**Never assume RCP coverage protects Lambda functions or SNS topics**
Lambda and SNS are NOT in the RCP supported-services list as of August 2026. Relying on org-level RCPs leaves these services unprotected against external access.
✅ Instead: Enforce inbound Lambda access via resource-based policies with confused-deputy conditions + SCPs. For SNS, use topic policies with SourceArn/SourceAccount conditions.

---

## Integration Patterns

**Lambda identity planes: execution role (outbound) + resource-based policy (inbound)**
Two independent IAM planes govern each Lambda function. The execution role controls what AWS services the function calls — auto-rotating STS credentials. The resource-based policy controls who can invoke the function — requires confused-deputy conditions when the principal is a service. Access Analyzer validates both continuously. Neither should be broader than necessary.

**Multi-tenant DynamoDB isolation: Cognito identity pool + session tags + LeadingKeys**
Cognito identity pool vends temporary credentials with session tags mapping the user's sub to `aws:PrincipalTag/userId`. The DynamoDB policy on the identity-pool role uses `dynamodb:LeadingKeys` condition: `ForAllValues:StringEquals { "dynamodb:LeadingKeys": "${aws:PrincipalTag/userId}" }`. IAM enforces per-user isolation at the policy layer — application bugs cannot bypass it. Exclude `Scan` from the policy; complex queries may require redesign.

**OIDC-based CI/CD (zero stored credentials)**
Create IAM OIDC identity provider for the CI system. Create a deployment role scoped to both `aud` + `sub` (specific repo + branch). CI workflow exchanges JWT for temporary credentials via `AssumeRoleWithWebIdentity`. For cross-account deployment, chain one additional `sts:AssumeRole` to the target account's deployment role. Total role-chain session hard cap: **1 hour** — cannot be overridden by `max-session-duration` settings.

**Common problems**:
- **Role chaining session > 1 hour** → Redesign to assume the target role directly from the originating identity; avoid multi-hop chains in automated pipelines.
- **Access Analyzer flags service-principal grant** → Add `aws:SourceAccount` + `aws:SourceArn` conditions; analyzer re-scans within 30 minutes.
- **SCP blocks legitimate Lambda calls after OU attachment** → Check CloudTrail `AccessDenied`; test SCP on isolated account first; with Sep 2025 full IAM language, use conditions to narrow scope rather than broader allows.

---

## Verification Loop

The agent MUST execute after each IAM configuration change:

### 1. Detect shared execution roles
```bash
aws lambda list-functions | jq '[.Functions[].Role] | group_by(.) | map({role: .[0], count: length}) | .[] | select(.count > 1)'
# Expected: empty output (each role used by exactly 1 function)
```

### 2. Verify no long-lived keys in function environment
```bash
aws lambda get-function-configuration --function-name <name> \
  --query 'Environment.Variables' --output json
# Expected: no AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY keys present
```

### 3. Validate IAM policy document before attach
```bash
aws accessanalyzer validate-policy --policy-document file://policy.json --policy-type IDENTITY_POLICY
# Expected: no SECURITY_WARNING or ERROR findings
```

### 4. Check Access Analyzer external-access findings
```bash
aws accessanalyzer list-findings --analyzer-arn <arn> \
  --filter '{"status": {"eq": ["ACTIVE"]}}' --output table
# Expected: no ACTIVE findings on Lambda, SQS, SNS, S3, KMS, Secrets Manager resources
```

### 5. Verify MFA status (credential report)
```bash
aws iam generate-credential-report
aws iam get-credential-report --query 'Content' --output text | base64 -d | \
  awk -F',' '$8 == "false" {print "MFA MISSING:", $1}'
# Expected: no output (all users have MFA active)
```

**Troubleshooting**:
- `AccessDenied` after SCP change → Review CloudTrail; test on isolated account; check new Sep 2025 condition syntax
- Access Analyzer ACTIVE finding on resource-based policy → Add `aws:SourceAccount` + `aws:SourceArn` to service-principal grant
- Role chaining 1h session error → Redesign workflow to assume target role directly from originating identity; 1h cap is absolute

---

## Quick Reference

**Critical limits**:

| Resource | Limit | Notes |
|----------|-------|-------|
| Role chaining max session | 1 hour | Hard cap — cannot be overridden by `max-session-duration` |
| IAM resource-based policy size | 20 KB | `PutResourcePolicy` (full JSON) |
| Lambda authorizer cache TTL | 0–3600 seconds | Per API Gateway |
| Access Analyzer policy-gen CloudTrail window | 90 days | Maximum lookback |
| RCP supported services | S3, SQS, STS, KMS, Secrets Manager, EventBridge, DynamoDB, CloudWatch Logs | Lambda + SNS NOT covered (Aug 2026) |

**Identity primitive selection**:
- Serverless function → IAM execution role (one per function)
- Human workforce → IAM Identity Center (multi-account) or SAML/OIDC federation
- End-user app → Cognito user pool (API auth) + identity pool (direct AWS service access)
- CI/CD pipeline → OIDC federation (no stored credentials)
- Third-party vendor cross-account → IAM role with `sts:ExternalId` condition

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/securing-aws-iam-serverless/
├── SKILL.md                          ← This file (summary + guardrails)
└── blueprints/
    ├── evaluation-scenarios.md       ← 6 test scenarios
    └── policy-patterns.md           ← Full IAM policy JSON: ❌ wrong / ✅ correct
```

---

## External Resources

### Official Documentation
- [IAM User Guide — Security best practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html) — Primary reference (2026-08-28)
- [IAM User Guide — Confused deputy problem](https://docs.aws.amazon.com/IAM/latest/UserGuide/confused-deputy.html) — Confused-deputy conditions (2026-08-28)
- [Lambda Developer Guide — Execution role](https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html) — Per-function roles (2026-08-28)
- [AWS Organizations — Resource control policies](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_rcps.html) — RCP coverage + limits (2026-08-28)
- [IAM Access Analyzer](https://docs.aws.amazon.com/IAM/latest/UserGuide/what-is-access-analyzer.html) — Automated-reasoning analysis (2026-08-28)

### Security & Best Practices
- [IAM User Guide — Temporary security credentials](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp.html) — STS + execution roles (2026-08-28)
- [IAM User Guide — OIDC identity providers](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html) — CI/CD keyless auth (2026-08-28)
- [IAM Access Analyzer — Policy generation](https://docs.aws.amazon.com/IAM/latest/UserGuide/access-analyzer-policy-generation.html) — Least-privilege from CloudTrail (2026-08-28)
- [AWS What's New — Full IAM language for SCPs](https://aws.amazon.com/about-aws/whats-new/2025/09/aws-organizations-iam-language-service-control-policies/) — Sep 2025 (2026-08-28)
- [Centralized root access management](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_root-enable-root-access.html) — No standing root credentials (2026-08-28)
