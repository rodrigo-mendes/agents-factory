# Evaluation Scenarios — applying-waf-sustainability-pillar

Skill version pinned to: AWS WAF Sustainability Pillar, revision **2024-11-06**.

Use with `/evaluating-skill-scenarios applying-waf-sustainability-pillar`.

---

## Scenario 1 — Canonical: Review a variable-demand web API for sustainability

```json
{
  "skills": ["applying-waf-sustainability-pillar"],
  "query": "We have a variable-demand REST API on EC2 (fixed fleet, ~18% avg CPU, us-east-1). How do we improve its sustainability posture?",
  "expected_behavior": [
    "Instructs agent to establish a CCFT baseline and CloudWatch proxy KPIs before any optimization (Always Do #1)",
    "Identifies fixed fleet at 18% CPU as the 'chronically under-utilized always-on infrastructure' anti-pattern (Never Do #2)",
    "Recommends EC2 Auto Scaling + Instance Scheduler for non-prod, and Graviton right-sizing (SUS02-BP01, SUS05-BP01, SUS05-BP02)",
    "Raises SUS01-BP01 Ask-First for region selection — asks whether us-east-1 was chosen for latency/residency or by default",
    "Recommends managed/serverless options (Fargate or Lambda) if the workload pattern supports it (SUS05-BP03)"
  ]
}
```

---

## Scenario 2 — Edge Case: Real-time regulated workload with data-residency constraint

```json
{
  "skills": ["applying-waf-sustainability-pillar"],
  "query": "We run a financial trading platform in eu-west-1 due to GDPR residency rules and strict sub-10ms latency SLA. The sustainability team wants us to move to the lowest-carbon-intensity AWS region. What do we do?",
  "expected_behavior": [
    "Invokes the SUS01-BP01 Ask-First decision — region choice involves conflicting constraints (residency, latency, carbon)",
    "Correctly identifies that data-residency (GDPR) and sub-10ms SLA override carbon-intensity region optimization",
    "Does NOT mandate a region move; documents the trade-off as an ADR",
    "Recommends sustainability levers that remain available regardless of region: Graviton right-sizing, Auto Scaling, S3 Lifecycle, idle-asset cleanup (SUS02-BP01, SUS04, SUS05)",
    "Does not treat region choice as the only sustainability lever"
  ]
}
```

---

## Scenario 3 — Misuse / Anti-pattern trap: Publishing sustainability claims without measurement

```json
{
  "skills": ["applying-waf-sustainability-pillar"],
  "query": "Marketing wants to announce our platform is 'carbon-neutral' because we're on AWS. Can we say that?",
  "expected_behavior": [
    "Refuses to validate the claim without a CCFT baseline and defined KPIs",
    "Cites design principles 'Understand your impact' and 'Establish sustainability goals' as the entry point",
    "Explains the shared-responsibility model: AWS covers sustainability of the cloud; customer is responsible for sustainability in the cloud",
    "Identifies this as a greenwashing risk (Never Do #1)",
    "Provides actionable next step: pull CCFT data, define per-transaction proxy KPIs in CloudWatch, then assess whether and what claim can be substantiated"
  ]
}
```

---

## Scenario 4 — Best-practice ID verification: SUS 6 numbering after 2024-11-06 revision

```json
{
  "skills": ["applying-waf-sustainability-pillar"],
  "query": "Our ADR from 2023 references SUS06-BP01 as 'Keep your workload up to date'. Is that still correct?",
  "expected_behavior": [
    "Flags that SUS 6 was renumbered in the 2024-11-06 revision",
    "States that SUS06-BP01 is NOW 'Communicate and cascade your sustainability goals' (new best practice added in 2024-11-06)",
    "'Keep your workload up to date' is now SUS06-BP03 under the current revision",
    "Recommends updating the ADR to use current 2024-11-06 IDs",
    "Cites the document-revisions page as the source for the renumbering"
  ]
}
```

---

## Scenario 5 — Data lifecycle: S3 storage optimization

```json
{
  "skills": ["applying-waf-sustainability-pillar"],
  "query": "We store event logs in S3 Standard. After 30 days they're rarely accessed; after 180 days almost never. We keep them 7 years for compliance. How should we manage this?",
  "expected_behavior": [
    "Identifies the absence of lifecycle rules as the 'unmanaged data growth' anti-pattern (Never Do #3)",
    "Recommends S3 Lifecycle policy: transition to S3 Standard-IA at 30 days, S3 Glacier Instant Retrieval or Flexible Retrieval at 180 days, expire at 7 years (or S3 Glacier Deep Archive for lowest energy/cost)",
    "Alternatively recommends S3 Intelligent-Tiering if access patterns are less predictable",
    "Cites SUS04-BP03 (lifecycle policies) and SUS04-BP05 (remove unneeded data)",
    "Notes the data-minimization alignment with the Security pillar (attack surface reduction)"
  ]
}
```

---

## Scenario 6 — Organizational process: Cascading sustainability goals (SUS06-BP01 new)

```json
{
  "skills": ["applying-waf-sustainability-pillar"],
  "query": "Our CTO set a company-wide sustainability target but workload teams don't know their individual targets. What's the WAF guidance here?",
  "expected_behavior": [
    "Identifies this as SUS06-BP01 'Communicate and cascade your sustainability goals' — the new best practice added in the 2024-11-06 revision",
    "Recommends defining per-workload sustainability targets and assigning them to workload owners",
    "Recommends using the Well-Architected Tool to track per-workload SUS 1-6 review answers and improvement plans",
    "Also references SUS06-BP02 (adopt methods for rapid improvement) and SUS06-BP03 (keep workloads up to date)",
    "Does not confuse organizational sustainability (ESG) with the pillar's scope (environmental/energy efficiency)"
  ]
}
```
