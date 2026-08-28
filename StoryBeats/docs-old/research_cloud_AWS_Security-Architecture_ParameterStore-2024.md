# AWS Systems Manager Parameter Store — Security Architecture Knowledge Base

---

## Metadata

```yaml
Full_Name: "AWS Security Architecture — Systems Manager Parameter Store"
Cloud_Provider: "AWS"
Architecture_Domain: "Security Architecture — Configuration Management & Parameter Lifecycle"
Target_Edition: "AWS Systems Manager Parameter Store 2024–2025"
Architecture_Context: "Applications requiring centralized configuration management, hierarchical parameter organization, SecureString encryption via KMS, cross-account parameter sharing, and integration with compute services (Lambda, ECS, EKS, EC2, CloudFormation)"
Official_Source_URL: "https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-05-28"
Currency_Threshold: "2027-05-28 — review required after this date due to service feature velocity"
```

---

## Executive Summary

AWS Systems Manager Parameter Store is a fully managed, hierarchical configuration data store that enables secure storage, organization, and retrieval of configuration data at scale. It is designed for managing non-secret configuration values (database connection strings, application settings, resource identifiers, service endpoints) as well as lightweight encrypted values via the `SecureString` parameter type. Parameter Store integrates natively with AWS services including Lambda, EC2, ECS, Fargate, CloudFormation, CDK, CodeBuild, and AppConfig — enabling dynamic configuration updates without code changes or redeployments.

The 2024–2025 edition introduced **cross-account parameter sharing** for advanced parameters via AWS Resource Access Manager (RAM), enabling centralized configuration management across AWS Organizations. **Public parameters** were expanded with new service paths for AMI references, EKS, ECS, and other AWS service metadata. The **AWS Parameters and Secrets Lambda Extension** was updated (v86+ for x86, v86+ for ARM64 as of May 2026) with improved caching, localhost HTTP retrieval on port 2773, and support for both Parameter Store and Secrets Manager. **Parameter policies** (Expiration, ExpirationNotification, NoChangeNotification) provide lifecycle governance for advanced parameters, with EventBridge integration for automated notifications and remediation workflows.

The three most critical architecture guardrails for Parameter Store deployments are: (1) **always use `SecureString` type with customer-managed KMS keys for any sensitive configuration data** — `String` and `StringList` types store values in plaintext, visible in CloudTrail logs and API responses; (2) **implement hierarchical naming conventions aligned with environment, application, and component boundaries** — this enables path-based IAM policies, bulk retrieval via `GetParametersByPath`, and governance at scale; (3) **use Parameter Store for configuration data and AWS Secrets Manager for credentials requiring rotation** — Parameter Store does NOT provide automatic credential rotation, and mixing concerns leads to security gaps and operational confusion.

---

## Cloud Architecture Glossary

```
Term: Parameter
Definition: A named resource in Parameter Store consisting of a name (path), type (String | StringList | SecureString), value (up to 4 KB standard / 8 KB advanced), version history (up to 100 versions), optional description, tags, allowed pattern, data type, and tier designation. Parameters are regional resources identified by ARN: arn:aws:ssm:<region>:<account-id>:parameter/<name>.
Provider Docs Section: https://docs.aws.amazon.com/systems-manager/latest/userguide/what-is-a-parameter.html
Architect Usage: Model each distinct configuration value as a separate parameter. Use hierarchical names for grouping. Choose the correct type based on sensitivity requirements.
Common Confusion: A parameter is NOT a secret — it is a configuration value. While SecureString parameters provide encryption, Parameter Store lacks automatic rotation, cross-account sharing audit trails, and secret lifecycle management that Secrets Manager provides.

Term: Parameter Type — String
Definition: A parameter whose value is stored as a plaintext block of text (up to 4 KB standard / 8 KB advanced). Supports any text content. When data type is set to aws:ec2:image, Parameter Store validates the value is a valid AMI ID format.
Provider Docs Section: https://docs.aws.amazon.com/systems-manager/latest/userguide/what-is-a-parameter.html
Architect Usage: Use for non-sensitive configuration: endpoint URLs, resource names, feature configuration, environment identifiers. Value is visible in CloudTrail logs and API responses.
Common Confusion: String parameters are NOT encrypted in any way. The value appears in plaintext in CloudTrail, CLI output, and console. Never store passwords, API keys, or tokens as String type.

Term: Parameter Type — StringList
Definition: A parameter whose value is stored as a comma-separated list of plaintext values. Individual items cannot contain commas. Values are treated as a single string with comma delimiters by Parameter Store — parsing into individual items is the consumer's responsibility.
Provider Docs Section: https://docs.aws.amazon.com/systems-manager/latest/userguide/what-is-a-parameter.html
Architect Usage: Use for lists of non-sensitive values: allowed IP ranges, feature flags lists, environment tags, server lists. Retrieve as single string and split by comma in application code.
Common Confusion: StringList is NOT a native array — it is a string with commas. There is no array indexing or item-level access. If items contain commas, use JSON in a String parameter instead.

Term: Parameter Type — SecureString
Definition: A parameter whose value is encrypted at rest using an AWS KMS key (symmetric encryption only). Only the value is encrypted — parameter name, description, tags, and other metadata remain in plaintext. Decryption requires explicit --with-decryption flag on retrieval and kms:Decrypt permission on the KMS key.
Provider Docs Section: https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-paramstore-securestring.html
Architect Usage: Use for any sensitive configuration that does NOT require automatic rotation: license keys, lightweight secrets, encrypted configuration data, connection strings containing credentials. Prefer customer-managed KMS keys for fine-grained access control.
Common Confusion: SecureString does NOT provide automatic rotation (use Secrets Manager for that). The AWS-managed key (alias/aws/ssm) grants decrypt access to ALL IAM principals in the account — use customer-managed keys for access segregation.

Term: Parameter Hierarchy
Definition: A naming structure using forward slashes (/) to create hierarchical paths for parameters, with a maximum of 15 levels. Hierarchies enable path-based IAM policies, bulk retrieval via GetParametersByPath, and logical organization by environment/application/component.
Provider Docs Section: https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-paramstore-hierarchies.html
Architect Usage: Design hierarchies reflecting organizational structure: /{environment}/{application}/{component}/{parameter-name}. Use GetParametersByPath for bulk retrieval of entire application configurations. Apply IAM policies at path level.
Common Confusion: If a user has access to path /a, they can recursively access all sub-paths (/a/b, /a/b/c). IAM deny on /a/b does NOT prevent access via GetParametersByPath on /a with --recursive. Design hierarchies with this access model in mind.

Term: Parameter Tier — Standard
Definition: The default tier for parameters. Supports up to 10,000 parameters per AWS account and Region, values up to 4 KB, no parameter policies, no cross-account sharing. No additional charge beyond KMS usage for SecureString types.
Provider Docs Section: https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-advanced-parameters.html
Architect Usage: Use for most workloads. Sufficient for typical application configuration. Upgrade to advanced only when you need policies, larger values, higher parameter counts, or cross-account sharing.
Common Confusion: You can upgrade standard to advanced, but you CANNOT downgrade advanced back to standard. This is a one-way operation per parameter.

Term: Parameter Tier — Advanced
Definition: A higher tier supporting up to 100,000 parameters per account and Region, values up to 8 KB, parameter policies (Expiration, ExpirationNotification, NoChangeNotification), and cross-account sharing via AWS RAM. Incurs additional charges per advanced parameter per month.
Provider Docs Section: https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-advanced-parameters.html
Architect Usage: Use when you need parameter policies for lifecycle governance, larger values (4–8 KB), higher parameter counts (>10,000), or cross-account sharing. Evaluate cost impact — charges apply per advanced parameter.
Common Confusion: Advanced tier is NOT required for SecureString encryption — standard tier supports SecureString. Advanced tier adds policies and higher limits, not security features.

Term: Parameter Policy
Definition: A JSON-defined lifecycle policy attached to an advanced parameter that automates expiration, deletion notifications, or no-change notifications via Amazon EventBridge. Supports three policy types: Expiration (auto-delete at timestamp), ExpirationNotification (EventBridge event before expiration), and NoChangeNotification (EventBridge event if parameter unchanged for specified period).
Provider Docs Section: https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-policies.html
Architect Usage: Use NoChangeNotification to detect stale configuration that may indicate missed credential rotations. Use Expiration for temporary parameters (feature branch configs, temporary access tokens). Combine with EventBridge rules for automated remediation.
Common Confusion: Parameter policies use asynchronous, periodic scans — they do NOT execute at the exact timestamp. Expect up to several hours of delay between policy trigger time and actual execution.

Term: Parameter Version
Definition: An immutable historical record of a parameter's value at a point in time. Parameter Store retains up to 100 versions per parameter. Each version has a unique integer version number (incrementing from 1). Versions can be referenced explicitly in retrieval calls.
Provider Docs Section: https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-paramstore-versions.html
Architect Usage: Use version pinning in CloudFormation dynamic references for immutable deployments: {{resolve:ssm:/app/config:3}}. Use parameter history for audit trails and rollback scenarios. Latest version is returned by default when no version is specified.
Common Confusion: Parameter Store does NOT support staging labels (AWSCURRENT/AWSPREVIOUS) like Secrets Manager. Versions are integer-indexed only. Deleting a parameter deletes ALL versions permanently.

Term: Public Parameter
Definition: A read-only parameter published by AWS services or third parties under the /aws/service/ namespace. Provides service metadata such as latest AMI IDs, ECS-optimized AMI paths, EKS AMI versions, and regional service information. Public parameters are free to read and updated automatically by the owning service.
Provider Docs Section: https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-finding-public-parameters.html
Architect Usage: Reference public parameters for AMI IDs in launch templates and CloudFormation to always use latest patched images. Use /aws/service/global-infrastructure/ for region and AZ discovery. Eliminates manual AMI tracking.
Common Confusion: Public parameters are NOT available in all Regions for all services. Verify availability per Region before architecting dependencies. Public parameters use the standard /aws/service/ prefix — you cannot create parameters under this namespace.

Term: AWS Parameters and Secrets Lambda Extension
Definition: A Lambda layer that provides a local HTTP cache (localhost:2773) for retrieving parameters and secrets without requiring AWS SDK calls in application code. Supports both Parameter Store and Secrets Manager. Caches values with configurable TTL (default 300s, max 300s). Uses the Lambda function's execution role for authentication.
Provider Docs Section: https://docs.aws.amazon.com/systems-manager/latest/userguide/ps-integration-lambda-extensions.html
Architect Usage: Add as a Lambda layer to eliminate SDK dependencies for parameter retrieval. Reduces API calls (cost), improves latency (cached reads), and standardizes retrieval pattern. Requires X-Aws-Parameters-Secrets-Token header (set to AWS_SESSION_TOKEN).
Common Confusion: The extension can only be invoked during the INVOKE phase, NOT during INIT. The extension does NOT detect parameter changes before TTL expires — if you update a parameter, cached values remain stale until TTL expiration.

Term: Allowed Pattern
Definition: A regular expression constraint applied to a parameter that validates values on write (PutParameter). If the new value does not match the regex pattern, the write is rejected with ParameterPatternMismatchException.
Provider Docs Section: https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-paramstore-hierarchies.html
Architect Usage: Use allowed patterns to enforce data formats at write time: IP addresses, port ranges, ARN formats, environment names. Provides a guardrail against misconfiguration at the API layer.
Common Confusion: Allowed patterns are evaluated only on write — they do NOT retroactively validate existing values if the pattern is changed. Changing the pattern on an existing parameter does not trigger re-validation of the current value.

Term: Parameter Store Throughput
Definition: The rate of API transactions per second (TPS) that Parameter Store can process for GetParameter, GetParameters, and PutParameter in an account and Region. Default throughput is suitable for low-to-moderate workloads. Higher throughput can be enabled for additional cost to support high-frequency access patterns.
Provider Docs Section: https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-throughput.html
Architect Usage: Monitor for ThrottlingException errors. Enable higher throughput proactively for applications with concurrent parameter reads at scale. Throughput is independent of parameter tier — both standard and advanced parameters share the same TPS quota.
Common Confusion: Throughput is an account+Region setting, not per-parameter. A single high-volume parameter path can exhaust the quota for all parameters in that account and Region.

Term: Cross-Account Parameter Sharing
Definition: The ability to share advanced parameters with other AWS accounts using AWS Resource Access Manager (RAM). Shared parameters are read-only to consuming accounts. Only advanced-tier parameters can be shared. The owning account maintains full control.
Provider Docs Section: https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-shared-parameters.html
Architect Usage: Use for centralizing configuration in a shared-services account and distributing to workload accounts. Ideal for organization-wide settings (VPC CIDR blocks, common endpoint URLs, shared resource ARNs).
Common Confusion: Cross-account sharing requires advanced tier — standard parameters cannot be shared. Shared parameters are read-only to consumers; they cannot be modified from the consuming account.
```

---

## Architecture Guardrails

### ✅ Mandatory Patterns

**1. Use SecureString with Customer-Managed KMS Keys for Sensitive Data**
- Pillar Alignment: Security
- Why: String and StringList parameter values are stored and transmitted in plaintext — visible in CloudTrail logs, CLI output, API responses, and console. The AWS-managed key (alias/aws/ssm) grants decrypt access to ALL IAM principals in the account, providing no access segregation. AWS Well-Architected Security Pillar SEC07-BP01 mandates classification and encryption of sensitive data with appropriate key management.
- AWS Services: AWS Systems Manager Parameter Store (SecureString), AWS KMS (customer-managed keys), AWS IAM
- Architecture Decision:
  ```
  - ALL sensitive configuration values MUST use SecureString type
  - Create dedicated customer-managed KMS keys per application or security domain
  - Grant kms:Decrypt only to roles that need to read specific parameters
  - Grant kms:Encrypt and kms:GenerateDataKey only to roles that create/update parameters
  - Use separate KMS keys for different environments (dev/staging/prod)
  - Key policy must restrict access to specific IAM roles — not broad account-level access
  - Enable KMS key rotation (annual automatic rotation for symmetric keys)
  ```
- Verification:
  ```bash
  # Find parameters NOT using SecureString (potential misclassification)
  aws ssm describe-parameters \
    --parameter-filters "Key=Type,Values=String,StringList" \
    --query 'Parameters[*].[Name,Type]' --output table

  # Verify SecureString parameters use customer-managed keys (not aws/ssm)
  aws ssm describe-parameters \
    --parameter-filters "Key=Type,Values=SecureString" \
    --query 'Parameters[*].[Name,KeyId]' --output table

  # Verify KMS key is customer-managed (not AWS-managed)
  aws kms describe-key --key-id alias/aws/ssm \
    --query 'KeyMetadata.KeyManager'
  # Should return "AWS" — your parameters should NOT use this key
  ```
- Trade-offs: Customer-managed KMS keys add cost ($1/month per key + API call charges); requires explicit kms:Decrypt in IAM policies for consumers; adds complexity to cross-account scenarios (key policy must grant cross-account access)
- Source: https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-paramstore-securestring.html

---

**2. Implement Hierarchical Naming Conventions with Path-Based IAM Policies**
- Pillar Alignment: Security, Operational Excellence
- Why: Flat parameter naming creates ungovernable configuration sprawl. Without hierarchical structure, IAM policies require individual parameter ARNs, bulk retrieval is impossible, and environment isolation cannot be enforced at the API layer. AWS Well-Architected Operational Excellence Pillar OPS06-BP01 mandates organized, discoverable configuration.
- AWS Services: AWS Systems Manager Parameter Store (hierarchies, GetParametersByPath), AWS IAM (resource-based policies with wildcards)
- Architecture Decision:
  ```
  - Naming convention: /{environment}/{application}/{component}/{parameter-name}
    Example: /prod/payments-api/database/connection-string
    Example: /staging/auth-service/oauth/client-id
  - Maximum 15 levels of hierarchy — design for 3-5 levels typically
  - IAM policies use path-based resources:
    arn:aws:ssm:<region>:<account>:parameter/prod/payments-api/*
  - Use GetParametersByPath for bulk retrieval of all application config
  - Reserve top-level paths for environments: /prod/, /staging/, /dev/, /shared/
  - Use /shared/ prefix for cross-application parameters (VPC IDs, common endpoints)
  - Document naming convention in architecture decision record (ADR)
  ```
- Verification:
  ```bash
  # List all root-level parameters (should be none — all should be hierarchical)
  aws ssm describe-parameters \
    --parameter-filters "Key=Name,Option=Equals,Values=*" \
    --query 'Parameters[?!contains(Name, `/`)].Name'

  # Verify IAM policies use path-based restrictions (manual review)
  aws iam get-policy-version --policy-arn <policy-arn> --version-id v1

  # Retrieve all parameters for a specific application path
  aws ssm get-parameters-by-path --path "/prod/payments-api/" --recursive
  ```
- Trade-offs: Requires organizational agreement on naming standards upfront; hierarchy changes require parameter recreation (names are immutable); path-based access means granting /a also grants /a/b/c recursively
- Source: https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-paramstore-hierarchies.html

---

**3. Use Parameter Store for Configuration — Secrets Manager for Rotating Credentials**
- Pillar Alignment: Security, Operational Excellence
- Why: Parameter Store does NOT provide automatic credential rotation, managed rotation functions, or rotation scheduling. Storing rotating credentials in Parameter Store creates operational risk — credentials go stale without automated renewal. AWS explicitly recommends Secrets Manager for credentials requiring rotation, cross-account access, or fine-grained audit logging.
- AWS Services: AWS Systems Manager Parameter Store, AWS Secrets Manager, AWS Lambda (for custom rotation)
- Architecture Decision:
  ```
  Parameter Store is correct for:
  - Database connection strings (non-rotating components: host, port, dbname)
  - Application environment settings (LOG_LEVEL, ENV, FEATURE_FLAGS)
  - Service endpoint URLs (internal service discovery, third-party base URLs)
  - Resource identifiers (S3 bucket names, DynamoDB table names, ARNs)
  - Application tuning parameters (cache TTLs, batch sizes, timeouts)
  - License keys and non-rotating API tokens

  Secrets Manager is correct for:
  - Database credentials (username/password requiring rotation)
  - API keys requiring automatic rotation
  - OAuth client secrets
  - Third-party service credentials
  - Any credential with a defined rotation policy

  DO NOT use Parameter Store for:
  - Feature flags (use AWS AppConfig)
  - Dynamic configuration with gradual rollout (use AWS AppConfig)
  - Circuit breakers and operational levers (use AWS AppConfig)
  ```
- Verification:
  ```bash
  # Audit SecureString parameters for potential misplaced credentials
  aws ssm describe-parameters \
    --parameter-filters "Key=Type,Values=SecureString" \
    --query 'Parameters[*].Name' --output text

  # Check for parameter names suggesting credentials (manual review)
  # Names containing: password, secret, key, token, credential
  aws ssm describe-parameters \
    --parameter-filters "Key=Name,Option=Contains,Values=password" \
    --query 'Parameters[*].[Name,Type]' --output table
  ```
- Trade-offs: Using two services (Parameter Store + Secrets Manager) adds architectural complexity; developers must know which service to query; unified retrieval via Lambda Extension mitigates this (both accessible on localhost:2773)
- Source: https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html

---

**4. Enable Parameter Policies for Lifecycle Governance**
- Pillar Alignment: Security, Operational Excellence
- Why: Parameters without lifecycle governance accumulate indefinitely — stale configuration, forgotten temporary parameters, and unchanged credentials that should have been rotated create security drift. Parameter policies enforce automated governance via EventBridge notifications and expiration. AWS Well-Architected Security Pillar SEC02-BP04 mandates credential lifecycle management.
- AWS Services: AWS Systems Manager Parameter Store (advanced tier, parameter policies), Amazon EventBridge, AWS Lambda (remediation)
- Architecture Decision:
  ```
  - Apply NoChangeNotification policy to SecureString parameters:
    Alert if parameter unchanged for 90 days (indicates potential missed rotation)
  - Apply Expiration policy to temporary/time-bound parameters:
    Feature branch configs, temporary access grants, limited-time overrides
  - Apply ExpirationNotification 15 days before expiration:
    Gives teams time to renew or clean up
  - Create EventBridge rules to route policy events to:
    - SNS topic for team notification
    - Lambda function for automated remediation or escalation
  - Maximum 10 policies per parameter
  ```
- Verification:
  ```bash
  # List advanced parameters and their policies
  aws ssm describe-parameters \
    --parameter-filters "Key=Tier,Values=Advanced" \
    --query 'Parameters[*].[Name,Policies]' --output json

  # Verify EventBridge rules exist for parameter policy events
  aws events list-rules \
    --name-prefix "ssm-parameter-policy" \
    --query 'Rules[*].[Name,State]'
  ```
- Trade-offs: Requires advanced tier (additional cost per parameter); policies use asynchronous scans (not real-time enforcement — can have hours of delay); policy events require EventBridge rule configuration for action
- Source: https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-policies.html

---

**5. Use the AWS Parameters and Secrets Lambda Extension for Cached Retrieval**
- Pillar Alignment: Performance Efficiency, Cost Optimization
- Why: Direct SDK calls to Parameter Store on every Lambda invocation create unnecessary API call volume (cost), add latency, and risk throttling under concurrent load. The Lambda Extension provides local caching (TTL-based), reduces API calls by orders of magnitude, eliminates SDK dependency, and standardizes retrieval across runtimes.
- AWS Services: AWS Lambda (layer), AWS Parameters and Secrets Lambda Extension, AWS Systems Manager Parameter Store
- Architecture Decision:
  ```
  - Add extension as Lambda layer (region-specific ARN)
  - Retrieve extension ARN dynamically via public parameter:
    /aws/service/aws-parameters-and-secrets-lambda-extension/x86/latest
    /aws/service/aws-parameters-and-secrets-lambda-extension/arm64/latest
  - Configure environment variables:
    SSM_PARAMETER_STORE_TTL: 300 (default, seconds — adjust based on change frequency)
    PARAMETERS_SECRETS_EXTENSION_CACHE_SIZE: 1000 (default items)
    PARAMETERS_SECRETS_EXTENSION_LOG_LEVEL: INFO (use DEBUG for troubleshooting)
  - Retrieve parameters via HTTP GET to localhost:2773:
    GET http://localhost:2773/systemsmanager/parameters/get?name=%2Fapp%2Fconfig
  - Include header: X-Aws-Parameters-Secrets-Token: ${AWS_SESSION_TOKEN}
  - For SecureString: append &withDecryption=true
  - Lambda execution role must have: ssm:GetParameter, kms:Decrypt (for SecureString)
  ```
- Verification:
  ```bash
  # Verify Lambda function has extension layer attached
  aws lambda get-function-configuration --function-name <function> \
    --query 'Layers[*].Arn' --output table

  # Verify extension ARN is current version
  aws ssm get-parameter \
    --name "/aws/service/aws-parameters-and-secrets-lambda-extension/x86/latest" \
    --query "Parameter.Value" --output text

  # Check CloudWatch Logs for extension activity (set LOG_LEVEL=DEBUG)
  ```
- Trade-offs: Extension adds ~50ms to Lambda cold start; cached values may be stale during TTL window (reduce TTL for frequently changing parameters, increase for stable config); extension cannot be invoked during INIT phase
- Source: https://docs.aws.amazon.com/systems-manager/latest/userguide/ps-integration-lambda-extensions.html

---

### ⚠️ Architectural Decisions

**Parameter Store vs. Secrets Manager**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|------------|-----------|------------|-----------|
  | Parameter Store (String/StringList) | SSM Parameter Store | Cost (free for standard tier), simplicity, CloudFormation integration | Encryption, audit granularity | Non-sensitive config: endpoints, resource IDs, settings |
  | Parameter Store (SecureString) | SSM Parameter Store + KMS | Cost (cheaper than Secrets Manager), hierarchical organization | Automatic rotation, cross-account audit, managed rotation | Lightweight secrets not requiring rotation: license keys, static API tokens |
  | Secrets Manager | AWS Secrets Manager | Automatic rotation, fine-grained audit, cross-account access, managed rotation for RDS/Aurora | Cost ($0.40/secret/month + API calls), no hierarchy | Database credentials, rotating API keys, OAuth secrets, any credential with lifecycle |

- Cost Profile: Parameter Store standard tier is free (only KMS charges for SecureString). Advanced tier charges per parameter/month. Secrets Manager charges $0.40/secret/month + $0.05/10,000 API calls.
- Lock-in Assessment: Both services are AWS-specific. Parameter Store references ({{resolve:ssm:}}) are embedded in CloudFormation templates. Secrets Manager ARN references create similar coupling. Abstraction layer (environment variables injected at deployment) reduces lock-in.
- Architect Instruction: "Ask 'Does this credential require automatic rotation or will it be manually rotated on a defined schedule?' when determining storage service"
- Source: https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html

---

**Parameter Store vs. AppConfig for Dynamic Configuration**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|------------|-----------|------------|-----------|
  | Parameter Store | SSM Parameter Store | Simplicity, cost, IaC integration | Safe deployment, validation, rollback | Static configuration that changes infrequently (deploy-time values) |
  | AppConfig | AWS AppConfig | Safe deployment (gradual rollout), validation, automatic rollback on CloudWatch alarm | Simplicity (more setup required) | Feature flags, circuit breakers, dynamic config requiring runtime changes without deploy |

- Cost Profile: Parameter Store is free (standard) or low-cost (advanced). AppConfig charges for configuration retrievals beyond the free tier.
- Lock-in Assessment: AppConfig provides a deployment-safe abstraction over Parameter Store — it can use Parameter Store as a configuration source. This layered approach provides the benefits of both.
- Architect Instruction: "Ask 'Does this configuration change at runtime without a deployment, and does it need gradual rollout with automatic rollback?' when choosing between Parameter Store and AppConfig"
- Source: https://docs.aws.amazon.com/appconfig/latest/userguide/what-is-appconfig.html

---

**Standard vs. Advanced Parameter Tier**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|------------|-----------|------------|-----------|
  | Standard Tier | SSM Parameter Store | Cost (free), simplicity | Policies, sharing, higher limits | <10,000 params, values <4KB, no lifecycle policies needed |
  | Advanced Tier | SSM Parameter Store | Policies, cross-account sharing, 100K limit, 8KB values | Cost ($0.05/advanced parameter/month) | Need parameter policies, cross-account sharing, >10K params, or values >4KB |

- Cost Profile: Standard is free. Advanced is $0.05/advanced parameter/month. Upgrade is one-way (cannot downgrade).
- Lock-in Assessment: Tier decision is irreversible per parameter. Plan tier requirements before creation. Can always create a new standard parameter and delete the advanced one, but this resets version history.
- Architect Instruction: "Ask 'Do we need parameter policies, cross-account sharing, or will we exceed 10,000 parameters?' before upgrading to advanced tier — this is a one-way operation"
- Source: https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-advanced-parameters.html

---

**Throughput Configuration**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|------------|-----------|------------|-----------|
  | Default Throughput | SSM Parameter Store | Cost (no charge) | TPS capacity (lower limit) | Low-to-moderate workloads, infrequent parameter retrieval |
  | Higher Throughput | SSM Parameter Store | TPS capacity (higher limit for GetParameter, GetParameters, PutParameter) | Cost (charges apply for higher throughput) | High-concurrency workloads, frequent parameter retrieval at scale, ThrottlingException errors |

- Cost Profile: Default throughput is free. Higher throughput incurs per-account charges. Evaluate against caching strategy — extension caching often eliminates need for higher throughput.
- Lock-in Assessment: Throughput setting is account+Region level, reversible at any time. No lock-in concern.
- Architect Instruction: "Ask 'Are we seeing ThrottlingException errors, and have we already implemented client-side caching via Lambda Extension or SDK caching?' before enabling higher throughput"
- Source: https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-throughput.html

---

### 🚫 Anti-Patterns

**1. Storing Rotating Credentials in Parameter Store**
- Risk Level: HIGH
- Why: Parameter Store has NO automatic rotation capability. Credentials stored as SecureString remain static until manually updated. This violates the Security pillar principle of rotating credentials regularly (SEC02-BP04). Stale credentials have unbounded exposure windows — a compromised credential remains valid indefinitely.
- Instead: Use AWS Secrets Manager for any credential requiring rotation. Secrets Manager provides managed rotation for RDS/Aurora/Redshift/DocumentDB and custom Lambda rotation for other credential types. Minimum rotation interval: 4 hours.
- Detection:
  ```bash
  # Find SecureString parameters that haven't changed in >90 days
  aws ssm describe-parameters \
    --parameter-filters "Key=Type,Values=SecureString" \
    --query 'Parameters[?LastModifiedDate<`2026-02-28`].[Name,LastModifiedDate]' \
    --output table
  # Use NoChangeNotification policy for automated detection
  ```
- Impact: Credential compromise | Extended exposure window | Compliance violation (PCI-DSS requirement 8.2.4, SOC2 CC6.1)
- Source: https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html

---

**2. Using AWS-Managed KMS Key (alias/aws/ssm) for SecureString in Production**
- Risk Level: HIGH
- Why: The AWS-managed key grants kms:Decrypt permission to ALL IAM principals within the AWS account by default. Any IAM user, role, or service with ssm:GetParameter permission can decrypt ANY SecureString parameter using this key. This defeats the purpose of encryption — there is no access segregation between parameters. Violates Security pillar least-privilege principle (SEC03-BP01).
- Instead: Create dedicated customer-managed KMS keys per application or security domain. Grant kms:Decrypt in key policy only to specific IAM roles that need access. Use separate keys for different environments.
- Detection:
  ```bash
  # Find SecureString parameters using the AWS-managed key
  aws ssm describe-parameters \
    --parameter-filters "Key=Type,Values=SecureString" \
    --query 'Parameters[?KeyId==`alias/aws/ssm`].[Name,KeyId]' --output table

  # Or check for parameters without explicit KeyId (defaults to aws/ssm)
  aws ssm describe-parameters \
    --parameter-filters "Key=Type,Values=SecureString" \
    --query 'Parameters[*].[Name,KeyId]' --output table
  ```
- Impact: Data breach | Unauthorized access to sensitive configuration | No access segregation between teams/applications
- Source: https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-paramstore-access.html

---

**3. Flat Parameter Naming Without Hierarchy**
- Risk Level: MEDIUM
- Why: Flat naming (e.g., `db-password`, `api-endpoint`) prevents path-based IAM policies, makes bulk retrieval impossible, creates naming collisions as parameter count grows, and eliminates organizational discoverability. Violates Operational Excellence pillar principle of standardized configuration management (OPS06-BP01).
- Instead: Implement hierarchical naming: `/{env}/{app}/{component}/{param}`. Use GetParametersByPath for bulk retrieval. Apply IAM policies at path level. Document naming convention in ADR.
- Detection:
  ```bash
  # Find root-level parameters (not in a hierarchy)
  aws ssm describe-parameters \
    --query 'Parameters[?!contains(Name, `/`) || starts_with(Name, `/`) && length(split(Name, `/`)) < `4`].Name' \
    --output text
  ```
- Impact: Configuration sprawl | IAM policy complexity | Inability to bulk-retrieve application config | Team confusion
- Source: https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-paramstore-hierarchies.html

---

**4. Hardcoding Parameter Names in Application Code**
- Risk Level: MEDIUM
- Why: Hardcoded parameter paths create tight coupling between application code and infrastructure naming. Environment promotion (dev→staging→prod) requires code changes or complex build-time substitution. Violates 12-Factor App principle III (store config in the environment).
- Instead: Pass parameter paths as environment variables to compute resources. Use a single code path that reads from environment-injected paths: `PARAM_PATH=/prod/myapp/` in production, `/dev/myapp/` in development. Application code reads `GetParametersByPath(os.environ['PARAM_PATH'])`.
- Detection: Code review for hardcoded `/prod/`, `/staging/` paths in application source. Grep for `ssm.get_parameter.*name=.*/(prod|staging|dev)/`.
- Impact: Deployment friction | Environment coupling | Code changes required for configuration path changes
- Source: https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html

---

**5. Ignoring Throughput Limits Without Caching**
- Risk Level: MEDIUM
- Why: Applications making direct API calls on every request (no caching) exhaust Parameter Store TPS quotas rapidly under load. ThrottlingException cascades cause application failures. Default throughput is designed for low-to-moderate workloads — high-concurrency Lambda functions or container fleets exceed limits quickly.
- Instead: Implement caching at the application layer. Use the AWS Parameters and Secrets Lambda Extension (default TTL: 300s) for Lambda. Use SDK caching libraries for ECS/EKS/EC2. Only enable higher throughput after caching is implemented and throttling persists.
- Detection:
  ```bash
  # Check CloudWatch for throttling metrics
  aws cloudwatch get-metric-statistics \
    --namespace "AWS/SSM" \
    --metric-name "ThrottledRequests" \
    --dimensions Name=Service,Value=ParameterStore \
    --start-time $(date -d '-1 hour' --iso-8601=seconds) \
    --end-time $(date --iso-8601=seconds) \
    --period 300 --statistics Sum
  ```
- Impact: Application failures under load | Cascading throttling | Degraded performance
- Source: https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-throughput.html

---

**6. Granting ssm:GetParameter* on Resource "*" in Production**
- Risk Level: CRITICAL
- Why: Wildcard resource permissions allow any IAM principal with this policy to read ALL parameters in the account and Region — including SecureString parameters encrypted with the AWS-managed key. This is equivalent to granting read access to all configuration and lightweight secrets. Violates Security pillar least-privilege principle (SEC03-BP02).
- Instead: Scope ssm:GetParameter* to specific parameter path ARNs: `arn:aws:ssm:<region>:<account>:parameter/prod/myapp/*`. Use separate IAM policies per application/team with path-scoped resources.
- Detection:
  ```bash
  # Audit IAM policies for overly permissive SSM access
  # Use IAM Access Analyzer or manual policy review
  aws iam list-policies --scope Local \
    --query 'Policies[*].Arn' --output text | \
    xargs -I {} aws iam get-policy-version \
      --policy-arn {} --version-id v1 \
      --query 'PolicyVersion.Document'
  # Look for: "Resource": "*" combined with ssm:GetParameter*
  ```
- Impact: Data breach | Unauthorized configuration access | Credential exposure | Compliance violation
- Source: https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-paramstore-access.html

---

## Cloud-Native Design Patterns

**Hierarchical Configuration by Environment Pattern**
- Category: Data
- Problem: Applications require different configuration values per environment (dev/staging/prod) without code changes. Configuration must be isolated between environments while sharing the same retrieval pattern.
- Solution on AWS:
  ```
  Parameter hierarchy design:
    /{environment}/{application}/{component}/{parameter}

  Examples:
    /prod/payments-api/database/host → "prod-db.cluster-xyz.us-east-1.rds.amazonaws.com"
    /staging/payments-api/database/host → "staging-db.cluster-abc.us-east-1.rds.amazonaws.com"
    /dev/payments-api/database/host → "localhost"

  Application retrieves config using environment-injected base path:
    PARAM_BASE_PATH=/prod/payments-api/ (injected via ECS task def, Lambda env var, etc.)
    Application calls: GetParametersByPath(path=PARAM_BASE_PATH, recursive=true)

  IAM policies scope access by environment path:
    Production role: arn:aws:ssm:*:*:parameter/prod/payments-api/*
    Staging role: arn:aws:ssm:*:*:parameter/staging/payments-api/*
  ```
- Services Used: SSM Parameter Store (hierarchies, GetParametersByPath), IAM (path-based policies), ECS/Lambda (environment variable injection)
- When to Apply: Multi-environment deployments; applications promoted through CI/CD pipeline; teams needing environment isolation
- When NOT to Apply: Single-environment applications; configuration that changes at runtime (use AppConfig); credentials requiring rotation (use Secrets Manager)
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Environment Isolation | Path-based IAM prevents cross-environment access | Parameter duplication across environments |
  | Deployment Simplicity | Same code deploys to all environments | Requires environment variable injection mechanism |
  | Discoverability | GetParametersByPath returns entire app config | Naming convention must be documented and enforced |

- Complements: Infrastructure-as-Code (Terraform/CDK creating parameters per environment), CI/CD pipeline (injecting PARAM_BASE_PATH), AppConfig (for runtime dynamic config)
- Source: https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-paramstore-hierarchies.html

---

**Configuration Injection at Deploy-Time Pattern (CloudFormation/CDK)**
- Category: Data
- Problem: Infrastructure-as-Code templates need configuration values that are environment-specific but should not be hardcoded in template source. Template parameters become unwieldy at scale.
- Solution on AWS:
  ```
  CloudFormation dynamic references:
    {{resolve:ssm:/prod/vpc/id}}                    — String parameter (latest version)
    {{resolve:ssm:/prod/vpc/id:3}}                  — String parameter (specific version)
    {{resolve:ssm-secure:/prod/db/password}}        — SecureString parameter (latest)
    {{resolve:ssm-secure:/prod/db/password:2}}      — SecureString (specific version)

  CDK integration:
    StringParameter.valueForStringParameter(this, '/prod/vpc/id')     — resolved at deploy
    StringParameter.valueFromLookup(this, '/prod/vpc/id')             — resolved at synth

  ECS Task Definition (inject as environment variable or secret):
    containerDefinitions:
      - secrets:
          - name: DB_PASSWORD
            valueFrom: arn:aws:ssm:<region>:<account>:parameter/prod/app/db-password

  Lambda environment variable from Parameter Store:
    Environment:
      Variables:
        PARAM_PATH: /prod/myapp/
  ```
- Services Used: SSM Parameter Store, AWS CloudFormation (dynamic references), AWS CDK (StringParameter), Amazon ECS (secrets in task definitions), AWS Lambda (environment variables)
- When to Apply: IaC deployments needing external configuration; multi-stack architectures sharing values; environment-specific deployments from single template
- When NOT to Apply: Configuration that changes between deployments without stack update; secrets requiring rotation (use Secrets Manager dynamic references instead)
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Decoupling | Templates are environment-agnostic | Requires parameters to exist before stack creation |
  | Version Pinning | Specific versions ensure reproducible deploys | Must update version references for new config |
  | Security | ssm-secure references don't expose values in template | SecureString values not visible in stack events (limited debugging) |

- Complements: CI/CD pipeline (creating/updating parameters before deployment), Parameter Store hierarchies, CloudFormation stack sets (multi-account deployment)
- Source: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/dynamic-references-ssm.html

---

**Public Parameters for AMI Management Pattern**
- Category: Scalability
- Problem: Hardcoded AMI IDs in launch templates become stale as AWS releases patched images. Manual AMI tracking is error-prone and delays security patching. Each Region has different AMI IDs for the same image.
- Solution on AWS:
  ```
  Reference AWS-published public parameters for latest AMIs:
    /aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2
    /aws/service/ami-windows-latest/Windows_Server-2022-English-Full-Base
    /aws/service/eks/optimized-ami/<version>/amazon-linux-2/recommended/image_id
    /aws/service/ecs/optimized-ami/amazon-linux-2/recommended/image_id

  CloudFormation usage:
    ImageId: '{{resolve:ssm:/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2}}'

  EC2 Launch Template:
    aws ec2 create-launch-template --launch-template-data \
      '{"ImageId":"resolve:ssm:/aws/service/ami-amazon-linux-latest/..."}'

  Custom golden AMI pattern (organization-managed):
    1. Image Builder creates validated AMI
    2. Pipeline writes AMI ID to /shared/golden-ami/amazon-linux-2/latest
    3. Launch templates reference this parameter
    4. Stack update picks up new AMI automatically
  ```
- Services Used: SSM Parameter Store (public parameters), EC2 (launch templates), CloudFormation (dynamic references), EC2 Image Builder (golden AMI pipeline)
- When to Apply: Auto-scaling groups needing latest patched AMIs; EKS/ECS node groups; any EC2 fleet requiring consistent, up-to-date images
- When NOT to Apply: Immutable infrastructure where AMI pinning is intentional; environments requiring explicit AMI approval before adoption
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Security | Always uses latest patched AMI | May introduce untested changes |
  | Operational Effort | Eliminates manual AMI tracking | Requires trust in AWS patching cadence |
  | Reproducibility | Dynamic reference means current state | Cannot reproduce exact past deployment without version pinning |

- Complements: EC2 Image Builder (golden AMI pipeline), Auto Scaling Groups (instance refresh), Systems Manager Patch Manager
- Source: https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-finding-public-parameters.html

---

**Centralized Configuration with Cross-Account Sharing Pattern**
- Category: Data
- Problem: Multi-account AWS Organizations architectures need shared configuration (VPC CIDR ranges, common endpoints, organization-wide settings) accessible from workload accounts without duplication or synchronization.
- Solution on AWS:
  ```
  Architecture:
    Shared Services Account (owns parameters):
      /shared/networking/vpc-cidr-primary → "10.0.0.0/16"
      /shared/networking/transit-gateway-id → "tgw-abc123"
      /shared/security/waf-web-acl-arn → "arn:aws:wafv2:..."
      /shared/endpoints/internal-api-gateway → "https://api.internal.example.com"

    Share via AWS RAM:
      1. Parameters MUST be advanced tier
      2. Create RAM resource share
      3. Add parameter ARNs to share
      4. Add target accounts or OU
      5. Consumer accounts access via GetParameter (read-only)

    Consumer Account:
      aws ssm get-parameter \
        --name "arn:aws:ssm:us-east-1:111111111111:parameter/shared/networking/vpc-cidr-primary"
  ```
- Services Used: SSM Parameter Store (advanced tier, cross-account sharing), AWS RAM (Resource Access Manager), AWS Organizations
- When to Apply: Multi-account architectures; Landing Zone patterns; shared networking configuration; organization-wide policy parameters
- When NOT to Apply: Single-account architectures; parameters requiring write access from multiple accounts (not supported — read-only sharing); secrets (use Secrets Manager with resource policies for cross-account)
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Centralization | Single source of truth for org-wide config | Single point of failure if shared services account is unavailable |
  | Cost | No parameter duplication across accounts | Requires advanced tier ($0.05/param/month) |
  | Access Control | RAM-based sharing with organizational controls | Read-only — cannot update from consumer account |

- Complements: AWS Organizations (OU-based sharing), Landing Zone architecture, Terraform/CDK cross-account deployments
- Source: https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-shared-parameters.html

---

## Security Architecture

**Identity & Access Management for Parameter Store**
- AWS Services: AWS IAM (policies), AWS KMS (encryption keys), AWS Systems Manager Parameter Store, AWS CloudTrail (audit)
- Architecture:
  ```
  Access Model:
    1. IAM identity policy grants ssm:GetParameter* on specific parameter path ARNs
    2. For SecureString: IAM policy ALSO grants kms:Decrypt on the specific KMS key ARN
    3. For writing: ssm:PutParameter + kms:Encrypt + kms:GenerateDataKey on the KMS key
    4. ssm:DescribeParameters requires Resource: "*" (cannot be scoped to specific parameters)

  Key IAM Actions:
    - ssm:GetParameter — single parameter retrieval
    - ssm:GetParameters — batch retrieval (up to 10 parameters)
    - ssm:GetParametersByPath — hierarchical bulk retrieval
    - ssm:GetParameterHistory — version history access
    - ssm:PutParameter — create or update parameter
    - ssm:DeleteParameter / ssm:DeleteParameters — removal
    - ssm:DescribeParameters — list/search parameters (metadata only)

  Defense in Depth:
    Layer 1: IAM identity policy (attached to role/user)
    Layer 2: KMS key policy (controls decryption access for SecureString)
    Layer 3: Parameter Store tag-based conditions (aws:ResourceTag)
    Layer 4: AWS Organizations SCPs (deny Parameter Store actions at OU level)
    Layer 5: VPC endpoint policies (restrict which parameters can be accessed from VPC)

  Critical Security Note:
    GetParameterHistory returns ALL versions including current value.
    Denying GetParameter/GetParameters but allowing GetParameterHistory
    does NOT prevent access to current parameter values.
  ```
- Compliance Alignment: SOC2 CC6.1 (logical access controls), PCI-DSS 7.1 (restrict access to system components), HIPAA §164.312(a)(1) (access controls)
- Source: https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-paramstore-access.html

---

**Data Encryption Architecture**
- AWS Services: AWS KMS (symmetric encryption), AWS Systems Manager Parameter Store (SecureString), AWS CloudTrail (KMS API audit)
- Architecture:
  ```
  Encryption Model:
    - SecureString values are encrypted using AWS KMS symmetric keys
    - Parameter Store calls KMS GenerateDataKey (envelope encryption pattern implied)
    - Only symmetric KMS keys are supported (asymmetric keys cannot be used)
    - Encryption scope: value only — name, description, tags are plaintext

  KMS Key Options:
    1. AWS-managed key (alias/aws/ssm):
       - Free (no monthly key charge)
       - ALL account principals can decrypt (no access segregation)
       - Cannot customize key policy
       - Suitable only for non-production or low-sensitivity parameters

    2. Customer-managed key:
       - $1/month per key + API call charges
       - Key policy controls exactly who can decrypt
       - Supports key rotation (annual)
       - Enables cross-account access via key policy grants
       - Required for compliance workloads

  Key Management Strategy:
    /prod/app-a/* → CMK: arn:aws:kms:...:key/app-a-prod-key
    /prod/app-b/* → CMK: arn:aws:kms:...:key/app-b-prod-key
    /dev/*        → AWS-managed key (alias/aws/ssm) — acceptable for dev

  CloudTrail Integration:
    - Every GetParameter with --with-decryption generates KMS Decrypt event
    - Every PutParameter for SecureString generates KMS GenerateDataKey event
    - Enables detection of unauthorized decryption attempts
  ```
- Compliance Alignment: SOC2 CC6.7 (encryption of data at rest), PCI-DSS 3.4 (render PAN unreadable), HIPAA §164.312(a)(2)(iv) (encryption and decryption)
- Source: https://docs.aws.amazon.com/kms/latest/developerguide/services-parameter-store.html

---

**Audit & Monitoring Architecture**
- AWS Services: AWS CloudTrail, Amazon EventBridge, Amazon CloudWatch, AWS Config
- Architecture:
  ```
  CloudTrail Events (automatically logged):
    - ssm:PutParameter — who changed what, when
    - ssm:GetParameter / GetParameters / GetParametersByPath — who accessed what
    - ssm:DeleteParameter — who deleted what
    - kms:Decrypt / kms:GenerateDataKey — encryption key usage

  EventBridge Integration:
    - Parameter change events: source = "aws.ssm", detail-type = "Parameter Store Change"
    - Parameter policy events: Expiration, ExpirationNotification, NoChangeNotification
    - Route to: SNS (notification), Lambda (remediation), Step Functions (workflow)

  CloudWatch Metrics:
    - AWS/SSM namespace for API throttling metrics
    - Custom metrics via Lambda for parameter staleness detection

  Monitoring Pattern:
    1. EventBridge rule captures Parameter Store change events
    2. Lambda function validates: was change authorized? Is value format valid?
    3. SNS notification to security team for sensitive parameter changes
    4. CloudTrail Lake for historical query and compliance reporting
  ```
- Compliance Alignment: SOC2 CC7.2 (monitoring activities), PCI-DSS 10.2 (audit trail for access to cardholder data), HIPAA §164.312(b) (audit controls)
- Source: https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-paramstore-cwe.html

---

## Operational Patterns

**Configuration Retrieval at Scale**
- RTO/RPO: N/A (Parameter Store is a regional service with built-in high availability)
- AWS Services: SSM Parameter Store, AWS Parameters and Secrets Lambda Extension, AWS SDK caching libraries
- Cost Profile: Low — standard parameters free; API calls minimal with caching; higher throughput adds cost only if needed
- Automation:
  ```
  Caching Strategy (reduces API calls by ~99%):
    Lambda: AWS Parameters and Secrets Lambda Extension (TTL: 300s default)
    ECS/EKS: Application-level SDK caching (TTL: 300s, refresh on cache miss)
    EC2: Secrets Manager Agent or SDK with custom caching layer

  Retrieval Patterns:
    Single parameter: GetParameter (1 API call)
    Multiple unrelated: GetParameters (1 call, up to 10 parameters)
    Entire application config: GetParametersByPath (paginated, recursive)

  Performance Optimization:
    1. Use GetParametersByPath with --recursive for bulk retrieval at startup
    2. Cache ALL parameters in-memory with TTL-based invalidation
    3. Use Lambda Extension for serverless (eliminates SDK dependency)
    4. Monitor ThrottlingException — enable higher throughput if caching insufficient
  ```
- Source: https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-throughput.html

---

**Parameter Lifecycle Management**
- RTO/RPO: N/A
- AWS Services: SSM Parameter Store (policies), Amazon EventBridge, AWS Lambda, Amazon SNS
- Cost Profile: Low — EventBridge rules free for AWS service events; Lambda invocations minimal
- Automation:
  ```
  Lifecycle Governance (Advanced Tier):
    1. Expiration Policy:
       - Auto-delete temporary parameters at specified timestamp
       - Use for: feature branch configs, temporary overrides, time-limited access
       {"Type":"Expiration","Version":"1.0","Attributes":{"Timestamp":"2026-12-31T00:00:00.000Z"}}

    2. ExpirationNotification Policy:
       - EventBridge event N days/hours before expiration
       - Use for: alerting teams to renew or clean up before deletion
       {"Type":"ExpirationNotification","Version":"1.0","Attributes":{"Before":"15","Unit":"Days"}}

    3. NoChangeNotification Policy:
       - EventBridge event if parameter unchanged for N days
       - Use for: detecting stale credentials, forgotten configuration
       {"Type":"NoChangeNotification","Version":"1.0","Attributes":{"After":"90","Unit":"Days"}}

  Remediation Workflow:
    EventBridge Rule → Lambda Function → Actions:
      - Notify via SNS/Slack
      - Create Jira ticket for credential rotation
      - Auto-expire and recreate parameter
      - Escalate to security team
  ```
- Source: https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-policies.html

---

**Disaster Recovery for Configuration**
- RTO/RPO: RTO: Minutes (recreate from IaC) | RPO: Zero (parameters defined in IaC are reproducible)
- AWS Services: SSM Parameter Store, AWS CloudFormation/CDK/Terraform, AWS Backup (not applicable to Parameter Store directly)
- Cost Profile: Low — no additional services required if configuration is in IaC
- Automation:
  ```
  DR Strategy:
    Parameter Store does NOT support multi-Region replication (unlike Secrets Manager).

    Option 1: Infrastructure-as-Code (Recommended)
      - ALL parameters defined in CloudFormation/CDK/Terraform
      - Deploy to DR Region creates all parameters
      - RPO: Zero (parameters are code, not data)
      - RTO: Stack deployment time (minutes)

    Option 2: Cross-Region Sync via EventBridge + Lambda
      - EventBridge rule captures Parameter Store change events
      - Lambda function replicates changes to DR Region
      - RPO: Near-real-time (event propagation delay)
      - RTO: Immediate (DR Region always has current values)
      - Complexity: Custom code, eventual consistency

    Option 3: Export/Import Backup
      - Scheduled Lambda exports all parameters to S3 (JSON)
      - S3 cross-region replication ensures backup availability
      - Import script recreates parameters in DR Region
      - RPO: Backup frequency (hourly/daily)
      - RTO: Import script execution time

  Recommendation: Option 1 (IaC) for all parameters. Supplement with Option 2
  for parameters that change frequently outside of deployments.
  ```
- Source: https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html

---

## Reference Architectures

**Multi-Environment Configuration Management**
- Context: Applications deployed across dev/staging/prod environments needing centralized, secure, hierarchical configuration management
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Configuration Storage | SSM Parameter Store | Store all configuration values hierarchically |
  | Encryption | AWS KMS (CMK per env) | Encrypt SecureString parameters with env-specific keys |
  | Access Control | IAM Policies | Path-based access scoped to environment and application |
  | Retrieval (Lambda) | Parameters and Secrets Lambda Extension | Cached parameter retrieval via localhost:2773 |
  | Retrieval (ECS/EKS) | ECS Secrets injection / ASCP | Inject parameters as environment variables or mounted files |
  | Retrieval (IaC) | CloudFormation dynamic references | {{resolve:ssm:/prod/app/config}} in templates |
  | Lifecycle | Parameter Policies + EventBridge | Expiration, staleness detection, change notifications |
  | Audit | CloudTrail + EventBridge | Log all access and changes, alert on anomalies |
  | Sharing | AWS RAM (advanced tier) | Cross-account access for shared configuration |

- Key Decisions: Naming hierarchy structure; KMS key strategy (per-app vs per-env); standard vs advanced tier; caching TTL duration; which values in Parameter Store vs Secrets Manager vs AppConfig
- Scaling Path: Start with standard tier and default throughput → upgrade to advanced as policies and sharing are needed → enable higher throughput for high-concurrency workloads → add cross-account sharing via RAM for multi-account architectures
- Source: https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html

---

## Service Equivalence Map

| Category | AWS | Google Cloud | Azure | Oracle Cloud (OCI) |
|----------|-----|-------------|-------|--------------------|
| **Configuration Store** | SSM Parameter Store | Runtime Configurator / Secret Manager | App Configuration | OCI Resource Manager Variables |
| **Secret Management** | Secrets Manager | Secret Manager | Key Vault (Secrets) | OCI Vault (Secrets) |
| **Dynamic Config** | AppConfig | Remote Config (Firebase) | App Configuration (dynamic) | — |
| **Key Management** | KMS | Cloud KMS | Key Vault (Keys) | OCI Vault (Keys) |
| **Feature Flags** | AppConfig + Evidently | Firebase Remote Config | App Configuration (feature flags) | — |

> **⚠️ Important**: AWS uniquely separates configuration (Parameter Store) from secrets (Secrets Manager) as distinct services. Google Cloud and Azure merge these into single services (Secret Manager, Key Vault). This architectural difference means AWS Parameter Store patterns do not map 1:1 to other providers — the closest equivalents are subsets of broader services.

---

## Provider Differentiators

**Parameter Store — Hierarchical Configuration with Path-Based IAM**
- Category: Security / Data
- Unique Value: No other major cloud provider offers hierarchical configuration storage with native path-based IAM policy integration. AWS Parameter Store's hierarchy enables bulk retrieval (GetParametersByPath) AND access control (IAM resource ARN wildcards on paths) in a unified model. Other providers require separate authorization mechanisms for grouped configuration access.
- Architecture Impact: Enables "configuration-as-namespace" patterns where organizational structure maps directly to both storage layout AND access policy. Teams can self-serve configuration within their namespace without platform team intervention.
- When to Leverage: Multi-team organizations needing self-service configuration with governance; microservices architectures with dozens of services needing isolated but discoverable configuration.
- Caveat: Maximum 15 levels of hierarchy; parameter names are immutable (cannot restructure hierarchy without recreation); path-based IAM has the recursive access implication (access to /a grants /a/b).
- Source: https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-paramstore-hierarchies.html

---

**Public Parameters Ecosystem**
- Category: Data
- Unique Value: AWS publishes continuously-updated service metadata (AMI IDs, ECS/EKS optimized images, regional infrastructure data) as public parameters consumable via the same Parameter Store API. This creates a unified interface for both custom configuration AND AWS service discovery — no equivalent exists on other major clouds at this scale.
- Architecture Impact: Launch templates, CloudFormation stacks, and CI/CD pipelines can reference always-current AWS metadata without external lookups or manual updates. Eliminates an entire class of "stale AMI ID" operational issues.
- When to Leverage: Any workload using EC2/ECS/EKS that needs latest optimized AMIs; infrastructure automation needing region/AZ discovery; CI/CD pipelines building environment-specific deployments.
- Caveat: Not all public parameters available in all Regions; update frequency varies by service; no SLA on public parameter freshness.
- Source: https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-finding-public-parameters.html

---

**AWS Parameters and Secrets Lambda Extension**
- Category: Compute
- Unique Value: A single Lambda layer that provides unified, cached access to BOTH Parameter Store AND Secrets Manager via a simple HTTP localhost interface (port 2773). Eliminates SDK dependencies, reduces cold start impact of multiple API calls, and standardizes configuration retrieval across all Lambda runtimes (including custom runtimes).
- Architecture Impact: Lambda functions become runtime-agnostic for configuration retrieval — same HTTP GET pattern works in Python, Node.js, Java, Go, Rust, or custom runtimes. Caching reduces API costs and latency by ~99% for repeated retrievals within TTL window.
- When to Leverage: Any Lambda function retrieving parameters or secrets; functions in languages without official AWS SDK caching libraries; high-concurrency Lambda functions at risk of Parameter Store throttling.
- Caveat: Adds ~50ms to cold start; cannot be invoked during INIT phase; cached values stale during TTL window; requires X-Aws-Parameters-Secrets-Token header.
- Source: https://docs.aws.amazon.com/systems-manager/latest/userguide/ps-integration-lambda-extensions.html

---

## Scenario Coverage

**Standard Case**: Multi-service application with environment-specific configuration
- Approach: Hierarchical parameters under `/{env}/{service}/{component}/{param}` with SecureString for sensitive values using per-environment CMK keys. Lambda Extension for serverless retrieval, ECS secrets injection for containers, CloudFormation dynamic references for IaC. IAM policies scoped to service paths.
- Key Decisions: Naming convention depth (3-5 levels); KMS key granularity (per-service or per-environment); standard vs advanced tier; caching TTL based on change frequency.

**Edge Case**: High-throughput microservices architecture with 500+ Lambda functions
- Approach: Enable higher throughput at account level. Maximize caching via Lambda Extension (TTL=300s). Use GetParametersByPath for bulk retrieval at cold start rather than individual GetParameter calls. Monitor CloudWatch throttling metrics. Consider application-level config cache that survives across invocations (Lambda execution environment reuse).
- Key Decision: Whether to consolidate parameters into fewer JSON-structured String parameters (fewer API calls) vs maintaining granular parameters (better IAM scoping but more calls).

**Anti-Pattern Case**: Team requests storing database credentials with automatic rotation in Parameter Store
- Clarification: "Parameter Store does not provide automatic rotation. For credentials requiring rotation, use AWS Secrets Manager which provides managed rotation for RDS/Aurora/Redshift/DocumentDB and Lambda-based rotation for custom credentials. Parameter Store is appropriate for the non-secret components of database configuration (host, port, database name) while Secrets Manager handles the credential (username/password). Should we implement this split-storage pattern?"
