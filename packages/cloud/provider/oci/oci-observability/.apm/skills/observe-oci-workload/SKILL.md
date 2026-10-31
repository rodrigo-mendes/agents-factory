---
name: observe-oci-workload
description: "Designs, provisions, and validates end-to-end observability for OCI serverless workloads (APM & distributed tracing, Logging, Monitoring alarms, Connector Hub, Management Dashboards). Use when setting up or validating observability infrastructure for an OCI Functions workload, diagnosing missing telemetry signals, or building APM/custom dashboards."
argument-hint: "<capability-slug> [pillar: apm|logging|alarms|connector-hub|dashboards|all]"
context: fork
agent: oci-observability
disable-model-invocation: true
---

# Observe OCI Workload

Routes to the `oci-observability` agent, which owns all five observability pillars for OCI
serverless workloads: APM & distributed tracing, Logging, Monitoring alarms, Connector Hub
pipelines, and Management Dashboards.

## How to invoke

```
/observe-oci-workload <capability-slug> [pillar]
```

Examples:
- `/observe-oci-workload api-handler` — full 5-pillar observability design for the `api-handler` capability
- `/observe-oci-workload event-producer pillar:apm` — APM tracing only for `event-producer`
- `/observe-oci-workload audit-consumer pillar:logging` — structured logging setup for `audit-consumer`
- `/observe-oci-workload rr-rest-proxy pillar:all` — full observability stack (design + provision + validate)

## Agent workflow

The `oci-observability` agent follows a mandatory P0–P5 workflow:

1. **P0 — Verify Docs**: Load handoff records from `docs/handoff/<capability>/`; identify which observability skills are needed from the trigger-keyword table in the auto-loaded `observability-skills` instruction.
2. **P1 — Analyze**: Scan existing `.tf` files for provider version, existing APM/logging/alarms resources, compartment structure.
3. **P2 — Consult**: Read identified SKILL.md files; extract ✅/⚠️/🚫 patterns and composition order.
4. **P3 — Propose**: Present resources to create, naming convention, file structure, dependencies, and ⚠️ Ask-First items. Wait for approval.
5. **P4 — Implement**: Generate `.tf` files and dashboard JSON following skill patterns.
6. **P5 — Validate**: Run `terraform fmt -check` + `terraform validate`; optionally run `validating-oci-observability` scripts; write `docs/handoff/<capability>/result-observability.md`.

## Evaluation Scenarios

See [blueprints/evaluation-scenarios.md](./blueprints/evaluation-scenarios.md).
