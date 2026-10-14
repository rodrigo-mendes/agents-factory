# ==============================================================================
# Tests: Functions Variable Validations
# ==============================================================================
# Validates that Functions-related variables reject invalid inputs.
# All tests are plan-only (no cloud resources created).
# ==============================================================================

mock_provider "oci" {
  override_data {
    target = module.network.data.oci_core_services.all_services
    values = {
      services = [{
        id         = "ocid1.service.oc1..mock"
        name       = "All GRU Services In Oracle Services Network"
        cidr_block = "all-gru-services-in-oracle-services-network"
      }]
    }
  }
  override_data {
    target = module.vault.data.oci_objectstorage_namespace.this
    values = {
      namespace = "testnamespace"
    }
  }
}

variables {
  tenancy_ocid      = "ocid1.tenancy.oc1..test"
  compartment_ocid  = "ocid1.compartment.oc1..test"
  compartment_name  = "test-compartment"
  region            = "sa-saopaulo-1"
  api_handler_image = "gru.ocir.io/namespace/repo/api-handler:latest"
  api_facade_image  = "gru.ocir.io/namespace/repo/api-facade:latest"
  rest_proxy_image  = "gru.ocir.io/namespace/repo/rest-proxy:latest"
}

# ------------------------------------------------------------------------------
# function_shape
# ------------------------------------------------------------------------------

run "rejects_invalid_function_shape" {
  command = plan

  variables {
    function_shape = "INVALID_SHAPE"
  }

  expect_failures = [
    var.function_shape,
  ]
}

run "rejects_lowercase_function_shape" {
  command = plan

  variables {
    function_shape = "generic_x86"
  }

  expect_failures = [
    var.function_shape,
  ]
}

# ------------------------------------------------------------------------------
# apm_domain_id (function-app module)
# ------------------------------------------------------------------------------

run "function_app_accepts_empty_apm_domain_id" {
  command = plan
  # apm_domain_id no module function-app defaults to "" — must not fail validation
}

# Note: apm_domain_id is a module-level argument (module.apm.apm_domain_id → module.app_*.apm_domain_id),
# not a root variable. Its validation is covered in infra/modules/apm/variables_apm.tftest.hcl.
