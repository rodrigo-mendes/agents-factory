# AWS Secrets Manager — Security Architecture Knowledge Base

---

## Metadata

```yaml
Full_Name: "AWS Security Architecture — AWS Secrets Manager"
Cloud_Provider: "AWS"
Architecture_Domain: "Security Architecture — Secrets Management & Credential Lifecycle"
Target_Edition: "AWS Secrets Manager 2024–2025"
Architecture_Context: "Applications requiring centralized secrets management, automatic credential rotation, cross-account secret sharing, and integration with compute services (Lambda, ECS, EKS, EC2)"
Official_Source_URL: "https://docs.aws.amazon.com/secretsmanager/latest/userguide/"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-05-28"
Currency_Threshold: "2027-05-28 — review required after this date due to service feature velocity"
```

---

## Executive Summary

AWS Secrets Manager is a fully managed secrets lifecycle service that enables applications to replace hardcoded credentials with runtime API calls to retrieve secrets dynamically. It manages database credentials, API keys, OAuth tokens, and other sensitive configuration values throughout their lifecycles — including creation, encryption, rotation, retrieval, replication, and deletion. The service uses envelope encryption with AWS KMS (256-bit AES symmetric data keys) and transmits secrets securely over TLS. Secrets Manager integrates natively with RDS, Aurora, Redshift, DocumentDB, and other AWS services for managed rotation without requiring custom Lambda functions.

The 2024–2025 edition introduced **managed rotation** for supported services (RDS, Aurora, Redshift, DocumentDB), eliminating the need for customer-managed Lambda rotation functions for database secrets. **Managed external secrets rotation** was added for partner integrations. The **Secrets Manager Agent** (a local HTTP-based caching daemon) was released for standardized secret consumption across Lambda, ECS, EKS, and EC2. **BatchGetSecretValue** API enables efficient retrieval of multiple secrets in a single call. Multi-Region replication became a first-class feature with automatic synchronization of secret values across replica regions.

The three most critical architecture guardrails for Secrets Manager deployments are: (1) **never hardcode secrets in application code, environment variables, or configuration files** — always retrieve at runtime via API with client-side caching; (2) **enable automatic rotation for all database and service credentials** — rotation as frequently as every 4 hours reduces the window of compromised credential exposure; (3) **access Secrets Manager via VPC endpoints** — Lambda rotation functions and application workloads in private subnets must use interface VPC endpoints (AWS PrivateLink) to keep traffic off the public internet.

---

## Cloud Architecture Glossary

```
Term: Secret
Definition: A resource in Secrets Manager consisting of metadata (name, ARN, description, tags, rotation configuration, encryption key ARN) and one or more secret versions containing encrypted secret values. Secret values can be strings (up to 65,536 bytes) or binary data.
Provider Docs Section: https://docs.aws.amazon.com/secretsmanager/latest/userguide/whats-in-a-secret.html
Architect Usage: Model each distinct credential or sensitive configuration as a separate secret. Use JSON key-value pairs to store structured secrets (host, port, username, password, engine, dbname).
Common Confusion: A "secret" is not just the password — it is the entire resource including metadata, versioning, and rotation configuration. The secret value is the encrypted payload within the secret.

Term: Secret Version
Definition: An immutable copy of the encrypted secret value, identified by a version ID (UUID) and labeled with staging labels (AWSCURRENT, AWSPREVIOUS, AWSPENDING). Secrets Manager maintains at most 100 labeled versions per secret.
Provider Docs Section: https://docs.aws.amazon.com/secretsmanager/latest/userguide/whats-in-a-secret.html
Architect Usage: Always retrieve the AWSCURRENT version (default). During rotation, AWSPENDING contains the new credential being tested. Applications should implement retry logic during rotation windows.
Common Confusion: Secrets Manager does NOT maintain a linear version history. Only labeled versions are retained — unlabeled versions are garbage-collected. This is not a version control system.

Term: Staging Label
Definition: A text label attached to a secret version that indicates its lifecycle state: AWSCURRENT (active version returned by default), AWSPREVIOUS (previous active version), AWSPENDING (version being validated during rotation). Custom labels are also supported (up to 20 per secret).
Provider Docs Section: https://docs.aws.amazon.com/secretsmanager/latest/userguide/whats-in-a-secret.html
Architect Usage: Use AWSCURRENT for all application retrievals. Use AWSPREVIOUS as a rollback target if rotation produces a broken credential. Use custom labels for blue-green deployment scenarios.
Common Confusion: Two versions cannot share the same staging label. Moving a label from one version to another is atomic — Secrets Manager handles the swap.

Term: Managed Rotation
Definition: Automatic credential rotation performed entirely by the AWS service that owns the secret (e.g., RDS, Aurora, Redshift, DocumentDB), without requiring a customer-managed Lambda function. The service creates, validates, and activates new credentials.
Provider Docs Section: https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotate-secrets_managed.html
Architect Usage: Prefer managed rotation for all supported database services — it eliminates the operational burden of Lambda function maintenance, VPC networking, and rotation code bugs.
Common Confusion: Managed rotation is NOT available for all secret types. Custom application secrets, third-party API keys, and unsupported databases still require Lambda rotation functions.

Term: Lambda Rotation Function
Definition: An AWS Lambda function that implements the four-step rotation protocol (createSecret, setSecret, testSecret, finishSecret) to rotate credentials that are not supported by managed rotation. Secrets Manager invokes this function on a configurable schedule.
Provider Docs Section: https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotate-secrets_lambda-functions.html
Architect Usage: Deploy rotation functions in the same VPC as the database they rotate. Ensure the function has network access to both the database AND Secrets Manager (via VPC endpoint or NAT gateway).
Common Confusion: The rotation function is NOT a generic Lambda — it must implement the four-step contract. AWS provides templates for common databases (MySQL, PostgreSQL, Oracle, SQL Server, MariaDB, MongoDB, Redshift).

Term: Single User Rotation Strategy
Definition: A rotation strategy where the Lambda function updates the password for a single database user. During rotation, there is a brief window where the old password is invalid but the new password is not yet stored as AWSCURRENT.
Provider Docs Section: https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotation-strategy.html
Architect Usage: Use for most workloads. Implement exponential backoff retry in applications to handle the brief window during password change. Simpler to manage — no superuser secret required.
Common Confusion: The "brief window" of unavailability is typically milliseconds to low seconds. Applications with aggressive connection pooling may not notice it. Not the same as downtime.

Term: Alternating Users Rotation Strategy
Definition: A rotation strategy that maintains two database users (user and user_clone), alternating which one is the active credential. Requires a superuser secret for cloning. Provides zero-downtime rotation because the previous credential remains valid.
Provider Docs Section: https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotation-strategy.html
Architect Usage: Use for high-availability workloads where even millisecond credential unavailability is unacceptable. Requires additional database user management and a superuser secret.
Common Confusion: The cloned user does NOT automatically inherit permission changes made to the original user after cloning. Both users must be maintained in sync for permissions.

Term: Envelope Encryption
Definition: The encryption pattern where Secrets Manager requests a 256-bit AES data key from KMS (GenerateDataKey), encrypts the secret value with the plaintext data key, stores the encrypted data key alongside the encrypted secret, and discards the plaintext key from memory.
Provider Docs Section: https://docs.aws.amazon.com/secretsmanager/latest/userguide/security-encryption.html
Architect Usage: Understand that the KMS key never directly touches the secret value. Changing the KMS key re-encrypts the data keys (via Encrypt API), not the secret value. This affects key rotation planning.
Common Confusion: KMS key rotation (annual) is different from secret rotation. KMS key rotation changes the backing key material for NEW encryptions — existing data keys remain encrypted under the old key material (which KMS retains).

Term: Resource Policy
Definition: A JSON policy document attached directly to a secret that grants or denies access to specific principals (IAM users, roles, accounts, services). Enables cross-account access and service-principal authorization without modifying identity policies.
Provider Docs Section: https://docs.aws.amazon.com/secretsmanager/latest/userguide/auth-and-access_resource-policies.html
Architect Usage: Use resource policies for cross-account secret sharing. Combine with identity policies for defense-in-depth. Use BlockPublicPolicy to prevent overly permissive resource policies.
Common Confusion: Resource policies are evaluated in conjunction with identity policies (both must allow for cross-account access). For same-account access, either can grant permission independently.

Term: VPC Endpoint (Interface)
Definition: An AWS PrivateLink-powered elastic network interface (ENI) in your VPC that provides private connectivity to the Secrets Manager API (com.amazonaws.<region>.secretsmanager) without traversing the public internet.
Provider Docs Section: https://docs.aws.amazon.com/secretsmanager/latest/userguide/vpc-endpoint-overview.html
Architect Usage: Create VPC endpoints in every VPC where Lambda rotation functions or application workloads retrieve secrets. Enable private DNS so standard SDK calls route through the endpoint automatically.
Common Confusion: VPC endpoints are regional — you need one per VPC, not per subnet. The endpoint is placed in specific subnets but is accessible from the entire VPC (with private DNS enabled).

Term: Secrets Manager Agent
Definition: A language-agnostic local HTTP client (daemon process) that retrieves and caches secrets from Secrets Manager. Runs as a sidecar or daemon, exposing a localhost HTTP endpoint (port 2773) for secret retrieval. Supports Lambda, ECS, EKS, and EC2.
Provider Docs Section: https://docs.aws.amazon.com/secretsmanager/latest/userguide/secrets-manager-agent.html
Architect Usage: Use the agent to standardize secret retrieval across heterogeneous compute environments. Eliminates the need for per-language caching libraries. Reduces API call volume and latency.
Common Confusion: The agent is NOT the same as the AWS Parameters and Secrets Lambda Extension (which is Lambda-specific). The agent is a standalone binary that works anywhere.

Term: Replica Secret
Definition: A read-only copy of a primary secret that is automatically synchronized to another AWS Region. The replica maintains the same secret value but can use a different KMS key. Replication is asynchronous.
Provider Docs Section: https://docs.aws.amazon.com/secretsmanager/latest/userguide/replicate-secrets.html
Architect Usage: Use multi-region replication for disaster recovery (applications in the DR region can retrieve secrets locally) and for reducing cross-region latency. Promotion of a replica to standalone is supported.
Common Confusion: Replica secrets are read-only — you cannot PutSecretValue on a replica. Rotation happens only on the primary, and changes replicate automatically to all replicas.
```

---

## Architecture Guardrails

### ✅ Mandatory Patterns

**1. Eliminate Hardcoded Secrets — Retrieve at Runtime with Caching**
- Pillar Alignment: Security
- Why: Hardcoded credentials in source code, environment variables, container images, or configuration files are extractable via version control history, container inspection, process listing (/proc/*/environ), and memory dumps. AWS Well-Architected Security Pillar SEC02-BP02 mandates using temporary credentials and secrets management services.
- AWS Services: AWS Secrets Manager, Secrets Manager Agent, AWS Parameters and Secrets Lambda Extension, client-side caching libraries (Java, Python, .NET, Go, Rust)
- Architecture Decision:
  ```
  - Store all credentials, API keys, OAuth tokens, and connection strings in Secrets Manager
  - Retrieve secrets at application startup and cache locally (TTL-based, default 300s)
  - Use Secrets Manager client-side caching library for your runtime:
    - Java: aws-secretsmanager-caching-java
    - Python: aws-secretsmanager-caching-python
    - .NET: aws-secretsmanager-caching-net
    - Go: aws-secretsmanager-caching-go
    - Rust: aws-secretsmanager-caching-rust
  - For Lambda: use AWS Parameters and Secrets Lambda Extension (Layer)
  - For ECS/EKS: use Secrets Manager Agent sidecar or native ECS secret injection
  - For EC2: use Secrets Manager Agent daemon or SDK with caching library
  - Use CodeGuru Reviewer or Amazon Q to scan code for hardcoded secrets
  ```
- Verification:
  ```bash
  # Scan for hardcoded secrets in code (use CodeGuru or Amazon Q)
  # Verify application retrieves from Secrets Manager:
  aws cloudtrail lookup-events \
    --lookup-attributes AttributeKey=EventName,AttributeValue=GetSecretValue \
    --start-time $(date -d '-1 hour' --iso-8601=seconds)
  # Ensure no secrets in environment variables:
  aws ecs describe-task-definition --task-definition <task> \
    --query 'taskDefinition.containerDefinitions[*].environment'
  # Should use 'secrets' field, not 'environment' for sensitive values
  ```
- Trade-offs: Adds API latency on cold start (mitigated by caching); requires IAM permissions for secret access; introduces a runtime dependency on Secrets Manager availability
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html

---

**2. Enable Automatic Rotation for All Database Credentials**
- Pillar Alignment: Security
- Why: Long-lived credentials become increasingly likely to be compromised over time through credential stuffing, lateral movement, or insider threat. Automatic rotation limits the blast radius of compromised credentials to the rotation window (minimum 4 hours). AWS Well-Architected Security Pillar SEC02-BP04 mandates credential rotation.
- AWS Services: AWS Secrets Manager (managed rotation), AWS Lambda (custom rotation), Amazon RDS, Aurora, Redshift, DocumentDB
- Architecture Decision:
  ```
  - For RDS/Aurora/Redshift/DocumentDB: use managed rotation (no Lambda required)
    - Enable via console or CLI: aws secretsmanager rotate-secret --secret-id <id> --rotation-rules
    - Set rotation interval: minimum 4 hours, recommended 24-72 hours for databases
  - For other databases/services: deploy Lambda rotation function
    - Use AWS-provided rotation templates (SecretsManagerRotation*)
    - Deploy Lambda in same VPC as the database
    - Create Secrets Manager VPC endpoint in the Lambda VPC
    - Grant Lambda execution role: secretsmanager:GetSecretValue, secretsmanager:PutSecretValue,
      secretsmanager:DescribeSecret, secretsmanager:UpdateSecretVersionStage
  - Choose rotation strategy:
    - Single user: simpler, brief unavailability window (use retry logic)
    - Alternating users: zero-downtime, requires superuser secret
  - Test rotation manually before enabling automatic schedule:
    aws secretsmanager rotate-secret --secret-id <id>
  ```
- Verification:
  ```bash
  # Check rotation is enabled:
  aws secretsmanager describe-secret --secret-id <id> \
    --query '{RotationEnabled:RotationEnabled,RotationRules:RotationRules,LastRotated:LastRotatedDate}'
  # Verify rotation Lambda can reach Secrets Manager:
  aws lambda get-function --function-name <rotation-function> \
    --query 'Configuration.VpcConfig'
  # Use AWS Config rule: secretsmanager-rotation-enabled-check
  aws configservice get-compliance-details-by-config-rule \
    --config-rule-name secretsmanager-rotation-enabled-check
  ```
- Trade-offs: Managed rotation is limited to supported databases; Lambda rotation adds VPC networking complexity; alternating users doubles the database user count; rotation failures can lock out applications if not monitored
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotating-secrets.html

---

**3. Access Secrets Manager via VPC Endpoints (AWS PrivateLink)**
- Pillar Alignment: Security
- Why: Lambda rotation functions and application workloads in private subnets must reach the Secrets Manager API. Without a VPC endpoint, traffic must route through a NAT gateway and the public internet, increasing attack surface and data exfiltration risk. AWS Well-Architected Security Pillar SEC09-BP02 mandates encrypting data in transit and minimizing exposure.
- AWS Services: AWS PrivateLink, VPC Interface Endpoint (com.amazonaws.<region>.secretsmanager), VPC Endpoint Policies
- Architecture Decision:
  ```
  - Create interface VPC endpoint for Secrets Manager in every VPC that retrieves secrets:
    Service name: com.amazonaws.<region>.secretsmanager
    (FIPS variant: com.amazonaws.<region>.secretsmanager-fips)
  - Enable Private DNS on the endpoint (route standard API calls through endpoint)
  - Place endpoint ENIs in private subnets (one per AZ for HA)
  - Attach VPC Endpoint Policy to restrict access:
    - Allow only specific secrets (by ARN) or specific actions
    - Allow only specific principals (IAM roles) 
  - Use resource policy condition keys to enforce VPC-only access:
    "Condition": { "StringEquals": { "aws:sourceVpce": "vpce-1234567890abcdef0" } }
  - For Lambda rotation functions: ensure the Lambda VPC has the endpoint configured
  ```
- Verification:
  ```bash
  # List VPC endpoints for Secrets Manager:
  aws ec2 describe-vpc-endpoints \
    --filters Name=service-name,Values=com.amazonaws.<region>.secretsmanager \
    --query 'VpcEndpoints[*].{Id:VpcEndpointId,VPC:VpcId,State:State,PrivateDns:PrivateDnsEnabled}'
  # Verify endpoint policy is not overly permissive:
  aws ec2 describe-vpc-endpoints --vpc-endpoint-ids vpce-xxx \
    --query 'VpcEndpoints[0].PolicyDocument'
  # Test connectivity from within VPC:
  # (from EC2 instance in private subnet)
  aws secretsmanager get-secret-value --secret-id test-secret --region <region>
  ```
- Trade-offs: VPC endpoints incur hourly cost per AZ (~$0.01/hr per ENI + data processing); adds infrastructure to manage; private DNS may conflict with custom DNS configurations
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/vpc-endpoint-overview.html

---

**4. Encrypt Secrets with Customer Managed KMS Key for Cross-Account or Audit Scenarios**
- Pillar Alignment: Security
- Why: The default AWS managed key (`aws/secretsmanager`) provides encryption at no additional cost but does not support cross-account access, custom key policies, or granular CloudTrail auditing of key usage per secret. Customer managed keys (CMK) enable fine-grained access control, cross-account sharing, and key policy conditions.
- AWS Services: AWS Secrets Manager, AWS KMS (Customer Managed Key), AWS CloudTrail
- Architecture Decision:
  ```
  - Default: Use aws/secretsmanager managed key for single-account, simple deployments (free)
  - Use Customer Managed Key (CMK) when:
    - Cross-account secret access is required (mandatory — managed key doesn't allow it)
    - Granular key policy control is needed (restrict key usage to specific principals)
    - Compliance requires key audit trail separation
    - Key deletion/disabling needs to revoke all secret access immediately
  - CMK Key Policy best practices:
    - Add kms:ViaService condition: "secretsmanager.<region>.amazonaws.com"
    - Use encryption context conditions for fine-grained control
    - Grant kms:Decrypt to secret consumers, kms:GenerateDataKey to secret writers
  - Enable KMS key rotation (annual, automatic) for the CMK
  ```
- Verification:
  ```bash
  # Check which KMS key a secret uses:
  aws secretsmanager describe-secret --secret-id <id> \
    --query 'KmsKeyId'
  # If null, it uses the AWS managed key
  # Verify CMK key policy includes ViaService condition:
  aws kms get-key-policy --key-id <key-id> --policy-name default \
    --query 'Policy' | jq .
  # Verify CMK rotation is enabled:
  aws kms get-key-rotation-status --key-id <key-id>
  ```
- Trade-offs: CMK costs $1/month per key + API call charges; key policy management overhead; accidental key deletion/disabling makes secrets permanently inaccessible (schedule deletion with 7-30 day wait)
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/security-encryption.html

---

**5. Implement Least-Privilege IAM for Secret Access**
- Pillar Alignment: Security
- Why: Overly permissive IAM policies (e.g., `secretsmanager:*` on `*`) expose all secrets to any principal with that policy. AWS Well-Architected Security Pillar SEC03-BP02 mandates least-privilege access — each workload should only access the specific secrets it requires.
- AWS Services: AWS IAM (Identity Policies), AWS Secrets Manager (Resource Policies), ABAC (tag-based access control)
- Architecture Decision:
  ```
  - Identity policies: scope to specific secret ARNs or ARN patterns:
    Resource: "arn:aws:secretsmanager:<region>:<account>:secret:<app-name>/*"
  - Limit actions to what is needed:
    - Applications: secretsmanager:GetSecretValue, secretsmanager:DescribeSecret
    - Rotation functions: add PutSecretValue, UpdateSecretVersionStage
    - Administrators: full access to manage lifecycle (CreateSecret, DeleteSecret, etc.)
  - Use ABAC (tag-based access control) for scalable permissions:
    Condition: { "StringEquals": { "secretsmanager:ResourceTag/Environment": "${aws:PrincipalTag/Environment}" } }
  - Use resource policies for cross-account access and to enforce BlockPublicPolicy
  - Deny dangerous patterns in SCPs:
    Deny secretsmanager:GetSecretValue where ResourceTag/Classification = "restricted"
    unless principal is in the approved role
  ```
- Verification:
  ```bash
  # Identify who can access a secret:
  aws secretsmanager get-resource-policy --secret-id <id>
  # Use IAM Access Analyzer to validate policies:
  aws accessanalyzer validate-policy --policy-document file://policy.json --policy-type IDENTITY_POLICY
  # Use AWS Config rule: secretsmanager-secret-unused
  # Detects secrets not accessed within configurable days
  ```
- Trade-offs: Fine-grained policies increase management complexity; ABAC requires consistent tagging discipline; resource policies add another policy evaluation layer to debug
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/auth-and-access.html

---

**6. Monitor Secret Access and Lifecycle Events**
- Pillar Alignment: Security, Operational Excellence
- Why: Unmonitored secret access enables credential exfiltration without detection. AWS Well-Architected Security Pillar SEC04-BP01 mandates centralized logging. Secrets Manager integrates with CloudTrail (management events — free first copy), CloudWatch (metrics and alarms), AWS Config (compliance), and GuardDuty (anomaly detection).
- AWS Services: AWS CloudTrail, Amazon CloudWatch, AWS Config, Amazon GuardDuty, Amazon EventBridge
- Architecture Decision:
  ```
  - CloudTrail: all Secrets Manager API calls are logged as management events (automatic)
    - Monitor: GetSecretValue (access), CreateSecret, DeleteSecret, PutSecretValue, RotateSecret
    - Alert on: GetSecretValue from unexpected principals or regions
  - CloudWatch Alarms:
    - Metric: aws/secretsmanager/RotationSuccessful (count == 0 for expected rotations)
    - Metric: aws/secretsmanager/RotationFailed (count > 0 — immediate alert)
  - AWS Config Rules (built-in):
    - secretsmanager-rotation-enabled-check: ensures rotation is enabled
    - secretsmanager-scheduled-rotation-success-check: ensures rotation is succeeding
    - secretsmanager-secret-periodic-rotation: ensures secrets rotated within N days
    - secretsmanager-secret-unused: detects secrets not accessed within N days
    - secretsmanager-using-cmk: ensures customer managed key is used
  - GuardDuty: detects anomalous secret access patterns
  - EventBridge: route rotation failure events to SNS/PagerDuty for alerting
  ```
- Verification:
  ```bash
  # Verify CloudTrail is logging Secrets Manager events:
  aws cloudtrail lookup-events \
    --lookup-attributes AttributeKey=EventSource,AttributeValue=secretsmanager.amazonaws.com \
    --max-results 5
  # Check Config rules are active:
  aws configservice describe-config-rules \
    --config-rule-names secretsmanager-rotation-enabled-check
  # Verify GuardDuty is enabled:
  aws guardduty list-detectors
  ```
- Trade-offs: CloudTrail data events (if enabled beyond management events) incur cost; Config rules have per-evaluation charges; alert fatigue if thresholds are misconfigured
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/monitoring.html

---

### ⚠️ Architectural Decisions

**1. Secrets Manager vs Parameter Store (SecureString)**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Secrets Manager | AWS Secrets Manager | Automatic rotation, cross-region replication, resource policies, managed rotation for databases | Cost ($0.40/secret/month + $0.05/10K API calls) | Credentials requiring rotation, database passwords, API keys, cross-account sharing |
  | Parameter Store SecureString | AWS Systems Manager Parameter Store | Cost (free standard tier, $0.05/advanced/month), simple key-value access | No native rotation, no resource policies, no replication, 10K param limit (standard) | Configuration values, feature flags, non-rotating secrets, budget-constrained environments |
  | Parameter Store + Secrets Manager Reference | Both | Cost optimization — store reference in Parameter Store pointing to Secrets Manager secret | Additional indirection, two services to manage | ECS task definitions needing both config and secrets |

- Cost Profile: Secrets Manager is ~8x more expensive per secret/month than Parameter Store advanced tier, but includes rotation infrastructure that would cost more to build custom
- Lock-in Assessment: Both are AWS-native. Secrets Manager has cross-account and cross-region portability advantages. Parameter Store is simpler but more limited for secret lifecycle management
- Architect Instruction: "Choose Secrets Manager when credentials MUST be rotated automatically or shared cross-account. Choose Parameter Store when the value is configuration, not a credential, or when cost is the primary constraint and rotation is handled externally."
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html

---

**2. Rotation Strategy: Single User vs Alternating Users**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Single User | Secrets Manager + Lambda | Simplicity — one DB user, no superuser secret needed | Brief unavailability window during password change (milliseconds–seconds) | Most workloads with retry logic; ad-hoc or interactive users; simple permission model |
  | Alternating Users | Secrets Manager + Lambda + Superuser Secret | Zero-downtime rotation — previous credential always valid | Complexity — requires superuser secret, two DB users, permission sync | High-availability workloads; applications without retry logic; database server farms with replication lag |
  | Managed Rotation | Secrets Manager + RDS/Aurora native | Zero operational overhead — no Lambda, no VPC config | Limited to supported databases; less customization | RDS, Aurora, Redshift, DocumentDB master user credentials |

- Cost Profile: Single user is cheapest (one secret). Alternating users requires an additional superuser secret ($0.40/month) and double DB user management. Managed rotation eliminates Lambda cost entirely.
- Lock-in Assessment: Managed rotation is the most locked-in (AWS-service specific) but lowest operational burden. Lambda rotation is portable in pattern (can implement for any database).
- Architect Instruction: "Use managed rotation for RDS/Aurora/Redshift/DocumentDB master passwords. For application-level DB users, choose single user rotation unless the application has strict zero-downtime requirements for credential changes."
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotation-strategy.html

---

**3. Encryption Key Selection: AWS Managed Key vs Customer Managed Key**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | AWS Managed Key (aws/secretsmanager) | KMS AWS Managed Key | Cost (free), zero management | No cross-account access, no custom key policy, limited audit granularity | Single-account, simple deployments with no cross-account requirements |
  | Customer Managed Key (CMK) | KMS Customer Managed Key | Cross-account access, granular key policy, audit separation, immediate revocation via key disable | Cost ($1/month/key + API calls), key policy management | Cross-account secrets, compliance-driven audit, need to revoke all access via key |
  | External Key Store (XKS) | KMS with External Key Store | Key material never leaves customer HSM | Higher latency, availability depends on external store, complex setup | Regulatory requirements mandating customer-controlled key material (rare) |

- Cost Profile: Managed key = free; CMK = $1/month + ~$0.03/10K requests; XKS = CMK cost + external HSM infrastructure
- Lock-in Assessment: AWS managed and CMK are both KMS-native. XKS provides theoretical key portability but practical complexity is extreme
- Architect Instruction: "Use the AWS managed key unless you need cross-account secret sharing (which mandates CMK) or compliance requires key policy audit separation. Use XKS only when regulators explicitly require customer-held key material."
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/security-encryption.html

---

**4. Secret Retrieval Pattern: SDK Direct vs Caching Library vs Agent vs Lambda Extension**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | SDK Direct (GetSecretValue) | AWS SDK | Simplicity — no additional dependency | No caching, higher API cost, higher latency, rate limit risk | Infrequent access, scripts, one-time retrieval |
  | Client-Side Caching Library | Language-specific caching library | Reduced API calls, lower latency after first fetch, TTL-based refresh | Language-specific dependency, cache staleness window | Long-running applications (ECS, EC2, EKS pods) |
  | Secrets Manager Agent | Secrets Manager Agent (localhost HTTP) | Language-agnostic, single caching layer, works everywhere | Additional process to manage, port 2773 occupied | Polyglot environments, sidecar patterns, standardized access |
  | Lambda Extension | AWS Parameters and Secrets Lambda Extension | Optimized for Lambda lifecycle, shared cache across invocations | Lambda-only, adds ~50ms cold start, extension layer size | Lambda functions retrieving secrets |

- Cost Profile: Direct SDK has highest API cost. Caching reduces by ~95%+ depending on TTL. Agent and Extension further reduce by sharing cache across requests.
- Lock-in Assessment: All options are AWS-specific. The Agent provides the most portable interface (localhost HTTP) for potential future abstraction.
- Architect Instruction: "Use the Lambda Extension for Lambda functions. Use the client-side caching library for single-language services. Use the Secrets Manager Agent for polyglot environments or sidecar architectures in EKS/ECS."
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html

---

**5. Multi-Region Strategy: Replication vs Independent Secrets**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Multi-Region Replication | Secrets Manager ReplicateSecretToRegions | Automatic sync, single source of truth, DR readiness, low cross-region latency | Primary region dependency for writes, async replication lag, different KMS key per region | Active-passive DR, multi-region read workloads, global applications needing local secret access |
  | Independent Secrets per Region | Secrets Manager (per-region) | Full independence, no replication dependency, different values per region | Manual sync burden, drift risk, no atomic cross-region updates | Different credentials per region (different DB instances), fully independent regional deployments |

- Cost Profile: Replication charges $0.40/secret/month per replica region. Independent secrets cost the same but require separate rotation configuration per region.
- Lock-in Assessment: Replication is AWS-native with no portable equivalent. Independent secrets are the portable pattern but lose automation.
- Architect Instruction: "Use multi-region replication when the same credential is needed in multiple regions (DR failover, global read replicas). Use independent secrets when each region connects to a different resource with different credentials."
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/replicate-secrets.html

---

### 🚫 Anti-Patterns

**1. Hardcoded Credentials in Source Code or Environment Variables**
- Risk Level: CRITICAL
- Why: Security Pillar violation — SEC02-BP02. Credentials in code are exposed via version control (Git history), container image layers, CI/CD logs, and process environment inspection. Environment variables are visible to any process with the same UID and logged by many frameworks.
- Instead:
  ```
  Use Secrets Manager with runtime retrieval:
  - Applications: SDK call with client-side caching library
  - ECS: "secrets" field in task definition (valueFrom: secret ARN)
  - Lambda: Lambda Extension or environment variable backed by Secrets Manager reference
  - EKS: Secrets Store CSI Driver with Secrets Manager provider
  ```
- Detection:
  ```bash
  # CodeGuru Reviewer secrets detector (integrated with CI/CD)
  # Amazon Q security scans
  # git-secrets (pre-commit hook): git secrets --scan
  # truffleHog: trufflehog git file://. --only-verified
  # AWS Config: no built-in rule; use custom rule or CodeGuru
  ```
- Impact: Data breach — exposed credentials provide unauthorized access to databases, APIs, and services. Credential rotation does not help if the hardcoded value is the current password.
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html

---

**2. Wildcard IAM Permissions for Secrets Manager**
- Risk Level: CRITICAL
- Why: Security Pillar violation — SEC03-BP02 (least privilege). Policies like `"Action": "secretsmanager:*", "Resource": "*"` grant every principal with that policy full control over ALL secrets in the account, including production database credentials, API keys, and service tokens.
- Instead:
  ```
  Scope to specific actions and resources:
  {
    "Effect": "Allow",
    "Action": [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret"
    ],
    "Resource": "arn:aws:secretsmanager:<region>:<account>:secret:<app-prefix>-*"
  }
  For rotation functions, add only:
    "secretsmanager:PutSecretValue",
    "secretsmanager:UpdateSecretVersionStage"
  ```
- Detection:
  ```bash
  # IAM Access Analyzer finding type: ExternalPrincipal or UnusedAccess
  aws accessanalyzer list-findings --analyzer-name <name> \
    --filter '{"resourceType":{"eq":["AWS::SecretsManager::Secret"]}}'
  # Custom Config rule checking for wildcard policies
  # AWS IAM Policy Simulator for verifying effective permissions
  ```
- Impact: Credential theft, unauthorized secret modification, deletion of secrets causing service outages, compliance violation (SOC2 CC6.3, PCI DSS 7.1)
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/auth-and-access.html

---

**3. Disabled or Missing Secret Rotation**
- Risk Level: HIGH
- Why: Security Pillar violation — SEC02-BP04. Static credentials that never rotate provide an unlimited exploitation window once compromised. The attacker retains access indefinitely until manual detection and revocation.
- Instead:
  ```
  Enable automatic rotation:
  - For RDS/Aurora/Redshift/DocumentDB: managed rotation (no Lambda)
  - For other databases: Lambda rotation function with AWS templates
  - For API keys: custom Lambda rotation or short-lived token pattern
  - Minimum rotation schedule: 90 days (compliance baseline)
  - Recommended: 24-72 hours for database credentials
  - Maximum frequency: every 4 hours
  ```
- Detection:
  ```bash
  # AWS Config rule:
  aws configservice get-compliance-details-by-config-rule \
    --config-rule-name secretsmanager-rotation-enabled-check \
    --compliance-types NON_COMPLIANT
  # Direct query for secrets without rotation:
  aws secretsmanager list-secrets \
    --query 'SecretList[?RotationEnabled==`false`].{Name:Name,ARN:ARN,LastChanged:LastChangedDate}'
  ```
- Impact: Extended credential compromise window; compliance violations (PCI DSS 8.2.4 requires 90-day password changes); audit findings; potential data breach
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotating-secrets.html

---

**4. Rotation Lambda Without VPC Endpoint Access**
- Risk Level: HIGH
- Why: Reliability Pillar violation. A Lambda rotation function deployed in a VPC without a Secrets Manager VPC endpoint or NAT gateway cannot reach the Secrets Manager API. Rotation silently fails, leaving stale credentials that will eventually be revoked on the database side — causing application outages.
- Instead:
  ```
  Ensure rotation Lambda has connectivity to BOTH the database AND Secrets Manager:
  Option A (Recommended): VPC endpoint for Secrets Manager in the Lambda VPC
    Service: com.amazonaws.<region>.secretsmanager
    Private DNS: enabled
  Option B: NAT Gateway in public subnet with route from private subnet
    (More expensive, broader internet access than needed)
  Verify: manually trigger rotation and check CloudWatch Logs for the Lambda
  ```
- Detection:
  ```bash
  # Check Lambda VPC configuration:
  aws lambda get-function --function-name <rotation-fn> \
    --query 'Configuration.VpcConfig.{Subnets:SubnetIds,SGs:SecurityGroupIds}'
  # Check VPC has Secrets Manager endpoint:
  aws ec2 describe-vpc-endpoints \
    --filters Name=vpc-id,Values=<vpc-id> Name=service-name,Values=com.amazonaws.<region>.secretsmanager
  # Check rotation is succeeding:
  aws secretsmanager describe-secret --secret-id <id> \
    --query '{LastRotated:LastRotatedDate,RotationEnabled:RotationEnabled}'
  # CloudWatch Logs for rotation function errors:
  aws logs filter-log-events --log-group-name /aws/lambda/<rotation-fn> \
    --filter-pattern "ERROR"
  ```
- Impact: Service outage — rotation fails silently, credentials become stale, database eventually rejects the outdated password
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/vpc-endpoint-overview.html

---

**5. Sharing Secrets via Copy (Not Cross-Account Access)**
- Risk Level: MEDIUM
- Why: Copying secret values to another account (via manual process, SSM Parameter Store, or S3) creates unmanaged duplicates that don't rotate in sync. When the source rotates, the copy becomes invalid — causing outages. No audit trail links the copy to the original.
- Instead:
  ```
  Use Secrets Manager cross-account access:
  1. Encrypt secret with a Customer Managed KMS key (mandatory for cross-account)
  2. Attach resource policy to the secret granting the consuming account access:
     {
       "Effect": "Allow",
       "Principal": { "AWS": "arn:aws:iam::<consumer-account>:role/<role-name>" },
       "Action": "secretsmanager:GetSecretValue",
       "Resource": "*"
     }
  3. Grant the consumer role kms:Decrypt on the CMK (via key policy)
  4. Consumer retrieves secret directly via ARN from the source account
  Alternative: Use multi-region replication within the same organization
  ```
- Detection:
  ```bash
  # Look for secrets being retrieved from unusual accounts (CloudTrail):
  # Check for resource policies allowing cross-account access properly:
  aws secretsmanager get-resource-policy --secret-id <id>
  # Verify no manual copy processes exist (audit CI/CD pipelines)
  ```
- Impact: Service outage when source credential rotates; credential drift between environments; compliance gap (no audit trail for the copy); secrets proliferation outside managed lifecycle
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/auth-and-access_examples_cross.html

---

**6. Unencrypted Secret Metadata Exposure**
- Risk Level: MEDIUM
- Why: Secrets Manager does NOT encrypt secret names, descriptions, tags, rotation settings, or the KMS key ARN. These metadata fields should not contain sensitive information (e.g., don't put the password in the secret name or description).
- Instead:
  ```
  - Use generic, descriptive names: "prod/myapp/database/primary" (not "prod-admin-P@ssw0rd")
  - Never put sensitive values in tags, descriptions, or secret names
  - Use hierarchical naming convention for organization:
    <environment>/<application>/<resource-type>/<identifier>
  - Store ALL sensitive data in the encrypted secret value (JSON payload)
  ```
- Detection:
  ```bash
  # Audit secret names and descriptions for sensitive patterns:
  aws secretsmanager list-secrets \
    --query 'SecretList[*].{Name:Name,Description:Description,Tags:Tags}'
  # Look for names containing: password, key, token, secret (the value itself)
  ```
- Impact: Information disclosure — metadata visible to anyone with secretsmanager:ListSecrets or secretsmanager:DescribeSecret permissions; compliance finding
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/security-encryption.html

---

## Cloud-Native Design Patterns

**Secret Injection at Container Runtime (ECS/EKS)**
- Category: Security
- Problem: Containers need database credentials and API keys at startup, but baking secrets into images or passing as environment variables is insecure.
- Solution on AWS:
  ```
  ECS:
  - Use "secrets" field in task definition (not "environment"):
    "secrets": [{ "name": "DB_PASSWORD", "valueFrom": "arn:aws:secretsmanager:<region>:<account>:secret:<name>:<key>::" }]
  - ECS agent retrieves at task launch and injects as environment variable
  - Rotation: application must handle credential refresh (or use shorter task lifecycle)

  EKS:
  - Deploy AWS Secrets and Configuration Provider (ASCP) for Secrets Store CSI Driver
  - Mount secrets as files in pod volumes (auto-refreshed)
  - Alternative: External Secrets Operator syncs Secrets Manager to Kubernetes Secrets
  - ASCP supports rotation sync (SecretProviderClass with rotationPollInterval)
  ```
- Services Used: AWS Secrets Manager, Amazon ECS (secrets in task def), Amazon EKS (Secrets Store CSI Driver), ASCP
- When to Apply: Any containerized workload requiring credentials
- When NOT to Apply: Serverless Lambda functions (use Lambda Extension instead)
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Security | No secrets in images or env vars at rest | Requires IAM role per task/pod for secret access |
  | Operations | Centralized rotation updates all consumers | Container restart may be needed if rotation changes credential |
  | Complexity | Native integration, no custom code | CSI driver / ASCP adds Kubernetes operator management |

- Complements: VPC Endpoints, IAM Roles for Tasks/Pods, Automatic Rotation
- Source: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/secrets-envvar-secrets-manager.html

---

**Centralized Secrets with Multi-Account Access (Hub-Spoke)**
- Category: Security
- Problem: In multi-account AWS Organizations, workloads in spoke accounts need access to shared credentials (e.g., shared database, third-party API keys) managed centrally.
- Solution on AWS:
  ```
  Hub Account (Security/Shared Services):
  - Store secrets in a dedicated secrets management account
  - Encrypt with Customer Managed KMS key (required for cross-account)
  - Attach resource policies granting spoke account roles access
  - Enable BlockPublicPolicy to prevent overly permissive policies

  Spoke Accounts (Workload Accounts):
  - Application roles assume cross-account read access
  - Retrieve secrets by full ARN (cross-account must use ARN, not name)
  - Cache retrieved secrets locally (reduce cross-account API calls)
  - No rotation function needed in spoke — rotation runs in hub

  KMS Key Policy (Hub Account):
  - Grant kms:Decrypt to spoke account roles
  - Condition: kms:ViaService = "secretsmanager.<region>.amazonaws.com"
  ```
- Services Used: AWS Secrets Manager, AWS KMS (CMK), AWS IAM (cross-account roles), AWS Organizations
- When to Apply: Multi-account environments with shared credentials
- When NOT to Apply: Single-account deployments; secrets that differ per account (use replication instead)
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Governance | Single source of truth, centralized rotation | Hub account is a critical dependency |
  | Security | Minimal secret proliferation, unified audit | Cross-account IAM complexity, KMS policy management |
  | Availability | No credential sync needed | Hub account outage blocks all spoke access (mitigate with replication) |

- Complements: Multi-Region Replication, ABAC tag-based access, SCPs for guardrails
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/auth-and-access_examples_cross.html

---

**Graceful Secret Rotation with Application Retry**
- Category: Resilience
- Problem: During single-user rotation, there is a brief window where the old password is revoked but the new password is not yet committed as AWSCURRENT. Applications using the old credential get authentication failures.
- Solution on AWS:
  ```
  Application-Side:
  - Implement exponential backoff retry with jitter for database connections
  - On authentication failure (specific error codes: 1045 MySQL, 28P01 PostgreSQL):
    1. Clear cached credential
    2. Re-retrieve secret from Secrets Manager (gets AWSCURRENT)
    3. Retry connection with new credential
  - Use connection pool libraries with credential refresh hooks

  Infrastructure-Side:
  - Use alternating users strategy for zero-downtime (if retry is not acceptable)
  - Set rotation window to low-traffic periods (ScheduleExpression cron)
  - Monitor rotation failures and alert immediately (CloudWatch + EventBridge)
  ```
- Services Used: AWS Secrets Manager (rotation), client-side caching libraries, CloudWatch Alarms
- When to Apply: Any workload using single-user rotation strategy
- When NOT to Apply: Applications using managed rotation (handled by the service) or alternating users (no unavailability)
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Simplicity | Single user rotation is simpler to manage | Application must handle retry logic |
  | Availability | Brief disruption (ms–seconds) only | Connection pool exhaustion during retry if many connections fail simultaneously |
  | Cost | One secret, one DB user | Retry logic adds code complexity and testing surface |

- Complements: Circuit Breaker pattern, Connection Pool refresh, Health Check endpoints
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotation-strategy.html

---

**Secrets-Backed Feature Configuration (Separation of Secrets from Config)**
- Category: Data
- Problem: Applications need both non-sensitive configuration (feature flags, endpoints, timeouts) and sensitive secrets (passwords, tokens). Mixing them in a single service creates either cost overhead or security gaps.
- Solution on AWS:
  ```
  Two-Layer Pattern:
  Layer 1 — Non-sensitive configuration:
  - AWS Systems Manager Parameter Store (Standard tier — free, up to 10K params)
  - Store: feature flags, service endpoints, timeout values, region config
  - Access: ssm:GetParameter with caching

  Layer 2 — Sensitive secrets:
  - AWS Secrets Manager
  - Store: database credentials, API keys, OAuth tokens, encryption keys
  - Access: secretsmanager:GetSecretValue with client-side caching
  - Enable rotation for all credentials

  Integration:
  - ECS task definitions can reference both (valueFrom supports both ARN formats)
  - Lambda can use both via the Parameters and Secrets Extension (single layer)
  - Parameter Store can reference Secrets Manager secrets (aws:secretsmanager:*)
  ```
- Services Used: AWS Secrets Manager, AWS Systems Manager Parameter Store, AWS Lambda Extension
- When to Apply: All applications — this is the recommended default pattern
- When NOT to Apply: Extremely simple applications with a single secret and no configuration
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Cost | Parameter Store free tier for config; pay only for actual secrets | Two services to manage, two permission sets |
  | Security | Clear separation — non-sensitive config doesn't need encryption overhead | Developers must correctly classify data as config vs secret |
  | Operations | Different lifecycle management per tier (config changes frequently, secrets rotate) | Two retrieval patterns in application code |

- Complements: Environment-specific naming conventions, ABAC tagging, CI/CD secret injection
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html

---

## Security Architecture

**Identity & Access Management for Secrets**
- AWS Services:
  - AWS IAM (identity policies for secret access)
  - AWS Secrets Manager (resource policies on secrets)
  - AWS KMS (key policies for encryption/decryption)
  - AWS Organizations SCPs (preventive guardrails)
  - ABAC (tag-based conditional access)
- Architecture:
  ```
  Three-Layer Authorization Model:
  1. Identity Policy (IAM role/user) → defines what actions the principal can perform
  2. Resource Policy (on the secret) → defines who can access this specific secret
  3. KMS Key Policy → controls who can decrypt the secret value

  For same-account access: identity policy OR resource policy can grant (either sufficient)
  For cross-account access: BOTH identity policy AND resource policy must allow

  SCP Guardrails (applied at OU/account level):
  - Deny secretsmanager:DeleteSecret without MFA
  - Deny secretsmanager:PutResourcePolicy without BlockPublicPolicy
  - Deny creating secrets without rotation enabled (custom SCP)
  ```
- Configuration Essentials:
  - Always use `secretsmanager:ResourceTag/*` conditions for ABAC at scale
  - Use `aws:RequestedRegion` condition to restrict secret creation to approved regions
  - Use `secretsmanager:BlockPublicPolicy: true` condition on PutResourcePolicy
  - Use `kms:ViaService` condition on CMK key policies to restrict key usage to Secrets Manager
- Verification:
  ```bash
  # IAM Access Analyzer — find external access:
  aws accessanalyzer list-findings --analyzer-name <org-analyzer>
  # Policy Simulator — test effective permissions:
  aws iam simulate-principal-policy --policy-source-arn <role-arn> \
    --action-names secretsmanager:GetSecretValue \
    --resource-arns "arn:aws:secretsmanager:<region>:<account>:secret:prod/*"
  ```
- Compliance Alignment: SOC2 CC6.1 (access controls), PCI DSS 7.1 (restrict access by need-to-know), HIPAA §164.312(a)(1) (access control)
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/auth-and-access.html

---

**Data Protection — Encryption at Rest and in Transit**
- AWS Services:
  - AWS KMS (envelope encryption — GenerateDataKey, Decrypt, Encrypt)
  - AWS Secrets Manager (manages data key lifecycle)
  - TLS 1.2+ (in-transit encryption for all API calls)
  - VPC Endpoints / PrivateLink (network-level encryption and isolation)
- Architecture:
  ```
  Encryption Flow:
  1. CreateSecret/PutSecretValue → Secrets Manager calls KMS GenerateDataKey
  2. KMS returns plaintext data key + encrypted data key
  3. Secrets Manager encrypts secret value with plaintext data key (AES-256)
  4. Plaintext key purged from memory immediately
  5. Encrypted data key stored alongside encrypted secret in metadata

  Decryption Flow:
  1. GetSecretValue → Secrets Manager calls KMS Decrypt with encrypted data key
  2. KMS returns plaintext data key
  3. Secrets Manager decrypts secret value and returns over TLS
  4. Plaintext key purged from memory

  What is NOT encrypted:
  - Secret name, description, tags, rotation config, KMS key ARN
  - Only the secret VALUE is encrypted

  Encryption Context (bound to ciphertext):
  - SecretARN: arn:aws:secretsmanager:<region>:<account>:secret:<name>
  - SecretVersionId: <version-uuid>
  ```
- Configuration Essentials:
  - Default: aws/secretsmanager managed key (free, sufficient for single-account)
  - Cross-account: Customer Managed Key mandatory (managed key doesn't support cross-account Decrypt)
  - Key rotation: enable annual automatic rotation on CMK (KMS retains old key material for decryption)
  - Encryption context: use in key policy conditions for fine-grained access control
- Verification:
  ```bash
  # Verify encryption key for a secret:
  aws secretsmanager describe-secret --secret-id <id> --query 'KmsKeyId'
  # Monitor KMS operations via CloudTrail:
  aws cloudtrail lookup-events \
    --lookup-attributes AttributeKey=EventSource,AttributeValue=kms.amazonaws.com \
    --lookup-attributes AttributeKey=ResourceType,AttributeValue=AWS::KMS::Key
  ```
- Compliance Alignment: SOC2 CC6.7 (encryption controls), PCI DSS 3.4 (render PAN unreadable), HIPAA §164.312(a)(2)(iv) (encryption), GDPR Art. 32 (security of processing)
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/security-encryption.html

---

**Network Security — Private Access**
- AWS Services:
  - VPC Interface Endpoint (com.amazonaws.<region>.secretsmanager)
  - VPC Endpoint Policies
  - Security Groups (on endpoint ENIs)
  - Resource Policies (aws:sourceVpc, aws:sourceVpce conditions)
- Architecture:
  ```
  Private Access Pattern:
  1. Create VPC Interface Endpoint in each VPC:
     - Service: com.amazonaws.<region>.secretsmanager
     - Subnets: one per AZ (for HA)
     - Security Group: allow inbound HTTPS (443) from application SGs
     - Private DNS: enabled (routes standard API calls through endpoint)
  
  2. VPC Endpoint Policy (restrict what can be done through this endpoint):
     - Allow only GetSecretValue and DescribeSecret
     - Restrict to specific secret ARN patterns

  3. Secret Resource Policy (restrict access TO the secret):
     - Condition: aws:sourceVpce = vpce-<id>
     - Denies all access NOT from the VPC endpoint

  4. Lambda Rotation Functions:
     - Deploy in same VPC as database
     - VPC must have Secrets Manager endpoint (or NAT gateway — less preferred)
     - Security group: allow outbound HTTPS to endpoint ENIs + outbound to DB port
  ```
- Configuration Essentials:
  - FIPS endpoint available: com.amazonaws.<region>.secretsmanager-fips (for FedRAMP/GovCloud)
  - IPv6 / dual-stack support available
  - Endpoint policy + resource policy + identity policy = defense-in-depth
  - Shared subnets: cannot create endpoints in shared subnets, but CAN use endpoints in shared subnets
- Verification:
  ```bash
  # Verify endpoint exists and is active:
  aws ec2 describe-vpc-endpoints \
    --filters Name=service-name,Values=com.amazonaws.<region>.secretsmanager \
    --query 'VpcEndpoints[*].{Id:VpcEndpointId,State:State,PrivateDns:PrivateDnsEnabled,Subnets:SubnetIds}'
  # Test from within VPC (should succeed without internet access):
  # From EC2 in private subnet (no NAT):
  aws secretsmanager list-secrets --max-results 1
  ```
- Compliance Alignment: SOC2 CC6.6 (network boundaries), PCI DSS 1.3 (restrict inbound/outbound traffic), HIPAA §164.312(e)(1) (transmission security)
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/vpc-endpoint-overview.html

---

## Operational Patterns

**Rotation Monitoring & Alerting**
- Operational Domain: Observability
- AWS Services:
  - Amazon CloudWatch Metrics (RotationSuccessful, RotationFailed)
  - Amazon EventBridge (SecretRotationStarted, SecretRotationSucceeded, SecretRotationFailed)
  - AWS CloudTrail (RotateSecret API call logging)
  - Amazon SNS (alert notifications)
- Architecture:
  ```
  Monitoring Stack:
  1. CloudWatch Metrics:
     - RotationSuccessful: should increment per rotation schedule
     - RotationFailed: should always be 0 — alarm on count > 0

  2. EventBridge Rules:
     - Pattern: { "source": ["aws.secretsmanager"], "detail-type": ["AWS API Call via CloudTrail"], "detail": { "eventName": ["RotateSecret"] } }
     - Target: SNS topic → PagerDuty/Slack for rotation failures
     - Pattern for rotation success: use for audit/compliance dashboards

  3. CloudTrail Analysis:
     - Filter: eventName = "GetSecretValue" AND userIdentity.arn NOT IN [expected-roles]
     - Alert on unexpected principals accessing secrets

  4. AWS Config Compliance Dashboard:
     - secretsmanager-rotation-enabled-check
     - secretsmanager-scheduled-rotation-success-check
     - secretsmanager-secret-periodic-rotation (customizable days)
  ```
- Cost Profile: Low — CloudWatch metrics free (basic), CloudTrail management events free (first copy), EventBridge rules free (AWS events), Config rules ~$0.001/evaluation
- Automation:
  ```
  Automated Remediation:
  - On RotationFailed: trigger SNS → Lambda that re-attempts rotation
  - On secretsmanager-secret-unused > 90 days: tag for review, alert owner
  - On unexpected GetSecretValue: trigger Security Hub finding → auto-revoke IAM session
  ```
- Runbook Skeleton:
  ```
  1. Detection: CloudWatch alarm or EventBridge notification for rotation failure
  2. Triage: Check rotation Lambda CloudWatch Logs for error details
  3. Common causes:
     - Lambda cannot reach database (security group / network issue)
     - Lambda cannot reach Secrets Manager (VPC endpoint missing)
     - Database user permissions changed (user can't change own password)
     - Superuser secret expired (alternating users strategy)
  4. Resolution: Fix root cause, manually trigger rotation, verify success
  5. Post-mortem: Document failure mode, add monitoring for precondition
  ```
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/monitoring.html

---

**Disaster Recovery — Multi-Region Replication**
- Operational Domain: DR
- RTO/RPO: RPO near-zero (async replication, seconds to minutes lag); RTO seconds (failover reads from replica)
- AWS Services:
  - AWS Secrets Manager (ReplicateSecretToRegions API)
  - AWS KMS (per-region encryption keys)
  - Amazon Route 53 (DNS failover for application layer)
- Architecture:
  ```
  Multi-Region DR Pattern:
  1. Primary Region:
     - All secrets created and managed here
     - Rotation runs only in primary (managed or Lambda)
     - Changes automatically replicate to all configured replica regions

  2. Replica Regions:
     - Read-only copies of secrets (same value, different KMS key)
     - Applications in DR region retrieve secrets locally (low latency)
     - On failover: promote replica to standalone (one-time action)

  3. Failover Procedure:
     a. Detect primary region failure (Route 53 health check or manual)
     b. Promote replica secrets to standalone (aws secretsmanager stop-replication-to-replica)
     c. Configure rotation in the new primary region
     d. Update application configuration to use local region secrets
     e. After recovery: re-establish replication from new primary

  4. Testing:
     - Regularly verify replica secret values match primary
     - Test promotion procedure in non-prod environment
     - Validate application can retrieve secrets from replica region
  ```
- Cost Profile: Medium — $0.40/secret/month per replica region + KMS costs in replica region + data transfer (minimal for secret values)
- Automation:
  ```
  - Use CloudFormation/Terraform to define replication configuration as code
  - EventBridge rule on replication failures → SNS alert
  - Periodic validation Lambda: compare primary and replica versions
  ```
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/replicate-secrets.html

---

**Cost Optimization — Secret Lifecycle Management**
- Operational Domain: FinOps
- AWS Services:
  - AWS Secrets Manager (ListSecrets, DescribeSecret)
  - AWS Config (secretsmanager-secret-unused rule)
  - AWS Cost Explorer (cost allocation tags)
  - Amazon CloudWatch (API call metrics)
- Architecture:
  ```
  Cost Optimization Strategy:
  1. Identify unused secrets:
     - AWS Config rule: secretsmanager-secret-unused (N days without GetSecretValue)
     - CloudTrail: find secrets never accessed by applications
     - Action: schedule deletion (7-30 day recovery window)

  2. Reduce API call costs:
     - Implement client-side caching (reduces calls by 95%+)
     - Use BatchGetSecretValue (retrieve up to 20 secrets per call)
     - Cache TTL: 300s default, adjust per secret sensitivity

  3. Right-size encryption:
     - Use aws/secretsmanager managed key (free) unless cross-account needed
     - Consolidate CMKs: one per account/region for Secrets Manager (not one per secret)

  4. Tag for cost allocation:
     - Required tags: Environment, Application, Team, CostCenter
     - Use cost allocation tags in Cost Explorer for chargeback

  5. Consider Parameter Store for non-rotating values:
     - Migrate static configuration from Secrets Manager to Parameter Store (free tier)
     - Keep only actual credentials in Secrets Manager

  Pricing Summary (as of 2024):
  - $0.40 per secret per month (prorated hourly)
  - $0.05 per 10,000 API calls
  - Lambda rotation: standard Lambda pricing
  - KMS: free (managed key) or $1/month (CMK) + $0.03/10K requests
  ```
- Cost Profile: Low management cost — primary expense is secret count × $0.40/month. API costs negligible with caching.
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html

---

## Reference Architectures

**Production Web Application with Rotating Database Credentials**
- Context: Three-tier web application (ALB → ECS Fargate → Aurora PostgreSQL) with automatic credential rotation
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Secrets Storage | AWS Secrets Manager | Store Aurora credentials with rotation |
  | Encryption | AWS KMS (CMK) | Encrypt secrets for cross-account audit |
  | Rotation | Managed Rotation (Aurora-native) | Rotate master password without Lambda |
  | Retrieval (ECS) | ECS Task Definition secrets field | Inject credential at container start |
  | Caching | Secrets Manager caching library (in app) | Reduce API calls, handle rotation refresh |
  | Network | VPC Endpoint (PrivateLink) | Private access from ECS tasks to Secrets Manager |
  | Monitoring | CloudWatch + EventBridge + Config | Rotation monitoring, compliance checks |
  | DR | Multi-Region Replication | Secret availability in DR region |

- Key Decisions:
  - Use managed rotation (Aurora supports it natively) — eliminates Lambda management
  - ECS secrets field injects at task start; application caching library handles refresh during rotation
  - CMK encryption enables future cross-account access if organization grows
  - VPC endpoint in ECS VPC — tasks in private subnets access Secrets Manager without NAT
- Scaling Path:
  - Single region → multi-region replication for DR
  - Single account → cross-account access via resource policies
  - Master password rotation → per-application-user rotation (Lambda-based)
  - Manual secret creation → IaC (CloudFormation/Terraform) with dynamic references
- Cost Baseline: ~$5-10/month for 10 secrets with rotation (secrets + API calls + minimal KMS)
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html

---

**Multi-Account Secrets Hub with Centralized Management**
- Context: AWS Organizations with 10+ accounts, centralized security account managing shared credentials
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Central Secrets Account | AWS Secrets Manager | Store and manage all shared secrets |
  | Encryption | AWS KMS (CMK per classification) | Separate keys for high/medium/low classification |
  | Access Control | Resource Policies + IAM Cross-Account Roles | Grant spoke account access to specific secrets |
  | Governance | AWS Organizations SCPs | Prevent spoke accounts from creating unmanaged secrets |
  | Audit | CloudTrail (Organization Trail) | Centralized logging of all secret access |
  | Compliance | AWS Config (Organization Rules) | Enforce rotation, unused detection across all accounts |
  | DR | Multi-Region Replication | Replicate critical secrets to DR region |

- Key Decisions:
  - Centralized vs distributed: centralize shared secrets (API keys, shared DB creds), let workload accounts manage app-specific secrets
  - CMK per classification level: high-security secrets get a separate key with stricter policy
  - SCPs prevent spoke accounts from `secretsmanager:CreateSecret` for regulated credential types
  - Resource policies on each secret explicitly name allowed spoke account roles
- Scaling Path:
  - 10 accounts → 100+ accounts: use ABAC (tag-based) instead of explicit ARNs in policies
  - Manual resource policies → automated via CloudFormation StackSets
  - Single region → multi-region for global workloads
- Cost Baseline: ~$50-100/month for 100 secrets with rotation + cross-account KMS operations
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/auth-and-access_examples_cross.html

---

## Service Equivalence Map

| Category | AWS | Google Cloud | Azure | Oracle Cloud (OCI) |
|----------|-----|-------------|-------|--------------------|
| **Secrets Management** | Secrets Manager | Secret Manager | Key Vault (Secrets) | OCI Vault (Secrets) |
| **Configuration** | Systems Manager Parameter Store | Runtime Configurator / Secret Manager | App Configuration | OCI Resource Manager |
| **Key Management** | KMS | Cloud KMS | Key Vault (Keys) | OCI Vault (Keys) |
| **Certificate Management** | Certificate Manager (ACM) | Certificate Manager | Key Vault (Certificates) | Certificates Service |
| **Rotation** | Native (managed + Lambda) | None (manual or external) | Key Vault Rotation Policy (limited) | None (manual) |
| **Cross-Account Sharing** | Resource Policies + CMK | IAM + Organization Policies | RBAC + Private Endpoints | Compartment Policies |
| **Multi-Region Replication** | Native (ReplicateSecretToRegions) | Automatic (global resource) | None (manual sync) | Cross-region not native |
| **Audit** | CloudTrail + Config | Audit Logs | Azure Monitor + Diagnostic Logs | Audit Service |
| **Client Caching** | Language-specific libraries + Agent | Language SDKs (no dedicated caching) | SDK (no dedicated caching) | SDK (no dedicated caching) |

> **⚠️ Important**: Azure Key Vault is a unified service for secrets, keys, and certificates. AWS separates these into Secrets Manager + KMS + ACM. GCP Secret Manager is secrets-only (like AWS). OCI Vault combines secrets and keys. Feature parity varies significantly — especially for rotation automation (AWS leads).

---

## Provider Differentiators

**Managed Rotation Without Lambda**
- Category: Security
- Unique Value: AWS Secrets Manager offers fully managed rotation for RDS, Aurora, Redshift, and DocumentDB database credentials without requiring a customer-managed Lambda function. The database service itself handles credential rotation internally.
- Architecture Impact: Eliminates VPC networking complexity for rotation functions, removes Lambda cold start concerns during rotation, reduces operational surface area. No rotation function code to maintain or debug.
- When to Leverage: Any workload using supported AWS managed databases — this is the default recommendation over Lambda rotation for supported services.
- Caveat: Only available for specific AWS database services. Custom databases, third-party APIs, and non-AWS resources still require Lambda rotation.
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotate-secrets_managed.html

**Secrets Manager Agent (Cross-Compute Caching Daemon)**
- Category: Security
- Unique Value: Language-agnostic local HTTP daemon that standardizes secret retrieval and caching across ALL AWS compute environments (Lambda, ECS, EKS, EC2) via a single interface (localhost:2773). No per-language caching library needed.
- Architecture Impact: Enables polyglot microservice architectures to standardize secret access without per-language dependencies. Sidecar pattern in EKS/ECS simplifies pod/task definitions.
- When to Leverage: Teams running multiple programming languages, organizations standardizing on sidecar patterns, environments where adding per-language SDK dependencies is undesirable.
- Caveat: Additional process to manage (daemon lifecycle); port 2773 must be available; adds a hop (localhost HTTP) compared to direct SDK calls.
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/secrets-manager-agent.html

**Native Multi-Region Replication**
- Category: Security / Reliability
- Unique Value: Built-in asynchronous replication of secrets to multiple AWS Regions with automatic synchronization. Replica secrets use region-local KMS keys and can be promoted to standalone during DR. No external tooling or custom sync logic needed.
- Architecture Impact: Enables true multi-region DR for secret-dependent workloads without manual credential distribution. Applications in DR region can retrieve secrets locally with low latency.
- When to Leverage: Active-passive or active-active multi-region architectures; workloads requiring <1 minute RTO for secret availability.
- Caveat: Replication is async (seconds to minutes lag); replicas are read-only; rotation happens only on primary; promoting a replica is a destructive operation (breaks replication link).
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/replicate-secrets.html

---

## Scenario Coverage

**Standard Case**: Web application with RDS database credentials requiring rotation
- Approach:
  - Store DB credentials in Secrets Manager with JSON structure (host, port, username, password, engine, dbname)
  - Enable managed rotation (Aurora/RDS native) with 24-hour schedule
  - Application uses client-side caching library with 300s TTL
  - ECS tasks inject secrets via task definition secrets field
  - VPC endpoint for Secrets Manager in application VPC
  - CloudWatch alarm on RotationFailed metric
- Key Decisions:
  - Rotation strategy: managed rotation (simplest for RDS/Aurora)
  - Encryption: AWS managed key (single account, no cross-account need)
  - Retrieval: caching library (single-language app) or Agent (polyglot)

**Edge Case**: Cross-account access with regulatory audit requirements and multi-region DR
- Approach:
  - Customer Managed KMS key (mandatory for cross-account)
  - Resource policy granting specific cross-account roles GetSecretValue
  - KMS key policy with kms:ViaService condition
  - Multi-region replication to DR region
  - Organization CloudTrail for unified audit
  - AWS Config organizational rules for compliance
  - Separate CMK per classification level (PII vs non-PII)
- Key Decisions:
  - Must use CMK (AWS managed key cannot be accessed cross-account)
  - Must define key policy carefully (key + identity + resource policy all evaluated)
  - Must test failover procedure (replica promotion)

**Anti-Pattern Case**: Team wants to store secrets in SSM Parameter Store "to save money" for production database credentials
- Clarification: "Does this credential require automatic rotation? Is there a compliance mandate for rotation frequency? Will this credential need cross-account access in the future?"
  - If rotation is required → must use Secrets Manager (Parameter Store has no native rotation)
  - If compliance mandates rotation every N days → Secrets Manager
  - If cross-account access needed → Secrets Manager (resource policies)
  - If truly static configuration (non-credential, no rotation) → Parameter Store is appropriate
  - Cost difference: $0.40/secret/month is the cost of NOT building custom rotation infrastructure
