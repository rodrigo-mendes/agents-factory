# Never Do Patterns — securing-aws-secrets-certificates

Full anti-patterns with wrong/correct examples. Summary in [../SKILL.md](../SKILL.md).

---

## Anti-Pattern 1 — Hardcoded Credentials in Source Code [CRITICAL]

**Why**: Violates SEC02-BP03. Credentials reach version control, build artifacts, container images, and CloudFormation templates. Detection by Amazon CodeGuru / Amazon Q Developer security scan.

```python
# 🚫 WRONG — password in source code
import psycopg2
conn = psycopg2.connect(
    host="mydb.cluster.us-east-1.rds.amazonaws.com",
    database="myapp",
    user="dbuser",
    password="mypassword123"  # CRITICAL: hardcoded credential
)
```

```python
# ✅ CORRECT — retrieve at runtime from Secrets Manager
import boto3, json
client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='prod/myapp/db-credentials')
creds = json.loads(secret['SecretString'])
conn = psycopg2.connect(
    host=creds['host'],
    database=creds['dbname'],
    user=creds['username'],
    password=creds['password']
)
```

Use Lambda Parameters and Secrets Extension for caching (TTL 300s) to avoid per-request API calls.

**Detection**: `git-secrets` pre-commit hook; Amazon Q Developer security scan; `grep -r "password\s*=" src/`.

---

## Anti-Pattern 2 — Plaintext Secrets in ECS/Lambda Environment Variables [HIGH]

**Why**: Environment variables visible in AWS console, CloudFormation templates, task definition API responses, and process inspection inside the container (`/proc/<pid>/environ`).

```json
// 🚫 WRONG — literal password in ECS environment array
{
  "containerDefinitions": [{
    "environment": [
      { "name": "DB_PASSWORD", "value": "mypassword123" }
    ]
  }]
}
```

```json
// ✅ CORRECT — reference to Secrets Manager ARN in ECS secrets array
{
  "containerDefinitions": [{
    "secrets": [
      {
        "name": "DB_PASSWORD",
        "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:prod/myapp/db-credentials:password::"
      }
    ]
  }]
}
```

The `valueFrom` format is `<secret-ARN>:<json-key>::` for a JSON key, or just the ARN for the full JSON string.

**Detection**:
```bash
aws ecs describe-task-definition --task-definition <name> \
  --query 'taskDefinition.containerDefinitions[*].environment' \
  | grep -i "password\|secret\|token\|key"
```

---

## Anti-Pattern 3 — No Secret Rotation [HIGH]

**Why**: SecretsManager.1 and SecretsManager.4 map to PCI DSS v4.0.1/8.6.3. An undetected credential compromise extends indefinitely with no rotation.

```bash
# 🚫 WRONG — check for non-rotating secrets
aws secretsmanager describe-secret --secret-id prod/db-password
# Output: RotationEnabled: false
# Or: LastRotatedDate older than 90 days
```

```bash
# ✅ CORRECT — enable rotation immediately
aws secretsmanager rotate-secret \
  --secret-id prod/db-password \
  --rotation-lambda-arn <arn> \
  --rotation-rules AutomaticallyAfterDays=30

# Confirm
aws secretsmanager describe-secret --secret-id prod/db-password \
  --query '{RotationEnabled:RotationEnabled,NextRotationDate:NextRotationDate}'
```

**Detection**: Security Hub controls SecretsManager.1 (rotation not enabled) and SecretsManager.4 (not rotated within 90 days).

---

## Anti-Pattern 4 — Self-Signed Certificates for Public Resources [HIGH]

**Why**: SEC09-BP01 explicit anti-pattern. Browser security warnings, no CRL/OCSP revocation, no automated renewal. PCI DSS 4.2.1 violation.

```bash
# 🚫 WRONG — OpenSSL self-signed cert on ALB
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
# Then imported to ACM and associated with ALB HTTPS listener
```

```bash
# ✅ CORRECT — free ACM public cert with DNS validation
aws acm request-certificate \
  --domain-name api.example.com \
  --validation-method DNS \
  --region us-east-1

# Associate with ALB HTTPS listener — zero cost, automated renewal
```

**Detection**:
```bash
aws elbv2 describe-listeners --load-balancer-arn <alb-arn> \
  --query 'Listeners[?Protocol==`HTTPS`].Certificates[*].CertificateArn'
# Then check each ARN in ACM — look for imported self-signed certs
```

---

## Anti-Pattern 5 — CloudFront Certificate Not in us-east-1 [HIGH]

**Why**: ACM certificate for CloudFront MUST be in `us-east-1`. Any other region → `InvalidViewerCertificate` error.

```bash
# 🚫 WRONG — cert in eu-west-1, then attached to CloudFront
aws acm request-certificate --domain-name example.com --region eu-west-1
# aws cloudfront create-distribution ... -> Error: InvalidViewerCertificate
```

```bash
# ✅ CORRECT — always us-east-1 for CloudFront
aws acm request-certificate \
  --domain-name example.com \
  --validation-method DNS \
  --region us-east-1
# Then: ALB in eu-west-1 needs its own ACM cert in eu-west-1
```

Two separate ACM certs are required: one in `us-east-1` for CloudFront, one in the ALB's region for the ALB.

---

## Anti-Pattern 6 — Wildcard Principal in KMS Key Policy [CRITICAL]

**Why**: `"Principal": "*"` allows any identity including anonymous principals. Security Hub KMS.5: CRITICAL severity.

```json
// 🚫 WRONG — wildcard principal grants any identity access
{
  "Effect": "Allow",
  "Principal": "*",
  "Action": "kms:*",
  "Resource": "*"
}
```

```json
// ✅ CORRECT — specific IAM role/user ARNs only
{
  "Effect": "Allow",
  "Principal": {
    "AWS": [
      "arn:aws:iam::123456789:role/KeyAdminRole",
      "arn:aws:iam::123456789:role/ECSTaskRole"
    ]
  },
  "Action": ["kms:Decrypt", "kms:GenerateDataKey"],
  "Resource": "*"
}
```

**Detection**:
```bash
aws kms get-key-policy --key-id <key-id> --policy-name default \
  | python3 -c "import json,sys; p=json.load(sys.stdin); [print('CRITICAL: wildcard principal') for s in p['Statement'] if s['Principal']=='*']"
```

---

## Anti-Pattern 7 — `"Resource": "*"` in IAM for KMS Cryptographic Operations [HIGH]

**Why**: Grants access to ALL KMS keys including cross-account keys where the IAM role has been granted access. Security Hub KMS.1 (managed policy) and KMS.2 (inline policy).

```json
// 🚫 WRONG — wildcard resource for decryption
{
  "Effect": "Allow",
  "Action": ["kms:Decrypt", "kms:GenerateDataKey"],
  "Resource": "*"
}
```

```json
// ✅ CORRECT — exact key ARN in Resource
{
  "Effect": "Allow",
  "Action": ["kms:Decrypt", "kms:GenerateDataKey"],
  "Resource": "arn:aws:kms:us-east-1:123456789:key/mrk-12345abcd"
}
```

Only these operations legitimately require `"Resource": "*"`:
- `kms:CreateKey`
- `kms:GenerateRandom`
- `kms:ListAliases`
- `kms:ListKeys`

Do NOT use alias ARN in Resource — it applies the policy to the alias object, not the underlying key.

---

## Anti-Pattern 8 — `aws:SourceIp` in Secrets Manager Resource Policy for Lambda Rotation [HIGH]

**Why**: Lambda rotation functions invoke Secrets Manager from AWS-internal address space, not from corporate IP ranges or VPC CIDRs. An `aws:SourceIp` condition silently blocks ALL rotation Lambda calls.

```json
// 🚫 WRONG — SourceIp blocks Lambda rotation
{
  "Effect": "Deny",
  "Principal": "*",
  "Action": "secretsmanager:*",
  "Resource": "*",
  "Condition": {
    "NotIpAddress": {
      "aws:SourceIp": ["203.0.113.0/24"]
    }
  }
}
```

```json
// ✅ CORRECT — SourceVpce restricts to the VPC endpoint
{
  "Effect": "Deny",
  "Principal": "*",
  "Action": "secretsmanager:*",
  "Resource": "*",
  "Condition": {
    "StringNotEquals": {
      "aws:SourceVpce": "vpce-0a12b34c56d78901a"
    }
  }
}
```

**Detection**: If rotation fails, check rotation Lambda CloudWatch Logs for `Access Denied` and inspect Secrets Manager resource policy for `SourceIp` conditions.

---

## Anti-Pattern 9 — Parameter Store SecureString for Rotating Credentials [HIGH]

**Why**: Parameter Store has no rotation capability. AWS explicitly recommends Secrets Manager for all credentials that require rotation, cross-account access, or fine-grained audit.

```bash
# 🚫 WRONG — DB password in Parameter Store with no rotation
aws ssm put-parameter \
  --name /myapp/prod/db-password \
  --value "mysecretpassword" \
  --type SecureString
# Result: password never rotated; no audit trail per credential; no cross-account sharing
```

```bash
# ✅ CORRECT — migrate to Secrets Manager with rotation
aws secretsmanager create-secret \
  --name prod/myapp/db-password \
  --kms-key-id <cmk-arn> \
  --secret-string '{"username":"dbuser","password":"mysecretpassword"}'
# Then enable rotation and delete the Parameter Store entry
```

---

## Anti-Pattern 10 — Certificate Pinning Against an ACM-Managed Certificate [HIGH]

**Why**: ACM managed renewal generates a NEW public-private key pair. Applications pinning the leaf certificate or public key will fail to connect after renewal — customer-facing outage.

```swift
// 🚫 WRONG — pinning the leaf certificate's public key
let pinnedPublicKey = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA..."  // ACM-issued key
// After ACM renewal: new key pair -> app fails to connect
```

```swift
// ✅ CORRECT — pin to Amazon Root CA (stable; does not change on leaf cert renewal)
// Amazon Root CA 1: "b9:a4:57:..." (stable root; does not change when leaf cert renews)
let pinnedRootCert = "amazon-root-ca-1.pem"
```

Amazon Root CA certificates are stable and do not change when ACM issues a renewed leaf certificate.

---

## Anti-Pattern 11 — Excluding KMS from CloudTrail [HIGH]

**Why**: Hiding KMS from CloudTrail creates a blind spot for key compromise, unauthorized decryption, and regulatory audit trails.

```bash
# 🚫 WRONG — KMS excluded from CloudTrail
aws cloudtrail put-event-selectors \
  --trail-name my-trail \
  --event-selectors '[{
    "ReadWriteType": "All",
    "IncludeManagementEvents": true,
    "ExcludeManagementEventSources": ["kms.amazonaws.com"]
  }]'
```

```bash
# ✅ CORRECT — never exclude KMS; or explicitly remove from exclusion list
aws cloudtrail put-event-selectors \
  --trail-name my-trail \
  --event-selectors '[{
    "ReadWriteType": "All",
    "IncludeManagementEvents": true,
    "ExcludeManagementEventSources": []
  }]'

# Verify
aws cloudtrail get-event-selectors --trail-name my-trail \
  --query 'EventSelectors[*].ExcludeManagementEventSources'
# Expected: [] (empty)
```

---

## Anti-Pattern 12 — Single AWS Account for All Private CA Hierarchy Levels [HIGH]

**Why**: SEC09-BP01 anti-pattern: "paying insufficient attention to CA hierarchy design." Root CA compromise in a shared account exposes the entire PKI hierarchy — all certificates must be reissued.

```
# 🚫 WRONG — root CA, intermediate CAs, end-entity issuance all in Account 123456789
aws acm-pca create-certificate-authority --certificate-authority-type ROOT ...  # in account 123456789
aws acm-pca create-certificate-authority --certificate-authority-type SUBORDINATE ...  # same account
```

```
# ✅ CORRECT — separate accounts per CA level
Account 111111111: Root CA only
  - Issues intermediate CA certificates
  - Then DISABLED/offline between issuance operations
  - Strictly limited admin access (hardware MFA required)

Account 222222222: Intermediate CAs
  - Issues end-entity certificates for workloads
  - Kubernetes pods, mTLS service identities, code signing

Account 333333333+: Workload accounts
  - Consume certificates via IssueCertificate API
  - ACM Private CA integrated with cert-manager / EKS PCA controller
```

**Detection**:
```bash
aws acm-pca list-certificate-authorities \
  --query 'CertificateAuthorities[*].{Type:Type,Status:Status,Arn:Arn}'
# If root and subordinate CAs appear in the same account, remediate
```

---

## Anti-Pattern 13 — Parameter Store Policy Overwrite [MEDIUM]

**Why**: `--policies` flag silently overwrites ALL existing policies. Existing `Expiration` and `ExpirationNotification` policies are deleted without warning.

```bash
# 🚫 WRONG — adds NoChangeNotification but silently deletes Expiration + ExpirationNotification
aws ssm put-parameter \
  --name /myapp/param \
  --policies '[{"Type":"NoChangeNotification","Version":"1.0","Attributes":{"After":"30","Unit":"Days"}}]'
# The parameter's existing Expiration and ExpirationNotification policies are now GONE
```

```bash
# ✅ CORRECT — always include all desired policies in a single call
aws ssm put-parameter \
  --name /myapp/param \
  --policies '[
    {"Type":"Expiration","Version":"1.0","Attributes":{"Timestamp":"2027-01-01T00:00:00.000Z"}},
    {"Type":"ExpirationNotification","Version":"1.0","Attributes":{"Before":"14","Unit":"Days"}},
    {"Type":"NoChangeNotification","Version":"1.0","Attributes":{"After":"30","Unit":"Days"}}
  ]'

# Verify all policies are present
aws ssm get-parameters --names /myapp/param \
  --query 'Parameters[*].Policies'
```

Max 10 policies per parameter. Downgrading from Advanced to Standard tier is NOT supported.
