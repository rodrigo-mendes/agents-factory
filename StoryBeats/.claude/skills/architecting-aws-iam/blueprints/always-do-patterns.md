# Always Do Patterns — AWS IAM (pinned 2026-07-31)

8 mandatory patterns for production multi-account AWS Organizations workloads.
All patterns have degree of freedom: **Medium** (architecture guidance) with **Low** verification commands.

---

## 1. Federate human users via IAM Identity Center (SEC02-BP04 / BP02)

**Why**: "Require your human users to use temporary credentials when accessing AWS... we recommend that you use AWS IAM Identity Center to manage access to your accounts and permissions within those accounts." (IAM best practices — federation, 2026-07-31)

**AWS Services**: AWS IAM Identity Center, external IdP (Entra ID / Okta / Ping Identity) via SAML/OIDC, AWS STS

**Architecture decision**:
- Connect IAM Identity Center to your authoritative corporate IdP
- Model access as permission sets (role + policies) mapped to IdP groups
- Users authenticate at the IdP → Identity Center issues short-lived account role sessions via STS
- Result: zero standing IAM users with passwords in member accounts

**Verification**:
```bash
# Credential report must show zero non-exception IAM users with console passwords
aws iam generate-credential-report
aws iam get-credential-report --query 'Content' --output text | base64 --decode | \
  awk -F, '$4 == "true" && $1 != "<root_account>"'
# Expected: no output (or only documented exceptions like CodeCommit service accounts)
```

**Source**: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#bp-users-federation-idp (accessed 2026-07-31)

---

## 2. Deliver IAM roles to workloads — never access keys (SEC02-BP02)

**Why**: "there is no need to distribute long lived credentials for an IAM user to your workloads running on AWS." Compute services deliver role credentials automatically to the AWS SDK.

**AWS Services**:
- EC2: instance profiles (role attached to instance, SDK auto-discovers via IMDS)
- Lambda: execution role
- ECS: task role (set in task definition)
- EKS: Pod Identity (recommended) or IRSA (IAM Roles for Service Accounts)
- Outside AWS: IAM Roles Anywhere (X.509 PKI) or `AssumeRoleWithWebIdentity` (OIDC/JWT from CI/CD) or `AssumeRoleWithSAML`

**Architecture decision**:
- Attach a least-privilege role to every workload compute resource
- For on-prem and CI/CD: use IAM Roles Anywhere (cert-based) or OIDC federation — never static keys
- SDK credential chain discovers role credentials automatically; no key distribution needed

**Verification**:
```bash
# No active access keys for application IAM users (workload-type check)
aws iam list-users --query 'Users[*].UserName' --output text | tr '\t' '\n' | \
  xargs -I{} sh -c 'aws iam list-access-keys --user-name {} --query "AccessKeyMetadata[?Status==\`Active\`].AccessKeyId" --output text'
# Expected: no output for workload service accounts

# Scan for hardcoded credentials in repos (if git-secrets installed)
git secrets --scan
```

**Source**: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#bp-workloads-use-roles (accessed 2026-07-31)

---

## 3. Require phishing-resistant MFA for all human sign-in (SEC02-BP01)

**Why**: "We recommend that you use phishing-resistant MFA such as passkeys and security keys wherever possible." Root MFA is now mandatory within 35 days of first console sign-in.

**AWS Services**: FIDO2 security keys (YubiKey etc.), passkeys, IAM Identity Center MFA policies, IAM MFA for direct-user accounts

**Architecture decision**:
- Root user: register phishing-resistant MFA immediately; register up to 8 devices (hardware keys preferred)
- Human users via Identity Center: enforce phishing-resistant MFA at the IdP or via Identity Center MFA policy
- For any residual IAM users: enforce MFA via an IAM policy condition `aws:MultiFactorAuthPresent = true`

**Verification**:
```bash
# Security Hub control IAM.4 — root MFA
aws securityhub get-findings \
  --filters '{"ProductFields":[{"Key":"ControlId","Value":"IAM.4","Comparison":"EQUALS"}],"ComplianceStatus":[{"Value":"FAILED","Comparison":"EQUALS"}]}'
# Expected: no findings (empty Findings array)

# AWS Config: root-account-mfa-enabled
aws configservice describe-compliance-by-config-rule \
  --config-rule-names root-account-mfa-enabled
# Expected: ComplianceType: COMPLIANT
```

**Source**: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#enable-mfa-for-privileged-users (accessed 2026-07-31)

---

## 4. Centrally remove root credentials from member accounts (SEC02-BP01)

**Why**: "We strongly recommend you don't access the AWS account root user unless you have a task that requires root user credentials." For Organizations: "we recommend removing root user credentials from member accounts to help prevent unauthorized use."

**AWS Services**: AWS Organizations (centralized root access management), AWS STS `AssumeRoot`

**Architecture decision**:
- Enable centralized root access management via AWS Organizations
- Remove root password, access keys, and MFA from every member account
- Perform the narrow list of root-only tasks via `AssumeRoot` from the management account or delegated admin
- Never create root access keys; use a group email address for root registration

**Monitoring** (set up alongside this pattern):
```bash
# CloudTrail / EventBridge rule: alert on root sign-in or AssumeRoot events
# GuardDuty finding: Policy:IAMUser/RootCredentialUsage

# Config rule: no root access keys
aws configservice describe-compliance-by-config-rule \
  --config-rule-names iam-root-access-key-check
# Expected: COMPLIANT
```

**Source**: https://docs.aws.amazon.com/IAM/latest/UserGuide/root-user-best-practices.html (accessed 2026-07-31)

---

## 5. Apply least-privilege and reduce continuously (SEC03-BP02 / BP04)

**Why**: "grant only the permissions required to perform a task... As your use case matures, you can work to reduce the permissions." Continuous reduction is as important as the initial grant.

**AWS Services**: Customer-managed IAM policies, IAM Access Analyzer (policy generation + unused-access analyzer), IAM last-accessed information, CloudTrail

**Architecture decision — three-phase lifecycle**:
1. **Start**: Attach an AWS managed policy with a plausible scope (e.g., `AmazonS3ReadOnlyAccess`) to unblock the workload
2. **Generate**: After sufficient CloudTrail activity, generate a least-privilege customer-managed policy via IAM Access Analyzer policy generation; replace the managed policy
3. **Prune**: On a schedule (quarterly recommended), review unused-access findings and last-accessed data; remove services/actions not used in the review window

**Verification**:
```bash
# List unused-access findings for the org
aws accessanalyzer list-findings --analyzer-arn <UNUSED_ACCESS_ANALYZER_ARN> \
  --filter '{"status":{"eq":["ACTIVE"]}}'

# Last-accessed for a specific role
aws iam generate-service-last-accessed-details --arn <ROLE_ARN>
aws iam get-service-last-accessed-details --job-id <JOB_ID>
# Review: any service with LastAuthenticated older than 90 days is a pruning candidate
```

**Source**: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#grant-least-privilege (accessed 2026-07-31)

---

## 6. Establish org-wide guardrails: SCPs (principal) + RCPs (resource) (SEC03-BP05)

**Why**: "use AWS Organizations service control policies (SCPs) to establish permissions guardrails to control access for all principals... use resource control policies (RCPs) to establish permissions guardrails to control access for AWS resources." Note: "No permissions are granted by SCPs and RCPs."

**AWS Services**: AWS Organizations, SCPs, RCPs (applied at org/OU/account level)

**Baseline SCP recommendations** (deny-based guardrails):
- Deny root actions in member accounts
- Deny disabling CloudTrail or AWS Config
- Restrict to allowed Regions (`aws:RequestedRegion`)
- Deny leaving the organization
- Deny IAM user/key creation (if all-role policy in force)

**Baseline RCP recommendations** (data perimeter):
- S3: deny access unless `aws:PrincipalOrgID` matches your org ID and `aws:SecureTransport = true`
- Secrets Manager, KMS: similar org-ID conditions

**Verification**:
```bash
aws organizations list-policies --filter SERVICE_CONTROL_POLICY
aws organizations list-policies --filter RESOURCE_CONTROL_POLICY
# Confirm baseline SCPs and RCPs are attached to root or target OUs

# Simulate effective permissions (IAM policy simulator — console or API)
aws iam simulate-principal-policy \
  --policy-source-arn <PRINCIPAL_ARN> \
  --action-names <ACTION> \
  --resource-arns <RESOURCE_ARN>
```

**Source**: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#bp-permissions-guardrails (accessed 2026-07-31)

---

## 7. Enable IAM Access Analyzer and wire into CI/CD (SEC03-BP07)

**Why**: IAM Access Analyzer "provides more than 100 policy checks" and "monitors supported resource types continuously and generates a finding for resources that allow public or cross-account access."

**AWS Services**: IAM Access Analyzer (four types), IaC pipeline (Terraform/CloudFormation/CDK)

**Architecture decision**:
- External-access analyzer: create one per Region at org scope (monitors S3, KMS, Lambda, SQS, SNS, ECR, Secrets Manager, etc.)
- Unused-access analyzer: create one at org scope (Region-independent; monitors unused roles, keys, passwords, services)
- CI/CD gate: add `validate-policy` pre-apply; add `check-no-new-access` against a baseline reference policy post-plan

**Verification**:
```bash
# Confirm org-level analyzers exist
aws accessanalyzer list-analyzers \
  --query 'analyzers[?type==`ORGANIZATION`||type==`ORGANIZATION_UNUSED_ACCESS`]'

# Validate a policy in a pipeline step
aws accessanalyzer validate-policy \
  --policy-document file://policy.json \
  --policy-type IDENTITY_POLICY
# Expected: no SECURITY_WARNING or ERROR findings

# Check no new access vs baseline
aws accessanalyzer check-no-new-access \
  --new-policy-document file://new-policy.json \
  --existing-policy-document file://baseline-policy.json \
  --policy-type IDENTITY_POLICY
# Expected: {"result": "PASS"}
```

**Source**: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#bp-preview-access (accessed 2026-07-31)

---

## 8. Add Condition elements to enforce data perimeter (SEC03-BP02)

**Why**: "You can grant access to actions and resources, but only if the access request meets specific conditions." Conditions are the mechanism for enforcing the network, encryption, and organizational boundaries of a data perimeter.

**Key condition keys**:
- `aws:SecureTransport: true` — require TLS on any API call to the resource
- `aws:SourceVpc` / `aws:SourceVpce` — restrict access to calls originating from a specific VPC or endpoint
- `aws:PrincipalOrgID` — restrict to principals within the AWS Organization
- `aws:ViaAWSService: true` — allow AWS services acting on the principal's behalf (avoids breaking service integrations)
- `aws:ResourceOrgID` — restrict cross-account resource access to same-org resources only

**Example pattern** (S3 bucket policy deny-unless-org):
```json
{
  "Effect": "Deny",
  "Principal": "*",
  "Action": "s3:*",
  "Resource": ["arn:aws:s3:::example-bucket", "arn:aws:s3:::example-bucket/*"],
  "Condition": {
    "StringNotEqualsIfExists": {
      "aws:PrincipalOrgID": "o-EXAMPLE"
    },
    "BoolIfExists": {
      "aws:PrincipalIsAWSService": "false"
    }
  }
}
```

**Verification**:
```bash
# Policy simulator: confirm org-external principal is denied
aws iam simulate-custom-policy \
  --policy-input-list file://bucket-policy.json \
  --action-names s3:GetObject \
  --resource-arns arn:aws:s3:::example-bucket/key \
  --caller-arn arn:aws:iam::EXTERNAL_ACCOUNT:root
# Expected: DENY
```

**Source**: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#use-policy-conditions (accessed 2026-07-31)
