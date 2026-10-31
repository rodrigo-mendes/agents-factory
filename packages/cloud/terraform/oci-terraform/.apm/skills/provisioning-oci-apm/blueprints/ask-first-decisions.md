# Ask First Decisions — provisioning-oci-apm

6 architectural crossroads that require user confirmation before implementation.
These are **high freedom** decisions — do not assume; always present options and wait.

---

## Decision 1: Free Tier vs Paid APM Domain

⚠️ `is_free_tier` is **immutable** — wrong choice requires full domain recreation.

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| `is_free_tier = true` | Zero cost | Retention limits, trace cap, no SLA | Dev/test/PoC |
| `is_free_tier = false` | Full retention, higher volume, SLA | Ingestion cost | Production, compliance |

**Ask**: "Is this environment production or long-lived? Has APM trace ingestion cost been approved?"

---

## Decision 2: Vantage Point Type

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **Public VP** | Zero infra, global coverage | Cannot reach private endpoints | Public internet-facing URLs |
| **Dedicated VP (DVP)** | VCN-private access, customer IPs | RM stack + Streaming dependency, DVP instance cost | VCN-internal APIs, private DBs |
| **On-Premise VP** | Monitors inside on-prem networks | Worker infra management | Hybrid cloud, behind-firewall endpoints |

**Ask**: "Are the monitored endpoints public or internal? If internal, are they in OCI VCN (DVP) or on-premises (On-Premise VP)?"

**DVP prerequisite**: Requires pre-provisioned Resource Manager stack OCID (`dvp_stack_id`) and OCI Streaming stream (`dvp_stream_id`).

---

## Decision 3: Inline Monitor vs Script-Based Monitor

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **REST / BROWSER** (inline) | Simple HCL, no script mgmt | Limited test logic | URL health check, header/status validation |
| **SCRIPTED_REST (JS)** | Complex auth flows, multi-step | Script maintenance, JS in state | OAuth flows, JSON payload validation |
| **SCRIPTED_BROWSER (SIDE/JS)** | Full browser simulation | Execution limits, versioning | Login flows, SPA validation |
| **SCRIPTED_BROWSER (PLAYWRIGHT_TS)** | Typed tests, rich assertions | TypeScript build step | Complex UI workflows, accessibility |

**Ask**: "Does this monitor need to validate response body content, perform multi-step flows, or simulate user interaction? If scripted, what language does the team prefer?"

---

## Decision 4: Multi-Environment APM Domain Strategy

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **Separate domain per env** | Full isolation, independent key rotation | Higher cost, more state files | Production + regulated environments |
| **Single domain + compartments** | Lower cost, central view | Shared data keys, trace commingling risk | Dev-only, small teams |
| **Shared domain + naming convention** | Lowest resource count | Zero isolation | PoC only |

**Recommended**: Separate APM domain per environment boundary (dev / staging / prod).

**Ask**: "How many environments share this APM deployment? Do compliance requirements mandate trace data isolation between environments?"

---

## Decision 5: State Isolation Strategy

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **Directory per environment** | Full isolation, independent plan/apply, zero blast-radius crossover | Code duplication (mitigated by modules) | Production APM — domain recreation risk |
| **Terraform Workspaces** | Single codebase, dynamic naming | Shared backend bucket risk, `terraform.workspace` anti-patterns | Simple 2-env setups with identical config |
| **Terragrunt DRY** | Module reuse + per-env state isolation | External tool dependency | Teams already using Terragrunt |

**Recommended for APM**: Directory per environment. APM domain recreation is permanently destructive — workspace approaches sharing a backend bucket increase accidental cross-env apply risk.

**Ask**: "Does the team use Terragrunt? How many team members will run applies against production APM?"

---

## Decision 6: Apdex Rule Granularity

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **Single global catch-all** | Minimal config | One-size-fits-all thresholds | Uniform service latency profiles |
| **Per-service rules** | Accurate per-tier SLA tracking | More config resources, priority management | Mixed latency profiles (batch vs API vs UI) |
| **Per-operation rules** | Maximum granularity | Config sprawl, rule count approaching limit | Critical transactions (checkout, payment) |

**Ask**: "Do you have different SLA targets for different services or operations? What is the P95 latency target for each service tier?"
