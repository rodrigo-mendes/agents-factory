# Never Do Patterns — architecting-aws-multi-account-organizations

Source: research base `research_cloud_AWS_Organization_Architecture_Multi_Account_Strategy_2026.md`
(AWS Organizations 2026; research date 2026-08-26; all sources accessed 2026-08-26).

---

## ND-1 — Workloads in the management account

**Risk**: CRITICAL · **Pillar**: Security
**Why**: SCPs do not restrict IAM users/roles in the management account; a compromised workload there can modify SCPs, remove accounts or read billing for the whole org.

- ❌ EC2 apps, RDS, Lambda in the management account; using it as a general-purpose account.
- ✅ One member account per workload (or workload group) in the Workloads OU; management account holds only org automation and billing.

```bash
aws resourcegroupstaggingapi get-resources --profile management-account-profile \
  --query "ResourceTagMappingList[*].ResourceARN"   # Any compute/storage/database ARN = finding
```

**Source**: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices_mgmt-acct.html (accessed 2026-08-26)

---

## ND-2 — No organization CloudTrail trail

**Risk**: CRITICAL · **Pillar**: Security, Operational Excellence
**Why**: Member accounts without their own trail have zero API audit; attackers operate undetected. Compliance violation (SOC 2, PCI-DSS, HIPAA).

- ❌ Inconsistent per-account trails; no trail in the management account.
- ✅ One org trail (management account or Security Tooling as delegated admin), all accounts and Regions, to the Log Archive bucket with Object Lock, log file validation and CMK encryption.

```bash
aws cloudtrail describe-trails --include-shadow-trails false \
  --query "trailList[?IsOrganizationTrail==\`true\`]"     # Expected: at least one
aws cloudtrail get-trail-status --name <trail-name> --query "IsLogging"   # Expected: true
```

**Source**: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/creating-trail-organization.html (accessed 2026-08-26)

---

## ND-3 — SCP Allow-list without FullAWSAccess

**Risk**: HIGH · **Pillar**: Reliability, Operational Excellence
**Why**: Detaching `FullAWSAccess` without a replacement Allow policy blocks every action in the affected OU — including remediation.

- ❌ Detaching `FullAWSAccess` as a "restrictive baseline"; partial Allow-lists missing critical services.
- ✅ Deny-list strategy: keep `FullAWSAccess` at all levels, add targeted `Deny` statements; test in the Policy Staging OU first.

```bash
aws organizations list-policies-for-target --target-id <root-or-ou-id> \
  --filter SERVICE_CONTROL_POLICY --query "Policies[?Name=='FullAWSAccess']"   # Expected: present at every OU
```

**Source**: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html (accessed 2026-08-26)

---

## ND-4 — No RCP data perimeter

**Risk**: HIGH · **Pillar**: Security
**Why**: SCPs cannot stop principals outside the org from using permissive resource policies on S3, KMS, SQS, Secrets Manager. RCPs close the gap.

- ❌ Relying only on SCPs; assuming "nobody outside the org can reach my S3".
- ✅ RCP at the root denying non-org principals, preserving AWS service principals:

```json
{
  "Effect": "Deny",
  "Action": "s3:*",
  "Resource": "*",
  "Condition": {
    "StringNotEqualsIfExists": { "aws:PrincipalOrgID": "<your-org-id>" },
    "BoolIfExists": { "aws:PrincipalIsAWSService": "false" }
  }
}
```

```bash
aws organizations list-policies --filter RESOURCE_CONTROL_POLICY \
  --query "Policies[*].{Name:Name,Id:Id}"   # Expected: at least one RCP beyond RCPFullAWSAccess
```

**Source**: https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_data-perimeters.html (accessed 2026-08-26)

---

## ND-5 — Security services in misaligned delegated admin accounts

**Risk**: HIGH · **Pillar**: Security, Operational Excellence
**Why**: GuardDuty, Detective and Security Hub CSPM must share one delegated admin, or Security Hub → Detective navigation breaks. Audit Manager must share Security Hub CSPM's account to collect its evidence.

- ❌ GuardDuty in account A, Security Hub CSPM in B, Detective in C.
- ✅ One Security Tooling account as delegated admin for GuardDuty, Security Hub CSPM, Detective, Config, Macie, IAM Access Analyzer, Firewall Manager, Audit Manager, Inspector. Exception: Security Lake → Log Archive account.

```bash
for svc in guardduty.amazonaws.com securityhub.amazonaws.com \
  detective.amazonaws.com config.amazonaws.com; do
  echo -n "$svc: "
  aws organizations list-delegated-administrators --service-principal $svc \
    --query "DelegatedAdministrators[0].Id" --output text
done   # Expected: same account ID for the first three
```

**Source**: https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/security-tooling.html (accessed 2026-08-26)

---

## ND-6 — No cost alerting or budget alerts

**Risk**: MEDIUM · **Pillar**: Cost Optimization
**Why**: Misconfiguration overruns (open NAT gateways, data transfer, runaway scaling) surface only on the monthly bill.

- ❌ No AWS Budgets; no Cost Anomaly Detection; monthly bill review as the only control.
- ✅ Budgets for total org, per-OU (cost categories) and per-service thresholds (alerts at 80% and 100%); Cost Anomaly Detection with SNS; tag policies enforcing cost-allocation tags.

```bash
aws budgets describe-budgets --account-id <management-account-id> \
  --query "Budgets[*].{Name:BudgetName,Type:BudgetType}"   # Expected: at least one budget
```

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/cost_monitor_usage_config_tools.html (accessed 2026-08-26); https://docs.aws.amazon.com/cost-management/latest/userguide/coh-delegated-admin.html (accessed 2026-08-26)
