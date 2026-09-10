# Evaluation Scenarios — securing-aws-iam-serverless

Skill under test: `securing-aws-iam-serverless`
Research source: `StoryBeat/docs/research_cloud_AWS_IAM_Security_Serverless_2026.md` (2026-08-28)

---

## Scenario 1 — Canonical: Design IAM for a new multi-tenant serverless API

```json
{
  "skills": ["securing-aws-iam-serverless"],
  "query": "I'm building a serverless API on AWS with API Gateway, multiple Lambda functions, and DynamoDB. Each user should only see their own data. How should I design the IAM model?",
  "expected_behavior": [
    "Specifies one dedicated IAM execution role per Lambda function (not one shared role for all functions)",
    "Scopes each execution role to exact actions and specific resource ARNs for that function's DynamoDB table",
    "Recommends Cognito user pool for API Gateway authentication (end-user scenario)",
    "Recommends Cognito identity pool with session tags (aws:PrincipalTag/userId) + DynamoDB LeadingKeys condition for per-user data isolation",
    "Does NOT suggest storing AWS credentials in environment variables",
    "Mentions IAM Access Analyzer for continuous validation"
  ]
}
```

---

## Scenario 2 — Canonical: EventBridge rule triggering Lambda — resource-based policy

```json
{
  "skills": ["securing-aws-iam-serverless"],
  "query": "I have an EventBridge rule that needs to trigger a Lambda function. What IAM configuration do I need and are there any security conditions I should add?",
  "expected_behavior": [
    "Instructs to add a Lambda resource-based policy (AddPermission or PutResourcePolicy) granting events.amazonaws.com invoke permission",
    "Explicitly requires aws:SourceAccount condition (account number of the EventBridge rule owner)",
    "Recommends also adding aws:SourceArn condition scoped to the specific EventBridge rule ARN for tightest scope",
    "Explains the confused-deputy risk: without source conditions, any account configuring EventBridge could invoke the function",
    "Notes that EventBridge IS covered by RCPs (org-level enforcement option) but Lambda is NOT — the resource-based policy is the primary control",
    "Does NOT recommend an open service-principal grant with no conditions"
  ]
}
```

---

## Scenario 3 — Edge Case: CI/CD pipeline deploying Lambda across dev/staging/prod accounts

```json
{
  "skills": ["securing-aws-iam-serverless"],
  "query": "Our GitHub Actions pipeline needs to deploy Lambda functions to three AWS accounts (dev, staging, prod). How should we set up IAM to avoid storing long-lived credentials in GitHub secrets?",
  "expected_behavior": [
    "Recommends OIDC federation: create IAM OIDC identity provider in each account for token.actions.githubusercontent.com",
    "Specifies trust policy must constrain BOTH aud (sts.amazonaws.com) AND sub (repo:Org/Repo:ref:refs/heads/<branch> or environment)",
    "Warns that omitting the sub condition allows any GitHub repository to assume the role (supply-chain risk)",
    "Notes role chaining hard cap of 1 hour if using AssumeRole from the OIDC-assumed role to a target account role",
    "Recommends scoping deployment role permissions to minimum actions needed (Lambda:UpdateFunctionCode, IAM:PassRole on specific ARNs)",
    "Does NOT recommend storing AWS_ACCESS_KEY_ID in GitHub secrets"
  ]
}
```

---

## Scenario 4 — Edge Case: Applying SCPs/RCPs to a multi-account organization

```json
{
  "skills": ["securing-aws-iam-serverless"],
  "query": "We want org-wide guardrails so no external principal can access our S3 buckets, SQS queues, or Lambda functions across all accounts. Can we use RCPs for all of these?",
  "expected_behavior": [
    "Confirms RCPs can enforce org-wide external-access guardrails for S3, SQS, KMS, Secrets Manager, DynamoDB, EventBridge — GA Nov 2024",
    "Explicitly states Lambda functions and SNS topics are NOT covered by RCPs as of August 2026",
    "Provides compensating controls for Lambda: resource-based policies with aws:SourceArn/SourceAccount conditions + SCPs to restrict who can add permissions",
    "Recommends monitoring AWS What's New for RCP service expansion",
    "Advises testing SCP/RCP changes on an isolated account and monitoring CloudTrail AccessDenied events before OU-wide rollout",
    "Notes Sep 2025 full IAM language for SCPs enables condition-based guardrails (e.g., deny S3 access outside business hours)"
  ]
}
```

---

## Scenario 5 — Anti-Pattern Trap: Team requests a shared admin role for all Lambda functions

```json
{
  "skills": ["securing-aws-iam-serverless"],
  "query": "Our dev team wants to use a single IAM role with Action: '*', Resource: '*' for all our Lambda functions to simplify deployment. Is that okay?",
  "expected_behavior": [
    "Clearly identifies this as a critical anti-pattern that violates the least-privilege Security pillar",
    "Explains lateral movement risk: compromise of any one function grants full account access",
    "Does NOT approve the shared admin role under any circumstances",
    "Offers concrete alternative: enumerate specific AWS services each function calls; create one role per function scoped to those actions + resource ARNs",
    "Mentions IAM Access Analyzer policy generation (90-day CloudTrail burn-in) as a practical path to derive minimal per-function policies",
    "Suggests permissions boundary pattern so team can self-service role creation within a guardrail"
  ]
}
```

---

## Scenario 6 — Anti-Pattern Trap: Misapplying RCP to protect Lambda from external access

```json
{
  "skills": ["securing-aws-iam-serverless"],
  "query": "I've attached an RCP to our OU that denies all external-account access to our resources. Do my Lambda functions now have external access protection?",
  "expected_behavior": [
    "Explicitly corrects the misunderstanding: Lambda functions are NOT covered by RCPs as of August 2026",
    "Confirms the RCP does protect S3, SQS, STS, KMS, Secrets Manager, EventBridge, DynamoDB, CloudWatch Logs in the OU",
    "States Lambda must be protected via its own resource-based policy with aws:SourceArn/aws:SourceAccount conditions on any service-principal grant",
    "Recommends enabling IAM Access Analyzer external-access findings per Region to detect unprotected Lambda resource-based policies",
    "Does NOT claim Lambda is automatically protected by the existing RCP",
    "Advises monitoring AWS What's New for Lambda addition to RCP supported services"
  ]
}
```
