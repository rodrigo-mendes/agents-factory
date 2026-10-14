---
description: Add native Terraform v1.11 test cases (.tftest.hcl) to validate infrastructure configurations and module standards
argument-hint: Target module path, variables to validate, validation scenarios
context: fork
agent: oci-terraform
background: false
disable-model-invocation: true
---

Execute this task now for the OCI serverless project. Read the referenced skill below for the canonical patterns, gather the "Required information", then carry the task through to completion. If the target below is empty, ask for the required information before proceeding.

**Request / target (from the user):** $ARGUMENTS

# Add Terraform Tests

**Skill**: `testing-terraform-modules`

## What this does

Generates declarative unit and integration test blocks in standard Terraform testing files (`.tftest.hcl`) to validate OCI Terraform configurations, variable checks, and output accuracy.

## Required information

1. **Target Module**: Which Terraform module or root environment folder do you want to write tests for?
2. **Test Scope**: Unit tests (dry-run plan only using mock and validation assertions) or integration tests (applying to actual environment)?
3. **Variables**: What custom inputs or variable configurations need to be fed into the test blocks?
4. **Validation Assertions**: What resources, variable values, or output structures must be asserted during the tests (e.g., checking tag mappings, VCN ranges, resource principal policy rules)?
5. **Environments**: Are there specific deployment scenarios (dev vs prod) to evaluate separately?

## What will be generated

- A `.tftest.hcl` test file in the designated directory
- Mock data providers if simulating OCI resource provisioning behavior
- Plan-only test steps (`run` blocks with `command = plan`) validating variable constraints and standard compliant structures
- Custom assertion statements verifying resource properties (ex: `assert { condition = ... }`)
- Integration test steps if actual OCI deployment validations are desired
- Validation instructions showing how to invoke tests locally using `terraform test`
