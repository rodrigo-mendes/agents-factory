# Module: Observability

Provisiona OCI Logging e Monitoring Alarms para a stack serverless.

## Recursos Criados

- **Log Group** — Grupo de logs para infraestrutura serverless
- **Service Logs** — Functions invoke, API Gateway access e execution
- **Notification Topic** — Tópico ONS para alertas
- **Monitoring Alarms** — Erros de Function, latência P95, API Gateway 5xx

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| `compartment_ocid` | OCID do compartment | `string` | - | yes |
| `functions_application_id` | OCID da Functions Application | `string` | - | yes |
| `api_deployment_id` | OCID do API Gateway Deployment | `string` | - | yes |
| `enable_logging` | Habilitar OCI Logging | `bool` | `true` | no |
| `enable_monitoring_alarms` | Habilitar Monitoring Alarms | `bool` | `true` | no |
| `alarm_duration_threshold_ms` | Threshold P95 latência (1-300000 ms) | `number` | `25000` | no |
| `notification_topic_name` | Nome base do Notification Topic | `string` | `serverless-alerts` | no |
| `environment` | Nome do ambiente | `string` | - | yes |
| `project_name` | Nome do projeto | `string` | - | yes |
| `tags` | Tags para os recursos | `map(string)` | `{}` | no |

## Uso

```hcl
module "observability" {
  source = "../../modules/observability"

  compartment_ocid         = var.compartment_ocid
  functions_application_id = module.app_api_handler.application_id
  api_deployment_id        = module.api_gateway.deployment_id
  enable_logging           = true
  enable_monitoring_alarms = true
  alarm_duration_threshold_ms = 25000
  environment              = var.environment
  project_name             = var.project_name
  tags                     = local.tags
}
```

## Outputs

| Name | Description |
|------|-------------|
| `log_group_id` | OCID do Log Group (null se logging desabilitado) |
| `notification_topic_id` | OCID do Notification Topic (null se monitoring desabilitado) |

## Dependências

- **Function App** — `functions_application_id` do módulo function-app
- **API Gateway** — `api_deployment_id` do módulo api-gateway
- Deve ser provisionado **após** functions e API Gateway
