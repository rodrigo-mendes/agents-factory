---
name: architecting-aws-iam
description: "Enforces AWS IAM security best practices for production multi-account AWS Organizations workloads (IAM Security Best Practices + Well-Architected SEC02/SEC03, pinned 2026-07-31). Use when designing, reviewing, or auditing identity and access management architecture on AWS — covering federation, workload roles, org guardrails (SCPs/RCPs), least-privilege lifecycle, and IAM Access Analyzer integration."
---

## Function

Specialist in AWS Identity and Access Management (IAM) security architecture for general-purpose production multi-account AWS Organizations workloads. Aligned to the AWS Well-Architected Security Pillar best practices SEC02 (identity) and SEC03 (permissions).

## Version Context

**Technology**: AWS IAM (Identity and Access Management)
**Pinned to**: AWS IAM Security Best Practices + Well-Architected Security Pillar — living/`latest` docs, state as of **2026-07-31**
**Currency threshold**: Re-verify by **2027-07-31** (IAM guidance evolves; all sources are living/latest)
**Scope**: General production multi-account AWS Organizations estate

**Key shifts captured (2024–2026)**:
- Centralized root access management via AWS Organizations — remove root credentials from member accounts; use `AssumeRoot` for rare root-only tasks
- Resource Control Policies (RCPs) added alongside SCPs — RCPs bound what resources can grant (data perimeter); SCPs bound what principals can do
- IAM Access Analyzer matured: four analyzer types — external-access, internal-access, unused-access, plus policy validation / custom policy checks / policy generation
- Phishing-resistant MFA (passkeys, FIDO2 security keys) is now the recommended default; root MFA mandatory within 35 days

**Deprecated direction**: Long-term IAM access keys and per-account IAM users for human access are now a documented narrow exception, not the default.

⚠️ **CRITICAL — Agent Warning**:
This skill is pinned to **2026-07-31** IAM guidance. Reject patterns predating the "temporary credentials first / centralized root access" direction. Do not present IAM users with access keys as a normal default.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — 8 mandatory IAM patterns with rationale, AWS services, and verification
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — 4 architectural crossroads requiring context before prescribing
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — 7 anti-patterns (CRITICAL/HIGH/MEDIUM) with correct alternatives and detection
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 3 test cases: canonical, edge, misuse
- **[Verification Loop](#verification-loop)** — CLI commands to audit IAM posture
- **[Quick Reference](#quick-reference)** — Effective-permission formula, key CLI commands, service limits
- **[External Resources](#external-resources)** — Official AWS documentation links (all dated 2026-07-31)

---

## Blueprints & Guardrails

### ✅ Always Do

For full rationale, verification commands, and AWS service details, see [Always Do Patterns](./blueprints/always-do-patterns.md).

Domain complexity: **Complex** — security-critical, multi-layer, multi-account. All 8 patterns are mandatory.

- **Federate human users via IAM Identity Center (no standing IAM users)** — Connect IdP (Entra ID/Okta/Ping) to IAM Identity Center; model access as permission sets mapped to IdP groups; humans assume account roles for short sessions. Applies to SEC02-BP04 / BP02.
- **Deliver IAM roles to workloads — never access keys** — EC2 instance profiles, Lambda execution roles, ECS task roles, EKS Pod Identity/IRSA auto-deliver STS credentials the SDK discovers; for outside-AWS: IAM Roles Anywhere (X.509) or OIDC/SAML federation. Applies to SEC02-BP02.
- **Require phishing-resistant MFA for all sign-in** — FIDO2/passkeys on every root user (register up to 8 devices); enforce MFA at IdP/Identity Center for all human sign-in; root MFA mandatory within 35 days. Applies to SEC02-BP01.
- **Centrally remove root credentials from member accounts** — Enable Organizations centralized root access management; remove member root password/keys/MFA; perform rare root-only tasks via `AssumeRoot` from the management/delegated-admin account only. Applies to SEC02-BP01.
- **Apply least-privilege and reduce continuously** — Start from AWS managed policies; generate fine-grained customer-managed policies from CloudTrail activity via IAM Access Analyzer policy generation; prune unused access on a schedule using unused-access findings. Applies to SEC03-BP02 / BP04.
- **Establish org-wide guardrails: SCPs (principal) + RCPs (resource)** — Baseline SCPs deny root actions in member accounts, CloudTrail/Config tampering, Region restriction, leaving org; RCPs enforce data perimeter (no resource shared outside org). Guardrails cap but never grant — add identity/resource policies separately. Applies to SEC03-BP05.
- **Enable IAM Access Analyzer and wire policy validation into CI/CD** — Org-level external-access analyzer per Region; org-level unused-access analyzer (one suffices); `validate-policy` + `check-no-new-access` as pipeline gates blocking policies with new unintended access. Applies to SEC03-BP07.
- **Add Condition elements to enforce data perimeter** — Include `aws:SecureTransport`, `aws:SourceVpc`, `aws:PrincipalOrgID`, `aws:ViaAWSService` in policies to restrict by encryption, network origin, and org boundary. Applies to SEC03-BP02.

### ⚠️ Ask First

For tradeoff matrices and decision guidance, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

Pause and ask before prescribing these patterns:

- **Human access model** — Ask: "Which external IdP is authoritative, and is this single-account or multi-account?" IAM Identity Center is the recommended default for multi-account orgs; direct SAML/OIDC per account for single-account; IAM users only for the documented exception cases.
- **Delegation model** — Ask: "Must developers self-serve IAM role creation?" Yes → mandate permissions boundaries + SCP enforcing the boundary on every created role. No → central IaC pipeline creates all roles.
- **Authorization model at scale** — Ask: "Is there a governed tagging standard enforced via SCP/tag policies?" Yes with enforcement → ABAC (one policy, tag-matching conditions) for multi-team isolation. No → default to RBAC; ABAC without enforced tags is an access-control gap.
- **Emergency break-glass access** — Ask: "What is the recovery path if IAM Identity Center or the IdP becomes unavailable?" Always define a monitored break-glass IAM role; never rely on ad-hoc root usage as the recovery plan.

### 🚫 Never Do

For side-by-side wrong/correct examples, detection commands, and blast-radius impact, see [Never Do Patterns](./blueprints/never-do-patterns.md).

| Anti-Pattern | Risk | Correct Alternative |
|---|---|---|
| Long-term access keys as the default credential | CRITICAL | IAM roles via compute (instance profile / execution role / Pod Identity); IAM Roles Anywhere for outside-AWS |
| Root access keys / routine root sign-in | CRITICAL | Centralize root removal via Organizations; `AssumeRoot` for rare tasks; federated admin role for day-to-day |
| `Action: "*"` / `Resource: "*"` on application roles | HIGH | Start from AWS managed policy → generate least-privilege via IAM Access Analyzer → validate in CI |
| No MFA on root or privileged users | CRITICAL | Phishing-resistant MFA (FIDO2/passkey) on root; enforce MFA at IdP/Identity Center for all humans |
| Unmonitored public/cross-account resource sharing | HIGH | Org-level external-access analyzer; `aws:PrincipalOrgID` conditions; RCPs for data perimeter |
| Treating SCPs/RCPs/boundaries as permission grants | MEDIUM | Guardrails only cap maximum; grant via identity-based or resource-based policies |
| Stale unused roles/keys/permissions never pruned | MEDIUM | IAM Access Analyzer unused-access findings; schedule remediation using last-accessed data |

---

## Integration Patterns

For detailed examples, see [Always Do Patterns](./blueprints/always-do-patterns.md) (workload identity section) and [Ask First Decisions](./blueprints/ask-first-decisions.md) (cross-account, ABAC sections).

**Key integrations**:
- **IAM Identity Center + external IdP** — SAML/OIDC trust; IdP authenticates users → Identity Center maps groups to permission sets → short-lived account-role sessions. No per-account IAM users.
- **IAM Roles + compute services** — SDK auto-discovers credentials from instance/container metadata endpoint (EC2/Lambda/ECS/EKS); no key distribution required.
- **IAM Access Analyzer + IaC CI/CD** — `validate-policy` and `check-no-new-access` block unintended access in pipelines; org-level analyzers provide runtime posture.
- **AWS Organizations (SCPs + RCPs) + IAM** — SCPs restrict what principals may do; RCPs restrict what resources may grant. Neither grants — identity/resource policies still required to allow.

**Common problems**:
- **SDK not discovering credentials in container** → Verify ECS task role or EKS Pod Identity annotation on the pod; check IMDS endpoint reachability (IMDSv2 hop limit for containers).
- **Cross-account `AssumeRole` denied** → Confirm trust policy in account B names account A principal, AND account A identity policy grants `sts:AssumeRole`; for resource-based services the resource policy must also allow.
- **SCP "allow" not granting access** → SCPs do not grant; add an allow in the identity-based or resource-based policy; run IAM policy simulator to confirm effective permissions.

---

## Verification Loop

Run after any IAM architecture design, policy change, or new account baseline. Degree of freedom: **Low** — run the exact commands shown.

### 1. Credential audit
```bash
aws iam generate-credential-report
aws iam get-credential-report --query 'Content' --output text | base64 --decode > credential-report.csv
# Expected: root_account row shows access_key_1_active = false, access_key_2_active = false
# Flag any non-root IAM user that is NOT a documented exception (CodeCommit / Keyspaces / third-party plugin)
```

### 2. Org guardrail audit
```bash
aws organizations list-policies --filter SERVICE_CONTROL_POLICY
aws organizations list-policies --filter RESOURCE_CONTROL_POLICY
aws accessanalyzer list-analyzers \
  --query 'analyzers[*].{name:name,type:type,status:status,arn:arn}'
# Expected: org-level EXTERNAL_ACCESS per Region + org-level UNUSED_ACCESS
```

### 3. Least-privilege posture
```bash
aws accessanalyzer list-findings --analyzer-arn <ANALYZER_ARN> \
  --filter '{"status":{"eq":["ACTIVE"]}}'

aws accessanalyzer validate-policy \
  --policy-document file://policy.json --policy-type IDENTITY_POLICY

aws accessanalyzer check-no-new-access \
  --new-policy-document file://new-policy.json \
  --existing-policy-document file://reference-policy.json \
  --policy-type IDENTITY_POLICY

aws iam generate-service-last-accessed-details --arn <ROLE_ARN>
# Then: aws iam get-service-last-accessed-details --job-id <JOB_ID>
```

### 4. MFA and root check
```bash
aws configservice describe-compliance-by-config-rule \
  --config-rule-names root-account-mfa-enabled
# Expected: COMPLIANT

aws configservice describe-compliance-by-config-rule \
  --config-rule-names iam-root-access-key-check
# Expected: COMPLIANT
```

**Troubleshooting**:
- `NoSuchEntityException` on `AssumeRole` → trust policy does not name the calling principal; inspect with `aws iam get-role --role-name <name>`
- Access Analyzer finding `ACTIVE` on S3/KMS resource → add `aws:PrincipalOrgID` condition or archive with documented justification
- Credential report shows `password_enabled = true` for non-root user → remove console access and migrate to federation

---

## Quick Reference

**Effective permission formula**:
```
Effective = (identity-based policy ∩ resource-based policy [if cross-account])
           ∩ SCPs ∩ RCPs ∩ permissions boundaries ∩ session policies

Key: No guardrail grants. Allow must exist in an identity- or resource-based policy.
```

**Essential CLI commands**:
```bash
aws iam generate-credential-report
aws accessanalyzer list-analyzers
aws accessanalyzer validate-policy --policy-document file://policy.json --policy-type IDENTITY_POLICY
aws accessanalyzer check-no-new-access --new-policy-document file://new.json --existing-policy-document file://ref.json --policy-type IDENTITY_POLICY
aws organizations list-policies --filter SERVICE_CONTROL_POLICY
aws iam get-service-last-accessed-details --job-id <JOB_ID>
```

**Critical limits**:

| Resource | Limit | Note |
|---|---|---|
| Managed policies per role | 10 | Hard limit |
| Inline policy size | 2,048 chars | Managed policy version: 6,144 chars |
| SCP / RCP document size | 5,120 chars | Per policy document |
| Access key age | 0 days (target) | Prefer roles; rotate per SEC02-BP05 if unavoidable |
| MFA devices per root user | 8 | Register multiple phishing-resistant devices |

---

## Blueprints Directory Structure

```
StoryBeats/.claude/skills/architecting-aws-iam/
├── SKILL.md                              <- This file (index + guardrail summaries)
└── blueprints/
    ├── always-do-patterns.md             <- 8 mandatory patterns: rationale, services, verification
    ├── ask-first-decisions.md            <- 4 architectural crossroads with tradeoff matrices
    ├── never-do-patterns.md              <- 7 anti-patterns: wrong vs correct, detection, impact
    └── evaluation-scenarios.md           <- 3 test cases (canonical, edge, misuse)
```

---

## External Resources

### Official AWS Documentation (all accessed 2026-07-31)
- [IAM Security Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [Root User Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/root-user-best-practices.html)
- [IAM Access Analyzer](https://docs.aws.amazon.com/IAM/latest/UserGuide/what-is-access-analyzer.html)
- [Permissions Boundaries](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html)
- [ABAC for AWS](https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction_attribute-based-access-control.html)

### Well-Architected Security Pillar (accessed 2026-07-31)
- [Identity Management — SEC02-BP01–BP06](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/identity-management.html)
- [Permissions Management — SEC03-BP01–BP09](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/permissions-management.html)

### Organization-Wide Controls (accessed 2026-07-31)
- [Service Control Policies (SCPs)](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html)
- [Resource Control Policies (RCPs)](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_rcps.html)
- [AWS Security Reference Architecture](https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/organizations.html)

> Currency: AWS IAM docs are living (`latest`). Re-verify against these pages by **2027-07-31**.
