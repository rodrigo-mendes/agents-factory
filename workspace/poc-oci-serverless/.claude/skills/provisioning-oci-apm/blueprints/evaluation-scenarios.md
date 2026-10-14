# Evaluation Scenarios — provisioning-oci-apm

3 evaluation scenarios for testing skill effectiveness.

---

## Scenario 1: Provision a Production APM Domain

```json
{
  "skills": ["provisioning-oci-apm"],
  "query": "Create Terraform HCL to provision a production OCI APM domain in compartment ocid1.compartment.oc1..abc for application 'payment-service'.",
  "expected_behavior": [
    "Sets is_free_tier = false for production",
    "Includes lifecycle.prevent_destroy = true",
    "Includes lifecycle.ignore_changes = [is_free_tier]",
    "Reads APM data keys via oci_apm_data_keys data source and stores private key in oci_vault_secret",
    "Does NOT output the raw private data key value",
    "Includes defined_tags and freeform_tags with environment and application labels",
    "Uses variable validation with regex for compartment_id OCID format"
  ]
}
```

---

## Scenario 2: Add a REST Synthetic Monitor with Interval Validation

```json
{
  "skills": ["provisioning-oci-apm"],
  "query": "Add a REST synthetic monitor for https://api.example.com/health that runs every 2 minutes. The team wants it temporarily disabled without losing run history.",
  "expected_behavior": [
    "Sets repeat_interval_in_seconds = 120 (>= 60 minimum for REST — valid)",
    "Sets status = var.monitoring_enabled ? 'ENABLED' : 'DISABLED' (not count = 0)",
    "Does NOT use count = 0 to disable the monitor",
    "Includes variable validation asserting repeat_interval_in_seconds >= 60",
    "Sets timeout_in_seconds <= 60 (50% of 120s interval, no retry)",
    "References apm_domain_id via resource attribute, not hardcoded OCID",
    "Includes freeform_tags and defined_tags"
  ]
}
```

---

## Scenario 3: Create a Metric Group with SLA Alarm

```json
{
  "skills": ["provisioning-oci-apm"],
  "query": "Create Terraform resources to track HTTP 5xx error rate from the checkout service spans, publish it as a custom metric, and alert when error rate exceeds 3% for 5 minutes.",
  "expected_behavior": [
    "Creates oci_apm_config_config with config_type = 'SPAN_FILTER' first (filter_text targeting checkout-service 5xx spans)",
    "Creates oci_apm_config_config with config_type = 'METRIC_GROUP' referencing filter_id = oci_apm_config_config.<span_filter>.id (not a hardcoded OCID)",
    "Sets namespace consistently in both METRIC_GROUP and oci_monitoring_alarm query",
    "Creates oci_monitoring_alarm with query using the exact namespace string",
    "Adds depends_on = [oci_apm_config_config.<metric_group>] on the alarm",
    "Both config resources include freeform_tags"
  ]
}
```
