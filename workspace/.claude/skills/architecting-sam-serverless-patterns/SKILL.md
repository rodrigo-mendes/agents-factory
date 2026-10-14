---
name: architecting-sam-serverless-patterns
description: "Architects and deploys serverless web applications on AWS using SAM 2026 (AWS::Serverless-2016-10-31 transform). Covers least-privilege IAM, safe deployments, observability, cold-start mitigation, and async resilience patterns. Use when designing, implementing, or reviewing SAM-based serverless applications targeting AL2023 runtimes."
---

## Function

Specialist in AWS Serverless Application Model (SAM) 2026 architecture patterns, covering the SAM Template Specification, SAM CLI toolchain, Lambda compute, API Gateway, DynamoDB, and Well-Architected Serverless Lens guardrails for production web applications.

## Version Context

**Technology**: AWS SAM (AWS::Serverless-2016-10-31 transform)
**Target version**: SAM 2026 / AWS Lambda AL2023
**Release date**: 2026-09-01 (research currency threshold: 2027-09-01)
**Support status**: Active

**Critical changes in this version**:
- Amazon Linux 2 reached EOL June 30, 2026 — AL2-based runtimes (`nodejs20.x`, `python3.10`, `java17`, `java11`) are deprecated; target AL2023 identifiers
- Lambda Durable Functions (`DurableConfig`) GA December 2025 — year-long executions with checkpointing; supported runtimes: Python 3.13/3.14, Node.js 22/24, Java 17+
- `AWS::Serverless::WebSocketApi` added May 2026 — SAM-native WebSocket API support
- SnapStart expanded to Python 3.12+ and .NET 8+ (November 2024)
- SQS ESM Provisioned mode: `MinimumPollers`/`MaximumPollers` for up to 100,000 concurrent invocations
- `sam sync --express` mode defaults to enabled from September 1, 2026

**Deprecated**: All AL2-based runtime identifiers (nodejs20.x, python3.10, java17, java11)

⚠️ **CRITICAL — Agent Warning**:
This skill targets SAM 2026 with AL2023 runtimes.
Reject patterns using deprecated AL2 runtime identifiers.
Do not mix SAM Connectors with hand-authored IAM wildcard policies.

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — ✅⚠️🚫 mandatory, decision, anti-pattern summaries
- **[Integration Patterns](#integration-patterns)** — async, orchestration, edge protection compositions
- **[Verification Loop](#verification-loop)** — post-generation validation commands
- **[Quick Reference](#quick-reference)** — essential commands and critical limits
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 6 test cases (canonical, edge, misuse)
- **[External Resources](#external-resources)** — official AWS documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

**1. Least-Privilege IAM via SAM Policy Templates and SAM Connectors** (Security, CRITICAL)
Use `DynamoDBCrudPolicy: {TableName: !Ref MyTable}` or `AWS::Serverless::Connector` with `Permissions: [Read|Write]` for all function-to-service permissions. SAM generates resource-scoped IAM policies at transform time. Never attach AWS managed policies (`AmazonDynamoDBFullAccess`) or inline `Action: "*"`.
```yaml
MyFunction:
  Type: AWS::Serverless::Function
  Properties:
    Policies:
      - DynamoDBCrudPolicy:
          TableName: !Ref MyTable
  Connectors:
    ToQueue:
      Properties:
        Destination: {Id: MyQueue}
        Permissions: [Write]
```

**2. X-Ray Active Tracing with Lambda Powertools** (Operational Excellence)
Set `Tracing: Active` in `Globals.Function`. Use Powertools Logger (structured JSON → CloudWatch Logs Insights), Tracer (`@tracer.capture_lambda_handler` → X-Ray subsegments + SDK auto-instrumentation), and Metrics (EMF — zero synchronous CloudWatch API calls).
```yaml
Globals:
  Function:
    Tracing: Active
    Environment:
      Variables:
        POWERTOOLS_SERVICE_NAME: my-service
        LOG_LEVEL: INFO
```
Choose Application Signals (ADOT, zero-code) OR Powertools Tracer (code-first, decorator). They conflict — do not combine.

**3. Safe Deployments via CodeDeploy with Canary/Linear Strategies** (Reliability)
Combine `AutoPublishAlias` + `DeploymentPreference` + CloudWatch error rate alarm + PostTraffic integration test hook. SAM auto-creates the CodeDeploy deployment group. Supported strategies: `Canary10Percent5Minutes`, `Canary10Percent15Minutes`, `Linear10PercentEvery1Minute`, `Linear10PercentEvery10Minutes`, `AllAtOnce`.
⚠️ First deployment must omit `DeploymentPreference` — CodeDeploy requires a prior version; add on the second deploy.
```yaml
MyFunction:
  Type: AWS::Serverless::Function
  Properties:
    AutoPublishAlias: live
    DeploymentPreference:
      Type: Canary10Percent5Minutes
      Alarms: [!Ref MyFunctionErrorAlarm]
      Hooks:
        PostTraffic: !Ref PostTrafficHookFunction
```

**4. Reserved Concurrency on Functions Accessing Downstream Resources** (Reliability)
Set `ReservedConcurrentExecutions` on every function calling RDS, DynamoDB, or any service with connection/throughput limits. Baseline with CloudWatch `ConcurrentExecutions` metric. Formula: `concurrency = avg_req_per_sec × avg_duration_sec`. Setting to `0` is an emergency kill switch.

**5. Idempotent Function Design with On-Failure Destinations** (Reliability, CRITICAL)
Set `EventInvokeConfig.DestinationConfig.OnFailure` on every async-triggered function — on-failure destinations carry the full invocation record (payload + response + error reason), unlike a DLQ which carries only the raw event. For idempotency, use Powertools Idempotency backed by a DynamoDB table (`partition_key: id`, `TTL attribute: expiration`, default TTL: 3600 s). Cost: 2 DynamoDB WCUs per non-idempotent call.

**6. Authorization and Throttling on All Public API Endpoints** (Security + Reliability, CRITICAL)
Every public endpoint needs an authorizer AND stage-level throttling. Greenfield: Cognito User Pool + HTTP API JWT authorizer. WAF evaluation order: **WAF → resource policies → IAM → Lambda authorizers → Cognito**. Attach WAF Regional ACL to API Gateway stage AND WAF Global ACL to CloudFront for defense in depth.

---

### ⚠️ Ask First

**1. API Layer — HTTP API vs REST API vs Function URL vs ALB**
Ask: "Does the API need WAF direct attachment, per-client API keys, response caching, or private VPC endpoint?"

| Option | Cost/M calls | Key Capability | Use When |
|--------|-------------|----------------|----------|
| HTTP API (v2) | $1.00 | Native JWT, auto-deploy, OIDC | Greenfield web/mobile with Cognito — default choice |
| REST API (v1) | $3.50 | WAF direct, API keys, caching, private endpoint | Monetised public API; compliance requiring WAF on APIGW |
| Function URL | $0 API cost | Simplest setup, dual-stack IPv6 | Single-function webhook; IAM_AUTH service-to-service |
| ALB + Lambda | Fixed hourly | Mixed EC2/ECS/Lambda routing | Hybrid workloads already using ALB |

REST ↔ HTTP API migration requires full redeploy — choose upfront.

**2. Compute Packaging — zip vs container image**
Ask: "Is SnapStart required? Are there large classpath dependencies or custom OS binaries?"

| Option | Constraint | Use When |
|--------|-----------|----------|
| Zip | Max 250 MB uncompressed, no custom OS | Python/Node.js; SnapStart-compatible; SAM default |
| Container image (OCI) | Up to 10 GB; ECR cost; SnapStart NOT available | Java/.NET large classpath; container-standardised CI |

Packaging type is **immutable after function creation** — decide before first deploy.

**3. Compute Architecture — arm64 vs x86_64**
Ask: "Do all third-party native dependencies and Lambda Layers provide arm64 builds?"
arm64 (Graviton2): better price-performance; default for SAM 2026 greenfield.
x86_64: universal binary compatibility; use only when arm64 builds unavailable for a dependency.

**4. Data Store — DynamoDB vs Aurora Serverless v2 + RDS Proxy vs RDS provisioned**
Ask: "Are complex SQL joins or ACID transactions across multiple tables required?"
- No → DynamoDB on-demand (no TCP connection overhead on cold start; auto-scales with Lambda burst)
- Yes → Aurora Serverless v2 + RDS Proxy (SQL, fine-grained capacity scaling; connection pooling required)
- Steady-state high-concurrency → RDS provisioned + RDS Proxy (reduces failover time up to 66%)

**5. Cold Start Mitigation — SnapStart vs Provisioned Concurrency vs none**
Ask: "What is the P99 latency SLA? Which runtime? Is container image packaging used?"

| Option | Idle Cost | Runtimes | Constraint |
|--------|----------|----------|------------|
| SnapStart | None (Java); min 3 h cache (Python/.NET) | Java 11+, Python 3.12+, .NET 8+ | Not for container images, EFS, ephemeral >512 MB |
| Provisioned Concurrency | Per GB-second continuously | All runtimes | Cannot combine with SnapStart; cannot use on $LATEST |
| None ($LATEST) | None | All | Tolerate >1 s cold starts |

Recommendation: SnapStart first; Provisioned Concurrency only when SnapStart cannot meet requirements.

---

### 🚫 Never Do

**1. Wildcard IAM Policies** (Risk: CRITICAL)
Using `Action: "*", Resource: "*"` or AWS managed policies (`AmazonDynamoDBFullAccess`) gives a compromised function full account blast radius.
Use SAM Policy Templates (`DynamoDBCrudPolicy: {TableName: !Ref MyTable}`) or SAM Connectors (`Permissions: [Write]`) instead.
Detection: IAM Access Analyzer, `cfn-lint` security rules, AWS Security Hub CSPM Lambda controls.

**2. Secrets Hardcoded in SAM Template Environment Variables** (Risk: CRITICAL)
Secrets in template `Environment.Variables` are visible to any IAM principal with CloudFormation read access; rotation requires code redeployment.
Store only the secret ARN in environment variables; retrieve the value at runtime via Powertools Parameters or the Lambda Parameters and Secrets Extension:
```yaml
Environment:
  Variables:
    SECRET_ARN: !Ref MyDatabaseSecret  # ARN only; not the value
```
Detection: `git-secrets` pre-commit hook; Checkov / `cfn-nag` static scanning; AWS Macie.

**3. No On-Failure Destination on Async Invocations** (Risk: CRITICAL)
Async invocations without `EventInvokeConfig.DestinationConfig.OnFailure` silently drop failed events after Lambda's built-in retries. No alerts, no recovery path — data loss on every transient error.
Always set `DestinationConfig.OnFailure` (SQS, SNS, S3, or EventBridge). FIFO queues and FIFO SNS are NOT supported as destinations.
Detection: `aws lambda get-function-event-invoke-config --function-name <name>` — absence of `DestinationConfig`.

**4. Synchronous Lambda-to-Lambda Chaining** (Risk: HIGH)
`lambda_client.invoke(FunctionName='B', InvocationType='RequestResponse')` causes timeout cascades, doubled billing, and no retry isolation.
Route via SQS Event Source Mapping (decoupled, retries isolated) or Step Functions Express Workflow (synchronous orchestration with state visibility).
Detection: AWS X-Ray Service Map — direct Lambda-to-Lambda trace segments.

**5. No Throttling or Authorization on Public API Endpoints** (Risk: CRITICAL)
An unauthenticated, unthrottled public API allows unbounded Lambda invocations — exhausts account concurrency, incurs runaway cost, and creates a DDoS vector.
Always set `Auth.DefaultAuthorizer` and `MethodSettings.ThrottlingBurstLimit`/`ThrottlingRateLimit` on every public stage.
Detection: `aws apigateway get-method` → `authorizationType: NONE`; AWS Security Hub control `APIGateway.1`.

**6. Monolithic Lambda ("Lambdalith") as Permanent Architecture** (Risk: HIGH)
A single function with all routes prevents per-route independent scaling, right-sizing memory, and safe canary deployments. `DeploymentPreference` is less precise across a large application surface.
Decompose into bounded-context functions, each with appropriate `MemorySize`, `Timeout`, and `ReservedConcurrentExecutions`. A Lambdalith is acceptable only as a time-boxed migration step with a documented remediation deadline.
Detection: SAM template with one function and many API event sources; `MemorySize: 3008` compensating for bloat.

---

## Integration Patterns

**Async / Event-Driven** — EventBridge as domain event bus (fan-out to multiple targets) + SQS standard queue (durable buffer for Lambda ESM). Lambda returns HTTP 202 immediately on async invocation. Configure `FunctionResponseTypes: [ReportBatchItemFailures]` on SQS ESM to prevent re-processing successful records in a failed batch. Set DLQ on the SQS queue itself (not on the Lambda function) when SQS is the event source.

**Orchestration Decision** — Step Functions Standard Workflows (exactly-once, full audit history 90 days, up to 1 year, fan-out/Distributed Map) vs Express Workflows (at-least-once/at-most-once, up to 5 minutes, CloudWatch Logs only) vs EventBridge Choreography (no duration limit, loose coupling, no central coordinator). Workflow type is **immutable after creation** — choose before first deploy.

**Long-Running Sequential Flows** — Lambda `DurableConfig` (GA December 2025) for sequential flows up to 1 year with automatic checkpointing and no Step Functions overhead. Cannot be added to existing functions — must be set at creation. Use Step Functions Standard for fan-out, complex branching, or exactly-once semantics.

**Secrets at Runtime** — Use Lambda Parameters and Secrets Extension (local HTTP endpoint, no SDK call) or Powertools Parameters for cold-start secret retrieval. Store ARN in environment variable; fetch value in init code (outside handler) for warm reuse.

**Common Problems**:
- **`CAPABILITY_AUTO_EXPAND` missing** → direct CloudFormation deployment of SAM templates fails; always add alongside `CAPABILITY_IAM` and `CAPABILITY_NAMED_IAM`
- **SnapStart + Provisioned Concurrency** → cannot be combined; choose one
- **Application Signals + Powertools Tracer** → conflict; choose one observability approach per function
- **DurableConfig on existing function** → not supported; must be set at function creation

---

## Verification Loop

Run after every code-generation or template modification:

### 1. SAM Validate
```bash
sam validate --lint
# Expected: "Template is valid" with no warnings
# Exit code: 0
```

### 2. SAM Build
```bash
sam build
# Expected: "Build Succeeded" with all functions listed
# Exit code: 0
```

### 3. Security Checks
```bash
cfn-lint template.yaml --include-checks I
# Expected: 0 errors; review warnings
aws iam simulate-principal-policy \
  --policy-source-arn <function-role-arn> \
  --action-names dynamodb:DeleteTable \
  --resource-arns "*"
# Expected: "implicitDeny" for overly broad actions
```

### 4. Deployment Verification
```bash
aws lambda get-function-event-invoke-config --function-name <name>
# Expected: DestinationConfig.OnFailure set for all async functions
aws apigateway get-method --rest-api-id <id> --resource-id <id> --http-method GET
# Expected: authorizationType != "NONE"
aws lambda get-function-configuration --function-name <name> --query 'TracingConfig'
# Expected: {Mode: "Active"}
```

**Troubleshooting**:
- `CAPABILITY_AUTO_EXPAND` error → add to `sam deploy --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND CAPABILITY_NAMED_IAM`
- `DeploymentPreference` failure on first deploy → remove `DeploymentPreference` block; deploy once without it; add on second deploy
- `DurableConfig` rejected → function was created without it; must be recreated
- SnapStart init generates same UUID per invocation → move PRNG/UUID generation into handler, not init code

---

## Quick Reference

**Essential commands**:
```bash
sam init --app-template hello-world-powertools-python  # bootstrap with Powertools
sam build                                               # compile + package all functions
sam validate --lint                                     # template + cfn-lint validation
sam sync --watch                                        # sub-second dev loop (dev stack only)
sam deploy --guided                                     # first deploy with samconfig.toml generation
sam pipeline init                                       # generate CI/CD (GitHub Actions, CodePipeline, GitLab)
```

**Critical limits**:

| Resource | Limit | Notes |
|----------|-------|-------|
| Lambda zip (uncompressed) | 250 MB | Container images: up to 10 GB |
| Lambda timeout | 900 s | DurableConfig: up to 31,622,400 s |
| Lambda concurrency (account default) | 1,000 | Adjustable; `ReservedConcurrentExecutions: 0` = kill switch |
| SQS ESM batch size | 10,000 msg | Provisioned mode: up to 100,000 concurrent invocations |
| SnapStart caching (Python/.NET) | Minimum 3 hours per version | Java: no additional cost |
| Powertools Idempotency DynamoDB item | 400 KB | Function response must be smaller |
| WAF request body inspection | 16 KB default; up to 64 KB configurable | |
| JWT JWKS public key cache | 2 hours | HTTP API JWT authorizer |

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/architecting-sam-serverless-patterns/
├── SKILL.md                              <- This file (summary + guardrails)
└── blueprints/
    └── evaluation-scenarios.md           <- 6 test cases (canonical, edge, misuse)
```

---

## External Resources

### Official Documentation (all dated 2026-09-01)
- [SAM Developer Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html) — Primary SAM reference
- [SAM Policy Templates](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-policy-templates.html) — 60+ named policy snippets
- [SAM Connectors](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam-connector.html) — Intent-based IAM
- [Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html) — Well-Architected guardrails source
- [Lambda SnapStart](https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html) — Supported runtimes, cost model
- [DurableConfig Property](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-property-function-durableconfig.html) — GA December 2025
- [SAM DeploymentPreference](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/automating-updates-to-serverless-apps.html) — Canary/Linear strategies
- [Lambda Async Invocation Records](https://docs.aws.amazon.com/lambda/latest/dg/invocation-async-retain-records.html) — On-failure destinations
- [HTTP API JWT Authorizer](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html) — Cognito JWT flow
- [HTTP API vs REST API](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html) — Feature comparison
- [Serverless Multi-Tier Architectures Whitepaper](https://docs.aws.amazon.com/whitepapers/latest/serverless-multi-tier-architectures-api-gateway-lambda/serverless-multi-tier-architectures-api-gateway-lambda.pdf) — Reference architecture
