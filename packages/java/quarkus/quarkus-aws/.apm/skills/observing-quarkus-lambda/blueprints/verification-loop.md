# Verification Loop

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. This loop does not add commands of its own: it lists the pillar loops in order and the single combined expectation. Commands are representative, adapt to your environment.

## Order

1. Logs: [logging verification loop](../../logging-quarkus-lambda-v3-40/blueprints/verification-loop.md). Expected: one JSON log line from a deployed invocation carries an `mdc` object with `AWSRequestId` and `tenantId` (medium confidence on the path `mdc.<key>`).
2. Traces: [tracing verification loop](../../tracing-quarkus-lambda-v3-40/blueprints/verification-loop.md#verification-loop). Expected: the function has `TracingConfig Mode=Active` and a trace for the invocation shows the subsegment with the `tenantId` annotation. Check the trace segment destination first: when Transaction Search is enabled, `BatchGetTraces` cannot find the trace ("You cannot find traces through this API if Transaction Search is enabled since trace is not indexed in X-Ray", [BatchGetTraces](https://docs.aws.amazon.com/xray/latest/api/API_BatchGetTraces.html)), so use the CloudWatch Logs retrieval path.
3. Metrics: [monitoring verification loop](../../monitoring-quarkus-lambda-v3-40/blueprints/verification-loop.md). Expected: the metric appears in the custom namespace; statistics are visible within about 2 minutes of the first publish and `list-metrics` within about 15 minutes ([monitoring Quick Reference](../../monitoring-quarkus-lambda-v3-40/SKILL.md#quick-reference)).

## Combined expectation

For one invocation with a known `AWSRequestId` and `tenantId`:

| Pillar | Evidence | Pass when |
|---|---|---|
| Log | Logs Insights on `mdc.AWSRequestId` | the line exists with `mdc.tenantId` set |
| Trace | trace list filtered by annotation `tenantId` | at least one trace; metadata holds the request id |
| Metric | `list-metrics` on the custom namespace | the metric exists with only the bounded dimensions |

A local test through the mock event server does not prove the JVM MDC path or any trace id (see [correlation recipe](./correlation-recipe.md#what-the-recipe-does-not-claim)); run this loop on a deployed function. Infrastructure checks (log group, tracing config, alarms) belong to `validating-aws-observability` (name only).
