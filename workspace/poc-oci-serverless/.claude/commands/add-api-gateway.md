---
description: Provision OCI API Gateway resources (Gateway + Deployment + Routes) with Terraform
argument-hint: Routes (path, methods), backend functions, auth type, CORS settings
context: fork
agent: oci-terraform
background: false
disable-model-invocation: true
---

Execute this task now for the OCI serverless project. Read the referenced skill below for the canonical patterns, gather the "Required information", then carry the task through to completion. If the target below is empty, ask for the required information before proceeding.

**Request / target (from the user):** $ARGUMENTS

# Add API Gateway

**Skill**: `provisioning-oci-api-gateway`

## What this does

Provisions OCI API Gateway resources (Gateway, Deployment, Routes, Policies) with Terraform, including auth configuration and CORS.

## Required information

1. **New or existing gateway?**: Create a new gateway or add routes to existing?
2. **Routes**: For each route:
   - Path (e.g., `/api/v1/orders`)
   - HTTP methods (GET, POST, PUT, DELETE)
   - Backend function OCID or reference
3. **Authentication**: Route auth type (No auth / API Key / OAuth2 / JWT / Custom)
4. **CORS**: Enable CORS? (allowed origins, methods, headers)
5. **Subnet**: Which subnet to deploy the gateway in?
6. **Rate limiting**: Request rate limits? (requests per second)

## What will be generated

- `oci_apigateway_gateway` resource (if new gateway)
- `oci_apigateway_deployment` with route configurations
- Request/response policies (auth, CORS, rate limiting)
- Variables with validation blocks
- Outputs for gateway hostname and deployment endpoint
