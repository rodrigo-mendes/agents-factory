---
description: 'Provision OCI custom Management Dashboards (+ APM/logging/alarms observability stack) with Terraform'
agent: oci-observability
argument-hint: 'Dashboard name/scope, widgets & APM QL queries, target compartment, existing APM/log OCIDs'
---

# Add APM Dashboards

**Skill**: `provisioning-custom-dashboard-oci-observability`

## What this does

Provisions OCI custom **Management Dashboards** with Terraform (`oracle/oci` v8.x), optionally
alongside the supporting observability stack — APM domains, Logging log groups, and Monitoring
alarms — in one integrated module.

## Required information

1. **Dashboard scope**: What should the dashboard show? (function latency, error rate, traces, logs, alarm state)
2. **Widgets / APM QL**: Which widgets and APM QL / metric queries per tile?
3. **Existing observability OCIDs**: APM domain OCID, log group OCIDs, alarm OCIDs to reference (or provision fresh?)
4. **Full stack vs dashboard-only**: Provision the whole APM+logging+alarms stack, or just the dashboard over existing resources?
5. **Compartment**: Target compartment OCID
6. **IAM**: Who gets `use` vs `manage` on the dashboard?

## What will be generated

- `oci_management_dashboard_management_dashboard` resource(s) with widget/tile JSON
- Optional `oci_apm_apm_domain`, `oci_logging_log_group`/`oci_logging_log`, and `oci_monitoring_alarm` resources (full-stack mode)
- IAM policy statements for dashboard `use`/`manage`
- Variables with validation blocks
- Outputs for dashboard OCID(s)

> **Note:** This skill is a superset of `provisioning-oci-apm` + `provisioning-oci-logging` +
> `oci-monitoring-alarms`. For a single isolated pillar, use `/add-apm-infrastructure`,
> `/add-logging`, or `/design-monitoring-alarms` instead.
