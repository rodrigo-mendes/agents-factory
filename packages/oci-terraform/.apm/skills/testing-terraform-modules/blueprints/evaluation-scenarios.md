# Evaluation Scenarios — testing-terraform-modules

## Scenario 1: Canonical — Write tests for a new VCN module

```json
{
  "skills": ["testing-terraform-modules"],
  "query": "I've created a new Terraform module for OCI VCN provisioning. Write tests covering variable validation, the optional internet gateway toggle, and successful OCID output format.",
  "expected_behavior": [
    "Creates a .tftest.hcl file in tests/ directory",
    "Uses command = plan for variable validation and conditional resource tests",
    "Uses command = apply only for the OCID output format test",
    "Each assert block has a meaningful error_message",
    "Uses expect_failures for invalid input tests",
    "Does NOT run apply tests for every scenario — only where real state is needed"
  ]
}
```

## Scenario 2: Edge — Selecting the right test tier (unit vs integration)

```json
{
  "skills": ["testing-terraform-modules"],
  "query": "I need to test that my function module correctly wires the subnet ID from the network module output into the function application resource. Should I write a plan test or an apply test?",
  "expected_behavior": [
    "Identifies this as a cross-module dependency — recommends integration (apply) test",
    "Explains that plan tests cannot verify real output wiring across module boundaries",
    "Warns that apply tests create real OCI resources — run nightly, not on every PR",
    "Asks whether there is a dedicated test compartment before proceeding",
    "Does NOT suggest plan-only for cross-module output validation"
  ]
}
```

## Scenario 3: Edge — Parallel test isolation with state_key

```json
{
  "skills": ["testing-terraform-modules"],
  "query": "I have 10 independent unit tests for my networking module and they're running sequentially, making my PR checks slow. How do I speed this up?",
  "expected_behavior": [
    "Adds `test { parallel = true }` block at the top of the test file",
    "Adds unique state_key to each run block",
    "Confirms all 10 tests use command = plan (safe to parallelize)",
    "Notes that parallel apply tests require unique state_key to avoid state conflicts",
    "Does NOT enable parallel without state_key on run blocks"
  ]
}
```

## Scenario 4: Misuse — Apply tests on every PR

```json
{
  "skills": ["testing-terraform-modules"],
  "query": "Add integration tests to my CI pipeline to run on every pull request.",
  "expected_behavior": [
    "Warns that apply tests create real OCI resources — unsuitable for every PR",
    "Explains the cost and speed impact (minutes vs seconds, real cloud charges)",
    "Recommends plan-only tests for PR checks",
    "Recommends apply tests in a nightly CI job or pre-staging gate",
    "Does NOT add command = apply tests to the PR pipeline without this warning"
  ]
}
```

## Scenario 5: Edge — Test for negative input (expect_failures)

```json
{
  "skills": ["testing-terraform-modules"],
  "query": "My compartment_id variable has a validation rule that rejects non-OCID strings. Write a test that verifies invalid input is rejected.",
  "expected_behavior": [
    "Uses expect_failures = [var.compartment_id]",
    "Sets compartment_id to a clearly invalid value (e.g., 'not-a-valid-ocid')",
    "Uses command = plan (no real resources needed to test validation rejection)",
    "Does NOT use an assert block for negative tests — uses expect_failures",
    "Does NOT wrap the test in a try/catch workaround"
  ]
}
```
