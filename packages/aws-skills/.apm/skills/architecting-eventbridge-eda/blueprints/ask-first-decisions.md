# Ask-First Decisions — AWS EventBridge EDA (2026)

Decision matrices for the 4 architectural crossroads in SKILL.md. Confirm with the user before designing.
Source research: `workspace/docs/research_cloud_AWS_EventBridge_EDA_2026.md` (research date 2026-08-28).

---

## D1 — Bus vs Pipes vs Scheduler vs SNS / Kinesis

Ask: "Is this many-to-many routing (bus), a single producer-to-consumer wiring (Pipes), a time-triggered task (Scheduler), or pure high fan-out / ordered streaming (SNS / Kinesis)?"

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| Event bus + rules | Content-based routing, schema registry | Ordering; per-event cost on custom bus | Multiple producers fan out to multiple consumers |
| EventBridge Pipes | Built-in polling, filter + enrich, source order, low $/event | 1 source to 1 target; no wildcard filter | Wiring one stream/queue to one target |
| EventBridge Scheduler | One-time/recurring, time zones, 270+ targets | Not event-triggered; 256 KB input cap | cron / rate / at tasks |
| Amazon SNS | Millions of endpoints, lowest latency | Attribute-based filtering only | Extreme fan-out |
| Kinesis Data Streams | Per-shard ordering, replay window | No content routing; shard management | Ordered high-throughput streaming |

- Cost anchors: custom bus $1.00/M; Pipes $0.40/M; Scheduler free to 14M invocations/month then $1.00/M; AWS-service events on the default bus free.
- Scale: bus PutEvents 10,000 TPS (primary Regions, adjustable); Pipes 3,000 concurrent executions; Scheduler 10,000,000 schedules per Region.
- Lock-in: all AWS-proprietary control planes; event JSON is portable, rule/pattern/pipe definitions are not.

Sources: [eb-pipes](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-pipes.html), [pricing](https://aws.amazon.com/eventbridge/pricing/), [EDA landing page](https://aws.amazon.com/event-driven-architecture/) (all accessed 2026-08-28)

---

## D2 — Choreography vs orchestration (saga)

Ask: "How many services participate, and do we need centralized compensation, timeout control and end-to-end visibility (orchestration), or maximal decoupling (choreography)?"

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| Choreography (bus + rules + Lambda) | Loose coupling, no central SPOF | Global timeout/retry control; traceability | Few participants, teams own their reactions |
| Orchestration (Step Functions + EventBridge triggers) | Central visibility, retries, compensations | Central coupling point | Many participants; compensation logic needed |

- Cost: choreography = per-event bus cost + Lambda; orchestration = Step Functions transitions (Express cheaper at volume) + Lambda.
- Ops: choreography spreads logic (harder to trace); orchestration centralizes it.

Source: [Saga choreography (AWS Prescriptive Guidance)](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga-choreography.html) (accessed 2026-08-28)

---

## D3 — Default bus vs custom buses per domain

Ask: "Do domains need isolation (policy, CMK) and is a central audit account needed (hub-and-spoke)?"

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| Single default bus | Simplicity; free AWS-service ingestion | Domain isolation; per-domain policy/CMK | Small system, mostly AWS-service events |
| Custom bus per domain | Bounded-context isolation | More buses/rules to manage (100 buses per Region) | Multiple teams with distinct security postures |
| Hub-and-spoke (bus-to-bus) | Central governance/audit | No third hop; custom-event billing on delivery | Central account aggregates domain buses |

- Remind: a receiver bus cannot forward received events to a third bus (`THIRD_ACCOUNT_HOP_DETECTED` / `THIRD_REGION_HOP_DETECTED`).
- Limits: 100 buses per Region; 300 rules per bus (100 in af-south-1 / eu-south-1).

Sources: [eb-event-bus](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-event-bus.html), [eb-bus-to-bus](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-bus-to-bus.html) (accessed 2026-08-28)

---

## D4 — Pipes enrichment compute

Ask: "Is enrichment a single code call, a multi-step flow, or a call to an existing HTTP API? Can it finish within the 5-minute pipe execution ceiling?"

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| Lambda | Arbitrary code, up to 6 MB response | Shares the pipe execution budget | Custom transform/lookup in code |
| Step Functions Express only | Multi-step enrichment | Standard workflows unsupported | Several coordinated calls |
| API Gateway / API Destination | Reuse an existing HTTP API | Network latency, auth management | Reference data behind an HTTP API |

- Enrichment response max 6 MB; total pipe execution (enrichment + target) max 5 minutes, not adjustable.
- An empty enrichment response (`""`, `{}`, `[]`) suppresses the target (acts as a filter).
- Cost: Pipes $0.40/M plus enrichment compute; API Destinations $0.20/M, credentials in Secrets Manager.
- The research file's option table mentions a "15-min" ceiling for Lambda, which conflicts with its own 5-minute pipe limit; this blueprint uses 5 minutes (as in SKILL.md). (unverified: the 15-min figure)

Source: [pipes-enrichment](https://docs.aws.amazon.com/eventbridge/latest/userguide/pipes-enrichment.html) (accessed 2026-08-28)
