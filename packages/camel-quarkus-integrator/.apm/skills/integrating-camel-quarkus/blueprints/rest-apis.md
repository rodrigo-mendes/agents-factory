# REST APIs Blueprint

Back to [SKILL.md](../SKILL.md). Shared workflow, structure skill and boundaries live there; this file holds only the inbound-HTTP specialty.

## Specializations

1. **REST endpoints**: `rest()` DSL verbs, JSON binding, status codes, error mapping, content negotiation.
2. **API documentation**: contract-first or code-first OpenAPI.
3. **Uploads and downloads**: multipart uploads on platform-http.

## Required Skills

| Need | Skill |
|---|---|
| Always | `developing-camel-quarkus-core-v3-40`, `structuring-camel-quarkus-projects` |
| Any inbound HTTP | `developing-camel-quarkus-platform-http-v3-40` |
| REST DSL, binding, OpenAPI, CORS, validation | `developing-camel-quarkus-rest-v3-40` |
| User chooses Jakarta REST resources (Ask First) | `developing-quarkus-rest-v3-40` |
| Uploaded files saved or forwarded | `developing-camel-quarkus-file-v3-40` |
| XML bodies | `developing-camel-quarkus-jaxb-v3-40` |

## What to Ask

- Operations (verbs, paths, request and response bodies); do they come from an existing OpenAPI document?
- Allowed callers and origins (CORS), and whether the API must be public.
- Upload limits (extensions, size), if files are received.

## Ask First Decisions

| Decision | Options | Source |
|---|---|---|
| Contract-first vs code-first OpenAPI | `rest().openApi()` vs REST DSL + OpenAPI extension | Ask First in the REST skill |
| REST DSL vs Quarkus REST resource calling a `ProducerTemplate` | Camel-owned API vs existing JAX-RS layer; coexistence on one server is unverified | Ask First in the platform-http, core and `developing-quarkus-rest-v3-40` skills |
| Request validation level | Headers/params/body parse vs schema validation | Ask First "Request validation" in the REST skill |
| CORS policy | Quarkus filter vs Camel `enableCORS` | Ask First "CORS" in the REST skill |
| Authentication method | No installed skill covers authentication; see [Out of Scope](../SKILL.md#out-of-scope) | User |
| Versioning and rate limiting | No installed skill covers them; ask, then decide whether to proceed without | User |

## Quality Standards

### ✅ Always Do

- **One `direct:` hand-off per operation**; the REST route only receives, binds, and delegates (boundaries matrix in SKILL.md).
- **Restrict methods and whitelist upload extensions** on every consumer (platform-http skill, Always Do).
- **Enable JSON binding explicitly** and set the HTTP server through `quarkus.http.*`, not Camel (REST skill, Always Do).
- **Provide an OpenAPI document** when the API is public or shared (team convention; mechanics in the REST skill).

### ⚠️ Ask First

- **Authentication and authorization**: out of scope; ask before leaving the API open.
- **Allowed origins** before enabling CORS; do not ship Camel's default CORS (`*`) to production, use explicit origins (medium confidence; REST skill, Ask First "CORS", unversioned manual).
- **Upload size and temp-file policy** before accepting uploads.

### 🚫 Never Do

- **Never configure HTTPS with `SSLContextParameters` on the server.** Instead: Quarkus TLS registry (platform-http skill).
- **Never use hyphens or `$` in path parameter names.** Instead: camelCase names (REST skill, Never Do).
- **Never accept unrestricted uploads.** Instead: method restriction, extension whitelist, body limits.
