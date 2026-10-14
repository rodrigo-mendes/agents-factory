---
name: testing-terraform-modules
description: Tests Terraform modules with v1.11 native testing framework — static analysis, plan-only unit tests, apply integration tests, parallel execution, and test design patterns.
---

## Version Context

**Technology**: Terraform Native Testing Framework
**Target Version**: Terraform v1.11+ (native `terraform test` command)
**Test File Format**: `.tftest.hcl`
**Support Status**: Active — GA since Terraform v1.6, parallel support in v1.11

**Key Capabilities (v1.11)**:
- Native `terraform test` command (no external tools required)
- Plan-only tests (unit tests — no cloud resources created)
- Apply tests (integration tests — creates and destroys real resources)
- `parallel = true` with `state_key` for independent test isolation
- `expect_failures` for negative testing (validating rejection of invalid inputs)
- Auto-cleanup: resources created during tests are automatically destroyed

**Critical Constraints**:
- Test files MUST use `.tftest.hcl` extension
- Apply tests create real OCI resources — run in CI nightly, not on every PR
- Plan-only tests are free and fast — run on every build

⚠️ **CRITICAL — Agent Warning**:
This skill targets Terraform v1.11+ native testing. Do not use Terratest, kitchen-terraform, or other external testing frameworks unless specifically requested. Plan-only tests (`command = plan`) are free and fast; apply tests (`command = apply`) create real cloud resources and incur cost.

## Quick Navigation

- **[Always Do Patterns](#-always-do)** — Mandatory testing patterns
- **[Ask First Decisions](#️-ask-first)** — Test strategy decisions
- **[Never Do Patterns](#-never-do)** — Testing anti-patterns
- **[Verification Loop](#verification-loop)** — Test execution commands
- **[Quick Reference](#quick-reference)** — Most used patterns at a glance

---

## Blueprints & Guardrails

### ✅ Always Do

#### Testing Pyramid

| Tier | Tool | What It Validates | Speed | CI/CD Stage |
|------|------|-------------------|-------|-------------|
| 1 — Static | `terraform fmt -check`, `terraform validate` | Syntax, formatting, correctness | Seconds | PR check |
| 2 — Unit | `terraform test` (plan-only) | Logic, variable validation, conditionals | Seconds | PR check |
| 3 — Integration | `terraform test` (apply) | Real resource creation + assertions | Minutes | Nightly/staging |

#### Static Analysis — Always Run First

```bash
# Format check (CI/CD — fails on unformatted code)
terraform fmt -check -recursive

# Validate (after init)
terraform init -backend=false
terraform validate
```

**Why it's mandatory**: Static analysis catches syntax errors and formatting issues in seconds — cheapest validation
**Failure if omitted**: Malformed HCL or unformatted code committed to repository

#### Test File Location & Naming

```
project/
├── modules/
│   └── vcn/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── tests/
│   ├── vcn.tftest.hcl           # Tests for VCN module
│   ├── compute.tftest.hcl       # Tests for compute module
│   └── networking.tftest.hcl    # Tests for networking stack
└── environments/
    └── ...
```

- Test files use `.tftest.hcl` extension
- Place in `tests/` directory at project root
- Name matches the module being tested

#### Unit Test — Plan Only (No Real Resources)

```hcl
# tests/vcn.tftest.hcl

variables {
  compartment_id  = "ocid1.compartment.oc1..test"
  display_name    = "test-vcn"
  vcn_cidr_blocks = ["10.0.0.0/16"]
}

# Unit test — plan only, no real resources
run "validates_cidr_format" {
  command = plan

  assert {
    condition     = length(var.vcn_cidr_blocks) > 0
    error_message = "At least one CIDR block must be provided"
  }
}

run "validates_display_name_rejection" {
  command = plan

  variables {
    display_name = ""
  }

  expect_failures = [
    var.display_name
  ]
}
```

**Why it's mandatory**: Plan-only tests validate logic without creating resources — free, fast, safe
**Failure if omitted**: Variable validation errors only caught at apply time, potentially in production

#### Integration Test — Apply (Creates Real Resources)

```hcl
# tests/vcn_integration.tftest.hcl

variables {
  compartment_id  = "ocid1.compartment.oc1..test-compartment"
  display_name    = "integration-test-vcn"
  vcn_cidr_blocks = ["10.0.0.0/16"]
}

run "creates_vcn_successfully" {
  command = apply

  assert {
    condition     = oci_core_vcn.this.state == "AVAILABLE"
    error_message = "VCN should be in AVAILABLE state after creation"
  }

  assert {
    condition     = length(oci_core_vcn.this.cidr_blocks) == 1
    error_message = "VCN should have exactly one CIDR block"
  }
}
```

**Why it's mandatory**: Integration tests validate real resource creation and cloud provider behavior
**Failure if omitted**: Module works in plan but fails on apply due to API constraints or quota

#### Parallel Test Execution (v1.11+)

```hcl
test {
  parallel = true
}

run "test_a" {
  state_key = "a"
  command   = plan

  variables {
    display_name = "test-a"
  }

  assert {
    condition     = length(var.display_name) > 0
    error_message = "display_name must not be empty"
  }
}

run "test_b" {
  state_key = "b"
  command   = plan

  variables {
    display_name = "test-b"
  }

  assert {
    condition     = length(var.display_name) > 0
    error_message = "display_name must not be empty"
  }
}
```

**Why it's mandatory**: Parallel execution reduces test suite time for large module libraries
**Failure if omitted**: Sequential tests waste CI/CD time on independent test cases

---

### ⚠️ Ask First

#### Test Tier Selection
**Decision point**: Which test tier is appropriate for the change?

| Change Type | Recommended Tier | Reason |
|------------|-----------------|--------|
| Variable validation rule | Unit (plan-only) | No resources needed, fast feedback |
| Conditional resource (count/for_each) | Unit (plan-only) | Plan shows resource count |
| New resource type | Integration (apply) | Validates API compatibility |
| Cross-module dependency | Integration (apply) | Validates output wiring |

**Agent behavior**: "Before writing tests, ask: 'Should these tests create real OCI resources (integration) or only validate the plan (unit)?'"

#### Integration Test Environment
**Decision point**: Where should integration tests run?

| Option | Cost | Speed | When to choose |
|--------|------|-------|----------------|
| Dedicated test compartment | Low (clean up after test) | Fast | Isolated testing |
| Dev environment | None (reuse existing) | Fast | Small projects |
| Ephemeral compartment per PR | Medium | Slow | Enterprise CI/CD |

**Agent behavior**: "Before configuring integration tests, ask: 'Do you have a dedicated test compartment for integration tests?'"

---

### 🚫 Never Do

#### Apply Tests on Every PR

```hcl
# 🚫 INCORRECT — apply test runs on every PR, slow + costly
run "creates_resources" {
  command = apply  # Creates real OCI resources!
}
```

**Why it's prohibited**: Apply tests create real cloud resources — cost, speed, and resource limits
**Real impact**: CI/CD pipeline takes minutes instead of seconds; incurs cloud costs per PR

**Correct approach**: Run apply tests nightly or before staging deployment, use plan-only for PRs.

#### Tests Without `error_message`

```hcl
# 🚫 INCORRECT — no explanation of failure
assert {
  condition = length(var.vcn_cidr_blocks) > 0
}

# ✅ CORRECT — meaningful error message
assert {
  condition     = length(var.vcn_cidr_blocks) > 0
  error_message = "At least one CIDR block must be provided"
}
```

**Why it's prohibited**: Without `error_message`, test failures produce cryptic output
**Real impact**: Developers waste time diagnosing test failures without context

---

## Test Patterns by Module Type

### Variable Validation Tests
```hcl
run "rejects_invalid_ocid" {
  command = plan

  variables {
    compartment_id = "not-a-valid-ocid"
  }

  expect_failures = [
    var.compartment_id
  ]
}
```

### Conditional Resource Tests
```hcl
run "creates_igw_when_enabled" {
  command = plan

  variables {
    enable_internet_gateway = true
  }

  assert {
    condition     = length(oci_core_internet_gateway.this) == 1
    error_message = "Internet Gateway should be created when enabled"
  }
}

run "skips_igw_when_disabled" {
  command = plan

  variables {
    enable_internet_gateway = false
  }

  assert {
    condition     = length(oci_core_internet_gateway.this) == 0
    error_message = "Internet Gateway should not be created when disabled"
  }
}
```

### Output Value Tests
```hcl
run "outputs_vcn_id" {
  command = apply

  assert {
    condition     = can(regex("^ocid1\\.vcn\\.", output.vcn_id))
    error_message = "vcn_id output must be a valid VCN OCID"
  }
}
```

---

## Test Design Rules

1. **Every module MUST have at least one plan-only test** validating variable constraints
2. **Use `expect_failures`** to test that invalid inputs are rejected
3. **Use `command = plan`** for unit tests — fast, free, no cloud resources
4. **Use `command = apply`** only for integration tests — run in CI nightly, not on every PR
5. **Use `state_key`** to isolate independent test runs for parallel execution
6. **Test assertions MUST have meaningful `error_message`** — explain what failed and why
7. **Integration tests MUST clean up** — `terraform test` auto-destroys after test completion

---

## Verification Loop

### 1. Static Analysis
```bash
terraform fmt -check -recursive
terraform init -backend=false && terraform validate
```
**Expected output**: No format issues; `Success! The configuration is valid.`
**Exit code**: 0

### 2. Run Unit Tests
```bash
terraform test -filter=tests/vcn.tftest.hcl
```
**Expected output**: `Success! N passed, 0 failed.`
**Exit code**: 0

### 3. Run All Tests
```bash
terraform test
```
**Expected output**: `Success! N passed, 0 failed.`
**Exit code**: 0

### 4. Verbose Test Output
```bash
terraform test -verbose
```
**Expected output**: Detailed per-run output with plan/apply details
**Exit code**: 0

**Troubleshooting**:
- `Error: Test file not found` → Ensure test files are in `tests/` with `.tftest.hcl` extension
- `Error: Provider configuration not present` → Run `terraform init` before `terraform test`
- Apply test timeout → Increase function/resource timeouts in test variables
- Parallel test conflict → Ensure each `run` block has a unique `state_key`

---

## Quick Reference

**Essential commands**:
```bash
# Run all tests
terraform test

# Run specific test file
terraform test -filter=tests/vcn.tftest.hcl

# Run with verbose output
terraform test -verbose

# Static analysis (always first)
terraform fmt -check -recursive
terraform init -backend=false && terraform validate
```

**Test file skeleton**:
```hcl
# tests/<module>.tftest.hcl

variables {
  compartment_id = "ocid1.compartment.oc1..test"
  # ... test variables
}

run "validates_required_input" {
  command = plan
  assert {
    condition     = <expression>
    error_message = "Descriptive error message"
  }
}

run "rejects_invalid_input" {
  command = plan
  variables { invalid_var = "bad-value" }
  expect_failures = [var.invalid_var]
}
```

**External Resources**:
- [Terraform Test Command](https://developer.hashicorp.com/terraform/cli/commands/test)
- [Test Configuration Syntax](https://developer.hashicorp.com/terraform/language/tests)
- [Testing Best Practices](https://developer.hashicorp.com/terraform/language/tests/best-practices)
