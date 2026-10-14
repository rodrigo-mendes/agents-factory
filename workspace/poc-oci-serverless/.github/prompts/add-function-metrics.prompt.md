---
description: 'Add custom metrics instrumentation to OCI Java Functions using OCI Monitoring API'
agent: oci-functions-java
argument-hint: 'Metrics to emit, namespace, alarm integration'
---

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
