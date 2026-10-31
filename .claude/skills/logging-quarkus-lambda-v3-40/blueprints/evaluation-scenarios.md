# Evaluation Scenarios: logging-quarkus-lambda-v3-40

Six scenarios, covering the four required types. The `skill-evaluator` agent runs these. Back to [SKILL.md](../SKILL.md).

## Contents

- [Scenario 1: Canonical Path](#scenario-1-canonical-path)
- [Scenario 2: Edge Case (Lambda level vs Quarkus level)](#scenario-2-edge-case-lambda-level-vs-quarkus-level)
- [Scenario 3: Misuse Rejection (out-of-scope request)](#scenario-3-misuse-rejection-out-of-scope-request)
- [Scenario 4: Anti-Pattern Trap (copying the AWS sample)](#scenario-4-anti-pattern-trap-copying-the-aws-sample)
- [Scenario 5: Anti-Pattern Trap (log group, pretty print, deprecated key)](#scenario-5-anti-pattern-trap-log-group-pretty-print-deprecated-key)
- [Scenario 6: Edge Case (Powertools and open MDC questions)](#scenario-6-edge-case-powertools-and-open-mdc-questions)

---

## Scenario 1: Canonical Path

**Type**: Standard successful invocation

```yaml
id: 1
name: canonical-json-logs-with-request-and-tenant-id
skills: ["logging-quarkus-lambda-v3-40"]
query: "My Quarkus 3.40 Lambda runs on the java21 managed runtime. Make its logs JSON with the request id and the tenant id on every line."
must_pass:
  - "Adds io.quarkus:quarkus-logging-json (BOM-managed) and sets quarkus.log.console.json.enabled=true with %dev and %test set to false"
  - "Puts AWSRequestId (context.getAwsRequestId()) and tenantId into MDC at the start of the handler and removes both in finally (medium confidence, M2)"
  - "Says the JVM managed-runtime path sets no MDC while native, dev and test do through the poll loop, tagged (medium confidence), and that the tenant comes from the verified token"
  - "Keeps pretty-print false and level/timestamp keys at their defaults; leaves the log group and retention to provisioning-aws-cloudwatch-v6 by name"
must_not:
  - "Adds any Log4j dependency or aws-lambda-java-log4j2"
  - "States the JVM no-MDC behaviour as High or as a documented guide fact"
  - "Writes Terraform for the log group"
```

---

## Scenario 2: Edge Case (Lambda level vs Quarkus level)

**Type**: Interaction of two level settings

```yaml
id: 2
name: edge-application-log-level-versus-quarkus-level
skills: ["logging-quarkus-lambda-v3-40"]
query: "I set ApplicationLogLevel=DEBUG on the function but I still see no DEBUG lines. Also can I just use ECS format for our log shipper?"
must_pass:
  - "Explains that Lambda filters only what the code emits and that quarkus.log.level defaults to INFO, so Quarkus drops DEBUG lines first"
  - "Presents where the level is set as an Ask-First decision: QUARKUS_LOG_LEVEL override (medium confidence), ${AWS_LAMBDA_LOG_LEVEL:INFO} expression (medium confidence), Lambda only; TRACE needs build-time quarkus.log.min-level"
  - "Warns that environment update replaces the whole Variables structure"
  - "Says log-format=ecs renames level and timestamp (medium confidence), which breaks Lambda level filtering, and asks whether filtering is used"
must_not:
  - "Claims Quarkus reads AWS_LAMBDA_LOG_LEVEL on its own"
  - "Recommends ecs without asking about Lambda filtering"
```

---

## Scenario 3: Misuse Rejection (out-of-scope request)

**Type**: Request outside the skill scope

```yaml
id: 3
name: misuse-tracing-metrics-terraform-quarkus4
skills: ["logging-quarkus-lambda-v3-40"]
query: "Add X-Ray tracing and custom CloudWatch metrics to my Quarkus Lambda, create the log group with Terraform, and do it for Quarkus 4."
must_pass:
  - "Declines to cover tracing and metrics here and points to tracing-quarkus-lambda-v3-40 and monitoring-quarkus-lambda-v3-40 by name"
  - "Points the log group and retention HCL to provisioning-aws-cloudwatch-v6 and group design to monitoring-cloudwatch-observability by name"
  - "States the skill is locked to Quarkus 3.40.x and does not assert Quarkus 4 behaviour"
must_not:
  - "Writes X-Ray, metrics or Terraform content"
  - "Claims the logging patterns hold on Quarkus 4"
```

---

## Scenario 4: Anti-Pattern Trap (copying the AWS sample)

**Type**: Plausible but wrong advice

```yaml
id: 4
name: trap-aws-sample-env-dump-and-log4j2
skills: ["logging-quarkus-lambda-v3-40"]
query: "The AWS Java logging page logs System.getenv() and uses aws-lambda-java-log4j2 with a log4j2.xml. Copy that into my Quarkus 3.40 Lambda."
must_pass:
  - "Refuses the environment dump: Lambda sets AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY and AWS_SESSION_TOKEN, and masking does not cover events ingested before a policy exists"
  - "Refuses Log4j artifacts, quoting the guide: Do not include any Log4j dependencies; offers quarkus-logging-json and log4j2-jboss-logmanager only for libraries that use the Log4j 2 API"
  - "Offers to log identifiers and bounded facts through MDC and short messages; secrets from Secrets Manager"
must_not:
  - "Adds aws-lambda-java-log4j2 or log4j-slf4j2-impl"
  - "Logs System.getenv(), the whole event or a token"
```

---

## Scenario 5: Anti-Pattern Trap (log group, pretty print, deprecated key)

**Type**: Three misconfigurations in one request

```yaml
id: 5
name: trap-aws-prefix-pretty-print-enable-key
skills: ["logging-quarkus-lambda-v3-40"]
query: "Review this: logging-config LogGroup=aws/orders-app; quarkus.log.console.json.pretty-print=true; quarkus.log.console.json.enable=true; and tenantId is put in MDC but never removed."
must_pass:
  - "Rejects the aws/ prefix because Lambda cannot create the group and logs are not sent; proposes a name without the prefix"
  - "Rejects pretty-print=true (parsers fail; guide warning) and keeps false; notes the multi-line event split as (medium confidence)"
  - "Replaces enable with enabled (deprecated for removal since 3.19)"
  - "Requires MDC.remove in finally for tenantId, noting that leaking across invocations is an inference (medium confidence) but breaks tenant isolation if true"
must_not:
  - "Accepts any of the four settings"
  - "States the MDC leak mechanism as documented"
```

---

## Scenario 6: Edge Case (Powertools and open MDC questions)

**Type**: Questions the research could not resolve

```yaml
id: 6
name: edge-powertools-mdc-class-and-key-case
skills: ["logging-quarkus-lambda-v3-40"]
query: "Can I use Powertools for AWS Lambda (Java) logging in Quarkus 3.40? Which MDC class do I use, and does Logs Insights treat AWSRequestId and AWSrequestId as the same field?"
must_pass:
  - "Says Powertools logging compatibility with Quarkus 3.40 is (unverified): Powertools needs log4j2 or logback while Quarkus says not to include Log4j dependencies; names implementing-lambda-powertools-java without a link and proposes an ADR spike, defaulting to quarkus-logging-json"
  - "Cites both MDC classes (org.jboss.logmanager.MDC in the guide, org.jboss.logging.MDC in the poll loop), says a shared store is (unverified), and defaults to the guide's class"
  - "Says Lambda's JSON spells the key AWSrequestId and Quarkus AWSRequestId, and that Insights case handling is (unverified); suggests querying both or standardising on the MDC key"
must_not:
  - "Asserts Powertools works or does not work with Quarkus"
  - "Asserts the two MDC classes share a store, or that Insights is case insensitive"
```
