# Never-Do Anti-Patterns — AWS Organizations Governance (2024-2025)

Source: AWS Organizations User Guide + Organizing Your AWS Environment whitepaper (April 30, 2025). All sources accessed 2026-07-31.

Every entry uses exact AWS service names and provides a side-by-side WRONG / CORRECT example.

---

## NP-1 — Running workloads / storing data in the management account

**Risk Level**: CRITICAL
**WAF Pillars**: Security

**Why**: "SCPs don't affect users or roles in the management account" — every resource there is outside the org's preventive permission guardrails. AWS: "Avoid deploying workloads to the organization's management account."

**Blast radius**: Entire organization — the management account controls billing, policies, and all account lifecycle operations.

```
# WRONG
Deploy an EC2/RDS-backed application and its S3 data buckets in the management account;
grant developers IAM AdministratorAccess there "because SCPs will protect it."
# Result: No SCP guardrail applies. Any compromise of those resources = management-account compromise.

# CORRECT
Keep the management account empty of workloads.
Create a member account under the Workloads OU for the application.
Register a dedicated Audit member account as delegated administrator for security tooling.
SCPs and RCPs then apply to all workload resources.
```

**Detection**:
```bash
# Run in management account — should return near-empty
aws resourcegroupstaggingapi get-resources \
  --query 'ResourceTagMappingList[].ResourceARN'
# Add an EventBridge rule alerting on resource-creation CloudTrail events in the management account
```

**Impact**: Data breach / Compliance violation / Cascading failure (un-guardrailed privileged blast radius).

Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices_mgmt-acct.html

---

## NP-2 — Removing FullAWSAccess (or missing a root-level Allow) in an allow-list SCP

**Risk Level**: CRITICAL
**WAF Pillars**: Reliability, Operational Excellence

**Why**: "You should not remove the FullAWSAccess policy unless you modify or replace it... otherwise all AWS actions from member accounts will fail." "Missing an Allow statement at the root-level... will effectively block all access."

**Blast radius**: Every account below the affected node — potentially the entire organization if done at the root.

```
# WRONG
Detach FullAWSAccess at the root.
Attach only an "Allow S3" SCP at one OU.
Expect other services to keep working.
# Result: All member-account API calls fail — complete lockout.

# CORRECT (deny-list strategy — recommended)
Keep FullAWSAccess at every node.
Layer explicit Deny guardrails on top.

# CORRECT (allow-list strategy — only if an explicit service whitelist is required)
Attach the service-allow SCP at EVERY level: root → OU → account.
Validate in a Policy Staging OU with a test account before rollout.
Never leave any node without at least one effective Allow.
```

**Detection**:
```bash
ROOT_ID=$(aws organizations list-roots --query 'Roots[0].Id' --output text)
aws organizations list-policies-for-target \
  --target-id "$ROOT_ID" \
  --filter SERVICE_CONTROL_POLICY \
  --query 'Policies[].{Name:Name,AwsManaged:AwsManaged}'
# Verify FullAWSAccess is present (AwsManaged=true) OR a custom replacement Allow is attached
```

**Impact**: Service outage (org-wide lockout of all member-account actions).

Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps_evaluation.html

---

## NP-3 — Attaching untested SCPs directly to the organization root

**Risk Level**: HIGH
**WAF Pillars**: Reliability, Operational Excellence

**Why**: AWS "strongly recommends that you don't attach SCPs to the root of your organization without thoroughly testing the impact." A single Deny at the root affects ALL accounts beneath it simultaneously.

**Blast radius**: All member accounts in the organization at the same time.

```
# WRONG
Author a broad Deny SCP.
Attach it to the root in production to "roll it out fast."
# Result: Users locked out of services in use across all member accounts.

# CORRECT
Create a Policy Staging OU with one or two test accounts.
Attach the new SCP to the Policy Staging OU only.
Validate against IAM service-last-accessed data and CloudTrail service usage.
Confirm no unintended denials.
Promote the SCP to target OUs, then to root, with gradual expansion.
```

**Detection**:
```bash
# Monitor for AttachPolicy events targeting the root in CloudTrail
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=AttachPolicy \
  --query 'Events[?contains(CloudTrailEvent, `r-`) == `true`]'
# Require a staging-OU validation gate in the change management process
```

**Impact**: Service outage / Cost overrun (from emergency workarounds) — broad, simultaneous lockout.

Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html

---

## NP-4 — No SCP preventing accounts from leaving/closing the organization

**Risk Level**: HIGH
**WAF Pillars**: Security, Operational Excellence

**Why**: Member accounts can otherwise "leave your organization or close themselves, which can disrupt governance, billing, and security controls."

**Blast radius**: Any member account that leaves escapes all org guardrails, audit logging, and consolidated billing.

```
# WRONG
Rely on FullAWSAccess only.
A member-account admin runs: aws organizations leave-organization
# Result: Account exits governance, escapes all SCPs/RCPs, loses org audit trail.

# CORRECT
Attach this SCP at the root:
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "DenyLeaveAndClose",
    "Effect": "Deny",
    "Action": [
      "organizations:LeaveOrganization",
      "account:CloseAccount"
    ],
    "Resource": "*"
  }]
}
# Note: Auto-applied to console-created orgs after July 10, 2026.
# CLI/SDK/CloudFormation orgs and pre-existing orgs must attach manually.
```

**Detection**:
```bash
ROOT_ID=$(aws organizations list-roots --query 'Roots[0].Id' --output text)
aws organizations list-policies-for-target \
  --target-id "$ROOT_ID" \
  --filter SERVICE_CONTROL_POLICY
# Alert on CloudTrail events: LeaveOrganization, CloseAccount
```

**Impact**: Compliance violation / loss of audit continuity / billing disruption.

Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices_mgmt-acct.html

---

## NP-5 — Flat single-account (no isolation between environments/workloads)

**Risk Level**: HIGH
**WAF Pillars**: Security, Reliability, Cost Optimization

**Why**: The account "acts as an isolation boundary for identity and access management" and a billing boundary. AWS recommends "using several accounts to separate your workloads, rather than relying on a single account."

**Blast radius**: All environments/workloads share one blast radius — one compromise or misconfiguration affects everything.

```
# WRONG
One AWS account holding prod + dev + test for many teams.
IAM tags are the only separation.
Single commingled bill with no cost attribution per team/workload.

# CORRECT
Separate member accounts per workload per environment under the Workloads OU:
  - Workloads/Prod/workload-a-prod
  - Workloads/NonProd/workload-a-dev
  - Workloads/NonProd/workload-a-test
Inherited SCPs from the OU enforce guardrails automatically.
Cost Explorer shows clean per-account attribution.
Automate provisioning via Account Factory to manage at scale.
```

**Detection**:
```bash
# Mature org should show workload/environment-scoped accounts, not one shared account
aws organizations list-accounts --query 'Accounts[].{Name:Name,Id:Id,Status:Status}'
# Check Cost Explorer: is cost attribution possible per workload/environment?
```

**Impact**: Data breach / Service outage / Cost overrun (no attribution) / Compliance violation.

Source: https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/organizing-your-aws-environment.html

---

## NP-6 — No organization-wide CloudTrail trail (per-account or missing audit logging)

**Risk Level**: HIGH
**WAF Pillars**: Security, Operational Excellence

**Why**: Per-account trails can be disabled or deleted by that account's admin, and there is no central, consistent audit record. An organization trail logs "events for the management account and all member accounts" and cannot be altered by member accounts.

**Blast radius**: Org-wide audit/forensics capability — gaps in any account undermine incident response and compliance.

```
# WRONG
Each team enables (or forgets to enable) its own trail in its own account.
A compromised account's admin turns logging off to hide activity.
# Result: No forensic record; compliance audit fails.

# CORRECT
Enable one multi-Region AWS CloudTrail organization trail
(from the management account or CloudTrail delegated administrator).
Deliver to a central, access-restricted Amazon S3 bucket in the Log Archive account.
Enable log-file validation and SSE-KMS.
Member accounts can see but cannot modify or delete it.
```

**Verification**:
```bash
aws cloudtrail describe-trails \
  --query 'trailList[?IsOrganizationTrail==`true`].[Name,IsMultiRegionTrail,LogFileValidationEnabled]'
# Expected: exactly one org trail with IsOrganizationTrail=true, IsMultiRegionTrail=true
```

**Impact**: Compliance violation / undetectable breach (no forensics).

Source: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/creating-trail-organization.html

---

## NP-7 — Using the management account as the delegated administrator for security services

**Risk Level**: MEDIUM
**WAF Pillars**: Security

**Why**: AWS: "the AWS security best practices follow the principle of least privilege and doesn't recommend this configuration." It concentrates security operations in the highest-privilege, un-guardrailed account.

**Blast radius**: Security tooling + management/billing authority collapse into one account, widening compromise impact.

```
# WRONG
aws guardduty enable-organization-admin-account \
  --admin-account-id <management-account-id>
# Result: GuardDuty findings, compliance reports, and org billing all in one un-guardrailed account.

# CORRECT
Register a dedicated Security Tooling/Audit member account in the Security OU:
aws guardduty enable-organization-admin-account \
  --admin-account-id <audit-account-id>
aws securityhub enable-organization-admin-account \
  --admin-account-id <audit-account-id>
# Use the SAME Audit account across all Regions for both services.
# Configure GuardDuty auto-enable = ALL.
```

**Verification**:
```bash
aws guardduty list-organization-admin-accounts
aws securityhub list-organization-admin-accounts
# Expected: AccountId = Audit/Security Tooling account, NOT the management account
```

**Impact**: Compliance violation / widened blast radius on management-account compromise.

Source: https://docs.aws.amazon.com/guardduty/latest/ug/guardduty_organizations.html

---

## NP-8 — Mirroring the corporate org chart / mixing security accounts into the core Security OU

**Risk Level**: MEDIUM
**WAF Pillars**: Operational Excellence, Security

**Why**: AWS guidance: organize by function (common controls), not rigid org structure; "maintain a clean security OU that adheres to AWS Control Tower requirements... contain only the essential security accounts... For additional security-related accounts, create a separate OU outside the core security OU."

**Blast radius**: Governance clarity and Control Tower compliance across the whole account topology.

```
# WRONG
Create OUs named after departments (Finance-OU, Engineering-OU, HR-OU).
Place a general-purpose "SecOps sandbox," pentest accounts, and tooling accounts inside the core Security OU.
# Result: Policy confusion; Control Tower non-conformance; Security OU drifts from managed state.

# CORRECT
Function-based OUs: Security, Infrastructure, Workloads, Sandbox.
Core Security OU: Log Archive account + Audit/Security Tooling account ONLY.
Additional security-related accounts (pentest, SecOps sandbox): separate OU outside core Security OU.
Never mirror the corporate reporting structure in the OU tree.
```

**Detection**:
```bash
# Inspect Security OU contents
SECURITY_OU_ID=<security-ou-id>
aws organizations list-accounts-for-parent \
  --parent-id "$SECURITY_OU_ID" \
  --query 'Accounts[].{Name:Name,Id:Id}'
# Expected: only Log Archive + Audit/Security Tooling accounts
```

**Impact**: Governance drift / Control Tower non-conformance / harder-to-reason-about effective policy.

Source: https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/organizing-your-aws-environment.html
