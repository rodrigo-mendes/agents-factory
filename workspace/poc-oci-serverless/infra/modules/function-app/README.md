# Module: Function App

Provisiona uma OCI Functions Application isolada com uma Function. Cada instância do módulo cria uma Application separada, garantindo isolamento de blast radius entre functions.

## Recursos Criados

- **Functions Application** — Container lógico para a Function (inclui trace config e tags)
- **Function** — Function serverless com imagem Docker do OCIR

## Uso

```hcl
module "app_api_handler" {
  source = "../../modules/function-app"

  compartment_ocid   = var.compartment_ocid
  subnet_id          = module.network.subnet_private_id
  nsg_ids            = [module.network.nsg_functions_id]
  application_name   = "app-api-handler"
  function_name      = "api-handler"
  function_image     = var.api_handler_image
  memory_in_mbs      = 256
  timeout_in_seconds = 60
  function_config    = { LOG_LEVEL = "INFO" }
  environment        = var.environment
  tags               = local.tags

  depends_on = [module.iam]
}
```

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| `compartment_ocid` | OCID do compartment | `string` | — | yes |
| `subnet_id` | OCID da subnet privada (Functions) | `string` | — | yes |
| `nsg_ids` | Lista de NSG OCIDs | `list(string)` | `[]` | no |
| `application_name` | Nome da Application | `string` | — | yes |
| `function_name` | Nome da Function | `string` | — | yes |
| `function_image` | URI da imagem Docker no OCIR | `string` | — | yes |
| `memory_in_mbs` | Memória alocada (128, 256, 512, 1024, 2048) | `number` | `256` | no |
| `timeout_in_seconds` | Timeout de execução (5-300) | `number` | `60` | no |
| `provisioned_concurrency` | Instâncias pré-aquecidas (0-40) | `number` | `0` | no |
| `trace_enabled` | Habilitar tracing (APM) | `bool` | `true` | no |
| `function_config` | Variáveis de configuração da Function | `map(string)` | `{}` | no |
| `function_shape` | Arquitetura: GENERIC_X86, GENERIC_ARM, GENERIC_X86_ARM | `string` | `GENERIC_X86` | no |
| `environment` | Nome do ambiente | `string` | — | yes |
| `tags` | Freeform tags | `map(string)` | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| `application_id` | OCID da Functions Application |
| `function_id` | OCID da Function |
| `invoke_endpoint` | Endpoint de invocação da Function (sensitive) |

## Dependências

- **Network** — `subnet_id` e `nsg_ids` do módulo network
- **IAM** — Policies devem existir antes (`depends_on = [module.iam]`)
- **OCIR** — Imagem Docker deve estar publicada no Container Registry

## Notas

- A variável `ENVIRONMENT` é automaticamente adicionada ao `function_config`
- O `function_shape` deve ser compatível com a arquitetura da imagem Docker (`linux/amd64` para X86, `linux/arm64` para ARM)
- Use `provisioned_concurrency > 0` para eliminar cold starts em functions críticas
