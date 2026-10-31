# Integration Patterns — testing-terraform-modules

## Test File Structure

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

---

## Unit Test — Plan Only (No Real Resources)

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

**Why**: Plan-only tests validate logic without creating resources — free, fast, safe.
**If omitted**: Variable validation errors only caught at apply time, potentially in production.

---

## Integration Test — Apply (Creates Real Resources)

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

**Why**: Integration tests validate real resource creation and cloud provider behavior.
**If omitted**: Module works in plan but fails on apply due to API constraints or quota.

---

## Parallel Test Execution (v1.11+)

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

**Why**: Parallel execution reduces test suite time for large module libraries.
**If omitted**: Sequential tests waste CI/CD time on independent test cases.

---

## Variable Validation Tests

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

---

## Conditional Resource Tests

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

---

## Output Value Tests

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

## Test File Skeleton

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
