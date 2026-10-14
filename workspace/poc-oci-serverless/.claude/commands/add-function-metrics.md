---
description: Add custom metrics instrumentation to OCI Java Functions using OCI Monitoring API. Use when instrumenting a Java function to emit custom metrics to OCI Monitoring.
argument-hint: Metrics to emit, namespace, alarm integration
context: fork
agent: oci-functions-java
background: false
disable-model-invocation: true
---

Execute this task now for the OCI serverless project. Read the referenced skill below for the canonical patterns, gather the "Required information", then carry the task through to completion. If the target below is empty, ask for the required information before proceeding.

**Request / target (from the user):** $ARGUMENTS

# Add Function Metrics

**Skill**: `monitoring-oci-java-functions`

## What this does

Instruments OCI Java Functions with custom metrics using OCI Monitoring API (PostMetricData) — metric definitions, batch publishing, alarm integration, and Terraform monitoring stack.

## Required information

1. **Metrics to emit**: What to measure? (latency, error count, throughput, business metrics)
2. **Metric namespace**: Custom namespace name (e.g., `custom_serverless`)
3. **Dimensions**: Which dimensions per metric? (functionName, operation, status)
4. **Publishing frequency**: Per-invocation or batched?
5. **Alarm integration**: Create alarms for these metrics?
6. **Resource Principal**: Already configured for OCI SDK access?

## What will be generated

- MonitoringClient initialization with Resource Principal auth
- PostMetricData helper with batching support
- Metric dimension builders
- Timeout budget integration (metrics should not consume function timeout)
- pom.xml dependency for oci-java-sdk-monitoring
- Terraform alarm resources (if alarm integration requested)
