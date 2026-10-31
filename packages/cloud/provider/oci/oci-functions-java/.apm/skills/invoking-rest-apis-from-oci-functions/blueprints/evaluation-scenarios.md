# Evaluation Scenarios — invoking-rest-apis-from-oci-functions

## Scenario 1: Canonical — OCI SDK client calling another OCI service

```json
{
  "skills": ["invoking-rest-apis-from-oci-functions"],
  "query": "My OCI Function needs to read a secret from OCI Vault and then call OCI Object Storage to write a result file. Show the Java implementation.",
  "expected_behavior": [
    "Uses ResourcePrincipalAuthenticationDetailsProvider — no API keys or config files",
    "Both SecretsClient and ObjectStorageClient initialized in @FnConfiguration",
    "ClientConfiguration sets explicit readTimeoutMillis below function timeout on both clients",
    "RetryConfiguration limits attempts to 3 max (not SDK default of 8)",
    "BmcException caught and classified: 404 not retried, 429/5xx retried",
    "Does NOT create clients inside handleRequest method"
  ]
}
```

## Scenario 2: Canonical — Calling an external REST API with OAuth2

```json
{
  "skills": ["invoking-rest-apis-from-oci-functions"],
  "query": "My function calls a third-party REST API secured with OAuth2 client credentials. Credentials are stored in OCI Vault. Show the implementation.",
  "expected_behavior": [
    "Uses java.net.http.HttpClient (built-in, no extra dependency) for external REST",
    "HttpClient initialized once in @FnConfiguration — not per invocation",
    "OAuth2 token retrieved from Vault via OCI SDK SecretsClient",
    "Token cached with volatile+synchronized pattern; refreshed 60s before expiry",
    "Every HttpRequest sets an explicit .timeout(Duration.ofSeconds(N)) below function timeout",
    "Does NOT embed client_id/client_secret in source code or func.yaml",
    "Does NOT use OCI SDK client for external (non-OCI) REST — uses HttpClient instead"
  ]
}
```

## Scenario 3: Edge — SDK read timeout exceeds function timeout

```json
{
  "skills": ["invoking-rest-apis-from-oci-functions"],
  "query": "My function keeps getting 503 'Function Invoke Timedout' errors even though each individual API call seems fast. What is wrong?",
  "expected_behavior": [
    "Identifies the SDK default read timeout (60s) exceeding the default function timeout (30s)",
    "Shows how to set ClientConfiguration.builder().readTimeoutMillis(15000).build()",
    "Notes function timeout can be configured up to 300s — SDK timeout must remain below it",
    "Checks that retry strategy total time also fits within the budget",
    "Does NOT suggest simply increasing the function timeout as the only fix"
  ]
}
```

## Scenario 4: Edge — Function-to-function invocation, sync vs detached

```json
{
  "skills": ["invoking-rest-apis-from-oci-functions"],
  "query": "I need Function A to trigger Function B to do heavy processing. Function B can take up to 10 minutes. Should I call it synchronously?",
  "expected_behavior": [
    "Identifies the problem: Function A's timeout (max 300s) would be exceeded waiting for Function B",
    "Recommends Detached invocation via FunctionsInvokeClient with InvocationMode.DETACHED",
    "Explains detached invocations can run up to 720s independently",
    "Notes caller receives a 202 Accepted immediately — no response body from target",
    "Does NOT generate synchronous invocation code for a 10-minute target function",
    "References ask-first-decisions.md for the full sync vs detached decision matrix"
  ]
}
```

## Scenario 5: Misuse — API keys embedded in function config

```json
{
  "skills": ["invoking-rest-apis-from-oci-functions"],
  "query": "Can I put my external API key in func.yaml config so the function can read it via context.getConfiguration()?",
  "expected_behavior": [
    "Identifies the security vulnerability: func.yaml config is visible in OCI console and logs",
    "Mandates storing secrets in OCI Vault and retrieving via SecretsClient at runtime",
    "Explains the correct pattern: store VAULT_SECRET_OCID in func.yaml, not the secret value",
    "Does NOT generate code that reads a raw API key from function configuration",
    "References skill `designing-oci-vault-security` for Vault setup"
  ]
}
```
