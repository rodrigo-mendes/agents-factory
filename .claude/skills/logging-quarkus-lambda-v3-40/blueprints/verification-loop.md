# Verification Loop

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. Commands are representative: adapt names and paths to your project. Expected output is what the cited pages and source describe.

## Contents

- [Build and configuration checks](#build-and-configuration-checks)
- [Invoke and read the log](#invoke-and-read-the-log)
- [Logs Insights queries](#logs-insights-queries)
- [Tests](#tests)
- [Checklist](#checklist)

## Build and configuration checks

```bash
# Representative - Quarkus 3.40.1.1
# 1. Extension present
mvn -q dependency:tree -Dincludes=io.quarkus:quarkus-logging-json
# Expected: io.quarkus:quarkus-logging-json:jar:3.40.1.1

# 2. Config keys present, deprecated key absent (never-do F5)
grep -nE "quarkus\.log\.console\.json\.(enabled|pretty-print|log-format)" src/main/resources/application.properties
grep -n "quarkus.log.console.json.enable=" src/main/resources/application.properties
# Expected for the second command: no match

# 3. No Log4j backend on the classpath (never-do F2)
mvn -q dependency:tree -Dincludes=org.apache.logging.log4j:log4j-core,com.amazonaws:aws-lambda-java-log4j2
# Expected: no output

# 4. No dumping of the environment or the whole event (never-do F1)
grep -rnE "System\.getenv\(\)|writeValueAsString\(event" src/main/java
# Expected: no match
```

## Invoke and read the log

```bash
# Representative - tail of the log, up to 4 KB, base64-encoded (AWS Java logging)
aws lambda invoke --function-name orders out --log-type Tail \
  --query 'LogResult' --output text --cli-binary-format raw-in-base64-out | base64 --decode
# Expected: START/END/REPORT lines plus one-line JSON records with "level" and "mdc":{"AWSRequestId":...}

# Current Lambda logging configuration
aws lambda get-function-configuration --function-name orders --query LoggingConfig
# Expected: LogFormat, ApplicationLogLevel, SystemLogLevel and LogGroup "/aws/lambda/orders" (output shape: medium confidence)
```

If `mdc` is empty on a JVM function, the handler did not put the id (see [MDC and request id](./mdc-and-request-id.md)); if it is empty after a put, the MDC class question is open (unverified, [U4](./unverified-and-risks.md#unverified-items)).

## Logs Insights queries

Standard log class only; dot notation for nested JSON; Quarkus key names and `mdc.<key>` queries are (medium confidence) ([discovered fields](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_AnalyzeLogData-discoverable-fields.html)).

```text
fields @timestamp, level, message, mdc.AWSRequestId, mdc.tenantId
| filter level = "ERROR"
| sort @timestamp desc
```

```text
fields @timestamp, @requestId, @duration, @billedDuration, @maxMemoryUsed
| filter @type = "REPORT"
```

Lambda logs get the discovered fields `@requestId`, `@duration`, `@billedDuration`, `@type`, `@maxMemoryUsed` and `@memorySize`, "but only for the first embedded JSON fragment in each log event"; at most 200 fields are extracted from a JSON log. Whether `@type = "REPORT"` also matches when the system log format is JSON, or on an OS-only runtime, is (unverified): verify with one invoke.

## Tests

```java
// Quarkus 3.40 - @QuarkusTest against the mock event server (illustrative, medium confidence)
@QuarkusTest
class OrdersLambdaTest {
    @Test
    void logsDoNotFailInvocation() {
        given().contentType("application/json").body(new OrderEvent(/*...*/))
               .when().post().then().statusCode(200);
    }
}
```

`quarkus-test-amazon-lambda` and `LambdaClient` were removed in Quarkus 3.31; test with `quarkus-junit` and RestAssured against the mock event server ([Migration Guide 3.31](https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31)); see `testing-quarkus-amazon-lambda-v3-40`. The guide says tests need the `java.util.logging.manager` system property set to `org.jboss.logmanager.LogManager`; which setups need it is (medium confidence). The mock-server path sets MDC `AWSRequestId` through the poll loop (medium confidence), so it does not prove the JVM handler path.

## Checklist

- [ ] `quarkus-logging-json` on the classpath, `enabled=true` in production, `false` in `%dev` and `%test`
- [ ] `pretty-print` not set to `true`; no `quarkus.log.console.json.enable`
- [ ] No Log4j artifact in the dependency tree
- [ ] Every handler puts and clears `AWSRequestId` and `tenantId` in `finally` (JVM mode; medium confidence, M2)
- [ ] One invoke shows one-line JSON with `level` and `mdc`
- [ ] No environment dump, no event dump, no tokens in any log call
- [ ] Log group retention set in IaC (`provisioning-aws-cloudwatch-v6`)
