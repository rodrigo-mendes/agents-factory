# AWS Lambda — Serverless Patterns Knowledge Base

---

## Metadata

```yaml
Full_Name: "AWS Serverless Patterns — AWS Lambda"
Cloud_Provider: "AWS"
Architecture_Domain: "Serverless Patterns"
Target_Edition: "AWS Lambda 2024"
Architecture_Context: "Event-driven serverless applications using AWS Lambda as the primary compute primitive — covering synchronous APIs, asynchronous event processing, scheduled jobs, streaming consumers, and orchestrated workflows"
Official_Source_URL: "https://docs.aws.amazon.com/lambda/latest/dg/welcome.html"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-05-25"
Currency_Threshold: "2027-05-25 — review required after this date due to Lambda feature velocity"
```

---

## Executive Summary

AWS Lambda is the foundational compute primitive of the AWS serverless ecosystem. It executes function code in response to events from 200+ AWS service integrations and HTTP endpoints, charging only for invocation count and execution duration (rounded to 1ms). Lambda's 2024 edition consolidated a substantial set of capabilities: SnapStart for Java (GA since late 2022, extended to Python/Node.js in 2024), response streaming for HTTP APIs, 10 GB ephemeral storage per function, 16-vCPU/10 GB memory ceiling, and native IPv6 support in VPC. The Lambda managed runtimes now include Python 3.12, Node.js 22, Java 21 (Corretto), Ruby 3.3, and the AL2023-based custom runtime. Deprecated runtimes (Node.js 16, Python 3.8, Java 8 non-Corretto) are past end-of-support and blocked from new deployments.

The 2024 edition's most architecturally significant changes are: (1) **SnapStart for Python and Node.js** — eliminates cold start penalty for latency-sensitive workloads without the complexity of provisioned concurrency; (2) **Lambda response streaming** — enables progressive HTTP response delivery for LLM inference, large file generation, and long-running API operations without timeout constraints; (3) **Advanced Logging Controls** — JSON-structured log output natively, log level filtering per function, selectable log group destination. These shift multiple "Ask First" decisions (SnapStart vs Provisioned Concurrency, streaming vs buffered response) into well-defined patterns with clearer cost/latency profiles.

The three most critical architecture guardrails for Lambda deployments are: (1) **never share execution roles across multiple Lambda functions** — overly broad IAM permissions on a shared role violate least-privilege and expand blast radius across all functions sharing that role; (2) **always configure a Dead Letter Queue (DLQ) or on-failure event destination for all asynchronous invocations** — without it, events are silently discarded after retry exhaustion; (3) **always set per-function reserved concurrency for critical paths** — without it, a traffic spike on one function can exhaust the account-level concurrency pool and cause throttling on unrelated functions.

---

## Cloud Architecture Glossary

```
Term: Invocation Model
Definition: The mechanism by which Lambda receives and processes events. Three models: Synchronous (caller waits for response — API Gateway, ALB, SDK), Asynchronous (Lambda queues the event internally and retries on failure — S3, SNS, EventBridge), and Poll-based (Lambda polls a stream/queue and processes batches — SQS, Kinesis, DynamoDB Streams, MSK, Kafka).
Provider Docs Section: https://docs.aws.amazon.com/lambda/latest/dg/invocation-sync.html
Architect Usage: Invocation model determines error handling strategy. Synchronous → caller handles errors. Asynchronous → DLQ/on-failure destination required. Poll-based → bisect-on-error and destination for failures.
Common Confusion: S3 event notifications invoke Lambda asynchronously, not synchronously — even though S3 triggers look like "direct integrations." This means S3 events are retried up to 3 times by Lambda internally before going to DLQ.

Term: Cold Start
Definition: The latency penalty incurred when Lambda initializes a new execution environment: downloading the deployment package, starting the runtime, running the Init code (outside the handler), and establishing VPC network interfaces (if applicable). Does NOT occur on warm invocations (reused execution environments).
Provider Docs Section: https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html
Architect Usage: Cold start impact is runtime- and package-size-dependent. Java/C# cold starts are 1–5s. Python/Node.js are 200–800ms. AL2023 custom runtimes vary. Mitigation options: SnapStart (Java/Python/Node.js), Provisioned Concurrency (all runtimes), minimized deployment package size, avoid VPC unless required.
Common Confusion: Cold start ≠ function timeout. A cold start is initialization latency before the handler runs. The 15-minute function timeout applies to the handler execution itself, not to initialization.

Term: Execution Environment
Definition: A secure, isolated runtime environment (micro-VM via Firecracker) that hosts exactly one concurrent Lambda function invocation. Contains the runtime process, the function code, and the /tmp file system. Environments are reused across invocations of the same function version for a period of time (minutes to hours).
Provider Docs Section: https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html
Architect Usage: Execution environment reuse is the mechanism behind warm starts. Safe to cache SDK clients, DB connections, and configuration in module-level global scope — they persist across invocations in the same environment. Do NOT store user-specific state in globals.
Common Confusion: Lambda does not provide a persistent process — execution environments are ephemeral and may be replaced at any time. Do not rely on in-memory state surviving across Lambda deployments, version updates, or environment recycling.

Term: Provisioned Concurrency
Definition: A configuration that initializes a specified number of execution environments in advance and keeps them warm, eliminating cold starts for those environments. Billed at a higher rate than on-demand invocations even when idle.
Provider Docs Section: https://docs.aws.amazon.com/lambda/latest/dg/provisioned-concurrency.html
Architect Usage: Use for synchronous APIs with strict P99 latency SLAs. Apply to a function Alias (not $LATEST) or Version. Combine with Application Auto Scaling to adjust based on schedule or custom metrics. Do NOT use for async/batch functions where cold start tolerance is higher.
Common Confusion: Provisioned Concurrency does not increase the maximum concurrency limit — it guarantees warm environments for the configured count. If traffic exceeds provisioned concurrency, on-demand (cold) environments are used.

Term: Reserved Concurrency
Definition: A hard limit on the maximum number of concurrent invocations for a specific function. Acts as both a ceiling (throttles invocations above limit) and a floor (reserves capacity from the account pool for this function).
Provider Docs Section: https://docs.aws.amazon.com/lambda/latest/dg/configuration-concurrency.html
Architect Usage: Set reserved concurrency on critical functions to guarantee capacity and on high-volume functions to prevent them from starving others. Setting reserved concurrency to 0 effectively disables a function.
Common Confusion: Reserved Concurrency ≠ Provisioned Concurrency. Reserved = maximum concurrent invocations (throttle ceiling). Provisioned = pre-warmed environments (eliminates cold starts). They are orthogonal settings.

Term: SnapStart
Definition: A Lambda feature (supported on Java Corretto 11+, Python 3.12+, Node.js 20+ as of 2024) that pre-initializes execution environments when a function version is published, snapshots the initialized state, and restores from snapshot on subsequent invocations — eliminating cold start initialization overhead.
Provider Docs Section: https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html
Architect Usage: Enable SnapStart for synchronous, latency-sensitive functions on supported runtimes. Requires publishing a function version (not $LATEST). Verify that Init code is deterministic and idempotent — SnapStart replays Init from snapshot, not from scratch.
Common Confusion: SnapStart is not Provisioned Concurrency. SnapStart reduces cold start duration by restoring from a snapshot (near-zero Init time) but still incurs a brief environment restore latency (~100ms). Provisioned Concurrency eliminates cold starts entirely by keeping environments alive.

Term: Event Source Mapping
Definition: A Lambda resource that reads from a poll-based event source (SQS, Kinesis, DynamoDB Streams, MSK, self-managed Kafka, Amazon MQ) and invokes the function with batches of records. Managed by the Lambda service — no polling code in the function.
Provider Docs Section: https://docs.aws.amazon.com/lambda/latest/dg/invocation-eventsourcemapping.html
Architect Usage: Configure batch size, batching window, bisect-on-batch-item-failure, maximum retry attempts, destination for failures, and parallelization factor (Kinesis/DynamoDB Streams). Enabling bisect-on-batch-item-failure is critical for poison-pill message isolation.
Common Confusion: SQS-triggered Lambda is poll-based (Event Source Mapping), not push-based — Lambda polls SQS internally. This differs from SNS → Lambda which is push-based (asynchronous invocation). Error handling strategies differ between these two patterns.

Term: Lambda Extension
Definition: A process (internal or external) that runs alongside the Lambda function handler within the execution environment. Internal extensions run in the function process; external extensions run as separate processes. Used for monitoring agents, security scanners, secrets fetchers, and custom runtime capabilities.
Provider Docs Section: https://docs.aws.amazon.com/lambda/latest/dg/lambda-extensions.html
Architect Usage: Lambda Extensions are the approved mechanism for integrating APM agents (Datadog, Dynatrace, New Relic), secrets managers (Secrets Manager cache), and security tools (AWS AppConfig, Parameter Store caching). Extensions add Init latency — measure impact before enabling in production.
Common Confusion: Extensions share CPU and memory with the function handler. A poorly written extension can increase cold start time and reduce available compute for the handler. External extensions are processes — they can leak memory independent of handler code.

Term: Function URL
Definition: A dedicated HTTPS endpoint for a Lambda function that enables direct HTTP invocation without API Gateway. Supports IAM authentication or NONE (public). Supports response streaming. Regional, not globally distributed.
Provider Docs Section: https://docs.aws.amazon.com/lambda/latest/dg/lambda-urls.html
Architect Usage: Use Function URLs for simple, single-function HTTP APIs where API Gateway features (auth, routing, throttling, caching, WAF) are not needed. Ideal for webhook receivers, LLM streaming endpoints, and S3-triggered image processing APIs.
Common Confusion: Function URLs bypass API Gateway — they do not inherit API Gateway features like WAF integration, usage plans, throttling policies, or custom domain mapping at the API level. For production APIs requiring these, use API Gateway.

Term: Lambda Power Tuning
Definition: An AWS-provided open-source Step Functions state machine (AWS Lambda Power Tuning) that runs a function at multiple memory configurations, measures performance and cost, and returns an optimization recommendation. Not a Lambda built-in — deployed separately.
Provider Docs Section: https://docs.aws.amazon.com/lambda/latest/operatorguide/profile-functions.html
Architect Usage: Run Power Tuning before production deployment of CPU-intensive or latency-sensitive functions. Memory directly controls allocated CPU (higher memory = more CPU). Optimal memory setting is rarely the minimum or maximum — profiling is required.
Common Confusion: Lambda memory setting controls BOTH memory AND CPU — they are not independently configurable. Increasing memory from 128 MB to 1024 MB gives significantly more CPU, which often reduces execution time enough to decrease total cost despite higher per-ms billing rate.

Term: Destination
Definition: An asynchronous invocation result routing target for successful (on-success) or failed (on-failure) invocations. Valid destinations: SQS queue, SNS topic, EventBridge event bus, Lambda function. Supersedes DLQ for asynchronous functions — richer metadata including original event payload.
Provider Docs Section: https://docs.aws.amazon.com/lambda/latest/dg/invocation-async-retain-records.html
Architect Usage: Always configure an on-failure destination for asynchronous Lambda functions in production. Prefer Destinations over DLQ for new designs — Destinations pass the full invocation result including error details. DLQ only receives the original event payload without error context.
Common Confusion: Destinations ≠ DLQ. Both handle failed async invocations, but Destinations provide richer failure metadata and support on-success routing as well. SQS-triggered Lambda (poll-based) uses its own failure destination setting in the Event Source Mapping, not the function-level Destination.
```

---

## Architecture Framework Analysis: AWS Well-Architected Serverless Lens

```
Pillar: Operational Excellence
Definition: The ability to run and monitor systems to deliver business value and to continually improve supporting processes and procedures.
Key Design Principles:
  - Organize operations as code (IaC for Lambda functions, event source mappings, layers)
  - Make frequent, small, reversible changes (function aliases for traffic shifting)
  - Refine operations procedures frequently (game days, chaos engineering)
  - Anticipate failure (DLQ, on-failure destinations, circuit breakers)
  - Learn from all operational failures (structured logs, distributed tracing)
Applies To Event-Driven Serverless: Serverless Lens mandates structured JSON logging (Lambda Advanced Logging Controls), distributed tracing via X-Ray or ADOT, and deployment via IaC (SAM/CDK/Terraform). Function aliases enable canary deployments with automatic rollback via CloudWatch alarms.
Assessment Questions:
  1. Are all Lambda function configurations (memory, timeout, concurrency) defined in IaC?
  2. Are structured logs emitted in JSON with correlation IDs propagated across service boundaries?
  3. Are canary deployments configured for production function updates with alarm-triggered rollback?
Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/operational-excellence.html

Pillar: Security
Definition: The ability to protect data, systems, and assets while delivering business value through risk assessments and mitigation strategies.
Key Design Principles:
  - Apply security at all layers (function code, execution role, VPC, API Gateway, WAF)
  - Enable traceability (CloudTrail for Lambda API calls, X-Ray for invocation chains)
  - Implement least privilege (per-function execution roles, no wildcard policies)
  - Protect data in transit and at rest (encrypted environment variables, KMS, TLS)
  - Keep people away from data (automated incident response, no direct prod access)
Applies To Event-Driven Serverless: Every Lambda function must have a dedicated execution role with only the permissions it needs. Environment variables containing secrets must be encrypted with a CMK. VPC attachment must be evaluated for functions accessing private resources — not applied universally.
Assessment Questions:
  1. Does each Lambda function have its own execution role with minimum required permissions?
  2. Are all secrets accessed via Secrets Manager or Parameter Store — never in environment variables in plaintext?
  3. Are function invocations authenticated (IAM auth on Function URLs, API Gateway authorizers)?
Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/security.html

Pillar: Reliability
Definition: The ability of a workload to perform its intended function correctly and consistently.
Key Design Principles:
  - Test recovery procedures (DLQ draining runbooks, replay procedures)
  - Automatically recover from failure (retry policies, DLQ, circuit breakers via Step Functions)
  - Scale horizontally (Lambda scales automatically — architect for stateless handlers)
  - Stop guessing capacity (no pre-provisioning — monitor reserved concurrency headroom)
  - Manage change in automation (alias-based deployments, automated rollback)
Applies To Event-Driven Serverless: Serverless Lens reliability depends on idempotent handler design (required for async/poll-based invocations with retries), poison-pill handling (bisect-on-batch-item-failure for Kinesis/SQS), and DLQ strategy for every async invocation path.
Assessment Questions:
  1. Is every Lambda handler designed to be idempotent (safe to invoke multiple times with the same event)?
  2. Is there a DLQ or on-failure destination configured for every asynchronous Lambda invocation path?
  3. Is bisect-on-batch-item-failure enabled for all Event Source Mappings?
Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/reliability.html

Pillar: Performance Efficiency
Definition: The ability to use computing resources efficiently to meet system requirements and to maintain that efficiency as demand changes.
Key Design Principles:
  - Democratize advanced technologies (use managed event sources — no polling code)
  - Go global in minutes (Lambda@Edge / CloudFront Functions for edge processing)
  - Use serverless architectures (Lambda over EC2 for irregular workloads)
  - Experiment more often (Lambda Power Tuning for memory optimization)
  - Consider mechanical sympathy (runtime selection, package size, init code optimization)
Applies To Event-Driven Serverless: Memory tuning via Lambda Power Tuning is mandatory before production for CPU-intensive functions. SnapStart is the first-line cold start mitigation for Java/Python/Node.js. VPC attachment adds ~100ms cold start — avoid unless private resource access is required.
Assessment Questions:
  1. Have all production Lambda functions been profiled with Lambda Power Tuning?
  2. Is SnapStart or Provisioned Concurrency used for latency-sensitive synchronous functions?
  3. Is VPC attachment limited to functions that genuinely require private network access?
Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/performance-efficiency.html

Pillar: Cost Optimization
Definition: The ability to avoid unnecessary costs and achieve business outcomes at the lowest price point.
Key Design Principles:
  - Implement cloud financial management (Lambda cost tracking via Cost Allocation Tags)
  - Adopt a consumption model (Lambda charges only for invocation count + duration)
  - Measure overall efficiency (cost per invocation, cost per transaction metric)
  - Stop spending money on undifferentiated heavy lifting (SQS/SNS/EventBridge vs custom queuing)
  - Analyze and attribute expenditure (per-function cost dashboards via Cost Explorer)
Applies To Event-Driven Serverless: Lambda cost optimization is primarily driven by memory tuning (higher memory often reduces duration enough to decrease total cost) and avoiding architectural patterns that cause excessive invocations (fan-out storms, recursive invocations).
Assessment Questions:
  1. Has Lambda Power Tuning been run to find the cost-optimal memory setting for each function?
  2. Are SQS batching and Kinesis aggregation configured to reduce per-invocation count?
  3. Is there a circuit breaker or concurrency limit to prevent runaway recursive invocation cost?
Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/cost-optimization.html

Pillar: Sustainability
Definition: Minimizing environmental impact of running cloud workloads.
Key Design Principles:
  - Understand your impact (Lambda billing granularity enables per-function carbon proxy metrics)
  - Establish sustainability goals (minimize idle compute — Lambda's consumption model is inherently efficient)
  - Maximize utilization (optimize function duration — shorter execution = less compute = lower emissions)
  - Use managed services (avoid self-managed queue consumers that run continuously)
  - Minimize data transfer (process data close to storage — use S3 Object Lambda, Lambda@Edge)
Applies To Event-Driven Serverless: Lambda's pay-per-use model is inherently sustainable — no idle compute. Duration optimization (memory tuning, efficient code) directly reduces both cost and environmental impact.
Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/sustainability-pillar.html
```

---

## Architecture Guardrails

### ✅ Mandatory Patterns

**Per-Function Execution Role (Least Privilege)**
- Pillar Alignment: Security
- Why: AWS Well-Architected Serverless Lens — "Grant each function only the permissions that it requires. Use separate IAM roles for each function to implement the principle of least privilege."
- AWS Services: AWS IAM (Roles, Policies), AWS Lambda (Execution Role)
- Architecture Decision:
  Each Lambda function is assigned a unique IAM role. Policies are scoped to specific resources (ARN-level) and specific actions required by that function. No wildcard `*` on actions or resources. Trust policy restricts to `lambda.amazonaws.com` only.
  ```
  Execution Role per function:
    - AWSLambdaBasicExecutionRole (or inline policy for CloudWatch Logs)
    - Explicit resource ARNs: arn:aws:s3:::my-bucket/prefix/*
    - Explicit actions: s3:GetObject only (not s3:*)
    - No cross-function role sharing
  ```
- Verification:
  ```bash
  # List all Lambda execution roles and check for wildcard policies
  aws lambda list-functions --query 'Functions[*].[FunctionName,Role]' --output table
  # Check attached policies for wildcard actions
  aws iam get-policy-version --policy-arn <arn> --version-id v1
  # AWS Security Hub control: Lambda.1 - Lambda functions should prohibit public access
  # IAM Access Analyzer: identifies overly permissive policies
  ```
- Trade-offs: More IAM roles to manage. Mitigate with IaC (SAM/CDK auto-generates per-function roles).
- Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/security.html

**Dead Letter Queue / On-Failure Destination for Async Invocations**
- Pillar Alignment: Reliability
- Why: AWS Serverless Lens — "Use dead-letter queues and on-failure destinations to capture events that fail processing after maximum retries are exhausted. Without them, failed events are silently discarded."
- AWS Services: Amazon SQS (DLQ), Amazon SNS, Amazon EventBridge, AWS Lambda (Async Destinations)
- Architecture Decision:
  All Lambda functions invoked asynchronously (S3, SNS, EventBridge, direct async SDK calls) must have an on-failure Destination or DLQ configured. Prefer Destinations (richer metadata). Configure maximum retry attempts (0–2) explicitly — do not rely on the default of 2 retries.
  ```
  Async function configuration:
    - on_failure_destination: SQS ARN or EventBridge bus ARN
    - maximum_retry_attempts: 1 (for non-idempotent) or 2 (for idempotent)
    - maximum_event_age_seconds: set to business SLA (e.g., 3600s)
  DLQ on destination SQS:
    - Alarm on ApproximateNumberOfMessagesVisible > 0
    - Retention period: 14 days (max)
  ```
- Verification:
  ```bash
  # Find async Lambda functions without DLQ or destinations
  aws lambda list-functions --output json | jq '.Functions[] | select(.DeadLetterConfig == null) | .FunctionName'
  # Check event destinations
  aws lambda get-function-event-invoke-config --function-name <name>
  # AWS Security Hub: Lambda.4 - Lambda functions should have a dead-letter queue configured
  ```
- Trade-offs: Small additional cost for SQS DLQ storage and SNS delivery. Requires operational procedure for DLQ draining.
- Source: https://docs.aws.amazon.com/lambda/latest/dg/invocation-async-retain-records.html

**Reserved Concurrency Isolation for Critical Functions**
- Pillar Alignment: Reliability
- Why: AWS Serverless Lens — "Set reserved concurrency for mission-critical functions to guarantee capacity and prevent account-level concurrency exhaustion caused by other functions."
- AWS Services: AWS Lambda (Reserved Concurrency), Amazon CloudWatch (concurrency alarms)
- Architecture Decision:
  Production workloads must not share the default account concurrency pool without any reservation. Assign reserved concurrency to: (a) critical customer-facing functions to guarantee availability, and (b) high-volume background functions to cap their footprint.
  ```
  Concurrency strategy:
    - Critical API functions: reserved concurrency = max expected concurrent invocations × 1.5
    - High-volume batch functions: reserved concurrency = cap at safe level (e.g., 100)
    - Account default pool: leave headroom of 20–30% above peak reservation
  Alarm: ConcurrentExecutions approaching reserved limit → scale or investigate
  ```
- Verification:
  ```bash
  aws lambda list-functions --output json | jq '.Functions[] | {name: .FunctionName, reserved: .ReservedConcurrentExecutions}'
  # Check account-level concurrency usage
  aws lambda get-account-settings
  # CloudWatch metric: Lambda/ConcurrentExecutions per function
  ```
- Trade-offs: Reserved concurrency reduces the pool available to other functions. Over-reservation wastes headroom. Requires periodic review as traffic patterns change.
- Source: https://docs.aws.amazon.com/lambda/latest/dg/configuration-concurrency.html

**Structured JSON Logging with Correlation IDs**
- Pillar Alignment: Operational Excellence
- Why: AWS Serverless Lens — "Use structured logging to enable filtering, aggregation, and searching of logs. Propagate correlation IDs to trace requests across distributed function invocations."
- AWS Services: AWS Lambda (Advanced Logging Controls), Amazon CloudWatch Logs, AWS X-Ray, AWS Powertools for Lambda
- Architecture Decision:
  Enable Lambda Advanced Logging Controls (JSON log format, log level filtering). Use AWS Lambda Powertools (Python/TypeScript/Java/.NET) for structured logging, tracing, and metrics. Propagate a correlation ID (request ID or generated trace ID) in every log entry and downstream call.
  ```
  Lambda function configuration:
    - LoggingConfig.LogFormat: JSON
    - LoggingConfig.ApplicationLogLevel: INFO (WARN in production)
    - LoggingConfig.SystemLogLevel: WARN
  Log event structure:
    { "level": "INFO", "service": "order-processor", "correlation_id": "...", "message": "...", "timestamp": "..." }
  ```
- Verification:
  Check Lambda function Logging Configuration in AWS Console or CLI:
  ```bash
  aws lambda get-function-configuration --function-name <name> --query 'LoggingConfig'
  ```
- Trade-offs: Slight log verbosity increase. JSON logs cost more than plain text if not filtered. Mitigate with log level control.
- Source: https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs.html

**Idempotent Handler Design**
- Pillar Alignment: Reliability
- Why: AWS Serverless Lens — "Design functions to be idempotent. Lambda may invoke your function more than once for the same event in asynchronous and poll-based invocation models."
- AWS Services: AWS Lambda Powertools (Idempotency utility), Amazon DynamoDB (idempotency table), Amazon SQS (message deduplication ID)
- Architecture Decision:
  Every Lambda handler must be safe to invoke multiple times with the same input without producing duplicate side effects. Use AWS Lambda Powertools Idempotency (DynamoDB-backed) for functions that write to external systems, trigger payments, or send notifications.
  ```
  Idempotency patterns:
    1. Conditional writes: DynamoDB PutItem with condition expression (attribute_not_exists(pk))
    2. Powertools Idempotency decorator: @idempotent — checks DynamoDB before executing handler
    3. SQS FIFO with MessageDeduplicationId for exactly-once processing
    4. Database UPSERT with unique constraint on idempotency key
  ```
- Verification: Load test with duplicate events; verify no duplicate database writes, no duplicate downstream API calls.
- Trade-offs: DynamoDB idempotency table adds ~1–2ms per invocation (cached lookups). FIFO SQS has lower throughput than standard SQS (3000 msg/s with batching vs unlimited).
- Source: https://docs.powertools.aws.dev/lambda/python/latest/utilities/idempotency/

**AWS X-Ray Distributed Tracing**
- Pillar Alignment: Operational Excellence, Security
- Why: AWS Serverless Lens — "Implement distributed tracing to identify the root cause of latency issues and errors across service boundaries in event-driven architectures."
- AWS Services: AWS X-Ray, AWS Distro for OpenTelemetry (ADOT), Lambda (X-Ray integration), API Gateway (X-Ray), SQS (X-Ray), SNS (X-Ray)
- Architecture Decision:
  Enable X-Ray active tracing on all Lambda functions. Propagate trace context (X-Amzn-Trace-Id header) in all downstream HTTP calls and SDK calls. Segment sensitive operations (DB queries, external API calls) as subsegments. For new deployments, prefer ADOT Lambda Layer over native X-Ray SDK for vendor-neutral tracing.
  ```bash
  # Enable X-Ray via IaC (SAM/CDK) or CLI
  aws lambda update-function-configuration --function-name <name> --tracing-config Mode=Active
  ```
- Trade-offs: X-Ray adds ~1–5% request overhead and costs per trace. ADOT layer adds ~30–50 MB to deployment package size.
- Source: https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html

---

### ⚠️ Architectural Decisions

**Cold Start Mitigation Strategy**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | SnapStart | Lambda SnapStart (Java 11+, Python 3.12+, Node.js 20+) | Init latency (near-zero restore), no idle cost | Requires published version, restore latency ~100ms, Init code must be deterministic | New deployments on supported runtimes needing low p99 latency |
  | Provisioned Concurrency | Lambda Provisioned Concurrency + Application Auto Scaling | Eliminates cold starts entirely for provisioned count | Billed when idle, requires capacity planning | Strict P99 SLA (<100ms), predictable traffic patterns, financial services |
  | Keep-Warm Ping | EventBridge Scheduler + synthetic invocations | Zero additional Lambda cost for low-frequency pings | Does not work at scale, synthetic traffic pollutes metrics, anti-pattern for high concurrency | NOT RECOMMENDED — use SnapStart or Provisioned Concurrency instead |
  | None / Accept Cold Starts | No mitigation | Zero cost | Cold start latency on first invocations | Async workloads, batch processing, scheduled jobs, internal tooling |

- Cost Profile: SnapStart = free (no additional cost). Provisioned Concurrency = billed per environment-hour even when idle (~3× on-demand rate). Accept cold starts = lowest cost.
- Scaling Characteristics: Provisioned Concurrency provides warm environments up to the configured count; beyond that, on-demand environments are used (with cold starts). SnapStart provides fast restore for any new environment.
- Operational Burden: SnapStart requires publishing Lambda versions (not $LATEST). Provisioned Concurrency requires concurrency capacity planning and auto-scaling policy tuning.
- Lock-in Assessment: Both are Lambda-specific features with no direct equivalent on other providers (GCP Cloud Run has minimum instances, Azure Functions has Premium Plan always-on).
- Ask The Architect: "What is the acceptable P99 latency budget for this function's cold start path, and what is the traffic pattern (predictable peaks vs random spikes)?"
- Source: https://docs.aws.amazon.com/lambda/latest/dg/provisioned-concurrency.html

**HTTP Trigger Strategy: API Gateway vs Application Load Balancer vs Function URL**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | API Gateway HTTP API | Amazon API Gateway (HTTP API) | Cost (70% cheaper than REST API), JWT auth, low latency | Fewer features than REST API (no caching, no request validation) | Most serverless REST/HTTP APIs, microservices, mobile backends |
  | API Gateway REST API | Amazon API Gateway (REST API) | Full feature set: caching, request validation, usage plans, X-Ray | Higher cost, higher latency than HTTP API | APIs needing caching, throttling per-method, API key management, request/response transformation |
  | Application Load Balancer | AWS ALB + Lambda Target Group | EC2/ECS/Lambda unified routing, health checks, WAF integration, static IP | No native JWT auth, manual auth lambda required | Hybrid environments routing to both Lambda and containers, internal APIs |
  | Function URL | Lambda Function URL | Simplest setup, no API Gateway cost, supports response streaming | No request routing, no native throttling, no WAF, regional only | Webhook receivers, LLM streaming, single-function endpoints, development/testing |

- Cost Profile: Function URL = free (Lambda invocation only). HTTP API = ~$1/million requests. REST API = ~$3.50/million requests. ALB = ~$0.008/LCU-hour + $0.008/GB processed.
- Scaling Characteristics: All scale with Lambda's concurrency model. API Gateway has a default 10,000 RPS regional limit (adjustable). ALB scales independently. Function URLs scale with Lambda account concurrency.
- Operational Burden: REST API has the most configuration surface area. HTTP API and Function URLs have simpler configuration. ALB requires load balancer management.
- Lock-in Assessment: API Gateway is AWS-specific. ALB has equivalents (GCP Cloud Load Balancing, Azure Application Gateway). Function URLs are Lambda-specific.
- Ask The Architect: "Does this API need request caching, throttling per consumer, WAF integration, or routing to non-Lambda backends? If yes, use API Gateway. If it's a single-function endpoint with streaming, use Function URL."
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html

**Asynchronous Communication Pattern: SQS vs SNS vs EventBridge**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Point-to-Point Queue | Amazon SQS Standard/FIFO | At-least-once delivery, decoupling, backpressure, batching | No fan-out, single consumer pattern, ordering requires FIFO | Command-style messages, work queues, rate limiting downstream |
  | Fan-out Pub/Sub | Amazon SNS + SQS fan-out | One publisher → multiple subscribers, push delivery | No filtering on content (basic attribute filtering only), no replay | Notifications, broadcasting events to multiple consumers |
  | Event Bus | Amazon EventBridge | Content-based routing, schema registry, event archive/replay, SaaS integration | Higher cost than SQS/SNS, 1-second event delivery SLA | Domain events, microservices event bus, cross-account routing, SaaS integrations |
  | Streaming | Amazon Kinesis Data Streams | Ordered, replayable, multi-consumer, millisecond delivery | Operational complexity (shard management), higher cost for low-volume | High-throughput event streams, analytics pipelines, audit logs |

- Cost Profile: SQS = $0.40/million requests. SNS = $0.50/million. EventBridge = $1/million custom events. Kinesis = $0.015/shard-hour + $0.04/million PUT records.
- Scaling Characteristics: SQS scales unboundedly. SNS: 1M fan-out per topic. EventBridge: 10,000 rules per bus (adjustable). Kinesis: linear scaling by adding shards.
- Lock-in Assessment: All are AWS-specific. EventBridge schema registry has no direct cross-provider equivalent.
- Ask The Architect: "Is this a command (SQS) or an event (EventBridge/SNS)? Does it need content-based routing (EventBridge)? Does it need replay (Kinesis or EventBridge Archive)? Does it need ordering (SQS FIFO or Kinesis)?"
- Source: https://aws.amazon.com/event-driven-architecture/

**Orchestration vs Choreography**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Orchestration | AWS Step Functions (Standard or Express) | Visibility, centralized error handling, retry logic, human approval steps, audit trail | Additional service cost, state machine complexity, latency per state | Multi-step workflows with compensation logic, long-running processes, financial transactions |
  | Choreography | Amazon EventBridge + Lambda | Loose coupling, independent deployment, no central coordinator, lower cost | Distributed debugging, event chain visibility requires X-Ray + EventBridge tracing, harder to reason about | Simple event chains, independent services, high-throughput event processing |

- Cost Profile: Step Functions Standard = $0.025/1000 state transitions (expensive for high-frequency workflows). Express = $1/million state transitions + duration. EventBridge = $1/million events.
- Operational Burden: Step Functions requires workflow definition (ASL JSON/YAML). EventBridge requires event schema management. Choreography has distributed debugging complexity.
- Ask The Architect: "Does this workflow need compensating transactions, human approval, or an audit trail of every state transition? If yes, use Step Functions. If it's a simple publish/subscribe chain, use EventBridge choreography."
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html

---

### 🚫 Anti-Patterns

**Recursive Lambda Invocations Without Circuit Breaker**
- Risk Level: CRITICAL
- Why: Reliability + Cost — Lambda can invoke itself (via SQS, SNS, or SDK) in a loop. Without a circuit breaker, a single buggy deployment can trigger thousands of recursive invocations in seconds, exhausting account concurrency and generating unbounded costs.
- Instead:
  - Never have a Lambda function trigger itself via the same event source it processes
  - Use Step Functions for recursive/looping workflows (built-in iteration control)
  - Set reserved concurrency as a hard cap on recursive functions
  - Enable Lambda Recursive Loop Detection (AWS-managed, detects Lambda→SQS→Lambda→SQS loops and halts after 16 recursions as of 2023)
  ```bash
  # Verify recursive loop detection is enabled (default on, verify not disabled)
  aws lambda get-function-recursion-config --function-name <name>
  ```
- Detection:
  ```bash
  # Monitor for exponential invocation growth
  # CloudWatch alarm: Lambda/Invocations with Sum > threshold in 1-minute period
  # Check for Lambda → SQS → Lambda patterns in architecture diagrams
  aws lambda get-function-recursion-config --function-name <name>
  ```
- Impact: Cost overrun (unbounded), Service outage (concurrency exhaustion for all functions in account)
- Source: https://docs.aws.amazon.com/lambda/latest/dg/invocation-recursion.html

**Storing Sensitive Data in Lambda Environment Variables Without KMS Encryption**
- Risk Level: CRITICAL
- Why: Security — Lambda environment variables are stored encrypted at rest by AWS-managed keys by default, but are visible in plaintext in the console and API to anyone with `lambda:GetFunctionConfiguration` permission. Without a CMK, there is no audit trail of who accessed the key.
- Instead:
  - Store secrets in AWS Secrets Manager or AWS Systems Manager Parameter Store (SecureString)
  - Fetch at runtime using the AWS Parameters and Secrets Lambda Extension (cached, no SDK call overhead)
  - If environment variables must be used, encrypt with a KMS CMK (customer-managed) and grant decrypt only to the function execution role
  ```
  # Preferred: Fetch from Secrets Manager at init time (cached)
  # Use Lambda Extension: AWS Parameters and Secrets Lambda Extension Layer
  # GET http://localhost:2773/secretsmanager/get?secretId=my-secret
  ```
- Detection:
  ```bash
  # List functions with environment variables — check for API keys, passwords, connection strings
  aws lambda get-function-configuration --function-name <name> --query 'Environment'
  # AWS Security Hub: Lambda.3 - Lambda functions should use supported runtimes
  # AWS Config Rule: lambda-function-settings-check
  ```
- Impact: Data breach (credentials exposed via Lambda API), Compliance violation (GDPR, PCI-DSS, SOC2)
- Source: https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html#configuration-envvars-encryption

**Overly Broad Lambda Execution Role (Wildcard Permissions)**
- Risk Level: CRITICAL
- Why: Security — AWS Serverless Lens — "Granting AdministratorAccess or wildcard resource/action policies to Lambda execution roles is equivalent to giving function code the ability to exfiltrate all AWS resources and escalate privileges."
- Instead:
  - Create per-function execution roles with specific actions and resource ARNs
  - Use AWS IAM Access Analyzer to detect overly permissive policies
  - Start from AWSLambdaBasicExecutionRole and add only required permissions
  ```
  # BAD:
  { "Effect": "Allow", "Action": "*", "Resource": "*" }
  # GOOD:
  { "Effect": "Allow", "Action": ["dynamodb:GetItem", "dynamodb:PutItem"],
    "Resource": "arn:aws:dynamodb:us-east-1:123456789:table/MyTable" }
  ```
- Detection:
  ```bash
  aws iam get-policy-version --policy-arn <role-policy-arn> --version-id v1
  # AWS IAM Access Analyzer: enables.finding of external + internal overly permissive access
  # AWS Config Rule: iam-policy-no-statements-with-admin-access
  ```
- Impact: Data breach, privilege escalation, lateral movement to all AWS resources in the account
- Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/security.html

**Synchronous Lambda Chains (Lambda Calling Lambda Directly)**
- Risk Level: HIGH
- Why: Reliability + Cost — Calling a Lambda function synchronously from another Lambda function doubles timeout risk (both timeouts consume concurrency), doubles cost (both functions billed for duration simultaneously), and creates tight coupling. A failure in the downstream function propagates to the upstream caller.
- Instead:
  - For workflows: AWS Step Functions (orchestration)
  - For decoupled async work: SQS → Lambda (downstream function)
  - For fire-and-forget: Async Lambda invocation (`InvocationType: Event`) — but add DLQ
  - For real-time fan-out: EventBridge or SNS
  ```
  # BAD: Lambda A calls Lambda B synchronously
  lambda_client.invoke(FunctionName='B', InvocationType='RequestResponse')
  # GOOD: Lambda A sends message to SQS; Lambda B polls SQS
  sqs_client.send_message(QueueUrl=..., MessageBody=...)
  ```
- Detection: Code review — search for `InvocationType='RequestResponse'` in Lambda code. Architecture diagram review.
- Impact: Cascading failure (upstream timeout on downstream failure), doubled concurrency consumption, doubled cost, tight coupling
- Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/reliability.html

**Missing Timeout Configuration (Relying on 3-second Default)**
- Risk Level: HIGH
- Why: Reliability — The Lambda default timeout of 3 seconds is appropriate for simple functions but catastrophic for functions that call external services, run database queries, or process large events. A too-short timeout causes silent failures that generate retry storms.
- Instead:
  - Set explicit timeouts per function based on P99 measured execution time × 2 safety margin
  - Set downstream SDK call timeouts (HTTP client timeouts) to < Lambda function timeout
  - Alert on Lambda duration approaching timeout threshold (80% of configured timeout)
  ```
  # Recommended timeout strategy:
  # Simple in-memory function: 5–10s
  # DB query function: 30–60s
  # External HTTP call: 30s (with 25s SDK client timeout)
  # Stream processor: 300s (Kinesis/SQS batch processing)
  ```
- Detection:
  ```bash
  aws lambda list-functions --query 'Functions[?Timeout==`3`].[FunctionName,Timeout]' --output table
  # CloudWatch alarm: Lambda/Duration > 80% of configured timeout
  ```
- Impact: Service outage (functions timing out silently), retry storms (async functions retry on timeout), data inconsistency
- Source: https://docs.aws.amazon.com/lambda/latest/dg/configuration-function-common.html

**Lambda in VPC Without Endpoints (Triggering NAT Gateway Costs)**
- Risk Level: MEDIUM
- Why: Cost + Performance — Lambda functions in a VPC route all AWS API calls through a NAT Gateway by default (since Lambda has no public IP). NAT Gateway costs $0.045/GB processed and adds network latency. VPC Endpoints ($0.01/hour + $0.01/GB) are significantly cheaper for high-volume AWS API access.
- Instead:
  - Add VPC Interface Endpoints for every AWS service the Lambda function calls (DynamoDB, S3, Secrets Manager, SQS, etc.)
  - Use S3 Gateway Endpoint (free) for S3 access from VPC
  - Consider: does this function actually need VPC? Lambda can access DynamoDB, S3, SQS, EventBridge natively without VPC
  ```
  # Free: S3 Gateway Endpoint — no NAT needed for S3 from VPC
  # Interface Endpoints to create: com.amazonaws.region.execute-api, dynamodb, secretsmanager, sqs
  ```
- Detection:
  ```bash
  # Identify VPC-attached Lambda functions without corresponding VPC endpoints
  aws lambda list-functions --query 'Functions[?VpcConfig.VpcId!=null].[FunctionName]' --output text
  aws ec2 describe-vpc-endpoints --filters Name=vpc-id,Values=<vpc-id>
  ```
- Impact: Cost overrun (NAT Gateway charges at scale), Performance degradation (NAT Gateway latency)
- Source: https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html

---

## Cloud-Native Design Patterns

**Event-Driven Fan-Out**
- Category: Scalability
- Problem: A single event must trigger multiple independent downstream processing pipelines without coupling the producer to each consumer.
- Solution on AWS:
  SNS topic or EventBridge event bus as the fan-out hub. Multiple SQS queues subscribe to the SNS topic (fan-out pattern). Each SQS queue drives a dedicated Lambda function. Consumers are independently deployable, scalable, and isolatable.
  ```
  Producer → SNS Topic → SQS Queue A → Lambda A (email notification)
                       → SQS Queue B → Lambda B (analytics ingestion)
                       → SQS Queue C → Lambda C (audit log writer)
  ```
- Services Used:
  - Amazon SNS: fan-out hub, push delivery to SQS subscribers
  - Amazon SQS: per-consumer queue (decouples Lambda from SNS, adds DLQ support)
  - AWS Lambda: per-consumer processor (independent scaling, isolated failures)
  - Amazon EventBridge: alternative fan-out hub with content-based routing
- When to Apply: Order placed → notify email + update inventory + generate invoice. User signup → send welcome email + create CRM record + trigger onboarding workflow.
- When NOT to Apply: Single consumer patterns (use SQS directly). When consumers need ordering guarantees (use Kinesis or SQS FIFO). When fan-out count changes frequently (EventBridge is simpler to modify than SNS subscriptions).
- Trade-offs:
  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Decoupling | Producers have zero knowledge of consumers | Consumer addition requires subscription management |
  | Resilience | Consumer failure is isolated — doesn't affect producer or other consumers | DLQ needed per SQS queue |
  | Cost | Pay-per-message — no idle cost | SNS + SQS charges per message per subscriber |
  | Scalability | Each consumer scales independently | SQS FIFO limits throughput if ordering needed |
- Complements: Dead Letter Queue pattern, Idempotent Consumer, Event Sourcing
- Source: https://docs.aws.amazon.com/sns/latest/dg/sns-sqs-as-subscriber.html

**Saga Pattern (Distributed Transactions)**
- Category: Data, Resilience
- Problem: A multi-step business transaction spans multiple Lambda functions and data stores. Any step can fail, requiring compensating transactions to maintain consistency without distributed 2-phase commit.
- Solution on AWS:
  AWS Step Functions Standard Workflow as the saga orchestrator. Each step is a Lambda function. On failure, Step Functions invokes compensating Lambda functions in reverse order. State is maintained in the Step Functions execution context.
  ```
  Step Functions Workflow:
    1. Reserve Inventory (Lambda) → success: proceed / failure: end
    2. Charge Payment (Lambda) → success: proceed / failure: Release Inventory (Lambda)
    3. Create Shipment (Lambda) → success: proceed / failure: Refund Payment + Release Inventory
    4. Notify Customer (Lambda) → success: complete
  Compensating transactions defined in Catch blocks per state.
  ```
- Services Used:
  - AWS Step Functions Standard: saga orchestrator, maintains execution state, retry + compensate logic
  - AWS Lambda: individual transaction steps and compensating actions
  - Amazon DynamoDB: per-service data stores with conditional writes for idempotency
  - Amazon SNS/EventBridge: notify completion or failure to downstream systems
- When to Apply: E-commerce order processing (inventory + payment + shipping), financial transfers (debit + credit), travel booking (flight + hotel + car).
- When NOT to Apply: Single-service operations (use DB transactions). Read-only operations. High-frequency, low-value operations where compensation cost exceeds benefit.
- Trade-offs:
  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Consistency | Eventually consistent across services without 2PC | Temporary inconsistency window during compensation |
  | Visibility | Full execution audit trail in Step Functions console | Step Functions Standard cost ($0.025/1000 transitions) |
  | Complexity | Compensation logic centralized in state machine | State machine definition complexity grows with steps |
  | Resilience | Automatic retries and compensation on failure | Compensation logic must be carefully tested |
- Complements: Idempotent Consumer, Dead Letter Queue, Event Sourcing
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/concepts-saga-pattern.html

**CQRS with Lambda (Command Query Responsibility Segregation)**
- Category: Data, Scalability
- Problem: Read and write workloads have different scaling, latency, and consistency requirements. A single Lambda function handling both creates performance bottlenecks and tight coupling between read and write models.
- Solution on AWS:
  Separate Lambda functions for commands (writes) and queries (reads). Command Lambda writes to DynamoDB (source of truth) and publishes events to EventBridge or DynamoDB Streams. Read-model Lambda consumes events and updates a query-optimized store (ElastiCache, OpenSearch, Aurora read replica).
  ```
  Command Path: API Gateway → Command Lambda → DynamoDB → DynamoDB Streams → Projection Lambda → Read Store
  Query Path:   API Gateway → Query Lambda → Read Store (ElastiCache/OpenSearch)
  ```
- Services Used:
  - AWS Lambda (Command): validates, writes to DynamoDB, publishes events
  - AWS Lambda (Query): reads from read-optimized store
  - AWS Lambda (Projection): consumes DynamoDB Streams to update read models
  - Amazon DynamoDB: write store (source of truth)
  - Amazon ElastiCache/OpenSearch/Aurora: read stores optimized for query patterns
  - Amazon DynamoDB Streams: event source for projection Lambda
- When to Apply: High read:write ratio workloads. Complex read queries on DynamoDB that require secondary indexes on multiple attributes. Reporting/analytics alongside transactional writes.
- When NOT to Apply: Simple CRUD applications with balanced read/write ratios. When eventual consistency in the read model is unacceptable. Small teams without capacity to manage separate read/write infrastructure.
- Trade-offs:
  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Scalability | Read/write scale independently | Multiple Lambda functions and data stores to manage |
  | Performance | Query store optimized for read patterns | Eventual consistency — reads may lag writes |
  | Cost | Right-sized compute per operation type | Additional data store costs (ElastiCache, OpenSearch) |
  | Complexity | Clean separation of concerns | Projection lag monitoring and catchup strategy required |
- Complements: Event Sourcing, DynamoDB Streams, Fan-Out Pattern
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-data-persistence/cqrs-pattern.html

**Claim Check Pattern (Large Message Handling)**
- Category: Communication, Scalability
- Problem: Event-driven architectures have message size limits: SQS max 256 KB, SNS max 256 KB, EventBridge max 256 KB, Lambda async payload max 256 KB. Large payloads (images, documents, large JSON objects) cannot be passed directly between Lambda functions via events.
- Solution on AWS:
  Producer Lambda stores the large payload in S3 and passes only the S3 object reference (the "claim check") in the event message. Consumer Lambda retrieves the payload from S3 using the reference.
  ```
  Producer: PUT large payload → S3 → publish {bucket, key, metadata} → SQS/EventBridge
  Consumer: receive {bucket, key} → GET s3://bucket/key → process full payload
  S3 lifecycle: delete object after processing (or retain for audit)
  ```
- Services Used:
  - Amazon S3: large payload store
  - Amazon SQS / EventBridge: lightweight event/command message with S3 reference
  - AWS Lambda: producer (writes to S3, publishes reference) and consumer (reads from S3)
  - Amazon S3 Event Notifications: alternative — S3 directly triggers Lambda on large object creation
- When to Apply: Any payload exceeding event size limits. Image/video processing pipelines. ETL jobs with large input files. Batch processing with file-based inputs.
- When NOT to Apply: Small payloads under size limits (adds unnecessary S3 round-trip latency). When payload data is sensitive and S3 access control adds unacceptable complexity.
- Trade-offs:
  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Scalability | No message size constraints | Extra S3 GET per consumer invocation adds latency (~5–20ms) |
  | Cost | S3 storage is cheap ($0.023/GB) | Additional S3 API calls per message |
  | Simplicity | Works with all AWS messaging services | Requires S3 lifecycle management to avoid orphaned objects |
- Complements: Fan-Out Pattern, S3 Event Notifications, Lambda Event Source Mapping
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/claim-check.html

**Strangler Fig for Monolith Extraction**
- Category: Migration
- Problem: Incrementally extract functionality from a monolithic application to Lambda functions without a big-bang rewrite.
- Solution on AWS:
  API Gateway as the routing facade in front of the monolith. Route specific URL paths or API methods to Lambda functions as they are extracted. The monolith handles all unextracted routes. Over time, Lambda handles increasing traffic share until the monolith is retired.
  ```
  Phase 1: API Gateway → Monolith (all routes)
  Phase 2: API Gateway → Lambda (POST /orders), → Monolith (all other routes)
  Phase 3: API Gateway → Lambda (all routes), Monolith retired
  ```
- Services Used:
  - Amazon API Gateway: routing facade, path-based routing to Lambda vs. monolith (HTTP integration)
  - AWS Lambda: extracted microservices/functions
  - AWS ALB: alternative facade for TCP/HTTP routing
  - Amazon RDS Proxy: shared DB connection pool during transition when Lambda and monolith share DB
- When to Apply: Legacy monoliths on EC2/ECS that need incremental modernization. Teams unwilling or unable to do a full rewrite.
- When NOT to Apply: Monoliths with tightly coupled shared state that cannot be cleanly extracted. Monoliths where the cost of maintaining two codebases exceeds the refactoring cost.
- Trade-offs:
  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Risk | Incremental — can stop at any point | Dual maintenance burden during migration |
  | Speed | Can deploy extracted functions independently | Routing logic in API Gateway grows in complexity |
  | Testing | A/B comparison between old and new implementations | Shared database creates coupling during transition |
- Complements: CQRS, Event-Driven Architecture, Database-per-Service
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-data-persistence/strangler-fig.html

---

## Security Architecture

**Lambda Execution Role Governance**
- Security Domain: Identity & Access Management
- AWS Services:
  - AWS IAM: per-function execution roles with least-privilege policies
  - AWS IAM Access Analyzer: identifies overly permissive Lambda execution role policies
  - AWS Config: `lambda-function-public-access-prohibited` and custom policy checks
  - AWS Security Hub: Lambda security controls (Lambda.1 through Lambda.5)
  - AWS CloudTrail: audits all `lambda:InvokeFunction` and `iam:PassRole` API calls
- Architecture:
  Each Lambda function has a dedicated IAM role. Trust policy: `lambda.amazonaws.com` only. Permissions: explicit service actions on explicit resource ARNs. No `iam:PassRole` to Lambda unless strictly controlled. Lambda execution role cannot be assumed by humans. Periodic review via Access Analyzer.
  ```
  Trust Policy: { "Principal": { "Service": "lambda.amazonaws.com" } }
  Permission Boundary: optional — cap maximum permissions on all Lambda roles
  SCP (if multi-account): deny lambda:CreateFunction without specific tag
  ```
- Configuration Essentials:
  - `lambda:ListFunctions` — allow only to CI/CD role and specific admin roles, not developers
  - `lambda:GetFunctionConfiguration` — restrict to prevent environment variable exposure
  - Enable `lambda:PutFunctionConcurrency` restriction — prevents concurrency manipulation
- Verification:
  ```bash
  # AWS IAM Access Analyzer — review all Lambda execution role findings
  aws accessanalyzer list-findings --analyzer-arn <arn> --filter '{"resourceType": {"contains": ["AWS::Lambda"]}}'
  # Security Hub check
  aws securityhub get-findings --filters '{"GeneratorId": [{"Value": "arn:aws:securityhub:::ruleset/cis-aws-foundations-benchmark/v/1.4.0/rule/Lambda.1", "Comparison": "PREFIX"}]}'
  ```
- Compliance Alignment: SOC2 CC6.1, CIS AWS Foundations Benchmark (Lambda controls), PCI DSS 7.1 (least privilege)
- Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/security.html

**Secrets and Configuration Management**
- Security Domain: Data Security
- AWS Services:
  - AWS Secrets Manager: secrets (DB credentials, API keys, OAuth tokens) — automatic rotation
  - AWS Systems Manager Parameter Store (SecureString): configuration values and non-rotating secrets
  - AWS Parameters and Secrets Lambda Extension: caches secrets locally in execution environment (reduces latency + API calls)
  - AWS KMS: CMK for encrypting environment variables and Secrets Manager secrets
  - AWS IAM: `secretsmanager:GetSecretValue` on specific secret ARN only
- Architecture:
  Lambda function has no secrets in environment variables or deployment package. At init time, function fetches secrets via the Lambda Extension (HTTP call to localhost:2773). Extension caches with configurable TTL (default 300s for Secrets Manager). KMS CMK encrypts secrets at rest. CloudTrail logs every `Decrypt` operation.
  ```
  # Fetch secret via Lambda Extension (in Init code, cached):
  GET http://localhost:2773/secretsmanager/get?secretId=prod/myapp/db-credentials
  # Response cached for 300s — subsequent invocations in same environment hit local cache
  ```
- Configuration Essentials:
  - Secret rotation: enable automatic rotation for DB credentials (built-in Lambda rotation functions)
  - KMS CMK: use customer-managed key, not AWS-managed — enables key policy control and CloudTrail audit
  - Resource-based policy on secret: restrict to specific Lambda execution role ARNs
- Verification:
  ```bash
  # Verify no plaintext secrets in environment variables
  aws lambda get-function-configuration --function-name <name> --query 'Environment.Variables'
  # Check Secrets Manager rotation status
  aws secretsmanager describe-secret --secret-id <name> --query 'RotationEnabled'
  ```
- Compliance Alignment: GDPR Art. 32 (encryption), PCI DSS 3.4 (key management), HIPAA §164.312(e)(1)
- Source: https://docs.aws.amazon.com/secretsmanager/latest/userguide/lambda-functions.html

**Lambda Network Security (VPC Architecture)**
- Security Domain: Network Security
- AWS Services:
  - Amazon VPC: private subnets for Lambda in VPC deployments
  - VPC Security Groups: Lambda security group with egress-only rules
  - VPC Interface Endpoints: private connectivity to AWS services (no internet egress required)
  - AWS Network Firewall / AWS WAF: for API Gateway + Lambda exposed to internet
  - AWS ALB with WAF: WAF web ACL for L7 protection on Lambda-backed HTTP endpoints
- Architecture:
  Lambda functions in VPC are placed in private subnets (no direct internet access). Security group: no inbound rules; egress only to required ports/destinations. VPC Endpoints for all AWS service calls (DynamoDB, S3, Secrets Manager, SQS). API Gateway with WAF web ACL for internet-facing Lambda APIs.
  ```
  Internet → WAF → API Gateway → Lambda (Private Subnet)
                                      ↓ VPC Interface Endpoints
                                   DynamoDB / Secrets Manager / S3
  No NAT Gateway required with full VPC Endpoint coverage.
  ```
- Configuration Essentials:
  - Lambda security group: inbound NONE, outbound TCP 443 to VPC CIDR and endpoint security groups
  - VPC Endpoint policy: restrict to specific Lambda execution role ARNs
  - API Gateway: associate WAF web ACL with stage — minimum Core Rule Set (CRS)
  - Enable VPC Flow Logs for all Lambda VPC subnets
- Verification:
  ```bash
  # Check Lambda VPC configuration
  aws lambda get-function-configuration --function-name <name> --query 'VpcConfig'
  # Verify WAF association with API Gateway
  aws wafv2 get-web-acl-for-resource --resource-arn <api-gateway-stage-arn>
  ```
- Compliance Alignment: PCI DSS 1.3 (network segmentation), SOC2 CC6.6, CIS AWS Foundations
- Source: https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html

**Function Code Security**
- Security Domain: Supply Chain Security
- AWS Services:
  - AWS Lambda (Code Signing): ensures deployment packages are signed by a trusted publisher
  - Amazon ECR (Image Signing): for container image-based Lambda functions
  - Amazon Inspector: scans Lambda function code and container images for CVEs
  - AWS CodeGuru Security: SAST analysis of Lambda function code in CI/CD pipelines
  - AWS Config Rule: `lambda-function-settings-check`
- Architecture:
  Lambda deployment pipeline enforces code signing (AWS Signer) before deployment. Amazon Inspector continuously scans deployed Lambda functions for CVEs in dependencies. Runtime is pinned to a specific managed runtime version (not `provided.al2023` without explicit version). Dependencies are pinned to exact versions (no range operators in requirements.txt/package.json).
  ```
  CI/CD Pipeline:
  Build → CodeGuru Security Scan → Sign with AWS Signer → Deploy to Lambda
  Post-deploy: Inspector scan → Security Hub finding → alert if CRITICAL CVE
  ```
- Configuration Essentials:
  - Code signing: `AWSSignerSigningProfileVersionArn` in Lambda function configuration
  - Inspector: enable `Lambda standard scanning` in Amazon Inspector settings
  - Runtime: set `UpdateRuntimeOn: Auto` for managed runtimes or explicit version pinning
- Verification:
  ```bash
  aws lambda get-code-signing-config --code-signing-config-arn <arn>
  aws inspector2 list-findings --filter-criteria '{"lambdaFunctionName": [{"comparison": "EQUALS", "value": "<name>"}]}'
  ```
- Compliance Alignment: NIST SSDF (software supply chain), SOC2 CC7.1
- Source: https://docs.aws.amazon.com/lambda/latest/dg/configuration-codesigning.html

---

## Operational Patterns

**Lambda Observability Stack**
- Operational Domain: Observability
- AWS Services:
  - Amazon CloudWatch (Metrics): Lambda built-in metrics — Invocations, Errors, Duration, Throttles, ConcurrentExecutions, IteratorAge
  - Amazon CloudWatch (Logs + Insights): structured JSON logs, cross-function log queries
  - AWS Lambda Advanced Logging Controls: JSON log format, per-function log level
  - AWS X-Ray / ADOT Lambda Layer: distributed traces across Lambda chains
  - Amazon CloudWatch Synthetics: canary scripts for end-to-end API health
  - AWS Lambda Powertools: structured logging, tracing, custom metrics (EMF)
- Architecture:
  Every Lambda function emits: (1) structured JSON logs with correlation ID and business context, (2) X-Ray trace segments for all downstream calls, (3) custom business metrics via Embedded Metric Format (EMF) — zero additional CloudWatch PutMetricData API calls, metrics embedded in log lines. CloudWatch Dashboard aggregates per-function and per-service health. Alarms on Errors > 0 and Throttles > 0 and IteratorAge > SLA threshold.
  ```
  Minimum required CloudWatch alarms per function:
  - Errors: > 0 for 1 minute → SNS → PagerDuty
  - Throttles: > 0 for 5 minutes → SNS → Slack
  - Duration: > 80% of configured timeout → SNS → Slack
  - IteratorAge (Kinesis/DynamoDB Streams): > SLA_MS → SNS → PagerDuty
  ```
- Cost Profile: Medium. CloudWatch Logs ingestion at $0.50/GB. X-Ray traces at $5/million traces. EMF metrics free within standard CloudWatch metrics pricing.
- Automation:
  - Automated: alarm creation (IaC), log retention policy (IaC — never use default/never-expire)
  - Manual: alarm threshold tuning after baselining production traffic, DLQ investigation
- Source: https://docs.aws.amazon.com/lambda/latest/operatorguide/monitoring-observability.html

**Disaster Recovery for Serverless**
- Operational Domain: DR
- RTO/RPO:
  | DR Pattern | RTO | RPO | Notes |
  |------------|-----|-----|-------|
  | Backup & Restore | Hours | Hours | Lambda code in S3/ECR; DynamoDB PITR restore |
  | Pilot Light | Minutes | Minutes | Lambda auto-deploys in second region; DynamoDB Global Tables |
  | Warm Standby | Minutes | Seconds | Active second region with traffic; Route 53 health check failover |
  | Multi-Region Active-Active | Seconds | Near-zero | Route 53 latency routing; DynamoDB Global Tables; EventBridge global endpoints |
- AWS Services:
  - AWS Lambda: regional service — auto-available in failover region once code deployed
  - Amazon DynamoDB Global Tables: active-active multi-region replication
  - Amazon EventBridge Global Endpoints: multi-region event bus failover
  - AWS Route 53: health check-based failover routing
  - AWS SAM / CDK: deploy identical Lambda stack to secondary region
  - Amazon S3 Cross-Region Replication: Lambda deployment artifacts in secondary region
- Architecture:
  Lambda itself has no DR complexity — code is stateless. DR challenge is state (DynamoDB, RDS, S3). For active-passive DR: DynamoDB Global Tables replication to secondary region + Route 53 failover + pre-deployed Lambda stack (warm standby). For active-active: EventBridge Global Endpoints + DynamoDB Global Tables + Route 53 latency routing.
- Cost Profile: Medium–High. DynamoDB Global Tables adds ~2× write cost. Multi-region Lambda Provisioned Concurrency doubles warm compute cost.
- Automation: Route 53 health check failover is fully automated. DynamoDB Global Tables replication is automatic. Lambda re-deployment to failover region should be IaC-automated in CI/CD pipeline.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/disaster-recovery-dr-objectives.html

**Lambda FinOps / Cost Optimization**
- Operational Domain: FinOps
- AWS Services:
  - AWS Lambda Power Tuning: Step Functions state machine for memory optimization
  - Amazon CloudWatch: cost attribution via function-level dimension
  - AWS Cost Explorer: Lambda cost breakdown by function name (requires cost allocation tags)
  - AWS Compute Optimizer: Lambda function right-sizing recommendations
  - AWS Budgets: Lambda cost alerts
- Architecture:
  Tagging strategy: all Lambda functions tagged with `Environment`, `Service`, `Team`, `CostCenter`. Cost Explorer filter on `aws:lambda:FunctionName` resource tag. Lambda Power Tuning run on all CPU-intensive functions pre-production. AWS Compute Optimizer reviews recommendations monthly. SQS batching maximized (batch size 10 for SQS, batching window 20s) to reduce invocation count. Kinesis Enhanced Fan-Out only when needed (adds cost).
  ```
  Cost levers (highest impact first):
  1. Memory tuning (Lambda Power Tuning) — can reduce cost 30–60%
  2. Batch size maximization (SQS/Kinesis) — reduces invocation count
  3. Init code optimization (reduce cold start duration — billed)
  4. Provisioned Concurrency right-sizing (scope to peak hours only via auto-scaling)
  5. Avoid VPC + NAT Gateway (replace with VPC Endpoints)
  ```
- Cost Profile: Lambda pricing: $0.0000166667/GB-second + $0.20/million requests (arm64: ~20% cheaper). Graviton2 (arm64) runtime offers cost reduction — use `Architectures: [arm64]` in function config.
- Automation:
  - Automated: Lambda Power Tuning in CI/CD pipeline, budget alerts via AWS Budgets
  - Manual: Provisioned Concurrency schedule review, architecture decisions for cost reduction
- Source: https://docs.aws.amazon.com/lambda/latest/operatorguide/cost-optimize.html

**Blue-Green / Canary Deployment for Lambda**
- Operational Domain: Change Management
- RTO: Seconds (alias traffic shift rollback). RPO: Zero (no state change on Lambda update)
- AWS Services:
  - AWS Lambda (Versions and Aliases): version immutability, alias traffic weighting
  - AWS CodeDeploy (Lambda deployment group): canary and linear deployment strategies with automatic rollback
  - Amazon CloudWatch Alarms: trigger automatic rollback on error rate increase
  - AWS SAM: `AutoPublishAlias` and `DeploymentPreference` configuration
- Architecture:
  Every Lambda function update publishes a new Version. Alias `production` traffic-shifts from old version to new version using CodeDeploy. Pre-traffic and post-traffic hook Lambda functions run integration tests. CloudWatch alarm on `Errors` or `Duration` triggers automatic rollback to previous version. Canary: 10% for 10 minutes before 100% shift.
  ```yaml
  # SAM template snippet:
  DeploymentPreference:
    Type: Canary10Percent10Minutes
    Alarms:
      - !Ref FunctionErrorAlarm
    Hooks:
      PreTraffic: !Ref PreTrafficHookFunction
      PostTraffic: !Ref PostTrafficHookFunction
  ```
- Cost Profile: Low. CodeDeploy for Lambda is free. Minor cost for pre/post-traffic hook Lambda invocations.
- Automation: Fully automated via SAM + CodeDeploy — rollback triggered automatically on alarm breach.
- Source: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/automating-updates-to-serverless-apps.html

---

## Reference Architectures

**Serverless REST API (Three-Tier)**
- Context: Standard CRUD API backend for web/mobile applications
- AWS Source: https://serverlessland.com/patterns/apigw-lambda-dynamodb
- Services Composition:
  | Layer | Service | Purpose | Alternative |
  |-------|---------|---------|-------------|
  | Edge / WAF | Amazon CloudFront + AWS WAF | DDoS, bot protection, caching | API Gateway WAF directly |
  | API | Amazon API Gateway HTTP API | Routing, auth (JWT), throttling, CORS | API Gateway REST API (more features) |
  | Auth | Amazon Cognito User Pool / Lambda Authorizer | JWT validation, custom auth | API Gateway IAM auth |
  | Compute | AWS Lambda (arm64, Python 3.12 / Node.js 22) | Business logic per endpoint | Lambda container image |
  | Data | Amazon DynamoDB (on-demand) | Primary data store, single-table design | RDS Aurora Serverless v2 |
  | Secrets | AWS Secrets Manager + Lambda Extension | DB credentials, API keys | SSM Parameter Store |
  | Observability | CloudWatch + X-Ray + Lambda Powertools | Logs, traces, metrics | Datadog, New Relic via Extension |

- Architecture Diagram Description:
  Client → CloudFront (WAF web ACL) → API Gateway HTTP API (JWT authorizer → Cognito) → Lambda function (one per resource group, arm64) → DynamoDB (single-table design, on-demand). Lambda uses Powertools for structured logging, X-Ray tracing, and EMF custom metrics. Secrets fetched from Secrets Manager via Lambda Extension at init time. CloudWatch alarms on Errors, Throttles, Duration. CodeDeploy canary deployment with automatic rollback.

- Key Decisions:
  - Single-table vs multi-table DynamoDB: single-table for access pattern-optimized queries; multi-table for teams unfamiliar with single-table patterns
  - One Lambda per resource vs one Lambda for all routes: prefer one Lambda per resource group (Order Lambda, User Lambda) for independent scaling and deployment
  - HTTP API vs REST API: HTTP API unless request validation, caching, or usage plans are required

- Scaling Path:
  - 0–10K RPM: DynamoDB on-demand, Lambda default concurrency, no provisioned concurrency
  - 10K–100K RPM: DynamoDB provisioned + auto-scaling, reserved concurrency per function, CloudFront caching
  - 100K+ RPM: DynamoDB Global Tables for multi-region, API Gateway regional limit increase, ElastiCache read-through cache for hot items

- Cost Baseline: Low. Under 1M requests/month: Lambda ~$0.20, API Gateway ~$1.00, DynamoDB on-demand ~$1.25/GB. Negligible for <100K RPM.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/event-driven-architectures.html

**Serverless Event Processing Pipeline**
- Context: High-throughput event ingestion and processing (IoT, clickstream, audit logs, order events)
- AWS Source: https://serverlessland.com/patterns/kinesis-lambda
- Services Composition:
  | Layer | Service | Purpose | Alternative |
  |-------|---------|---------|-------------|
  | Ingestion | Amazon Kinesis Data Streams | Ordered, replayable event stream | Amazon MSK (Kafka), SQS |
  | Consumer | AWS Lambda (Event Source Mapping) | Stream processor, batch-aware | Kinesis Data Firehose (no code) |
  | Processing | AWS Lambda | Transform, enrich, validate events | AWS Glue (for ETL) |
  | Storage — Hot | Amazon DynamoDB | Real-time aggregations, entity state | ElastiCache |
  | Storage — Cold | Amazon S3 via Kinesis Data Firehose | Raw event archive, Athena queryable | S3 direct from Lambda |
  | Orchestration | AWS Step Functions Express | Multi-step enrichment workflows | Lambda chaining via SQS |
  | Observability | CloudWatch + X-Ray + IteratorAge alarm | Stream lag monitoring | Amazon Managed Service for Prometheus |

- Architecture Diagram Description:
  Producers → Kinesis Data Streams (N shards) → Lambda (Event Source Mapping, parallelization factor 10, bisect-on-error, on-failure SQS DLQ) → DynamoDB (real-time state) + Kinesis Data Firehose (S3 archive). IteratorAge CloudWatch alarm triggers auto-scaling on Kinesis shard count (Application Auto Scaling). Step Functions Express for complex multi-step processing.

- Key Decisions:
  - Shard count: start with estimated_peak_records_per_second / 1000 (Kinesis limit per shard)
  - Parallelization factor: 1–10 concurrent Lambda invocations per shard — increase for CPU-bound processing
  - Batch size: 100–10,000 records — larger batches = fewer invocations = lower cost

- Scaling Path:
  - <1K events/sec: SQS → Lambda (simpler, lower cost)
  - 1K–100K events/sec: Kinesis Data Streams with auto-scaling shards
  - 100K+ events/sec: Kinesis Enhanced Fan-Out per consumer + parallelization factor 10

- Cost Baseline: Medium. Kinesis: $0.015/shard-hour ($11/shard/month). Lambda: invocation + duration. DynamoDB: on-demand for variable load. S3: $0.023/GB storage.
- Source: https://docs.aws.amazon.com/lambda/latest/dg/with-kinesis.html

**Serverless Workflow Orchestration**
- Context: Multi-step business processes with compensation logic, human approval, and audit trail
- AWS Source: https://docs.aws.amazon.com/step-functions/latest/dg/tutorials.html
- Services Composition:
  | Layer | Service | Purpose | Alternative |
  |-------|---------|---------|-------------|
  | Trigger | API Gateway / EventBridge | Workflow initiation | Direct SDK StartExecution |
  | Orchestrator | AWS Step Functions Standard | State machine, retry/compensate | Step Functions Express (no audit trail) |
  | Workers | AWS Lambda | Individual workflow steps | ECS Fargate (long-running tasks) |
  | Human Approval | Step Functions WaitForTaskToken + SNS | Pause for human decision | SES + approval Lambda |
  | State Store | AWS Step Functions (built-in) | Workflow execution state | DynamoDB (if external tracking needed) |
  | Notifications | Amazon SNS / EventBridge | Workflow completion events | SES, Slack via Lambda |
  | Observability | Step Functions X-Ray, Execution History | Visual debugging, audit trail | CloudWatch Logs |

- Architecture Diagram Description:
  API Gateway → Lambda (validates input) → Step Functions StartExecution → State Machine: (1) Validate → (2) Reserve → (3) Charge [WaitForTaskToken human approval if > $10K] → (4) Fulfill → (5) Notify. Each step is a Lambda function with retry configuration (3 retries, exponential backoff). Catch blocks invoke compensating Lambda functions. Final state published to EventBridge.

- Key Decisions:
  - Standard vs Express: Standard for business workflows needing audit trail (max 1 year, $0.025/1000 transitions). Express for high-frequency internal workflows (max 5 min, $1/million transitions).
  - Lambda vs Activity: use Lambda integration (sync); reserve Activities for on-premises workers
  - Map state vs parallel: Map for variable-size parallel processing; Parallel for fixed branches

- Scaling Path:
  - Low volume (<100/day): Standard Workflows, no cost concern
  - Medium volume (1K–100K/day): evaluate Standard vs Express based on audit requirements
  - High volume (>100K/day): Express Workflows + async patterns

- Cost Baseline: Medium. Step Functions Standard: $0.025/1000 state transitions. 10-step workflow at 1000 executions/day = $0.25/day.
- Source: https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html

---

## Provider Differentiators

```
Differentiator: Lambda SnapStart
Category: Compute
Unique Value: Pre-initializes execution environments when a function version is published and restores from a memory snapshot on cold starts — delivering near-zero Init phase latency without idle compute cost. Supported on Java 11+, Python 3.12+, Node.js 20+ as of 2024.
Architecture Impact: Eliminates the Java cold start penalty (previously 1–5s) without Provisioned Concurrency. Changes the cold start mitigation decision tree: SnapStart is the first option for supported runtimes; Provisioned Concurrency is reserved for strict P99 SLAs requiring zero restore latency.
When to Leverage: Synchronous API backends on Java/Python/Node.js where cold starts impact user experience. Replaces Provisioned Concurrency for most use cases.
Caveat: Init code must be deterministic (no timestamps, no random seeds in globals). Restore latency ~100ms (not zero). Requires publishing function versions (not $LATEST). Not available for container image-based functions.
Source: https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html

Differentiator: Lambda Response Streaming
Category: Compute
Unique Value: Lambda function can progressively stream response bytes to the client via Function URL or API Gateway (HTTP API) before the handler returns — enabling real-time output for LLM inference, large file generation, and long-running operations. No other provider offers native function-level response streaming with this integration depth.
Architecture Impact: Enables serverless LLM inference endpoints without the 29-second API Gateway integration timeout constraint (streaming bypasses the buffer). Changes the architecture for AI/ML inference APIs: Lambda + Function URL with streaming replaces SageMaker or EC2-hosted inference for many use cases.
When to Leverage: LLM token streaming (Bedrock → Lambda → client). Large file generation (PDF, Excel). Progressive data export APIs. Long-running synchronous operations where partial results are valuable.
Caveat: Function URL or API Gateway HTTP API only (not REST API). Maximum response payload: 20 MB for buffered, unlimited for streaming. Node.js and Python runtimes only for streaming SDK. Adds latency to Time-To-First-Byte for small responses.
Source: https://docs.aws.amazon.com/lambda/latest/dg/configuration-response-streaming.html

Differentiator: Lambda Extensions API
Category: Compute
Unique Value: Allows third-party agents and AWS services to run as sidecar processes within the Lambda execution environment — enabling deep integration of APM, security scanning, secrets caching, and configuration management without modifying function code.
Architecture Impact: Standardizes the integration pattern for observability and security tooling. Secrets Manager and Parameter Store caching via the official Lambda Extension eliminates per-invocation API calls (reduces latency and cost). APM vendors (Datadog, Dynatrace, New Relic) provide certified Lambda Layers with Extensions — no code changes required.
When to Leverage: Integrating enterprise APM tools without instrumenting function code. Caching secrets and configuration (AWS Parameters and Secrets Lambda Extension). Custom security controls (RASP agents).
Caveat: External extensions run as separate processes — they consume CPU and memory from the function's allocation. Poorly written extensions increase cold start time. Always measure extension overhead with Lambda Power Tuning.
Source: https://docs.aws.amazon.com/lambda/latest/dg/lambda-extensions.html

Differentiator: EventBridge Pipes + Lambda
Category: Data
Unique Value: EventBridge Pipes provides a fully managed, point-to-point integration between event sources (SQS, DynamoDB Streams, Kinesis, MSK, MQ) and targets (Lambda, Step Functions, API Gateway, EventBridge Bus) with built-in filtering, enrichment (Lambda or API Gateway), and transformation (JSONata/input transformer) — without writing polling code.
Architecture Impact: Replaces the pattern of custom Lambda functions whose sole purpose is to filter events from a stream and forward qualifying events to another Lambda. Reduces Lambda function count, eliminates "glue code" functions, and provides a no-code/low-code alternative for event routing.
When to Leverage: Filtering DynamoDB Streams to only process INSERT events. Enriching SQS messages with metadata from an external API before processing. Routing Kinesis events to different Lambda functions based on event content.
Caveat: EventBridge Pipes supports 1:1 routing only (one source to one target). For fan-out, use EventBridge Bus as the Pipe target, then route to multiple consumers via rules. Enrichment adds latency (~50–100ms per Pipe invocation).
Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-pipes.html

Differentiator: AWS Graviton (arm64 Lambda)
Category: Compute
Unique Value: Lambda supports arm64 (Graviton2) architecture with ~20% better price-performance vs x86_64 for the same memory configuration. Graviton2 provides significantly better performance-per-dollar for compute-intensive workloads.
Architecture Impact: arm64 Lambda is a drop-in replacement for most Python, Node.js, and Java functions with no code changes. Reduces Lambda cost by ~20% for all invocations. Should be the default architecture for new Lambda functions.
When to Leverage: All new Lambda functions. Especially impactful for CPU-intensive functions (image processing, ML inference, data transformation).
Caveat: arm64 binaries required for native dependencies (e.g., numpy, pandas, cryptographic libraries). Custom runtimes and container images must use arm64 base images. Verify Lambda Layer compatibility with arm64 before switching.
Source: https://docs.aws.amazon.com/lambda/latest/dg/foundation-arch.html

Differentiator: AWS Lambda Powertools
Category: Operational
Unique Value: AWS-maintained open-source library (Python, TypeScript, Java, .NET) providing production-grade implementations of: structured logging, distributed tracing (X-Ray), custom metrics (EMF), idempotency (DynamoDB-backed), feature flags (AppConfig), batch processing, parameters (SSM/Secrets Manager cache), streaming, and event utilities. Reduces boilerplate code by 60–80% for production-grade Lambda functions.
Architecture Impact: Standardizes the serverless operational baseline across teams. Idempotency utility removes the need to hand-roll DynamoDB idempotency tables. Logger propagates correlation IDs automatically. Tracer instruments all boto3/AWS SDK calls as X-Ray subsegments automatically.
When to Leverage: Every new Lambda function project. Particularly valuable for idempotency, structured logging, and tracing with minimal code overhead.
Caveat: Adds ~15–40 MB to Python/TypeScript deployment packages (mitigate with Lambda Layers). Not applicable for non-AWS serverless platforms.
Source: https://docs.powertools.aws.dev/lambda/
```

---

## Scenario Coverage

**Standard Case**: CRUD REST API backend for a web application
- Approach:
  - API Gateway HTTP API → Lambda (arm64, Python 3.12 with SnapStart, Powertools) → DynamoDB (on-demand)
  - Cognito User Pool JWT authorizer on API Gateway
  - Secrets Manager + Lambda Extension for DB credentials
  - CloudWatch structured JSON logs + X-Ray tracing
  - SAM/CDK deployment with CodeDeploy canary (10% for 5 minutes, auto-rollback on alarm)
  - Reserved concurrency on critical write path functions
  - Per-function execution roles with DynamoDB table-level permissions

- Key Decisions:
  - Single-table vs multi-table DynamoDB (access pattern complexity)
  - HTTP API vs REST API (caching requirements)
  - SnapStart vs Provisioned Concurrency (P99 SLA strictness)

**Edge Case**: 100K+ concurrent users during a flash sale (traffic spike 100× baseline)
- Approach:
  - Pre-scale Provisioned Concurrency using Application Auto Scaling scheduled scaling (start 30 min before event)
  - DynamoDB Global Tables with provisioned WCU + auto-scaling for peak write throughput
  - SQS-buffered checkout (immediate 202 Accepted response, async checkout processing)
  - CloudFront caching for product catalog reads (Lambda not involved)
  - Account concurrency limit increase pre-approved with AWS Support
  - SQS FIFO with deduplication for exactly-once checkout processing
  - Step Functions Express for checkout state machine (high-frequency, no audit trail required)

**Anti-Pattern Case**: Developer proposes sharing a single Lambda execution role (LambdaFullAccessRole with `*` permissions) across all functions to "simplify IAM management"
- Clarification:
  Ask: "What is the blast radius if the most exposed function (public-facing API) is exploited? With a shared wildcard role, an attacker who exploits one function gains access to all AWS resources the shared role covers."
  Refuse and propose: Per-function execution roles generated automatically by SAM/CDK (`AutoCreateRoles: true`). Use IAM Permission Boundaries to cap maximum permissions on all Lambda roles. Implement AWS Config rule `iam-policy-no-statements-with-admin-access` to detect violations in CI/CD pipeline.

---

## Service Equivalence Map (Serverless Compute)

| Category | AWS | Google Cloud | Azure | Oracle Cloud (OCI) |
|----------|-----|-------------|-------|--------------------|
| **FaaS** | Lambda | Cloud Functions (Gen 2) | Azure Functions | OCI Functions |
| **Serverless Containers** | Lambda Container Image | Cloud Run | Container Apps | — |
| **Workflow Orchestration** | Step Functions | Cloud Workflows | Logic Apps / Durable Functions | OCI Process Automation |
| **API Gateway** | API Gateway HTTP/REST | API Gateway / Apigee | API Management | OCI API Gateway |
| **Event Bus** | EventBridge | Eventarc | Event Grid | OCI Events |
| **Queue** | SQS | Cloud Tasks | Service Bus Queues | OCI Queue |
| **Pub/Sub** | SNS | Pub/Sub | Service Bus Topics | OCI Streaming |
| **Streaming** | Kinesis | Dataflow | Event Hubs | OCI Streaming |
| **Scheduled Tasks** | EventBridge Scheduler | Cloud Scheduler | Azure Logic Apps / Timer | OCI Scheduling |
| **Edge Functions** | Lambda@Edge / CloudFront Functions | Cloud Functions (global) | Azure Functions + Front Door | — |
| **IaC for Serverless** | AWS SAM / CDK | Cloud Deploy | Bicep / ARM | OCI Resource Manager |

> **⚠️ Important**: Lambda's invocation models (synchronous, asynchronous, poll-based), SnapStart, response streaming, Extensions API, and Provisioned Concurrency have no direct feature-parity equivalents across providers. Architecture patterns valid on Lambda may require significant redesign on GCP Cloud Functions or Azure Functions.
