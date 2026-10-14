# ==============================================================================
# Tests: Required Variable Validations
# ==============================================================================
# Validates that required variables reject invalid inputs.
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
# tenancy_ocid
# ------------------------------------------------------------------------------

run "rejects_invalid_tenancy_ocid" {
  command = plan

  variables {
    tenancy_ocid = "invalid-ocid"
  }

  expect_failures = [
    var.tenancy_ocid,
  ]
}

run "rejects_empty_tenancy_ocid" {
  command = plan

  variables {
    tenancy_ocid = ""
  }

  expect_failures = [
    var.tenancy_ocid,
  ]
}

run "rejects_compartment_as_tenancy_ocid" {
  command = plan

  variables {
    tenancy_ocid = "ocid1.compartment.oc1..wrongtype"
  }

  expect_failures = [
    var.tenancy_ocid,
  ]
}

# ------------------------------------------------------------------------------
# compartment_ocid
# ------------------------------------------------------------------------------

run "rejects_invalid_compartment_ocid" {
  command = plan

  variables {
    compartment_ocid = "not-a-valid-ocid"
  }

  expect_failures = [
    var.compartment_ocid,
  ]
}

run "rejects_empty_compartment_ocid" {
  command = plan

  variables {
    compartment_ocid = ""
  }

  expect_failures = [
    var.compartment_ocid,
  ]
}

run "rejects_tenancy_as_compartment_ocid" {
  command = plan

  variables {
    compartment_ocid = "ocid1.tenancy.oc1..wrongtype"
  }

  expect_failures = [
    var.compartment_ocid,
  ]
}

# ------------------------------------------------------------------------------
# api_handler_image
# ------------------------------------------------------------------------------

run "rejects_dockerhub_api_handler_image" {
  command = plan

  variables {
    api_handler_image = "docker.io/library/nginx:latest"
  }

  expect_failures = [
    var.api_handler_image,
  ]
}

run "rejects_non_ocir_api_handler_image" {
  command = plan

  variables {
    api_handler_image = "my-registry.com/namespace/repo:tag"
  }

  expect_failures = [
    var.api_handler_image,
  ]
}

run "rejects_empty_api_handler_image" {
  command = plan

  variables {
    api_handler_image = ""
  }

  expect_failures = [
    var.api_handler_image,
  ]
}

# ------------------------------------------------------------------------------
# api_facade_image
# ------------------------------------------------------------------------------

run "rejects_dockerhub_api_facade_image" {
  command = plan

  variables {
    api_facade_image = "docker.io/library/nginx:latest"
  }

  expect_failures = [
    var.api_facade_image,
  ]
}

run "rejects_non_ocir_api_facade_image" {
  command = plan

  variables {
    api_facade_image = "my-registry.com/namespace/repo:tag"
  }

  expect_failures = [
    var.api_facade_image,
  ]
}

# ------------------------------------------------------------------------------
# rest_proxy_image
# ------------------------------------------------------------------------------

run "rejects_dockerhub_rest_proxy_image" {
  command = plan

  variables {
    rest_proxy_image = "docker.io/library/nginx:latest"
  }

  expect_failures = [
    var.rest_proxy_image,
  ]
}

run "rejects_non_ocir_rest_proxy_image" {
  command = plan

  variables {
    rest_proxy_image = "my-registry.com/namespace/repo:tag"
  }

  expect_failures = [
    var.rest_proxy_image,
  ]
}

# ------------------------------------------------------------------------------
# compartment_name
# ------------------------------------------------------------------------------

run "rejects_empty_compartment_name" {
  command = plan

  variables {
    compartment_name = ""
  }

  expect_failures = [
    var.compartment_name,
  ]
}

run "rejects_compartment_name_too_long" {
  command = plan

  variables {
    compartment_name = "aaaaaaaaaabbbbbbbbbbccccccccccddddddddddeeeeeeeeeeaaaaaaaaaabbbbbbbbbbccccccccccddddddddddeeeeeeeeeeX"
  }

  expect_failures = [
    var.compartment_name,
  ]
}

# ------------------------------------------------------------------------------
# region
# ------------------------------------------------------------------------------

run "rejects_invalid_region_format" {
  command = plan

  variables {
    region = "invalid_region"
  }

  expect_failures = [
    var.region,
  ]
}

run "rejects_empty_region" {
  command = plan

  variables {
    region = ""
  }

  expect_failures = [
    var.region,
  ]
}

run "rejects_uppercase_region" {
  command = plan

  variables {
    region = "SA-SAOPAULO-1"
  }

  expect_failures = [
    var.region,
  ]
}
