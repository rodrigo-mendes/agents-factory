# ==============================================================================
# Tests: General Variable Validations
# ==============================================================================
# Validates that general/cross-cutting variables reject invalid inputs.
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
# environment
# ------------------------------------------------------------------------------

run "rejects_invalid_environment" {
  command = plan

  variables {
    environment = "production"
  }

  expect_failures = [
    var.environment,
  ]
}

run "rejects_uppercase_environment" {
  command = plan

  variables {
    environment = "DEV"
  }

  expect_failures = [
    var.environment,
  ]
}

run "rejects_empty_environment" {
  command = plan

  variables {
    environment = ""
  }

  expect_failures = [
    var.environment,
  ]
}

# ------------------------------------------------------------------------------
# vault_key_protection_mode
# ------------------------------------------------------------------------------

run "rejects_invalid_vault_key_protection_mode" {
  command = plan

  variables {
    vault_key_protection_mode = "INVALID"
  }

  expect_failures = [
    var.vault_key_protection_mode,
  ]
}

run "rejects_lowercase_vault_key_protection_mode" {
  command = plan

  variables {
    vault_key_protection_mode = "software"
  }

  expect_failures = [
    var.vault_key_protection_mode,
  ]
}
