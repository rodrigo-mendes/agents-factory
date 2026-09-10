# Evaluation Scenarios — applying-waf-operational-excellence-pillar

Skill under test: `applying-waf-operational-excellence-pillar`
Edition: AWS Well-Architected Framework — Operational Excellence Pillar, November 6, 2024

---

## Scenario 1 — Canonical: Pre-go-live OE readiness review

```json
{
  "skills": ["applying-waf-operational-excellence-pillar"],
  "query": "We are launching a new customer-facing REST API on AWS Lambda + API Gateway next week. What OE pillar requirements must be satisfied before we go live?",
  "expected_behavior": [
    "Identifies OPS 7 (Operational Readiness Review) as a hard gate before go-live",
    "Requires ORR checklist covering workload, processes, and personnel",
    "Requires SSM Automation runbooks for routine operational tasks",
    "Requires playbooks for incident investigation paths",
    "Requires OPS 4 observability: business KPIs (BP01), application telemetry (BP02), user-experience telemetry (BP03), dependency telemetry (BP04), distributed tracing BP05 via CloudWatch + X-Ray",
    "Requires OPS 5/6: CI/CD pipeline with canary or blue/green deployment strategy and alarm-triggered rollback — not manual or AllAtOnce",
    "References the November 6, 2024 edition"
  ]
}
```

---

## Scenario 2 — Canonical: OPS question mapping for a Well-Architected Review

```json
{
  "skills": ["applying-waf-operational-excellence-pillar"],
  "query": "We are running a Well-Architected Review for the OE pillar on our production workload. List all 11 OPS questions in sequence, identify which best-practice area each belongs to, and highlight the top 3 HIGH-risk questions.",
  "expected_behavior": [
    "Lists all 11 OPS questions (OPS 1 through OPS 11) verbatim or closely paraphrased",
    "Correctly assigns each to its area: OPS 1–3 to Organization, OPS 4–7 to Prepare, OPS 8–10 to Operate, OPS 11 to Evolve",
    "Identifies OPS 4 (observability), OPS 6 (deployment risk), and OPS 7 (readiness to support) as the top HIGH-risk questions",
    "Does NOT confuse the pre-2023 OPS 4/OPS 8 framing with the current edition",
    "References the November 6, 2024 edition"
  ]
}
```

---

## Scenario 3 — Architectural decision: Deployment strategy selection

```json
{
  "skills": ["applying-waf-operational-excellence-pillar"],
  "query": "We have a high-traffic customer-facing API that gets 10 million requests per day. Which OPS 6 deployment strategy should we use to mitigate deployment risk, and why?",
  "expected_behavior": [
    "Surfaces the Ask-First decision: asks about acceptable blast radius, rollback time, and capacity cost tolerance",
    "Recommends canary deployment for high-traffic APIs where blast radius must be minimized",
    "Explains canary as CodeDeploy canary configuration with alarm-triggered automatic rollback",
    "Contrasts with blue/green (instant rollback, double capacity cost) and rolling (simpler but mixed-version window)",
    "Does NOT recommend AllAtOnce/big-bang deployment",
    "References OPS 5/OPS 6 and the design principle 'Make frequent, small, reversible changes'"
  ]
}
```

---

## Scenario 4 — Observability tooling decision for EKS workload

```json
{
  "skills": ["applying-waf-operational-excellence-pillar"],
  "query": "Our new workload runs on Amazon EKS and emits high-cardinality Prometheus metrics. Should we use native CloudWatch or Amazon Managed Prometheus + Managed Grafana for observability?",
  "expected_behavior": [
    "Surfaces the Ask-First decision: confirms workload is container/Kubernetes-heavy with high-cardinality metrics",
    "Recommends Amazon Managed Prometheus + Managed Grafana as the preferred choice for EKS/Kubernetes high-cardinality telemetry",
    "Notes that native CloudWatch is simpler but metric/log cost grows with cardinality/volume",
    "Notes that Managed Prometheus/Grafana provides OSS/PromQL portability and multi-cloud fit",
    "Ties recommendation to OPS 4 (Implement observability) and OPS 8 (Utilize workload observability)",
    "Does NOT recommend a third-party tool without surfacing license cost and egress concerns"
  ]
}
```

---

## Scenario 5 — Anti-pattern: Request to skip ORR and runbooks

```json
{
  "skills": ["applying-waf-operational-excellence-pillar"],
  "query": "We are behind schedule. Can we go live now and add runbooks and monitoring later once we see what breaks in production?",
  "expected_behavior": [
    "Flags this as the HIGH-risk anti-pattern: launching without an ORR (OPS 7)",
    "Flags this as the HIGH-risk anti-pattern: telemetry added after incidents rather than designed in (OPS 4)",
    "Clearly refuses to endorse the approach",
    "Asks the clarifying questions: What is the ORR outcome? Where are the runbooks/playbooks? Which observability signals (KPIs, traces) exist? Who owns incident response?",
    "Proposes a minimum viable OE posture that can gate go-live without excessive delay",
    "Does NOT suggest runbooks/monitoring can safely be deferred"
  ]
}
```

---

## Scenario 6 — Edge case: Orphan alerts and no post-incident process

```json
{
  "skills": ["applying-waf-operational-excellence-pillar"],
  "query": "Our CloudWatch alarms send email to a shared team inbox. After incidents we restore service and move on. Are there OE pillar gaps?",
  "expected_behavior": [
    "Identifies the MEDIUM-risk anti-pattern: alerts with no owner, no runbook, no escalation path (OPS 10)",
    "Identifies the MEDIUM-risk anti-pattern: no post-incident analysis or feedback loop (OPS 11)",
    "Recommends routing alarms through SNS and AWS Systems Manager Incident Manager with a named owner and on-call schedule",
    "Recommends binding each alarm to a runbook/playbook",
    "Recommends blameless post-incident analysis after every customer-impacting event with action tracking and org-wide sharing",
    "References OPS 10 (event management) and OPS 11 (evolve) explicitly"
  ]
}
```
