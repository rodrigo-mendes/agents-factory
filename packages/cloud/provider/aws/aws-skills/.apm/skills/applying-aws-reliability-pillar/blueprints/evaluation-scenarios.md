# Evaluation Scenarios — applying-aws-reliability-pillar

Test cases for `/evaluating-skill-scenarios applying-aws-reliability-pillar`.

---

## Scenario 1 — Canonical: Multi-AZ Web Application Design

```json
{
  "skills": ["applying-aws-reliability-pillar"],
  "query": "Design a highly available web application on AWS for a production e-commerce workload. The business requires less than 1 hour of downtime per year. Recommend the architecture.",
  "expected_behavior": [
    "Recommends EC2 Auto Scaling group spanning ≥2 AZs (≥3 preferred) behind an Application Load Balancer with cross-zone load balancing",
    "Specifies Amazon RDS Multi-AZ with synchronous standby for the database tier",
    "Includes AWS Backup with cross-Region copy for RDS and EBS",
    "References REL10-BP01 (fault isolation) and Design Principle 3 (scale horizontally)",
    "Mentions CloudWatch KPI-based alarms driving Auto Scaling policies",
    "Does NOT recommend single-AZ deployment as a cost-saving measure"
  ]
}
```

---

## Scenario 2 — Canonical: DR Strategy Selection

```json
{
  "skills": ["applying-aws-reliability-pillar"],
  "query": "Our business has defined RTO of 15 minutes and RPO of 5 minutes for our critical order management service. Which DR strategy should we use and why?",
  "expected_behavior": [
    "Identifies that 15-minute RTO and 5-minute RPO rules out Backup & Restore (RTO hours) and likely Pilot Light (RTO tens of minutes)",
    "Recommends Warm Standby (RTO minutes, RPO seconds) as the appropriate tier",
    "Mentions Multi-Site Active/Active only if the business requires near-zero RTO/RPO or global distribution",
    "Specifies IaC (CloudFormation/StackSets) for all DR infrastructure to prevent configuration drift (REL13-BP04)",
    "Recommends Amazon Application Recovery Controller (ARC) for data-plane-independent failover",
    "Notes that data-plane operations only should be used during DR (REL11-BP04) — no control-plane API calls during recovery",
    "Asks to confirm whether data residency regulations permit cross-Region data transfer before confirming multi-Region"
  ]
}
```

---

## Scenario 3 — Canonical: Fault Injection Testing Plan

```json
{
  "skills": ["applying-aws-reliability-pillar"],
  "query": "How do we validate that our AWS workload will actually recover within our defined RTO/RPO targets before a real disaster?",
  "expected_behavior": [
    "Recommends AWS Fault Injection Service (FIS) for controlled failure experiments",
    "Specifies that each FIS experiment template must include CloudWatch-based stop conditions to auto-halt on real customer impact",
    "Lists representative experiment scenarios: AZ impairment, instance termination, network latency injection",
    "Recommends scheduling game days via Amazon EventBridge on a regular cadence",
    "Emphasizes measuring achieved RTO/RPO vs targets after each drill and recording results",
    "References Design Principle 2 (Test recovery procedures via automation) and REL13-BP03",
    "Does NOT recommend running experiments without stop conditions in production"
  ]
}
```

---

## Scenario 4 — Edge Case: Near-Zero RPO/RTO for Mission-Critical Global Workload

```json
{
  "skills": ["applying-aws-reliability-pillar"],
  "query": "We need near-zero RTO and RPO for a globally distributed financial transactions platform. The workload uses a relational database. Design the reliability architecture.",
  "expected_behavior": [
    "Recommends Multi-Site Active/Active DR strategy",
    "Specifies Aurora Global Database for the relational tier: cross-Region replication lag <1 second, managed secondary promotion in <1 minute even in complete regional outage",
    "Recommends Amazon Application Recovery Controller (ARC) routing controls for immediate, control-plane-independent traffic shifting",
    "Includes AWS FIS game days to validate recovery before a real event",
    "Notes that Aurora Global Database uses active-passive replication (writes to primary only) — contrast with DynamoDB global tables for active-active NoSQL",
    "Warns about highest cost/complexity tier and asks whether the business truly requires near-zero RTO/RPO or whether Warm Standby would suffice",
    "Notes data residency regulatory confirmation required before cross-Region deployment"
  ]
}
```

---

## Scenario 5 — Anti-Pattern Trap: Replication-Only Backup Strategy

```json
{
  "skills": ["applying-aws-reliability-pillar"],
  "query": "We've set up S3 Cross-Region Replication to our DR Region and DynamoDB global tables. Our backup strategy is complete, right?",
  "expected_behavior": [
    "Flags REL-ND-4: replication alone does not protect against data corruption or accidental deletion",
    "Quotes REL13-BP02 directly: 'Continuous data replication protects against some types of disaster, but not data corruption/destruction unless strategy also includes versioning or PITR'",
    "Specifies required additions: S3 versioning (protects against deletion/corruption), DynamoDB PITR (restore to any point in time), AWS Backup for independent point-in-time restore capability",
    "Explains that corrupted or deleted data is replicated to the DR copy, making both copies unusable",
    "Does NOT validate the replication-only strategy as complete"
  ]
}
```

---

## Scenario 6 — Anti-Pattern Trap: Single-AZ Cost Savings Request

```json
{
  "skills": ["applying-aws-reliability-pillar"],
  "query": "Our client wants to save costs by running a single EC2 instance and a single-AZ RDS in production instead of Multi-AZ. Can we do this?",
  "expected_behavior": [
    "Flags REL-ND-1 (CRITICAL): single-AZ deployment means AZ failure = complete production outage with no automatic recovery",
    "Quantifies the RTO implication: a single EC2 instance with no ASG requires manual operator intervention with no automatic recovery; RDS without Multi-AZ requires Multi-AZ to be pre-enabled — cannot be enabled during an outage",
    "Asks the client for their defined RTO/RPO requirements and presents the quantified cost of downtime (from their own business impact analysis) against the incremental cost of Multi-AZ + ASG",
    "States that if the client confirms acceptance of the RTO/RPO implications in writing, the decision should be documented along with the accepted risk",
    "Does NOT proceed silently or accept the single-AZ approach without surfacing the risk explicitly",
    "References REL10-BP01 and Design Principle 3 (scale horizontally)"
  ]
}
```
