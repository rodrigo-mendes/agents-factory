# Always Do Patterns — architecting-aws-security-pillar

Source: AWS Well-Architected Framework Security Pillar, November 6, 2024 (verified 2026-08-27)

---

## SEC-AD-1 — Separate workloads via multi-account structure

**Pillar alignment**: Security foundations (SEC01-BP01)
**Risk if omitted**: HIGH — one compromised workload can access all co-resident workloads

**Architecture decision**:
Design an OU hierarchy aligned to data sensitivity, workload type, and environment. Typical structure:

```
Root
├── Security OU          ← Log Archive account, Security Tooling account
├── Infrastructure OU    ← Networking account, Shared Services account
├── Workloads OU
│   ├── Prod OU         ← One account per production workload
│   └── Non-Prod OU     ← One account per team/environment
└── Sandbox OU          ← Unrestricted developer accounts
```

Apply SCPs at the OU level so all accounts beneath inherit guardrails. Apply RCPs to restrict resource access from external principals (new in this edition). Use AWS Control Tower Account Factory to vend new accounts with baseline controls pre-applied.

**Verification**:
```bash
aws organizations list-accounts \
  --query 'Accounts[*].{Id:Id,Name:Name,Status:Status}'
aws organizations list-policies --filter SERVICE_CONTROL_POLICY
aws organizations list-policies --filter RESOURCE_CONTROL_POLICY
# AWS Config aggregator compliance view in the management/security account
# Security Hub AWS Foundational Security Best Practices score
```

**Trade-offs**: More accounts increases governance overhead; requires centralized tooling (Control Tower or DIY pipeline) and cross-account IAM role design from day one. The blast-radius reduction is worth this overhead for all production workloads.

**Source**: SEC01-BP01 https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_securely_operate_multi_accounts.html

---

## SEC-AD-2 — Federated human access with temporary credentials via IAM Identity Center

**Pillar alignment**: Identity and access management (SEC02-BP04)
**Risk if omitted**: HIGH — permanent credentials provide persistent unauthorized access with no automatic expiry

**Architecture decision**:
Route all human access through IAM Identity Center connected to the corporate IdP (Okta, Entra ID) or the native identity store. Define permission sets per job function (least privilege). Users authenticate once and receive short-lived STS credentials (1–12 hour default) for the target account.

```
Corporate IdP (Okta/Entra ID)
  ↕ SAML/OIDC
IAM Identity Center
  └─ Permission Sets (per job function)
       └─ Provisioned as IAM roles in each target account
            └─ STS AssumeRole → short-lived credentials
```

No per-user IAM users with permanent access keys. No programmatic credentials for humans.

**Verification**:
```bash
# Confirm no active human access keys
aws iam generate-credential-report
aws iam get-credential-report --query 'Content' --output text | base64 -d | \
  awk -F',' 'NR>1 {print $1, $4, $9, $14}'
# access_key_1_active and access_key_2_active should be false for all human users

# Confirm federated flow is in use
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=AssumeRoleWithSAML \
  --max-items 5
```

**Source**: SEC02-BP04 + IAM best practices https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html [✓✓ Triangulated]

---

## SEC-AD-3 — Workloads use IAM roles, never embedded keys

**Pillar alignment**: Identity and access management (SEC03 series)
**Risk if omitted**: HIGH — embedded keys are difficult to rotate, easily leaked via source control

**Architecture decision per compute type**:

| Compute type | Credential mechanism |
|---|---|
| EC2 | Instance profile (IAM role attached at launch) |
| Lambda | Execution role |
| ECS | Task role |
| EKS (pods) | Pod Identity (one role per Kubernetes service account via EKS Pod Identity Agent add-on) |
| On-premises / external | IAM Roles Anywhere with X.509 certificates from a registered Trust Anchor |

The AWS SDK auto-discovers credentials via the credential provider chain — no credential management code required.

**Verification**:
```bash
# Check for IAM Access Analyzer unused-access findings (active keys not used in 90+ days)
aws accessanalyzer list-findings \
  --analyzer-arn arn:aws:access-analyzer:REGION:ACCOUNT:analyzer/ANALYZER \
  --filter '{"findingType":{"contains":["UnusedIAMUserAccessKey"]}}'

# Verify EKS Pod Identity add-on
aws eks describe-addon \
  --cluster-name MY_CLUSTER \
  --addon-name eks-pod-identity-agent \
  --query 'addon.status'
# Expected: ACTIVE
```

**Source**: SEC03 series + IAM best practices [✓✓ Triangulated]

---

## SEC-AD-4 — Phishing-resistant MFA for all IAM and root users

**Pillar alignment**: Identity and access management (SEC02 / Design Principle 1)
**Risk if omitted**: HIGH — TOTP-based MFA is bypassable by phishing attacks targeting the TOTP code

**Architecture decision**:
Enforce FIDO2/WebAuthn passkeys or hardware security keys (YubiKey, etc.) for:
- All IAM Identity Center users (enforced via MFA setting in Identity Center configuration)
- Any remaining IAM users (if present — ideally none)
- Root user of every account (use hardware key stored in a physical vault)

Delete all root access keys. Block root API key creation via SCP.

**SCP example to block root API key creation**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyRootAccessKeyCreation",
      "Effect": "Deny",
      "Action": "iam:CreateAccessKey",
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:PrincipalType": "Root"
        }
      }
    }
  ]
}
```

**Verification**:
```bash
# IAM credential report — mfa_active column
aws iam get-credential-report --query 'Content' --output text | base64 -d | \
  awk -F',' 'NR>1 {print $1, $8}'  # column 8 = mfa_active

# AWS Config rules
aws configservice describe-compliance-by-config-rule \
  --config-rule-names mfa-enabled-for-iam-console-access root-account-mfa-enabled
```

**Source**: IAM best practices + Security Pillar Design Principle 1 [✓✓ Triangulated]

---

## SEC-AD-5 — Encryption at rest with AWS KMS

**Pillar alignment**: Data protection (SEC08-BP01 / SEC08-BP02)
**Risk if omitted**: HIGH — unencrypted media or snapshots expose data if mishandled

**Architecture decision**:

1. Classify data: public / internal / confidential / restricted
2. Map classification to key type:
   - Restricted (PCI, HIPAA, FedRAMP) → KMS CMK with explicit key policy and CloudTrail audit
   - Confidential → KMS CMK
   - Internal → AWS-managed KMS key
   - Public → AWS-managed KMS key or S3-managed (SSE-S3)
3. Enable service-level defaults:
   - S3: bucket default encryption (SSE-KMS or SSE-S3)
   - EBS: account-level encryption-by-default (`aws ec2 enable-ebs-encryption-by-default`)
   - RDS: storage encryption enabled at creation time

**Verification**:
```bash
# AWS Config rules
aws configservice describe-compliance-by-config-rule \
  --config-rule-names encrypted-volumes s3-bucket-server-side-encryption-enabled rds-storage-encrypted

# EBS encryption default
aws ec2 get-ebs-encryption-by-default
# Expected: {"EbsEncryptionByDefault": true}
```

**Source**: SEC08-BP01/02 https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-data-at-rest.html [✓✓ Triangulated]

---

## SEC-AD-6 — Continuous detection: logging and threat detection

**Pillar alignment**: Detection (SEC04-BP01 through BP04)
**Risk if omitted**: CRITICAL — breaches undetected, forensic investigation impossible, compliance failures

**Architecture decision (four-part)**:
1. **SEC04-BP01**: Organizational CloudTrail trail → Log Archive S3 bucket (Object Lock WORM enabled). Include management events + S3 data events for sensitive buckets. Member accounts must not be allowed to disable the trail (enforce via SCP).
2. **SEC04-BP02**: Centralize logs — all GuardDuty, Config, Security Hub findings, and VPC Flow Logs route to the Log Archive or Security Tooling account.
3. **SEC04-BP03**: Correlate findings in Security Hub. Enable AWS Foundational Security Best Practices and CIS AWS Foundations Benchmark standards. Assign the Security Tooling account as the delegated admin.
4. **SEC04-BP04**: Automate remediation — EventBridge rule (filter High/Critical severity + specific finding type) → Lambda function or SSM Automation runbook.

**Verification**:
```bash
# Confirm organizational trail
aws cloudtrail describe-trails \
  --query 'trailList[?IsOrganizationTrail==`true`].{Name:Name,S3Bucket:S3BucketName}'
# Expected: at least one trail with IsOrganizationTrail: true

# GuardDuty org-wide status
aws guardduty get-organization-configuration \
  --detector-id $(aws guardduty list-detectors --query 'DetectorIds[0]' --output text)
# Expected: AutoEnable: ALL or NEW

# Security Hub enabled standards
aws securityhub get-enabled-standards
# Expected: aws-foundational-security-best-practices present and READY
```

**Source**: SEC04 https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/detection.html [✓✓ Triangulated]

---

## SEC-AD-7 — Defense-in-depth infrastructure protection (network and compute)

**Pillar alignment**: Infrastructure protection (SEC05 protecting networks / SEC06 protecting compute)
**Risk if omitted**: HIGH — single perimeter control is insufficient; trust boundaries must be enforced at every layer

**Architecture decision (network — SEC05)**:
- Workloads in private subnets; no direct internet ingress to application or data tiers
- Internet ingress terminates at CloudFront or ALB in a public subnet, fronted by AWS WAF (managed rule groups: Core, SQLi, IP Reputation, rate-based)
- Egress via NAT Gateway or VPC endpoints for AWS services (prefer VPC endpoints to keep traffic off the internet)
- Security Groups as the primary stateful control; NACLs as a coarse secondary layer
- AWS Shield (Advanced for high-value, revenue-critical internet-facing workloads)

**Architecture decision (compute — SEC06)**:
- Automated patching via Systems Manager Patch Manager; no manual patch windows
- No inbound management ports (22/3389) in security groups; use Systems Manager Session Manager for shell access
- Immutable AMIs built from a hardened pipeline (no snowflake servers)
- Continuous CVE scanning via Amazon Inspector; findings fed to Security Hub

**Verification**:
```bash
# Confirm no SSH open to internet
aws ec2 describe-security-groups \
  --filters "Name=ip-permission.from-port,Values=22" \
            "Name=ip-permission.cidr,Values=0.0.0.0/0" \
  --query 'SecurityGroups[*].GroupId'
# Expected: empty

# WAF association on ALBs
aws wafv2 list-resources-for-web-acl \
  --web-acl-arn ARN_OF_WEBACL \
  --resource-type APPLICATION_LOAD_BALANCER
# Expected: all internet-facing ALBs listed

# Systems Manager patch compliance
aws ssm describe-patch-compliance-data \
  --filters 'Key=PatchGroup,Values=production'
```

**Source**: SEC05/SEC06 https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/infrastructure-protection.html

---

## SEC-AD-8 — Secure the software delivery lifecycle (application security)

**Pillar alignment**: Application security (SEC11-BP01 through SEC11-BP08)
**Risk if omitted**: HIGH — defects resolved at production are 100x more expensive than at design; supply chain attacks

**Architecture decision (four areas per SEC11)**:

1. **Organization & culture**: Train builders on secure coding (SEC11-BP01); embed security ownership in workload teams (SEC11-BP08)
2. **Security of the pipeline**: Protect pipeline infrastructure itself — branch protection, required code reviews, artifact signing with AWS Signer (SEC11-BP06/07)
3. **Security in the pipeline**: Mandatory stages for SAST (CodeGuru/Q Developer), SCA (Inspector), secret scanning; penetration testing cadence (SEC11-BP02/03/04)
4. **Dependency management**: Centralize all packages in AWS CodeArtifact; no direct internet package registries in production builds; threat-model each workload (SEC11-BP05)

Deployments are programmatic only (CodePipeline) — no manual production changes (SEC11-BP06).

**Verification**:
```bash
# Inspector coverage for ECR images
aws inspector2 list-coverage \
  --filter-criteria '{"resourceType":[{"comparison":"EQUALS","value":"AWS_ECR_CONTAINER_IMAGE"}]}' \
  --query 'coveredResources[*].{Resource:resourceId,Status:scanStatus.statusCode}'
# Expected: ACTIVE for all container images in production repositories

# CodeArtifact as the only configured package source
aws codeartifact list-domains --query 'domains[*].name'
# All builds should reference CodeArtifact repository URLs, not public registries directly
```

**Source**: SEC11 https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/application-security.html
