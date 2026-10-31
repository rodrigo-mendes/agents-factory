---
name: testing-terraform-modules
description: "Tests Terraform modules with the v1.11 native testing framework — static analysis, plan-only unit tests, apply integration tests, parallel execution, and test design patterns. Use when writing or running Terraform native tests (.tftest.hcl) for OCI modules, adding module test coverage, or debugging failing terraform test runs."
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

- **Always Do Patterns** (below) — Mandatory testing patterns
- **Ask First Decisions** (below) — Test strategy decisions
- **Never Do Patterns** (below) — Testing anti-patterns
- **[Integration Patterns](./blueprints/integration-patterns.md)** — Full .tftest.hcl examples (unit, integration, parallel, conditional, output)
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — Canonical, edge, and misuse test cases
- **Verification Loop** (below) — Test execution commands
- **Quick Reference** (below) — Most used patterns at a glance

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

**Why it's mandatory**: Catches syntax errors and formatting issues in seconds — cheapest validation.
**Failure if omitted**: Malformed HCL or unformatted code committed to repository.

#### Test File Location & Naming

- Test files use `.tftest.hcl` extension
- Place in `tests/` directory at project root
- Name matches the module being tested
- See [Integration Patterns](./blueprints/integration-patterns.md) for file structure and full examples.

#### Assertions Must Have `error_message`

```hcl
# ✅ CORRECT — meaningful error message
assert {
  condition     = length(var.vcn_cidr_blocks) > 0
  error_message = "At least one CIDR block must be provided"
}
```

**Why**: Without `error_message`, test failures produce cryptic output.
**If omitted**: Developers waste time diagnosing test failures without context.

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
# 🚫 INCORRECT — apply test on every PR: slow + costly
run "creates_resources" {
  command = apply  # Creates real OCI resources!
}

# ✅ CORRECT — use plan for PR checks; apply only in nightly/staging
run "validates_resource_config" {
  command = plan
}
```

**Why it's prohibited**: Apply tests create real cloud resources — cost, speed, and resource limits.
**Real impact**: CI/CD pipeline takes minutes instead of seconds; incurs cloud costs per PR.

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

**Why it's prohibited**: Without `error_message`, test failures produce cryptic output.
**Real impact**: Developers waste time diagnosing test failures without context.

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

**External Resources**:
- [Terraform Test Command](https://developer.hashicorp.com/terraform/cli/commands/test)
- [Test Configuration Syntax](https://developer.hashicorp.com/terraform/language/tests)
- [Testing Best Practices](https://developer.hashicorp.com/terraform/language/tests/best-practices)
