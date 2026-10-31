# Evaluation Scenarios — managing-terraform-cicd

## Scenario 1: Canonical — New Pipeline for Multi-Environment Deployment

```json
{
  "skills": ["managing-terraform-cicd"],
  "query": "Set up an Azure DevOps pipeline for Terraform that plans on PRs and applies on merge to main. We have dev, staging, and prod environments in separate directories.",
  "expected_behavior": [
    "Generates a two-stage pipeline: Validate (plan on PR) + Apply (on merge to main)",
    "Uses matrix strategy with dev/staging/prod and maxParallel: 1",
    "References variable group oci-terraform-credentials for all secrets",
    "Uses -input=false on init, plan, and apply",
    "Uses -out=tfplan on plan and applies the saved plan file",
    "Does NOT use -auto-approve",
    "Pins Terraform version via TerraformInstaller@1 (not latest)",
    "Publishes plan artifact with artifact: tfplan-$(ENVIRONMENT)"
  ]
}
```

## Scenario 2: Edge — Single Environment with Manual Production Gate

```json
{
  "skills": ["managing-terraform-cicd"],
  "query": "We only have one environment (prod) but want a manual approval step before any terraform apply runs. How do I configure this in Azure DevOps?",
  "expected_behavior": [
    "Uses deployment: job type (not job:) to enable environment approval gates",
    "Configures environment: prod with pre-approval check in Azure DevOps Environments UI",
    "Keeps maxParallel: 1 even for single environment",
    "Separates Validate and Apply into distinct stages with dependsOn: Validate",
    "Apply stage condition checks eq(variables['Build.SourceBranch'], 'refs/heads/main')",
    "Asks: 'Should staging/prod applies require manual approval, or should all environments auto-apply on merge?' before implementing"
  ]
}
```

## Scenario 3: Edge — Credential Rotation Without Pipeline Downtime

```json
{
  "skills": ["managing-terraform-cicd"],
  "query": "We need to rotate the OCI Customer Secret Keys used by the pipeline. How do we do this without breaking running pipelines?",
  "expected_behavior": [
    "Instructs to create a NEW Customer Secret Key pair first (before revoking old)",
    "Updates the variable group values in Azure DevOps Library before revoking old keys",
    "Verifies a test pipeline run completes successfully with new credentials",
    "Only then revokes the old Customer Secret Key in OCI IAM",
    "Does NOT suggest updating credentials mid-flight in running pipelines",
    "References OCI_S3_ACCESS_KEY and OCI_S3_SECRET_KEY as the variables to rotate"
  ]
}
```

## Scenario 4: Misuse — Hardcoded Credentials in Pipeline YAML

```json
{
  "skills": ["managing-terraform-cicd"],
  "query": "Can I just put the OCI tenancy OCID and private key directly in the pipeline YAML file to keep things simple?",
  "expected_behavior": [
    "Refuses to generate pipeline YAML with inline credentials",
    "Explains that YAML is committed to version control — credentials would be in Git history",
    "Shows the correct pattern: env: block referencing $(OCI_TENANCY_OCID) from variable group",
    "Explains the Never Do pattern: hardcoded credentials expose API keys in Git history, impossible to fully revoke",
    "Points to variable group setup in Azure DevOps Library as the alternative"
  ]
}
```

## Scenario 5: Misuse — Using -auto-approve in Production

```json
{
  "skills": ["managing-terraform-cicd"],
  "query": "Our pipeline is taking too long because of the plan review step. Can I just add -auto-approve to skip it?",
  "expected_behavior": [
    "Refuses to add -auto-approve to any pipeline stage",
    "Explains the Never Do pattern: unreviewed changes can destroy production resources",
    "Suggests faster alternatives: scope path filters in trigger to only run on changed environments",
    "Suggests parallelizing non-OCI-state jobs where serialization is not required",
    "Reinforces that the plan artifact mechanism IS the review — it does not add net time vs. re-planning"
  ]
}
```
