# Evaluation Scenarios — cloud-architecture-researcher

Used to verify that the skill activates correctly, enforces provider-edition absolutism, produces
architecture knowledge bases with full decision traceability (context/forces/solution/trade-offs/
verification), fires Ask First gates for underspecified multi-cloud requests, and rejects misuse
requests (implementation asks, unversioned queries, architecture-decision shortcuts).

---

## Scenario 1: Standard research request — provider + edition + context pinned (canonical path)

```json
{
  "skills": ["cloud-architecture-researcher"],
  "query": "Research AWS Well-Architected Framework 2024 for a B2B SaaS platform with multi-tenant requirements. Target audience: cloud architects and tech leads.",
  "expected_behavior": [
    "Sets CLOUD_PROVIDER=AWS, ARCHITECTURE_DOMAIN=Well-Architected Framework, TARGET_EDITION=AWS WAF 2024, ARCHITECTURE_CONTEXT=B2B SaaS with multi-tenant requirements",
    "Maps all 6 AWS WAF pillars to the multi-tenant SaaS context: Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, Sustainability",
    "Always Do patterns include: multi-AZ for stateful services, encryption at rest/in-transit, IAM least-privilege, VPC with public/private subnets, centralized logging, automated backups, tagging strategy, Secrets Manager for credentials, DR strategy with RTO/RPO defined",
    "Ask First decisions include: compute model (Lambda vs ECS vs EC2), data architecture (RDS vs DynamoDB vs Aurora Serverless), messaging (SQS vs Kinesis vs EventBridge), account strategy (single vs Organizations multi-account), region strategy (single vs active-passive vs active-active)",
    "Never Do patterns each include ❌ wrong architecture description and ✅ correct architecture with exact AWS service names",
    "Uses exact AWS service names throughout — no generic terms ('managed object store' instead of 'S3' is not acceptable)",
    "Sources cite AWS Well-Architected Framework documentation and AWS Architecture Center URLs dated <= 12 months"
  ],
  "success_criteria": {
    "must_pass": [
      "All 6 AWS WAF pillars addressed with multi-tenant SaaS context applied per pillar",
      "Every Never Do entry includes ❌ wrong pattern and ✅ correct architecture (not prose-only prohibition)",
      "Exact AWS service names used (S3, RDS, Lambda, CloudWatch, etc.) — no generic substitutes",
      "At least one SaaS-specific lens or scenario guidance cited (AWS SaaS Lens if available in WAF 2024)",
      "Trade-off table present for at least the compute model and data architecture Ask First decisions"
    ],
    "must_not": [
      "Mix AWS WAF 2023 guidance that was superseded in 2024 edition",
      "Use generic terms where provider-specific names exist",
      "Produce Never Do prohibitions without architecture-level correct alternatives",
      "Omit the multi-tenant context from pillar analysis"
    ]
  }
}
```

---

## Scenario 2: Edge case — underspecified multi-cloud request triggers Ask First guardrail

```json
{
  "skills": ["cloud-architecture-researcher"],
  "query": "Research networking architecture patterns for AWS, Azure, and GCP. We need to compare hub-spoke vs mesh topology across all three providers.",
  "expected_behavior": [
    "Recognizes the query as multi-cloud scope without edition pinning, output format, or per-provider vs. unified preference — all three are required inputs per the Ask First guardrail",
    "Does NOT begin research immediately; activates the mandatory 'Ask First — Multi-cloud scope' gate",
    "Presents scope-clarification options to the user: (A) per-provider sections in one document, (B) comparison matrix with one row per service/decision, (C) unified patterns with provider callouts",
    "Requests edition pinning per provider (e.g., AWS WAF 2024, Azure CAF date, GCP Architecture Framework date)",
    "Explains why it is stopping: cross-provider comparisons are Medium Confidence by default and need explicit scope to avoid conflating provider behaviors",
    "Does NOT produce networking research output, Service Equivalence Maps, or lock-in assessments before scope is confirmed"
  ],
  "success_criteria": {
    "must_pass": [
      "Skill does not produce research output before scope is confirmed",
      "Skill explicitly activates the Ask First gate and names the missing inputs (format, edition per provider)",
      "Skill presents at least two distinct output format options for the user to choose from",
      "Skill states that cross-provider comparisons will be marked Medium Confidence once research proceeds"
    ],
    "must_not": [
      "Proceed directly to research without asking for scope confirmation",
      "Produce a Service Equivalence Map, lock-in assessment, or per-provider constraints before the gate is resolved",
      "Refuse to help entirely — must offer to proceed once scope inputs are provided"
    ]
  }
}
```

---

## Scenario 5: Edge case — pre-scoped multi-cloud request produces research with provider fidelity

```json
{
  "skills": ["cloud-architecture-researcher"],
  "query": "Research hub-spoke vs mesh networking topology for AWS, Azure, and GCP. Use comparison matrix format. Pin to AWS WAF 2024, Azure CAF November 2024, GCP Architecture Framework 2024. Target audience: cloud architects evaluating topology for a hybrid enterprise network.",
  "expected_behavior": [
    "Sets CLOUD_PROVIDER=Multi-Cloud, ARCHITECTURE_DOMAIN=Networking Architecture, TARGET_EDITION pinned per-provider as instructed, OUTPUT_FORMAT=comparison matrix",
    "Uses exact provider-specific service names for hub-spoke: AWS Transit Gateway, Azure Virtual WAN, GCP Network Connectivity Center; for mesh: AWS VPC Peering, Azure VNet Peering, GCP VPC Peering",
    "Produces the Service Equivalence Map for networking primitives across all three providers",
    "Documents lock-in assessment per topology option and per provider",
    "Flags where provider capabilities diverge (e.g., AWS Transit Gateway attachment limits vs Azure Virtual WAN branch site limits vs GCP Cloud Interconnect constraints)",
    "Sources each provider's content from its own official documentation — no cross-provider assumptions",
    "Marks all cross-provider comparisons as Medium Confidence with a note that each must be validated against current per-provider docs"
  ],
  "success_criteria": {
    "must_pass": [
      "Hub-spoke and mesh services named exactly for each provider (AWS Transit Gateway / Azure Virtual WAN / GCP Network Connectivity Center; AWS VPC Peering / Azure VNet Peering / GCP VPC Peering)",
      "Service Equivalence Map section present covering networking primitives across all three providers",
      "Lock-in assessment present for each topology option across providers",
      "Provider-specific constraints documented (limits, GA status, regional availability) for at least one provider",
      "Cross-provider comparisons explicitly marked as Medium Confidence"
    ],
    "must_not": [
      "Use generic names ('cloud router', 'managed VPN', 'hub gateway') where provider-specific names exist",
      "Present one provider's behavior as universal (e.g., describe Azure VWAN limits as if they apply to AWS TGW)",
      "Mark cross-provider comparisons as High Confidence without per-provider source links"
    ]
  }
}
```

---

## Scenario 3: Misuse / out-of-scope — asked to produce an Architecture Decision Record, not research

```json
{
  "skills": ["cloud-architecture-researcher"],
  "query": "Write an Architecture Decision Record (ADR) for why we chose AWS EKS over ECS for our platform. Include the decision, status, context, consequences, and alternatives considered.",
  "expected_behavior": [
    "Recognizes this is an ADR authoring request for a specific already-made decision, not an architecture research request — this skill produces a knowledge base for architects to make decisions, not ADRs documenting decisions already made",
    "Explicitly declines producing a final ADR as deliverable",
    "Explains correct routing: ADR authoring belongs to the architect agent consuming the knowledge base; this skill provides the research (EKS vs ECS trade-offs, WAF alignment, operational burden) that informs the ADR",
    "Offers to instead research AWS container orchestration options (EKS vs ECS vs App Runner) within the AWS WAF framework, producing the structured trade-off knowledge that an architect can use to write the ADR",
    "Does NOT produce an ADR document with Status/Context/Decision/Consequences sections"
  ],
  "success_criteria": {
    "must_pass": [
      "Skill declines to produce the ADR as deliverable",
      "Skill explains the research-vs-decision-documentation boundary",
      "Skill offers a corrected research scope (AWS container orchestration trade-off research)"
    ],
    "must_not": [
      "Produce an ADR document as primary output",
      "Silently shift from research mode to decision documentation mode",
      "Generate a Status/Context/Decision/Consequences structured document"
    ]
  }
}
```

---

## Scenario 4: Anti-pattern trap — requesting architectures with known systemic risks

```json
{
  "skills": ["cloud-architecture-researcher"],
  "query": "We want to deploy our production database as a single-AZ RDS instance to save costs. Also, we'll store our API keys directly in our Lambda environment variables — it's simpler than Secrets Manager. Research OCI best practices for our setup.",
  "expected_behavior": [
    "Flags both requests as Never Do violations before producing research output",
    "For single-AZ production database: ❌ shows single-AZ RDS with no Multi-AZ standby — cites Reliability pillar violation, describes blast radius (full data layer outage on AZ failure, potential data loss within RPO window); ✅ shows Multi-AZ deployment with automatic failover, cites specific RTO/RPO guarantees from AWS documentation",
    "For API keys in Lambda env vars: ❌ shows Lambda environment variable with plaintext API key — explains keys are visible in console, exported in describe-function API, stored unencrypted in function config; ✅ shows AWS Secrets Manager retrieval pattern (secretsmanager:GetSecretValue) or SSM Parameter Store with KMS encryption, cites Security pillar",
    "Proceeds to research OCI best practices after flagging and correcting the anti-patterns — does not refuse entirely",
    "OCI research uses OCI-specific service names (OCI DB Systems with Data Guard for HA, OCI Vault for secrets management)"
  ],
  "success_criteria": {
    "must_pass": [
      "Both anti-patterns (single-AZ production DB, plaintext secrets in env vars) explicitly flagged with pillar citation",
      "❌ wrong architecture and ✅ correct architecture with exact service names for both",
      "Research output uses OCI service names for the corrected patterns (OCI Vault, OCI DB with Data Guard or Autonomous Database)",
      "Skill does not refuse to produce research — it corrects and proceeds"
    ],
    "must_not": [
      "Produce research that normalizes single-AZ for production stateful workloads",
      "Show plaintext API keys in environment variables as an acceptable pattern",
      "Silently comply with both requests without flagging the reliability and security violations"
    ]
  }
}
```
