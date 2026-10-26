# Evaluation Scenarios — managing-aws-costs

5 test scenarios covering canonical use, edge cases, decision crossroads, and anti-pattern traps.

---

## Scenario 1 — Canonical: FinOps Foundation Setup for a New AWS Organization

```json
{
  "skills": ["managing-aws-costs"],
  "query": "We are setting up a new AWS Organization with 20 member accounts. We need full cost attribution per team and per project, proactive alerts, and automated enforcement when accounts overspend. What should we configure and in what order?",
  "expected_behavior": [
    "Prescribes the pre-account-vending checklist: tagging taxonomy + Tag Policy at OU root first",
    "Specifies Cost Allocation Tag activation in the Billing console (separate from resource tagging) with 24h propagation caveat",
    "Creates Cost Categories mapping account + tag to financial units (BU > team > environment)",
    "Configures CUR 2.0 via Data Exports (Parquet, cross-account delivery to a dedicated analytics account) — not legacy CUR",
    "Adds FOCUS 1.2 export if multi-cloud tooling is in scope (asks first)",
    "Enables Cost Anomaly Detection AWS-managed monitors from the management account for org-wide coverage",
    "Configures per-account monthly Budgets with stacked alerts: 80% SNS / 100% AUTOMATIC SCP Budget Action / 120% MANUAL Budget Action",
    "Enables Cost Optimization Hub org-wide from the management account",
    "Does NOT recommend enabling hourly Cost Explorer granularity unless accounts exceed $10k/day spend (would ask first)"
  ]
}
```

---

## Scenario 2 — Edge Case: AWS Channel Partner Billing with Custom Rates and Margin Analysis

```json
{
  "skills": ["managing-aws-costs"],
  "query": "We are an AWS Channel Partner billing 15 customers at custom rates. Each customer needs cost visibility at their custom pricing. We also need internal margin analysis (difference between what we charge and what AWS bills us).",
  "expected_behavior": [
    "Identifies AWS Billing Conductor as the correct service for pro forma (custom-priced) billing data",
    "Prescribes dual CUR 2.0 exports: standard CUR 2.0 (true AWS cost, management account) + pro forma CUR 2.0 (customer-facing pricing, per Billing Conductor billing group)",
    "Explains that Billing Conductor does NOT affect the actual AWS invoice — management account still pays the real invoice",
    "Recommends separate Athena databases for each export to compute margin = standard cost minus pro forma revenue",
    "Configures per-billing-group Budgets for per-customer spend alerts",
    "Notes Cost Optimization Hub should be enabled on the management account for partner's own infrastructure (not shared with customers)",
    "Tags all partner infrastructure separately from customer workloads for clean attribution",
    "Does NOT recommend applying Billing Conductor to the partner's own infrastructure accounts"
  ]
}
```

---

## Scenario 3 — Decision Crossroads: Choosing Between Cost Explorer API and Athena for a Reporting Pipeline

```json
{
  "skills": ["managing-aws-costs"],
  "query": "Our FinOps team wants to build an automated cost reporting system that generates per-team breakdowns daily for 200 AWS accounts across 30 services. Should we use the Cost Explorer API or Athena on CUR 2.0?",
  "expected_behavior": [
    "Asks: what is the expected query frequency? (identifies this as a high-volume automated pipeline scenario)",
    "Calculates or illustrates the API cost risk: 200 accounts x multiple services x daily queries = thousands of billable requests/run at $0.01/page",
    "Mandates Athena on CUR 2.0 for this high-volume batch pipeline",
    "Explains CUR 2.0 Parquet + S3 partitioning by year/month keeps Athena queries < $1 each",
    "Notes Cost Explorer API is still appropriate for the ad-hoc interactive analysis and GetCostForecast calls (low-volume)",
    "Does NOT recommend the Cost Explorer API as the primary data source for a 200-account daily pipeline",
    "Mentions the ~24h data latency of CUR 2.0 and confirms it is acceptable for daily reporting use cases (real-time is architecturally impossible through any Cost Management API)"
  ]
}
```

---

## Scenario 4 — Anti-Pattern Trap: Architect Proposes Using Legacy CUR for a New Athena Pipeline

```json
{
  "skills": ["managing-aws-costs"],
  "query": "We want to set up a new Athena + QuickSight cost analytics pipeline. Our engineer suggests using the existing Legacy CUR export we already have configured. Should we proceed?",
  "expected_behavior": [
    "Identifies the anti-pattern: building a new analytics pipeline on legacy CUR",
    "Explains WHY legacy CUR breaks pipelines: schema varies month-to-month as service usage and tags change — silently breaks Athena partition schemas, Redshift COPY jobs, and QuickSight datasets",
    "States that AWS explicitly labels legacy CUR as 'Legacy' and recommends CUR 2.0 for all new setups",
    "Prescribes creating a new CUR 2.0 export via Data Exports (Parquet, fixed 125-column schema)",
    "References the official CUR 2.0 migration guide for migrating existing legacy exports",
    "Does NOT recommend keeping the legacy CUR as the data source for a new pipeline",
    "Does NOT suggest a workaround to normalize the legacy CUR schema — the correct action is migration to CUR 2.0"
  ]
}
```

---

## Scenario 5 — Anti-Pattern Trap: Broad AUTOMATIC Budget Action SCP in Production

```json
{
  "skills": ["managing-aws-costs"],
  "query": "We want to automatically stop all spending when a production account hits its monthly budget. Can we configure a Budget Action to automatically apply a Deny-All SCP to the production account at 100%?",
  "expected_behavior": [
    "Identifies the anti-pattern: broad AUTOMATIC SCP in production (Deny-All would block existing running workloads, causing unplanned outages)",
    "Explains the risk: an AUTOMATIC Budget Action fires without human review — a Deny-All SCP applied at 100% during off-hours can cascade into a production incident",
    "Recommends MANUAL approval for production accounts (user must click 'Run action' in Budgets console — it is not automated)",
    "If AUTOMATIC enforcement is required in production, prescribes scoping the SCP narrowly to deny only NEW resource creation: ec2:RunInstances, rds:CreateDBInstance, etc. — never deny actions on EXISTING running resources",
    "Suggests the stacked alert pattern: 80% actual → SNS alert; 100% actual → MANUAL Budget Action (narrow SCP); 120% forecasted → escalation review",
    "Does NOT approve a Deny-All AUTOMATIC SCP for production without the above qualifications",
    "Does NOT conflate AUTOMATIC and MANUAL approval workflows — explains the 'Requires approval' state and what it means"
  ]
}
```
