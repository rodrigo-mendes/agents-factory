---
name: terraform-multi-function
description: "Multi-function composition patterns for OCI Functions + API Gateway. Use when composing multiple OCI Functions as isolated Applications and routing API Gateway requests to specific function backends per route."
paths:
  - "**/*.tf"
  - "**/*.tfvars"
  - "**/*.hcl"
---
# Multi-Function Composition

## Overview

This instruction covers patterns for composing multiple OCI Functions as isolated Applications and routing API Gateway requests to specific function backends per route. Each function gets its own `oci_functions_application` via the `modules/function-app` module.

## When This Applies

- Creating or modifying `modules/function-app/` (Application + Function per instance)
- Creating or modifying `modules/api-gateway/` with `route_backends`
- Adding new functions to an environment composition (`environments/<env>/apps.tf`)

## Skill References

For complete provisioning patterns and HCL examples, load:
- **Function App module**: `.claude/skills/provisioning-oci-functions/SKILL.md`
- **API Gateway module**: `.claude/skills/provisioning-oci-api-gateway/SKILL.md` → section "Multi-Backend Routing"
- **Integrated stack**: `.claude/skills/provisioning-oci-serverless-stack/SKILL.md` → section "Multi-Function Composition"

## Architecture

```
modules/function-app (instance per function):
├── module "app_api_handler"    → Application + Function A
├── module "app_api_facade"     → Application + Function B
└── module "app_rest_proxy"     → Application + Function C

modules/api-gateway (single instance, multi-route):
├── Route /hello           → Function A (app_api_handler.function_id)
├── Route /facade/hello    → Function B (app_api_facade.function_id)
├── Route /facade/secret   → Function B (app_api_facade.function_id)
├── Route /proxy/store/*   → Function C (app_rest_proxy.function_id)
└── Route /health          → Stock Response (built-in)
```

## Mandatory Patterns

### Function App Module — One Module Instance Per Function

```hcl
# environments/<env>/apps.tf

module "app_<name>" {
  source = "../../modules/function-app"

  compartment_ocid   = var.compartment_ocid
  subnet_id          = module.network.subnet_private_id
  nsg_ids            = var.use_nsg ? [module.network.nsg_functions_id] : []
  application_name   = "app-<name>"
  function_name      = "<name>"
  function_image     = var.<name>_image
  memory_in_mbs      = 256
  timeout_in_seconds = 60
  function_config    = { LOG_LEVEL = "INFO" }
  function_shape     = var.function_shape
  trace_enabled      = var.trace_enabled
  environment        = var.environment
  tags               = local.tags

  depends_on = [module.iam]
}
```

**Module outputs**:
```hcl
output "application_id" { value = oci_functions_application.this.id }
output "function_id"    { value = oci_functions_function.this.id }
output "invoke_endpoint" { value = oci_functions_function.this.invoke_endpoint }
```

### API Gateway Module — `var.route_backends` (required)

```hcl
variable "route_backends" {
  type = list(object({
    path        = string
    methods     = list(string)
    function_id = string
    auth_type   = optional(string, "AUTHENTICATION_ONLY")
  }))
  description = "Lista de routes com function_id individual por rota."
}
```

**Usage in environment**:
```hcl
module "api_gateway" {
  source = "../../modules/api-gateway"

  route_backends = [
    { path = "/hello",  methods = ["GET", "POST"], function_id = module.app_api_handler.function_id, auth_type = "ANONYMOUS" },
    { path = "/users",  methods = ["GET"],         function_id = module.app_api_handler.function_id, auth_type = "AUTHENTICATION_ONLY" },
    { path = "/facade", methods = ["POST"],        function_id = module.app_api_facade.function_id,  auth_type = "AUTHENTICATION_ONLY" },
  ]
  # ... gateway config ...
}
```

## Adding a New Function

1. Create function code in `services/<function-name>/`
2. Build and push Docker image to OCIR
3. Add `module "app_<name>"` block in `environments/<env>/apps.tf`
4. Add route entry in `route_backends` of `module "api_gateway"`
5. Add image variable in `variables.tf` + `terraform.tfvars`
6. `terraform plan` → `terraform apply`

## ✅ Always Do

- Use module instance name matching function name: `module "app_<function_name>"`
- Reference function_id via module output: `module.app_<name>.function_id`
- Keep `depends_on = [module.iam]` for all function-app instances
- Validate `route_backends` function_ids with OCID regex in the module
- Use `auth_type = "ANONYMOUS"` only for public endpoints (health, hello)

## 🚫 Never Do

- Create raw `oci_functions_function` resources outside of `modules/function-app`
- Share a single Application across multiple unrelated functions
- Hardcode function OCIDs in route_backends (always use module output references)
- Put function-specific configuration (OAuth URLs, etc.) in the module — keep in environment `apps.tf`
