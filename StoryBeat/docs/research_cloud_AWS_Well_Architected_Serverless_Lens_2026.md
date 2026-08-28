# AWS Well-Architected Framework — Serverless Applications Lens (Research Knowledge Base)

## Metadata

```yaml
Full_Name: "AWS Well-Architected Framework — Serverless Applications Lens"
Cloud_Provider: "AWS"
Architecture_Domain: "Well-Architected Framework - Serverless Lens"
Target_Edition: "AWS Well-Architected Serverless Lens 2026"
Architecture_Context: "General-purpose serverless production workloads (not specified in request)"
Official_Source_URL: "https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-08-27"
Research_Depth: "exhaustive (default)"
Currency_Threshold: "2027-08-27 — review after this date"
```

> ## ⚠️⚠️ CRITICAL CURRENCY / VERSION WARNING — READ FIRST
>
> The requested `TARGET_EDITION` "AWS Well-Architected Serverless Lens 2026" **does not correspond to a
> 2026 content revision.** Verification of the official source revealed:
>
> - The **PDF carries a 2026 copyright stamp**, but this is an auto-updated boilerplate year, **not** a
>   content revision date.
> - The **HTML content publication date is `July 14, 2022`** (source:
>   [welcome.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/welcome.html),
>   accessed 2026-08-27). This is the most recent substantive revision of the Serverless Applications Lens.
>
> **Consequence per this project's Version Absolutism + 12-month-currency rules:** the entire body of
> this lens is **>12 months old** (≈4 years). Every pattern below is sourced from the July-2022 content
> and is tagged accordingly. Serverless capabilities that AWS released *after* July 2022 (e.g., Lambda
> SnapStart for Java, Lambda function recursion detection, expanded arm64/Graviton guidance, updated
> Powertools for AWS Lambda, Lambda response streaming, provisioned-concurrency and pricing changes) are
> **NOT reflected in this lens** and must be independently verified before use. See
> [§ Migration Notes](#migration-notes--post-2022-gaps) for the specific gaps.
>
> **Recommendation:** Treat this as "Serverless Lens (2022 content, 2026 copyright)". If your organization
> requires a genuinely current serverless best-practices baseline, supplement this lens with the current
> AWS Lambda Developer Guide, the AWS Prescriptive Guidance serverless patterns, and the "Building
> Well-Architected Serverless Applications" AWS Compute Blog series (2019–2021).

---

## Executive Summary

The **Serverless Applications Lens** is an official *lens* extension of the AWS Well-Architected
Framework. A "lens" narrows the six Well-Architected pillars (Operational Excellence, Security,
Reliability, Performance Efficiency, Cost Optimization, Sustainability) to a specific technology domain —
here, serverless workloads built on managed, event-driven, pay-per-value AWS services (AWS Lambda, Amazon
API Gateway, AWS Step Functions, Amazon DynamoDB, Amazon SQS/SNS/EventBridge/Kinesis, Amazon Cognito, and
edge services). The lens deliberately covers **only the serverless-specific guidance**; the base
Well-Architected Framework whitepaper still applies for everything not restated
([welcome.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/welcome.html), 2022-07-14).

**What "changed" in the "2026" edition:** effectively nothing at the content level. The lens content is
dated **July 14, 2022**; the "2026" is a PDF copyright artifact only (see the critical warning above). The
lens still documents five core layers (compute, data, messaging & streaming, user management & identity,
edge) plus systems monitoring/deployment, and six reference scenarios (RESTful microservices, Alexa
skills, mobile backend, streaming processing, web application, event-driven architectures). Notably, the
lens's Sustainability pillar guidance is thin, and Incident Response / Change Management defer entirely to
the base framework ("There are no operational practices unique to serverless applications for this best
practice" — [change-management.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/change-management.html)).

**Three most critical guardrails for general serverless production workloads:** (1) **Least-privilege,
one-IAM-role-per-function** — sharing an IAM role across Lambda functions "will likely violate
least-privileged access" ([identity-and-access-management.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/identity-and-access-management.html)).
(2) **Design for failures and duplicates (idempotency + dead-letter queues)** — operations must be
idempotent because events can be delivered more than once, and failed async transactions must land in a
DLQ ([general-design-principles.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/general-design-principles.html),
[failure-management.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/failure-management.html)).
(3) **Orchestrate with state machines, not chained functions** — chaining Lambda invocations in code
produces a "monolithic and tightly coupled application"; use AWS Step Functions instead
([general-design-principles.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/general-design-principles.html)).

---

## Cloud Architecture Glossary

```
Term: Serverless Applications Lens
Definition: A domain-specific extension of the AWS Well-Architected Framework that applies the six pillars to serverless workloads, covering only serverless-specific best practices.
Provider Docs Section: welcome.html
Architect Usage: Use alongside (not instead of) the base Well-Architected Framework whitepaper.
Common Confusion: Confused with the base WAF; the Lens omits any guidance already covered generally.
```
```
Term: Concurrency (vs. total requests)
Definition: The number of in-flight (simultaneous) function executions. Serverless design tradeoffs are evaluated on concurrency, not total request count.
Provider Docs Section: general-design-principles.html ("Think concurrent requests, not total requests")
Architect Usage: Size reserved/provisioned concurrency and downstream capacity against peak concurrent executions.
Common Confusion: Treating Lambda scaling as request-per-second capacity rather than concurrent-execution capacity.
```
```
Term: Reserved Concurrency
Definition: A per-function cap that guarantees (and limits) a function's share of the account concurrency pool.
Provider Docs Section: reliability / metrics pages (Throttles, ConcurrentExecutions)
Architect Usage: Protect critical functions and prevent one function from starving others in the account.
Common Confusion: Confused with Provisioned Concurrency (which pre-warms environments to remove cold starts).
```
```
Term: Provisioned Concurrency
Definition: Pre-initialized Lambda execution environments kept warm to eliminate cold-start latency for latency-sensitive workloads.
Provider Docs Section: selection.html; metrics (ProvisionedConcurrencySpilloverInvocations)
Architect Usage: Enable for user-facing, latency-sensitive functions; monitor spillover.
Common Confusion: Confused with Reserved Concurrency; it removes cold starts but adds always-on cost.
```
```
Term: Cold Start
Definition: The latency incurred when Lambda initializes a new execution environment (download code, start runtime, run static init) before handling a request.
Provider Docs Section: selection.html / performance-efficiency.html
Architect Usage: Optimize static initialization, minimize package/dependencies, consider provisioned concurrency.
Common Confusion: Assuming cold starts affect every invocation — they affect only new environments.
```
```
Term: Dead-Letter Queue (DLQ)
Definition: A dedicated queue (Amazon SQS or SNS) that retains failed asynchronous transactions for investigation and retry.
Provider Docs Section: failure-management.html
Architect Usage: Configure per-function DLQ / "Destination on Failure" for async and stream sources.
Common Confusion: Confused with Lambda "Destinations" (on-success/on-failure routing), which supersede legacy DLQ config.
```
```
Term: Idempotency
Definition: The property that an operation produces the same result whether executed once or multiple times, required because events may be delivered more than once.
Provider Docs Section: general-design-principles.html ("Design for failures and duplicates")
Architect Usage: Use idempotency keys / conditional writes (DynamoDB) so retried events do not double-process.
Common Confusion: Assuming exactly-once delivery from event sources.
```
```
Term: Lambda Authorizer
Definition: An Amazon API Gateway authorization mechanism that invokes a Lambda function to authenticate/validate a caller against a custom IdP or token.
Provider Docs Section: identity-and-access-management.html (SEC 1)
Architect Usage: Use for custom auth logic; can be shared cross-account to centralize authorization.
Common Confusion: Confused with API Keys, which are NOT an auth mechanism (usage tracking only).
```
```
Term: EMF (CloudWatch Embedded Metric Format)
Definition: A log format that lets Lambda emit custom metrics embedded in structured logs, processed asynchronously by CloudWatch with no performance impact.
Provider Docs Section: opex-metrics-and-alerts.html
Architect Usage: Emit custom metrics when Powertools is unavailable for your runtime.
Common Confusion: Confused with the CloudWatch PutMetricData API (synchronous, higher latency/cost).
```
```
Term: Powertools for AWS Lambda
Definition: AWS-maintained developer libraries that standardize structured logging, custom metrics, and tracing across supported runtimes.
Provider Docs Section: opex-logging.html / opex-metrics-and-alerts.html (referenced as "Lambda Powertools")
Architect Usage: Adopt to enforce structured JSON logs, correlation IDs, and EMF metrics consistently.
Common Confusion: The lens calls it "Lambda Powertools"; the current product name is "Powertools for AWS Lambda".
```
```
Term: Step Functions Express vs. Standard Workflows
Definition: Two Step Functions execution models — Express (high-volume, short-duration, at-least-once, cheaper per transition) vs. Standard (durable, long-running, exactly-once, auditable).
Provider Docs Section: failure-management.html / selection.html
Architect Usage: Express for short synchronous/async high-volume; Standard for long-running durable audited workflows.
Common Confusion: Assuming Express provides exactly-once durability like Standard.
```
```
Term: IteratorAge
Definition: A CloudWatch metric for stream-based (Kinesis/DynamoDB Streams) Lambda invocations indicating how far behind the consumer is.
Provider Docs Section: opex-metrics-and-alerts.html
Architect Usage: Alarm on IteratorAge to detect stream consumer lag / poison-pill stalls.
Common Confusion: Confused with SQS ApproximateAgeOfOldestMessage (queue-based, not stream-based).
```
```
Term: Enhanced Fan-Out (Kinesis)
Definition: A Kinesis Data Streams feature providing dedicated read throughput per consumer for multi-consumer scenarios.
Provider Docs Section: selection.html (PER 1)
Architect Usage: Use when multiple consumers read the same stream and share-throughput contention occurs.
Common Confusion: Assuming standard shared-throughput reads scale for many consumers.
```

---

## Architecture Guardrails

### ✅ Mandatory Patterns

**1. One least-privilege IAM role per Lambda function**
- Pillar Alignment: Security (SEC 2 — security boundaries)
- Why: "Sharing an IAM role within more than one Lambda function will likely violate least-privileged access." Smaller functions with scoped activities contribute to a well-architected serverless application ([identity-and-access-management.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/identity-and-access-management.html)).
- AWS Services: AWS IAM, AWS Lambda.
- Architecture Decision: Each function gets a dedicated execution role granting only the specific actions/resources it needs; use tag-based access control for API-level granularity.
- Verification: `aws iam list-roles` + review per-function role policies; IAM Access Analyzer to detect over-broad grants; check no two functions share one role.
- Source: [identity-and-access-management.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/identity-and-access-management.html) (2022-07-14) `[✓✓ Triangulated | Lens SEC 2 + AWS Lambda security best practices]`

**2. Control API access with a real authorization mechanism (not API keys)**
- Pillar Alignment: Security (SEC 1 — control access to your serverless API)
- Why: Five valid API Gateway auth mechanisms exist — AWS_IAM, Amazon Cognito user pools, Lambda authorizer, resource policies, and mutual TLS. "API Gateway API Keys is not a security mechanism and should not be used for authorization unless it's a public API" ([identity-and-access-management.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/identity-and-access-management.html)).
- AWS Services: Amazon API Gateway, AWS IAM/STS, Amazon Cognito, AWS Lambda (authorizer), AWS WAF.
- Architecture Decision: Choose AWS_IAM for in-AWS callers, Cognito user pools for end users/social IdP, Lambda authorizer for custom/external IdP, resource policies to restrict by account/IP/VPCE, and mTLS for IoT/app-to-app. Layer AWS WAF managed rule groups (SQLi/XSS) in front.
- Verification: Inspect each API method's `authorizationType`; confirm WAF WebACL associated; confirm API keys are not the sole gate.
- Source: [identity-and-access-management.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/identity-and-access-management.html) (2022-07-14)

**3. Orchestrate workflows with AWS Step Functions state machines, not chained Lambda code**
- Pillar Alignment: Operational Excellence / Reliability (general design principle)
- Why: "Chaining Lambda executions within the code to orchestrate the workflow … results in a monolithic and tightly coupled application. Instead, use a state machine to orchestrate transactions and communication flows" ([general-design-principles.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/general-design-principles.html)).
- AWS Services: AWS Step Functions (Standard & Express), AWS Lambda.
- Architecture Decision: Move retry/back-off/try-catch/saga rollback logic out of function code into Step Functions; pick Express for short high-volume, Standard for durable long-running/audited workflows.
- Verification: Review whether functions invoke other functions directly (anti-pattern) vs. Step Functions state definitions; check for saga/DLQ steps.
- Source: [general-design-principles.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/general-design-principles.html), [failure-management.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/failure-management.html) (2022-07-14) `[✓✓ Triangulated | Lens design principles + failure-management]`

**4. Design idempotent operations and capture async failures in a DLQ**
- Pillar Alignment: Reliability (failure management) + design principle "Design for failures and duplicates"
- Why: "Operations triggered from requests or events must be idempotent, as failures can occur and a given request or event can be delivered more than once." Failed async transactions "should be captured and retried whenever possible. Otherwise, data loss can occur" ([general-design-principles.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/general-design-principles.html), [failure-management.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/failure-management.html)).
- AWS Services: AWS Lambda (Maximum Retry Attempts, Maximum Record Age, Destination on Failure, Bisect Batch on Function Error), Amazon SQS (DLQ), Amazon Kinesis / DynamoDB Streams, AWS Step Functions.
- Architecture Decision: Attach per-function SQS DLQ; set retry/record-age controls; for Kinesis/DynamoDB Streams handle poison pills via bisect-batch and DLQ; inspect partial-failure responses (`PutRecords`, `BatchWriteItem`).
- Verification: Confirm DLQ / on-failure destination configured per async function; test duplicate-event handling.
- Source: [failure-management.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/failure-management.html) (2022-07-14)

**5. Structured JSON logging with correlation IDs**
- Pillar Alignment: Operational Excellence (Operate — centralized/structured logging)
- Why: "Unstructured logging using `print` or `console.log` statements is unfavorable." Structured JSON is auto-discovered by CloudWatch Logs Insights; correlation IDs enable end-to-end request tracing ([opex-logging.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/opex-logging.html)).
- AWS Services: Amazon CloudWatch Logs, CloudWatch Logs Insights, Powertools for AWS Lambda ("Lambda Powertools").
- Architecture Decision: Emit JSON logs including timestamp, level, service, function name, request ID, cold_start flag, correlation ID; propagate correlation ID and log level to downstream services; sample DEBUG logs at scale.
- Verification: Query logs in CloudWatch Logs Insights (fields auto-discovered); confirm correlation IDs present across services.
- Source: [opex-logging.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/opex-logging.html) (2022-07-14)

**6. Distributed tracing with AWS X-Ray active tracing**
- Pillar Alignment: Operational Excellence (Operate — distributed tracing)
- Why: "Active tracing with AWS X-Ray should be enabled to provide distributed tracing capabilities as well as to enable visual service maps for faster troubleshooting" ([opex-distributed-tracing.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/opex-distributed-tracing.html)).
- AWS Services: AWS X-Ray (active tracing, service maps, subsegments, annotations).
- Architecture Decision: Enable active tracing on Lambda; add subsegments for external dependencies and annotations (indexed key-value pairs) for business transactions; tune socket read/write timeouts to fail fast.
- Verification: Confirm `TracingConfig=Active` on functions; inspect X-Ray service map for full-path coverage.
- Source: [opex-distributed-tracing.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/opex-distributed-tracing.html) (2022-07-14)

**7. Comprehensive CloudWatch metrics + tiered alarms**
- Pillar Alignment: Operational Excellence (Operate — metrics and alerts)
- Why: The lens prescribes four metric tiers (Business, Customer experience, System, Operational) and both individual- and aggregate-level CloudWatch alarms with an explicit per-service metric list ([opex-metrics-and-alerts.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/opex-metrics-and-alerts.html)).
- AWS Services: Amazon CloudWatch (metrics, alarms, dashboards, EMF), Powertools for AWS Lambda.
- Architecture Decision: Alarm on Lambda `Duration`, `Errors`, `Throttles`, `ConcurrentExecutions`; stream `IteratorAge`; async `DeadLetterErrors`; provisioned `ProvisionedConcurrencySpilloverInvocations`; API Gateway `IntegrationLatency`, `Latency`, `5XXError`; SQS `ApproximateAgeOfOldestMessage`; DynamoDB throttle metrics; Step Functions `ExecutionsFailed`/`ExecutionThrottled`; EventBridge `FailedInvocations`/`ThrottledRules`.
- Verification: Review CloudWatch alarm inventory against the lens metric list per service in use.
- Source: [opex-metrics-and-alerts.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/opex-metrics-and-alerts.html) (2022-07-14)

**8. Encrypt sensitive data before it reaches logs/persistence; validate all input**
- Pillar Alignment: Security (Data protection SEC 3 + application security)
- Why: Request paths/query strings in URLs "might not" be encrypted and can leak into CloudWatch Logs; "We strictly advise against sending, logging, and storing unencrypted sensitive data." API Gateway request validation should be the first step; secrets belong in a rotating secrets manager ([data-protection.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/data-protection.html)).
- AWS Services: AWS KMS (encryption at rest for DynamoDB/OpenSearch/S3), AWS Secrets Manager, Amazon API Gateway (request validation, access logs), AWS Signer (code signing).
- Architecture Decision: Encrypt sensitive payloads client-side or before processing; enable encryption at rest on all data stores; use API Gateway JSON-schema request validation + deep app-level validation; store secrets in Secrets Manager with rotation and audited access; sign Lambda code with AWS Signer.
- Verification: Confirm encryption-at-rest on S3/DynamoDB/OpenSearch; confirm request validators on API methods; confirm no secrets in env vars/code; confirm code signing config.
- Source: [data-protection.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/data-protection.html) (2022-07-14)

### ⚠️ Architectural Decisions

**Decision — Compute/orchestration provisioning model per function**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | On-demand Lambda | AWS Lambda | Cost (pay-per-use, free when idle) | Cold-start latency on new environments | Spiky/unpredictable traffic |
  | Provisioned Concurrency | AWS Lambda | Predictable low latency (no cold starts) | Always-on cost even when idle | Latency-sensitive, steady user-facing APIs |
  | Reserved Concurrency | AWS Lambda | Blast-radius isolation, throttle protection | Caps max throughput of the function | Protecting critical fns / limiting noisy fns |

- Cost Profile: On-demand cheapest at rest; Provisioned adds standing cost; billing is per-1ms so faster init = cheaper.
- Lock-in Assessment: High AWS coupling (Lambda-specific config); portable via container image packaging but runtime model differs.
- Architect Instruction: "Ask whether the function is latency-sensitive and steady (→ provisioned concurrency) or spiky/background (→ on-demand), and whether it needs isolation from account-level throttling (→ reserved concurrency)."
- Source: [selection.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/selection.html) (2022-07-14)

**Decision — Step Functions workflow type**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Express (Sync/Async) | AWS Step Functions | High volume, low per-transition cost | Durability, exactly-once, long duration | Short-running high-volume orchestration |
  | Standard | AWS Step Functions | Durability, audit, long-running, exactly-once | Higher per-transition cost | Long-running audited business workflows |

- Cost Profile: Express billed by duration/memory (cheaper at high volume); Standard billed per state transition.
- Lock-in Assessment: Step Functions ASL is AWS-proprietary.
- Architect Instruction: "Ask the expected execution duration, volume, and durability/audit requirements before choosing Express vs. Standard."
- Source: [failure-management.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/failure-management.html), [selection.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/selection.html) (2022-07-14)

**Decision — API Gateway endpoint type & DynamoDB capacity mode**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Edge-optimized endpoint | Amazon API Gateway | Latency for geographically dispersed clients | Regional control | Global consumer base |
  | Regional endpoint | Amazon API Gateway | In-region latency / same-Region AWS calls | Global edge acceleration | Regional consumers / AWS-internal callers |
  | DynamoDB on-demand | Amazon DynamoDB | Zero capacity planning | Higher unit cost at steady high load | Unpredictable traffic |
  | DynamoDB provisioned | Amazon DynamoDB | Lower cost at consistent load | Requires capacity planning/auto-scaling | Predictable consistent traffic |

- Cost Profile: On-demand DynamoDB costs more per request but avoids over-provisioning; provisioned cheaper when utilization is high/steady.
- Lock-in Assessment: DynamoDB is AWS-proprietary NoSQL; migration requires schema/access-pattern redesign.
- Architect Instruction: "Ask whether traffic is predictable (→ provisioned/regional) or bursty/global (→ on-demand/edge)."
- Source: [selection.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/selection.html) (2022-07-14)

### 🚫 Anti-Patterns

**Sharing one IAM role across multiple Lambda functions**
- Risk Level: HIGH
- Why: Security — violates least privilege (SEC 2); over-broad roles "open up your systems for abuse."
- Instead: Dedicated least-privilege execution role per function; tag-based access control for granularity.
- Detection: Enumerate function execution roles; flag any role attached to >1 function; IAM Access Analyzer.
- Impact: Compliance violation / lateral privilege escalation / data breach.
- Source: [identity-and-access-management.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/identity-and-access-management.html) (2022-07-14)

**Using API Gateway API Keys as an authorization mechanism**
- Risk Level: HIGH
- Why: Security — "API Gateway API Keys is not a security mechanism"; keys only track usage.
- Instead: AWS_IAM, Cognito user pools, Lambda authorizer, resource policies, or mTLS; keys only for usage plans on public APIs.
- Detection: Find API methods whose only gate is `x-api-key`; confirm an authorizer/authType is set.
- Impact: Unauthorized API access / data exfiltration.
- Source: [identity-and-access-management.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/identity-and-access-management.html) (2022-07-14)

**Chaining Lambda functions in code to orchestrate a workflow**
- Risk Level: MEDIUM
- Why: Operational Excellence/Reliability — produces "a monolithic and tightly coupled application."
- Instead: AWS Step Functions state machine (Express/Standard) for orchestration, retries, and saga rollback.
- Detection: Search function code for direct `lambda.invoke` calls forming a chain.
- Impact: Tight coupling, hidden failures, harder retries/observability.
- Source: [general-design-principles.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/general-design-principles.html) (2022-07-14)

**Async processing with no DLQ / no partial-failure handling**
- Risk Level: HIGH
- Why: Reliability — failed async transactions cause data loss and degraded customer experience; `PutRecords`/`BatchWriteItem` return success if only one record succeeds.
- Instead: Per-function SQS DLQ + `Destination on Failure`; inspect partial-batch responses; use bisect-batch + max-retry/record-age for streams.
- Detection: Check for missing DLQ/on-failure destination on async functions; code review for unchecked batch responses.
- Impact: Silent data loss / stuck shards (blocked Kinesis/DynamoDB Stream processing).
- Source: [failure-management.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/failure-management.html) (2022-07-14)

**Logging/persisting unencrypted sensitive data (incl. in URL path/query strings)**
- Risk Level: CRITICAL
- Why: Security — sensitive data in URL paths/query strings can leak into CloudWatch Logs unencrypted.
- Instead: Encrypt client-side or before processing; send secrets in POST body; encryption at rest via KMS; enable API Gateway logging only after consulting compliance.
- Detection: Review access logs / standard output for PII; confirm encryption-at-rest on all stores.
- Impact: Data breach / compliance violation.
- Source: [data-protection.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/data-protection.html) (2022-07-14)

> Concrete ❌ Wrong / ✅ Correct pairs for these anti-patterns are in the [Never-Do Anti-Patterns](#never-do-anti-patterns) section below.

---

## Cloud-Native Design Patterns

**Event-driven, just-in-time processing**
- Category: Communication
- Problem: Tightly coupled synchronous chains cause cascading failures and idle cost.
- Solution on AWS: Trigger transactions from events (S3 object writes, DynamoDB updates) so processing is consumer-agnostic and lean; "Use events to trigger transactions" ([general-design-principles.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/general-design-principles.html)).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Coupling | Loosely coupled, independently scalable | Harder end-to-end tracing (mitigate with X-Ray + correlation IDs) |
  | Delivery | Just-in-time, elastic | At-least-once delivery → must be idempotent |

- Source: [general-design-principles.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/general-design-principles.html) (2022-07-14)

**Saga / orchestrated rollback with Step Functions**
- Category: Resilience
- Problem: Multi-step synchronous transactions need coordinated rollback on failure.
- Solution on AWS: Use Step Functions state machines to implement the Saga pattern, decoupling try/catch/back-off/retry from function code; save failed states to a DLQ step ([failure-management.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/failure-management.html)).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Reliability | Deterministic compensation/rollback | Added orchestration cost & ASL learning curve |
  | Observability | Built-in execution history | Standard workflow per-transition cost |

- Source: [failure-management.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/failure-management.html) (2022-07-14)

**Share-nothing, stateless functions with external state**
- Category: Scalability
- Problem: Local/temporary storage in Lambda is short-lived and not guaranteed.
- Solution on AWS: "Share nothing" — keep functions stateless; persist durable state externally (DynamoDB, S3) and manage transient state in Step Functions execution context ([general-design-principles.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/general-design-principles.html)).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Scaling | Horizontal, unlimited concurrency | External state adds latency/cost |
  | Portability | Hardware-agnostic ("assume no hardware affinity") | Requires idempotent external writes |

- Source: [general-design-principles.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/general-design-principles.html) (2022-07-14)

---

## Security Architecture

**Identity & API access control**
- AWS Services: Amazon API Gateway (AWS_IAM, Cognito user pools, Lambda authorizer, resource policies, mTLS), Amazon Cognito, AWS IAM/STS, AWS WAF.
- Architecture: Select the auth mechanism by caller type (see Mandatory Pattern 2). Cross-account Lambda authorizers and shared Cognito user pools centralize authorization for multi-account/microservice fleets. Private endpoints + VPC endpoint policies + resource policies confine internal APIs to specific VPCs/IP ranges. Layer AWS WAF managed rule groups (SQLi/XSS) in front of APIs.
- Compliance Alignment: Supports access-control and network-isolation controls (framework reference only — not legal advice).
- Source: [identity-and-access-management.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/identity-and-access-management.html) (2022-07-14)

**Data protection & application security**
- AWS Services: AWS KMS, AWS Secrets Manager, Amazon API Gateway (request validation, access logs), AWS Signer, Amazon CloudWatch Logs.
- Architecture: Encrypt sensitive data before processing/logging; encryption at rest on DynamoDB/OpenSearch/S3; API Gateway JSON-schema request validation as first-line input validation, plus deep app-level validation (separate Lambda/library/service); AWS Signer enforces trusted, unaltered Lambda code in CI/CD; secrets in Secrets Manager with rotation + audited access.
- Compliance Alignment: Supports encryption, secrets management, and input-validation controls (framework reference only).
- Source: [data-protection.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/data-protection.html) (2022-07-14)

**Reduced attack surface (managed infrastructure)**
- AWS Services: AWS Lambda (managed runtime patching), AWS-managed services generally.
- Architecture: Serverless removes OS patching/binary updates, reducing attack surface — but OWASP and application-security best practices still apply; validate/sanitize inbound events and perform security code review as for non-serverless apps.
- Compliance Alignment: Shared-responsibility shift toward AWS for infrastructure patching.
- Source: [security-pillar.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/security-pillar.html) (2022-07-14)

> Note: The lens explicitly **defers Incident Response** to the base Well-Architected Framework ("will not be described in this document because the practices from the AWS Well-Architected Framework still apply").

---

## Operational Patterns

**Observability stack (metrics, logs, traces)**
- {{AWS}} Services: Amazon CloudWatch (metrics/alarms/dashboards/EMF), CloudWatch Logs + Logs Insights, AWS X-Ray, Powertools for AWS Lambda.
- Cost Profile: Low–Medium; primary drivers are log volume/retention, custom metrics, and X-Ray trace sampling.
- Automation: Automate alarm creation from the lens per-service metric list; sample DEBUG logs and X-Ray traces at scale; use EMF for async, zero-latency custom metrics.
- Source: [operate.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/operate.html), [opex-metrics-and-alerts.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/opex-metrics-and-alerts.html) (2022-07-14)

**Failure management / resiliency**
- RTO/RPO: Not prescribed by the lens (defer to base framework); DLQ retention governs recoverability of failed async events.
- AWS Services: AWS Lambda (retry/record-age/on-failure/bisect-batch), Amazon SQS (DLQ), Step Functions (saga/DLQ steps), Kinesis/DynamoDB Streams.
- Cost Profile: Low; DLQ + Step Functions add marginal cost vs. data-loss risk.
- Automation: Automate DLQ redrive and poison-pill isolation; use Step Functions for retry/back-off instead of custom code.
- Source: [failure-management.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/failure-management.html) (2022-07-14)

**Deployment & operational health (OPS 1)**
- AWS Services: CloudWatch dashboards (automated cross-service/per-service), Powertools, EMF; deployment covered under Operate → Deploying/Prototyping/Configuration/Testing sub-areas.
- Cost Profile: Low.
- Automation: Understand the health of the serverless app (OPS 1) via the four-tier metric model (Business/Customer/System/Operational) and tiered alarms.
- Source: [operate.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/operate.html), [opex-metrics-and-alerts.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/opex-metrics-and-alerts.html) (2022-07-14)

> **Change Management:** The lens states "There are no operational practices unique to serverless applications for this best practice" — defer to the base framework.

---

## Reference Architectures

The lens defines **six reference scenarios** ([scenarios.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/scenarios.html)): RESTful microservices, Alexa skills, mobile backend, streaming processing, web application, event-driven architectures. Two are detailed below.

**RESTful microservices**
- AWS Source: [restful-microservices.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/restful-microservices.html) (2022-07-14)
- Context: Secure, replicable, resilient HTTP microservice with managed services.
- Services Composition:

  | Layer | Service | Purpose | Alternative |
  |-------|---------|---------|-------------|
  | API | Amazon API Gateway | RESTful HTTP endpoint; built-in auth, throttling, security, fault tolerance, request/response mapping | AWS AppSync (GraphQL) |
  | Compute | AWS Lambda | Business logic processing incoming API calls | — |
  | Data | Amazon DynamoDB | Schemaless NoSQL persistence, scales on demand | — |
  | Observability | Amazon CloudWatch Logs / Logs Insights / OpenSearch / S3+Athena | Access-pattern analysis from API Gateway logs | — |

- Key Decisions: Tightly bound service contract to the API; use API Gateway logging to understand consumer geography, partitioning impact, anomalies, errors/latency/cache behavior.
- Scaling Path: DynamoDB + Lambda scale on demand; front with CloudFront for global reach (see web application).
- Cost Baseline: Low at rest (pay-per-use); scales with request volume.
- Source: [restful-microservices.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/restful-microservices.html) (2022-07-14)

**Web application**
- AWS Source: [web-application.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/web-application.html) (2022-07-14)
- Context: Scalable, resilient, globally available web app with minimal operational overhead.
- Services Composition:

  | Layer | Service | Purpose | Alternative |
  |-------|---------|---------|-------------|
  | Identity | Amazon Cognito user pools | User management + IdP; tokens authenticate API Gateway calls | Lambda authorizer / external IdP |
  | Edge/CDN | Amazon CloudFront | Accelerate static + backend content via global PoPs; cache cacheable API calls | — |
  | Static hosting | Amazon S3 | Host HTML/CSS/JS/images served via CloudFront | AWS Amplify Hosting (SPA) |
  | API | Amazon API Gateway | Secure HTTPS REST endpoint | — |
  | Compute | AWS Lambda | CRUD operations over DynamoDB | — |
  | Data | Amazon DynamoDB | Elastic NoSQL store | — |

- Key Decisions: Use API Gateway usage plans + Cognito scopes for tiered/premium users; AWS Amplify Hosting for SPA atomic deploys/cache/custom domains; reuse RESTful microservices pattern for the backend.
- Scaling Path: CloudFront + S3 + Lambda + DynamoDB scale elastically; "go global in minutes."
- Cost Baseline: Pay-per-use; optimize idle cost vs. server-based.
- Source: [web-application.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/web-application.html) (2022-07-14)

---

## Performance Efficiency (Selection / Review / Monitoring / Tradeoffs)

The Performance Efficiency pillar has four areas — Selection, Review, Monitoring, Tradeoffs — and takes a data-driven approach ([performance-efficiency.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/performance-efficiency.html)). **PER 1** guidance ([selection.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/selection.html)):

- Run performance tests at steady and burst rates; tune capacity units and provisioning model; load-test after changes.
- **Amazon API Gateway:** Edge endpoints for geographically dispersed customers; Regional for regional customers / same-Region AWS calls.
- **AWS Lambda:** Test different memory settings (CPU, network, storage IOPS allocated proportionally); optimize static initialization; consider provisioned concurrency.
- **AWS Step Functions:** Test Standard vs. Express; account for per-second execution-start and state-transition rates.
- **Amazon DynamoDB:** On-demand for unpredictable traffic; provisioned for consistent traffic.
- **Amazon Kinesis:** Enhanced fan-out for dedicated I/O per consumer in multi-consumer scenarios; extended batch window for low-volume transactions with Lambda.
- Source: [selection.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/selection.html), [performance-efficiency.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/performance-efficiency.html) (2022-07-14)

## Cost Optimization (COST 1)

Four cost areas — Cost-effective resources, Matching supply and demand, Expenditure and usage awareness, Optimizing over time ([cost-optimization.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/cost-optimization.html)). **COST 1** ([cost-effective-resources.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/cost-effective-resources.html)):

- Serverless reduces capacity-planning effort via pay-per-value pricing and demand-based scaling; Lambda costs nothing while idle.
- Because Lambda proportionally allocates CPU/network/storage IOPS by memory, **faster initiation is cheaper** due to the 1-ms billing increment — optimizing performance directly reduces cost.
- Avoid over-provisioning "just in case"; benchmark with empirical data.
- Source: [cost-optimization.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/cost-optimization.html), [cost-effective-resources.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/cost-effective-resources.html) (2022-07-14)

> `⚠️ Migration Note`: The lens's cost/performance guidance predates broadly-recommended 2023+ levers such as **AWS Lambda arm64/Graviton2** cost-performance optimization and **Lambda SnapStart** (Java cold-start reduction). Validate these against current AWS Lambda docs.

---

## Framework Pillars (Serverless-Specific Summary)

```
Pillar: Operational Excellence
Definition: Ability to run and monitor systems to deliver business value and continually improve supporting processes.
Key Design Principles (serverless): Four areas — Organization, Prepare, Operate, Evolve. Serverless-specific focus on metrics/alerts, structured logging, distributed tracing, prototyping, configuration, testing, deploying.
Applies To context: Four-tier metrics (Business/Customer/System/Operational) + tiered CloudWatch alarms + X-Ray tracing.
Assessment Questions: OPS 1 — How do you understand the health of your serverless application?
Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/operational-excellence-pillar.html (2022-07-14)
```
```
Pillar: Security
Definition: Ability to protect information, systems, and assets through risk assessment and mitigation.
Key Design Principles (serverless): Five areas — IAM, Detective controls, Infrastructure protection, Data protection, Incident response (deferred to base framework).
Assessment Questions: SEC 1 (control API access), SEC 2 (security boundaries / least privilege), SEC 3 (application security).
Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/security-pillar.html (2022-07-14)
```
```
Pillar: Reliability
Definition: Ability to recover from disruptions, dynamically acquire resources, and mitigate misconfiguration/transient issues.
Key Design Principles (serverless): Three areas — Foundations, Change management (no serverless-unique practices), Failure management (DLQ, retries, idempotency, saga, partial-failure handling).
Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/reliability-pillar.html (2022-07-14)
```
```
Pillar: Performance Efficiency
Definition: Efficient use of computing resources to meet requirements as demand and technology evolve.
Key Design Principles (serverless): Four areas — Selection, Review, Monitoring, Tradeoffs (data-driven; PER 1 memory/provisioning/capacity tuning).
Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/performance-efficiency.html (2022-07-14)
```
```
Pillar: Cost Optimization
Definition: Continual refinement to build cost-aware systems that maximize ROI.
Key Design Principles (serverless): Four areas — Cost-effective resources, Matching supply and demand, Expenditure/usage awareness, Optimizing over time (COST 1; 1-ms billing; faster init = cheaper).
Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/cost-optimization.html (2022-07-14)
```
```
Pillar: Sustainability
Definition: Minimizing environmental impact of running cloud workloads (base framework pillar).
Key Design Principles (serverless): Not substantively expanded in this 2022 lens content; defer to base Well-Architected Sustainability pillar.
Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/the-pillars-of-the-well-architected-framework.html (2022-07-14)
```

---

## Mandatory Patterns

See [Architecture Guardrails → ✅ Mandatory Patterns](#-mandatory-patterns) above (patterns 1–8), each with pillar alignment, AWS services, verification, and dated source.

## Architectural Decisions

See [Architecture Guardrails → ⚠️ Architectural Decisions](#-architectural-decisions) above.

## Never-Do Anti-Patterns

Every entry below pairs a concrete ❌ Wrong / ✅ Correct example using exact AWS service names.

**1. Shared IAM role across functions**
- ❌ Wrong: One `lambda-exec-role` with `dynamodb:*` on `*` attached to 12 different Lambda functions.
- ✅ Correct: `order-writer-role` granting only `dynamodb:PutItem` on `arn:aws:dynamodb:...:table/Orders`, attached to the single `order-writer` Lambda.
- Detection: Enumerate execution roles; flag any role on >1 function; IAM Access Analyzer.
- Source: [identity-and-access-management.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/identity-and-access-management.html) (2022-07-14)

**2. API keys as authorization**
- ❌ Wrong: API Gateway method with `apiKeyRequired: true` and no authorizer, treating the key as the security gate.
- ✅ Correct: API Gateway method with `authorizationType: COGNITO_USER_POOLS` (or AWS_IAM / Lambda authorizer / mTLS); API keys used only in usage plans for throttling.
- Detection: List methods where the only control is `x-api-key`.
- Source: [identity-and-access-management.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/identity-and-access-management.html) (2022-07-14)

**3. Code-chained Lambda orchestration**
- ❌ Wrong: `functionA` calls `lambda.invoke(functionB)` which calls `functionC`, embedding retry/rollback logic in code.
- ✅ Correct: AWS Step Functions Standard state machine orchestrating A→B→C with built-in retries, catch, and a saga compensation branch feeding an SQS DLQ.
- Detection: Grep function code for `Invoke`/`invoke` calls forming chains.
- Source: [general-design-principles.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/general-design-principles.html) (2022-07-14)

**4. Async processing with no DLQ / unchecked partial failures**
- ❌ Wrong: Async Lambda consumer with no on-failure destination; code assumes `dynamodb.BatchWriteItem` fully succeeded.
- ✅ Correct: Lambda with `Destination on Failure` → Amazon SQS DLQ, `MaximumRetryAttempts`/`MaximumRecordAge`/`Bisect Batch on Function Error` set; code inspects `UnprocessedItems` from `BatchWriteItem` and `FailedRecordCount` from `PutRecords`.
- Detection: Functions lacking DLQ/on-failure destination; code not inspecting batch responses.
- Source: [failure-management.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/failure-management.html) (2022-07-14)

**5. Unencrypted sensitive data in URLs/logs/stores**
- ❌ Wrong: `GET /users?ssn=123-45-6789` with API Gateway access logging enabled and an S3 bucket with default (unencrypted) storage.
- ✅ Correct: SSN sent in an encrypted POST body; S3/DynamoDB encryption at rest via AWS KMS; secrets in AWS Secrets Manager with rotation; API Gateway logging enabled only after compliance review.
- Detection: Scan access logs/stdout for PII; confirm KMS encryption-at-rest on all stores.
- Source: [data-protection.html](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/data-protection.html) (2022-07-14)

## Service Equivalence Map

The request scopes a single provider (AWS). A cross-provider map is not required by this skill for
single-provider research, but the serverless-equivalence subset is included to aid architects comparing
options:

| Category | AWS | Google Cloud | Azure | Oracle Cloud (OCI) |
|----------|-----|-------------|-------|--------------------|
| Serverless functions | AWS Lambda | Cloud Functions | Azure Functions | OCI Functions |
| API management | Amazon API Gateway | API Gateway / Apigee | API Management | OCI API Gateway |
| Workflow orchestration | AWS Step Functions | Workflows | Logic Apps / Durable Functions | OCI (no direct equivalent) |
| NoSQL data store | Amazon DynamoDB | Firestore / Bigtable | Cosmos DB | OCI NoSQL Database |
| Event bus | Amazon EventBridge | Eventarc | Event Grid | OCI Events |
| Pub/Sub | Amazon SNS | Pub/Sub | Service Bus Topics | OCI Notifications |
| Queue | Amazon SQS | Cloud Tasks | Service Bus Queues | OCI Queue |
| Streaming | Amazon Kinesis | Pub/Sub / Dataflow | Event Hubs | OCI Streaming |
| Identity (end user) | Amazon Cognito | Identity Platform | Entra External ID | OCI IAM Identity Domains |
| Secrets | AWS Secrets Manager | Secret Manager | Key Vault | OCI Vault |
| CDN/Edge | Amazon CloudFront | Cloud CDN | Front Door | OCI CDN |
| Tracing | AWS X-Ray | Cloud Trace | Application Insights | OCI APM |

> ⚠️ Equivalence ≠ feature parity. Validate each service's limits, pricing, and regional availability against current provider docs.

## Provider Differentiators (AWS Serverless)

```
Differentiator: AWS Step Functions (Express + Standard) tightly integrated with 200+ AWS services
Category: Compute / Orchestration
Unique Value: Native SDK integrations remove custom glue code; Saga/retry/back-off handled declaratively.
Architecture Impact: Shifts orchestration and error handling out of Lambda code (Mandatory Pattern 3).
When to Leverage: Multi-step transactions requiring durable, audited, or high-volume orchestration.
Caveat: ASL is AWS-proprietary; Express is at-least-once (not exactly-once).
Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/failure-management.html (2022-07-14)
```
```
Differentiator: Lambda proportional resource allocation with 1-ms billing
Category: Compute / Cost
Unique Value: CPU/network/IOPS scale with memory; faster init is cheaper due to 1-ms increments.
Architecture Impact: Memory tuning is simultaneously a performance AND cost lever.
When to Leverage: Any latency- or cost-sensitive function; use power-tuning to find the optimum.
Caveat: Over-allocation wastes cost; under-allocation raises duration.
Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/cost-effective-resources.html (2022-07-14)
```

## Scenario Coverage

**Standard Case**: Serverless RESTful microservice / web application for general production workloads.
- Approach: Amazon API Gateway (auth + throttling) → AWS Lambda (least-privilege role, structured logging, X-Ray) → Amazon DynamoDB; CloudFront + S3 + Cognito for the web front end; CloudWatch four-tier metrics + alarms.
- Key Decisions: Endpoint type (edge vs regional), DynamoDB capacity mode, provisioned vs on-demand concurrency, auth mechanism.

**Edge Case**: High-volume stream processing with multiple consumers.
- Approach: Amazon Kinesis with enhanced fan-out per consumer; Lambda with bisect-batch, max-retry, max-record-age, DLQ on failure; alarm on `IteratorAge`; Step Functions Express for short high-volume orchestration.

**Anti-Pattern Case**: Request to "just use one broad IAM role and API keys to ship faster."
- Clarification: Refuse/flag — per SEC 1/SEC 2, use per-function least-privilege roles and a real authorizer (Cognito/IAM/Lambda authorizer/mTLS); API keys are usage-tracking only. Ask which caller types must be supported before choosing the auth mechanism.

---

## Migration Notes — Post-2022 Gaps

Because the lens content is dated **2022-07-14**, the following widely-used serverless capabilities are
**absent or under-represented** and must be independently verified against current AWS docs before
architecture decisions (each tagged `⚠️ Migration Note`):

| Capability | Status vs. lens | Verify at |
|---|---|---|
| Lambda SnapStart (Java, later Python/.NET) | Not covered | AWS Lambda Developer Guide |
| Lambda arm64 / Graviton2 cost-performance | Not emphasized | AWS Lambda pricing / compute docs |
| Lambda response streaming | Not covered | AWS Lambda Developer Guide |
| Lambda function recursion detection | Not covered | AWS Lambda Developer Guide |
| Lambda "Destinations" (on-success/on-failure) | Partially (DLQ-centric framing) | AWS Lambda async invocation docs |
| Powertools for AWS Lambda (current name/features) | Referenced as "Lambda Powertools" | Powertools for AWS Lambda docs |
| Sustainability pillar serverless guidance | Thin/deferred | Base Well-Architected Sustainability pillar |

---

## Source Bibliography

All sources are official AWS documentation, **content publication date 2022-07-14**, PDF copyright 2026,
**all accessed 2026-08-27**. Per this project's 12-month currency rule, the entire lens is flagged:
`> ⚠️ Source dated 2022-07; verify currency.`

| # | Section | URL |
|---|---------|-----|
| 1 | Welcome / publication date | https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/welcome.html |
| 2 | Definitions (layers) | https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/definitions.html |
| 3 | General design principles | https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/general-design-principles.html |
| 4 | Scenarios overview | https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/scenarios.html |
| 5 | RESTful microservices | https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/restful-microservices.html |
| 6 | Web application | https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/web-application.html |
| 7 | Operational Excellence pillar | https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/operational-excellence-pillar.html |
| 8 | Operate (OPS 1) | https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/operate.html |
| 9 | Metrics and alerts | https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/opex-metrics-and-alerts.html |
| 10 | Centralized/structured logging | https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/opex-logging.html |
| 11 | Distributed tracing | https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/opex-distributed-tracing.html |
| 12 | Security pillar | https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/security-pillar.html |
| 13 | Identity & access management (SEC 1/2) | https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/identity-and-access-management.html |
| 14 | Data protection (SEC 3) | https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/data-protection.html |
| 15 | Reliability pillar | https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/reliability-pillar.html |
| 16 | Change management | https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/change-management.html |
| 17 | Failure management | https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/failure-management.html |
| 18 | Performance Efficiency pillar | https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/performance-efficiency.html |
| 19 | Selection (PER 1) | https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/selection.html |
| 20 | Cost Optimization pillar | https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/cost-optimization.html |
| 21 | Cost-effective resources (COST 1) | https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/cost-effective-resources.html |
| 22 | Serverless Lens PDF (2026 copyright) | https://docs.aws.amazon.com/pdfs/wellarchitected/latest/serverless-applications-lens/wellarchitected-serverless-applications-lens.pdf |

**Secondary (dated) supplements** — AWS Compute Blog "Building Well-Architected Serverless Applications" series (2019–2021): performance [part 1](https://aws.amazon.com/blogs/compute/building-well-architected-serverless-applications-optimizing-application-performance-part-1/), [part 2](https://aws.amazon.com/blogs/compute/building-well-architected-serverless-applications-optimizing-application-performance-part-2/), [part 3](https://aws.amazon.com/blogs/compute/building-well-architected-serverless-applications-optimizing-application-performance-part-3/), [cost](https://aws.amazon.com/blogs/compute/building-well-architected-serverless-applications-optimizing-application-costs). `> ⚠️ Source dated 2019–2021; verify currency.`

---

## §7 Research Iteration Changelog

| Iteration | Item | Action | Outcome | Source |
|-----------|------|--------|---------|--------|
| 0 (baseline) | TARGET_EDITION "2026" validity | Verified PDF vs HTML publication date | RESOLVED — content is 2022-07-14; "2026" is copyright-only. Flagged prominently. | welcome.html |
| 0 | Performance Efficiency pillar content | First fetch (`...-pillar.html`) returned empty/hallucinated | RESOLVED — correct URL is `performance-efficiency.html` + `selection.html` | selection.html |
| 0 | Cost Optimization pillar content | First fetch returned unverified generic content | RESOLVED — correct URL `cost-optimization.html` + `cost-effective-resources.html` | cost-effective-resources.html |
| 0 | Change Management best practices | Fetched | RESOLVED — lens explicitly states no serverless-unique practices | change-management.html |

**Unresolved / irresolvable items:** None. All eight Mandatory Patterns, five Anti-Patterns, and all six
pillars are sourced to dated official documentation. The only outstanding caveat is the systemic currency
gap (content is 2022), addressed via the [Migration Notes](#migration-notes--post-2022-gaps) section
rather than left unverified.

---

## Verification Loop Results (P5)

```
[✓] TARGET_EDITION stated in metadata and throughout — WITH critical correction (2022 content).
[✓] All 6 mandatory output sections present: Framework Pillars, Mandatory Patterns,
    Architectural Decisions, Anti-Patterns, Service Equivalence Map, Source Bibliography.
[✓] Every pattern cites an official provider URL with access date (2026-08-27).
[✓] Every Never-Do entry has a side-by-side ❌ Wrong / ✅ Correct example using exact service names (5/5).
[✓] All sources dated; entire lens flagged >12 months (2022-07) per rule.
[✓] Serverless service classes covered in equivalence subset.
[✓] No generic cloud terms where AWS service names exist.
```

> **Recommended next step:** run `/skill-best-practices-validator` on any SKILL.md generated from this
> research, and re-run this research after AWS publishes a genuine content revision of the Serverless
> Applications Lens.
