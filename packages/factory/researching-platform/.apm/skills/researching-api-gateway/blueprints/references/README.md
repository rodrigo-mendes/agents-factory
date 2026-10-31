# Reference Index — researching-api-gateway

Index of the official sources and documentation categories already named in this skill's
[SKILL.md](../../SKILL.md) and blueprints. It adds no new facts.

> **Status:** no per-vendor reference cards (`<vendor>-<version>.md`) exist in this folder yet.
> Create them from the [reference card template](../../../researching-platform-software/blueprints/shared/reference-card-template.md)
> (worked example: [reference-card-example-kafka-3.7.md](../../../researching-platform-software/blueprints/shared/reference-card-example-kafka-3.7.md)).

## Official Sources (from SKILL.md → External Resources)

> Entries are copied verbatim. SKILL.md records no fetch date for any of them, so each is
> **(unverified)** until a dated fetch is recorded in a vendor reference card.

| Gateway | Primary Docs | K8s Ingress/Operator | Release Notes | Status |
|---|---|---|---|---|
| Kong Gateway | docs.konghq.com | Kong Ingress Controller (KIC) | docs.konghq.com/gateway/changelog | (unverified) |
| Apache APISIX | apisix.apache.org/docs | apisix-ingress-controller | github.com/apache/apisix/releases | (unverified) |
| Tyk | tyk.io/docs | Tyk Operator | github.com/TykTechnologies/tyk/releases | (unverified) |
| Traefik Enterprise | doc.traefik.io/traefik-enterprise | Traefik Hub / Proxy | doc.traefik.io/traefik/observability | (unverified) |
| KrakenD | krakend.io/docs | KrakenD Helm chart | github.com/krakend/krakend-ce/releases | (unverified) |
| Envoy Gateway | gateway.envoyproxy.io | Envoy Gateway (Gateway API) | github.com/envoyproxy/gateway/releases | (unverified) |

## Documentation Categories

Categories this skill expects each vendor's docs to cover, taken from the headings of
[category-specifics.md](../category-specifics.md):

- Control Plane / Data Plane Separation (Vendor-Neutral)
- Request Processing Phases (Neutral Model)
- Rate Limiting Backends (Neutral)
- Authentication Patterns (Neutral)
- Declarative / GitOps Config Pattern
- Blue/Green & Canary Route Switching
- Neutral KPIs
- Universal Anti-Patterns
- §API Management Specifics (always emit for this sibling)
- Ecosystem Adjacencies

## Shared Sources

- [output-format-base.md](../../../researching-platform-software/blueprints/shared/output-format-base.md) — output skeleton; every claim cites an official docs URL with a date
- [research-scope-operations.md](../../../researching-platform-software/blueprints/shared/research-scope-operations.md) — shared research scope §1–§12
- [deployment-guides/](../../../researching-platform-software/blueprints/shared/deployment-guides/) — per-`DEPLOYMENT_MODEL` playbooks
- [evaluation-scenarios.md](../evaluation-scenarios.md) — behavioral test cases for this skill
