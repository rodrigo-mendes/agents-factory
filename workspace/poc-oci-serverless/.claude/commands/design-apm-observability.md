---
description: Design OCI APM observability architecture — distributed tracing, OpenTelemetry, RUM, and cost governance
argument-hint: Services to trace, latency requirements, budget constraints
context: fork
agent: oci-observability
background: false
disable-model-invocation: true
---

Execute this task now for the OCI serverless project. Read the referenced skill below for the canonical patterns, gather the "Required information", then carry the task through to completion. If the target below is empty, ask for the required information before proceeding.

**Request / target (from the user):** $ARGUMENTS

# Design APM Observability

**Skill**: `monitoring-oci-apm`

## What this does

Designs APM and distributed tracing architecture using OCI Application Performance Monitoring — instrumentation strategy, OpenTelemetry integration, synthetic monitoring, and cost governance.

## Required information

1. **Services to trace**: Which services need distributed tracing? (Functions, OKE, compute)
2. **Instrumentation approach**: Auto-instrumentation agent or manual OpenTelemetry SDK?
3. **Trace sampling**: Full capture or sampling strategy? (cost vs visibility)
4. **Synthetic monitoring**: External URL health checks needed?
5. **RUM**: Browser/mobile Real User Monitoring required?
6. **Latency requirements**: Apdex thresholds and SLO targets?
7. **Budget constraints**: Free-tier domain or paid throughput?
8. **Security**: Data key rotation? Restrict trace data access?

## What will be delivered

- APM domain architecture (free vs paid, regional placement)
- Instrumentation strategy per service type
- OpenTelemetry collector configuration guidance
- Synthetic monitor placement and scheduling
- Sampling and retention recommendations
- Cost estimation and governance controls
- Provisioning handoff to `@oci-observability` (`/add-apm-dashboards`, `/add-apm-infrastructure`, `/add-logging`, `/add-connector-hub`)
