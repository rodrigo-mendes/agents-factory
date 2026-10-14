---
description: Provision OCI Logging resources (Log Groups, Logs, Unified Monitoring Agent) with Terraform
argument-hint: Log group name, service logs, custom logs, retention
context: fork
agent: oci-observability
background: false
disable-model-invocation: true
---

Execute this task now for the OCI serverless project. Read the referenced skill below for the canonical patterns, gather the "Required information", then carry the task through to completion. If the target below is empty, ask for the required information before proceeding.

**Request / target (from the user):** $ARGUMENTS

# Add Logging

**Skill**: `provisioning-oci-logging`

## What this does

Provisions OCI Logging infrastructure with Terraform — Log Groups, service/custom Log objects, and Unified Monitoring Agent configurations for observability pipelines.

## Required information

1. **Log group name**: Name for the log group
2. **Log type**: Service log (OCI-managed) or custom log (application)?
3. **Service logs**: Which OCI services to enable logging for? (Functions, API Gateway, VCN Flow Logs)
4. **Custom logs**: Need UMA agent configuration for compute/OKE?
5. **Retention (days)**: Log retention period (30-180 days)
6. **Archival**: Route logs to Object Storage for long-term retention?
7. **Compartment**: Target compartment OCID

## What will be generated

- `oci_logging_log_group` resource
- `oci_logging_log` resources (service and/or custom)
- `oci_logging_unified_agent_configuration` (if custom logs)
- Log retention configuration
- Variables with validation blocks
- Outputs for log group OCID and log OCIDs
