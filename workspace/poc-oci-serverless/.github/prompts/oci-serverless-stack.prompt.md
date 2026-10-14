---
description: 'Generic entry point for end-to-end serverless capability creation spanning Java function code and Terraform infrastructure. Routes to the oci-serverless-stack agent.'
agent: oci-serverless-stack
argument-hint: 'Describe the serverless capability you want to create end-to-end'
---

# OCI Serverless Full-Stack Creation

## Context Collection

Before starting, I need to understand your end-to-end requirement.

**Answer these questions:**

1. **Function name**: What should the function be called?

2. **API route**: What path and HTTP method(s) will expose this function? (e.g., `GET /api/v1/orders`)

3. **Authentication**: What auth type for the API route? (No auth / API Key / OAuth2 / JWT)

4. **Function capabilities**: What will the function do?
   - Read/write Object Storage
   - Call external REST APIs
   - Publish events to Streaming/Notifications
   - Process incoming events
   - Simple request/response

5. **Existing infrastructure**: Is there already a VCN, Functions Application, API Gateway, or IAM setup?

## Workflow

Once I have your answers, I will follow the P0–P5 workflow:
- **P0**: Load both Java and Terraform skills
- **P1**: Analyze existing components across both domains
- **P2**: Consult patterns and plan dependency order
- **P3**: Present end-to-end plan (Java + Terraform + API Gateway)
- **P4**: Implement in order: Function code → Terraform infra → API route
- **P5**: Validate both `mvn compile` and `terraform validate`, plus cross-domain consistency

> **Tip**: For Java-only or Terraform-only work, use `@oci-functions-java` or `@oci-terraform` instead.
