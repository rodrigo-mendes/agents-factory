# HTTP Clients Blueprint

Back to [SKILL.md](../SKILL.md). Shared workflow, structure skill and boundaries live there; this file holds only the outbound-HTTP specialty.

## Specializations

1. **Outbound calls from routes**: `http:`/`https:` producers, status handling, timeouts, authentication, proxy forwarding.
2. **Enrichment**: calling an external API to add data to the exchange.
3. **Resilience**: circuit breaker with fallback on external calls.

## Required Skills

| Need | Skill |
|---|---|
| Always | `developing-camel-quarkus-http-v3-40`, `developing-camel-quarkus-core-v3-40`, `structuring-camel-quarkus-projects` |
| Call is a typed service API outside any route (user chooses) | `developing-quarkus-rest-v3-40` (Quarkus REST client) |
| Request or response XML | `developing-camel-quarkus-jaxb-v3-40` |
| Log requests and responses with masking | `developing-camel-quarkus-log-v3-40` |

## What to Ask

- Target URL, method, request and response formats.
- Authentication scheme the partner requires (Basic, Bearer, OAuth2 client credentials), and where secrets live.
- Latency budget and expected volume.
- What to do on failure: retry, fallback response, dead letter, fail to the caller.
- Whether the partner's TLS supports TLS 1.3.

## Ask First Decisions

| Decision | Options | Source |
|---|---|---|
| Timeouts and pools | Set all explicitly | Ask First in the HTTP skill |
| Status handling (medium confidence) | Throw and `onException` vs branch on response code | Ask First in the HTTP skill |
| 4xx/429 behavior (medium confidence) | Hidden `Retry-After` retry vs immediate failure | Ask First in the HTTP skill |
| TLS scope | Keep TLSv1.3 vs named TLS configuration for a legacy peer | Ask First in the HTTP skill |
| Camel `http` vs Quarkus REST client (medium confidence) | Route-embedded vs typed service API | Ask First in the HTTP skill |
| Circuit breaker | `circuitBreaker()` with `onFallback` on `camel-quarkus-microprofile-fault-tolerance`; configuration defaults are unverified, so set every option and test the timeout path | Always Do in the HTTP skill |

## Quality Standards

### ✅ Always Do

- **Reference the TLS registry bean explicitly on `https:` endpoints** when the bridge is used (HTTP skill, Always Do).
- **Use `camel-quarkus-microprofile-fault-tolerance` for circuit breakers** (HTTP skill).

### ⚠️ Ask First

- **Authentication scheme** and secret source (a secrets manager is out of scope) (medium confidence).
- **Credentials and API keys**: keep them in configuration placeholders, not in the URI string or in code (medium confidence; HTTP skill).
- **Retry and fallback strategy** before adding resilience.
- **Handling `HttpOperationFailedException` with `onException`** (medium confidence; the HTTP skill tags the throw semantics medium and the exception package unverified, so resolve its import in the IDE).
- **Proxy-style forwarding** of an inbound request (header leakage; see the HTTP skill).

### 🚫 Never Do

- **Never add `camel-quarkus-resilience4j`.** Instead: `camel-quarkus-microprofile-fault-tolerance`.
- **Never use OpenSSL-style cipher names or unknown protocols in `quarkus.tls.*`.** Instead: JSSE names in a named configuration (HTTP skill).
- **Never make an HTTP call without an error path.** Instead: `onException` or an explicit status check (team convention).
