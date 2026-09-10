# Evaluation Scenarios — securing-aws-secrets-certificates

Test cases for `/evaluating-skill-scenarios securing-aws-secrets-certificates`.

---

## Scenario 1 — Canonical: ECS Fargate Web App with RDS Aurora Credentials

```json
{
  "skills": ["securing-aws-secrets-certificates"],
  "query": "We're building a public-facing web application: CloudFront → ALB → ECS Fargate → RDS Aurora PostgreSQL. Design the secrets and certificate management architecture.",
  "expected_behavior": [
    "Requests two separate ACM certificates: us-east-1 for CloudFront, app-region for ALB; both with DNS validation",
    "Stores Aurora credentials in Secrets Manager with alternating-users Lambda rotation",
    "Defines ECS task IAM role with secretsmanager:GetSecretValue on exact secret ARN + kms:Decrypt on CMK ARN with kms:ViaService condition",
    "Creates Secrets Manager + KMS VPC interface endpoints in the ECS VPC with private DNS enabled",
    "Deploys rotation Lambda in same VPC as VPC endpoints",
    "Specifies CloudFront TLSv1.2_2021 policy and ALB ELBSecurityPolicy-TLS13-1-2-2021-06",
    "Enables CMK automatic rotation for prod-secrets and prod-rds CMKs separately",
    "Enables Security Hub controls: KMS.4, SecretsManager.1, SecretsManager.4, ACM.1 as baseline"
  ]
}
```

---

## Scenario 2 — Architectural Decision: Rotation Strategy Selection

```json
{
  "skills": ["securing-aws-secrets-certificates"],
  "query": "Should I use single-user or alternating-users rotation for our RDS PostgreSQL production database? The app has SLA of 99.99% uptime.",
  "expected_behavior": [
    "Asks whether the application can tolerate a brief credential rejection window during rotation",
    "Given 99.99% SLA, recommends alternating-users strategy (zero auth denial window)",
    "Explains the tradeoff: alternating-users requires a superuser secret (+$0.40/month) and manual permission sync if original user permissions change post-clone",
    "Notes that single-user has a brief window where old credentials may still be cached in app connections",
    "Provides AWS-provided Aurora PostgreSQL alternating-users template reference"
  ]
}
```

---

## Scenario 3 — Edge Case: Multi-Account Organization with Centralized Secrets

```json
{
  "skills": ["securing-aws-secrets-certificates"],
  "query": "We have 20 workload accounts and want to centralize all secrets in a dedicated secrets management account. How do we set this up?",
  "expected_behavior": [
    "Requires Customer Managed Key (CMK) in the secrets account — AWS managed key does not support cross-account decryption",
    "Secrets Manager resource policy in secrets account grants cross-account access to workload account IAM roles",
    "Workload account IAM policies also grant the secret ARN (dual permission requirement for cross-account KMS)",
    "VPC PrivateLink between workload account VPCs and secrets account endpoint (or AWS PrivateLink sharing)",
    "Notes April 2026 update: Secrets Manager console now accepts cross-account CMK ARN input directly",
    "Recommends AWS Config Multi-Account Aggregator for centralized compliance monitoring",
    "Adds kms:ViaService condition to restrict CMK usage to secretsmanager requests"
  ]
}
```

---

## Scenario 4 — Anti-Pattern Trap: Developer Requests Environment Variable for DB Password

```json
{
  "skills": ["securing-aws-secrets-certificates"],
  "query": "Can I just put the database password in an ECS environment variable? It's easier to configure.",
  "expected_behavior": [
    "Refuses the plaintext environment variable approach (HIGH risk anti-pattern)",
    "Explains that environment variables are visible in console, CloudFormation templates, task definition API, and process inspection",
    "Offers two correct alternatives: (1) ECS task definition secrets array with valueFrom pointing to the Secrets Manager ARN; (2) SDK-based retrieval at runtime with Lambda Parameters and Secrets Extension caching",
    "Clarifies: the secret ARN can be an environment variable, but never the password value itself",
    "Distinguishes when to use each alternative: env var injection (static, needs force-new-deploy on rotation) vs SDK caching (live refresh, no restart needed)"
  ]
}
```

---

## Scenario 5 — Edge Case: mTLS Certificate Requirements for Service Mesh

```json
{
  "skills": ["securing-aws-secrets-certificates"],
  "query": "We need mTLS between microservices in our EKS cluster. Can ACM handle this?",
  "expected_behavior": [
    "Identifies that ACM public certificates cannot be used for mTLS client certificates",
    "Notes ACM no longer issues clientAuth EKU certificates as of June 2025",
    "Recommends AWS Private CA for internal mTLS certificate issuance",
    "Asks whether this is high-volume short-lived certificates — if yes, recommends Private CA Short-lived mode ($50/month vs $400/month general-purpose)",
    "Notes Private CA certs issued via IssueCertificate API are NOT eligible for ACM managed renewal",
    "Recommends separate AWS accounts per CA hierarchy level: root CA account (offline between operations) + intermediate CA account",
    "Suggests EKS: ACM PCA controller or cert-manager with AWSPCA issuer for automated certificate lifecycle in pods"
  ]
}
```

---

## Scenario 6 — Misuse: CloudFront Certificate Region

```json
{
  "skills": ["securing-aws-secrets-certificates"],
  "query": "I requested an ACM certificate for my domain in eu-west-1 and now I can't attach it to my CloudFront distribution. What went wrong?",
  "expected_behavior": [
    "Immediately identifies the root cause: CloudFront requires ACM certificates to be in us-east-1",
    "States this is a HIGH-risk known anti-pattern (CloudFront certificate not in us-east-1)",
    "Provides the correct command: aws acm request-certificate --domain-name example.com --validation-method DNS --region us-east-1",
    "Clarifies that the eu-west-1 certificate can still be used for the ALB in that region (two separate certificates are required: one per service type)",
    "Notes the eu-west-1 certificate cannot be deleted until all associations are removed, and DNS CNAME validation for the new us-east-1 cert must be added to the DNS zone"
  ]
}
```
