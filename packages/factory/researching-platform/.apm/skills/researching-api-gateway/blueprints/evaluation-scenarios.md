# Evaluation Scenarios — researching-api-gateway

Cross-vendor coverage required: at least one Kong scenario AND at least one APISIX (or Tyk) scenario. This directly verifies the anti-Kong-bias goal of the refactoring.

---

## Scenario 1 — Kong on Kubernetes (KIC)

**Input**:
```
/researching-api-gateway Kong 3.7 deployment=kubernetes-operator depth=standard
```

**must_pass**:
- Recommends Kong Ingress Controller (KIC) for Kubernetes
- Documents DB-backed vs DB-less (declarative) config models with decK for GitOps
- Restricts Kong Admin API (port 8001) to internal network — flagged as CRITICAL
- Documents plugin execution phases (access phase for auth + rate-limiting)
- Rate-limit backend: local vs Redis vs cluster (Kong-specific)
- Includes `## API Management Specifics` section
- References `blueprints/references/kong-3.7.md`

**must_not**:
- Recommend exposing the Kong Admin API publicly
- Place rate-limiting before auth
- Omit the CP/DP separation discussion

---

## Scenario 2 — Apache APISIX on Kubernetes (anti-bias check)

**Input**:
```
/researching-api-gateway Apache APISIX 3.9 deployment=kubernetes-operator depth=standard
```

**must_pass**:
- Uses APISIX's own terminology and architecture: Route, Service, Upstream, Consumer, Plugin, etcd-backed config (APISIX uses etcd, NOT PostgreSQL)
- Documents apisix-ingress-controller for Kubernetes
- Documents APISIX plugins (not Kong plugins): `limit-req`, `limit-count`, `jwt-auth`, `key-auth`, `openid-connect`
- Notes APISIX stores config in etcd (fundamentally different from Kong's PostgreSQL/DB-less)
- Restricts APISIX Admin API + dashboard to internal network
- References `blueprints/references/apisix-3.9.md`

**must_not**:
- **Contain any `KONG_*` environment variable** (would prove Kong bias leaked)
- Reference `deck` (Kong's CLI) for APISIX — APISIX uses ADC or the Admin API
- Reference PostgreSQL as APISIX's config backend (it's etcd)
- Describe APISIX plugin phases using Kong's phase names

---

## Scenario 3 — Tyk on VM

**Input**:
```
/researching-api-gateway Tyk 5.3 deployment=vm depth=standard
```

**must_pass**:
- Uses Tyk terminology: API Definition, Gateway, Dashboard, Pump, Redis (Tyk requires Redis for distributed state)
- Documents that Tyk requires Redis for rate limiting, quotas, and analytics — architectural dependency
- Documents Tyk middleware chain (not Kong plugins)
- Documents Tyk Sync for GitOps
- References `blueprints/references/tyk-5.3.md`

**must_not**:
- Contain `KONG_*` env vars or Kong plugin names
- Omit the Redis dependency (critical for Tyk)

---

## Scenario 4 — Rate Limit Correctness

**Input**:
```
/researching-api-gateway Kong 3.7 (workload: hard rate limit across 5 gateway nodes)
```

**must_pass**:
- Rejects the local (in-memory) rate-limit backend for a hard limit across nodes
- Recommends the Redis backend (or cluster policy) for accurate distributed counting
- Explains that local backend would allow up to 5× the intended limit

---

## Scenario 5 — Admin API Security

**Input**:
```
/researching-api-gateway Kong 3.7 (question: how to expose the admin API for a remote team)
```

**must_pass**:
- Refuses to recommend public exposure of the raw admin API
- Recommends: RBAC + mTLS on the admin API, OR an authenticated proxy, OR Kong Manager with auth, OR GitOps (decK) instead of direct admin access
- Frames public admin API exposure as a CRITICAL anti-pattern
