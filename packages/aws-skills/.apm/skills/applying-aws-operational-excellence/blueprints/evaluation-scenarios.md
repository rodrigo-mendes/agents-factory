# Evaluation Scenarios — applying-aws-operational-excellence

Skill under test: `applying-aws-operational-excellence`
Edition: AWS Well-Architected Framework — Operational Excellence Pillar, November 6, 2024

---

## Scenario 1 — Canonical: New Production Workload OE Review

```json
{
  "skills": ["applying-aws-operational-excellence"],
  "query": "We are launching a new customer-facing Node.js API on AWS Lambda behind API Gateway. What Operational Excellence patterns must we implement before going to production?",
  "expected_behavior": [
    "Identifies all six Always-Do patterns: IaC, observability from day one, CI/CD with canary/blue-green, runbooks + incident management, multi-account governance, Q Business for ops teams",
    "Recommends CloudFormation or CDK for Lambda/API Gateway resources — no console deployment",
    "Requires CloudWatch metrics, X-Ray tracing, alarms on customer-impacting thresholds, and an org-wide CloudTrail trail before first production deployment",
    "Recommends CodePipeline + CodeDeploy canary with automatic CloudWatch alarm-triggered rollback",
    "References November 6, 2024 edition of the OE pillar"
  ]
}
```

---

## Scenario 2 — Architectural Decision: Deployment Strategy Selection

```json
{
  "skills": ["applying-aws-operational-excellence"],
  "query": "Our team is debating whether to use canary or blue/green deployments for a financial services API. Which should we choose?",
  "expected_behavior": [
    "Invokes Ask-First decision A: asks about rollback time requirement and blast-radius tolerance before recommending",
    "Presents the tradeoff table: canary (incremental safety, lower cost) vs blue/green (instant full-environment rollback, double capacity cost during transition)",
    "Does NOT prescribe a single answer without knowing the rollback time requirement",
    "Notes that all-at-once is inappropriate for customer-facing production workloads in financial services",
    "Explains that CodeDeploy alarm-triggered automatic rollback applies to both canary and blue/green"
  ]
}
```

---

## Scenario 3 — Anti-Pattern Trap: Console-Driven Production Change

```json
{
  "skills": ["applying-aws-operational-excellence"],
  "query": "We need to make a quick config change in production — can we just update the Lambda environment variable directly in the console to save time?",
  "expected_behavior": [
    "Identifies this as OE-N1 (Click-Ops) — HIGH risk anti-pattern",
    "Explains: console mutation creates config drift, is unrepeatable, and produces an unknown production state",
    "Offers the correct alternative: update the CloudFormation/CDK stack or SSM Parameter Store via a fast-path pipeline — maintains audit trail and auto-rollback capability",
    "Does NOT endorse the console change even for 'quick fixes'",
    "References CloudTrail detection method: ConsoleLogin followed by mutating API calls with no corresponding stack event"
  ]
}
```

---

## Scenario 4 — Edge Case: Regulated Workload with Approval Gates

```json
{
  "skills": ["applying-aws-operational-excellence"],
  "query": "We operate a PCI-DSS workload and need to ensure all production deployments have a documented human approval before release. How do we implement this with OE patterns?",
  "expected_behavior": [
    "Recommends CodePipeline with a manual approval action and Amazon SNS notification to approvers",
    "Recommends AWS Config rules to validate compliance posture pre-deployment",
    "Recommends a post-deployment Config conformance pack to verify deployed state matches the approved baseline",
    "Notes that CloudTrail captures approver identity for audit — satisfying PCI DSS 10.x audit log requirements",
    "Does NOT skip OE-A1 through OE-A5 — all mandatory patterns still apply; manual approval gate is additive",
    "References the Scenario Coverage 'Edge Case' from the November 2024 edition"
  ]
}
```

---

## Scenario 5 — Misuse: Stale Source with 5 Design Principles

```json
{
  "skills": ["applying-aws-operational-excellence"],
  "query": "I found an AWS blog post from 2022 that lists the 5 OE design principles. Should I use that as my reference?",
  "expected_behavior": [
    "Explicitly flags the 2022 source as stale — the November 6, 2024 edition expanded OE design principles from 5 to 8",
    "Names the three new principles: 'Organize teams around business outcomes', 'Implement observability for actionable insights', 'Use managed services'",
    "Notes that 'Perform operations as code' was renamed to 'Safely automate where possible'",
    "Directs to the current stable official source: https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/",
    "Does NOT accept the 5-principle model or blend it with the current edition"
  ]
}
```

---

## Scenario 6 — Complex: Multi-Account Governance Gap Identification

```json
{
  "skills": ["applying-aws-operational-excellence"],
  "query": "Our startup runs all workloads — dev, staging, and production — in a single AWS account. We want to improve our operational posture. What is the highest-risk gap?",
  "expected_behavior": [
    "Identifies the flat single-account architecture as OE-N6 — HIGH risk anti-pattern",
    "Explains: no workload isolation, no audit boundary, blast radius spans all workloads, no SCP guardrails",
    "Recommends immediate path: enroll in AWS Control Tower to establish a landing zone; use AWS Organizations + SCPs; automate account vending via Service Catalog",
    "Recommends the verification command: `aws organizations list-accounts` to confirm current state",
    "Advises that this must be remediated before other OE improvements have their full intended effect — lack of account isolation undermines blast-radius controls in OE-A3 and audit boundaries in OE-A2"
  ]
}
```
