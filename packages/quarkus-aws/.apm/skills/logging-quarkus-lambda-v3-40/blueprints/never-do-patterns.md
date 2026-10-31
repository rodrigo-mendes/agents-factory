# Never-Do Patterns

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. Severity wording: low, moderate, high. F1 to F5 are the five High rows of the SKILL.md Never Do table; F6 to F8 are tagged anti-patterns that stay out of that table because the claim or its alternative is not High.

## Contents

- [F1. Logging environment variables, the event or secrets](#f1-logging-environment-variables-the-event-or-secrets-severity-high)
- [F2. Log4j dependencies in a Quarkus app](#f2-log4j-dependencies-in-a-quarkus-app-severity-high)
- [F3. Custom log group starting with aws/](#f3-custom-log-group-starting-with-aws-severity-high)
- [F4. Pretty-printed JSON](#f4-pretty-printed-json-severity-moderate)
- [F5. Deprecated quarkus.log.console.json.enable](#f5-deprecated-quarkuslogconsolejsonenable-severity-low)
- [F6. Expecting ApplicationLogLevel DEBUG to show lines Quarkus never emitted](#f6-expecting-applicationloglevel-debug-to-show-lines-quarkus-never-emitted-severity-moderate)
- [F7. Renaming level or timestamp while using Lambda filtering](#f7-renaming-level-or-timestamp-while-using-lambda-filtering-severity-moderate)
- [F8. Leaving tenantId or the request id in MDC](#f8-leaving-tenantid-or-the-request-id-in-mdc-severity-high)

## F1. Logging environment variables, the event or secrets (severity: high)

Lambda sets the reserved variables `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` and `AWS_SESSION_TOKEN` with "The access keys obtained from the function's execution role" ([AWS env vars](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html)). AWS's own Java sample logs `gson.toJson(System.getenv())`, and its CLI output shows an `"AWS_SESSION_TOKEN"` value in the log ([AWS Java logging](https://docs.aws.amazon.com/lambda/latest/dg/java-logging.html)). Masking applies only to data ingested after a policy exists: "log events ingested to the log group before that time are not masked" ([masking](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/mask-sensitive-log-data.html)). Family rule 7: no PII or secrets in logs. Impact: the execution role's credentials and customer data become readable to anyone with log read access.

```java
// ❌ WRONG - copied from the AWS sample
Log.info("ENV: " + System.getenv());
Log.info("EVENT: " + objectMapper.writeValueAsString(event));

// ✅ CORRECT - identifiers and bounded facts only
MDC.put("AWSRequestId", context.getAwsRequestId());   // org.jboss.logmanager.MDC
Log.info("order received");                           // no env, no tokens, no PII
```

Secrets come from Secrets Manager or SSM (family rule 5); AWS recommends Secrets Manager over environment variables ([AWS env vars](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html)).

## F2. Log4j dependencies in a Quarkus app (severity: high)

Quarkus 3.40 supports the Log4j 2 API through the adapter `org.jboss.logmanager:log4j2-jboss-logmanager` and says "Do not include any Log4j dependencies, as the `log4j2-jboss-logmanager` library contains everything needed" ([logging guide](https://quarkus.io/version/3.40/guides/logging)). AWS's Java recipe needs `log4j-layout-template-json`, `log4j-slf4j2-impl` and the `Lambda` appender ([AWS Java logging](https://docs.aws.amazon.com/lambda/latest/dg/java-logging.html)), a different backend. For SLF4J the Quarkus adapter is `org.jboss.slf4j:slf4j-jboss-logmanager`. Impact: two logging backends; for native builds "the native build can fail" without the JBoss adapters.

```xml
<!-- ❌ WRONG - Quarkus 3.40 app -->
<dependency><groupId>com.amazonaws</groupId><artifactId>aws-lambda-java-log4j2</artifactId></dependency>
<dependency><groupId>org.apache.logging.log4j</groupId><artifactId>log4j-slf4j2-impl</artifactId></dependency>

<!-- ✅ CORRECT - JBoss LogManager backend plus the JSON extension -->
<dependency><groupId>io.quarkus</groupId><artifactId>quarkus-logging-json</artifactId></dependency>
<!-- only if a library logs through the Log4j 2 API: -->
<dependency><groupId>org.jboss.logmanager</groupId><artifactId>log4j2-jboss-logmanager</artifactId></dependency>
```

Powertools logging inside Quarkus is (unverified); see [decision A1](./ask-first-decisions.md#a1-who-produces-the-json).

## F3. Custom log group starting with aws/ (severity: high)

"custom log group names mustn't begin with the string `aws/`. If you create a custom log group beginning with `aws/`, Lambda won't be able to create the log group. As a result of this, your Event Function's logs won't be sent to CloudWatch" ([AWS log groups](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-loggroups.html)).

```bash
# ❌ WRONG (representative)
aws lambda update-function-configuration --function-name orders --logging-config LogGroup=aws/orders-app

# ✅ CORRECT (representative)
aws lambda update-function-configuration --function-name orders --logging-config LogGroup=orders-app
```

## F4. Pretty-printed JSON (severity: moderate)

`quarkus.log.console.json.pretty-print` defaults to `false`; the guide warns "some JSON parsers will fail to read the pretty printed output" ([logging guide](https://quarkus.io/version/3.40/guides/logging)). Multi-line stdout becomes several CloudWatch events (medium confidence: `aws-lambda-java-log4j2` README, main branch); that a one-line record keeps a stack trace in one event is an inference (medium confidence).

```properties
# ❌ WRONG
quarkus.log.console.json.pretty-print=true

# ✅ CORRECT - the 3.40 default
quarkus.log.console.json.pretty-print=false
```

## F5. Deprecated quarkus.log.console.json.enable (severity: low)

In source at tag 3.40.1.1, `enable()` is `@Deprecated(forRemoval = true, since = "3.19")`; use `enabled` ([source at tag](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/logging-json/runtime/src/main/java/io/quarkus/logging/json/runtime/JsonLogConfig.java)).

```properties
# ❌ WRONG
quarkus.log.console.json.enable=false

# ✅ CORRECT
quarkus.log.console.json.enabled=false
```

## F6. Expecting ApplicationLogLevel DEBUG to show lines Quarkus never emitted (severity: moderate)

Tagged here, not in the SKILL.md table, because the working alternative uses the runtime override of `quarkus.log.level`, which is (medium confidence). `quarkus.log.level` defaults to `INFO`; Lambda: "if you set your Event Function's log level in your code, this setting takes precedence over any other log level settings you configure" ([AWS log-level filtering](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-log-level.html)). Below DEBUG "adjust the minimum level at build time" ([logging guide](https://quarkus.io/version/3.40/guides/logging)). With `min-level` at INFO, `isDebugEnabled()` checks become dead code in native mode. Impact: no DEBUG lines during an incident despite the Lambda setting.

```bash
# ❌ WRONG (representative) - Quarkus app still at quarkus.log.level=INFO
aws lambda update-function-configuration --function-name orders \
  --logging-config LogFormat=JSON,ApplicationLogLevel=DEBUG

# ✅ CORRECT (representative) - raise the Quarkus level too (decision A4, medium confidence)
aws lambda update-function-configuration --function-name orders \
  --environment "Variables={QUARKUS_LOG_LEVEL=DEBUG}"   # replaces ALL variables: include the existing ones
```

## F7. Renaming level or timestamp while using Lambda filtering (severity: moderate)

The AWS rule is High (missing or invalid `level`, or an invalid timestamp, becomes INFO); the Quarkus ECS and GCP renames come from source at the tag (medium confidence), so the row stays out of the table. Impact: ERROR lines are treated as INFO and dropped when `ApplicationLogLevel` is WARN or higher (medium confidence).

```properties
# ❌ WRONG while Lambda log-level filtering is used
quarkus.log.console.json.log-format=ecs

# ✅ CORRECT - the 3.40 default
quarkus.log.console.json.log-format=default
```

## F8. Leaving tenantId or the request id in MDC (severity: high)

Environments are reused and AWS says "Avoid global variables for context-specific information" ([AWS lifecycle](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html)). Quarkus's own poll loop removes `AWSRequestId` in `finally`. That MDC values survive on the thread across invocations in the Quarkus Lambda runtime is an inference (medium confidence). Impact: a later invocation logs another tenant's id, which breaks tenant isolation in logs (family rules 6 and 7).

```java
// ❌ WRONG
MDC.put("tenantId", tenant);       // never removed
return process(event);

// ✅ CORRECT
MDC.put("tenantId", tenant);
try { return process(event); } finally { MDC.remove("tenantId"); }
```
