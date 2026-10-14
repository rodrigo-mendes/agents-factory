# Evaluation Scenarios — provisioning-oci-serverless-stack

## Scenario 1: Canonical — Full serverless stack from scratch

```json
{
  "skills": ["provisioning-oci-serverless-stack"],
  "query": "Provision a complete OCI serverless stack: a private-subnet Function Application with one Java function, an API Gateway in a public subnet routing /api/orders POST to that function with JWT auth and rate limiting, and the minimum IAM to wire them together.",
  "expected_behavior": [
    "Creates oci_functions_application in a private subnet",
    "Creates oci_functions_function referencing an OCIR image via variable",
    "Creates oci_apigateway_gateway with endpoint_type = 'PUBLIC' in a public subnet",
    "Creates oci_apigateway_deployment with JWT authentication_policy, rate_limiting, and a route with ORACLE_FUNCTIONS_BACKEND",
    "Creates oci_identity_dynamic_group matching functions by compartment.id",
    "Creates oci_identity_policy granting 'use fn-invocation' to the API Gateway service principal",
    "Adds depends_on = [module.iam] on both function-app and api-gateway modules",
    "Uses encrypted remote state backend (OCI Object Storage with versioning = 'Enabled')",
    "Does NOT hardcode any OCID — uses module output references throughout"
  ]
}
```

## Scenario 2: Edge — Adding a second Function to an existing stack

```json
{
  "skills": ["provisioning-oci-serverless-stack"],
  "query": "I have the stack deployed. I need to add a second function 'func-api-facade' to handle /secret and /store routes. How do I extend the Terraform without destroying existing resources?",
  "expected_behavior": [
    "Adds a new module 'app_api_facade' block in apps.tf using the function-app module",
    "Adds two new entries to route_backends with function_id = module.app_api_facade.function_id",
    "Instructs to run terraform plan first and verify only new resource additions (no destructive changes)",
    "Confirms existing routes and the api-handler function are untouched",
    "Does NOT suggest recreating the API Gateway or the Dynamic Group",
    "References the Multi-Function Composition section and the 'Adding a New Function' checklist"
  ]
}
```

## Scenario 3: Edge — State management recovery after corrupted state

```json
{
  "skills": ["provisioning-oci-serverless-stack"],
  "query": "Two team members ran terraform apply concurrently on the same stack. The state file may be corrupted. How do I recover without destroying live infrastructure?",
  "expected_behavior": [
    "Identifies lack of native state locking on OCI S3-compatible backend as the root cause",
    "Advises to NOT run terraform apply until state is verified",
    "Recommends: (1) restore previous state version from Object Storage versioned bucket, (2) run terraform plan to compare state vs. real infrastructure",
    "If plan shows drift: use terraform import to reconcile real resources back into state",
    "Long-term recommendation: migrate to OCI Resource Manager (built-in locking) or Terraform Cloud for native locking",
    "Does NOT suggest terraform destroy as a recovery path"
  ]
}
```

## Scenario 4: Edge — Cold start latency SLA requirement

```json
{
  "skills": ["provisioning-oci-serverless-stack"],
  "query": "Our SLA requires <100ms P99 response time including Function execution. We are seeing 800ms–2s cold starts in production.",
  "expected_behavior": [
    "Identifies cold start as the issue and presents the 'Ask First' decision on Provisioned Concurrency",
    "Recommends enabling provisioned_concurrency with strategy = 'CONSTANT' and configured units",
    "Explains trade-off: provisioned concurrency eliminates cold starts but incurs constant compute cost (billing even when idle)",
    "Asks for expected steady-state concurrent invocations to size the provisioned units",
    "Does NOT suggest reducing Function memory or timeout as a cold start fix",
    "May also suggest keeping the JVM warm via Function configuration and optimized container image layers"
  ]
}
```

## Scenario 5: Misuse — Hardcoded credentials in Terraform provider block

```json
{
  "skills": ["provisioning-oci-serverless-stack"],
  "query": "For our CI/CD pipeline I want to put the OCI user OCID, fingerprint, and private key directly in provider.tf so the pipeline can authenticate without extra configuration.",
  "expected_behavior": [
    "Identifies hardcoded credentials as the most critical 'Never Do' anti-pattern in this skill",
    "Explains that provider.tf is committed to version control — credentials become permanently leaked in git history even if later removed",
    "Points out that CI/CD logs may capture plan output containing credential references",
    "Recommends Resource Principal auth for OCI Resource Manager pipelines or environment variables (TF_VAR_) for external CI/CD",
    "For external CI/CD: use OCI API key stored in CI/CD secrets manager (GitHub Actions secrets, GitLab CI variables) — never in .tf files",
    "Does NOT generate a provider block with user_ocid, fingerprint, or private_key_path pointing to committed files"
  ]
}
```
