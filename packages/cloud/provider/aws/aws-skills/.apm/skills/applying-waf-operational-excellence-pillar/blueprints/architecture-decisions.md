# Architecture Decisions — AWS OE Pillar

Full decision matrices for the three Ask-First decisions in `applying-waf-operational-excellence-pillar`.
Source: AWS Well-Architected OE Pillar, November 6, 2024 edition.

---

## Decision 1 — Deployment Strategy (OPS 6: Mitigate Deployment Risks)

**When to surface**: Anytime a deployment strategy is being selected for a workload.
**Question to ask**: "What is the acceptable blast radius and rollback time for a bad deploy, and can you afford duplicate capacity during cutover?"

| Strategy | AWS Service | Blast Radius | Rollback Speed | Capacity Cost | Best When |
|---|---|---|---|---|---|
| Rolling | CodeDeploy / ECS rolling / ASG | Medium (mixed-version window) | Slow (re-deploy) | $ (no extra) | Low-risk, stateless internal services |
| Blue/Green | CodeDeploy + ALB target groups | Low (instant cutover) | Instant (route back) | $$$ (double capacity during cutover) | Customer-facing, zero-tolerance for mixed versions |
| Canary | CodeDeploy canary config / Lambda aliases | Lowest (small % traffic first) | Fast (stop canary) | $$ (partial extra) | High-traffic APIs where blast radius must be tiny |

**Operational considerations**:
- Canary requires alarm-driven automated rollback wiring — the CodeDeploy deployment fails if a CloudWatch alarm triggers during the canary interval
- Blue/Green requires environment duplication automation (CloudFormation/CDK) to avoid manual drift
- Rolling exposes a mixed-version window that complicates stateful or session-aware workloads

**Lock-in**: All three use AWS CodeDeploy (AWS-native tooling); the *patterns* (rolling/B/G/canary) are portable concepts.

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/framework/oe-prepare.html (OPS 6) — accessed 2026-08-27

---

## Decision 2 — Observability Tooling (OPS 4 / OPS 8)

**When to surface**: When selecting or recommending an observability stack.
**Question to ask**: "Is this workload container/Kubernetes-heavy or multi-cloud, and what telemetry cardinality/volume do you expect?"

| Option | AWS Services | Optimizes | Sacrifices | Best When |
|---|---|---|---|---|
| Native CloudWatch stack | CloudWatch + X-Ray + Application Signals | Deepest AWS integration, minimal ops overhead | Cost at high cardinality; limited OSS/PromQL portability | AWS-centric teams wanting lowest friction |
| Managed OSS | Amazon Managed Prometheus + Amazon Managed Grafana | OSS/PromQL portability, high-cardinality container metrics, Kubernetes native | More dashboard configuration; team must know PromQL | EKS/Kubernetes workloads; high-cardinality metrics; multi-cloud telemetry strategy |
| Third-party | Datadog / New Relic (via AWS integrations) | Rich unified UX across heterogeneous estate | License cost ($$$), egress charges, vendor lock-in | Large organizations with existing third-party tooling across non-AWS estate |

**Cost profile**: Native CloudWatch ($$ ingestion + retention scaling with volume) | Managed OSS ($$, depends on scrape interval and retention) | Third-party ($$$ licensing + egress)

**Portability**: Managed OSS (Prometheus/Grafana) is most portable — metrics and dashboards are reusable across clouds. Native CloudWatch is most locked-in but lowest friction for pure-AWS workloads.

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/implement-observability.html (OPS 4) — accessed 2026-08-27

---

## Decision 3 — Automation Depth (Design Principle: "Safely automate where possible")

**When to surface**: When deciding how to automate an operational response or runbook.
**Question to ask**: "Is this event well-understood and frequent enough to justify full automation, and do we have rate control, error thresholds, and approvals in place?"

| Depth | AWS Services | Optimizes | Sacrifices | Best When |
|---|---|---|---|---|
| Manual runbook | SSM Documents (operator-executed) | Human judgment; low build investment | Toil, slower MTTR, human error risk | Rare or novel events; early operational maturity; regulatory checkpoints |
| Approval-gated automation | SSM Automation + approval steps | Balance of speed and human oversight | Approval latency added to response time | Higher-risk changes; regulatory/compliance gates; moderate event frequency |
| Fully automated with guardrails | EventBridge + SSM Automation + CloudWatch alarms + rate control | Fastest MTTR; lowest toil; consistent execution | Requires mature guardrail design and testing before enabling | Well-understood, frequently-occurring, low-novelty events |

**Guardrail requirements for full automation** (design principle 3):
- Rate control: limit concurrent automation executions
- Error thresholds: abort/alert when failure rate exceeds threshold
- Approval steps: include manual approvals for actions with significant blast radius
- Targeting: use consistent Resource Tags + Resource Groups to scope automation to intended resources only

**Lock-in**: SSM Automation and EventBridge are AWS-native; automation logic (the procedure itself) is conceptually portable but requires re-authoring on other clouds.

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/framework/oe-design-principles.html — accessed 2026-08-27
