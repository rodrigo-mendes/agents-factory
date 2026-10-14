---
description: 'Provision OCI Service Connector Hub resources (data pipelines, log routing, metrics) with Terraform'
agent: oci-observability
argument-hint: 'Source type, target type, data flow description'
---

# Add Connector Hub

**Skill**: `provisioning-oci-connector-hub`

## What this does

Provisions OCI Service Connector Hub resources with Terraform — data routing pipelines from Logging/Streaming sources to Object Storage, Functions, Logging Analytics, or Monitoring targets.

## Required information

1. **Source type**: Logging, Streaming, or Queue?
2. **Source details**: Which log group/stream/queue to read from?
3. **Target type**: Object Storage, Functions, Logging Analytics, Monitoring, Notifications, or Streaming?
4. **Target details**: Destination bucket/function/stream?
5. **Task (optional)**: Apply log filter or function processing between source and target?
6. **Batch size/time**: Batching configuration for throughput optimization?
7. **Compartment**: Target compartment OCID

## What will be generated

- `oci_sch_service_connector` resource with source/target config
- IAM policy statements for connector service principal
- Log filter expressions (if filtering needed)
- Function task reference (if processing needed)
- Variables with validation blocks
- Outputs for connector OCID and state
