# ==============================================================================
# Tests: Networking Variable Validations
# ==============================================================================
# Validates that networking-related variables reject invalid inputs.
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
# vcn_cidr_block
# ------------------------------------------------------------------------------

run "rejects_invalid_vcn_cidr" {
  command = plan

  variables {
    vcn_cidr_block = "not-a-cidr"
  }

  expect_failures = [
    var.vcn_cidr_block,
  ]
}

run "rejects_empty_vcn_cidr" {
  command = plan

  variables {
    vcn_cidr_block = ""
  }

  expect_failures = [
    var.vcn_cidr_block,
  ]
}

# ------------------------------------------------------------------------------
# subnet_public_cidr
# ------------------------------------------------------------------------------

run "rejects_invalid_subnet_public_cidr" {
  command = plan

  variables {
    subnet_public_cidr = "999.999.999.999/99"
  }

  expect_failures = [
    var.subnet_public_cidr,
  ]
}

run "rejects_empty_subnet_public_cidr" {
  command = plan

  variables {
    subnet_public_cidr = ""
  }

  expect_failures = [
    var.subnet_public_cidr,
  ]
}

# ------------------------------------------------------------------------------
# subnet_private_cidr
# ------------------------------------------------------------------------------

run "rejects_invalid_subnet_private_cidr" {
  command = plan

  variables {
    subnet_private_cidr = "abc.def.ghi/jkl"
  }

  expect_failures = [
    var.subnet_private_cidr,
  ]
}

run "rejects_empty_subnet_private_cidr" {
  command = plan

  variables {
    subnet_private_cidr = ""
  }

  expect_failures = [
    var.subnet_private_cidr,
  ]
}
