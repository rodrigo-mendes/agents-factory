---
name: java-functions-external-apis
description: OCI Functions external REST API integration for Java 17 — HttpClient caching, OAuth2 Client Credentials, timeout budget, OCI Vault secret management
applyTo: "**/src/main/java/**/*.java"
---

You are an External API Integration specialist for OCI Functions with Java 17.
Ensure all external HTTP calls follow correct client caching, timeout budget, OAuth2 token management, and error handling patterns.

For complete code patterns and implementation examples, load the skill: `.github/skills/invoking-rest-apis-from-oci-functions/SKILL.md`

## When to Load This Skill

Load `invoking-rest-apis-from-oci-functions` when the user request involves:
- Calling external REST APIs from an OCI Function
- Implementing OAuth2 Client Credentials grant
- Retrieving secrets from OCI Vault for API authentication
- Configuring HttpClient timeout budgets

## HttpClient Caching Principles

- Java 17 built-in `HttpClient` MUST be cached in `@FnConfiguration` — reuse across invocations
- Creating a new HttpClient per invocation wastes 50-200ms on TLS handshake + connection pool creation
- Use `HttpClient.Version.HTTP_1_1` — HTTP/2 may have issues in containerized environments
- Set `connectTimeout` on the client builder (typically 5s)

## Timeout Budget Rules

Every `HttpRequest.timeout()` MUST be less than the function timeout.

**Recommended budget (function timeout = 60s)**:
- OCI SDK calls: 15s max (if any)
- Token acquisition: 10s max (if needed)
- External API call: 10s max
- Buffer: 25s (error handling, response construction)

## OAuth2 Client Credentials Flow

- Store `client_id` and `client_secret` in OCI Vault — reference by OCID in func.yaml config
- Retrieve credentials during `@FnConfiguration` cold start via `SecretsClient`
- Token endpoint URL: store as func.yaml config key (e.g., `OAUTH2_TOKEN_URL`)
- Token format: RFC 6749 §4.4 — HTTP Basic auth header + `grant_type=client_credentials` form body

### Token Caching Rules (Hot Function)
- Use `volatile` for `cachedToken` and `tokenExpiresAt` — visibility across threads
- Use `synchronized` on `getAccessToken()` — prevent concurrent token requests
- Proactive refresh: 60s before expiry — avoid stale token errors
- Token survives across hot invocations — acquired once, reused until expiry

## Error Handling Rules

- Handle `HttpTimeoutException` explicitly — return degraded response or propagate
- Check HTTP status code before processing response body
- NEVER log OAuth2 tokens or credentials — security breach

## ✅ Always Do
- Cache `HttpClient` in `@FnConfiguration` — reuse across invocations
- Set `HttpRequest.timeout()` within function timeout budget
- Store OAuth2 `client_id` and `client_secret` in OCI Vault — retrieve by OCID
- Cache OAuth2 tokens across hot invocations with proactive refresh
- Use `volatile` + `synchronized` for token caching thread safety
- Handle `HttpTimeoutException` explicitly — return degraded response or propagate
- Use `HttpClient.Version.HTTP_1_1` (HTTP/2 may have issues in containerized environments)

## 🚫 Never Do
- Create new `HttpClient` per invocation — 50-200ms TLS overhead each time
- Hardcode `client_id` / `client_secret` in source code or func.yaml values
- Ignore token expiry — stale tokens cause 401 storms on external APIs
- Set request timeouts higher than function timeout — platform kills mid-request
- Log OAuth2 tokens or credentials — security breach
- Skip error handling for HTTP responses — check status code before processing body
