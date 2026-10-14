# ==============================================================================
# Module: APM
# ==============================================================================
# Provisiona um OCI APM Domain (free tier) e expõe as data keys para
# instrumentação de funções serverless.
# ==============================================================================

resource "oci_apm_apm_domain" "this" {
  compartment_id = var.compartment_ocid
  display_name   = "apm-${var.project_name}-${var.environment}"
  description    = "APM Domain para funções serverless (${var.project_name}-${var.environment})"
  is_free_tier   = true
  freeform_tags  = var.tags

  lifecycle {
    ignore_changes = [is_free_tier]
  }
}

data "oci_apm_data_keys" "private" {
  apm_domain_id = oci_apm_apm_domain.this.id
  data_key_type = "PRIVATE"
}
