---
title: AWS Serverless Patterns — Architecture Research
cloud_provider: AWS
architecture_domain: Serverless Patterns
target_edition: AWS Well-Architected Framework 2025 — Serverless Lens
research_date: 2026-07-31
primary_audience: Cloud Architects and Tech Leads
---

# AWS Serverless Patterns — Architecture Research

> **Target edition:** AWS Well-Architected Framework — **Serverless Applications Lens**.
> Research date: **2026-07-31**. Audience: **Cloud Architects and Tech Leads**.

## ⚠️ Version Absolutism Notice (read first)

The requested `TARGET_EDITION` is *"AWS Well-Architected Framework 2025 — Serverless Lens."* Version
absolutism requires an honest correction:

- The **AWS Well-Architected Serverless Applications Lens** whitepaper carries a
  **publication date of July 14, 2022**. It is the **current and only published edition** of the
  Serverless Lens — AWS has **not** released a "2025" Serverless Lens whitepaper as of the research
  date. ⚠️ (source > 12 months old, but it is the current stable edition, so it is retained per the
  Source Hierarchy exception). Source: [Serverless Applications Lens — Welcome](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/welcome.html) (Publication date: July 14, 2022; accessed 2026-07-31).
- The **core** AWS Well-Architected Framework (6 pillars, including **Sustainability**, added Dec 2021)
  is a living document and is current.
- Where the 2022 Lens is stale relative to current service behavior, this document **overrides Lens
  prose with the current, living service documentation** (AWS Lambda Developer Guide, API Gateway
  Developer Guide, Step Functions Developer Guide, EventBridge User Guide, and the AWS decision
  guides), each dated at point of extraction. **Every "2025-current" claim below is sourced to a
  living AWS service doc accessed 2026-07-31**, not to the 2022 Lens.

Treat this document as: *"Serverless Lens design principles (2022, current edition) reconciled with
2026-current AWS service documentation."*

---

## Framework Pillars

**Edition:** Well-Architected **Serverless Applications Lens** (Publication July 14, 2022 ⚠️ — current
edition) + living core Framework (6 pillars).

### Serverless general design principles (Lens)

The Lens defines seven serverless-specific design principles. Verbatim (source below):

1. **Speedy, simple, singular** — Functions are concise, short, single-purpose; their environment may
   live only up to the request lifecycle.
2. **Think concurrent requests, not total requests** — Design trade-offs are evaluated on the
   concurrency model, not aggregate request counts.
3. **Share nothing** — Runtime environment and infrastructure are short-lived; local/temp storage is
   not guaranteed. Prefer persistent storage for durable requirements.
4. **Assume no hardware affinity** — Use hardware-agnostic code; CPU flags may not be consistently
   available.
5. **Orchestrate your application with state machines, not functions** — Chaining Lambda executions in
   code produces a monolithic, tightly-coupled application; use a state machine (Step Functions).
6. **Use events to trigger transactions** — React to events (e.g., new S3 object, DB update) for
   just-in-time, consumer-agnostic processing.
7. **Design for failures and duplicates** — Operations must be **idempotent**; requests/events can be
   delivered more than once. Include retries for downstream calls.

Source: [Serverless Lens — Design principles](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/general-design-principles.html) (2022 edition; accessed 2026-07-31).

### The six pillars (serverless framing)

| Pillar | Serverless best-practice areas (Lens) | Key AWS services |
|--------|----------------------------------------|------------------|
| **Operational Excellence** | Prepare / operate / evolve; structured JSON logging, EMF custom metrics, tracing, deployment automation | Amazon CloudWatch, AWS X-Ray, Powertools for AWS Lambda, AWS SAM/CDK |
| **Security** | Identity & access management, Detective controls, Infrastructure protection, Data protection, Incident response. Serverless removes OS/patching burden but OWASP + app-sec still apply | AWS IAM, Amazon Cognito, AWS WAF, AWS Secrets Manager, AWS Security Hub CSPM, Amazon GuardDuty Lambda Protection |
| **Reliability** | Foundations, Change management, Failure management; throttling/concurrency, retries, DLQ, self-healing | Reserved/provisioned concurrency, Amazon SQS DLQ, Lambda destinations, Step Functions |
| **Performance Efficiency** | Right-size memory (CPU scales with memory), cold-start mitigation, execution-environment reuse | Provisioned concurrency, Lambda SnapStart, AWS Lambda Power Tuning |
| **Cost Optimization** | Pay-per-use, right-sizing, workflow-type selection, anomaly detection | AWS Cost Anomaly Detection, Step Functions Express, Lambda Power Tuning |
| **Sustainability** | Maximize utilization of managed services; avoid idle provisioned capacity | Managed serverless services (shared-tenant efficiency) |

Sources: [Serverless Lens — Pillars](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/the-pillars-of-the-well-architected-framework.html), [Security pillar](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/security-pillar.html), [Reliability pillar](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/reliability-pillar.html) (all 2022 edition; accessed 2026-07-31); pillar-service mappings reconciled with [Lambda best practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html) (living doc; accessed 2026-07-31).

---

## Mandatory Patterns

Target edition: Serverless Lens (2022, current) + living service docs (2026-07-31).

### Pattern: Single-responsibility Lambda functions ("speedy, simple, singular")
**Why:** Lens design principle #1 + #5. Small, single-purpose functions reduce cold-start weight,
simplify IAM scoping, and avoid the monolithic "God function." Pillar alignment: Operational
Excellence, Performance Efficiency.
**Provider Service:** AWS Lambda.
**Architecture Decision:** One function = one business capability. Orchestrate multi-step flows with
AWS Step Functions rather than chaining logic inside a single handler.
**Verification:** Review each function's handler scope; `aws lambda list-functions` and inspect
per-function IAM role attachment. Audit that no function contains an internal orchestration loop.
**Trade-offs:** More deployable units → more CI/CD and observability surface; requires an
orchestration layer (Step Functions cost/state-transition billing).
**Source:** [Serverless Lens — Design principles](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/general-design-principles.html) (2022; accessed 2026-07-31).

### Pattern: Statelessness + execution-environment reuse
**Why:** "Share nothing" — runtime is short-lived; storing user data in the execution environment
risks cross-invocation data leaks. Reusing SDK clients/DB connections across warm invocations reduces
latency and cost. Pillar: Security + Performance Efficiency.
**Provider Service:** AWS Lambda.
**Architecture Decision:** Initialize SDK clients and DB connections **outside** the handler; cache
static assets in `/tmp`. Never store per-user state in module scope. Use keep-alive to maintain
persistent connections (Lambda purges idle connections).
**Verification:** Code review: connection/client init outside handler. Confirm no mutable user state
persists across invocations. `REPORT` log line shows `Max Memory Used` for right-sizing.
**Trade-offs:** `/tmp` and memory are not guaranteed persistent; keep-alive requires runtime-specific
config.
**Source:** [Lambda best practices — Function code](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html) (living doc; accessed 2026-07-31).

### Pattern: Idempotent handlers for at-least-once delivery
**Why:** Lens principle #7; Lambda event source mappings and async invocation are **at-least-once** —
duplicate delivery can occur. Pillar: Reliability.
**Provider Service:** AWS Lambda + Powertools for AWS Lambda (Idempotency utility).
**Architecture Decision:** Validate events, deduplicate using an idempotency key persisted in Amazon
DynamoDB (Powertools Idempotency utility handles this across Python/TypeScript/Java/.NET).
**Verification:** Replay the same event twice; confirm a single side effect. Inspect the DynamoDB
idempotency table for stored keys.
**Trade-offs:** Adds a DynamoDB dependency + read/write cost and TTL management.
**Source:** [Lambda best practices — Write idempotent code](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html) (living doc; accessed 2026-07-31).

### Pattern: Event source mapping tuning (batch size + batching window + partial batch response)
**Why:** Efficient stream/queue consumption; partial batch response avoids reprocessing an entire
batch when one record fails. Pillar: Performance Efficiency + Reliability.
**Provider Service:** AWS Lambda event source mapping (Amazon SQS, Amazon Kinesis, Amazon DynamoDB
Streams).
**Architecture Decision:** Tune `BatchSize` and batching window (up to 5 min / 6 MB payload) to poll
frequency; enable **partial batch response** for streams so only failed records are retried. For SQS
sources, ensure function timeout does not exceed the queue **Visibility Timeout**.
**Verification:** `aws lambda get-event-source-mapping`; CloudWatch `IteratorAge` alarm (e.g., 30000
ms) for Kinesis; confirm reported batch item failures.
**Trade-offs:** Larger batches raise per-invoke memory/latency; misconfigured visibility timeout →
duplicate invocations.
**Source:** [Lambda best practices — Working with streams](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html) (living doc; accessed 2026-07-31).

### Pattern: Dead-letter queues & Lambda destinations on async invocation
**Why:** Async invocation queues events internally and retries on failure; without a DLQ/destination,
exhausted events are silently dropped. Pillar: Reliability.
**Provider Service:** AWS Lambda async invocation → Amazon SQS / Amazon SNS (DLQ) or EventBridge/SQS
**on-failure destination**.
**Architecture Decision:** Configure an on-failure destination (or DLQ) plus `MaximumRetryAttempts`
and `MaximumEventAge` for every asynchronously-invoked function. Destinations capture full invocation
records (superset of DLQ behavior).
**Verification:** `aws lambda get-function-event-invoke-config` shows `DestinationConfig`,
`MaximumRetryAttempts`, `MaximumEventAgeInSeconds`. Confirm DLQ/destination receives a forced failure.
**Trade-offs:** Requires a downstream sink + monitoring; DLQ alone lacks the richer invocation-record
context that destinations provide.
**Source:** [Invoking a Lambda function asynchronously](https://docs.aws.amazon.com/lambda/latest/dg/invocation-async.html) (living doc; accessed 2026-07-31).

### Pattern: Reserved concurrency to protect downstream dependencies
**Why:** Lambda scales seamlessly but upstream/downstream systems (RDS, third-party APIs) may not.
Pillar: Reliability.
**Provider Service:** AWS Lambda reserved concurrency.
**Architecture Decision:** Set reserved concurrency to cap a function's scaling to what downstream
dependencies can absorb; combine with timeouts, retries, and **backoff with jitter**.
**Verification:** `aws lambda get-function-concurrency`; load test and confirm throttles at the cap.
**Trade-offs:** Reserved concurrency is subtracted from the account's unreserved pool; too low a cap
causes end-user throttling.
**Source:** [Lambda best practices — Function scalability](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html) (living doc; accessed 2026-07-31).

### Pattern: Least-privilege IAM execution roles
**Why:** Security pillar — reduce blast radius of a compromised function. Lens explicitly calls out
misconfigured permissions as a top serverless risk.
**Provider Service:** AWS IAM (per-function execution role).
**Architecture Decision:** One narrowly-scoped execution role **per function**; grant only the exact
actions/resources needed. Never attach broad managed policies (e.g., `*:*`).
**Verification:** IAM Access Analyzer; AWS Security Hub CSPM Lambda controls; review policy for
wildcards.
**Trade-offs:** More roles to author/maintain; requires policy iteration during development.
**Source:** [Lambda best practices — most-restrictive IAM](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html) + [Serverless Lens — Security pillar](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/security-pillar.html) (accessed 2026-07-31).

### Pattern: Secrets via AWS Secrets Manager / Parameter Store (never hard-coded)
**Why:** Security pillar — hard-coded credentials are an OWASP-class exposure. Lens: env vars for
operational params, secret stores for credentials.
**Provider Service:** AWS Secrets Manager or AWS Systems Manager Parameter Store; env vars for
non-secret config.
**Architecture Decision:** Store connection strings/API keys in Secrets Manager/Parameter Store; fetch
at cold start and cache in the (module-scope) execution environment; pass non-secret config as
environment variables.
**Verification:** Scan code/env for plaintext secrets; confirm the function role has scoped
`secretsmanager:GetSecretValue` on the specific secret ARN only.
**Trade-offs:** Secrets Manager adds per-secret + API cost; adds a fetch dependency at init.
**Source:** [Lambda best practices — environment variables & permissions](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html) (living doc; accessed 2026-07-31).

### Pattern: Observability — structured JSON logging, EMF metrics, X-Ray tracing
**Why:** Operational Excellence pillar. Structured logs are searchable; EMF emits metrics through logs
(async, low-latency) instead of synchronous CloudWatch API calls; X-Ray traces distributed calls.
**Provider Service:** Amazon CloudWatch Logs (Logs Insights), Embedded Metric Format, AWS X-Ray,
Powertools for AWS Lambda (Logger/Metrics/Tracer).
**Architecture Decision:** Emit structured JSON logs; use EMF for custom metrics; enable active X-Ray
tracing; alarm on CloudWatch metrics rather than emitting metrics from within handler code.
**Verification:** `aws lambda get-function-configuration` → `TracingConfig.Mode = Active`; confirm EMF
metric log lines; query Logs Insights.
**Trade-offs:** X-Ray and CloudWatch custom metrics add cost; sampling needed at high volume.
**Source:** [Lambda best practices — Metrics and alarms](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html) (living doc; accessed 2026-07-31).

### Pattern: Orchestrate with AWS Step Functions, not code-chained Lambdas
**Why:** Lens principle #5 — state-machine orchestration prevents monolithic, tightly-coupled flows
and provides built-in retry/catch/error handling. Pillar: Reliability + Operational Excellence.
**Provider Service:** AWS Step Functions (Standard or Express).
**Architecture Decision:** Model multi-step business processes as a state machine with `Retry`/`Catch`;
use `.sync`/`.waitForTaskToken` (Standard) for callback patterns.
**Verification:** Execution history in the Step Functions console / CloudWatch Logs; confirm no
Lambda-invokes-Lambda chaining remains.
**Trade-offs:** Standard billed per state transition; Express billed per execution/duration/memory.
Adds ASL authoring skill requirement.
**Source:** [Step Functions — Choosing workflow type](https://docs.aws.amazon.com/step-functions/latest/dg/choosing-workflow-type.html) + [Serverless Lens — Design principles](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/general-design-principles.html) (accessed 2026-07-31).

---

## Architectural Decisions

Target edition: reconciled with living AWS decision guides & service docs (accessed 2026-07-31).

### Decision: API front door — REST API vs HTTP API vs AppSync

**Options:**

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|------------|-----------|------------|-----------|
| REST API | Amazon API Gateway (REST) | API keys, per-client throttling/usage plans, request validation, AWS WAF, private endpoints, caching, X-Ray, edge-optimized | Higher price, higher latency, no built-in JWT authorizer | You need API management (keys, usage plans), WAF, request validation, or a private API |
| HTTP API | Amazon API Gateway (HTTP) | Lower price, lower latency, native JWT authorizer, automatic deployments, CORS | No API keys, no per-client rate limiting, no WAF, no caching, no request validation, no X-Ray | Simple, cost-sensitive Lambda/HTTP proxy APIs with JWT/OIDC auth |
| GraphQL | AWS AppSync | Single GraphQL endpoint, real-time subscriptions, per-field resolvers, client-driven queries | GraphQL learning curve, different auth/caching model | Mobile/web clients needing flexible queries, real-time data, or data aggregation |

**Cost Profile:** HTTP API < REST API for equivalent traffic; AppSync priced per query/resolver +
real-time connection minutes.
**Scaling Characteristics:** All three are managed and auto-scale; REST API caching offloads backend.
**Operational Burden:** REST API has the largest config surface (stages, models, usage plans); HTTP
API is leanest; AppSync requires GraphQL schema/resolver expertise.
**Lock-in Assessment:** All AWS-proprietary control planes; REST/HTTP expose standard REST so client
portability is high; AppSync (GraphQL) has AWS-specific resolver mapping.
**Ask The Architect:** *"Do you need API keys, per-client rate limiting, AWS WAF, request validation,
or private endpoints? If yes → REST API. If you just need a low-latency JWT-secured proxy → HTTP API.
If clients need flexible GraphQL queries or real-time subscriptions → AppSync."*
**Source:** [Choose between REST APIs and HTTP APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html) (living doc; accessed 2026-07-31).

### Decision: Messaging backbone — EventBridge vs SNS vs SQS vs Kinesis

**Options:**

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|------------|-----------|------------|-----------|
| Event bus | Amazon EventBridge | Content-based routing, 140+ event sources, cross-account, SaaS partners, schema registry | No ordering guarantees, no persistence | Event-driven architecture, routing by event content, cross-account/SaaS events |
| Pub/sub fan-out | Amazon SNS | Push to many subscribers (SQS, Lambda, HTTP, email, SMS); FIFO topics for ordering | No persistence (real-time only) | Fan-out one message to many consumers |
| Queue / buffer | Amazon SQS | Durable buffering, decoupling, pull-based back-pressure, FIFO ordering, DLQ | No routing/fan-out on its own | Decoupling producers/consumers, absorbing spikes, work queues |
| Stream | Amazon Kinesis Data Streams | Ordered, replayable, high-throughput shards, multiple consumers | Shard management, more ops overhead | Real-time analytics, ordered replayable event streams |

**Cost Profile:** EventBridge per event + target invocation; SNS per request/notification; SQS per
request + data; Kinesis per shard-hour + PUT payload units.
**Scaling Characteristics:** SQS/SNS/EventBridge auto-scale; Kinesis throughput scales linearly with
shard count (add shards, choose a good partition key).
**Operational Burden:** EventBridge/SNS/SQS are near-zero ops; Kinesis requires shard capacity
planning and IteratorAge monitoring.
**Lock-in Assessment:** All AWS-proprietary; SQS/SNS use standard queue/pub-sub semantics (moderate
portability); EventBridge rules and Kinesis are more AWS-specific.
**Ask The Architect:** *"Do you need routing by content (EventBridge), fan-out to many (SNS), durable
decoupling/buffering (SQS), or ordered replayable streams (Kinesis)? Combine them — e.g., SNS→SQS
fan-out, or EventBridge Pipes for point-to-point."*
**Source:** [AWS Decision Guide — SQS, SNS, or EventBridge?](https://docs.aws.amazon.com/decision-guides/latest/sns-or-sqs-or-eventbridge/sns-or-sqs-or-eventbridge.html) (Last updated **July 31, 2024** ⚠️ — >12 months but current stable guidance; accessed 2026-07-31).

### Decision: Step Functions Standard vs Express Workflows

**Options:**

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|------------|-----------|------------|-----------|
| Standard | AWS Step Functions (Standard) | Up to **1 year** duration, **exactly-once**, full execution history (90 days), `.sync`/`.waitForTaskToken`, Distributed Map | Higher per-transition cost, lower start rate | Long-running, auditable, **non-idempotent** actions (payments, EMR clusters) |
| Express (async) | AWS Step Functions (Express) | High-volume, **at-least-once**, no state-transition limit, cheap at scale | Max **5 min**, no `.sync`/callback, no Distributed Map/Activities, history only via CloudWatch Logs | High-throughput idempotent event processing (IoT/streaming) |
| Express (sync) | AWS Step Functions (Express, `StartSyncExecution`) | Request/response orchestration of microservices, **at-most-once** | Max 5 min; no auto-restart on exception | Synchronous microservice orchestration behind API Gateway/Lambda |

**Cost Profile:** Standard = per state transition; Express = per execution + duration + memory
(cheaper for high-volume short flows).
**Scaling Characteristics:** Express has no state-transition rate limit and scales on demand; Standard
is bounded by state-transition quotas.
**Operational Burden:** Express requires CloudWatch Logs for history (no built-in visual history);
Standard offers richer built-in debugging.
**Lock-in Assessment:** ASL is AWS-proprietary; workflow **type is immutable** after creation
(re-create to change).
**Ask The Architect:** *"Is the workflow long-running/auditable/non-idempotent (Standard) or a
high-volume idempotent flow under 5 minutes (Express)? Do you need a synchronous response
(Express Sync) or callbacks/`.sync` integrations (Standard only)?"*
**Source:** [Step Functions — Choosing workflow type](https://docs.aws.amazon.com/step-functions/latest/dg/choosing-workflow-type.html) (living doc; accessed 2026-07-31).

### Decision: Compute model — Lambda vs AWS Fargate vs Amazon ECS/EKS

**Options:**

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|------------|-----------|------------|-----------|
| FaaS | AWS Lambda | Zero-idle cost, event-driven, fast auto-scale, no server mgmt | **15-min max** execution, 6 MB sync payload, cold starts, /tmp limits | Event-driven, spiky, short tasks; glue between managed services |
| Serverless containers | AWS Fargate | Long-running, custom runtimes, larger resources, no node mgmt | Slower scale, pay while running, no scale-to-zero (without extra tooling) | Long-running services, large images, steady traffic |
| Managed containers | Amazon ECS / Amazon EKS | Full control, sidecars, daemonsets, cost at high steady utilization | You manage cluster/nodes (EC2 mode), most ops overhead | Complex orchestration, existing Kubernetes investment |

**Cost Profile:** Lambda cheapest for spiky/low-duty-cycle; Fargate/ECS cheaper at sustained high
utilization.
**Scaling Characteristics:** Lambda scales per-request in seconds; Fargate/ECS scale by task/pod
(slower).
**Operational Burden:** Lambda lowest; EKS highest.
**Lock-in Assessment:** Lambda most AWS-specific (handler model); containers (Fargate/ECS/EKS) are the
most portable.
**Ask The Architect:** *"Does the workload finish within 15 minutes and fit Lambda's resource/payload
limits? If it is long-running, needs large images, or steady high utilization → Fargate/ECS."*
**Source:** [Lambda best practices — quotas & scalability](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html) + [Lambda quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html) (living docs; accessed 2026-07-31).

### Decision: Cold start — on-demand vs provisioned concurrency vs SnapStart

**Options:**

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|------------|-----------|------------|-----------|
| On-demand | AWS Lambda (default) | Lowest cost (pay per invoke), no idle charge | Cold-start latency on scale-up | Async/batch, latency-tolerant, spiky traffic |
| Provisioned concurrency | AWS Lambda PC | Pre-initialized env → consistent low latency | Extra charge for pre-warmed capacity | Latency-sensitive synchronous APIs with predictable load |
| SnapStart | AWS Lambda SnapStart | Faster init from a cached snapshot (no per-hour PC charge) | Runtime/feature constraints; init-time snapshot semantics (idempotent init) | Reducing cold starts without paying for provisioned concurrency |

**Cost Profile:** On-demand cheapest; provisioned concurrency adds hourly pre-warm cost; SnapStart
avoids PC hourly charge.
**Scaling Characteristics:** PC handles requests up to the configured level then bursts to on-demand.
**Operational Burden:** PC requires capacity tuning + possibly Application Auto Scaling; SnapStart
requires snapshot-safe init code.
**Lock-in Assessment:** All AWS-Lambda-specific configuration.
**Ask The Architect:** *"Is p99 cold-start latency user-facing and unacceptable? If yes and load is
predictable → provisioned concurrency; if you want lower cost → evaluate SnapStart for the runtime.
Otherwise on-demand."*
**Source:** [Lambda best practices — Function scalability (provisioned concurrency, throttle
tolerance)](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html) + [Provisioned concurrency](https://docs.aws.amazon.com/lambda/latest/dg/provisioned-concurrency.html) (living docs; accessed 2026-07-31).

### Decision: Synchronous vs asynchronous invocation

**Options:**

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|------------|-----------|------------|-----------|
| Synchronous (RequestResponse) | Lambda via API Gateway/SDK | Immediate response, simple request/reply | Caller waits; throttling surfaces to client; retries are caller's job | User-facing APIs needing a response |
| Asynchronous (Event) | Lambda async + internal queue | Decoupling, built-in retries, DLQ/destinations | Eventual processing; needs idempotency + failure sinks | Background/event processing, fan-out, buffering |

**Cost Profile:** Comparable per-invoke; async adds DLQ/destination sink cost.
**Scaling Characteristics:** Async buffers via Lambda's internal queue (StatusCode 202) smoothing
spikes; sync throttles surface to the caller.
**Operational Burden:** Async requires DLQ/destination + idempotency design.
**Lock-in Assessment:** AWS-specific invocation semantics.
**Ask The Architect:** *"Does the caller need the result now (sync) or can processing happen in the
background with retries and a DLQ (async)?"*
**Source:** [Invoking a Lambda function asynchronously](https://docs.aws.amazon.com/lambda/latest/dg/invocation-async.html) (living doc; accessed 2026-07-31).

### Decision: Single-account vs multi-account serverless deployment

**Options:** Single account (simplest, shared blast radius) vs multi-account via AWS Organizations
(isolation per environment/team, consolidated billing, SCP guardrails).
**Cost Profile:** Multi-account has no direct surcharge; adds cross-account networking/ops overhead.
**Scaling Characteristics:** Per-account Lambda concurrency quotas isolate noisy neighbors in
multi-account.
**Operational Burden:** Multi-account requires landing-zone tooling (Control Tower), cross-account IAM.
**Lock-in Assessment:** AWS Organizations-specific.
**Ask The Architect:** *"Do compliance/isolation/quota-isolation needs justify multi-account with
Organizations, or is a single account with per-env stacks sufficient?"*
**Source:** [Serverless Lens — Security pillar (IAM)](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/security-pillar.html) (2022; accessed 2026-07-31). ⚠️ Multi-account specifics defer to the living AWS Organizations documentation.

---

## Anti-Patterns

Target edition: Serverless Lens (2022, current) + living Lambda docs (accessed 2026-07-31).

### Anti-Pattern: Lambda invoking Lambda synchronously (code-chained orchestration)
**Why:** Reliability + Operational Excellence pillars. Lens principle #5 — chaining Lambda executions
in code creates a monolithic, tightly-coupled app; the caller pays (double-billing) while blocked and
inherits the callee's failures.
**Risk Level:** HIGH
**Blast Radius:** Cascading failures and latency across the call chain; doubled compute cost.
❌ **Wrong:** `orderFunction` (AWS Lambda) synchronously `Invoke`s `paymentFunction` (AWS Lambda) and
blocks on the response, which in turn invokes `inventoryFunction`.
✅ **Correct:** Orchestrate with **AWS Step Functions** (state machine `Retry`/`Catch`), or decouple
via **Amazon EventBridge**/**Amazon SQS** between functions.
**Detection:** Grep function code for `lambda.invoke`/`InvocationType=RequestResponse`; X-Ray service
map showing Lambda→Lambda edges.
**Impact:** Cascading failure + cost overrun.
**Source:** [Serverless Lens — Design principles (#5)](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/general-design-principles.html) (accessed 2026-07-31).

### Anti-Pattern: Recursive / self-invoking functions without guardrails
**Why:** Cost + Reliability. A function that invokes itself (directly or via its own trigger) can run
away, causing an unbounded invocation storm and cost blow-up.
**Risk Level:** CRITICAL
**Blast Radius:** Account-wide concurrency exhaustion; runaway bill.
❌ **Wrong:** A Lambda writes to the same Amazon S3 bucket/prefix that triggers it, re-invoking itself
on every write.
✅ **Correct:** Break the cycle (write to a different bucket/prefix); if a runaway is detected, set
**reserved concurrency to `0`** immediately to throttle all invocations while fixing the code.
**Detection:** CloudWatch invocation-count spike; Lambda recursive-loop detection signals; Cost
Anomaly Detection alert.
**Impact:** Cost overrun + service outage.
**Source:** [Lambda best practices — Avoid recursive invocations](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html) (living doc; accessed 2026-07-31).

### Anti-Pattern: Storing state / user data in the execution environment
**Why:** Security + Reliability. "Share nothing" — environments are short-lived and reused across
invocations; storing user data risks cross-invocation data leaks.
**Risk Level:** HIGH
**Blast Radius:** Data leakage between users/requests; nondeterministic behavior.
❌ **Wrong:** Caching per-user session data in a module-level global that persists across warm
invocations.
✅ **Correct:** Persist state in **Amazon DynamoDB**/**Amazon ElastiCache**/**Amazon S3**; only cache
**immutable, non-user** assets in `/tmp` or module scope.
**Detection:** Code review for mutable global state keyed by request/user; concurrency stress test
observing cross-request bleed.
**Impact:** Data breach / compliance violation.
**Source:** [Lambda best practices — Function code (don't store user data in the environment)](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html) + [Serverless Lens — Design principles (#3)](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/general-design-principles.html) (accessed 2026-07-31).

### Anti-Pattern: Hard-coded credentials / connection strings in code
**Why:** Security pillar (OWASP-class). Secrets in code leak via source control and function packages.
**Risk Level:** CRITICAL
**Blast Radius:** Full credential compromise of downstream systems.
❌ **Wrong:** `const dbUrl = "postgres://admin:P@ss@prod-db..."` embedded in the Lambda package.
✅ **Correct:** Store in **AWS Secrets Manager** / **AWS Systems Manager Parameter Store**; fetch at
init with a scoped IAM permission; use environment variables for non-secret config only.
**Detection:** Secret scanning (git-secrets, Amazon CodeGuru/Inspector); review env/package for
plaintext secrets.
**Impact:** Data breach.
**Source:** [Lambda best practices — environment variables & permissions](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html) (living doc; accessed 2026-07-31).

### Anti-Pattern: Overly broad IAM permissions on execution roles
**Why:** Security pillar. Wildcard permissions turn a single compromised function into an
account-wide risk.
**Risk Level:** CRITICAL
**Blast Radius:** Lateral movement across the AWS account.
❌ **Wrong:** Execution role with `Action: "*"`, `Resource: "*"` (or broad `s3:*`, `dynamodb:*`).
✅ **Correct:** Per-function role scoped to exact actions and resource ARNs (e.g.,
`dynamodb:PutItem` on one table ARN).
**Detection:** IAM Access Analyzer; AWS Security Hub CSPM Lambda controls; policy wildcard scan.
**Impact:** Data breach / privilege escalation.
**Source:** [Lambda best practices — most-restrictive IAM permissions](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html) + [Serverless Lens — Security pillar](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/security-pillar.html) (accessed 2026-07-31).

### Anti-Pattern: Missing DLQ / destination on async invocations
**Why:** Reliability pillar. Without a failure sink, events that exhaust retries are dropped silently.
**Risk Level:** HIGH
**Blast Radius:** Silent data/event loss.
❌ **Wrong:** Async-invoked Lambda with no `DestinationConfig` and no DLQ; failed events vanish after
retries.
✅ **Correct:** Configure an **on-failure destination** (Amazon SQS/EventBridge) or DLQ plus
`MaximumRetryAttempts` and `MaximumEventAge`.
**Detection:** `aws lambda get-function-event-invoke-config` shows no `DestinationConfig`; force a
failure and confirm nothing is captured.
**Impact:** Silent data loss.
**Source:** [Invoking a Lambda function asynchronously](https://docs.aws.amazon.com/lambda/latest/dg/invocation-async.html) (living doc; accessed 2026-07-31).

### Anti-Pattern: Using Lambda for long-running workloads (>15 min)
**Why:** Reliability + Performance. Lambda hard-caps at a 15-minute timeout; long jobs will be killed
mid-execution.
**Risk Level:** MEDIUM
**Blast Radius:** Truncated jobs, partial state, retries.
❌ **Wrong:** A single Lambda running a 40-minute batch/ETL job.
✅ **Correct:** Use **AWS Step Functions** (Standard, up to 1 year) to chunk the work, or run it on
**AWS Fargate**/**Amazon ECS**; use Step Functions **Distributed Map** for large-scale parallelism.
**Detection:** CloudWatch `Duration` approaching timeout; `Task timed out` errors.
**Impact:** Service outage / incomplete processing.
**Source:** [Lambda quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html) + [Step Functions — Choosing workflow type](https://docs.aws.amazon.com/step-functions/latest/dg/choosing-workflow-type.html) (living docs; accessed 2026-07-31).

### Anti-Pattern: Unbounded concurrency without reserved concurrency
**Why:** Reliability. Lambda out-scales fragile downstream systems (RDS connection pools, third-party
APIs), causing downstream collapse.
**Risk Level:** HIGH
**Blast Radius:** Downstream dependency saturation → cascading outage.
❌ **Wrong:** A Lambda hitting an RDS instance with no reserved-concurrency cap, opening thousands of
connections under a spike.
✅ **Correct:** Set **reserved concurrency** to the downstream's safe limit; add **timeouts, retries,
backoff with jitter**; use **Amazon RDS Proxy** for connection pooling.
**Detection:** Downstream connection/error spikes; CloudWatch `ConcurrentExecutions` vs downstream
capacity.
**Impact:** Cascading failure.
**Source:** [Lambda best practices — Function scalability](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html) (living doc; accessed 2026-07-31).

### Anti-Pattern: No X-Ray tracing / no structured observability in production
**Why:** Operational Excellence. Without tracing you cannot diagnose distributed latency/failures.
**Risk Level:** MEDIUM
**Blast Radius:** Extended MTTR; blind spots in incident response.
❌ **Wrong:** Production Lambdas with `TracingConfig.Mode = PassThrough`, unstructured `print` logs,
and metrics emitted via synchronous CloudWatch API calls in the handler.
✅ **Correct:** Enable **active AWS X-Ray** tracing, **structured JSON logging** (Powertools Logger),
and **EMF** for metrics; alarm on CloudWatch metrics.
**Detection:** `aws lambda get-function-configuration` → `TracingConfig.Mode`; check for JSON logs +
EMF lines.
**Impact:** Prolonged outage / slow incident response.
**Source:** [Lambda best practices — Metrics and alarms](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html) (living doc; accessed 2026-07-31).

### Anti-Pattern: Monolithic "God function"
**Why:** Operational Excellence + Performance. A function handling many responsibilities is hard to
scale, secure (over-broad IAM), and cold-start-optimize.
**Risk Level:** MEDIUM
**Blast Radius:** Whole-feature coupling; over-privileged role; heavy cold starts.
❌ **Wrong:** One Lambda with a giant `switch(event.type)` handling orders, payments, and inventory.
✅ **Correct:** Decompose into single-responsibility functions; route with **Amazon EventBridge** and
orchestrate with **AWS Step Functions**.
**Detection:** Handler size/branching review; one role with many unrelated permissions.
**Impact:** Reduced reliability + security blast-radius growth.
**Source:** [Serverless Lens — Design principles (#1, #5)](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/general-design-principles.html) (accessed 2026-07-31).

### Anti-Pattern: Ignoring idempotency / missing retry design
**Why:** Reliability. Async invocation and event source mappings are **at-least-once**; non-idempotent
handlers double-charge, duplicate records, or corrupt state on redelivery.
**Risk Level:** HIGH
**Blast Radius:** Duplicate side effects (double payments, duplicate rows).
❌ **Wrong:** A payment handler that charges a card on every delivery of the same event, with no
dedupe.
✅ **Correct:** Idempotency key persisted in **Amazon DynamoDB** (Powertools Idempotency utility);
retries with backoff/jitter for downstream calls.
**Detection:** Replay an event twice; confirm a single side effect; inspect the idempotency table.
**Impact:** Data corruption / financial loss.
**Source:** [Lambda best practices — Write idempotent code](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html) + [Serverless Lens — Design principles (#7)](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/general-design-principles.html) (accessed 2026-07-31).

---

## Service Equivalence

**Scope note & sourcing caveat:** AWS does not publish an official cross-cloud equivalence table
(that would violate the Source Hierarchy if sourced to third parties). The mappings below use each
provider's **official product names** and represent **architectural role equivalence**, *not*
feature parity. Treat non-AWS entries as "closest managed equivalent," to be verified against each
provider's own current docs before design decisions.

### Compute (FaaS)
| Role | AWS | Google Cloud | Microsoft Azure | Oracle Cloud (OCI) |
|------|-----|-------------|-----------------|--------------------|
| Functions-as-a-Service | AWS Lambda | Cloud Run functions (formerly Cloud Functions) | Azure Functions | OCI Functions (Fn Project-based) |

### API management / front door
| Role | AWS | Google Cloud | Microsoft Azure | Oracle Cloud (OCI) |
|------|-----|-------------|-----------------|--------------------|
| Managed API gateway | Amazon API Gateway | Google Cloud API Gateway / Apigee | Azure API Management | OCI API Gateway |

### Workflow orchestration
| Role | AWS | Google Cloud | Microsoft Azure | Oracle Cloud (OCI) |
|------|-----|-------------|-----------------|--------------------|
| Serverless orchestration | AWS Step Functions | Google Cloud Workflows | Azure Logic Apps / Durable Functions | OCI Functions + OCI Streaming (no direct managed equivalent) ⚠️ |

### Event routing / eventing
| Role | AWS | Google Cloud | Microsoft Azure | Oracle Cloud (OCI) |
|------|-----|-------------|-----------------|--------------------|
| Event bus / routing | Amazon EventBridge | Eventarc | Azure Event Grid | OCI Events |

### Messaging / queuing
| Role | AWS | Google Cloud | Microsoft Azure | Oracle Cloud (OCI) |
|------|-----|-------------|-----------------|--------------------|
| Managed queue | Amazon SQS | Cloud Tasks (task queue) / Pub/Sub | Azure Service Bus / Storage Queues | OCI Queue |
| Pub/sub | Amazon SNS | Google Cloud Pub/Sub | Azure Event Grid / Service Bus topics | OCI Notifications |
| Streaming | Amazon Kinesis Data Streams | Google Cloud Pub/Sub / Dataflow | Azure Event Hubs | OCI Streaming |

⚠️ **Verification required:** These equivalences are directional. Notably, OCI has no single managed
Step Functions equivalent (composed from OCI Functions + OCI Streaming/Events), and GCP's Pub/Sub
spans both messaging and streaming roles. Validate against each provider's current official
documentation before committing to a portability strategy.

---

## Reference Architectures

Target edition: patterns assembled from living AWS service docs (accessed 2026-07-31).
Canonical diagrams: [AWS Serverless architecture patterns](https://aws.amazon.com/architecture/serverless/).

### 1. Web application backend (synchronous request/response)
**Flow:** Client → **Amazon API Gateway** (REST or HTTP API) → **AWS Lambda** (single-responsibility)
→ **Amazon DynamoDB**.
**Key decisions:** HTTP API for low-latency JWT-secured proxy; REST API when API keys/WAF/request
validation/caching are required. Lambda execution role scoped to the specific DynamoDB table ARN.
Enable X-Ray (REST API + Lambda). Consider provisioned concurrency/SnapStart for latency-sensitive
endpoints.
**Sources:** [REST vs HTTP API](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html); [Lambda best practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html) (accessed 2026-07-31).

### 2. Event processing pipeline (asynchronous, decoupled)
**Flow:** Event source → **Amazon EventBridge** (content-based routing) → **Amazon SQS** (buffer /
back-pressure) → **AWS Lambda** (idempotent consumer) → **Amazon SNS** (fan-out notifications).
Failures → **on-failure destination / DLQ (Amazon SQS)**.
**Key decisions:** EventBridge for routing by content; SQS to absorb spikes and decouple; reserved
concurrency to protect downstream; idempotent handler (DynamoDB idempotency key); DLQ + partial batch
response. Ensure Lambda timeout ≤ SQS visibility timeout.
**Sources:** [SQS/SNS/EventBridge decision guide](https://docs.aws.amazon.com/decision-guides/latest/sns-or-sqs-or-eventbridge/sns-or-sqs-or-eventbridge.html) (Last updated July 31, 2024 ⚠️); [Lambda async invocation](https://docs.aws.amazon.com/lambda/latest/dg/invocation-async.html); [Lambda best practices — streams](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html) (accessed 2026-07-31).

### 3. Workflow orchestration (stateful, multi-step)
**Flow:** Trigger (**Amazon API Gateway** or **Amazon EventBridge**) → **AWS Step Functions**
(Standard for durable/non-idempotent; Express for high-volume idempotent) → **AWS Lambda** task states
→ **Amazon S3** (artifacts) with `Retry`/`Catch` and callback (`.waitForTaskToken`) where needed.
**Key decisions:** Standard for auditable, long-running (up to 1 year), exactly-once,
non-idempotent steps (e.g., payments); Express for sub-5-minute high-throughput idempotent flows;
Distributed Map (Standard only) for large-scale parallel S3 processing. Workflow type is **immutable**
— choose deliberately.
**Sources:** [Step Functions — Choosing workflow type](https://docs.aws.amazon.com/step-functions/latest/dg/choosing-workflow-type.html); [Serverless Lens — Design principles (#5)](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/general-design-principles.html) (accessed 2026-07-31).

---

## Source Bibliography

### Primary — AWS Well-Architected Serverless Applications Lens (Publication July 14, 2022 ⚠️ — current edition)
- [Serverless Applications Lens — Welcome](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/welcome.html) — Publication date July 14, 2022; accessed 2026-07-31.
- [Serverless Lens — Design principles](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/general-design-principles.html) — 2022 edition; accessed 2026-07-31.
- [Serverless Lens — The pillars](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/the-pillars-of-the-well-architected-framework.html) — 2022 edition; accessed 2026-07-31.
- [Serverless Lens — Security pillar](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/security-pillar.html) — 2022 edition; accessed 2026-07-31.
- [Serverless Lens — Reliability pillar](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/reliability-pillar.html) — 2022 edition; accessed 2026-07-31.

### Primary — Living AWS service documentation (current; accessed 2026-07-31)
- [AWS Lambda — Best practices for working with functions](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html) — living doc; accessed 2026-07-31.
- [AWS Lambda — Invoking a function asynchronously (DLQ/destinations/retries)](https://docs.aws.amazon.com/lambda/latest/dg/invocation-async.html) — living doc; accessed 2026-07-31.
- [Amazon API Gateway — Choose between REST APIs and HTTP APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html) — living doc; accessed 2026-07-31.
- [AWS Step Functions — Choosing workflow type (Standard vs Express)](https://docs.aws.amazon.com/step-functions/latest/dg/choosing-workflow-type.html) — living doc; accessed 2026-07-31.
- [AWS Decision Guide — SQS, SNS, or EventBridge?](https://docs.aws.amazon.com/decision-guides/latest/sns-or-sqs-or-eventbridge/sns-or-sqs-or-eventbridge.html) — Last updated July 31, 2024 ⚠️ (>12 months, current stable); accessed 2026-07-31.

### Secondary — AWS reference (living portals)
- [AWS Serverless architecture patterns portal](https://aws.amazon.com/architecture/serverless/) — living portal (undated); accessed 2026-07-31. ⚠️ Not individually date-stamped.
- [AWS Lambda quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html) — living doc; accessed 2026-07-31.
- [AWS Lambda — Provisioned concurrency](https://docs.aws.amazon.com/lambda/latest/dg/provisioned-concurrency.html) — living doc; accessed 2026-07-31.

### Referenced AWS tooling (from official docs)
- Powertools for AWS Lambda (Idempotency, Logger, Metrics, Batch) — referenced from the Lambda best-practices page; accessed 2026-07-31.
- AWS Security Hub CSPM Lambda controls; Amazon GuardDuty Lambda Protection — referenced from the Lambda best-practices page; accessed 2026-07-31.

### Excluded (Source Hierarchy — rejected)
- Third-party serverless cost/feature comparison blogs — **not authoritative**; used only to confirm official cross-provider product names, never for claims.

---

## Research Gaps & Unverified Items

- ⚠️ **No "2025" Serverless Lens exists.** The current published Serverless Applications Lens is dated July 14, 2022. All "current" behavior in this document is sourced to living service docs.
- ⚠️ **Sustainability & Cost pillar serverless specifics** summarized from the pillar index; validate against the living Well-Architected Framework if deep sustainability guidance is required.
- ⚠️ **Cross-provider equivalence** is directional (architectural role), not feature-parity, and is unverified against non-AWS official docs in this pass. Verify against Google Cloud, Azure, and OCI official documentation before portability decisions.
- ⚠️ **SnapStart runtime support and constraints** referenced at high level; confirm current supported runtimes in the living Lambda SnapStart documentation for your language.
- **Recommended next step:** run `/skill-best-practices-validator` on any skill authored from this research, and re-verify the 2022 Lens links against any future Serverless Lens re-publication.
