# Post-2022 Gaps — applying-aws-serverless-well-architected-lens

The Serverless Applications Lens content is dated **2022-07-14** (https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/welcome.html, accessed 2026-08-27). The "2026" on the PDF is a copyright stamp only — no content revision exists. Capabilities released after July 2022 are absent or under-represented and must be verified against current AWS documentation before any architecture decision.

> ⚠️ Treat every row below as a `Migration Note`: the lens is silent, so the lens cannot be cited as authority for these features.

---

## Gap inventory

| Capability | Status vs. lens | Verify at |
|---|---|---|
| Lambda SnapStart (Java, later Python/.NET) | Not covered | AWS Lambda Developer Guide |
| Lambda arm64 / Graviton2 cost-performance | Not emphasized | AWS Lambda pricing / compute docs |
| Lambda response streaming | Not covered | AWS Lambda Developer Guide |
| Lambda function recursion detection | Not covered | AWS Lambda Developer Guide |
| Lambda Destinations (on-success / on-failure) | Partially (DLQ-centric framing) | AWS Lambda async invocation docs |
| Powertools for AWS Lambda (current name / features) | Referenced as "Lambda Powertools" | Powertools for AWS Lambda docs |
| Sustainability pillar serverless guidance | Thin / deferred | Base Well-Architected Sustainability pillar |

**Source**: research knowledge base, Migration Notes section, derived from the lens content dated 2022-07-14.

---

## Notes per gap

### Lambda SnapStart (Java)
- SnapStart snapshots the initialized execution environment to cut Java cold starts; Java integration uses the Coordinated Restore at Checkpoint (CRaC) API. Source: https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html (published 2023-11 per research; verified 2026-06-01).
- Network clients (AWS SDK, HTTP connection pools) left open at checkpoint can fail after restore — close them in `beforeCheckpoint` and recreate them in `afterRestore`. (unverified — the Java research cites "Lambda SnapStart CRaC Lifecycle" without a dated URL)
- Do not initialize `SecureRandom` seeds or cryptographic keys during static init under SnapStart — they would be frozen in the snapshot and duplicated across restored environments; initialize lazily or regenerate in `afterRestore`. (unverified)
- SnapStart vs. Provisioned Concurrency trade-offs (cost, architecture support) — the Java research claims SnapStart is limited to x86_64 and has no standing cost. (unverified — confirm in the Lambda Developer Guide; SnapStart pricing for some runtimes may differ)
- Relationship to [ask-first-decisions.md](./ask-first-decisions.md) Decision 1: for Java functions, raise SnapStart as an additional option alongside Provisioned Concurrency.

### arm64 / Graviton2
- The lens's cost/performance guidance predates the broadly recommended arm64/Graviton2 lever. Source: research Cost Optimization migration note (lens dated 2022-07-14).
- The Java research states arm64 is "20% cheaper". (unverified — confirm against current AWS Lambda pricing)

### Recursion detection
- The lens does not cover Lambda recursion detection. Independently, avoid functions that write back to the resource that triggers them (e.g., S3 object write → same bucket/prefix trigger; DynamoDB Streams → same table) — use prefix filters such as `incoming/` → `processed/` or exit guards. (unverified — Java research anti-pattern without a dated official URL)

### Lambda Destinations
- The lens frames failure capture around DLQs; Lambda Destinations (`on-failure` → SQS) are the async-invocation mechanism referenced in the SKILL.md verification loop (`put-function-event-invoke-config`).
- The Java research states async triggers retry 2 times by default before discarding. (unverified — research cites "AWS Lambda Destinations Documentation" without a dated URL)

### Powertools for AWS Lambda
- The lens calls it "Lambda Powertools"; the current product name is "Powertools for AWS Lambda". Docs: https://docs.powertools.aws.dev/lambda/ (unverified for currency — no access date in the research).

### Response streaming
- Not covered by the lens and not detailed in either research file. (unverified — verify in the AWS Lambda Developer Guide: https://docs.aws.amazon.com/lambda/latest/dg/welcome.html)

### Sustainability
- The lens does not substantively expand the Sustainability pillar; defer to the base Well-Architected Sustainability pillar. Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/the-pillars-of-the-well-architected-framework.html (2022-07-14)

---

## Also deferred to the base framework (not gaps, but not lens content)

- **Incident response**: "will not be described in this document because the practices from the AWS Well-Architected Framework still apply." Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/security-pillar.html (2022-07-14)
- **Change management**: "There are no operational practices unique to serverless applications for this best practice." Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/change-management.html (2022-07-14)

---

## Source-quality caveat

The Java research file (Java 21 / AWS SDK 2.45.1, research date 2026-06-02) lists the lens welcome page as "Published: August 14, 2024", which conflicts with the 2022-07-14 date verified in the primary lens research. This skill follows the 2022-07-14 date; claims taken only from the Java research are marked (unverified) above.
