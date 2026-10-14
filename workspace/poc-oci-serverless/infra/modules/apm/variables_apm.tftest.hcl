# ==============================================================================
# Tests: APM Module Variable Validations
# ==============================================================================
# Validates that APM module variables reject invalid inputs.
# Tests run inside the module itself (not the environment composition).
# All tests are plan-only (no cloud resources created).
# ==============================================================================

mock_provider "oci" {}

variables {
  compartment_ocid = "ocid1.compartment.oc1..test"
  project_name     = "serverless-poc"
  environment      = "dev"
  tags             = {}
}

# ------------------------------------------------------------------------------
# project_name
# ------------------------------------------------------------------------------

run "apm_rejects_empty_project_name" {
  command = plan

  variables {
    project_name = ""
  }

  expect_failures = [
    var.project_name,
  ]
}

# ------------------------------------------------------------------------------
# environment
# ------------------------------------------------------------------------------

run "apm_rejects_invalid_environment" {
  command = plan

  variables {
    environment = "production"
  }

  expect_failures = [
    var.environment,
  ]
}

run "apm_rejects_uppercase_environment" {
  command = plan

  variables {
    environment = "DEV"
  }

  expect_failures = [
    var.environment,
  ]
}

# ------------------------------------------------------------------------------
# compartment_ocid
# ------------------------------------------------------------------------------

run "apm_rejects_invalid_compartment_ocid" {
  command = plan

  variables {
    compartment_ocid = "invalid-ocid-format"
  }

  expect_failures = [
    var.compartment_ocid,
  ]
}

run "apm_accepts_valid_compartment_ocid" {
  command = plan
  # baseline variables are all valid — plan should succeed without failures
}
