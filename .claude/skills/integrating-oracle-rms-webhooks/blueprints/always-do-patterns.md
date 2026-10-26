# Always Do — RMS/MFCS Webhook Integration

## 1. Correct MerchIntegrations Base URL
`MerchIntegrations` is a **sibling** of `RmsReSTServices` under the tenant, not a child.
```
✅ https://<host>/rgbu-<env>/MerchIntegrations/services/foundation/item/{id}
🚫 https://<host>/rgbu-<env>/RmsReSTServices/MerchIntegrations/...   # 404 Tomcat
```
If the function config uses `STORE_SOURCE_BASE_URL=.../RmsReSTServices` (for storeDetail), MerchIntegrations calls require a **separate** base (absolute URL). Example: `ITEM_ENRICH_PATH_TEMPLATE` in `func-rr-rest-proxy` accepts an absolute URL (`{id}` placeholder).

## 2. By-id via PATH param
```
✅ GET /services/foundation/<ent>/{id}     # path-param; 404 if absent; {items:[record]}
🚫 GET /services/foundation/<ent>?item={id}  # publish endpoint ignores it → WRONG item returned (200)
```
Response envelope: extract `payload.items[0]` OR `items[0]` (fallback). Example: `RestProxyFunction.extractSingleItem`.

## 3. Envelope parsing: `payload.items`
Items are nested under `payload.items` (PAYLOAD). EVENT has no `payload`. Branch by `type`:
```
type=PAYLOAD → iterate payload.items
type=EVENT   → fetch delta (since/before) OR by-id
```
POJOs with `@JsonIgnoreProperties(ignoreUnknown=true)` (forward-compat — MFCS payloads are wide).

## 4. OAuth2 client-credentials (cache)
Replicate `RmsClient.getAccessToken()` (`services/func-rr-rest-proxy/.../client/RmsClient.java:51-101`):
```java
String cred = Base64.getEncoder().encodeToString((clientId+":"+clientSecret).getBytes());
// POST oauthTokenUrl, header Authorization: Basic <cred>,
// Content-Type: application/x-www-form-urlencoded, body: grant_type=client_credentials&scope=<scope>
```
- Cache: `volatile cachedToken` + `volatile tokenExpiresAt`, `synchronized`, refresh **60s before** expiry.
- Secrets (`client_id`/`client_secret`) in OCI Vault, referenced by OCID; read in `@FnConfiguration`.
- Scope: `rgbu:merch:MFCS-PAR1`. Token URL: IDCS `/oauth2/v1/token`.

## 5. Retry + timeout budget
- Retry on 5xx/timeout, exponential backoff (2 attempts typical). Fail-fast on 4xx.
- `HttpRequest.timeout()` < function timeout. 1 GET RMS per enriched item → size carefully: large batches exceed 60s.
- HttpClient cached (HTTP/1.1) in `@FnConfiguration`.

## 6. Idempotency
Delivery is **at-least-once**. Use idempotent operations (PUT/upsert), dedup by `item`+`updateDateTime` or external marker. The same `uuid`/item reprocessed must not duplicate the effect.

## 7. PAYLOAD custom: `include=`
`queryParameter` on the webhook = `include=items.<field>,...` (e.g., `items.action,items.item,items.status,items.itemDescription`). Delivers only the required fields → less traffic. If the function enriches by id, the custom payload can be minimal (`items.item,items.action`).

## 8. Observability
- MDC `webhookId`/`correlationId` = envelope `uuid`. Log on entry, post-fetch item, post-transform, timing per call.
- CLIENT spans: `RMS.OAuthToken`, `RMS.ItemFetch`/`RMS.<Ent>Fetch`, downstream. `peer.service`, `http.method`, `http.status_code`.
