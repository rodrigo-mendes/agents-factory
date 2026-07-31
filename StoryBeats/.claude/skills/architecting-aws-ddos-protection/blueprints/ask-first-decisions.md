# Ask First Decisions — AWS Shield DDoS Architecture

> Source: AWS WAF Developer Guide + Well-Architected Security Pillar SEC05. All sources accessed 2026-07-31.
> For each decision point: confirm with the architect/workload owner before prescribing a pattern.

---

## Decision 1: Shield Standard vs Shield Advanced

**Ask the architect**: "Is this workload business-critical, revenue-bearing, or SLA-bound? Does it process regulated data (PCI, HIPAA)?"

| Option | AWS Service | Cost | Optimizes | Sacrifices | Best When |
|--------|-------------|------|-----------|------------|-----------|
| Shield Standard only | AWS Shield Standard | Free | Zero cost; automatic L3/L4 everywhere | No L7 protection, no SRT, no cost protection, no health-based detection, no advanced metrics | Non-critical / experimental workloads; downtime-tolerant apps |
| Shield Advanced | AWS Shield Advanced + WAF | $3,000/month (1-yr) | L7 protection, SRT, proactive engagement, cost protection, Firewall Manager, real-time metrics | Flat monthly fee + DTO fees + WAF beyond the covered ceiling | Business-critical, revenue-generating, regulated, or SLA-bound internet-facing workloads |

**Cost profile**:
- Standard: $0
- Advanced: $3,000/month (1-year commitment, auto-renew) billed to the AWS Organizations payer account; covers the entire consolidated-billing family. Standard WAF fees covered up to 1,500 WCUs / default body size / 50 billion requests/month per protected resource. DTO fees still apply.

**Default recommendation**: If the workload is business-critical → Shield Advanced. If genuinely experimental and downtime-tolerant → Standard.

**Source**: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-overview.html

---

## Decision 2: CloudFront + Shield vs ALB + Shield (global edge vs regional)

**Ask the architect**: "Can this workload sit behind CloudFront? Is it HTTP(S)? Is caching or global distribution acceptable?"

| Option | AWS Service | DTO Rate | Optimizes | Sacrifices | Best When |
|--------|-------------|----------|-----------|------------|-----------|
| CloudFront (edge) + Shield Advanced + WAF | CloudFront, Shield Advanced, WAF | $0.025/GB | Absorbs attacks at global edge; largest surface reduction; lower DTO cost | CDN semantics; cache/behavior config; CloudFront learning curve | Web/HTTP(S) apps, static+dynamic content, global users |
| ALB (regional) + Shield Advanced + WAF | ALB, Shield Advanced, WAF | $0.050/GB | Regional L7 routing; direct VPC integration; simpler | Attack hits regional capacity; higher DTO cost | Regional-only apps; non-cacheable APIs where CloudFront fronting is not viable |

**Cost profile**: CloudFront DTO under Shield Advanced = $0.025/GB; ELB/EC2/Global Accelerator DTO = $0.050/GB. CloudFront reduces both the attack surface and the DTO cost.

**Default recommendation**: Prefer CloudFront + WAF + Shield for any HTTP(S) workload. Use ALB + WAF + Shield only where a direct regional entry point is architecturally required; keep the ALB's origin private (restrict security groups to CloudFront/ALB path only).

**Source**: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-edge-services.html

---

## Decision 3: Managed WAF rules vs custom WAF rules alongside Shield

**Ask the architect**: "What is your WCU budget? Do you have app-specific traffic patterns or known abuse signatures that managed rules do not cover?"

| Option | AWS Service | WCU Cost | Optimizes | Sacrifices | Best When |
|--------|-------------|----------|-----------|------------|-----------|
| AWS Managed Rules + Layer 7 Anti-DDoS group | AWS WAF Managed Rule Groups | Covered under Shield Advanced ceiling | Fast baseline coverage, AWS-maintained, Layer 7 Anti-DDoS included | Less app-specific tuning; AWS controls rule updates | Standard web apps; initial posture without bespoke traffic data |
| Custom rules (rate-based, geo, string/regex) | AWS WAF custom rules | Counts toward the 1,500-WCU covered ceiling | App-specific precision; full control | Authoring, maintenance, false-positive management | Known abuse signatures; bespoke traffic patterns; after baselining with managed rules |

**WCU budget constraints**:
- Automatic L7 mitigation rule group: 150 WCUs
- Standard WAF fees covered: up to 1,500 WCUs per protected resource
- Bot Control, CAPTCHA, large-body inspection, and WCUs beyond 1,500 are billed separately

**Default recommendation**: Start with AWS Managed Rules + the included Layer 7 Anti-DDoS Amazon Managed Rule group. Add custom rate-based/signature rules only for app-specific patterns, while staying within the 1,500-WCU covered budget where possible.

**Source**: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html

---

## Decision 4: Per-resource manual enablement vs Firewall Manager org-wide (Shield Advanced policy)

**Ask the architect**: "Is this a multi-account AWS Organizations estate? How many accounts and resources will need coverage? How fast do new resources appear?"

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| Manual per-resource protection | Shield Advanced (console/API) | Fine-grained control; simple for a few resources | Drift risk — new resources unprotected until manually added | Small footprint; single account; few rarely-changing internet-facing resources |
| Firewall Manager Shield Advanced policy (org-wide) | AWS Firewall Manager + AWS Organizations | Auto-covers new accounts/resources on creation; central WAF rule deployment; included at no extra charge for Advanced customers | Requires AWS Organizations + a designated Firewall Manager admin account | Multi-account orgs; many or frequently-changing resources; need to ensure no gaps |

**Operational impact**: Firewall Manager scales protection automatically as new accounts and resources are created. Manual enablement does not — new resources remain unprotected until explicitly added, creating a drift risk.

**Cost**: Firewall Manager Shield Advanced policies are included at no additional charge for Shield Advanced customers. The $3,000/month subscription is billed once to the payer account and covers the entire billing family.

**Default recommendation**: Multi-account AWS Organizations estate → drive Shield/WAF via a Firewall Manager Shield Advanced policy from the designated security account. Single account with few resources → manual per-resource enablement is acceptable.

**Source**: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html
