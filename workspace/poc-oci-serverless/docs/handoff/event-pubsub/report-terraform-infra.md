---
kind: report
from: "@oci-terraform"
to: "@oci-serverless-stack"
refs: pderiso-implementa-o-pattern-eager-quokka.md (plan Fase 1)
capability: event-pubsub
outcome: success
createdAt: 2026-07-21T18:11:03Z
---

## What changed

New modules:
- infra/modules/streaming/{versions,variables,main,outputs}.tf — OCI Streaming (private Stream Pool + Stream event-stream).
- infra/modules/service-connector/{versions,variables,main,outputs}.tf — Service Connector Hub, for_each sobre var.connectors (fan-out).

Modified:
- infra/modules/iam/main.tf — nova oci_identity_policy.streaming (producer stream-push + SCH STREAM_READ/STREAM_CONSUME/fn-invocation). Statements existentes intactos.
- infra/modules/iam/outputs.tf — novo output policy_streaming_id.
- infra/environments/dev/main.tf — module streaming + module service_connector; 3 apps novas em module.observability.functions_applications.
- infra/environments/dev/apps.tf — 3 module app_* (producer/notify/audit) + rota /events (POST, AUTHENTICATION_ONLY) em route_backends.
- infra/environments/dev/variables.tf — event_producer_image, evt_consumer_notify_image, evt_consumer_audit_image, notify_target_url, streaming_use_cmek, sch_batch_size_in_kbs, sch_batch_time_in_sec.
- infra/environments/dev/outputs.tf — function_id/application_id de producer/notify/audit, stream_id, stream_pool_id, service_connector_ids, events_url.

NAO tocado: services/ (codigo Java, agente paralelo). prod NAO alterado (so dev nesta fase).

## Resources / OCIDs

Nenhum recurso aplicado (deploy e fase posterior; so fmt/validate). Recursos declarados:
- oci_streaming_stream_pool.this (private endpoint na subnet privada) -> output stream_pool_id.
- oci_streaming_stream.event_stream (name event-stream, partitions=3, retention=168h) -> outputs stream_id, messages_endpoint.
- oci_sch_service_connector.this["notify"] (sch-event-notify-dev) e ["audit"] (sch-event-audit-dev), mesma source stream -> output service_connector_ids.
- oci_identity_policy.streaming -> output policy_streaming_id.
- 3 Applications + 3 Functions (producer/notify/audit) via modules/function-app.

Interface modulo streaming:
- Inputs: compartment_ocid, subnet_id, nsg_ids=[], kms_key_id="" (CMEK opcional), stream_name="event-stream", partitions=3, retention_in_hours=168, project_name, environment, tags={}.
- Outputs: stream_id, stream_pool_id, messages_endpoint, stream_name.

Interface modulo service-connector:
- Inputs: compartment_ocid, stream_id, connectors (map de {display_name, function_id, batch_size_in_kbs?, batch_time_in_sec?}), cursor_kind="TRIM_HORIZON", default_batch_size_in_kbs=128, default_batch_time_in_sec=60, connector_state="ACTIVE", iam_dependencies=[], tags={}.
- Outputs: connector_ids (map key->OCID), connector_states.

## function_config emitido por app (CONTRATO com o Java)

app_event_producer (func-event-producer):
  ENVIRONMENT="dev", COMPARTMENT_OCID=<compartment_ocid>, METRIC_NAMESPACE="event_pubsub_analytics",
  LOG_LEVEL="INFO", SERVICE_NAME="func-event-producer", APM_DOMAIN_URL=module.apm.data_upload_endpoint,
  APM_DATA_KEY=module.apm.private_data_key, STREAM_OCID=module.streaming.stream_id,
  STREAM_MESSAGES_ENDPOINT=module.streaming.messages_endpoint

app_evt_consumer_notify (func-evt-consumer-notify):
  ENVIRONMENT="dev", COMPARTMENT_OCID=<compartment_ocid>, METRIC_NAMESPACE="event_pubsub_analytics",
  LOG_LEVEL="INFO", SERVICE_NAME="func-evt-consumer-notify", APM_DOMAIN_URL=module.apm.data_upload_endpoint,
  APM_DATA_KEY=module.apm.private_data_key, NOTIFY_TARGET_URL=var.notify_target_url (default https://httpbin.org/post)

app_evt_consumer_audit (func-evt-consumer-audit):
  ENVIRONMENT="dev", COMPARTMENT_OCID=<compartment_ocid>, METRIC_NAMESPACE="event_pubsub_analytics",
  LOG_LEVEL="INFO", SERVICE_NAME="func-evt-consumer-audit", APM_DOMAIN_URL=module.apm.data_upload_endpoint,
  APM_DATA_KEY=module.apm.private_data_key

Chaves conferem com o contrato do plano. Namespace event_pubsub_analytics. Stream event-stream.

## Novas variables (dev) + defaults

event_producer_image      = gru.ocir.io/placeholder/serverless/func-event-producer:latest      (regex OCIR)
evt_consumer_notify_image = gru.ocir.io/placeholder/serverless/func-evt-consumer-notify:latest  (regex OCIR)
evt_consumer_audit_image  = gru.ocir.io/placeholder/serverless/func-evt-consumer-audit:latest   (regex OCIR)
notify_target_url         = https://httpbin.org/post   (regex ^https?://)
streaming_use_cmek        = false   (bool)
sch_batch_size_in_kbs     = 128      (1-6000)
sch_batch_time_in_sec     = 60       (1-600)

Defaults placeholder nos 3 *_image garantem validate sem valores reais; no deploy sobrescrever via -var (tfvars permission-blocked).

## Novos outputs (dev)

event_producer_function_id, event_producer_application_id, evt_consumer_notify_function_id,
evt_consumer_notify_application_id, evt_consumer_audit_function_id, evt_consumer_audit_application_id,
stream_id, stream_pool_id, service_connector_ids, events_url.
(event_producer_application_id = applicationId consumido pelo dashboard oci_faas da Fase 3.)

## Validation

- terraform fmt -recursive infra/ -> OK (reformatou so alinhamento de map em main.tf)
- terraform fmt -recursive -check infra/ -> OK exit 0
- terraform -chdir=infra/environments/dev init -backend=false -> OK (5 modulos novos; oracle/oci v8.21.0)
- terraform -chdir=infra/environments/dev validate -> OK "Success! The configuration is valid." (0 warnings, 0 errors)
- Rule-check: sem OCIDs hardcoded nos modulos novos; sem hashicorp/oci; sem terraform_remote_state; todas vars novas com type+description+validation.
- NAO rodei plan/apply (proibido nesta fase; sem credencial). Erros server-side (schema oci_sch_service_connector) so aparecem no apply.

## Acceptance status

- [x] modules/streaming/ pool privado + stream event-stream (3 part, 168h) + outputs -> OK
- [x] modules/service-connector/ reusavel via for_each, 2 connectors mesma source, batch tunavel -> OK
- [x] IAM producer stream-push + SCH STREAM_READ/STREAM_CONSUME/fn-invocation (compartment-scoped) -> OK
- [x] Wiring dev: 3 apps, rota /v1/events AUTHENTICATION_ONLY, streaming+SCH modules, outputs p/ dashboard -> OK
- [x] fmt/validate verdes -> OK

## Deviations from plan

1. Provider/TF version: modulos novos usam oracle/oci >= 6.0, < 9.0 / TF >= 1.5 (padrao do repo, todos os modulos irmaos), nao ~> 8.0/>= 1.7 dos SKILLs. HCL compativel; init resolveu v8.21.0.
2. Tags: convencao do repo e input var.tags alimentado por local.tags do env (nao local.common_tags inline). Modulos novos aceitam var.tags e fazem merge com Component. Alinhado ao sibling-module style.
3. NSG do stream pool: reusei nsg_functions_id. Nao criei NSG/regras 9092 dedicadas -- egress do NSG functions ja e all->0.0.0.0/0 e a subnet privada roteia p/ Service Gateway (todos servicos OCI), entao o private endpoint do pool e alcancavel no POC. Se restringir egress depois, adicionar regra TCP 9092.
4. Ordem de apply (streaming+IAM antes do SCH): expressa em codigo via iam_dependencies=[module.iam.policy_streaming_id] + stream_id real. Um apply unico ja respeita a ordem por dependencia; se preferir faseado, -target=module.streaming -target=module.iam primeiro.
5. Slug de capability: event-pubsub (capability multi-funcao; sem work-order previo).

## Open issues / blockers

- Imagens dos 3 servicos ainda nao existem (codigo Java e o stream paralelo). Defaults placeholder passam no validate mas NAO no deploy.
- prod nao espelhado (so dev nesta fase).
- Schema real do oci_sch_service_connector so e validado server-side no apply.

## Next action

Fase 2 (codigo Java) roda em paralelo. Quando as 3 imagens estiverem prontas e a Fase 1 puder ser aplicada -- Hand off: run /deploy-function (@oci-deployer) -- build+push das 3 imagens, apply (streaming+IAM antes de ativar SCH), smoke em POST /v1/events. Context: docs/handoff/event-pubsub/report-terraform-infra.md.
