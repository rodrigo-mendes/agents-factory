# AWS Key Management Service (KMS) — Security Architecture Knowledge Base

---

## Metadata

```yaml
Full_Name: "AWS Security Architecture — AWS Key Management Service (KMS)"
Cloud_Provider: "AWS"
Architecture_Domain: "Security Architecture — Cryptographic Key Management & Data Encryption"
Target_Edition: "AWS KMS 2024–2025"
Architecture_Context: "Production workloads requiring encryption at rest and in transit, envelope encryption for application data, cross-account key sharing, multi-Region key replication, and integration with 100+ AWS services for server-side encryption"
Official_Source_URL: "https://docs.aws.amazon.com/kms/latest/developerguide/"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-05-28"
Currency_Threshold: "2027-05-28 — review required after this date due to service feature velocity"
```

---

## Executive Summary

AWS Key Management Service (AWS KMS) is a fully managed service that enables creation and control of cryptographic keys used to encrypt and sign data across AWS services and custom applications. KMS keys are protected by FIPS 140-3 Security Level 3 validated hardware security modules (HSMs) and never leave AWS KMS unencrypted. The service provides centralized key management, access control via key policies and IAM, full audit trail via CloudTrail, and seamless integration with 100+ AWS services for server-side encryption. KMS supports symmetric encryption keys (AES-256-GCM), asymmetric keys (RSA, ECC, ML-DSA for post-quantum cryptography), and HMAC keys for message authentication.

The 2024–2025 edition introduced **ML-DSA (Module-Lattice Digital Signature Algorithm) key support** — a NIST post-quantum cryptography standard for digital signatures. **On-demand key rotation** allows immediate key material rotation independent of automatic rotation schedules. **Custom rotation periods** enable configuring automatic rotation from 90 to 2560 days instead of the fixed 365-day default. **Resource Control Policies (RCPs)** in AWS Organizations can now enforce encryption requirements across member accounts. AWS managed keys were confirmed as a **legacy key type** no longer created for new AWS services since 2021 — new services default to AWS owned keys.

The three most critical architecture guardrails for KMS deployments are: (1) **use customer managed keys (CMKs) for all production workloads requiring auditability, cross-account sharing, or compliance evidence** — AWS owned keys provide no visibility or control; (2) **implement least-privilege key policies with explicit conditions** — every KMS key must have a key policy, and no principal has any permission unless explicitly allowed; (3) **enable automatic key rotation for all symmetric encryption CMKs** — rotation creates new key material while preserving the ability to decrypt previously encrypted data, with no application code changes required.

---

## Cloud Architecture Glossary

```
Term: KMS Key (formerly Customer Master Key / CMK)
Definition: A logical key resource in AWS KMS that represents a container for cryptographic key material. Identified by a key ARN and key ID. A KMS key contains one or more HSM backing keys (HBKs) representing current and rotated key material versions. KMS keys never leave AWS KMS unencrypted.
Provider Docs Section: https://docs.aws.amazon.com/kms/latest/developerguide/concepts.html
Architect Usage: A KMS key is the top-level resource for key management decisions — policies, rotation, access grants, and aliases attach to the KMS key. The underlying key material rotates independently without changing the key's logical identity.
Common Confusion: A KMS key is NOT the raw cryptographic material — it is the logical container. The term "CMK" (Customer Master Key) is deprecated; official documentation now uses "KMS key" exclusively.

Term: Customer Managed Key
Definition: A KMS key created, owned, and fully managed by the customer. Provides full control over key policies, IAM policies, grants, enable/disable state, rotation configuration, tags, aliases, and deletion scheduling. Incurs a monthly fee (pro-rated hourly) plus per-use fees.
Provider Docs Section: https://docs.aws.amazon.com/kms/latest/developerguide/concepts.html#customer-mgn-key
Architect Usage: Use customer managed keys for production workloads requiring: audit trail visibility, cross-account sharing, custom key policies, compliance evidence, or rotation control. The KeyManager field in DescribeKey response is "CUSTOMER".
Common Confusion: Customer managed keys are NOT automatically created — you must explicitly create them. They are NOT free — monthly fee applies per key plus API usage. Cross-account sharing requires explicit key policy grants.

Term: AWS Managed Key
Definition: A KMS key created and managed by an AWS service in your account. Identified by alias format "aws/<service-code>" (e.g., aws/ebs, aws/s3). Automatically rotated annually. Cannot be managed, rotated manually, shared cross-account, or deleted by the customer. Legacy key type — no longer created for new AWS services since 2021.
Provider Docs Section: https://docs.aws.amazon.com/kms/latest/developerguide/concepts.html#aws-managed-key
Architect Usage: AWS managed keys have NO monthly fee but incur per-use charges. They CANNOT be used for cross-account resource sharing. Resource Control Policies (RCPs) do NOT apply to AWS managed keys. Use customer managed keys instead when control or cross-account access is needed.
Common Confusion: AWS managed keys are NOT the same as AWS owned keys. AWS managed keys exist in YOUR account and produce CloudTrail logs. AWS owned keys exist in AWS's service account and provide NO visibility to customers.

Term: AWS Owned Key
Definition: A KMS key owned and managed by an AWS service in a service-managed account. Provides encryption-by-default with zero cost and zero operational burden. Cannot be viewed, audited, rotated, or managed by the customer. Used by new AWS services since 2021 as the default encryption mechanism.
Provider Docs Section: https://docs.aws.amazon.com/kms/latest/developerguide/concepts.html#aws-owned-key
Architect Usage: AWS owned keys are appropriate when convenience is paramount and you do NOT need audit trails, cross-account sharing, or compliance evidence for the encryption key. They enable frictionless cross-account and cross-region data sharing.
Common Confusion: You CANNOT view CloudTrail events for AWS owned keys. If compliance requires demonstrating key management controls, you MUST use customer managed keys instead.

Term: Envelope Encryption
Definition: The pattern where AWS KMS generates a data key (GenerateDataKey API), returns both plaintext and encrypted copies, the application encrypts data with the plaintext data key locally, stores the encrypted data key alongside the ciphertext, and discards the plaintext data key. Decryption reverses the process: AWS KMS decrypts the data key, then the application decrypts the data locally.
Provider Docs Section: https://docs.aws.amazon.com/kms/latest/developerguide/concepts.html#enveloping
Architect Usage: Envelope encryption is the FUNDAMENTAL pattern for all AWS service integrations with KMS. It minimizes KMS API calls (reducing cost and latency), enables encryption of data larger than 4 KB, and keeps bulk data off the network to KMS.
Common Confusion: The KMS key does NOT directly encrypt your data in most scenarios — it encrypts the data key. GenerateDataKey is the most common KMS API call in integrated services. The encrypted data key is typically stored as metadata alongside the ciphertext.

Term: Data Key
Definition: A symmetric encryption key (typically 256-bit AES) generated by AWS KMS via GenerateDataKey or GenerateDataKeyWithoutPlaintext APIs. Used outside of AWS KMS to encrypt application data. AWS KMS does NOT store, manage, or track data keys after generation — lifecycle and usage are entirely application-controlled.
Provider Docs Section: https://docs.aws.amazon.com/kms/latest/developerguide/concepts.html#data-keys
Architect Usage: Data keys should be used once or a limited number of times to avoid key exhaustion. Request a new data key for each encryption operation when feasible. The encrypted data key must be stored alongside the ciphertext for later decryption.
Common Confusion: AWS KMS does NOT retain data keys. If you lose the encrypted data key, you CANNOT recover it from KMS. The data key is generated ON the HSM and returned via TLS — it is never stored in KMS.

Term: Key Policy
Definition: A resource-based policy (JSON document) attached to a KMS key that defines who can use and manage the key. Every KMS key MUST have exactly one key policy. Unlike IAM policies, key policies are Regional and apply only to the KMS key they are attached to. No principal has ANY permission to a KMS key unless explicitly allowed in a key policy, IAM policy, or grant.
Provider Docs Section: https://docs.aws.amazon.com/kms/latest/developerguide/key-policies.html
Architect Usage: The key policy is the PRIMARY access control mechanism for KMS keys. The default key policy enables IAM policies to grant permissions — without this statement, IAM policies have NO effect on the key. Always include the root account statement to prevent key lockout.
Common Confusion: Key policies are NOT the same as IAM policies. An IAM policy alone CANNOT grant access to a KMS key unless the key policy explicitly enables IAM policy evaluation. A key policy with no root account access creates an UNMANAGEABLE key.

Term: Grant
Definition: A policy instrument that allows AWS principals to use a KMS key for specific operations without modifying the key policy or IAM policy. Grants are commonly used by AWS services to use customer managed keys on behalf of the user. Grants can be revoked or retired without modifying policies.
Provider Docs Section: https://docs.aws.amazon.com/kms/latest/developerguide/grants.html
Architect Usage: AWS services (EBS, RDS, S3) create grants to access your customer managed keys. Grants support constraints (encryption context) and are eventually consistent — use CreateGrant token for immediate use. Grants persist until explicitly revoked.
Common Confusion: Grants are NOT part of the key policy document. They are separate authorization mechanisms with their own lifecycle. Grants allow temporary, scoped access without the risk of policy document size limits.

Term: Encryption Context
Definition: A set of non-secret key-value pairs included in cryptographic operations (Encrypt, Decrypt, GenerateDataKey) that provides additional authenticated data (AAD). The same encryption context used during encryption MUST be provided during decryption. Logged in CloudTrail for every API call.
Provider Docs Section: https://docs.aws.amazon.com/kms/latest/developerguide/concepts.html#encrypt_context
Architect Usage: ALWAYS use encryption context for defense-in-depth. Include contextual identifiers (tenant ID, resource ARN, environment) to bind ciphertext to its intended context. Use kms:EncryptionContext condition keys in policies to enforce context requirements.
Common Confusion: Encryption context is NOT encrypted — it is stored in plaintext alongside the ciphertext. It provides integrity protection and policy enforcement, NOT confidentiality. It is AAD in AES-GCM, not additional plaintext to encrypt.

Term: HSM Backing Key (HBK)
Definition: The actual cryptographic key material (256-bit symmetric or RSA/ECC private key) stored within the AWS KMS HSM fleet. One or more HBKs comprise a KMS key — the active HBK encrypts new data, while older HBKs (from rotation) decrypt previously encrypted data. HBKs never leave HSMs in plaintext.
Provider Docs Section: https://docs.aws.amazon.com/kms/latest/developerguide/concepts.html#key-hierarchy
Architect Usage: Key rotation creates a NEW HBK within the same KMS key. The key ID/ARN remains the same. AWS KMS automatically selects the correct HBK for decryption based on ciphertext metadata. No application code changes are required after rotation.
Common Confusion: Key rotation does NOT re-encrypt existing data. Old ciphertext remains encrypted under the old HBK. Key rotation only affects NEW encrypt operations. To re-encrypt existing data under new key material, you must explicitly re-encrypt each ciphertext.

Term: Multi-Region Key
Definition: A set of interoperable KMS keys in different AWS Regions that share the same key material (key ID prefix: mrk-). Consists of one primary key and one or more replica keys. Multi-Region keys allow encrypting in one Region and decrypting in another without cross-Region API calls.
Provider Docs Section: https://docs.aws.amazon.com/kms/latest/developerguide/multi-region-keys-overview.html
Architect Usage: Use multi-Region keys for disaster recovery, global applications, and cross-Region data replication scenarios. Rotation is a shared property — rotating the primary propagates to all replicas. Multi-Region keys have higher monthly cost than single-Region keys.
Common Confusion: Multi-Region keys are NOT the same as replicating data keys. They share actual KMS key material across Regions. They are NOT automatically created — you must explicitly replicate them. Primary key must be rotated first.

Term: Key Store
Definition: The secure storage backend for KMS key material. AWS KMS supports: (1) Standard key store — AWS-managed HSM fleet (default, FIPS 140-3 Level 3); (2) AWS CloudHSM key store — key material in customer-owned CloudHSM cluster; (3) External key store (XKS) — key material in customer-managed external key manager outside AWS.
Provider Docs Section: https://docs.aws.amazon.com/kms/latest/developerguide/key-store-overview.html
Architect Usage: Use the standard key store for 99% of workloads. CloudHSM key store only when regulations mandate single-tenant HSMs. External key store only when regulations mandate key material never enters AWS — accepting significant latency and availability trade-offs.
Common Confusion: All key store types provide FIPS 140-3 Level 3 validation. The standard key store is NOT less secure — it is multi-tenant at the hardware level but provides single-tenant logical isolation. CloudHSM/XKS adds operational complexity without improving cryptographic security.

Term: Symmetric Encryption KMS Key
Definition: The default and most common KMS key type. Uses a single 256-bit AES-GCM key for both encryption and decryption. All key material stays within AWS KMS HSMs. All AWS service integrations require symmetric encryption keys. Supports automatic and on-demand key rotation.
Provider Docs Section: https://docs.aws.amazon.com/kms/latest/developerguide/concepts.html#symmetric-cmks
Architect Usage: Use symmetric encryption keys for ALL AWS service integrations (S3, EBS, RDS, etc.) and for envelope encryption patterns. Only choose asymmetric keys when external parties need to encrypt/verify without calling AWS KMS.
Common Confusion: You CANNOT download or export the symmetric key material from a standard key store. If you need to perform cryptographic operations outside AWS without calling KMS, use asymmetric keys or data keys.

Term: Asymmetric KMS Key
Definition: A KMS key containing a mathematically related public/private key pair (RSA, ECC, ML-DSA, or SM2). The private key never leaves AWS KMS unencrypted. The public key can be downloaded for use outside AWS KMS. Supports encryption/decryption OR signing/verification (not both for the same key).
Provider Docs Section: https://docs.aws.amazon.com/kms/latest/developerguide/symmetric-asymmetric.html
Architect Usage: Use asymmetric keys when external systems need to encrypt data or verify signatures without AWS credentials or KMS API access. NOT supported by AWS service integrations (S3, EBS, etc.) — these require symmetric keys. Manual rotation only.
Common Confusion: Asymmetric KMS keys do NOT support automatic or on-demand key rotation. You must rotate them manually (create a new key and update aliases). AWS services that integrate with KMS do NOT support asymmetric keys for server-side encryption.
```

---

## Architecture Guardrails

### ✅ Mandatory Patterns

**Use Customer Managed Keys for Production Workloads**
- Pillar Alignment: Security — SEC08-BP01 Implement secure key management
- Why: Customer managed keys provide full auditability via CloudTrail, cross-account sharing capability, custom key policies, rotation control, and compliance evidence. AWS owned keys provide no visibility or management control.
- AWS Services: AWS KMS (CreateKey, PutKeyPolicy), AWS CloudTrail, AWS IAM
- Architecture Decision:
  Create dedicated customer managed symmetric encryption keys per workload domain (e.g., `alias/prod/payments/encryption`, `alias/prod/user-data/encryption`). Implement key policies that restrict usage to specific IAM roles and conditions. Tag keys with cost allocation, ownership, and compliance metadata.
- Verification:
  ```bash
  aws kms list-keys --query 'Keys[].KeyId' --output text | xargs -I {} aws kms describe-key --key-id {} --query 'KeyMetadata.{KeyId:KeyId,KeyManager:KeyManager,KeyState:KeyState,Origin:Origin}'
  ```
  Verify all production resources use keys where KeyManager=CUSTOMER.
- Trade-offs: Monthly cost per key ($1/month) plus API usage fees ($0.03/10,000 requests). Operational responsibility for key lifecycle management.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/framework/sec_protect_data_rest_key_mgmt.html

---

**Enable Automatic Key Rotation**
- Pillar Alignment: Security — SEC08-BP01 Implement secure key management
- Why: Key rotation creates new cryptographic material, reducing the risk associated with prolonged key usage. Automatic rotation requires no application changes — AWS KMS transparently uses the correct key material for decryption based on ciphertext metadata.
- AWS Services: AWS KMS (EnableKeyRotation, GetKeyRotationStatus)
- Architecture Decision:
  Enable automatic key rotation on ALL symmetric encryption customer managed keys with AWS_KMS origin. Configure rotation period between 90–2560 days (default: 365 days). Use on-demand rotation for immediate rotation needs.
- Verification:
  ```bash
  aws kms list-keys --query 'Keys[].KeyId' --output text | xargs -I {} sh -c 'echo "Key: {}"; aws kms get-key-rotation-status --key-id {}'
  ```
  All keys should show `KeyRotationEnabled: true`.
- Trade-offs: KMS charges for first and second rotation of key material (capped at second rotation). Rotation does NOT re-encrypt existing data — old ciphertext remains protected by old key material.
- Source: https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html

---

**Implement Least-Privilege Key Policies**
- Pillar Alignment: Security — SEC08-BP01, SEC03-BP07 Analyze public and cross-account access
- Why: Every KMS key must have exactly one key policy. No principal has ANY permission to a KMS key unless explicitly granted. The default key policy enables IAM policies — without this, even account administrators cannot manage the key.
- AWS Services: AWS KMS (PutKeyPolicy, GetKeyPolicy), AWS IAM
- Architecture Decision:
  Key policies must: (1) Include root account access to prevent lockout; (2) Separate key administrators from key users; (3) Use condition keys (kms:ViaService, kms:CallerAccount, kms:EncryptionContext) to restrict usage context; (4) Grant only required operations (Encrypt, Decrypt, GenerateDataKey) — never use `kms:*`.
- Verification:
  ```bash
  aws kms get-key-policy --key-id <key-id> --policy-name default --output text | python3 -m json.tool
  ```
  Review for wildcard actions, missing conditions, and overly broad principal specifications.
- Trade-offs: Restrictive policies may block legitimate use cases if conditions are too narrow. Key policy changes are eventually consistent — test in non-production first.
- Source: https://docs.aws.amazon.com/kms/latest/developerguide/key-policies.html

---

**Use Encryption Context for All Operations**
- Pillar Alignment: Security — SEC08-BP02 Enforce encryption at rest
- Why: Encryption context provides additional authenticated data (AAD) in AES-GCM operations, binding ciphertext to its intended purpose. It is logged in CloudTrail, enabling fine-grained audit of which resource/tenant each operation was for. Policies can enforce encryption context via condition keys.
- AWS Services: AWS KMS (Encrypt, Decrypt, GenerateDataKey with EncryptionContext parameter), AWS CloudTrail
- Architecture Decision:
  Define a standard encryption context schema per workload: include tenant ID, resource type, and environment. Enforce via IAM policy conditions using `kms:EncryptionContext:<key>` condition key. Fail closed — deny operations without required context.
- Verification:
  Review CloudTrail events for KMS operations and confirm encryption context is present in requestParameters. Alert on operations lacking expected context keys.
- Trade-offs: Applications must track and provide encryption context for decryption. Context mismatch causes decryption failure (by design — this is the security benefit).
- Source: https://docs.aws.amazon.com/kms/latest/developerguide/concepts.html#encrypt_context

---

**Access KMS via VPC Endpoints in Private Subnets**
- Pillar Alignment: Security — SEC09-BP02 Enforce encryption in transit
- Why: Workloads in private subnets (Lambda in VPC, ECS tasks, EC2 instances) must reach KMS for encryption operations. VPC interface endpoints (AWS PrivateLink) keep traffic within the AWS network without requiring internet gateway, NAT gateway, or public IP.
- AWS Services: AWS KMS, Amazon VPC (Interface Endpoints), AWS PrivateLink
- Architecture Decision:
  Create VPC interface endpoint for `com.amazonaws.<region>.kms` in all VPC subnets that host workloads performing encryption operations. Enable private DNS. Restrict endpoint policy to required KMS actions only.
- Verification:
  ```bash
  aws ec2 describe-vpc-endpoints --filters "Name=service-name,Values=com.amazonaws.*.kms" --query 'VpcEndpoints[].{VpcId:VpcId,State:State,SubnetIds:SubnetIds}'
  ```
- Trade-offs: VPC endpoint hourly cost (~$0.01/hour per AZ) plus data processing charges ($0.01/GB). Required for private subnet workloads — without it, KMS calls fail or require expensive NAT gateway.
- Source: https://docs.aws.amazon.com/kms/latest/developerguide/kms-vpc-endpoint.html

---

**Audit All KMS Operations via CloudTrail**
- Pillar Alignment: Security — SEC04-BP01 Configure service and application logging
- Why: Every AWS KMS API call is logged to CloudTrail, including the key ARN, caller identity, encryption context, and result. This provides complete cryptographic operation audit trail for compliance (SOC2, PCI-DSS, HIPAA) and forensic analysis.
- AWS Services: AWS KMS, AWS CloudTrail, Amazon EventBridge, Amazon CloudWatch
- Architecture Decision:
  Ensure CloudTrail is enabled in all Regions with KMS data events captured. Create EventBridge rules for critical events: DeleteKey, DisableKey, ScheduleKeyDeletion, PutKeyPolicy. Set CloudWatch alarms for unusual KMS error rates or access from unexpected principals.
- Verification:
  ```bash
  aws cloudtrail get-event-selectors --trail-name <trail-name> --query 'EventSelectors[].DataResources'
  ```
  Confirm KMS events are captured. Query CloudTrail for `RotateKey` events to verify rotation is occurring.
- Trade-offs: High-volume KMS usage (millions of Encrypt/Decrypt calls) generates significant CloudTrail volume. Use event data stores with selective filtering for cost management.
- Source: https://docs.aws.amazon.com/kms/latest/developerguide/logging-using-cloudtrail.html

---

### ⚠️ Architectural Decisions

**Key Type Selection: Customer Managed vs AWS Managed vs AWS Owned**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Customer Managed Key | AWS KMS (CreateKey) | Full control, auditability, cross-account sharing, custom rotation, compliance evidence | Cost ($1/month + usage), operational responsibility | Compliance requirements, cross-account sharing, custom policies |
  | AWS Managed Key | AWS KMS (aws/<service>) | No monthly cost, automatic rotation, zero management | No cross-account sharing, no custom policies, no lifecycle control, legacy type | Legacy workloads already using them |
  | AWS Owned Key | AWS KMS (service-managed) | Zero cost, zero management, seamless cross-account sharing | No visibility, no audit trail, no control, cannot demonstrate compliance | Non-sensitive data, convenience-first workloads |

- Cost Profile: Customer managed: ~$1/month/key + $0.03/10K requests. AWS managed: $0/month + $0.03/10K requests. AWS owned: $0 total.
- Lock-in Assessment: All options are AWS-native. Customer managed keys support key material import (BYOK) for portability. External key stores (XKS) keep material outside AWS entirely.
- Architect Instruction: "Ask 'Does this workload require encryption key audit trails for compliance?' when selecting key type. If yes → Customer Managed Key."
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/aws-kms-best-practices/key-management.html

---

**Key Store Selection: Standard vs CloudHSM vs External (XKS)**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Standard Key Store | AWS KMS (default) | Availability, performance, cost, operational simplicity | Multi-tenant HSM hardware (single-tenant logical isolation) | 99% of workloads — default choice |
  | CloudHSM Key Store | AWS KMS + AWS CloudHSM | Single-tenant HSM, FIPS 140-3 Level 3 physical control | Cost ($1.50/hr/HSM), availability (min 2 HSMs), operational complexity | Regulatory mandate for single-tenant HSM |
  | External Key Store (XKS) | AWS KMS + External Key Manager | Key material never enters AWS, ultimate sovereignty | Latency (each operation requires external call), availability dependent on external manager, cost | Digital sovereignty laws requiring key material outside AWS |

- Cost Profile: Standard: $1/month/key. CloudHSM: $1.50/hour/HSM × 2 minimum = ~$2,190/month baseline. XKS: External manager licensing + $1/month/key + connectivity costs.
- Lock-in Assessment: Standard and CloudHSM key material cannot be exported. XKS maintains key material externally — maximum portability at maximum operational cost.
- Architect Instruction: "Ask 'Does regulation explicitly require single-tenant HSMs or key material outside AWS?' — if the answer is not definitively yes with citation, use Standard Key Store."
- Source: https://docs.aws.amazon.com/kms/latest/developerguide/key-store-overview.html

---

**Key Management Model: Centralized vs Decentralized**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Centralized (dedicated security account) | AWS KMS + AWS Organizations + cross-account grants | Unified governance, consistent policies, single audit point | Operational flexibility for application teams, cross-account policy complexity | Small number of keys, strong central security team, external customer access |
  | Decentralized (keys in workload accounts) | AWS KMS + IAM policies per account | Team autonomy, simpler policies, distributed quota usage | Consistency across accounts, potential policy drift, harder to audit holistically | Many workload accounts, strong IaC pipelines, application teams own security |

- Cost Profile: Both models have the same KMS pricing. Centralized may reduce total key count but increases cross-account API calls.
- Lock-in Assessment: Both models are internal organizational choices — no vendor lock-in difference.
- Architect Instruction: "Ask 'Does the organization have automated IaC pipelines for consistent cross-account key deployment?' — if no, centralized model reduces drift risk."
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/aws-kms-best-practices/key-management.html

---

**Symmetric vs Asymmetric KMS Keys**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Symmetric Encryption (AES-256-GCM) | AWS KMS symmetric key | AWS service integration, automatic rotation, envelope encryption, performance | Cannot share key material externally, both parties need KMS access | Server-side encryption, envelope encryption, ALL AWS service integrations |
  | Asymmetric RSA/ECC | AWS KMS asymmetric key | External parties can encrypt/verify without AWS credentials, public key downloadable | No AWS service integration for encryption, no automatic rotation, slower | External client encryption, code signing, certificate authorities |
  | Asymmetric ML-DSA (Post-Quantum) | AWS KMS ML-DSA key | Quantum-resistant digital signatures, future-proof | No encryption support (signing only), no automatic rotation, limited ecosystem | Long-lived signatures that must remain valid into post-quantum era |

- Cost Profile: Same pricing regardless of key type ($1/month + usage). Asymmetric operations are computationally more expensive but same API price.
- Lock-in Assessment: Symmetric keys are AWS-internal only. Asymmetric public keys are standard formats (PKIX DER/PEM) — portable for verification.
- Architect Instruction: "Ask 'Do external systems need to perform crypto operations without AWS credentials?' — if yes → asymmetric. Otherwise → symmetric."
- Source: https://docs.aws.amazon.com/kms/latest/developerguide/symmetric-asymmetric.html

---

### 🚫 Anti-Patterns

**Wildcard KMS Permissions in IAM Policies**
- Risk Level: CRITICAL
- Why: Granting `kms:*` on `Resource: *` violates SEC03-BP06 (least-privilege access). It allows any principal with this policy to create keys, modify key policies, schedule key deletion, decrypt any ciphertext, and disable rotation across ALL keys in the account.
- Instead: Grant specific actions (kms:Encrypt, kms:Decrypt, kms:GenerateDataKey) on specific key ARNs with condition keys (kms:ViaService, kms:EncryptionContext, kms:CallerAccount).
- Detection:
  ```bash
  aws iam list-policies --scope Local --query 'Policies[].Arn' | xargs -I {} aws iam get-policy-version --policy-arn {} --version-id $(aws iam get-policy --policy-arn {} --query 'Policy.DefaultVersionId' --output text) --query 'PolicyVersion.Document' | grep -l '"kms:\*"'
  ```
  Use IAM Access Analyzer to identify overly permissive KMS policies.
- Impact: Data breach — unauthorized decryption of sensitive data. Key deletion — permanent data loss. Privilege escalation via key policy modification.
- Source: https://docs.aws.amazon.com/kms/latest/developerguide/iam-policies-best-practices.html

---

**Using AWS Managed Keys for Cross-Account Resource Sharing**
- Risk Level: HIGH
- Why: AWS managed keys (aws/<service>) CANNOT be shared cross-account. Resources encrypted with AWS managed keys cannot be shared with other accounts (e.g., encrypted EBS snapshots, RDS snapshots, S3 objects). This creates a hard architectural constraint that blocks data sharing patterns.
- Instead: Use customer managed keys with cross-account key policy grants. Include the consuming account's principal in the key policy with required conditions.
- Detection: Attempt to share an encrypted resource cross-account — if using AWS managed key, the operation fails with AccessDeniedException on KMS decrypt.
- Impact: Architecture blocker — unable to implement cross-account data sharing, disaster recovery, or multi-account deployment patterns.
- Source: https://docs.aws.amazon.com/kms/latest/developerguide/concepts.html#aws-managed-key

---

**Missing Root Account Access in Key Policy**
- Risk Level: CRITICAL
- Why: If a key policy does not include the `"arn:aws:iam::<account-id>:root"` principal with `kms:*` permission, AND the key administrators/users are deleted from IAM, the key becomes permanently unmanageable. AWS Support CANNOT recover keys with inaccessible key policies.
- Instead: Always include the default key policy statement that enables the root account and allows IAM policies:
  ```json
  {
    "Sid": "Enable IAM policies",
    "Effect": "Allow",
    "Principal": {"AWS": "arn:aws:iam::<account-id>:root"},
    "Action": "kms:*",
    "Resource": "*"
  }
  ```
- Detection:
  ```bash
  aws kms get-key-policy --key-id <key-id> --policy-name default --output text | grep -c "arn:aws:iam::[0-9]*:root"
  ```
  Alert if the count is 0 for any customer managed key.
- Impact: Permanent data loss — encrypted data becomes permanently inaccessible if the key becomes unmanageable. AWS cannot intervene.
- Source: https://docs.aws.amazon.com/kms/latest/developerguide/key-policy-default.html#key-policy-default-allow-root-enable-iam

---

**Disabling Key Rotation on Customer Managed Keys**
- Risk Level: HIGH
- Why: Without rotation, a single set of key material is used indefinitely. While KMS keys (as wrapping keys) are at low exhaustion risk, many compliance frameworks (PCI-DSS, SOC2) mandate periodic key rotation. Disabled rotation fails compliance audits.
- Instead: Enable automatic key rotation with appropriate period (90–2560 days). Default 365 days meets most compliance requirements. Use on-demand rotation for incident response.
- Detection:
  ```bash
  aws kms list-keys --query 'Keys[].KeyId' --output text | xargs -I {} sh -c 'STATUS=$(aws kms get-key-rotation-status --key-id {} --query KeyRotationEnabled --output text); if [ "$STATUS" = "False" ]; then echo "ROTATION DISABLED: {}"; fi'
  ```
  AWS Config rule: `cmk-backing-key-rotation-enabled`.
- Impact: Compliance violation — audit findings. Increased risk window if key material is ever compromised.
- Source: https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html

---

**Deleting KMS Keys Without Impact Analysis**
- Risk Level: CRITICAL
- Why: KMS key deletion is IRREVERSIBLE after the waiting period (7–30 days). All data encrypted under the deleted key becomes PERMANENTLY inaccessible. AWS cannot recover deleted keys.
- Instead: (1) Disable the key first and monitor CloudTrail for decrypt attempts over 30+ days. (2) Set CloudWatch alarm on `Decrypt` calls using disabled keys. (3) Only schedule deletion after confirming zero usage. (4) Use maximum 30-day waiting period.
- Detection: AWS Config rule: monitor for `ScheduleKeyDeletion` API calls. EventBridge rule to alert on deletion scheduling.
- Impact: Permanent data loss — all data encrypted under the key is irrecoverable. No AWS support path for recovery.
- Source: https://docs.aws.amazon.com/kms/latest/developerguide/deleting-keys.html

---

**Hardcoding Key IDs Instead of Using Aliases**
- Risk Level: MEDIUM
- Why: Hardcoding key IDs (UUIDs) in application configuration or IaC templates creates tight coupling. Key rotation via new key creation (manual rotation), key replacement, or disaster recovery requires updating all references.
- Instead: Use KMS aliases (alias/prod/myapp/encryption) that can be repointed to different keys without application changes. Aliases are mutable references to immutable key resources.
- Detection: Search application code and IaC templates for UUID patterns in KMS key references. Prefer alias ARN or alias name patterns.
- Impact: Operational friction — key migration requires coordinated deployments. Increased blast radius for key-related incidents.
- Source: https://docs.aws.amazon.com/kms/latest/developerguide/kms-alias.html

---

**Ignoring KMS Request Quotas**
- Risk Level: HIGH
- Why: AWS KMS enforces per-account, per-Region request quotas (default: 5,500–30,000 requests/second depending on operation and Region). Exceeding quotas causes ThrottlingException, which breaks encryption/decryption for ALL workloads in the account sharing that Region.
- Instead: Implement client-side data key caching (AWS Encryption SDK caching CMM), use S3 Bucket Keys to reduce KMS calls by 99%, distribute workloads across accounts/Regions, and request quota increases proactively.
- Detection: CloudWatch metric `ThrottleCount` for KMS. Set alarms at 80% of quota threshold.
- Impact: Service outage — encryption/decryption operations fail across all workloads in the affected account and Region.
- Source: https://docs.aws.amazon.com/kms/latest/developerguide/requests-per-second.html

---

## Cloud-Native Design Patterns

**Envelope Encryption Pattern**
- Category: Data
- Problem: Encrypting large volumes of data directly with KMS is impractical due to 4 KB plaintext limit, API latency, cost per call, and throttling risk.
- Solution on AWS:
  1. Call `GenerateDataKey` with KMS key ARN → returns plaintext data key + encrypted data key
  2. Encrypt data locally using plaintext data key (AES-256-GCM)
  3. Store encrypted data key as metadata alongside ciphertext
  4. Discard plaintext data key from memory
  5. For decryption: call `Decrypt` with encrypted data key → get plaintext data key → decrypt data locally
- Services Used: AWS KMS (GenerateDataKey, Decrypt), application-side AES-256-GCM implementation (or AWS Encryption SDK)
- When to Apply: ALL data encryption scenarios — this is the default pattern for AWS service integrations (S3, EBS, RDS, DynamoDB, etc.)
- When NOT to Apply: Only when encrypting data < 4 KB that will be stored/transmitted entirely through KMS (rare — use direct Encrypt/Decrypt).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Performance | Bulk encryption at local speeds | Two KMS API calls per encrypt/decrypt cycle |
  | Cost | One KMS call per data key (not per byte) | Data key management responsibility |
  | Security | KMS key never touches bulk data | Application must securely handle plaintext data key in memory |

- Complements: Data Key Caching, S3 Bucket Keys
- Source: https://docs.aws.amazon.com/kms/latest/developerguide/concepts.html#enveloping

---

**Data Key Caching Pattern**
- Category: Scalability
- Problem: High-throughput workloads generating thousands of encrypt operations per second exhaust KMS request quotas and incur excessive cost/latency from GenerateDataKey calls.
- Solution on AWS:
  Use the AWS Encryption SDK with Caching Cryptographic Materials Manager (Caching CMM). Cache data keys locally with configurable: max age (time-based expiry), max bytes encrypted (byte threshold), max messages encrypted (usage count). Reuse cached data keys for multiple encrypt operations within bounds.
- Services Used: AWS Encryption SDK (Caching CMM), AWS KMS (GenerateDataKey — reduced call frequency)
- When to Apply: High-throughput encryption (>1000 encrypts/second), latency-sensitive paths, workloads approaching KMS request quotas.
- When NOT to Apply: Low-volume encryption, scenarios requiring unique data keys per encryption (highest security), data classification requiring per-record key isolation.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Throughput | Orders of magnitude fewer KMS calls | Shared data key across multiple encryptions |
  | Security | Still meets most compliance requirements | Larger blast radius if cached key is compromised |
  | Cost | Dramatically reduced KMS API costs | Cache management complexity |

- Complements: Envelope Encryption, S3 Bucket Keys
- Source: https://docs.aws.amazon.com/encryption-sdk/latest/developer-guide/data-caching-details.html

---

**S3 Bucket Keys Pattern**
- Category: Cost / Scalability
- Problem: Server-side encryption with KMS (SSE-KMS) on S3 generates one KMS GenerateDataKey call per object PUT. High-volume buckets (millions of objects/day) exhaust KMS quotas and incur significant KMS costs.
- Solution on AWS:
  Enable S3 Bucket Keys — S3 generates a short-lived bucket-level data key from KMS, then derives per-object keys locally. Reduces KMS requests by up to 99%.
- Services Used: Amazon S3 (Bucket Key configuration), AWS KMS (reduced GenerateDataKey calls)
- When to Apply: Any S3 bucket using SSE-KMS encryption with significant write volume. Should be enabled by default for new buckets.
- When NOT to Apply: Workloads requiring per-object KMS CloudTrail audit entries (Bucket Keys show the bucket ARN in CloudTrail, not individual object ARN).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Cost | Up to 99% reduction in KMS API costs | None for most workloads |
  | Audit | Normal bucket-level audit trail | Individual object encryption events not logged separately |
  | Performance | Reduced latency (fewer KMS round-trips) | None |

- Complements: Envelope Encryption, Data Key Caching
- Source: https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-key.html

---

**Cross-Account Encryption Pattern**
- Category: Data
- Problem: Multi-account architectures require sharing encrypted resources (EBS snapshots, RDS snapshots, S3 objects) across account boundaries while maintaining encryption.
- Solution on AWS:
  1. Create customer managed key in the source account
  2. Add cross-account principal to key policy with required operations (kms:Decrypt, kms:CreateGrant, kms:DescribeKey)
  3. In consuming account, create IAM policy allowing KMS operations on the source key ARN
  4. Share encrypted resource (snapshot, S3 object) via resource-level sharing mechanisms
  5. Consuming account decrypts using the source account's KMS key (or re-encrypts under local key)
- Services Used: AWS KMS (key policy, grants), AWS RAM (resource sharing), IAM (cross-account policies)
- When to Apply: Any multi-account architecture sharing encrypted resources — DR, dev/staging environments, data lake consumers, shared services.
- When NOT to Apply: Single-account deployments, data that can be re-encrypted before sharing.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Flexibility | Enables multi-account encrypted resource sharing | Cross-account key policy management complexity |
  | Security | Granular control over who decrypts shared data | Key policy in source account must trust external principals |
  | Operations | Single key for resource lifecycle | Key deletion in source breaks all consumers |

- Complements: Multi-Region Keys, Centralized Key Management
- Source: https://docs.aws.amazon.com/kms/latest/developerguide/key-policy-modifying-external-accounts.html

---

**Multi-Region Encryption for DR Pattern**
- Category: Resilience
- Problem: Disaster recovery requires decrypting data in a secondary Region, but standard KMS keys are Regional — you cannot use a key from Region A to decrypt in Region B.
- Solution on AWS:
  1. Create multi-Region primary key in primary Region (key ID prefix: mrk-)
  2. Replicate to DR Region(s) as replica keys
  3. Encrypt data in primary Region with the primary key
  4. Replicate encrypted data to DR Region (S3 replication, EBS snapshot copy, DynamoDB global tables)
  5. Decrypt in DR Region using the local replica key — same key material, no cross-Region KMS calls
- Services Used: AWS KMS (multi-Region keys), S3 CRR, DynamoDB Global Tables, EBS snapshot copy
- When to Apply: Active-passive DR, global applications, regulatory requirements for data locality with encryption.
- When NOT to Apply: Single-Region workloads, scenarios where re-encryption under a local key is acceptable during failover.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | RTO | Instant decryption in DR Region — no cross-Region API calls | Higher monthly key cost (per-Region charge for each replica) |
  | Complexity | Transparent to applications — same key ID works in both Regions | Rotation coordination (primary must be rotated first) |
  | Security | Same key material everywhere — interoperable ciphertext | Shared key material increases blast radius if compromised |

- Complements: Cross-Region Replication, Pilot Light DR, Warm Standby
- Source: https://docs.aws.amazon.com/kms/latest/developerguide/multi-region-keys-overview.html

---

## Security Architecture

**Identity & Access Management for KMS**
- AWS Services: AWS KMS (Key Policies, Grants), AWS IAM (Identity Policies), AWS Organizations (SCPs, RCPs)
- Architecture:
  Three mechanisms control KMS key access: (1) **Key Policies** — mandatory resource policy on every key, primary authorization mechanism; (2) **IAM Policies** — identity-based, only effective if key policy enables IAM evaluation; (3) **Grants** — delegated, scoped, temporary access for AWS services. Access requires explicit ALLOW in key policy OR (key policy enables IAM + IAM policy allows). SCPs can deny across organization. RCPs can enforce encryption requirements.
- Configuration Essentials:
  - Always include root account in key policy (lockout prevention)
  - Separate `kms:Create*`, `kms:Put*`, `kms:Enable*`, `kms:Disable*`, `kms:Schedule*` (administrators) from `kms:Encrypt`, `kms:Decrypt`, `kms:GenerateDataKey*` (users)
  - Use `kms:ViaService` condition to restrict key usage to specific AWS services
  - Use `kms:CallerAccount` condition for cross-account keys
  - Use `kms:EncryptionContext` conditions for tenant isolation
- Verification:
  ```bash
  aws kms get-key-policy --key-id <key-id> --policy-name default
  aws kms list-grants --key-id <key-id>
  aws accessanalyzer list-findings --analyzer-arn <arn> --filter '{"resourceType":{"eq":["AWS::KMS::Key"]}}'
  ```
- Compliance Alignment: SOC2 CC6.1 (logical access controls), PCI-DSS 3.5 (key management), HIPAA §164.312(a)(2)(iv) (encryption key management)
- Source: https://docs.aws.amazon.com/kms/latest/developerguide/control-access.html

---

**Data Protection — Encryption at Rest**
- AWS Services: AWS KMS, Amazon S3 (SSE-KMS), Amazon EBS (encryption), Amazon RDS (encryption), DynamoDB (encryption), EFS (encryption)
- Architecture:
  All AWS service integrations use symmetric encryption KMS keys via envelope encryption. The service calls `GenerateDataKey` to obtain a data key encrypted under the KMS key, encrypts the data locally, and stores the encrypted data key alongside the ciphertext. For decryption, the service calls `Decrypt` to unwrap the data key, then decrypts locally. The KMS key never directly touches customer data.
- Configuration Essentials:
  - S3: Enable default encryption with SSE-KMS and customer managed key + Bucket Keys
  - EBS: Enable default EBS encryption per Region with customer managed key
  - RDS: Enable encryption at instance creation (cannot enable after creation)
  - DynamoDB: Uses AWS owned key by default; specify customer managed key for audit requirements
- Verification:
  ```bash
  # S3
  aws s3api get-bucket-encryption --bucket <bucket>
  # EBS
  aws ec2 get-ebs-encryption-by-default
  aws ec2 get-ebs-default-kms-key-id
  # RDS
  aws rds describe-db-instances --query 'DBInstances[].{DBId:DBInstanceIdentifier,Encrypted:StorageEncrypted,KmsKeyId:KmsKeyId}'
  ```
- Compliance Alignment: SOC2 CC6.7 (encryption of data at rest), PCI-DSS 3.4 (render PAN unreadable), HIPAA §164.312(a)(2)(iv)
- Source: https://docs.aws.amazon.com/kms/latest/developerguide/service-integration.html

---

**Key Lifecycle Security — Deletion Protection**
- AWS Services: AWS KMS, AWS CloudTrail, Amazon EventBridge, Amazon CloudWatch
- Architecture:
  Implement defense-in-depth against accidental or malicious key deletion: (1) SCPs deny `kms:ScheduleKeyDeletion` except from breakglass role; (2) EventBridge rule triggers on ScheduleKeyDeletion events; (3) CloudWatch alarm on Decrypt failures for disabled/pending-deletion keys; (4) Mandatory 30-day waiting period (maximum allowed); (5) Multi-party approval for deletion via IAM role requiring MFA from multiple administrators.
- Configuration Essentials:
  - SCP: `{"Effect": "Deny", "Action": "kms:ScheduleKeyDeletion", "Resource": "*", "Condition": {"StringNotLike": {"aws:PrincipalArn": "arn:aws:iam::*:role/BreakGlassKeyDeletion"}}}`
  - EventBridge rule: `{"source": ["aws.kms"], "detail-type": ["AWS API Call via CloudTrail"], "detail": {"eventName": ["ScheduleKeyDeletion", "DisableKey"]}}`
  - Always disable keys before scheduling deletion; monitor for 30+ days
- Verification:
  Monitor CloudTrail for ScheduleKeyDeletion events. Review AWS Config compliance for `kms-cmk-not-scheduled-for-deletion` rule.
- Compliance Alignment: SOC2 CC6.5 (information disposal), PCI-DSS 3.6.5 (retirement of keys)
- Source: https://docs.aws.amazon.com/kms/latest/developerguide/deleting-keys.html

---

## Operational Patterns

**Key Rotation Operations**
- RTO/RPO: N/A (rotation is non-disruptive — no downtime)
- AWS Services: AWS KMS (EnableKeyRotation, RotateKeyOnDemand, GetKeyRotationStatus, ListKeyRotations), AWS CloudTrail, Amazon EventBridge
- Cost Profile: Low — charges for first and second rotated key material versions only (capped at second rotation). No per-rotation operation cost.
- Automation:
  - Enable automatic rotation via IaC (CloudFormation/Terraform) at key creation time
  - Use EventBridge to detect `KMS CMK Rotation` events for compliance reporting
  - On-demand rotation for incident response (compromised key material suspicion)
  - ListKeyRotations API for rotation history audit
- Runbook Skeleton:
  1. Detection: AWS Config rule `cmk-backing-key-rotation-enabled` alerts on non-compliant keys
  2. Triage: Identify key owner via tags, determine if rotation was intentionally disabled
  3. Resolution: Enable rotation or perform on-demand rotation if overdue
  4. Validation: `aws kms get-key-rotation-status --key-id <id>` confirms rotation enabled
  5. Post-mortem: Document why rotation was disabled, update automation to prevent recurrence
- Source: https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html

---

**KMS Throttling Response**
- RTO/RPO: Minutes (quota increase requests may take hours/days for approval)
- AWS Services: AWS KMS, Amazon CloudWatch (ThrottleCount metric), AWS Service Quotas
- Cost Profile: Low — mitigation involves caching (reduces KMS costs) or architecture changes
- Automation:
  - CloudWatch alarm on KMS ThrottleCount metric at 80% quota threshold
  - Implement exponential backoff with jitter in application code for KMS calls
  - AWS Encryption SDK Caching CMM for high-throughput workloads
  - S3 Bucket Keys to reduce per-object KMS calls by 99%
  - Request quota increase proactively before scaling events
- Runbook Skeleton:
  1. Detection: CloudWatch alarm fires on ThrottleCount > threshold
  2. Triage: Identify which KMS key(s) and which callers are generating highest request volume
  3. Resolution: Enable caching (short-term), request quota increase (medium-term), re-architect (long-term)
  4. Validation: ThrottleCount drops to zero, application error rates normalize
  5. Post-mortem: Capacity plan for next scaling event, implement caching at application layer
- Source: https://docs.aws.amazon.com/kms/latest/developerguide/requests-per-second.html

---

**Key Compromise Incident Response**
- RTO/RPO: Depends on scope — key disable is immediate, re-encryption depends on data volume
- AWS Services: AWS KMS (DisableKey, ScheduleKeyDeletion, CreateKey), AWS CloudTrail, Amazon EventBridge, AWS Security Hub
- Cost Profile: High during incident — requires re-encryption of all affected data under new key
- Automation:
  - Automated key disable via Lambda triggered by GuardDuty/Security Hub finding
  - Automated new key creation with identical policy
  - Data re-encryption pipeline (service-specific: S3 inventory + batch copy, EBS snapshot copy, RDS snapshot copy + restore)
- Runbook Skeleton:
  1. Detection: Anomalous Decrypt pattern detected (unusual principal, unusual encryption context, unusual volume)
  2. Triage: Confirm compromise vs legitimate use. Review CloudTrail for unauthorized access.
  3. Containment: Disable the compromised key immediately (`aws kms disable-key --key-id <id>`)
  4. Recovery: Create new key, re-encrypt affected data, update aliases to point to new key
  5. Eradication: Revoke compromised credentials, update key policy to remove unauthorized access
  6. Post-mortem: Root cause analysis, improve detection rules, implement additional conditions
- Source: https://docs.aws.amazon.com/kms/latest/developerguide/deleting-keys.html

---

**FinOps — KMS Cost Optimization**
- RTO/RPO: N/A
- AWS Services: AWS KMS, AWS Cost Explorer, S3 Bucket Keys, AWS Encryption SDK (Caching CMM)
- Cost Profile: KMS costs: $1/month/key (CMK) + $0.03/10,000 API requests. First and second rotated key materials add $1/month each (capped).
- Automation:
  - Tag all KMS keys with cost allocation tags (team, environment, application)
  - Use Cost Explorer filtered by `$REGION-KMS-Keys` usage type
  - Identify unused keys via CloudTrail (no Encrypt/Decrypt/GenerateDataKey in 90+ days) → disable → delete
  - Enable S3 Bucket Keys on all SSE-KMS buckets (99% reduction in KMS calls)
  - Implement Caching CMM for high-throughput workloads
  - Consider AWS owned keys for non-compliance-sensitive workloads (zero cost)
- Runbook Skeleton:
  1. Monthly: Review Cost Explorer for KMS spend anomalies
  2. Quarterly: Audit unused keys (no API calls in 90 days) — disable candidates
  3. Action: Enable Bucket Keys on high-volume S3 buckets
  4. Action: Implement caching for workloads exceeding 10,000 KMS calls/month
  5. Validate: Month-over-month KMS cost trend should be flat or declining relative to data growth
- Source: https://aws.amazon.com/kms/pricing/

---

## Reference Architectures

**Multi-Account Encryption with Centralized Key Management**
- Context: Enterprise with multiple workload accounts (dev, staging, production) requiring consistent encryption with centralized key governance
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Key Management | AWS KMS (Security account) | Central key creation, policy management, rotation |
  | Access Control | Key Policies + Cross-account grants | Allow workload accounts to use keys for encrypt/decrypt |
  | Governance | AWS Organizations SCPs | Prevent key deletion, enforce encryption |
  | Audit | AWS CloudTrail (Organization trail) | Centralized logging of all KMS operations |
  | Compliance | AWS Config (Organization rules) | Detect keys without rotation, unencrypted resources |
  | Cost | AWS Cost Explorer | Key usage attribution via tags |

- Key Decisions:
  - Keys live in security/shared-services account — workload accounts have usage permissions only
  - Separate keys per environment (dev/staging/prod) and per data classification
  - SCPs prevent workload accounts from creating their own keys (optional — depends on governance model)
  - Aliases follow naming convention: `alias/<env>/<app>/<purpose>`
- Scaling Path:
  Start with one key per data classification per environment. As teams grow, consider delegating key creation to workload accounts with guardrails (SCP + AWS Config). For global workloads, introduce multi-Region keys.
- Cost Baseline: ~$1/month per key × number of environments × number of data domains + API usage
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/aws-kms-best-practices/key-management.html

---

**Serverless Encryption Architecture**
- Context: Lambda-based application processing sensitive data with encryption at rest across S3, DynamoDB, and SQS
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Encryption Keys | AWS KMS (customer managed) | Single key per application for all service encryption |
  | Object Storage | Amazon S3 (SSE-KMS + Bucket Keys) | Encrypted object storage |
  | Database | Amazon DynamoDB (encryption with CMK) | Encrypted table data |
  | Messaging | Amazon SQS (SSE-KMS) | Encrypted messages in transit-at-rest |
  | Compute | AWS Lambda (execution role with KMS permissions) | Runtime decrypt/encrypt operations |
  | Secrets | AWS Secrets Manager (encrypted with same CMK) | Application credentials |

- Key Decisions:
  - Single CMK per application simplifies policy management but limits granular access control
  - Lambda execution role needs kms:Decrypt + kms:GenerateDataKey (not kms:Encrypt for most read-heavy workloads)
  - Use kms:ViaService condition to restrict key usage to specific services only
  - Lambda in VPC requires KMS VPC endpoint for private subnet deployments
- Scaling Path:
  High-throughput Lambda invocations may hit KMS quotas → implement data key caching via AWS Encryption SDK. For multi-tenant workloads, consider per-tenant keys for isolation.
- Cost Baseline: $1/month for the key + $0.03/10K Lambda invocations calling KMS
- Source: https://docs.aws.amazon.com/kms/latest/developerguide/service-integration.html

---

## Service Equivalence Map

| Capability | AWS | Google Cloud | Azure | Oracle Cloud (OCI) |
|------------|-----|-------------|-------|--------------------|
| **Key Management Service** | AWS KMS | Cloud KMS | Azure Key Vault | OCI Vault / Key Management |
| **HSM-backed Keys** | KMS Standard Key Store (FIPS 140-3 L3) | Cloud HSM | Key Vault (HSM tier) | OCI Vault (HSM-backed) |
| **Single-tenant HSM** | AWS CloudHSM | Cloud HSM Dedicated | Azure Dedicated HSM / Managed HSM | OCI Dedicated KMS |
| **External Key Manager** | External Key Store (XKS) | Cloud EKM | Azure Key Vault BYOK | OCI External Key Management |
| **Envelope Encryption SDK** | AWS Encryption SDK | Tink / Cloud KMS Client Libraries | Azure SDK encryption | OCI SDK encryption |
| **Key Rotation** | Automatic (90–2560 days) + On-demand | Automatic (configurable) | Automatic (configurable) | Automatic (configurable) |
| **Multi-Region Keys** | Multi-Region Keys (mrk-) | Global keys | N/A (replicate via Key Vault) | Cross-region vault replication |
| **Post-Quantum Crypto** | ML-DSA keys | N/A (preview) | N/A | N/A |
| **FIPS Validation** | FIPS 140-3 Level 3 | FIPS 140-2 Level 3 | FIPS 140-2 Level 2/3 | FIPS 140-2 Level 3 |

> **⚠️ Important**: Service equivalence does NOT mean feature parity. AWS KMS multi-Region keys, ML-DSA support, and External Key Store (XKS) have no direct equivalents in all providers. Always validate provider-specific capabilities against your requirements.

---

## Provider Differentiators

**Multi-Region Keys**
- Category: Data / Resilience
- Unique Value: KMS keys that share identical key material across multiple AWS Regions, enabling encrypt-in-one-Region and decrypt-in-another without cross-Region API calls. Key ID prefixed with `mrk-` for identification. Rotation synchronized across all replicas from the primary key.
- Architecture Impact: Eliminates the need for re-encryption during cross-Region data replication. Simplifies multi-Region DR architecture. Reduces decryption latency for global applications.
- When to Leverage: Global applications, multi-Region DR, cross-Region data replication (S3 CRR, DynamoDB Global Tables, Aurora Global Database).
- Caveat: Higher monthly cost per replica. Rotation must be initiated on primary key. Primary key deletion requires deleting all replicas first (7-day waiting per replica).
- Source: https://docs.aws.amazon.com/kms/latest/developerguide/multi-region-keys-overview.html

**ML-DSA (Post-Quantum) Keys**
- Category: Security
- Unique Value: First major cloud provider to offer NIST-standardized post-quantum digital signature algorithm (Module-Lattice Digital Signature Algorithm) in a managed key service. Protects against future quantum computing threats to digital signatures.
- Architecture Impact: Enables "crypto-agile" architecture — organizations can begin transitioning signing workloads to quantum-resistant algorithms today while maintaining backward compatibility.
- When to Leverage: Long-lived digital signatures (code signing, document signing, certificates) that must remain valid into the post-quantum era (10+ year signature validity requirements).
- Caveat: Signing only — no encryption support. Larger signature sizes than RSA/ECC. Limited ecosystem support (verifiers must support ML-DSA). No automatic rotation.
- Source: https://docs.aws.amazon.com/kms/latest/developerguide/symm-asymm-choose-key-spec.html#key-spec-mldsa

**External Key Store (XKS)**
- Category: Security / Sovereignty
- Unique Value: Allows KMS keys to use cryptographic key material stored in a customer-managed external key manager (on-premises or third-party cloud). Key material NEVER enters AWS infrastructure. Satisfies digital sovereignty requirements where key material must remain outside any cloud provider.
- Architecture Impact: Enables AWS service usage while maintaining absolute key material control. Introduces external dependency for every cryptographic operation — latency and availability depend on external manager.
- When to Leverage: Strict digital sovereignty regulations (EU data sovereignty), internal mandates prohibiting key material in any cloud, financial services requiring key material isolation.
- Caveat: Significant latency impact (every operation requires round-trip to external manager). Availability limited by external manager SLA. Higher operational complexity. Not supported for all key types.
- Source: https://docs.aws.amazon.com/kms/latest/developerguide/keystore-external.html

---

## Scenario Coverage

**Standard Case**: Production SaaS application with multi-service encryption
- Approach: Create one customer managed symmetric encryption key per application domain. Enable automatic rotation (365 days). Configure key policies with least-privilege (separate admin/user roles). Enable S3 Bucket Keys for storage. Use kms:ViaService and kms:EncryptionContext conditions. Deploy VPC endpoints in all private subnets. Tag keys for cost allocation.
- Key Decisions: Single key vs per-service key (start with per-domain, split only if access patterns diverge). Caching strategy for high-throughput paths. Alias naming convention.

**Edge Case**: Multi-Region active-active with cross-Region encrypted data replication
- Approach: Create multi-Region primary key (mrk-) in primary Region. Replicate to all active Regions. Configure S3 Cross-Region Replication with same key material. DynamoDB Global Tables with multi-Region key. Application code uses local replica key ARN for decryption — no cross-Region KMS calls.
- Key Considerations: Rotation propagation delay across Regions (eventual consistency). Primary key failure doesn't affect replica decrypt operations. Cost scales with number of replica Regions.

**Anti-Pattern Case**: Request to disable audit logging on KMS operations or use AWS owned keys for PCI-DSS scoped data
- Clarification: "Is the data in scope for PCI-DSS, SOC2, HIPAA, or other compliance framework requiring demonstrable encryption key management controls? If yes, AWS owned keys are NOT acceptable — customer managed keys with CloudTrail logging are MANDATORY. Disabling KMS audit logging violates SEC04-BP01 and likely violates compliance requirements. What is the specific compliance framework and data classification?"
