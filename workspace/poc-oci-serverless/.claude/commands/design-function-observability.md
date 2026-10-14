---
description: Design full observability strategy for OCI Java Functions — logging + metrics + tracing (three pillars)
argument-hint: Current observability gaps, SLO targets, budget
context: fork
agent: oci-serverless-architect
background: false
disable-model-invocation: true
---

Execute this task now for the OCI serverless project. Read the referenced skill below for the canonical patterns, gather the "Required information", then carry the task through to completion. If the target below is empty, ask for the required information before proceeding.

**Request / target (from the user):** $ARGUMENTS

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
- Dashboard recommendations (Management Dashboards scope: ops golden-signals, SLA/SLO, distributed-tracing view, alerting surface) — provisioned by `@oci-observability` via `provisioning-custom-dashboard-oci-observability`; capture render-valid widget shape from the Console `{JSON}` editor and validate live with `check-dashboards.sh` (5th pillar). See `.claude/rules/observability-skills.md` gotchas.
- IAM requirements (Resource Principal policies)
- Cost estimation per pillar
- Implementation roadmap with `@oci-functions-java` for code changes
- Infrastructure guidance with `@oci-terraform` for provisioning
