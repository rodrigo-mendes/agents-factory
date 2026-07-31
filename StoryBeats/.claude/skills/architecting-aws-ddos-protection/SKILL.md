---
name: architecting-aws-ddos-protection
description: "Architects DDoS protection on AWS using Shield Standard, Shield Advanced, AWS WAF, and CloudFront edge services. Use when designing, reviewing, or validating the DDoS resilience posture of internet-facing AWS workloads — including business-critical applications, regulated services, and multi-account AWS Organizations estates requiring Well-Architected Security Pillar SEC05 compliance."
---

## Function

Specialist in AWS DDoS architecture for cloud architects and tech leads. Covers Shield Standard/Advanced, AWS WAF layer-7 integration, health-based detection, SRT onboarding, DDoS cost protection, and Firewall Manager org-wide governance. Targets AWS Shield 2025 (current living docs, research date 2026-07-31). Maps to Well-Architected Security Pillar SEC05 — Protecting networks (BP01–BP04).

## Version Context

**Technology**: AWS Shield (Standard & Advanced)
**Target edition**: AWS Shield 2025 (current) — living/`latest` docs; no semantic version number
**Docs base**: AWS WAF, AWS Firewall Manager, and AWS Shield Advanced Developer Guide (current)
**Research date**: 2026-07-31
**Currency threshold**: Re-verify by **2027-07-31** (living docs; pricing especially volatile)

**Current capability anchors** (reject guidance that does not use these terms):
- "Protection pack (web ACL)" — WAF web ACL attached to a Shield Advanced protected resource
- "Automatic application layer DDoS mitigation" — opt-in L7 auto-mitigation in count or block mode
- "Layer 7 Anti-DDoS Amazon Managed Rule group" — included with Shield Advanced subscription
- "Health-based detection" via Route 53 health checks — prerequisite for proactive engagement
- "Proactive engagement" — SRT human outreach when a health-checked resource becomes unhealthy

**Pricing anchors** (re-verify before contracting — from AWS Shield pricing page, 2026-07-31):
- Shield Advanced: $3,000/month, 1-year commitment; covers the full consolidated-billing family
- CloudFront DTO under Shield Advanced: $0.025/GB
- ALB / EC2 / Global Accelerator DTO under Shield Advanced: $0.050/GB
- WAF standard fees covered: up to 1,500 WCUs / default body size / 50 billion requests per protected resource
- Automatic L7 mitigation rule group: consumes 150 WCUs from the covered 1,500-WCU budget

⚠️ **CRITICAL — Agent warning**: Reject any guidance predating "automatic application layer DDoS mitigation" or "protection pack (web ACL)" terminology as potentially outdated.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — 9 mandatory patterns with verification commands
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — 4 architectural decision matrices with tradeoff tables
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — 7 anti-patterns with wrong/correct examples
- **[Reference Architecture](./blueprints/reference-architecture.md)** — Canonical DDoS-resilient AWS architecture
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — Test cases for this skill
- **[Verification Loop](#verification-loop)** — AWS CLI posture-validation commands
- **[Quick Reference](#quick-reference)** — Tier gap and cost table at a glance
- **[External Resources](#external-resources)** — Official documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

Full patterns with verification commands: [Always Do Patterns](./blueprints/always-do-patterns.md)

**Mandatory patterns** (Complex tier — security-critical, multi-layer, SEC05-aligned):

1. **Enable Shield Advanced on every internet-facing resource** — Shield "doesn't automatically protect resources." Protectable types: CloudFront distributions, Route 53 hosted zones, Global Accelerator standard accelerators, EC2 Elastic IPs, ALBs, Classic LBs. Any unprotected public resource is a DDoS perimeter gap.

2. **Subscribe to Shield Advanced before an attack** — The 1-year subscription, SRT access role, health checks, and proactive engagement contacts require pre-configuration. You cannot obtain the Advanced posture mid-attack.

3. **Attach AWS WAF to every L7 entry point** — Shield (Standard or Advanced network layer) does NOT stop HTTP/HTTPS request floods. L7 defense requires AWS WAF with managed rules + rate-based rules. Shield Advanced covers standard WAF fees up to 1,500 WCUs per protected resource.

4. **Enable health-based detection via Route 53 health checks** — Associate a Route 53 health check with each Shield Advanced protected resource (except Route 53 zones). Hard prerequisite for proactive engagement; improves detection accuracy.

5. **Pre-configure SRT access (IAM role + support plan) before any attack** — Create an IAM role with `AWSShieldDRTAccessPolicy` trusting `drt.shield.amazonaws.com`. Requires Business or Enterprise Support plan. Configure during onboarding, not during an incident.

6. **Enable SRT proactive engagement with current 24x7 contacts** — Requires health-based detection first. Provide primary and secondary contacts with time zones; keep contacts current. Shortens time-to-mitigation for large L7 attacks.

7. **Rely on DDoS cost protection: protect all resources and request credits after attacks** — Service credits offset attack-driven DTO/scaling spikes on Shield Advanced-protected resources only. File credit requests via AWS Support after an attack-driven cost spike.

8. **Centralize visibility via Firewall Manager + CloudWatch + Security Hub** — Deploy a Firewall Manager Shield Advanced policy from the org security account to auto-protect new accounts/resources and deploy WAF rules org-wide. Route findings to CloudWatch dashboards and Security Hub.

9. **Add AWS WAF rate-based rules as a layered complement to Shield** — Shield Advanced automatic L7 mitigation enforces rate limiting on known DDoS sources; supplement with custom rate-based rules tuned to your normal traffic profile. Start in count mode, then block.

### ⚠️ Ask First

Full decision matrices with tradeoff tables: [Ask First Decisions](./blueprints/ask-first-decisions.md)

**Architectural decision points** (confirm with the architect/workload owner before prescribing):

- **Shield Standard vs Shield Advanced** — Ask: "Is this workload business-critical, revenue-bearing, or SLA-bound?" If yes: Advanced. Experimental or downtime-tolerant: Standard may suffice. The gap is large (no L7, no SRT, no cost protection in Standard).

- **CloudFront + Shield vs ALB + Shield** — Ask: "Can this workload sit behind CloudFront?" CloudFront absorbs attacks at global edge (lower DTO: $0.025/GB). ALB is regional (DTO: $0.050/GB); use only where a regional entry point is architecturally required.

- **Managed WAF rules vs custom WAF rules alongside Shield** — Ask: "What is the WCU budget and traffic profile?" Start with AWS Managed Rules + the Layer 7 Anti-DDoS managed rule group; add custom rules only for app-specific patterns, staying within the covered 1,500-WCU ceiling where possible.

- **Per-resource manual enablement vs Firewall Manager org-wide** — Ask: "Single account or multi-account AWS Organizations?" Multi-account: Firewall Manager Shield policy (auto-protects new resources, no extra charge, no drift). Single account: manual per-resource enablement is acceptable.

### 🚫 Never Do

Full anti-patterns with wrong/correct examples: [Never Do Patterns](./blueprints/never-do-patterns.md)

**Prohibited patterns** (each causes service outage, compliance gap, or unbounded cost):

- **Expose EC2 instances directly to the internet without edge/ALB + WAF + Shield** — No CloudFront/ALB in front means no surface reduction and no L7 filtering. Blast radius: full application outage + uncovered cost. Risk: CRITICAL.

- **Rely on Shield Standard alone for business-critical or regulated workloads** — Standard provides no L7 protection, no SRT, no proactive engagement, no cost protection, no advanced metrics. Risk: HIGH.

- **Skip health-based detection (no Route 53 health checks on protected resources)** — Detection is slower and less accurate; proactive engagement is silently non-functional. Risk: HIGH.

- **Skip SRT pre-configuration before an attack** — No IAM role or wrong support plan means SRT cannot act during the most critical minutes of an active event. Risk: HIGH.

- **Ignore DDoS cost protection by leaving resources unprotected or not claiming credits** — Attack-driven DTO/scaling spikes on unprotected resources are fully billable with no reimbursement path. Risk: MEDIUM.

- **Use Shield without AWS WAF for HTTP/HTTPS endpoints (layer-7 gap)** — Shield's network-layer protection does not stop web request floods. Endpoints without a WAF web ACL are vulnerable to L7 DDoS despite Shield being "on." Risk: HIGH.

- **Single-region deployment with no Route 53 failover or edge front** — No edge absorption and no DNS failover path means full outage if the regional entry point is saturated. Risk: MEDIUM.

---

## Integration Patterns

Key service composition for canonical DDoS resilience. Full reference architecture: [Reference Architecture](./blueprints/reference-architecture.md).

**Canonical request path** (edge-fronted, private origin):
`Route 53 (health-checked failover)` → `CloudFront + WAF` → `ALB + WAF` → `EC2/ECS (private subnet)`

**Shield Advanced service integrations**:
- **Shield Advanced ↔ AWS WAF** — WAF web ACL is the "protection pack"; automatic L7 mitigation adds a 150-WCU rule group. Standard WAF fees covered up to 1,500 WCUs per protected resource.
- **Shield Advanced ↔ Route 53** — Health checks enable health-based detection and unlock SRT proactive engagement.
- **Shield Advanced ↔ Firewall Manager** — Shield Advanced policies auto-protect new accounts/resources org-wide; included at no extra charge for Advanced customers.
- **Shield Advanced ↔ CloudWatch** — `DDoSDetected` metric and attack volume metrics for dashboards and alarms.
- **Shield Advanced ↔ Security Hub** — Firewall Manager routes Shield findings; provides org-wide CSPM visibility.

**Common problems**:
- **WAF attached to ALB but not CloudFront** → WAF is per-resource; attach a separate web ACL to the CloudFront distribution (scope: CLOUDFRONT, region: us-east-1).
- **Proactive engagement enabled but never triggers** → Verify Route 53 health check is associated in Shield Advanced (`describe-protection` should show non-empty `HealthCheckIds`).
- **SRT cannot access WAF logs during an attack** → Verify the IAM role trusts `drt.shield.amazonaws.com` and has `AWSShieldDRTAccessPolicy` attached; verify Business/Enterprise Support is active.
- **Automatic L7 mitigation configured but not blocking** → Confirm action is set to "block" (not "count") in Shield console; 150-WCU rule group must be within the WAF WCU budget.

---

## Verification Loop

Run after any Shield posture change to validate correctness.

### 1. Subscription active

```bash
aws shield describe-subscription
# Expected: JSON with "SubscriptionState": "ACTIVE"
```

### 2. Protected resources inventory

```bash
aws shield list-protections --query 'Protections[*].{Name:Name,Resource:ResourceArn}'
# Expected: every internet-facing resource ARN present (CloudFront, Route 53, ALB, EIP)
```

### 3. Health checks associated

```bash
aws shield describe-protection --protection-id <ID> --query 'Protection.HealthCheckIds'
# Expected: non-empty array with Route 53 health check ID(s)
```

### 4. WAF web ACL attached to CloudFront

```bash
aws wafv2 list-resources-for-web-acl --web-acl-arn <arn> --resource-type CLOUDFRONT --region us-east-1
# Expected: CloudFront distribution ARN in associated resources
```

### 5. WAF web ACL attached to regional ALB

```bash
aws wafv2 list-resources-for-web-acl --web-acl-arn <arn> --resource-type APPLICATION_LOAD_BALANCER --region <region>
# Expected: ALB ARN listed
```

### 6. SRT access configured

```bash
aws shield describe-drt-access
# Expected: JSON with non-empty "RoleArn"
```

### 7. Proactive engagement enabled

```bash
aws shield describe-emergency-contact-settings
# Expected: "EmergencyContactList" with populated contacts
aws shield describe-subscription --query 'Subscription.ProactiveEngagementStatus'
# Expected: "ENABLED"
```

### 8. Firewall Manager Shield policy (multi-account)

```bash
aws fms list-policies
# Expected: at least one Shield Advanced policy entry
```

**Troubleshooting**:
- `SubscriptionState` absent → Subscribe at the payer account level; one subscription covers the consolidated-billing family
- `HealthCheckIds` empty → Associate a Route 53 health check using `aws shield associate-health-check`
- `describe-drt-access` returns empty `RoleArn` → Grant SRT access in Shield Advanced console during onboarding
- `ProactiveEngagementStatus` = `PENDING` → Health-based detection not yet set up; associate health checks first

---

## Quick Reference

**Shield Standard vs Advanced — tier gap**:

| Feature | Shield Standard | Shield Advanced |
|---------|----------------|-----------------|
| Cost | Free | $3,000/month (1-yr commitment) |
| L3/L4 protection | Automatic | Automatic + enhanced |
| L7 protection | None | AWS WAF (standard fees covered) |
| SRT access | None | Yes (requires Business/Enterprise Support) |
| Proactive engagement | None | Yes (requires health-based detection) |
| DDoS cost protection | None | Service credits (request after attack) |
| Firewall Manager policy | N/A | Included, no extra charge |
| Health-based detection | None | Yes (Route 53 health checks) |
| Advanced CloudWatch metrics | None | Yes |

**Protectable resource types** (Shield Advanced — explicit opt-in required):
CloudFront distributions, Route 53 hosted zones, Global Accelerator standard accelerators, EC2 Elastic IPs, Application Load Balancers, Classic Load Balancers.

**SRT activation checklist** (must be complete before any attack):
1. Business or Enterprise Support plan active on the account
2. IAM role with `AWSShieldDRTAccessPolicy` trusting `drt.shield.amazonaws.com`
3. Route 53 health check associated with each protected resource
4. Proactive engagement enabled with current 24x7 contact details

---

## Blueprints Directory Structure

```
.claude/skills/architecting-aws-ddos-protection/
├── SKILL.md                              <- This file (summaries + guardrails)
└── blueprints/
    ├── always-do-patterns.md             <- 9 mandatory patterns with full verification commands
    ├── ask-first-decisions.md            <- 4 decision matrices with complete tradeoff tables
    ├── never-do-patterns.md              <- 7 anti-patterns with wrong/correct examples
    ├── reference-architecture.md         <- Canonical DDoS-resilient AWS architecture
    └── evaluation-scenarios.md           <- Test cases for skill evaluation
```

---

## External Resources

### Official AWS Documentation (all accessed 2026-07-31 — living/`latest` docs)
- [AWS Shield chapter — AWS WAF Dev Guide](https://docs.aws.amazon.com/waf/latest/developerguide/shield-chapter.html)
- [How AWS Shield and Shield Advanced work](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-overview.html)
- [Shield Advanced capabilities and options](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html)
- [Protected resource types](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-protected-resources.html)
- [AWS DDoS Resiliency Best Practices — edge services](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-edge-services.html)
- [Responding to DDoS events in AWS](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-responding.html)
- [Authorizing the SRT](https://docs.aws.amazon.com/waf/latest/developerguide/authorize-srt.html)

### Well-Architected Framework
- [Protecting networks — SEC05 (BP01–BP04)](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-networks.html) — Accessed 2026-07-31

### Pricing (re-verify before contracting)
- [AWS Shield Pricing](https://aws.amazon.com/shield/pricing/) — $3,000/month Shield Advanced; DTO rates by resource type
- [AWS WAF Pricing](https://aws.amazon.com/waf/pricing/) — WCU rates; Bot Control / CAPTCHA extras not covered by Shield subscription
