---
name: managing-aws-costs
description: "Governs AWS cost management using Cost Explorer, Budgets, Cost Anomaly Detection, Data Exports (CUR 2.0), and Cost Optimization Hub for production AWS workloads. Use when designing FinOps foundations, configuring multi-account cost attribution, implementing automated budget enforcement, or building billing analytics pipelines on AWS."
---

## Function
Specialist in AWS FinOps and Cloud Financial Management for production AWS Organizations workloads using the AWS Cost Management 2026 service family.

## Version Context

**Technology**: AWS Cost Management — Cost Explorer, Budgets, CAD, Data Exports, COH
**Target edition**: AWS Cost Management 2026
**Research date**: 2026-08-28
**Support status**: Active

**Key 2025–2026 changes**:
- Cost Explorer 18-month ML forecasting (Nov 2025): model uses 36 months of history; AI-powered forecast explanations via Amazon Q Developer (console preview)
- Cost Anomaly Detection accelerated detection + expanded managed monitoring (Nov 2025): rolling 24-hour windows; AWS-managed monitors now cover linked accounts, tags, and categories
- Data Exports cross-account delivery (March 2026): CUR 2.0 / FOCUS / COH / Carbon exports deliverable to any authorized account's S3 bucket
- Cost Optimization Hub Cost Efficiency metric + Billing dashboard widget (Nov 2025 + July 2026)

**Deprecated / superseded**:
- Legacy CUR → replaced by CUR 2.0 via Data Exports (no official shutdown date announced)
- Cost Explorer standalone rightsizing → replaced by Cost Optimization Hub (single pane, deduplicated)
- "Custom monitors" (CAD) → renamed to "customer managed monitors" (terminology only)

⚠️ **CRITICAL — Agent Warning**:
This skill targets AWS Cost Management 2026.
Reject patterns from pre-2024 guidance: legacy CUR pipelines, separate billing console navigation,
Cost Explorer rightsizing as the primary recommendation tool.
Do not mix legacy CUR with CUR 2.0 / Data Exports patterns.

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — ✅⚠️🚫 mandatory, decision, and forbidden patterns
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 5 test scenarios for skill validation
- **[Verification Loop](#verification-loop)** — CLI validation commands with expected outputs
- **[Quick Reference](#quick-reference)** — Critical limits, quotas, and essential CLI commands
- **[External Resources](#external-resources)** — Official AWS documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

**Mandatory patterns for all AWS Cost Management implementations** (Complex tier — 7 patterns):

- **Activate Cost Allocation Tags and Cost Categories before the first invoice** — Billing data cannot be retroactively tagged. Without activation, cost attribution is permanently lost for that billing period. Define a mandatory tagging taxonomy (`project`, `environment`, `owner`, `cost-center`) enforced via Tag Policies at the Organization root. Activate user-defined tags in the Billing console. Create Cost Categories mapping account + tag combinations to financial units (BU → team → environment). Allow up to 24h for propagation.
  Verification: `aws ce list-cost-allocation-tags --status ACTIVE`

- **Enable Cost Anomaly Detection from the management account for org-wide coverage** — Create one AWS-managed monitor covering all linked accounts + a second for cost allocation tags and cost categories. Route individual alerts to SNS → AWS User Notifications → Slack/PagerDuty. Set combined absolute AND percentage thresholds to reduce alert noise. CAD is free; requires ≥10 days of history before detecting anomalies.
  Verification: `aws ce get-anomaly-monitors` — expect status ACTIVE.

- **Configure per-account Budgets with stacked threshold alerts and SCP Budget Actions** — Stack three alerts: 80% actual → SNS notification; 100% actual → AUTOMATIC Budget Action (SCP denying new resource provisioning on member account); 120% forecasted → MANUAL Budget Action (engineering review). First 2 action-enabled budgets/month are free; each additional = $0.10/day. From the management account, Budget Actions can apply SCPs cross-account; EC2/RDS stop actions cannot target other accounts.

- **Use CUR 2.0 via Data Exports for all new billing analytics pipelines — never legacy CUR** — CUR 2.0 has a fixed, stable 125-column schema (Parquet/CSV). Legacy CUR schema varies month-to-month as service usage and tags change, silently breaking Athena partition schemas and Redshift COPY jobs. AWS explicitly labels legacy CUR "Legacy" and recommends CUR 2.0 for all new setups.
  Verification: Billing console → Data Exports → status "Active / Healthy".

- **Enable Cost Optimization Hub from the management account** — COH is AWS's stated replacement for Cost Explorer's standalone rightsizing feature. It applies your actual RI/SP commercial terms and deduplicates across 18+ recommendation types, covering EC2, EBS, Lambda, Fargate, RDS, DynamoDB, Savings Plans, RIs, and more. Enable org-wide from the management account. Export recommendations via COH Data Exports → S3 for weekly savings tracking.

- **Apply least-privilege IAM for billing access using FinOps-persona permission sets** — Use IAM Identity Center permission sets per persona:

  | Persona | IAM Actions | Scope |
  |---|---|---|
  | FinOps Analyst | `ce:Get*`, `ce:List*`, `ce:Describe*` | Management account (read-only) |
  | Budget Admin | `budgets:*`, `ce:Get*` | Per-account or org-wide |
  | Billing Admin | `aws-portal:*`, `cur:*`, `ce:*` | Management account only |

  Migrate legacy `aws-portal:ViewBilling` policies to granular billing actions introduced with the unified console (May 2024 bulk migration tooling).

- **Deliver Data Exports to a dedicated analytics account — not the management account** — Cross-account delivery (March 2026 feature) allows CUR 2.0 / FOCUS 1.2 exports to target any authorized S3 bucket. Deliver to a separate FinOps/analytics account. This isolates billing data from management account operations and enables least-privilege analytics access. Partition S3 by year/month for Athena query cost efficiency.

### ⚠️ Ask First

**Architectural decisions requiring project context** (Complex tier — 4 decision points):

- **Cost Explorer API vs. Athena on CUR 2.0 for cost queries** — Ask: "Is this interactive/ad-hoc or an automated pipeline? Does it run >100×/day?" The Cost Explorer API costs $0.01 per paginated request — each page is a separate billable request. A pipeline querying daily data across 50 accounts × multiple services × 12 months can generate thousands of billable requests per run. Mandate Athena on CUR 2.0 for high-volume batch reporting. Reserve Cost Explorer API for low-volume interactive queries and forecasting.

  | Option | Optimizes | Sacrifices | Best When |
  |---|---|---|---|
  | Cost Explorer API | Developer simplicity, forecasting, recommendations | Cost ($0.01/request), limited granularity | Ad-hoc queries, RI/SP recommendations, <100 calls/day |
  | Athena on CUR 2.0 | Full line-item granularity, arbitrary SQL, cost-efficient at scale | Setup complexity, ~24h latency, Athena query costs ($5/TB, use Parquet to stay <$1/query) | High-volume pipelines, per-resource attribution, chargeback systems |

- **Compute Savings Plans vs. EC2 Instance Savings Plans vs. Standard Reserved Instances** — Ask: "Will the workload change instance type/size in the next 12 months? Does it involve Lambda or Fargate?" Compute SPs (broadest flexibility across EC2/Lambda/Fargate, up to 66% discount) for mixed/evolving workloads. EC2 Instance SPs (up to 72%, instance-family/region locked) for stable single-family EC2. Standard RIs (up to 72%, instance-type/AZ locked) only for fully predictable, never-changing, EC2-only workloads. Size using Cost Explorer's 30-day lookback recommendations.

- **Budget Actions: AUTOMATIC vs. MANUAL approval** — Ask: "Would an automated SCP enforcement in this account during off-hours block a critical production service?" AUTOMATIC for non-prod accounts with bounded, well-understood spend patterns. MANUAL for production accounts, shared-service accounts, and during the first 30 days of a new budget. If AUTOMATIC is used in production, scope the SCP narrowly to deny only new resource creation (`ec2:RunInstances`, `rds:CreateDBInstance`) — not actions on existing running resources.

- **CUR 2.0 only vs. CUR 2.0 + FOCUS 1.2 export** — Ask: "Does the team use multi-cloud FinOps tooling (Apptio, CloudZero, Flexera, Spot.io)?" If yes, add a FOCUS 1.2 export alongside CUR 2.0. FOCUS 1.2 is the standardized multi-cloud schema; AWS natively provides FOCUS 1.2 with AWS-specific columns (capacity reservation info, invoice IDs, virtual currency support). CUR 2.0 remains the higher-granularity option for AWS-only analytics.

### 🚫 Never Do

| Anti-Pattern | Why Prohibited | Correct Alternative |
|---|---|---|
| Build a new billing analytics pipeline on legacy CUR | Schema varies month-to-month as service usage and tags change, silently breaking Athena partition schemas, Redshift COPY jobs, and QuickSight datasets. AWS labels it "Legacy" and directs all new setups to CUR 2.0. | Create a CUR 2.0 export via Data Exports (Parquet, fixed 125-column schema). Migrate existing pipelines using the official CUR 2.0 migration guide. |
| Query Cost Explorer API at high frequency (>100×/day) for batch reporting | At $0.01/paginated request, a reporting pipeline querying 50 accounts × multiple services × daily granularity generates thousands of billable requests/run — the cost-monitoring tool itself becomes a material cost line item. | Use Athena on CUR 2.0 S3 data for batch/automated pipelines. Reserve the Cost Explorer API for low-volume interactive queries and forecasting only. |
| Build per-service rightsizing reports by aggregating EC2/RDS/Lambda recommendation APIs separately | Produces overlapping savings estimates — the same resource appears in multiple engines with inconsistent savings figures that do not account for RI/SP commercial terms, inflating savings projections. | Enable Cost Optimization Hub from the management account. COH applies your actual RI/SP terms and deduplicates across 18+ recommendation types — use it as the single source. |
| Expand to multi-account without first activating Cost Allocation Tags, Cost Categories, Budgets, and CAD | Billing data cannot be retroactively tagged; cost attribution gap is permanent after the first billing cycle. Directly violates WAF COST 1 and COST 3 design principles. | Enforce a pre-account-vending checklist: tagging taxonomy + Tag Policy at OU root; Cost Categories updated; per-account Budget + Budget Actions configured; CAD AWS-managed monitors auto-include new linked accounts. |
| Apply AUTOMATIC Budget Actions with a broad SCP scope in production accounts | A broad SCP (e.g., `Deny *` on EC2) applied automatically during off-hours can block critical running workloads, causing an unplanned production outage. | Scope the SCP to deny only new resource provisioning (`ec2:RunInstances`, `rds:CreateDBInstance`, etc.) — never deny actions on existing running resources. Use MANUAL approval for production accounts or test the SCP scope in non-prod first. |

---

## Integration Patterns

**Key integrations**:

- **Data Exports → S3 → Athena + QuickSight** — CUR 2.0 Parquet (cross-account delivery to analytics account) → AWS Glue Crawler (auto-schema, partitioned by year/month) → Athena SQL → QuickSight executive dashboards. Athena cost: typically <$1/query with Parquet columnar partitioning.

- **AWS Budgets → SNS → AWS User Notifications → Slack/PagerDuty** — Budget threshold alert → SNS topic → AWS Chatbot + EventBridge rules → multi-channel routing. For anomaly alerts, configure individual alerts (real-time, requires SNS) alongside daily/weekly email digest summaries.

- **Cost Optimization Hub → Data Exports → S3 → weekly savings report** — Schedule recurring COH Data Exports (Parquet/CSV) → S3 → Athena weekly query → savings opportunity report for architecture team review and RI/SP purchase decisions.

- **Budget Actions → SCP → Organizations** — Budget Action from management account applies SCP to member account when 100% actual threshold is crossed. SCP cross-account enforcement supported; EC2/RDS stop actions cannot target instances in other accounts.

**Common problems**:
- **Tags not in Cost Explorer after 24h** → Confirm the tags are applied to resources AND explicitly activated in the Billing console — these are two separate steps.
- **CAD not detecting anomalies in a new account** → Requires ≥10 days of historical data; normal for newly added accounts.
- **Budget Action stuck in "Requires approval" state** → MANUAL approval requires clicking "Run action" on the Alert details page in the Budgets console — it is not an automated chain.
- **CUR 2.0 S3 bucket receiving no files** → Verify the S3 bucket policy explicitly allows `bcm-data-exports.amazonaws.com` to write (cross-account delivery requires an explicit bucket policy grant).

---

## Verification Loop

Run after configuring any cost governance component:

### 1. Verify Cost Allocation Tags Active
```bash
aws ce list-cost-allocation-tags --status ACTIVE
# Expected: JSON array includes project, environment, owner, cost-center tags with Status: ACTIVE
# Exit code: 0
```

### 2. Verify Data Exports Active
```bash
aws bcm-data-exports list-exports
# Expected: exports with status "HEALTHY" for CUR 2.0 (and FOCUS 1.2 if configured)
# Exit code: 0
```

### 3. Verify Budgets and Actions Configured
```bash
aws budgets describe-budgets --account-id <ACCOUNT_ID>
# Expected: budget entries present; notifications at 80% / 100% / 120%
# Exit code: 0
```

### 4. Verify Cost Anomaly Detection Monitors Active
```bash
aws ce get-anomaly-monitors
# Expected: at least one AWS-managed monitor with MonitorType: DIMENSIONAL, status ACTIVE
# Exit code: 0
```

### 5. Manual Console Checks
```
Billing console → Cost allocation tags → "Active" status for all taxonomy keys
Billing console → Cost Anomaly Detection → monitors status "Active"
Billing console → Data Exports → export status "Active" / "Healthy"
Budgets console → Actions tab → action state "Standby" (AUTOMATIC) or awaiting trigger
Cost Optimization Hub → verify org-wide opt-in is active
```

**Troubleshooting**:
- `InvalidParameterException` on `ce:` commands → Verify IAM caller has explicit `ce:Get*` / `ce:List*` permissions (billing access is NOT included in default policies).
- `AccessDeniedException` on `aws-portal:*` → Migrate legacy billing IAM policies to the new granular actions (May 2024 unified console migration tooling).
- No files in analytics S3 bucket after 24h → Check S3 bucket policy includes `bcm-data-exports.amazonaws.com` as a trusted principal with `s3:PutObject` permission.

---

## Quick Reference

**Essential CLI commands**:
```bash
# List active cost allocation tags
aws ce list-cost-allocation-tags --status ACTIVE

# Get 18-month cost forecast
aws ce get-cost-forecast \
  --time-period Start=2026-09-01,End=2027-03-01 \
  --metric BLENDED_COST \
  --granularity MONTHLY

# List cost anomaly monitors
aws ce get-anomaly-monitors

# List Data Exports
aws bcm-data-exports list-exports

# Describe budgets for an account
aws budgets describe-budgets --account-id <ACCOUNT_ID>

# List cost categories
aws ce list-cost-categories
```

**Critical limits and costs**:

| Resource | Limit / Cost | Notes |
|---|---|---|
| AWS Budgets per management account | 20,000 max | Service quota |
| Free action-enabled budgets per account/month | 2 | Additional: $0.10/day each |
| Budget Actions per account | 100 max | |
| Cost Explorer API | $0.01 per paginated request | Each page = 1 billable request |
| Cost Allocation Tag propagation | Up to 24h after activation | Cannot backfill past billing periods |
| CAD historical data required | ≥10 days before detection starts | New accounts must wait |
| CAD anomaly detection latency | Up to 24h after usage event | |
| CUR 2.0 delivery cadence | Up to 3×/day | Finalized ~6th–7th of following month |
| Cost Explorer forecast horizon | 18 months (Nov 2025) | ML model uses 36 months of history |
| CAD AWS-managed monitors per mgmt account | 2 total (1 services + 1 linked/tag/category) | |
| Customer managed CAD monitors per mgmt account | 500 | 10 values per linked/tag monitor |

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/managing-aws-costs/
├── SKILL.md                              <- This file (index + guardrails)
└── blueprints/
    └── evaluation-scenarios.md           <- 5 test scenarios for skill validation
```

---

## External Resources

### Official Documentation
- [AWS Cost Management User Guide](https://docs.aws.amazon.com/cost-management/latest/userguide/) — Primary reference (2026)
- [Cost Explorer](https://docs.aws.amazon.com/cost-management/latest/userguide/ce-what-is.html) — Interactive analysis and forecasting
- [AWS Budgets](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html) — Alerts and Budget Actions
- [Budget Actions](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-controls.html) — SCP and IAM enforcement
- [Cost Anomaly Detection](https://docs.aws.amazon.com/cost-management/latest/userguide/getting-started-ad.html) — ML-based spend anomaly monitoring
- [Data Exports / CUR 2.0](https://docs.aws.amazon.com/cur/latest/userguide/what-is-data-exports.html) — Line-item billing data exports
- [CUR 2.0 Migration Guide](https://docs.aws.amazon.com/cur/latest/userguide/dataexports-migrate.html) — Migrating from legacy CUR
- [Cost Categories](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/manage-cost-categories.html) — Cost attribution grouping
- [Cost Allocation Tags](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/cost-alloc-tags.html) — Tag activation for cost attribution
- [Cost Optimization Hub](https://docs.aws.amazon.com/cost-management/latest/userguide/cost-optimization-hub.html) — Consolidated recommendations
- [Service Quotas](https://docs.aws.amazon.com/cost-management/latest/userguide/management-limits.html) — Verified service limits
- [Cost Explorer API Reference](https://docs.aws.amazon.com/aws-cost-management/latest/APIReference/) — API operations
- [Cost Explorer Pricing](https://aws.amazon.com/aws-cost-management/aws-cost-explorer/pricing/) — Per-request costs
- [WAF Cost Optimization Pillar](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html) — COST 1–11 design principles

### What's New (2025–2026)
- [Cost Explorer 18-month forecasting (Nov 2025)](https://aws.amazon.com/about-aws/whats-new/2025/11/cost-explorer-18-month-forecasting-ai-powered-forecasts/)
- [CAD accelerated detection (Nov 2025)](https://aws.amazon.com/about-aws/whats-new/2025/11/aws-cost-anomaly-detection-accelerates-anomaly/)
- [CAD expanded managed monitoring (Nov 2025)](https://aws.amazon.com/about-aws/whats-new/2025/11/aws-cost-anomaly-detection-managed-monitoring/)
- [Data Exports cross-account delivery (March 2026)](https://aws.amazon.com/about-aws/whats-new/2026/03/aws-data-exports-cross-account-delivery-cost/)
