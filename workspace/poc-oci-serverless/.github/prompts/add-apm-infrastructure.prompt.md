---
description: 'Provision OCI APM resources (domains, synthetic monitors, Apdex rules, span filters) with Terraform'
agent: oci-observability
argument-hint: 'APM domain name, synthetic monitor targets, data key security'
---

# Add APM Infrastructure

**Skill**: `provisioning-oci-apm`

## What this does

Provisions OCI Application Performance Monitoring resources with Terraform — APM domains, synthetic monitors, Apdex rules, span filters, metric groups, and data key management.

## Required information

1. **APM domain name**: Name for the APM domain
2. **Free tier**: Use free-tier domain or paid?
3. **Synthetic monitors**: URLs to monitor with synthetic checks?
4. **Vantage points**: Which OCI regions for synthetic monitoring?
5. **Apdex rules**: Custom Apdex thresholds per operation?
6. **Data key security**: Auto-generate or provide existing data keys?
7. **Compartment**: Target compartment OCID

## What will be generated

- `oci_apm_apm_domain` resource
- `oci_apm_synthetics_monitor` resources (if synthetic monitoring)
- `oci_apm_config_config` for Apdex rules and span filters
- Data key outputs for agent instrumentation
- Variables with validation blocks
- Outputs for APM domain OCID and data upload endpoint
