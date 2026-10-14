# Evaluation Scenarios — architecting-aws-saas-multitenant

Test cases for `/evaluating-skill-scenarios architecting-aws-saas-multitenant`.

---

## Scenario 1 — Canonical: Tenant Isolation Model Selection

```json
{
  "skills": ["architecting-aws-saas-multitenant"],
  "query": "We are building a B2B SaaS platform on AWS. Most customers are SMBs sharing infrastructure, but we have a handful of enterprise customers requiring dedicated resources for compliance. What tenant isolation model should we use and how should we enforce it?",
  "expected_behavior": [
    "Recommends Bridge model: Pool for SMB tenants, Silo for enterprise/compliance tenants",
    "Specifies enforcement at IAM/data layer (dynamodb:LeadingKeys or RDS row-level security), not just application code",
    "Describes deriving tenant context from JWT claim via Cognito, not from request body",
    "Does NOT recommend single isolation model without acknowledging the mixed-tier requirement"
  ]
}
```

---

## Scenario 2 — Canonical: Per-Tenant Cost Attribution Setup

```json
{
  "skills": ["architecting-aws-saas-multitenant"],
  "query": "Our SaaS platform runs on a shared AWS account with multiple tenants. Finance is asking for a monthly cost-to-serve report per tenant. How do we set this up?",
  "expected_behavior": [
    "Requires cost allocation tags applied at resource creation with tenant ID",
    "Requires activating cost allocation tags in the AWS Billing console",
    "Mentions CloudWatch EMF with tenant ID dimension for operational metering",
    "Recommends aggregating by tier (not per-tenant) when tenant count is very high to control CloudWatch metric cost",
    "References AWS Cost Explorer as the reporting tool"
  ]
}
```

---

## Scenario 3 — Canonical: Automated Tenant Onboarding Pipeline

```json
{
  "skills": ["architecting-aws-saas-multitenant"],
  "query": "Right now an engineer manually clicks through the AWS console to provision each new tenant's Cognito user pool, IAM role, and DynamoDB table. We want to automate this. What is the recommended approach?",
  "expected_behavior": [
    "Identifies manual onboarding as an anti-pattern (AP-6)",
    "Recommends AWS Step Functions orchestrating CloudFormation/CDK for resource provisioning",
    "Specifies the workflow must be idempotent and auditable",
    "Zero manual console steps must remain after automation",
    "Mentions onboarding pipeline as part of the SaaS control plane"
  ]
}
```

---

## Scenario 4 — Edge Case: Sustainability Pillar in SaaS Context

```json
{
  "skills": ["architecting-aws-saas-multitenant"],
  "query": "We are doing a Well-Architected Review for our SaaS product. What does the SaaS Lens say about the Sustainability pillar for multi-tenant architectures?",
  "expected_behavior": [
    "Correctly states that the SaaS Lens (April 4, 2023) does NOT cover the Sustainability pillar",
    "Directs to the base Well-Architected Framework Sustainability pillar guidance",
    "Suggests applying pooling and managed/serverless services to maximize utilization (base-framework guidance)",
    "Does NOT fabricate SaaS-Lens-specific Sustainability best practices"
  ]
}
```

---

## Scenario 5 — Edge Case: Noisy Neighbor in Pool Architecture

```json
{
  "skills": ["architecting-aws-saas-multitenant"],
  "query": "One of our largest tenants is causing Lambda throttling that affects all other tenants on our platform. We use a single shared Lambda function. How do we fix this?",
  "expected_behavior": [
    "Identifies the issue as noisy-neighbor anti-pattern (AP-5)",
    "Recommends Lambda reserved concurrency per tier to isolate compute quota",
    "Recommends API Gateway usage plans with per-tenant or per-tier rate limits",
    "May suggest SQS queue per tenant as a buffer for spiky tenants",
    "Does NOT suggest simply increasing total account concurrency without isolation"
  ]
}
```

---

## Scenario 6 — Misuse / Anti-Pattern Trap: Application-Layer-Only Isolation

```json
{
  "skills": ["architecting-aws-saas-multitenant"],
  "query": "We have a pool DynamoDB table where tenant data is separated by a tenant_id attribute. Our Lambda functions filter by WHERE tenant_id = :tenantId in every query. Is this sufficient for tenant isolation?",
  "expected_behavior": [
    "Flags application-code-only isolation as anti-pattern AP-1",
    "Explains that a single missed filter, injection, or SDK misconfiguration exposes all tenants",
    "Requires dynamodb:LeadingKeys IAM condition key enforcing isolation at the AWS policy layer",
    "Requires tenant ID as the partition key (leading key) of the table",
    "Requires tenant-scoped STS session credentials via AssumeRole, not a shared IAM role",
    "Does NOT endorse the current approach as 'good enough'"
  ]
}
```
