---
name: integrating-oracle-rms-webhooks
description: "Integrates OCI Functions with Oracle Retail Merchandising Foundation Cloud (MFCS/RMS) Publish APIs via webhook: webhook registration (webhooks/manage), EVENT vs PAYLOAD envelope modes, enrichment by id, foundation endpoints (delta since/before and by-id path param), and OAuth2 IDCS auth. Use when consuming RMS webhooks, registering a webhook listener, calling foundation endpoints (item, locations, diff*, tax*, etc.), or building/debugging the consumer function."
---

# Integrating Oracle RMS/Merchandising (MFCS) Webhooks

Consume and configure the **Publish APIs** of Oracle Retail Merchandising Foundation Cloud (MFCS) via **webhook**, from OCI Functions (Java FDK) or CLI. Distills what was implemented and **validated live** in `services/func-rr-rest-proxy` (flow `foundation/item`).

> Legend: ✅ **validated live** in this codebase · ◻️ **inferred** from swagger/docs (uniform Publish API pattern — confirm per entity).

## Version Context

- **API**: Merch Integration REST Services (MFCS) `26.1.x` — tenant `<mfcs-tenant>`, host `<mfcs-host>` (this project's npe example: tenant `rgbu-rex-brxs-par1-mfcs`, host `rex-npe.retail.sa-vinhedo-1.ocs.oraclecloud.com` — replace per environment).
- **Auth**: OAuth2 **client-credentials** via IDCS (`https://idcs-<id>.identity.oraclecloud.com/oauth2/v1/token`), scope `rgbu:merch:<APP-ENV>` (this project: `rgbu:merch:MFCS-PAR1`). Header `Authorization: Basic base64(client_id:client_secret)`, body `grant_type=client_credentials&scope=<scope>`. Secrets in OCI Vault. ✅
- **Consumer**: OCI Functions (Java 17, FDK v1.1.x, fn-events `APIGatewayFunction`) behind API Gateway. Reference impl: `services/func-rr-rest-proxy/`.
- **Swagger**: `.../MerchIntegrations/swagger-ui/` — **auth-gated (IDCS SSO)**, does not open headless.
- **Network**: The MerchIntegrations host sits behind the **IDCS Cloud Gate** with a **network allowlist**. The function reaches it (OCI VCN egress is permitted); calls from local machine receive **302 → IDCS authorize**. Run `rms-get`/`register-webhook` from inside OCI or from an allowlisted VPN. ✅ (observed)

**Known Gotchas**:
- `?item=<id>` on the delta endpoint returns 200 with the **wrong item** (first cache row) — use path-param `/{id}` for by-id lookup. ✅ (real trap)
- Base URL is `MerchIntegrations` sibling of `RmsReSTServices`, NOT a child: `https://<host>/rgbu-<env>/MerchIntegrations`. Concatenating onto `RmsReSTServices` → 404.

## Publish API Architecture (how the webhook is born)

```
entity table → trigger → ICL_RMS_<ENT>  (Integration Change Log)
   → job MERCHAPI_DELTA_EXT_<ENT>_ADHOC_PROCESS → MERCHAPI_EXT_<ENT> (JSON cache)
   → engine polls MERCHAPI_EXT_<ENT> every intervalSeconds → POST to listenerUrl (webhook)
```
Example item: `ITEM_MASTER → ICL_RMS_ITEM_MASTER → MERCHAPI_DELTA_EXT_ITEM_ADHOC_PROCESS → MERCHAPI_EXT_ITEM → webhook`.

## Webhook Payload Modes

| Mode | `includePayload` | Receives | Use |
|------|------------------|----------|-----|
| **EVENT** | `N` | Notification only (uuid/service/since/timestamp) | Low traffic (Oracle recommended); consumer fetches via delta/by-id |
| **PAYLOAD full** | `Y` | Modified entities with **all** attributes | No extra lookup needed |
| **PAYLOAD custom** | `Y` + `queryParameter=include=...` | Only selected fields | ✅ tested (`include=items.action,items.item,items.status,items.itemDescription`) |

## Received Envelope (POST to listener)

EVENT (no `payload`): ✅
```json
{"type":"EVENT","timestamp":"2026-05-29T02:06:57Z","service":"foundation/item",
 "uuid":"5784...","environment":"rgbu-rex-brxs-par1-mfcs","since":"2026-05-29T02:01:56Z"}
```
PAYLOAD (items under **`payload.items`**, NOT at root): ✅
```json
{"type":"PAYLOAD","timestamp":"...","service":"foundation/item","uuid":"1d00...",
 "environment":"...","since":"...",
 "payload":{"items":[{"action":"UPDATE","item":"100010000","status":"A","itemDescription":"..."}],
            "hasMore":false,"limit":1000,"count":3,"links":[...]}}
```
`action` ∈ {UPDATE, DELETE, ...} (map to the destination verb).

## Foundation Endpoints

- **MerchIntegrations base** (⚠️ **sibling** of `RmsReSTServices`, not child): ✅
  `https://<host>/rgbu-<env>/MerchIntegrations` — NOT `.../RmsReSTServices/MerchIntegrations`.
- **Delta/publish**: `GET /services/foundation/<ent>?since=&before=&limit=1000&offsetkey=&include=&exclude=` → `{items:[...], hasMore, limit, count, links}`. ◻️ (item ✅)
- **By-id lookup**: `GET /services/foundation/<ent>/{id}` — **path-param**, 404 if absent, `action`=null, returns `{items:[<record>]}`. ✅ (item; same pattern for `diffid/{diffId}`, `difftype/{diffType}`, `diffgroup/{diffGroupId}` ◻️).
- **Webhook config**: `.../services/administration/operations/webhooks/manage` (upload/download config). ◻️ POST by default.

Foundation entities (swagger): `item`, `aif/locations`, `diffgroup`, `diffid`, `difftype`, `banners`, `channels`, `taxGroupRule`, `taxLocation`, `administration/fiscalCalendar`, etc. Each publish entity typically has a sibling by-id `/{id}`.

## Consumer Pattern (function)

```
webhook → parse envelope (payload.items) → per item: enrich by-id → transform → forward → aggregate (200/207)
```
- Idempotency required (at-least-once delivery).
- Timeout budget: 1 GET RMS per item; large batches (`limit` up to 1000) exceed 60s → use async (Queue/Connector Hub).

## Scripts

Located in `.claude/skills/integrating-oracle-rms-webhooks/scripts/` (resolve repo root via `git`, run from any directory). See `scripts/README.md`.

| Script | Use |
|--------|-----|
| `rms-token.sh` | Obtains and prints an OAuth2 access_token (debug) |
| `rms-get.sh` | `GET` foundation: `--entity item --id <id>` (by-id) or `--since/--before` (delta) |
| `register-webhook.sh` | `--action register\|list\|disable` on `webhooks/manage` |
| `simulate-webhook.sh` | POST EVENT/PAYLOAD envelope to `--listener <url>` (tests the function) |
| `lib-rms.sh` | Config + helpers + `rms_token()` (creds via env or Vault) — sourced by others |

## Quick Navigation

- **[Always Do](./blueprints/always-do-patterns.md)** — Mandatory patterns (auth cache, base URL, by-id, parse, retry, idempotency)
- **[Ask First](./blueprints/ask-first-decisions.md)** — Decisions (EVENT vs PAYLOAD, enrich, listener auth, sync vs async)
- **[Never Do](./blueprints/never-do-patterns.md)** — Traps (base URL concatenation, `?item=`, items at root, logging secrets)
- **[Integration Patterns](./blueprints/integration-patterns.md)** — Consumer function + observability + async
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — Canonical, edge, and misuse test cases

---

## Blueprints & Guardrails

### ✅ Always Do

- Correct MerchIntegrations base URL (sibling of RmsReSTServices). By-id via **path** `/{id}`. Parse `payload.items`.
- OAuth2 token cache (volatile+synchronized, refresh 60s before expiry) — see `services/func-rr-rest-proxy/.../client/RmsClient.java:51-101`.
- `@JsonIgnoreProperties(ignoreUnknown=true)` on every inbound POJO. Retry 5xx/timeout with backoff.
- Idempotency. Log `uuid` (correlation). Secrets in Vault.

---

### ⚠️ Ask First

- Webhook mode (EVENT vs PAYLOAD full/custom). Enrich by id vs trust the payload. Listener auth (ANONYMOUS route vs credentialName). `intervalSeconds`/`pageLimit`. Sync vs async for large batches.

---

### 🚫 Never Do

- **Wrong**: `sourceBaseUrl(/RmsReSTServices) + /MerchIntegrations/...` → 404. **Correct**: use `https://<host>/rgbu-<env>/MerchIntegrations` directly.
- **Wrong**: `?item=<id>` for by-id lookup → returns wrong item. **Correct**: path-param `GET /services/foundation/item/{id}`.
- **Wrong**: reading `items` at envelope root. **Correct**: read `payload.items`.
- **Wrong**: logging OAuth2 token or Vault secret. **Correct**: log only the token expiry timestamp.
- **Wrong**: synchronous enrichment for large batches (1000 items × 1 GET = timeout). **Correct**: async via Queue or Connector Hub.

---

## Verification Loop

Run these from an OCI-internal host or allowlisted VPN (network allowlist required):

### 1. Obtain Token
```bash
./scripts/rms-token.sh
# Expected: prints a JWT access_token string
```

### 2. Fetch Item by ID
```bash
./scripts/rms-get.sh --entity item --id <item-id>
# Expected: {"items":[{"item":"<item-id>","status":"A",...}]}
# Exit code: 0
```

### 3. Fetch Delta
```bash
./scripts/rms-get.sh --entity item --since 2026-01-01T00:00:00Z --before 2026-01-02T00:00:00Z
# Expected: {"items":[...], "hasMore":false, "count":N}
```

### 4. Simulate Webhook
```bash
./scripts/simulate-webhook.sh --listener https://<apigw-host>/<path> --type EVENT
# Expected: HTTP 200 from the function
```

### 5. Verify Function Logs
```bash
oci logging search --search-query 'search "<log-group-ocid>/<log-ocid>" | where message like "uuid" | limit 5'
# Expected: log entries containing the uuid from the simulated webhook
```

**Troubleshooting**:
- `302 → IDCS authorize` on any endpoint → not on OCI network or allowlisted VPN.
- `404` on MerchIntegrations → base URL wrong — check for `/RmsReSTServices/MerchIntegrations` concatenation.
- `401` on token endpoint → client_id/secret wrong or scope mismatch.
- `200` with wrong item on delta → using `?item=` filter; switch to path-param `/{id}`.

---

## Reference Implementation

`services/func-rr-rest-proxy/`: `client/RmsClient.java` (OAuth2, delta, by-id), `RestProxyFunction.java` (`handleItemWebhook`, enrich→transform→send), `model/WebhookEnvelope.java` (envelope parse), `func.yaml` (`ITEM_ENRICH_PATH_TEMPLATE`).

---

## External Resources

- [Oracle Merchandising RESTful Web Services](https://docs.oracle.com/en/industries/retail/merchandising/23.1/rmsob/merchandising-restful-web-services.htm) — official REST API reference (verified 2026-07-26)
- [Oracle Retail Integration Cloud Service — Publish APIs Customer Enablement Overview](https://docs.oracle.com/en/industries/retail/) — white paper (navigate to Merchandising Integration) (verified 2026-07-26)
- MerchIntegrations Swagger: `.../MerchIntegrations/swagger-ui/` — **auth-gated (IDCS SSO required)**; not accessible headless (verified 2026-07-26)
- [OCI Vault — Secret Management](https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Concepts/keyoverview.htm) — for OAuth2 client credential storage (verified 2026-07-26)
- [OCI Functions Pricing](https://www.oracle.com/cloud/pricing/) — current pricing reference (verified 2026-07-26)
