# Evaluation Scenarios — engineering-terraform-oci

## Scenario 1: Canonical — New OCI Module with State Backend and Version Pinning

```json
{
  "skills": ["engineering-terraform-oci"],
  "query": "Create the root module skeleton for a new OCI serverless project: Functions + API Gateway + Networking. Include state backend, version pinning, and tagging.",
  "expected_behavior": [
    "Pins Terraform version: required_version = '~> 1.9' in terraform {} block",
    "Pins OCI provider: source = 'oracle/oci', version = '~> 8.15' in required_providers",
    "Configures backend 'oci' {} with partial config (namespace passed via -backend-config, not hardcoded)",
    "Defines common_tags local with Environment, Application, ManagedBy = 'Terraform'",
    "Applies common_tags to every resource via tags = local.common_tags",
    "Sets prevent_destroy = true on the state bucket and critical OCI resources",
    "Enforces .gitignore for *.tfstate, .terraform/, secrets.auto.tfvars, *.tfplan",
    "Does NOT use a local backend (no team state locking)"
  ]
}
```

## Scenario 2: Edge Case — State Backend Initialization Failure

```json
{
  "skills": ["engineering-terraform-oci"],
  "query": "terraform init fails with 'Error: namespace required' when using the OCI backend. How do I fix this?",
  "expected_behavior": [
    "Identifies that the OCI backend does not accept namespace directly in the backend {} block in some Terraform versions — must be passed via partial config",
    "Provides the correct command: terraform init -backend-config='namespace=<tenancy-namespace>'",
    "Alternatively: create a backend-override.hcl file with namespace = '<value>' and pass -backend-config=backend-override.hcl",
    "Confirms the backend bucket, key, and region are also specified (either in block or -backend-config)",
    "Checks that the IAM dynamic group policy allows the runner identity to use object-family in the state bucket compartment",
    "Does NOT hardcode the namespace value inside the backend {} block in the committed .tf file"
  ]
}
```

## Scenario 3: Edge Case — Concurrent Apply State Lock Stuck

```json
{
  "skills": ["engineering-terraform-oci"],
  "query": "A CI/CD pipeline run failed midway. Now terraform plan shows 'Error acquiring the state lock'. No other pipeline is running. How do I safely unlock?",
  "expected_behavior": [
    "First verifies no active CI run is in progress (check CI system, OCI Compute runner status)",
    "Retrieves the LOCK_ID from the error message output",
    "Runs terraform force-unlock <LOCK_ID> — only after confirming no active run",
    "Warns that force-unlock without confirming no active run risks state corruption from concurrent writes",
    "Recommends adding -lock-timeout=60s to terraform plan/apply in CI to reduce stuck-lock likelihood",
    "Does NOT run force-unlock immediately without checking for active runs"
  ]
}
```

## Scenario 4: Edge Case — Module Refactor with moved {} Block

```json
{
  "skills": ["engineering-terraform-oci"],
  "query": "I'm refactoring my Terraform code: renaming oci_functions_application.app to oci_functions_application.serverless_app. How do I avoid destroying and recreating the resource?",
  "expected_behavior": [
    "Uses moved {} block to register the address change without destroy/recreate",
    "Syntax: moved { from = oci_functions_application.app; to = oci_functions_application.serverless_app }",
    "Runs terraform plan to verify the plan shows '1 to move' with no destroy/replace",
    "Notes that moved {} is stable since Terraform v1.1 and production-safe",
    "Cautions to NOT delete the moved {} block until after the apply is confirmed (keeping it is safe; removing too early on a pending apply loses the migration)",
    "Does NOT suggest terraform state mv as the first option (moved {} is the declarative IaC-safe approach)"
  ]
}
```

## Scenario 5: Misuse Case — API Keys in Terraform Configuration

```json
{
  "skills": ["engineering-terraform-oci"],
  "query": "The fastest way to authenticate our CI/CD GitHub Actions runner to OCI is to put the API key fingerprint, private_key, and tenancy_ocid directly in the provider block. Can I do that?",
  "expected_behavior": [
    "Blocks this pattern: CRITICAL Never Do — API keys in .tf files are a credential exposure risk",
    "Explains that .tf files are committed to VCS; keys become part of git history even if later removed",
    "OCI API keys never expire unless manually rotated — leaked key = persistent full tenancy compromise",
    "Provides the correct alternative for GitHub Actions: use environment variables (TF_VAR_* or OCI_* env vars) populated from GitHub Actions secrets",
    "For OCI Compute runners: use InstancePrincipal (auth = 'InstancePrincipal') — no key rotation needed",
    "For pipelines without OCI Compute: use SecurityToken (auth = 'SecurityToken') or workload identity federation",
    "Does NOT suggest putting keys in a .auto.tfvars file as a workaround (same exposure if committed)"
  ]
}
```
