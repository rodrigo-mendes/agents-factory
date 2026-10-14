---
description: 'Provision OCI API Gateway resources (Gateway + Deployment + Routes) with Terraform'
agent: oci-terraform
argument-hint: 'Routes (path, methods), backend functions, auth type, CORS settings'
---

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
