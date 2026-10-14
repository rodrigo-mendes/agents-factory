---
kind: work-order
from: "@oci-serverless-architect"
to: "@oci-terraform"
capability: func-api-facade
stream: c-terraform-integration
dependsOn: [stream-a, stream-b]
status: completed
createdAt: 2026-05-18T00:00:00Z
---

## Scope

Provision the `func-api-facade` Function resource and configure API Gateway routes to invoke it. This stream depends on Stream A (func.yaml and Docker image must exist) and Stream B (Vault and bucket must be provisioned).

## Components

- [ ] Add `func-api-facade` Function resource to infrastructure composition
  - Reuse existing `modules/functions/` module with new parameters
  - Application: `app-integration-patterns` (shared application for all pattern functions)
  - Function name: `func-api-facade`
  - Image: `gru.ocir.io/${namespace}/patterns/func-api-facade:0.0.1`
  - Memory: 256 MB
  - Timeout: 60s
  - Config: `{ ENVIRONMENT = var.environment }`
  - Tracing: enabled
- [ ] Configure API Gateway routes for the new function
  - Route: `GET,POST /hello` → `func-api-facade`
  - Route: `POST /secret` → `func-api-facade`
  - Route: `POST /store` → `func-api-facade`
  - Auth: JWT (if enabled) with anonymous fallback for `/health`
- [ ] Wire Observability for the new function
  - Service Log: invoke log for new application
  - Alarm: error rate > 5% over 5 min
  - Alarm: P95 latency > 25s
  - Alarm: 5xx responses > 5 in 5 min window

## Constraints

### Function Resource

```hcl
module "fn_api_facade" {
  source = "./modules/functions"

  compartment_ocid            = var.compartment_ocid
  subnet_id                   = module.network.subnet_private_id
  nsg_ids                     = var.use_nsg ? [module.network.nsg_functions_id] : []
  application_name            = "app-integration-patterns"
  function_name               = "func-api-facade"
  function_image              = "gru.ocir.io/${var.ocir_namespace}/patterns/func-api-facade:0.0.1"
  function_memory_in_mbs      = 256
  function_timeout_in_seconds = 60
  function_config             = { ENVIRONMENT = var.environment }
  function_shape              = "GENERIC_X86"
  provisioned_concurrency     = 0
  trace_enabled               = true
  environment                 = var.environment
  tags                        = local.tags

  depends_on = [module.iam]
}
```

### API Gateway Routes

The API Gateway module currently accepts a single `function_id`. Two options:

**Option A (Recommended)**: Extend `api_routes` variable to support per-route `function_id`:
```hcl
api_routes = [
  { path = "/hello",  methods = ["GET", "POST"], function_id = module.fn_api_facade.function_id },
  { path = "/secret", methods = ["POST"],        function_id = module.fn_api_facade.function_id },
  { path = "/store",  methods = ["POST"],        function_id = module.fn_api_facade.function_id },
]
```

**Option B**: Create a second API Gateway deployment with a different path prefix (e.g., `/v1/facade/`).

Decision: Use **Option A** — extend the `api-gateway` module to support per-route function_id with fallback to the module-level `function_id` for backward compatibility.

### Module Changes Required

1. **`modules/api-gateway/variables.tf`**: Add optional `function_id` to `api_routes` object type
2. **`modules/api-gateway/main.tf`**: Use `routes.value.function_id` if set, else fallback to `var.function_id`
3. **Root `main.tf`**: Add `module "fn_api_facade"` block + update `api_routes` variable

### Observability Configuration

| Alarm | Metric | Threshold | Window |
|-------|--------|-----------|--------|
| Error rate | `FunctionInvocationErrors` | > 5% | 5 min |
| Latency P95 | `FunctionDuration` P95 | > 25,000 ms | 5 min |
| 5xx responses | `ApiGateway5xxCount` | > 5 | 5 min |

## Dependencies

### From Stream A (Java)

- `func.yaml` exists at `services/func-api-facade/func.yaml`
- Docker image built and pushed to OCIR: `gru.ocir.io/${namespace}/patterns/func-api-facade:0.0.1`
- Note: For `terraform plan` the image doesn't need to exist, but `terraform apply` requires it

### From Stream B (Infra)

- Vault module outputs: `vault_id`, `key_id` (for function config if needed)
- Object Storage bucket exists: `bucket-api-facade-{environment}`
- IAM policies verified as sufficient

### Existing Resources (already provisioned)

- VCN + subnets from `module.network`
- NSGs from `module.network`
- Dynamic Groups + Policies from `module.iam`
- API Gateway resource from `module.api_gateway`

## Acceptance Criteria

- [ ] `cd infra && terraform validate` passes
- [ ] `terraform plan` shows new function resource and updated API GW deployment
- [ ] API Gateway routes `/hello`, `/secret`, `/store` resolve to `func-api-facade` function OCID
- [ ] Observability alarms configured for the new function
- [ ] Backward compatibility: existing `api-handler` function and routes remain unaffected
- [ ] `cd infra/tests && ./run_tests.sh` passes (structural tests)
