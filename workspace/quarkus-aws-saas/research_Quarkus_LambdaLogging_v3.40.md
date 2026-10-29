# Research: Logging in Quarkus 3.40 LTS AWS Lambda functions into CloudWatch Logs (v3.40)

> Unit U11 -> future skill `logging-quarkus-lambda-v3-40` (package `quarkus-aws`).
> Target: Quarkus 3.40 LTS, patch 3.40.1.1. Research date (read date of every source): 2026-10-28.
> Spec: `.claude/skills/researching-technical-frameworks/SKILL.md` + `blueprints/output-format-template.md`.
> Family facts/rules applied as given: `workspace/quarkus-aws-saas/_family_facts_v3.40.md`, `_family_rules_v3.40.md` (rules 7, 9-12), inherited `workspace/_family_facts_v3.40.md`, `workspace/_family_rules_v3.40.md`.
> Approval: relayed by the orchestrator (scope + fan-out approved by the user on 2026-10-28, recorded in `workspace/quarkus-aws-saas/PIPELINE_STATE.md#approvals`). No new approval was requested or implied.
> Evidence rule (family rule 5): High = a versioned official page (quarkus.io/version/3.40, source at tag 3.40.1.1, Maven Central POM) or the current AWS documentation page read by the researcher. Main-branch sources and inferences = (medium confidence). No page = (unverified). Facts read from Quarkus source code (not a guide statement) are tagged (medium confidence) to match family fact 24.
> Source ids `[Sn]` resolve in the Source Bibliography. Tag notation: plain `(medium confidence)` / `(unverified)`.

---

## Metadata

```yaml
Full_Name: Quarkus 3.40 LTS logging (JBoss Logging / JBoss LogManager, quarkus-logging-json) on AWS Lambda (quarkus-amazon-lambda) with CloudWatch Logs and Lambda advanced logging controls
Target_Version: Quarkus 3.40 LTS, patch 3.40.1.1 (quarkus-logging-json 3.40.1.1; aws-lambda-java-core 1.4.0 as managed by quarkus-bom 3.40.1.1)
Release_Date: Quarkus 3.40 released 2026-09-30; 3.40.1.1 on 2026-10-19 (family fact, https://quarkus.io/releases)
Support_Status: LTS, community-maintained until 2027-09-30 (family fact, https://quarkus.io/releases)
Primary_Docs: https://quarkus.io/version/3.40/guides/logging ; https://docs.aws.amazon.com/lambda/latest/dg/java-logging.html
Official_Repo: https://github.com/quarkusio/quarkus/tree/3.40.1.1
Research_Date: 2026-10-28
Domain_Complexity: Standard
Research_Depth: deep
Max_Iterations: 3
Gap_Loop_Ran: true
Iterations_Used: 3 of 3
Triangulated_Count: 4          # A1, A3, A5, A7
Unverified_Count: 9            # U1..U9 (Research Gaps)
Irresolvable_Count: 4          # U1, U2, U3, U6 after the gap loop
Research_Quality_Score: 81%    # approximate: ~70 sourced claims counted; (70 - 9 - 4) / 70
```

Scope covered: Quarkus 3.40 logging basics that matter on Lambda; JSON logging (`quarkus-logging-json`); MDC for `requestId`/`tenantId`; how the Lambda request id reaches the log; Lambda advanced logging controls (`LoggingConfig`) and their interaction with Java and OS-only runtimes; `AWS_LAMBDA_LOG_FORMAT` / `AWS_LAMBDA_LOG_LEVEL`; log group naming, retention, cost; no PII/secrets (family rule 7); native-mode differences; structured fields for Logs Insights.

Out of scope (pointers only): tracing (U12), metrics (U13), Powertools logging (`implementing-lambda-powertools-java`), log infrastructure design (`monitoring-cloudwatch-observability`), Quarkus 4 (family rule 1), IaC (retention and log groups go to `provisioning-aws-cloudwatch-v6`, family rule 4).

---

## Executive Summary

Quarkus 3.40 logs through JBoss Logging on top of JBoss LogManager. The `io.quarkus.logging.Log` API is rewritten at build time into a `private static final org.jboss.logging.Logger` field per application class. Levels are set per category with `quarkus.log.category."<name>".level`; the root `quarkus.log.level` defaults to `INFO` and the build-time `quarkus.log.min-level` defaults to `DEBUG`. The console handler writes to `System.out` by default (`quarkus.log.console.stderr=false`) with the pattern `%d{yyyy-MM-dd HH:mm:ss,SSS} %-5p [%c] (%t) %s%e%n` [S1][S3]. In 3.40, JSON logging is not a built-in core switch. It comes from the `io.quarkus:quarkus-logging-json` extension (3.40.1.1 POM: "Add JSON formatter for console logging"). Once the extension is on the classpath, console JSON is on unless `quarkus.log.console.json.enabled=false`: `enabled` has no default, and the code falls back to the deprecated `enable` key, which defaults to `true` [S1][S5][S6][S7]. MDC entries go under a nested `"mdc"` object, or at root level with `quarkus.log.console.json.mdc.flat-fields=true` [S1].

On the AWS side, Lambda sends everything a Java function writes to stdout/stderr to the CloudWatch Logs group `/aws/lambda/<function name>` [S15][S19]. Advanced logging controls (`LoggingConfig`: `LogFormat` JSON/Text, `ApplicationLogLevel`, `SystemLogLevel`, `LogGroup`) apply to "All Java runtimes except Java 8 on Amazon Linux 1". Lambda's own JSON wrapping of application logs covers only `LambdaLogger` and Log4j2 [S17]. Any other library, Quarkus's JBoss LogManager included, must itself write JSON with a `"level"` key and an RFC 3339 `"timestamp"`; otherwise Lambda treats the line as `INFO`. Lambda "doesn't double-encode any logs that are already JSON encoded" [S15][S17][S18]. The Quarkus Lambda runtime does not read `AWS_LAMBDA_LOG_LEVEL` / `AWS_LAMBDA_LOG_FORMAT`; this was checked in the 3.40.1.1 poll loop [S9], and no Quarkus page says otherwise (unverified for the rest of Quarkus). The request id reaches the log differently per mode. In native and dev/test mode, the 3.40.1.1 poll loop puts it into JBoss MDC under the key `AWSRequestId` and removes it after each invocation. In JVM mode on the managed Java runtime, the code path (`QuarkusStreamHandler` -> `AmazonLambdaRecorder.handle`) sets no MDC, so the handler must put `Context.getAwsRequestId()` into MDC itself [S9][S10][S11][S12] (medium confidence: source code, not a guide statement).

Three critical patterns: (1) emit one-line JSON via `quarkus-logging-json`, keep the `level` and `timestamp` keys under those names, and disable JSON in `%dev`/`%test` [S1][S6][S18]; (2) put `AWSRequestId` and `tenantId` into MDC at the start of every invocation and remove them in `finally`; never log secrets, tokens or PII (family rule 7) [S9][S20][S21]; (3) set an explicit retention on the log group, because CloudWatch keeps log data "indefinitely" by default and Lambda never deletes the log group [S15][S23]. Domain complexity tier is **Standard**. The work touches several concerns (two logging stacks that must agree on JSON keys, two runtimes: JVM managed and native OS-only, cost, security/PII), but it involves no auth or crypto of its own.

---

## Architectural Guardrails

> Confidence legend: 🟢 High (2+ official sources, dated <=12mo) | 🟡 Medium (1 source, main-branch source, source-code reading or inference) | 🔴 Low (community source or dated >24mo - verify before use)

### ✅ Mandatory Patterns

**A1. Produce JSON logs with `quarkus-logging-json` (3.40.1.1); keep it off in dev/test**
> Confidence: 🟢 High | [✓✓ Triangulated | logging guide 3.40 (2026-10-28) + `quarkus-logging-json-3.40.1.1.pom` (2026-10-28) + `JsonLogConfig.java`/`LoggingJsonRecorder.java` at tag 3.40.1.1 (2026-10-28)]
- Why: the 3.40 guide says "Add the `quarkus-logging-json` extension to enable the JSON logging format and its related configuration". When it is active, "any format string or color settings are ignored" [S1]. The guide shows `%dev.quarkus.log.console.json.enabled=false` and `%test.quarkus.log.console.json.enabled=false` [S1]. In the 3.40.1.1 source, `enabled` is `Optional<Boolean>` with no `@WithDefault`. The recorder evaluates `config.enabled().orElse(config.enable())`, and `enable()` is `@WithDefault("true")` and `@Deprecated(forRemoval = true, since = "3.19")` [S6][S7]. Adding the extension therefore turns console JSON on. The default is called "effectively true" here because it is derived from code, not stated on a page (medium confidence). Lambda log-level filtering for non-`LambdaLogger`/non-Log4j2 libraries needs JSON on stdout/stderr [S15][S18].
- Code:
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
  %dev.quarkus.log.console.json.enabled=false
  %test.quarkus.log.console.json.enabled=false
  ```
- Source: https://quarkus.io/version/3.40/guides/logging (2026-10-28); https://repo1.maven.org/maven2/io/quarkus/quarkus-logging-json/3.40.1.1/quarkus-logging-json-3.40.1.1.pom (2026-10-28); https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/logging-json/runtime/src/main/java/io/quarkus/logging/json/runtime/JsonLogConfig.java (2026-10-28)

**A2. Put the Lambda request id and the tenant id into MDC per invocation, remove them in `finally`**
> Confidence: 🟡 Medium | Sources: AWS java-logging (2026-10-28) + `AbstractLambdaPollLoop.java` at 3.40.1.1 (2026-10-28) + logging guide 3.40 (2026-10-28); the "JVM path sets no MDC" part rests on source reading (M2)
- Why: in AWS's Java sample, `Context` carries `awsRequestId`, the unique request id of the invocation [S15]. Lambda's own Java JSON objects carry the request id as `"AWSrequestId"` [S15][S17]. Quarkus 3.40.1.1's poll loop (used for native builds and dev/test) uses `org.jboss.logging.MDC.put("AWSRequestId", requestId)` and `MDC.remove("AWSRequestId")` in a `finally` block [S9][S12]. The JVM managed-runtime path (`QuarkusStreamHandler.handleRequest` -> `AmazonLambdaRecorder.handle`) has no MDC code [S10][S11] (medium confidence). AWS: "Avoid global variables for context-specific information ... this prevents global variable leaks across invocations" [S21]. Family rule 7 requires `requestId`/`tenantId` in JSON logs; family rule 6 requires the tenant to come from the token. The 3.40 guide's MDC examples use `org.jboss.logmanager.MDC` [S1]. Whether `org.jboss.logging.MDC` writes to the same store is (unverified) (U4). The guide says JSON output carries MDC under `"mdc"` [S1].
- Code (illustrative; the handler body is not from a guide):
  ```java
  // Quarkus 3.40.1.1 - quarkus-amazon-lambda, JVM (java21) or native
  import com.amazonaws.services.lambda.runtime.Context;
  import com.amazonaws.services.lambda.runtime.RequestHandler;
  import io.quarkus.logging.Log;
  import jakarta.inject.Named;
  import org.jboss.logmanager.MDC;

  @Named("orders")
  public class OrdersLambda implements RequestHandler<OrderEvent, OrderResult> {
      @Override
      public OrderResult handleRequest(OrderEvent event, Context context) {
          MDC.put("AWSRequestId", context.getAwsRequestId());
          MDC.put("tenantId", tenantFromVerifiedToken(event)); // family rule 6: never from path alone
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
- Source: https://docs.aws.amazon.com/lambda/latest/dg/java-logging.html (2026-10-28); https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/common-runtime/src/main/java/io/quarkus/amazon/lambda/runtime/AbstractLambdaPollLoop.java (2026-10-28); https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html (2026-10-28)

**A3. Log through JBoss Logging / `io.quarkus.logging.Log` to the console handler on stdout**
> Confidence: 🟢 High | [✓✓ Triangulated | AWS java-logging (2026-10-28) + logging guide 3.40 (2026-10-28) + all-config 3.40 (2026-10-28)]
- Why: AWS: "To output logs from your function code, you can use methods on java.lang.System, or any logging module that writes to stdout or stderr" [S15]. Quarkus: "When using the JBoss Logging API, your application requires no additional dependencies" [S1]. `Log` calls are rewritten "into JBoss Logging calls on the generated logger field" [S1]. `quarkus.log.console.enabled` defaults to `true` and `quarkus.log.console.stderr` to `false` (stdout) [S1][S3]. Use `Log` only in application classes, not in extensions or external dependencies [S1].
- Code:
  ```java
  // Quarkus 3.40 - application class only
  import io.quarkus.logging.Log;
  Log.info("payment authorized");        // becomes a JBoss Logging call at build time
  ```
- Source: https://docs.aws.amazon.com/lambda/latest/dg/java-logging.html (2026-10-28); https://quarkus.io/version/3.40/guides/logging (2026-10-28)

**A4. Keep the JSON keys `level` and `timestamp` (RFC 3339) when Lambda log-level filtering is used**
> Confidence: 🟡 Medium | Sources: AWS log-level filtering (2026-10-28) + AWS java-logging (2026-10-28); the Quarkus key names come from jboss-logmanager main branch (M1)
- Why: "your Event Function code must output log events to `stdout` or `stderr` as JSON formatted objects that contain a key value pair with the key `"level"`". "If the `"level"` value field is invalid or missing, Lambda assigns the log output the level INFO". "If you don't supply a valid timestamp, Lambda assigns the log the level INFO" [S18]. The Java page repeats this for "another logging library" [S15]. JBoss LogManager's `StructuredFormatter.Key` writes `"level"` and `"timestamp"`, and the default timestamp is `ISO_OFFSET_DATE_TIME` [S14] (medium confidence; main branch). That this format satisfies RFC 3339 is an inference (medium confidence) (M7). Therefore do not rename `level`/`timestamp` with `key-overrides` [S1], and do not change `date-format` to a non-RFC 3339 pattern.
- Code:
  ```properties
  # Quarkus 3.40 - leave level/timestamp keys and date-format at their defaults
  # quarkus.log.console.json.key-overrides=...   (do not override level/timestamp)
  # quarkus.log.console.json.date-format=default (default value)
  ```
- Source: https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-log-level.html (2026-10-28); https://raw.githubusercontent.com/jboss-logging/jboss-logmanager/main/src/main/java/org/jboss/logmanager/formatters/StructuredFormatter.java (2026-10-28, main branch)

**A5. Set an explicit retention on the function's log group (via Terraform, `provisioning-aws-cloudwatch-v6`)**
> Confidence: 🟢 High | [✓✓ Triangulated | CloudWatch Logs "Working with log groups" (2026-10-28) + AWS java-logging "Managing log retention" (2026-10-28)]
- Why: "By default, log data is stored in CloudWatch Logs indefinitely" [S23]. "Log groups aren't deleted automatically when you delete a function. To avoid storing logs indefinitely, delete the log group, or configure a retention period" [S15]. Deletion after retention "typically takes up to 72 hours" [S23]. "By default, CloudWatch automatically creates a log group named `/aws/lambda/<function name>` ... when it's first invoked" [S19]. Create the group with retention in IaC before the first invoke (`provisioning-aws-cloudwatch-v6`; family rule 4, no SAM/CDK). The ordering advice is an inference from the auto-create sentence (medium confidence).
- Code: none here. HCL belongs to `provisioning-aws-cloudwatch-v6` (family rule 4).
- Source: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Working-with-log-groups-and-streams.html (2026-10-28); https://docs.aws.amazon.com/lambda/latest/dg/java-logging.html (2026-10-28)

**A6. Grant `logs:PutLogEvents` to the execution role (included in `AWSLambdaBasicExecutionRole`)**
> Confidence: 🟡 Medium (single source)
- Why: "For your Event Function to send logs to CloudWatch Logs, it must have the logs:PutLogEvents permission". "When you configure your Event Function's log group using the AWS CLI, Lambda won't automatically add the `logs:PutLogEvents` permission". "This permission is included in the AWSLambdaBasicExecutionRole managed policy" [S19].
- Source: https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-loggroups.html (2026-10-28)

**A7. Set levels per category; quiet the AWS SDK**
> Confidence: 🟢 High | [✓✓ Triangulated | logging guide 3.40 (2026-10-28) + AWS java-logging log4j2 example (2026-10-28)]
- Why: Quarkus keys `quarkus.log.category."<category-name>".level` (default `INFO`) and `quarkus.log.level` (default `INFO`) [S1][S3]. AWS's own Java logging sample sets `software.amazon.awssdk` to `WARN` [S15]. The goal is to cut verbose logs, because JSON adds size [S17] and filtering "helps you manage storage costs" [S16].
- Code:
  ```properties
  # Quarkus 3.40
  quarkus.log.level=INFO
  quarkus.log.category."software.amazon.awssdk".level=WARN
  quarkus.log.category."com.example.orders".level=DEBUG
  ```
- Source: https://quarkus.io/version/3.40/guides/logging (2026-10-28); https://docs.aws.amazon.com/lambda/latest/dg/java-logging.html (2026-10-28)

**A8. One JSON record per line: keep `pretty-print=false` (the default)**
> Confidence: 🟡 Medium (single versioned source; the multi-line split is main-branch evidence)
- Why: `quarkus.log.console.json.pretty-print` default `false`; the guide warns "some JSON parsers will fail to read the pretty printed output" [S1]. The record delimiter defaults to newline [S1]. AWS's `aws-lambda-java-log4j2` README (main branch): "System.out: One log statement but with a line break (AWS Lambda writes two events to CloudWatch)" [S27] (medium confidence) (M5).
- Source: https://quarkus.io/version/3.40/guides/logging (2026-10-28)

**A9. Do not depend on `AWS_LAMBDA_LOG_GROUP_NAME` / `AWS_LAMBDA_LOG_STREAM_NAME` under SnapStart**
> Confidence: 🟡 Medium (single source)
- Why: "The `AWS_LAMBDA_LOG_GROUP_NAME` and `AWS_LAMBDA_LOG_STREAM_NAME` environment variables are not available in Lambda SnapStart functions" [S20]. JVM + SnapStart vs native is an Ask-First item (family rule 3).
- Source: https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html (2026-10-28)

### ⚠️ Conditional Patterns

**C1. Who produces the JSON: Quarkus, Lambda, or Powertools?**
> Confidence: 🟡 Medium
- Options: (A) `quarkus-logging-json` writes JSON to stdout, and Lambda passes it through ("doesn't double-encode") [S1][S15][S17]. (B) Quarkus plain text plus Lambda `LogFormat=JSON`: what the Java runtime does with plain `System.out` lines that do not come from `LambdaLogger`/Log4j2 is (unverified) (U1). (C) Powertools for AWS Lambda (Java): its logging requires "either log4j2 or logback as your log provider" [S26], while Quarkus routes Log4j through `log4j2-jboss-logmanager` and says "Do not include any Log4j dependencies" [S1]. Whether Powertools logging works with Quarkus 3.40 is (unverified) (U2): no official page states it. For Powertools see `implementing-lambda-powertools-java`.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A quarkus-logging-json | Documented on both sides; MDC, additional fields | One more extension | Default choice for this family (rule 7) |
  | B plain text + Lambda JSON | No extension | Behaviour (unverified); no MDC fields; text lines get INFO | Not recommended |
  | C Powertools | Lambda-context keys, sampling | Quarkus compatibility (unverified) | Only after a spike + ADR |

- Agent: "Ask the user whether an existing Powertools standard must be kept; otherwise propose A."
- Source: https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-logformat.html (2026-10-28); https://docs.aws.amazon.com/powertools/java/latest/core/logging/ (2026-10-28)

**C2. MDC nested (`mdc.*`) vs flat (`mdc.flat-fields=true`)**
> Confidence: 🟡 Medium
- Options: nested (default `false`): `{"...","mdc":{"requestId":"abc123"}}`. Flat: `{"...","requestId":"abc123"}` [S1].
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | Nested | No key collisions with formatter keys | Queries use `mdc.AWSRequestId` (dot notation, medium confidence) | Many MDC keys |
  | Flat | Root-level `AWSRequestId`, as in AWS's own Java JSON (key spelling differs, see U8) | Collision risk with `level`/`message` | Simple Logs Insights queries |

- Agent: "Ask whether existing dashboards or queries expect root-level request id fields."
- Source: https://quarkus.io/version/3.40/guides/logging (2026-10-28); https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_AnalyzeLogData-discoverable-fields.html (2026-10-28)

**C3. Lambda `LogFormat`: Text (default) vs JSON**
> Confidence: 🟢 High (each fact quoted from AWS pages)
- Options: Text: "the default log format for all Lambda runtimes is plain text" [S17]. JSON: system logs become `{"time","type","record"}` objects [S17], and log-level filtering becomes available. "To use log-level filtering, your Event Function must be configured to use the JSON log format" [S18]. Switching to JSON without levels sets application and system levels to `INFO` [S17]. JSON "can increase" log size [S17]. Changing the format affects only new logs [S17].
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | Text | Smaller system lines, existing text tooling | No Lambda level filtering | Tooling parses text `START/END/REPORT` |
  | JSON | Filtering; structured `platform.*` records | Size; queries on `REPORT` text change | Default recommendation of AWS ("we recommend that you select JSON") [S17] |

- Agent: "Ask whether any metric filter or query parses plain-text REPORT lines before switching."
- Source: https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-logformat.html (2026-10-28)

**C4. Where the effective level is set**
> Confidence: 🟡 Medium
- Options: (A) `quarkus.log.level`, overridden at deploy time by the env var `QUARKUS_LOG_LEVEL`. Env vars have ordinal 300 and override `application.properties` (250) [S4]. That `quarkus.log.level` is runtime-overridable is inferred from the guide calling only `min-level` "a build-time configuration option" (medium confidence) (M4). (B) `quarkus.log.level=${AWS_LAMBDA_LOG_LEVEL:INFO}`. Expressions work with env vars and accept defaults [S4]. Lambda sets `AWS_LAMBDA_LOG_LEVEL` when application log-level filtering is configured [S18], and its values (TRACE..FATAL) are all Quarkus level names [S1][S18]. Whether this mapping behaves as expected is (medium confidence). (C) Lambda `ApplicationLogLevel` only. Lambda filters only what the code emits: "if you set your Event Function's log level in your code, this setting takes precedence" [S18]. Quarkus drops lines below `quarkus.log.level` before Lambda sees them [S1].
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A QUARKUS_LOG_LEVEL | Pure Quarkus; works in JVM and native | Two knobs (Quarkus + Lambda) | Teams that own app config |
  | B expression on AWS_LAMBDA_LOG_LEVEL | One knob in LoggingConfig | Depends on Lambda setting the var (only with filtering configured) | Ops-driven level changes |
  | C Lambda only | No app change | Cannot raise detail above `quarkus.log.level` | Lowering noise only |

- Agent: "Ask who changes log levels in production (dev team vs ops) and whether TRACE is ever needed. TRACE needs `quarkus.log.min-level=TRACE` at build time [S1]."
- Source: https://quarkus.io/version/3.40/guides/config-reference (2026-10-28); https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-log-level.html (2026-10-28)

**C5. Default `/aws/lambda/<fn>` log group vs custom/shared log group; log class**
> Confidence: 🟢 High
- Options: default group, auto-created at first invoke [S19]. Custom group via `LoggingConfig.LogGroup`: many functions may share one group, and streams are then named `YYYY/MM/DD/<function_name>[<function_version>][<execution_environment_GUID>]` [S19]. Logs Insights field discovery is "supported only for log groups in the Standard log class" [S22]. Data protection masking works in Standard and Infrequent Access [S24].
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | Default per function | Zero config, per-function retention | Many groups | Default |
  | Shared custom group | One retention/IAM scope per app | Name must not start with `aws/`; shared retention | Many small functions of one app |
  | Infrequent Access class | Cost (unverified numbers, U6) | No Logs Insights field discovery [S22] | Archive-only logs |

- Agent: "Ask about retention needs and whether Logs Insights must work on this group. IaC goes to `provisioning-aws-cloudwatch-v6`; group design to `monitoring-cloudwatch-observability`."
- Source: https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-loggroups.html (2026-10-28)

**C6. Exception output: `detailed` vs `formatted` vs `detailed-and-formatted`**
> Confidence: 🟢 High (option names and defaults) / 🟡 Medium (size effect)
- Options: `quarkus.log.console.json.exception-output-type` default `detailed`; options `detailed`, `formatted`, `detailed-and-formatted` [S1]. `print-details` default `false`, and the guide warns details "can be expensive" [S1]. Relative size per option is not stated (medium confidence).
- Agent: "Ask whether stack traces are queried as structured frames or only read by humans."
- Source: https://quarkus.io/version/3.40/guides/logging (2026-10-28)

**C7. Structured format profile: `log-format` `default` vs `ecs` vs `gcp`**
> Confidence: 🟡 Medium (key renames read from source at tag 3.40.1.1)
- Options: `default`, `ecs` (Elastic Common Schema), `gcp` [S1]. In source at 3.40.1.1, ECS renames `timestamp` -> `@timestamp` and `level` -> `log.level`, and GCP renames `level` -> `severity` [S7]. Lambda filtering needs `"level"` and a valid timestamp, otherwise it assigns INFO [S18]. So `ecs`/`gcp` break Lambda level filtering (medium confidence). Choose `ecs` only when logs are shipped to an ECS consumer and Lambda filtering is not used.
- Source: https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/logging-json/runtime/src/main/java/io/quarkus/logging/json/runtime/LoggingJsonRecorder.java (2026-10-28)

### 🚫 Forbidden Patterns

**N1. Dumping environment variables or the whole `Context`/event into the log**
> Severity: Critical
> Confidence: 🟢 High
- Why: Lambda sets the reserved variables `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` and `AWS_SESSION_TOKEN` with "The access keys obtained from the function's execution role" [S20]. AWS's own Java sample logs `gson.toJson(System.getenv())`, and its CLI output shows an `"AWS_SESSION_TOKEN"` value in the log [S15]. Family rule 7: no PII/secrets in logs. CloudWatch masking applies only to data ingested after a policy exists: "log events ingested to the log group before that time are not masked" [S24].
- Impact: credentials of the execution role and customer data become readable by anyone with log read access.
- ❌ Wrong:
  ```java
  // Quarkus 3.40 Lambda - copied from the AWS sample
  Log.info("ENV: " + System.getenv());
  Log.info("EVENT: " + objectMapper.writeValueAsString(event));
  ```
- ✅ Correct:
  ```java
  // Quarkus 3.40 Lambda - log identifiers and bounded facts only
  MDC.put("AWSRequestId", context.getAwsRequestId());
  Log.info("order received");   // no env, no tokens, no PII
  ```
- Source: https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html (2026-10-28); https://docs.aws.amazon.com/lambda/latest/dg/java-logging.html (2026-10-28)

**N2. Adding Log4j dependencies (or AWS's `aws-lambda-java-log4j2` + `log4j2.xml` recipe) to a Quarkus app**
> Severity: High
> Confidence: 🟢 High
- Why: Quarkus 3.40 supports the Log4j 2 API through the adapter `org.jboss.logmanager:log4j2-jboss-logmanager` and says "Do not include any Log4j dependencies, as the `log4j2-jboss-logmanager` library contains everything needed" [S1]. AWS's Java recipe needs `log4j-layout-template-json`, `log4j-slf4j2-impl` and the `Lambda` appender [S15], which is a different logging backend. For SLF4J the Quarkus adapter is `org.jboss.slf4j:slf4j-jboss-logmanager` [S1].
- Impact: two logging backends; for native builds, "the native build can fail" without the JBoss adapters [S1].
- ❌ Wrong:
  ```xml
  <!-- Quarkus 3.40 app -->
  <dependency><groupId>com.amazonaws</groupId><artifactId>aws-lambda-java-log4j2</artifactId></dependency>
  <dependency><groupId>org.apache.logging.log4j</groupId><artifactId>log4j-slf4j2-impl</artifactId></dependency>
  ```
- ✅ Correct:
  ```xml
  <!-- Quarkus 3.40 app: JBoss LogManager backend + JSON extension -->
  <dependency><groupId>io.quarkus</groupId><artifactId>quarkus-logging-json</artifactId></dependency>
  <!-- only if a library logs via the Log4j 2 API: -->
  <dependency><groupId>org.jboss.logmanager</groupId><artifactId>log4j2-jboss-logmanager</artifactId></dependency>
  ```
- Source: https://quarkus.io/version/3.40/guides/logging (2026-10-28); https://docs.aws.amazon.com/lambda/latest/dg/java-logging.html (2026-10-28)

**N3. Expecting Lambda `ApplicationLogLevel=DEBUG` to show DEBUG lines that Quarkus never emitted**
> Severity: Moderate
> Confidence: 🟢 High
- Why: `quarkus.log.level` defaults to `INFO` [S1][S3]. Lambda: "if you set your Event Function's log level in your code, this setting takes precedence over any other log level settings you configure" [S18]. Below DEBUG, "adjust the minimum level at build time" [S1]. With `min-level` INFO, `isDebugEnabled()` checks become dead code in native mode [S1].
- Impact: no DEBUG lines during an incident despite the Lambda setting.
- ❌ Wrong:
  ```bash
  # Representative - Quarkus 3.40 app still at quarkus.log.level=INFO
  aws lambda update-function-configuration --function-name orders \
    --logging-config LogFormat=JSON,ApplicationLogLevel=DEBUG
  ```
- ✅ Correct:
  ```bash
  # Representative - raise the Quarkus level too (runtime override, see C4)
  aws lambda update-function-configuration --function-name orders \
    --environment "Variables={QUARKUS_LOG_LEVEL=DEBUG}"   # replaces ALL variables: include existing ones
  ```
  The `--environment` call "replaces" the entire `Variables` structure [S20].
- Source: https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-log-level.html (2026-10-28); https://quarkus.io/version/3.40/guides/logging (2026-10-28)

**N4. Pretty-printed JSON in Lambda**
> Severity: Moderate
> Confidence: 🟢 High (Quarkus warning) / 🟡 Medium (event split, M5)
- Why: "some JSON parsers will fail to read the pretty printed output" [S1]; multi-line stdout becomes several CloudWatch events [S27] (medium confidence).
- ❌ Wrong:
  ```properties
  quarkus.log.console.json.pretty-print=true
  ```
- ✅ Correct:
  ```properties
  quarkus.log.console.json.pretty-print=false   # Quarkus 3.40 default
  ```
- Source: https://quarkus.io/version/3.40/guides/logging (2026-10-28)

**N5. Custom log group name starting with `aws/`**
> Severity: High
> Confidence: 🟢 High
- Why: "custom log group names mustn't begin with the string `aws/`. If you create a custom log group beginning with `aws/`, Lambda won't be able to create the log group. As a result of this, your Event Function's logs won't be sent to CloudWatch" [S19].
- ❌ Wrong:
  ```bash
  aws lambda update-function-configuration --function-name orders --logging-config LogGroup=aws/orders-app
  ```
- ✅ Correct:
  ```bash
  aws lambda update-function-configuration --function-name orders --logging-config LogGroup=orders-app
  ```
- Source: https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-loggroups.html (2026-10-28)

**N6. Renaming `level`/`timestamp` (key-overrides, `log-format=ecs|gcp`, custom non-RFC 3339 `date-format`) while relying on Lambda log-level filtering**
> Severity: Moderate
> Confidence: 🟡 Medium (the AWS rule is High; the Quarkus ECS/GCP renames come from source at tag, M-class)
- Why: missing or invalid `"level"`, or an invalid timestamp, makes Lambda assign `INFO` [S18]. ECS/GCP rename those keys [S7].
- Impact: ERROR lines are treated as INFO and are dropped when `ApplicationLogLevel=WARN` or higher (medium confidence) (M3).
- ❌ Wrong:
  ```properties
  quarkus.log.console.json.log-format=ecs
  ```
- ✅ Correct:
  ```properties
  quarkus.log.console.json.log-format=default   # Quarkus 3.40 default
  ```
- Source: https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-log-level.html (2026-10-28)

**N7. Leaving `tenantId`/request id in MDC after the invocation**
> Severity: High
> Confidence: 🟡 Medium (the AWS reuse rule is High; MDC thread reuse in the Quarkus Lambda runtime is an inference)
- Why: environments are reused, and "Avoid global variables for context-specific information" [S21]. Quarkus's own poll loop removes `AWSRequestId` in `finally` [S9].
- Impact: a later invocation logs another tenant's id, which breaks tenant isolation in logs (family rule 6/7).
- ❌ Wrong:
  ```java
  MDC.put("tenantId", tenant);       // never removed
  return process(event);
  ```
- ✅ Correct:
  ```java
  MDC.put("tenantId", tenant);
  try { return process(event); } finally { MDC.remove("tenantId"); }
  ```
- Source: https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html (2026-10-28)

**N8. `quarkus.log.console.json.enable` (deprecated) in new 3.40 config**
> Severity: Low
> Confidence: 🟢 High (source at tag; annotation text)
- Why: `enable()` is `@Deprecated(forRemoval = true, since = "3.19")`; use `enabled` [S6].
- ❌ Wrong: `quarkus.log.console.json.enable=false`
- ✅ Correct: `quarkus.log.console.json.enabled=false`
- Source: https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/logging-json/runtime/src/main/java/io/quarkus/logging/json/runtime/JsonLogConfig.java (2026-10-28)

---

## Migration Guide

> Confidence: 🟢 High for listed items | Sources: `JsonLogConfig.java` at 3.40.1.1 (2026-10-28) + family facts (2026-10-28) + AWS java-logging (2026-10-28)

**Breaking Changes / deprecations relevant to logging on Quarkus 3.40 Lambda**:
- `quarkus.log.console.json.enable` is deprecated for removal since 3.19; use `quarkus.log.console.json.enabled` [S6].
- `quarkus-test-amazon-lambda` / `LambdaClient` were removed in Quarkus 3.31; test logging output with `quarkus-junit` + RestAssured against the mock event server (family fact 23).
- `quarkus.snapstart.enable` -> `quarkus.snapstart.enabled` (family fact 22). This is not logging, but it sits in the same `application.properties`.
- AWS: "any libraries related to aws-lambda-java-log4j (v1.0.0 or 1.0.1) should not be used under any circumstance" [S15]. This does not apply to Quarkus apps, which use no Log4j backend (N2).
- AWS: a Lambda service change adds a `status` field (and `ErrorType` on crashes) to plain-text `REPORT` lines; "you may see minor differences between the structure and content of system log messages" [S21]. Text-parsing metric filters must tolerate it.
- No Quarkus 3.40 migration note on logging was found in the guides read. A 3.40 changelog/migration wiki entry for logging was not fetched (L4).

**Upgrade Steps** (moving an existing Quarkus Lambda from plain text to JSON):
1. Add `io.quarkus:quarkus-logging-json` (BOM-managed, 3.40.1.1) [S5].
2. Add `%dev`/`%test` `quarkus.log.console.json.enabled=false` [S1].
3. Add MDC put/remove for `AWSRequestId` and `tenantId` in each handler (A2).
4. Update Logs Insights queries and metric filters for the JSON field names (`level`, `message`, `mdc.*`); see Quality Control.
5. Optionally set Lambda `LogFormat=JSON` (C3), then `ApplicationLogLevel` / `SystemLogLevel` [S17][S18].

**Compatibility Matrix**:

| Dependency | Min | Max | Notes |
|------------|-----|-----|-------|
| Quarkus | 3.40.0 | 3.40.x | 3.40.1.1 pinned (family rule 1) |
| quarkus-logging-json | 3.40.1.1 | 3.40.1.1 | BOM-managed [S5] |
| aws-lambda-java-core | 1.4.0 | 1.4.0 | As managed by quarkus-bom 3.40.1.1 [S13] (partly read) |
| Lambda Java runtime for JSON app logs | Java 11+ (all except Java 8 on AL1) | java25 | [S17]; family fact 15 for java17/21/25 runtimes |
| Lambda OS-only runtime (native) | provided.al2023 | - | Log-level filtering only via JSON `level` key [S18]; family fact 13 |

---

## Implementation Blueprint

> Confidence: 🟡 Medium overall (the snippets combine High facts; the composition is illustrative)

**Lifecycle**:
```java
// Quarkus 3.40.1.1 - Init: nothing to initialise for logging (Log API is build-time wired) [S1]
// Usage: per invocation, MDC put -> log -> MDC remove in finally (A2)
// Cleanup: the poll loop (native/dev/test) also removes "AWSRequestId" in finally [S9]
@Named("orders")
public class OrdersLambda implements RequestHandler<OrderEvent, OrderResult> {
    @Override
    public OrderResult handleRequest(OrderEvent event, Context context) {
        MDC.put("AWSRequestId", context.getAwsRequestId());
        MDC.put("tenantId", tenantFromVerifiedToken(event));
        try {
            Log.info("order received");
            OrderResult r = process(event);
            Log.info("order processed");
            return r;
        } catch (RuntimeException e) {
            Log.error("order failed", e);      // JSON: exception-output-type=detailed by default [S1]
            throw e;
        } finally {
            MDC.remove("tenantId");
            MDC.remove("AWSRequestId");
        }
    }
}
```

**application.properties (Quarkus 3.40)**:
```properties
quarkus.lambda.handler=orders
quarkus.log.level=INFO
quarkus.log.category."software.amazon.awssdk".level=WARN
quarkus.log.console.json.enabled=true
%dev.quarkus.log.console.json.enabled=false
%test.quarkus.log.console.json.enabled=false
quarkus.log.console.json.additional-field."service".value=orders
# optional (C2): quarkus.log.console.json.mdc.flat-fields=true
```
`additional-field."field-name".value` and `.type` (`string`, `int`, `long`, default `string`) [S1]. `quarkus.lambda.handler` selects the CDI-named handler (family fact 11).

**Integration**: Quarkus 3.40 ↔ AWS Lambda HTTP extensions
```java
// Quarkus 3.40.1.1 - quarkus-amazon-lambda-http (preview, family fact 25) + quarkus-rest
// Context is injectable with @Context in Jakarta REST resources, or with @Inject elsewhere [S28]
@Path("/orders")
public class OrdersResource {
    @POST
    public Response create(@Context com.amazonaws.services.lambda.runtime.Context lambda, Order o) {
        MDC.put("AWSRequestId", lambda.getAwsRequestId());
        try { Log.info("create order"); return Response.ok().build(); }
        finally { MDC.remove("AWSRequestId"); }
    }
}
```
Whether a JAX-RS filter is a better place for the MDC put/remove is not covered by any page read (medium confidence, design choice).

**Native mode (Quarkus 3.40, `provided.al2023`)**:
- With `min-level` INFO, lower-level checks "always ... return `false`" and become dead code [S1].
- Libraries logging via SLF4J, Commons Logging or Log4j 2 need the JBoss adapters, or "the native build can fail" [S1].
- The poll loop runs in native builds (`@BuildStep(onlyIf = NativeBuild.class)` -> `startPollLoop`) and sets MDC `AWSRequestId` [S9][S12] (medium confidence).
- OS-only runtimes: Lambda sets `AWS_LAMBDA_LOG_LEVEL`/`AWS_LAMBDA_LOG_FORMAT` "to integrate Lambda advanced logging controls into a custom runtime" [S18]; Quarkus's poll loop does not read them [S9] (U3).
- `_X_AMZN_TRACE_ID` "is not defined for OS-only runtimes" [S20]; tracing belongs to U12.
- Whether `quarkus-logging-json` has any native-specific limitation is not stated (unverified) (U7).

---

## Quality Control

**Verification Commands**:
```bash
# Representative - adapt to your environment (Quarkus 3.40.1.1)
# 1. Extension present
mvn -q dependency:tree -Dincludes=io.quarkus:quarkus-logging-json
# Expected: io.quarkus:quarkus-logging-json:jar:3.40.1.1

# 2. Config keys present (no deprecated key)
grep -nE "quarkus\.log\.console\.json\.(enabled|pretty-print|log-format)" src/main/resources/application.properties
grep -n "quarkus.log.console.json.enable=" src/main/resources/application.properties   # Expected: no match (N8)

# 3. No Log4j backend on the classpath (N2)
mvn -q dependency:tree -Dincludes=org.apache.logging.log4j:log4j-core,com.amazonaws:aws-lambda-java-log4j2
# Expected: no output

# 4. Invoke and see the tail of the log (up to 4 KB, base64) [S15]
aws lambda invoke --function-name orders out --log-type Tail \
  --query 'LogResult' --output text --cli-binary-format raw-in-base64-out | base64 --decode
# Expected: START/END/REPORT lines plus one-line JSON records with "level" and "mdc":{"AWSRequestId":...}

# 5. Current Lambda logging configuration
aws lambda get-function-configuration --function-name orders --query LoggingConfig
# Expected: {"LogFormat": "...", "ApplicationLogLevel": ..., "SystemLogLevel": ..., "LogGroup": "/aws/lambda/orders"} (output shape medium confidence)
```

**Logs Insights queries** (Standard log class only [S22]; dot notation for nested JSON [S22]; Quarkus key names (medium confidence) M1):
```
fields @timestamp, level, message, mdc.AWSRequestId, mdc.tenantId
| filter level = "ERROR"
| sort @timestamp desc
```
```
fields @timestamp, @requestId, @duration, @billedDuration, @maxMemoryUsed
| filter @type = "REPORT"
```
Lambda logs get the discovered fields `@requestId`, `@duration`, `@billedDuration`, `@type`, `@maxMemoryUsed` and `@memorySize`, "but only for the first embedded JSON fragment in each log event". Insights extracts a maximum of 200 fields from a JSON log [S22]. That `@type = "REPORT"` also matches when the system log format is JSON is (unverified) (U9).

**Mocking / tests**:
```java
// Quarkus 3.40 - @QuarkusTest against the mock event server (family facts 14, 23)
@QuarkusTest
class OrdersLambdaTest {
    @Test
    void logsDoNotFailInvocation() {
        given().contentType("application/json").body(new OrderEvent(/*...*/))
               .when().post().then().statusCode(200);
    }
}
```
The 3.40 logging guide says that for tests "it is necessary to set the `java.util.logging.manager` system property to `org.jboss.logmanager.LogManager`" (Surefire/Gradle examples) [S1]. The context of that sentence (which test setups need it) was only partly read (medium confidence). Keep JSON off in `%test` [S1] so test output stays readable. Whether the mock event server path sets MDC `AWSRequestId`: the dev/test poll loop does set it [S9][S11] (medium confidence).

---

## Production Readiness

- **Performance**: `Log` is wired at build time [S1]. Async console logging exists (`quarkus.log.console.async.enabled`, default `false`; queue 512, overflow `block`) [S1]. Its interaction with the Lambda freeze after return is not documented (unverified, not filed separately: design choice; keep the default). `print-details=true` "can be expensive" [S1].
- **Scalability**: one log stream per execution environment instance [S15]. A shared custom group keeps streams apart by function name and version [S19]. Lambda Managed Instances interleave concurrent invocations in one stream and "only support the JSON log format", which is why the request id must be in each entry [S19] (out of scope beyond this note).
- **Monitoring**: system log levels per event are mapped on [S18] (e.g. `report` status!=success -> WARN, `logsDropped` -> WARN). Keep `SystemLogLevel` at least `WARN` so failures stay visible. Metrics and alarms belong to U13 / `monitoring-cloudwatch-observability`.
- **Cost**: JSON "adds additional metadata ... the size of your Event Function's log messages can increase" [S17]. Filtering "helps you manage storage costs" [S16]. Free tier: "5 GB Data (ingestion, archive storage, and data scanned by Logs Insights queries)" [S25]. Per-GB prices were not rendered on the pricing page, and the examples conflict ($0.25 vs $0.50 per GB for the same scenario): (unverified) (U6). Do not quote numbers.
- **Retention**: default indefinite; set per group; deletion lag up to 72 hours [S23] (A5).
- **Security**: no secrets/PII (N1, family rule 7). Data protection policies can mask credentials, financial data, PII, PHI and device ids at ingest; only `logs:Unmask` holders see raw data; events ingested earlier are not masked [S24]. Secrets come from Secrets Manager/SSM (family rule 5; AWS recommends Secrets Manager over env vars [S20]). The execution role needs only `logs:PutLogEvents` for its group (A6).
- **SnapStart**: `AWS_LAMBDA_LOG_GROUP_NAME`/`STREAM_NAME` are unavailable [S20] (A9). Restore/init reports appear as `RESTORE_REPORT`/`INIT_REPORT` [S21].

---

## Reference Implementations

- Quarkus 3.40 logging guide (all JSON keys, MDC, adapters): https://quarkus.io/version/3.40/guides/logging
- AWS Java logging page, including the SLF4J + Log4j2 sample (a non-Quarkus reference for the JSON shape Lambda itself produces): https://docs.aws.amazon.com/lambda/latest/dg/java-logging.html
- AWS sample apps listed there (`java-basic`, `java-events`, `s3-java`): https://github.com/awsdocs/aws-lambda-developer-guide/tree/main/sample-apps (not fetched; main branch; listed by [S15])
- Quarkus 3.40.1.1 Lambda poll loop (MDC `AWSRequestId` handling): [S9]
- Powertools for AWS Lambda (Java) logging: https://docs.aws.amazon.com/powertools/java/latest/core/logging/ (pointer only; see `implementing-lambda-powertools-java`)

---

## Source Bibliography

All read on 2026-10-28.

**Primary (Quarkus, versioned)**:
- [S1] Quarkus 3.40 "Logging configuration" - https://quarkus.io/version/3.40/guides/logging - read in full in two windows (0-100000 and 100000-199486 of 199486 chars), plus targeted re-reads. Page shows "Version: 3.40 (latest)".
- [S2] Quarkus 3.40 "AWS Lambda" - https://quarkus.io/version/3.40/guides/aws-lambda - read in full; no logging content (archetype 3.40.1.1; `DISABLE_SIGNAL_HANDLERS=true`).
- [S3] Quarkus 3.40 "All configuration options" - https://quarkus.io/version/3.40/guides/all-config - partly read: 0-232437 in three windows; only core logging keys found (`quarkus.log.level`, `min-level`, `console.format`, `console.stderr`); no `quarkus.log.console.json.*` and no `quarkus.lambda.*` keys in the served text (L1).
- [S4] Quarkus 3.40 "Configuration reference" - https://quarkus.io/version/3.40/guides/config-reference - partly read (env var mapping, ordinals, property expressions) (L2).
- [S28] Quarkus 3.40 "AWS Lambda with Quarkus REST, Undertow, or Reactive Routes" - https://quarkus.io/version/3.40/guides/aws-lambda-http - targeted read ("Injectable AWS Context Variables"; no logging/MDC text).

**Primary (Quarkus source at tag 3.40.1.1 / Maven Central)**:
- [S5] https://repo1.maven.org/maven2/io/quarkus/quarkus-logging-json/3.40.1.1/quarkus-logging-json-3.40.1.1.pom
- [S6] https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/logging-json/runtime/src/main/java/io/quarkus/logging/json/runtime/JsonLogConfig.java
- [S7] https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/logging-json/runtime/src/main/java/io/quarkus/logging/json/runtime/LoggingJsonRecorder.java
- [S8] https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/logging-json/runtime/src/main/java/io/quarkus/logging/json/runtime/JsonFormatter.java (extends `org.jboss.logmanager.formatters.JsonFormatter`; key names not defined here)
- [S9] https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/common-runtime/src/main/java/io/quarkus/amazon/lambda/runtime/AbstractLambdaPollLoop.java
- [S10] https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/runtime/src/main/java/io/quarkus/amazon/lambda/runtime/QuarkusStreamHandler.java
- [S11] https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/runtime/src/main/java/io/quarkus/amazon/lambda/runtime/AmazonLambdaRecorder.java
- [S12] https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/deployment/src/main/java/io/quarkus/amazon/lambda/deployment/AmazonLambdaProcessor.java
- [S13] https://repo1.maven.org/maven2/io/quarkus/quarkus-bom/3.40.1.1/quarkus-bom-3.40.1.1.pom - partly read (0-100000 of 419419 chars; `aws-lambda-java-core` 1.4.0 found; jboss-logmanager/jboss-logging versions not reached) (L3).

**Supporting (main branch, medium)**:
- [S14] https://raw.githubusercontent.com/jboss-logging/jboss-logmanager/main/src/main/java/org/jboss/logmanager/formatters/StructuredFormatter.java - `Key` enum (`timestamp`, `level`, `message`, `loggerName`, `loggerClassName`, `mdc`, `ndc`, `sequence`, `threadName`, `threadId`, `hostName`, `processName`, `processId`, `exception`, `stackTrace`, ...) and default `ISO_OFFSET_DATE_TIME`. The jboss-logmanager version used by 3.40.1.1 was not confirmed (L3).
- [S27] https://github.com/aws/aws-lambda-java-libs/blob/main/aws-lambda-java-log4j2/README.md - multi-line `System.out` -> two CloudWatch events; `AWS_LAMBDA_LOG_FORMAT=JSON` selects `LambdaJSONFormat`; shows v1.6.5.

**Primary (AWS, current documentation)**:
- [S15] Log and monitor Java Lambda functions - https://docs.aws.amazon.com/lambda/latest/dg/java-logging.html - full.
- [S16] Working with Lambda function logs (advanced controls overview) - https://docs.aws.amazon.com/lambda/latest/dg/monitoring-logs.html - full. (The brief's URL `monitoring-cloudwatchlogs-advanced.html` returned only a title; the anchor `#monitoring-cloudwatchlogs-advanced` lives on this page.)
- [S17] Configuring JSON and plain text log formats - https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-logformat.html - full.
- [S18] Log-level filtering - https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-log-level.html - full.
- [S19] Configuring CloudWatch log groups - https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-loggroups.html - full.
- [S20] Working with Lambda environment variables (defined runtime environment variables) - https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html - full. (`configuration-envvars-runtime.html` returned only a title.) `AWS_LAMBDA_LOG_FORMAT` and `AWS_LAMBDA_LOG_LEVEL` are not in the reserved list on this page.
- [S21] Understanding the Lambda execution environment lifecycle - https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html - full.
- [S22] CloudWatch Logs Insights: supported logs and discovered fields - https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_AnalyzeLogData-discoverable-fields.html - full.
- [S23] Working with log groups and log streams (retention) - https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Working-with-log-groups-and-streams.html - full.
- [S24] Help protect sensitive log data with masking - https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/mask-sensitive-log-data.html - full.
- [S25] Amazon CloudWatch pricing - https://aws.amazon.com/cloudwatch/pricing/ - partly read (0-100000 of 154061; price tables not rendered) (L5).
- [S26] Powertools for AWS Lambda (Java) - Logging - https://docs.aws.amazon.com/powertools/java/latest/core/logging/ - targeted read (examples show 2.11.0; no Quarkus/JBoss text; "GraalVM support" listed).

**Validation**: no community sources used. One WebSearch (Powertools + Quarkus) returned only official Powertools pages; one WebSearch (RIC System.out behaviour) returned a third-party mirror, which was rejected and replaced by [S27].

---

## Research Gaps

Coverage limits (pages read only partly): L1 [S3] JSON keys absent from the served all-config text; L2 [S4] targeted sections only; L3 [S13] BOM read 0-100000 of 419419 (jboss-logmanager version unknown); L4 no Quarkus 3.40 changelog/migration-wiki page on logging fetched; L5 [S25] price tables not rendered.

```
Gap: U1 - What the Lambda Java managed runtime does with plain-text System.out lines (not LambdaLogger/Log4j2) when LogFormat=JSON (wrapped with AWSrequestId, or passed as-is)
Impact: decides whether option B of C1 is viable; text lines get level INFO either way [S18]
Workaround: use quarkus-logging-json (option A)
Follow-up: aws-lambda-java-libs runtime-interface-client source at the deployed runtime version
§7-ref: Iteration 1 - IRRESOLVABLE
```
```
Gap: U2 - Whether Powertools for AWS Lambda (Java) logging works with Quarkus 3.40 (JVM or native)
Impact: Powertools requires log4j2/logback [S26]; Quarkus forbids Log4j deps with its adapter [S1]
Workaround: treat as an ADR spike; point to implementing-lambda-powertools-java
Follow-up: Powertools Java docs/issues, Quarkiverse
§7-ref: Iteration 2 - IRRESOLVABLE
```
```
Gap: U3 - Whether any Quarkus 3.40 component reads AWS_LAMBDA_LOG_LEVEL / AWS_LAMBDA_LOG_FORMAT (poll loop does not [S9])
Impact: Lambda LoggingConfig alone does not change Quarkus levels/format
Workaround: C4 option A or B
Follow-up: grep quarkusio/quarkus at tag 3.40.1.1 for AWS_LAMBDA_LOG_
§7-ref: Iteration 1 - IRRESOLVABLE
```
```
Gap: U4 - Whether org.jboss.logging.MDC (used by the Quarkus Lambda poll loop) and org.jboss.logmanager.MDC (used in the 3.40 guide) share one store
Impact: the brief named org.jboss.logging.MDC; the guide uses org.jboss.logmanager.MDC
Workaround: use org.jboss.logmanager.MDC as in the guide
Follow-up: jboss-logging LoggerProvider for JBoss LogManager
§7-ref: not run (budget used)
```
```
Gap: U5 - How JUL-originated levels (SEVERE, WARNING, FINE) are rendered in the Quarkus JSON "level" field, and whether Lambda accepts them (invalid -> INFO [S18])
Impact: library errors logged via JUL might be filtered as INFO
Workaround: test the output of a JUL-logging dependency
Follow-up: jboss-logmanager formatter source at the 3.40.1.1 version
§7-ref: not run (budget used)
```
```
Gap: U6 - CloudWatch Logs per-GB prices (Standard / Infrequent Access ingestion, storage, Insights scan)
Impact: cost estimates
Workaround: state the free tier only; link the pricing page
Follow-up: AWS Pricing Calculator / pricing API
§7-ref: Iteration 3 (no fetch possible beyond the rendered page) - IRRESOLVABLE
```
```
Gap: U7 - Native-image specific limitations of quarkus-logging-json in 3.40 (none stated)
Impact: low
Workaround: build native in CI and check one JSON line
Follow-up: quarkus-logging-json deployment module at tag
§7-ref: not run (budget used)
```
```
Gap: U8 - Request id key spelling and case sensitivity: Lambda Java JSON uses "AWSrequestId" [S15][S17]; the AWS log4j2 example and the Quarkus poll loop use "AWSRequestId" [S15][S9]; whether Logs Insights field names are case-sensitive is not stated
Impact: queries spanning Lambda-generated and Quarkus-generated lines
Workaround: query both spellings or standardize on the MDC key
Follow-up: CloudWatch Logs Insights query syntax page
§7-ref: not run (budget used)
```
```
Gap: U9 - System-log JSON format and the @type/@requestId discovered fields on OS-only runtimes (provided.al2023) and with LogFormat=JSON
Impact: REPORT-based queries for native functions
Workaround: verify with one invoke
Follow-up: Lambda log format page "managed runtimes" scope vs OS-only runtimes
§7-ref: not run (budget used)
```

Observation (not a gap): the AWS log-level page lists TRACE as an application level in its table, but its CLI text lists `ApplicationLogLevel` values as "DEBUG, INFO, WARN, ERROR, or FATAL" [S18]. Both are quoted; TRACE via CLI is (medium confidence).

---

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Conditional C1 | U1 plain-text stdout under LogFormat=JSON | Searched RIC source; found only multi-line split evidence (added as M5) | https://github.com/aws/aws-lambda-java-libs/blob/main/aws-lambda-java-log4j2/README.md (2026-10-28) |
| 1 | Conditional C1 | U1 | ⚠️ IRRESOLVABLE - no official page states the wrapping behaviour | - |
| 1 | Implementation Blueprint | U3 Quarkus reads AWS_LAMBDA_LOG_* | Checked poll loop: not read | [S9] (2026-10-28) |
| 1 | Implementation Blueprint | U3 | ⚠️ IRRESOLVABLE - rest of the code base not searched within budget | - |
| 2 | Conditional C1 | U2 Powertools + Quarkus | Searched Powertools docs; backends limited to log4j2/logback, no Quarkus text | [S26] (2026-10-28) |
| 2 | Conditional C1 | U2 | ⚠️ IRRESOLVABLE - no official compatibility statement | - |
| 3 | Mandatory A2 | Does the JVM path set MDC AWSRequestId? | Resolved (medium confidence): native -> `startPollLoop` (sets MDC); JVM non-dev -> no poll loop, `QuarkusStreamHandler` sets no MDC | [S11][S12] (2026-10-28) |
| 3 | Production Readiness | U6 prices | ⚠️ IRRESOLVABLE - pricing tables are dynamic and not rendered | [S25] |

---

## Completion Checklist

- [x] Domain complexity tier assessed and documented (Standard)
- [x] All scope areas cited (basics, JSON, MDC, request id, LoggingConfig, env vars, log group/retention/cost, PII, native, Insights)
- [x] Pattern counts driven by domain needs (9 ✅, 7 ⚠️, 8 🚫)
- [x] Every anti-pattern has alternative (❌/✅ in N1-N8)
- [x] All CLI commands validated/marked as representative
- [x] Integration examples complete (plain RequestHandler; HTTP extension with `@Context`)
- [x] Sources dated and linked (all 2026-10-28)
- [x] Security documented (N1, masking, IAM)
- [x] 1+ copy-paste working example (application.properties + handler; handler body illustrative)
- [x] Confidence badge applied to every pattern entry
- [x] All Always-Do patterns triangulated (deep) or downgraded to 🟡 Medium (A2, A4, A6, A8, A9 downgraded)
- [x] Research Iteration Changelog present and complete
- [x] Research_Quality_Score calculated and added to Metadata
- [x] Every Research Gap cross-referenced in §7 (U4, U5, U7, U8, U9 marked "not run (budget used)")

---

## Agent Operation Notes

- **High Confidence (execute without asking)**: A1, A3, A5, A7 (✓✓); every AWS quote in C3/C5/N1/N2/N3/N5; Quarkus key names and defaults read on the 3.40 guide (`quarkus.log.level` INFO, `min-level` DEBUG, `console.stderr` false, JSON `pretty-print` false, `exception-output-type` detailed, `log-format` default, `mdc.flat-fields` false, `additional-field.*.type` string).
- **Medium Confidence (validate with user)**: M1 Quarkus JSON key names `level`/`timestamp`/`mdc` and the `ISO_OFFSET_DATE_TIME` default (jboss-logmanager main branch [S14]). M2 the JVM managed-runtime path sets no MDC; native/dev/test sets `AWSRequestId` (source at tag, not a guide). M3 level-less text lines are dropped when `ApplicationLogLevel` > INFO (inference from [S18]). M4 `quarkus.log.level` is runtime-overridable (inferred from [S1]). M5 multi-line stdout splits into several events ([S27], main branch). M6 one JSON record per line keeps a stack trace in one event (inference). M7 `ISO_OFFSET_DATE_TIME` satisfies RFC 3339 (inference). M8 ECS/GCP key renames (source at tag [S7]). M9 Logs Insights `mdc.<key>` dot-notation queries on Quarkus output (inference from [S22]). Also the "effectively true" `json.enabled` default (from code [S6][S7]), TRACE via CLI (observation), and the test-only `java.util.logging.manager` context.
- **Low Confidence (must ask human)**: U1-U9; IRRESOLVABLE U1, U2, U3, U6.
- **Edge Cases (pause)**: Quarkus 4.0 GA is planned for end of November 2026 (inherited family fact); content here is 3.40-only (family rule 1). Lambda Managed Instances force JSON format [S17] (out of scope).
- **Emergency Stop**: not triggered (official sources exist for every High claim).
- **Contradictions with family facts**: none found. Notes for the orchestrator: (a) the brief names `org.jboss.logging.MDC`, the 3.40 guide uses `org.jboss.logmanager.MDC` [S1], and the Quarkus Lambda source uses `org.jboss.logging.MDC` [S9] (U4); (b) the brief's AWS URLs `monitoring-cloudwatchlogs-advanced.html` and `configuration-envvars-runtime.html` served only a title; their content was read at [S16]/[S17]/[S18]/[S19] and [S20].
