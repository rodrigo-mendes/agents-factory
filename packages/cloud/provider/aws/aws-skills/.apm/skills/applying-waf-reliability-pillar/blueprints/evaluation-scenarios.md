# Evaluation Scenarios — applying-waf-reliability-pillar

6 test cases covering canonical use, edge cases, and anti-pattern traps.

---

## Scenario 1 — Canonical: Multi-AZ baseline design review

```json
{
  "skills": ["applying-waf-reliability-pillar"],
  "query": "We are deploying a production web API on AWS using EC2 with an ALB. The RDS instance is single-AZ in us-east-1a. Review this architecture against the Reliability Pillar.",
  "expected_behavior": [
    "Identifies single-AZ RDS as a CRITICAL anti-pattern (REL10-BP01)",
    "Recommends enabling RDS Multi-AZ or migrating to Aurora multi-AZ",
    "Verifies EC2 ASG spans >=2 AZs behind the ALB",
    "Asks for defined RTO/RPO to guide DR strategy selection (REL13-BP01)",
    "Provides AWS CLI detection command for MultiAZ=false"
  ]
}
```

---

## Scenario 2 — Canonical: DR strategy selection

```json
{
  "skills": ["applying-waf-reliability-pillar"],
  "query": "Our business requires RTO of 15 minutes and RPO of 2 minutes for our order processing service. Which DR strategy should we use?",
  "expected_behavior": [
    "Identifies Pilot Light as the matching DR tier (RPO minutes / RTO tens of minutes)",
    "References the DR Strategy Matrix and REL13-BP02",
    "Recommends AWS Elastic Disaster Recovery, Aurora replicas, and ARC for failover routing",
    "Emphasizes testing the strategy (REL13-BP03) — not leaving it ad-hoc",
    "Notes that data-plane failover via ARC is required to avoid control-plane dependency during recovery"
  ]
}
```

---

## Scenario 3 — Edge case: Multi-Site Active/Active with data-residency constraints

```json
{
  "skills": ["applying-waf-reliability-pillar"],
  "query": "We need near-zero RTO and RPO for a global payments workload and we're considering Multi-Site Active/Active. We also have data-residency requirements — customer data cannot leave the EU.",
  "expected_behavior": [
    "Confirms Multi-Site Active/Active is appropriate for mission-critical near-zero RTO/RPO",
    "Flags data-residency constraints as an Ask-First item before recommending specific Regions",
    "Notes that near-zero RPO still requires point-in-time backups for logical corruption/deletion",
    "Warns about write-conflict handling with DynamoDB global tables (last-writer-wins)",
    "Recommends Aurora Global Database for managed low-RPO cross-Region replication",
    "Does NOT make compliance/regulatory commitments — surfaces as compliance-scope question"
  ]
}
```

---

## Scenario 4 — Edge case: Control-plane dependency in DR runbook

```json
{
  "skills": ["applying-waf-reliability-pillar"],
  "query": "Our DR runbook says: on failover, run a script that calls RunInstances to launch 50 EC2 instances in the recovery Region and then updates the ASG desired capacity to 50. Is this a valid approach?",
  "expected_behavior": [
    "Identifies this as a CRITICAL anti-pattern: control-plane dependency during recovery (REL11-BP04, REL13-BP02 named anti-pattern)",
    "Explains that control planes have lower availability design goals and may be degraded during broad failures",
    "Recommends pre-provisioning the recovery Region (static stability, REL11-BP05)",
    "Recommends using Amazon ARC data-plane routing controls to flip traffic — not resource creation",
    "Provides the correct Warm Standby pattern as an alternative"
  ]
}
```

---

## Scenario 5 — Anti-pattern trap: Retry storm

```json
{
  "skills": ["applying-waf-reliability-pillar"],
  "query": "Our microservice retries failed HTTP calls every 1 second, up to 100 times. We also have API Gateway retry on error. During a downstream outage, we saw a cascade. What went wrong?",
  "expected_behavior": [
    "Identifies fixed-interval retries as the anti-pattern (REL05-BP03)",
    "Identifies retrying at multiple layers (app + API Gateway) as the retry storm cause",
    "Recommends exponential backoff + jitter at a single layer with bounded max retries (3-5)",
    "Recommends making mutating operations idempotent (REL04-BP04) so retries are safe",
    "Notes AWS SDKs implement retries/backoff by default — leverage SDK rather than custom loops"
  ]
}
```

---

## Scenario 6 — Anti-pattern trap: Asking the skill to set RTO/RPO or make compliance commitments

```json
{
  "skills": ["applying-waf-reliability-pillar"],
  "query": "Tell me what our RTO and RPO should be, and confirm that using Aurora Global Database makes us SOC 2 compliant.",
  "expected_behavior": [
    "Declines to invent RTO/RPO — explains these are business requirements derived from business impact analysis (REL13-BP01)",
    "Directs user to obtain RTO/RPO from business stakeholders, not from the skill",
    "Declines to make compliance commitments — states compliance scope must be verified with qualified assessors",
    "Offers to explain what DR strategies are achievable at different RTO/RPO targets once business-defined objectives are provided",
    "Does NOT fabricate specific RPO/RTO numbers or confirm SOC 2 scope"
  ]
}
```
