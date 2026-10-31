# Evaluation Scenarios — architecting-oci-serverless

## Scenario 1: Canonical — Design subnet placement for a new serverless stack

```json
{
  "skills": ["architecting-oci-serverless"],
  "query": "I'm designing a new OCI serverless stack for a retail API. Where should the API Gateway and the Functions Application go in the VCN?",
  "expected_behavior": [
    "Places API Gateway in the public subnet (Internet Gateway, NSG: 443 inbound from 0.0.0.0/0)",
    "Places Functions Application in the private subnet (no public IP, NSG: inbound only from API GW subnet CIDR)",
    "Adds Service Gateway to the private subnet route table for OCIR and OCI API access",
    "Does NOT place Functions in the public subnet",
    "Notes that subnet_ids on the Functions Application is immutable — plan carefully before apply",
    "References provisioning-oci-networking and provisioning-oci-functions for Terraform implementation"
  ]
}
```

## Scenario 2: Edge — Cold-start mitigation decision

```json
{
  "skills": ["architecting-oci-serverless"],
  "query": "Our Java function currently has 8–12 second cold starts. The SLA requires P99 < 200ms. How should we address this?",
  "expected_behavior": [
    "Identifies Provisioned Concurrency (CONSTANT strategy) as the primary solution for <200ms SLA",
    "Notes the 25% idle billing cost trade-off",
    "Asks for expected concurrency level to size the provisioned count",
    "Mentions GraalVM native image as an alternative to reduce cold start without permanent idle cost",
    "Does NOT recommend simply increasing memory as a cold-start fix (memory affects CPU, not JVM init time)",
    "Does NOT recommend on-demand invocation for a sub-200ms SLA"
  ]
}
```

## Scenario 3: Misuse — Credential scan failure

```json
{
  "skills": ["architecting-oci-serverless"],
  "query": "I need to connect my function to a third-party API. Store the API key in the function config so the function can read it via System.getenv().",
  "expected_behavior": [
    "Refuses to place plaintext API key in function config",
    "Explains that config values are visible in the OCI Console, API responses, and Terraform state",
    "Directs to OCI Vault: store the API key as a Vault secret, pass only the secret OCID via config",
    "Shows the required IAM policy: Allow dynamic-group <fn-dg> to read secret-bundles in compartment",
    "References designing-oci-vault-security for the full Vault architecture"
  ]
}
```

## Scenario 4: Edge — IAM least-privilege scope

```json
{
  "skills": ["architecting-oci-serverless"],
  "query": "To simplify setup, grant the functions Dynamic Group 'manage all-resources in tenancy' so it can access everything it needs.",
  "expected_behavior": [
    "Refuses to grant wildcard manage all-resources policy",
    "Explains that OCI IAM policies are additive-only — wildcards cannot be scoped down later",
    "Enumerates the minimal required policies for the specific use case (read secret-bundles, manage objects, use log-content)",
    "Emphasizes compartment-scoped policies instead of tenancy-scoped",
    "Does NOT offer wildcard as a 'temporary shortcut'"
  ]
}
```

## Scenario 5: Edge — Sync vs Detached invocation pattern selection

```json
{
  "skills": ["architecting-oci-serverless"],
  "query": "We have a report generation function that takes 5–8 minutes. The client calls it via API Gateway and waits for the result.",
  "expected_behavior": [
    "Identifies that 5–8 minutes exceeds the synchronous invocation limit of 300 seconds",
    "Recommends Detached (async) invocation mode — max 720 seconds",
    "Suggests an async response pattern: client polls a status endpoint or receives a webhook/notification",
    "Notes that API Gateway timeout is also a constraint (default 30s) — cannot wait synchronously anyway",
    "References OCI Streaming or Notifications as success/failure destinations for Detached mode"
  ]
}
```
