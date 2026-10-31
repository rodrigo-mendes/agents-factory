# Never-do patterns

Back to [SKILL.md](../SKILL.md). Research date 2026-10-28. Source ids resolve in the [source bibliography](./source-bibliography.md). Code is illustrative and was not compiled (medium confidence, M16). Unconfirmed variants of these rules (scope, version override, REST streaming) are Ask First items, see [ask-first decisions](./ask-first-decisions.md).

## Contents

- [N1 API key in properties, code or Lambda environment](#n1-api-key-in-properties-code-or-lambda-environment)
- [N2 Static AWS credentials for Bedrock](#n2-static-aws-credentials-for-bedrock)
- [N3 Multi or SSE endpoint behind an HTTP API](#n3-multi-or-sse-endpoint-behind-an-http-api)
- [N4 Timeout above the gateway limit](#n4-timeout-above-the-gateway-limit)
- [N5 Request logging or prompt tracing in production](#n5-request-logging-or-prompt-tracing-in-production)
- [N6 Real provider calls in tests](#n6-real-provider-calls-in-tests)

## N1 API key in properties, code or Lambda environment

Severity: high. Why: AWS recommends Secrets Manager "instead of environment variables" for API keys [S43]; the extension says "Never embed API keys, or other credentials directly in your source code" and warns that leaked keys allow "unauthorized access and abuse of your account" [S16]. Family rule 5 (secrets come from Secrets Manager or SSM). The extension docs also suggest the environment variable `QUARKUS_LANGCHAIN4J_OPENAI_API_KEY` [S33] (contradiction C5, resolved for Lambda in favour of AWS and rule 5). Impact: the key leaks through Git, the Lambda console or configuration dumps.

```properties
# ❌ WRONG
quarkus.langchain4j.openai.api-key=sk-live-...
# or the Lambda environment variable QUARKUS_LANGCHAIN4J_OPENAI_API_KEY=sk-live-...
```

```properties
# ✅ CORRECT: no api-key line in properties; the key lives in Secrets Manager or SSM
# the delivery mechanism (config source or ModelAuthProvider) is Ask First D3
quarkus.langchain4j.openai.chat-model.model-name=<chosen model>
```

## N2 Static AWS credentials for Bedrock

Severity: high. Why: Lambda already supplies execution-role credentials [S43], and with nothing configured the extension uses the SDK default chain [S31][S27]. The `dev` page: "Do not configure AWS credentials in `application.properties`." [S10]. Impact: long-lived keys outside IAM rotation, and under SnapStart the runtime uses container credentials instead of key variables (https://docs.aws.amazon.com/lambda/latest/dg/snapstart-activate.html).

```properties
# ❌ WRONG
quarkus.langchain4j.bedrock.aws.credentials-provider=staticKeys
```

```properties
# ✅ CORRECT: nothing; the SDK default chain resolves the Lambda execution role
quarkus.langchain4j.bedrock.chat-model.model-id=<chosen model or inference-profile id>
```

## N3 Multi or SSE endpoint behind an HTTP API

Severity: high. Scope: `quarkus-amazon-lambda-http` and an HTTP API; the `quarkus-amazon-lambda-rest` extension on a REST API is Ask First D10 (medium confidence, M4). Why: the 3.40.1.1 HTTP handler buffers until `LastHttpContent` [S46]; an HTTP API has no response streaming [S39]; Lambda streams natively only on Node.js managed runtimes [S41]. The streaming guide itself says "methods returning Multi are considered non-blocking. Do not use blocking code inside streaming pipelines." [S11]. Impact: no time-to-first-byte gain, and the full generation must still finish inside the gateway limit [S37][S38]. How an SSE body is encoded (text or base64) is (unverified, U9). Streaming models apply no `maxRetries` in the recorders (medium confidence, M5).

```java
// ❌ WRONG: behind API Gateway + quarkus-amazon-lambda-http
@POST @Produces(MediaType.SERVER_SENT_EVENTS)
public Multi<String> stream(String q) { return assistant.respondToQuestion(q); }
```

```java
// ✅ CORRECT: blocking String, bounded by @Timeout (pattern 5)
@POST @Produces(MediaType.TEXT_PLAIN)
public String answer(String q) { return assistant.answer(q); }
```

## N4 Timeout above the gateway limit

Severity: high. Why: a REST API allows up to 29 s (raisable for Regional and private APIs with a throttle trade-off) [S37] and an HTTP API 30 s, not raisable [S38]; the guide's 60 s `@Timeout` is an example, not a default [S12]. Impact: API Gateway answers first. What status it returns on an integration timeout and whether the function keeps running were not re-read (unverified, U8). Provider timeouts times attempts above the limit have the same effect (medium confidence, M1).

```java
// ❌ WRONG: copied from the guide, behind a 29 s REST API
@Timeout(value = 60, unit = ChronoUnit.SECONDS)
String answer(@UserMessage String question);
```

```java
// ✅ CORRECT: below the gateway limit
@Timeout(value = 25, unit = ChronoUnit.SECONDS)
String answer(@UserMessage String question);
```

## N5 Request logging or prompt tracing in production

Severity: high. Why: the defaults are off [S24][S25]; the extension says "Avoid logging full prompts and responses unless absolutely necessary for auditing." and to "remove any Personally Identifiable Information (PII) or other sensitive details." [S16]; family rule 7 (JSON logs with requestId and tenantId, no PII). Whether request logging masks the `Authorization` or `x-api-key` header was not verified (unverified, U10). Impact: PII, and possibly credentials, in CloudWatch Logs or a trace backend.

```properties
# ❌ WRONG
quarkus.langchain4j.log-requests=true
quarkus.langchain4j.tracing.include-prompt=true
```

```properties
# ✅ CORRECT: dev profile only
%dev.quarkus.langchain4j.log-requests=true
quarkus.langchain4j.tracing.include-prompt=false
```

## N6 Real provider calls in tests

Severity: moderate. Why: tests must be deterministic and must not spend vendor quota; WireMock is the documented way to test model HTTP calls "without calling a real model" [S13][S14], and the AI service is mockable with `@InjectMock` [S26][S47]. Impact: flaky tests, cost, a real key needed in CI.

```properties
# ❌ WRONG: real key, real endpoint
%test.quarkus.langchain4j.openai.api-key=${OPENAI_API_KEY}
```

```properties
# ✅ CORRECT: local stub server and a placeholder key
%test.quarkus.langchain4j.openai.base-url=http://localhost:${quarkus.wiremock.devservices.port}/v1
%test.quarkus.langchain4j.openai.api-key=test-key
```
