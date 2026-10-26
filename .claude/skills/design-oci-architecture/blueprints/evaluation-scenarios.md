# Evaluation Scenarios — design-oci-architecture

## Scenario 1: Canonical — Full-Stack Architecture Design

```json
{
  "skills": ["design-oci-architecture"],
  "query": "We are building a new serverless capability: a REST API for managing store data that authenticates users via OCI IAM Identity Domains and needs to store results in Object Storage. Design the full stack.",
  "expected_behavior": [
    "Routes to @oci-serverless-architect and triggers the full P0-P6 workflow",
    "Identifies scope as 'full-stack': Functions + API Gateway + IAM + Networking",
    "Presents architecture overview: API Gateway (public subnet) → Function (private subnet) → Object Storage (via Service Gateway)",
    "Specifies IAM: Dynamic Group for Functions with Resource Principal, policy for fn-invocation, FaaS virtual-network-family, and read repos",
    "Recommends JWT auth at API Gateway using IAM Identity Domain JWKS endpoint",
    "Recommends rate limiting per route (CLIENT_IP) and CORS with explicit origins",
    "Does NOT generate .tf or .java files — produces ADRs and handoff work-orders"
  ]
}
```

## Scenario 2: Edge — Security Model Review of an Existing Architecture

```json
{
  "skills": ["design-oci-architecture"],
  "query": "Review the security model of our existing OCI serverless architecture. Functions config has DB_PASSWORD as a plaintext environment variable.",
  "expected_behavior": [
    "Routes to @oci-serverless-architect and triggers P1 (Analyze) scan of .tf files and func.yaml",
    "Identifies the plaintext DB_PASSWORD as a critical Never-Do pattern: credentials visible in OCI Console and Terraform state",
    "Recommends replacing DB_PASSWORD with DB_SECRET_OCID pointing to an OCI Vault secret",
    "Specifies the required IAM policy: 'Allow dynamic-group <fn-dg> to read secret-bundles in compartment <name>'",
    "Recommends the function reads the secret at runtime using ResourcePrincipalAuthenticationDetailsProvider",
    "Produces a remediation ADR documenting the before/after design decision",
    "Does NOT refactor the Java or Terraform code itself — delegates to @oci-functions-java and @oci-terraform via work-orders"
  ]
}
```

## Scenario 3: Edge — API Surface Design for Multi-Function Gateway

```json
{
  "skills": ["design-oci-architecture"],
  "query": "We have three Functions: one for store data, one for item data, and one for webhooks. How should we structure the API Gateway routes and deployments?",
  "expected_behavior": [
    "Routes to @oci-serverless-architect with scope 'api-surface'",
    "Recommends a single API Gateway with a single deployment grouping all three routes under a shared path prefix (e.g., /v1/)",
    "Maps each Function to its own ORACLE_FUNCTIONS_BACKEND route: /v1/stores, /v1/items, /v1/webhooks",
    "Applies JWT authentication at the Deployment level (not per-route) for the store and item routes",
    "Recommends ANONYMOUS auth for the webhook route with signature-based validation inside the Function",
    "Notes that rate limiting must be configured per route with different limits (webhook may need higher throughput)",
    "Asks whether a second deployment or gateway is needed if webhook auth model differs significantly"
  ]
}
```

## Scenario 4: Misuse — Requesting Code Generation

```json
{
  "skills": ["design-oci-architecture"],
  "query": "Design the architecture and also write the Terraform for the VCN, subnets, and API Gateway.",
  "expected_behavior": [
    "Produces the architecture design, ADRs, and component diagrams for VCN + API Gateway",
    "Generates the Terraform work-order (stream-b-terraform-infra.md) under docs/handoff/<capability>/ specifying the resources to create",
    "Does NOT write the actual .tf files directly — clearly delegates to @oci-terraform via the work-order",
    "Instructs the user to run /provision-oci-serverless-stack (@oci-serverless-stack) with the handoff context to execute the implementation"
  ]
}
```
