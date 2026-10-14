---
description: 'Design full observability strategy for OCI Java Functions — logging + metrics + tracing (three pillars)'
agent: oci-serverless-architect
argument-hint: 'Current observability gaps, SLO targets, budget'
---

# Design Function Observability

**Skill**: `observing-oci-java-functions`

## What this does

Designs a comprehensive observability strategy for OCI Java Functions orchestrating all three pillars: structured logging (OCI Logging), custom metrics (OCI Monitoring), and distributed tracing (OCI APM).

## Required information

1. **Current state**: What observability exists today? (none, basic stdout, partial)
2. **Function count**: How many functions to instrument?
3. **Call chains**: Multi-function chains that need distributed tracing?
4. **SLO targets**: Latency, error rate, availability requirements?
5. **Alerting needs**: What conditions should trigger notifications?
6. **Budget constraints**: Free-tier APM sufficient or paid?
7. **Compliance**: Audit trail requirements for log retention?
8. **Team readiness**: Ops team familiar with OCI Logging/Monitoring/APM?

## What will be delivered

- Observability architecture overview (three pillars mapped to OCI services)
- Per-pillar implementation recommendations:
  - Logging: framework, format, routing pipeline
  - Metrics: custom metrics, alarm strategy, dashboards
  - Tracing: instrumentation approach, sampling, correlation
- IAM requirements (Resource Principal policies)
- Cost estimation per pillar
- Implementation roadmap with `@oci-functions-java` for code changes
- Infrastructure guidance with `@oci-terraform` for provisioning
