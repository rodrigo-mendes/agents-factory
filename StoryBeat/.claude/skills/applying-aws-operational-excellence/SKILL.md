---
name: applying-aws-operational-excellence
description: "Applies AWS Well-Architected Framework Operational Excellence pillar patterns to multi-account production workloads. Use when designing, auditing, or reviewing AWS architectures for deployment safety, observability, incident management, multi-account governance, and continuous improvement practices aligned to the November 2024 edition."
---

## Function

Specialist in Operational Excellence (OE) for AWS Well-Architected Framework, November 6, 2024 edition. Covers: IaC + Config as Code, full-stack observability, CI/CD with safe deployments, runbook-driven incident management, multi-account governance, and AI-assisted operations.

## Version Context

**Technology**: AWS Well-Architected Framework — Operational Excellence Pillar
**Target edition**: November 6, 2024 (current stable)
**Research date**: 2026-08-27 | **Currency threshold**: 2027-08-27
**Official source**: https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/

**Key changes in November 2024 edition**:
- Design principles expanded from 5 to **8**; three new principles added
- "Perform operations as code" renamed to **"Safely automate where possible"** (automation must include guardrails)
- New principles: "Organize teams around business outcomes", "Implement observability for actionable insights", "Use managed services"
- OPS02-BP02 updated: leverage **Amazon Q Business** for workforce collaboration
- OPS10 updated: **AWS Health planned lifecycle events** integrated into incident management

**Deprecated**: Any source citing only 5 OE design principles is stale — reject it.

⚠️ **CRITICAL — Agent Warning**:
This skill targets the **November 6, 2024 edition** of the OE pillar.
Reject patterns from older editions. The 5-principle model is superseded.

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — ✅⚠️🚫 operational patterns
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 6 test cases
- **[Integration Patterns](#integration-patterns)** — Service composition and cross-pillar wiring
- **[Verification Loop](#verification-loop)** — AWS CLI validation commands
- **[Quick Reference](#quick-reference)** — Critical limits and essential commands
- **[External Resources](#external-resources)** — Official dated links

---

## Blueprints & Guardrails

### ✅ Always Do

**OE-A1 — IaC + Config as Code**
All infrastructure resources are defined in CloudFormation stacks or CDK constructs. Operational procedures are SSM Automation documents committed to source control. AWS Config rules enforce configuration compliance continuously. No manual console mutations are permitted in production. Aligns to "Safely automate where possible."
- Services: AWS CloudFormation, AWS CDK, AWS Systems Manager (Automation), AWS Config
- Verification: `aws cloudformation detect-stack-drift` — detect out-of-band changes; Config conformance pack — validate continuous compliance.

**OE-A2 — Full-Stack Observability from Day One**
Instrument for both business KPIs and operational metrics before the first production deployment — never retrofitted after an incident. Enable metrics, logs, distributed traces, and an org-wide CloudTrail trail. Alarm on customer-impacting thresholds with automated notification. Aligns to "Implement observability for actionable insights."
- Services: Amazon CloudWatch (metrics, logs, alarms, dashboards), AWS X-Ray (traces), Amazon CloudWatch Application Signals (APM), AWS CloudTrail
- Verification: `aws cloudwatch describe-alarms` — confirm alarms present; `aws cloudtrail describe-trails` — confirm org trail active and logging to central S3 bucket.

**OE-A3 — CI/CD with Small Reversible Deployments**
All production deployments flow through an automated pipeline. Configure CodeDeploy for canary or blue/green delivery. A CloudWatch alarm breach automatically triggers CodeDeploy rollback. Track deployment frequency and rollback success rate as operational metrics. Aligns to "Make frequent, small, reversible changes."
- Services: AWS CodePipeline, AWS CodeBuild, AWS CodeDeploy (canary/blue-green), Amazon CloudWatch (rollback alarm trigger)
- Verification: `aws deploy get-deployment` — confirm deployment type and rollback configuration; `aws codepipeline list-pipeline-executions` — review execution history.

**OE-A4 — Incident Management with Runbooks**
Every recurring operational task and incident-response step is implemented as an SSM Automation runbook in source control. EventBridge routes CloudWatch alarms and AWS Health events to SSM Incident Manager. Response plans define escalation paths per severity tier. Post-incident reviews are mandatory for Sev1/Sev2 events. Aligns to "Anticipate failure" and OPS10.
- Services: Amazon EventBridge, AWS Systems Manager Incident Manager, AWS Systems Manager Automation, AWS Health
- Verification: SSM Incident Manager response plans configured per severity tier; EventBridge rules route alarms and AWS Health events to Incident Manager.

**OE-A5 — Centralized Multi-Account Governance**
All workloads run in isolated AWS accounts under a Control Tower landing zone. SCPs prevent disabling of audit controls and creation of resources in unapproved regions. Account vending is automated via Service Catalog. A central security/audit account aggregates Config findings. Aligns to "Organize teams around business outcomes."
- Services: AWS Organizations, AWS Control Tower, AWS Config, AWS Service Catalog
- Verification: `aws organizations list-accounts` — confirm multi-account structure; Control Tower guardrail compliance dashboard — confirm all guardrails compliant.

**OE-A6 — AI-Assisted Operations (Amazon Q Business)**
Adopt Amazon Q Business to surface operational runbooks, reduce knowledge silos, and accelerate incident resolution for operational teams. Required by OPS02-BP02 (November 2024 update).
- Services: Amazon Q Business (connected to operational knowledge sources: Confluence, S3, ServiceNow as applicable)
- Verification: Amazon Q Business application configured and connected to at least one operational knowledge source.

### ⚠️ Ask First

**Decision A — Deployment Strategy: Canary vs Blue/Green vs All-at-Once**
Ask: "What is the rollback time requirement and blast-radius tolerance for this workload?"

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| All-at-once | Speed, cost | Blast radius, rollback safety | Low-risk, non-prod |
| Canary | Safety, gradual reversibility | Complexity | Customer-facing prod with risk tolerance |
| Blue/Green | Instant full-environment rollback | Double capacity cost during transition | Zero-downtime, critical prod |

**Decision B — Log and Metrics Retention Policy**
Ask: "What is the compliance retention requirement, and what is the acceptable query latency for historical logs?"

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| Active CloudWatch Logs retention | Fast query, compliance access | Higher cost per GB | Active troubleshooting/compliance window |
| Archive to S3/Glacier via Lifecycle | Cost | Hours-to-days retrieval | Long-term audit only |

**Decision C — Observability Tooling: Managed vs Self-Hosted**
Ask: "Does the team have capacity to operate an observability stack, and is multi-cloud portability a requirement?"

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| Managed (CloudWatch, Managed Grafana/Prometheus) | Lower operational burden | Vendor coupling, cost at scale | Most AWS workloads |
| Self-hosted (EC2 + OSS Prometheus/Grafana/Loki) | Flexibility, portability | Operational burden, patching | Multi-cloud or specialized requirements |

### 🚫 Never Do

**OE-N1 — Manual "Click-Ops" Production Changes** — Risk: HIGH
Console mutations introduce config drift, are unrepeatable, and create an unknown production state. Violates "Safely automate where possible."
- Detect: CloudTrail `ConsoleLogin` followed by mutating API calls with no corresponding CloudFormation stack event; `aws cloudformation detect-stack-drift` returns drifted resources.
- Instead: All changes via CloudFormation/CDK pipelines and SSM Automation; no direct console mutations in production.

**OE-N2 — Retrofitting Observability After an Incident** — Risk: HIGH
Silent failures go undetected; MTTR is high without a telemetry baseline. Violates "Implement observability for actionable insights."
- Detect: `aws cloudwatch describe-alarms` returns empty; `aws cloudtrail describe-trails` shows no active trail; no dashboards exist.
- Instead: CloudWatch metrics/alarms, X-Ray tracing, and CloudTrail enabled before first production deployment.

**OE-N3 — Big-Bang Infrequent Releases** — Risk: HIGH
Large batched releases have large blast radius and slow recovery. Violates "Make frequent, small, reversible changes."
- Detect: CodePipeline execution history shows low deployment frequency; CodeDeploy has no rollback configuration.
- Instead: CI/CD pipeline with canary or blue/green deployment; automatic CloudWatch alarm-triggered rollback.

**OE-N4 — Hero-Driven Incident Response (No Runbooks)** — Risk: MEDIUM
Individual expertise is not scalable or transferable; inconsistent response increases MTTR. Violates "Anticipate failure."
- Detect: No SSM Incident Manager response plans; no post-incident review documents; resolution depends on specific individuals.
- Instead: SSM Incident Manager response plans with SSM Automation runbooks; mandatory post-incident reviews with documented action items.

**OE-N5 — No Game Days or Failure Testing** — Risk: MEDIUM
Without failure simulation, the team has an unknown risk profile; real incidents become the first stress test. Violates "Anticipate failure."
- Detect: No AWS FIS experiment history; no game-day records or after-action reports.
- Instead: AWS Fault Injection Service (FIS) game days on a regular schedule; document outcomes and feed results into procedure updates.

**OE-N6 — Flat Single-Account with No Governance** — Risk: HIGH
No workload isolation, no audit boundary; a single misconfiguration affects all workloads. Violates "Organize teams around business outcomes."
- Detect: `aws organizations list-accounts` returns a single account; no Control Tower enrollment; no SCPs applied.
- Instead: AWS Organizations + Control Tower landing zone with SCPs; isolated accounts per workload/environment; centralized audit account.

---

## Integration Patterns

**Full OE Posture — Service Composition**

| Layer | Service | Purpose |
|-------|---------|---------|
| Governance | AWS Organizations + Control Tower | Multi-account landing zone, SCPs, guardrails |
| IaC | CloudFormation / CDK | All infrastructure defined and deployed as code |
| CI/CD | CodePipeline + CodeBuild + CodeDeploy | Automated build, test, canary/blue-green deploy, auto-rollback |
| Observability | CloudWatch + X-Ray + CloudTrail | Metrics, traces, alarms, API audit trail |
| Incident | SSM Incident Manager + EventBridge + SSM Automation | Auto-incident creation, runbook execution |
| Compliance | AWS Config + Config Rules | Continuous configuration compliance |
| AI Ops | Amazon Q Business | Workforce knowledge sharing, operational productivity |

**Common integration problems**:
- **Problem**: CloudWatch alarm does not trigger CodeDeploy rollback → **Solution**: Confirm the alarm ARN is configured in the CodeDeploy deployment group's `autoRollbackConfiguration.alarmConfiguration`; verify alarm state is ALARM-triggerable (not in INSUFFICIENT_DATA).
- **Problem**: EventBridge rule does not create SSM Incident Manager incidents from CloudWatch alarms → **Solution**: Verify EventBridge rule target is `aws.ssm-incidents` with `StartIncident` API; confirm response plan ARN is correct; check IAM permissions on the EventBridge rule's execution role.
- **Problem**: AWS Health events not routing to SSM Incident Manager (OPS10) → **Solution**: Enable AWS Health event forwarding in EventBridge; add a rule matching `aws.health` source events; confirm the target response plan handles `EVENT` type incidents.

---

## Verification Loop

Execute after each architecture review or implementation:

### 1. IaC Coverage
```bash
aws cloudformation describe-stacks --query "Stacks[*].StackName"
aws cloudformation detect-stack-drift --stack-name <STACK_NAME>
# Expected: All production resources in stacks; DriftStatus = NOT_CHECKED or IN_SYNC
```

### 2. Observability Baseline
```bash
aws cloudwatch describe-alarms --query "MetricAlarms[*].AlarmName"
aws cloudtrail describe-trails --query "trailList[?IsOrganizationTrail==\`true\`]"
# Expected: Alarms exist; at least one org-wide trail active
```

### 3. Deployment Safety
```bash
aws deploy get-deployment-group --application-name <APP> --deployment-group-name <DG> \
  --query "deploymentGroupInfo.deploymentStyle"
# Expected: deploymentOption = WITH_TRAFFIC_CONTROL (blue/green or canary)
```

### 4. Multi-Account Governance
```bash
aws organizations list-accounts --query "Accounts[*].Id"
# Expected: Multiple accounts; confirm Control Tower enrollment in AWS Console
```

### 5. Incident Readiness
```bash
aws ssm-incidents list-response-plans
# Expected: At least one response plan per severity tier
```

**Troubleshooting**:
- `detect-stack-drift` reports drifted resources → Investigate CloudTrail for console mutations; remediate via CloudFormation stack update.
- `describe-alarms` returns empty → Instrument CloudWatch metrics and create alarms before next deployment.
- `list-accounts` returns single account → Enroll in Control Tower; migrate workloads to isolated accounts.

---

## Quick Reference

**Critical AWS CLI commands**:
```bash
aws cloudformation detect-stack-drift --stack-name <name>
aws cloudwatch describe-alarms --alarm-name-prefix <prefix>
aws cloudtrail describe-trails
aws organizations list-accounts
aws ssm-incidents list-response-plans
aws deploy get-deployment-group --application-name <app> --deployment-group-name <dg>
```

**Critical limits**:

| Resource | Limit | Scope |
|----------|-------|-------|
| OE Design Principles | 8 (Nov 2024) | Reject any source citing 5 |
| CodeDeploy blue/green capacity | 2x normal | During deployment window only |
| CloudWatch Logs retention | Configure per compliance requirement | Default = never expire |
| SSM Automation concurrent executions | 75 (soft limit) | Per account per region |

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/applying-aws-operational-excellence/
├── SKILL.md                              <- This file (guardrails + summaries)
└── blueprints/
    └── evaluation-scenarios.md           <- 6 test scenarios for skill-evaluator
```

---

## External Resources

### Official Documentation
- [OE Pillar Overview](https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/) — Current stable (Nov 6, 2024)
- [OE Design Principles](https://docs.aws.amazon.com/wellarchitected/latest/framework/oe-design-principles.html) — 8 principles (accessed 2026-08-27)
- [AWS Well-Architected Framework](https://docs.aws.amazon.com/wellarchitected/latest/framework/) — All five pillars

### November 2024 Edition Announcement
- [AWS Blog: Nov 2024 WAF Updates](https://aws.amazon.com/blogs/architecture/announcing-updates-to-the-aws-well-architected-framework-guidance-3/) — 2024-11-06; authoritative source for OPS02-BP02 (Q Business) and OPS10 (AWS Health)

### Related Services
- [AWS Systems Manager Incident Manager](https://docs.aws.amazon.com/incident-manager/latest/userguide/) — Runbooks and response plans
- [AWS Fault Injection Service](https://docs.aws.amazon.com/fis/latest/userguide/) — Game day tooling
- [AWS Control Tower](https://docs.aws.amazon.com/controltower/latest/userguide/) — Landing zone and guardrails
