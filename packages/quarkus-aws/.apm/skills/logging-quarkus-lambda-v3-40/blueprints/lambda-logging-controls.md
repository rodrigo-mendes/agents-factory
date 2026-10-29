# Lambda Logging Controls, Log Groups, Retention

Back to [SKILL.md](../SKILL.md). Fetched 2026-10-28. The AWS pages are current documentation (not versioned). Scope: how Lambda's advanced logging controls interact with a Quarkus 3.40 function; the log group IaC is out of scope (`provisioning-aws-cloudwatch-v6`).

## Contents

- [Advanced logging controls](#advanced-logging-controls)
- [LogFormat JSON and ApplicationLogLevel](#logformat-json-and-applicationloglevel)
- [Quarkus and the AWS_LAMBDA_LOG variables](#quarkus-and-the-aws_lambda_log-variables)
- [Log groups, retention and cost](#log-groups-retention-and-cost)
- [Masking](#masking)
- [System log levels](#system-log-levels)

## Advanced logging controls

`LoggingConfig` carries `LogFormat` (JSON or Text), `ApplicationLogLevel`, `SystemLogLevel` and `LogGroup`. They apply to "All Java runtimes except Java 8 on Amazon Linux 1" ([AWS log formats](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-logformat.html), overview: [AWS monitoring logs](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-logs.html)). Whether they behave the same on an OS-only runtime for system logs and the `@type` and `@requestId` discovered fields is (unverified).

## LogFormat JSON and ApplicationLogLevel

- Lambda's own JSON wrapping of application logs covers only `LambdaLogger` and Log4j2. Any other library, the JBoss LogManager included, must itself write JSON with a `"level"` key and an RFC 3339 `"timestamp"`; otherwise Lambda assigns INFO ([AWS Java logging](https://docs.aws.amazon.com/lambda/latest/dg/java-logging.html), [AWS log-level filtering](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-log-level.html)).
- Lambda "doesn't double-encode any logs that are already JSON encoded" ([AWS log formats](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-logformat.html)). So `quarkus-logging-json` output passes through; the line then carries the `mdc` object.
- "To use log-level filtering, your Event Function must be configured to use the JSON log format" ([AWS log-level filtering](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-log-level.html)).
- Level-less text lines are INFO; they are dropped when `ApplicationLogLevel` is above INFO (medium confidence).
- Lambda filters only what the code emits; Quarkus drops lines below `quarkus.log.level` first. Decision: [A4](./ask-first-decisions.md#a4-where-the-effective-level-is-set).
- `ApplicationLogLevel=TRACE` via the CLI: table and CLI text disagree (medium confidence).
- What the runtime does with plain `System.out` text under `LogFormat=JSON` is (unverified); use the extension.
- Switching to JSON without levels sets application and system levels to `INFO`; JSON "can increase" log size; the change affects only new logs.

## Quarkus and the AWS_LAMBDA_LOG variables

Lambda sets `AWS_LAMBDA_LOG_LEVEL` and `AWS_LAMBDA_LOG_FORMAT` "to integrate Lambda advanced logging controls into a custom runtime" ([AWS log-level filtering](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-log-level.html)); they are not in the reserved list of the environment variables page ([AWS env vars](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html)). Quarkus's poll loop does not read them (medium confidence, source at tag); whether any other Quarkus component does is (unverified). Therefore `LoggingConfig` alone does not change Quarkus levels or format.

## Log groups, retention and cost

- "By default, CloudWatch automatically creates a log group named `/aws/lambda/<function name>` ... when it's first invoked" ([AWS log groups](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-loggroups.html)). Creating the group with retention in IaC before the first invoke is an inference (medium confidence).
- Custom group names "mustn't begin with the string `aws/`" ([never-do F3](./never-do-patterns.md#f3-custom-log-group-starting-with-aws-severity-high)).
- Retention default is indefinite; Lambda never deletes the log group; deletion after retention "typically takes up to 72 hours" ([CloudWatch log groups](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Working-with-log-groups-and-streams.html), [AWS Java logging](https://docs.aws.amazon.com/lambda/latest/dg/java-logging.html)).
- One log stream per execution environment instance; a shared custom group keeps streams apart by function name and version. Lambda Managed Instances interleave concurrent invocations in one stream and "only support the JSON log format", which is why the request id must be in each entry (out of scope beyond this note) ([AWS log groups](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-loggroups.html)).
- Execution role: `logs:PutLogEvents`, included in `AWSLambdaBasicExecutionRole` (medium confidence); see [always-do 8](./always-do-patterns.md#8-grant-putlogevents-to-the-execution-role).
- Cost: JSON "adds additional metadata ... the size of your Event Function's log messages can increase" ([AWS log formats](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-logformat.html)); filtering "helps you manage storage costs" ([AWS monitoring logs](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-logs.html)). Free tier: "5 GB Data (ingestion, archive storage, and data scanned by Logs Insights queries)" ([pricing](https://aws.amazon.com/cloudwatch/pricing/)). Per-GB prices were not rendered and the page examples conflict ($0.25 vs $0.50 per GB for the same scenario): (unverified). Do not quote numbers. The page was read 0 to 100,000 of 154,061 characters (L5).

## Masking

CloudWatch data protection policies can mask credentials, financial data, PII, PHI and device ids at ingest; only `logs:Unmask` holders see raw data; events ingested before the policy exists "are not masked" ([masking](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/mask-sensitive-log-data.html)). Masking is a second line of defence, not a reason to log sensitive data (never-do [F1](./never-do-patterns.md#f1-logging-environment-variables-the-event-or-secrets-severity-high)).

## System log levels

AWS maps system log levels per event (for example a `report` status other than success maps to WARN, and `logsDropped` maps to WARN). Keep `SystemLogLevel` at least `WARN` so failures stay visible ([AWS log-level filtering](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-log-level.html)). A Lambda service change adds a `status` field (and `ErrorType` on crashes) to plain-text `REPORT` lines, so text-parsing metric filters must tolerate minor differences ([AWS lifecycle](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html)). Metrics and alarms belong to `monitoring-quarkus-lambda-v3-40` and `monitoring-cloudwatch-observability`.
