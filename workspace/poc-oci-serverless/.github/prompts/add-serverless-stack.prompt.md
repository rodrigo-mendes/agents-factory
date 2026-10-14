---
description: 'Provision a complete OCI serverless stack (Functions + API Gateway + IAM) as an integrated Terraform module'
agent: oci-terraform
argument-hint: 'Function name, API route, auth type for integrated provisioning'
---

# Add Serverless Stack

**Skill**: `provisioning-oci-serverless-stack`

## What this does

Provisions a complete, integrated serverless API stack with Terraform — combining Functions, API Gateway, and IAM in a single coordinated module. Use this instead of provisioning each service individually.

## Required information

1. **Function name**: Name for the serverless function
2. **API route**: Path and HTTP methods (e.g., `POST /api/v1/orders`)
3. **Auth type**: API route authentication (No auth / API Key / OAuth2 / JWT)
4. **Docker image**: Function image source (OCIR path)
5. **Memory/timeout**: Function resource sizing
6. **Existing infrastructure**: Is there already a VCN, subnet, or compartment?
7. **Mode**: Full scaffold from scratch or incremental addition to existing stack?

## What will be generated

- `oci_functions_application` + `oci_functions_function`
- `oci_apigateway_gateway` + `oci_apigateway_deployment` with routes
- `oci_identity_dynamic_group` + `oci_identity_policy` (least privilege)
- Coordinated variables, outputs, and cross-resource references
- All resources tagged with `local.common_tags`

> **Tip**: For individual service provisioning, use the specific prompts: `add-functions-infra`, `add-api-gateway`, `add-iam`.
