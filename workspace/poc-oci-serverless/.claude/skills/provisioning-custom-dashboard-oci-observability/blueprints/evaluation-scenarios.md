# Evaluation Scenarios — provisioning-oci-observability

Three scenarios to validate skill effectiveness. Run against each target model before publishing.

---

## Scenario 1: APM Domain Bootstrap

```json
{
  "skills": ["provisioning-oci-observability"],
  "query": "Create Terraform for an OCI APM domain linked to a log group, with span filter and Apdex configuration for a production Java REST API. Store the private data key securely.",
  "expected_behavior": [
    "Creates oci_logging_log_group and references its id in oci_apm_apm_domain.log_group_id",
    "Sets is_free_tier = false for production environment",
    "Creates oci_apm_config_config with config_type = SPAN_FILTER and filter_text",
    "Creates oci_apm_config_config with config_type = APDEX with rules block containing satisfied_response_time and tolerating_response_time",
    "Creates oci_vault_secret using base64encode of APM data key value",
    "Output for APM data key is marked sensitive = true",
    "Provider uses auth = 'InstancePrincipal' (not API key config)",
    "Provider constraint uses ~> 8.0"
  ]
}
```

---

## Scenario 2: Monitoring Alarm for APM Error Rate

```json
{
  "skills": ["provisioning-oci-observability"],
  "query": "Create an OCI monitoring alarm that fires WARNING when APM error rate exceeds 5% for 5 minutes, and escalates to CRITICAL at 20%. Notify an SNS-style topic.",
  "expected_behavior": [
    "Creates oci_ons_notification_topic before the alarm",
    "Creates oci_monitoring_alarm with namespace = 'oracle_apm_rum'",
    "Sets pending_duration = 'PT5M'",
    "Sets repeat_notification_duration to prevent notification spam",
    "Includes overrides block with severity = 'CRITICAL' and different query threshold",
    "Uses message_format = 'ONS_OPTIMIZED'",
    "Does NOT use namespace without pending_duration (anti-pattern avoided)"
  ]
}
```

---

## Scenario 3: Management Dashboard Tile for APM

```json
{
  "skills": ["provisioning-oci-observability"],
  "query": "Create an IaC-managed Management Dashboard saved search widget showing APM error rate as a line chart, referencing the APM domain from a module output.",
  "expected_behavior": [
    "Uses oci_management_dashboard_management_saved_search (not the import resource)",
    "Sets provider_id = 'apm'",
    "Sets type = 'SEARCH_SHOW_IN_DASHBOARD'",
    "In data_config JSON, apmDomainId references module.apm.apm_domain_id (not a hardcoded OCID)",
    "Encodes all JSON fields (ui_config, data_config, nls, drilldown_config, parameters_config) with jsonencode()",
    "Sets is_oob_saved_search = false",
    "Does NOT use import_details inline variable (anti-pattern avoided)"
  ]
}
```
