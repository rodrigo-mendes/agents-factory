# Verification Loop

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. All commands are representative: adapt to your environment.

## Verification Loop

```bash
# 1. Tracing mode on the version that serves traffic
aws lambda get-function-configuration --function-name my-function --qualifier live \
  --query 'TracingConfig.Mode'
# Expected: "Active"

# 2. X-Ray path: dependency present
mvn -q dependency:tree -Dincludes=com.amazonaws:aws-xray-recorder-sdk-aws-sdk-v2
# Expected: com.amazonaws:aws-xray-recorder-sdk-aws-sdk-v2:jar:2.18.3 (version from the quarkus-bom 3.40.1.1 POM, medium confidence)

# 3. OTel path: dependency present
mvn -q dependency:tree -Dincludes=io.opentelemetry.instrumentation:opentelemetry-aws-sdk-2.2
# Expected: ...opentelemetry-aws-sdk-2.2:jar:2.28.1-alpha (the version the quarkus-bom 3.40.1.1 POM manages, medium confidence);
# no output means the artifact is not in your tree (the pages read do not state how it gets there)

# 4. Static checks on code (no AWS call)
grep -rn "_X_AMZN_TRACE_ID" src/main/java                    # Expected: no match (F3)
grep -rnE 'putAnnotation\("[^"]*[_ -][^"]*"' src/main/java   # Expected: no match (F5)
grep -rn "eusp.enabled=true" src/main/resources              # Expected: no match (F4)

# 5. After an invocation, traces exist
aws xray get-trace-summaries --start-time $(date -d '-10 min' +%s) --end-time $(date +%s) \
  --filter-expression 'service("my-function")'
# Expected: at least one TraceSummary (sampling permitting: 1 request/s + 5%)
# Caveat: if Transaction Search is enabled, traces are not indexed in X-Ray; an empty result is not a failure.
# Check the trace segment destination first and, when spans go to CloudWatch Logs, retrieve them there.
```

Why: the `BatchGetTraces` API page says "You cannot find traces through this API if Transaction Search is enabled since trace is not indexed in X-Ray" (family fact, verified by the orchestrator 2026-10-28). Source: https://docs.aws.amazon.com/xray/latest/api/API_BatchGetTraces.html

## Tests

- The pages read do not document testing tracing in Quarkus Lambda tests. Whether the Quarkus mock event server (dev 8080, test 8081) sends a `Lambda-Runtime-Trace-Id` header is (unverified).
- X-Ray SDK without a segment: Lambda sets `AWS_XRAY_CONTEXT_MISSING=LOG_ERROR` in AWS. The default context-missing behaviour of SDK 2.18.3 outside Lambda is (unverified); setting `AWS_XRAY_CONTEXT_MISSING=LOG_ERROR` in the test environment is only a precaution, not a documented step.
- OTel: `quarkus.otel.sdk.disabled=true` (runtime, default `false`) or `quarkus.otel.exporter.otlp.enabled=false` ("Telemetry is still generated and propagated, but not sent", paraphrase) keep tests from exporting. An in-memory span exporter for assertions is not documented on the pages read.
- Testing patterns in depth: `testing-quarkus-amazon-lambda-v3-40` ([SKILL](../../testing-quarkus-amazon-lambda-v3-40/SKILL.md)).

Source: https://quarkus.io/version/3.40/guides/opentelemetry ; https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html
