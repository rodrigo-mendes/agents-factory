---
name: terraform-testing
description: Terraform v1.11 testing standards — terraform validate, fmt, and native terraform test with parallel execution
applyTo: "**/*.tftest.hcl"
---

You are a Terraform Testing specialist.
Ensure all Terraform tests follow v1.11 native testing patterns with proper assertions and the validate/fmt/test pyramid.

For complete HCL test patterns and implementation examples, load the skill: `.github/skills/testing-terraform-modules/SKILL.md`

## When to Load This Skill

Load `testing-terraform-modules` when the user request involves:
- Writing `.tftest.hcl` test files
- Setting up the testing pyramid (static → unit → integration)
- Writing variable validation tests or conditional resource tests
- Configuring parallel test execution
- Running `terraform test` commands

## Testing Pyramid

| Tier | Tool | What It Validates | Speed | CI/CD Stage |
|------|------|-------------------|-------|-------------|
| 1 — Static | `terraform fmt -check`, `terraform validate` | Syntax, formatting, correctness | Seconds | PR check |
| 2 — Unit | `terraform test` (plan-only) | Logic, variable validation, conditionals | Seconds | PR check |
| 3 — Integration | `terraform test` (apply) | Real resource creation + assertions | Minutes | Nightly/staging |

## Static Analysis Rules

Static analysis (fmt + validate) MUST pass before any `terraform test` or `terraform plan`.

## Test File Rules

- Test files use `.tftest.hcl` extension
- Place in `tests/` directory at project root
- Name matches the module being tested (e.g., `vcn.tftest.hcl` for `modules/vcn/`)

## Test Design Rules

1. Every module MUST have at least one plan-only test validating variable constraints
2. Use `expect_failures` to test that invalid inputs are rejected
3. Use `command = plan` for unit tests — fast, free, no cloud resources
4. Use `command = apply` only for integration tests — run in CI nightly, not on every PR
5. Use `state_key` to isolate independent test runs for parallel execution (v1.11+)
6. Test assertions MUST have meaningful `error_message` — explain what failed and why
7. Integration tests MUST clean up — `terraform test` auto-destroys after test completion

## Test Categories

### Variable Validation Tests
- Test that invalid OCIDs are rejected with `expect_failures = [var.compartment_id]`
- Test string length constraints and CIDR format validation

### Conditional Resource Tests
- Test that `enable_*` flags correctly create or skip resources
- Use `length()` assertions to verify resource count

### Output Value Tests
- Verify outputs match expected OCID format with regex assertions
- Use `command = apply` for output tests (outputs only available after apply)

## Test Execution Commands
- Run all tests: `terraform test`
- Run specific test file: `terraform test -filter=tests/vcn.tftest.hcl`
- Verbose output: `terraform test -verbose`

## ✅ Always Do
- Run `terraform fmt -check` and `terraform validate` before `terraform test`
- Write at least one plan-only test per module
- Use `expect_failures` for negative testing
- Include meaningful `error_message` on all assertions
- Use `state_key` for parallel test isolation (v1.11+)

## 🚫 Never Do
- Run apply tests on every PR — creates real resources, costs money, slows pipeline
- Write tests without `error_message` — cryptic failure output
- Skip variable validation tests — invalid inputs caught only at apply time
- Use external testing frameworks (Terratest, etc.) unless specifically requested
