# Never Do Patterns — AWS IAM (pinned 2026-07-31)

7 anti-patterns with risk level, wrong vs correct examples, detection commands, and impact.

---

## 1. Long-term IAM access keys as the default credential

**Risk**: CRITICAL — violates SEC02-BP02 (temporary credentials)

**Why prohibited**: Static access keys leak in source code, container images, CI logs, and S3 bucket dumps. They do not auto-rotate. A leaked key provides persistent access until manually revoked. Long-term keys are an explicit narrow exception list (CodeCommit, Keyspaces, third-party client that cannot federate), not the default.

```
# WRONG: Application reads static credentials from environment
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
# (set in EC2 user data, baked into AMI, stored in .env file, hardcoded in app config)
```

```
# CORRECT: EC2 instance profile — SDK auto-discovers credentials from IMDS; no key distribution
# In Terraform:
resource "aws_instance" "app" {
  iam_instance_profile = aws_iam_instance_profile.app.name
  # ...
}
# For outside-AWS workloads: IAM Roles Anywhere (X.509 certificate trust)
# For CI/CD: aws-actions/configure-aws-credentials with OIDC, no stored keys
```

**Detection**:
```bash
aws iam generate-credential-report && aws iam get-credential-report \
  --query 'Content' --output text | base64 --decode | \
  awk -F, '$9 == "true" || $14 == "true"'
# Returns rows where access_key_1_active or access_key_2_active = true; review each
```

**Impact**: Data breach / account compromise via leaked static credential.

**Source**: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#bp-workloads-use-roles (accessed 2026-07-31)

---

## 2. Root access keys / routine root user sign-in

**Risk**: CRITICAL — violates SEC02-BP01

**Why prohibited**: Root has unrestricted access including billing and account closure. Root access keys cannot be permission-bounded and bypass most guardrails. AWS explicitly states: "We strongly recommend that you do not create access keys for your root user."

```
# WRONG: CI pipeline authenticates as root using root access keys
AWS_ACCESS_KEY_ID=AKIA... (root user key)
AWS_SECRET_ACCESS_KEY=...

# WRONG: Administrator signs in as root to perform routine tasks (console login as root user daily)
```

```
# CORRECT:
# - No root access keys exist (verify with Config rule iam-root-access-key-check: COMPLIANT)
# - Member account root credentials removed via Organizations centralized root access management
# - Rare root-only tasks (e.g., GovCloud linking, changing root email) done via AssumeRoot from management account
# - Day-to-day admin via a federated administrator role (never root)
```

**Detection**:
```bash
aws configservice describe-compliance-by-config-rule --config-rule-names iam-root-access-key-check
# Expected: COMPLIANT. NON_COMPLIANT = root has active access key; delete immediately.

# GuardDuty finding to monitor: Policy:IAMUser/RootCredentialUsage
# CloudTrail: alert via EventBridge on eventSource=signin.amazonaws.com AND userIdentity.type=Root
```

**Impact**: Full account takeover; irreversible actions (account closure, billing manipulation).

**Source**: https://docs.aws.amazon.com/IAM/latest/UserGuide/root-user-best-practices.html#ru-bp-access (accessed 2026-07-31)

---

## 3. Wildcard `Action: "*"` or `Resource: "*"` in production identity policies

**Risk**: HIGH — violates SEC03-BP02 (least privilege)

**Why prohibited**: Wildcard grants give the workload far more permissions than any task requires, enabling privilege escalation, lateral movement, and a massively enlarged blast radius on compromise. "To unblock a deploy" is not a valid justification.

```json
// WRONG: customer-managed policy attached to application role "to make it work"
{
  "Effect": "Allow",
  "Action": "*",
  "Resource": "*"
}
```

```bash
# CORRECT: Generate a least-privilege policy from actual CloudTrail activity
# Step 1 — generate policy from activity
aws accessanalyzer start-policy-generation \
  --policy-generation-details '{"principalArn":"arn:aws:iam::123456789012:role/AppRole"}' \
  --cloud-trail-details '{"trailArn":"arn:aws:cloudtrail:us-east-1:123456789012:trail/MyTrail","accessRole":"arn:aws:iam::123456789012:role/AccessAnalyzerRole","startTime":"2026-01-01T00:00:00Z","endTime":"2026-07-01T00:00:00Z"}'

# Step 2 — validate before attaching
aws accessanalyzer validate-policy --policy-document file://generated-policy.json --policy-type IDENTITY_POLICY
# Expected: no ERROR or SECURITY_WARNING findings
```

**Detection**:
```bash
aws accessanalyzer validate-policy --policy-document file://policy.json --policy-type IDENTITY_POLICY
# A policy with Action:* or Resource:* produces SECURITY_WARNING findings
```

**Impact**: Privilege escalation; large blast radius on credential compromise; compliance violation.

**Source**: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#best-practice-policy-validation (accessed 2026-07-31)

---

## 4. No MFA on root or privileged users

**Risk**: CRITICAL — violates SEC02-BP01

**Why prohibited**: Password-only sign-in is phishable. AWS now mandates root MFA within 35 days of the first console sign-in. Without MFA, a phished or brute-forced password is sufficient for full account access.

```
# WRONG: Root user and IAM administrator accounts have no MFA device registered.
# Password-only sign-in enabled.
```

```
# CORRECT:
# - Root: register phishing-resistant MFA (FIDO2 security key / passkey) immediately
#   Register up to 8 devices for redundancy
# - Human users via Identity Center: enforce phishing-resistant MFA at the IdP or via
#   Identity Center MFA policy (require MFA for all users / specific permission sets)
# - Residual IAM users (exception cases only): enforce via IAM policy condition:
#   "Condition": {"Bool": {"aws:MultiFactorAuthPresent": "true"}}
```

**Detection**:
```bash
aws configservice describe-compliance-by-config-rule --config-rule-names root-account-mfa-enabled
# Expected: COMPLIANT

# Credential report: mfa_active column for each user
aws iam get-credential-report --query 'Content' --output text | base64 --decode | \
  awk -F, '$8 == "false" && $4 == "true"'
# Returns IAM users with console password but no MFA — remediate or disable console access
```

**Impact**: Account compromise via credential phishing; full access to the AWS account.

**Source**: https://docs.aws.amazon.com/IAM/latest/UserGuide/root-user-best-practices.html#ru-bp-mfa (accessed 2026-07-31)

---

## 5. Unmonitored public / cross-account resource sharing

**Risk**: HIGH — violates SEC03-BP07

**Why prohibited**: Resource-based policies (S3 bucket policies, KMS key policies, Lambda resource policies, SQS, SNS, Secrets Manager, ECR, etc.) can silently grant access to external principals. Without an external-access analyzer, these exposures accumulate undetected.

```json
// WRONG: S3 bucket policy grants to AWS: * (public) or to an unknown external account with no analyzer
{
  "Effect": "Allow",
  "Principal": "*",
  "Action": "s3:GetObject",
  "Resource": "arn:aws:s3:::sensitive-bucket/*"
}
```

```bash
# CORRECT: Enable org-level external-access analyzer per Region
aws accessanalyzer create-analyzer \
  --analyzer-name org-external-access-us-east-1 \
  --type ORGANIZATION

# Add org-boundary condition to sensitive resources
# S3 bucket policy — deny access from outside org:
# "Condition": {"StringNotEquals": {"aws:PrincipalOrgID": "o-EXAMPLE"}}
# (pair with aws:ViaAWSService condition to allow AWS service integrations)

# Review findings
aws accessanalyzer list-findings --analyzer-arn <EXTERNAL_ACCESS_ANALYZER_ARN> \
  --filter '{"status":{"eq":["ACTIVE"]}}'
# Triage each ACTIVE finding: archive with justification or remediate
```

**Impact**: Data exfiltration; compliance violation (GDPR, SOC2, PCI-DSS data-boundary requirements).

**Source**: https://docs.aws.amazon.com/IAM/latest/UserGuide/what-is-access-analyzer.html (accessed 2026-07-31)

---

## 6. Treating SCPs / RCPs / permissions boundaries as if they grant access

**Risk**: MEDIUM — leads to either broken deployments or a false sense of security

**Why prohibited**: "No permissions are granted by SCPs and RCPs." A permissions boundary also does not grant. Misunderstanding this breaks deployments (assuming SCP allow = access) or creates unintended standing access (assuming SCP allow = sufficient). The effective-permission formula is a multi-way intersection, not a union.

```
# WRONG MENTAL MODEL:
# "We attached an SCP that allows s3:PutObject — our Lambda should now be able to write to S3."
# Result: Lambda still denied. The identity policy was never updated.
```

```
# CORRECT MENTAL MODEL:
# Effective = (identity-based policy ∩ resource-based policy [if cross-account])
#            ∩ SCPs ∩ RCPs ∩ permissions boundaries ∩ session policies
#
# Every layer must ALLOW; any DENY in any layer wins.
# SCPs/RCPs/boundaries only cap the maximum — the identity policy must still grant.

# Validate with policy simulator before deploying
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::ACCOUNT:role/LambdaRole \
  --action-names s3:PutObject \
  --resource-arns arn:aws:s3:::target-bucket/key
# Check OrganizationsDecisionDetail and EvalDecision in output
```

**Impact**: Broken deployments (service degradation) or unintended access (security gap depending on direction of misunderstanding).

**Source**: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#bp-permissions-guardrails (accessed 2026-07-31)

---

## 7. Stale unused roles / keys / permissions never pruned

**Risk**: MEDIUM — violates SEC03-BP04 (reduce permissions continuously)

**Why prohibited**: Unused access expands the attack surface silently. An unused role with broad permissions is a dormant credential that can be activated by an attacker who gains access to the trust chain (e.g., a compromised EC2 instance, CI environment, or third-party vendor).

```
# WRONG: IAM roles and access keys accumulate for years with no last-accessed review.
# Roles from decommissioned projects still exist; keys from departed employees still active.
```

```bash
# CORRECT: Enable unused-access analyzer at org scope
aws accessanalyzer create-analyzer \
  --analyzer-name org-unused-access \
  --type ORGANIZATION_UNUSED_ACCESS \
  --configuration '{"unusedAccess":{"unusedAccessAge":90}}'

# Review findings: unused roles, unused access keys, unused passwords, unused services/actions
aws accessanalyzer list-findings --analyzer-arn <UNUSED_ACCESS_ANALYZER_ARN> \
  --filter '{"status":{"eq":["ACTIVE"]}}'

# Last-accessed detail for a specific role
aws iam generate-service-last-accessed-details --arn <ROLE_ARN>
aws iam get-service-last-accessed-details --job-id <JOB_ID>
# Services not accessed in the review window (e.g., 90 days) → remove from policy or delete role
```

**Impact**: Enlarged blast radius on any compromise; dormant credentials abused months after the original access was intended to be revoked.

**Source**: https://docs.aws.amazon.com/IAM/latest/UserGuide/what-is-access-analyzer.html#what-is-access-analyzer-unused-access-analysis (accessed 2026-07-31)
