# API Management Template

Structure-only template for the conditional **API Management Specifics** section of the research
output. Include it when `PLATFORM_CATEGORY=api-management`. It contains no vendor facts: fill every
`[placeholder]` from the official docs of `{{PLATFORM_SOFTWARE}} {{TARGET_VERSION}}`, cite each with a
URL and date, and mark anything without a source "(unverified)".

Modelled on:
- [output-format-base.md](../output-format-base.md) — section "API Management Specifics"
- [researching-api-gateway/blueprints/category-specifics.md](../../../../researching-api-gateway/blueprints/category-specifics.md) — section "§API Management Specifics"

---

## API Management Specifics

### 1. Control Plane vs Data Plane

| Plane | How it works | HA mechanism | Source |
|---|---|---|---|
| Control plane | [How routes/plugins are configured — database vs declarative] | [clustering/sync mechanism] | [URL] (DATE) |
| Data plane | [How requests are processed — proxy mode] | [independent scaling from control plane] | [URL] (DATE) |

**Chosen CP/DP topology**: [single-tier / CP-DP separated — rationale]

### 2. Config Model & Change Workflow

**Config model**: [database-backed / declarative (DB-less)]
**Change workflow**: [GitOps sync / admin API / CLI — audit trail]

```yaml
# Representative — adapt to your environment
# Source: [Official declarative config docs URL] (DATE)
[Minimal declarative config for a route + plugin]
```

### 3. Plugin / Filter Lifecycle & Execution Order

| Order | Plugin / Filter | Phase | Purpose | Source |
|---|---|---|---|---|
| 1 | [auth plugin] | [phase] | Authentication | [URL] (DATE) |
| 2 | [rate-limit plugin] | [phase] | Rate limiting | [URL] (DATE) |
| 3 | [transformation plugin] | [phase] | Transformation | [URL] (DATE) |

### 4. Rate-Limit Backend

| Backend | Accuracy in chosen topology | Config | Source |
|---|---|---|---|
| [memory / Redis / cluster] | [trade-off] | [config keys] | [URL] (DATE) |

### 5. Authentication

| Method | Plugin / Filter | Config example | Source |
|---|---|---|---|
| [JWT / OAuth2 / OIDC / mTLS / Key Auth] | [name] | [snippet] | [URL] (DATE) |

### 6. Developer Portal

[Whether included, edition required, how to configure] — Source: [URL] (DATE)

### 7. Multi-Tenancy & Admin API Access

- **Tenancy model**: [workspaces / teams / RBAC on the admin API]
- **Admin API exposure**: [network restriction applied]

### 8. Blue/Green & Canary Route Switching

[Mechanism for zero-downtime route updates] — Source: [URL] (DATE)

---

**Source**: [Official docs URL] (DATE)
