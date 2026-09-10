# Reference Card Template

Canonical skeleton for a per-vendor, version-pinned reference card produced by any sibling of the
platform-software family. Every `researching-<family>/blueprints/references/<vendor>-<version>.md`
MUST follow this structure.

**How to use this template**
1. Copy this skeleton into `references/<vendor>-<version>.md` (filename encodes the exact version — Version Absolutism).
2. Fill every applicable section from **official documentation only**; cite each fact with a URL + access date.
3. Keep only the conditional sections that apply to this platform's category (see markers).
4. Anything you cannot verify from an official source → mark `⚠️ unverified` and record it in the sibling's Research Iteration Changelog.
5. A fully-worked instance of this template: [reference-card-example-kafka-3.7.md](./reference-card-example-kafka-3.7.md).

> Section legend: **[ALWAYS]** = required for every card · **[DATASTORE]** = only when the sibling is a datastore family · **[STREAMING]** = only for streaming/messaging brokers · **[API-GW]** = only for API gateways · **[K8S]** = only when a Kubernetes operator is in scope.

---

## `<Platform> <Version>` Reference Card   **[ALWAYS]**

Pinned facts for **`<Platform> <Version>.x`**. Imported by `researching-<family>` when
`PLATFORM_SOFTWARE=<Platform>` and `TARGET_VERSION` in `[<version>, <version>.x]`.

**Version snapshot**: `<version>` released `<YYYY-MM-DD>` (source: `<release-notes URL>`)

---

## Architecture / Topology Note   **[ALWAYS]**

- Core architectural model in this version (single-node / cluster / replica / ring / CP-DP split)
- What changed vs the previous stable version (new defaults, deprecated features, removed APIs)
- Default coordination / metadata mechanism (if any) and its status in this version
- Source: `<URL>` (DATE)

---

## Critical Configuration (top-20)   **[ALWAYS]**

| Parameter | Scope | Default (`<version>`) | Recommended | Unit | Source |
|-----------|-------|-----------------------|-------------|------|--------|
| `<key>` | `<broker/instance/topic/index/...>` | `<default>` | `<recommended + rationale>` | `<unit>` | `<URL>` (DATE) |

> All defaults pinned to `<version>`. Never carry a default across versions without re-verifying.

---

## HA Topology   **[ALWAYS]**

```
Minimum production cluster: <node count + roles>
Replication model: <sync / async / quorum> — <consistency guarantee>
Leader election / failover: <mechanism, trigger, duration>
Split-brain mitigation: <quorum size (odd) / fencing / epoch>
```

Source: `<HA docs URL>` (DATE)

---

## Backup, Restore & PITR   **[ALWAYS]**

- **Backup tool(s)**: `<official tool + version>`
- **Backup command**: `<exact command>`  → Source `<URL>` (DATE)
- **Restore command**: `<exact command>`
- **Restore verification**: `<integrity check>`
- **PITR**: supported? `<yes/no>`; granularity `<...>`; mechanism `<WAL/binlog/oplog archiving>`
- **Typical RTO / RPO**: `<values>`

---

## Upgrade Path to `<Version>`   **[ALWAYS]**

| From | Direct? | Notes / breaking changes |
|------|---------|--------------------------|
| `<prev>` | `<yes/no>` | `<protocol/data-format compatibility, prerequisites>` |

- **Rolling upgrade**: `<ordered steps>`
- **Rollback trigger + procedure**: `<condition → steps>`
- **Breaking changes in `<version>`**: `<list>` — Source `<release-notes URL>` (DATE)

---

## Observability — Metrics   **[ALWAYS]**

| Metric (exact name) | Type | Alert threshold |
|---------------------|------|-----------------|
| `<exact_metric_name>` | `<gauge/counter>` | `<alert when>` |

- **Exporter / endpoint**: `<name + port>`  — Source `<URL>` (DATE)
- ≥ 8 metrics required.

---

## Security Hardening   **[ALWAYS]**

- **Authentication**: `<mechanisms; default on/off in this version>`
- **Authorization**: `<RBAC/ACL model; least-privilege setup>`
- **TLS in transit**: `<client↔server; intra-cluster; min TLS version>`
- **Encryption at rest**: `<native? or OS-level>`
- **Network**: `<ports + which must be restricted>`
- Source: `<security docs URL>` (DATE)

---

## Data Modeling specifics   **[DATASTORE]**

- Physical model constraints for this version (size limits, key/partition rules, index types available)
- Schema-evolution / online-migration tooling + limits
- Version-specific modeling gotchas
- Cross-reference: `researching-<family>/blueprints/data-modeling.md` for the neutral guidance
- Source: `<URL>` (DATE)

---

## Delivery / Messaging specifics   **[STREAMING]**

- Supported delivery guarantees (at-most / at-least / exactly-once) + exact config to achieve each
- Ordering guarantees and partition/key model
- Consumer-group / subscription model + offset storage
- Dead-letter mechanism
- Source: `<URL>` (DATE)

---

## API Management specifics   **[API-GW]**

- Config model (DB-backed vs declarative) + sync tool
- Plugin/filter execution order for auth → rate-limit → transform
- Rate-limit backend options + accuracy in cluster
- Auth methods with concrete config
- Admin/config API hardening (never public)
- Source: `<URL>` (DATE)

---

## Kubernetes Operator   **[K8S]**

- **Operator**: `<name + version compatible with this platform version>`
- **Helm chart**: `<repo URL + chart version>` (DATE)
- **CRDs**: `<list>`
- **Minimal Custom Resource**:

```yaml
# Minimal functional CR for <Platform> <Version>
# Source: <operator docs URL> (DATE)
<minimal CR>
```

- Storage class / PVC guidance, PDB, topology spread — see [deployment-guides/kubernetes-operator-guide.md](./deployment-guides/kubernetes-operator-guide.md)

---

## Ecosystem (`<version>`-compatible)   **[ALWAYS]**

| Tool | Purpose | Compatibility | Source |
|------|---------|---------------|--------|
| `<tool>` | `<what it adds>` | `<version range>` | `<URL>` (DATE) |

---

## Known Issues in `<version>`   **[ALWAYS]**

- Check the official issue tracker for blockers fixed in later patch releases before recommending this exact version.
- `<list any known blocker + tracker URL>`
