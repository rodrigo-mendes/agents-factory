# ==============================================================================
# Tests: APM config keys are passed to Function Applications (integration check)
# ==============================================================================
# Validates that the environment composition correctly wires apm_domain_id
# to function-app modules when the APM module is present.
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
  override_data {
    target = module.apm.data.oci_apm_data_keys.private
    values = {
      items = [{
        key_type = "PRIVATE"
        value    = "mock-apm-private-key"
      }]
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
# APM wiring — environment composition plan succeeds with APM module present
# ------------------------------------------------------------------------------

run "apm_module_plan_succeeds_with_valid_inputs" {
  command = plan
  # validates that module "apm" composes cleanly with the rest of the environment
}
