---
description: 'Add a new function to an existing OCI Functions Application and register its routes in the API Gateway'
agent: oci-serverless-stack
argument-hint: 'Function name, image, routes, memory/timeout, existing application reference'
---

# Add Function to Existing App

**Skills**: `provisioning-oci-functions`, `provisioning-oci-api-gateway`, `developing-oci-functions-java`

## What this does

Adds a new function to an **existing** Functions Application and registers per-route targeting in the existing API Gateway Deployment. Uses the multi-function infrastructure (`var.functions` + `var.route_backends`).

## Required information

1. **Function name**: Name for the new function (e.g., `func-api-facade`)
2. **Docker image**: OCIR image URI (e.g., `gru.ocir.io/ns/repo/func:tag`)
3. **API routes**: Paths and methods to route to this function (e.g., `POST /secret`, `POST /store`)
4. **Memory**: Function memory in MB (128, 256, 512, 1024, 2048)
5. **Timeout**: Function timeout in seconds (5-300)
6. **Auth type per route**: AUTHENTICATION_ONLY (default) or ANONYMOUS
7. **Function-specific config**: Additional config vars (optional)

## Prerequisites

- Existing `var.functions` list in `terraform.tfvars` (or migration from legacy single-function)
- Existing API Gateway Deployment
- Function Docker image already built and pushed to OCIR

## What will be generated

### Infrastructure (Terraform)
- New entry in `var.functions` list → creates `oci_functions_function` resource
- New entries in `var.route_backends` → creates routes targeting the new function
- No changes to existing resources (additive only)

### Java (if requested)
- New project under `services/{function-name}/` with:
  - `pom.xml`, `func.yaml`, `Dockerfile`
  - Handler class, DTOs, service clients
  - Test class with FnTestingRule

## Adding to Existing Environment

This prompt adds a new function to an existing environment by:
1. Creating a new `module "app_<name>"` block in `apps.tf` using `../../modules/function-app`
2. Adding route entries in `route_backends` of `module.api_gateway`
3. Adding the corresponding image variable in `variables.tf` and `terraform.tfvars`

## Validation

```bash
# Terraform plan should show only ADD operations, no DESTROY
terraform plan -var-file="terraform.tfvars"

# Java build (new function)
cd services/{function-name} && mvn clean package
```
