---
description: Provision OCI Object Storage buckets (lifecycle policies, encryption, access control) with Terraform
argument-hint: Bucket name, access type, lifecycle rules, encryption
context: fork
agent: oci-terraform
background: false
disable-model-invocation: true
---

Execute this task now for the OCI serverless project. Read the referenced skill below for the canonical patterns, gather the "Required information", then carry the task through to completion. If the target below is empty, ask for the required information before proceeding.

**Request / target (from the user):** $ARGUMENTS

# Add Object Storage Infrastructure

**Skill**: `provisioning-oci-object-storage`

## What this does

Provisions OCI Object Storage buckets with Terraform — lifecycle policies, CMEK encryption, IAM access control, and event-driven pipeline integration.

## Required information

1. **Bucket name**: Name for the bucket (must be unique in namespace)
2. **Access type**: Private (default), public read, or public read-write?
3. **Storage tier**: Standard or Archive?
4. **Versioning**: Enable object versioning?
5. **Lifecycle rules**: Auto-archive or auto-delete after N days?
6. **Encryption**: Default Oracle-managed keys or customer-managed (Vault)?
7. **Event integration**: Emit events on object create/update/delete?
8. **Compartment**: Target compartment OCID

## What will be generated

- `oci_objectstorage_bucket` resource with access and versioning config
- `oci_objectstorage_object_lifecycle_policy` (if lifecycle rules needed)
- Customer-managed encryption key reference (if Vault integration)
- IAM policy statements for Function access (if event-driven)
- Variables with validation blocks
- Outputs for bucket name, namespace, and OCID
