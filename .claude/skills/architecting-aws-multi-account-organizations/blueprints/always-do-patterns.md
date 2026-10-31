# Always Do Patterns — architecting-aws-multi-account-organizations

Source: research base `research_cloud_AWS_Organization_Architecture_Multi_Account_Strategy_2026.md`
(AWS Organizations 2026; research date 2026-08-26; all sources accessed 2026-08-26).

---

## AD-1 — Isolated Management Account (no workloads)

**Pillar**: Security · **Why**: SCPs do not apply to IAM users/roles in the management account; a workload there runs outside the org guardrails.

**Decision**: Use the management account only for org resources/OUs/policies, org-level automation, consolidated billing and break-glass access. All workloads live in member accounts under governed OUs.

```bash
aws resourcegroupstaggingapi get-resources --profile management-account-profile \
  --query "ResourceTagMappingList[*].ResourceARN"   # Expected: no compute/storage/database ARNs
aws iam list-users --profile management-account-profile   # Expected: no long-term IAM users
```

**Trade-offs**: Cross-account roles needed for automation touching the management account; more complex break-glass.
**Source**: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices_mgmt-acct.html (accessed 2026-08-26)

---

## AD-2 — Root SCP denying LeaveOrganization + CloseAccount

**Pillar**: Security · **Why**: Without it, a member-account admin can leave the org or close the account, bypassing governance.

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "DenyLeaveOrg",
    "Effect": "Deny",
    "Action": ["organizations:LeaveOrganization", "account:CloseAccount"],
    "Resource": "*"
  }]
}
```

> Orgs created via the Console **after July 10, 2026** receive this SCP automatically. Orgs created via CLI/SDK/CloudFormation, or before that date, must add it manually.

```bash
aws organizations list-policies --filter SERVICE_CONTROL_POLICY --query "Policies[*].{Name:Name,Id:Id}"
aws organizations list-targets-for-policy --policy-id <policy-id>   # Expected: root (r-xxxx) is a target
```

**Trade-offs**: Closing an account requires management-account action — an intended gate.
**Source**: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices_mgmt-acct.html (accessed 2026-08-26)

---

## AD-3 — Delegate security services to the Security Tooling account

**Pillar**: Security · **Why**: A member account holding delegated admin IS subject to SCP/RCP guardrails; the management account is not.

**Decision**: Register one Security Tooling (Audit) member account as delegated admin for CloudTrail, Security Hub CSPM, GuardDuty, Detective, Config, Macie, IAM Access Analyzer, Firewall Manager, Audit Manager, Inspector, Security Incident Response, Systems Manager. GuardDuty, Detective and Security Hub CSPM **must** share the same account. Exception: Security Lake delegates to the Log Archive account.

```bash
for svc in guardduty.amazonaws.com securityhub.amazonaws.com detective.amazonaws.com; do
  aws organizations list-delegated-administrators --service-principal $svc \
    --query "DelegatedAdministrators[0].Id" --output text
done   # Expected: same account ID
```

**Trade-offs**: One account holds high privilege — protect it with dedicated SCPs and the most restricted permission sets.
**Source**: https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/security-tooling.html (accessed 2026-08-26)

---

## AD-4 — Centralized Log Archive with immutable storage

**Pillar**: Security, Operational Excellence · **Why**: Logs are the forensic record; a compromised member account must not be able to tamper with them.

**Decision**: One S3 bucket in the Log Archive account with Object Lock (COMPLIANCE mode), Versioning, SSE-KMS with a CMK, and a bucket policy restricting writes to the org trail ARN. Org trail: multi-Region, global-service events, log file validation on. Config delivery channel and VPC Flow Logs to the same archive. No routine human logins.

```bash
aws s3api get-object-lock-configuration --bucket <central-log-bucket> --profile log-archive
# Expected: ObjectLockEnabled = Enabled
aws cloudtrail get-trail-status --name <org-trail-name>   # Expected: IsLogging = true
```

**Trade-offs**: Cross-account bucket policy grants; KMS key policy must allow CloudTrail; extra storage cost.
**Source**: https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/log-archive.html (accessed 2026-08-26)

---

## AD-5 — IAM Identity Center for all human access

**Pillar**: Security · **Why**: Long-lived IAM users with static credentials are a primary attack vector.

**Decision**: Enable IAM Identity Center in the management account; delegate administration to the Shared Services account. Role-aligned permission sets (ReadOnly, Developer, SecurityAdmin, OrgAdmin). Enforce MFA; use an external IdP where available. For the management account, assign individual users (not groups) to permission sets.

```bash
aws sso-admin list-instances                          # Expected: an Identity Center instance
aws iam list-users --profile <member-account>         # Expected: zero IAM users
```

**Trade-offs**: Access via the portal or `aws sso login`; no long-lived programmatic keys by design.
**Source**: https://docs.aws.amazon.com/singlesignon/latest/userguide/delegated-admin.html (accessed 2026-08-26)

---

## AD-6 — Management account root user hardening

**Pillar**: Security · **Why**: The management root user has unlimited org-wide power and cannot be constrained by policy.

**Decision**: Register ≥ 2 MFA devices (up to 8; FIDO2 passkey preferred). No root access keys. Group email address, split custody (password group ≠ MFA group). Alert on `userIdentity.type = Root` via CloudTrail + EventBridge/CloudWatch + SNS. Enable centralized root access management and remove member-account root credentials; use `sts:AssumeRoot` from the Security Tooling account for root-only tasks.

```bash
aws iam get-account-summary --query \
  "SummaryMap.{MFA:AccountMFAEnabled,Keys:AccountAccessKeysPresent}"   # Expected: MFA=1, Keys=0
```

**Source**: https://docs.aws.amazon.com/IAM/latest/UserGuide/root-user-best-practices.html (accessed 2026-08-26); https://aws.amazon.com/about-aws/whats-new/2025/06/aws-iam-mfa-root-users-across-all-account-types/ (June 2025)

---

## AD-7 — Data perimeter: SCP + RCP + VPC endpoint policies

**Pillar**: Security · **Why**: SCPs alone cannot stop external identities reaching org resources; RCPs close that gap.

1. **Identity axis (RCP)** — deny non-org principals on org resources (`aws:PrincipalOrgID`); keep `aws:PrincipalIsAWSService` / `aws:ViaAWSService` exceptions.
2. **Resource axis (SCP)** — deny org principals access to resources outside the org (`aws:ResourceOrgID`).
3. **Network axis (SCP + VPC endpoint policy)** — restrict to approved networks (`aws:SourceVpc`, `aws:SourceVpce`, `aws:VpcSourceIp`).

Start with S3, STS, KMS, SQS, Secrets Manager (the original five RCP services); verify the current list in the RCP docs.

```bash
aws organizations list-policies --filter RESOURCE_CONTROL_POLICY --query "Policies[*].Name"
# Expected: at least one RCP beyond RCPFullAWSAccess
```

**Source**: https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_data-perimeters.html (accessed 2026-08-26); https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_rcps.html (accessed 2026-08-26)

---

## AD-8 — SCP deny-list strategy (keep FullAWSAccess)

**Pillar**: Security, Reliability · **Why**: Removing `FullAWSAccess` without an explicit Allow-list blocks all actions, including remediation.

**Decision**: Keep `FullAWSAccess` at every level; layer targeted `Deny` SCPs: Region restriction (`aws:RequestedRegion`), member root-user restriction, security-service protection (`cloudtrail:StopLogging`, `guardduty:DeleteDetector`, `config:StopConfigurationRecorder`, `securityhub:DisableSecurityHub`), `iam:CreateUser` / `iam:CreateAccessKey`, and leave/close protection at root. Test in the Policy Staging OU, then promote one OU at a time.

```bash
aws organizations list-policies-for-target --target-id <root-or-ou-id> \
  --filter SERVICE_CONTROL_POLICY --query "Policies[?Name=='FullAWSAccess']"   # Expected: present
```

**Source**: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html (accessed 2026-08-26); https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps_examples.html (accessed 2026-08-26)
