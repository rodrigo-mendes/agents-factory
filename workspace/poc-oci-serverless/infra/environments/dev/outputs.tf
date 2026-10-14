# ==============================================================================
# Outputs: dev environment
# ==============================================================================

# --- API Gateway ---

output "api_base_url" {
  value       = module.api_gateway.deployment_endpoint
  description = "URL base da API (gateway endpoint + path prefix)"
}

output "health_check_url" {
  value       = "${module.api_gateway.deployment_endpoint}/health"
  description = "URL do health check"
}

output "api_gateway_hostname" {
  value       = module.api_gateway.gateway_hostname
  description = "Hostname do API Gateway"
}

output "api_gateway_id" {
  value       = module.api_gateway.gateway_id
  description = "OCID do API Gateway"
}

# --- API Gateway URLs per Function ---

output "api_handler_url_hello" {
  value       = "${module.api_gateway.deployment_endpoint}/hello"
  description = "URL da rota /hello (api-handler)"
}

output "api_facade_url_hello" {
  value       = "${module.api_gateway.deployment_endpoint}/facade/hello"
  description = "URL da rota /facade/hello (api-facade)"
}

output "api_facade_url_secret" {
  value       = "${module.api_gateway.deployment_endpoint}/facade/secret"
  description = "URL da rota /facade/secret (api-facade)"
}

output "api_facade_url_store" {
  value       = "${module.api_gateway.deployment_endpoint}/facade/store"
  description = "URL da rota /facade/store (api-facade)"
}

output "rest_proxy_url_store_create" {
  value       = "${module.api_gateway.deployment_endpoint}/proxy/store/create"
  description = "URL da rota /proxy/store/create (rest-proxy)"
}

output "rest_proxy_url_store_update" {
  value       = "${module.api_gateway.deployment_endpoint}/proxy/store/update"
  description = "URL da rota /proxy/store/update (rest-proxy)"
}

# --- Functions ---

output "api_handler_function_id" {
  value       = module.app_api_handler.function_id
  description = "OCID da Function api-handler"
}

output "api_handler_application_id" {
  value       = module.app_api_handler.application_id
  description = "OCID da Application api-handler"
}

output "api_facade_function_id" {
  value       = module.app_api_facade.function_id
  description = "OCID da Function func-api-facade"
}

output "api_facade_application_id" {
  value       = module.app_api_facade.application_id
  description = "OCID da Application func-api-facade"
}

output "rest_proxy_function_id" {
  value       = module.app_rest_proxy.function_id
  description = "OCID da Function func-rr-rest-proxy"
}

output "rest_proxy_application_id" {
  value       = module.app_rest_proxy.application_id
  description = "OCID da Application func-rr-rest-proxy"
}

# --- Event-Driven Pub/Sub (Pattern 02) — Functions ---

output "event_producer_function_id" {
  value       = module.app_event_producer.function_id
  description = "OCID da Function func-event-producer"
}

output "event_producer_application_id" {
  value       = module.app_event_producer.application_id
  description = "OCID da Application app-event-producer (usado pelo dashboard oci_faas applicationId)"
}

# --- Event-Driven Pub/Sub (Pattern 02) — Consumers (Functions) ---

output "evt_consumer_notify_function_id" {
  value       = module.app_evt_consumer_notify.function_id
  description = "OCID da Function func-evt-consumer-notify (target do SCH notify)"
}

output "evt_consumer_notify_application_id" {
  value       = module.app_evt_consumer_notify.application_id
  description = "OCID da Application app-evt-consumer-notify (usado pelos alarmes/queries oci_faas por applicationId)"
}

output "evt_consumer_audit_function_id" {
  value       = module.app_evt_consumer_audit.function_id
  description = "OCID da Function func-evt-consumer-audit (target do SCH audit)"
}

output "evt_consumer_audit_application_id" {
  value       = module.app_evt_consumer_audit.application_id
  description = "OCID da Application app-evt-consumer-audit (usado pelos alarmes/queries oci_faas por applicationId)"
}

# --- Event-Driven Pub/Sub (Pattern 02) — Service Connector Hub ---

output "service_connector_ids" {
  value       = module.service_connector.connector_ids
  description = "Mapa nome-lógico (notify/audit) → OCID do Service Connector Hub"
}

output "service_connector_states" {
  value       = module.service_connector.connector_states
  description = "Mapa nome-lógico (notify/audit) → lifecycle_state do SCH (verificar ACTIVE pós-apply)"
}

# --- Event-Driven Pub/Sub (Pattern 02) — Streaming ---

output "stream_id" {
  value       = module.streaming.stream_id
  description = "OCID do Stream event-stream"
}

output "stream_pool_id" {
  value       = module.streaming.stream_pool_id
  description = "OCID do Stream Pool (endpoint PÚBLICO)"
}

output "events_url" {
  value       = "${module.api_gateway.deployment_endpoint}/events"
  description = "URL da rota POST /v1/events (event-producer)"
}

# --- Network ---

output "vcn_id" {
  value       = module.network.vcn_id
  description = "OCID do VCN"
}

output "subnet_private_id" {
  value       = module.network.subnet_private_id
  description = "OCID da subnet privada (Functions)"
}

output "subnet_public_id" {
  value       = module.network.subnet_public_id
  description = "OCID da subnet pública (API Gateway)"
}

# --- Vault ---

output "vault_id" {
  value       = module.vault.vault_id
  description = "OCID do KMS Vault"
}

output "vault_key_id" {
  value       = module.vault.key_id
  description = "OCID da KMS Key"
}

# --- Observability (consumido pelos scripts de validação) ---

output "compartment_ocid" {
  value       = var.compartment_ocid
  description = "OCID do compartment (para queries de logging/monitoring)"
}

output "region" {
  value       = var.region
  description = "Região OCI"
}

output "log_group_id" {
  value       = module.observability.log_group_id
  description = "OCID do Log Group de observabilidade"
}

output "notification_topic_id" {
  value       = module.observability.notification_topic_id
  description = "OCID do Notification Topic de alarmes"
}

output "alarm_subscription_id" {
  value       = module.observability.alarm_subscription_id
  description = "OCID da subscription de email dos alarmes (null se não configurada)"
}

output "apm_domain_id" {
  value       = module.apm.apm_domain_id
  description = "OCID do APM Domain"
}

# --- Dashboards ---

output "dashboard_ids" {
  value       = module.dashboards.dashboard_ids
  description = "Mapa dos Management Dashboards do rest-proxy (key -> display_name + import_id)"
}
