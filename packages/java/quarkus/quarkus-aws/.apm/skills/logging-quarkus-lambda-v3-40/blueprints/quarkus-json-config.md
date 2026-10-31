# Quarkus JSON Configuration

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. Keys and defaults come from the 3.40 logging guide ([logging guide](https://quarkus.io/version/3.40/guides/logging)) unless a line says otherwise. The all-config page served no `quarkus.log.console.json.*` keys (L1 in the register), so these defaults are stated per key from the guide.

## Contents

- [How logging is wired in 3.40](#how-logging-is-wired-in-340)
- [Enabled default](#enabled-default)
- [Reference application.properties](#reference-applicationproperties)
- [Key names and timestamp](#key-names-and-timestamp)
- [Format profiles](#format-profiles)
- [Exception and size controls](#exception-and-size-controls)
- [Native mode](#native-mode)

## How logging is wired in 3.40

- Quarkus logs through JBoss Logging on top of JBoss LogManager. The `io.quarkus.logging.Log` API is rewritten at build time into a `private static final org.jboss.logging.Logger` field per application class.
- Defaults: `quarkus.log.level` `INFO`; `quarkus.log.min-level` `DEBUG` (build time); `quarkus.log.console.enabled` `true`; `quarkus.log.console.stderr` `false`; console pattern `%d{yyyy-MM-dd HH:mm:ss,SSS} %-5p [%c] (%t) %s%e%n` ([logging guide](https://quarkus.io/version/3.40/guides/logging), [all-config](https://quarkus.io/version/3.40/guides/all-config)).
- Category levels: `quarkus.log.category."<name>".level`. Init: nothing to initialise for logging, because the `Log` API is wired at build time.
- With JSON active "any format string or color settings are ignored" ([logging guide](https://quarkus.io/version/3.40/guides/logging)).

## Enabled default

In the 3.40.1.1 source, `quarkus.log.console.json.enabled` is `Optional<Boolean>` with no `@WithDefault`. The recorder evaluates `config.enabled().orElse(config.enable())`, and the deprecated `enable()` is `@WithDefault("true")` ([JsonLogConfig](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/logging-json/runtime/src/main/java/io/quarkus/logging/json/runtime/JsonLogConfig.java), [LoggingJsonRecorder](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/logging-json/runtime/src/main/java/io/quarkus/logging/json/runtime/LoggingJsonRecorder.java)). So adding the extension turns console JSON on ("effectively true", medium confidence): it is derived from code, not stated on a page. Write `enabled=true` explicitly in production and `false` in `%dev` and `%test`. Do not group this key under a shared default with other keys.

## Reference application.properties

```properties
# Quarkus 3.40 - illustrative composition of documented keys (medium confidence)
quarkus.lambda.handler=orders
quarkus.log.level=INFO
quarkus.log.category."software.amazon.awssdk".level=WARN
quarkus.log.console.json.enabled=true
%dev.quarkus.log.console.json.enabled=false
%test.quarkus.log.console.json.enabled=false
quarkus.log.console.json.additional-field."service".value=orders
# optional (decision A2): quarkus.log.console.json.mdc.flat-fields=true
```

`additional-field."field-name".value` and `.type` (`string`, `int`, `long`; default `string`) ([logging guide](https://quarkus.io/version/3.40/guides/logging)). `quarkus.lambda.handler` selects the CDI-named handler ([aws-lambda guide](https://quarkus.io/version/3.40/guides/aws-lambda)); see `developing-quarkus-amazon-lambda-v3-40`.

## Key names and timestamp

The JSON formatter extends the JBoss LogManager JSON formatter ([JsonFormatter](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/logging-json/runtime/src/main/java/io/quarkus/logging/json/runtime/JsonFormatter.java)); its key names are not defined in the Quarkus source. From jboss-logmanager `StructuredFormatter` (main branch; version used by 3.40.1.1 not confirmed): keys include `timestamp`, `level`, `message`, `loggerName`, `loggerClassName`, `mdc`, `ndc`, `sequence`, `threadName`, `threadId`, `hostName`, `processName`, `processId`, `exception`, `stackTrace`; default timestamp `ISO_OFFSET_DATE_TIME` (medium confidence). Whether that output satisfies RFC 3339 is an inference (medium confidence). Lambda needs `level` and a valid timestamp for filtering ([AWS log-level filtering](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-log-level.html)), so leave `key-overrides` and `date-format` alone for these two keys. How JUL levels render in `level` is (unverified).

## Format profiles

| Profile | Effect | Lambda filtering |
|---|---|---|
| `default` (default) | Keys as above | Works with `level` and `timestamp` |
| `ecs` | `timestamp` becomes `@timestamp`, `level` becomes `log.level` (source at tag 3.40.1.1, medium confidence) | Breaks (medium confidence) |
| `gcp` | `level` becomes `severity` (medium confidence) | Breaks (medium confidence) |

See [decision A6](./ask-first-decisions.md#a6-structured-format-profile-and-key-names).

## Exception and size controls

| Key | Default | Note |
|---|---|---|
| `quarkus.log.console.json.pretty-print` | `false` | Keep `false`; see [F4](./never-do-patterns.md#f4-pretty-printed-json-severity-moderate) |
| `quarkus.log.console.json.exception-output-type` | `detailed` | Options `detailed`, `formatted`, `detailed-and-formatted`; size effect not stated (medium confidence) |
| `quarkus.log.console.json.print-details` | `false` | Guide: details "can be expensive" |
| `quarkus.log.console.async.enabled` | `false` | Queue 512, overflow `block`; interaction with the Lambda freeze after return is (unverified); keep the default |

A multi-line record splits into several CloudWatch events (medium confidence); a one-line record keeps a stack trace in one event (medium confidence). The record delimiter defaults to newline ([logging guide](https://quarkus.io/version/3.40/guides/logging)).

## Native mode

- With `min-level` at INFO, lower-level checks "always ... return `false`" and become dead code ([logging guide](https://quarkus.io/version/3.40/guides/logging)).
- Libraries logging through SLF4J, Commons Logging or Log4j 2 need the JBoss adapters, or "the native build can fail" ([logging guide](https://quarkus.io/version/3.40/guides/logging)).
- The poll loop runs in native builds (`@BuildStep(onlyIf = NativeBuild.class)` to `startPollLoop`) and sets MDC `AWSRequestId` (medium confidence, source at tag); see [MDC and request id](./mdc-and-request-id.md).
- Whether `quarkus-logging-json` has any native-specific limitation is not stated (unverified). Build native in CI and check one JSON line.
- Tests: the guide says that for tests "it is necessary to set the `java.util.logging.manager` system property to `org.jboss.logmanager.LogManager`"; which test setups need it was only partly read (medium confidence). Keep JSON off in `%test`.
