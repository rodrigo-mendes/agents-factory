# Always-Do Patterns

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. Patterns 1 to 5 are High and appear in the SKILL.md Always Do list. Patterns 6 to 9 carry a tag and are not in that list (evidence rule: Always Do holds High claims only).

## Contents

- [1. Add the JSON extension](#1-add-the-json-extension)
- [2. Disable JSON in dev and test](#2-disable-json-in-dev-and-test)
- [3. Log through JBoss Logging to stdout](#3-log-through-jboss-logging-to-stdout)
- [4. Set levels per category](#4-set-levels-per-category)
- [5. Set retention on the log group](#5-set-retention-on-the-log-group)
- [6. Put request id and tenant id into MDC and clear them](#6-put-request-id-and-tenant-id-into-mdc-and-clear-them)
- [7. Keep the level and timestamp keys](#7-keep-the-level-and-timestamp-keys)
- [8. Grant PutLogEvents to the execution role](#8-grant-putlogevents-to-the-execution-role)
- [9. Do not depend on log group variables under SnapStart](#9-do-not-depend-on-log-group-variables-under-snapstart)

## 1. Add the JSON extension

The guide says: "Add the `quarkus-logging-json` extension to enable the JSON logging format and its related configuration". When JSON is active, "any format string or color settings are ignored" ([logging guide](https://quarkus.io/version/3.40/guides/logging)). Lambda log-level filtering for libraries other than `LambdaLogger` and Log4j2 needs JSON on stdout or stderr ([AWS Java logging](https://docs.aws.amazon.com/lambda/latest/dg/java-logging.html), [AWS log-level filtering](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-log-level.html)).

```xml
<!-- Quarkus 3.40.1.1: version managed by io.quarkus.platform:quarkus-bom 3.40.1.1 -->
<dependency>
  <groupId>io.quarkus</groupId>
  <artifactId>quarkus-logging-json</artifactId>
</dependency>
```

```properties
# Quarkus 3.40 - application.properties
quarkus.log.console.json.enabled=true
```

Writing `enabled=true` explicitly is safe; that the extension alone turns JSON on is derived from code (medium confidence), see [Quarkus JSON configuration](./quarkus-json-config.md#enabled-default).

## 2. Disable JSON in dev and test

The guide shows `%dev.quarkus.log.console.json.enabled=false` and `%test.quarkus.log.console.json.enabled=false` ([logging guide](https://quarkus.io/version/3.40/guides/logging)). It keeps local and test output readable.

```properties
# Quarkus 3.40 - application.properties
%dev.quarkus.log.console.json.enabled=false
%test.quarkus.log.console.json.enabled=false
```

## 3. Log through JBoss Logging to stdout

AWS: "To output logs from your function code, you can use methods on java.lang.System, or any logging module that writes to stdout or stderr" ([AWS Java logging](https://docs.aws.amazon.com/lambda/latest/dg/java-logging.html)). Quarkus: "When using the JBoss Logging API, your application requires no additional dependencies"; `Log` calls are rewritten "into JBoss Logging calls on the generated logger field"; use `Log` only in application classes, not in extensions or external dependencies. `quarkus.log.console.enabled` defaults to `true` and `quarkus.log.console.stderr` to `false` ([logging guide](https://quarkus.io/version/3.40/guides/logging)).

```java
// Quarkus 3.40 - application class only
import io.quarkus.logging.Log;

Log.info("payment authorized");   // rewritten to a JBoss Logging call at build time
```

## 4. Set levels per category

Quarkus keys `quarkus.log.category."<category-name>".level` and `quarkus.log.level` both default to `INFO` ([logging guide](https://quarkus.io/version/3.40/guides/logging)). AWS's Java logging sample sets `software.amazon.awssdk` to `WARN` ([AWS Java logging](https://docs.aws.amazon.com/lambda/latest/dg/java-logging.html)). JSON "can increase" the log size ([AWS log formats](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-logformat.html)), so cut verbose categories.

```properties
# Quarkus 3.40
quarkus.log.level=INFO
quarkus.log.category."software.amazon.awssdk".level=WARN
quarkus.log.category."com.example.orders".level=DEBUG
```

`DEBUG` lines from a category are emitted only if `quarkus.log.min-level` (build time, default `DEBUG`) allows them; for `TRACE` set `quarkus.log.min-level=TRACE` at build time ([logging guide](https://quarkus.io/version/3.40/guides/logging)).

## 5. Set retention on the log group

"By default, log data is stored in CloudWatch Logs indefinitely" ([CloudWatch log groups](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Working-with-log-groups-and-streams.html)). "Log groups aren't deleted automatically when you delete a function. To avoid storing logs indefinitely, delete the log group, or configure a retention period" ([AWS Java logging](https://docs.aws.amazon.com/lambda/latest/dg/java-logging.html)). Deletion after the retention period "typically takes up to 72 hours".

No HCL here. The log group and its retention belong to `provisioning-aws-cloudwatch-v6` (family rule 4: no SAM or CDK); the group design belongs to `monitoring-cloudwatch-observability`. Creating the group in IaC before the first invoke is an inference from "automatically creates a log group ... when it's first invoked" (medium confidence), see [log groups](./lambda-logging-controls.md#log-groups-retention-and-cost).

## 6. Put request id and tenant id into MDC and clear them

Tag: (medium confidence) for the per-mode behaviour, read from source code at tag 3.40.1.1 and not stated by a guide (M2). The 3.40.1.1 poll loop (native builds, dev and test) puts the request id into MDC under `AWSRequestId` and removes it in `finally`. The JVM managed-runtime path (`QuarkusStreamHandler` to `AmazonLambdaRecorder.handle`) has no MDC code, so the handler puts `Context.getAwsRequestId()` into MDC itself and clears it. Family rule 7 requires `requestId` and `tenantId` in JSON logs; family rule 6 requires the tenant to come from the verified token, never from the path alone. AWS: "Avoid global variables for context-specific information" ([AWS lifecycle](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html)); leaving values after the invocation can leak the previous tenant into the next one (medium confidence, M19). The per-mode table is in [MDC and request id](./mdc-and-request-id.md).

```java
// Quarkus 3.40.1.1 - quarkus-amazon-lambda, JVM or native (illustrative body, medium confidence)
import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import io.quarkus.logging.Log;
import jakarta.inject.Named;
import org.jboss.logmanager.MDC;   // the 3.40 guide's class; sharing a store with org.jboss.logging.MDC is (unverified)

@Named("orders")
public class OrdersLambda implements RequestHandler<OrderEvent, OrderResult> {
    @Override
    public OrderResult handleRequest(OrderEvent event, Context context) {
        MDC.put("AWSRequestId", context.getAwsRequestId());
        MDC.put("tenantId", tenantFromVerifiedToken(event)); // never from the path alone
        try {
            Log.info("order received");
            return process(event);
        } finally {
            MDC.remove("tenantId");
            MDC.remove("AWSRequestId");
        }
    }
}
```

Keep the key `AWSRequestId` so JVM and native lines agree. Lambda's own Java JSON spells it `AWSrequestId`; how Insights treats the case is (unverified), see [MDC and request id](./mdc-and-request-id.md#key-spelling).

## 7. Keep the level and timestamp keys

Tag: (medium confidence) for the Quarkus key names (M1) and the RFC 3339 match (M7). AWS: the code must output JSON objects with the key `"level"`; "If the `"level"` value field is invalid or missing, Lambda assigns the log output the level INFO"; "If you don't supply a valid timestamp, Lambda assigns the log the level INFO" ([AWS log-level filtering](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-log-level.html)). Quarkus writes `level` and `timestamp` by default and the default timestamp is `ISO_OFFSET_DATE_TIME` (jboss-logmanager main branch). So leave `key-overrides` and `date-format` for those keys at their defaults while Lambda filtering is used; the alternatives are in [decision A6](./ask-first-decisions.md#a6-structured-format-profile-and-key-names).

```properties
# Quarkus 3.40 - do not override level/timestamp
# quarkus.log.console.json.key-overrides=...   (not for level or timestamp)
# quarkus.log.console.json.date-format=default (default value)
```

## 8. Grant PutLogEvents to the execution role

Tag: (medium confidence) (M14). AWS: "For your Event Function to send logs to CloudWatch Logs, it must have the logs:PutLogEvents permission"; when the log group is configured through the AWS CLI "Lambda won't automatically add the `logs:PutLogEvents` permission"; "This permission is included in the AWSLambdaBasicExecutionRole managed policy" ([AWS log groups](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-loggroups.html)). The policy itself is IaC (`provisioning-aws-cloudwatch-v6`).

## 9. Do not depend on log group variables under SnapStart

Tag: (medium confidence) (M15). "The `AWS_LAMBDA_LOG_GROUP_NAME` and `AWS_LAMBDA_LOG_STREAM_NAME` environment variables are not available in Lambda SnapStart functions" ([AWS env vars](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html)). Do not read them for log fields; use the MDC request id instead. JVM with SnapStart vs native is always an Ask-First decision in `developing-quarkus-amazon-lambda-v3-40` (family rule 3).
