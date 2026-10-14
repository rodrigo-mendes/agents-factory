# Evaluation Scenarios — integrating-oracle-rms-webhooks

## Scenario 1: Canonical — EVENT mode consumer with by-id enrichment

```json
{
  "skills": ["integrating-oracle-rms-webhooks"],
  "query": "My OCI Function receives an EVENT webhook from RMS for the 'foundation/item' service. I need to enrich each item by calling the by-id endpoint and then forward the full record downstream.",
  "expected_behavior": [
    "Parses the EVENT envelope: reads uuid, service, since fields",
    "Calls GET /services/foundation/item/{id} with path-param — NOT ?item=<id>",
    "Uses correct MerchIntegrations base URL (sibling of RmsReSTServices, not child)",
    "Caches OAuth2 token with volatile+synchronized pattern; refreshes 60s before expiry",
    "Reads secrets (client_id, client_secret) from OCI Vault — not from func.yaml config values",
    "Applies @JsonIgnoreProperties(ignoreUnknown=true) on WebhookEnvelope and item POJOs",
    "Logs uuid for correlation on every invocation"
  ]
}
```

## Scenario 2: Canonical — PAYLOAD custom mode, no enrichment needed

```json
{
  "skills": ["integrating-oracle-rms-webhooks"],
  "query": "I want to register a webhook that delivers only item, status, and itemDescription fields inline. My function should not call back to RMS for enrichment.",
  "expected_behavior": [
    "Configures webhook with includePayload=Y and queryParameter=include=items.action,items.item,items.status,items.itemDescription",
    "Parses items from payload.items — NOT from envelope root",
    "Skips the enrichment step (no by-id call) since payload is already complete",
    "Still applies idempotency guard using uuid as deduplication key",
    "Does NOT attempt ?item= filter on the publish endpoint for selective fields"
  ]
}
```

## Scenario 3: Edge — Large batch exceeds function timeout

```json
{
  "skills": ["integrating-oracle-rms-webhooks"],
  "query": "My function handles webhook batches that can contain up to 1000 items. Each item requires a by-id enrichment call to RMS. The function times out after 60s. How do I fix this?",
  "expected_behavior": [
    "Identifies: 1000 items × ~100ms per GET RMS = ~100s, which exceeds the 60s function timeout",
    "Recommends async processing: push items to OCI Queue or OCI Streaming and return 200 immediately",
    "Alternatively: reduce batch size via webhook pageLimit setting",
    "Notes that synchronous enrichment of large batches is a Never Do pattern",
    "Does NOT suggest simply increasing function timeout as the sole solution"
  ]
}
```

## Scenario 4: Edge — Network allowlist blocks local testing

```json
{
  "skills": ["integrating-oracle-rms-webhooks"],
  "query": "When I run rms-get.sh from my laptop I get a 302 redirect to IDCS. But the function works fine in OCI. What is wrong?",
  "expected_behavior": [
    "Explains the MerchIntegrations host is behind the IDCS Cloud Gate with a network allowlist",
    "Local machine IP is not on the allowlist; OCI VCN egress is permitted",
    "Recommends running scripts from inside OCI (e.g., OCI Cloud Shell, Bastion) or from an allowlisted VPN",
    "Notes simulate-webhook.sh can still be run locally to test the function's listener side",
    "Does NOT suggest disabling the Cloud Gate or bypassing IDCS authentication"
  ]
}
```

## Scenario 5: Misuse — Wrong base URL construction

```json
{
  "skills": ["integrating-oracle-rms-webhooks"],
  "query": "I built the base URL as: https://<host>/rgbu-<env>/RmsReSTServices/MerchIntegrations/services/foundation/item. My calls all return 404.",
  "expected_behavior": [
    "Identifies the root cause: MerchIntegrations is a sibling application, not a path under RmsReSTServices",
    "Correct URL: https://<host>/rgbu-<env>/MerchIntegrations/services/foundation/item",
    "Flags this as a Never Do pattern documented in never-do-patterns.md",
    "Does NOT generate code using the /RmsReSTServices/MerchIntegrations path",
    "References func.yaml ITEM_ENRICH_PATH_TEMPLATE pattern in services/func-rr-rest-proxy/"
  ]
}
```
