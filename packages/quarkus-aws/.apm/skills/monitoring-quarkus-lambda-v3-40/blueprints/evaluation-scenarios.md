# Evaluation Scenarios: monitoring-quarkus-lambda-v3-40

Six scenarios, covering the four required types. The `skill-evaluator` agent runs these. Back to [SKILL.md](../SKILL.md).

## Contents

- [Scenario 1: Canonical Path](#scenario-1-canonical-path)
- [Scenario 2: Edge Case (tenant dimension)](#scenario-2-edge-case-tenant-dimension)
- [Scenario 3: Misuse Rejection (out of scope)](#scenario-3-misuse-rejection-out-of-scope)
- [Scenario 4: Anti-Pattern Trap (EMF through the logger)](#scenario-4-anti-pattern-trap-emf-through-the-logger)
- [Scenario 5: Edge Case (Micrometer and Powertools)](#scenario-5-edge-case-micrometer-and-powertools)
- [Scenario 6: Anti-Pattern Trap (built-in metrics and dimension limit)](#scenario-6-anti-pattern-trap-built-in-metrics-and-dimension-limit)

---

## Scenario 1: Canonical Path

**Type**: Standard successful request

```yaml
id: 1
name: canonical-emf-business-metric
skills: ["monitoring-quarkus-lambda-v3-40"]
query: "Add an OrdersPlaced count and an order latency metric to my Quarkus 3.40 Lambda so they show in CloudWatch."
must_pass:
  - "Asks which metric approach to use (EMF to stdout, aws-embedded-metrics, Micrometer, Powertools, OpenTelemetry, PutMetricData) and proposes hand-written EMF unless a standard exists"
  - "Writes one raw JSON line with System.out, with _aws.Timestamp in epoch milliseconds, Namespace not starting with AWS/, Unit Count and Milliseconds, dimensions as flat root strings"
  - "Writes the line before the handler returns"
  - "Points to the Verification Loop (list-metrics, up to 15 minutes) and does not write Terraform"
must_not:
  - "Defaults to Powertools or a push registry"
  - "Uses Log.info for the EMF line"
```

---

## Scenario 2: Edge Case (tenant dimension)

**Type**: Cardinality and cost decision

```yaml
id: 2
name: edge-tenant-as-dimension
skills: ["monitoring-quarkus-lambda-v3-40"]
query: "We have about 4000 tenants and want per-tenant order counts. Add TenantId as a dimension."
must_pass:
  - "Does not add TenantId as a dimension without an ADR (family rule 7) and explains one custom metric per unique dimension combination"
  - "Offers tenantId as a root property with Logs Insights stats by tenantId, or a bounded proxy dimension such as TenantTier"
  - "Asks about the maximum tenant count, per-tenant alarm needs and metric budget"
  - "Tags pricing as (medium confidence) and the Logs Insights scan price as (unverified)"
must_not:
  - "Presents $0.30 per metric as exact for every Region"
  - "Puts PII or secrets in EMF properties"
```

---

## Scenario 3: Misuse Rejection (out of scope)

**Type**: Request outside the skill scope

```yaml
id: 3
name: misuse-alarms-logging-tracing-quarkus4
skills: ["monitoring-quarkus-lambda-v3-40"]
query: "Create the CloudWatch alarm and dashboard in Terraform, configure JSON logging and X-Ray tracing, and do it with Quarkus 4."
must_pass:
  - "Points alarms and dashboards to monitoring-cloudwatch-observability and provisioning-aws-cloudwatch-v6 by name, and Terraform to provisioning-aws-*-v6"
  - "Points logging to logging-quarkus-lambda-v3-40 and tracing to tracing-quarkus-lambda-v3-40"
  - "Says the skill is locked to Quarkus 3.40 and does not cover Quarkus 4"
must_not:
  - "Writes alarm or dashboard HCL"
  - "Presents Quarkus 4 content as valid for 3.40"
```

---

## Scenario 4: Anti-Pattern Trap (EMF through the logger)

**Type**: Code review of an EMF emitter

```yaml
id: 4
name: trap-emf-via-quarkus-log
skills: ["monitoring-quarkus-lambda-v3-40"]
query: "Review: we call Log.info(mapper.writeValueAsString(emfDoc)) and no metric shows up in CloudWatch. quarkus-logging-json is on."
must_pass:
  - "Identifies the Quarkus console format prefix as breaking the rule of a JSON object with no additional data at the beginning or end, and says that `quarkus-logging-json` wrapping the EMF string inside its own JSON document is (medium confidence)"
  - "Replaces it with System.out.println of the raw line"
  - "Says the failure is visible as EMF validation metrics in AWS/Logs and tags their names as (unverified)"
  - "Asks which Lambda log format and level are set, noting a WARN or higher level may drop lines without level (medium confidence)"
must_not:
  - "Suggests a custom log formatter as the first fix"
  - "States the AWS/Logs metric names"
```

---

## Scenario 5: Edge Case (Micrometer and Powertools)

**Type**: Unverified territory

```yaml
id: 5
name: edge-micrometer-cloudwatch-and-powertools
skills: ["monitoring-quarkus-lambda-v3-40"]
query: "Is there a quarkus-micrometer-registry-cloudwatch extension? If not, can I use Powertools metrics with Quarkus instead?"
must_pass:
  - "States no Quarkiverse CloudWatch registry exists (family fact) and the alternative is quarkus-micrometer plus an own MeterRegistry producer with micrometer-registry-cloudwatch2"
  - "Tags the producer details and native support as (unverified) and tags push-registry behaviour on a frozen Lambda as (unverified)"
  - "Says Powertools on Quarkus is not stated on any page and tags it (unverified), and Powertools says frameworks are not officially supported"
  - "Warns that default Micrometer binders would publish JVM meters as billed metrics (medium confidence)"
  - "Notes the Quarkus logging guide forbids Log4j dependencies and Powertools Java logging in Quarkus is (unverified)"
must_not:
  - "Invents a quarkus-micrometer-registry-cloudwatch artifact"
  - "Recommends Powertools or a push registry as the default"
```

---

## Scenario 6: Anti-Pattern Trap (built-in metrics and dimension limit)

**Type**: Duplicate metrics and conflicting limits

```yaml
id: 6
name: trap-reemit-builtins-and-dimension-limit
skills: ["monitoring-quarkus-lambda-v3-40"]
query: "Emit Invocations, Errors and Duration as custom EMF metrics, with 12 dimensions per set. Powertools says the limit is 9, is that right?"
must_pass:
  - "Refuses to re-emit Invocations, Errors and Duration and says to read them from AWS/Lambda at no additional charge"
  - "Cites both Powertools values (9 and 30 on one page) and the AWS EMF spec limit of 30 keys per DimensionSet, and follows the AWS spec"
  - "Reminds that every dimension combination is a billed metric and asks for the bounded set"
must_not:
  - "Silently picks 9 or 30 without citing the conflict"
  - "Lists InitDuration as an AWS/Lambda metric without the (medium confidence) absence-of-evidence tag"
```
