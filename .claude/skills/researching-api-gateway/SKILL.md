---
name: researching-api-gateway
description: "Researches self-managed API gateways / API management platforms (Kong, Apache APISIX, Tyk, Traefik Enterprise, KrakenD, Envoy Gateway) into a hallucination-proof, version-absolute knowledge base covering installation, control-plane/data-plane HA, plugin/filter lifecycle, rate limiting, auth, and observability. Use when researching an API gateway the team will install and operate itself (not managed services like AWS API Gateway or Azure APIM)."
argument-hint: "<platform> <version> [deployment=bare-metal|vm|container-compose|kubernetes-operator|hybrid] [depth=exhaustive] [iterations=5] (e.g. Kong 3.7 deployment=kubernetes-operator / APISIX 3.9)"
context: fork
agent: framework-researcher
disable-model-invocation: true
---

# API Gateway Research

## INPUT VARIABLES

- `PLATFORM_SOFTWARE`: Kong Gateway | Apache APISIX | Tyk | Traefik Enterprise | KrakenD | Envoy Gateway
- `TARGET_VERSION`: exact semver
- `DEPLOYMENT_MODEL`, `RESEARCH_DEPTH`, `MAX_ITERATIONS`: standard passthrough

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)**
- **[Category Specifics](./blueprints/category-specifics.md)** — Neutral CP/DP, plugin lifecycle, rate-limit, auth patterns
- **[Reference Card Template](../../templates/platform-research/reference-card-template.md)** — Skeleton every per-vendor card follows (worked example: reference-card-example-kafka-3.7.md)
- **[Reference Cards](./blueprints/references/)** — Per-vendor pinned playbooks (kong, apisix, tyk, ...)
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)**
- **[Shared Output Template](../../templates/platform-research/output-format-base.md)**
- **[Shared Research Scope](../../templates/platform-research/research-scope-operations.md)**

## Blueprints & Guardrails

### ✅ Always Do

- **Read the vendor reference card first** — plugin/filter names, config keys, and admin API shapes are vendor-specific; never derive from memory
- **Separate control plane from data plane in the topology** — every gateway has this split; document HA of each independently
- **Restrict the admin/config API to internal networks** — the single most common critical misconfiguration
- **Document plugin/filter execution order** — auth must run before rate-limiting before transformation
- **State the rate-limit backend** — local (per-node, inaccurate in cluster) vs shared (Redis/distributed)

### ⚠️ Ask First

- **Config model** — database-backed vs declarative/GitOps (DB-less) — impacts HA and change workflow
- **Auth strategy** — Key/JWT/OAuth2/OIDC/mTLS — surface the options for the gateway
- **Deployment topology** — single-tier vs CP/DP separation — depends on scale and multi-cluster needs
- **`DEPLOYMENT_MODEL`** if unspecified

### 🚫 Never Do

| Anti-Pattern | Why Forbidden | Correct Alternative |
|---|---|---|
| Expose the admin/config API publicly | Full control of all routes/plugins by anyone on the network | Restrict admin API to loopback / internal CIDR; front with auth proxy |
| Use local (per-node) rate-limit backend in a clustered gateway | Limits bypassed by routing to a different node | Use a shared backend (Redis / distributed counter) |
| Place rate-limiting before authentication in the filter chain | Unauthenticated requests consume rate-limit budget | Order: auth → rate-limit → transformation |
| Wildcard CORS on internal/credentialed APIs | Any origin can call with user credentials | Restrict allowed origins to known frontends |
| DB-less mode without a GitOps pipeline | Config drift across nodes; no audit trail | Pair declarative config with Git-based sync workflow |
| Copy one gateway's plugin config to another | Kong plugins ≠ APISIX plugins ≠ Tyk middleware | Use each gateway's own plugin/filter system from its reference card |

## Research Scope

Shared: **[research-scope-operations.md](../../templates/platform-research/research-scope-operations.md)** §1–§12.

API-gateway-specific: **[category-specifics.md](./blueprints/category-specifics.md)**.

## Output Format

Base: **[output-format-base.md](../../templates/platform-research/output-format-base.md)**.

Save as `research_platform_{{PLATFORM_SOFTWARE}}_v{{TARGET_VERSION}}.md` in `StoryBeat/docs/`.

Conditional sections:
- **§K8s Kubernetes Deployment Blueprint** — when `DEPLOYMENT_MODEL=kubernetes-operator`
- **§API Management Specifics** — always for this sibling (CP/DP, plugin lifecycle, auth, rate limit)
- Data Modeling NOT applicable

## External Resources

| Gateway | Primary Docs | K8s Ingress/Operator | Release Notes |
|---|---|---|---|
| Kong Gateway | docs.konghq.com | Kong Ingress Controller (KIC) | docs.konghq.com/gateway/changelog |
| Apache APISIX | apisix.apache.org/docs | apisix-ingress-controller | github.com/apache/apisix/releases |
| Tyk | tyk.io/docs | Tyk Operator | github.com/TykTechnologies/tyk/releases |
| Traefik Enterprise | doc.traefik.io/traefik-enterprise | Traefik Hub / Proxy | doc.traefik.io/traefik/observability |
| KrakenD | krakend.io/docs | KrakenD Helm chart | github.com/krakend/krakend-ce/releases |
| Envoy Gateway | gateway.envoyproxy.io | Envoy Gateway (Gateway API) | github.com/envoyproxy/gateway/releases |
