# Ask First Decisions — AWS Lambda Serverless Architecture

**Tier**: Complex | **Source**: Lambda Developer Guide, accessed 2026-07-31

Confirm these decisions with the architect before committing to an implementation. Each has material trade-offs.

---

## Decision 1 — Packaging: .zip archive vs container image

**Source**: [Lambda quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html)

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| **.zip archive** (≤ 50 MB zipped / 250 MB unzipped, ≤ 5 layers) | Fast deploys, layer sharing, simplicity | 250 MB unzipped ceiling | Standard functions, shared deps via layers |
| **Container image** (up to 10 GB ECR, uncompressed) | Large ML models, existing container tooling, binary size | Slower cold start, ECR lifecycle management | Deps > 250 MB, ML inference, container CI/CD already established |

**Cost profile**: Runtime cost is comparable; container adds ECR storage cost.

**Question to ask**: "Do your dependencies exceed 250 MB unzipped, or do you have an existing container pipeline that must be reused? If neither, prefer .zip + Lambda Layers."

---

## Decision 2 — Cold-start strategy: none vs SnapStart vs Provisioned Concurrency

**Sources**: [SnapStart GA](https://aws.amazon.com/blogs/aws/aws-lambda-snapstart-for-python-and-net-functions-is-now-generally-available/) · [Lambda pricing](https://aws.amazon.com/lambda/pricing/)

| Option | Mechanism | Optimizes | Sacrifices | Best when |
|---|---|---|---|---|
| **On-demand (no mitigation)** | Default | Lowest cost — pure pay-per-use | Tail latency on cold starts | Async/batch workloads, latency-tolerant |
| **SnapStart** | Firecracker snapshot restore — Java 11+, Python 3.12+, .NET 8+ | Sub-second starts, no idle charge | Cache+restore charges; entropy/uniqueness caveats; not all runtimes | Spiky latency-sensitive traffic on supported runtimes |
| **Provisioned Concurrency** | Pre-initialized environments kept warm | Zero cold start for the reserved count | Idle charge even when unused | Predictable, sustained low-latency traffic |
| **Provisioned Concurrency + Application Auto Scaling** | Scheduled/target-tracking PC | Warm capacity aligned to demand curve | Configuration complexity | Known daily/weekly traffic shape |

**Cost order**: On-demand < SnapStart (usage-based restore) < Provisioned Concurrency (idle charge).

**SnapStart caveats**:
- Requires idempotent initialization (uniqueness/entropy: re-seed random generators in the `AfterRestore` hook).
- Incurs snapshot cache charges and restore charges per invocation.
- Not available for all runtimes or all regions — verify availability.

**Question to ask**: "What is the p99 latency SLO, and is traffic pattern spiky or steady? On a supported runtime, prefer SnapStart for spiky; Provisioned Concurrency for steady sustained-low-latency."

---

## Decision 3 — CPU architecture: arm64 (Graviton) vs x86_64

**Source**: [Lambda runtimes](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html)

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| **arm64 (Graviton)** | Lower price and often better price-performance; ~20% cost reduction vs x86_64 | Native deps must be rebuilt for ARM; AVX2 instructions unavailable | Greenfield workloads, compiled deps rebuildable, cost-sensitive |
| **x86_64** | Maximum binary/ISV compatibility | Higher unit price | x86-only native binaries, AVX2 workloads, legacy ISV software |

**Note**: All supported runtimes offer both architectures. For pure Python/Node.js/JVM workloads with no native extensions, arm64 is the default recommendation.

**Question to ask**: "Do any native dependencies (C extensions, shared objects, AVX2 instructions) pin you to x86_64? If not, default to arm64."

---

## Decision 4 — Concurrency control: unreserved vs reserved vs provisioned

**Source**: [Lambda quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html) · [Best practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| **Unreserved (shared pool)** | Simplicity, full elasticity | No protection for fragile downstreams; noisy-neighbor risk within the account | Independent functions, elastic downstreams |
| **Reserved concurrency** | Caps a function; protects downstream (RDS, rate-limited API) from being overwhelmed; free | Can cause throttling if set too low; draws from shared account pool | DB-backed functions, rate-limited third-party APIs |
| **Provisioned concurrency** | Eliminates cold start for the pre-initialized count | Idle cost (pays even when not serving traffic) | Latency-critical sync endpoints |

**Account default**: 1,000 concurrent executions (increasable via Support). Reserving concurrency on one function reduces the pool available to all others in the account.

**Burst scaling**: 1,000 new environments per 10 seconds, then +500/minute.

**Question to ask**: "What is the throughput ceiling (requests/sec) of the slowest downstream dependency? Set reserved concurrency to match that limit, not Lambda's capability."

---

## Decision 5 — Orchestration: Step Functions vs EventBridge vs direct async

**Sources**: [Serverless Lens — Design principles](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/general-design-principles.html) (⚠️ 2022-07) · [Best practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)

| Option | Service | Optimizes | Sacrifices | Best when |
|---|---|---|---|---|
| **State machine** | AWS Step Functions | Visibility, built-in retries, compensation (saga), human-in-loop, execution history | Per-state-transition cost | Multi-step workflows, sagas, long-running orchestration |
| **Event bus / router** | Amazon EventBridge | Loose coupling, fan-out to multiple consumers, schema registry | Eventual consistency, no workflow visibility | Event-driven microservices, integrations, decoupled side effects |
| **Direct async invoke** | Lambda Event type + Destinations | Lowest overhead | No workflow visibility, limited retry control | Simple fire-and-forget with DLQ; point-to-point async |

**Design principle (Serverless Lens)**: "Orchestrate your application with state machines, not functions." — Avoid hand-coding retries and state in Lambda.

**Question to ask**: "Is this a multi-step workflow that needs retry/compensation and execution history (Step Functions), or a broadcast event that multiple consumers react to (EventBridge), or a simple one-shot async call (direct + DLQ)?"

---

## Decision 6 — Networking: VPC-attached vs non-VPC

**Sources**: [Lambda quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html) · [Lambda security](https://docs.aws.amazon.com/lambda/latest/dg/lambda-security.html)

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| **Non-VPC** | Simplicity; internet egress via Lambda-managed network; no ENI management | Cannot reach private-subnet resources directly | Function only calls public AWS service endpoints or HTTPS APIs |
| **VPC-attached** | Can reach private RDS, ElastiCache, internal services | ENI management; potential cold-start/scaling impact; NAT Gateway required for internet egress | Must reach private-subnet resources |

**Key gotchas**:
- ENIs per VPC quota: **500** (shared with EFS mount targets) — increasable.
- Private-subnet Lambda functions need a **NAT Gateway** (in a public subnet) for internet egress; VPC endpoints for AWS services (DynamoDB, S3, SQS) avoid NAT charges.
- Modern Lambda VPC connectivity uses Hyperplane ENIs (pre-provisioned, lower cold-start impact than older per-function ENIs).

**Question to ask**: "Does the function need to reach resources in a private subnet (RDS, ElastiCache, internal ALB)? If it only calls public endpoints, skip the VPC to avoid ENI complexity."

---

## Decision 7 — HTTP front door: API Gateway vs ALB vs Function URL

**Source**: [Lambda Developer Guide — Lambda function URLs](https://docs.aws.amazon.com/lambda/latest/dg/urls-configuration.html) · [Lambda quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html)

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| **API Gateway (REST or HTTP API)** | Throttling, auth (Cognito, Lambda authorizer), usage plans, WAF integration, request validation | Cost per million calls + data transfer; config surface area | Public/managed APIs requiring governance, rate limiting, API keys |
| **Application Load Balancer** | Existing ALB stacks, host/path-based routing to multiple targets | No usage plans or API keys; no native API schema | Migrating containerized/EC2 apps to Lambda; existing ALB already in use |
| **Function URL** (built-in HTTPS endpoint) | Simplest configuration; IAM or no-auth options; free HTTPS endpoint | No WAF, no throttling, no usage plans — unsuitable for public production APIs | Internal endpoints, webhooks with IAM auth, dev/test, simple backends |

**Warning on Function URLs**: Do not expose Function URLs (with `AuthType: NONE`) for public production APIs handling untrusted input. Use API Gateway + AWS WAF instead.

**Question to ask**: "Is this a public production API needing WAF, rate limiting, and auth governance (API Gateway), an endpoint behind an existing ALB stack (ALB), or a simple internal/webhook endpoint with IAM auth (Function URL)?"

---

## Compliance Decisions (Cannot Default)

> ⚠️ These decisions depend on the organization's certification scope and billing agreements. Surface and confirm before prescribing:

- **SOC2/HIPAA/PCI-DSS/GDPR** controls — What compliance certifications are in scope? What AWS services are authorized? (GuardDuty Lambda Protection, Security Hub, AWS Config mandatory rules, data residency constraints)
- **Compute Savings Plans** — Is the organization enrolled? What commit percentage covers Lambda? (Savings Plans coverage reduces on-demand Lambda costs by up to ~17%)
