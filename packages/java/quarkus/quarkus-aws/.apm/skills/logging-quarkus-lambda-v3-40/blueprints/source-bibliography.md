# Source bibliography

Back to [register](./unverified-and-risks.md) · [SKILL.md](../SKILL.md). Moved out of the register on 2026-10-28 to keep it under 160 lines; content unchanged.


All read 2026-10-28.

**Quarkus 3.40 (versioned) and registry**

| # | URL | Coverage | Used for |
|---|---|---|---|
| S1 | https://quarkus.io/version/3.40/guides/logging | full, two windows (0 to 100,000 and 100,000 to 199,486 of 199,486 characters), plus targeted re-reads | levels, console handler, JSON keys, MDC, adapters, native notes |
| S2 | https://quarkus.io/version/3.40/guides/aws-lambda | full; no logging content | handler and archetype context |
| S3 | https://quarkus.io/version/3.40/guides/all-config | partly (L1) | core logging keys and defaults |
| S4 | https://quarkus.io/version/3.40/guides/config-reference | targeted (L2) | environment variables, ordinals, expressions |
| S28 | https://quarkus.io/version/3.40/guides/aws-lambda-http | targeted read ("Injectable AWS Context Variables"); no logging text | `Context` injection in Jakarta REST resources |
| S5 | https://repo1.maven.org/maven2/io/quarkus/quarkus-logging-json/3.40.1.1/quarkus-logging-json-3.40.1.1.pom | full | extension existence and description |
| S6 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/logging-json/runtime/src/main/java/io/quarkus/logging/json/runtime/JsonLogConfig.java | full | `enabled`, deprecated `enable` |
| S7 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/logging-json/runtime/src/main/java/io/quarkus/logging/json/runtime/LoggingJsonRecorder.java | full | enabled fallback, ECS and GCP key renames |
| S8 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/logging-json/runtime/src/main/java/io/quarkus/logging/json/runtime/JsonFormatter.java | full | extends the JBoss LogManager JSON formatter |
| S9 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/common-runtime/src/main/java/io/quarkus/amazon/lambda/runtime/AbstractLambdaPollLoop.java | full | MDC `AWSRequestId`, no `AWS_LAMBDA_LOG_*` |
| S10 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/runtime/src/main/java/io/quarkus/amazon/lambda/runtime/QuarkusStreamHandler.java | full | JVM path |
| S11 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/runtime/src/main/java/io/quarkus/amazon/lambda/runtime/AmazonLambdaRecorder.java | full | JVM path |
| S12 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/deployment/src/main/java/io/quarkus/amazon/lambda/deployment/AmazonLambdaProcessor.java | full | poll loop started in native builds |
| S13 | https://repo1.maven.org/maven2/io/quarkus/quarkus-bom/3.40.1.1/quarkus-bom-3.40.1.1.pom | partly (L3) | `aws-lambda-java-core` 1.4.0 |

**Supporting (main branch)**: S14 https://raw.githubusercontent.com/jboss-logging/jboss-logmanager/main/src/main/java/org/jboss/logmanager/formatters/StructuredFormatter.java (key enum, default timestamp format, M1); S27 https://github.com/aws/aws-lambda-java-libs/blob/main/aws-lambda-java-log4j2/README.md (multi-line stdout split, M5).

**AWS (current documentation)**

| # | URL | Used for |
|---|---|---|
| S15 | https://docs.aws.amazon.com/lambda/latest/dg/java-logging.html | stdout logging, sample, log groups, retention |
| S16 | https://docs.aws.amazon.com/lambda/latest/dg/monitoring-logs.html | advanced controls overview |
| S17 | https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-logformat.html | Text and JSON formats |
| S18 | https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-log-level.html | log-level filtering |
| S19 | https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-loggroups.html | log groups, `aws/` prefix, permissions |
| S20 | https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html | reserved variables, SnapStart variables |
| S21 | https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html | environment reuse |
| S22 | https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_AnalyzeLogData-discoverable-fields.html | Insights discovered fields |
| S23 | https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Working-with-log-groups-and-streams.html | retention |
| S24 | https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/mask-sensitive-log-data.html | data protection masking |
| S25 | https://aws.amazon.com/cloudwatch/pricing/ | free tier (L5) |
| S26 | https://docs.aws.amazon.com/powertools/java/latest/core/logging/ | Powertools backends (targeted read) |

Family facts used (orchestrator-verified 2026-10-28): 11, 13, 15, 22, 23, 24 (tagging style only), 25, 36 of `workspace/quarkus-aws-saas/_family_facts_v3.40.md`. Community sources: none used.
