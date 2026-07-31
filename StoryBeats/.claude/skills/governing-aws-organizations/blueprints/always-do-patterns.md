# Always-Do Patterns — AWS Organizations Governance (2024-2025)

Source: AWS Organizations User Guide + Organizing Your AWS Environment whitepaper (April 30, 2025). All sources accessed 2026-07-31.

---

## AD-1 — Enable "All features" mode, not consolidated-billing-only

**WAF Pillars**: Security, Operational Excellence

SCPs, RCPs, declarative policies, tag/backup policies, and service integrations are "available only in an organization that has all features enabled." Consolidated-billing-only mode cannot restrict principal permissions or integrate other AWS services org-wide.

**Architecture Decision**: Enable all features at org creation. If migrating from consolidated-billing-only, every invited member must accept the `ENABLE_ALL_FEATURES` handshake.

**Verification**:
```bash
aws organizations describe-organization --query 'Organization.FeatureSet'
# Expected: "ALL"
```

**Trade-offs**: Member accounts gain org-level governance (they cannot opt out of SCPs); requires member consent to migrate from consolidated-billing-only.

Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_getting-started_concepts.html

---

## AD-2 — Keep the management account free of workloads; use delegated administrators

**WAF Pillars**: Security

"Organizations service control policies (SCPs) do not work to restrict any users or roles in the management account." Any resource there is un-guardrailed. AWS: "Avoid deploying workloads to the organization's management account."

**Architecture Decision**: Register dedicated member accounts as delegated administrators for Organizations policy management and for each integrated service (GuardDuty, Security Hub, Config, CloudFormation StackSets, Service Catalog, IAM Access Analyzer, etc.).

**Verification**:
```bash
# Resource inventory in management account — should be near-empty
aws resourcegroupstaggingapi get-resources \
  --query 'ResourceTagMappingList[].ResourceARN'

# List registered delegated administrators
aws organizations list-delegated-administrators
```

**Trade-offs**: Slightly more setup (register delegated admins per service); vastly reduced blast radius.

Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices_mgmt-acct.html

---

## AD-3 — Protect the management account root user and restrict access

**WAF Pillars**: Security

The management account "is key to all administrative tasks" and is the payer/owner. AWS: restrict access to "only those admin users who need rights to make changes"; periodically review who has the email, password, MFA, and phone number.

**Architecture Decision**:
1. Enforce MFA on the root user
2. Store root credentials via a documented break-glass process not reliant on one individual
3. Perform quarterly access reviews
4. Grant day-to-day access via IAM Identity Center permission sets — never via root

**Verification**:
```bash
# Check root MFA (from management account)
aws iam get-account-summary --query 'SummaryMap.AccountMFAEnabled'
# Expected: 1
```

**Trade-offs**: Operational discipline overhead; essential given the management account is un-guardrailed by SCPs.

Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices_mgmt-acct.html

---

## AD-4 — Attach a preventive SCP that blocks leaving/closing accounts

**WAF Pillars**: Security, Operational Excellence

Member accounts can otherwise leave or close themselves, "which can disrupt governance, billing, and security controls."

**SCP statement** (attach at root):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyLeaveAndClose",
      "Effect": "Deny",
      "Action": [
        "organizations:LeaveOrganization",
        "account:CloseAccount"
      ],
      "Resource": "*"
    }
  ]
}
```

**IMPORTANT**: Organizations created via the AWS Management Console AFTER July 10, 2026 receive this SCP automatically. Organizations created via CLI/SDK/CloudFormation, or before that date, MUST create and attach it manually.

**Verification**:
```bash
ROOT_ID=$(aws organizations list-roots --query 'Roots[0].Id' --output text)
aws organizations list-policies-for-target \
  --target-id "$ROOT_ID" \
  --filter SERVICE_CONTROL_POLICY \
  --query 'Policies[].Name'
# Expected: shows the deny SCP by name
```

**Trade-offs**: None material — approved departures still possible via management account / delegated admin action.

Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices_mgmt-acct.html

---

## AD-5 — Enable an organization CloudTrail trail into a locked Log Archive account

**WAF Pillars**: Security, Operational Excellence

An organization trail "logs events for the management account and all member accounts." Member accounts "do not have sufficient permissions to delete organization trails, turn logging on or off, or otherwise change an organization trail" — tamper resistance by design.

**Architecture Decision**:
- Enable a multi-Region org trail from the management account or a CloudTrail delegated administrator
- Central S3 bucket in the Log Archive account, structured as `<org-id>/<account-id>/...`
- Enable log-file validation and SSE-KMS encryption

**Verification**:
```bash
aws cloudtrail describe-trails \
  --query 'trailList[?IsOrganizationTrail==`true`].[Name,IsMultiRegionTrail,S3BucketName,LogFileValidationEnabled]'
# Expected: IsOrganizationTrail=true, IsMultiRegionTrail=true, LogFileValidationEnabled=true
```

**Trade-offs**: Storage cost of centralized logs; a member account can still only see its own events in Event History (not the full org trail).

Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/creating-trail-organization.html

---

## AD-6 — Centralize security services via delegated administrators in a dedicated Audit account

**WAF Pillars**: Security

"AWS security best practices follow the principle of least privilege and doesn't recommend" using the management account as the delegated administrator for security services.

**Architecture Decision**:
- Register the Audit account as delegated administrator per service in every Region where GuardDuty/Security Hub run
- Use the SAME Audit/Security Tooling account across all Regions for both services (they are Regional)
- Set GuardDuty auto-enable to ALL for full coverage of existing + new accounts

**Verification**:
```bash
# GuardDuty delegated admin
aws guardduty list-organization-admin-accounts
# Expected: AccountId = Audit account (NOT management account)

# Security Hub delegated admin
aws securityhub list-organization-admin-accounts
# Expected: AccountId = Audit account

# GuardDuty auto-enable
aws guardduty describe-organization-configuration \
  --detector-id <detector-id> \
  --query 'AutoEnableOrganizationMembers'
# Expected: "ALL"
```

**Trade-offs**: GuardDuty delegated admin manages up to 50,000 members per Region; must configure per Region separately.

Source: https://docs.aws.amazon.com/guardduty/latest/ug/guardduty_organizations.html

---

## AD-7 — Design OUs by function; maintain a clean Control-Tower-compliant Security OU

**WAF Pillars**: Operational Excellence, Security

OUs "are useful when you need to apply the same controls to a subset of accounts." AWS: "maintain a clean security OU that adheres to AWS Control Tower requirements... contain only the essential security accounts... For additional security-related accounts, create a separate OU outside the core security OU."

**Recommended OU structure**:

| OU | Accounts | Purpose |
|----|----------|---------|
| Security (core) | Log Archive, Audit/Security Tooling | Tamper-resistant logs + delegated-admin security tooling |
| Infrastructure | Network, Shared Services | Centralized networking, Transit Gateway, shared CI/CD |
| Workloads > Prod | Per-workload prod accounts | Production; stricter SCP/RCP guardrails |
| Workloads > Non-Prod | Per-workload dev/test accounts | Non-production; relaxed guardrails, cost caps |
| Sandbox | Sandbox accounts | Experimentation; limited production access |
| Policy Staging | Test accounts | Validate new policies before broad rollout |

**Verification**:
```bash
ROOT_ID=$(aws organizations list-roots --query 'Roots[0].Id' --output text)
aws organizations list-organizational-units-for-parent --parent-id "$ROOT_ID"
# Expected: top-level OUs match functional structure above
```

**Trade-offs**: More OUs = more policy attach points to manage; keep hierarchy shallow (max 5 levels, usually 2-3 in practice).

Source: https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/recommended-ous-and-accounts.html

---

## AD-8 — Centralize workforce access with an IAM Identity Center organization instance

**WAF Pillars**: Security, Operational Excellence

The organization instance "is the best practice... the only instance that enables you to manage access to AWS accounts and it is recommended for all production use." One point of federation, one certificate to manage.

**Architecture Decision**:
1. Deploy IAM Identity Center in the management account (organization instance)
2. Connect the corporate IdP (Entra ID, Okta, etc.) via SAML + SCIM
3. Define permission sets by job function (not by individual user)
4. Assign groups to accounts/OUs
5. Avoid long-lived IAM users for humans
6. Optionally register a delegated administrator for Identity Center

**Verification**:
```bash
aws sso-admin list-instances \
  --query 'Instances[?OwnerAccountId==`<management-account-id>`]'
# Expected: one organization instance

# Review permission-set assignments per account
aws sso-admin list-account-assignments \
  --instance-arn <instance-arn> \
  --account-id <account-id>
```

**Trade-offs**: Identity Center account quota is 7,000 (adjustable). Legacy `sso`/`identitystore` API namespaces remain for backward compatibility but "AWS SSO" branding is deprecated.

Source: https://docs.aws.amazon.com/singlesignon/latest/userguide/what-is.html

---

## AD-9 — Enforce standards with declarative, tag, and backup policies

**WAF Pillars**: Security, Cost Optimization, Reliability

Declarative policies keep a configuration "always maintained when the service adds new features or APIs." Tag policies "standardize the tags attached to AWS resources." Backup policies "centrally manage and apply backup plans."

**Architecture Decision**:
- Attach Tag policies enforcing mandatory cost-allocation/ownership tags
- Attach Backup policies enforcing minimum retention and DR requirements
- Attach declarative EC2 policy to block public AMIs / enforce IMDSv2 org-wide
- Stage all new policies in the Policy Staging OU first before attaching to root or workload OUs

**Verification**:
```bash
# List all policy types
aws organizations list-policies --filter TAG_POLICY --query 'Policies[].Name'
aws organizations list-policies --filter BACKUP_POLICY --query 'Policies[].Name'
aws organizations list-policies --filter DECLARATIVE_POLICY --query 'Policies[].Name'

# Check effective policy on an account
aws organizations describe-effective-policy \
  --policy-type TAG_POLICY \
  --target-id <account-id>
```

**Trade-offs**: Declarative policy inheritance merges (not intersects) — model carefully before rollout. Tag policies can report violations without enforcement (Report mode) before switching to Enforcement.

Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_getting-started_concepts.html
