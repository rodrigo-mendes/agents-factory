# AWS Serverless Architecture — Lambda & Event-Driven Patterns
**Version**: AWS Serverless Application Lens — Well-Architected Framework 2025
**Research Date**: 2026-07-31
**Target Edition**: AWS Serverless Application Lens 2025
**Architecture Context**: Real-time / event-driven platform
**Audience**: Cloud Architects and Tech Leads
**Status**: Research complete — ready for skill authoring

---

> ⚠️ **CRITICAL SOURCE-CURRENCY CORRECTION (read before using this document).**
> The `TARGET_EDITION` label above ("AWS Serverless Application Lens — Well-Architected Framework **2025**") was carried in from the research request. **Verification against the official source shows no such 2025 edition exists.** The AWS **Serverless Applications Lens** whitepaper has a single **Publication date: July 14, 2022** (confirmed on the official page's `welcome.html` header and the "Document revisions" page, accessed 2026-07-31). Source: [Serverless Applications Lens — Welcome](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/welcome.html).
>
> **Anti-hallucination ruling (Version Absolutism):** This document does **not** assert a 2025 Lens. The effective edition used here is:
> **AWS Serverless Applications Lens (published 2022-07-14 — only published version) — treated as *supporting* framework guidance per the source-hierarchy rule for sources > 12 months old — cross-checked, fact-by-fact, against the continuously-updated service Developer Guides** (AWS Lambda, Step Functions, EventBridge) and the official **SQS/SNS/EventBridge Decision Guide (last updated 2024-07-31)**, all accessed **2026-07-31**.
> Every pillar/design-principle claim sourced *solely* from the 2022 Lens is flagged inline with `⚠️ Source dated 2022-07; verify currency.` Every service-level claim is anchored to a continuously-updated Developer Guide.

---

## Table of Contents

1. [Framework Pillars — Serverless Applications Lens](#1-framework-pillars--serverless-applications-lens)
2. [Always-Do Patterns (mandatory)](#2-always-do-patterns-mandatory)
3. [Ask-First Decisions (context-dependent)](#3-ask-first-decisions-context-dependent)
4. [Never-Do Anti-patterns](#4-never-do-anti-patterns)
5. [Service Equivalence Map](#5-service-equivalence-map)
6. [Source Bibliography](#6-source-bibliography)
7. [Anti-Hallucination Checklist (self-verification)](#7-anti-hallucination-checklist-self-verification)

---

## 1. Framework Pillars — Serverless Applications Lens

**Edition in force:** AWS Serverless Applications Lens (2022-07-14) as *supporting* guidance, cross-checked against the AWS Well-Architected Framework (continuously updated) and service Developer Guides (accessed 2026-07-31).

The AWS Well-Architected Framework defines **six pillars**. The Serverless Applications Lens narrows each pillar to serverless-specific best practices. Pillar list and design principles below are taken from the Serverless Applications Lens.

> ⚠️ Source dated 2022-07; verify currency. The pillar *framing* is stable, but always re-validate serverless-specific best practices against the current service Developer Guides. Source: [Serverless Applications Lens — The pillars](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/the-pillars-of-the-well-architected-framework.html) (accessed 2026-07-31).

| Pillar | Serverless framing (event-driven platform) | Top real-time / event-driven concern |
|---|---|---|
| **Operational Excellence** | Structured logs, EMF metrics, X-Ray tracing across async hops; versions/aliases for safe deploy | End-to-end trace correlation across event boundaries |
| **Security** | Least-privilege execution role *per function*, per-function isolation, secrets outside code, KMS-encrypted env vars | Blast-radius isolation per event consumer |
| **Reliability** | Idempotency, retries with backoff, DLQ / on-failure destinations, partial batch response, quota awareness | At-least-once delivery + guaranteed duplicates |
| **Performance Efficiency** | Right-sized memory (= CPU), cold-start strategy (SnapStart / Provisioned Concurrency), arm64, connection reuse | Cold-start tail latency on latency-sensitive paths |
| **Cost Optimization** | Pay-per-use; memory/duration tuning; arm64; avoid idle Provisioned Concurrency | GB-seconds + per-event cost at high event volume |
| **Sustainability** | Right-sizing, arm64 (Graviton) efficiency, eliminate idle capacity | Match compute to bursty event demand |

### Serverless General Design Principles (from the Lens)

Source: [Serverless Applications Lens — General design principles](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/general-design-principles.html) (⚠️ dated 2022-07; verify currency; accessed 2026-07-31):

1. **Speedy, simple, singular** — functions are concise, short, single-purpose; prefer faster initializations.
2. **Think concurrent requests, not total requests** — evaluate design trade-offs on concurrency, not aggregate request count.
3. **Share nothing** — the runtime environment and infrastructure are short-lived; local `/tmp` is not guaranteed to persist; use durable stores for state.
4. **Assume no hardware affinity** — underlying infrastructure may change; write hardware-agnostic code.
5. **Orchestrate your application with state machines, not functions** — chaining Lambdas in code creates a tightly-coupled monolith; use AWS Step Functions.
6. **Use events to trigger transactions** — asynchronous, consumer-agnostic, just-in-time processing.
7. **Design for failures and duplicates** — operations must be idempotent; include retries for downstream calls.

These principles are the backbone of the Always-Do / Never-Do sections below, especially for a real-time / event-driven platform where principles **5, 6, and 7** are load-bearing.

---

## 2. Always-Do Patterns (mandatory)

Non-negotiable standards for AWS serverless production workloads on an event-driven platform. Every entry follows the required format. All Developer-Guide sources are continuously updated and were accessed **2026-07-31**.

### AD-1 — Choose the invocation model deliberately (sync vs async vs poll-based)

**Pattern:** Match each Lambda trigger to the correct invocation model and its error-handling contract.
**Why:** Error handling, retries, payload limits, and back-pressure differ *entirely* by invocation model. Synchronous (`RequestResponse`) returns errors to the caller with no built-in retry; asynchronous (`Event`) is queued by Lambda, retried twice, then routed to a DLQ/destination; event source mappings (poll-based) deliver batches **at least once** and support partial batch response. Aligns with **Reliability** and the "use events to trigger transactions" design principle.
**Provider Service:** AWS Lambda (invocation models), Amazon API Gateway / Application Load Balancer / Lambda Function URLs (sync front doors), Amazon S3 / Amazon SNS / Amazon EventBridge (async sources), Amazon SQS / Amazon Kinesis Data Streams / Amazon DynamoDB Streams / Amazon MSK (event source mappings).
**Architecture Decision:** Public real-time request/response → sync via API Gateway. Fire-and-forget side effects → async invoke with an on-failure destination. High-volume streams/queues → event source mapping with tuned batch size + batching window + `ReportBatchItemFailures`.
**Verification:** For async, confirm `DestinationConfig`/`DeadLetterConfig` is set (`aws lambda get-function-event-invoke-config`). For event source mappings, confirm `FunctionResponseTypes=["ReportBatchItemFailures"]` (`aws lambda get-event-source-mapping`).
**Trade-offs:** Sync couples caller latency to function duration; async adds eventual consistency; poll-based mandates idempotency (guaranteed duplicates).
**Source:** [Lambda invocation](https://docs.aws.amazon.com/lambda/latest/dg/lambda-invocation.html), [Best practices for working with Lambda functions](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html) (accessed 2026-07-31).

### AD-2 — Single-responsibility, stateless function design

**Pattern:** One function = one purpose; no mutable cross-invocation user state.
**Why:** "Speedy, simple, singular" and "Share nothing": execution environments are short-lived and reused unpredictably, so per-user state stored in globals can leak across invocations/tenants and is not durable. Aligns with **Operational Excellence** and **Security**.
**Provider Service:** AWS Lambda (execution environment), Amazon DynamoDB / Amazon ElastiCache (external state).
**Architecture Decision:** Initialize *immutable, non-sensitive* clients/SDK connections in module/global scope (reused across warm invocations); keep only per-request logic in the handler; persist all mutable state to DynamoDB/ElastiCache.
**Verification:** Inspect the CloudWatch `REPORT` line `Init Duration` (warm invocations skip init) and `Max Memory Used`; code review confirms no mutable user state in module scope.
**Trade-offs:** Connection reuse improves latency/cost but forbids per-request mutable globals; multi-tenant isolation may require separate functions/versions.
**Source:** [Best practices — Function code](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html), [Serverless Applications Lens — General design principles](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/general-design-principles.html) (⚠️ 2022-07; verify currency) (accessed 2026-07-31).

### AD-3 — Idempotent handlers on every at-least-once source

**Pattern:** Make every SQS/Kinesis/DynamoDB-Streams/async consumer idempotent.
**Why:** "Lambda event source mappings process each event **at least once**, and duplicate processing of records can occur… we strongly recommend that you make your function code idempotent." Aligns with **Reliability** and "design for failures and duplicates."
**Provider Service:** AWS Lambda, Amazon DynamoDB (idempotency store), **Powertools for AWS Lambda — Idempotency utility** (Python / TypeScript / Java / .NET).
**Architecture Decision:** Derive an idempotency key (message ID, event ID, or business key); use a conditional `PutItem` in DynamoDB or the Powertools Idempotency decorator with a DynamoDB persistence store and TTL; make downstream writes safe to repeat.
**Verification:** Replay a duplicate event and assert a single side effect; monitor a duplicate-key/conditional-check-failed metric.
**Trade-offs:** Adds a DynamoDB read/write per event (cost + latency); idempotency-key TTL must exceed the redelivery window.
**Source:** [Best practices — Working with streams and queues](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html), [Powertools for AWS Lambda](https://docs.aws.amazon.com/powertools/) (accessed 2026-07-31).

### AD-4 — Error handling with DLQ / on-failure destinations + partial batch response

**Pattern:** Never let failed events vanish; capture them and retry granularly.
**Why:** Async invocations are retried by Lambda twice and then dropped unless a DLQ/destination captures them. For stream/queue sources, enable partial batch response "to retry only the failed records instead of the entire batch." Aligns with **Reliability**.
**Provider Service:** Amazon SQS (DLQ), Amazon SNS / Amazon EventBridge (destinations), AWS Lambda on-failure destinations, **Powertools Batch Processing** utility.
**Architecture Decision:** Async functions → on-failure **Destination** (richer than a bare DLQ: includes request + response context) or DLQ. Stream/queue consumers → return `ReportBatchItemFailures` and configure `BisectBatchOnFunctionError` / `MaximumRetryAttempts` on the event source mapping; attach a source DLQ for poison messages.
**Verification:** Inject one failing record in a batch; confirm only that record is retried and poison messages land in the DLQ; alarm on `DeadLetterErrors`.
**Trade-offs:** DLQ requires a re-drive/reprocessing runbook; partial batch response requires the handler to return the correct failure structure.
**Source:** [Best practices — Working with streams and queues](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html), [Lambda invocation — Asynchronous](https://docs.aws.amazon.com/lambda/latest/dg/invocation-async.html) (accessed 2026-07-31).

### AD-5 — Observability: structured JSON logs, EMF metrics, Lambda Insights, X-Ray tracing

**Pattern:** Emit structured logs, asynchronous custom metrics (EMF), enable Lambda Insights, and propagate X-Ray traces across every async hop.
**Why:** "Use structured JSON logging for better observability" and "Emit custom metrics asynchronously using Embedded Metric Format (EMF)… reduces latency" versus synchronous `PutMetricData`. **CloudWatch Lambda Insights** adds system-level metrics (CPU, memory, network, init/shutdown phases) via a managed extension layer. **AWS X-Ray** stitches distributed traces across API Gateway → Lambda → SQS/EventBridge → downstream. Aligns with **Operational Excellence**.
**Provider Service:** Amazon CloudWatch Logs, Amazon CloudWatch Metrics (EMF), Amazon CloudWatch Lambda Insights (extension layer), AWS X-Ray, Powertools Logger/Metrics/Tracer.
**Architecture Decision:** JSON logs at INFO with a correlation/trace ID; EMF for business metrics; enable active tracing (`TracingConfig.Mode=Active`) and Lambda Insights on latency-sensitive functions; pass trace context through SQS message attributes / EventBridge event so traces survive async boundaries.
**Verification:** Query CloudWatch Logs Insights for the JSON schema; confirm EMF metrics appear without in-code `PutMetricData`; confirm a connected service map in the X-Ray/CloudWatch console; confirm the Lambda Insights layer is attached (`aws lambda get-function` → `Layers`).
**Trade-offs:** X-Ray and Lambda Insights add small cost + a few ms overhead; trace propagation across async hops needs explicit context passing.
**Source:** [Best practices — Metrics and alarms / logging](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html), [Monitoring functions with Lambda Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Lambda-Insights.html), [Using AWS Lambda with AWS X-Ray](https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html) (accessed 2026-07-31).

### AD-6 — Least-privilege execution role, one role per function

**Pattern:** Scope each function's IAM execution role to exact actions and resource ARNs; no wildcards.
**Why:** "Use most-restrictive permissions when setting IAM policies. Understand the resources and operations your Lambda function needs, and limit the execution role to these permissions." Aligns with **Security** (per-function blast-radius isolation).
**Provider Service:** AWS IAM execution role (identity policy) + Lambda resource-based function policy (who may invoke); AWS Security Hub CSPM Lambda controls and Amazon GuardDuty Lambda Protection for detection.
**Architecture Decision:** One dedicated role per function; scope `Action` and `Resource` to exact ARNs (e.g., a single queue/table); grant invoke rights via the resource-based policy, not broad principals.
**Verification:** IAM Access Analyzer; Security Hub CSPM Lambda controls; `aws lambda get-policy`; `aws iam get-role-policy`.
**Trade-offs:** More roles/policies to manage (offset by IaC modules); tight scoping needs an inventory of downstream ARNs.
**Source:** [Best practices — Security](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html), [Security in Lambda](https://docs.aws.amazon.com/lambda/latest/dg/lambda-security.html) (accessed 2026-07-31).

### AD-7 — Secrets in AWS Secrets Manager, never in environment variables

**Pattern:** Fetch sensitive credentials at runtime from AWS Secrets Manager; never store secrets in plaintext env vars.
**Why:** Environment variables are visible via `GetFunctionConfiguration` and are not a secrets store; hardcoding credentials is a critical exposure. Env vars should carry only non-secret operational params (bucket name, log level), and even those should be KMS-encrypted. Aligns with **Security**.
**Provider Service:** AWS Secrets Manager (with the Lambda extension / cache for fewer API calls), AWS Systems Manager Parameter Store (SecureString), AWS KMS (customer-managed key for env-var encryption).
**Architecture Decision:** Store secret in Secrets Manager; grant the execution role `secretsmanager:GetSecretValue` on that secret's ARN only; retrieve at init and cache in the execution environment; enable automatic rotation.
**Verification:** Console shows env vars KMS-encrypted; no secret-like keys in `GetFunctionConfiguration`; no secrets in CloudWatch Logs; Secrets Manager rotation enabled.
**Trade-offs:** Retrieval adds a small init latency (mitigated by the Secrets Manager extension/cache) and cost per API call.
**Source:** [Security in Lambda](https://docs.aws.amazon.com/lambda/latest/dg/lambda-security.html), [Best practices — Function configuration](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html) (accessed 2026-07-31).

### AD-8 — Concurrency controls: reserved concurrency to protect downstreams

**Pattern:** Set **reserved concurrency** on functions that call fragile/rate-limited downstreams; know the account concurrency pool.
**Why:** The account default is **1,000 concurrent executions** (increasable). Reserved concurrency both guarantees and caps a function's share, protecting downstreams (RDS, third-party APIs) from overload and isolating noisy neighbors. Setting reserved concurrency to `0` is the emergency kill-switch for a runaway/recursive function. Aligns with **Reliability** and **Cost Optimization**.
**Provider Service:** AWS Lambda reserved concurrency; Application Auto Scaling (for provisioned-concurrency targets).
**Architecture Decision:** Determine the throughput ceiling of the slowest downstream; set reserved concurrency at or below it; leave headroom in the shared account pool for other functions.
**Verification:** `aws lambda get-function-concurrency`; CloudWatch `ConcurrentExecutions` and `Throttles` metrics; alarm on sustained `Throttles`.
**Trade-offs:** Reserving on one function reduces the shared pool available to all others; set too low and legitimate traffic is throttled.
**Source:** [Lambda function scaling / reserved concurrency](https://docs.aws.amazon.com/lambda/latest/dg/lambda-concurrency.html), [Lambda quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html) (accessed 2026-07-31).

### AD-9 — Correct VPC-Lambda configuration (only when required)

**Pattern:** Attach a function to a VPC **only** when it must reach private resources; then configure subnets, security groups, and egress correctly.
**Why:** VPC attachment lets Lambda reach private Amazon RDS/ElastiCache/internal services but adds Hyperplane-ENI management; a private-subnet function needs a **NAT Gateway** (or VPC endpoints) for internet/AWS-API egress. Aligns with **Security** and **Performance Efficiency**.
**Provider Service:** AWS Lambda VPC config, Amazon VPC (private subnets, security groups), NAT Gateway, AWS PrivateLink / Gateway VPC endpoints (S3, DynamoDB).
**Architecture Decision:** Place functions in private subnets across ≥2 AZs; use a least-privilege security group; add VPC endpoints for AWS services to avoid NAT cost; ENIs-per-VPC quota is **500** (shared with EFS, increasable). If the function only calls public AWS/HTTPS endpoints, **do not** attach a VPC.
**Verification:** `aws lambda get-function-configuration` → `VpcConfig`; confirm subnets are private with a NAT route or VPC endpoints; test reachability to the private resource.
**Trade-offs:** VPC networking adds ENI/egress cost and can affect scaling; over-attaching to a VPC is a common and costly anti-pattern.
**Source:** [Configuring a Lambda function to access resources in a VPC](https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html), [Security in Lambda](https://docs.aws.amazon.com/lambda/latest/dg/lambda-security.html), [Lambda quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html) (accessed 2026-07-31).

### AD-10 — Orchestrate multi-step workflows with Step Functions, not code

**Pattern:** Model multi-step / saga / long-running flows as an AWS Step Functions state machine.
**Why:** "Orchestrate your application with state machines, not functions." State machines provide built-in retries, `Catch`/compensation, execution history, and visibility; hand-coded Lambda chains become a tightly-coupled monolith. Aligns with **Operational Excellence** and **Reliability**.
**Provider Service:** AWS Step Functions (Standard for durable/auditable up to 1 year with exactly-once semantics; Express for high-volume event processing up to 5 minutes with at-least-once/at-most-once).
**Architecture Decision:** Use `Retry`/`Catch` in ASL; use Standard for non-idempotent business transactions (payments) and Express for high-throughput idempotent event/stream processing (see Decision D2).
**Verification:** Step Functions execution history in console/API; CloudWatch `ExecutionsFailed`/`ExecutionThrottled` metrics.
**Trade-offs:** Standard is billed per state transition (cost grows with steps); Express is billed by executions × duration × memory.
**Source:** [Choosing workflow type in Step Functions](https://docs.aws.amazon.com/step-functions/latest/dg/choosing-workflow-type.html), [Serverless Applications Lens — Design principles](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/general-design-principles.html) (⚠️ 2022-07; verify currency) (accessed 2026-07-31).

### AD-11 — Stay on a supported runtime; own the upgrade cadence

**Pattern:** Run only supported managed runtimes; plan proactive migrations.
**Why:** Deprecated runtimes stop receiving security patches and eventually block create/update. **Amazon Linux 2 reaches end of life on June 30, 2026**; migrate AL2-based runtimes to AL2023-based runtimes. Aligns with **Security** and **Operational Excellence**.
**Provider Service:** AWS Lambda managed runtimes; AWS Trusted Advisor / AWS Health Dashboard (deprecation notices, ~180-day notice).
**Architecture Decision:** Track the supported-runtimes table; use versions + aliases so runtime upgrades are canary-deployable and reversible via alias repoint.
**Verification:** `aws lambda list-functions` cross-referenced with the supported-runtimes table; Trusted Advisor "Functions Using Deprecated Runtimes".
**Trade-offs:** Upgrade testing effort; native dependencies may need rebuilds (especially for arm64).
**Source:** [Lambda runtimes (supported/deprecated)](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html) (accessed 2026-07-31).

---

## 3. Ask-First Decisions (context-dependent)

Valid patterns with material trade-offs. Ask the architect the framed question before committing. Each cites a dated official source.

### D1 — Lambda vs AWS Fargate / Amazon ECS for event consumers

| Option | AWS mechanism | Optimizes | Sacrifices | Best when |
|---|---|---|---|---|
| **AWS Lambda** | Per-event, event source mapping | No servers, per-ms billing, instant scale-to-zero, native event integrations | 15-min max duration; cold-start tail latency; per-invoke model | Bursty/spiky event volume, short (<15 min) tasks, scale-to-zero economics |
| **AWS Fargate (ECS)** | Long-running containers | No duration cap, steady high-throughput, warm connections, large deps | Pays for running tasks (no scale-to-zero without tuning); you manage the consumer loop | Sustained high-throughput consumers, >15-min processing, heavy per-container state |
| **Amazon ECS on EC2** | Container on managed EC2 | Max control, GPU/special instances, cheapest at steady scale | You manage capacity/patching | Specialized hardware, very high steady throughput |

- **Ask the architect:** "Is the consumer bursty and short-lived (Lambda) or a sustained, always-on, high-throughput stream consumer that benefits from warm connections and no 15-min cap (Fargate/ECS)? What is the p99 latency budget and the cold-start tolerance?"
- **Decision factors:** duration ceiling (Lambda hard cap 900 s / 15 min), cold-start sensitivity, steady-vs-spiky load, cost at target throughput.
- **Source:** [Lambda quotas — timeout](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html); [Serverless Applications Lens — Scenarios](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/scenarios.html) (⚠️ 2022-07; verify currency) (accessed 2026-07-31).

### D2 — Step Functions Standard vs Express Workflows

Verified from the Step Functions Developer Guide (accessed 2026-07-31):

| Attribute | **Standard Workflows** | **Express Workflows** |
|---|---|---|
| Max duration | **1 year** | **5 minutes** |
| Execution semantics | **Exactly-once** | Async: **at-least-once** · Sync: **at-most-once** |
| State persistence between transitions | Yes (durable) | No |
| Idempotency on duplicate execution name | Auto (idempotent response) | Not managed (concurrent executions) |
| Pricing | Per **state transition** | Per **execution × duration × memory** |
| Execution history | Retained 90 days; console + API | Not captured by SFN; must enable CloudWatch Logs |
| State-transition rate | Soft quota (e.g., 5,000 bucket in us-east-1/us-west-2/eu-west-1) | **Unlimited** |
| Distributed Map / Activities / `.sync` / `.waitForTaskToken` | Supported | **Not** supported |

- **Ask the architect:** "Is this a **non-idempotent, durable, auditable** business transaction (payments, EMR cluster) needing exactly-once and long duration → **Standard**? Or a **high-volume, idempotent, short (<5 min)** event/stream/IoT ingestion path → **Express**?"
- **Real-time / event-driven note:** For high-TPS stream ingestion, transformation, and IoT, AWS explicitly recommends **Express** (at-least-once → handlers must be idempotent). For sagas/human-in-the-loop/compensation, use **Standard**. Workflow type is **immutable after creation**.
- **Source:** [Choosing workflow type in Step Functions](https://docs.aws.amazon.com/step-functions/latest/dg/choosing-workflow-type.html), [Step Functions service quotas](https://docs.aws.amazon.com/step-functions/latest/dg/service-quotas.html) (accessed 2026-07-31).

### D3 — Event routing: Amazon EventBridge vs Amazon SQS vs Amazon SNS

Verified from the official **AWS Decision Guide** (last updated **2024-07-31**) and the EventBridge User Guide (accessed 2026-07-31):

| Attribute | **Amazon SQS** | **Amazon SNS** | **Amazon EventBridge** |
|---|---|---|---|
| Communication model | Pull (poll queue) | Push (pub/sub) | Push, event-driven (rules → targets) |
| Persistence | Messages persist until consumed/expired (retention up to 14 days) | Not persisted (real-time) | Not persisted (real-time; archive/replay available) |
| Delivery guarantee | At-least-once | At-least-once (HTTP/S); exactly-once for Lambda & SQS subscribers | At-least-once |
| Ordering | FIFO queues = strict order | FIFO topics = order | **No ordering guarantee** |
| Filtering / routing | Basic (visibility timeout, DLQ) | Subscription filter policies | **Advanced content-based pattern matching** |
| Fan-out | Not natively (pair with SNS) | Native pub/sub fan-out | Fan-out via rules to many targets |
| Typical use | Decouple microservices, buffer/load-level, async task queue | Fan-out notifications, pub/sub, mobile push | Event-driven arch, real-time stream routing, cross-account, SaaS integrations, schema registry |

- **Ask the architect:** "Start from the *pattern*: point-to-point durable **work queue** with retries/DLQ → **SQS**; broadcast the same message to **many subscribers** → **SNS**; **schema-aware routing/filtering** of events from many sources to many targets, with archive/replay and cross-account → **EventBridge**. Common combo: **SNS→SQS** fan-out with per-consumer durability; **EventBridge Pipes** for point-to-point source→target with enrichment."
- **Real-time / event-driven note:** EventBridge gives loose coupling + content filtering + replay but **no ordering**; when strict ordering matters use SQS FIFO / SNS FIFO / Kinesis. When you cannot lose a message, SQS's persistence + DLQ is the safest.
- **Source:** [Decision guide: SQS, SNS, or EventBridge?](https://docs.aws.amazon.com/decision-guides/latest/sns-or-sqs-or-eventbridge/sns-or-sqs-or-eventbridge.html) (2024-07-31); [What is Amazon EventBridge?](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-what-is.html) (accessed 2026-07-31).

### D4 — Lambda Layers vs deployment-package bundling vs container image

| Option | AWS mechanism | Optimizes | Sacrifices | Best when |
|---|---|---|---|---|
| **Layers** | Up to 5 layers, shared across functions; counts toward 250 MB unzipped | Dependency reuse, smaller function packages, faster iteration | Versioning/coordination across functions; still bound by 250 MB unzipped | Shared deps across many functions |
| **Bundled .zip** | 50 MB zipped / 250 MB unzipped | Self-contained, reproducible builds, tree-shaking | Larger per-function upload; duplicated deps | Independent functions, modern bundlers |
| **Container image** | Up to 10 GB (Amazon ECR) | Large deps / ML models, existing container CI/CD | Slower cold start, ECR lifecycle management | Big binaries, ML inference, container pipelines |

- **Ask the architect:** "Are dependencies shared across many functions (**Layers**), self-contained per function (**bundled .zip**), or too large / already containerized (**container image**, up to 10 GB)?"
- **Source:** [Lambda quotas — deployment package / layers](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html), [Working with Lambda layers](https://docs.aws.amazon.com/lambda/latest/dg/chapter-layers.html) (accessed 2026-07-31).

### D5 — Cold-start strategy: on-demand vs Provisioned Concurrency vs SnapStart (latency-sensitive paths)

| Option | AWS mechanism | Optimizes | Sacrifices | Best when |
|---|---|---|---|---|
| **On-demand (no mitigation)** | Default | Pure pay-per-use, lowest cost | Cold-start tail latency | Async/batch, latency-tolerant consumers |
| **Provisioned Concurrency** | Pre-warmed environments (+ Application Auto Scaling) | Zero cold start for the reserved count | Pays even when idle; free tier N/A | Predictable, sustained low-latency sync traffic |
| **SnapStart** | Firecracker snapshot restore (Java, Python 3.12+, .NET 8+) | Sub-second starts, **no idle charge** | Cache+restore charges; uniqueness/entropy caveats; runtime-limited | Spiky latency-sensitive traffic on a supported runtime |

- **Cost profile:** on-demand < SnapStart (usage-based restore) < Provisioned Concurrency (idle charge).
- **Ask the architect:** "What is the p99 latency SLO on the real-time path, and is traffic spiky or steady? Spiky + supported runtime → **SnapStart**; steady low-latency → **Provisioned Concurrency**; latency-tolerant → leave **on-demand**."
- **Source:** [Configuring provisioned concurrency](https://docs.aws.amazon.com/lambda/latest/dg/provisioned-concurrency.html), [Improving startup performance with SnapStart](https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html), [Lambda pricing](https://aws.amazon.com/lambda/pricing/) (accessed 2026-07-31).

> ⚠️ **Ask-First (organizational, cannot default):** Compliance-specific patterns (SOC 2 / HIPAA / PCI-DSS / GDPR) and cost commitments (Compute Savings Plans covering Lambda) depend on the organization's certification scope and billing agreements. Surface and ask before prescribing.

---

## 4. Never-Do Anti-patterns

Each entry follows the required ❌ Wrong / ✅ Correct / Detection format with exact AWS service names. Sources accessed **2026-07-31**.

### NA-1 — Long-running synchronous processing in Lambda (> 15-min timeout anti-pattern)

- **Pillar:** Reliability, Cost Optimization · **Risk:** HIGH.
- ❌ **Wrong:** Configuring an AWS Lambda function to run a multi-hour batch job, or synchronously blocking an Amazon API Gateway caller while a long job runs — Lambda's hard timeout ceiling is **900 s (15 min)**, after which the invocation fails with a timeout.
- ✅ **Correct:** Decompose into <15-min steps orchestrated by **AWS Step Functions** (Standard, up to 1 year), or offload long/steady batch compute to **AWS Fargate** / **AWS Batch**. For long client waits, return `202 Accepted` and process asynchronously via **Amazon SQS** + Lambda.
- **Detection:** `aws lambda list-functions --query 'Functions[?Timeout==\`900\`]'`; CloudWatch alarm on `Duration` approaching timeout and on `Errors` with timeout cause.
- **Source:** [Lambda quotas — function timeout](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html); [Choosing workflow type](https://docs.aws.amazon.com/step-functions/latest/dg/choosing-workflow-type.html).

### NA-2 — Storing state in the Lambda execution context between invocations

- **Pillar:** Security, Reliability · **Risk:** MEDIUM-HIGH.
- ❌ **Wrong:** Caching per-user/session data in a module-global variable in an AWS Lambda function, assuming it persists — environments are reused unpredictably across invocations and tenants ("share nothing" violation), causing cross-invocation data leaks and lost state.
- ✅ **Correct:** Persist mutable state in **Amazon DynamoDB** or **Amazon ElastiCache**; keep only immutable, non-sensitive assets (SDK clients, static config) in module scope / `/tmp`.
- **Detection:** Code review for mutable global user state; scan for module-scope dicts/maps keyed by user/request ID.
- **Source:** [Best practices — Function code](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html); [Serverless Applications Lens — Design principles ("Share nothing")](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/general-design-principles.html) (⚠️ 2022-07; verify currency).

### NA-3 — Unbounded fan-out without throttling

- **Pillar:** Reliability, Cost Optimization · **Risk:** HIGH.
- ❌ **Wrong:** An **Amazon SNS** topic or **Amazon EventBridge** rule fanning out to many **AWS Lambda** consumers with no back-pressure, letting a spike overwhelm a fragile downstream (e.g., Amazon RDS) or exhaust the account's 1,000-concurrency pool.
- ✅ **Correct:** Insert **Amazon SQS** buffers between fan-out and consumers (queue-based load leveling) and cap each consumer with **Lambda reserved concurrency** sized to the slowest downstream; for SNS fan-out use the **SNS→SQS** pattern so each consumer drains at its own safe rate.
- **Detection:** CloudWatch `ConcurrentExecutions` vs account limit, `Throttles`, and downstream saturation metrics; review topic/rule targets for missing SQS buffers.
- **Source:** [Lambda function scaling / reserved concurrency](https://docs.aws.amazon.com/lambda/latest/dg/lambda-concurrency.html); [Decision guide: SQS, SNS, or EventBridge?](https://docs.aws.amazon.com/decision-guides/latest/sns-or-sqs-or-eventbridge/sns-or-sqs-or-eventbridge.html) (2024-07-31).

### NA-4 — Direct Lambda-to-Lambda synchronous chaining

- **Pillar:** Operational Excellence, Reliability, Cost Optimization · **Risk:** HIGH.
- ❌ **Wrong:** Function A calls `lambda.invoke` (RequestResponse) on Function B, which invokes Function C — hand-coding retries and state. This creates a tightly-coupled monolith, doubles cost (A pays while it waits for B), and has no execution visibility.
- ✅ **Correct:** Model the flow as an **AWS Step Functions** state machine (built-in `Retry`/`Catch`/compensation + execution history), or decouple stages asynchronously via **Amazon EventBridge** / **Amazon SQS**.
- **Detection:** Grep application code for synchronous `lambda.invoke` / `InvocationType='RequestResponse'` chains; architecture review.
- **Source:** [Serverless Applications Lens — "Orchestrate with state machines, not functions"](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/general-design-principles.html) (⚠️ 2022-07; verify currency); [Choosing workflow type](https://docs.aws.amazon.com/step-functions/latest/dg/choosing-workflow-type.html).

### NA-5 — Missing idempotency in Amazon SQS / stream consumers (at-least-once delivery)

- **Pillar:** Reliability · **Risk:** HIGH.
- ❌ **Wrong:** An **Amazon SQS**-triggered **AWS Lambda** function that inserts an order row with no dedupe — because SQS/event source mappings deliver **at least once**, a redelivered message creates a duplicate order (double charge/email).
- ✅ **Correct:** Idempotent write keyed by message/business ID — conditional `PutItem` in **Amazon DynamoDB**, or the **Powertools for AWS Lambda Idempotency** utility backed by a DynamoDB persistence store with TTL. Also set the SQS **visibility timeout ≥ function timeout** so a message is not redelivered mid-processing.
- **Detection:** Replay a message and assert a single side effect; compare SQS `VisibilityTimeout` vs Lambda `Timeout`; monitor a conditional-check-failed / duplicate-key metric.
- **Source:** [Best practices — Working with streams and queues](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html); [Decision guide (SQS at-least-once)](https://docs.aws.amazon.com/decision-guides/latest/sns-or-sqs-or-eventbridge/sns-or-sqs-or-eventbridge.html) (2024-07-31).

### NA-6 — Hardcoded secrets in code or plaintext environment variables

- **Pillar:** Security · **Risk:** CRITICAL.
- ❌ **Wrong:** `DB_PASSWORD = "P@ssw0rd"` in the handler, or a plaintext `DB_PASSWORD` **AWS Lambda** environment variable readable via `aws lambda get-function-configuration`.
- ✅ **Correct:** Store the credential in **AWS Secrets Manager** (or SSM Parameter Store SecureString); fetch at runtime via a least-privilege execution role scoped to that secret's ARN; encrypt any config env vars with a **customer-managed AWS KMS key**; enable rotation.
- **Detection:** AWS Security Hub CSPM Lambda controls; scan `get-function-configuration` output for secret-like keys; git secret scanning (e.g., in CI).
- **Source:** [Security in Lambda](https://docs.aws.amazon.com/lambda/latest/dg/lambda-security.html); [Best practices — Function configuration](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html).

### NA-7 — Wildcard execution-role permissions in production

- **Pillar:** Security · **Risk:** CRITICAL.
- ❌ **Wrong:** An **AWS Lambda** execution role with `{"Action": "*", "Resource": "*"}` (or `s3:*` on `*`) — a compromised function can act across the entire account.
- ✅ **Correct:** Scope the **AWS IAM** execution role to exact operations and ARNs, e.g., `s3:GetObject` on `arn:aws:s3:::orders-bucket/*` only; one role per function.
- **Detection:** AWS IAM Access Analyzer; AWS Security Hub CSPM; `aws iam get-role-policy`.
- **Source:** [Best practices — Security](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html); [Security in Lambda](https://docs.aws.amazon.com/lambda/latest/dg/lambda-security.html).

### NA-8 — Async invocations with no DLQ or on-failure destination

- **Pillar:** Reliability · **Risk:** HIGH.
- ❌ **Wrong:** An **Amazon S3** / **Amazon SNS**-triggered async **AWS Lambda** function with no DLQ/destination — failed events silently vanish after Lambda's 2 retries.
- ✅ **Correct:** Configure an **on-failure Destination** (Amazon SQS / Amazon SNS / Amazon EventBridge / another Lambda) or a **dead-letter queue (Amazon SQS)** to capture failed invocation records; alarm on `DeadLetterErrors`.
- **Detection:** `aws lambda get-function-event-invoke-config` for `DestinationConfig`; `get-function-configuration` for `DeadLetterConfig`; CloudWatch `Errors`/`DeadLetterErrors` alarms.
- **Source:** [Lambda invocation — Asynchronous](https://docs.aws.amazon.com/lambda/latest/dg/invocation-async.html); [Best practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html).

### NA-9 — Running on a deprecated runtime

- **Pillar:** Security · **Risk:** HIGH.
- ❌ **Wrong:** New **AWS Lambda** function on a deprecated runtime (e.g., `python3.8`, `nodejs16.x`, `go1.x`, `dotnet6`, or the original `provided` on Amazon Linux) — no security patches, eventual create/update block.
- ✅ **Correct:** Use a supported AL2023-based runtime and migrate all Amazon Linux 2-based runtimes **before AL2 EOL (June 30, 2026)**; deploy runtime upgrades behind versions + aliases for safe rollback.
- **Detection:** AWS Trusted Advisor "Functions Using Deprecated Runtimes"; AWS Health Dashboard; `aws lambda list-functions` vs the supported-runtimes table.
- **Source:** [Lambda runtimes (supported/deprecated, AL2 EOL)](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html).

---

## 5. Service Equivalence Map

Serverless / event-driven service classes across providers. **Equivalence ≠ feature parity** — cold-start behavior, max duration, memory ceilings, concurrency models, ordering, and pricing differ substantially. Validate limits/pricing per provider before relying on any mapping. Mapping consolidated from each provider's official service catalog (accessed 2026-07-31); AWS entries anchored to the AWS Developer Guides cited above.

| Category | **AWS** | **Microsoft Azure** | **Google Cloud** | **Oracle Cloud (OCI)** |
|---|---|---|---|---|
| FaaS (serverless functions) | AWS Lambda | Azure Functions | Cloud Run functions (Cloud Functions) | OCI Functions |
| Serverless containers | AWS Lambda (container image) / AWS Fargate | Azure Container Apps | Cloud Run | OCI Container Instances |
| Workflow orchestration | AWS Step Functions | Azure Logic Apps / Durable Functions | Workflows | OCI Functions + Events / Resource Manager |
| Event bus / router | Amazon EventBridge | Azure Event Grid | Eventarc | OCI Events |
| Message queue | Amazon SQS | Azure Service Bus / Storage Queues | Cloud Tasks / Pub/Sub | OCI Queue |
| Pub/Sub notifications | Amazon SNS | Azure Event Grid / Service Bus topics | Pub/Sub | OCI Notifications |
| Streaming | Amazon Kinesis Data Streams | Azure Event Hubs | Pub/Sub | OCI Streaming |
| API front door | Amazon API Gateway | Azure API Management | API Gateway / Apigee | OCI API Gateway |
| Secrets | AWS Secrets Manager | Azure Key Vault | Secret Manager | OCI Vault |
| Key management | AWS KMS | Azure Key Vault | Cloud KMS | OCI Vault / KMS |
| Serverless NoSQL | Amazon DynamoDB | Azure Cosmos DB | Firestore | OCI NoSQL Database |
| Observability | Amazon CloudWatch + AWS X-Ray | Azure Monitor / Application Insights | Cloud Monitoring / Logging / Trace | OCI Monitoring / APM |

> ⚠️ AWS Lambda specifics (900 s / 15-min max duration, 10 GB memory ceiling, SnapStart, event source mappings with partial batch response) have no exact cross-provider equal. Step Functions Standard's **exactly-once, 1-year** durable model is likewise distinctive.

---

## 6. Source Bibliography

### Primary — official AWS service documentation (continuously updated; accessed 2026-07-31)
- [Best practices for working with AWS Lambda functions](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html) — code, configuration, scaling, metrics, streams/queues, security.
- [Lambda invocation](https://docs.aws.amazon.com/lambda/latest/dg/lambda-invocation.html) and [Asynchronous invocation](https://docs.aws.amazon.com/lambda/latest/dg/invocation-async.html) — sync/async/poll models, retries, destinations, DLQ.
- [Understanding Lambda function scaling / reserved concurrency](https://docs.aws.amazon.com/lambda/latest/dg/lambda-concurrency.html).
- [Configuring provisioned concurrency](https://docs.aws.amazon.com/lambda/latest/dg/provisioned-concurrency.html) · [Improving startup performance with SnapStart](https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html).
- [Configuring a Lambda function to access resources in a VPC](https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html).
- [Security in AWS Lambda](https://docs.aws.amazon.com/lambda/latest/dg/lambda-security.html) — IAM, VPC, secrets, KMS, code signing.
- [Lambda runtimes (supported/deprecated, AL2 EOL 2026-06-30)](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html).
- [Working with Lambda layers](https://docs.aws.amazon.com/lambda/latest/dg/chapter-layers.html) · [Lambda quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html).
- [Using AWS Lambda with AWS X-Ray](https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html) · [Monitoring functions with CloudWatch Lambda Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Lambda-Insights.html).
- [Choosing workflow type in Step Functions (Standard vs Express)](https://docs.aws.amazon.com/step-functions/latest/dg/choosing-workflow-type.html) · [Step Functions service quotas](https://docs.aws.amazon.com/step-functions/latest/dg/service-quotas.html).
- [What is Amazon EventBridge?](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-what-is.html) — event buses, Pipes, Scheduler.

### Primary — official AWS decision guide (dated; still current)
- [Decision guide: Amazon SQS, Amazon SNS, or Amazon EventBridge?](https://docs.aws.amazon.com/decision-guides/latest/sns-or-sqs-or-eventbridge/sns-or-sqs-or-eventbridge.html) — **Last updated 2024-07-31** (within 24 months; the SQS/SNS/EventBridge model is stable — verified against the EventBridge User Guide).

### Framework guidance — ⚠️ Serverless Applications Lens (dated 2022-07; supporting only)
- [Serverless Applications Lens — Welcome (Publication date: July 14, 2022)](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/welcome.html) — `⚠️ Source dated 2022-07; verify currency.` **No 2025 edition exists.**
- [Serverless Applications Lens — The pillars](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/the-pillars-of-the-well-architected-framework.html) — `⚠️ 2022-07`.
- [Serverless Applications Lens — General design principles](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/general-design-principles.html) — `⚠️ 2022-07`.
- [Serverless Applications Lens — Scenarios](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/scenarios.html) — `⚠️ 2022-07`.
- [AWS Well-Architected Framework (main, continuously updated)](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html).

### Pricing & tooling (accessed 2026-07-31)
- [AWS Lambda pricing](https://aws.amazon.com/lambda/pricing/) · [AWS Step Functions pricing](https://aws.amazon.com/step-functions/pricing/).
- [Powertools for AWS Lambda](https://docs.aws.amazon.com/powertools/) — idempotency, logging, metrics, batch, tracing.
- [Serverless Land](https://serverlessland.com/) — official AWS serverless patterns (secondary; verify per-pattern).

---

## 7. Anti-Hallucination Checklist (self-verification)

- [x] **TARGET_EDITION stated in metadata and every major section** — plus an explicit correction: the "2025" Lens does **not** exist; effective edition = Serverless Applications Lens 2022-07 (supporting) cross-checked against continuously-updated Developer Guides.
- [x] **All 6 mandatory sections present** — Framework Pillars, Always-Do Patterns, Ask-First Decisions, Never-Do Anti-patterns, Service Equivalence Map, Source Bibliography.
- [x] **Every pattern cites an official AWS URL with access date** (2026-07-31; decision guide dated 2024-07-31; Lens dated 2022-07).
- [x] **Every Never-Do entry has ❌ Wrong / ✅ Correct + Detection with exact AWS service names.**
- [x] **AWS-specific names used throughout** — Amazon SQS / Amazon SNS / Amazon EventBridge / AWS Step Functions / AWS Lambda / Amazon API Gateway (no generic "message queue"/"event bus" where a product name exists).
- [x] **Sources > 12 months flagged** — Serverless Applications Lens (2022-07) flagged with `⚠️ Source dated 2022-07; verify currency` at every use; treated as supporting only.

### Residual gaps / must-confirm before skill authoring

- **Edition mismatch (resolved by flag):** Request assumed a "2025" Lens; none exists. The skill should cite the 2022 Lens as supporting guidance anchored to Developer Guides.
- **Compliance scope** (SOC 2 / HIPAA / PCI-DSS / GDPR) — `unverified`; org-specific, not prescribed here.
- **Cost commitments** (Compute Savings Plans covering Lambda) — `unverified`; billing-agreement dependent.

> **Recommended next step:** run `/skill-best-practices-validator` on the authored skill, then pass this file to `/skill-creator` for the event-driven platform skill set.
