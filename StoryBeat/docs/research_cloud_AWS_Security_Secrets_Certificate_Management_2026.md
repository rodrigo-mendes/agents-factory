# AWS Security Architecture — Secrets & Certificate Management

## Metadata
```yaml
Full_Name: "AWS Security Architecture — Secrets & Certificate Management (ACM, KMS, Parameter Store, Secrets Manager)"
Cloud_Provider: "AWS"
Architecture_Domain: "Security Architecture — Secrets & Certificate Management (ACM, KMS, Parameter Store, Secrets Manager)"
Target_Edition: "AWS Security Services 2026"
Architecture_Context: "web application"
Official_Source_URL: "https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-08-31"
Currency_Threshold: "2027-08-31"
Research_Depth: "exhaustive"
Max_Iterations: 8
Research_Quality_Score: "86%"
Gap_Loop_Ran: "true"
Iterations_Used: "6 of 8"
Triangulated_Count: 42
Unverified_Count: 12
Irresolvable_Count: 5
```

---

## Executive Summary

AWS secrets and certificate management is the discipline of provisioning, storing, rotating, auditing, and revoking the cryptographic secrets and X.509 certificates that a web application requires to operate securely. The four core AWS services in this domain — AWS Key Management Service (KMS), AWS Secrets Manager, AWS Systems Manager Parameter Store, and AWS Certificate Manager (ACM) — compose into a layered architecture: KMS provides the envelope-encryption foundation; Secrets Manager and Parameter Store build on KMS to store credentials and configuration; ACM manages TLS certificate lifecycle for every internet-facing endpoint. Together they implement the Well-Architected Security Pillar SEC02 (identity/secrets), SEC08 (data at rest), and SEC09 (data in transit) best practices.

In 2026 the most significant changes are: (1) ACM now issues certificates with 198-day validity (reduced from the historical 398-day maximum); (2) ACM no longer issues certificates with the clientAuth extended key usage as of June 2025, aligning with new browser requirements; (3) KMS on-demand key rotation is now supported for both AWS_KMS-origin and EXTERNAL-origin symmetric CMKs with a custom RotationPeriodInDays beyond the previous 365-day default; (4) the Secrets Manager console (April 2026) supports entering a cross-account CMK ARN directly; and (5) the Workload Credentials Provider (formerly Secrets Manager Agent) now uses post-quantum ML-KEM key exchange by default.

The three most critical architecture guardrails for a web application are: never embed long-lived credentials — replace with IAM roles everywhere possible and rotate remaining credentials via Secrets Manager with automated Lambda rotation; enforce private connectivity — route all Secrets Manager API calls through VPC PrivateLink interface endpoints, scope access via aws:SourceVpce resource-policy conditions, and co-locate rotation Lambda functions in the same VPC as the database; and never use self-signed certificates or manual renewal — request ACM-managed certs (free), use DNS validation for fully automated renewal, and always provision CloudFront certificates in us-east-1 regardless of the application primary region.

---

## Cloud Architecture Glossary

```
Term: Customer Managed Key (CMK)
Definition: A KMS key created, owned, and managed by the customer in their AWS account. Full control over key policies, IAM policies, grants, rotation schedule (including RotationPeriodInDays), and deletion scheduling. KeyManager value: CUSTOMER. Billed at $1.00/month per key.
Provider Docs Section: https://docs.aws.amazon.com/kms/latest/developerguide/concepts.html
Architect Usage: Required when cross-account key access, fine-grained key policy conditions (kms:ViaService, kms:EncryptionContext), or compliance-mandated rotation control is needed. Always reference by key ARN in IAM Resource elements, never by alias.
Common Confusion: Confused with AWS managed keys (alias aws/<service>), which are visible in the account but cannot have their key policies modified and do not support cross-account access.
```

```
Term: AWS Managed Key
Definition: A KMS key created and managed by an AWS service on behalf of the customer. Alias format: aws/<service> (e.g., aws/s3, aws/secretsmanager). Auditable in CloudTrail; key policy managed by the service and not modifiable. Rotated annually since May 2022. No monthly storage fee. Does not support cross-account sharing.
Provider Docs Section: https://docs.aws.amazon.com/kms/latest/developerguide/concepts.html
Architect Usage: Suitable for single-account workloads with no cross-account requirements. Not usable for cross-account Secrets Manager secrets — CMK required for those.
Common Confusion: Confused with AWS owned keys (in an AWS-service-managed account, not visible in the customer CloudTrail, no monthly charge).
```

```
Term: Envelope Encryption
Definition: A two-layer encryption pattern where a data key (AES-256 symmetric) encrypts the plaintext data locally, and the data key is then encrypted (wrapped) by a KMS key. The encrypted data and encrypted data key are stored together. To decrypt: call KMS Decrypt on the encrypted data key, recover the plaintext data key, decrypt the data, then discard the plaintext data key immediately from memory.
Provider Docs Section: https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html
Architect Usage: Used automatically by Secrets Manager and Parameter Store SecureString (advanced tier). For application-layer encryption, use AWS Encryption SDK. CMK rotation does NOT re-encrypt existing data keys — only new GenerateDataKey calls use new material.
Common Confusion: Confused with direct KMS encryption (Encrypt API), which encrypts data directly under the KMS key — only viable for small payloads up to 4 KB.
```

```
Term: KMS Automatic Key Rotation
Definition: The process by which AWS KMS generates new cryptographic key material (a new HSM backing key) for a symmetric CMK on a configurable schedule without changing the key ID, ARN, or alias. All previous backing key versions are retained for decryption. Supported only for symmetric encryption CMKs with AWS_KMS or EXTERNAL origin.
Provider Docs Section: https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html
Architect Usage: Enable on all CMKs. Custom RotationPeriodInDays supported (default 365). Monitor via EventBridge KMS CMK Rotation event and CloudTrail RotateKey. Use on-demand rotation for immediate unplanned rotation without changing the automatic schedule.
Common Confusion: Confused with manual rotation, which requires creating a new KMS key and updating aliases or application config. Manual rotation is the only option for asymmetric keys, HMAC keys, and custom key store keys.
```

```
Term: Encryption Context
Definition: An optional but recommended set of non-secret key-value pairs passed to KMS cryptographic operations. Cryptographically bound to the resulting ciphertext — decryption must supply the identical context. Appears in CloudTrail logs and can be referenced in IAM/key policy condition keys (e.g., kms:EncryptionContext:<key>).
Provider Docs Section: https://docs.aws.amazon.com/kms/latest/developerguide/concepts.html
Architect Usage: Secrets Manager passes SecretARN + SecretVersionId; Parameter Store passes PARAMETER_ARN. Use kms:EncryptionContext:SecretARN in IAM conditions to scope decryption to a specific resource.
Common Confusion: Confused with a password or authentication credential. The encryption context is not secret and appears in CloudTrail logs.
```

```
Term: Alternating-Users Rotation (Secrets Manager)
Definition: A Secrets Manager rotation strategy maintaining two database users (original + clone) with identical permissions. Both users credentials are valid simultaneously. Rotation alternates between them. Requires a superuser secret because most users cannot clone themselves.
Provider Docs Section: https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotation-strategy.html
Architect Usage: Use for high-availability production databases where even a brief auth-denial window during rotation is unacceptable. If the original users permissions change post-clone, the cloned users permissions must be updated manually.
Common Confusion: Confused with single-user rotation, which updates a single users password and has a brief window where the new credential is in the secret but not yet accepted by all database connections.
```

```
Term: SecureString (Parameter Store)
Definition: A Parameter Store parameter type whose value is encrypted using AWS KMS. Standard SecureString uses KMS Encrypt directly; advanced SecureString uses envelope encryption via AWS Encryption SDK. Default key is aws/ssm. Retrieve with WithDecryption=true to receive plaintext.
Provider Docs Section: https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html
Architect Usage: Use for configuration values requiring encryption that do not need automatic rotation. For credentials requiring rotation, cross-region replication, or fine-grained per-secret audit, use Secrets Manager instead.
Common Confusion: Confused with Secrets Manager — SecureString does not provide automatic rotation, cross-account resource-based policies, or native database credential integration.
```

```
Term: Parameter Policy (Parameter Store)
Definition: Advanced-tier-only feature that assigns lifecycle rules to a parameter: Expiration (deletes parameter at timestamp), ExpirationNotification (EventBridge event N days/hours before expiry), NoChangeNotification (EventBridge event if not modified for N days). Max 10 policies per parameter.
Provider Docs Section: https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-policies.html
Architect Usage: Adding a new policy via --policies OVERWRITES ALL existing policies. Always include all desired policies in a single call. Parameter policies cannot rotate credentials — they only alert or delete.
Common Confusion: Confused with key rotation — parameter policies trigger alerts/deletion but perform no credential rotation.
```

```
Term: ACM Managed Renewal
Definition: The automatic certificate renewal process where ACM renews a certificate without human action (DNS-validated, with CNAME record still in place) or sends email notices (email-validated). Eligible certificates must be associated with an AWS service (ALB, CloudFront, API GW).
Provider Docs Section: https://docs.aws.amazon.com/acm/latest/userguide/managed-renewal.html
Architect Usage: Always use DNS validation with association to AWS services for fully automated renewal. The certificate ARN does not change on renewal. Each regions certificate renews independently.
Common Confusion: Confused with manual renewal of imported certificates — imported certs must be renewed and re-imported manually.
```

```
Term: Certificate Transparency (CT) Log
Definition: A publicly accessible, append-only log of all publicly trusted TLS certificates. ACM automatically submits all public certificates to CT logs before issuance. Domain name is visible; private key is not. Cannot be opted out of per browser policy requirements.
Provider Docs Section: https://docs.aws.amazon.com/acm/latest/userguide/acm-concepts.html
Architect Usage: Do not include sensitive information in public certificate domain names — they appear permanently in public CT logs and are searchable by anyone.
Common Confusion: Confused with CloudTrail logging — CT logs are public internet-facing logs; CloudTrail logs are private AWS account logs of API calls.
```

```
Term: AWS Private CA (Private Certificate Authority)
Definition: An AWS service for establishing a private root or subordinate CA hierarchy and issuing TLS certificates via API. Certificates are exportable. Use cases: internal TLS, mTLS, Kubernetes pod certs, code signing, IAM Roles Anywhere (X.509 to temporary IAM creds for on-premises).
Provider Docs Section: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_protect_data_transit_key_cert_mgmt.html
Architect Usage: Deploy each CA level in a separate AWS account (root CA, intermediate CAs, end-entity). Private certs via IssueCertificate API are NOT eligible for ACM managed renewal.
Common Confusion: Confused with ACM public certificates — Private CA issues internally trusted certs; browsers do not trust them by default.
```

```
Term: VPC Interface Endpoint (PrivateLink) for Secrets Manager
Definition: An AWS PrivateLink-powered interface endpoint that routes Secrets Manager API calls through the VPC private network without traversing the public internet. Service name: com.amazonaws.<region>.secretsmanager. Private DNS enabled: standard regional hostname resolves to private endpoint with no code changes.
Provider Docs Section: https://docs.aws.amazon.com/secretsmanager/latest/userguide/vpc-endpoint-overview.html
Architect Usage: Mandatory in regulated environments. Enforce via aws:SourceVpce condition in Secrets Manager resource policies. Rotation Lambda must be in the same VPC as the endpoint. Do not use aws:SourceIp conditions for Lambda rotation.
Common Confusion: Confused with NAT Gateway — NAT routes traffic to the public Secrets Manager endpoint; VPC endpoint eliminates that public traversal entirely.
```

```
Term: ECS Task IAM Role vs Task Execution Role
Definition: Two distinct IAM roles for ECS. Task IAM Role: grants permissions to application code INSIDE the container (e.g., secretsmanager:GetSecretValue). Task Execution Role: grants permissions to the ECS CONTROL PLANE to pull container images and inject secrets before the container starts.
Provider Docs Section: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html
Architect Usage: Never put Secrets Manager GetSecretValue permission on the execution role unless needed for injection at container start. On EC2-backed ECS with awsvpc network mode, set ECS_AWSVPC_BLOCK_IMDS=true.
Common Confusion: Confused with each other — execution role is for ECS infrastructure; task role is for application business logic at runtime.
```

```
Term: Zelkova (Policy Validation)
Definition: An automated reasoning engine used by Secrets Manager and IAM Access Analyzer to analyze resource-based policies and determine if they grant overly broad or public access. Invoked automatically when attaching a resource policy via the Secrets Manager console or calling ValidateResourcePolicy API.
Provider Docs Section: https://docs.aws.amazon.com/secretsmanager/latest/userguide/auth-and-access_resource-based-policies.html
Architect Usage: Always call PutResourcePolicy with BlockPublicPolicy=true. Use ValidateResourcePolicy in IaC CI/CD pipelines.
Common Confusion: Confused with runtime enforcement — Zelkova performs static policy analysis at authoring time, not at runtime access evaluation.
```

```
Term: KMS Grant
Definition: A policy instrument for programmatic, temporary delegation of specific KMS operations to a principal. Each grant covers exactly one KMS key; can only allow (never deny); supports encryption context or SourceArn constraints; subject to eventual consistency; max 50,000 grants per key.
Provider Docs Section: https://docs.aws.amazon.com/kms/latest/developerguide/grants.html
Architect Usage: Use for temporary/programmatic access by AWS services (e.g., Secrets Manager rotation Lambda). Limit kms:CreateGrant broadly — it is equivalent in security impact to kms:PutKeyPolicy.
Common Confusion: Confused with IAM policies — grants are key-specific, can only allow, and are separate from IAM policy evaluation.
```

---

## Architecture Guardrails

> Confidence legend: High (2+ official sources, dated 12mo or less) | Medium (1 source or dated 12-24mo) | Low (community source or dated more than 24mo — verify before use)

### Mandatory Patterns

**Replace Long-Term Credentials with IAM Roles** [HIGH CONFIDENCE]
- Pillar Alignment: SEC02-BP03 (Store and use secrets securely), SEC02-BP05 (Audit and rotate credentials periodically)
- Why: "Eliminate reliance on long-term static credentials" — Well-Architected Security Pillar Design Principle 1. IAM roles deliver temporary credentials automatically via EC2 instance metadata, Lambda execution context, ECS credential endpoint, or EKS IRSA.
- AWS Services: IAM Roles, ECS Task IAM Role, Lambda Execution Role, EKS IRSA / Pod Identity, IAM Roles Anywhere
- Architecture Decision:
  - EC2: attach instance profile — never place IAM access keys in user data, AMI, or application config.
  - ECS Fargate: define taskRoleArn in task definition — app code receives temporary credentials from 169.254.170.2.
  - Lambda: assign execution role with least-privilege permissions scoped to exact resource ARNs.
  - EKS: use IRSA or EKS Pod Identity to bind an IAM role to a Kubernetes service account.
  - On-premises: use IAM Roles Anywhere with X.509 certificates from AWS Private CA.
- Verification: aws iam generate-credential-report — check for IAM users with active access keys on compute resources. Security Hub control: IAM.4.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_identities_secrets.html, 2026-08-31

**Store All Credentials in Secrets Manager with Automatic Rotation** [HIGH CONFIDENCE]
- Pillar Alignment: SEC02-BP03, SecretsManager.1, SecretsManager.4
- Why: "Application/database passwords — Rotate: Store in AWS Secrets Manager with automated rotation." AWS Security Pillar Remove/Replace/Rotate strategy.
- AWS Services: AWS Secrets Manager, Lambda (rotation function), Amazon EventBridge
- Architecture Decision:
  - All DB credentials, API keys, OAuth tokens go to Secrets Manager — not Parameter Store, not environment variables, not code.
  - Enable automatic rotation: choose managed rotation (RDS) or Lambda-backed rotation (all others).
  - Compliance baseline: 90 days (SecretsManager.4). Use alternating-users strategy for production databases.
  - Rotation Lambda: deploy in the same VPC as the database + create a Secrets Manager VPC endpoint in that VPC.
- Verification: aws secretsmanager describe-secret --secret-id <arn> → RotationEnabled: true. Security Hub: SecretsManager.1, SecretsManager.2, SecretsManager.4.
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotating-secrets.html, 2026-08-31

**Enable CMK Automatic Rotation** [HIGH CONFIDENCE]
- Pillar Alignment: SEC08-BP01 (Implement secure key management), KMS.4
- Why: KMS key rotation mandated by CIS AWS Foundations Benchmark v5.0.0/3.6, PCI DSS v4.0.1/3.7.4, and NIST 800-53 r5 SC-12, SC-28(3).
- AWS Services: AWS KMS (customer managed keys)
- Architecture Decision:
  - Enable automatic rotation: aws kms enable-key-rotation --key-id <key-id>
  - Set RotationPeriodInDays to match compliance framework (default 365).
  - Key ID, ARN, alias unchanged after rotation — no application code changes required.
  - Use on-demand rotation for immediate unplanned rotation: aws kms rotate-key-on-demand --key-id <key-id>
  - Monitor: EventBridge rule matching KMS CMK Rotation event → SNS notification.
- Verification: aws kms get-key-rotation-status --key-id <key-id> → KeyRotationEnabled: true. Security Hub: KMS.4.
- Source: https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html, 2026-08-31

**Use ACM for All Public TLS Certificates with DNS Validation** [HIGH CONFIDENCE]
- Pillar Alignment: SEC09-BP01 (Implement secure key and certificate management), SEC09-BP02 (Enforce encryption in transit)
- Why: "Manual steps during certificate deployment or renewal processes" is a HIGH-risk anti-pattern per Well-Architected SEC09-BP01.
- AWS Services: AWS Certificate Manager (ACM), Amazon CloudFront, ALB, Amazon API Gateway
- Architecture Decision:
  - Request ACM public certificate for every internet-facing domain — no charge.
  - Always use DNS validation: one CNAME per domain; ACM auto-renews while CNAME remains.
  - CloudFront cert MUST be in us-east-1. ALB in another region: separate ACM cert in the ALBs region.
  - Never pin ACM certificates — managed renewal generates a new key pair.
  - Monitor: EventBridge ACM Certificate Approaching Expiration event + CloudWatch DaysToExpiry alarm.
- Verification: aws acm describe-certificate --certificate-arn <arn> → DomainValidationOptions[].ValidationStatus: SUCCESS. Security Hub: ACM.1.
- Source: https://docs.aws.amazon.com/acm/latest/userguide/acm-bestpractices.html, 2026-08-31

**Route Secrets Manager Calls Through VPC PrivateLink** [HIGH CONFIDENCE]
- Pillar Alignment: SEC09-BP02, SEC03-BP02
- Why: Private endpoints eliminate public internet traversal for secret retrieval.
- AWS Services: VPC Interface Endpoint (PrivateLink), AWS Secrets Manager, AWS KMS
- Architecture Decision:
  - Create interface endpoint com.amazonaws.<region>.secretsmanager in each application VPC.
  - Enable private DNS — standard hostname resolves to private endpoint with no code changes.
  - Also create com.amazonaws.<region>.kms endpoint if using CMK-encrypted secrets.
  - Enforce via Secrets Manager resource policy: aws:SourceVpce condition.
  - Rotation Lambda in same VPC as endpoint. Never use aws:SourceIp for Lambda rotation conditions.
- Verification: aws ec2 describe-vpc-endpoints --filters Name=service-name,Values=com.amazonaws.<region>.secretsmanager
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/vpc-endpoint-overview.html, 2026-08-31

**Scope KMS Key Policies to Specific Principals** [HIGH CONFIDENCE]
- Pillar Alignment: SEC08-BP01, KMS.1, KMS.2, KMS.5
- Why: "Overly broad permissions to access key material" is a HIGH-risk anti-pattern per SEC08-BP01. KMS.5 classifies publicly accessible KMS keys as CRITICAL severity.
- AWS Services: AWS KMS, IAM
- Architecture Decision:
  - Key policy: never "Principal": "*". Specify exact IAM role/user ARNs or account root ARN.
  - IAM Resource: always the key ARN — never "*", alias name, or alias ARN.
  - Only CreateKey, GenerateRandom, ListAliases, ListKeys legitimately require Resource: *
  - Cross-account: key policy in Account A grants Account B principal AND Account B IAM policy grants the key ARN.
  - Add kms:ViaService: secretsmanager.<region>.amazonaws.com to restrict CMK to Secrets Manager requests.
- Verification: aws kms get-key-policy --key-id <key-id> --policy-name default — review Principal elements. Security Hub: KMS.1, KMS.2, KMS.5.
- Source: https://docs.aws.amazon.com/kms/latest/developerguide/iam-policies-best-practices.html, 2026-08-31

**Enforce Encryption at Rest with Separate CMKs per Data Classification** [HIGH CONFIDENCE]
- Pillar Alignment: SEC08-BP02 (Enforce encryption at rest)
- Why: "Using the same encryption key for all data regardless of classification" — explicit SEC08-BP02 anti-pattern.
- AWS Services: AWS KMS (CMK), Amazon S3, Amazon RDS, Amazon EBS, Amazon EFS, AWS Secrets Manager
- Architecture Decision:
  - One CMK per sensitivity level or service boundary (prod-secrets CMK, prod-rds CMK, staging CMK — separate keys).
  - Enable default encryption: S3 (all new objects by default); EBS (account-level default encryption); EFS (default encryption).
  - Monitor: AWS Config rules encrypted-volumes, rds-storage-encrypted, s3-default-encryption-kms.
- Verification: aws config get-compliance-details-by-config-rule --config-rule-name encrypted-volumes. Security Hub: EC2.3, RDS.3.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_protect_data_rest_encrypt.html, 2026-08-31

**Enforce TLS 1.2 Minimum on All Endpoints** [HIGH CONFIDENCE]
- Pillar Alignment: SEC09-BP02 (Enforce encryption in transit)
- Why: AWS deprecated TLS 1.0 and TLS 1.1 for AWS API endpoints as of February 2024.
- AWS Services: Amazon CloudFront, ALB, Amazon API Gateway, Amazon S3
- Architecture Decision:
  - CloudFront: security policy TLSv1.2_2021 or TLSv1.2_2019 minimum. Prefer TLSv1.2_2021 (includes TLS 1.3).
  - ALB: HTTPS listener with ELBSecurityPolicy-TLS13-1-2-2021-06.
  - S3: bucket policy condition "aws:SecureTransport": "true" to deny HTTP-only requests.
  - HTTP to HTTPS redirect: CloudFront viewer protocol policy or ALB redirect rule.
- Verification: aws cloudfront get-distribution --id <id> → ViewerCertificate.MinimumProtocolVersion. Config rule: alb-https-required.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_protect_data_transit_encrypt.html, 2026-08-31

**Log All KMS and Secrets Manager Activity to CloudTrail** [HIGH CONFIDENCE]
- Pillar Alignment: SEC02-BP05, SEC08-BP01
- Why: "Monitor Secrets Manager activity via CloudTrail for unexpected access or deletion attempts" — SEC02-BP03. "Pay special attention to monitoring key destruction events" — SEC08-BP01.
- AWS Services: AWS CloudTrail, Amazon CloudWatch Logs, Amazon EventBridge, Amazon GuardDuty
- Architecture Decision:
  - CloudTrail trail MUST include kms.amazonaws.com management events — never add to ExcludeManagementEventSources.
  - CloudWatch Logs Insights queries for KMS Decrypt by unexpected principals.
  - EventBridge rule on ScheduleKeyDeletion KMS event → SNS alert.
  - Enable GuardDuty for anomalous Secrets Manager access patterns.
- Verification: aws cloudtrail get-event-selectors --trail-name <name> — confirm kms.amazonaws.com is NOT in ExcludeManagementEventSources.
- Source: https://docs.aws.amazon.com/kms/latest/developerguide/logging-using-cloudtrail.html, 2026-08-31

**Use Parameter Store for Static Config; Secrets Manager for Credentials** [HIGH CONFIDENCE]
- Pillar Alignment: SEC02-BP03
- Why: Official AWS documentation states: "If you manage credentials such as usernames, passwords, or any other secrets, we recommend using AWS Secrets Manager." Parameter Store has no rotation capability.
- AWS Services: AWS Secrets Manager, AWS Systems Manager Parameter Store
- Architecture Decision:
  - Parameter Store: AMI IDs, endpoint URLs, feature flags, environment names — non-rotating, cost-sensitive.
  - Secrets Manager: DB passwords, API keys, OAuth tokens — anything requiring rotation, cross-account sharing, or fine-grained audit.
- Verification: Audit Parameter Store SecureString parameters for credential patterns and migrate to Secrets Manager.
- Source: https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html, 2026-08-31

---

### Architectural Decisions

**KMS Key Type Selection** [HIGH CONFIDENCE]

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| AWS owned key | AWS-managed (invisible) | Zero management overhead; free | No audit trail in your CloudTrail; no key policy control | Default encryption with no compliance requirement |
| AWS managed key (aws/service) | Customer-visible; service-managed | No monthly cost; auditable in CloudTrail | No key policy changes; no cross-account | Single-account workloads with standard compliance |
| Customer managed key (CMK) | AWS KMS | Full control: key policies, grants, custom rotation, cross-account | $1/month/key; operational overhead | Cross-account access, compliance mandates, fine-grained audit |

- Cost Profile: AWS owned = $0; AWS managed = $0 storage; CMK = $1.00/month/key + $0.03/10K symmetric API calls
- Lock-in Assessment: KMS is AWS-specific. Keys cannot be exported in plaintext.
- Architect Instruction: "Ask whether this secret or data store needs to be shared across AWS accounts or requires a custom key policy — if yes, CMK is required."
- Source: https://docs.aws.amazon.com/kms/latest/developerguide/concepts.html, 2026-08-31

**Secrets Manager Rotation Strategy** [HIGH CONFIDENCE]

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| Managed rotation | Secrets Manager (RDS integration) | Zero Lambda management | Limited to RDS/supported services | RDS managed secrets |
| Single-user Lambda rotation | Secrets Manager + Lambda | Simplicity; works for all secret types | Brief rotation-window auth-denial risk | Batch jobs, dev/staging, low-traffic |
| Alternating-users Lambda rotation | Secrets Manager + Lambda + superuser secret | Zero auth denial during rotation | Requires superuser secret; manual permission sync | Production databases; HA applications |

- Cost Profile: Lambda invocation costs per rotation. Alternating-users: +$0.40/month for superuser secret.
- Architect Instruction: "Ask whether the application can tolerate a brief credential rejection during rotation — if no, use alternating-users strategy."
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotation-strategy.html, 2026-08-31

**Secret Retrieval Pattern (Compute Layer)** [HIGH CONFIDENCE]

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| ECS secret injection (env var) | Secrets Manager + ECS | Zero application code | Secret static at task start; rotation needs force-new-deploy | Simple apps; infrequently rotating secrets |
| Lambda Parameters and Secrets Extension | Secrets Manager + Lambda extension | Runtime-agnostic caching (TTL 300s default) | Slightly higher cold-start | Lambda functions (all runtimes) |
| Language-specific caching SDK | Secrets Manager SDK | Fine-grained TTL control; in-process cache | Application code dependency | Long-running services needing live refresh |
| Workload Credentials Provider sidecar | Secrets Manager (Rust agent) | HTTP API at localhost; role chaining; post-quantum | Not encrypted in local cache | ECS/EKS sidecar pattern |

- Cost Profile: Extension/sidecar reduces API call cost by caching (300s TTL vs per-request).
- Architect Instruction: "Ask whether the secret must refresh without a container restart — if yes, use SDK-based retrieval with caching; if no, ECS injection is acceptable."
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/secrets-manager-agent.html, 2026-08-31

**ACM Certificate Scope: Wildcard vs SAN** [HIGH CONFIDENCE]

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| Wildcard (*.example.com) | ACM | One cert for all subdomains at one level; one DNS CNAME | Does not cover apex or nested subdomains | Many ephemeral subdomains; test environments |
| SAN cert (multiple FQDNs) | ACM | Covers exact domains including apex and different hosts | One CNAME per FQDN; cannot add domains later without new cert | Known stable set of domains; apex + www + api |

- Cost Profile: Both free for ACM-managed certs with integrated services.
- Architect Instruction: "Ask whether test environments use dynamically generated subdomain names — if yes, use a wildcard cert."
- Source: https://docs.aws.amazon.com/acm/latest/userguide/acm-concepts.html, 2026-08-31

**Public ACM Certificate vs Private CA** [HIGH CONFIDENCE]

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| ACM public cert | ACM (Amazon Trust Services) | Free; browser-trusted; automated renewal | Cannot be exported; no mTLS client certs | Internet-facing HTTPS (CloudFront, ALB, API GW) |
| Private CA general-purpose | AWS Private CA ($400/month) | Full PKI control; exportable; mTLS; IAM Roles Anywhere | High fixed cost; no browser trust by default | Internal mTLS; Kubernetes pods; on-premises IAM creds |
| Private CA short-lived | AWS Private CA ($50/month) | Lower cost for high-volume short-lived certs | Short validity requires automated renewal pipeline | Short-lived cert workloads; frequent rotation |

- Cost Profile: Public = free. Private CA General = $400/month + $0.75/cert. Private CA Short-lived = $50/month + $0.058/cert.
- Architect Instruction: "Ask whether the certificate is for a public internet-facing endpoint or for internal/mTLS — public endpoints use ACM public certs; internal/mTLS requires Private CA."
- Source: https://aws.amazon.com/private-ca/pricing/, 2026-08-31

**Multi-Region Secrets Architecture** [MEDIUM CONFIDENCE]

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| Single-region; cross-region SDK calls | Secrets Manager (primary only) | Simplicity; no replication cost | Latency for non-primary region; primary dependency | Primary-region workloads with occasional cross-region reads |
| Multi-region replication | Secrets Manager + replication | Local read latency; regional resilience | +$0.40/secret/month per replica region; own KMS key per replica | Active-active multi-region; DR with fast RPO |
| Centralized secrets account | Secrets Manager + cross-account IAM | Central governance; single audit trail | Cross-account complexity; CMK required | Large orgs; shared platform; compliance central governance |

- Architect Instruction: "Ask whether each region requires sub-second secret retrieval or must operate independently during a primary-region outage — if yes, use replication."
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/create-manage-multi-region-secrets.html, 2026-08-31

---

### Anti-Patterns

**Hardcoded Credentials in Source Code** [HIGH CONFIDENCE]
- Risk Level: CRITICAL
- Why: Violates SEC02-BP03. "Storing long-term credentials in source code or configuration files" — explicit Well-Architected anti-pattern. Credentials in code reach version control, build artifacts, and container images.
- Wrong: db_password = "mypassword123" hardcoded in application code.
- Correct: Retrieve at runtime via secretsmanager.get_secret_value(SecretId='prod/myapp/db-credentials') or use the Lambda Parameters and Secrets Extension with caching.
- Detection: Amazon CodeGuru Reviewer / Amazon Q Developer security scan; git-secrets pre-commit hook.
- Impact: Data breach; unauthorized database access; PCI DSS 8.6.3 compliance violation.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_identities_secrets.html, 2026-08-31

**Plaintext Secrets in ECS/Lambda Environment Variables** [HIGH CONFIDENCE]
- Risk Level: HIGH
- Why: Environment variables visible in AWS console, CloudFormation templates, task definition APIs, and process inspection inside container.
- Wrong: { "name": "DB_PASSWORD", "value": "mysecretvalue" } in ECS task definition environment array.
- Correct: { "name": "DB_PASSWORD", "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:prod/db-password-abc123" } in ECS task definition secrets array.
- Detection: aws ecs describe-task-definition --task-definition <name> — inspect containerDefinitions[].environment for credential patterns.
- Impact: Credential exposure in console/deployment logs; compliance violation.
- Source: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/secrets-envvar-secrets-manager.html, 2026-08-31

**No Secret Rotation** [HIGH CONFIDENCE]
- Risk Level: HIGH
- Why: SecretsManager.1 and SecretsManager.4 are Security Hub controls mapped to PCI DSS v4.0.1/8.6.3. No rotation means an undetected credential compromise extends indefinitely.
- Wrong: Secrets Manager secret prod/db-password created 18 months ago; RotationEnabled: false.
- Correct: aws secretsmanager rotate-secret --secret-id prod/db-password --rotation-lambda-arn <arn> --rotation-rules AutomaticallyAfterDays=30
- Detection: aws secretsmanager describe-secret → RotationEnabled: false or LastRotatedDate older than 90 days. Security Hub: SecretsManager.1, SecretsManager.4.
- Impact: Extended breach window; PCI DSS 8.6.3 audit failure.
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html, 2026-08-31

**Self-Signed Certificates for Public Resources** [HIGH CONFIDENCE]
- Risk Level: HIGH (Well-Architected Security Pillar explicit classification)
- Why: SEC09-BP01 anti-pattern: "using self-signed certificates for public resources." Browser warnings; no CRL/OCSP revocation path; no automated renewal.
- Wrong: OpenSSL-generated self-signed cert deployed on an ALB HTTPS listener for api.example.com.
- Correct: Request free ACM public certificate for api.example.com with DNS validation; associate with ALB HTTPS listener.
- Detection: aws elbv2 describe-listeners → inspect Certificates[].CertificateArn in ACM console for imported self-signed certs.
- Impact: Browser security warnings; PCI DSS 4.2.1 violation.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_protect_data_transit_key_cert_mgmt.html, 2026-08-31

**CloudFront Certificate Not in us-east-1** [HIGH CONFIDENCE]
- Risk Level: HIGH
- Why: ACM certificate for CloudFront MUST be in us-east-1. Certificate in any other region cannot be associated with CloudFront distributions.
- Wrong: ACM certificate for example.com requested in eu-west-1, then attempted attachment to CloudFront distribution.
- Correct: aws acm request-certificate --domain-name example.com --validation-method DNS --region us-east-1
- Detection: CloudFront distribution creation fails with InvalidViewerCertificate.
- Impact: CloudFront distribution creation failure; application deployment blocker.
- Source: https://docs.aws.amazon.com/acm/latest/userguide/acm-services.html, 2026-08-31

**Wildcard Principal in KMS Key Policy** [HIGH CONFIDENCE]
- Risk Level: CRITICAL
- Why: "Principal": "*" allows any identity including anonymous to use the KMS key. SEC08-BP01 anti-pattern: "overly broad permissions to access key material."
- Wrong: { "Principal": "*", "Action": "kms:*", "Effect": "Allow", "Resource": "*" } in key policy.
- Correct: Specify exact IAM role/user ARNs or account root ARN as Principal. Combine with IAM policies on specific roles for non-administrator operations.
- Detection: aws kms get-key-policy --key-id <key-id> --policy-name default → check Principal element. Security Hub: KMS.5.
- Impact: Data breach; unauthorized decryption of all data encrypted under the key.
- Source: https://docs.aws.amazon.com/kms/latest/developerguide/iam-policies-best-practices.html, 2026-08-31

**"Resource": "*" in IAM Policy for KMS Cryptographic Operations** [HIGH CONFIDENCE]
- Risk Level: HIGH
- Why: Grants access to ALL KMS keys in ALL accounts where the principals account has been granted cross-account access.
- Wrong: { "Effect": "Allow", "Action": ["kms:Decrypt", "kms:GenerateDataKey"], "Resource": "*" }
- Correct: Specify exact key ARN in Resource element. Only CreateKey, GenerateRandom, ListAliases, ListKeys legitimately require Resource: *
- Detection: Review IAM policies for "Resource": "*" with kms:Decrypt or kms:GenerateDataKey. Security Hub: KMS.1 (managed policy), KMS.2 (inline policy).
- Impact: Unintended cross-account decryption; privilege escalation.
- Source: https://docs.aws.amazon.com/kms/latest/developerguide/iam-policies-best-practices.html, 2026-08-31

**aws:SourceIp in Secrets Manager Resource Policy for Lambda Rotation** [HIGH CONFIDENCE]
- Risk Level: HIGH
- Why: Lambda rotation functions invoke Secrets Manager from AWS-internal address space — not from corporate IP ranges or VPC CIDRs. An aws:SourceIp condition blocks all rotation Lambda calls.
- Wrong: Condition with IpAddress: { aws:SourceIp: ["203.0.113.0/24"] } in Secrets Manager resource policy.
- Correct: Condition with StringEquals: { aws:SourceVpce: "vpce-0a12b34c56d78901a" }
- Detection: If rotation fails, inspect rotation Lambda CloudWatch Logs and Secrets Manager resource policy for SourceIp conditions.
- Impact: Secret rotation failure; credentials never updated.
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html, 2026-08-31

**Parameter Store SecureString for Rotating Credentials** [HIGH CONFIDENCE]
- Risk Level: HIGH
- Why: Parameter Store has no rotation capability. AWS explicitly recommends Secrets Manager for all credentials.
- Wrong: /myapp/prod/db-password as SecureString with no rotation mechanism.
- Correct: Migrate to Secrets Manager with managed RDS rotation or Lambda-backed rotation function.
- Detection: aws ssm describe-parameters --filters Key=Type,Values=SecureString — cross-reference with known credential naming patterns.
- Impact: Credential exposure; compliance violation; audit failure.
- Source: https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html, 2026-08-31

**Certificate Pinning Against an ACM-Managed Certificate** [HIGH CONFIDENCE]
- Risk Level: HIGH
- Why: ACM managed renewal generates a new public-private key pair. Applications pinning the certificate or public key will fail to connect after renewal.
- Wrong: Mobile application pinning the base64-encoded public key of an ACM-issued certificate.
- Correct: Pin to the Amazon Root CA certificate (stable; does not change on leaf cert renewal).
- Detection: Review application SSL context initialization for certificate pinning patterns.
- Impact: Application connection failure post-renewal; customer-facing outage.
- Source: https://docs.aws.amazon.com/acm/latest/userguide/acm-bestpractices.html, 2026-08-31

**Excluding KMS from CloudTrail** [HIGH CONFIDENCE]
- Risk Level: HIGH
- Why: Excluding kms.amazonaws.com from CloudTrail hides all key usage and management events.
- Wrong: CloudTrail event selector with ExcludeManagementEventSources: ["kms.amazonaws.com"].
- Correct: Never exclude KMS from CloudTrail.
- Detection: aws cloudtrail get-event-selectors --trail-name <name> — verify kms.amazonaws.com is NOT in ExcludeManagementEventSources.
- Impact: Blind spot for key compromise; regulatory audit failure.
- Source: https://docs.aws.amazon.com/kms/latest/developerguide/logging-using-cloudtrail.html, 2026-08-31

**Single AWS Account for All Private CA Hierarchy Levels** [HIGH CONFIDENCE]
- Risk Level: HIGH (Well-Architected SEC09-BP01 classification)
- Why: SEC09-BP01 anti-pattern: "paying insufficient attention to CA hierarchy design." Single account means root CA compromise exposes the entire hierarchy.
- Wrong: Root CA, intermediate CAs, and end-entity certificate issuance all in the same AWS account.
- Correct: Account 1: Root CA only — issues intermediate CA certificates, then suspended/offline. Account 2+: Intermediate CAs — issue end-entity certs for workloads.
- Detection: aws acm-pca list-certificate-authorities — if root and subordinate CAs in same account, this is the anti-pattern.
- Impact: Root CA compromise → entire PKI hierarchy untrusted; all certificates must be reissued.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_protect_data_transit_key_cert_mgmt.html, 2026-08-31

**Parameter Store Policy Overwrite (Silent Deletion of Existing Policies)** [HIGH CONFIDENCE]
- Risk Level: MEDIUM
- Why: Adding a new parameter policy via --policies OVERWRITES ALL existing policies silently.
- Wrong: aws ssm put-parameter --name /myapp/param --policies '[{"Type":"NoChangeNotification",...}]' when parameter already has Expiration + ExpirationNotification policies — silently deletes both.
- Correct: Always include all desired policies in a single --policies call.
- Detection: aws ssm get-parameters --names /myapp/param — inspect Policies field after any update.
- Impact: Parameters silently fail to expire or notify; compliance drift.
- Source: https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-policies.html, 2026-08-31

---

## Cloud-Native Design Patterns

**Envelope Encryption for Application Data**
- Category: Data
- Problem: Encrypting large volumes of data directly with KMS is slow (API latency per call), expensive (API call fees), and limited (KMS max direct encryption payload: 4 KB).
- Solution on AWS:
  1. Call kms:GenerateDataKey on a CMK — receive plaintext data key + encrypted data key.
  2. Encrypt data locally (AES-256-GCM) using the plaintext data key via AWS Encryption SDK.
  3. Store encrypted data alongside the encrypted data key; discard plaintext key from memory immediately.
  4. Decrypt: kms:Decrypt on the encrypted data key → recover plaintext data key → decrypt data locally.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Performance | Local encryption after one KMS call; no per-record KMS API latency | One KMS call per encryption operation |
  | Cost | KMS API fees only on data key operations | CMK cost $1/month + $0.03/10K symmetric API calls |
  | Key rotation | CMK rotation does not require re-encrypting existing data keys | Re-encrypting data keys requires application-level operation |
  | Auditability | Every GenerateDataKey/Decrypt logged in CloudTrail with encryption context | High CloudTrail volume at scale |

- Source: https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html, 2026-08-31

**Secret Rotation with Zero Downtime (Alternating-Users)**
- Category: Resilience
- Problem: Rotating a database credential causes a brief window where the database has the new password but the application holds the old one, causing auth failures in high-availability applications.
- Solution on AWS:
  - Provision two database users (original + clone) with identical permissions.
  - Configure Secrets Manager alternating-users rotation with a superuser secret.
  - Rotation Lambda alternates: each rotation updates the non-current users password; AWSCURRENT label switches to freshly-rotated user.
  - Both users credentials valid at all times — no auth denial window.
  - Applications retry on auth failure (exponential backoff + jitter) as defense-in-depth.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Availability | Zero auth denial during rotation | Requires superuser secret; two IAM grants on database |
  | Complexity | AWS-provided templates for RDS MySQL, PostgreSQL, Oracle, SQL Server, MariaDB, DocumentDB, Redshift | Manual permission sync if original users permissions change post-clone |
  | Cost | Same Lambda rotation invocation cost as single-user | Additional superuser secret: +$0.40/month |

- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotation-strategy.html, 2026-08-31

**Certificate Lifecycle Automation (ACM + EventBridge)**
- Category: Resilience
- Problem: Expired TLS certificates cause immediate, customer-visible outages. Manual expiry tracking is error-prone at scale.
- Solution on AWS:
  1. Request ACM-managed certificates with DNS validation — automated renewal with no human action.
  2. EventBridge rule on ACM Certificate Approaching Expiration (source: aws.acm) → SNS notification.
  3. CloudWatch alarm on AWS/CertificateManager DaysToExpiry metric (threshold: 45 days) → SNS.
  4. For imported certs: EventBridge rule → Lambda calls acm:ImportCertificate with renewed cert.
  5. Verify renewal via ACM Certificate Available EventBridge event.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Operational burden | Zero for ACM-managed with DNS validation | DNS CNAME must remain in place perpetually |
  | Visibility | Multi-channel alerting at 45/30/7/1 days before expiry | EventBridge and CloudWatch alarm costs (minimal) |
  | Imported certs | Same alerting applies; Lambda reimport automates renewal | Lambda development effort; private key management remains customer responsibility |

- Source: https://docs.aws.amazon.com/acm/latest/userguide/supported-events.html, 2026-08-31

**Private Connectivity for Secrets (PrivateLink + VPC Endpoint)**
- Category: Data
- Problem: Secrets Manager API calls from private subnets traverse the public internet by default (via NAT Gateway), exposing API traffic to network interception.
- Solution on AWS:
  1. Create interface VPC endpoint com.amazonaws.<region>.secretsmanager in the application VPC.
  2. Enable private DNS — standard hostname resolves to private endpoint with no code changes.
  3. Attach custom endpoint policy: restrict to secretsmanager:GetSecretValue and secretsmanager:DescribeSecret on specific secret ARNs.
  4. Secrets Manager resource policy with aws:SourceVpce condition — denies requests not from the endpoint.
  5. Rotation Lambda in same VPC — calls Secrets Manager via same endpoint.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Security | Traffic never leaves AWS private network; endpoint policy adds access control | ~$0.01/hour/AZ + $0.01/GB processed |
  | Cost | Eliminates NAT Gateway data processing cost for Secrets Manager traffic | Interface endpoint hourly cost in each AZ |
  | Complexity | Private DNS transparent — no code changes | Each VPC and region needs its own endpoint |

- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/vpc-endpoint-overview.html, 2026-08-31

---

## Security Architecture

**Identity and Access Management for Secrets** [HIGH CONFIDENCE]
- AWS Services: IAM Roles, ECS Task IAM Role, Lambda Execution Role, EKS IRSA, Secrets Manager resource policy, KMS key policy, IAM Roles Anywhere
- Architecture: Application compute uses IAM roles (never long-term IAM user credentials). Each application role has a least-privilege policy scoped to the exact secret ARN. Secrets Manager resource policy provides defense-in-depth (aws:SourceVpce condition). KMS key policy restricts kms:Decrypt to the application role with kms:ViaService condition.
  Compute (ECS Task) → IAM Task Role → secretsmanager:GetSecretValue (secret ARN) → kms:Decrypt (CMK ARN + kms:ViaService) → Secrets Manager VPC Endpoint → Secrets Manager → KMS → returns decrypted secret value
- Compliance Alignment: NIST 800-53 r5 AC-2, AC-3, AC-6; PCI DSS v4.0.1/8.6.3, 8.3.9. Security Hub: SecretsManager.1, SecretsManager.4, KMS.1, KMS.2.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_identities_secrets.html, 2026-08-31

**Encryption at Rest (Data Layer)** [HIGH CONFIDENCE]
- AWS Services: AWS KMS (CMK), AWS Secrets Manager, Amazon RDS, Amazon S3, Amazon EBS, SSM Parameter Store (SecureString)
- Architecture: Every data store uses envelope encryption: unique per-record data key encrypted under a CMK. CMKs scoped per environment and data classification. Automatic rotation enabled on all CMKs. S3 default encryption with CMK + S3 Bucket Keys to reduce KMS API call volume. AWS Config continuously evaluates encryption compliance.
- Compliance Alignment: NIST 800-53 r5 SC-28, SC-12, SC-28(3); PCI DSS v4.0.1/3.7.4 (key rotation). Security Hub: KMS.3, KMS.4, KMS.5.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_protect_data_rest_key_mgmt.html, 2026-08-31

**Encryption in Transit (Network Layer)** [HIGH CONFIDENCE]
- AWS Services: ACM (TLS certificates), CloudFront, ALB, API Gateway, AWS PrivateLink
- Architecture: All internet-facing traffic terminates TLS at CloudFront (ACM cert us-east-1, TLSv1.2_2021 policy) or ALB (ACM cert regional, ELBSecurityPolicy-TLS13-1-2-2021-06). S3 bucket policy enforces aws:SecureTransport: true. Internal service communication uses VPC PrivateLink. CloudFront HTTP to HTTPS redirect enabled.
- Compliance Alignment: NIST 800-53 r5 SC-28(3), SC-7(16); PCI DSS v4.0.1/4.2.1. Security Hub: ACM.1, ACM.2.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_protect_data_transit_encrypt.html, 2026-08-31

**Detective Controls and Compliance Monitoring** [HIGH CONFIDENCE]
- AWS Services: AWS CloudTrail, Amazon CloudWatch Logs, AWS Security Hub, Amazon GuardDuty, AWS Config, Amazon EventBridge
- Architecture: CloudTrail (multi-region, log file integrity validation) → CloudWatch Logs → Logs Insights queries for anomalous KMS/Secrets Manager access patterns. Security Hub aggregates CSPM findings across accounts. GuardDuty monitors for anomalous credential access. AWS Config rules with multi-account aggregator.

  Security Hub Control Reference:

  | Domain | Control | Severity | Compliance |
  |--------|---------|----------|------------|
  | KMS — no wildcard Decrypt (managed policy) | KMS.1 | Medium | NIST AC-3, AC-6 |
  | KMS — no wildcard Decrypt (inline policy) | KMS.2 | Medium | NIST AC-3, AC-6 |
  | KMS — not pending deletion | KMS.3 | Critical | NIST SC-12 |
  | KMS — rotation enabled | KMS.4 | Medium | CIS 3.6; PCI DSS 3.7.4; NIST SC-12, SC-28(3) |
  | KMS — not publicly accessible | KMS.5 | Critical | CSPM |
  | SM — rotation enabled | SecretsManager.1 | Medium | NIST AC-2(1), AC-3(15); PCI DSS 8.6.3, 8.3.9 |
  | SM — rotation succeeds | SecretsManager.2 | Medium | NIST AC-2(1); PCI DSS 8.6.3 |
  | SM — unused secrets removed within 90 days | SecretsManager.3 | Medium | NIST AC-2(1) |
  | SM — rotated within 90 days | SecretsManager.4 | Medium | NIST AC-2(1); PCI DSS 8.6.3, 8.3.9 |
  | ACM — renewal within 30 days of expiry | ACM.1 | Medium | NIST SC-28(3), SC-7(16); PCI DSS 4.2.1 |
  | ACM — RSA key 2048 bits or greater | ACM.2 | High | PCI DSS 4.2.1 |

- Source: https://docs.aws.amazon.com/securityhub/latest/userguide/kms-controls.html, 2026-08-31

---

## Operational Patterns

**Automated TLS Certificate Renewal (ACM-Issued)**
- RTO/RPO: Zero downtime — ARN unchanged on renewal; new cert deployed automatically to associated services
- AWS Services: ACM, Amazon EventBridge, Amazon CloudWatch, Amazon SNS
- Cost Profile: Low — ACM managed certs are free; CloudWatch alarm cost negligible
- Automation:
  - Fully automated: DNS CNAME must remain in place; ACM renews automatically starting 60 days before expiry.
  - Monitor: EventBridge rule on ACM Certificate Approaching Expiration (30 days default for public, 45 for private/imported; configurable via PutAccountConfiguration) → SNS.
  - CloudWatch alarm: AWS/CertificateManager DaysToExpiry < 30 → SNS.
  - Email-validated certs: ACM sends renewal emails at 45, 30, 7, 1 day before expiry — manual action required. Migrate to DNS validation to eliminate.
  - Manual decision: Review and update certificate if domain names change.
- Source: https://docs.aws.amazon.com/acm/latest/userguide/supported-events.html, 2026-08-31

**Secret Rotation Execution and Propagation**
- RTO/RPO: Near-zero for alternating-users; seconds for single-user (brief auth failure window mitigated by retry logic)
- AWS Services: Secrets Manager, Lambda (rotation function), Amazon ECS, EventBridge
- Cost Profile: Medium — Lambda invocation costs per rotation; ECS force-new-deploy triggers task replacement
- Automation:
  - Rotation Lambda invoked by Secrets Manager on schedule (cron/rate expression).
  - After rotation: EventBridge native event Secret Label Updated (AWSCURRENT moved) triggers downstream automation.
  - ECS env var injection (static at task start): EventBridge rule → ECS force-new-deployment API call → containers restart.
  - SDK-based retrieval with caching (Lambda extension TTL 300s): cache expires automatically; no container restart needed.
  - Manual decision: Rotation failure (SecretsManager.2) — investigate Lambda CloudWatch Logs, database connectivity, or permissions.
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/monitoring-eventbridge.html, 2026-08-31

**Regional Failover with Replicated Secrets**
- RTO/RPO: RTO fast (promote-to-standalone is an API call); RPO near-synchronous [UNVERIFIED: no official numeric RTO/RPO SLA from AWS documentation]
- AWS Services: Secrets Manager (multi-region replication), AWS KMS (per-region CMK), Amazon Route 53
- Cost Profile: High — additional $0.40/secret/month per replica region + per-region KMS costs
- Automation:
  - Rotation from primary propagates automatically to all replicas — no per-replica rotation Lambda needed.
  - Failover: promote replica to standalone: aws secretsmanager stop-replication-to-replica --secret-id <arn-in-replica-region>
  - Manual decision: After promoting, reconfigure rotation Lambda in the failover region.
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/create-manage-multi-region-secrets.html, 2026-08-31

**Compliance Drift Detection and Remediation**
- RTO/RPO: N/A — continuous monitoring; remediation triggered on policy violation detection
- AWS Services: AWS Config, AWS Security Hub, Amazon EventBridge, AWS Lambda (auto-remediation), Amazon SNS
- Cost Profile: Low — Config rule evaluation + Lambda remediation invocation costs
- Automation:
  - AWS Config rules continuously evaluate: cmk-backing-key-rotation-enabled (KMS.4), secretsmanager-rotation-enabled-check (SecretsManager.1), acm-certificate-expiration-check (ACM.1, 30-day threshold), encrypted-volumes (EBS).
  - Non-compliant finding → EventBridge → Lambda auto-remediation for safe idempotent remediations.
  - Security Hub aggregates findings across accounts via Config multi-account aggregator.
  - Manual decision: Rotation failure (SecretsManager.2) — requires root cause analysis before re-enabling.
- Source: https://docs.aws.amazon.com/securityhub/latest/userguide/secretsmanager-controls.html, 2026-08-31

---

## Reference Architectures

**Standard Web Application — Secrets and Certificate Management Stack**
- Context: Public-facing web application (CloudFront → ALB → ECS Fargate → RDS Aurora)
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Edge certificate | ACM (us-east-1) | Public TLS cert for CloudFront; DNS-validated; auto-renewed; free |
  | CDN | Amazon CloudFront | TLS termination (TLSv1.2_2021 policy); HTTP to HTTPS redirect |
  | Load balancer certificate | ACM (app region) | Regional TLS cert for ALB HTTPS listener; separate from CloudFront cert |
  | Load balancer | Application Load Balancer (ALB) | TLS termination toward ECS; WAF integration |
  | App-code identity | IAM Task Role (ECS) | Grants secretsmanager:GetSecretValue on exact secret ARNs + kms:Decrypt on CMK |
  | ECS infra identity | IAM Task Execution Role | Grants ECS control plane permission to inject secrets at container start |
  | Compute | ECS Fargate | Application containers; task isolation per container |
  | Secrets store | AWS Secrets Manager | Aurora DB credentials; API keys; alternating-users rotation; CMK-encrypted |
  | Config store | SSM Parameter Store | Feature flags; endpoint URLs; non-rotating config |
  | Secrets encryption | AWS KMS CMK (prod-secrets) | Auto-rotation enabled; kms:ViaService condition; $1/month |
  | DB encryption | AWS KMS CMK (prod-rds) | Separate from secrets CMK; auto-rotation enabled |
  | Private connectivity | VPC Interface Endpoint (PrivateLink) | Secrets Manager + KMS endpoints; private DNS enabled |
  | Rotation engine | Lambda (RDS PostgreSQL alternating-users template) | Deployed in app VPC; calls SM via VPC endpoint |
  | Certificate monitoring | EventBridge + CloudWatch | ACM Certificate Approaching Expiration rule; DaysToExpiry alarm (30 days) |
  | Audit | AWS CloudTrail (multi-region, log integrity) | All KMS and Secrets Manager API calls |
  | Threat detection | Amazon GuardDuty | Anomalous Secrets Manager access detection |
  | Compliance | AWS Security Hub + AWS Config | KMS.1-5, SecretsManager.1-4, ACM.1-2; multi-account aggregator |

- Key Decisions:
  1. CloudFront cert in us-east-1; ALB cert in app region — two separate ACM certificate requests required.
  2. ECS Fargate: task isolation per container; ECS_AWSVPC_BLOCK_IMDS=true not needed on Fargate (needed on EC2 launch type).
  3. Rotation Lambda in app VPC + Secrets Manager VPC endpoint in app VPC — rotation traffic never leaves AWS network.
  4. Alternating-users rotation for Aurora — zero auth denial during rotation window.
  5. CMK per tier (secrets vs RDS) — different key policies, different rotation periods.
  6. ECS secret injection static at task start — force-new-deployment required after rotation. For live refresh: use SDK + Lambda extension caching.
- Scaling Path:
  - Single-region: one secret per credential pair, one CMK per tier, one VPC endpoint per VPC.
  - Multi-AZ: Secrets Manager and KMS are multi-AZ by default — no additional configuration.
  - Multi-region active-active: SM replication to secondary region with region-specific KMS key; CloudFront geographic routing.
  - Multi-account org: centralized secrets account + cross-account resource policies + VPC PrivateLink + Config Aggregator.
- Source: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html, 2026-08-31

**Multi-Region Disaster Recovery — Secrets Architecture**
- Context: Active-primary/passive-secondary regional architecture; RPO near-zero; RTO minutes
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Primary secrets | Secrets Manager (us-east-1) | Primary secrets; rotation executed here; replication source |
  | Replica secrets | Secrets Manager (us-west-2) | Read-local in secondary region; rotation propagated from primary |
  | Primary CMK | AWS KMS CMK (us-east-1) | Encrypts primary secrets; auto-rotation enabled |
  | Replica CMK | AWS KMS CMK (us-west-2) | Encrypts replica secrets independently; auto-rotation enabled |
  | VPC endpoint (primary) | PrivateLink (us-east-1) | App VPC to Secrets Manager private network |
  | VPC endpoint (secondary) | PrivateLink (us-west-2) | DR app VPC to Secrets Manager private network |
  | Rotation Lambda | Lambda (us-east-1) | Runs in primary region; rotation propagates automatically to replicas |
  | Health checks | Amazon Route 53 | Monitors primary region health; triggers failover routing |
  | Failover automation | EventBridge + Lambda | Promotes replica to standalone on DR trigger |
  | Audit | CloudTrail (both regions) | Separate trails per region; replication events logged in both |

- Key Decisions:
  1. Each replica uses its own regional KMS key — encrypted independently in each region.
  2. Rotation from primary propagates to all replicas automatically — no per-replica rotation Lambda needed.
  3. Failover: aws secretsmanager stop-replication-to-replica promotes secondary to standalone.
  4. After recovery: re-establish replication from the original primary or treat promoted secret as new primary.
  5. GovCloud and China regions are isolated — cannot replicate across commercial/GovCloud/China boundaries.
  6. April 2026: Secrets Manager console supports cross-account CMK ARN input directly.
- Scaling Path: Add regions by calling ReplicateSecretToRegions with the new region + regional CMK ARN.
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/create-manage-multi-region-secrets.html, 2026-08-31

---

## Provider Differentiators

**KMS Automatic Key Rotation without Key ID Change**
AWS KMS automatic rotation replaces the cryptographic key material on a configurable schedule while the key ID, ARN, and alias remain unchanged. Applications require zero code changes for key rotation. All previous backing key versions retained for decryption. Custom RotationPeriodInDays is supported beyond the previous 365-day default.
[Source: https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html, 2026-08-31]

**Secrets Manager Managed Rotation (Zero Lambda for RDS)**
For Amazon RDS managed secrets, Secrets Manager handles rotation entirely without a Lambda function — deeply integrated with RDS, including password synchronization and validation.
[Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotating-secrets.html, 2026-08-31]

**Post-Quantum Key Exchange in Workload Credentials Provider**
The AWS Workload Credentials Provider (formerly Secrets Manager Agent) uses post-quantum ML-KEM (Kyber) key exchange by default for the in-memory secret cache transport, providing forward secrecy against future quantum computer attacks.
[Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/secrets-manager-agent.html, 2026-08-31]

**Certificate Transparency Compliance (Mandatory)**
ACM automatically submits all public certificates to public CT logs before issuance — required by browser policy and cannot be opted out of. Domain names in public certificate CNs/SANs will appear in publicly searchable CT logs permanently.
[Source: https://docs.aws.amazon.com/acm/latest/userguide/acm-concepts.html, 2026-08-31]

**Zelkova Policy Validation (Proactive)**
Secrets Manager uses the Zelkova automated reasoning engine to analyze resource policies for overly broad access at authoring time — before the policy is applied — rather than only at runtime access evaluation. Combined with BlockPublicPolicy=true, this prevents public-access misconfigurations before they reach production.
[Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/auth-and-access_resource-based-policies.html, 2026-08-31]

**KMS FIPS 140-3 Level 3 HSMs**
AWS KMS uses FIPS 140-3 Level 3 validated hardware security modules (HSMs) for all key operations. There is no mechanism to export KMS key material in plaintext — the private key for any CMK never leaves the HSM boundary.
[Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_protect_data_rest_key_mgmt.html, 2026-08-31]

---

## Scenario Coverage

**Standard Case: ECS Fargate Web App with RDS Aurora Credentials**
- Approach:
  1. Store Aurora credentials in Secrets Manager (CMK-encrypted); enable alternating-users Lambda rotation using the managed Aurora PostgreSQL template.
  2. ECS task definition secrets field: inject DB credentials at container start using the secret ARN.
  3. Task IAM role: secretsmanager:GetSecretValue on exact secret ARN + kms:Decrypt on CMK ARN with kms:ViaService condition.
  4. Create Secrets Manager + KMS VPC endpoints in the ECS VPC; rotation Lambda in same VPC.
  5. ACM public cert (us-east-1 for CloudFront, app-region for ALB); DNS validation.
  6. Security Hub enabled: KMS.4, SecretsManager.1, SecretsManager.4, ACM.1 as baseline controls.
- Key Decisions: Alternating-users vs single-user rotation; ECS env var injection (static, force-new-deploy on rotation) vs SDK-based runtime retrieval (live cache refresh with Lambda extension).

**Edge Case: Multi-Account Organization with Centralized Secrets**
- Approach: Dedicated secrets management account hosts all Secrets Manager secrets. Workload accounts retrieve via cross-account IAM roles + Secrets Manager resource policies. CMK required in secrets account (AWS managed key does not support cross-account decryption). VPC PrivateLink between workload account VPCs and secrets account endpoint. AWS Config Multi-Account Aggregator for cross-account compliance monitoring. As of April 2026, the Secrets Manager console accepts cross-account CMK ARN input directly.

**Edge Case: Short-Lived mTLS Certificates for Service Mesh**
- Approach: AWS Private CA (short-lived mode, $50/month) issues service identity certificates with validity of hours to days. Kubernetes pods use the ACM PCA controller or cert-manager with AWSPCA issuer. High certificate volume at short validity benefits from $0.058/cert short-lived pricing vs $0.75/cert general-purpose pricing. Each CA hierarchy level in a separate AWS account; root CA offline between issuance operations.

**Anti-Pattern Case: Developer Requests "Put the DB Password in an Environment Variable"**
- Clarification: Never store the actual credential value in an environment variable. Store only the Secrets Manager secret ARN as an environment variable and retrieve the credential at runtime.
  - If credential must update without a container restart: use SDK-based retrieval with the Lambda Parameters and Secrets Extension (TTL 300s cache) or language-specific caching library.
  - If restart is acceptable on rotation: use ECS task definition secrets field with valueFrom pointing to the secret ARN — a force-new-deployment picks up the post-rotation value.
  - Either way: the password value itself never appears in the task definition, CloudFormation template, or deployment pipeline.

---

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | KMS | AWS managed key annual rotation since May 2022 (changed from 3-year cycle) | Added — confirmed from official concepts page | https://docs.aws.amazon.com/kms/latest/developerguide/concepts.html (2026-08-31) |
| 2 | KMS | On-demand key rotation now supported for EXTERNAL-origin symmetric CMKs | Added — confirmed from rotate-keys.html | https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html (2026-08-31) |
| 3 | KMS | Resource * in IAM for kms:Decrypt grants access to external-account keys | Added — confirmed from iam-policies-best-practices.html | https://docs.aws.amazon.com/kms/latest/developerguide/iam-policies-best-practices.html (2026-08-31) |
| 4 | KMS | Alias ARN in IAM policy Resource element applies policy to alias, not underlying key | Added — confirmed from iam-policies-best-practices.html | https://docs.aws.amazon.com/kms/latest/developerguide/iam-policies-best-practices.html (2026-08-31) |
| 5 | Secrets Manager | kms:ViaService condition restricts CMK to Secrets Manager requests only | Added — confirmed from security-encryption.html | https://docs.aws.amazon.com/secretsmanager/latest/userguide/security-encryption.html (2026-08-31) |
| 6 | Secrets Manager | Workload Credentials Provider uses post-quantum ML-KEM key exchange by default | Added — confirmed from secrets-manager-agent.html | https://docs.aws.amazon.com/secretsmanager/latest/userguide/secrets-manager-agent.html (2026-08-31) |
| 7 | Secrets Manager | aws:SourceIp blocks Lambda rotation — use aws:SourceVpce instead | Added — confirmed from best-practices.html | https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html (2026-08-31) |
| 8 | Parameter Store | Advanced to Standard downgrade not supported; policy overwrite deletes all existing policies | Added — confirmed from parameter-store-policies.html | https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-policies.html (2026-08-31) |
| 9 | ACM | June 2025: ACM no longer issues certs with clientAuth EKU per browser requirements | Added — confirmed from acm-concepts.html | https://docs.aws.amazon.com/acm/latest/userguide/acm-concepts.html (2026-08-31) |
| 10 | ACM | ACME certs (CertificateKeyPairOrigin: ACME) cannot be used with CloudFront/ALB/API GW | Added — confirmed from acm-services.html | https://docs.aws.amazon.com/acm/latest/userguide/acm-services.html (2026-08-31) |
| 11 | ACM | EventBridge expiry defaults: 45 days (private/imported), 30 days (public); PutAccountConfiguration to change | Added — confirmed from supported-events.html | https://docs.aws.amazon.com/acm/latest/userguide/supported-events.html (2026-08-31) |
| 12 | WAF | TLS 1.0 and 1.1 deprecated for AWS API endpoints as of February 2024 | Added — confirmed from sec_protect_data_transit_encrypt.html | https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_protect_data_transit_encrypt.html (2026-08-31) |
| 13 | WAF | KMS.5 (key not publicly accessible) classified Critical severity; KMS.3 (not pending deletion) Critical | Added — confirmed from kms-controls.html | https://docs.aws.amazon.com/securityhub/latest/userguide/kms-controls.html (2026-08-31) |
| 14 | Ref Arch | ECS secret injection: secrets static at task start; rotation requires force-new-deployment | Added — confirmed from secrets-envvar-secrets-manager.html | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/secrets-envvar-secrets-manager.html (2026-08-31) |
| 15 | Ref Arch | ECS EC2 mode: ECS_AWSVPC_BLOCK_IMDS=true recommended to prevent cross-task IMDS access | Added — confirmed from task-iam-roles.html | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html (2026-08-31) |
| 16 | Ref Arch | SM replication: rotation from primary propagates automatically to all replicas | Added — confirmed from create-manage-multi-region-secrets.html | https://docs.aws.amazon.com/secretsmanager/latest/userguide/create-manage-multi-region-secrets.html (2026-08-31) |
| 17 | Ref Arch | April 2026: SM console supports cross-account CMK ARN input directly | Added — confirmed via AWS What's New feed | https://aws.amazon.com/about-aws/whats-new/ (2026-08-31) |
| 18 | KMS | RDS/EBS/Secrets Manager KMS service-specific integration pages returned minimal HTML | IRRESOLVABLE — services-rds.html, services-ebs.html, services-secrets-manager.html all returned minimal HTML. Standard KMS integration patterns consistent with Well-Architected guidance but not confirmed from individual service integration pages. | — |
| 19 | Secrets Manager | Rotation schedule minimum 4h / maximum 1000 days | IRRESOLVABLE — rotate-secrets-cli.html returned empty body content. Values from secondary source (CDK RotationScheduleOptions API reference) only; not verified from primary Secrets Manager CLI documentation page. | — |
| 20 | Secrets Manager | SM replication RTO/RPO SLAs | IRRESOLVABLE — No official AWS documentation publishes a specific numeric RTO or RPO SLA for Secrets Manager secret replication lag. Described as near-synchronous; no numeric SLA found. | — |
| 21 | Parameter Store | GetParametersByPath behavior with explicit deny on sub-path | IRRESOLVABLE — sysman-paramstore-access.html failed to render actual documentation content. Access inheritance behavior sourced from WebSearch summary only; marked as unverified for exact wording. | — |
| 22 | WAF | HIPAA and SOC 2 explicit control-to-Security Hub mapping | IRRESOLVABLE — Security Hub control metadata does not enumerate HIPAA-specific or SOC 2 Trust Service Criteria references in fetched documentation. Alignment exists via NIST 800-53 controls (AWS Artifact for exact mapping). | — |
