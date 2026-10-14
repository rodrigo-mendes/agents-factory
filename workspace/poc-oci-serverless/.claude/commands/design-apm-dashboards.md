---
description: Design OCI APM Management Dashboards — widget layout, APM QL queries, global filters, and dashboard IAM
argument-hint: Signals to visualize, audience, existing APM domain, IAM scope
context: fork
agent: oci-observability
background: false
disable-model-invocation: true
---

Execute this task now for the OCI serverless project. Read the referenced skill below for the canonical patterns, gather the "Required information", then carry the task through to completion. If the target below is empty, ask for the required information before proceeding.

**Request / target (from the user):** $ARGUMENTS

# Design APM Dashboards

**Skill**: `monitoring-oci-apm-dashboards`

## What this does

Designs OCI APM **Management Dashboard** architecture — unified observability across Java
microservices, browser RUM, and synthetic monitors: widget/tile layout, APM QL query design,
global filters, trace sampling considerations, and dashboard-specific IAM (`use` vs `manage`).

## Required information

1. **Audience**: Who consumes the dashboard? (SRE on-call, dev team, leadership)
2. **Signals**: Which signals to visualize? (latency percentiles, error rate, trace waterfalls, Apdex, RUM, synthetics)
3. **APM domain**: Existing APM domain OCID, or does it need designing first?
4. **Global filters**: Filter by service, operation, region, environment?
5. **Sampling**: Full capture or sampling — how does it affect widget fidelity?
6. **IAM**: `use`-only viewers vs `manage` editors; which groups/dynamic groups?

## What will be delivered

- Dashboard layout design (tiles, widget types, drill-down paths)
- APM QL query set per widget
- Global filter and variable strategy
- Dashboard IAM (RBAC) recommendation — `use` vs `manage`
- Trace sampling / fidelity guidance
- Handoff to `/add-apm-dashboards` for Terraform provisioning
