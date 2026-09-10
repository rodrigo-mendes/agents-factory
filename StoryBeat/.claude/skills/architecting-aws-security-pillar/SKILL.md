---
name: architecting-aws-security-pillar
description: "Applies the AWS Well-Architected Framework Security Pillar to multi-account production workloads on AWS. Use when designing, auditing, or hardening an AWS architecture against the seven security best-practice areas: foundations, identity and access management, detection, infrastructure protection, data protection, incident response, and application security."
---

## Function
Specialist in AWS security architecture following the Well-Architected Framework Security Pillar (November 6, 2024 — current stable edition as of 2026-08-27).

## Version Context

**Framework**: AWS Well-Architected Framework — Security Pillar
**Edition**: November 6, 2024 (current stable — verified 2026-08-27; no 2025/2026 edition supersedes this)
**Support status**: Current stable

**Key additions in this edition**:
- Resource Control Policies (RCPs) alongside SCPs for restricting resource-level access from external principals (SEC01-BP01)
- Expanded guidance on EKS Pod Identity for workload credential assignment (SEC03 series)

**Seven best-practice areas**: Security foundations (SEC01) · IAM (SEC02–SEC03) · Detection (SEC04) · Infrastructure protection (SEC05–SEC06) · Data protection (SEC07–SEC09) · Incident response (SEC10) · Application security (SEC11)

> ⚠️ **CRITICAL — Agent Warning**: This skill targets the November 6, 2024 edition. Reject pre-2024 patterns
> (e.g., IRSA-first for EKS; no RCP guidance). The edition is flagged >12 months old relative to 2026-08-27
> but retained per Version Absolutism — it is the current stable release with no successor.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — SEC-AD-1 through SEC-AD-8 with full verification commands
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — Three architectural decision matrices (governance model, identity source, encryption key ownership)
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — SEC-ND-1 through SEC-ND-8 with wrong/correct examples
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — Canonical, edge-case, and anti-pattern-trap test cases
- **[Verification Loop](#verification-loop)** — AWS CLI validation commands and expected outputs
- **[Quick Reference](#quick-reference)** — Day-one baseline checklist and critical service limits
- **[External Resources](#external-resources)** — Official documentation links (all dated)

---

## Blueprints & Guardrails

### ✅ Always Do

For full detail, verification commands, and trade-off notes, see [Always Do Patterns](./blueprints/always-do-patterns.md).

- **SEC-AD-1 — Separate workloads via multi-account structure** — AWS accounts are a hard isolation boundary. Use AWS Organizations with an OU hierarchy aligned to data sensitivity and environment. Apply SCP/RCP guardrails at the OU level. Use Control Tower Account Factory for new accounts. Risk if omitted: High blast radius on any single compromise. (SEC01-BP01)
- **SEC-AD-2 — Federated human access with IAM Identity Center** — Route all human AWS access through IAM Identity Center → STS temporary credentials scoped to least-privilege permission sets. No per-user IAM users with permanent access keys. Verify with `aws iam get-credential-report`. (SEC02-BP04)
- **SEC-AD-3 — Workloads use IAM roles, never embedded keys** — Attach a least-privilege IAM role to every compute resource. EC2: instance profile. Lambda: execution role. EKS: Pod Identity (one role per service account). External/on-premises: IAM Roles Anywhere with X.509 certificates. (SEC03 series)
- **SEC-AD-4 — Phishing-resistant MFA for all IAM/root users** — Enforce FIDO2/WebAuthn passkeys or hardware security keys for IAM Identity Center users and any remaining IAM users. Enable MFA on the root user of every account; delete all root access keys. (SEC02 / Design Principle 1)
- **SEC-AD-5 — Encryption at rest with AWS KMS** — Classify data by sensitivity. Enable KMS CMKs for regulated/confidential data stores. Enable S3 default encryption, EBS encryption-by-default, and RDS storage encryption for all sensitive stores. Run Macie to discover unclassified sensitive data. (SEC08-BP01/02)
- **SEC-AD-6 — Continuous detection: logging and threat detection** — Enable before any workload reaches production: (1) Organizational CloudTrail trail → Log Archive S3 with Object Lock, (2) GuardDuty org-wide, (3) Security Hub with AWS Foundational Security Best Practices standard, (4) AWS Config aggregator. (SEC04-BP01 through BP04)
- **SEC-AD-7 — Defense-in-depth infrastructure protection** — Workloads in private subnets; AWS WAF (managed rule groups) on all internet-facing ALB/CloudFront distributions; Security Groups as the primary stateful control; no inbound management ports (use Systems Manager Session Manager); continuous CVE scanning with Amazon Inspector. (SEC05/SEC06)
- **SEC-AD-8 — Secure the software delivery lifecycle** — Embed SAST/SCA/secret-scanning as mandatory pipeline gates (CodePipeline/CodeBuild). Centralize dependencies in CodeArtifact. Deploy programmatically only — no manual production changes. Threat-model each workload. Sign artifacts with AWS Signer. (SEC11-BP01 through BP08)

### ⚠️ Ask First

For complete decision matrices with option comparisons and trade-offs, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

- **Decision A — Multi-account governance model** — Ask whether an existing landing zone or DIY Organizations setup is already in place. Retrofitting Control Tower onto a mature DIY setup is high-effort; recommend DIY when governance requirements exceed Control Tower's constraints.
- **Decision B — Identity source for IAM Identity Center** — Ask whether a corporate IdP (Okta, Entra ID, Ping) already exists. Use external IdP federation when one exists (single source of truth); use native identity store only for greenfield organizations without a directory.
- **Decision C — Encryption key ownership per data store** — Ask the data classification for each store before recommending key type. CMKs for regulated/restricted data. AWS-managed keys for lower sensitivity tiers. Imported key material/external key store only when off-AWS key custody is mandated.

### 🚫 Never Do

For complete ❌ wrong / ✅ correct code examples and detection commands, see [Never Do Patterns](./blueprints/never-do-patterns.md).

| Anti-pattern | Risk Level | Correct Alternative |
|---|---|---|
| **SEC-ND-1** — Long-term static access keys for human users | CRITICAL | IAM Identity Center → STS temporary credentials; GitHub Actions OIDC → IAM role for CI |
| **SEC-ND-2** — Root user for daily operations or no root MFA | CRITICAL | Lock root in vault; FIDO2 MFA on root; delete root access keys; operate via IAM roles only |
| **SEC-ND-3** — Multiple unrelated workloads in one account | CRITICAL | Separate accounts per workload/env under dedicated OUs with SCP guardrails |
| **SEC-ND-4** — Wildcard (`*`) actions or resources in IAM policies | HIGH | IAM Access Analyzer policy generation from CloudTrail; policy validation in CI/CD |
| **SEC-ND-5** — No organizational CloudTrail or GuardDuty | CRITICAL | Org trail → Log Archive S3 (Object Lock); SCP blocking trail disablement; GuardDuty org-wide |
| **SEC-ND-6** — Unencrypted data at rest in sensitive stores | HIGH | KMS encryption on all S3/EBS/RDS stores; Macie to discover unclassified sensitive data |
| **SEC-ND-7** — Internet-facing endpoint with no WAF or DDoS protection | HIGH | AWS WAF with managed rule groups on ALB/CloudFront; Shield Advanced for high-value targets |
| **SEC-ND-8** — Security groups with `0.0.0.0/0` on port 22/3389 | HIGH | Remove all inbound management port rules; use Systems Manager Session Manager exclusively |

---

## Integration Patterns

- **IAM Identity Center ↔ External IdP** — SCIM provisioning for user lifecycle automation; SAML/OIDC for authentication; permission sets provisioned as IAM roles per account.
- **GuardDuty ↔ Security Hub ↔ EventBridge** — GuardDuty findings aggregate in Security Hub → EventBridge rules filter High/Critical → Lambda or SSM Automation runbook for automated remediation.
- **CloudTrail Org Trail ↔ Log Archive S3 (Object Lock)** — Immutable centralized audit log; member accounts have no write/delete access; deny disablement via SCP.
- **IAM Access Analyzer ↔ CI/CD Pipeline** — Policy validation (100+ checks) as a mandatory pre-deploy gate; unused-access analyzer for monthly least-privilege hygiene.
- **Amazon Inspector ↔ Security Hub** — CVE and software composition findings from Inspector aggregated in Security Hub alongside GuardDuty, Config, and Access Analyzer findings.

**Common problems**:
- **GuardDuty findings overwhelming the team** → Suppress known-safe findings with suppression rules; never disable GuardDuty; tune Security Hub to High/Critical severity.
- **SCP accidentally blocks a required AWS service operation** → Test SCPs in a non-production OU first; use the Organizations SCP policy simulator; maintain a break-glass account outside the OU.
- **IAM Identity Center users cannot authenticate after IdP reconfiguration** → Keep the old SAML metadata active until all sessions rotate; test identity source changes in a staging Identity Center instance.

---

## Verification Loop

Run after any security architecture configuration:

### 1. Multi-account structure
```bash
aws organizations list-accounts \
  --query 'Accounts[*].{Id:Id,Name:Name,Status:Status}'
aws organizations list-policies --filter SERVICE_CONTROL_POLICY
# Expected: multiple accounts per environment; at least one SCP active at the root or OU level
```

### 2. IAM credential hygiene
```bash
aws iam generate-credential-report
aws iam get-credential-report --query 'Content' --output text | base64 -d | \
  awk -F',' 'NR>1 {print $1, $4, $9, $14}'
# Expected: no human users with access_key_*_active=true; mfa_active=true for all console users
```

### 3. Detection baseline
```bash
aws cloudtrail describe-trails \
  --query 'trailList[*].{Name:Name,IsOrgTrail:IsOrganizationTrail}'
# Expected: at least one trail with IsOrganizationTrail: true

aws guardduty list-detectors
# Expected: detectors present in each enabled region; verify org-wide status in GuardDuty console
```

### 4. Security group hygiene
```bash
aws ec2 describe-security-groups \
  --filters "Name=ip-permission.from-port,Values=22" \
            "Name=ip-permission.cidr,Values=0.0.0.0/0" \
  --query 'SecurityGroups[*].{GroupId:GroupId,GroupName:GroupName}'
# Expected: empty result set — no security groups expose SSH to the internet
```

**Troubleshooting**:
- `AccessDeniedException` on `describe-trails` → Use a cross-account security-audit IAM role with `cloudtrail:DescribeTrails` permission.
- GuardDuty shows no org-wide enabled status → Delegate GuardDuty administration to a designated security account; enable org-wide from that account.
- Credential report shows active access keys on human users → Migrate to IAM Identity Center federated access; deactivate and delete keys after migration verified.
- Config recorder shows `NOT_RECORDING` → Enable Config recorder and delivery channel in every region where workloads run; use a Config aggregator in the management account.

---

## Quick Reference

**Day-one security baseline (before first production workload)**:
1. AWS Organizations + OU hierarchy created
2. CloudTrail organizational trail → Log Archive S3 (Object Lock) enabled
3. GuardDuty enabled org-wide with designated administrator account
4. Security Hub enabled org-wide; AWS Foundational Security Best Practices standard active
5. IAM Identity Center configured (federated to corporate IdP if available)
6. Root MFA (FIDO2/hardware key) enabled on management account and all member accounts
7. SCP attached at root blocking root API key creation and CloudTrail trail disablement

**Critical service limits**:

| Resource | Limit | Scope |
|---|---|---|
| SCP policy document size | 5,120 characters | Per SCP |
| SCPs attached per OU/account | 5 | Simultaneous |
| GuardDuty findings retention in console | 90 days | Export to S3 for long-term retention |
| AWS KMS API call throughput (default) | 10,000 req/sec | Per region; request increase for high-volume workloads |
| IAM Identity Center permission sets | 2,000 | Per IAM Identity Center instance |
| AWS Config rules | 500 managed + 150 custom | Per account per region |

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/architecting-aws-security-pillar/
├── SKILL.md                              ← This file (summary + guardrails)
└── blueprints/
    ├── always-do-patterns.md             ← SEC-AD-1 through SEC-AD-8 with full detail
    ├── ask-first-decisions.md            ← Decision A/B/C with option comparison matrices
    ├── never-do-patterns.md              ← SEC-ND-1 through SEC-ND-8 with wrong/correct examples
    └── evaluation-scenarios.md           ← Test cases for the skill evaluator
```

---

## External Resources

### Official Documentation
- [Security Pillar — Welcome](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html) — Nov 6, 2024 edition (current stable, verified 2026-08-27) ⚠️ >12mo
- [Security foundations — Design principles + 7 areas](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/security.html) — Accessed 2026-08-27
- [Identity and access management (SEC02–SEC03)](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/identity-and-access-management.html) — Accessed 2026-08-27
- [Detection (SEC04)](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/detection.html) — Accessed 2026-08-27
- [Infrastructure protection (SEC05–SEC06)](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/infrastructure-protection.html) — Accessed 2026-08-27
- [Data protection (SEC07–SEC09)](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/data-protection.html) — Accessed 2026-08-27
- [Incident response (SEC10)](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/incident-response.html) — Accessed 2026-08-27
- [Application security (SEC11)](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/application-security.html) — Accessed 2026-08-27

### Security & Best Practices
- [IAM Security Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html) — Current stable, accessed 2026-08-27
- [SEC01 — Operate workloads securely (multi-account)](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_securely_operate_multi_accounts.html) — SCP/RCP and multi-account isolation
- [Protecting data at rest (SEC08)](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-data-at-rest.html) — KMS CMK guidance
- [AWS Well-Architected Tool](https://console.aws.amazon.com/wellarchitected/) — Score workloads against SEC-BP questions using the Security Pillar lens
