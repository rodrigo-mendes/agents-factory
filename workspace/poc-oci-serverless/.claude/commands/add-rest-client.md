---
description: Add external REST API invocation capability to an existing OCI Function using Java 17 HttpClient and OCI SDK v3.x+
argument-hint: Target API, auth method (OAuth2/API Key/OCI signing/none), and existing function class
context: fork
agent: oci-functions-java
background: false
disable-model-invocation: true
---

Execute this task now for the OCI serverless project. Read the referenced skill below for the canonical patterns, gather the "Required information", then carry the task through to completion. If the target below is empty, ask for the required information before proceeding.

**Request / target (from the user):** $ARGUMENTS

# Add REST Client Integration

**Skill**: `invoking-rest-apis-from-oci-functions`

## What this does

Adds the ability to invoke external REST APIs (OCI services, other Functions, or third-party APIs) from an existing OCI Function, with proper HttpClient caching, auth, and timeout management.

## Required information

1. **Target API**: What API will be called? (URL or OCI service name)
2. **Auth method**:
   - OAuth2 Client Credentials
   - API Key (header-based)
   - OCI Request Signing (for OCI service APIs)
   - None (public API)
3. **Existing function class**: Which class to add the REST client to?
4. **HTTP methods**: Which operations? (GET, POST, PUT, DELETE)
5. **Secret management**: Are credentials stored in OCI Vault? (secret OCID)

## What will be generated

- Java 17 HttpClient with connection caching (hot function model)
- Auth handler (OAuth2 token management, API key injection, or OCI signing)
- Request/response serialization with proper error handling
- Timeout budget management (function timeout minus safety margin)
- OCI Vault secret retrieval (if credentials in Vault)
- Updated pom.xml with required dependencies
