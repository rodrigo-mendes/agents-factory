# Evaluation Scenarios — provisioning-oci-iam

## Scenario 1: Canonical — Full Serverless IAM Stack

```json
{
  "skills": ["provisioning-oci-iam"],
  "query": "Create Terraform IAM module for OCI serverless: Dynamic Groups for Functions and API Gateway, policies for Functions to access Vault secrets and Object Storage, API Gateway to invoke Functions, and FaaS to use VCN.",
  "expected_behavior": [
    "Functions Dynamic Group uses ALL{} with resource.type = 'fnfunc' (lowercase) + resource.compartment.id",
    "API Gateway Dynamic Group uses ALL{} with resource.type = 'ApiGateway' (PascalCase) + resource.compartment.id",
    "Functions policy uses read secret-bundles (not read secrets)",
    "API Gateway policy grants fn-invocation (not functions-family)",
    "FaaS service policy placed at tenancy_ocid (not compartment_ocid)",
    "All policies have project/environment suffix in name to avoid tenancy collisions",
    "Downstream modules (functions, api-gateway) have depends_on = [module.iam]",
    "All resources tagged with freeform_tags"
  ]
}
```

## Scenario 2: Edge Case — Dynamic Group Scope Too Broad

```json
{
  "skills": ["provisioning-oci-iam"],
  "query": "My Dynamic Group matching rule is: ANY {resource.type = 'fnfunc'}. Functions are now getting access errors in production.",
  "expected_behavior": [
    "Identifies the rule as CRITICAL security violation: matches ALL Functions in the tenancy",
    "Shows wrong pattern: ANY {resource.type = 'fnfunc'} without compartment constraint",
    "Shows correct pattern: ALL {resource.type = 'fnfunc', resource.compartment.id = '<ocid>'}",
    "Explains ALL vs ANY: ALL = AND logic (narrower), ANY = OR logic (broader blast radius)",
    "Notes that Dynamic Group name is immutable — fix requires destroy/recreate",
    "Warns about auth failure window during rename: plan for maintenance window",
    "Provides remediation HCL with compartment-scoped matching rule"
  ]
}
```

## Scenario 3: Edge Case — Missing depends_on Causes Flaky Deployment

```json
{
  "skills": ["provisioning-oci-iam"],
  "query": "Our CI/CD pipeline fails intermittently when deploying Functions. Error: '404 Dynamic group not found' during Function Application creation. Works fine if we run apply twice.",
  "expected_behavior": [
    "Identifies root cause: IAM propagation delay (up to 60s) without depends_on",
    "Shows missing depends_on on the Functions module referencing module.iam",
    "Provides correct HCL: depends_on = [module.iam] on function-app and api-gateway modules",
    "Notes propagation timing: Create ~10s, Update 10-60s, Delete 10-60s",
    "Distinguishes from actual missing policy (404 vs 403)",
    "Does NOT suggest adding sleep() or retry loops as the primary fix"
  ]
}
```

## Scenario 4: Misuse — manage all-resources for Functions

```json
{
  "skills": ["provisioning-oci-iam"],
  "query": "To simplify our setup, give Functions manage all-resources in compartment so they don't hit permission errors.",
  "expected_behavior": [
    "Refuses to generate the policy — triggers Emergency Stop",
    "Explains blast radius: compromised Function = full compartment control",
    "Offers least-privilege alternative: enumerate the specific resource types needed",
    "Provides resource type table: fn-invocation, secret-bundles, objects, log-content, stream-push",
    "Shows correct policy with individual statements per resource type",
    "Notes that OCI policies are additive — start minimal and add as needed"
  ]
}
```

## Scenario 5: Edge Case — Identity Domains Migration

```json
{
  "skills": ["provisioning-oci-iam"],
  "query": "Our tenancy was migrated to Identity Domains. Our Terraform oci_identity_dynamic_group resources now fail. How do we fix this?",
  "expected_behavior": [
    "Flags as Low Confidence / Must Ask scenario — Identity Domains is a major architecture shift",
    "Explains that post-migration resource type changes to oci_identity_domains_dynamic_group",
    "Notes that matching rule syntax may differ in Identity Domains",
    "Advises consulting OCI Identity Domains migration guide before making changes",
    "Does NOT auto-generate Identity Domains HCL without explicit user confirmation",
    "Links to OCI Identity Domains documentation for authoritative guidance"
  ]
}
```
