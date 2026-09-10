---
name: protecting-workloads-ddos-shield
description: "Architects DDoS protection for internet-facing AWS workloads using AWS Shield Standard, Shield Advanced, and the AWS WAF Anti-DDoS Managed Rule Group (2026 edition). Use when designing, reviewing, or migrating DDoS defenses on AWS — including Shield Advanced enrollment, WAF web ACL pairing, L7AM retirement migration, and org-wide enforcement via Firewall Manager."
---

## Function
Specialist in DDoS protection architecture for AWS internet-facing workloads using AWS Shield (Standard + Advanced), AWS WAF Anti-DDoS Managed Rule Group, and AWS Firewall Manager.

## Version Context

**Technology**: AWS Shield (DDoS Protection)
**Target edition**: AWS Shield 2026
**Research date**: 2026-08-26
**Currency threshold**: 2027-08-26
**Support status**: Active

**Critical changes in this edition**:
- **Anti-DDoS AMR GA (2025-06)**: `AWSManagedRulesAntiDDoSRuleSet` is the go-forward L7 defense — 50 WCUs, seconds-scale mitigation, Challenge action support
- **L7AM default replaced (2026-03-26)**: Anti-DDoS AMR is now the default HTTP-flood solution
- **Auto-migration timeline**: Count-mode deployment 2026-07-27; auto-upgrade of eligible web ACLs 2026-10-01; L7AM retirement 2027-01-01
- **Network security director (preview, Dec 2025)**: Multi-account posture analysis via delegated admin; NOT included in Shield Advanced subscription

**Deprecated**:
- Legacy Layer 7 Automatic Mitigation (L7AM) — retires 2027-01-01; do not build new designs on it

⚠️ **CRITICAL — Agent Warning**:
This skill targets AWS Shield 2026. L7AM-based patterns are legacy and retire 2027-01-01.
Reject any design that enables Shield Advanced L7AM (`ddos-automatic-app-layer-response`) for new workloads.
Use `AWSManagedRulesAntiDDoSRuleSet` exclusively for L7 DDoS defense.

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — ✅ Always Do / ⚠️ Ask First / 🚫 Never Do
- **[Integration Patterns](#integration-patterns)** — Reference architectures and service composition
- **[Verification Loop](#verification-loop)** — AWS CLI validation commands
- **[Quick Reference](#quick-reference)** — Limits, costs, migration timeline
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — Test cases for this skill
- **[External Resources](#external-resources)** — Official AWS documentation

---

## Blueprints & Guardrails

### ✅ Always Do

**1. Terminate public traffic at Shield-protectable edge or regional services**
Shield Advanced only protects a fixed set of resource types. Front all internet-facing origins with CloudFront, Global Accelerator (standard accelerators), ALB, or Route 53; keep EC2/containers in private subnets with no public IP. Protectable types: CloudFront distributions, Route 53 hosted zones, Global Accelerator standard accelerators, EC2 Elastic IPs (+ associated NLBs), ALBs, Classic Load Balancers.
- Verification: `aws shield list-protections` — every internet-facing resource ARN must appear.

**2. Attach an AWS WAF web ACL with `AWSManagedRulesAntiDDoSRuleSet` to every Shield Advanced L7 resource**
Shield Advanced L7 protection is delivered *through* AWS WAF. A CloudFront distribution or ALB enrolled in Shield Advanced with no web ACL has zero application-layer defense. Add the Anti-DDoS AMR (50 WCUs). Shield Advanced covers standard WAF costs up to 1,500 WCUs and 50 billion requests/month on protected resources.
- Verification: `aws wafv2 get-web-acl --name <acl-name> --scope CLOUDFRONT --id <id>` — confirm `AWSManagedRulesAntiDDoSRuleSet` present and not overridden to Count for enforcement mode.

**3. Enable Route 53 health-based detection on every protected resource (except hosted zones)**
Health checks reduce false positives, speed detection when a resource becomes unhealthy, and are a hard prerequisite for SRT proactive engagement. Associate a Route 53 health check with each protected resource, enable proactive engagement, and set emergency contacts. Requires AWS Business or Enterprise Support for SRT access.
- Verification: Shield console → protected resource → Health check associated = yes; `aws shield describe-emergency-contact-settings` returns contacts.

**4. Enforce Shield Advanced coverage org-wide via AWS Firewall Manager**
Manual per-resource enrollment drifts; new resources created by pipelines are silently unprotected. Designate a Firewall Manager admin account, create a Shield Advanced policy scoped to the OU, and route compliance findings to SNS or Security Hub. Shield Advanced protection policies carry no extra Firewall Manager charge for subscribers.
- Verification: `aws fms list-policies` — Shield Advanced policy present; compliance status shows 0 non-compliant resources.

**5. Proactively migrate to Anti-DDoS AMR; do not depend on auto-upgrade for tier-1 endpoints**
Legacy L7AM retires 2027-01-01. Auto-upgrade runs 2026-10-01 with no control over timing or configuration. For tier-1 workloads: declare the Anti-DDoS AMR in IaC, validate in Count mode during the free evaluation window (through 2026-09-30), then switch to Challenge or Block before October.
- Verification: IaC references `AWSManagedRulesAntiDDoSRuleSet`, not `ddos-automatic-app-layer-response`.

### ⚠️ Ask First

**1. Shield Standard vs Shield Advanced**
Ask whether the workload's availability is revenue/mission-critical and whether cost-spike protection or 24/7 SRT support is required.

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| Shield Standard (free) | Zero cost, zero-touch | No L7 auto-mitigation, no SRT, no cost protection, no diagnostics | Non-critical / internal / low-exposure workloads |
| Shield Advanced ($3,000/mo, 1-yr commitment) | L7 mitigation, cost credits, SRT, visibility, Firewall Manager | $36k+/yr floor; Business/Enterprise Support for SRT | Business-critical internet-facing apps; regulated/high-value targets |

Cost profile: Advanced = $3,000/month per payer account + DTO fees ($0.025/GB CloudFront; $0.050/GB ELB/EC2/Global Accelerator).

**2. Anti-DDoS AMR action: Challenge vs Block vs Count**
Ask whether protected endpoints serve browsers or programmatic/API clients. Validate in Count mode before enforcing.

| Action | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| Count | Observability, zero user impact | No active mitigation | Evaluation / tuning phase |
| Challenge | Blocks bots via silent browser verification | Non-browser/API clients may fail | Browser-facing web apps |
| Block | Hard stop on attack sources | Risk of false-positives on legit clients | APIs / when Challenge is infeasible |

**3. L7AM migration timing for existing workloads**
Ask whether the team can validate the Anti-DDoS AMR in Count mode before 2026-10-01. Migration is mandatory (L7AM retires 2027-01-01) — the only choice is proactive vs. auto-upgraded.

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| Let auto-migration run (Oct 1, 2026) | Zero effort | Less control over cutover timing/config | Low-risk web ACLs |
| Migrate proactively now | Full control, early tuning | Requires IaC + policy changes now | Tier-1 / regulated endpoints |

**4. Shield network security director adoption**
Ask whether the organization needs continuous multi-account network posture management. This capability is in preview, NOT included in a Shield Advanced subscription, and has limited regional availability (Ireland, Frankfurt, Hong Kong, Singapore, Sydney as of Dec 2025). Confirm GA status and pricing before production dependence.

### 🚫 Never Do

| Anti-Pattern | Why | Correct Alternative |
|---|---|---|
| Expose raw EC2/Elastic IP origins directly to the internet (no CloudFront/ALB fronting) | Origins receive only Elastic-IP-level mitigation; no L7 defense; blast radius is the instance | CloudFront (or Global Accelerator) → Shield Advanced ALB → private EC2; WAF web ACL + Anti-DDoS AMR at edge/ALB |
| Subscribe to Shield Advanced but leave resources un-enrolled | Shield Advanced does NOT auto-protect; unprotected resources get no L7 mitigation and no cost protection — you pay $3,000/month with gaps | Create a Firewall Manager Shield Advanced policy scoped to the OU; verify 100% compliance coverage |
| Enroll a CloudFront/ALB in Shield Advanced without attaching a WAF web ACL | L7 protection requires a web ACL; without it HTTP floods reach the application and SRT has no L7 controls to tune | Attach a web ACL with `AWSManagedRulesAntiDDoSRuleSet` (Challenge/Block, sensitivity tuned) before enrolling |
| Build new IaC that enables L7AM (`ddos-automatic-app-layer-response`) | L7AM retires 2027-01-01; new designs built on it incur forced rework; mitigation latency is minutes vs seconds | IaC declares a WAF web ACL with `AWSManagedRulesAntiDDoSRuleSet` (50 WCUs) as the L7 defense |
| Enable SRT proactive engagement without a Route 53 health check associated | Proactive engagement is only available for resources with health-based detection enabled; the SRT cannot reach you without it | Associate a Route 53 health check, enable health-based detection, then enable proactive engagement and set emergency contacts |

---

## Integration Patterns

**Edge-terminated defense-in-depth (canonical pattern)**

```
Route 53 hosted zone (Shield Advanced)
  └─ Route 53 health checks (health-based detection)
  └─ CloudFront distribution (Shield Advanced)
        └─ WAF web ACL
              └─ AWSManagedRulesAntiDDoSRuleSet (Challenge, Medium sensitivity)
        └─ ALB (Shield Advanced) → private EC2/containers
Firewall Manager Shield Advanced policy → auto-enrolls new resources
Shield network security director → continuous posture assessment (preview)
```

Layer composition:
- L3/L4: Shield Standard (automatic, always-on) + Shield Advanced (enhanced)
- L7: Anti-DDoS AMR via WAF web ACL (seconds-scale detection; 50 WCUs)
- Governance: Firewall Manager for org-wide enrollment and compliance reporting
- Response: SRT + proactive engagement (requires Business/Enterprise Support)

**Multi-resource correlation via protection groups**
When an application spans multiple ALBs or CloudFront distributions, define a Shield Advanced protection group with auto-inclusion membership criteria. Shield detects and mitigates the group holistically, catching distributed correlated attacks that per-resource detection misses.

**Non-browser/API endpoint pattern**
Replace Challenge with Block action in Anti-DDoS AMR. Add rate-based rules alongside the AMR. Validate in Count mode during the 2026-07-27→2026-09-30 free evaluation window before enforcing.

**Common problems**:
- **Anti-DDoS AMR not appearing in WAF console**: Confirm Shield Advanced subscription is active in the same payer account; the managed rule group is only available to subscribers.
- **Proactive engagement shows enabled but SRT never calls**: Verify a Route 53 health check is associated with the protected resource (hard prerequisite) and emergency contacts are set (`aws shield describe-emergency-contact-settings`).
- **Cost-protection credit not received after an attack**: Credits are not automatic — file a request via the Shield console after the attack; applies only to protected resources.

---

## Verification Loop

Run after any Shield/WAF configuration change:

### 1. Confirm all internet-facing resources are protected
```bash
aws shield list-protections --query 'Protections[*].ResourceArn'
# Expected: ARN for every CloudFront distribution, ALB, EIP, Route 53 hosted zone
```

### 2. Confirm Anti-DDoS AMR is active on each web ACL
```bash
aws wafv2 list-web-acls --scope CLOUDFRONT --region us-east-1
# For each ACL:
aws wafv2 get-web-acl --name <acl-name> --scope CLOUDFRONT --id <id> --region us-east-1 \
  --query 'WebACL.Rules[?Name==`AWSManagedRulesAntiDDoSRuleSet`]'
# Expected: rule entry with OverrideAction NOT set to Count (for enforcement mode)
```

### 3. Confirm Firewall Manager Shield Advanced policy compliance
```bash
aws fms list-policies --query 'PolicyList[?PolicyName!=null]'
aws fms get-compliance-detail --policy-id <id> --member-account <account-id>
# Expected: 0 non-compliant resources
```

### 4. Confirm proactive engagement and health checks
```bash
aws shield describe-emergency-contact-settings
# Expected: EmergencyContactList with at least one contact

aws shield describe-subscription \
  --query 'Subscription.ProactiveEngagementStatus'
# Expected: "ENABLED"
```

### 5. Confirm no legacy L7AM IaC references
```bash
grep -r "ddos-automatic-app-layer-response\|AutomaticResponseAction\|AutomaticApplicationLayerDDoSMitigationConfig" ./infra/
# Expected: no output (all legacy L7AM references removed)
```

**Troubleshooting**:
- `ResourceNotFoundException` on `aws shield` commands → Shield Advanced not subscribed in this payer account
- Anti-DDoS AMR not available → Subscription required; rule group only accessible to Shield Advanced subscribers
- `aws fms` access denied → Must run from Firewall Manager admin account or delegated admin

---

## Quick Reference

**Protectable resource types**:
CloudFront distributions, Route 53 hosted zones, Global Accelerator standard accelerators, EC2 Elastic IPs (+ NLBs), ALBs, Classic Load Balancers

**Critical limits and costs**:

| Resource | Limit / Cost | Notes |
|---|---|---|
| Shield Advanced subscription | $3,000/month per payer account (1-yr commitment) | Covers all linked accounts |
| WAF WCU coverage | 1,500 WCUs per protected web ACL | Exceeding = non-standard WAF cost |
| Anti-DDoS AMR WCUs | 50 WCUs | vs legacy L7AM 150 WCUs |
| WAF requests covered | 50 billion requests/month on protected resources | |
| CloudFront DTO fee | $0.025/GB | On Shield Advanced protected distributions |
| ELB/EC2/GA DTO fee | $0.050/GB | On Shield Advanced protected resources |

**L7AM retirement timeline**:

| Date | Event |
|---|---|
| 2025-06 | Anti-DDoS AMR GA |
| 2026-03-26 | AMR becomes default HTTP-flood solution |
| 2026-07-27 | Shield Advanced deploys AMR in Count mode to eligible web ACLs (free evaluation starts) |
| 2026-09-30 | Free evaluation window ends |
| 2026-10-01 | Auto-upgrade of eligible web ACLs to AMR enforcement |
| 2027-01-01 | Legacy L7AM retired |

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/protecting-workloads-ddos-shield/
├── SKILL.md                              ← This file
└── blueprints/
    └── evaluation-scenarios.md           ← Test cases for skill-evaluator
```

---

## External Resources

### Official Documentation
- [How AWS Shield and Shield Advanced work](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-overview.html) — Accessed 2026-08-26
- [AWS Shield Advanced capabilities and options](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html) — Accessed 2026-08-26
- [List of AWS resources that AWS Shield Advanced protects](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-protected-resources.html) — Accessed 2026-08-26
- [AWS Shield Pricing](https://aws.amazon.com/shield/pricing/) — Accessed 2026-08-26

### Migration & New Features
- [AWS Shield Advanced embracing Anti-DDoS Managed Rule Group (Security Blog)](https://aws.amazon.com/blogs/security/aws-shield-advanced-is-embracing-the-aws-waf-anti-ddos-managed-rule-group-what-changes-and-how-to-prepare/) — 2026-08-26; covers L7AM→AMR migration timeline and steps
- [AWS Shield network security director multi-account analysis (What's New, 2025-12-12)](https://aws.amazon.com/about-aws/whats-new/2025/12/aws-shield-network-security-director-multi-account-analysis) — Accessed 2026-08-26
- [Legacy L7AM documentation (retiring 2027-01-01)](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-automatic-app-layer-response.html) — Reference only; do not build new designs on this
