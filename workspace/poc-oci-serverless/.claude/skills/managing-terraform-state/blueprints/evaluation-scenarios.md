# Evaluation Scenarios — managing-terraform-state

## Scenario 1: Canonical — Migrate Local State to OCI Object Storage Backend

```json
{
  "skills": ["managing-terraform-state"],
  "query": "We have been using local state for our dev environment. Now we need a team member to also run Terraform and the CI/CD pipeline needs shared state. How do I migrate to a remote backend on OCI Object Storage?",
  "expected_behavior": [
    "Generates a complete backend.tf with all required skip_* flags for OCI S3 compatibility",
    "Provides the credential export commands for AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY",
    "Instructs to run terraform init with -migrate-state flag to copy existing local state",
    "Warns that OCI Object Storage has no native state locking — serialize applies with maxParallel: 1",
    "Asks: 'Is this a solo workflow or does a team need shared state access? Does CI/CD need to apply changes?' before starting"
  ]
}
```

## Scenario 2: Canonical — Import Existing OCI Resource Without Downtime

```json
{
  "skills": ["managing-terraform-state"],
  "query": "We have a VCN in OCI that was created manually. How do I bring it under Terraform management without destroying and recreating it?",
  "expected_behavior": [
    "Uses declarative import {} block (not CLI terraform import command)",
    "Shows import block with to = oci_core_vcn.existing and id = <OCID>",
    "Instructs to run terraform plan -generate-config-out=generated.tf to scaffold the resource config",
    "Explains to review generated.tf before applying",
    "Does NOT suggest terraform import (CLI) as primary approach — notes it leaves no audit trail"
  ]
}
```

## Scenario 3: Edge — Rename a Resource Without Destroy/Recreate

```json
{
  "skills": ["managing-terraform-state"],
  "query": "I renamed oci_core_vcn.main_vcn to oci_core_vcn.this in my code. Now terraform plan shows it will destroy and recreate the VCN. How do I fix this?",
  "expected_behavior": [
    "Generates a moved {} block: from = oci_core_vcn.main_vcn, to = oci_core_vcn.this",
    "Explains that moved {} prevents destroy/recreate and is tracked in version control",
    "Instructs to run terraform plan after adding moved block — expected output: 0 changes",
    "Does NOT suggest terraform state mv as primary solution (CLI only, no audit trail)",
    "Notes the moved block can be removed after the change is applied and all team members have run plan"
  ]
}
```

## Scenario 4: Edge — State Drift Detection After Manual OCI Console Change

```json
{
  "skills": ["managing-terraform-state"],
  "query": "Someone updated the VCN display name in the OCI Console directly, not through Terraform. How do I detect this drift and decide what to do?",
  "expected_behavior": [
    "Instructs to run terraform plan -refresh-only to detect drift without applying changes",
    "Explains exit code 2 means drift was detected (not an error)",
    "Presents two options: apply the -refresh-only plan to accept the manual change, OR apply a normal plan to revert to Terraform-defined state",
    "Warns NOT to run terraform apply without reviewing the -refresh-only output first",
    "Asks: 'Should Terraform revert the manual change, or should the state be updated to match the current OCI state?'"
  ]
}
```

## Scenario 5: Misuse — Using `terraform_remote_state` for Cross-Stack Dependencies

```json
{
  "skills": ["managing-terraform-state"],
  "query": "My compute stack needs the VCN OCID from the networking stack. Can I use terraform_remote_state to read it?",
  "expected_behavior": [
    "Refuses to generate terraform_remote_state data source configuration",
    "Shows the Never Do pattern with side-by-side wrong/correct code",
    "Explains that terraform_remote_state exposes ALL outputs creating tight coupling between stacks",
    "Provides the correct pattern: variable vcn_id injected via tfvars or TF_VAR_vcn_id",
    "Provides the correct data source: data oci_core_vcn existing with vcn_id = var.vcn_id",
    "Explains real impact: output changes in one stack can silently break dependent stacks"
  ]
}
```

## Scenario 6: Misuse — Force-Unlock Without Investigation

```json
{
  "skills": ["managing-terraform-state"],
  "query": "My pipeline is stuck with a state lock error. Can I just run terraform force-unlock to clear it?",
  "expected_behavior": [
    "Does NOT immediately provide the force-unlock command",
    "Explains the Never Do pattern: another process may be actively modifying state",
    "Instructs to first identify the lock holder from the error message (includes lock ID and timestamp)",
    "Check CI/CD pipeline for any running Terraform jobs before unlocking",
    "Only provide force-unlock command once user confirms no active process holds the lock",
    "Warns: concurrent state modification from premature force-unlock causes corruption — resources orphaned or duplicated"
  ]
}
```
