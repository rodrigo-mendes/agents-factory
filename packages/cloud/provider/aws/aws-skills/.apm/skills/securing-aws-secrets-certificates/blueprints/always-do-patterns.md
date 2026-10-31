# Always Do Patterns — securing-aws-secrets-certificates

Full mandatory patterns with implementation guidance. Summary in [../SKILL.md](../SKILL.md).

---

## Pattern 1 — Replace Long-Term Credentials with IAM Roles

**Pillar**: SEC02-BP03, SEC02-BP05 | **Confidence**: HIGH

IAM roles deliver temporary credentials automatically. No static access keys on compute.

| Compute Type | Mechanism | What NOT to do |
|---|---|---|
| EC2 | Instance Profile (attached to EC2) | Access keys in user data / AMI |
| ECS Fargate | `taskRoleArn` in task definition | Access keys in container env vars |
| Lambda | Execution Role assigned to function | Hardcoded credentials in function code |
| EKS | IRSA or EKS Pod Identity → Kubernetes SA | Shared IAM user credentials mounted as k8s secret |
| On-premises | IAM Roles Anywhere + X.509 cert from Private CA | Long-term IAM user access keys |

**Verification**:
```bash
aws iam generate-credential-report
aws iam get-credential-report --query 'Content' --output text | base64 -d | \
  awk -F',' 'NR>1 && ($4=="true" || $8=="true") {print $1, "has active access keys"}'
# Expected: no EC2/ECS/Lambda service accounts with active access keys
# Security Hub: IAM.4
```

---

## Pattern 2 — Store Credentials in Secrets Manager with Automatic Rotation

**Pillar**: SEC02-BP03, SecretsManager.1, SecretsManager.4 | **Confidence**: HIGH

All credentials (DB passwords, API keys, OAuth tokens) go to Secrets Manager. Compliance baseline: 90-day rotation.

```bash
# Create secret with CMK encryption
aws secretsmanager create-secret \
  --name prod/myapp/db-credentials \
  --kms-key-id arn:aws:kms:us-east-1:123456789:key/mrk-12345 \
  --secret-string '{"username":"dbuser","password":"initial-value"}'

# Enable rotation (alternating-users for production)
aws secretsmanager rotate-secret \
  --secret-id prod/myapp/db-credentials \
  --rotation-lambda-arn arn:aws:lambda:us-east-1:123456789:function:SecretsManagerRDSPostgreSQLRotationAlternatingUsers \
  --rotation-rules AutomaticallyAfterDays=30

# Verify
aws secretsmanager describe-secret --secret-id prod/myapp/db-credentials \
  --query '{RotationEnabled:RotationEnabled,LastRotated:LastRotatedDate}'
```

**ECS task definition injection** (static at container start):
```json
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
Note: value is static at task start. After rotation, trigger `aws ecs update-service --force-new-deployment`.

---

## Pattern 3 — Enable CMK Automatic Rotation

**Pillar**: SEC08-BP01, KMS.4 | **Confidence**: HIGH

Required by CIS AWS Foundations Benchmark v5.0.0/3.6, PCI DSS v4.0.1/3.7.4, NIST 800-53 r5 SC-12, SC-28(3).

```bash
# Enable automatic rotation
aws kms enable-key-rotation --key-id <key-id>

# Set custom rotation period (e.g., 90 days for PCI DSS)
aws kms enable-key-rotation --key-id <key-id> --rotation-period-in-days 90

# On-demand rotation (immediate, does not reset the automatic schedule)
aws kms rotate-key-on-demand --key-id <key-id>

# Monitor: EventBridge rule for rotation event
aws events put-rule \
  --name KMSKeyRotationAlert \
  --event-pattern '{"source":["aws.kms"],"detail-type":["KMS CMK Rotation"]}'
```

Key rotation does NOT require application code changes — key ID, ARN, and alias remain the same. All previous backing key versions are retained for decryption.

---

## Pattern 4 — Use ACM for All Public TLS Certificates with DNS Validation

**Pillar**: SEC09-BP01, SEC09-BP02, ACM.1 | **Confidence**: HIGH

ACM-managed certificates are free. DNS validation enables fully automated renewal.

```bash
# CloudFront certificate MUST be in us-east-1
aws acm request-certificate \
  --domain-name example.com \
  --subject-alternative-names www.example.com api.example.com \
  --validation-method DNS \
  --region us-east-1

# ALB certificate in the ALB's region
aws acm request-certificate \
  --domain-name api.example.com \
  --validation-method DNS \
  --region us-east-1  # change to ALB region if different

# Get CNAME record to add to DNS
aws acm describe-certificate \
  --certificate-arn <arn> \
  --query 'Certificate.DomainValidationOptions[*].{Domain:DomainName,Name:ResourceRecord.Name,Value:ResourceRecord.Value}'
```

ACM renews automatically starting 60 days before expiry as long as the DNS CNAME record remains in place.

```bash
# Monitor: EventBridge rule for certificate approaching expiration
aws events put-rule \
  --name ACMCertExpiryAlert \
  --event-pattern '{"source":["aws.acm"],"detail-type":["ACM Certificate Approaching Expiration"]}'

# CloudWatch alarm: DaysToExpiry < 30
aws cloudwatch put-metric-alarm \
  --alarm-name ACMCertExpiry30Days \
  --namespace AWS/CertificateManager \
  --metric-name DaysToExpiry \
  --threshold 30 \
  --comparison-operator LessThanThreshold \
  --evaluation-periods 1 --period 86400 --statistic Minimum \
  --alarm-actions <sns-arn>
```

---

## Pattern 5 — Route Secrets Manager Calls Through VPC PrivateLink

**Pillar**: SEC09-BP02, SEC03-BP02 | **Confidence**: HIGH

Eliminates public internet traversal for secret retrieval. Required in regulated environments.

```bash
# Create VPC interface endpoint for Secrets Manager
aws ec2 create-vpc-endpoint \
  --vpc-id <vpc-id> \
  --vpc-endpoint-type Interface \
  --service-name com.amazonaws.us-east-1.secretsmanager \
  --subnet-ids <subnet-id-az1> <subnet-id-az2> \
  --security-group-ids <sg-id> \
  --private-dns-enabled

# Also create for KMS if using CMK-encrypted secrets
aws ec2 create-vpc-endpoint \
  --vpc-id <vpc-id> \
  --vpc-endpoint-type Interface \
  --service-name com.amazonaws.us-east-1.kms \
  --subnet-ids <subnet-id-az1> <subnet-id-az2> \
  --security-group-ids <sg-id> \
  --private-dns-enabled
```

**Secrets Manager resource policy with SourceVpce enforcement**:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Deny",
    "Principal": "*",
    "Action": "secretsmanager:*",
    "Resource": "*",
    "Condition": {
      "StringNotEquals": {
        "aws:SourceVpce": "vpce-0a12b34c56d78901a"
      }
    }
  }]
}
```

Attach with: `aws secretsmanager put-resource-policy --secret-id <id> --resource-policy file://policy.json --block-public-policy`

---

## Pattern 6 — Scope KMS Key Policies to Specific Principals

**Pillar**: SEC08-BP01, KMS.1, KMS.2, KMS.5 | **Confidence**: HIGH

KMS.5 (publicly accessible key) is classified CRITICAL severity by Security Hub.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "KeyAdminPermissions",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789:role/KeyAdminRole"
      },
      "Action": ["kms:Create*", "kms:Describe*", "kms:Enable*", "kms:Put*", "kms:Update*",
                 "kms:Revoke*", "kms:Disable*", "kms:Get*", "kms:Delete*", "kms:ScheduleKeyDeletion"],
      "Resource": "*"
    },
    {
      "Sid": "SecretsManagerUsage",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789:role/ECSTaskRole"
      },
      "Action": ["kms:Decrypt", "kms:GenerateDataKey"],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "kms:ViaService": "secretsmanager.us-east-1.amazonaws.com"
        }
      }
    }
  ]
}
```

**IAM policy for application role** (cross-account: must specify key ARN):
```json
{
  "Effect": "Allow",
  "Action": ["kms:Decrypt", "kms:GenerateDataKey"],
  "Resource": "arn:aws:kms:us-east-1:123456789:key/mrk-12345"
}
```

Only `CreateKey`, `GenerateRandom`, `ListAliases`, `ListKeys` legitimately require `"Resource": "*"`.

---

## Pattern 7 — Separate CMKs per Data Classification

**Pillar**: SEC08-BP02 | **Confidence**: HIGH

One CMK per sensitivity tier prevents a compromised key from exposing all data.

Recommended CMK tiers for a web application:
- `prod-secrets-cmk` — Secrets Manager secrets (prod)
- `prod-rds-cmk` — RDS Aurora encryption
- `prod-s3-cmk` — S3 buckets (PII/sensitive)
- `staging-cmk` — All staging resources (combined is acceptable for non-prod)

```bash
# S3 bucket default encryption with CMK
aws s3api put-bucket-encryption \
  --bucket my-sensitive-bucket \
  --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"aws:kms","KMSMasterKeyID":"<cmk-arn>"},"BucketKeyEnabled":true}]}'

# Account-level EBS default encryption
aws ec2 enable-ebs-encryption-by-default

# Config rule compliance check
aws config get-compliance-details-by-config-rule \
  --config-rule-name encrypted-volumes
```

---

## Pattern 8 — Enforce TLS 1.2 Minimum on All Endpoints

**Pillar**: SEC09-BP02 | **Confidence**: HIGH

AWS deprecated TLS 1.0 and 1.1 for AWS API endpoints as of February 2024.

```bash
# CloudFront: TLSv1.2_2021 (includes TLS 1.3) — preferred
# Allowed policies: TLSv1.2_2021, TLSv1.2_2019

# S3 bucket policy: deny non-HTTPS
aws s3api put-bucket-policy --bucket <bucket-name> --policy '{
  "Statement": [{
    "Effect": "Deny",
    "Principal": "*",
    "Action": "s3:*",
    "Resource": ["arn:aws:s3:::<bucket-name>", "arn:aws:s3:::<bucket-name>/*"],
    "Condition": {"Bool": {"aws:SecureTransport": "false"}}
  }]
}'

# ALB: ELBSecurityPolicy-TLS13-1-2-2021-06 on HTTPS listener
# Verify CloudFront minimum TLS version
aws cloudfront get-distribution --id <dist-id> \
  --query 'Distribution.DistributionConfig.ViewerCertificate.MinimumProtocolVersion'
# Expected: TLSv1.2_2021 or TLSv1.2_2019
```

---

## Pattern 9 — Log All KMS and Secrets Manager Activity to CloudTrail

**Pillar**: SEC02-BP05, SEC08-BP01 | **Confidence**: HIGH

KMS events hidden from CloudTrail = blind spot for key compromise and credential access.

```bash
# Verify KMS is NOT excluded from CloudTrail
aws cloudtrail get-event-selectors --trail-name <trail-name> \
  --query 'EventSelectors[*].ExcludeManagementEventSources'
# Expected: empty array or does not contain "kms.amazonaws.com"

# EventBridge rule: alert on ScheduleKeyDeletion
aws events put-rule \
  --name KMSKeyDeletionAlert \
  --event-pattern '{
    "source": ["aws.kms"],
    "detail-type": ["AWS API Call via CloudTrail"],
    "detail": {"eventName": ["ScheduleKeyDeletion"]}
  }'

# CloudWatch Logs Insights: find unexpected KMS Decrypt calls
# Query: fields @timestamp, userIdentity.arn, requestParameters.keyId
# | filter eventName="Decrypt" and userIdentity.type="IAMUser"
# | sort @timestamp desc
```

Enable GuardDuty for anomalous Secrets Manager access detection (automatically monitors for unusual `GetSecretValue` patterns).

---

## Pattern 10 — Parameter Store for Static Config; Secrets Manager for Credentials

**Pillar**: SEC02-BP03 | **Confidence**: HIGH

Official AWS guidance: "If you manage credentials such as usernames, passwords, or any other secrets, we recommend using AWS Secrets Manager."

| Store | Use for | Do NOT use for |
|---|---|---|
| Parameter Store (Standard/SecureString) | AMI IDs, endpoint URLs, feature flags, env names, app config | Rotating credentials, cross-account secrets |
| Secrets Manager | DB passwords, API keys, OAuth tokens, TLS private keys | Non-credential config (cost optimization) |

Parameter Store SecureString limitations vs Secrets Manager:
- No automatic rotation
- No cross-account resource-based policies
- No native database credential integration
- No Secrets Manager EventBridge events

```bash
# Audit: find SecureString parameters matching credential patterns
aws ssm describe-parameters \
  --parameter-filters Key=Type,Values=SecureString \
  --query 'Parameters[*].{Name:Name,LastModified:LastModifiedDate}'
# Review names matching: *password*, *secret*, *token*, *key* -> migrate to Secrets Manager
```
