# Never Do Patterns — architecting-aws-security-pillar

Source: AWS Well-Architected Framework Security Pillar, November 6, 2024 (verified 2026-08-27)

Each pattern includes the risk level, the wrong approach, the correct alternative, and detection commands.

---

## SEC-ND-1 — Long-term static access keys for human users

**Risk level**: CRITICAL
**Violates**: Design Principle 1 — Implement a strong identity foundation

**Why**: Leaked long-term keys provide persistent unauthorized access with no automatic expiry. Human access keys stored in `~/.aws/credentials` or copied into CI secrets are a leading cause of cloud breaches.

```
# ❌ WRONG — IAM user with permanent access key
aws iam create-access-key --user-name deploy-admin
# Key stored in ~/.aws/credentials or pasted into GitHub Secrets
# Key is valid indefinitely; no automatic rotation; no expiry on leak
```

```
# ✅ CORRECT — IAM Identity Center federated sign-in
# Human users authenticate via SSO; receive STS temporary credentials (1–12 hour TTL)
aws sso login --profile my-account-role
# Credentials expire automatically; no rotation required

# For CI/CD (GitHub Actions): use OIDC → IAM role (no stored credentials at all)
# In GitHub Actions workflow:
# - uses: aws-actions/configure-aws-credentials@v4
#   with:
#     role-to-assume: arn:aws:iam::ACCOUNT:role/GitHubActionsRole
#     aws-region: us-east-1
```

**Detection**:
```bash
aws iam get-credential-report --query 'Content' --output text | base64 -d | \
  awk -F',' 'NR>1 && ($9=="true" || $14=="true") {print $1, "HAS ACTIVE KEY"}'
# Any output here requires immediate remediation
```

**Impact**: Data breach; persistent unauthorized access post-credential exposure with no automatic revocation.

**Source**: IAM best practices https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html

---

## SEC-ND-2 — Root user for daily operations or no root MFA

**Risk level**: CRITICAL
**Violates**: Design Principle 1; root credentials are not restricted by SCPs

**Why**: Root user credentials cannot be restricted by SCPs — compromise equals total account takeover. Root access keys enable programmatic full-access without console login.

```
# ❌ WRONG — Root access key used by automation script
# ~/.aws/credentials:
[default]
aws_access_key_id = AKIA...ROOT...
aws_secret_access_key = ...
# No MFA configured on root user
```

```
# ✅ CORRECT — Root credentials locked; operations run under least-privilege IAM roles
# 1. Delete root access keys:
aws iam delete-access-key --access-key-id AKIA... --user-name root
# (Run as the root user via console — cannot delete root keys via IAM API as another principal)

# 2. Enable FIDO2 hardware key on root (must be done in AWS console)
# 3. All operations via IAM Identity Center permission sets → STS temporary credentials
```

**Detection**:
```bash
aws configservice describe-compliance-by-config-rule \
  --config-rule-names root-account-mfa-enabled iam-root-access-key-check

# CloudTrail alert on root usage:
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=Username,AttributeValue=root \
  --max-items 5
```

**Impact**: Total account takeover; all resources and data in the account fully exposed. SCPs offer zero protection when root is compromised.

**Source**: IAM best practices https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html

---

## SEC-ND-3 — Multiple unrelated workloads in one account

**Risk level**: CRITICAL
**Violates**: SEC01-BP01 — multi-account isolation principle

**Why**: One compromised workload can access production data if they share an account. Risk classification: High in the Security Pillar.

```
# ❌ WRONG — prod-api, dev-api, and analytics in account 123456789012
# Single account hosts:
#   - prod-api ECS service with customer data
#   - dev-api EC2 instances with developer access
#   - analytics Glue jobs reading prod S3 buckets
# A dev IAM role misconfiguration can reach prod resources
```

```
# ✅ CORRECT — Separate accounts per workload/environment under OUs
# Account structure (via Organizations):
#   Prod OU
#     └─ account: prod-api-workload (111111111111)
#   Non-Prod OU
#     └─ account: dev-api-workload  (222222222222)
#     └─ account: analytics-dev     (333333333333)
# Cross-account access is explicit, audited, and governed by SCPs
```

**Detection**:
```bash
# Review account/OU structure
aws organizations list-children \
  --parent-id ROOT_ID \
  --child-type ORGANIZATIONAL_UNIT

# Look for mixed-environment tags on resources in a single account
aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=Environment,Values=prod,dev,staging
# If prod AND dev resources appear in the same account → architectural remediation required
```

**Impact**: Wide blast radius — compromise of one workload exposes all co-resident workloads regardless of IAM policy intent.

**Source**: SEC01-BP01 https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_securely_operate_multi_accounts.html

---

## SEC-ND-4 — Wildcard (`*`) actions or resources in IAM policies

**Risk level**: HIGH
**Violates**: Design Principle 1 — least privilege; enables privilege escalation

**Why**: Wildcard policies allow lateral movement and privilege escalation if the identity's credentials are compromised. Action `*` on resource `*` is effectively unrestricted.

```json
// ❌ WRONG — application role with wildcard permissions
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "*",
      "Resource": "*"
    }
  ]
}
```

```json
// ✅ CORRECT — least-privilege policy generated from observed CloudTrail activity
// Generated by IAM Access Analyzer policy generation, then validated with policy checks
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::my-app-bucket/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:ACCOUNT:table/my-table"
    }
  ]
}
```

**Detection**:
```bash
# IAM Access Analyzer policy validation
aws accessanalyzer validate-policy \
  --policy-document file://policy.json \
  --policy-type IDENTITY_POLICY
# Look for findings of type SUGGESTION or WARNING regarding overly permissive wildcards

# Unused-access findings (permissions granted but never used in 90 days)
aws accessanalyzer list-findings \
  --analyzer-arn arn:aws:access-analyzer:REGION:ACCOUNT:analyzer/ANALYZER \
  --filter '{"findingType":{"contains":["UnusedPermission"]}}'
```

**Impact**: Privilege escalation; lateral movement across services and accounts.

**Source**: IAM best practices https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html

---

## SEC-ND-5 — No organizational CloudTrail trail or disabled GuardDuty

**Risk level**: CRITICAL
**Violates**: Design Principle 2 — Maintain traceability

**Why**: Without an audit trail and threat detection, breaches go undetected and forensic investigation is impossible. Compliance requirements (SOC2, ISO 27001, PCI-DSS) cannot be demonstrated.

```bash
# ❌ WRONG — per-account trail only (misses future accounts) or CloudTrail disabled
aws cloudtrail describe-trails
# Returns only per-account trails with IsOrganizationTrail: false
# OR: no trails returned at all
```

```bash
# ✅ CORRECT — organizational trail + GuardDuty org-wide
# 1. Create organizational trail from management account
aws cloudtrail create-trail \
  --name org-audit-trail \
  --s3-bucket-name log-archive-cloudtrail \
  --is-multi-region-trail \
  --is-organization-trail \
  --enable-log-file-validation

# 2. Enable GuardDuty org-wide (from delegated admin account)
aws guardduty create-detector --enable
aws guardduty update-organization-configuration \
  --detector-id DETECTOR_ID \
  --auto-enable-organization-members ALL

# 3. SCP to prevent disabling CloudTrail in member accounts
# (Attach to root or Workloads OU)
```

```json
// SCP — deny disabling CloudTrail
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyDisableCloudTrail",
      "Effect": "Deny",
      "Action": [
        "cloudtrail:DeleteTrail",
        "cloudtrail:StopLogging",
        "cloudtrail:UpdateTrail"
      ],
      "Resource": "*"
    }
  ]
}
```

**Detection**:
```bash
aws cloudtrail describe-trails \
  --query 'trailList[?IsOrganizationTrail==`true`]'
# Expected: non-empty; if empty → CRITICAL finding
```

**Impact**: Undetected breach; forensic investigation impossible; compliance audit failure (SOC2, ISO 27001, PCI-DSS).

**Source**: SEC04 https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/detection.html

---

## SEC-ND-6 — Unencrypted data at rest in sensitive stores

**Risk level**: HIGH
**Violates**: Design Principle 5 — Protect data in transit and at rest

**Why**: Unencrypted EBS snapshots, S3 objects, or RDS instances expose data if media, snapshots, or objects are accessed outside their intended context.

```bash
# ❌ WRONG — S3 bucket with encryption disabled, RDS with no storage encryption
aws s3api get-bucket-encryption --bucket my-bucket
# Error: ServerSideEncryptionConfigurationNotFoundError

aws rds describe-db-instances \
  --query 'DBInstances[?StorageEncrypted==`false`].DBInstanceIdentifier'
# Returns instance IDs → unencrypted production database
```

```bash
# ✅ CORRECT — enforce encryption on all sensitive stores

# 1. S3: enforce default encryption on bucket
aws s3api put-bucket-encryption \
  --bucket my-bucket \
  --server-side-encryption-configuration '{
    "Rules": [{"ApplyServerSideEncryptionByDefault": {
      "SSEAlgorithm": "aws:kms",
      "KMSMasterKeyID": "arn:aws:kms:REGION:ACCOUNT:key/CMK_KEY_ID"
    }}]}'

# 2. EBS: enable account-level encryption by default
aws ec2 enable-ebs-encryption-by-default

# 3. RDS: encryption must be set at creation — to encrypt an existing unencrypted instance:
#    a. Create a snapshot of the unencrypted instance
#    b. Copy the snapshot with encryption enabled (specifying a CMK)
#    c. Restore a new instance from the encrypted snapshot
#    d. Update the application connection string and decommission the old instance

# 4. Run Macie to discover unclassified sensitive data in S3
aws macie2 create-classification-job \
  --job-type ONE_TIME \
  --s3-job-definition '{"bucketDefinitions":[{"accountId":"ACCOUNT","buckets":["my-bucket"]}]}'
```

**Detection**:
```bash
aws configservice describe-compliance-by-config-rule \
  --config-rule-names encrypted-volumes s3-bucket-server-side-encryption-enabled rds-storage-encrypted
# Expected: all rules COMPLIANT
```

**Impact**: Data exposure on media, snapshot, or object theft; compliance violation (HIPAA, PCI-DSS, GDPR).

**Source**: SEC08 https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-data-at-rest.html

---

## SEC-ND-7 — Internet-facing endpoint without WAF or DDoS protection

**Risk level**: HIGH
**Violates**: Design Principle 3 — Apply security at all layers (SEC05 infrastructure protection)

**Why**: An internet-facing API or web app without edge protection is exposed to L7 attacks (SQLi, XSS, bot abuse) and volumetric DDoS, risking service outage, data breach, and cost overrun.

```bash
# ❌ WRONG — ALB exposed directly to 0.0.0.0/0 with no WAF WebACL
aws elbv2 describe-load-balancers \
  --query 'LoadBalancers[?Scheme==`internet-facing`].LoadBalancerArn' | \
  xargs -I {} aws wafv2 get-web-acl-for-resource --resource-arn {}
# Error: WAF is not associated with this resource → CRITICAL for internet-facing workloads
```

```bash
# ✅ CORRECT — WAF WebACL with managed rule groups on ALB/CloudFront

# 1. Create WebACL with managed rules
aws wafv2 create-web-acl \
  --name production-webacl \
  --scope REGIONAL \
  --default-action '{"Allow": {}}' \
  --rules '[
    {"Name":"CoreRuleSet","Priority":1,"Statement":{"ManagedRuleGroupStatement":{"VendorName":"AWS","Name":"AWSManagedRulesCommonRuleSet"}},"OverrideAction":{"None":{}},"VisibilityConfig":{"SampledRequestsEnabled":true,"CloudWatchMetricsEnabled":true,"MetricName":"CoreRuleSet"}},
    {"Name":"SQLiRuleSet","Priority":2,"Statement":{"ManagedRuleGroupStatement":{"VendorName":"AWS","Name":"AWSManagedRulesSQLiRuleSet"}},"OverrideAction":{"None":{}},"VisibilityConfig":{"SampledRequestsEnabled":true,"CloudWatchMetricsEnabled":true,"MetricName":"SQLiRuleSet"}},
    {"Name":"IPReputationList","Priority":3,"Statement":{"ManagedRuleGroupStatement":{"VendorName":"AWS","Name":"AWSManagedRulesAmazonIpReputationList"}},"OverrideAction":{"None":{}},"VisibilityConfig":{"SampledRequestsEnabled":true,"CloudWatchMetricsEnabled":true,"MetricName":"IPReputationList"}}
  ]' \
  --visibility-config '{"SampledRequestsEnabled":true,"CloudWatchMetricsEnabled":true,"MetricName":"production-webacl"}'

# 2. Associate with ALB
aws wafv2 associate-web-acl \
  --web-acl-arn WAF_ACL_ARN \
  --resource-arn ALB_ARN
```

**Detection**:
```bash
aws wafv2 list-resources-for-web-acl \
  --web-acl-arn WAF_ACL_ARN \
  --resource-type APPLICATION_LOAD_BALANCER
# All internet-facing ALBs must appear here

# AWS Config rule
aws configservice describe-compliance-by-config-rule \
  --config-rule-names alb-waf-enabled
```

**Impact**: Service outage from DDoS, data breach via L7 injection, significant cost overrun from bot/scraper traffic.

**Source**: SEC05 https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/infrastructure-protection.html

---

## SEC-ND-8 — Security groups with port 22 or 3389 open to `0.0.0.0/0`

**Risk level**: HIGH
**Violates**: SEC05 (protecting networks) and SEC06 (protecting compute)

**Why**: Exposing SSH (22) or RDP (3389) to the internet invites brute-force attacks and exploitation of unpatched instances. Management access does not require open ports when Systems Manager Session Manager is available.

```bash
# ❌ WRONG — security group with SSH open to the internet
# Inbound rule: tcp/22 from 0.0.0.0/0 (and ::/0) on production EC2
```

```bash
# ✅ CORRECT — remove all inbound management port rules; use Session Manager

# 1. Revoke the offending rule
aws ec2 revoke-security-group-ingress \
  --group-id sg-XXXXXXXX \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0

# 2. Ensure Systems Manager Agent is installed and EC2 has SSM-capable IAM role
aws ssm describe-instance-information \
  --query 'InstanceInformationList[*].{Id:InstanceId,Ping:PingStatus}'
# Expected: all production instances show PingStatus: Online

# 3. Start a Session Manager session (no open ports required)
aws ssm start-session --target i-XXXXXXXXXXXXXXXXX
```

**Detection**:
```bash
# Find security groups with SSH open to the internet
aws ec2 describe-security-groups \
  --filters "Name=ip-permission.from-port,Values=22" \
            "Name=ip-permission.cidr,Values=0.0.0.0/0" \
  --query 'SecurityGroups[*].{GroupId:GroupId,GroupName:GroupName,VpcId:VpcId}'

# AWS Config managed rules
aws configservice describe-compliance-by-config-rule \
  --config-rule-names restricted-ssh restricted-common-ports

# Security Hub FSBP findings
# EC2.13: Security groups should not allow ingress from 0.0.0.0/0 or ::/0 to port 22
# EC2.14: Security groups should not allow ingress from 0.0.0.0/0 or ::/0 to port 3389
```

**Impact**: Instance compromise via brute-force or known exploit; lateral movement; cryptomining or ransomware deployment.

**Source**: SEC05/SEC06 https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/infrastructure-protection.html
