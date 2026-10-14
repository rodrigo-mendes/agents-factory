# Always-Do Patterns — AWS OE Pillar (OPS 1–11)

Full guidance for each mandatory pattern in `applying-waf-operational-excellence-pillar`.
Source: AWS Well-Architected OE Pillar, November 6, 2024 edition.

---

## Pattern 1 — Define operating model with explicit ownership (OPS 1–3)

**OPS area**: Organization | **Design principle**: "Organize teams around business outcomes"

**What to do**:
- Set shared goals and priorities aligned to business outcomes
- Assign named owners to every application, workload, platform, infrastructure component, process, and procedure
- Maintain a risk registry with impact and tradeoff analysis for each identified risk
- Govern multi-account environments centrally with AWS Organizations + Control Tower

**AWS services**:
- AWS Organizations + AWS Control Tower (multi-account guardrails, account blueprints)
- AWS Trusted Advisor + AWS Well-Architected Tool (priority shaping, gap analysis)

**Verification**:
```bash
# Confirm Control Tower guardrails deployed on an OU
aws controltower list-enabled-controls --target-identifier <OU-ARN>
```

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/framework/oe-organization.html — accessed 2026-08-27

---

## Pattern 2 — Implement observability before go-live (OPS 4)

**OPS area**: Prepare | **Design principle**: "Implement observability for actionable insights"

**Five OPS04 best practices (all required)**:

| BP | Name | What it covers |
|---|---|---|
| OPS04-BP01 | Identify KPIs | Business-aligned metrics that map to outcomes |
| OPS04-BP02 | Application telemetry | App-level metrics and structured logs |
| OPS04-BP03 | User-experience telemetry | Synthetic monitoring, Real User Monitoring |
| OPS04-BP04 | Dependency telemetry | Third-party and internal service health |
| OPS04-BP05 | Distributed tracing | End-to-end request tracing across components |

**AWS services**:
- Amazon CloudWatch (metrics, logs, alarms, dashboards)
- AWS X-Ray + CloudWatch Application Signals (distributed tracing, service map)
- Amazon Managed Service for Prometheus + Amazon Managed Grafana (OSS/K8s-heavy workloads)

**Verification**:
```bash
# Confirm KPI alarms exist
aws cloudwatch describe-alarms --query 'MetricAlarms[*].{Name:AlarmName,State:StateValue}'

# Confirm X-Ray service map populated
aws xray get-service-graph \
  --start-time $(date -d '1 hour ago' +%s) \
  --end-time $(date +%s)
```

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/implement-observability.html — accessed 2026-08-27

---

## Pattern 3 — Small, reversible, automated deployments with rollback (OPS 5 / OPS 6)

**OPS area**: Prepare | **Design principle**: "Make frequent, small, reversible changes"

**What to do**:
- Build a CI/CD pipeline: CodePipeline (orchestration) → CodeBuild (build/test) → CodeDeploy (deploy)
- Use canary or blue/green deployment configuration — never AllAtOnce for customer-facing workloads
- Wire automatic rollback to CloudWatch alarms (deployment fails if alarm triggers)
- Maintain consistent sandbox/dev/test/prod environments via CloudFormation/CDK stacks

**AWS services**: AWS CodePipeline, AWS CodeBuild, AWS CodeDeploy, AWS CloudFormation / CDK

**Verification**:
```bash
# Confirm deployment style is not AllAtOnce
aws deploy get-deployment-group \
  --application-name <app> \
  --deployment-group-name <dg> \
  --query 'deploymentGroupInfo.deploymentStyle'
# Expected: {"deploymentOption":"WITH_TRAFFIC_CONTROL","deploymentType":"BLUE_GREEN"} or CANARY equivalent
```

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/framework/oe-prepare.html — accessed 2026-08-27

---

## Pattern 4 — Gate production on ORR + runbooks + playbooks (OPS 7)

**OPS area**: Prepare | **Design principle**: "Anticipate failure"

**What to do**:
- Complete an ORR checklist before go-live covering: workload, processes, procedures, and personnel
- Codify routine operational tasks as SSM Automation runbooks (repeatable, expected operations)
- Author playbooks for incident investigation paths (unknown/unplanned events)
- Run pre-mortems to identify failure scenarios and test team response before launch
- Capture any areas requiring remediation plans; do not suppress risks

**AWS services**: AWS Systems Manager Automation (runbooks), AWS Systems Manager Incident Manager (response), AWS Well-Architected Tool, AWS Config (compliance checks)

**Verification**:
```bash
# Confirm SSM Automation documents exist for runbook coverage
aws ssm list-documents --document-type Automation \
  --query 'DocumentIdentifiers[*].Name'
# Expected: list of named runbook documents
```

**Note**: OPS 7 leaf best-practice pages (OPS07-BPxx) are confirmed from oe-prepare.html verbatim. The SSM service mapping is architect-standard inference at Medium confidence — verify against OPS07 detail pages before treating as authoritative.

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/framework/oe-prepare.html — accessed 2026-08-27

---

## Pattern 5 — Operations as code with automation guardrails (design principle 3)

**OPS area**: Prepare / Operate | **Design principle**: "Safely automate where possible"

**What to do**:
- Define all infrastructure as CloudFormation/CDK; no manual console provisioning
- Define operational procedures as SSM Automation documents
- Add guardrails to every automated response: rate control, error thresholds, and manual approval steps
- Apply a consistent resource tagging strategy for organization, cost accounting, access control, and automation targeting

**AWS services**: AWS CloudFormation / CDK, AWS Systems Manager Automation, AWS Resource Groups + Tags

**Verification**:
```bash
# Confirm resources are tag-governed
aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=Environment,Values=production \
  --query 'ResourceTagMappingList[*].ResourceARN' | wc -l
# Expected: count matching the known production resource inventory
```

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/framework/oe-design-principles.html + oe-prepare.html — accessed 2026-08-27

---

## Pattern 6 — Business-aligned health metrics, owned alerts, audience dashboards (OPS 8/9/10)

**OPS area**: Operate | **Design principles**: "Learn from all operational events and metrics"; "Implement observability"

**What to do**:
- Define expected business/customer outcomes first; then select metrics that measure them
- Establish metric baselines; alert on deviations (not just threshold crossings)
- Build audience-tailored dashboards: customer-facing / business / developer / operations
- Route every alarm through SNS + AWS Systems Manager Incident Manager to a named owner and on-call schedule
- Bind each alarm to a runbook (routine response) or playbook (investigation); escalate business-impacting novel events to decision-makers

**AWS services**: Amazon CloudWatch (dashboards, metrics, alarms), AWS X-Ray, AWS CloudTrail, VPC Flow Logs, SNS, AWS Systems Manager Incident Manager

**Verification**:
```bash
# Confirm no alarm is in INSUFFICIENT_DATA (unconfigured)
aws cloudwatch describe-alarms \
  --state-value INSUFFICIENT_DATA \
  --query 'MetricAlarms[*].AlarmName'
# Expected: empty list

# Confirm Incident Manager response plans exist
aws ssm-incidents list-response-plans \
  --query 'responsePlanSummaries[*].name'
```

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/framework/oe-operate.html — accessed 2026-08-27

---

## Pattern 7 — Blameless post-incident analysis and continuous improvement loop (OPS 11)

**OPS area**: Evolve | **Design principles**: "Refine operations procedures frequently"; "Learn from all operational events and metrics"

**What to do**:
- Run blameless post-incident analysis after every customer-impacting event
- Identify contributing factors and produce tracked preventative actions
- Archive operational logs to S3; catalog with AWS Glue; query trends with Amazon Athena; visualize with Amazon QuickSight
- Share learnings across all affected teams — not just the responding team
- Dedicate regular recurring cycles to incremental improvement (not just post-incident)

**AWS services**: Amazon S3 (long-term log archive), AWS Glue + Data Catalog (log discovery/preparation), Amazon Athena (SQL trend analysis), Amazon QuickSight (visualization)

**Verification**:
```bash
# Confirm Glue catalog contains operational log databases
aws glue get-databases \
  --query 'DatabaseList[*].{Name:Name,Description:Description}'
# Expected: at least one database for operational/incident log analytics
```

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/framework/oe-evolve.html — accessed 2026-08-27
