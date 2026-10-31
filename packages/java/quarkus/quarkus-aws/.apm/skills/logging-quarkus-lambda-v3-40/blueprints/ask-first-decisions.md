# Ask-First Decisions

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. Each decision lists options, a tradeoff table and the question to put to the user. Do not choose silently.

## Contents

- [A1. Who produces the JSON](#a1-who-produces-the-json)
- [A2. MDC placement, API and shape](#a2-mdc-placement-api-and-shape)
- [A3. Lambda LogFormat](#a3-lambda-logformat)
- [A4. Where the effective level is set](#a4-where-the-effective-level-is-set)
- [A5. Log group and log class](#a5-log-group-and-log-class)
- [A6. Structured format profile and key names](#a6-structured-format-profile-and-key-names)
- [A7. Exception output](#a7-exception-output)

## A1. Who produces the JSON

- A: `quarkus-logging-json` writes JSON to stdout; Lambda passes it through because it "doesn't double-encode any logs that are already JSON encoded" ([AWS log formats](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-logformat.html)). Lambda's own JSON wrapping covers only `LambdaLogger` and Log4j2; any other library must write JSON with a `level` key itself ([AWS Java logging](https://docs.aws.amazon.com/lambda/latest/dg/java-logging.html)).
- B: Quarkus plain text plus Lambda `LogFormat=JSON`. What the Java runtime does with plain `System.out` lines is (unverified); text lines carry no `level`, so Lambda assigns INFO ([AWS log-level filtering](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-log-level.html)).
- C: Powertools for AWS Lambda (Java) logging requires "either log4j2 or logback as your log provider" ([Powertools logging](https://docs.aws.amazon.com/powertools/java/latest/core/logging/)), while Quarkus says "Do not include any Log4j dependencies" ([logging guide](https://quarkus.io/version/3.40/guides/logging)). Whether it works with Quarkus 3.40 is (unverified). Name `implementing-lambda-powertools-java` only.

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A | Documented on both sides; MDC and additional fields | One more extension | Default for this family (family rule 7) |
| B | No extension | Behaviour (unverified); no MDC fields; text lines get INFO | Not recommended |
| C | Lambda-context keys, sampling | Quarkus compatibility (unverified) | Only after a spike and an ADR |

Ask: "Must an existing Powertools standard be kept? Otherwise propose A."

## A2. MDC placement, API and shape

- Placement: the handler body or, for the HTTP extension, a Jakarta REST filter or the resource method. Which is better is a design choice (medium confidence, M18). Per-mode behaviour: [MDC and request id](./mdc-and-request-id.md).
- API: the 3.40 guide's MDC examples use `org.jboss.logmanager.MDC`; the Quarkus poll loop uses `org.jboss.logging.MDC`. Same store: (unverified). Default to the guide's class.
- Shape: nested (default, `"mdc":{"AWSRequestId":"..."}`) or flat with `quarkus.log.console.json.mdc.flat-fields=true` ([logging guide](https://quarkus.io/version/3.40/guides/logging)).

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| Nested | No key collisions with formatter keys | Queries use `mdc.AWSRequestId` (medium confidence) | Many MDC keys |
| Flat | Root-level `AWSRequestId` as in AWS's own Java JSON (spelling differs, (unverified) case handling) | Collision risk with `level` or `message` | Simple Logs Insights queries |

Ask: "Do existing dashboards or queries expect root-level request id fields? Which MDC class does the code base already use?"

## A3. Lambda LogFormat

- Text: "the default log format for all Lambda runtimes is plain text" ([AWS log formats](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-logformat.html)).
- JSON: system logs become `{"time","type","record"}` objects; switching without levels sets application and system levels to `INFO`; JSON can increase log size; the change affects only new logs. "To use log-level filtering, your Event Function must be configured to use the JSON log format" ([AWS log-level filtering](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-log-level.html)). AWS recommends JSON ("we recommend that you select JSON").

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| Text | Smaller system lines, existing text tooling | No Lambda level filtering | Tooling parses `START`, `END`, `REPORT` text |
| JSON | Filtering, structured `platform.*` records | Size; queries on `REPORT` text change | AWS's recommendation |

Ask: "Does any metric filter or query parse plain-text REPORT lines before we switch?"

## A4. Where the effective level is set

- A: `quarkus.log.level`, overridden at deploy time by `QUARKUS_LOG_LEVEL`. Env vars (ordinal 300) override `application.properties` (250) ([config reference](https://quarkus.io/version/3.40/guides/config-reference)). That `quarkus.log.level` is runtime-overridable is inferred from the guide calling only `min-level` build-time (medium confidence).
- B: `quarkus.log.level=${AWS_LAMBDA_LOG_LEVEL:INFO}`. Expressions work with env vars and accept defaults; Lambda sets `AWS_LAMBDA_LOG_LEVEL` when application log-level filtering is configured. That the mapping behaves as expected is (medium confidence). Quarkus reading `AWS_LAMBDA_LOG_*` anywhere else is (unverified); the poll loop does not.
- C: Lambda `ApplicationLogLevel` only. "If you set your Event Function's log level in your code, this setting takes precedence"; Quarkus drops lines below `quarkus.log.level` before Lambda sees them. So `ApplicationLogLevel=DEBUG` shows no DEBUG lines that Quarkus never emitted (quarkus default `INFO`).
- `ApplicationLogLevel=TRACE` via the CLI: the AWS table lists TRACE, the CLI text lists DEBUG, INFO, WARN, ERROR, FATAL (medium confidence). TRACE in Quarkus needs `quarkus.log.min-level=TRACE` at build time.

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A | Pure Quarkus; JVM and native | Two knobs (Quarkus and Lambda) | Teams that own app config |
| B | One knob in `LoggingConfig` | Depends on Lambda setting the variable | Ops-driven level changes |
| C | No app change | Cannot raise detail above `quarkus.log.level` | Lowering noise only |

Ask: "Who changes log levels in production, dev team or ops, and is TRACE ever needed?" An `update-function-configuration --environment` call "replaces" the whole `Variables` structure ([AWS env vars](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html)): include the existing variables.

## A5. Log group and log class

- Default group `/aws/lambda/<function name>`, auto-created at first invoke. Custom group through `LoggingConfig.LogGroup`: many functions may share it, streams are named `YYYY/MM/DD/<function_name>[<function_version>][<execution_environment_GUID>]` ([AWS log groups](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-loggroups.html)).
- Logs Insights field discovery is "supported only for log groups in the Standard log class" ([discovered fields](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_AnalyzeLogData-discoverable-fields.html)). Data protection masking works in Standard and Infrequent Access ([masking](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/mask-sensitive-log-data.html)).

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| Default per function | Zero config, per-function retention | Many groups | Default |
| Shared custom group | One retention and IAM scope per app | Name must not start with `aws/`; shared retention | Many small functions of one app |
| Infrequent Access class | Cost, prices (unverified) | No Logs Insights field discovery | Archive-only logs |

Ask: "What retention is needed, and must Logs Insights work on this group?" IaC goes to `provisioning-aws-cloudwatch-v6`; design to `monitoring-cloudwatch-observability`.

## A6. Structured format profile and key names

- `quarkus.log.console.json.log-format` accepts `default`, `ecs` (Elastic Common Schema) and `gcp` ([logging guide](https://quarkus.io/version/3.40/guides/logging)). In source at tag 3.40.1.1, ECS renames `timestamp` to `@timestamp` and `level` to `log.level`, and GCP renames `level` to `severity` (medium confidence). Lambda filtering needs `level` and a valid timestamp ([AWS log-level filtering](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-log-level.html)); a missing one makes Lambda assign INFO, so ERROR lines can be dropped when `ApplicationLogLevel` is WARN or higher (medium confidence).
- The default key names and timestamp format are (medium confidence). How JUL levels (SEVERE, WARNING, FINE) render in `level` and whether Lambda accepts them is (unverified).
- Choose `ecs` only when logs go to an ECS consumer and Lambda filtering is not used.

Ask: "Is Lambda log-level filtering used, or is an ECS consumer the only reader of these logs?"

## A7. Exception output

`quarkus.log.console.json.exception-output-type` default `detailed`; options `detailed`, `formatted`, `detailed-and-formatted`. `print-details` default `false`; the guide warns details "can be expensive" ([logging guide](https://quarkus.io/version/3.40/guides/logging)). Relative size per option is not stated (medium confidence).

Ask: "Are stack traces queried as structured frames, or only read by humans?"
