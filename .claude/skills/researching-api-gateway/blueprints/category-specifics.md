# API Gateway — Neutral Category Specifics

Patterns for API gateways / API management platforms. Vendor-specific plugin names, config keys, admin API shapes, and CLI live in `references/<vendor>-<version>.md`.

---

## Control Plane / Data Plane Separation (Vendor-Neutral)

Every API gateway distinguishes two planes:

| Plane | Responsibility | Stateful? |
|---|---|---|
| Control plane | Where routes, services, plugins, and consumers are configured | Holds config (DB or declarative file) |
| Data plane | Where live API traffic is proxied and policies enforced | Stateless proxy — scales horizontally |

Deployment models (neutral):

1. **Combined** — control and data plane in the same process (simplest; small scale)
2. **DB-backed** — data plane nodes read config from a shared database via the control plane
3. **Declarative / DB-less** — each data plane node loads config from a file (GitOps); no shared DB
4. **CP/DP split (enterprise)** — dedicated control plane cluster + independently scaled data plane clusters, often multi-region

For each chosen model, document:
- HA of the control plane (DB HA, or config-file distribution)
- HA of the data plane (stateless — front with L4/L7 load balancer)
- Config propagation latency (how long until a config change reaches all data planes)

---

## Request Processing Phases (Neutral Model)

Every gateway processes a request through ordered phases. Vendor terminology differs (Kong "plugins", APISIX "plugins", Tyk "middleware", Envoy "filters"), but the neutral order is:

```
1. TLS termination / certificate selection
2. Routing (match request to a route/service)
3. Rewrite (modify request path/headers before upstream)
4. Access control (authentication, authorization, ACL, rate limiting)
5. Upstream selection / load balancing
6. Response header manipulation
7. Response body manipulation
8. Logging / telemetry (async, after response)
```

**Critical ordering rule**: authentication MUST precede rate-limiting (so unauthenticated traffic doesn't consume rate budget), which MUST precede request transformation.

---

## Rate Limiting Backends (Neutral)

| Backend | Accuracy in cluster | Trade-off |
|---|---|---|
| Local (in-memory per node) | Inaccurate — each node counts independently; limit effectively N× | Lowest latency; only correct for single-node or sticky routing |
| Shared external store (e.g., Redis) | Accurate — all nodes share the counter | Adds a dependency + ~1ms latency per request |
| Distributed gossip / sync (enterprise) | Approximate — eventually consistent counters | No external dependency; slight overcount tolerated |

**Rule**: in any multi-node data plane, never use the local backend for a hard limit — it is bypassed by routing to a different node.

---

## Authentication Patterns (Neutral)

| Auth method | How it works | When to use |
|---|---|---|
| API Key | Client sends a key in header/query; gateway validates against consumer registry | Internal / partner APIs; simple |
| JWT | Gateway validates signature + claims (exp, iss, aud) against a configured key/JWKS | Stateless auth; OAuth2 resource server |
| OAuth2 / OIDC | Gateway integrates with an IdP; validates access tokens; may do token introspection | User-facing APIs with an identity provider |
| mTLS | Client presents a certificate; gateway validates against a CA | Service-to-service; zero-trust networks |
| HMAC / signature | Request signed with a shared secret; gateway verifies signature | Webhooks; high-integrity B2B |

Neutral hardening rules:
- Never accept credentials in query strings (logged in access logs) — header or body only
- Strip credentials before forwarding upstream (hide_credentials equivalent)
- Skip auth on CORS preflight (OPTIONS) only where the gateway supports it safely

---

## Declarative / GitOps Config Pattern

```
1. Config stored as version-controlled files (YAML/JSON) in Git
2. CI validates config on PR (syntax + policy checks)
3. On merge, a sync tool applies config to the gateway (control plane or each DB-less node)
4. Rollback = revert the Git commit + re-sync
```

Benefits: audit trail, review workflow, reproducibility. The reference card names the vendor's sync tool.

---

## Blue/Green & Canary Route Switching

Neutral pattern for zero-downtime API changes:

- **Blue/green**: two upstream targets; switch route to point at the new version atomically
- **Canary**: weighted routing — send X% of traffic to the new upstream, ramp up gradually
- **Header/consumer-based**: route specific consumers (internal testers) to the new version

The gateway's upstream/load-balancer config (reference card) implements these.

---

## Neutral KPIs

| Metric | Purpose | Alert When |
|---|---|---|
| Request rate (by route/service) | Traffic baseline | anomalous spike/drop |
| Latency p99 (gateway overhead + upstream) | Performance | > SLA |
| Error rate 5xx (by route) | Upstream health | > threshold |
| Error rate 4xx (by route) | Client / auth issues | spike may indicate attack or misconfig |
| Upstream latency | Backend health | > threshold |
| Rate-limit rejections | Throttling activity | spike may indicate abuse |
| Active connections | Load | approaching capacity |
| Plugin/filter execution time | Overhead per policy | slow plugin degrading all traffic |

---

## Universal Anti-Patterns

| Anti-Pattern | Consequence | Correct Alternative |
|---|---|---|
| Admin/config API publicly exposed | Full takeover of routing and policies | Bind admin API to loopback / internal CIDR; front with auth |
| Local rate-limit backend in cluster | Limit bypassed via node routing | Shared backend (Redis / distributed counter) |
| Rate-limit before auth | Unauthenticated traffic consumes budget | Order: auth → rate-limit → transform |
| Wildcard CORS on credentialed APIs | Any origin calls with user credentials | Explicit allowed-origin list |
| No request size limit | Large-payload DoS | Enforce max payload size |
| DB-less without GitOps | Config drift; no audit | Git-based declarative pipeline |
| Credentials in query string | Leaked in access logs / proxies | Header or body only; strip before upstream |
| No upstream health checks | Traffic sent to dead backends | Active + passive health checks configured |

---

## §API Management Specifics (always emit for this sibling)

Document, using the vendor reference card:
1. **CP/DP topology** chosen and HA of each
2. **Config model** (DB-backed vs declarative) and change workflow
3. **Plugin/filter execution order** for the required policies
4. **Rate-limit backend** and accuracy in the chosen topology
5. **Auth method(s)** with concrete config
6. **Developer portal** availability (if the platform offers one)
7. **Multi-tenancy** (workspaces / teams / RBAC on the admin API)

---

## Ecosystem Adjacencies

Neutral list (vendor names in reference cards):

- Declarative config / sync CLI (decK for Kong, ADC for APISIX, Tyk Sync)
- Admin/management UI
- Developer portal
- Ingress controller (for Kubernetes)
- Plugin/filter SDK for custom policies
- Observability exporters (Prometheus per vendor)
