# Integration Patterns — RMS/MFCS Webhook Consumer

## Pattern A — Synchronous function (webhook → enrich → transform → forward)
Reference implementation: `services/func-rr-rest-proxy/`.

```
API Gateway (POST /proxy/item/webhook, ANONYMOUS)
  → RestProxyFunction.handler  (fn-events APIGatewayFunction<String,StoreResponse>)
     → parse WebhookEnvelope (payload.items)             [model/WebhookEnvelope.java]
     → MDC.put(webhookId, uuid); log WEBHOOK type/uuid/count
     → per item:
         RMS.ItemFetch  : rmsClient.getItemById(id)       [client/RmsClient.java]
         log ENRICH item=<id> full=<json>
         buildItemModel → marshal XML ; log TRANSFORM
         BrxServices.PostItem : forward (PUT/POST/DELETE by action)
     → aggregate: 200 (all ok) / 207 (partial) / 500
```
Reusable pieces:
- `RmsClient.getAccessToken()` — OAuth2 cache.
- `RmsClient.getItemById(id)` — by-id path-param, configurable URL (`ITEM_ENRICH_PATH_TEMPLATE`).
- `WebhookEnvelope` — `{type,uuid,service,since,payload:{items[]}}`, `@JsonIgnoreProperties(ignoreUnknown=true)`.
- `extractSingleItem` / `extractItemsArray` — `payload.items[0]` with fallback.

## Pattern B — Async for large batches
```
webhook → thin function: validate + enqueue ids (OCI Queue/Streaming) → quick 200 response
worker (ConnectorHubFunction / Queue consumer): drains, enrich by-id, transform, forward
```
Avoids exceeding 60s when `pageLimit` is high. Idempotency enforced in the worker.

## Pattern C — EVENT + delta
EVENT webhook (uuid/since only) → function calls delta `GET foundation/<ent>?since=&before=` (before = event `timestamp`) → processes rows. Good for low traffic.

## Observability (3 pillars)
- **Logs** (JSON, source `app-<fn>-dev`): `WEBHOOK`, `ENRICH item=.. full=..`, `TRANSFORM item=.. xml=..`, `BRX_SEND item=.. elapsed=..ms`. MDC: `webhookId`,`traceId`,`spanId`.
- **Traces** (APM/OTel): spans `RMS.OAuthToken`, `RMS.ItemFetch`, `<Downstream>.Post` with duration → time spent per external API.
- **Metrics** (OCI Monitoring, endpoint `telemetry-ingestion`): e.g. `RestProxyWebhookItems` dims route/mode/result.
Validate with skill `validating-oci-observability`.

## Terraform config (consumer function)
- App config: `STORE_SOURCE_BASE_URL` (RmsReSTServices), MerchIntegrations enrich base (absolute URL), `STORE_OAUTH_TOKEN_URL`/`SCOPE`, `STORE_OAUTH_CLIENT_ID_OCID`/`SECRET_OCID` (Vault), `APM_*`, `COMPARTMENT_OCID`.
- API Gateway route for the webhook (e.g. `/proxy/item/webhook`, POST, ANONYMOUS).
- IAM: function dynamic group + policy `read secret-bundles` on Vault.

## Registering the webhook in RMS
`scripts/register-webhook.sh --service foundation/item --listener <gw>/proxy/item/webhook` → POST `webhooks/manage` with `credentialName`, `includePayload`, `intervalSeconds`, `queryParameter=include=...`. See `scripts/README.md`.
