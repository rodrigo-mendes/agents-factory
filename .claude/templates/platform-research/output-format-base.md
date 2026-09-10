# Platform Software Research — Output Template

Save as `research_platform_{{PLATFORM_SOFTWARE}}_v{{TARGET_VERSION}}.md` in `StoryBeat/docs/`.

---

## Metadata

```yaml
Platform_Software: "{{PLATFORM_SOFTWARE}}"
Target_Version: "{{TARGET_VERSION}}"
Platform_Category: "{{PLATFORM_CATEGORY}}"
Datastore_Type: "{{DATASTORE_TYPE}}"          # required when Platform_Category=datastore; omit otherwise
Deployment_Model: "{{DEPLOYMENT_MODEL}}"
HA_Topology: "{{HA_TOPOLOGY}}"
Workload_Profile: "{{WORKLOAD_PROFILE}}"
Scale_Target: "{{SCALE_TARGET}}"
Official_Source_URL: "{{OFFICIAL_SOURCE_IF_KNOWN}}"
Output_Format: Markdown
Primary_Audience: Platform Engineers and Tech Leads
Research_Date: "[YYYY-MM-DD]"
Currency_Threshold: "[Date 12 months from research — review after this date]"
Research_Depth: "[quick/standard/deep/exhaustive]"
Max_Iterations: "[N]"
Research_Quality_Score: "[N%]"
# Research_Quality_Score = (total_claims - unverified - irresolvable) / total_claims * 100
Gap_Loop_Ran: "[true/false]"
Iterations_Used: "[N of MAX_ITERATIONS]"
Triangulated_Count: "[N]"
Unverified_Count: "[N]"
Irresolvable_Count: "[N]"
Conditional_Sections_Active: "[K8s / API-Management / Data-Modeling — list those applicable]"
```

---

## Executive Summary

[3 paragraphs:
1. What `{{PLATFORM_SOFTWARE}}` is, its core architectural model, and its primary role in the `{{PLATFORM_CATEGORY}}` space
2. What changed in `{{TARGET_VERSION}}` vs the previous stable — new features, config defaults changed, deprecated options, breaking changes
3. The three most critical operational guardrails for `{{WORKLOAD_PROFILE}}` on `{{DEPLOYMENT_MODEL}}`]

---

## Platform Glossary

10–20 terms from official `{{PLATFORM_SOFTWARE}} {{TARGET_VERSION}}` documentation:

```
Term: [Exact term from official docs]
Definition: [Exact meaning per TARGET_VERSION]
Source: [Official docs URL with section name]
Architect Usage: [How to apply this term in operational decisions]
Common Confusion: [What it is frequently confused with — especially cross-platform confusion]
```

> Confidence legend: 🟢 High (2+ official sources, dated ≤12mo) | 🟡 Medium (1 source or dated 12–24mo) | 🔴 Low (community source or dated >24mo)

---

## Operational Guardrails

### ✅ Mandatory Configs

**[Config Name]**
- Scope: [broker | instance | topic | cluster | node]
- Default ({{TARGET_VERSION}}): [value — cite exact source]
- Recommended for `{{WORKLOAD_PROFILE}}`: [value + rationale]
- Verification:
  ```bash
  # Representative — adapt to your environment
  [command to verify this config is applied]
  # Expected: [expected output]
  ```
- Source: [Official docs URL] (DATE)

### ⚠️ Topology Decisions

**[Decision Point]**
- Options:

  | Option | Topology | Optimizes | Sacrifices | Min Nodes | Best When |
  |--------|----------|-----------|------------|-----------|-----------|

- Failover: [Automatic vs manual — trigger condition]
- Split-brain risk: [Risk level and mitigation]
- Ask The Engineer: "[Specific question to ask before choosing]"
- Source: [Official docs URL]

### 🚫 Anti-Patterns

**[Anti-Pattern Name]**
- Risk Level: [CRITICAL | HIGH | MEDIUM]
- Why: [Security/Reliability/Data-loss reason — cite framework or official docs]
- ❌ Wrong:
  ```
  [Exact insecure/dangerous config or command — {{PLATFORM_SOFTWARE}}-specific]
  ```
- ✅ Correct:
  ```
  [Exact secure/correct config or command — {{PLATFORM_SOFTWARE}}-specific]
  ```
- Detection:
  ```bash
  # Representative — adapt to your environment
  [command to detect this anti-pattern]
  ```
- Impact: [Data breach | Data loss | Service outage | Cascading failure]
- Source: [Official security docs URL] (DATE)

---

## Installation & Bootstrap Blueprint

> Sub-sections by `DEPLOYMENT_MODEL`. Include only the relevant model(s), or all if `DEPLOYMENT_MODEL=hybrid`.

### Bare-Metal / VM / systemd

```bash
# Representative — adapt to your environment
# Step 1: Install
[Official package install command — deb/rpm/tar — with exact version pin]
# Source: [URL] (DATE)

# Step 2: Configure
[Minimal production config file with key params set]

# Step 3: Start & verify
[systemd unit start + health check command]
# Expected: [expected output]
```

### Container / Docker Compose

```yaml
# Representative — adapt to your environment
# Source: [Official image URL with TAG pinned to TARGET_VERSION] (DATE)
[Minimal docker-compose.yml for TARGET_VERSION — no 'latest' tag]
```

### Kubernetes Operator

```bash
# Representative — adapt to your environment
# Operator: [Official operator name and version]
# Helm chart: [Official helm chart repo URL] (DATE)
helm repo add [repo-name] [URL]
helm install [release-name] [chart] --version [EXACT_VERSION] -f values.yaml
```

```yaml
# Minimal Custom Resource (CR) for TARGET_VERSION
# Source: [operator docs URL] (DATE)
[Minimal CR YAML with required fields only]
```

> Full K8s operator guidance: [Kubernetes Deployment Blueprint](#kubernetes-deployment-blueprint)

---

## Configuration Reference

Top-20 parameters critical for `{{WORKLOAD_PROFILE}}` on `{{PLATFORM_SOFTWARE}} {{TARGET_VERSION}}`:

| Parameter | Scope | Default | Recommended | Unit | Source |
|-----------|-------|---------|-------------|------|--------|
| [param name] | [scope] | [default per TARGET_VERSION] | [recommended for WORKLOAD_PROFILE] | [unit] | [URL] (DATE) |

> ⚠️ All defaults are for `{{TARGET_VERSION}}`. Verify before applying to other versions.

---

## HA & Failover Topology

**Topology**: `{{HA_TOPOLOGY}}`

```
[ASCII diagram of the topology — nodes, roles, replication direction, client connection point]

Example (primary-replica):
  ┌─────────┐    sync/async    ┌─────────┐    ┌─────────┐
  │ Primary │ ──────────────► │ Replica │    │ Replica │
  └─────────┘                 └─────────┘    └─────────┘
       ▲
   writes + reads
```

**Failover Behavior**:
- Automatic failover trigger: [condition — e.g., "primary unreachable for > N seconds"]
- Failover duration (typical): [seconds/minutes]
- Client reconnection: [how clients detect and reconnect]
- Requires manual intervention when: [condition — e.g., "split-brain detected"]

**Split-Brain Mitigation**:
- Risk: [scenario that causes split-brain]
- Mitigation: [quorum requirement / STONITH / epoch-based leader election]
- Detection command:
  ```bash
  # Representative — adapt to your environment
  [command to detect split-brain]
  ```

**Quorum requirements**: [Minimum nodes for quorum — must be odd (3, 5, 7)]
**Source**: [Official HA docs URL] (DATE)

---

## Backup, Restore & PITR

**Backup Strategy**: [Logical vs Physical vs Snapshot — recommended for WORKLOAD_PROFILE]

### Backup Procedure

```bash
# Representative — adapt to your environment
# Tool: [Official backup tool name and version]
# Source: [Official backup docs URL] (DATE)
[Exact backup command with key flags]
# Expected output: [what success looks like]
```

### Restore Procedure

```bash
# Representative — adapt to your environment
# Source: [Official restore docs URL] (DATE)
[Exact restore command with key flags]
# Expected output: [what success looks like]
```

### Restore Verification

```bash
# Representative — adapt to your environment
[Command to verify data integrity post-restore]
# Expected: [checksum / record count / application health check]
```

**PITR** (Point-in-Time Recovery):
- Supported: [yes/no — cite source]
- Granularity: [seconds / transaction / checkpoint]
- Procedure: [link to official PITR docs]

**Typical RTO**: [minutes] | **Typical RPO**: [seconds/minutes — depends on backup frequency]
**Source**: [Official backup docs URL] (DATE)

---

## Upgrade & Migration Path

**Compatibility Matrix**:

| From Version | To Version | Direct Upgrade | Notes |
|---|---|---|---|
| [version range] | {{TARGET_VERSION}} | [Yes/No] | [breaking changes or prerequisites] |

**Rolling Upgrade Procedure** (for `{{HA_TOPOLOGY}}`):

```bash
# Representative — adapt to your environment
# Source: [Official upgrade docs URL] (DATE)
# Step 1: [Upgrade one node at a time — start with replica/follower]
# Step 2: [Verify node rejoins cluster]
# Step 3: [Repeat for remaining nodes]
# Step 4: [Upgrade primary/leader last]
[Exact commands per step]
```

**Rollback Trigger**: [Condition that warrants rollback — e.g., data corruption, quorum loss]
**Rollback Procedure**:
```bash
# Representative — adapt to your environment
[Exact rollback steps]
```

**Breaking Changes in `{{TARGET_VERSION}}`**: [List from official release notes with source URL]
**Source**: [Official upgrade docs URL] (DATE)

---

## Observability & KPIs

Critical metrics for `{{PLATFORM_SOFTWARE}} {{TARGET_VERSION}}` on `{{WORKLOAD_PROFILE}}`:

| Metric Name | Scope | Unit | Normal Range | Alert Threshold | Exporter |
|---|---|---|---|---|---|
| [exact metric name from exporter] | [broker/node/topic/index] | [unit] | [normal] | [alert when] | [prometheus exporter or native endpoint] |

> ≥ 8 metrics required. Use exact metric names from the official exporter or monitoring docs.

**Official Exporter**: [Name, version, and docs URL]
**Metrics endpoint**: [e.g., `:9090/metrics`, `:9644/metrics`, JMX exporter config]
**Source**: [Official monitoring docs URL] (DATE)

---

## Security Hardening Checklist

### Authentication & Authorization

- [ ] [Specific authn mechanism enabled — e.g., `requirepass`, `--auth`, `SASL_SSL`]
  - Config: `[param = value]`
  - Source: [URL] (DATE)
- [ ] [RBAC / ACL configured with least-privilege]
  - Config: `[param = value]`

### TLS / Encryption in Transit

- [ ] Client ↔ Broker/Server TLS enabled
  - Config: `[param = value]`
- [ ] Broker ↔ Broker (intra-cluster) TLS enabled (where supported)
  - Config: `[param = value]`
- [ ] Certificate rotation procedure documented
- Source: [Official TLS docs URL] (DATE)

### Encryption at Rest

- [ ] Data directory encrypted (OS-level: LUKS / dm-crypt / cloud KMS)
- [ ] Backup files encrypted
- Source: [URL] (DATE)

### Network Policy

- [ ] Platform port(s) accessible only from application subnet: `[ports list]`
- [ ] Management/admin port restricted to ops CIDR
- [ ] Replication ports firewalled between cluster nodes only

---

## Failure Modes & Runbooks

**[Failure Scenario Name]**
- Trigger: [Condition that causes this failure]
- Detection:
  ```bash
  # Representative — adapt to your environment
  [Command that reveals this failure]
  # Expected output indicating failure: [output]
  ```
- Immediate Response: [First action to take]
- Recovery Procedure:
  ```bash
  # Representative — adapt to your environment
  [Recovery commands in order]
  ```
- Prevention: [Config or architectural change that prevents recurrence]
- Source: [Official ops runbook or troubleshooting docs URL] (DATE)

> ≥ 3 failure scenarios required. Common ones: primary/leader node failure, disk full, network partition, replication lag spike, OOM kill.

---

## Ecosystem & Adjacent Tools

| Tool | Role | Compatibility | Official Docs |
|---|---|---|---|
| [companion tool name] | [what it adds] | `{{PLATFORM_SOFTWARE}} {{TARGET_VERSION}}` compatible: [yes/no] | [URL] (DATE) |

---

## Research Iteration Changelog

> Mandatory when `RESEARCH_DEPTH` is `standard`, `deep`, or `exhaustive`. Omit for `quick`.

| Iteration | Section | Item | Action | Source |
|---|---|---|---|---|
| 1 | [Section name] | [Claim or config] | Added / Resolved / Updated | [URL] (DATE) |
| 2 | [Section name] | [Claim or config] | ⚠️ IRRESOLVABLE — [one-line rationale] | — |

> Add one row per gap-loop resolution. `IRRESOLVABLE` rows remain permanently as an audit trail.

---

## Kubernetes Deployment Blueprint

> **Conditional section** — include when `DEPLOYMENT_MODEL=kubernetes-operator`. Full guidance in [deployment-guides/kubernetes-operator-guide.md](./deployment-guides/kubernetes-operator-guide.md).

**Official Operator**: [Name, version, and maintainer]
**Helm Chart**: [Official chart repo URL + exact chart version] (DATE)
**CRD / Custom Resource**:

```yaml
# Representative minimal CR for {{PLATFORM_SOFTWARE}} {{TARGET_VERSION}}
# Source: [operator docs URL] (DATE)
apiVersion: [operator-api-group/version]
kind: [CRKind]
metadata:
  name: [instance-name]
spec:
  version: "{{TARGET_VERSION}}"
  [minimal required fields]
```

**StatefulSet vs Operator trade-offs**:

| Aspect | StatefulSet (manual) | Operator |
|---|---|---|
| Upgrade | Manual rolling restart | Automated via CR |
| Backup | Custom scripting | Integrated (if supported) |
| Day-2 ops | High effort | Lower effort |
| Vendor lock-in | None | Operator-specific CRD |

**Storage Class**: [Recommended storage class for WORKLOAD_PROFILE — e.g., local-path, ceph-rbd, ebs-csi]
**PodDisruptionBudget**: [Minimum available pods during disruption]
**TopologySpreadConstraints**: [Spread across zones for HA]
**Rolling Upgrade via CR**: [Steps to update version field in CR]
**Source**: [Operator docs URL] (DATE)

---

## API Management Specifics

> **Conditional section** — include when `PLATFORM_CATEGORY=api-management`. Full guidance in [category-templates/api-management-template.md](./category-templates/api-management-template.md).

**Control Plane vs Data Plane**:
- Control plane: [How routes/plugins are configured — database vs declarative]
- Data plane: [How requests are processed — proxy mode]
- HA of control plane: [clustering/sync mechanism]
- HA of data plane: [independent scaling from control plane]

**Declarative Configuration**:
```yaml
# Representative — adapt to your environment
# Source: [Official declarative config docs URL] (DATE)
[Minimal declarative config for a route + plugin]
```

**Plugin Lifecycle & Order**: [Execution phase of each plugin type — access, rewrite, response]
**Rate-limit Backend**: [memory vs Redis vs cluster — trade-offs and config]
**Auth Plugins Available**: [JWT / OAuth2 / mTLS / Key Auth — with config example]
**Developer Portal**: [Whether included, how to configure]
**Blue/Green Route Switching**: [Mechanism for zero-downtime route updates]
**Source**: [Official docs URL] (DATE)

---

## Data Modeling

> **Conditional section** — include when `PLATFORM_CATEGORY=datastore`. Content driven by `DATASTORE_TYPE`. Full guidance in [data-modeling/modeling-{{DATASTORE_TYPE}}.md](./data-modeling/).

**Access-Pattern-First Principle**: All schema decisions must start from the documented `WORKLOAD_PROFILE` read/write patterns — not from the entity model.

### Logical → Physical Model

[Describe the schema / data model appropriate for `DATASTORE_TYPE` and `WORKLOAD_PROFILE`]

### Indexing Strategy

| Index Name | Type | Fields | Write Amplification | When to Use |
|---|---|---|---|---|
| [name] | [B-tree/GIN/HNSW/SSI] | [fields] | [low/medium/high] | [access pattern] |

### Partitioning / Sharding Strategy

- **Partition/Shard Key**: [field — rationale for low cardinality hotspot avoidance]
- **Cardinality**: [estimated distinct values]
- **Hot-key detection command**:
  ```bash
  # Representative — adapt to your environment
  [command to identify hot partitions/shards]
  ```

### Consistency Model Impact

- **Platform's consistency guarantee**: [strong / eventual / session / monotonic-read]
- **Modeling implications**: [idempotency requirements, read-your-writes pattern, conflict resolution]

### Schema Evolution

| Operation | Online? | Tool/Procedure | Risk |
|---|---|---|---|
| Add column/field | [yes/no] | [pg_repack / pt-osc / field versioning] | [low/medium/high] |
| Rename field | [yes/no] | [procedure] | [risk] |
| Change type | [yes/no] | [procedure] | [risk] |

### Modeling Anti-Patterns

| Anti-Pattern | DATASTORE_TYPE | Why Bad | Correct Alternative |
|---|---|---|---|
| [anti-pattern name] | [type] | [consequence] | [correct approach] |

> Full type-specific modeling guidance: [data-modeling/modeling-{{DATASTORE_TYPE}}.md](./data-modeling/)
> Source: [Official data modeling docs URL] (DATE)
