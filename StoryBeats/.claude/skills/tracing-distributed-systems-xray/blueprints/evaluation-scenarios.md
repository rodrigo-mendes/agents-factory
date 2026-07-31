# Evaluation Scenarios — tracing-distributed-systems-xray

Source: [SKILL.md](../SKILL.md) | Research: 2026-07-31

Three scenarios to validate that the skill activates correctly, handles edge cases, and guards against misuse.

---

## Scenario 1 — Canonical: New microservice needing end-to-end tracing on ECS

```json
{
  "skills": ["tracing-distributed-systems-xray"],
  "query": "We are building a new order-processing microservice on ECS Fargate. It receives requests from API Gateway, calls DynamoDB, and publishes to SQS. We need distributed tracing with AWS X-Ray. How should we instrument it?",
  "expected_behavior": [
    "Recommends ADOT or raw OpenTelemetry SDK — NOT the X-Ray SDK (maintenance-mode)",
    "Proposes an OTel Collector sidecar container in the ECS task definition emitting OTLP on 4317/4318",
    "Sets OTEL_PROPAGATORS=tracecontext,xray to handle both W3C and X-Amzn-Trace-Id at the API Gateway boundary",
    "Notes that DynamoDB calls will appear as inferred segments and SQS will use passive propagation",
    "Asks which instrumentation stack (raw OTel vs. ADOT vs. Application Signals) before writing final config",
    "Provides IAM policy with xray:PutTraceSegments and xray:PutTelemetryRecords for the task role",
    "Includes a sampling rule to suppress health-check paths and 100% sampling for the checkout POST endpoint",
    "Marks order_id and customer_id as annotations (not metadata) for filter-expression searchability"
  ]
}
```

**What correct output looks like**:
- OTel Collector sidecar config with `awsxray` exporter targeting `us-east-1`
- Task IAM role with `xray:PutTraceSegments` + `xray:GetSamplingRules`
- `OTEL_PROPAGATORS=tracecontext,xray` in environment variables
- `aws.xray.annotations = "order_id,customer_id"` span attribute
- Sampling rule suppressing `/health` GET; 100% on `POST /checkout`

---

## Scenario 2 — Edge Case: Rare intermittent 5xx errors lost under default sampling

```json
{
  "skills": ["tracing-distributed-systems-xray"],
  "query": "We have an intermittent 503 error that appears roughly once every 2,000 requests on our payment service. Our current X-Ray sampling is at the default (1/sec + 5%). We've missed the failing trace three times this week. How do we ensure we capture these errors without disabling sampling for all traffic?",
  "expected_behavior": [
    "Identifies the problem: default head sampling probabilistically drops the rare-error trace",
    "Presents Decision 2 (sampling strategy): asks whether the goal is catching error traces (tail sampling) or 100% capture (Transaction Search)",
    "Explains tail sampling via OTel Collector tailsamplingprocessor: keeps all ERROR-status and high-latency traces, samples the rest",
    "Notes that tail sampling requires a central gateway collector (all spans of a trace must arrive at one place) — triggers Decision 3",
    "Alternatively proposes Transaction Search (100% spans to aws/spans) with a bounded indexing percentage, noting the additional CloudWatch Logs ingestion cost",
    "Does NOT recommend simply disabling sampling on all paths (cost anti-pattern)",
    "Provides the tailsamplingprocessor config with a status_code ERROR policy and probabilistic fallback"
  ]
}
```

**What correct output looks like**:
- Asks Decision 2 before prescribing a solution
- Tail sampling config with `status_code: [ERROR]` policy + probabilistic fallback at 5%
- Central gateway collector topology note (mandatory for tail sampling)
- Cost comparison: tail sampling (moderate) vs. Transaction Search (highest) vs. tightened head sampling (lowest)
- Does NOT recommend `AlwaysOn` sampler as the solution

---

## Scenario 3 — Misuse / Anti-Pattern Trap: Team proposes standardizing on X-Ray SDK for all new services

```json
{
  "skills": ["tracing-distributed-systems-xray"],
  "query": "Our architecture team wants to standardize all new Python microservices on aws-xray-sdk-python with the X-Ray Daemon as the sidecar. Can you give us a template for that setup?",
  "expected_behavior": [
    "Flags immediately that the X-Ray SDK and Daemon are in maintenance mode as of 2026-02-25 (security-only), with end-of-support on 2027-02-25",
    "Refuses to provide an X-Ray SDK template as a new-service standard",
    "Explains the forced re-platform risk before the 2027-02-25 EOS deadline",
    "Asks the clarifying question: does tracing need to feed any non-AWS backends?",
    "Recommends the correct alternative: aws-opentelemetry-distro (Python ADOT) + OTel Collector sidecar with awsxray exporter",
    "Provides a migration-path overview: instrument with OTel SDK first; keep X-Ray SDK only during transition for existing services",
    "Does NOT generate an aws-xray-sdk-python setup as a forward-looking architecture decision"
  ]
}
```

**What correct output looks like**:
- Explicit callout of maintenance-mode status and EOS date
- No X-Ray SDK template for new services
- Redirect to ADOT / OTel with the `awsxray` exporter
- Asks about non-AWS backends before recommending raw OTel vs. ADOT vs. Application Signals
- Mentions the migration guide: [Migrating from X-Ray to OpenTelemetry](https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html)

---

## Grading Notes

| Check | Pass | Fail |
|-------|------|------|
| Recommends OTel/ADOT (not X-Ray SDK) for new services | Always | Suggests X-Ray SDK for new code |
| Stops to ask instrumentation stack or sampling strategy before coding | Decision-point queries trigger the ask | Codes straight to a single opinionated answer without asking |
| Treats `X-Amzn-Trace-Id` from untrusted clients as a security concern | Mentions stripping at trust boundary | Passes client header through without comment |
| Uses annotations for searchable business keys | Sets `aws.xray.annotations` or `putAnnotation` | Uses `putMetadata` for order_id/customer_id |
| Respects sampling cost | Proposes rules to suppress health checks | Recommends `AlwaysOn` or no sampling plan |
