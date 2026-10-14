# Evaluation Scenarios — deploying-oci-functions

## Scenario 1: Canonical — Standard Version Bump Deploy

```json
{
  "skills": ["deploying-oci-functions"],
  "query": "I need to deploy version 0.0.15 of my func-rr-rest-proxy function. Previous version was 0.0.14 and is working.",
  "expected_behavior": [
    "Starts with pre-flight checks before any build command",
    "Runs ./build-push.sh 0.0.15 from the function's service directory",
    "Updates terraform.tfvars to reference the new image tag",
    "Runs terraform plan and confirms exactly 1 resource change (image attribute only)",
    "Runs terraform apply only after plan is verified",
    "Runs smoke test (curl) and interprets HTTP 200 or 400 as success",
    "Does NOT skip pre-flight or terraform plan steps"
  ]
}
```

## Scenario 2: Edge — Pre-Flight Catches Missing CMD

```json
{
  "skills": ["deploying-oci-functions"],
  "query": "I added a new function class and updated the handler. Running the deploy workflow now.",
  "expected_behavior": [
    "Pre-flight script checks for CMD in Dockerfile before build",
    "If CMD is missing: reports FATAL error and stops — does NOT proceed to docker build",
    "Provides the fix: add CMD [\"<package>.<Class>::handler\"] to Dockerfile",
    "After fix, re-runs pre-flight to confirm all checks pass before building",
    "Does NOT suggest skipping pre-flight to save time"
  ]
}
```

## Scenario 3: Edge — Plan Shows More Than 1 Change

```json
{
  "skills": ["deploying-oci-functions"],
  "query": "I ran terraform plan and it shows 3 resources will change, not just 1. Should I still apply?",
  "expected_behavior": [
    "Flags the situation as requiring investigation before applying",
    "Lists common causes: tfvars changed for other resources, provider upgrade, or drift",
    "Instructs to review each planned change before proceeding",
    "States the rule: a clean version bump should produce exactly 1 change (image attribute)",
    "Does NOT auto-approve when unexpected changes are present",
    "Recommends -target flag if only the function resource needs updating"
  ]
}
```

## Scenario 4: Misuse Guard — Tag Reuse

```json
{
  "skills": ["deploying-oci-functions"],
  "query": "The build failed halfway. Can I just rebuild with the same version tag 0.0.15?",
  "expected_behavior": [
    "Explicitly blocks tag reuse — states this is a hard Never Do",
    "Explains the risk: OCIR overwrites the tag, Terraform state still references it, no audit trail",
    "Instructs to increment to 0.0.16 instead",
    "Notes that even in dev, monotonically increasing tags are mandatory",
    "Does NOT suggest that tag reuse is acceptable in development environments"
  ]
}
```

## Scenario 5: Edge — Rollback Required After Smoke Test Failure

```json
{
  "skills": ["deploying-oci-functions"],
  "query": "Post-deploy smoke test returns 502. How do I roll back?",
  "expected_behavior": [
    "Immediately triggers rollback protocol",
    "Reverts terraform.tfvars to the previous image tag (e.g., 0.0.14)",
    "Runs terraform apply to restore previous function version",
    "Verifies rollback with curl returning previous behavior",
    "Notes that the failed image (0.0.15) remains in OCIR for post-mortem investigation",
    "Does NOT suggest force-deleting state or removing the pushed image before debugging"
  ]
}
```
