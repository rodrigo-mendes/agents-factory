# Evaluation Scenarios — monitoring-oci-apm-dashboards

Used to test whether the skill activates correctly, produces safe outputs, and applies the right pattern from context.

---

## Scenario 1: Java Agent Instrumentation on Kubernetes

```json
{
  "skills": ["monitoring-oci-apm-dashboards"],
  "query": "How do I instrument a Java Spring Boot application running on OKE with OCI APM? The app connects to an Autonomous Database. I want latency and SQL metrics visible on a dashboard.",
  "expected_behavior": [
    "Provides APM Java Agent injection via -javaagent JVM flag in Kubernetes container spec",
    "Shows Agent.properties with upload endpoint and service name configuration",
    "Uses init container pattern to inject the agent binary into the application pod",
    "Retrieves Private Data Key from OCI Vault using Instance Principal (NOT hardcoded in config)",
    "Provides APM QL query for SQL latency: show spans | where dbStatement is not null | group by dbStatement | select avg(duration)",
    "Warns to use PreparedStatement for all JDBC queries (anti-pattern 3 prevention)",
    "Instructs to link dashboard APM QL widget to global ApmDomain filter variable"
  ]
}
```

---

## Scenario 2: Securing a Production Dashboard — IAM Audit

```json
{
  "skills": ["monitoring-oci-apm-dashboards"],
  "query": "Our security team flagged that several individual users have 'manage management-dashboards' on the production compartment. How do I fix this and prevent it going forward?",
  "expected_behavior": [
    "Identifies the anti-pattern: individual user IAM grants for manage management-dashboards",
    "Provides audit CLI command to detect user-level grants: oci iam policy list ... | grep 'allow user.*manage management-dashboards'",
    "Provides correct fix: remove individual grants, create ObservabilityEngineers group, assign manage management-dashboards to the group only",
    "Provides correct IAM policy syntax for group-level grant",
    "Explains blast radius: individual grants survive team changes, invisible in membership audits",
    "Does NOT suggest modifying production dashboards directly — recommends pipeline-based JSON import workflow"
  ]
}
```

---

## Scenario 3: Choosing Widget Data Source for a High-Volume Service

```json
{
  "skills": ["monitoring-oci-apm-dashboards"],
  "query": "We have a payment service processing 10 million requests per hour. We need an always-on executive dashboard showing SLA (p99 latency, error rate) and a separate SRE debug dashboard. Which APM visualization approach should we use for each?",
  "expected_behavior": [
    "Asks about retention SLA and confirms high volume before recommending sampling",
    "Recommends OCI Monitoring metrics (via APM Dynamic Metric Generation) for the executive SLA dashboard — fast rendering, low cost, supports OCI Alarms",
    "Recommends APM QL (Trace Explorer widgets) for the SRE diagnostic dashboard — span-level granularity, SQL statement analysis",
    "Recommends enabling Dynamic Metric Generation in APM Domain admin for ApmRequestCount, ApmResponseTime, ApmErrorRate",
    "Recommends sampling rules: 100% for 5xx/4xx errors, 10% for 2xx success traces (Decision 3 pattern)",
    "Provides MQL example for SLA metric widget: ApmRequestCount[5m].sum()",
    "Warns against using APM QL for the always-on executive dashboard — explains cost and rendering latency tradeoffs"
  ]
}
```

---

## Scenario 4 (Edge): Migrating Dashboard Across Compartments

```json
{
  "skills": ["monitoring-oci-apm-dashboards"],
  "query": "We need to copy our production APM dashboard to a new staging compartment for testing. How do we do this safely?",
  "expected_behavior": [
    "Instructs to export dashboard as JSON via OCI Console Actions → Export Dashboard Definition",
    "Warns that importing does not migrate the APM Domain — the JSON must be updated with the staging APM Domain OCID before import",
    "Explains how to update domain OCIDs in JSON: replace production OCID with staging OCID",
    "Instructs to use OCI CLI or Resource Manager for programmatic import",
    "Recommends verifying no hardcoded OCIDs remain in widget queries after import (Verification Loop step 4)",
    "Does NOT suggest manually recreating widgets — always use JSON export/import"
  ]
}
```
