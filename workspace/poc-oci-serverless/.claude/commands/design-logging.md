---
description: Design OCI Logging and observability architecture including log collection, retention, alerting, and archival pipelines
argument-hint: Services to monitor, retention needs, alerting requirements
context: fork
agent: oci-observability
background: false
disable-model-invocation: true
---

Execute this task now for the OCI serverless project. Read the referenced skill below for the canonical patterns, gather the "Required information", then carry the task through to completion. If the target below is empty, ask for the required information before proceeding.

**Request / target (from the user):** $ARGUMENTS

# Design Logging

**Skill**: `designing-oci-logging`

## What this does

Designs the logging and observability architecture for OCI workloads — log group hierarchy, collection strategy, retention policies, alerting pipelines, and archival patterns.

## Required information

1. **Services to monitor**: Which OCI services need logging? (Functions, API Gateway, VCN, Load Balancer)
2. **Custom logs**: Application-level logging from compute/OKE needed?
3. **Retention requirements**: Operational retention (30-180 days)? Long-term archival?
4. **Alerting needs**: Which log patterns should trigger alerts or notifications?
5. **Routing requirements**: Send logs to Logging Analytics, Object Storage, or external SIEM?
6. **Compliance**: Regulatory log retention and audit trail requirements?
7. **Cost constraints**: Volume-based pricing considerations?

## What will be delivered

- Log group hierarchy design
- Service log enablement strategy (which services, which log categories)
- Custom log collection design (UMA configurations)
- Retention and archival pipeline (Logging → Connector Hub → Object Storage)
- Alerting strategy (log-derived metrics, alarm rules)
- Cost estimation and optimization recommendations
- Provisioning handoff to `@oci-observability` (`/add-apm-dashboards`, `/add-apm-infrastructure`, `/add-logging`, `/add-connector-hub`)
