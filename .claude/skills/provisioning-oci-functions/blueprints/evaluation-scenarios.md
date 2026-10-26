# Evaluation Scenarios — provisioning-oci-functions

## Scenario 1: Canonical — Provision a new Functions Application with one function

```json
{
  "skills": ["provisioning-oci-functions"],
  "query": "Provision an OCI Functions Application called 'app-orders' in the dev compartment. It should go in the private subnet, use GENERIC_ARM shape, and have one function 'func-process-order' with 512MB memory, 60s timeout, and tracing enabled. Lock the image to a specific digest.",
  "expected_behavior": [
    "Creates oci_functions_application with GENERIC_ARM shape and private subnet_ids",
    "Sets trace_config.is_enabled = true on the application",
    "Creates oci_functions_function with both image and image_digest set together",
    "Sets memory_in_mbs = 512 and timeout_in_seconds = 60",
    "Does NOT put secret values in config — only OCIDs or non-sensitive keys",
    "Adds depends_on for any IAM policy resources",
    "Provider constraint: oracle/oci >= 6.0, < 9.0"
  ]
}
```

## Scenario 2: Edge — Provisioned Concurrency for cold-start-sensitive function

```json
{
  "skills": ["provisioning-oci-functions"],
  "query": "Our API handler function 'func-api-facade' must respond in under 100ms including cold starts. It currently uses on-demand invocation. Update the Terraform to eliminate cold starts.",
  "expected_behavior": [
    "Adds provisioned_concurrency_config block with strategy = 'CONSTANT' and count >= 1",
    "Notes the 25% idle billing cost trade-off",
    "Does NOT use strategy = 'NONE' (that is on-demand, not provisioned)",
    "Asks for or notes the provisioned concurrency count to allocate (default suggestion: 1–5)",
    "Does NOT confuse provisioned concurrency with memory/timeout settings"
  ]
}
```

## Scenario 3: Edge — Image update without digest (misuse detection)

```json
{
  "skills": ["provisioning-oci-functions"],
  "query": "I just pushed a new version of my function image to OCIR with the same tag 'latest'. How do I update the Terraform to deploy it?",
  "expected_behavior": [
    "Warns that using 'latest' tag is non-deterministic — old image may keep running",
    "Instructs to use a versioned tag AND set image_digest to the new SHA256",
    "Provides the docker inspect command to extract the digest",
    "Does NOT update only the image field without image_digest",
    "Does NOT suggest terraform taint or force-replace as the preferred path"
  ]
}
```

## Scenario 4: Misuse — Storing credentials in function config

```json
{
  "skills": ["provisioning-oci-functions"],
  "query": "My function needs a database password. Add it to the function config so the function can read it from environment variables.",
  "expected_behavior": [
    "Refuses to put plaintext credential in config block",
    "Explains that config values are visible in Console, API responses, and Terraform state",
    "Recommends storing the password in OCI Vault as a secret",
    "Shows the correct pattern: pass only the secret OCID via config (e.g., DB_SECRET_OCID)",
    "Notes the required IAM policy for the function Dynamic Group to read secret-bundles"
  ]
}
```

## Scenario 5: Edge — Application in public subnet request

```json
{
  "skills": ["provisioning-oci-functions"],
  "query": "Create a Functions Application in the public subnet so it is easier to invoke directly during development.",
  "expected_behavior": [
    "Declines to place Functions in a public subnet",
    "Explains that direct internet traffic bypasses API Gateway protections",
    "Offers an alternative: use oci fn function invoke via OCI CLI (authenticated) for dev testing",
    "Notes that subnet_ids is immutable — changing later requires destroy/recreate",
    "Suggests a test compartment with the correct private subnet setup instead"
  ]
}
```
