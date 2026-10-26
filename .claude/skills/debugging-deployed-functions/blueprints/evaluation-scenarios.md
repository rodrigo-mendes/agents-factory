# Evaluation Scenarios — debugging-deployed-functions

## Scenario 1: Canonical — 502 Container Crash (Missing CMD)

```json
{
  "skills": ["debugging-deployed-functions"],
  "query": "My OCI Function returns 502 with an empty response body. The function was just deployed for the first time. OCI Logging shows no logs at all. What do I check?",
  "expected_behavior": [
    "Classifies 502 + empty body as Layer 0 cascading failure amplifier",
    "First check is CMD presence in Dockerfile: grep '^CMD' Dockerfile",
    "Explains that missing CMD causes container death before any code runs — hence zero logs",
    "Provides the fix: add CMD [\"com.example.MyFunction::handler\"] to Dockerfile",
    "Warns that after fixing CMD, additional errors may appear (cascade unrolling) and to budget for 2-3 more cycles",
    "Does NOT suggest checking Vault or IAM before CMD is confirmed present"
  ]
}
```

## Scenario 2: Edge — IAM Policy Missing (503 Vault 401)

```json
{
  "skills": ["debugging-deployed-functions"],
  "query": "My function was working yesterday. Today it returns 503 with detalhe: 'Vault secret retrieval failed: BmcException status 401'. I didn't change any code. What happened?",
  "expected_behavior": [
    "Classifies as IAM/Dynamic Group issue (not code bug)",
    "First diagnostic: check dynamic group matching rule via OCI CLI oci iam dynamic-group list",
    "Second diagnostic: check IAM policy via oci iam policy list for the compartment",
    "Notes that BmcException 401 from Vault = function identity not authorized, not wrong credentials",
    "Distinguishes 401 (authorization) from 404 (secret not found) — different root causes",
    "Suggests: verify dynamic group includes the function's compartment OCID",
    "Does NOT suggest rebuilding or redeploying as first action"
  ]
}
```

## Scenario 3: Edge — Cold Start Timeout (504)

```json
{
  "skills": ["debugging-deployed-functions"],
  "query": "My function has timeout_in_seconds=60. It worked locally but times out (504) in OCI. I'm making 3 external API calls in configure() and 2 in handler(). How do I debug this?",
  "expected_behavior": [
    "Applies the timeout budget calculator: Init Budget = 60 - 15 (cold start) - HandlerReserve",
    "Identifies that 3 SDK calls in configure() with default retries likely blow the init budget",
    "Calculates per-call budget: (60 - 15 - 20) / (3 calls × 2 retries) = 4.2s max per attempt",
    "Recommends reducing MaxAttempts, connectTimeout, readTimeout to fit within budget",
    "Optionally: increase timeout_in_seconds if downstream is legitimately slow",
    "Does NOT suggest adding more retries as the fix"
  ]
}
```

## Scenario 4: Misuse Guard — Skipping HTTP Status Classification

```json
{
  "skills": ["debugging-deployed-functions"],
  "query": "My function is broken. Can you just check all the possible issues: CMD, pom.xml, Vault, IAM, network, timeouts?",
  "expected_behavior": [
    "Redirects to the Classify → Investigate → Eliminate methodology",
    "Asks for the HTTP status code first (502 vs 503 vs 504 vs 500)",
    "Explains that each status points to a different diagnostic layer",
    "Does NOT check all possible issues simultaneously without classification",
    "Provides the curl command to capture full response with HTTP status",
    "Explains that parallel diagnosis wastes time and misses cascading failures"
  ]
}
```

## Scenario 5: Edge — Cascading Failure in New Function

```json
{
  "skills": ["debugging-deployed-functions"],
  "query": "I built a new function with Vault access, OAuth, and JAXB. After deploy I got 502. I fixed CMD and now I get 500 with 'No http provider'. I fix that and now get 503 OAuth 401. Am I regressing?",
  "expected_behavior": [
    "Identifies this as a cascading failure unrolling — NOT regression",
    "Explains the Invisibility Amplifier pattern: Layer 0 was hiding Layers 1, 2, 3",
    "Confirms progress: each new error = previous layer fixed, next layer now visible",
    "Applies cascade budget: 4 capabilities (Vault + OAuth + JAXB + SDK) → budget 4-6 more cycles",
    "Next step: 503 OAuth 401 → check Vault secret content and IAM dynamic group",
    "Does NOT recommend rollback — explicitly states each error is forward progress"
  ]
}
```
