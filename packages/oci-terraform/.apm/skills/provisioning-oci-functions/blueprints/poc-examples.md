# Worked Examples — provisioning-oci-functions

Source: `workspace/poc-oci-serverless/infra/modules/function-app/`

---

## Worked example (from the reference PoC)

### Application + Function — `infra/modules/function-app/main.tf`

The PoC deploys one `oci_functions_application` per logical function (isolated application model).
Each module instance receives its own subnet, NSG list, and config map.

```hcl
# from infra/modules/function-app/main.tf

resource "oci_functions_application" "this" {
  compartment_id             = var.compartment_ocid
  display_name               = "${var.application_name}-${var.environment}"
  subnet_ids                 = [var.subnet_id]
  shape                      = var.function_shape   # GENERIC_X86 | GENERIC_ARM | GENERIC_X86_ARM
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
  application_id     = oci_functions_application.this.id
  display_name       = "${var.function_name}-${var.environment}"
  image              = var.function_image     # must include digest (image@sha256:...)
  memory_in_mbs      = var.memory_in_mbs
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
```

**Key patterns from this example:**
- `shape` is Application-level and **immutable** — changing it forces destroy/recreate.
- `subnet_ids` is also **immutable** — plan carefully before first apply.
- `image` uses an image reference; in practice pin it with `image_digest` to avoid silent deploy drift.
- `provisioned_concurrency_config` is only emitted when `provisioned_concurrency > 0` (dynamic block).
- `freeform_tags` receives `var.tags` (a `local.common_tags` map from the environment layer).
