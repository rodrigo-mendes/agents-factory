# AWS Well-Architected Framework — Serverless Applications Lens Knowledge Base

---

## Metadata

```yaml
Full_Name: "AWS Well-Architected Framework — Serverless Applications Lens"
Cloud_Provider: "AWS"
Architecture_Domain: "Well-Architected Serverless"
Target_Edition: "AWS WAF Serverless Lens 2024"
Architecture_Context: "Production serverless applications on AWS leveraging Lambda, API Gateway, DynamoDB, SQS, SNS, EventBridge, Step Functions, S3, CloudFront, Route 53, and Cognito — covering event-driven architectures, synchronous APIs, asynchronous processing, orchestrated workflows, and global distribution patterns"
Official_Source_URL: "https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/welcome.html"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-05-28"
Currency_Threshold: "2027-05-28 — review required after this date due to AWS serverless service evolution velocity"
```

---

## Executive Summary

The AWS Well-Architected Framework Serverless Applications Lens extends the six standard Well-Architected pillars with serverless-specific guidance for designing, deploying, and operating production workloads on AWS's managed event-driven compute, storage, and integration services. Unlike traditional cloud architectures where infrastructure management dominates operational effort, serverless architectures shift responsibility entirely to service composition, event flow design, and operational observability — making architecture decisions (not infrastructure decisions) the primary determinant of quality outcomes.

The 2024 edition of the Serverless Lens reflects a matured serverless ecosystem where: (1) **Lambda SnapStart** (Java/Python/Node.js) replaces Provisioned Concurrency as the default cold start mitigation strategy, fundamentally simplifying the performance efficiency pillar guidance; (2) **Step Functions JSONata, Variables, and HTTPS Endpoints** eliminate entire categories of "glue Lambda functions" — reducing function count, operational surface, and cost for orchestrated workflows; (3) **EventBridge Pipes** consolidates filtering, enrichment, and routing that previously required custom Lambda code into a managed point-to-point integration; (4) **Lambda Advanced Logging Controls** and **CloudWatch Logs JSON format** make structured logging a configuration decision rather than a code implementation effort. These shifts collectively reduce the Lambda function count in well-designed architectures by 30–50% compared to 2022-era patterns, directly improving the security posture (fewer IAM roles), cost profile (fewer invocations), and operational simplicity (fewer components to monitor).

The three most critical architecture guardrails across all pillars for serverless workloads are: (1) **every asynchronous invocation path must have an explicit failure destination** — the silent discard of failed events after retry exhaustion is the #1 data loss vector in serverless architectures; (2) **every Lambda function must have a dedicated, least-privilege execution role with explicit resource ARNs** — shared roles with wildcard permissions are the #1 security anti-pattern; (3) **all handlers must be idempotent** — Lambda's invocation models guarantee at-least-once delivery for async and poll-based patterns, making duplicate processing a certainty over time, not a possibility.

---

## Cloud Architecture Glossary

```
Term: Serverless Applications Lens
Definition: A supplemental perspective within the AWS Well-Architected Framework that provides serverless-specific best practices, assessment questions, and architecture patterns across all six WAF pillars. The Lens assumes workloads built primarily with Lambda, API Gateway, DynamoDB, S3, Step Functions, SQS, SNS, EventBridge, and Kinesis.
Provider Docs Section: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/welcome.html
Architect Usage: Use the Serverless Lens as the primary architecture review framework for workloads where >70% of compute is serverless. Conduct Serverless Lens reviews at design time (architecture decision records), pre-launch (Well-Architected Review), and quarterly (operational reviews).
Common Confusion: The Serverless Lens is not a replacement for the base Well-Architected Framework — it supplements it. All six base pillar guidelines still apply; the Lens adds serverless-specific interpretation and assessment questions.

Term: Event-Driven Architecture (EDA)
Definition: An architectural style where state changes (events) are produced, detected, consumed, and reacted to by loosely coupled services. In AWS serverless context, events flow between services (S3 → Lambda, DynamoDB Streams → Lambda, EventBridge → Step Functions) via managed event sources without direct service-to-service coupling.
Provider Docs Section: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/event-driven-architectures.html
Architect Usage: EDA is the default architectural style for serverless workloads. Design around events (facts that happened) not commands (requests to do something). Use EventBridge as the central event bus. Use SQS for command-style point-to-point messaging. Use Kinesis for ordered, replayable event streams.
Common Confusion: Event-driven ≠ asynchronous-only. Synchronous request-response APIs (API Gateway → Lambda) coexist with asynchronous event flows in the same architecture. EDA refers to the inter-service communication pattern, not the user-facing interaction model.

Term: Invocation Model
Definition: The mechanism by which Lambda receives events. Three models: Synchronous (caller waits — API Gateway, ALB, SDK), Asynchronous (Lambda queues internally with 0–2 retries — S3, SNS, EventBridge), and Poll-based (Lambda polls event source — SQS, Kinesis, DynamoDB Streams). Each model has distinct error handling, retry, and scaling characteristics.
Provider Docs Section: https://docs.aws.amazon.com/lambda/latest/dg/lambda-invocation.html
Architect Usage: The invocation model determines the entire error handling strategy. Synchronous: caller must handle errors. Asynchronous: configure DLQ/on-failure destination. Poll-based: configure bisect-on-error, max retries, and failure destination on the Event Source Mapping.
Common Confusion: The invocation model is determined by the event source, not by the function code. The same Lambda function can be invoked synchronously by API Gateway and asynchronously by EventBridge simultaneously — requiring both error handling strategies.

Term: Serverless Composition
Definition: The practice of composing multiple managed AWS services (Lambda, DynamoDB, SQS, Step Functions, EventBridge, API Gateway) into an application architecture where no single service handles all responsibilities. Each service is selected for its specific capability — compute (Lambda), state (DynamoDB), routing (EventBridge), orchestration (Step Functions), API management (API Gateway).
Provider Docs Section: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/design-principles.html
Architect Usage: Prefer service composition over custom code. Use DynamoDB TTL instead of Lambda cron for expiration. Use Step Functions instead of Lambda-calling-Lambda for workflows. Use EventBridge rules instead of Lambda filters for routing. Use API Gateway direct integrations instead of Lambda pass-throughs for simple AWS service calls.
Common Confusion: Serverless ≠ Lambda-only. Over-using Lambda (Lambda as glue for every integration) is an anti-pattern. The Well-Architected Serverless Lens explicitly recommends direct service integrations (API Gateway → DynamoDB, Step Functions → DynamoDB, EventBridge Pipes) to reduce Lambda function count.

Term: Blast Radius
Definition: The scope of impact when a failure, misconfiguration, or security breach occurs. In serverless architectures, blast radius is managed through: per-function IAM roles (security blast radius), reserved concurrency (availability blast radius), separate DLQs per event source (data loss blast radius), and multi-account isolation (organizational blast radius).
Provider Docs Section: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/reliability.html
Architect Usage: Every architecture decision should be evaluated for blast radius. Sharing IAM roles across functions maximizes security blast radius. Sharing the default concurrency pool maximizes availability blast radius. A single account for all environments maximizes organizational blast radius.
Common Confusion: Blast radius in serverless is often underestimated because there are no servers to fail. But IAM role compromise, concurrency exhaustion, and poison-pill events can cascade across all functions in an account — the blast radius is the AWS account, not a single server.

Term: Direct Service Integration
Definition: An API Gateway or Step Functions configuration that invokes an AWS service (DynamoDB, SQS, SNS, S3, etc.) directly via the AWS SDK without a Lambda function intermediary. API Gateway uses VTL mapping templates or HTTP proxy. Step Functions uses SDK service integrations (200+ supported services).
Provider Docs Section: https://docs.aws.amazon.com/step-functions/latest/dg/concepts-service-integrations.html
Architect Usage: Use direct integrations when the operation is a simple pass-through (API Gateway → DynamoDB PutItem, Step Functions → SQS SendMessage). Eliminates a Lambda function (reduces cost, latency, IAM surface, and operational complexity). Reserve Lambda for business logic that cannot be expressed in VTL/ASL.
Common Confusion: Direct integrations are not "less powerful" — they are more reliable because they remove a failure point (Lambda function) from the invocation path. However, they lack custom error handling and complex transformation capabilities that Lambda provides.

Term: Well-Architected Review (Serverless)
Definition: A structured assessment process using the Serverless Lens questionnaire to evaluate a serverless workload against best practices across all six pillars. Produces a list of High Risk Issues (HRIs) and Medium Risk Issues (MRIs) with remediation guidance. Can be conducted via the AWS Well-Architected Tool in the console or via the API.
Provider Docs Section: https://docs.aws.amazon.com/wellarchitected/latest/userguide/lenses-custom.html
Architect Usage: Conduct a Serverless Lens review before production launch and quarterly thereafter. Focus remediation on HRIs first. Use the AWS Well-Architected Tool to track improvement plans. Share results with security and operations teams.
Common Confusion: A Well-Architected Review is not an audit — it is a self-assessment. There is no pass/fail. The goal is to identify improvement opportunities, not to achieve a score. The review should be conducted by the team that owns the workload, not by an external auditor.

Term: Function Composition Pattern
Definition: The architectural approach to structuring Lambda functions within a service. Options: single-purpose function (one handler per API route), fat function (one handler with internal routing for multiple related routes), Lambda-lith (entire application in one function). The Serverless Lens recommends single-purpose functions grouped by domain resource.
Provider Docs Section: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/operational-excellence.html
Architect Usage: Group functions by domain entity (OrderFunction handles create/get/update order). Each function group gets its own IAM role scoped to its domain resources. Avoid Lambda-lith (entire monolith in one function) — it defeats the purpose of serverless granular scaling and deployment.
Common Confusion: "Single-purpose function" does not mean one Lambda per API route. It means one Lambda per logical domain operation group. Having 50 Lambda functions for 50 API routes is over-granular. Having 5 Lambda functions for 5 domain aggregates (Orders, Users, Products, Payments, Notifications) is optimal.

Term: Serverless Event Fork Pipeline
Definition: An architecture pattern where a single event triggers multiple independent processing paths via SNS fan-out or EventBridge rule matching. Each fork processes the event for a different purpose (analytics, storage, notification, enrichment) independently and in parallel.
Provider Docs Section: https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-data-persistence/event-fork-pipeline.html
Architect Usage: Use when a single domain event (e.g., "OrderPlaced") must trigger independent downstream actions (send confirmation email, update inventory, write to analytics). Each fork has its own SQS queue, DLQ, Lambda function, and IAM role — failures in one fork do not affect others.
Common Confusion: Event fork ≠ Lambda calling multiple services sequentially. In a fork pipeline, the fan-out service (SNS/EventBridge) delivers the event to all forks simultaneously. In sequential processing, one Lambda calls services one-by-one — creating coupling and cascading failure risk.

Term: Throttling vs Concurrency Limit
Definition: Throttling is the rejection of Lambda invocations when the configured concurrency limit (reserved or account) is reached. Throttled invocations receive a 429 TooManyRequestsException. For synchronous invocations, the caller receives the error. For asynchronous invocations, Lambda retries internally (up to configured retry count). For poll-based invocations, Lambda reduces polling rate.
Provider Docs Section: https://docs.aws.amazon.com/lambda/latest/dg/invocation-scaling.html
Architect Usage: Distinguish between deliberate throttling (reserved concurrency as a circuit breaker) and unintentional throttling (account limit exhaustion). Monitor the Throttles CloudWatch metric and alarm on > 0. Use reserved concurrency both as protection (for critical functions) and as a cap (for high-volume functions that should not consume the entire pool).
Common Confusion: Throttling ≠ cold start. Throttling rejects the invocation entirely (429 error). Cold start delays the invocation (higher latency). They are completely different phenomena with different causes and different solutions. Provisioned Concurrency addresses cold starts; Reserved Concurrency addresses throttling risk.
```

---

## Architecture Framework Analysis: AWS Well-Architected Serverless Lens (2024 Edition)

### Pillar 1: Operational Excellence

```
Pillar: Operational Excellence
Definition: The ability to run and monitor serverless systems to deliver business value and to continually improve supporting processes and procedures.
Key Design Principles:
  - Perform operations as code (IaC for all serverless resources — SAM, CDK, Terraform)
  - Make frequent, small, reversible changes (Lambda aliases + CodeDeploy canary)
  - Refine operations procedures frequently (runbook automation, chaos engineering)
  - Anticipate failure (DLQ for every async path, on-failure destinations, Step Functions Catch)
  - Learn from all operational failures (structured logs, distributed traces, post-mortems)
  - Use managed services to reduce operational burden (direct integrations over custom Lambda glue)
Applies To Serverless Production Workloads:
  Serverless operational excellence requires: (1) structured JSON logging via Lambda Advanced Logging Controls + Powertools, (2) distributed tracing via X-Ray/ADOT across all service boundaries, (3) deployment automation via SAM/CDK with CodeDeploy canary and auto-rollback, (4) per-function CloudWatch alarms (Errors, Throttles, Duration, IteratorAge), (5) IaC for ALL resources including IAM roles, DLQs, alarms, and dashboards.
Assessment Questions:
  1. Are all serverless resources defined in IaC with environment parity (dev/staging/prod)?
  2. Is structured JSON logging with correlation IDs implemented across all Lambda functions?
  3. Are deployments automated with canary traffic shifting and alarm-triggered rollback?
  4. Is there a runbook for DLQ message investigation and replay?
  5. Are CloudWatch dashboards and alarms defined for all critical service metrics?
Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/operational-excellence.html
```

### Pillar 2: Security

```
Pillar: Security
Definition: The ability to protect data, systems, and assets while delivering business value through risk assessments and mitigation strategies.
Key Design Principles:
  - Implement a strong identity foundation (per-function IAM roles, Cognito for user auth)
  - Enable traceability (CloudTrail for Lambda API calls, X-Ray for invocation chains)
  - Apply security at all layers (WAF on API Gateway, IAM auth, VPC for private resources)
  - Automate security best practices (Security Hub, GuardDuty, Config rules, automated remediation)
  - Protect data in transit and at rest (KMS for environment variables, TLS for all communications)
  - Keep people away from data (no direct prod access, automated incident response)
  - Prepare for security events (runbooks, GuardDuty findings → Lambda auto-remediation)
Applies To Serverless Production Workloads:
  Serverless security pillar mandates: (1) per-function execution roles with explicit resource ARNs — never wildcard permissions, (2) secrets in Secrets Manager/Parameter Store — never in environment variables or code, (3) WAF web ACL on all internet-facing API Gateway stages, (4) Cognito or Lambda authorizers on every API route, (5) Amazon Inspector scanning Lambda functions for dependency CVEs, (6) code signing via AWS Signer for deployment integrity.
Assessment Questions:
  1. Does each Lambda function have its own execution role with minimum required permissions?
  2. Are all secrets fetched from Secrets Manager/Parameter Store — never stored as plaintext environment variables?
  3. Is WAF attached to all public-facing API Gateway stages/CloudFront distributions?
  4. Are all API routes protected by authorization (IAM, Cognito, Lambda authorizer)?
  5. Is Amazon Inspector enabled for Lambda function vulnerability scanning?
Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/security.html
```

### Pillar 3: Reliability

```
Pillar: Reliability
Definition: The ability of a serverless workload to perform its intended function correctly and consistently when it's expected to.
Key Design Principles:
  - Design for failure (every async path has a DLQ/destination, every handler is idempotent)
  - Test recovery procedures (DLQ draining runbooks, event replay procedures)
  - Scale horizontally (Lambda scales automatically — design for stateless handlers)
  - Stop guessing capacity (use on-demand DynamoDB, monitor reserved concurrency headroom)
  - Manage change in automation (alias-based deployments, automated rollback)
  - Isolate blast radius (per-function reserved concurrency, per-service DLQ, multi-account)
Applies To Serverless Production Workloads:
  Serverless reliability depends on: (1) idempotent handlers — mandatory for async/poll-based invocations with retries, (2) DLQ/on-failure destination for EVERY async invocation path, (3) bisect-on-batch-item-failure for all Event Source Mappings (Kinesis, DynamoDB Streams, SQS), (4) reserved concurrency to isolate critical functions from account-level exhaustion, (5) DynamoDB Point-in-Time Recovery enabled for all production tables.
Assessment Questions:
  1. Is every Lambda handler designed to be idempotent (safe for duplicate invocations)?
  2. Is there a DLQ or on-failure destination for every asynchronous invocation path?
  3. Is bisect-on-batch-item-failure enabled for all stream-based Event Source Mappings?
  4. Are reserved concurrency limits set for both critical and high-volume functions?
  5. Is DynamoDB PITR enabled for all production tables?
Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/reliability.html
```

### Pillar 4: Performance Efficiency

```
Pillar: Performance Efficiency
Definition: The ability to use computing resources efficiently to meet system requirements and to maintain that efficiency as demand changes and technologies evolve.
Key Design Principles:
  - Democratize advanced technologies (use managed services — no custom polling code)
  - Go global in minutes (Lambda@Edge, CloudFront Functions, DynamoDB Global Tables)
  - Use serverless architectures (Lambda over EC2 for irregular workloads)
  - Experiment more often (Lambda Power Tuning for memory optimization)
  - Consider mechanical sympathy (runtime selection, arm64, package size, Init code optimization)
  - Eliminate Lambda glue (direct integrations, Step Functions JSONata, EventBridge Pipes)
Applies To Serverless Production Workloads:
  Performance efficiency requires: (1) Lambda Power Tuning for all CPU-intensive functions before production, (2) SnapStart as first-line cold start mitigation for Java/Python/Node.js, (3) arm64 (Graviton2) as default architecture for 20% better price-performance, (4) VPC attachment only when genuinely required for private resource access, (5) direct service integrations to eliminate Lambda intermediaries where business logic is unnecessary.
Assessment Questions:
  1. Have all production Lambda functions been profiled with Lambda Power Tuning?
  2. Is SnapStart enabled for latency-sensitive synchronous functions on supported runtimes?
  3. Are Lambda functions using arm64 architecture where dependency compatibility allows?
  4. Is VPC attachment limited to functions that genuinely require private network access?
  5. Are direct service integrations used where Lambda would only pass data through?
Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/performance-efficiency.html
```

### Pillar 5: Cost Optimization

```
Pillar: Cost Optimization
Definition: The ability to run serverless systems at the lowest price point while achieving business outcomes.
Key Design Principles:
  - Implement cloud financial management (Lambda cost tracking via Cost Allocation Tags)
  - Adopt a consumption model (Lambda's pay-per-invocation, DynamoDB on-demand)
  - Measure overall efficiency (cost per transaction, cost per business event)
  - Stop spending money on undifferentiated heavy lifting (managed services over custom code)
  - Analyze and attribute expenditure (per-function cost dashboards via Cost Explorer)
  - Optimize data transfer costs (VPC Endpoints over NAT Gateway, regional service calls)
Applies To Serverless Production Workloads:
  Serverless cost optimization is driven by: (1) Lambda memory tuning via Power Tuning — optimal memory often reduces duration enough to decrease total cost, (2) batch size maximization for SQS/Kinesis to reduce invocation count, (3) elimination of Lambda intermediaries with direct integrations, (4) VPC Endpoints instead of NAT Gateway for VPC-attached functions, (5) DynamoDB on-demand for variable workloads (provisioned + auto-scaling for predictable high-volume), (6) arm64 for 20% cost reduction.
Assessment Questions:
  1. Has Lambda Power Tuning been run to find cost-optimal memory for each function?
  2. Are SQS batch sizes and batching windows maximized to reduce invocation count?
  3. Is there a tagging strategy enabling per-function and per-service cost attribution?
  4. Are VPC Endpoints used instead of NAT Gateway for VPC-attached Lambda AWS API calls?
  5. Is Provisioned Concurrency scoped to minimum required hours (not 24/7)?
Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/cost-optimization.html
```

### Pillar 6: Sustainability

```
Pillar: Sustainability
Definition: Minimizing the environmental impact of running serverless workloads.
Key Design Principles:
  - Understand your impact (Lambda's per-invocation model enables proxy carbon metrics)
  - Establish sustainability goals (minimize idle compute — Lambda is inherently efficient)
  - Maximize utilization (optimize function duration — shorter execution = lower emissions)
  - Use managed services (avoid self-managed consumers that run continuously idle)
  - Reduce downstream impact (minimize data movement, process data close to storage)
  - Use arm64 (Graviton2 is more energy-efficient than x86_64 for equivalent compute)
Applies To Serverless Production Workloads:
  Lambda's pay-per-use model is inherently sustainable — zero idle compute. Further optimization: (1) arm64/Graviton2 for energy efficiency, (2) duration optimization via memory tuning reduces compute time, (3) batch processing reduces invocation overhead per unit of work, (4) Lambda@Edge/CloudFront Functions process data at the edge — reducing data transfer.
Assessment Questions:
  1. Are Lambda functions using arm64 (Graviton2) architecture where possible?
  2. Is function duration optimized (Power Tuning applied)?
  3. Are batch sizes maximized to reduce per-unit compute overhead?
Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/sustainability-pillar.html
```

---

## Three-Tier Operational Guardrails

### ✅ Mandatory Patterns

**Per-Function Least-Privilege Execution Roles**
- Pillar Alignment: Security
- Why: AWS Serverless Lens — "Grant each function only the permissions that it requires. Use separate IAM roles for each function to implement the principle of least privilege." A shared role with broad permissions means a vulnerability in one function compromises all resources accessible by all functions sharing that role.
- AWS Services: AWS IAM (Roles, Policies), AWS Lambda (Execution Role), IAM Access Analyzer, AWS Config
- Architecture Decision:
  Each Lambda function has a unique IAM role. Trust policy: `lambda.amazonaws.com` only. Permission policies scope actions to specific resource ARNs. No wildcard `*` on actions or resources. SAM/CDK auto-generate per-function roles. Permission Boundaries cap maximum possible permissions across all Lambda roles.
  ```
  Role naming: {service}-{function}-{env}-role
  Trust: { "Principal": { "Service": "lambda.amazonaws.com" } }
  Permissions:
    ✅ { "Action": ["dynamodb:GetItem", "dynamodb:PutItem"], "Resource": "arn:aws:dynamodb:*:*:table/Orders" }
    ❌ { "Action": "*", "Resource": "*" }
  ```
- Verification:
  ```bash
  aws iam list-attached-role-policies --role-name <function-role>
  aws accessanalyzer list-findings --analyzer-arn <arn> --filter '{"resourceType": {"contains": ["AWS::IAM::Role"]}}'
  # AWS Config: iam-policy-no-statements-with-admin-access
  # Security Hub: Lambda.1 (public access), IAM.1 (wildcard policies)
  ```
- Trade-offs: More IAM roles to manage (mitigated by IaC auto-generation). Slightly more complex cross-function data access patterns.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/security.html

**Dead Letter Queue / On-Failure Destination for All Async Paths**
- Pillar Alignment: Reliability
- Why: AWS Serverless Lens — "Use dead-letter queues and on-failure destinations to capture events that fail processing. Without them, failed events are silently discarded after retry exhaustion." Silent data loss is the most dangerous failure mode in serverless — it is invisible to monitoring unless explicitly instrumented.
- AWS Services: Amazon SQS (DLQ), AWS Lambda (Async Destinations, Event Source Mapping failure destination), Amazon EventBridge, Amazon SNS
- Architecture Decision:
  Every Lambda function invoked asynchronously MUST have an on-failure destination. Every Event Source Mapping MUST have a failure destination. Prefer Destinations over legacy DLQ (richer error metadata). Configure maximum retry attempts explicitly. Alarm on DLQ message count > 0.
  ```
  Async function: on_failure_destination → SQS DLQ (14-day retention)
  Event Source Mapping: on_failure → SQS DLQ or S3 (for large-batch failures)
  CloudWatch Alarm: ApproximateNumberOfMessagesVisible > 0 → SNS → PagerDuty
  DLQ Retention: 14 days (maximum)
  Operational runbook: DLQ investigation → root cause → fix → replay via DLQ redrive
  ```
- Verification:
  ```bash
  # Find async functions without DLQ/destination
  aws lambda list-functions --output json | jq '.Functions[] | select(.DeadLetterConfig == null) | .FunctionName'
  # Check event invoke configs
  aws lambda list-function-event-invoke-configs --function-name <name>
  # Security Hub: Lambda.4 (DLQ configured)
  ```
- Trade-offs: Small SQS cost for DLQ storage. Requires operational procedure for DLQ investigation and replay.
- Source: https://docs.aws.amazon.com/lambda/latest/dg/invocation-async-retain-records.html

**Idempotent Handler Design**
- Pillar Alignment: Reliability
- Why: AWS Serverless Lens — "Design functions to be idempotent. Lambda may invoke your function more than once for the same event in asynchronous and poll-based invocation models." At-least-once delivery is a guaranteed behavior for SQS Standard, SNS, EventBridge, and Lambda async invocations — duplicate processing WILL occur.
- AWS Services: AWS Lambda Powertools (Idempotency utility), Amazon DynamoDB (idempotency table), Amazon SQS FIFO (MessageDeduplicationId)
- Architecture Decision:
  Every handler writing to external systems must implement idempotency. Use Lambda Powertools Idempotency utility (DynamoDB-backed) for critical write operations. Use conditional writes (PutItem with attribute_not_exists) for database operations. Use SQS FIFO MessageDeduplicationId for exactly-once processing scenarios.
  ```
  Idempotency strategy per invocation model:
    Synchronous (API Gateway): Client-generated idempotency key in X-Idempotency-Key header
    Asynchronous (EventBridge/SNS): event.detail.id or event.MessageId as idempotency key
    Poll-based (SQS): message.MessageId as idempotency key
    Poll-based (Kinesis): record.eventID as idempotency key
  
  Implementation (Lambda Powertools):
    @idempotent(persistence_store=DynamoDBPersistenceLayer(table_name="idempotency"))
    def handler(event, context): ...
  ```
- Verification: Load test with duplicate events; verify no duplicate writes, no duplicate notifications, no duplicate charges.
- Trade-offs: DynamoDB idempotency table adds ~1–2ms per invocation. FIFO SQS has lower throughput than Standard. Idempotency key TTL must be tuned (too short → duplicates accepted; too long → storage growth).
- Source: https://docs.powertools.aws.dev/lambda/python/latest/utilities/idempotency/

**Structured JSON Logging with Correlation IDs**
- Pillar Alignment: Operational Excellence
- Why: AWS Serverless Lens — "Use structured logging to enable filtering, aggregation, and searching across distributed function invocations. Propagate correlation IDs to trace requests across service boundaries." Unstructured text logs are unsearchable at scale and make incident response impossible in distributed serverless systems.
- AWS Services: AWS Lambda (Advanced Logging Controls), Amazon CloudWatch Logs (Insights), AWS Lambda Powertools (Logger), AWS X-Ray
- Architecture Decision:
  All Lambda functions emit structured JSON logs. Lambda Advanced Logging Controls configured for JSON format. AWS Lambda Powertools Logger used for automatic correlation ID injection, cold start annotation, and service name decoration. Log level filtering configured per-function (INFO for most; WARN for high-volume stream processors).
  ```
  Lambda Logging Configuration:
    LogFormat: JSON
    ApplicationLogLevel: INFO (production: WARN for high-volume)
    SystemLogLevel: WARN
  
  Log structure (via Powertools):
    { "level": "INFO", "service": "order-service", "function_name": "createOrder",
      "correlation_id": "abc-123", "cold_start": false, "message": "Order created",
      "order_id": "ORD-456", "timestamp": "2024-01-15T10:30:00.000Z" }
  ```
- Verification:
  ```bash
  aws lambda get-function-configuration --function-name <name> --query 'LoggingConfig'
  # Verify JSON structure: CloudWatch Logs Insights → parse @message | limit 5
  ```
- Trade-offs: JSON logs consume slightly more storage than plain text. Mitigated by log level control and CloudWatch Logs retention policies (set explicitly — never default/infinite).
- Source: https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs.html

**Reserved Concurrency Isolation**
- Pillar Alignment: Reliability
- Why: AWS Serverless Lens — "Set reserved concurrency for mission-critical functions to guarantee capacity and prevent account-level concurrency exhaustion caused by other functions." Without reservation, a traffic spike on ANY function in the account can throttle ALL other functions sharing the default concurrency pool.
- AWS Services: AWS Lambda (Reserved Concurrency), Amazon CloudWatch (ConcurrentExecutions metric)
- Architecture Decision:
  Critical customer-facing functions: reserved concurrency = expected peak × 1.5 (guarantees capacity). High-volume background functions: reserved concurrency = cap at safe level (prevents pool exhaustion). Default pool: maintain 20–30% headroom above total reservations.
  ```
  Concurrency allocation strategy:
    Account limit: 1000 (default, request increase for production)
    Critical API functions (orders, auth): reserved = 200 each
    Background processors (analytics, notifications): reserved = 50 each (cap)
    Unreserved pool: 1000 - 500 (reserved) = 500 (for spikes)
  
  Alarm: ConcurrentExecutions / ReservedConcurrency > 80% → investigate
  ```
- Verification:
  ```bash
  aws lambda get-account-settings  # Check AccountLimit and UnreservedConcurrentExecutions
  aws lambda list-functions --output json | jq '[.Functions[] | select(.ReservedConcurrentExecutions != null)]'
  ```
- Trade-offs: Reserved concurrency reduces pool available to other functions. Over-reservation wastes headroom. Requires periodic review as traffic patterns change.
- Source: https://docs.aws.amazon.com/lambda/latest/dg/configuration-concurrency.html

**Distributed Tracing (X-Ray / ADOT)**
- Pillar Alignment: Operational Excellence, Reliability
- Why: AWS Serverless Lens — "Implement distributed tracing to identify root cause of latency and errors across service boundaries." Serverless architectures have many service hops; without tracing, debugging a slow request requires manual correlation across CloudWatch log groups for Lambda, API Gateway, DynamoDB, SQS, and Step Functions.
- AWS Services: AWS X-Ray, AWS Distro for OpenTelemetry (ADOT), Lambda (X-Ray integration), API Gateway (X-Ray), Step Functions (X-Ray), Lambda Powertools (Tracer)
- Architecture Decision:
  X-Ray active tracing enabled on all Lambda functions and API Gateway stages. Trace context propagated in all downstream HTTP calls. Subsegments for database queries and external API calls. For new deployments, prefer ADOT Lambda Layer for vendor-neutral tracing.
  ```
  # Enable X-Ray on Lambda
  TracingConfig: { Mode: Active }
  # Enable X-Ray on API Gateway
  TracingEnabled: true (on Stage)
  # Lambda Powertools Tracer auto-instruments all boto3 calls
  ```
- Verification:
  ```bash
  aws lambda get-function-configuration --function-name <name> --query 'TracingConfig'
  # X-Ray console: verify end-to-end trace visibility across services
  ```
- Trade-offs: ~1–5% request latency overhead. X-Ray charges $5/million traces sampled. ADOT layer adds ~30–50 MB to deployment package.
- Source: https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html

**DynamoDB Point-in-Time Recovery (PITR)**
- Pillar Alignment: Reliability
- Why: DynamoDB is fully managed but does NOT protect against application-level data corruption (buggy code writing bad data) or accidental deletes (operator error, misconfigured TTL). PITR enables table restoration to any second within the preceding 35-day window.
- AWS Services: Amazon DynamoDB (PITR), AWS Backup (for cross-account copies)
- Architecture Decision:
  PITR enabled on ALL production DynamoDB tables. AWS Backup rule for cross-region copy of critical tables (DR). Recovery testing performed quarterly.
  ```
  PITR: Enabled (all production tables)
  Recovery window: 35 days (non-configurable maximum)
  Recovery test: quarterly (restore to temp table, validate data integrity)
  ```
- Verification:
  ```bash
  aws dynamodb describe-continuous-backups --table-name <name>
  # Expect: ContinuousBackupsStatus: ENABLED, PointInTimeRecoveryStatus: ENABLED
  ```
- Trade-offs: ~20% additional storage cost for PITR. Restoration creates a new table (requires application reconfiguration or alias swap).
- Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/PointInTimeRecovery.html

---

### ⚠️ Architectural Decisions

**Compute Model: Lambda vs Containers vs Hybrid**

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| Lambda (event-driven) | AWS Lambda | Zero idle cost, auto-scaling, no infra management | 15-min max duration, 10 GB memory ceiling, cold starts | Request/event durations <15 min, variable traffic, <10 GB memory |
| Lambda Container Image | AWS Lambda (container runtime) | Familiar container tooling, up to 10 GB image size | Same Lambda limits (timeout, memory), larger cold starts | Existing container workflows, large dependency trees, ML inference |
| ECS Fargate | Amazon ECS on Fargate | Long-running processes, no duration limits, predictable latency | Minimum task charge (~1 min), no auto-scale-to-zero | Continuous processing, WebSocket servers, >15-min tasks |
| App Runner | AWS App Runner | Simplest container deployment, auto-scaling including to zero | Limited networking control, fewer integration points | Simple HTTP services, team unfamiliar with ECS/EKS |

- Cost Profile: Lambda = cheapest for <1M invocations/month. Fargate = cheaper at sustained high-throughput (>100K concurrent requests). App Runner = middle ground.
- Lock-in Assessment: Lambda event-driven patterns (invocation models, destinations, ESM) are deeply AWS-specific. Container workloads on Fargate are more portable to GKE/AKS.
- Ask The Architect: "What is the maximum single-request duration? Is traffic pattern spiky/variable or sustained/predictable? Does the workload need >10 GB memory?"
- Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/compute-layer.html

**Data Store: DynamoDB vs Aurora Serverless v2 vs ElastiCache**

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| DynamoDB (on-demand) | Amazon DynamoDB | Latency (single-digit ms), zero capacity planning, serverless-native | Complex queries, JOINs, ad-hoc analytics | Known access patterns, key-value/document, high-write workloads |
| Aurora Serverless v2 | Amazon Aurora Serverless v2 | Relational queries, transactions, complex JOINs | Minimum ACU charge (never zero), cold start on scale-up | Complex data relationships, existing relational schema, need SQL |
| ElastiCache Serverless | Amazon ElastiCache Serverless | Sub-millisecond latency, session store, caching | Not a primary data store, volatile | Hot data caching, session management, rate limiting |
| S3 + Athena | Amazon S3 + Amazon Athena | Analytics at scale, schema-on-read, cost for infrequent queries | High latency (seconds), not for transactional workloads | Logs, event archives, ad-hoc analytics, data lake |

- Cost Profile: DynamoDB on-demand ~ $1.25/million writes + $0.25/million reads. Aurora Serverless v2 minimum ~ $43/month (0.5 ACU). ElastiCache Serverless ~ $90/month minimum.
- Scaling: DynamoDB scales instantly (on-demand) with per-partition limits. Aurora Serverless v2 scales ACUs in 0.5 increments (seconds to scale). ElastiCache Serverless scales ECPU automatically.
- Ask The Architect: "Are access patterns known and finite? (DynamoDB). Do you need JOINs or complex transactions? (Aurora). Do you need sub-millisecond reads for hot data? (ElastiCache)."
- Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/data-layer.html

**Asynchronous Communication: SQS vs SNS vs EventBridge vs Kinesis**

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| Point-to-point queue | Amazon SQS Standard/FIFO | Decoupling, backpressure, at-least-once delivery, DLQ support | No fan-out (single consumer), no content-based routing | Command messages, work queues, rate limiting downstream |
| Pub/Sub fan-out | Amazon SNS + SQS | One event → multiple subscribers, message filtering | No replay, limited filtering (attribute-based) | Broadcasting events, multi-consumer notification |
| Event bus | Amazon EventBridge | Content-based routing, schema registry, archive/replay, SaaS integration | Higher cost ($1/M), 1-second delivery latency | Domain events, cross-account routing, event-driven microservices |
| Ordered streaming | Amazon Kinesis Data Streams | Ordered, replayable, multi-consumer, sub-second delivery | Shard management complexity, higher cost at low volume | High-throughput event streams, analytics pipelines, audit logs |

- Cost Profile: SQS $0.40/M. SNS $0.50/M. EventBridge $1/M custom events. Kinesis $0.015/shard-hour + $0.04/M PUT.
- Key Decision Criteria: Is it a command or event? (SQS vs EventBridge). Need fan-out? (SNS/EventBridge). Need ordering? (SQS FIFO/Kinesis). Need replay? (Kinesis/EventBridge Archive).
- Ask The Architect: "Is this a command (one consumer should act) or an event (multiple consumers may react)? Do you need content-based routing? Do you need message replay for debugging/reprocessing?"
- Source: https://aws.amazon.com/event-driven-architecture/

**Orchestration: Step Functions vs EventBridge Choreography**

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| Orchestration (Standard) | AWS Step Functions Standard | Full audit trail, centralized error handling, saga compensation, human approval | $0.025/1000 transitions, state machine complexity | Multi-step business workflows, compensation logic, regulatory audit |
| Orchestration (Express) | AWS Step Functions Express | High-frequency workflows, low cost ($1/M executions) | 5-min max, at-least-once semantics, no execution history API | High-volume data processing, event enrichment pipelines |
| Choreography | EventBridge + Lambda | Loose coupling, independent deployment, no coordinator | Distributed debugging, harder to reason about failures | Simple event chains, independent services, high autonomy |
| Hybrid | Step Functions + EventBridge | Complex flows with event notification | Architectural complexity | Workflows that produce domain events consumed by other services |

- Cost Profile: Step Functions Standard expensive for high-frequency (>10K/day for multi-step). Express economical at scale. EventBridge cheapest for simple routing.
- Ask The Architect: "Does this workflow need compensating transactions, human approval, or an audit trail? If yes → Step Functions. Simple event reaction with no compensation → Choreography."
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html

**Cold Start Mitigation: SnapStart vs Provisioned Concurrency vs Accept**

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| SnapStart | Lambda SnapStart | Near-zero init, no idle cost | ~100ms restore latency, requires published versions, init must be deterministic | Java/Python/Node.js functions needing low P99 without idle cost |
| Provisioned Concurrency | Lambda Provisioned Concurrency + Auto Scaling | Zero cold start for provisioned count | Billed when idle (~3× on-demand), requires capacity planning | Strict P99 <100ms SLA, predictable traffic, financial services |
| Accept cold starts | No mitigation | Zero additional cost | Cold start latency (200ms–5s depending on runtime) | Async functions, batch processing, internal tooling |
| arm64 + minimal package | Lambda arm64 + tree-shaking | Reduced init time via smaller package | Limited impact for large frameworks | All functions — always optimize regardless of other strategies |

- Cost Profile: SnapStart = free. Provisioned Concurrency = ~3× on-demand rate per environment-hour.
- Ask The Architect: "What is the P99 latency budget? Is the traffic pattern predictable (scheduled peaks) or random (spikes)? Is the function on a supported runtime (Java/Python/Node.js)?"
- Source: https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html

**API Layer: HTTP API vs REST API vs Function URL vs ALB**

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| HTTP API | API Gateway HTTP API | Cost (~70% cheaper), latency, JWT auth | No WAF, no caching, no request validation, no usage plans | Most serverless APIs, microservices, mobile backends |
| REST API | API Gateway REST API | Full features: WAF, caching, validation, usage plans, API keys | Higher cost (~$3.50/M), higher latency | External-facing APIs needing WAF, caching, per-client throttling |
| Function URL | Lambda Function URL | Simplest setup, zero API Gateway cost, response streaming | No routing, no WAF, no throttling, regional only | Webhooks, LLM streaming, single-function endpoints |
| ALB | Application Load Balancer | Hybrid Lambda+container routing, WAF, sticky sessions | No native JWT auth, hourly base charge | Mixed Lambda/ECS workloads, internal APIs, WebSocket + HTTP |

- Cost Profile: Function URL = free. HTTP API ~$1/M. REST API ~$3.50/M. ALB ~$16/month base + LCU charges.
- Ask The Architect: "Does the API need WAF protection, request validation, or per-client throttling? If yes → REST API. If simple JWT-protected proxy → HTTP API. If single-endpoint with streaming → Function URL."
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html

---

### 🚫 Anti-Patterns

**Recursive Lambda Invocations Without Circuit Breaker**
- Risk Level: CRITICAL
- Why: Reliability + Cost — Lambda can invoke itself via SQS, SNS, or SDK in a loop. Without a circuit breaker, one buggy deployment triggers thousands of recursive invocations in seconds, exhausting account concurrency and generating unbounded cost.
- Instead:
  - Never have a Lambda function trigger itself via the same event source
  - Use Step Functions for iterative/looping workflows (built-in iteration control)
  - Set reserved concurrency as a hard cap on recursive-capable functions
  - Enable Lambda Recursive Loop Detection (default on — detects and halts Lambda→SQS→Lambda→SQS loops after 16 recursions)
- Detection:
  ```bash
  aws lambda get-function-recursion-config --function-name <name>
  # CloudWatch alarm: Lambda/Invocations with Sum > 10× baseline in 1-minute period
  # Architecture review: identify Lambda → SQS/SNS/EventBridge → same Lambda patterns
  ```
- Impact: Cost overrun (unbounded — $thousands in minutes), Service outage (account concurrency exhausted for ALL functions)
- Source: https://docs.aws.amazon.com/lambda/latest/dg/invocation-recursion.html

**Shared Wildcard Execution Roles**
- Risk Level: CRITICAL
- Why: Security — A shared role with `"Action": "*", "Resource": "*"` means any vulnerability in any function grants full AWS account access. This violates least-privilege and enables privilege escalation, lateral movement, and data exfiltration.
- Instead:
  - Per-function execution roles auto-generated by SAM/CDK
  - Explicit action lists and resource ARNs in every policy
  - Permission Boundaries as a safety net on all Lambda roles
  - IAM Access Analyzer to detect overly permissive policies
  - AWS Config rule: `iam-policy-no-statements-with-admin-access`
- Detection:
  ```bash
  aws iam get-role-policy --role-name <lambda-role> --policy-name <inline-policy>
  # Check for Action: "*" or Resource: "*"
  aws accessanalyzer list-findings --analyzer-arn <arn>
  ```
- Impact: Data breach, privilege escalation, full account compromise, compliance violation (SOC2, PCI-DSS, HIPAA)
- Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/security.html

**Synchronous Lambda Chains (Lambda Calling Lambda)**
- Risk Level: HIGH
- Why: Reliability + Cost — Synchronous Lambda→Lambda invocations double timeout risk, double cost (both billed simultaneously), create tight coupling, and propagate failures upstream. A timeout in the downstream function wastes the upstream function's full execution duration.
- Instead:
  - Orchestrated workflows: AWS Step Functions
  - Decoupled async: SQS → Lambda (downstream)
  - Fire-and-forget: EventBridge or SNS → Lambda
  - Direct composition: Step Functions task → multiple Lambda tasks in sequence
  ```
  ❌ Lambda A → lambda_client.invoke(FunctionName='B', InvocationType='RequestResponse')
  ✅ Lambda A → SQS → Lambda B (decoupled)
  ✅ Step Functions → Lambda A → Lambda B (orchestrated)
  ```
- Detection: Code search for `lambda_client.invoke` with `InvocationType='RequestResponse'` or `'Event'`. Architecture diagram review.
- Impact: Cascading failure, doubled cost, tight coupling, timeout amplification
- Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/reliability.html

**Missing Async Error Handling (No DLQ/Destination)**
- Risk Level: HIGH
- Why: Reliability — Asynchronous Lambda invocations retry 0–2 times on failure. After retries are exhausted, without a DLQ or on-failure destination, the event is permanently discarded. This is SILENT DATA LOSS — no alarm fires, no log entry is produced for the discarded event.
- Instead:
  - Configure on-failure destination (SQS or EventBridge) for every async function
  - Configure failure destination on every Event Source Mapping
  - Set maximum_retry_attempts explicitly (don't rely on default)
  - Alarm on DLQ message count > 0
- Detection:
  ```bash
  aws lambda list-functions --output json | jq '.Functions[] | select(.DeadLetterConfig == null) | .FunctionName'
  aws lambda list-event-source-mappings --output json | jq '.EventSourceMappings[] | select(.DestinationConfig == null) | .EventSourceArn'
  ```
- Impact: Silent data loss, undetected processing failures, business data inconsistency
- Source: https://docs.aws.amazon.com/lambda/latest/dg/invocation-async-retain-records.html

**Storing Secrets in Environment Variables or Code**
- Risk Level: CRITICAL
- Why: Security — Lambda environment variables are visible in plaintext to anyone with `lambda:GetFunctionConfiguration` permission. Secrets in code are committed to version control and exposed in deployment artifacts. Both violate data protection requirements.
- Instead:
  - AWS Secrets Manager for rotating secrets (DB credentials, API keys)
  - AWS Systems Manager Parameter Store (SecureString) for static configuration
  - AWS Parameters and Secrets Lambda Extension for cached local fetching
  - KMS CMK if environment variables must be used (encrypt values, grant decrypt to execution role only)
- Detection:
  ```bash
  aws lambda get-function-configuration --function-name <name> --query 'Environment.Variables'
  # Scan for patterns: API_KEY, PASSWORD, SECRET, TOKEN, CREDENTIAL in variable names
  # AWS Config: lambda-function-settings-check
  ```
- Impact: Credential exposure, data breach, compliance violation (GDPR, PCI-DSS, SOC2, HIPAA)
- Source: https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html#configuration-envvars-encryption

**Lambda Functions Without Explicit Timeout Configuration**
- Risk Level: HIGH
- Why: Reliability — Lambda's default timeout is 3 seconds. Functions calling external services (databases, APIs, S3) routinely exceed this. A too-short timeout causes silent failures that trigger retry storms for async invocations, amplifying load and cost.
- Instead:
  - Set explicit timeout per function based on P99 measured duration × 2 safety margin
  - Set downstream HTTP client timeouts < Lambda function timeout
  - Alarm when duration exceeds 80% of configured timeout
  ```
  Timeout guidelines:
    Simple compute: 10s
    Database query: 30–60s
    External HTTP API call: 30s (with 25s client timeout)
    Stream batch processor: 300s
    Step Functions task: match with state machine TimeoutSeconds
  ```
- Detection:
  ```bash
  aws lambda list-functions --query 'Functions[?Timeout==`3`].[FunctionName]' --output table
  ```
- Impact: Silent failures, retry storms, cascading timeouts, data processing stalls
- Source: https://docs.aws.amazon.com/lambda/latest/dg/configuration-function-common.html

**API Gateway Without Authorization**
- Risk Level: CRITICAL
- Why: Security — An API Gateway endpoint deployed without authorization is publicly accessible immediately. Automated scanners discover and exploit unprotected endpoints within minutes of deployment. Without auth, any client can invoke your backend Lambda functions.
- Instead:
  - Cognito JWT authorizer (HTTP API) or Cognito User Pool authorizer (REST API)
  - Lambda authorizer for custom auth logic
  - IAM authorization for service-to-service communication
  - API keys (for identification only — NOT as sole auth mechanism)
  - WAF web ACL on all public stages
- Detection:
  ```bash
  # REST API: check for methods without authorization
  aws apigateway get-resources --rest-api-id <id> --output json | jq '.items[].resourceMethods | to_entries[] | select(.value.authorizationType == "NONE")'
  # HTTP API: check routes without authorizer
  aws apigatewayv2 get-routes --api-id <id> --output json | jq '.Items[] | select(.AuthorizationType == "NONE")'
  ```
- Impact: Unauthorized access, data breach, resource abuse, cost overrun from abuse traffic
- Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/security.html

**Monolithic Lambda (Lambda-lith)**
- Risk Level: MEDIUM
- Why: Operational Excellence + Performance — Deploying an entire application framework (Express.js, Flask, Spring) inside a single Lambda function defeats serverless benefits: no granular scaling, no per-route IAM isolation, large deployment package (slow cold starts), single IAM role for all operations, all-or-nothing deployments.
- Instead:
  - Single-purpose functions grouped by domain resource (OrderFunction, UserFunction)
  - API Gateway routing to specific Lambda functions per resource path
  - Shared libraries via Lambda Layers or private npm/PyPI packages
  - If framework pattern preferred: AWS App Runner or ECS Fargate for container-based deployment
- Detection: Lambda function with >50 MB deployment package. Single function handling >10 API routes. Function timeout set to maximum (900s). Single execution role with permissions spanning multiple DynamoDB tables, S3 buckets, and SQS queues.
- Impact: No granular scaling, oversized IAM role blast radius, slow cold starts, all-or-nothing deployments, difficult debugging
- Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/operational-excellence.html

---

## Cloud-Native Design Patterns for Serverless

**Event-Driven Fan-Out**
- Category: Scalability, Decoupling
- Problem: A single domain event must trigger multiple independent downstream processes without coupling the producer to consumers.
- Solution on AWS:
  SNS topic or EventBridge event bus as the fan-out hub. Per-consumer SQS queues subscribe to the hub. Each consumer has its own Lambda function, SQS queue, DLQ, and IAM role — failures in one consumer are fully isolated.
  ```
  Producer → EventBridge (event bus) → Rule A → SQS A → Lambda A (email)
                                     → Rule B → SQS B → Lambda B (analytics)
                                     → Rule C → SQS C → Lambda C (audit)
  Each consumer path: SQS (main queue) + SQS (DLQ) + Lambda + IAM role
  ```
- Services Used: EventBridge (routing), SQS (per-consumer buffering + DLQ), Lambda (processing)
- When to Apply: OrderPlaced → notify + inventory + invoice. UserSignedUp → welcome + CRM + onboarding.
- When NOT to Apply: Single consumer (use SQS directly). When ordering is required across consumers (use Kinesis).
- Trade-offs:
  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Resilience | Consumer failure isolation | DLQ per consumer to manage |
  | Coupling | Zero knowledge between producer/consumers | Consumer addition requires rule/subscription |
  | Cost | Pay-per-message, no idle cost | EventBridge $1/M + SQS $0.40/M per consumer |
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-data-persistence/event-fork-pipeline.html

**Saga Pattern (Distributed Transactions)**
- Category: Data, Resilience
- Problem: A multi-step business transaction spans multiple services/databases. Any step can fail, requiring compensating transactions.
- Solution on AWS:
  Step Functions Standard Workflow as saga orchestrator. Each step is a Lambda function (or direct service integration). Catch blocks invoke compensating functions on failure. Execution history provides full audit trail.
  ```
  Step Functions State Machine:
    1. ReserveInventory (Lambda) → catch: end
    2. ChargePayment (Lambda) → catch: ReleaseInventory
    3. CreateShipment (Lambda) → catch: RefundPayment → ReleaseInventory
    4. NotifyCustomer (Lambda/SNS direct integration)
  Each Task state: Retry (3 attempts, exponential backoff) + Catch (compensating action)
  ```
- Services Used: Step Functions Standard (orchestrator), Lambda (transaction steps), DynamoDB (per-service state with conditional writes for idempotency)
- When to Apply: E-commerce checkout, financial transfers, multi-service provisioning.
- When NOT to Apply: Single-service ACID transactions, read-only operations, high-frequency low-value operations.
- Trade-offs:
  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Consistency | Eventually consistent across services | Temporary inconsistency during compensation |
  | Audit | Full execution history in Step Functions | $0.025/1000 state transitions |
  | Complexity | Compensation logic centralized | State machine definition grows with steps |
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-data-persistence/saga-pattern.html

**CQRS (Command Query Responsibility Segregation)**
- Category: Data, Scalability
- Problem: Read and write workloads have different scaling, latency, and query pattern requirements that cannot be optimized with a single data model.
- Solution on AWS:
  Command path: API Gateway → Lambda (write) → DynamoDB (source of truth). Query path: DynamoDB Streams → Lambda (projection) → read-optimized store (ElastiCache/OpenSearch). Read API queries the optimized store.
  ```
  Write: API Gateway → Command Lambda → DynamoDB → DynamoDB Streams
  Project: DynamoDB Streams → Projection Lambda → ElastiCache / OpenSearch
  Read: API Gateway → Query Lambda → ElastiCache / OpenSearch
  ```
- Services Used: DynamoDB (write store), DynamoDB Streams (CDC), Lambda (projection), ElastiCache/OpenSearch (read store)
- When to Apply: High read:write ratio workloads, complex query patterns on DynamoDB, analytics alongside transactional writes.
- When NOT to Apply: Simple CRUD with balanced read/write, when eventual consistency in reads is unacceptable.
- Trade-offs:
  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Performance | Read store optimized for query patterns | Eventual consistency — reads may lag writes |
  | Scalability | Read and write scale independently | Multiple data stores to manage |
  | Cost | Right-sized per operation type | Additional infrastructure (ElastiCache/OpenSearch) |
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-data-persistence/cqrs-pattern.html

**Claim Check Pattern (Large Payload Handling)**
- Category: Communication, Scalability
- Problem: Serverless messaging has size limits (SQS 256 KB, SNS 256 KB, EventBridge 256 KB, Lambda async 256 KB, Step Functions state 256 KB). Large payloads cannot pass directly through event-driven architectures.
- Solution on AWS:
  Producer stores large payload in S3. Event message contains only the S3 reference (bucket + key). Consumer retrieves payload from S3.
  ```
  Producer: large payload → S3 PutObject → publish { bucket, key, metadata } → SQS/EventBridge
  Consumer: receive { bucket, key } → S3 GetObject → process full payload
  Cleanup: S3 Lifecycle rule deletes claim-check objects after processing window
  ```
- Services Used: S3 (payload store), SQS/EventBridge (reference message), Lambda (producer/consumer)
- When to Apply: Image/video processing, large document ETL, batch data payloads, ML model input.
- When NOT to Apply: Small payloads within limits (adds unnecessary S3 round-trip latency).
- Trade-offs:
  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Scalability | No message size constraints | Extra S3 GET adds 5–20ms latency |
  | Cost | S3 is cheap ($0.023/GB) | Additional S3 API calls |
  | Cleanup | Lifecycle rules automate deletion | Orphaned objects if lifecycle misconfigured |
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/claim-check.html

**Circuit Breaker with Step Functions**
- Category: Resilience
- Problem: A downstream service is degraded or failing. Continuing to invoke it wastes resources, amplifies the failure, and degrades the caller.
- Solution on AWS:
  Step Functions state machine implements circuit breaker logic: tracks failure count in DynamoDB, opens circuit (skips calls) when threshold exceeded, attempts half-open probe after cooldown period, closes circuit on success.
  ```
  Step Functions State Machine:
    1. CheckCircuitState (DynamoDB GetItem) → Choice:
       - OPEN + cooldown not expired → return cached/fallback response
       - OPEN + cooldown expired → HALF_OPEN → attempt call
       - CLOSED → attempt call
    2. CallDownstream (Lambda/HTTPS endpoint) → success → update DynamoDB (reset failure count)
                                              → failure → increment failure count → if threshold → OPEN circuit
  ```
- Services Used: Step Functions (orchestrator), DynamoDB (circuit state store with TTL for auto-reset), Lambda/HTTPS endpoint (downstream call)
- When to Apply: External API calls, third-party integrations, cross-service synchronous calls.
- When NOT to Apply: Internal AWS managed services (they have their own retry and availability guarantees).
- Trade-offs:
  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Resilience | Protects system from cascading failure | Additional DynamoDB reads per call |
  | User Experience | Fast fallback instead of timeout | Degraded response during open circuit |
  | Complexity | Centralized failure management | State machine definition overhead |
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/circuit-breaker.html

**Strangler Fig (Serverless Migration)**
- Category: Migration
- Problem: Incrementally extract functionality from a monolith to serverless without a big-bang rewrite.
- Solution on AWS:
  API Gateway as routing facade. Route specific paths to Lambda functions as they are extracted. Monolith handles remaining routes via HTTP integration. Over time, Lambda handles increasing traffic share.
  ```
  Phase 1: API Gateway → HTTP proxy → Monolith (all routes)
  Phase 2: API Gateway → Lambda (POST /orders)
                       → HTTP proxy → Monolith (everything else)
  Phase 3: API Gateway → Lambda (all routes) — monolith retired
  
  Shared database during transition: RDS Proxy for connection pooling
  ```
- Services Used: API Gateway (facade), Lambda (new services), ALB/HTTP (monolith backend), RDS Proxy (shared DB)
- When to Apply: Legacy monoliths needing incremental modernization. Teams unwilling to do full rewrite.
- When NOT to Apply: Tightly coupled monoliths with shared in-memory state. When dual maintenance cost exceeds rewrite cost.
- Trade-offs:
  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Risk | Incremental — stop at any point | Dual maintenance during transition |
  | Speed | Deploy extracted functions independently | Routing complexity grows |
  | Data | Shared DB during transition | DB coupling until database-per-service migration |
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-data-persistence/strangler-fig.html

---

## Security Architecture

**Identity & Access Management (Serverless)**
- Security Domain: Identity
- AWS Services:
  - AWS IAM: per-function execution roles, permission boundaries, SCPs
  - Amazon Cognito: user authentication (User Pools), AWS credential brokering (Identity Pools)
  - API Gateway authorizers: JWT (HTTP API), Cognito (REST API), Lambda (custom auth)
  - IAM Access Analyzer: overly permissive role detection
  - AWS STS: temporary credentials for cross-account access
- Architecture:
  Three trust boundaries: (1) User → API (Cognito JWT validation at API Gateway), (2) API → Lambda (IAM invoke permission), (3) Lambda → AWS services (execution role). Each boundary has independent authorization. No shared roles. No hardcoded credentials.
  ```
  User Authentication: Cognito User Pool → JWT → API Gateway JWT authorizer
  Service Authorization: Lambda execution role → least-privilege IAM policies → specific resource ARNs
  Cross-Account: STS AssumeRole with ExternalId for cross-account Lambda invocations
  M2M Auth: Cognito Resource Server + client_credentials grant for service-to-service
  ```
- Configuration Essentials:
  - Cognito: PKCE for public clients, client secret for server-side clients
  - API Gateway: authorization on EVERY route (no NONE auth type in production)
  - Lambda: trust policy restricts to `lambda.amazonaws.com` only
  - Permission Boundaries: cap maximum permissions for all Lambda roles in account
- Verification:
  ```bash
  aws accessanalyzer list-findings --analyzer-arn <arn>
  aws apigatewayv2 get-routes --api-id <id> --query 'Items[?AuthorizationType==`NONE`]'
  ```
- Compliance Alignment: SOC2 CC6.1/CC6.3, PCI-DSS 7.1/7.2, HIPAA §164.312(d), CIS AWS Foundations
- Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/security.html

**Network Security (Serverless)**
- Security Domain: Network
- AWS Services:
  - Amazon API Gateway: WAF integration, resource policies, TLS enforcement
  - AWS WAF: web ACL with Core Rule Set (CRS), rate-based rules, bot control
  - Amazon CloudFront: edge security layer, geo-restriction, signed URLs
  - Amazon VPC: private subnets for Lambda when accessing private resources
  - VPC Endpoints: private connectivity to AWS services (no internet egress)
  - AWS Shield Advanced: DDoS protection for API Gateway, CloudFront, ALB
- Architecture:
  Internet-facing: Client → CloudFront (WAF + Shield) → API Gateway (regional) → Lambda. Internal: Lambda in private subnet → VPC Endpoints (DynamoDB, S3, Secrets Manager, SQS). No NAT Gateway when VPC Endpoints cover all AWS service calls.
  ```
  Public API security stack:
    CloudFront → WAF (Core Rule Set + rate limiting + bot control) → API Gateway → Lambda
  
  VPC Lambda security:
    Lambda (private subnet, no inbound rules) → VPC Endpoints (no internet required)
    Security Group: egress-only to endpoint security groups on port 443
  ```
- Compliance Alignment: PCI-DSS 1.3 (network segmentation), SOC2 CC6.6, NIST 800-53 SC-7
- Source: https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html

**Data Security (Serverless)**
- Security Domain: Data
- AWS Services:
  - AWS Secrets Manager: rotating secrets (DB credentials, API keys, tokens)
  - AWS Systems Manager Parameter Store: configuration and non-rotating secrets (SecureString)
  - AWS Parameters and Secrets Lambda Extension: local caching (no per-invocation API calls)
  - AWS KMS: CMK for environment variable encryption, DynamoDB encryption, S3 encryption
  - Amazon DynamoDB: encryption at rest (AWS-managed or CMK)
  - Amazon S3: SSE-S3 (default), SSE-KMS, bucket policies
- Architecture:
  Zero secrets in code or environment variables. All secrets fetched at Lambda init via Extension (cached 300s). KMS CMK for all encryption (enables CloudTrail audit of Decrypt operations). DynamoDB encrypted at rest. S3 SSE-KMS for sensitive data buckets. Secrets rotated automatically.
  ```
  Secret access flow:
    Lambda Init → GET localhost:2773/secretsmanager/get?secretId=prod/db-creds
    Extension returns cached value (TTL 300s) → no network call on warm invocations
    CloudTrail logs every kms:Decrypt call → audit trail for secret access
  ```
- Compliance Alignment: GDPR Art. 32, PCI-DSS 3.4/3.5/3.6, HIPAA §164.312(e)(1)
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/lambda-functions.html

---

## Operational Patterns

**Serverless Observability Stack**
- Operational Domain: Observability
- AWS Services:
  - CloudWatch Metrics: Lambda (Invocations, Errors, Duration, Throttles, ConcurrentExecutions, IteratorAge), API Gateway (4XX, 5XX, Latency, Count), DynamoDB (ConsumedRCU/WCU, ThrottledRequests), SQS (ApproximateNumberOfMessagesVisible, ApproximateAgeOfOldestMessage)
  - CloudWatch Logs + Insights: structured JSON logs, cross-service queries
  - AWS X-Ray / ADOT: distributed traces across Lambda → API Gateway → DynamoDB → SQS → Step Functions
  - Lambda Powertools: structured logging + tracing + EMF custom metrics
  - CloudWatch Synthetics: canary scripts for end-to-end health
  - CloudWatch Dashboards: per-service and per-function operational views
- Architecture:
  Every function: structured JSON logs + X-Ray trace + custom business metrics (EMF). Per-function alarms: Errors > 0, Throttles > 0, Duration > 80% timeout, IteratorAge > SLA. Per-service dashboard: invocation volume, error rate, latency percentiles, DLQ depth.
  ```
  Minimum alarm set per Lambda function:
    - Errors > 0 for 1 minute → P1 alert
    - Throttles > 0 for 5 minutes → P2 alert
    - Duration > 80% × timeout for 5 minutes → P2 alert
    - (Stream functions) IteratorAge > SLA_MS → P1 alert
  
  Per-service dashboard widgets:
    - Invocation count (sum), Error rate (%), P50/P95/P99 duration
    - ConcurrentExecutions vs reserved limit
    - DLQ message count (should be 0)
    - DynamoDB ThrottledRequests (should be 0)
  ```
- Cost Profile: Medium — CloudWatch Logs $0.50/GB ingestion, X-Ray $5/M traces, dashboards $3/month each.
- Automation: Alarm creation via IaC (SAM/CDK). Log retention set explicitly (never default infinite). Dashboard generation automated.
- Source: https://docs.aws.amazon.com/lambda/latest/operatorguide/monitoring-observability.html

**Serverless Disaster Recovery**
- Operational Domain: DR
- RTO/RPO:

  | DR Pattern | RTO | RPO | Cost | Serverless Implementation |
  |------------|-----|-----|------|--------------------------|
  | Backup & Restore | Hours | Hours | $ | Lambda code in S3/ECR; DynamoDB PITR restore to new table |
  | Pilot Light | Minutes | Minutes | $$ | Lambda deployed in DR region (not invoked); DynamoDB Global Tables |
  | Warm Standby | Minutes | Seconds | $$$ | Active DR region receiving traffic; Route 53 health check failover |
  | Multi-Region Active-Active | Seconds | Near-zero | $$$$ | DynamoDB Global Tables + EventBridge Global Endpoints + Route 53 latency routing |

- AWS Services: DynamoDB Global Tables (active-active replication), EventBridge Global Endpoints (multi-region event bus failover), Route 53 (health check failover/latency routing), SAM/CDK (multi-region deployment), S3 CRR (deployment artifacts)
- Architecture:
  Lambda is stateless — DR complexity is entirely about state (DynamoDB, S3). Active-active: both regions handle traffic via Route 53 latency routing. DynamoDB Global Tables replicate writes bidirectionally. EventBridge Global Endpoints fail over events automatically on health check failure.
  ```
  Active-Active Architecture:
    Route 53 (latency routing) → Region A: API GW → Lambda → DynamoDB Global Table
                                → Region B: API GW → Lambda → DynamoDB Global Table
    EventBridge Global Endpoint: primary Region A, failover Region B (health check based)
  ```
- Cost Profile: DynamoDB Global Tables adds ~2× write cost. Multi-region Lambda = same cost (deployed in both, invoked per traffic).
- Automation: Route 53 health check failover is automatic. DynamoDB Global Tables replication is automatic. Lambda deployment to DR region automated in CI/CD.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/disaster-recovery-dr-objectives.html

**Serverless FinOps / Cost Optimization**
- Operational Domain: FinOps
- AWS Services: Lambda Power Tuning, AWS Compute Optimizer, Cost Explorer, AWS Budgets, CloudWatch (custom cost metrics)
- Architecture:
  ```
  Cost optimization levers (highest impact first):
    1. Memory tuning (Lambda Power Tuning) — 30–60% cost reduction possible
    2. arm64 architecture — 20% cost reduction (all new functions)
    3. Batch size maximization (SQS batch 10, Kinesis batch 100–10000) — fewer invocations
    4. Direct service integrations — eliminate Lambda intermediaries ($0/invocation)
    5. Step Functions Express over Standard for high-frequency workflows — 25× cheaper per execution
    6. VPC Endpoints instead of NAT Gateway — eliminate $0.045/GB data processing
    7. DynamoDB on-demand vs provisioned — evaluate at >$100/month spend per table
    8. Provisioned Concurrency auto-scaling (schedule to peak hours only)
    9. EventBridge Pipes over custom Lambda filters — managed, no compute cost
    10. CloudWatch Logs retention policy — never use default (infinite/never expire)
  
  Tagging strategy:
    All resources: Environment, Service, Team, CostCenter
    Cost Explorer: filter by aws:lambda:FunctionName, service tag
  ```
- Cost Profile: Lambda pricing: $0.0000166667/GB-second + $0.20/M requests. arm64: ~20% cheaper. Graviton2 (arm64) should be default for all new functions.
- Automation: Lambda Power Tuning in CI/CD pipeline. Budget alerts via AWS Budgets. Compute Optimizer recommendations reviewed monthly.
- Source: https://docs.aws.amazon.com/lambda/latest/operatorguide/cost-optimize.html

**Blue-Green / Canary Deployment**
- Operational Domain: Change Management
- AWS Services: Lambda (Versions + Aliases), AWS CodeDeploy (Lambda deployment group), CloudWatch Alarms, AWS SAM (DeploymentPreference)
- Architecture:
  Every Lambda update publishes a new Version. Alias `prod` traffic-shifts from old → new via CodeDeploy canary strategy. CloudWatch alarm on Errors triggers automatic rollback to previous version.
  ```yaml
  # SAM DeploymentPreference:
  DeploymentPreference:
    Type: Canary10Percent10Minutes  # 10% for 10 min, then 100%
    Alarms:
      - !Ref FunctionErrorAlarm
      - !Ref FunctionDurationAlarm
    Hooks:
      PreTraffic: !Ref PreTrafficTestFunction
      PostTraffic: !Ref PostTrafficTestFunction
  ```
- Cost Profile: Free — CodeDeploy for Lambda has no additional charge.
- Automation: Fully automated — alarm breach triggers instant rollback to previous version. No manual intervention required.
- Source: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/automating-updates-to-serverless-apps.html

---

## Reference Architectures

**Serverless REST API (Three-Tier)**
- Context: Standard CRUD API backend for web/mobile applications
- AWS Source: https://serverlessland.com/patterns/apigw-lambda-dynamodb
- Services Composition:

  | Layer | Service | Purpose | Alternative |
  |-------|---------|---------|-------------|
  | Edge | CloudFront + WAF | DDoS, caching, bot protection | API Gateway WAF directly |
  | API | API Gateway HTTP API | Routing, JWT auth, CORS, throttling | REST API (if WAF/caching/validation needed) |
  | Auth | Cognito User Pool | JWT issuance, user directory, MFA | Lambda authorizer (custom logic) |
  | Compute | Lambda (arm64, Python 3.12 / Node.js 22, SnapStart) | Business logic | Lambda container image |
  | Data | DynamoDB (on-demand) | Primary store, single-table design | Aurora Serverless v2 (if relational) |
  | Secrets | Secrets Manager + Lambda Extension | DB credentials, API keys | SSM Parameter Store |
  | Observability | CloudWatch + X-Ray + Powertools | Logs, traces, metrics | Datadog/New Relic via Extension |

- Key Decisions:
  - HTTP API vs REST API (need WAF/caching? → REST API)
  - Single-table vs multi-table DynamoDB (team experience with single-table patterns)
  - One Lambda per route vs per resource group (prefer per resource group)

- Scaling Path:
  - 0–10K RPM: DynamoDB on-demand, default concurrency, no provisioned concurrency
  - 10K–100K RPM: Reserved concurrency, CloudFront caching for reads, DynamoDB auto-scaling
  - 100K+ RPM: Multi-region (Global Tables + Route 53 latency), ElastiCache for hot reads
- Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/event-driven-architectures.html

**Serverless Event Processing Pipeline**
- Context: High-throughput event ingestion (IoT, clickstream, audit, orders)
- AWS Source: https://serverlessland.com/patterns/kinesis-lambda
- Services Composition:

  | Layer | Service | Purpose | Alternative |
  |-------|---------|---------|-------------|
  | Ingestion | Kinesis Data Streams | Ordered, replayable stream | SQS (simpler, no ordering), MSK (Kafka) |
  | Processing | Lambda (ESM, parallelization factor 10) | Stream consumer, batch processor | Kinesis Data Firehose (no code) |
  | Hot Storage | DynamoDB | Real-time aggregations, entity state | ElastiCache |
  | Cold Storage | S3 via Firehose | Raw event archive, Athena queryable | Direct S3 from Lambda |
  | Orchestration | Step Functions Express | Multi-step enrichment | Lambda chaining via SQS |
  | Error Handling | SQS DLQ + bisect-on-batch-item-failure | Poison-pill isolation | Manual retry logic |

- Key Decisions:
  - Kinesis vs SQS: need ordering + replay + multiple consumers → Kinesis
  - Shard count: peak_records_per_second / 1000
  - Parallelization factor: 1–10 concurrent Lambda per shard
  - Batch size: larger → fewer invocations → lower cost

- Scaling Path:
  - <1K events/sec: SQS → Lambda (simpler)
  - 1K–100K events/sec: Kinesis + auto-scaling shards + parallelization factor 10
  - 100K+ events/sec: Enhanced Fan-Out per consumer + Distributed Map for batch reprocessing
- Source: https://docs.aws.amazon.com/lambda/latest/dg/with-kinesis.html

**Serverless Workflow (Saga Orchestration)**
- Context: Multi-step business processes with compensation, approval, and audit trail
- AWS Source: https://docs.aws.amazon.com/step-functions/latest/dg/tutorials.html
- Services Composition:

  | Layer | Service | Purpose | Alternative |
  |-------|---------|---------|-------------|
  | Trigger | API Gateway / EventBridge | Workflow initiation | Direct StartExecution SDK call |
  | Orchestrator | Step Functions Standard | Saga coordination, retry, compensate | Express (no audit trail) |
  | Workers | Lambda + Direct Integrations | Business steps | ECS Fargate (long tasks) |
  | Data Transform | JSONata (in-state) | Payload transformation | Lambda pass-through (legacy) |
  | Variables | Step Functions Variables | Cross-state data sharing | Input/ResultPath chain (legacy) |
  | External Calls | HTTPS Endpoint task | Third-party API calls | Lambda intermediary (legacy) |
  | Approval | WaitForTaskToken + SNS | Human decision gates | Custom approval Lambda |
  | Notification | SNS/EventBridge direct integration | Workflow completion events | Lambda notification handler |

- Key Decisions:
  - Standard vs Express: audit trail required → Standard; >10K/day → Express
  - Lambda vs direct integration: business logic → Lambda; simple AWS call → direct integration
  - JSONata vs Lambda: data transformation → JSONata (2024 feature); complex logic → Lambda
  - Map state (inline vs distributed): <40 items → inline; millions of items → Distributed Map from S3

- Scaling Path:
  - Low volume (<100/day): Standard, no concerns
  - Medium (1K–100K/day): Evaluate Standard cost vs Express semantics
  - High (>100K/day): Express Workflows for child executions, Standard for parent orchestration
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html

---

## Provider Differentiators (Serverless-Specific)

```
Differentiator: Lambda SnapStart (Java/Python/Node.js)
Category: Compute
Unique Value: Pre-initializes execution environments on version publish and restores from memory snapshot on cold starts — near-zero Init phase latency without idle compute cost. No equivalent on GCP Cloud Functions or Azure Functions.
Architecture Impact: Eliminates the Java cold start penalty (1–5s → ~100ms) without Provisioned Concurrency cost. Changes the cold start decision tree: SnapStart first, Provisioned Concurrency only for strict P99 <100ms requirements.
When to Leverage: All synchronous Lambda functions on Java/Python/Node.js where cold starts impact user experience.
Caveat: Init code must be deterministic. Requires published versions. Not for container-image functions.
Source: https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html

Differentiator: Step Functions JSONata + Variables + HTTPS Endpoints (2024)
Category: Orchestration
Unique Value: Eliminates 3 categories of Lambda "glue functions": (1) JSONata replaces Lambda for data transformation, (2) Variables replace Lambda for cross-state data sharing, (3) HTTPS Endpoints replace Lambda for external API calls. Reduces function count, cost, and operational surface by 30–50% in orchestrated workflows.
Architecture Impact: Step Functions becomes a true low-code orchestration platform — Lambda reserved for business logic only. Architecture diagrams simplify. IAM role surface reduces. Cold start latency eliminated for transform/routing steps.
When to Leverage: All new Step Functions workflows. Migration of existing workflows with "glue Lambda" functions.
Caveat: JSONata has a learning curve. HTTPS Endpoints require EventBridge Connection for authentication. Variables are scoped to execution (not persistent).
Source: https://docs.aws.amazon.com/step-functions/latest/dg/transforming-data.html

Differentiator: EventBridge Pipes
Category: Integration
Unique Value: Managed point-to-point integration with built-in filtering, enrichment, and transformation — replacing custom Lambda "filter and forward" functions. Connects SQS, Kinesis, DynamoDB Streams, MSK directly to targets (Lambda, Step Functions, API destinations) with optional Lambda/API enrichment.
Architecture Impact: Eliminates a class of Lambda functions whose sole purpose was filtering events from a stream and forwarding qualifying events. Reduces function count, simplifies architecture, removes custom polling code.
When to Leverage: DynamoDB Streams → filter to INSERT only → Lambda. SQS → enrich with metadata → Step Functions. Kinesis → filter by event type → EventBridge bus.
Caveat: 1:1 routing only (one source → one target). Not for fan-out (use EventBridge Bus as target, then rules). Adds ~50–100ms latency for enrichment step.
Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-pipes.html

Differentiator: Lambda Response Streaming
Category: Compute
Unique Value: Progressive HTTP response streaming from Lambda to client (via Function URL or HTTP API) before handler completes. Enables LLM token streaming, large file generation, and long-running operations without timeout constraints.
Architecture Impact: Enables serverless LLM inference endpoints without SageMaker. Bypasses API Gateway's 29-second integration timeout for streaming use cases. Changes the architecture for AI/ML APIs.
When to Leverage: LLM token streaming (Bedrock → Lambda → client), large file generation, progressive data export.
Caveat: Function URL or HTTP API only (not REST API). Node.js/Python streaming SDK required. Unlimited response size.
Source: https://docs.aws.amazon.com/lambda/latest/dg/configuration-response-streaming.html

Differentiator: Lambda Powertools (AWS-maintained)
Category: Operational
Unique Value: Production-grade utilities (Python/TypeScript/Java/.NET) for structured logging, tracing, metrics (EMF), idempotency, feature flags, batch processing, and parameter caching. Reduces boilerplate 60–80%.
Architecture Impact: Standardizes operational baseline across teams. Idempotency utility provides DynamoDB-backed exactly-once semantics without custom implementation. Logger auto-propagates correlation IDs.
When to Leverage: Every Lambda function project. Non-negotiable for production workloads.
Caveat: Adds 15–40 MB to deployment package (use Lambda Layers). AWS-specific (not portable).
Source: https://docs.powertools.aws.dev/lambda/

Differentiator: DynamoDB Global Tables + EventBridge Global Endpoints
Category: Multi-Region
Unique Value: Active-active multi-region serverless architecture with automatic data replication (DynamoDB) and event failover (EventBridge). No equivalent managed multi-region serverless stack on other providers.
Architecture Impact: Enables multi-region active-active serverless with near-zero RPO and seconds RTO — without custom replication logic. Route 53 latency routing + Global Tables + Global Endpoints = complete multi-region serverless.
When to Leverage: Mission-critical workloads requiring <5s RTO and near-zero RPO. Global user base requiring low-latency access in multiple regions.
Caveat: DynamoDB Global Tables: ~2× write cost, last-writer-wins conflict resolution. EventBridge Global Endpoints: health check latency for failover.
Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GlobalTables.html
```

---

## Scenario Coverage

**Standard Case**: Production serverless REST API with event-driven backend
- Approach:
  - API Gateway HTTP API → Lambda (arm64, SnapStart, Powertools) → DynamoDB (on-demand, single-table)
  - Cognito User Pool JWT authorizer on all routes
  - Asynchronous side effects via EventBridge: OrderPlaced → fan-out to notification + analytics + fulfillment
  - Each consumer: SQS queue + DLQ + dedicated Lambda + per-function IAM role
  - Step Functions Standard for multi-step order fulfillment (saga with compensation)
  - CloudFront + WAF for edge security and caching
  - Full observability: Powertools (logging + tracing + metrics), X-Ray, CloudWatch alarms
  - CodeDeploy canary deployment (10% for 10 min, auto-rollback on alarm)
- Key Decisions:
  - HTTP API vs REST API → HTTP API (unless WAF/caching/validation needed at API level)
  - Single-table vs multi-table DynamoDB → based on team single-table design experience
  - SnapStart vs Provisioned Concurrency → SnapStart for standard P99; Provisioned for sub-100ms SLA

**Edge Case**: Flash sale with 100× traffic spike
- Approach:
  - Pre-scale: Provisioned Concurrency (scheduled scaling) 30 min before event
  - DynamoDB: switch to provisioned + aggressive auto-scaling for peak write throughput
  - Queue-buffered checkout: immediate 202 Accepted → SQS → Lambda (async processing)
  - CloudFront: aggressive caching for product catalog (no Lambda for reads during spike)
  - Account concurrency increase pre-approved with AWS Support
  - SQS FIFO with deduplication for exactly-once checkout
  - Circuit breaker on payment gateway (Step Functions-based)

**Anti-Pattern Case**: Developer proposes "simplifying" by sharing one IAM role across all Lambda functions
- Clarification:
  Ask: "What is the blast radius if the public-facing API function is compromised? With a shared wildcard role, the attacker gains access to every AWS resource every function touches — DynamoDB tables, S3 buckets, SQS queues, Secrets Manager secrets across all services."
  Instruction: Per-function roles are auto-generated by SAM/CDK (zero manual effort). Add Permission Boundaries as a safety net. Enable IAM Access Analyzer. Implement `iam-policy-no-statements-with-admin-access` Config rule in CI/CD.

**Anti-Pattern Case**: Architecture without DLQs "because our code doesn't fail"
- Clarification:
  Ask: "What happens when the downstream database has a 5-minute outage? For async Lambda invocations (S3, SNS, EventBridge), events are retried 0–2 times and then permanently discarded. For SQS, messages exceed retention period. Without a DLQ, you have zero visibility into lost events and no replay capability."
  Instruction: DLQ is mandatory for ALL async paths. It costs <$1/month for DLQ storage. The business cost of a single lost order/payment event far exceeds the infrastructure cost. Add CloudWatch alarm on DLQ depth > 0.

---

## Cross-Reference to Existing Research

This document synthesizes and extends the serverless architecture knowledge base established across the following research documents:

| Document | Domain | Key Contribution to This Lens |
|----------|--------|-------------------------------|
| `research_cloud_AWS_Serverless-Patterns_Lambda-2024.md` | Lambda compute | Invocation models, cold start mitigation, design patterns, reference architectures |
| `research_cloud_AWS_API-Gateway-Architecture_2024.md` | API management | HTTP/REST/WebSocket API selection, authorization patterns, VPC Links |
| `research_cloud_AWS_DynamoDB-Architecture_2024.md` | NoSQL data | Access pattern design, capacity modes, Global Tables, single-table design |
| `research_cloud_AWS_Messaging-Architecture_SQS-2024.md` | Messaging | Queue patterns, FIFO semantics, DLQ strategy, visibility timeout |
| `research_cloud_AWS_Workflow-Orchestration_StepFunctions-2024.md` | Orchestration | Standard/Express selection, JSONata, Variables, saga patterns, Distributed Map |
| `research_cloud_AWS_S3-Architecture_2024.md` | Object storage | Bucket types, lifecycle policies, event notifications, replication |
| `research_cloud_AWS_CDN-Architecture_CloudFront-2024.md` | Edge delivery | Distribution patterns, caching, edge functions, OAC security |
| `research_cloud_AWS_Route53-Architecture_2024.md` | DNS & traffic | Routing policies, health checks, multi-region failover, ALIAS records |
| `research_cloud_AWS_Security-Architecture_Cognito-2024.md` | Identity (CIAM) | User Pools, JWT auth, federation, feature plans, PKCE flows |

Architects should consult individual service research documents for deep-dive guidance on specific service configuration. This Lens document provides the holistic architectural perspective — how services compose together under Well-Architected principles.

---

## Well-Architected Review Checklist (Serverless Lens Summary)

### Operational Excellence
- [ ] All resources defined in IaC (SAM/CDK/Terraform)
- [ ] Structured JSON logging with correlation IDs (Powertools)
- [ ] Distributed tracing enabled (X-Ray/ADOT)
- [ ] Canary deployments with auto-rollback (CodeDeploy)
- [ ] CloudWatch alarms per function (Errors, Throttles, Duration)
- [ ] CloudWatch Logs retention explicitly set (not infinite)
- [ ] DLQ investigation runbook documented and tested

### Security
- [ ] Per-function execution roles (no shared roles, no wildcards)
- [ ] Authorization on every API route (Cognito/Lambda authorizer/IAM)
- [ ] WAF attached to public API Gateway stages / CloudFront
- [ ] Secrets in Secrets Manager / Parameter Store (not env vars/code)
- [ ] Amazon Inspector enabled for Lambda vulnerability scanning
- [ ] Code signing enabled (AWS Signer)
- [ ] VPC Endpoints for Lambda in VPC (no NAT for AWS API calls)

### Reliability
- [ ] DLQ/on-failure destination for every async invocation path
- [ ] Every handler is idempotent (Powertools Idempotency or equivalent)
- [ ] bisect-on-batch-item-failure for all stream Event Source Mappings
- [ ] Reserved concurrency set for critical and high-volume functions
- [ ] DynamoDB PITR enabled for all production tables
- [ ] Explicit function timeouts (not default 3s)
- [ ] Lambda Recursive Loop Detection verified enabled

### Performance Efficiency
- [ ] Lambda Power Tuning run for all CPU-intensive functions
- [ ] SnapStart enabled for latency-sensitive functions (supported runtimes)
- [ ] arm64 (Graviton2) architecture used where dependencies allow
- [ ] VPC attachment only for functions needing private resource access
- [ ] Direct service integrations used (eliminate Lambda glue)
- [ ] Batch sizes optimized for stream/queue consumers

### Cost Optimization
- [ ] arm64 architecture (20% cost reduction)
- [ ] Memory tuned via Power Tuning
- [ ] Batch sizes maximized (reduce invocation count)
- [ ] VPC Endpoints instead of NAT Gateway
- [ ] DynamoDB on-demand for variable workloads (or provisioned + auto-scaling for steady)
- [ ] Provisioned Concurrency scheduled (not 24/7)
- [ ] CloudWatch Logs retention policy set (30/60/90 days)
- [ ] Cost allocation tags on all resources
- [ ] Step Functions Express for high-frequency workflows

### Sustainability
- [ ] arm64 (Graviton2) — more energy-efficient
- [ ] Function duration optimized (shorter execution = less compute)
- [ ] Batch processing reduces per-unit overhead
- [ ] Managed services preferred over always-on custom consumers
