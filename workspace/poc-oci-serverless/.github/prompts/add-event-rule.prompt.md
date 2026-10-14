---
description: 'Provision OCI Events Rules for event-driven automation with Terraform'
agent: oci-terraform
argument-hint: 'Event type, source service, condition filter, target action'
---

# Add Event Rule

**Skill**: `provisioning-oci-events`

## What this does

Provisions OCI Events Rules with Terraform to automate responses to OCI service events (e.g., trigger a function when an object is uploaded to a bucket).

## Required information

1. **Event type**: Which OCI event to react to? (e.g., `com.oraclecloud.objectstorage.createobject`)
2. **Source service**: Which OCI service emits the event? (Object Storage, IAM, Functions, etc.)
3. **Condition filter**: Any filtering conditions? (resource name, compartment, attributes)
4. **Target action**: What should happen when the event fires?
   - Invoke an OCI Function
   - Publish to Streaming
   - Send a Notification
5. **Target resource**: OCID of the function/stream/topic to invoke
6. **Compartment**: Target compartment OCID

## What will be generated

- `oci_events_rule` with condition, action type, and target
- Event condition JSON with proper attribute filtering
- Variables with OCID validation
- Outputs for rule OCID and state
