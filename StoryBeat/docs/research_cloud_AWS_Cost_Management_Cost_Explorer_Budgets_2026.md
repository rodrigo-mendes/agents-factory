# AWS Cost Management: Cost Explorer & Budgets — Cloud Architecture Research (2026)

> Anti-hallucination research base. Every fact is sourced to official AWS documentation
> (docs.aws.amazon.com, aws.amazon.com What's New, AWS blogs) with an access or publish date.
> Sources older than 12 months are flagged ⚠️ >12mo but retained when they are the current stable
> edition. Items that could not be confirmed against an official source are tagged `[unverified]`.
> Do not treat this file as legal or compliance advice.

## Metadata

```yaml
Full_Name: "AWS Cost Management — Cost Explorer & Budgets"
Cloud_Provider: "AWS"
Architecture_Domain: "Cost Management Architecture - Cost Explorer & Budgets"
Target_Edition: "AWS Cost Management 2026"
Architecture_Context: "FinOps and Cloud Financial Management for production AWS workloads"
Official_Source_URL: "https://docs.aws.amazon.com/cost-management/latest/userguide/"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-08-28"
Currency_Threshold: "2027-08-28"
Research_Depth: "exhaustive"
```

---

## Executive Summary

The **AWS Billing and Cost Management** service family is the unified platform for understanding,
controlling, and optimizing AWS spend. As of 2026 it spans ten major capabilities: Cost Explorer,
Data Exports (CUR 2.0 + FOCUS), Cost Anomaly Detection, Cost Categories, Cost Allocation Tags,
AWS Budgets (with Budget Actions), Cost Optimization Hub, Savings Plans, Reservations, and
Billing Conductor. The November 2023 **unified console** consolidated the former separate
Billing and Cost Management consoles into a single surface.
Source: https://aws.amazon.com/about-aws/whats-new/2023/11/unified-billing-cost-management-console

The three most impactful 2025–2026 changes are:

1. **Cost Explorer 18-month forecasting** (Nov 2025): ML model now uses up to 36 months of
   historical data and the forecast horizon extended from 12 to 18 months; explainable
   AI-powered forecasts via Amazon Q Developer added (console preview).
   Source: https://aws.amazon.com/about-aws/whats-new/2025/11/cost-explorer-18-month-forecasting-ai-powered-forecasts/

2. **Cost Anomaly Detection accelerated detection + expanded managed monitoring** (Nov 2025):
   rolling 24-hour detection windows (down from 24h batch) and AWS-managed monitors now cover
   all linked accounts, cost allocation tags, or cost categories — not just AWS services.
   Source: https://aws.amazon.com/about-aws/whats-new/2025/11/aws-cost-anomaly-detection-accelerates-anomaly/
   + https://aws.amazon.com/about-aws/whats-new/2025/11/aws-cost-anomaly-detection-managed-monitoring/

3. **Data Exports cross-account delivery** (March 2026): Standard/CUR 2.0/FOCUS/COH/Carbon
   exports can now be delivered to any authorized account's S3 bucket.
   Source: https://aws.amazon.com/about-aws/whats-new/2026/03/aws-data-exports-cross-account-delivery-cost/

The three most critical FinOps guardrails for any production workload are: (1) **Cost Allocation
Tags + Cost Categories activated and applied** to all chargeable resources before the first
invoice; (2) **Budgets with forecast alerts and Budget Actions** on all accounts, including
SCP-based automated enforcement; and (3) **Cost Anomaly Detection AWS-managed monitors enabled
in the management account** for org-wide coverage. Any architecture lacking these three elements
has no cost governance before reaching any Well-Architected Cost Optimization best practice.

---

## Cloud Architecture Glossary

```
Term: Cost Explorer
Definition: Interactive AWS console and API (ce.) for visualizing, analyzing, and forecasting
  cost and usage data. Supports 14-month daily history (opt-in: 38 months monthly), 18-month
  ML forecasting, rightsizing recommendations, and RI/SP purchase recommendations.
Provider Docs Section: https://docs.aws.amazon.com/cost-management/latest/userguide/ce-what-is.html
Architect Usage: Ad-hoc cost analysis, trend detection, RI/SP sizing, budget variance
  investigations. For automation, use the ce. API ($0.01/paginated request).
Common Confusion: Confused with CUR/Data Exports. Cost Explorer is an interactive lens over
  aggregated data; CUR/Data Exports is the raw line-item feed for downstream analytics.
```

```
Term: AWS Budgets
Definition: Proactive alerting service that fires SNS/email notifications when actual or
  forecasted spend/usage/RI-coverage/SP-coverage crosses configurable thresholds.
  Six budget types: cost, usage, RI utilization, RI coverage, SP utilization, SP coverage.
Provider Docs Section: https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html
Architect Usage: Set per-account, per-service, or per-tag cost ceilings with forecast alerts.
  Combine with Budget Actions for automated enforcement (apply IAM policy, SCP, stop EC2/RDS).
Common Confusion: Budgets alert on thresholds — they do not prevent spending. Use Budget Actions
  for enforcement. The first 2 action-enabled budgets/month are free; each additional = $0.10/day.
```

```
Term: Budget Actions
Definition: Automated enforcement tied to a Budget threshold. Three action types: apply an IAM
  policy, apply a Service Control Policy (SCP), or stop specific EC2/RDS instances (via SSM).
  Supports AUTOMATIC or MANUAL approval workflows.
Provider Docs Section: https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-controls.html
Architect Usage: Use SCP actions from the management account for cross-account budget enforcement.
  EC2/RDS stop actions cannot target instances in other accounts — only SCPs can cross accounts.
Common Confusion: Manual approval ("Requires approval" state) requires the user to click
  "Run action" in the Budget alert detail page — it is not an automated approval chain.
```

```
Term: Cost Anomaly Detection (CAD)
Definition: ML-based service that learns historical spend patterns and alerts when anomalous
  spend is detected. Free service. Four monitor dimensions: AWS services, linked accounts,
  cost allocation tags, cost categories.
Provider Docs Section: https://docs.aws.amazon.com/cost-management/latest/userguide/getting-started-ad.html
Architect Usage: Enable from the management account for org-wide coverage. Use the AWS-managed
  monitor for the broadest automatic coverage. Add SNS for real-time (individual) alerts;
  email subscriptions support daily/weekly digests.
Common Confusion: CAD requires ≥10 days of historical data before it begins detecting anomalies.
  It only analyzes Usage charge type / NetUnblendedCost — not all charge types.
```

```
Term: Cost Optimization Hub (COH)
Definition: Consolidated dashboard of 18+ optimization recommendations (rightsizing, idle
  resources, Savings Plans, RIs, Graviton migration, etc.) across accounts and regions.
  Launched Nov 2023; free service. Recommendation engine is AWS Compute Optimizer.
Provider Docs Section: https://docs.aws.amazon.com/cost-management/latest/userguide/cost-optimization-hub.html
Architect Usage: Use COH as the single pane for recommendations — AWS explicitly recommends COH
  over Cost Explorer's standalone rightsizing feature. Enable from the management account.
  Export recommendations to S3 via Data Exports for reporting/audit.
Common Confusion: COH consolidates and deduplicates savings estimates — viewing the same
  resource's savings in Compute Optimizer and COH may look different because COH applies your
  actual RI/SP commercial terms.
```

```
Term: Data Exports / CUR 2.0
Definition: AWS's recommended successor to the legacy Cost and Usage Report. Delivers raw
  line-item billing data to S3 (Parquet/CSV) with a fixed, stable schema (125 columns).
  Also supports FOCUS 1.0/1.2 (FinOps Open Cost & Usage Spec), COH recommendations, and
  carbon emissions export types.
Provider Docs Section: https://docs.aws.amazon.com/cur/latest/userguide/what-is-data-exports.html
Architect Usage: Use CUR 2.0 via Data Exports for Athena/Redshift/QuickSight analytics
  pipelines. Migrate from legacy CUR (schema varies month-to-month, not recommended for new
  setups). FOCUS 1.2 export is the standard for multi-cloud FinOps tooling.
Common Confusion: Legacy CUR is still available but is explicitly labeled "Legacy" and
  no hard shutdown date has been announced [unverified: sunset date].
```

```
Term: Cost Categories
Definition: Rule-based grouping engine that maps AWS costs into custom named categories
  (e.g., "team:payments", "env:prod") using account, tag, service, charge type, or other
  cost categories as dimensions. Appears as filter/grouping in Cost Explorer, Budgets, CUR,
  and Cost Anomaly Detection.
Provider Docs Section: https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/manage-cost-categories.html
Architect Usage: Build a cost attribution hierarchy (BU → team → environment) before
  cost allocation tags are exhaustive. Up to 24h to populate after create/edit.
Common Confusion: Cost Categories is a Billing & Cost Management construct — it does not
  tag resources in AWS; it remaps cost records at billing computation time.
```

```
Term: Cost Allocation Tags
Definition: Key-value metadata on AWS resources (two types: user-defined and AWS-generated)
  that must be explicitly activated in the Billing console before appearing in Cost Explorer
  and CUR. Activation propagates within ~24h.
Provider Docs Section: https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/cost-alloc-tags.html
Architect Usage: Define a mandatory tagging taxonomy (project, environment, owner, cost-center)
  enforced via SCPs/Tag Policies in AWS Organizations. Auto-activated tags (e.g., createdBy)
  do not count toward the tag quota.
Common Confusion: Tags applied to resources are NOT automatically available for cost allocation.
  Activation in the Billing console is a separate, explicit step.
```

```
Term: AWS Billing Conductor
Definition: Fully managed custom billing service for AWS Channel Partners and organizations
  with chargeback requirements. Creates pro forma (alternate) billing data by applying custom
  pricing rules to billing groups (subsets of Organization accounts).
Provider Docs Section: https://docs.aws.amazon.com/billingconductor/latest/userguide/what-is-billingconductor.html
Architect Usage: Use for MSP/reseller multi-tenant scenarios where end-customers need to see
  custom rates (markups, custom EDP). Accounts in a billing group see pro forma data.
  CUR 2.0 can be generated against pro forma data for downstream analytics.
Common Confusion: Billing Conductor does not affect the actual AWS invoice — it generates
  a separate pro forma view. The management account still receives and pays the real invoice.
```

```
Term: AWS Savings Plans
Definition: Flexible commitment-based pricing model that provides up to 66% discount vs.
  On-Demand in exchange for a consistent usage commitment ($/hr) over 1 or 3 years. Three types:
  Compute Savings Plans (broadest scope: EC2, Lambda, Fargate), EC2 Instance Savings Plans
  (specific instance family/region), and SageMaker Savings Plans.
Provider Docs Section: https://docs.aws.amazon.com/savingsplans/latest/userguide/what-is-savings-plans.html
Architect Usage: Prefer Compute Savings Plans for flexibility across services. Use Cost Explorer's
  Savings Plans recommendations (7/30/60-day lookback) to size commitments. Apply in the
  management account for org-wide benefit via consolidated billing.
Common Confusion: Savings Plans are not the same as Reserved Instances — SPs commit to a spend
  rate ($/hr), not a specific instance type/size. SPs are applied automatically; RIs require
  manual instance-type matching.
```

---

## Architecture Guardrails

### ✅ Mandatory Patterns

**Activate Cost Allocation Tags and Cost Categories Before First Invoice**
- Pillar Alignment: Cost Optimization — COST 1 (Implement cloud financial management) + COST 3 (Monitor usage and cost)
- Why: "Analyze and attribute expenditure" is design principle #5 of the Cost Optimization Pillar. Without activated tags, cost attribution is impossible retroactively — billing data cannot be backfilled.
  Source: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/design-principles.html
- AWS Services: Cost Allocation Tags (Billing console activation), AWS Cost Categories, AWS Organizations Tag Policies
- Architecture Decision:
  Define a mandatory tagging taxonomy (minimum: `project`, `environment`, `owner`, `cost-center`) enforced via Tag Policies at the Organization root. Activate user-defined tags in the Billing console. Create Cost Categories mapping account + tag combinations to financial units (BU → team → environment). Allow up to 24h for tag propagation.
- Verification:
  Billing console → Cost allocation tags → check "Active" status. Cost Explorer → Group by tag → verify attribution appears. CLI: `aws ce list-cost-allocation-tags --status ACTIVE`
- Source: https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/cost-alloc-tags.html

**Enable Cost Anomaly Detection from the Management Account (Org-Wide)**
- Pillar Alignment: Cost Optimization — COST 3 (Monitor usage and cost)
- Why: Unexpected spend events are a top cause of budget overruns in multi-account organizations. CAD detects anomalies up to 24h after the spend event — faster than any manual review cycle.
  Source: https://docs.aws.amazon.com/cost-management/latest/userguide/getting-started-ad.html
- AWS Services: AWS Cost Anomaly Detection, Amazon SNS, AWS User Notifications
- Architecture Decision:
  From the management account, enable one AWS-managed monitor covering all linked accounts. Enable a second AWS-managed monitor for cost allocation tags and cost categories. Configure individual alerts → SNS → notification routing (Slack/PagerDuty via AWS User Notifications). Set absolute + percentage thresholds combined with AND to reduce noise.
- Verification:
  Billing console → Cost Anomaly Detection → verify monitors status "Active". SNS → confirm subscriptions are confirmed.
- Source: https://docs.aws.amazon.com/cost-management/latest/userguide/getting-started-ad.html

**Configure Budgets with Forecast Alerts and SCP Budget Actions**
- Pillar Alignment: Cost Optimization — COST 2 (Govern usage)
- Why: Alerts alone do not prevent overspend. Budget Actions applying SCPs are the only native AWS mechanism to automatically restrict provisioning when spend approaches a limit.
  Source: https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-controls.html
- AWS Services: AWS Budgets, AWS Organizations (SCPs), Amazon SNS
- Architecture Decision:
  Create per-account monthly cost budgets from the management account. Stack three threshold alerts: 80% actual → SNS notification; 100% actual → AUTOMATIC Budget Action (SCP deny resource provisioning on member account); 120% forecasted → MANUAL Budget Action (escalation review). First 2 action-enabled budgets/account are free.
- Verification:
  Budgets console → Actions tab → verify action state "Standby". Test by simulating a threshold crossing in a non-prod account. CloudTrail → `budgets.amazonaws.com` events confirm action execution.
- Source: https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-controls.html

**Use CUR 2.0 via Data Exports for All Billing Analytics Pipelines**
- Pillar Alignment: Cost Optimization — COST 3 (Monitor usage and cost)
- Why: Legacy CUR schema varies month-to-month based on service usage and tag activation, breaking downstream Athena/Redshift queries. CUR 2.0 has a fixed, stable 125-column schema in Parquet/CSV, delivered via Data Exports — explicitly labeled "new and recommended" by AWS.
  Source: https://docs.aws.amazon.com/cur/latest/userguide/cur-overview.html
- AWS Services: AWS Data Exports, Amazon S3, Amazon Athena, Amazon QuickSight
- Architecture Decision:
  Create a CUR 2.0 export (Parquet, daily granularity) delivered cross-account to a central analytics S3 bucket (March 2026 feature). Add a FOCUS 1.2 export for multi-cloud FinOps tooling. Partition S3 by year/month for Athena cost efficiency. Use QuickSight for executive dashboards.
- Verification:
  Data Exports console → confirm export status "Active". S3 → verify Parquet files arrive within 24h. Athena → `SELECT count(*) FROM cost_and_usage_report` returns results.
- Source: https://docs.aws.amazon.com/cur/latest/userguide/what-is-data-exports.html

---

### ⚠️ Architectural Decisions

**Cost Explorer API vs. Athena on CUR 2.0 for Cost Queries**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Cost Explorer API | `ce.us-east-1.amazonaws.com` | Developer simplicity, pre-aggregated data, forecasting | Cost ($0.01/request), granularity limited to daily, no raw line items | Ad-hoc analysis, RI/SP recommendations, forecasting, low-volume automation |
  | Athena on CUR 2.0 | Athena + S3 (Data Exports) | Full line-item granularity, arbitrary SQL, cost-efficient at scale | Setup complexity, ~24h data latency, Athena query costs | High-volume reporting pipelines, per-resource attribution, chargeback systems |

- Cost Profile: Cost Explorer API = $0.01/paginated request (each page billable). Athena = $5.00/TB scanned (use columnar Parquet + partitioning to keep < $1/query).
- Lock-in Assessment: CUR 2.0 exports to S3 (portable). Cost Explorer API is AWS-only with no equivalent cross-cloud.
- Architect Instruction: "Ask whether this is a human-interactive query or an automated pipeline. If automated and runs >100×/day, mandate Athena on CUR 2.0 to avoid a Cost Explorer API cost spiral."
- Source: https://aws.amazon.com/aws-cost-management/aws-cost-explorer/pricing/ + https://docs.aws.amazon.com/cur/latest/userguide/what-is-data-exports.html

**Savings Plans vs. Reserved Instances for Compute Commitment**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Compute Savings Plans | Savings Plans (Compute) | Flexibility across EC2/Lambda/Fargate; applies automatically | Slightly lower max discount vs. EC2 Standard RIs | Mixed or evolving workloads; Fargate/Lambda heavy |
  | EC2 Instance Savings Plans | Savings Plans (EC2 Instance) | Higher discount within one instance family/region | Instance family and region locked | Stable EC2 workloads with predictable instance family |
  | EC2 Standard Reserved Instances | Reserved Instances | Highest discount (up to 72%) | Specific instance type/AZ locked; no cross-service flexibility | Fully predictable, single-instance-type steady-state workloads |

- Cost Profile: Compute SPs up to 66% savings; EC2 Instance SPs up to 72%; Standard RIs up to 72% with AZ/type lock.
- Lock-in Assessment: All three are AWS-specific commitment models. Convertible RIs and Compute SPs offer most flexibility within AWS.
- Architect Instruction: "Ask whether the workload's instance type/size is expected to change in the next 12 months. If yes, recommend Compute Savings Plans. If workload is 100% stable and EC2-only, Standard RIs maximize savings."
- Source: https://docs.aws.amazon.com/savingsplans/latest/userguide/what-is-savings-plans.html + https://docs.aws.amazon.com/cost-management/latest/userguide/ce-ris.html

**Budget Actions: AUTOMATIC vs. MANUAL Approval**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | AUTOMATIC | Budget Actions | Speed of enforcement; zero human latency | Risk of blocking legitimate workloads without review | Non-prod accounts; well-understood, bounded spend patterns |
  | MANUAL | Budget Actions | Human oversight before enforcement; avoids false-positive shutdowns | Relies on on-call engineer being available to approve | Prod accounts; shared-service accounts; first 30 days of a new budget |

- Architect Instruction: "Ask whether an automated SCP enforcement in this account during off-hours would block a critical production service. If yes, mandate MANUAL approval or scope the SCP narrowly to deny only new resource creation, not existing running resources."
- Source: https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-action-review.html

---

### 🚫 Anti-Patterns

**New Billing Analytics Pipeline on Legacy CUR**
- Risk Level: HIGH
- Why: Legacy CUR violates the Cost Optimization Pillar principle "Analyze and attribute expenditure" because its schema changes month-to-month as service usage and tags vary — breaking Athena partition schemas, Redshift COPY jobs, and QuickSight datasets silently. AWS explicitly labels it "Legacy" and directs all new setups to CUR 2.0 via Data Exports.
  Source: https://docs.aws.amazon.com/cur/latest/userguide/cur-overview.html
- Instead: Create a CUR 2.0 export via Data Exports (Parquet, fixed 125-column schema). Migrate existing pipelines using the official migration guide.
  Source: https://docs.aws.amazon.com/cur/latest/userguide/dataexports-migrate.html
- Detection: Data Exports console → Legacy data exports tab — any active legacy export is an anti-pattern for new setups. CLI: `aws cur describe-report-definitions` returning active reports.
- Impact: Cost overrun (pipeline maintenance), incorrect attribution (schema drift), compliance risk (incomplete audit data).
- Source: https://docs.aws.amazon.com/cur/latest/userguide/cur-overview.html

**Querying Cost Explorer API at High Frequency for Batch Reporting**
- Risk Level: HIGH
- Why: At $0.01 per paginated API request, a pipeline querying `GetCostAndUsage` with daily granularity across 12 months × 50 accounts × multiple services can generate thousands of billable requests per run, creating a cost-monitoring service that itself becomes a significant cost line item.
  Source: https://aws.amazon.com/aws-cost-management/aws-cost-explorer/pricing/
- Instead: Use Athena queries on CUR 2.0 exports in S3. Cost Explorer API should be reserved for low-volume, interactive, or forecast-only queries.
- Detection: Cost Explorer → API call costs appearing as a measurable line item in the billing data. CloudTrail → `ce:GetCostAndUsage` call volume.
- Impact: Cost overrun (self-referential cost monitoring spend spiral).
- Source: https://aws.amazon.com/aws-cost-management/aws-cost-explorer/pricing/

**Building Per-Service Rightsizing Reports Instead of Using Cost Optimization Hub**
- Risk Level: MEDIUM
- Why: Aggregating rightsizing recommendations per-service (EC2 Console, RDS Console, Lambda Console) without deduplication produces overlapping savings estimates — the same resource may appear in multiple recommendation engines with inconsistent savings figures that don't account for the customer's RI/SP commercial terms. AWS explicitly directs architects to Cost Optimization Hub as the single pane.
  Source: https://docs.aws.amazon.com/cost-management/latest/userguide/ce-rightsizing.html
- Instead: Enable Cost Optimization Hub from the management account. Export recommendations to S3 via Data Exports for audit and tracking.
- Detection: No Cost Optimization Hub opt-in in the management account. Manual aggregation scripts querying multiple recommendation APIs separately.
- Impact: Cost overrun (missed savings from double-counting), incorrect savings reporting.
- Source: https://docs.aws.amazon.com/cost-management/latest/userguide/cost-optimization-hub.html

**No Cost Governance Before Multi-Account Expansion**
- Risk Level: CRITICAL
- Why: Creating member accounts without first activating Cost Allocation Tags, Cost Categories, and Budgets means the cost attribution gap is permanent — billing data cannot be retroactively tagged. Within one billing cycle the management account loses visibility into per-team/per-project spend. This directly violates COST 1 and COST 3.
  Source: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/design-principles.html
- Instead: Enforce a pre-account-vending checklist: (1) tagging taxonomy + Tag Policy enforced at OU; (2) Cost Categories updated; (3) Budget + Budget Actions configured; (4) CAD monitor covers new account automatically (AWS-managed monitors include new accounts).
- Detection: Billing console → Cost Explorer → filter by "linked account" → accounts with no tag attribution. Accounts with 0 active cost allocation tags.
- Impact: Compliance violation (chargeback/showback failure), cost overrun (unattributed spend invisible until month-end invoice).
- Source: https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html

---

## Cloud-Native Design Patterns

**Multi-Account Cost Attribution with Consolidated Billing**
- Category: Data
- Problem: In a large AWS Organization, per-team and per-project cost attribution is opaque — the consolidated invoice shows total spend but not which team/workload drove it.
- Solution on AWS:
  Tag Policy at Organization root (mandatory tag keys) → Cost Allocation Tags activation (Billing console) → Cost Categories (map account+tag to financial unit) → CUR 2.0 export (Data Exports → S3 Parquet) → Athena + QuickSight per-team dashboard. Cost Anomaly Detection with tag-based monitor fires on per-team anomalies.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Granularity | Full line-item attribution per resource | Tag compliance requires enforcement (Tag Policy + SCPs) |
  | Latency | Daily data in CUR 2.0; Cost Explorer reflects within 24h | Not real-time; cost events visible next day |
  | Portability | FOCUS 1.2 export supports multi-cloud FinOps tools | CUR 2.0 schema is AWS-specific |

- Source: https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/consolidated-billing.html + https://docs.aws.amazon.com/cur/latest/userguide/what-is-data-exports.html

**Automated Budget Enforcement — Spend-Triggered SCP Guardrail**
- Category: Resilience
- Problem: Teams overspend in member accounts because there is no automated enforcement — only email alerts that may be ignored or missed outside business hours.
- Solution on AWS:
  AWS Budgets (monthly cost budget per account, managed from management account) → AUTOMATIC Budget Action at 100% actual → apply SCP to member account denying resource provisioning (`ec2:RunInstances`, `rds:CreateDBInstance`, etc.) → SNS alert to team lead. Budget Action reversed manually once the team acknowledges and a corrective plan is agreed.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Enforcement speed | Automatic, 24/7, no human in the loop | May block legitimate urgent workloads if SCP is too broad |
  | Cost | First 2 action-enabled budgets free; $0.10/day per additional | Negligible vs. cost of uncontrolled spend |
  | Reversibility | Action can be reversed + reset from console | Reversal is manual — requires engineering access |

- Source: https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-controls.html

**FinOps Reporting Pipeline — CUR 2.0 + Athena + QuickSight**
- Category: Data
- Problem: Cost Explorer's interactive UI is sufficient for ad-hoc queries but cannot serve 50+ stakeholders with custom views, historical trends, and chargeback reports.
- Solution on AWS:
  Data Exports (CUR 2.0 Parquet → S3, cross-account delivery to central analytics account) → AWS Glue Crawler (auto-schema, partitioned by year/month) → Athena (SQL queries per team/project/environment) → QuickSight (dashboards for FinOps team + business units). Cost Optimization Hub recommendations exported via Data Exports for weekly savings opportunity report.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Query cost | Parquet columnar = low Athena scan cost per query | Initial setup complexity (Glue, S3 partitioning, IAM) |
  | Freshness | Daily CUR 2.0 delivery; up to 3×/day | Not real-time; 8–24h latency |
  | Portability | FOCUS 1.2 allows same pipeline to support multi-cloud | Requires separate FOCUS export configuration |

- Source: https://docs.aws.amazon.com/cur/latest/userguide/what-is-data-exports.html + https://aws.amazon.com/about-aws/whats-new/2026/03/aws-data-exports-cross-account-delivery-cost/

---

## Security Architecture

**Least-Privilege IAM for Billing and Cost Management Access**
- AWS Services: AWS IAM, AWS Organizations, Cost Management console
- Architecture: Billing and Cost Management access is controlled via IAM `ce:*`, `aws-portal:*`, and `budgets:*` action namespaces. The unified console (Nov 2023) introduced fine-grained billing IAM actions — architects must migrate legacy `aws-portal:ViewBilling` policies to the new granular actions. Use IAM Identity Center permission sets for FinOps personas (read-only analyst vs. budget admin vs. billing admin).

  | Persona | IAM Actions | Scope |
  |---------|-------------|-------|
  | FinOps Analyst | `ce:Get*`, `ce:List*`, `ce:Describe*` (read-only) | Management account |
  | Budget Admin | `budgets:*`, `ce:Get*` | Per-account or org-wide |
  | Billing Admin | `aws-portal:*`, `cur:*`, `ce:*` | Management account only |

- Compliance Alignment: CIS AWS Benchmark — ensure billing access is restricted to named roles, not broad `*:*` wildcards. SOC 2 CC6.1 — least-privilege access to financial data.
- Source: https://docs.aws.amazon.com/cost-management/latest/userguide/ce-api.html + https://aws.amazon.com/about-aws/whats-new/2024/05/aws-console-based-bulk-policy-migration-billing-cost-management-console-access/

**Management Account Budget Enforcement via SCPs**
- AWS Services: AWS Organizations (SCPs), AWS Budgets (Budget Actions), AWS CloudTrail
- Architecture: Budget Actions from the management account can apply SCPs to member accounts when budget thresholds are crossed. The SCP pattern restricts new resource provisioning (not existing running resources) to avoid cascading outages. Combine with CloudTrail org trail in the management account to audit all budget action executions. Store action history beyond the 60-day console window in CloudTrail → S3.
- Compliance Alignment: Well-Architected Cost Optimization COST 2 — govern usage. SOC 2 CC7.2 — detection and response to cost anomalies as a security-adjacent control.
- Source: https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-controls.html + https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-action-review.html

---

## Operational Patterns

**FinOps Cadence — Weekly Review Automation**
- RTO/RPO (if applicable): N/A (reporting, not availability)
- AWS Services: Cost Explorer (API), AWS Budgets, Cost Optimization Hub (Data Exports), Amazon SNS, AWS Chatbot
- Cost Profile: Low — Cost Explorer API ~$5–20/month for automated weekly pulls; Athena queries on CUR 2.0 < $1/week with Parquet partitioning.
- Automation:

  | Step | Automate | Manual Decision Point |
  |------|----------|-----------------------|
  | Weekly cost summary report | Lambda → `GetCostAndUsage` → SNS/Slack | FinOps team reviews top 5 cost drivers |
  | Savings opportunity report | Data Exports (COH) → Athena → report | Architecture team selects RIs/SPs to purchase |
  | Anomaly investigation | CAD → SNS → AWS Chatbot alert | On-call engineer decides if anomaly is expected |
  | Budget threshold crossed | Budget Action (automatic at 100%) | Manual reversal + corrective plan after acknowledgement |

- Source: https://docs.aws.amazon.com/cost-management/latest/userguide/ce-api.html + https://docs.aws.amazon.com/cost-management/latest/userguide/cost-optimization-hub.html

**Month-End FinOps Close**
- RTO/RPO (if applicable): N/A
- AWS Services: Data Exports (CUR 2.0), Athena, Cost Categories, AWS Budgets
- Cost Profile: Low — primarily Athena query costs on existing CUR 2.0 S3 data.
- Automation:

  | Step | Automate | Manual Decision Point |
  |------|----------|-----------------------|
  | Wait for finalized CUR 2.0 | Scheduled Lambda on 8th of month (adjustments reflected ~6th–7th) | Confirm invoice matches CUR totals |
  | Per-team chargeback report | Athena query (Cost Categories filter) → QuickSight | Finance team approves allocations |
  | Commitment utilization review | Cost Explorer (RI/SP utilization budgets) | Decision: convert/exchange underutilized RIs |
  | Next-month forecast | `GetCostForecast` → 18-month horizon | Budget owners approve or request scope reduction |

- Source: https://docs.aws.amazon.com/cur/latest/userguide/what-is-cur.html + https://docs.aws.amazon.com/cost-management/latest/userguide/ce-forecast.html

---

## Reference Architectures

**Multi-Account FinOps Foundation**
- Context: Enterprise AWS Organization (10–500+ accounts) requiring full cost attribution, proactive alerts, anomaly detection, and automated enforcement.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Taxonomy | Tag Policies (Organizations) | Enforce mandatory tag keys at OU root |
  | Attribution | Cost Allocation Tags + Cost Categories | Map spend to financial units (BU/team/env) |
  | Raw data | Data Exports — CUR 2.0 (Parquet, cross-account S3) | Line-item billing data for analytics |
  | Standards | Data Exports — FOCUS 1.2 | Multi-cloud FinOps tooling interoperability |
  | Analytics | Athena + AWS Glue + QuickSight | Self-service cost dashboards |
  | Alerting | AWS Budgets (forecast + actual) + CAD | Proactive spend + anomaly alerts |
  | Enforcement | Budget Actions (SCP) | Automated provisioning restriction at threshold |
  | Optimization | Cost Optimization Hub (management account) | Consolidated rightsizing + commitment recommendations |
  | Reporting | COH Data Exports → S3 | Weekly savings opportunity tracking |

- Key Decisions: (1) Cross-account S3 delivery target — choose a dedicated FinOps/analytics account, not the management account. (2) AUTOMATIC vs MANUAL Budget Actions per account risk tier. (3) Savings Plans vs. RI commitment type per workload stability.
- Scaling Path: Start with management-account-only Cost Optimization Hub → expand to all member accounts. Add FOCUS 1.2 export when multi-cloud tools are adopted. Enable hourly Cost Explorer granularity only for accounts with >$10k/day spend.
- Source: https://docs.aws.amazon.com/cost-management/latest/userguide/cost-optimization-hub.html + https://aws.amazon.com/about-aws/whats-new/2026/03/aws-data-exports-cross-account-delivery-cost/

**MSP / Reseller Chargeback Architecture (Billing Conductor)**
- Context: AWS Channel Partner or enterprise with internal chargeback requirements needing custom per-team or per-customer pricing distinct from the actual AWS invoice.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Custom pricing | AWS Billing Conductor | Apply pricing rules + custom line items to billing groups |
  | Pro forma data | CUR 2.0 (Billing Conductor pro forma export) | Custom-priced line-item data per billing group |
  | Analytics | Athena + QuickSight | Per-customer/team invoicing dashboards |
  | Actual cost | Standard CUR 2.0 (management account) | True AWS cost for margin analysis |
  | Alerts | AWS Budgets per billing group | Per-customer spend alerts |

- Key Decisions: (1) Standard vs. transfer billing groups — transfer group moves a full account's billing to a different payer. (2) Pricing plan design — markup rules, custom line items, discount pass-through. (3) Run both standard CUR 2.0 (true cost) and pro forma CUR 2.0 (billed cost) for margin tracking.
- Scaling Path: Start with a single billing group for one team/customer → expand billing groups as customer base grows. Billing Conductor billing group quota: 20,000 budgets at management account level still applies to the underlying accounts.
- Source: https://docs.aws.amazon.com/billingconductor/latest/userguide/what-is-billingconductor.html

---

## Provider Differentiators

**Native FOCUS 1.2 Support in Data Exports**
AWS is among the first hyperscalers to provide a GA FOCUS 1.2 export (FinOps Open Cost & Usage Specification) natively, with AWS-specific columns added for capacity reservation information, invoice IDs for reconciliation, and virtual currency support. This enables multi-cloud FinOps tooling (Apptio, CloudZero, Flexera, Spot.io) to ingest AWS billing data in a standardized schema alongside Azure and GCP data without custom ETL.
Source: https://docs.aws.amazon.com/cur/latest/userguide/what-is-data-exports.html

**Cost Optimization Hub — Deduplicated, Commercial-Term-Aware Recommendations**
Unlike per-service recommendation engines (EC2 Console rightsizing, RDS recommendations), Cost Optimization Hub applies the customer's actual RI/SP commercial terms when computing estimated savings, then deduplicates overlapping recommendations across the 18+ recommendation types. This avoids the common pitfall where the sum of per-service savings estimates exceeds what is achievable due to double-counting.
Source: https://docs.aws.amazon.com/cost-management/latest/userguide/cost-optimization-hub.html

**Budget Actions — SCP Enforcement Without External Tooling**
AWS Budgets Budget Actions can apply Service Control Policies directly from the management account when a budget threshold is crossed, providing automated cost enforcement at the organizational policy layer — without requiring a third-party FinOps platform, custom Lambda, or manual SCP management. This is unique to AWS's Organizations + Budgets integration.
Source: https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-controls.html

**18-Month AI-Powered Forecasting with Explainability**
Cost Explorer's ML forecasting model (Nov 2025) uses up to 36 months of historical data and a horizon of 18 months — the longest native forecast horizon among the major hyperscalers at time of writing. The "Analyze with Amazon Q Developer" feature provides plain-language explanations of forecast drivers in the console, reducing the FinOps analyst skill requirement for root-cause interpretation.
Source: https://aws.amazon.com/about-aws/whats-new/2025/11/cost-explorer-18-month-forecasting-ai-powered-forecasts/

---

## Scenario Coverage

**Standard Case**: Multi-account enterprise organization with consolidated billing, shared services account, and per-team chargeback requirements.
- Approach: Tag Policy at Organization root → Cost Categories (BU → team → environment) → CUR 2.0 + FOCUS 1.2 via Data Exports to central analytics S3 → Athena + QuickSight dashboards. Cost Anomaly Detection AWS-managed monitors (services + linked accounts) from management account. Monthly cost budgets with AUTOMATIC SCP Budget Actions at 100% per member account. Cost Optimization Hub enabled org-wide with weekly COH Data Export for savings tracking.
- Key Decisions: Cross-account S3 delivery target for Data Exports; AUTOMATIC vs MANUAL Budget Actions per account tier; Compute Savings Plans sizing based on 30-day lookback recommendation.

**Edge Case**: AWS Channel Partner needing to bill end-customers at custom rates with per-customer cost visibility, while maintaining internal margin analysis.
- Approach: AWS Billing Conductor with billing groups per customer → pro forma CUR 2.0 export (customer-facing pricing) + standard CUR 2.0 export (true AWS cost) → dual Athena databases → margin = standard cost minus pro forma revenue. Per-billing-group Budgets for customer spend alerts. Cost Optimization Hub on management account for partner's own infrastructure optimization (not shared with customers).
- How to Handle: Billing Conductor does not affect the actual AWS invoice. Ensure the management account retains access to the standard CUR 2.0 for true-cost analysis. Tag all partner infrastructure separately from customer workloads.

**Anti-Pattern Case**: Architect proposes building a custom cost aggregation tool querying the Cost Explorer API hourly for 200 accounts to power a real-time cost dashboard.
- Clarification: Ask — (1) Does this need to be real-time, or is daily/hourly granularity from CUR 2.0 sufficient? Cost Explorer data itself has a ~8–24h latency for standard data and 48h for hourly data, so "real-time" is impossible via any Cost Management API. (2) At 200 accounts × multiple services × hourly queries, the API cost ($0.01/request) will exceed the value of the dashboard within weeks. Mandate Athena on CUR 2.0 for batch reporting. Reserve the Cost Explorer API for low-volume interactive queries and forecasting only.

---

## Cost Explorer — Full Reference

### Visualization, Dimensions, and Granularity

- **Granularity**: Monthly, daily, and hourly. Default view provides **14 months at daily
  granularity**. Monthly history extendable to **38 months** via Cost Management preferences
  (opt-in; available within ~48h of activation).
  Source: https://docs.aws.amazon.com/cost-management/latest/userguide/ce-granular-data.html
  + https://aws.amazon.com/blogs/aws-cloud-financial-management/extended-history-and-more-granular-data-available-within-aws-cost-explorer/

- **Hourly + resource-level granularity** (opt-in): covers the **past 14 days**; data lands
  within ~48h of enabling. Three separate opt-in features: resource-level at daily, all-services
  at hourly (no resource-level), and EC2 resource-level at hourly.
  Source: https://docs.aws.amazon.com/cost-management/latest/userguide/ce-granular-data.html
  + https://aws.amazon.com/about-aws/whats-new/2019/11/aws-cost-explorer-supports-hourly-resource-level-granularity/ ⚠️ >12mo, announcement for feature still active

- **Hourly granularity pricing**: $0.00000033 per usage record (≈ $0.01/1,000 records/month),
  billed daily.
  Source: https://aws.amazon.com/aws-cost-management/aws-cost-explorer/pricing/

- **Granularity restriction**: granular visibility only available for billing views showing
  chargeable data; not available for Billing Conductor standard/transfer billing groups.
  Source: https://docs.aws.amazon.com/cost-management/latest/userguide/ce-granular-data.html

- **Filter/group dimensions**: service, account, region, instance type, usage type, tags, cost
  categories, availability zone, purchase option, and more.
  Source: https://docs.aws.amazon.com/cost-management/latest/userguide/ce-modify.html

- **Standard daily data latency**: [unverified] — precise SLA for non-hourly data refresh not
  found in official docs. Recommendations refresh at least every 24h.
  Source: https://docs.aws.amazon.com/cost-management/latest/userguide/ri-recommendations.html

### Forecasting

- **Forecast horizon**: **18 months** (extended from 12 months, Nov 19, 2025). Available in
  both console and via `GetCostForecast` API.
  Source: https://aws.amazon.com/about-aws/whats-new/2025/11/cost-explorer-18-month-forecasting-ai-powered-forecasts/

- **ML model historical input**: **36 months** of historical data analyzed (extended from
  6 months); recent months weighted more heavily for seasonality/trend. [Note: one AWS blog
  cites 38 months; the official What's New states 36 — 36 taken as authoritative.]
  Source: https://aws.amazon.com/about-aws/whats-new/2025/11/cost-explorer-18-month-forecasting-ai-powered-forecasts/

- **Prediction interval**: fixed at **80%** in the console. If AWS lacks sufficient history
  (< 1 full billing cycle), no forecast is provided.
  Source: https://docs.aws.amazon.com/cost-management/latest/userguide/ce-forecast.html

- **API**: `GetCostForecast` / `GetUsageForecast`. The API accepts a caller-specified
  `PredictionIntervalLevel` (confidence level); higher confidence → wider interval.
  Source: https://docs.aws.amazon.com/aws-cost-management/latest/APIReference/API_GetCostForecast.html

- **AI-powered forecast explanations** ("Analyze with Amazon Q Developer"): console-only,
  public preview (Nov 2025). Not yet available via API.
  Source: https://aws.amazon.com/about-aws/whats-new/2025/11/cost-explorer-18-month-forecasting-ai-powered-forecasts/

- **Natural-language querying** (Amazon Q Developer "Ask question"): integrated into Cost
  Explorer console.
  Source: https://docs.aws.amazon.com/cost-management/latest/userguide/ce-forecast.html

- **Consolidated billing forecasting**: uses data from **all accounts** in the org. Newly added
  member accounts are excluded from forecasts until new spending patterns are analyzed.
  Source: https://docs.aws.amazon.com/cost-management/latest/userguide/ce-forecast.html

### RI and Savings Plans Recommendations

- **RI purchase recommendations**: analyzes On-Demand usage over a selectable lookback of
  **7, 30, or 60 days**. Adjustable parameters: Term, Offering class (standard/convertible),
  Payment option, and lookback days.
  Source: https://docs.aws.amazon.com/cost-management/latest/userguide/ri-recommendations.html
  + https://docs.aws.amazon.com/cost-management/latest/userguide/ce-ris.html

- **Savings Plans recommendations**: lookback of **7, 30, or 60 days**; usage already covered
  by RI/Spot/SP is excluded from the recommendation calculation.
  Source: https://docs.aws.amazon.com/savingsplans/latest/userguide/sp-recommendations.html

- **Recommendation refresh**: at least once every **24 hours**.
  Source: https://docs.aws.amazon.com/cost-management/latest/userguide/ri-recommendations.html

### EC2 Rightsizing Recommendations

- Identifies savings by **downsizing or terminating** underutilized EC2 instances; visible
  across member accounts in a single view (management account). Integrated with AWS Compute
  Optimizer.
  Source: https://docs.aws.amazon.com/cost-management/latest/userguide/ce-rightsizing.html

- **AWS explicitly recommends using Cost Optimization Hub** instead of Cost Explorer's
  standalone rightsizing feature.
  Source: https://docs.aws.amazon.com/cost-management/latest/userguide/ce-rightsizing.html

### Cost Explorer API

- **API endpoint**: `https://ce.us-east-1.amazonaws.com` (single global endpoint).
  Source: https://docs.aws.amazon.com/cost-management/latest/userguide/ce-api.html

- **Key API operations**: `GetCostAndUsage`, `GetCostForecast`, `GetUsageForecast`,
  `GetRightsizingRecommendation`, `GetSavingsPlansPurchaseRecommendation`,
  `GetReservationPurchaseRecommendation`, `GetCostAndUsageComparisons` (new; GA date
  [unverified]).
  Source: https://docs.aws.amazon.com/aws-cost-management/latest/APIReference/API_Operations_AWS_Cost_Explorer_Service.html

- **Pricing**: **$0.01 per paginated API request** against the primary billing view;
  **$0.01 per source** for custom billing views. Each page of a paginated result is a
  separate billable request.
  Source: https://aws.amazon.com/aws-cost-management/aws-cost-explorer/pricing/

- **IAM permission required**: users must be explicitly granted `ce:` permissions.
  Source: https://docs.aws.amazon.com/cost-management/latest/userguide/ce-api.html

---

## AWS Budgets — Full Reference

### Budget Types and Granularity

- **Six budget types**: cost budgets, usage budgets, RI utilization budgets, RI coverage
  budgets, Savings Plans utilization budgets, Savings Plans coverage budgets.
  Source: https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html

- **Budget periods**: monthly (fixed or variable/growing target), daily (utilization/coverage),
  and **custom period** (e.g., April 15 2025 – July 15 2025 for fiscal year/project/grant).
  Source: same URL.

- **Alert types**: **actual** (after accruing) and **forecasted** (before accruing) for
  cost/usage budgets. Utilization/coverage budgets alert when you fall below target.
  Source: same URL.

- **Cost tracking modes**: blended, unblended, net unblended, amortized, net amortized; with
  configurable include/exclude for discounts, refunds, support fees, taxes.
  Source: same URL.

- **Budget data refresh cadence**: up to 3×/day (~8–12h between updates).
  Source: same URL.

### Alert Notifications and Quotas

- **Notification channels**: Amazon SNS topic, email address, or both.
  Source: https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html

- **Verified service quotas**:
  - Total budgets per management account: **20,000**
  - Free action-enabled budgets per account per month: **2**
  - Actions per budget: **10**
  - Budget actions per account: **100**
  - Budgets using a custom billing view: **150**
  Source: https://docs.aws.amazon.com/cost-management/latest/userguide/management-limits.html

- **Pricing**:
  - Budget monitoring + notifications: **free**
  - First 2 action-enabled budgets/month: **free**
  - Each additional action-enabled budget: **$0.10/day**
  - Budget Reports (email delivery): **$0.01 per report delivery**
  Source: https://aws.amazon.com/aws-cost-management/aws-budgets/pricing/

### Budget Actions

- **Three action types**: (1) apply an IAM policy, (2) apply a Service Control Policy (SCP),
  (3) stop specific EC2 / RDS instances (SSM action subtypes `STOP_EC2_INSTANCES` /
  `STOP_RDS_INSTANCES`).
  Source: https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-controls.html

- **Cross-account behavior**: from the management account you can apply an SCP to another
  account, but **cannot** target EC2/RDS instances in another account. Multiple actions can
  fire at the same threshold.
  Source: same URL.

- **Approval workflow**: `AUTOMATIC` (fires immediately when threshold crossed) or `MANUAL`
  (user confirms via "Run action" → "Yes, I am sure" on the Alert details page).
  Action states: Standby → Requires approval → Completed → Reversed. A reversed action can
  be re-evaluated via **Reset**.
  Source: https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-action-review.html

- **Action history**: visible 60 days in console; full history via CloudTrail or
  `DescribeBudgetActionHistories` API.
  Source: same URL.

- **Required IAM role**: a service role that AWS Budgets assumes must be created. AWS provides
  a managed policy plus example inline policies for IAM/SCP actions and EC2/RDS stop actions.
  [unverified: exact managed-policy ARN not confirmed from official page text.]
  Source: https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-action-role.html

### Organizations Integration

- Management account controls member-account budget access via IAM policies. Management account
  can create budgets tracking a specific member account's cost. Member accounts create only their
  own budgets by default — no cross-account visibility.
  Source: https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html

---

## AWS Cost Anomaly Detection — Full Reference

### How It Works

- **ML model**: learns historical spend patterns; requires **≥10 days** of historical data
  before detecting anomalies; detects an anomaly **up to 24 hours** after usage.
  Source: https://docs.aws.amazon.com/cost-management/latest/userguide/getting-started-ad.html

- **What it analyzes**: Usage charge type and NetUnblendedCost only. Does not analyze all
  charge types.
  Source: https://docs.aws.amazon.com/cost-management/latest/userguide/management-limits.html

- **Cost**: **free**.
  Source: https://aws.amazon.com/aws-cost-management/aws-cost-anomaly-detection/faqs/

- **Accelerated detection** (Nov 2025): rolling 24-hour analysis windows (vs. prior daily batch).
  Source: https://aws.amazon.com/about-aws/whats-new/2025/11/aws-cost-anomaly-detection-accelerates-anomaly/

### Monitor Types and Dimensions

- **Four monitor dimensions**: AWS services, Linked (member) accounts, Cost allocation tags,
  Cost categories.
  Source: https://docs.aws.amazon.com/cost-management/latest/userguide/getting-started-ad.html

- **Two authoring methods**:
  - **AWS managed**: auto-tracks top 5,000 values per dimension; auto-includes new values/accounts.
    Now covers linked accounts, cost allocation tags, and cost categories (expanded Nov 2025 —
    previously services only).
    Source: https://aws.amazon.com/about-aws/whats-new/2025/11/aws-cost-anomaly-detection-managed-monitoring/
  - **Customer managed** (formerly "custom monitors"): manually select up to 10 values.
    [Note: terminology change — "custom monitors" renamed to "customer managed monitors".]

- **Linked account/tag/category monitors**: can only be created in the management account.
  Source: https://docs.aws.amazon.com/cost-management/latest/userguide/getting-started-ad.html

### Alerting

- **Three alert subscription types**:
  - Individual alerts: immediate; **require an SNS topic**
  - Daily summaries: email, top 10 anomalies by impact, generated 00:00 UTC
  - Weekly summaries: email
  Source: https://docs.aws.amazon.com/cost-management/latest/userguide/getting-started-ad.html

- **Threshold types**: absolute (dollar) and/or percentage, combinable with AND/OR.
  Source: same URL.

- **Advanced alerting via AWS User Notifications** (May 2025): multi-channel routing via
  EventBridge rules — email, AWS Chatbot / Amazon Q Developer in chat apps, Console Mobile App;
  per-rule thresholds.
  Source: https://aws.amazon.com/about-aws/whats-new/2025/05/aws-cost-anomaly-detection-advanced-alerting-user-notifications/

- **AI-powered cost investigations** (2025): plain-language root-cause via Amazon Q Developer
  in the console.
  Source: https://aws.amazon.com/blogs/aws-cloud-financial-management/introducing-ai-powered-cost-investigations-for-cost-anomalies/

### Quotas

- AWS managed monitors: 1 for AWS services per account; 1 additional (linked account/tag/category)
  per management account; total 2 managed per management account; 1 per member account.
- Values per AWS managed monitor: **5,000**
- Customer managed monitors per management account: **500**
- Values per customer managed monitor: **10** (linked/tag) or **1** (cost category)
- Alert subscriptions per account: **100**; email recipients per subscription: **10**;
  SNS topics per subscription: **1**
Source: https://docs.aws.amazon.com/cost-management/latest/userguide/management-limits.html

### Unsupported Services

CAD does not analyze: AWS Marketplace (except third-party foundation models on Amazon Bedrock),
AWS Support, WorkSpaces, Cost Explorer, Budgets, AWS Shield, Amazon Route 53, AWS Certificate Manager.
Source: https://docs.aws.amazon.com/cost-management/latest/userguide/management-limits.html

---

## Data Exports & CUR 2.0 — Full Reference

### Export Types

- **Five export types** available in Data Exports:
  1. **CUR 2.0** (table: `COST_AND_USAGE_REPORT`) — most granular line-item data; 125 columns;
     stable fixed schema (does not vary month-to-month unlike legacy CUR)
  2. **Cost Optimization Recommendations** (from Cost Optimization Hub) — recurring Parquet/CSV
     to S3
  3. **FOCUS 1.2 with AWS columns** — FinOps Open Cost & Usage Spec (adds capacity reservation
     info, invoice IDs, virtual currency support)
  4. **FOCUS 1.0 with AWS columns**
  5. **Carbon emissions**
  Source: https://docs.aws.amazon.com/cur/latest/userguide/what-is-data-exports.html

- **Output formats**: Parquet and CSV to a customer-owned Amazon S3 bucket. Cross-account
  delivery supported (March 2026).
  Source: same URL + https://aws.amazon.com/about-aws/whats-new/2026/03/aws-data-exports-cross-account-delivery-cost/

- **Delivery cadence**: first report up to 24h; thereafter updated at least once a day
  (up to 3×/day); each monthly file is cumulative; finalized after invoice at month-end,
  with later adjustments reflected ~6th–7th of the following month.
  Source: https://docs.aws.amazon.com/cur/latest/userguide/what-is-cur.html

### CUR 2.0 vs Legacy CUR

| Aspect | CUR 2.0 (recommended) | Legacy CUR |
|---|---|---|
| Schema stability | Fixed, stable, 125 columns | Varies month-to-month |
| Format | Parquet + CSV | CSV (split when > ~1M rows) |
| Delivery mechanism | Data Exports | Legacy CUR API |
| AWS positioning | **"New and recommended"** | **"Legacy"** — not recommended for new setups |
| Status | GA | Still available; no official shutdown date announced [unverified] |

Source: https://docs.aws.amazon.com/cur/latest/userguide/cur-overview.html
+ https://docs.aws.amazon.com/cur/latest/userguide/dataexports-migrate.html

### CUR 2.0 Column Groups

CUR 2.0 table (`COST_AND_USAGE_REPORT`) has up to 125 possible columns in 8 groups: Bill,
Cost category, Capacity reservation, Discount, Identity, Line item, Pricing, Product.
Source: https://docs.aws.amazon.com/cur/latest/userguide/table-dictionary-cur2.html

---

## Cost Categories and Cost Allocation Tags — Full Reference

### Cost Categories

- **Rule-based engine** that groups costs into custom categories using dimensions: account, tag,
  service, charge type, or other cost categories. Evaluated at billing computation time (multi-
  daily); changes propagate within **up to 24 hours**.
  Source: https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/manage-cost-categories.html

- **Available in**: Cost Explorer, AWS Budgets, CUR, and Cost Anomaly Detection (as a filter/
  grouping dimension in all four).
  Source: https://aws.amazon.com/aws-cost-management/aws-cost-categories/

- **Two authoring modes**: GUI Rule builder (AND conditions only) or JSON editor (AND/OR/NOT,
  supports nested conditions).
  Source: https://aws.amazon.com/aws-cost-management/aws-cost-categories/faqs/

### Cost Allocation Tags

- **Two types**:
  - **AWS-generated tags** (prefix `aws:`, e.g., `aws:createdBy`): created/applied by AWS.
    Activated by the management account owner — activation applies to all member accounts.
    Auto-activated tags do not count toward the tag quota.
  - **User-defined tags**: you create and apply. Must be activated separately.
  Source: https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/cost-alloc-tags.html
  + https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/aws-tags.html

- **Activation required**: both types must be explicitly activated in the Billing console.
  Can take **up to 24 hours** to activate; tag keys take up to 24h to appear for activation
  after being applied to resources.
  Source: https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/activating-tags.html

---

## Cost Optimization Hub — Full Reference

- **Consolidated recommendations**: 18+ optimization types including resource rightsizing,
  idle resource deletion, Savings Plans, Reserved Instances, Graviton migration, generation
  upgrades, and scale-in.
  Source: https://docs.aws.amazon.com/cost-management/latest/userguide/cost-optimization-hub.html

- **Supported resources**: EC2, EC2 Auto Scaling groups, EBS, Lambda, ECS-on-Fargate, RDS DB
  instances & storage, Aurora storage, ElastiCache, MemoryDB, DynamoDB (table + reserved
  capacity), DocumentDB, Redshift reserved nodes, OpenSearch RIs, SageMaker endpoints/SPs,
  WorkSpaces, NAT Gateway, Compute/EC2-Instance/SageMaker Savings Plans, and EC2/RDS RIs.
  Source: same URL.

- **Recommendation engine**: AWS Compute Optimizer (for rightsizing/idle recommendations).
  Savings estimates incorporate your specific RI/SP commercial terms and are deduplicated.
  Source: same URL.

- **Organizations scope**: opt in from the management account; choose management-account-only
  or management account + all member accounts.
  Source: https://docs.aws.amazon.com/organizations/latest/userguide/services-that-can-integrate-coh.html

- **AWS explicitly positions COH** as the replacement for Cost Explorer's standalone rightsizing
  feature.
  Source: https://docs.aws.amazon.com/cost-management/latest/userguide/ce-rightsizing.html

- **Cost Efficiency metric** (Nov 2025): measures/tracks efficiency over time; now surfaced in
  a new Billing & Cost Management dashboard widget (by account/Region/overall, July 2026).
  Source: https://aws.amazon.com/about-aws/whats-new/2025/11/aws-cost-optimization-hub-cost-efficiency-metric-measure-track
  + https://aws.amazon.com/about-aws/whats-new/2026/07/monitor-cost-efficiency-using-dashboards/

- **CSV download** in console (April 2026): single-click export complementing S3 Data Exports.
  Source: https://aws.amazon.com/about-aws/whats-new/2026/04/aws-cost-optimization-hub-csv-download/

---

## Well-Architected Cost Optimization Pillar — Alignment

### Design Principles (5)

Source: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/design-principles.html
(whitepaper publication date: June 27, 2024 ⚠️ >12mo, current stable)

1. **Implement cloud financial management** — build organizational CFM/FinOps capability
2. **Adopt a consumption model** — pay only for what you use
3. **Measure overall efficiency** — track output vs. cost
4. **Stop spending money on undifferentiated heavy lifting** — use managed services
5. **Analyze and attribute expenditure** — use cost allocation tags + Cost Categories

### COST Questions (COST 1–11) by Focus Area

Source: https://docs.aws.amazon.com/wellarchitected/latest/framework/cost-optimization.html

| Focus Area | Questions |
|---|---|
| Practice Cloud Financial Management | COST 1: How do you implement cloud financial management? · COST 2: How do you govern usage? |
| Expenditure and usage awareness | COST 3: How do you monitor usage and cost? · COST 4: How do you decommission resources? |
| Cost-effective resources | COST 5: How do you evaluate cost when you select services? · COST 6: How do you meet cost targets when you select resource type, size and number? · COST 7: How do you use pricing models to optimize cost? · COST 8: How do you plan for data transfer charges? |
| Manage demand and supply resources | COST 9: How do you manage demand, and supply resources? |
| Optimize over time | COST 10: How do you evaluate new services? · COST 11: How do you evaluate the cost of effort? |

[Note: COST question title wording partially verified — numbering and focus-area grouping confirmed;
exact sub-page title strings for COST 3, 9, 11 are partially unverified.]

### How the Pillar Maps to the AWS Cost Management Services

| COST Question | Primary AWS Services |
|---|---|
| COST 1: Cloud financial management | AWS Organizations, Cost Categories, Cost Allocation Tags |
| COST 2: Govern usage | AWS Budgets (Budget Actions + SCPs), Cost Categories |
| COST 3: Monitor usage and cost | Cost Explorer, Cost Anomaly Detection, AWS Budgets |
| COST 7: Pricing models | Savings Plans, Reserved Instances, Cost Explorer (recommendations) |
| COST 10: Evaluate new services | Cost Optimization Hub, AWS Compute Optimizer |

[Note: per-question tool enumeration partially verified — see whitepaper COST 2/COST 3 sub-pages for exact text.]

---

## Consolidated Billing & RI/SP Sharing

- **Consolidated billing** (AWS Organizations): combines billing/payment; shares **volume pricing
  discounts, RI discounts, and Savings Plans** across all accounts in the family.
  Source: https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/consolidated-billing.html

- **RI sharing**: all accounts can receive the hourly benefit of RIs purchased by any account;
  sharing can be **turned off** on the Billing Preferences page.
  Source: https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/ri-turn-off.html

- **SP application order**: applied first to the **owner account's** usage, then to other
  accounts' usage if sharing is enabled.
  Source: https://docs.aws.amazon.com/savingsplans/latest/userguide/sp-applying.html

- **RISP Group Sharing**: uses Cost Categories to control (prioritize/restrict) how RI/SP
  discounts are shared across an organization.
  Source: https://aws.amazon.com/blogs/aws-cloud-financial-management/control-your-aws-commitments-with-risp-group-sharing/

---

## Changelog — AWS Cost Management (2023–2026)

All items below are from dated official What's New posts unless noted.

| Date | Change | Type |
|---|---|---|
| Nov 2023 | Unified Billing and Cost Management console (consolidated navigation) | Renaming/consolidation |
| Nov 26, 2023 | Cost Optimization Hub launched (15+ recommendation types, free) | New feature |
| Nov 2023 | Data Exports + CUR 2.0 launched (stable schema, Parquet/CSV) | New feature |
| May 2024 | Cost Anomaly Detection latency reduced ~30% (3× daily analysis) | Enhancement |
| May 2024 | Bulk IAM billing policy migration tooling for unified console | Enhancement |
| June 2024 | Data Exports for FOCUS 1.0 (Preview) | New feature |
| June 21, 2024 | Data Exports for Cost Optimization Hub GA (S3 Parquet/CSV) | GA |
| Nov 2024 | Data Exports for FOCUS 1.0 GA (standardized columns: ListCost, ContractedCost, BilledCost, EffectiveCost) | GA |
| Nov 2024 | Enhanced root-cause insights for cost anomalies (service/account/region/usage-type ranking) | Enhancement |
| May 2025 | Cost Anomaly Detection advanced alerting via AWS User Notifications (multi-channel, EventBridge rules) | Enhancement |
| May 2025 | Cost Optimization Hub — Savings Plans & RI sharing preferences | Enhancement |
| July 2025 | Cost Anomaly Detection ML model accuracy improvements | Enhancement |
| July 2025 | Cost Optimization Hub — account names in optimization opportunities | Enhancement |
| Aug 2025 | Billing & Cost Management console — 6 new recommended actions (total 21, categorized) | Enhancement |
| Sept 2025 | CUR 2.0 GA in AWS Secret Region | Region expansion |
| Nov 2025 | Cost Explorer 18-month forecasting; ML model uses 36 months of history; AI-powered forecast explanations (Amazon Q Developer, console preview) | Enhancement |
| Nov 2025 | Cost Anomaly Detection — accelerated detection (rolling 24h windows) | Enhancement |
| Nov 2025 | Cost Anomaly Detection — expanded AWS-managed monitoring (covers linked accounts, tags, categories) | Enhancement |
| Nov 2025 | Cost Optimization Hub — Cost Efficiency metric | New feature |
| 2025 | Cost Anomaly Detection — AI-powered cost investigations (plain-language root-cause) | New feature (blog) |
| March 2026 | Data Exports — cross-account delivery to any authorized S3 bucket | New feature |
| April 2026 | Cost Optimization Hub — CSV download in console | Enhancement |
| July 2026 | Cost Efficiency metric widget in Billing & Cost Management Dashboards | Enhancement |

### Deprecated / Superseded Patterns

| Pattern | Replacement | Status |
|---|---|---|
| Legacy CUR (legacy Cost and Usage Reports) | CUR 2.0 via Data Exports | Superseded (no shutdown date announced [unverified]) |
| Separate Billing + Cost Management console navigation | Unified Billing and Cost Management console (Nov 2023) | Renamed/consolidated; IAM billing permissions reworked |
| Cost Explorer standalone rightsizing recommendations | Cost Optimization Hub (single pane + deduplication) | Pattern superseded (soft — no hard deprecation) |
| Custom CAD monitors terminology | Customer managed monitors | Terminology rename only — functionality unchanged |

---

## Architecture Patterns

### FinOps Governance Foundation (Management Account)

```
AWS Organizations (management account)
├── Cost Allocation Tags — mandatory tag taxonomy (project, environment, owner, cost-center)
│   └── Activate in Billing console → propagates to Cost Explorer + CUR (~24h)
├── Cost Categories — attribution hierarchy (BU → team → environment)
│   └── Rule-based, available in Cost Explorer / Budgets / CUR / CAD
├── Data Exports (CUR 2.0 + FOCUS 1.2) → S3 (Parquet)
│   └── Athena + QuickSight for self-service analytics
│   └── Cross-account delivery to central analytics account (March 2026)
├── Cost Anomaly Detection
│   ├── AWS-managed monitor (org-wide: services + linked accounts + tags + categories)
│   └── Individual alerts → SNS → PagerDuty/Slack via AWS User Notifications
└── Cost Optimization Hub (management account opt-in)
    └── Covers all member accounts; sourced from Compute Optimizer
    └── Recurring Data Exports → S3 for recommendation tracking
```

### Per-Account Budget Enforcement Pattern

```
Per-account cost budget (monthly) [in management account]
├── Alert 80% actual → SNS → email + Slack
├── Alert 100% actual → Budget Action (AUTOMATIC) → apply SCP to member account
│   └── SCP: deny resource provisioning (except emergency break-glass role)
└── Alert 120% forecasted → Budget Action (MANUAL) → engineering review required
```

### Cost Explorer API Integration Pattern

```
FinOps reporting pipeline:
GetCostAndUsage (daily, by service + account)  →  $0.01/page
GetCostForecast (monthly, 3 months ahead)       →  $0.01/page
GetSavingsPlansPurchaseRecommendation (weekly)  →  $0.01/page

Note: Use pagination budgets — each paginated page = 1 billable request.
Prefer Athena on CUR 2.0 for high-volume queries (avoids per-request API costs).
```

---

## Key Unverified Items

| Claim | Status |
|---|---|
| Precise daily-data latency SLA for standard Cost Explorer data | UNVERIFIED — no official SLA found |
| Cost Explorer console UI being free | UNVERIFIED from the fetched pricing page (widely stated but not confirmed on the official pricing page directly) |
| Exact 36 vs 38 months of ML history for CE forecasting | 36 taken from official What's New; AWS CFM blog says 38 — discrepancy flagged |
| GA date of `GetCostAndUsageComparisons` API operation | UNVERIFIED |
| Exact hard end-of-life/shutdown date for legacy CUR | UNVERIFIED — no official sunset date found |
| Managed-policy ARN for Budget Actions service role | UNVERIFIED — ARN not shown on official setup page |
| Exact COST 3, COST 9, COST 11 title wording in the whitepaper sub-pages | PARTIALLY VERIFIED — numbering/grouping confirmed; individual sub-page wording not transcribed |
| re:Invent 2025 multi-source Billing Views (up to 20 payer accounts) / 20-widget dashboard features | PARTIALLY VERIFIED via CFM blog; individual What's New pages not opened |

---

## Primary Source Anchors

- Cost Management user guide: https://docs.aws.amazon.com/cost-management/latest/userguide/
- Cost Explorer: https://docs.aws.amazon.com/cost-management/latest/userguide/ce-what-is.html
- AWS Budgets: https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html
- Budget Actions: https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-controls.html
- Cost Anomaly Detection: https://docs.aws.amazon.com/cost-management/latest/userguide/getting-started-ad.html
- Data Exports / CUR 2.0: https://docs.aws.amazon.com/cur/latest/userguide/what-is-data-exports.html
- Cost Categories: https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/manage-cost-categories.html
- Cost Allocation Tags: https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/cost-alloc-tags.html
- Cost Optimization Hub: https://docs.aws.amazon.com/cost-management/latest/userguide/cost-optimization-hub.html
- Service Quotas: https://docs.aws.amazon.com/cost-management/latest/userguide/management-limits.html
- Cost Explorer API reference: https://docs.aws.amazon.com/aws-cost-management/latest/APIReference/
- Cost Explorer pricing: https://aws.amazon.com/aws-cost-management/aws-cost-explorer/pricing/
- Budgets pricing: https://aws.amazon.com/aws-cost-management/aws-budgets/pricing/
- WAF Cost Optimization Pillar: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html
- Consolidated billing: https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/consolidated-billing.html
- Doc history: https://docs.aws.amazon.com/cost-management/latest/userguide/doc-history.html
