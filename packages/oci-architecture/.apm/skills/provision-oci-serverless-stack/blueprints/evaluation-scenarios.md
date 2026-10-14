# Evaluation Scenarios — provision-oci-serverless-stack

## Scenario 1: Canonical — End-to-End Capability from Work-Orders

```json
{
  "skills": ["provision-oci-serverless-stack"],
  "query": "The architect has approved the func-api-facade capability plan. The work-orders are in docs/handoff/func-api-facade/. Execute the full implementation.",
  "expected_behavior": [
    "Routes to @oci-serverless-stack and triggers the P0-P5 workflow",
    "Reads stream-a-java.md, stream-b-terraform-infra.md, stream-c-terraform-integration.md from docs/handoff/func-api-facade/",
    "Delegates Stream A to @oci-functions-java (handler, pom.xml, func.yaml) and Stream B to @oci-terraform (VCN, subnets, IAM) in parallel",
    "Waits for both streams to complete and verifies their report records (report-java.md, report-terraform-infra.md)",
    "Only proceeds to Stream C after both reports show outcome: success",
    "Delegates Stream C to @oci-terraform (Function resource + API Gateway route) using OCIDs from the stream B report",
    "Runs mvn compile, terraform fmt -check, terraform validate, and scripts/preflight.sh as final validation"
  ]
}
```

## Scenario 2: Edge — Stream A Failure Stops Stream C

```json
{
  "skills": ["provision-oci-serverless-stack"],
  "query": "Stream A (Java function) failed to compile during func-rr-rest-proxy provisioning. Stream B (Terraform infra) completed successfully. Should we proceed with Stream C?",
  "expected_behavior": [
    "Routes to @oci-serverless-stack and reads report-java.md for func-rr-rest-proxy",
    "Detects outcome: failed or outcome: partial in report-java.md",
    "STOPS before Stream C — does not delegate the Function resource or API Gateway route to @oci-terraform",
    "Surfaces the open issues / blockers from report-java.md to the user",
    "Waits for the Java issue to be resolved and report-java.md updated to outcome: success before retrying Stream C",
    "Does NOT proceed with a partial provisioning that would leave dangling Terraform resources without a function image"
  ]
}
```

## Scenario 3: Edge — Incremental Addition (Stream D)

```json
{
  "skills": ["provision-oci-serverless-stack"],
  "query": "We already have func-api-facade running in a Functions Application. We need to add func-rr-rest-proxy as a second function to the same Application and API Gateway.",
  "expected_behavior": [
    "Routes to @oci-serverless-stack and identifies this as an incremental addition (Stream D mode)",
    "Verifies the existing function-app module exists in infra/modules/function-app/",
    "Verifies the existing API Gateway deployment supports var.route_backends for multi-backend mode",
    "Delegates Stream D-Java to @oci-functions-java (new function project in services/) and Stream D-Terraform to @oci-terraform (new entry in var.functions and var.route_backends) in parallel",
    "Validates with terraform plan that the output shows ONLY + create operations — no destroy operations on the existing function",
    "Does NOT create a separate Functions Application for the new function"
  ]
}
```

## Scenario 4: Misuse — Missing Work-Orders

```json
{
  "skills": ["provision-oci-serverless-stack"],
  "query": "Provision a new OCI serverless capability for payment processing. No handoff files exist yet.",
  "expected_behavior": [
    "Routes to @oci-serverless-stack but detects that docs/handoff/<capability>/ has no work-order files",
    "Does NOT proceed with implementation without the structured work-orders",
    "Instructs the user to run /design-oci-architecture (@oci-serverless-architect) first to produce the architecture plan and work-order records",
    "Explains that work-orders carry scope, components, constraints, dependencies, and acceptance criteria that @oci-serverless-stack uses to delegate correctly to sub-agents"
  ]
}
```
