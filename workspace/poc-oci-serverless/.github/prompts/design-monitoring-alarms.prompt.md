---
description: 'Design OCI Monitoring alarms — multi-threshold alerting, suppressions, custom metrics, and IAM authorization'
agent: oci-observability
argument-hint: 'Metrics to alert on, severity levels, notification targets'
---

# Design Monitoring Alarms

**Skill**: `oci-monitoring-alarms`

## What this does

Designs and implements OCI Monitoring alarm architecture — threshold definitions, multi-severity alerting, maintenance window suppressions, custom metric pipelines, and IAM authorization patterns.

## Required information

1. **Metrics to alert on**: Which OCI metrics? (oci_faas, oci_apigateway, custom)
2. **Thresholds**: Warning and critical thresholds for each metric?
3. **Notification targets**: Email, PagerDuty, Slack (via ONS topics)?
4. **Suppressions**: Maintenance windows or recurring suppression schedules?
5. **Custom metrics**: Need PostMetricData ingestion from Functions?
6. **Composite alarms**: Combine multiple conditions into single alarm?
7. **IAM**: Who can acknowledge/resolve alarms?

## What will be generated

- `oci_monitoring_alarm` resources with MQL queries
- `oci_monitoring_alarm_suppression` for maintenance windows
- ONS topic integration for notifications
- Custom metric namespace definitions (if PostMetricData)
- IAM policy statements for alarm management
- Terraform variables and outputs
