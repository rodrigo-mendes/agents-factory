# Never Do — RMS/MFCS Pitfalls (all cost real debugging time)

## 🚫 Concatenate MerchIntegrations under RmsReSTServices
```
🚫 sourceBaseUrl(".../RmsReSTServices") + "/MerchIntegrations/services/foundation/item"
   → https://.../RmsReSTServices/MerchIntegrations/...  → HTTP 404 (Tomcat HTML)
✅ https://.../rgbu-<env>/MerchIntegrations/services/foundation/item/{id}
```
`MerchIntegrations` and `RmsReSTServices` are **siblings**. Affects both delta and by-id calls. Symptom: 404 HTML (not JSON); auth passed (not a 401).

## 🚫 Use `?item=` (or `?<ent>=`) for by-id lookup
The publish endpoint `foundation/item` has **no** filter by id (params: since/before/offsetkey/limit/include/exclude). `?item=100010000&limit=1` returns **HTTP 200 with the WRONG item** (first entry from cache — e.g., requested T-Shirt, received LAPTOP). Silent and dangerous.
```
✅ GET /services/foundation/item/{id}   # path-param
```

## 🚫 Read `items` at the envelope root
The real PAYLOAD nests under `payload.items`. Reading `items` at the root → always 0 items → silently falls into EVENT mode. Branch by `type`, read `payload.items`.

## 🚫 Log token/secret
Never log access_token, client_secret, or Basic header. In spans/logs: timing and status only. Secrets must come from Vault only — never from func.yaml/tfvars/code.

## 🚫 Synchronous enrichment of large batches
`pageLimit` up to 1000 × 1 GET RMS/item > 60s function timeout → 5xx with no cleanup. Large batches → async (Queue/Connector Hub).

## 🚫 Assume exactly-once delivery
Webhooks are **at-least-once** (+ heartbeat/replay). A non-idempotent handler duplicates data. Use upsert/dedup.

## 🚫 Trust the headless swagger
`.../MerchIntegrations/swagger-ui/` redirects to IDCS SSO (302) — WebFetch/curl without credentials cannot access it. Validate the by-id endpoint and `webhooks/manage` empirically with a real token.

## 🚫 Parse `readValue(body, Map.class)` without checking for array
Some RMS endpoints return an **array** at the root (e.g., storeDetail), not an object → `MismatchedInputException`. Check the shape (array vs object) for each endpoint.
