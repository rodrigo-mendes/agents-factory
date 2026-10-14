# ==============================================================================
# Module: Function App
# ==============================================================================
# Deploys a single OCI Functions Application with one Function.
# Each instance of this module represents one isolated application.
# ==============================================================================

resource "oci_functions_application" "this" {
  compartment_id             = var.compartment_ocid
  display_name               = "${var.application_name}-${var.environment}"
  subnet_ids                 = [var.subnet_id]
  shape                      = var.function_shape
  network_security_group_ids = var.nsg_ids

  config = merge(var.function_config, {
    "ENVIRONMENT" = var.environment
  })

  trace_config {
    is_enabled = var.trace_enabled
    domain_id  = var.apm_domain_id != "" ? var.apm_domain_id : null
  }

  freeform_tags = var.tags
}

resource "oci_functions_function" "this" {
  application_id = oci_functions_application.this.id
  display_name   = "${var.function_name}-${var.environment}"
  image          = var.function_image
  memory_in_mbs  = var.memory_in_mbs

  timeout_in_seconds = var.timeout_in_seconds

  dynamic "provisioned_concurrency_config" {
    for_each = var.provisioned_concurrency > 0 ? [1] : []
    content {
      strategy = "CONSTANT"
      count    = var.provisioned_concurrency
    }
  }

  trace_config {
    is_enabled = var.trace_enabled
  }

  freeform_tags = var.tags
}
