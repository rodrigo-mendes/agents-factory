# ==============================================================================
# Tests: API Gateway Variable Validations
# ==============================================================================
# Validates that API Gateway-related variables reject invalid inputs.
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
# api_gateway_endpoint_type
# ------------------------------------------------------------------------------

run "rejects_invalid_endpoint_type" {
  command = plan

  variables {
    api_gateway_endpoint_type = "INTERNAL"
  }

  expect_failures = [
    var.api_gateway_endpoint_type,
  ]
}

run "rejects_lowercase_endpoint_type" {
  command = plan

  variables {
    api_gateway_endpoint_type = "public"
  }

  expect_failures = [
    var.api_gateway_endpoint_type,
  ]
}

# ------------------------------------------------------------------------------
# rate_limit_requests_per_second
# ------------------------------------------------------------------------------

run "rejects_rate_limit_below_minimum" {
  command = plan

  variables {
    rate_limit_requests_per_second = -1
  }

  expect_failures = [
    var.rate_limit_requests_per_second,
  ]
}

run "rejects_rate_limit_above_maximum" {
  command = plan

  variables {
    rate_limit_requests_per_second = 10001
  }

  expect_failures = [
    var.rate_limit_requests_per_second,
  ]
}
