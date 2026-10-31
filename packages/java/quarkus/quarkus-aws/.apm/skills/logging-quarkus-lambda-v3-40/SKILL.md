---
name: logging-quarkus-lambda-v3-40
description: "Teaches logging from Quarkus 3.40 LTS Lambda functions to CloudWatch Logs: quarkus-logging-json, MDC AWSRequestId/tenantId, Lambda logging controls, no PII or secrets. Use when configuring or reviewing Lambda logs. Not for tracing, metrics, Terraform, Powertools or Quarkus 4."
---

# Logging Quarkus AWS Lambda functions 3.40

> Version lock: every claim applies to **Quarkus 3.40 LTS, patch 3.40.1.1 (`quarkus-logging-json`, `quarkus-amazon-lambda`)** only. Research date **2026-10-28**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page; each maps to a line of the [register](./blueprints/unverified-and-risks.md#tag-to-register-mapping).
> Scope: JSON logs on stdout, MDC `AWSRequestId` and `tenantId` (family rule 7's `requestId` names the concept, not the key), Lambda advanced logging controls (`LogFormat`, `ApplicationLogLevel`, `SystemLogLevel`, `LogGroup`), log group retention, no PII or secrets.
> Neighbours in this package: [developing-quarkus-amazon-lambda-v3-40](../developing-quarkus-amazon-lambda-v3-40/SKILL.md) (plain handlers, packaging, SnapStart) and [developing-quarkus-amazon-lambda-http-v3-40](../developing-quarkus-amazon-lambda-http-v3-40/SKILL.md) (HTTP extensions). By name only: `tracing-quarkus-lambda-v3-40`, `monitoring-quarkus-lambda-v3-40`, `observing-quarkus-lambda`, `monitoring-cloudwatch-observability` (log infrastructure design), `provisioning-aws-cloudwatch-v6` (Terraform log groups and retention), `implementing-lambda-powertools-java` (Powertools). Quarkus 4 is out of scope.

## Version Context

| Item | Value | Source (fetched 2026-10-28) |
|---|---|---|
| Quarkus | 3.40 LTS, released 2026-09-30, community-maintained until 2027-09-30; patch 3.40.1.1 released 2026-10-19 | https://quarkus.io/releases |
| JSON extension | `io.quarkus:quarkus-logging-json` 3.40.1.1, POM description "Add JSON formatter for console logging" | https://repo1.maven.org/maven2/io/quarkus/quarkus-logging-json/3.40.1.1/quarkus-logging-json-3.40.1.1.pom |
| Logging guide | Version 3.40, read in full (two windows) | https://quarkus.io/version/3.40/guides/logging |
| Lambda interface | `aws-lambda-java-core` 1.4.0 (medium confidence) as managed by `quarkus-bom` 3.40.1.1 (BOM of 419,419 characters read by targeted extraction only; L3 in the register) | https://repo1.maven.org/maven2/io/quarkus/quarkus-bom/3.40.1.1/quarkus-bom-3.40.1.1.pom |
| Java managed runtimes | `java25`, `java21`, `java17.al2023` (AL2023, deprecation 2029-06-30); `java17` (AL2) 2027-06-30 | https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html |
| OS-only runtime | `provided.al2023` (deprecation 2029-06-30); its pairing with Quarkus native is (medium confidence) | https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html |
| Lambda advanced logging controls | "All Java runtimes except Java 8 on Amazon Linux 1" (current AWS documentation, not versioned) | https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-logformat.html |

**Version-lifetime risk** (as of 2026-10-28; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- Quarkus 4.0.0 is "Upcoming" with no date on the releases page; Beta1 was published 2026-10-01 with the final release "planned for the end of November" ([releases](https://quarkus.io/releases), [Beta1 post](https://quarkus.io/blog/quarkus-4-0-0-beta1-released/)). Pin 3.40.x.
- The AWS logging pages are current documentation and can change; `quarkus.log.console.json.enable` is deprecated for removal since 3.19 ([source at tag](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/logging-json/runtime/src/main/java/io/quarkus/logging/json/runtime/JsonLogConfig.java)).

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Ask-first decisions in depth](./blueprints/ask-first-decisions.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Quarkus JSON configuration](./blueprints/quarkus-json-config.md)
- [MDC and request id per mode](./blueprints/mdc-and-request-id.md)
- [Lambda logging controls, log groups, retention](./blueprints/lambda-logging-controls.md)
- [Verification Loop](./blueprints/verification-loop.md)
- [Migration notes](./blueprints/migration-notes.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Add `io.quarkus:quarkus-logging-json` to get JSON console logs.** The guide says "Add the `quarkus-logging-json` extension to enable the JSON logging format" ([logging guide](https://quarkus.io/version/3.40/guides/logging)). See [patterns](./blueprints/always-do-patterns.md#1-add-the-json-extension).
- **Turn JSON off in dev and test with `%dev.` and `%test.quarkus.log.console.json.enabled=false`.** The guide shows both lines ([logging guide](https://quarkus.io/version/3.40/guides/logging)). See [patterns](./blueprints/always-do-patterns.md#2-disable-json-in-dev-and-test).
- **Log through JBoss Logging or `io.quarkus.logging.Log` in application classes.** Lambda collects what a function writes to stdout or stderr ([AWS Java logging](https://docs.aws.amazon.com/lambda/latest/dg/java-logging.html)). See [patterns](./blueprints/always-do-patterns.md#3-log-through-jboss-logging-to-stdout).
- **Set levels per category with `quarkus.log.category."<name>".level`.** The root `quarkus.log.level` defaults to `INFO` ([logging guide](https://quarkus.io/version/3.40/guides/logging)). See [patterns](./blueprints/always-do-patterns.md#4-set-levels-per-category).
- **Set an explicit retention on the function's log group.** "By default, log data is stored in CloudWatch Logs indefinitely" ([CloudWatch log groups](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Working-with-log-groups-and-streams.html)). The HCL belongs to `provisioning-aws-cloudwatch-v6`. See [patterns](./blueprints/always-do-patterns.md#5-set-retention-on-the-log-group).

Patterns that cannot be High stay out of this list and live, tagged, in [always-do-patterns 6 to 9](./blueprints/always-do-patterns.md#6-put-request-id-and-tenant-id-into-mdc-and-clear-them): in particular putting `AWSRequestId` and `tenantId` into MDC yourself in JVM mode and clearing them in `finally` (medium confidence, read from source code, M2 in the register). Apply it whenever logs must carry a request id.

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Who produces the JSON | A: `quarkus-logging-json` writes JSON and Lambda "doesn't double-encode any logs that are already JSON encoded" (the option this skill proposes unless a Powertools standard exists). B: plain text plus Lambda `LogFormat=JSON`; what the runtime does with plain `System.out` lines is (unverified). C: Powertools logging; it needs log4j2 or logback while Quarkus says "Do not include any Log4j dependencies", so compatibility is (unverified); see `implementing-lambda-powertools-java`. [Decision A1](./blueprints/ask-first-decisions.md#a1-who-produces-the-json) | "Must an existing Powertools standard be kept? Otherwise propose A." |
| MDC placement, API and shape | Poll loop (native, dev, test) sets `AWSRequestId`; the JVM managed-runtime path sets no MDC (medium confidence). Guide uses `org.jboss.logmanager.MDC`, the poll loop `org.jboss.logging.MDC`; whether they share a store is (unverified). Nested `mdc.*` (default) vs `mdc.flat-fields=true`. Lambda's own JSON spells the key `AWSrequestId`, Quarkus `AWSRequestId`; case handling in Insights is (unverified). [A2](./blueprints/ask-first-decisions.md#a2-mdc-placement-api-and-shape) | "Do dashboards or queries expect root-level request id fields? Which MDC class does the code base already use?" |
| Lambda `LogFormat` Text or JSON | Text is the default for all runtimes; JSON enables log-level filtering and structured system logs but grows log size. [A3](./blueprints/ask-first-decisions.md#a3-lambda-logformat) | "Does any metric filter or query parse plain-text `REPORT` lines?" |
| Where the effective level is set | `QUARKUS_LOG_LEVEL` override (medium confidence); expression `${AWS_LAMBDA_LOG_LEVEL:INFO}` (medium confidence); Lambda `ApplicationLogLevel` only, which cannot raise detail above `quarkus.log.level`. Quarkus reading `AWS_LAMBDA_LOG_*` outside the poll loop is (unverified). [A4](./blueprints/ask-first-decisions.md#a4-where-the-effective-level-is-set) | "Who changes levels in production, and is TRACE ever needed (build-time `min-level`)?" |
| Default or custom log group, log class | Default `/aws/lambda/<function>` vs shared custom group (name must not start with `aws/`) vs Infrequent Access class (no Logs Insights field discovery); prices are (unverified). [A5](./blueprints/ask-first-decisions.md#a5-log-group-and-log-class) | "What retention is needed, and must Logs Insights work on this group?" |
| Renaming `level` or `timestamp`, `log-format=ecs` or `gcp` | Lambda filtering needs a `level` key and a valid timestamp, otherwise it assigns INFO; ECS and GCP rename those keys (medium confidence). [A6](./blueprints/ask-first-decisions.md#a6-structured-format-profile-and-key-names) | "Is Lambda log-level filtering used, or is an ECS consumer the only reader?" |
| Exception output type | `detailed` (default), `formatted`, `detailed-and-formatted`; relative size is not stated (medium confidence). [A7](./blueprints/ask-first-decisions.md#a7-exception-output) | "Are stack traces queried as structured frames or only read by humans?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Log `System.getenv()`, the whole event or secrets; Lambda sets `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` and `AWS_SESSION_TOKEN` in the environment ([AWS env vars](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html)) | Log identifiers and bounded facts only; read secrets from Secrets Manager, which AWS recommends over environment variables ([AWS env vars](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html)) |
| Add Log4j dependencies or AWS's `aws-lambda-java-log4j2` recipe to a Quarkus app; the guide says "Do not include any Log4j dependencies" ([logging guide](https://quarkus.io/version/3.40/guides/logging)) | Use `quarkus-logging-json`; add `org.jboss.logmanager:log4j2-jboss-logmanager` only when a library logs through the Log4j 2 API ([logging guide](https://quarkus.io/version/3.40/guides/logging)) |
| Name a custom log group starting with `aws/`; Lambda "won't be able to create the log group" and logs are not sent ([AWS log groups](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-loggroups.html)) | Use a name without that prefix, for example `orders-app` ([AWS log groups](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-loggroups.html)) |
| Set `quarkus.log.console.json.pretty-print=true`; the guide warns that "some JSON parsers will fail to read the pretty printed output" ([logging guide](https://quarkus.io/version/3.40/guides/logging)) | Keep `quarkus.log.console.json.pretty-print=false`, the guide's default ([logging guide](https://quarkus.io/version/3.40/guides/logging)) |
| Write the deprecated `quarkus.log.console.json.enable` (deprecated for removal since 3.19, [source at tag](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/logging-json/runtime/src/main/java/io/quarkus/logging/json/runtime/JsonLogConfig.java)) | Write `quarkus.log.console.json.enabled` ([source at tag](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/logging-json/runtime/src/main/java/io/quarkus/logging/json/runtime/JsonLogConfig.java)) |

Full ❌/✅ code: [never-do patterns](./blueprints/never-do-patterns.md). Unconfirmed items: [register](./blueprints/unverified-and-risks.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| Root level and build-time minimum | `quarkus.log.level` default `INFO`; `quarkus.log.min-level` default `DEBUG` (build time) | https://quarkus.io/version/3.40/guides/logging |
| Console handler | `quarkus.log.console.enabled` default `true`; `quarkus.log.console.stderr` default `false` (stdout) | https://quarkus.io/version/3.40/guides/logging |
| JSON pretty print | `quarkus.log.console.json.pretty-print` default `false` | https://quarkus.io/version/3.40/guides/logging |
| JSON exception output | `quarkus.log.console.json.exception-output-type` default `detailed`; `print-details` default `false` | https://quarkus.io/version/3.40/guides/logging |
| JSON format profile | `quarkus.log.console.json.log-format` default `default`; also `ecs`, `gcp` | https://quarkus.io/version/3.40/guides/logging |
| MDC in JSON | nested under `mdc`; `quarkus.log.console.json.mdc.flat-fields` default `false` | https://quarkus.io/version/3.40/guides/logging |
| Extra fixed field | `quarkus.log.console.json.additional-field."name".value` and `.type` (default `string`) | https://quarkus.io/version/3.40/guides/logging |
| Default log group | `/aws/lambda/<function name>`, created at first invoke | https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-loggroups.html |
| Lambda `LogFormat` default | plain text for all Lambda runtimes | https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-logformat.html |
| Retention | default indefinite; deletion after retention "typically takes up to 72 hours" | https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Working-with-log-groups-and-streams.html |
| Logs Insights limits | field discovery only in the Standard log class; a maximum of 200 fields extracted from a JSON log | https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_AnalyzeLogData-discoverable-fields.html |
| Insights query on MDC | `mdc.AWSRequestId`, `mdc.tenantId` dot notation (medium confidence) | https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_AnalyzeLogData-discoverable-fields.html |
| CloudWatch free tier | "5 GB Data (ingestion, archive storage, and data scanned by Logs Insights queries)"; prices not quoted (unverified) | https://aws.amazon.com/cloudwatch/pricing/ |

## External Resources

All fetched 2026-10-28.

- Quarkus 3.40 logging guide: https://quarkus.io/version/3.40/guides/logging
- AWS Java logging: https://docs.aws.amazon.com/lambda/latest/dg/java-logging.html
- AWS JSON and text log formats: https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-logformat.html
- AWS log-level filtering: https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-log-level.html
- AWS log groups: https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-loggroups.html
- Full bibliography: [unverified and risks](./blueprints/unverified-and-risks.md#source-bibliography)
