# Ask-First Decisions — applying-aws-serverless-well-architected-lens

Source: AWS Well-Architected Framework — Serverless Applications Lens, content dated 2022-07-14 (accessed 2026-08-27).

> ⚠️ Source dated 2022-07; verify currency. Pricing and limits change — confirm against current AWS docs before committing.

Each decision below must be raised with the user before generating architecture or IaC. Do not pick an option silently.

---

## Decision 1 — Lambda concurrency provisioning model (per function)

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| On-demand | Cost (pay-per-use, free when idle) | Cold-start latency on new environments | Spiky / unpredictable traffic |
| Provisioned Concurrency | Predictable low latency (no cold starts) | Always-on cost even when idle | Latency-sensitive, steady user-facing APIs |
| Reserved Concurrency | Blast-radius isolation, throttle protection | Caps the function's max throughput | Protecting critical functions / limiting noisy ones |

**Cost profile**: On-demand is cheapest at rest; Provisioned adds standing cost; billing is per 1 ms, so faster initialization is cheaper.
**Lock-in**: High AWS coupling (Lambda-specific configuration).
**Monitor**: `ProvisionedConcurrencySpilloverInvocations` (Provisioned), `Throttles` / `ConcurrentExecutions` (Reserved).

**Ask**:
1. Is the function latency-sensitive with steady traffic (→ Provisioned)?
2. Is traffic spiky or background (→ On-demand)?
3. Does it need isolation from the account-level concurrency pool (→ Reserved)?

> Java workloads: Lambda SnapStart is a post-2022 alternative to Provisioned Concurrency not covered by the lens — see [post-2022-gaps.md](./post-2022-gaps.md).

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/selection.html (2022-07-14)

---

## Decision 2 — Step Functions workflow type

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| Express (Sync/Async) | High volume, low per-transition cost | Durability, exactly-once, long duration | Short-running high-volume orchestration |
| Standard | Durability, audit, long-running, exactly-once | Higher per-transition cost | Long-running audited business workflows / sagas |

**Cost profile**: Express is billed by duration/memory (cheaper at high volume); Standard is billed per state transition.
**Lock-in**: Amazon States Language (ASL) is AWS-proprietary.
**Caveat**: Express is at-least-once — steps must be idempotent.
**Performance note**: Test Standard vs. Express; account for per-second execution-start and state-transition rates.

**Ask**:
1. What is the expected execution duration?
2. What is the expected execution volume?
3. Is there a durability / audit / exactly-once requirement?

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/failure-management.html, https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/selection.html (2022-07-14)

---

## Decision 3 — API Gateway endpoint type and DynamoDB capacity mode

| Option | Service | Optimizes | Sacrifices | Best when |
|---|---|---|---|---|
| Edge-optimized endpoint | Amazon API Gateway | Latency for geographically dispersed clients | Regional control | Global consumer base |
| Regional endpoint | Amazon API Gateway | In-region latency / same-Region AWS calls | Global edge acceleration | Regional consumers / AWS-internal callers |
| On-demand capacity | Amazon DynamoDB | Zero capacity planning | Higher unit cost at steady high load | Unpredictable traffic |
| Provisioned capacity | Amazon DynamoDB | Lower cost at consistent load | Requires capacity planning / auto-scaling | Predictable consistent traffic |

**Cost profile**: On-demand DynamoDB costs more per request but avoids over-provisioning; provisioned is cheaper when utilization is high and steady.
**Lock-in**: DynamoDB is AWS-proprietary NoSQL; migration requires schema / access-pattern redesign.
**Performance note**: Run performance tests at steady and burst rates; load-test again after changes.

**Ask**:
1. Is traffic predictable (→ provisioned / regional) or bursty / global (→ on-demand / edge)?
2. Where are the API consumers located — one Region, or globally dispersed?

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/selection.html (2022-07-14)

---

## Related performance levers (lens PER 1 / COST 1)

- **Lambda memory**: CPU, network and storage IOPS scale proportionally with memory — test several settings; memory tuning is both a performance and a cost lever (1-ms billing).
- **Kinesis**: Enhanced fan-out for dedicated per-consumer throughput in multi-consumer scenarios; extended batch window for low-volume transactions with Lambda.
- Avoid over-provisioning "just in case" — benchmark with empirical data.

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/selection.html, https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/cost-effective-resources.html (2022-07-14)
