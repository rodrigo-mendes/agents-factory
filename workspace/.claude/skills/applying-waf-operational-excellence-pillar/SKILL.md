---
name: applying-waf-operational-excellence-pillar
description: "Applies the AWS Well-Architected Framework Operational Excellence pillar (OPS 1–11) to production workloads using the four best-practice areas: Organization, Prepare, Operate, and Evolve. Use when designing, reviewing, or auditing AWS architectures for observability, deployment safety, operational readiness, incident response, and continuous improvement — mapped question-by-question to the November 6, 2024 edition."
---

## Function

Specialist in the AWS Well-Architected Framework Operational Excellence pillar, November 6, 2024 edition. Covers all 4 best-practice areas, 8 design principles, and 11 OPS questions (OPS 1–11): operating model design (OPS 1–3), observability and deployment readiness (OPS 4–7), day-2 operations (OPS 8–10), and continuous improvement (OPS 11).

## Version Context

**Technology**: AWS Well-Architected Framework — Operational Excellence Pillar
**Target edition**: November 6, 2024 (current stable; whitepaper continuously updated at `/latest/`)
**Research date**: 2026-08-27 | **Currency threshold**: 2027-08-27
**Official source**: https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/welcome.html

**Key revision milestones (edition in force 2026)**:
- **2024-11-06**: Updated OPS 2, OPS 5, OPS 9, OPS 10 with gen-AI guidance
- **2024-06-27**: Consolidated OPS 1/2/3; revised risk ratings in OPS 10
- **2023-10-03**: OPS 4 rewritten to "Implement observability" (was "Design for operations"); OPS 8 rewritten to "Utilize workload observability" (was "Understanding operational health"); first principle elevated to "Organize teams around business outcomes"

**Deprecated**: Any source citing the pre-2023-10-03 OPS 4/OPS 8 framing ("Design for operations", "Understanding operational health") or fewer than 8 design principles — reject as stale.

⚠️ **CRITICAL — Agent Warning**:
This skill targets the **November 6, 2024 edition**. OPS question numbering and meaning changed across editions. Always confirm the edition when interpreting external OPS-numbered guidance.

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — Three-tier patterns (✅⚠️🚫)
- **[OE Framework Structure](#oe-framework-structure)** — 4 areas, 8 principles, 11 OPS questions
- **[Reference Architecture](#reference-architecture)** — OE-instrumented workload service map
- **[Verification Loop](#verification-loop)** — AWS CLI checks per OPS area
- **[Quick Reference](#quick-reference)** — Critical limits and tool commands
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 6 test cases
- **[Always-Do Patterns](./blueprints/always-do-patterns.md)** — Full OPS 1–11 per-pattern guidance
- **[Architecture Decisions](./blueprints/architecture-decisions.md)** — Deployment strategy, observability, automation depth

---

## Blueprints & Guardrails

### ✅ Always Do

For full per-pattern guidance and service mappings, see [Always-Do Patterns](./blueprints/always-do-patterns.md).

**Mandatory patterns — Complex domain (7 required):**

- **Define a business-aligned operating model with explicit ownership (OPS 1–3)** — Assign owners to every component, process, and procedure; maintain a risk registry; govern multi-account with AWS Organizations + Control Tower. Without ownership, OE is ungovernable.

- **Implement observability before go-live (OPS 4)** — Instrument all five OPS04 best practices: business KPIs (BP01), application telemetry (BP02), user-experience telemetry (BP03), dependency telemetry (BP04), and distributed tracing (BP05) via CloudWatch + X-Ray/Application Signals. Observability is designed in from day one, not bolted on.

- **Use small, reversible, automated deployments with alarm-triggered rollback (OPS 5 / OPS 6)** — CI/CD pipeline (CodePipeline + CodeBuild + CodeDeploy) with canary or blue/green strategy; automated rollback wired to CloudWatch alarms; consistent templated environments via CloudFormation/CDK.

- **Gate production on an Operational Readiness Review with runbooks and playbooks (OPS 7)** — Complete ORR checklist (workload + processes + personnel) before go-live; codify routine tasks as SSM Automation runbooks; author playbooks for incident investigation; run pre-mortems to anticipate failure.

- **Define operations as code with automation guardrails (design principle 3)** — CloudFormation/CDK for infra; SSM Automation for operational procedures; guardrails (rate control, error thresholds, manual approvals) on all automated responses; consistent resource tag strategy for targeting and accountability.

- **Operate with business-aligned health metrics, owned alerts, and dashboards (OPS 8 / OPS 9 / OPS 10)** — Map every alarm to a KPI and a named owner with a bound runbook/playbook; route alerts through SNS/Incident Manager to an on-call schedule; build audience-tailored dashboards (customer/business/dev/ops); establish metric baselines.

- **Run blameless post-incident analysis after every customer-impacting event (OPS 11)** — Track contributing factors and preventative actions; archive logs (S3 + Glue + Athena); share learnings org-wide; dedicate recurring cycles to incremental improvement.

### ⚠️ Ask First

For full option tables and tradeoff matrices, see [Architecture Decisions](./blueprints/architecture-decisions.md).

**Decision points — confirm before recommending:**

- **Deployment strategy (OPS 6)** — Rolling vs. blue/green vs. canary differ on blast radius, rollback speed, and capacity cost. Ask: *"What is the acceptable rollback time for a bad deploy, and can you afford duplicate capacity during cutover?"* Rolling ($) suits low-risk internal services; blue/green ($$$) suits customer-facing with low tolerance; canary ($$) suits high-traffic APIs.

- **Observability tooling (OPS 4 / OPS 8)** — Native CloudWatch + X-Ray vs. Amazon Managed Prometheus + Managed Grafana vs. third-party (Datadog/New Relic). Ask: *"Is this workload container/Kubernetes-heavy or multi-cloud, and what telemetry cardinality/volume do you expect?"* Native is lowest friction; managed OSS (Prometheus/Grafana) fits EKS and high-cardinality; third-party suits heterogeneous multi-cloud estates.

- **Automation depth (design principle "Safely automate where possible")** — Manual runbooks vs. approval-gated automation vs. fully automated with guardrails. Ask: *"Is this event well-understood and frequent enough to justify full automation, and are rate control / error thresholds / approvals in place?"* Fully automate only mature, well-understood events.

### 🚫 Never Do

| Anti-Pattern | Why | Correct Alternative |
|---|---|---|
| Launch to production without an ORR | Enters production with un-mitigated operational risk; no runbooks at first incident (OPS 7, HIGH) | Gate go-live: ORR checklist signed off, SSM runbooks for routine tasks, playbooks for incidents, owned escalation path |
| Add monitoring only after an incident (no designed-in observability) | Blind spots remain; slow diagnosis; violates OPS04-BP01–BP05 (OPS 4, HIGH) | Instrument KPIs, app telemetry, user-experience telemetry, dependency telemetry, and distributed tracing from day one |
| Use big-bang monolithic deployments with no rollback | Maximizes blast radius; no fast reversal path (OPS 5/6, HIGH) | Small, frequent automated deploys via CodeDeploy canary/blue-green with alarm-triggered automatic rollback |
| Provision and operate via manual console click-ops (no ops-as-code) | Configuration drift, inconsistent recovery, human error, and toil (design principle 3, MEDIUM) | CloudFormation/CDK for infra; SSM Automation for procedures; rate control + error thresholds + approvals on all automation |
| Create CloudWatch alarms with no owner, no runbook, and no escalation path | Alert fatigue; missed incidents; violates OPS 10 (MEDIUM) | Every alarm bound to a named owner, a runbook/playbook, and an on-call schedule via Incident Manager |
| Close incidents once service restores with no post-incident analysis | Repeated outages from the same root causes; stagnant operations maturity (OPS 11, MEDIUM) | Blameless post-incident analysis after every customer-impacting event; action tracking; org-wide shared learnings |

---

## OE Framework Structure

**Definition (verbatim)**: "A commitment to build software correctly while consistently delivering a great customer experience."

### 8 Design Principles (November 6, 2024 edition)

| # | Principle |
|---|---|
| 1 | Organize teams around business outcomes |
| 2 | Implement observability for actionable insights |
| 3 | Safely automate where possible |
| 4 | Make frequent, small, reversible changes |
| 5 | Refine operations procedures frequently |
| 6 | Anticipate failure |
| 7 | Learn from all operational events and metrics |
| 8 | Use managed services |

### 4 Best-Practice Areas → 11 OPS Questions

| Area | OPS # | Question |
|---|---|---|
| **Organization** | OPS 1 | How do you determine what your priorities are? |
| **Organization** | OPS 2 | How do you structure your organization to support your business outcomes? |
| **Organization** | OPS 3 | How does your organizational culture support your business outcomes? |
| **Prepare** | OPS 4 | How do you implement observability in your workload? |
| **Prepare** | OPS 5 | How do you reduce defects, ease remediation, and improve flow into production? |
| **Prepare** | OPS 6 | How do you mitigate deployment risks? |
| **Prepare** | OPS 7 | How do you know that you are ready to support a workload? |
| **Operate** | OPS 8 | How do you utilize workload observability in your organization? |
| **Operate** | OPS 9 | How do you understand the health of your operations? |
| **Operate** | OPS 10 | How do you manage workload and operations events? |
| **Evolve** | OPS 11 | How do you evolve operations? |

> Source: https://docs.aws.amazon.com/wellarchitected/latest/framework/operational-excellence.html — accessed 2026-08-27.

---

## Reference Architecture

**OE-instrumented production workload (composition from OE pillar best-practice areas)**:

| Layer | AWS Service(s) | OE Alignment |
|---|---|---|
| Governance / Operating Model | AWS Organizations + Control Tower | OPS 1–3 |
| IaC / Ops-as-code | CloudFormation / CDK + SSM Automation | Design principle 3 |
| CI/CD | CodePipeline + CodeBuild + CodeDeploy | OPS 5, OPS 6 |
| Observability | CloudWatch + X-Ray / Application Signals | OPS 4, OPS 8 |
| Managed OSS telemetry (containers) | Amazon Managed Prometheus + Managed Grafana | OPS 4, OPS 8 |
| Incident response | CloudWatch alarms + SNS + Incident Manager | OPS 10 |
| Evolution analytics | S3 + AWS Glue + Amazon Athena + QuickSight | OPS 11 |
| Well-Architected review | AWS Well-Architected Tool + Trusted Advisor | OPS 1–11 (gap analysis) |

Key architectural decisions for this composition: deployment strategy, observability tooling choice, and automation depth — see [Architecture Decisions](./blueprints/architecture-decisions.md).

---

## Verification Loop

Run after each OE design or review activity:

```bash
# OPS 4 — Confirm CloudWatch alarms exist for KPIs
aws cloudwatch describe-alarms --query 'MetricAlarms[*].AlarmName'
# Expected: list of alarms mapped to business KPIs

# OPS 6 — Confirm deployment group strategy (not AllAtOnce)
aws deploy get-deployment-group --application-name <app> --deployment-group-name <dg> \
  --query 'deploymentGroupInfo.deploymentStyle'
# Expected: BLUE_GREEN or CANARY

# OPS 4 — Confirm X-Ray / Application Signals tracing active
aws xray get-service-graph --start-time $(date -d '1 hour ago' +%s) --end-time $(date +%s)
# Expected: service map with connected nodes

# OPS 3 (org) — Confirm Control Tower controls deployed
aws controltower list-enabled-controls --target-identifier <OU-ARN>
# Expected: list of enabled guardrails

# OPS 11 — Confirm Glue catalog (log archival pipeline) operational
aws glue get-databases --query 'DatabaseList[*].Name'
# Expected: database(s) for operational log analytics
```

**Troubleshooting**:
- `describe-alarms` returns empty → observability gap; instrument OPS04-BP01–BP05 before go-live
- Deployment style is `IN_PLACE / AllAtOnce` → high blast radius; switch to canary or blue/green
- X-Ray returns no service graph → tracing not configured; enable in Lambda/API GW/ECS task definitions

---

## Quick Reference

**OE top-3 guardrails (minimum viable posture)**:
1. Observability designed in (OPS 4) — KPIs + traces before go-live
2. Small reversible deploys with auto-rollback (OPS 5/6)
3. ORR + runbooks/playbooks before production support (OPS 7)

**Critical Well-Architected Tool review path**:
```
OPS 1 → OPS 2 → OPS 3  (organization/ownership/culture)
OPS 4 → OPS 5 → OPS 6 → OPS 7  (readiness to operate)
OPS 8 → OPS 9 → OPS 10  (day-2 operations)
OPS 11  (continuous improvement)
```

**OPS question risk thresholds**:

| Risk Level | OPS Questions Typically Flagged | Action |
|---|---|---|
| HIGH | OPS 4 (no observability), OPS 6 (big-bang deploy), OPS 7 (no ORR) | Block go-live until resolved |
| MEDIUM | OPS 10 (orphan alerts), OPS 11 (no post-incident analysis), design principle 3 (click-ops) | Remediation plan required |

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/applying-waf-operational-excellence-pillar/
├── SKILL.md                         <- This file (summary + guardrails)
└── blueprints/
    ├── evaluation-scenarios.md      <- 6 test scenarios for skill-evaluator
    ├── always-do-patterns.md        <- Full per-OPS guidance with service details
    └── architecture-decisions.md   <- Deployment strategy, observability, automation depth
```

---

## External Resources

### Official Documentation (AWS Well-Architected OE Pillar)
- [OE Pillar Whitepaper (rev. 2024-11-06)](https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/welcome.html) — accessed 2026-08-27
- [Framework — Operational Excellence Overview](https://docs.aws.amazon.com/wellarchitected/latest/framework/operational-excellence.html) — accessed 2026-08-27
- [Design Principles](https://docs.aws.amazon.com/wellarchitected/latest/framework/oe-design-principles.html) — accessed 2026-08-27
- [Implement Observability (OPS 4 detail)](https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/implement-observability.html) — accessed 2026-08-27
- [Prepare Area (OPS 4–7)](https://docs.aws.amazon.com/wellarchitected/latest/framework/oe-prepare.html) — accessed 2026-08-27
- [Operate Area (OPS 8–10)](https://docs.aws.amazon.com/wellarchitected/latest/framework/oe-operate.html) — accessed 2026-08-27
- [Evolve Area (OPS 11)](https://docs.aws.amazon.com/wellarchitected/latest/framework/oe-evolve.html) — accessed 2026-08-27

### Tools & Governance
- [AWS Well-Architected Tool](https://docs.aws.amazon.com/wellarchitected/latest/userguide/intro.html) — OPS 1–11 gap analysis in-console
- [AWS Systems Manager Automation](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-automation.html) — runbooks/playbooks as code
- [AWS Systems Manager Incident Manager](https://docs.aws.amazon.com/incident-manager/latest/userguide/what-is-incident-manager.html) — owned incident response (OPS 10)
