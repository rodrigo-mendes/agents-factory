# Evaluation Scenarios — configuring-oci-monitoring-alarms

## Scenario 1: Production Alarm with Multi-Threshold CPU Alerting

```json
{
  "skills": ["configuring-oci-monitoring-alarms"],
  "query": "Create a Terraform alarm for an OCI Compute instance pool in the prod compartment that alerts CRITICAL above 95% CPU and WARNING above 80% CPU, with appropriate pending durations and PagerDuty notification.",
  "expected_behavior": [
    "Generates a single oci_monitoring_alarm resource using the overrides array (not two separate alarm resources)",
    "Places CRITICAL override at overrides[0] (evaluated first) with pending_duration PT1M–PT2M, and WARNING at overrides[1] with pending_duration PT3M–PT5M",
    "Base alarm rule set to INFO or WARNING for lower threshold",
    "Sets metric_compartment_id to var.prod_compartment_ocid with metric_compartment_id_in_subtree = false",
    "Sets evaluation_slack_duration to at least PT5M",
    "Sets repeat_notification_duration = PT15M on CRITICAL",
    "Uses oci_computeagent namespace and CpuUtilization metric with groupBy(resourceId)"
  ]
}
```

---

## Scenario 2: Custom Metric Ingestion with Secure IAM Authorization

```json
{
  "skills": ["configuring-oci-monitoring-alarms"],
  "query": "An OCI Functions application needs to emit a custom business metric called order_processing_latency_ms to OCI Monitoring. Set up the Terraform IAM resources and show the Python SDK snippet.",
  "expected_behavior": [
    "Creates oci_identity_dynamic_group matching resource.type = 'fnfunc' with resource.compartment.id scoped to the app compartment",
    "Creates oci_identity_policy with 'use metrics' verb (not 'manage' or 'read') scoped to the specific namespace via where target.metrics.namespace = 'myapp_*' or exact namespace",
    "Python SDK snippet uses oci.auth.signers.InstancePrincipalsSecurityTokenSigner() or resource principal — no hardcoded config dict with key_content",
    "SDK service_endpoint set to telemetry-ingestion.{region}.oraclecloud.com (not telemetry)",
    "No API keys, tenancy OCIDs, or private key content appears in any code or Terraform"
  ]
}
```

---

## Scenario 3: Maintenance Window Suppression with Recurring Schedule

```json
{
  "skills": ["configuring-oci-monitoring-alarms"],
  "query": "Configure OCI Monitoring to suppress all alarm notifications in the app compartment every Sunday night from 02:00 to 04:00 UTC for a weekly database patching window, using Terraform.",
  "expected_behavior": [
    "Creates oci_monitoring_alarm_suppression resource (NOT sets is_enabled = false on alarms)",
    "Uses alarm_suppression_target with target_type = COMPARTMENT and compartment_id pointing to the correct compartment",
    "Sets level = ALARM to suppress all alarms",
    "Includes suppression_conditions block with condition_type = RECURRENCE and FREQ=WEEKLY;BYDAY=SU;BYHOUR=2 in suppression_recurrence",
    "Sets suppression_duration = PT2H",
    "Sets time_suppress_from and time_suppress_until as RFC3339 anchor dates for the first occurrence",
    "Does NOT disable any alarm resource — explains that alarm evaluation continues and alarm history is preserved"
  ]
}
```
