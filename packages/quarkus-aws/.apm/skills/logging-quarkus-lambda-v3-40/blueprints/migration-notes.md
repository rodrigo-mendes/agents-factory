# Migration Notes

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. Items below are High unless tagged. No Quarkus 3.40 migration note on logging was found in the guides read; no changelog or migration-wiki page on logging was fetched (L4 in the register).

## Contents

- [Deprecations and removals](#deprecations-and-removals)
- [Moving from plain text to JSON](#moving-from-plain-text-to-json)
- [Compatibility matrix](#compatibility-matrix)

## Deprecations and removals

- `quarkus.log.console.json.enable` is deprecated for removal since 3.19; use `quarkus.log.console.json.enabled` ([JsonLogConfig at tag](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/logging-json/runtime/src/main/java/io/quarkus/logging/json/runtime/JsonLogConfig.java)). The deprecated key is also the fallback that makes the extension "effectively true" by default (medium confidence).
- `quarkus-test-amazon-lambda` and `LambdaClient` were removed in Quarkus 3.31 ([Migration Guide 3.31](https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31)); test with `quarkus-junit` and RestAssured against the mock event server.
- `quarkus.snapstart.enable` is deprecated since 3.26; use `quarkus.snapstart.enabled` ([all-config](https://quarkus.io/version/3.40/guides/all-config)). It is not logging, but it sits in the same `application.properties`.
- AWS: "any libraries related to aws-lambda-java-log4j (v1.0.0 or 1.0.1) should not be used under any circumstance" ([AWS Java logging](https://docs.aws.amazon.com/lambda/latest/dg/java-logging.html)). This does not apply to Quarkus apps, which use no Log4j backend ([never-do F2](./never-do-patterns.md#f2-log4j-dependencies-in-a-quarkus-app-severity-high)).
- AWS: a Lambda service change adds a `status` field (and `ErrorType` on crashes) to plain-text `REPORT` lines, and "you may see minor differences between the structure and content of system log messages" ([AWS lifecycle](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html)). Text-parsing metric filters must tolerate it.

## Moving from plain text to JSON

1. Add `io.quarkus:quarkus-logging-json` (BOM-managed, 3.40.1.1) ([POM](https://repo1.maven.org/maven2/io/quarkus/quarkus-logging-json/3.40.1.1/quarkus-logging-json-3.40.1.1.pom)).
2. Add `%dev.` and `%test.quarkus.log.console.json.enabled=false` ([logging guide](https://quarkus.io/version/3.40/guides/logging)).
3. Add the MDC put and remove for `AWSRequestId` and `tenantId` in each handler ([always-do 6](./always-do-patterns.md#6-put-request-id-and-tenant-id-into-mdc-and-clear-them), medium confidence).
4. Update Logs Insights queries and metric filters for the JSON field names (`level`, `message`, `mdc.*`) ([Verification Loop](./verification-loop.md#logs-insights-queries)).
5. Optionally set Lambda `LogFormat=JSON`, then `ApplicationLogLevel` and `SystemLogLevel` ([decision A3](./ask-first-decisions.md#a3-lambda-logformat)). Check whether any metric filter parses `REPORT` text first.

## Compatibility matrix

| Dependency | Min | Max | Notes |
|---|---|---|---|
| Quarkus | 3.40.0 | 3.40.x | 3.40.1.1 pinned (family rule 1) |
| `quarkus-logging-json` | 3.40.1.1 | 3.40.1.1 | BOM-managed |
| `aws-lambda-java-core` | 1.4.0 | 1.4.0 | As managed by `quarkus-bom` 3.40.1.1 (BOM partly read, L3) |
| Lambda Java runtimes with advanced logging controls | all except Java 8 on Amazon Linux 1 | `java25` | [AWS log formats](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-logformat.html); runtimes: [AWS runtimes](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html) |
| Lambda OS-only runtime (native) | `provided.al2023` | - | Log-level filtering only through the JSON `level` key; the poll loop does not read `AWS_LAMBDA_LOG_*` (medium confidence); `provided.al2023` per [AWS runtimes](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html) |
