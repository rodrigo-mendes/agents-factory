---
description: Provision OCI IAM resources (Dynamic Groups + Policies) with Terraform for serverless workloads
argument-hint: Resource type needing permissions, required actions, compartment scope
context: fork
agent: oci-terraform
background: false
disable-model-invocation: true
---

Execute this task now for the OCI serverless project. Read the referenced skill below for the canonical patterns, gather the "Required information", then carry the task through to completion. If the target below is empty, ask for the required information before proceeding.

**Request / target (from the user):** $ARGUMENTS

# Add IAM

**Skill**: `provisioning-oci-iam`

## What this does

Provisions IAM Dynamic Groups and Policies with Terraform to grant OCI Functions (or other resources) the permissions they need, following least-privilege principles.

## Required information

1. **Resource type**: What needs permissions? (Functions, API Gateway, Streaming, etc.)
2. **Required permissions**: What actions must be allowed? (e.g., read Object Storage, manage Vault secrets, publish to Streaming)
3. **Compartment scope**: Which compartment(s) should the policy apply to?
4. **Existing dynamic groups?**: Are there existing dynamic groups to reuse or create new?
5. **Matching rules**: Resource matching criteria (compartment OCID, resource type, specific resource OCID)

## What will be generated

- `oci_identity_dynamic_group` with matching rules
- `oci_identity_policy` with least-privilege statements
- Variables with OCID validation
- Outputs for dynamic group OCID
