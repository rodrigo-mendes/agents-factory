# Evaluation Scenarios — applying-aws-performance-efficiency

Test cases for `/evaluating-skill-scenarios applying-aws-performance-efficiency`.

---

## Scenario 1 — Canonical: New web application compute design

```json
{
  "skills": ["applying-aws-performance-efficiency"],
  "query": "We are designing a new web application on AWS. Traffic is variable with clear daily peaks (10x spike). The application is stateless. What compute architecture should we use?",
  "expected_behavior": [
    "Recommends EC2 Auto Scaling with target-tracking policy based on RequestCountPerTarget (ALB metric) — appropriate for steady HTTP workload with variable traffic",
    "Recommends Graviton5 M9g as the instance family (not Graviton4, not x86) since Graviton5 is the 2026 default for general-purpose ARM64",
    "Asks whether all application dependencies support ARM64 before committing to Graviton5",
    "Asks whether target region carries M9g instances",
    "Requires CloudWatch agent installation for memory metrics as prerequisite",
    "Recommends enabling Compute Optimizer across all accounts",
    "Does NOT recommend a fixed static fleet without an Auto Scaling policy (PE-ND-5)"
  ]
}
```

---

## Scenario 2 — Edge: Memory-optimised ARM64 workload in 2026

```json
{
  "skills": ["applying-aws-performance-efficiency"],
  "query": "We need a memory-optimised ARM64 EC2 instance for an in-memory data processing workload. Should we use an R-series Graviton5 instance?",
  "expected_behavior": [
    "Flags that R-series Graviton5 (R9g) was NOT confirmed GA as of 2026-08-28 based on the research",
    "Recommends defaulting to Graviton4 R8g for memory-optimised ARM64 until R-series Graviton5 is verified GA",
    "Advises verifying current R9g GA status against official EC2 instance-types page before making a design commitment",
    "Does NOT assert that R9g exists or is available — avoids hallucinating a GA that is unconfirmed",
    "Still recommends Graviton4 R8g as a valid, cost-effective choice over x86 for this use case"
  ]
}
```

---

## Scenario 3 — Anti-pattern trap: Team proposes oversized single instance

```json
{
  "skills": ["applying-aws-performance-efficiency"],
  "query": "Our team wants to use a single r8g.8xlarge instance for our API tier to avoid scaling complexity. We'll over-provision to be safe. Is this acceptable?",
  "expected_behavior": [
    "Identifies this as PE-ND-2 (over-provision instead of right-size) — Risk: HIGH",
    "Cites PERF02-BP04 and PERF02-BP05 as the violated best practices",
    "Does NOT accept the proposal without challenge",
    "Asks for p99 latency requirements and actual traffic profile (requests per second, daily/weekly shape)",
    "Asks whether the workload has been load-tested on a smaller instance in non-production",
    "Recommends starting with a Compute Optimizer-recommended right-sized instance in an EC2 Auto Scaling group with target-tracking",
    "Suggests load-testing evidence as the basis for sizing rather than safety-margin intuition",
    "Points out that a single oversized instance cannot horizontally scale and creates a single point of failure"
  ]
}
```

---

## Scenario 4 — Edge: Data store selection for mixed access patterns

```json
{
  "skills": ["applying-aws-performance-efficiency"],
  "query": "We have one Amazon RDS PostgreSQL instance that handles our relational queries, user session caching, full-text product search, and high-volume order ID lookups. Is this a good architecture?",
  "expected_behavior": [
    "Identifies this as PE-ND-6 — violates mechanical sympathy design principle (Risk: MEDIUM)",
    "References PERF03 data management best-practice area",
    "Recommends polyglot persistence: ElastiCache Redis for session caching, Amazon OpenSearch Service for full-text search, DynamoDB for high-volume key-value (order ID lookups), retain RDS/Aurora for relational queries",
    "Asks what the data access patterns and latency requirements are for each use case before finalising service selection",
    "Does NOT propose adding more RDS read replicas as the solution to search or caching bottlenecks"
  ]
}
```

---

## Scenario 5 — Canonical: Graviton migration decision

```json
{
  "skills": ["applying-aws-performance-efficiency"],
  "query": "We are running an existing fleet of m5.4xlarge (x86) EC2 instances. Should we migrate to Graviton5?",
  "expected_behavior": [
    "Recommends using AWS Compute Optimizer to identify Graviton migration candidates from the existing fleet",
    "Asks whether all application dependencies and third-party binaries support ARM64 — this is a prerequisite",
    "Asks whether the target region carries M9g instances (Graviton5 regional availability check)",
    "References expected gains: up to 25% better compute performance, up to 30% faster for databases, up to 35% faster for web applications vs Graviton4 (and further vs x86)",
    "Recommends benchmarking on M9g in non-production against current m5.4xlarge before production cutover",
    "Does NOT present Graviton4 as the current-generation option — Graviton5 (M9g) is the 2026 default for general-purpose ARM64"
  ]
}
```

---

## Scenario 6 — Misuse: Requesting guidance on a different WAF pillar

```json
{
  "skills": ["applying-aws-performance-efficiency"],
  "query": "How should we design our AWS IAM policies and S3 bucket policies for our multi-account workload according to the Well-Architected Framework?",
  "expected_behavior": [
    "Recognises that IAM and S3 bucket policy design belongs to the Security Pillar, not the Performance Efficiency Pillar",
    "States clearly that this skill is scoped to the Performance Efficiency Pillar (compute, data store, scaling, Graviton)",
    "Does NOT attempt to provide Security Pillar guidance from the Performance Efficiency Pillar knowledge base",
    "Suggests consulting the AWS Well-Architected Security Pillar documentation or the aws-iam-security-serverless skill if available"
  ]
}
```
