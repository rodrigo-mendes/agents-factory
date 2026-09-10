---
name: securing-aws-secrets-certificates
description: "Architects AWS secrets and certificate management using KMS, Secrets Manager, Parameter Store, and ACM. Use when designing credential storage, secret rotation, TLS certificate lifecycle, or encryption-at-rest/in-transit controls for AWS web applications targeting Well-Architected Security Pillar compliance (SEC02, SEC08, SEC09)."
---

## Function

Specialist in AWS Security Architecture — Secrets & Certificate Management (KMS, Secrets Manager, Parameter Store, ACM) for web applications. Implements SEC02-BP03 (secrets), SEC08-BP01/02 (encryption at rest), and SEC09-BP01/02 (encryption in transit).

## Version Context

**Technology**: AWS Security Services — Secrets & Certificate Management
**Target version**: AWS Security Services 2026
**Release date**: 2026-08-31 (research date)
**Support status**: Active
**Currency threshold**: 2027-08-31

**Critical 2026 changes**:
- ACM certificates now issued with 198-day validity (reduced from 398-day maximum)
- ACM no longer issues `clientAuth` EKU certificates as of June 2025
- KMS on-demand key rotation now supported for AWS_KMS and EXTERNAL-origin symmetric CMKs
- Secrets Manager console (April 2026) supports cross-account CMK ARN input directly
- Workload Credentials Provider (formerly Secrets Manager Agent) uses post-quantum ML-KEM key exchange by default

**Deprecated**: TLS 1.0 and 1.1 deprecated for AWS API endpoints as of February 2024.

⚠️ **CRITICAL — Agent Warning**:
This skill targets AWS Security Services 2026.
Reject patterns from pre-2024 sources for TLS policy and ACM certificate validity.
ACM certificates can NO longer have `clientAuth` EKU for public endpoints.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — 10 mandatory patterns with verification commands
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — 6 architectural crossroads with tradeoff matrices
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — 13 anti-patterns with wrong/correct examples
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 6 test cases for skill validation
- **[Verification Loop](#verification-loop)** — AWS CLI compliance checks
- **[Quick Reference](#quick-reference)** — Essential commands and Security Hub controls
- **[External Resources](#external-resources)** — Official documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

For complete patterns with verification commands, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**Mandatory patterns** (Complex domain — all 10 are required):

- **Replace long-term credentials with IAM roles** — Attach IAM roles to EC2/ECS/Lambda/EKS; use IAM Roles Anywhere for on-premises. Never place access keys in code, user data, AMIs, or environment variables. Security Hub: IAM.4.
- **Store all credentials in Secrets Manager with automatic rotation** — DB passwords, API keys, OAuth tokens go to Secrets Manager. Enable rotation (90-day maximum per SecretsManager.4). Use alternating-users strategy for production databases. Security Hub: SecretsManager.1, SecretsManager.4.
- **Enable CMK automatic rotation** — `aws kms enable-key-rotation --key-id <id>`. Set `RotationPeriodInDays` per compliance framework (default 365). Use on-demand rotation for unplanned events. Security Hub: KMS.4.
- **Use ACM for all public TLS certificates with DNS validation** — Request ACM public cert for every internet-facing domain. DNS validation = fully automated renewal; never email validation. CloudFront cert MUST be in `us-east-1`. Security Hub: ACM.1.
- **Route Secrets Manager calls through VPC PrivateLink** — Interface endpoint `com.amazonaws.<region>.secretsmanager` in every application VPC. Enable private DNS. Enforce `aws:SourceVpce` condition in Secrets Manager resource policy. Rotation Lambda in same VPC.
- **Scope KMS key policies to specific principals** — Never `"Principal": "*"`. Specify exact IAM role/user ARNs. IAM `Resource` element: always the key ARN, never `*` or alias ARN. Add `kms:ViaService` condition to restrict CMK to specific AWS service requests. Security Hub: KMS.1, KMS.2, KMS.5.
- **Enforce encryption at rest with separate CMKs per data classification** — One CMK per sensitivity tier (prod-secrets, prod-rds, staging). Enable account-level default EBS encryption, S3 default encryption, EFS default encryption. Security Hub: EC2.3, RDS.3.
- **Enforce TLS 1.2 minimum on all endpoints** — CloudFront: `TLSv1.2_2021` (includes TLS 1.3). ALB: `ELBSecurityPolicy-TLS13-1-2-2021-06`. S3 bucket policy: `aws:SecureTransport: true`. HTTP-to-HTTPS redirect on CloudFront and ALB.
- **Log all KMS and Secrets Manager activity to CloudTrail** — CloudTrail trail must include KMS management events; never add `kms.amazonaws.com` to `ExcludeManagementEventSources`. Enable GuardDuty for anomalous Secrets Manager access detection.
- **Use Parameter Store for static config; Secrets Manager for credentials** — Parameter Store: AMI IDs, feature flags, endpoint URLs. Secrets Manager: any value requiring rotation, cross-account access, or fine-grained audit. Never use Parameter Store SecureString as a credential store.

### ⚠️ Ask First

For complete decision matrices, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

**Architectural crossroads requiring context**:

- **KMS key type** — AWS owned key vs AWS managed key (`aws/<service>`) vs Customer Managed Key (CMK). Ask: "Does this secret or data store need cross-account access or a custom key policy?" CMK required if yes. Cost: CMK = $1/month/key.
- **Secrets Manager rotation strategy** — Managed (RDS only, zero Lambda) vs single-user Lambda (simple, brief auth-denial risk) vs alternating-users Lambda (zero downtime, needs superuser secret). Ask: "Can the application tolerate a brief credential rejection during rotation?"
- **Secret retrieval pattern for compute** — ECS env var injection (static at task start; needs force-new-deploy on rotation) vs Lambda Parameters and Secrets Extension (TTL 300s cache) vs language-specific SDK caching vs Workload Credentials Provider sidecar. Ask: "Must the secret refresh without a container restart?"
- **ACM certificate scope** — Wildcard (`*.example.com`) vs SAN cert (multiple FQDNs). Ask: "Do test environments use dynamically generated subdomain names?" Wildcard if yes; SAN for a stable set of known domains.
- **Public ACM cert vs Private CA** — ACM public (free, browser-trusted, no export, no mTLS) vs Private CA General ($400/month, exportable, mTLS, IAM Roles Anywhere) vs Private CA Short-lived ($50/month, high-volume short-lived certs). Ask: "Is the certificate for a public internet-facing endpoint or for internal/mTLS?"
- **Multi-region secrets architecture** — Single-region (simplicity) vs multi-region replication (+$0.40/secret/month/replica, local reads) vs centralized secrets account (governance, CMK required). Ask: "Must each region retrieve secrets sub-second or operate independently during a primary-region outage?"

### 🚫 Never Do

For complete anti-patterns with wrong/correct code, see [Never Do Patterns](./blueprints/never-do-patterns.md).

**Prohibited patterns** (13 identified, CRITICAL and HIGH risk):

- **Hardcoded credentials in source code** [CRITICAL] — Credentials reach version control, build artifacts, and container images. Use `secretsmanager.get_secret_value()` at runtime instead.
- **Plaintext secrets in ECS/Lambda environment variables** [HIGH] — Use `secrets` array with `valueFrom: <secret-ARN>` instead of `environment` array with the literal value.
- **No secret rotation** [HIGH] — SecretsManager.1/4 compliance failure; indefinite breach window. Enable automatic rotation within 90 days.
- **Self-signed certificates for public resources** [HIGH] — Browser warnings, no revocation path. Use free ACM public cert with DNS validation.
- **CloudFront certificate not in us-east-1** [HIGH] — CloudFront rejects ACM certs from any other region. Always `--region us-east-1` for CloudFront certs.
- **Wildcard principal (`"Principal": "*"`) in KMS key policy** [CRITICAL] — Allows any identity including anonymous to use the key. Specify exact ARNs.
- **`"Resource": "*"` in IAM for KMS cryptographic operations** [HIGH] — Grants access to all keys including cross-account. Use exact key ARN in `Resource`.
- **`aws:SourceIp` condition in Secrets Manager resource policy for Lambda rotation** [HIGH] — Lambda rotation calls come from AWS-internal addresses. Use `aws:SourceVpce` instead; `SourceIp` breaks rotation silently.
- **Parameter Store SecureString for rotating credentials** [HIGH] — Parameter Store has no rotation capability. Migrate to Secrets Manager with managed or Lambda-backed rotation.
- **Certificate pinning against an ACM-managed certificate** [HIGH] — ACM managed renewal generates a new key pair; pinned apps fail after renewal. Pin to Amazon Root CA instead.
- **Excluding KMS from CloudTrail** [HIGH] — Hides all key usage. Never set `ExcludeManagementEventSources: ["kms.amazonaws.com"]`.
- **Single AWS account for all Private CA hierarchy levels** [HIGH] — Root CA compromise untrusts entire PKI. Root CA in dedicated account; intermediate CAs in separate accounts.
- **Parameter Store policy overwrite** [MEDIUM] — `--policies` silently overwrites ALL existing policies. Always include all desired policies in a single call.

---

## Integration Patterns

For complete code examples, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**Primary integrations**:
- **Secrets Manager ↔ RDS Aurora** — Managed rotation (zero Lambda) or alternating-users Lambda template; task IAM role grants `secretsmanager:GetSecretValue` on exact secret ARN + `kms:Decrypt` on CMK ARN with `kms:ViaService`.
- **Secrets Manager ↔ ECS Fargate** — Secret injection via task definition `secrets` array (`valueFrom`); SDK-based retrieval via Lambda Parameters and Secrets Extension for live cache refresh.
- **ACM ↔ CloudFront + ALB** — Two separate ACM certificates: `us-east-1` for CloudFront, app-region for ALB. Both DNS-validated for automated renewal.
- **KMS ↔ S3 / EBS / EFS** — CMK per data classification tier; S3 Bucket Keys to reduce KMS API call volume; account-level EBS default encryption.
- **Secrets Manager ↔ EventBridge** — `Secret Label Updated` (AWSCURRENT moved) event triggers downstream automation (e.g., ECS force-new-deployment).

**Common problems**:
- **Rotation Lambda cannot reach Secrets Manager** → Rotation Lambda not in VPC, or no VPC endpoint in Lambda's VPC, or `aws:SourceIp` condition in resource policy. Solution: place Lambda in VPC with Secrets Manager VPC endpoint; use `aws:SourceVpce` condition.
- **CloudFront fails with `InvalidViewerCertificate`** → ACM cert is not in `us-east-1`. Request a new cert in `us-east-1`.
- **App fails post-rotation** → ECS env var injection is static; rotation requires force-new-deployment. Switch to SDK caching with Lambda extension for live refresh.

---

## Verification Loop

Run after any secrets/certificate architecture implementation:

### 1. KMS Rotation Status
```bash
aws kms get-key-rotation-status --key-id <key-id>
# Expected: KeyRotationEnabled: true
# If false: aws kms enable-key-rotation --key-id <key-id>
```

### 2. Secrets Manager Rotation Status
```bash
aws secretsmanager describe-secret --secret-id <secret-id>
# Expected: RotationEnabled: true, LastRotatedDate within 90 days
```

### 3. ACM Certificate Validation
```bash
aws acm describe-certificate --certificate-arn <arn> --region us-east-1
# Expected: DomainValidationOptions[].ValidationStatus: SUCCESS
# RenewalEligibility: ELIGIBLE
```

### 4. VPC Endpoint for Secrets Manager
```bash
aws ec2 describe-vpc-endpoints \
  --filters Name=service-name,Values=com.amazonaws.<region>.secretsmanager
# Expected: State: available, PrivateDnsEnabled: true
```

### 5. CloudTrail KMS Exclusion Check
```bash
aws cloudtrail get-event-selectors --trail-name <trail-name>
# Expected: kms.amazonaws.com NOT in ExcludeManagementEventSources
```

### 6. Security Hub Compliance Baseline
```bash
aws securityhub get-findings \
  --filters '{"ComplianceStatus":[{"Value":"FAILED","Comparison":"EQUALS"}],"GeneratorId":[{"Value":"aws-foundational-security-best-practices/v/1.0.0/KMS","Comparison":"PREFIX"}]}'
# Expected: no FAILED findings for KMS.1, KMS.2, KMS.4, KMS.5, SecretsManager.1, SecretsManager.4, ACM.1
```

**Troubleshooting**:
- `SecretsManager.2` (rotation failed) → Check rotation Lambda CloudWatch Logs; verify VPC endpoint and database connectivity
- `KMS.5` (key publicly accessible) → Inspect key policy for `"Principal": "*"`; replace with exact ARNs
- `ACM.1` (expiry approaching) → Verify DNS CNAME validation record still in place; check certificate association with AWS service

---

## Quick Reference

**Essential CLI commands**:
```bash
# Request ACM public cert (CloudFront)
aws acm request-certificate --domain-name example.com --validation-method DNS --region us-east-1

# Enable KMS rotation
aws kms enable-key-rotation --key-id <key-id>

# On-demand KMS rotation
aws kms rotate-key-on-demand --key-id <key-id>

# Enable Secrets Manager rotation
aws secretsmanager rotate-secret --secret-id <id> \
  --rotation-lambda-arn <arn> --rotation-rules AutomaticallyAfterDays=30

# Validate Secrets Manager resource policy
aws secretsmanager validate-resource-policy --resource-policy file://policy.json

# Promote multi-region replica to standalone (DR failover)
aws secretsmanager stop-replication-to-replica --secret-id <replica-arn>
```

**Security Hub controls baseline**:

| Control | Severity | Domain |
|---------|----------|--------|
| KMS.1 | Medium | No wildcard Decrypt (managed policy) |
| KMS.2 | Medium | No wildcard Decrypt (inline policy) |
| KMS.3 | Critical | CMK not pending deletion |
| KMS.4 | Medium | CMK rotation enabled |
| KMS.5 | Critical | CMK not publicly accessible |
| SecretsManager.1 | Medium | Rotation enabled |
| SecretsManager.2 | Medium | Rotation succeeds |
| SecretsManager.3 | Medium | Unused secrets removed within 90 days |
| SecretsManager.4 | Medium | Rotated within 90 days |
| ACM.1 | Medium | Renewal within 30 days of expiry |
| ACM.2 | High | RSA key 2048 bits or greater |

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/securing-aws-secrets-certificates/
├── SKILL.md                              <- This file (index + guardrails)
└── blueprints/
    ├── always-do-patterns.md             <- 10 mandatory patterns, verification commands, IAM examples
    ├── ask-first-decisions.md            <- 6 decision matrices with cost profiles
    ├── never-do-patterns.md              <- 13 anti-patterns with wrong/correct examples
    └── evaluation-scenarios.md           <- 6 test cases for skill-evaluator
```

---

## External Resources

### Official Documentation
- [Well-Architected Security Pillar — SEC02 (Secrets)](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_identities_secrets.html) — 2026-08-31
- [Well-Architected Security Pillar — SEC08 (Encryption at Rest)](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_protect_data_rest_key_mgmt.html) — 2026-08-31
- [Well-Architected Security Pillar — SEC09 (Encryption in Transit)](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_protect_data_transit_encrypt.html) — 2026-08-31
- [AWS KMS Key Rotation](https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html) — 2026-08-31
- [AWS KMS IAM Policy Best Practices](https://docs.aws.amazon.com/kms/latest/developerguide/iam-policies-best-practices.html) — 2026-08-31
- [Secrets Manager — Rotating Secrets](https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotating-secrets.html) — 2026-08-31
- [Secrets Manager — Rotation Strategy](https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotation-strategy.html) — 2026-08-31
- [Secrets Manager — VPC Endpoint](https://docs.aws.amazon.com/secretsmanager/latest/userguide/vpc-endpoint-overview.html) — 2026-08-31
- [Secrets Manager — Best Practices](https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html) — 2026-08-31
- [ACM Best Practices](https://docs.aws.amazon.com/acm/latest/userguide/acm-bestpractices.html) — 2026-08-31
- [ACM Supported Events (EventBridge)](https://docs.aws.amazon.com/acm/latest/userguide/supported-events.html) — 2026-08-31

### Security Hub Control References
- [Security Hub — KMS Controls](https://docs.aws.amazon.com/securityhub/latest/userguide/kms-controls.html) — 2026-08-31
- [Security Hub — Secrets Manager Controls](https://docs.aws.amazon.com/securityhub/latest/userguide/secretsmanager-controls.html) — 2026-08-31
- [AWS Private CA Pricing](https://aws.amazon.com/private-ca/pricing/) — 2026-08-31
