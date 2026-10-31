---
name: provisioning-oci-event-driven-pubsub
description: "Provisions the complete OCI event-driven pub/sub Terraform stack: Streaming (PUBLIC pool + Stream), Service Connector Hub (N connectors for fan-out), Functions consumer apps, and IAM ordering. Use when implementing the event-driven pub/sub pattern (02-event-driven) or any combination of Streaming + SCH + Functions. Cross-references provisioning-oci-streaming, provisioning-oci-connector-hub, and provisioning-oci-functions."
---

## Version Context

**Technology**: Terraform oracle/oci >= 6.0, < 9.0 (tested with v8.x)
**Terraform version**: >= 1.5 (project minimum per `infra/environments/*/versions.tf`)
**Pattern delivered**: event-pubsub — handoff evidence: `workspace/poc-oci-serverless/docs/handoff/event-pubsub/` (read-only reference)
**Modules implemented**:
- `infra/modules/streaming/` — Stream Pool + Stream
- `infra/modules/service-connector/` — N connectors via `for_each`
- `infra/modules/function-app/` — Functions Application + Function resource
- `infra/modules/iam/` — streaming policy (producer + SCH verbs)

**Key provider constraints**:
- `private_endpoint_settings` on `oci_streaming_stream_pool` is **optional+computed** — removing from HCL is a NO-OP; pool must be force-replaced to actually change endpoint type
- `provisioned_concurrency_config` on `oci_functions_function` is **optional+computed** — same trap; plain apply is a no-op; use `terraform apply -replace='<resource>'` to actually change it
- SCH `Sources` with private endpoints are immutable — connector must be recreated if pool is recreated

⚠️ **CRITICAL — Agent Warning**:
This skill composes multiple provisioning skills. Before generating any Terraform, load the cross-referenced skills for their specific resource patterns:
- `provisioning-oci-streaming` — Stream Pool + Stream resource patterns, immutability rules
- `provisioning-oci-connector-hub` — SCH resource patterns, IAM ordering, batch tuning
- `provisioning-oci-functions` — Function Application + Function resource patterns

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — Mandatory composition patterns
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — PUBLIC vs PRIVATE pool, cursor strategy, batch tuning
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — Composition anti-patterns, immutability traps
- **[Integration Patterns](./blueprints/integration-patterns.md)** — Complete HCL examples for the full stack
- **[Verification Loop](#verification-loop)** — Post-apply validation commands
- **[Module Architecture](#module-architecture)** — Module composition diagram
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — Canonical, edge, and misuse test cases

---

## Module Architecture

```
infra/
├── modules/
│   ├── streaming/          # Stream Pool + Stream (provisioning-oci-streaming)
│   │   ├── main.tf
│   │   ├── variables.tf    # pool_type, partitions, retention_in_hours
│   │   └── outputs.tf      # stream_id, messages_endpoint, kafka_bootstrap_servers
│   │
│   ├── service-connector/  # N SCH connectors via for_each (provisioning-oci-connector-hub)
│   │   ├── main.tf         # for_each = var.connectors
│   │   ├── variables.tf    # stream_id, connectors map, cursor_kind, batch params
│   │   └── outputs.tf      # connector_ids map
│   │
│   ├── function-app/       # Application + Function resources (provisioning-oci-functions)
│   │   ├── main.tf
│   │   └── variables.tf    # memory_in_mbs, timeout_in_seconds, provisioned_concurrency
│   │
│   └── iam/                # Dynamic groups + policies
│       ├── main.tf         # streaming_policy with 4 required verbs
│       └── outputs.tf      # policy_id (for depends_on in SCH module)
│
└── environments/dev/
    ├── apps.tf             # module.streaming + module.service_connector + module.app_*
    └── main.tf             # module.iam + module.network
```

**Dependency graph** (must apply in this order or with correct `depends_on`):

```
module.iam (streaming policy)
    ↓ (depends_on enforced via var.iam_dependencies in SCH module)
module.streaming (pool + stream)
    ↓ (stream_id output)
module.service_connector (N SCH connectors)
    ↓ (function_id inputs)
module.app_evt_consumer_* (consumer Function Applications)
```

---

## Blueprints & Guardrails

### ✅ Always Do

For complete patterns with HCL, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**Mandatory patterns**:
- **IAM before SCH activation** — `depends_on = [var.iam_dependencies]` in `oci_sch_service_connector`; a connector without policies enters FAILED and silently drops all data
- **PUBLIC pool when SCH is source** — omit `private_endpoint_settings` block; SCH is Oracle-managed and cannot reach private VCN endpoints
- **`prevent_destroy = true` on stream** — partitions and retention are immutable; accidental destroy loses all buffered events; force users to explicitly plan the migration
- **`for_each` on SCH connectors** — one connector per consumer; `var.connectors` map enables adding consumers without changing module structure
- **Batch tuning on SCH Functions target** — tune `batch_size_in_kbs` and `batch_time_in_sec` to workload; defaults cause either cold-start storms or excessive latency
- **All four IAM verbs in streaming policy** — stream-push (producer DG), STREAM_READ+STREAM_CONSUME (serviceconnector), fn-function (serviceconnector), fn-invocation (serviceconnector)
- **Consumer memory >= 1024 MB + timeout = 300 s** — minimum for JVM cold start to complete within SCH sync deadline

### ⚠️ Ask First

For complete decision matrices, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

**Decision points**:
- **PUBLIC vs PRIVATE pool** — PUBLIC when SCH is source; PRIVATE only for in-VCN-only clients
- **Cursor strategy** — LATEST (real-time) vs TRIM_HORIZON (replay + idempotency required)
- **Batch tuning values** — batch_size_in_kbs and batch_time_in_sec depend on event volume and latency tolerance
- **Provisioned concurrency** — ask if zero cold-start is required; minimum is count=10 per function (not 1); costly

### 🚫 Never Do

For complete anti-patterns, see [Never Do Patterns](./blueprints/never-do-patterns.md).

**Prohibited patterns**:
- **Private pool for SCH source** — SCH cannot reach private endpoints; the existing `provisioning-oci-streaming` skill's "always private" guidance is CORRECT for in-VCN-only clients and INCORRECT for SCH source — reconcile by choosing PUBLIC when SCH is involved
- **Removing `private_endpoint_settings` as a plain apply** — optional+computed; NO-OP; must use `-replace`
- **Setting `provisioned_concurrency = 1`** — rejected by OCI API; minimum is 10; plain apply with count=0 is also a no-op (optional+computed)
- **Single SCH connector for multiple consumers** — not possible; one target per connector
- **Missing `prevent_destroy` on stream** — immutable partitions+retention; accidental plan shows destroy without data-loss warning

---

## Verification Loop

Run after every `terraform apply` touching Streaming, SCH, or Functions consumers.

### 1. Stream Pool Endpoint Type
```bash
oci streaming admin stream-pool get \
  --stream-pool-id <POOL_OCID> \
  --query 'data.{"endpoint":"endpoint-fqdn","private-ep":"private-endpoint-settings","state":"lifecycle-state"}'
# Expected: state=ACTIVE, private-ep=null (PUBLIC pool), endpoint contains "cell-1.streaming..."
```

### 2. SCH Connectors ACTIVE
```bash
oci sch service-connector list \
  --compartment-id <COMP_OCID> \
  --query 'data[].{"name":"display-name","state":"lifecycle-state","details":"lifecycle-details"}'
# Expected: all connectors ACTIVE, details empty
```

### 3. IAM Verb Audit (streaming policy must have all four verbs)
```bash
oci iam policy list \
  --compartment-id <COMP_OCID> \
  --name policy-streaming-<env> \
  --query 'data[0].statements'
# Expected: stream-push, STREAM_READ, STREAM_CONSUME, fn-function, fn-invocation all present
```

### 4. Smoke Test + Fan-Out Proof
```bash
# Publish a test event
curl -s -X POST https://<apigw-hostname>/v1/events \
  -H 'Content-Type: application/json' \
  -d '{"event_type":"smoke.test","payload":{"id":"SMOKE-1"},"correlation_id":"smoke-001"}'
# Expected: 202 with event_id

# Wait 5-10 minutes (SCH poll interval), then check consumer logs
oci logging search log-entries \
  --search-query 'search "<LOG_GROUP_OCID>" | message like "%event_id=<EVENT_ID>%" | sort by datetime desc' \
  --time-start <T-10min ISO8601> --time-end <now ISO8601>
# Expected: >= 2 log entries (one per consumer) containing the same event_id
```

### 5. SCH Metrics (both connectors healthy)
```bash
oci monitoring metric-data summarize-metrics-data \
  --compartment-id <COMP_OCID> \
  --namespace oci_service_connector_hub \
  --query-text 'ErrorsAtSource[5m].sum()'
# Expected: 0

oci monitoring metric-data summarize-metrics-data \
  --compartment-id <COMP_OCID> \
  --namespace oci_service_connector_hub \
  --query-text 'ErrorsAtTarget[5m].sum()'
# Expected: 0
```

**Troubleshooting**:
- `ErrorsAtSource > 0` → pool is PRIVATE or missing STREAM_READ/STREAM_CONSUME verbs; check pool `private-endpoint-settings`
- `ErrorsAtTarget > 0`, zero function logs → missing `fn-function` verb; add it and re-apply
- `ErrorsAtTarget > 0`, function logs show `Received` then 60 s then 444 → memory < 1024 MB or timeout < 300 s; update both
- SCH connector in FAILED immediately after apply → IAM policy not created before connector or wrong compartment scope
- `terraform plan` shows no change after removing `private_endpoint_settings` → optional+computed trap; use `terraform apply -replace='module.streaming.oci_streaming_stream_pool.this'`

---

## Quick Reference

### Resource Reference

| Resource | Module | Key Variables |
|----------|--------|--------------|
| `oci_streaming_stream_pool` | `streaming` | No `private_endpoint_settings` (PUBLIC) |
| `oci_streaming_stream` | `streaming` | `partitions` (immutable), `retention_in_hours` (immutable), `prevent_destroy = true` |
| `oci_sch_service_connector` | `service-connector` | `for_each = var.connectors`, `depends_on = [var.iam_dependencies]`, `cursor_kind` |
| `oci_identity_policy` (streaming) | `iam` | 4 verbs: stream-push, STREAM_READ+STREAM_CONSUME, fn-function, fn-invocation |
| `oci_functions_application` | `function-app` | Consumer: `memory_in_mbs = 1024`, `timeout_in_seconds = 300` |

### IAM Policy Template
```hcl
statements = [
  "Allow dynamic-group ${dg_functions} to use stream-push in compartment ${compartment_name}",
  "Allow any-user to {STREAM_READ, STREAM_CONSUME} in compartment ${compartment_name} where all {request.principal.type='serviceconnector'}",
  "Allow any-user to use fn-function   in compartment ${compartment_name} where all {request.principal.type='serviceconnector'}",
  "Allow any-user to use fn-invocation in compartment ${compartment_name} where all {request.principal.type='serviceconnector'}",
]
```

### Handling Optional+Computed Attributes
```bash
# private_endpoint_settings and provisioned_concurrency_config are optional+computed.
# Removing them from HCL is a NO-OP (provider leaves existing value as-is).
# To actually remove/change them:
terraform apply -replace='module.streaming.oci_streaming_stream_pool.this'
# Or for function:
terraform apply -replace='module.app_evt_consumer_notify.oci_functions_function.this'
# Review the plan carefully — replace cascades to dependent resources (stream, SCH connectors)
```

---

## External Resources

- [OCI Streaming: oci_streaming_stream_pool](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/streaming_stream_pool) (verified 2026-07-26)
- [OCI Streaming: oci_streaming_stream](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/streaming_stream) (verified 2026-07-26)
- [OCI SCH: oci_sch_service_connector](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/sch_service_connector) (verified 2026-07-26)
- [OCI Functions: Provisioned Concurrency](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsusingprovisionedconcurrency.htm) (verified 2026-07-26)
- [Cross-reference: provisioning-oci-streaming](../provisioning-oci-streaming/SKILL.md) (verified 2026-07-26)
- [Cross-reference: provisioning-oci-connector-hub](../provisioning-oci-connector-hub/SKILL.md) (verified 2026-07-26)
- [Cross-reference: provisioning-oci-functions](../provisioning-oci-functions/SKILL.md) (verified 2026-07-26)
- Handoff Evidence: `workspace/poc-oci-serverless/docs/handoff/event-pubsub/` (verified 2026-07-26)
- Pattern Spec: `workspace/poc-oci-serverless/docs/patterns/02-event-driven/02-event-driven-pub-sub.md` (verified 2026-07-26)
