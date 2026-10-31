# Evaluation Scenarios — provisioning-oci-logging

These scenarios test whether the skill activates correctly and produces safe, accurate output.

---

## Scenario 1: New Application Logging Stack

```json
{
  "skills": ["provisioning-oci-logging"],
  "query": "Create Terraform code to set up OCI Logging for a new Node.js application running on compute instances. The app writes JSON logs to /var/log/nodeapp/*.log. We need 90-day retention and the logs should be searchable in the OCI Console.",
  "expected_behavior": [
    "Creates oci_logging_log_group with explicit freeform_tags and lifecycle prevent_destroy",
    "Creates oci_logging_log with log_type=CUSTOM, is_enabled=true, retention_duration=90",
    "Creates oci_identity_dynamic_group in tenancy compartment with instance.compartment.id matching rule",
    "Creates oci_identity_policy with 'use log-content' and 'read log-groups' statements",
    "Creates oci_logging_unified_agent_configuration with source_type=LOG_TAIL, parser_type=JSON, paths=['/var/log/nodeapp/*.log'], depends_on=[oci_identity_policy]",
    "Uses group_list=[oci_identity_dynamic_group.log_agents.id] (dynamic group OCID, not hardcoded instance OCID)",
    "Uses provider with auth=InstancePrincipal or ApiKey profile, no hardcoded credentials",
    "Includes variable validation for retention_duration constraining to [30,60,90,120,150,180]"
  ]
}
```

---

## Scenario 2: Compliance Log Archival Beyond 180 Days

```json
{
  "skills": ["provisioning-oci-logging"],
  "query": "We have a financial services application that needs audit logs retained for 7 years. OCI Logging maxes at 180 days. Set up the complete archival pipeline with Terraform.",
  "expected_behavior": [
    "Creates dedicated oci_logging_log_group for audit logs (separate from app logs), with lifecycle prevent_destroy=true",
    "Creates oci_logging_log with retention_duration=180 (maximum OCI Logging window)",
    "Creates oci_sch_service_connector sourcing the audit log group and targeting Object Storage",
    "Creates IAM policy with request.principal.type='serviceconnector' for SCH → Object Storage writes",
    "Creates oci_objectstorage_bucket with access_type=NoPublicAccess and versioning=Enabled",
    "Creates oci_objectstorage_object_lifecycle_policy with DELETE rule at time_amount=2557 (7 years in days)",
    "Warns that Connector Hub captures only new data from activation — must configure before 180-day window expires",
    "Does NOT mix audit logs with application logs in the same Log Group"
  ]
}
```

---

## Scenario 3: OKE Container Log Collection

```json
{
  "skills": ["provisioning-oci-logging"],
  "query": "Set up Terraform to collect logs from all containers running in our OKE cluster. The cluster ID is available as a Terraform variable. Use 60-day retention.",
  "expected_behavior": [
    "Creates oci_identity_dynamic_group in tenancy compartment with matching_rule using tag.oke-cluster-id.value to scope to the specific cluster",
    "Creates oci_logging_unified_agent_configuration with configuration_type=LOGGING",
    "Sets source_type=LOG_TAIL, paths=['/var/log/pods/**/*.log']",
    "Sets parser_type=CRI with is_merge_cri_fields=true",
    "Creates oci_logging_log with log_type=CUSTOM, retention_duration=60, is_enabled=true",
    "Does NOT use configuration_type=MONITORING (that is for Prometheus scraping, not log files)",
    "Does NOT hardcode any instance OCIDs in group_list",
    "Includes depends_on=[oci_identity_policy] on the UMA configuration resource"
  ]
}
```

---

## Scenario 4: Anti-Pattern Detection

```json
{
  "skills": ["provisioning-oci-logging"],
  "query": "Review this Terraform code and tell me if there are any issues:\n\nresource \"oci_logging_log\" \"app\" {\n  display_name = \"app-logs\"\n  log_group_id = oci_logging_log_group.main.id\n  log_type     = \"CUSTOM\"\n  is_enabled   = false\n}\n\nresource \"oci_logging_unified_agent_configuration\" \"ua\" {\n  group_association {\n    group_list = [\"ocid1.instance.oc1.iad.AAAAAAAAXXXXXXXX\"]\n  }\n}",
  "expected_behavior": [
    "Flags missing retention_duration (defaults to 30 days — CRITICAL data loss risk)",
    "Flags is_enabled=false (silently stops log ingestion — HIGH impact)",
    "Flags hardcoded instance OCID in group_list (new instances miss log collection — HIGH)",
    "Flags missing IAM policy for UMA (agent fails silently — HIGH)",
    "Provides corrected code with retention_duration=var.log_retention_days, is_enabled=var.logging_enabled, group_list=[oci_identity_dynamic_group.log_agents.id], and paired oci_identity_policy resource"
  ]
}
```
