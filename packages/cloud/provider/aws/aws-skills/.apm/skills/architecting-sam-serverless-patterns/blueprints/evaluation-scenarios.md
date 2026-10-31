# Evaluation Scenarios — architecting-sam-serverless-patterns

Skill under test: `architecting-sam-serverless-patterns`
Research date: 2026-09-01 | Currency threshold: 2027-09-01

---

## Scenario 1 — Canonical: Production Three-Tier Serverless Web Application

```json
{
  "skills": ["architecting-sam-serverless-patterns"],
  "query": "Design a production SAM template for a variable-traffic CRUD REST API with authenticated users, DynamoDB, and an async email notification flow. Include observability, safe deployments, and secrets management.",
  "expected_behavior": [
    "Uses AWS::Serverless::HttpApi with Cognito JWT authorizer and stage-level throttling",
    "Declares Globals.Function with Tracing: Active and POWERTOOLS_SERVICE_NAME env var",
    "Sets AutoPublishAlias: live and DeploymentPreference (Canary10Percent5Minutes) with a CloudWatch error alarm and PostTraffic hook",
    "Grants DynamoDB access via DynamoDBCrudPolicy or SAM Connectors — no wildcard IAM",
    "Uses EventInvokeConfig.DestinationConfig.OnFailure on the async email function",
    "References secrets via SECRET_ARN env var pointing to Secrets Manager (not plaintext values)",
    "Uses arm64 architecture and AL2023 runtime identifier (not deprecated AL2 runtimes)",
    "ReservedConcurrentExecutions set on functions accessing downstream resources",
    "Does NOT use a monolithic single-function design for the API"
  ]
}
```

---

## Scenario 2 — Edge Case: Multi-Region Active-Active with Near-Zero RPO

```json
{
  "skills": ["architecting-sam-serverless-patterns"],
  "query": "Our SAM application must achieve RPO near-zero and RTO < 5 minutes across two AWS regions. We use DynamoDB as the primary data store. Describe the architecture and SAM deployment approach.",
  "expected_behavior": [
    "Recommends DynamoDB Global Tables for continuous cross-region replication (near-zero RPO)",
    "Notes that Route 53 DNS TTL (typically 60 s) determines effective RTO and that client-side DNS caching can extend actual RTO beyond the configured TTL",
    "Recommends CloudFront as global entry point to reduce cross-region API Gateway latency",
    "Describes sam pipeline init with multi-region stage configuration to deploy identical SAM stacks per region",
    "Mentions AWS Application Recovery Controller (ARC) for write-to-one-region failover coordination",
    "Notes that active-active vs active-passive topology must be decided upfront",
    "Does NOT claim RTO = Route 53 TTL without caveating client-side DNS cache effects"
  ]
}
```

---

## Scenario 3 — Edge Case: Lambda Cold Start SLA for Java API

```json
{
  "skills": ["architecting-sam-serverless-patterns"],
  "query": "We have a Java 17 Lambda function using a zip package. Our SLA requires P99 < 500 ms including cold starts. What cold start mitigation should we use and how do we configure it in SAM?",
  "expected_behavior": [
    "Recommends SnapStart as first choice for Java 17 with zip packaging",
    "Shows AutoPublishAlias: live and SnapStart: ApplyOn: PublishedVersions in the function properties",
    "Notes that SnapStart has no additional cost for Java runtimes",
    "Warns that PRNG and UUID generation must occur in the handler (not init code) to avoid snapshot reuse issues",
    "Mentions that Provisioned Concurrency should be used only if SnapStart does not meet the SLA",
    "Does NOT suggest container image packaging if SnapStart is required (SnapStart incompatible with container images)",
    "Does NOT recommend keep-warm EventBridge scheduled pings as an official AWS pattern"
  ]
}
```

---

## Scenario 4 — Anti-Pattern Trap: Hardcoded Database Password

```json
{
  "skills": ["architecting-sam-serverless-patterns"],
  "query": "Can I store my RDS password directly in the SAM template under Environment.Variables so the Lambda function can read it from os.environ?",
  "expected_behavior": [
    "Flags this as a CRITICAL security anti-pattern — not just a best practice suggestion",
    "Explains that CloudFormation template environment variables are visible to any IAM principal with CloudFormation read access",
    "Explains that rotation requires code redeployment (operational risk)",
    "Shows the correct pattern: store only the secret ARN in env var, retrieve value at runtime via Powertools Parameters or Lambda Parameters and Secrets Extension",
    "Provides a SAM snippet: SECRET_ARN: !Ref MyDatabaseSecret with AWSSecretsManagerGetSecretValuePolicy",
    "Mentions detection tools: git-secrets pre-commit hook, Checkov, cfn-nag",
    "Does NOT suggest SSM Parameter Store SecureString for credentials requiring rotation (Secrets Manager is the recommendation)"
  ]
}
```

---

## Scenario 5 — Anti-Pattern Trap: Sync Lambda-to-Lambda Chain

```json
{
  "skills": ["architecting-sam-serverless-patterns"],
  "query": "FunctionA needs to call FunctionB and wait for the response before returning to the user. I'm using InvocationType='RequestResponse'. Is this OK for production?",
  "expected_behavior": [
    "Flags synchronous Lambda-to-Lambda chaining as a HIGH-risk anti-pattern",
    "Explains timeout cascade: FunctionB's timeout reduces the available timeout for FunctionA",
    "Explains doubled billing: both functions are billed for the full wait duration",
    "Explains no retry isolation: a transient failure in FunctionB propagates directly to FunctionA",
    "Offers two correct alternatives: (1) FunctionA → SQS queue → FunctionB via ESM for async decoupling, (2) Step Functions Express Workflow for synchronous orchestration with state visibility",
    "Mentions X-Ray Service Map as detection tool for direct Lambda-to-Lambda trace segments"
  ]
}
```

---

## Scenario 6 — Edge Case: First Deployment with DeploymentPreference

```json
{
  "skills": ["architecting-sam-serverless-patterns"],
  "query": "I added AutoPublishAlias and DeploymentPreference to my SAM template and ran sam deploy for the first time. The deployment failed with a CodeDeploy error about no previous version. How do I fix this?",
  "expected_behavior": [
    "Correctly identifies this as the known first-deployment constraint for DeploymentPreference",
    "Explains that CodeDeploy requires a prior Lambda function version to shift traffic from — which does not exist on first deploy",
    "Instructs to: remove DeploymentPreference block, run sam deploy (first deploy without gradual shifting), then add DeploymentPreference back for all subsequent deploys",
    "Notes that AutoPublishAlias alone can remain on the first deploy — only DeploymentPreference must be deferred",
    "Does NOT suggest switching to AllAtOnce strategy as a permanent workaround for this constraint"
  ]
}
```
