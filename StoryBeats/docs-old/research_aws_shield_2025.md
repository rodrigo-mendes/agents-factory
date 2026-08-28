---
Full_Name: "AWS Shield (Standard & Advanced) — DDoS Protection"
Cloud_Provider: "AWS"
Architecture_Domain: "Security Architecture — DDoS Protection (Network L3/L4 + Application L7)"
Target_Edition: "AWS Shield 2025 (current) — AWS WAF, Shield, and Shield Advanced Developer Guide (living/latest) + Well-Architected Security Pillar Infrastructure Protection (SEC05)"
Architecture_Context: "Production internet-facing workloads requiring DDoS mitigation, AWS WAF (layer-7) integration, and network-layer (layer 3/4) protection"
Official_Source_URL: "https://docs.aws.amazon.com/waf/latest/developerguide/shield-chapter.html"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-07-31"
Researcher: "framework-researcher (Senior Cloud Architecture Researcher)"
Currency_Threshold: "2027-07-31 (review by this date — Shield docs are living/latest; re-verify pricing and capabilities)"
---

# AWS Shield — Cloud Architecture Research Knowledge Base

> **Version Absolutism note.** AWS Shield is documented as a *living* (`latest`) service inside the
> **AWS WAF, AWS Firewall Manager, and AWS Shield Advanced Developer Guide** — there is no semantic
> version number. This research pins to `TARGET_EDITION` = **AWS Shield 2025 (current)** as published
> on the AWS docs site and the **Well-Architected Security Pillar — Protecting networks (SEC05)**
> best practices. Pricing and capability figures are from the AWS Shield pricing page and the
> developer guide. **All sources accessed 2026-07-31.** Any guidance predating the current
> "protection pack (web ACL)", "automatic application layer DDoS mitigation", and "Layer 7 Anti-DDoS
> Amazon Managed Rule group" terminology is treated as outdated and flagged where it appears.

---

## Executive Summary

- **AWS Shield is AWS's managed DDoS protection service, sold in two tiers.** **Shield Standard** is
  automatic, always-on, and **free** for every AWS customer; it defends against the most common
  network/transport layer (layer 3/4) volumetric and protocol attack vectors (e.g., UDP reflection,
  TCP SYN floods) at the AWS network edge. **Shield Advanced** is a paid managed subscription
  ($3,000/month, 1-year commitment) that adds layer-7 protection, expert response, cost protection,
  and centralized visibility.
- **The tier gap is large and matters for business-critical workloads.** Shield Advanced adds:
  AWS WAF integration with standard WAF fees covered, **automatic application layer (L7) DDoS
  mitigation**, **health-based detection** via Route 53 health checks, **protection groups**, enhanced
  real-time CloudWatch metrics, **AWS Firewall Manager** centralized policy management, the **Shield
  Response Team (SRT)**, **proactive engagement**, and **DDoS cost protection** (service credits for
  attack-driven scaling / data-transfer-out spikes).
- **Shield Advanced is opt-in per resource — it never protects resources automatically.** You must
  explicitly add each resource (or apply an AWS Firewall Manager Shield Advanced policy). Protectable
  resource types: **CloudFront distributions, Route 53 hosted zones, Global Accelerator standard
  accelerators, EC2 Elastic IP addresses (and the EC2 instances / Network Load Balancers behind
  them), Application Load Balancers, and Classic Load Balancers.**
- **Shield is a layered defense, not a standalone product.** The canonical DDoS-resilient AWS
  architecture reduces attack surface by fronting workloads with edge services (CloudFront, Route 53,
  Global Accelerator), attaching **AWS WAF** for layer-7 filtering and rate-based rules, keeping
  origins private, and enabling **Shield Advanced** on all internet-facing resources. This maps to
  Well-Architected **Security Pillar SEC05 (Protecting networks)**.
- **Two hard prerequisites are easy to miss.** (1) The **SRT requires a Business or Enterprise Support
  plan** and a pre-configured IAM role — you cannot spin this up mid-attack; (2) **proactive
  engagement requires health-based detection** (Route 53 health checks) to be enabled. Configure both
  *before* an attack, not during one.

---

## Framework Pillars

Shield is primarily a **Security** pillar concern (Infrastructure Protection), with strong ties to the
**Reliability** pillar (availability under attack) and the **Cost Optimization** pillar (DDoS cost
protection credits). The Well-Architected Security Pillar places network/DDoS defense under **SEC05 —
Protecting networks**.

```
Pillar: Security — Infrastructure Protection (SEC05: Protecting networks)
Definition: "Apply security at all layers" (Zero Trust). Network design forms the foundation of
  isolation and boundaries; designs must be backed by inspection and protection mechanisms with
  automation. Edge/serverless workloads apply the same best practices in a simplified form.
Key Design Principles (as they apply to DDoS/Shield):
  - Reduce and control the exposed attack surface (network layers + traffic flow control).
  - Add inspection-based protection at the edge and application layer (AWS Shield + AWS WAF).
  - Automate protection so mitigations scale without manual intervention.
Assessment Questions (SEC05 best-practice list):
  SEC05-BP01 Create network layers
  SEC05-BP02 Control traffic flow within your network layers
  SEC05-BP03 Implement inspection-based protection   ← AWS Shield Advanced + AWS WAF live here
  SEC05-BP04 Automate network protection             ← Firewall Manager + automatic L7 mitigation
Shield-specific mapping:
  - Shield Standard/Advanced = inspection-based protection at L3/L4 (and L7 for Advanced) → SEC05-BP03
  - AWS Firewall Manager Shield policies + automatic app-layer mitigation → SEC05-BP04
  - Edge fronting (CloudFront/Route 53/Global Accelerator) reduces surface → SEC05-BP01/BP02
Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-networks.html
        (accessed 2026-07-31)
```

---

## Cloud Architecture Glossary

```
Term: DDoS (Distributed Denial of Service)
Definition: An attack in which multiple compromised systems flood a target with traffic to prevent
  legitimate users from accessing a service or to crash the target under load.
Provider Docs Section: AWS WAF Dev Guide — How AWS Shield and Shield Advanced work
Architect Usage: The threat model Shield defends against; distinguish volumetric (bandwidth), protocol
  (state exhaustion), and application-layer (request flood) classes when designing mitigations.
Common Confusion: Confused with a simple traffic spike — DDoS is adversarial and multi-source.
```
```
Term: Layer 3 / Layer 4 (network & transport) attacks
Definition: Infrastructure-layer vectors. L3 = network volumetric (e.g., UDP reflection) saturating
  capacity; L4 = network protocol abuse (e.g., TCP SYN flood) exhausting connection state.
Provider Docs Section: AWS WAF Dev Guide — How AWS Shield and Shield Advanced work
Architect Usage: These are mitigated automatically by AWS (Standard and Advanced) at the network edge.
Common Confusion: Assuming L3/L4 protection also stops application floods — it does not; that is L7.
```
```
Term: Layer 7 (application) attacks
Definition: Vectors that flood an application with requests that are valid for the target (e.g., HTTP/
  HTTPS web request floods), denying service to legitimate users.
Provider Docs Section: AWS WAF Dev Guide — How AWS Shield and Shield Advanced work
Architect Usage: Mitigated only with Shield Advanced + AWS WAF (rate-based rules, automatic app-layer
  mitigation). Shield Standard does NOT provide L7 protection.
Common Confusion: Believing Shield alone covers HTTP floods — AWS WAF is required for layer 7.
```
```
Term: AWS Shield Standard
Definition: Always-on, automatic, no-additional-cost DDoS protection for all AWS customers against
  common L3/L4 attack vectors at the AWS network edge.
Provider Docs Section: AWS WAF Dev Guide — AWS Shield Standard overview
Architect Usage: The baseline every AWS workload already has; design for resiliency to leverage it.
Common Confusion: Assuming it must be "turned on" — it is automatic and cannot be subscribed to.
```
```
Term: AWS Shield Advanced
Definition: Paid managed subscription ($3,000/month, 1-year commitment) adding expanded DDoS
  detection/mitigation, L7 protection via AWS WAF, SRT access, cost protection, and centralized
  visibility for explicitly protected resources.
Provider Docs Section: AWS WAF Dev Guide — AWS Shield Advanced overview
Architect Usage: Enable on all internet-facing resources for business-critical/regulated workloads.
Common Confusion: Assuming it auto-protects all resources — you must add each resource explicitly.
```
```
Term: Shield Response Team (SRT)
Definition: AWS security engineers specializing in DDoS event response who can be engaged by Shield
  Advanced customers during an attack to build/manage custom AWS WAF mitigations.
Provider Docs Section: AWS WAF Dev Guide — Managed DDoS event response with SRT support
Architect Usage: Pre-authorize via an IAM role (AWSShieldDRTAccessPolicy); requires Business or
  Enterprise Support plan.
Common Confusion: Expecting SRT help on Shield Standard — SRT is Advanced-only and support-plan gated.
```
```
Term: Health-based detection
Definition: Association of Amazon Route 53 health checks with a Shield Advanced protected resource so
  detection/mitigation is informed by application health — reducing false positives and speeding
  mitigation when a resource is unhealthy.
Provider Docs Section: AWS WAF Dev Guide — Health-based detection using Route 53 health checks
Architect Usage: Enable on every protected resource except Route 53 hosted zones; it is a prerequisite
  for SRT proactive engagement.
Common Confusion: Thinking it is optional polish — it gates proactive engagement and improves accuracy.
```
```
Term: Proactive engagement
Definition: Feature where the SRT contacts you directly when a health-checked protected resource
  becomes unhealthy during a Shield Advanced-detected event.
Provider Docs Section: AWS WAF Dev Guide — Setting up proactive engagement
Architect Usage: Enable with up-to-date contact info; requires health-based detection to be enabled.
Common Confusion: Confusing it with automatic mitigation — proactive engagement is human outreach.
```
```
Term: DDoS cost protection
Definition: Shield Advanced service credits that offset AWS bill spikes caused by a DDoS attack on
  protected resources, including spikes in data-transfer-out (DTO) usage fees.
Provider Docs Section: AWS WAF Dev Guide — Requesting a credit after an attack
Architect Usage: A financial safety net; request a credit after an attack-driven cost spike.
Common Confusion: Assuming it is automatic — you request a credit; coverage is via service credits.
```
```
Term: Automatic application layer DDoS mitigation
Definition: Shield Advanced option that automatically adds/manages custom AWS WAF rules (and enforces
  rate limiting on known DDoS sources) in response to detected L7 attacks; can count or block.
Provider Docs Section: AWS WAF Dev Guide — Automating application layer DDoS mitigation
Architect Usage: Enable in "count" first to validate, then "block"; adds a 150-WCU rule group to the
  protection pack (web ACL).
Common Confusion: Assuming L7 is auto-mitigated by default — by default AWS only alarms on L7 to avoid
  blocking valid traffic; you must opt in to automatic mitigation.
```
```
Term: Protection group
Definition: A logical grouping of Shield Advanced protected resources for enhanced detection/mitigation
  of the group as a whole, with optional auto-inclusion of newly protected resources.
Provider Docs Section: AWS WAF Dev Guide — Grouping your Shield Advanced protections
Architect Usage: Group resources that form one application so cross-resource attacks are detected.
Common Confusion: Confusing it with Firewall Manager policies — groups are a detection construct.
```
```
Term: AWS Firewall Manager (Shield Advanced policy)
Definition: Centralized management service that auto-applies Shield Advanced protections to new
  accounts/resources and deploys AWS WAF rules org-wide. Shield Advanced Firewall Manager policies are
  included at no additional charge for Shield Advanced customers.
Provider Docs Section: AWS WAF Dev Guide — Using AWS Shield Advanced policies in Firewall Manager
Architect Usage: The mechanism for org-wide, consistent Shield/WAF coverage across accounts.
Common Confusion: Assuming per-resource manual enablement is the only option — Firewall Manager
  automates it across an AWS Organizations org.
```
```
Term: Protection pack (web ACL) / WCU
Definition: In current terminology the AWS WAF web ACL attached to a Shield-protected resource is a
  "protection pack"; its capacity is measured in Web ACL Capacity Units (WCUs).
Provider Docs Section: AWS WAF Dev Guide — Web ACL capacity units (WCUs)
Architect Usage: Shield Advanced covers standard WAF fees up to 1,500 WCUs; automatic L7 mitigation
  consumes 150 WCUs of that budget.
Common Confusion: Ignoring the 1,500-WCU / default-body-size / 50-billion-request coverage ceiling —
  beyond it, standard WAF/Shield pricing applies.
```

---

## Architecture Guardrails

### ✅ Mandatory Patterns (Always Do)

Each pattern maps to an official AWS Shield/WAF recommendation and/or Security Pillar SEC05 best
practice. All sources accessed 2026-07-31.

**Enable AWS Shield Advanced on all internet-facing resources**
- Why: Shield Advanced "doesn't automatically protect your resources" — protection applies only to
  resources you explicitly specify (or cover via a Firewall Manager Shield Advanced policy). Leaving
  any public resource unprotected creates a gap in the DDoS perimeter. (SEC05-BP03)
- Provider Service: AWS Shield Advanced, applied to CloudFront distributions, Route 53 hosted zones,
  Global Accelerator standard accelerators, EC2 Elastic IP addresses (and EC2 instances / Network Load
  Balancers behind them), Application Load Balancers, Classic Load Balancers.
- Architecture Decision: Inventory every internet-facing resource; add each to Shield Advanced (console/
  API) or enforce via a Firewall Manager Shield Advanced policy for auto-coverage of new resources.
- Verification: `aws shield list-protections` (each public resource has a protection); Firewall Manager
  Shield policy shows 100% compliance; console Shield "Protected resources" list.
- Trade-offs: Cost — one flat $3,000/month subscription covers the account family, but DTO fees and
  per-resource WAF beyond the covered ceiling still apply. Low latency/complexity impact.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-protected-resources.html
  (accessed 2026-07-31)

**Subscribe to Shield Advanced before an attack (proactive, not reactive)**
- Why: Shield Advanced is a subscription with a 1-year commitment and its response features (SRT
  access, proactive engagement, custom mitigations) require pre-configuration. You cannot obtain the
  Advanced posture mid-attack. Design for resiliency in advance. (SEC05-BP03/BP04)
- Provider Service: AWS Shield Advanced subscription (billed to the AWS Organizations payer account;
  one subscription covers all accounts in the consolidated billing family).
- Architecture Decision: Subscribe at the organization payer level; enroll critical accounts; enable
  SRT access and proactive engagement as part of onboarding, not incident response.
- Verification: `aws shield describe-subscription` returns an active subscription; console Overview
  shows subscription active and auto-renew.
- Trade-offs: Cost — $3,000/month even absent attacks; justified for business-critical availability SLAs.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary.html
  (accessed 2026-07-31)

**Configure AWS WAF with Shield Advanced for layer-7 protection**
- Why: Shield (Standard or Advanced network layer) does not stop application-layer floods. "Shield
  Advanced uses AWS WAF web ACLs, rules, and rule groups as part of its application layer protections."
  Your Shield Advanced subscription covers standard AWS WAF fees (up to 1,500 WCUs, default body size,
  up to 50 billion requests/month) for protected resources. (SEC05-BP03)
- Provider Service: AWS WAF (web ACL / "protection pack") attached to CloudFront and/or ALB, plus the
  Layer 7 Anti-DDoS Amazon Managed Rule group included with the subscription.
- Architecture Decision: Attach an AWS WAF web ACL to every L7 entry point (CloudFront distribution and
  regional ALB); include managed rule groups + rate-based rules; keep WCU usage within the covered
  ceiling where possible.
- Verification: `aws wafv2 get-web-acl` shows a web ACL associated with the CloudFront/ALB resource;
  Shield console shows the resource's associated web ACL.
- Trade-offs: Cost/complexity — WAF beyond 1,500 WCUs, Bot Control, CAPTCHA, or large-body inspection
  is billed separately; managed rules add evaluation but negligible latency at the edge.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html
  (accessed 2026-07-31)

**Enable health-based detection (Route 53 health checks) on protected resources**
- Why: "Using health checks with Shield Advanced helps prevent false positives and provides faster
  detection and mitigation when a protected resource is unhealthy." It is also a hard prerequisite:
  "Shield Advanced proactive engagement is available only for resources that have health-based
  detection enabled." Available for all protected resource types except Route 53 hosted zones. (SEC05-BP03)
- Provider Service: Amazon Route 53 health checks associated with Shield Advanced protected resources.
- Architecture Decision: Create a Route 53 health check per critical resource; associate it in Shield
  Advanced so detection is health-informed and proactive engagement is unlocked.
- Verification: `aws shield describe-protection` shows an associated `HealthCheckIds`; console shows a
  health check attached to the protection.
- Trade-offs: Minor Route 53 health-check cost; slight setup effort — required for accurate detection
  and proactive engagement.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html
  (accessed 2026-07-31)

**Pre-configure SRT access via an IAM role**
- Why: The SRT can only act on your behalf if you grant permissions before an event. Shield creates a
  role trusting the service principal `drt.shield.amazonaws.com` and attaches the managed policy
  `AWSShieldDRTAccessPolicy`, allowing the SRT to make Shield Advanced/AWS WAF API calls and access
  your WAF logs. SRT use also requires a Business or Enterprise Support plan. (SEC05-BP03)
- Provider Service: AWS IAM role (managed policy `AWSShieldDRTAccessPolicy`, trust principal
  `drt.shield.amazonaws.com`) + AWS Business/Enterprise Support plan.
- Architecture Decision: During onboarding, grant SRT access ("Create a new role for the SRT" or attach
  the managed policy to an existing role) and confirm the account is on Business/Enterprise Support.
- Verification: Console Shield Overview → "Configure AWS SRT support" shows SRT access granted; IAM role
  exists with `AWSShieldDRTAccessPolicy` and the `drt.shield.amazonaws.com` trust.
- Trade-offs: Requires paid support plan; grants AWS engineers scoped access to WAF logs/APIs — a
  deliberate trust decision.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/authorize-srt.html
  (accessed 2026-07-31)

**Enable SRT proactive engagement with current contacts**
- Why: With proactive engagement, "the SRT can proactively contact you… triages the DDoS event and
  creates AWS WAF mitigations… and, with your consent, can apply the AWS WAF rules." This shortens time-
  to-mitigation for large L7 attacks. Requires health-based detection. (SEC05-BP04)
- Provider Service: AWS Shield Advanced proactive engagement + Route 53 health checks + SRT.
- Architecture Decision: Provide 24x7 contact details (primary/secondary, time zones), enable proactive
  engagement, and keep contacts current.
- Verification: Console Shield Overview shows proactive engagement "Enabled" and populated contacts;
  `aws shield describe-emergency-contact-settings` returns contacts.
- Trade-offs: Requires health-based detection and up-to-date contacts; negligible cost.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-responding.html
  (accessed 2026-07-31)

**Rely on DDoS cost protection (do not disable / do request credits)**
- Why: "Shield Advanced offers some cost protection against spikes in your AWS bill that might result
  from a DDoS attack against your protected resources… including coverage for spikes in Shield Advanced
  data transfer out (DTO) usage fees," provided as Shield Advanced service credits. This protects the
  Cost Optimization pillar during attack-driven scaling.
- Provider Service: AWS Shield Advanced service credits (request after an attack).
- Architecture Decision: Treat cost protection as a claimable benefit; after an attack that drove a DTO/
  scaling cost spike on protected resources, file a credit request.
- Verification: Confirm resources are Shield Advanced-protected before the spike (`aws shield
  list-protections`); submit a credit request via AWS Support after the attack.
- Trade-offs: Coverage is via credits and applies to protected resources only — another reason to
  protect all internet-facing resources.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html
  (accessed 2026-07-31)

**Centralize visibility (Firewall Manager + CloudWatch + Security Hub)**
- Why: Shield Advanced "gives you access to advanced, real-time metrics and reports" via the Shield API/
  console and Amazon CloudWatch; Firewall Manager can centralize monitoring across accounts using an SNS
  topic or AWS Security Hub CSPM, and applies Shield/WAF protections org-wide at no additional charge.
  (SEC05-BP04)
- Provider Service: AWS Shield Advanced (CloudWatch metrics, global/event dashboard), AWS Firewall
  Manager (Shield Advanced policy), Amazon SNS, AWS Security Hub.
- Architecture Decision: Deploy a Firewall Manager Shield Advanced policy from the org security account;
  route findings to Security Hub and CloudWatch dashboards/alarms for DDoS metrics (e.g.,
  `DDoSDetected`, attack volume).
- Verification: `aws fms list-policies` shows a Shield policy; CloudWatch has Shield/DDoS metrics;
  Security Hub shows Firewall Manager findings.
- Trade-offs: Firewall Manager requires AWS Organizations + a designated admin account; Shield policies
  themselves are no-charge for Advanced customers.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html
  (accessed 2026-07-31)

**Use AWS WAF rate-based rules as a complement to Shield**
- Why: AWS DDoS resiliency best practices recommend rate-based rules to limit requests from individual
  source IPs as part of a layered defense; Shield Advanced automatic app-layer mitigation itself
  enforces AWS WAF rate limiting on known DDoS sources. (SEC05-BP03/BP04)
- Provider Service: AWS WAF rate-based rules in the web ACL attached to CloudFront/ALB.
- Architecture Decision: Add rate-based rules with thresholds tuned to your normal traffic profile;
  start in "count" to calibrate, then move to "block".
- Verification: `aws wafv2 get-web-acl` shows a `RateBasedStatement` rule; WAF sampled requests / metrics
  confirm rate-limit hits during load.
- Trade-offs: Mis-tuned thresholds can throttle legitimate spikes — calibrate with real traffic first.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-edge-services.html
  (accessed 2026-07-31)

### ⚠️ Architectural Decisions (Ask First)

**Shield Standard vs Shield Advanced (cost vs protection depth)**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Shield Standard only | AWS Shield Standard (free) | Zero cost; automatic L3/L4 | No L7 protection, no SRT, no cost protection, no health-based detection, no advanced metrics | Non-critical/experimental workloads; cost-sensitive apps that can tolerate downtime |
  | Shield Advanced | AWS Shield Advanced ($3,000/mo, 1-yr) | L7 protection, SRT, proactive engagement, cost protection, org-wide Firewall Manager, real-time metrics | Flat monthly fee + DTO fees + WAF beyond covered ceiling | Business-critical, revenue-generating, regulated, or SLA-bound internet-facing workloads |

- Cost Profile: Standard = $0. Advanced = $3,000/month (1-year commitment, auto-renew) billed to the
  AWS Organizations payer account; one subscription covers the whole consolidated-billing family. DTO
  fees still apply (see cost table). Standard WAF fees for protected resources are covered up to 1,500
  WCUs / default body size / 50 billion requests per month.
- Scaling Characteristics: Both scale at the AWS edge automatically for L3/L4; only Advanced adds
  automatic L7 scaling mitigation and cross-resource protection groups.
- Operational Burden: Standard = none. Advanced = onboarding (SRT role, health checks, WAF, Firewall
  Manager) + a support plan for SRT.
- Lock-in Assessment: AWS-native; the protection posture is portable in concept but tooling is AWS-specific.
- Ask The Architect: "Is this workload business-critical / revenue-bearing / SLA-bound? If yes,
  Shield Advanced; if it is experimental or downtime-tolerant, Standard may suffice."
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-overview.html (accessed 2026-07-31)

**CloudFront + Shield vs ALB + Shield (global edge vs regional)**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | CloudFront (edge) + Shield Advanced + WAF | Amazon CloudFront, AWS Shield Advanced, AWS WAF | Absorbs attacks at global edge; largest surface reduction; lower DTO rate ($0.025/GB) | CDN semantics; cache/behaviors config | Web/HTTP(S) apps, static+dynamic content, global users |
  | ALB (regional) + Shield Advanced + WAF | Application Load Balancer, AWS Shield Advanced, AWS WAF | Regional L7 routing; direct app integration | Attack hits regional capacity; higher DTO rate ($0.050/GB) | Regional apps, non-cacheable APIs behind a VPC |

- Cost Profile: CloudFront DTO under Shield Advanced = $0.025/GB; ELB/EC2/Global Accelerator DTO =
  $0.050/GB. Fronting with CloudFront both reduces surface and lowers DTO rate.
- Scaling Characteristics: CloudFront scales at hundreds of edge locations, absorbing volumetric load
  before it reaches the origin; an internet-facing ALB terminates attack traffic in-region.
- Operational Burden: CloudFront adds cache/behavior/origin config; ALB is simpler but less protective.
- Lock-in Assessment: Both AWS-native; CloudFront is a CDN commitment.
- Ask The Architect: "Can the workload sit behind CloudFront (cacheable or CloudFront-frontable)? Prefer
  CloudFront + WAF + Shield for maximum surface reduction; use ALB + WAF + Shield where a regional entry
  point is required, and keep the ALB's origin private."
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-edge-services.html (accessed 2026-07-31)

**Managed WAF rules vs custom WAF rules alongside Shield**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | AWS Managed Rules (+ Layer 7 Anti-DDoS managed rule group) | AWS WAF Managed Rule Groups | Fast coverage, AWS-maintained, included L7 anti-DDoS group | Less app-specific tuning | Standard web apps; baseline L7 posture |
  | Custom rules (rate-based, geo, string/regex, ACL) | AWS WAF custom rules | App-specific precision | Authoring + maintenance + WCU budget | Bespoke traffic patterns; known abuse signatures |

- Cost Profile: Standard WAF (managed + custom) covered up to 1,500 WCUs under Shield Advanced;
  automatic L7 mitigation consumes 150 WCUs; Bot Control/CAPTCHA/large-body/over-1,500-WCU are extra.
- Scaling Characteristics: Both evaluate at edge/regional scale; WCU budget is the practical ceiling.
- Operational Burden: Managed = low; custom = ongoing tuning and false-positive management.
- Lock-in Assessment: AWS WAF-specific rule syntax.
- Ask The Architect: "Start with AWS Managed Rules + the included Layer 7 Anti-DDoS group; add custom
  rate-based/signature rules only for app-specific patterns — while staying within the 1,500-WCU
  covered budget where possible."
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html
  (accessed 2026-07-31)

**Shield Advanced per-resource enablement vs consolidated account-level (Firewall Manager)**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Manual per-resource protection | AWS Shield Advanced (console/API) | Fine-grained control; simple for few resources | Drift risk; new resources unprotected until added | Small footprint, single account |
  | Firewall Manager Shield policy (org-wide) | AWS Firewall Manager + AWS Organizations | Auto-covers new accounts/resources; central WAF rule deployment; no extra charge for Shield policies | Requires Organizations + delegated admin account | Multi-account orgs; many/changing resources |

- Cost Profile: Subscription is billed once to the payer account for the whole billing family; Firewall
  Manager Shield Advanced policies are included at no additional charge for Advanced customers.
- Scaling Characteristics: Firewall Manager scales protection automatically as accounts/resources are
  created; manual enablement does not.
- Operational Burden: Firewall Manager needs org setup + a designated admin account; manual is simpler
  only at tiny scale.
- Lock-in Assessment: AWS Organizations + Firewall Manager are AWS-native governance constructs.
- Ask The Architect: "Is this a multi-account AWS Organizations estate? If yes, drive Shield/WAF via a
  Firewall Manager Shield Advanced policy from the security account so new resources are auto-protected;
  reserve manual per-resource protection for single-account footprints."
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html
  (accessed 2026-07-31)

### 🚫 Anti-Patterns (Never Do)

**Exposing EC2 instances directly to the internet without EIP + Shield + WAF**
- Why: Directly internet-exposed origins present the largest DDoS attack surface and cannot benefit from
  edge absorption or L7 filtering. AWS best practices call for reducing attack surface by fronting
  compute with edge/load-balancing services and keeping origins private. (Security / Reliability — SEC05-BP01/BP02)
- Risk Level: CRITICAL
- Blast Radius: The entire application — the exposed instance can be saturated (L3/L4) or flooded (L7),
  causing full outage.
- ❌ Wrong: An `Amazon EC2` instance with a public IP directly serving HTTP(S) to the internet, no
  `Amazon CloudFront`, no `Application Load Balancer`, no `AWS WAF`, and no Shield Advanced protection.
- ✅ Correct: `Amazon CloudFront` (+ `AWS WAF`) → `Application Load Balancer` (+ `AWS WAF`) → `Amazon EC2`
  in a private subnet; associate the public entry points and any `Elastic IP` with `AWS Shield Advanced`;
  restrict the origin security group to the CloudFront/ALB path.
- Detection: `aws ec2 describe-instances` for public IPs on app instances; AWS Config
  `ec2-instance-no-public-ip`; Security Hub; `aws shield list-protections` shows no protection.
- Impact: Service outage; attack-driven cost overrun on unprotected resources (no cost protection).
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-edge-services.html (accessed 2026-07-31)

**Relying on Shield Standard alone for business-critical / financial workloads**
- Why: Shield Standard provides no layer-7 protection, no SRT, no proactive engagement, no cost
  protection, no health-based detection, and no advanced metrics. Business-critical/regulated workloads
  need the Advanced posture. (Security / Reliability — SEC05-BP03)
- Risk Level: HIGH
- Blast Radius: Revenue/availability of the critical application during an L7 flood or sophisticated attack.
- ❌ Wrong: A payments/checkout API protected only by default `AWS Shield Standard`, with no Shield
  Advanced subscription and no AWS WAF.
- ✅ Correct: Subscribe `AWS Shield Advanced`, protect all internet-facing resources, attach `AWS WAF`
  (managed + rate-based rules), enable SRT access, health-based detection, and proactive engagement.
- Detection: `aws shield describe-subscription` (no active subscription); absence of WAF web ACL on the
  critical endpoint; no Firewall Manager Shield policy.
- Impact: Service outage / revenue loss during L7 attacks; no expert response; no cost protection.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-overview.html (accessed 2026-07-31)

**Not enabling health-based detection (missing Route 53 health checks)**
- Why: Without health checks, detection is more prone to false positives and slower when a resource is
  actually unhealthy, and — critically — proactive engagement is unavailable ("proactive engagement is
  available only for resources that have health-based detection enabled"). (Security — SEC05-BP03)
- Risk Level: HIGH
- Blast Radius: Slower/less accurate detection and no proactive SRT outreach for the affected resource.
- ❌ Wrong: A Shield Advanced-protected `Application Load Balancer` with no associated `Amazon Route 53`
  health check, and proactive engagement expected to work.
- ✅ Correct: Create a `Route 53` health check for the ALB and associate it with the Shield Advanced
  protection, then enable proactive engagement.
- Detection: `aws shield describe-protection` shows empty `HealthCheckIds`; console protection lacks a
  health check.
- Impact: Delayed mitigation; proactive engagement silently non-functional.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html
  (accessed 2026-07-31)

**Not pre-configuring SRT access before an attack**
- Why: The SRT can only act on your behalf if the `AWSShieldDRTAccessPolicy` role (trusting
  `drt.shield.amazonaws.com`) exists and a Business/Enterprise Support plan is active. Configuring this
  mid-attack wastes the most critical minutes. (Security — SEC05-BP03)
- Risk Level: HIGH
- Blast Radius: Extended outage during an active attack because the SRT cannot access WAF logs/APIs to
  build mitigations.
- ❌ Wrong: Shield Advanced subscribed but "Do not grant the SRT access to my account" selected, on a
  Developer support plan, discovered only during an active DDoS event.
- ✅ Correct: During onboarding, "Create a new role for the SRT" (or attach `AWSShieldDRTAccessPolicy`
  to an existing role trusting `drt.shield.amazonaws.com`) and ensure Business/Enterprise Support.
- Detection: Console Shield Overview shows SRT access not granted; no IAM role with
  `AWSShieldDRTAccessPolicy`; support plan is Basic/Developer.
- Impact: Service outage prolonged; no expert mitigation during the event.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/authorize-srt.html (accessed 2026-07-31)

**Ignoring DDoS cost protection (not protecting resources / not claiming credits)**
- Why: Cost protection (service credits, incl. DTO spikes) applies only to Shield Advanced *protected*
  resources. Unprotected resources hit by an attack accrue uncovered scaling/DTO costs, and credits go
  unclaimed. (Cost Optimization / Security)
- Risk Level: MEDIUM
- Blast Radius: Finance — unbounded attack-driven bill spike with no reimbursement path.
- ❌ Wrong: Internet-facing resources left outside Shield Advanced, so an attack-driven `data transfer
  out` spike is fully billable with no credit eligibility; or a credit is simply never requested.
- ✅ Correct: Protect all internet-facing resources with `AWS Shield Advanced` so DTO/scaling spikes are
  credit-eligible; after an attack-driven spike, request a Shield Advanced service credit via AWS Support.
- Detection: `aws shield list-protections` omits public resources; cost anomaly on DTO for unprotected
  resources in Cost Explorer.
- Impact: Cost overrun with no reimbursement.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html
  (accessed 2026-07-31)

**Using Shield without AWS WAF for HTTP/HTTPS endpoints (layer-7 gap)**
- Why: Shield's network-layer protection does not stop application-layer request floods. "For
  application layer (layer 7) DDoS attacks… by default it doesn't automatically apply mitigations."
  L7 defense requires AWS WAF (rate-based rules, managed rules, automatic app-layer mitigation).
  (Security — SEC05-BP03)
- Risk Level: HIGH
- Blast Radius: Any HTTP/HTTPS endpoint — vulnerable to web request floods despite Shield being "on".
- ❌ Wrong: A public `Amazon CloudFront` distribution or `Application Load Balancer` with Shield Advanced
  but no `AWS WAF` web ACL attached, assuming Shield covers HTTP floods.
- ✅ Correct: Attach an `AWS WAF` web ACL (managed rules + rate-based rules) to the CloudFront/ALB; enable
  Shield Advanced automatic application layer DDoS mitigation (start in "count", then "block").
- Detection: `aws wafv2 list-web-acls` / `get-web-acl` shows no ACL associated with the L7 resource;
  Shield console shows the resource without an associated web ACL.
- Impact: Service outage from L7 floods; no automatic mitigation.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-responding.html (accessed 2026-07-31)

**Single-region deployment with no Route 53 failover for DDoS resilience**
- Why: A single regional entry point concentrates blast radius; AWS DDoS resiliency best practices use
  global/edge services (CloudFront, Route 53, Global Accelerator) and DNS-based resilience so attacks
  are absorbed at the edge and traffic can fail over. (Reliability / Security — SEC05-BP01/BP02)
- Risk Level: MEDIUM
- Blast Radius: The whole application if the single region's entry point is saturated.
- ❌ Wrong: A single-region `Application Load Balancer` as the only public entry point, with a single
  `Route 53` A-record and no health-check-based failover, and no CloudFront/Global Accelerator front.
- ✅ Correct: Front with `Amazon CloudFront` and/or `AWS Global Accelerator`; use `Amazon Route 53`
  health-checked failover/latency records across regions; protect all entry points with Shield Advanced.
- Detection: Route 53 record set has no failover/health check; no CloudFront/Global Accelerator in the path.
- Impact: Regional outage under attack with no failover path.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-edge-services.html (accessed 2026-07-31)

---

## Service Equivalence Map

DDoS-protection equivalents across providers (for architects evaluating multi-cloud). Equivalence does
**not** imply feature parity — validate against each provider's current docs before deciding.

| Capability | AWS | Azure | GCP | OCI |
|------------|-----|-------|-----|-----|
| DDoS Standard (always-on, free) | AWS Shield Standard | Azure DDoS IP Protection / Network Protection (Basic infra always-on) | Cloud Armor Standard | OCI DDoS Protection (basic, always-on) |
| DDoS Advanced (managed subscription) | AWS Shield Advanced | Azure DDoS Network Protection | Cloud Armor Managed Protection Plus | OCI DDoS Protection (advanced) |
| WAF integration (layer 7) | AWS WAF | Azure Web Application Firewall | Cloud Armor (WAF rules) | OCI Web Application Firewall |
| CDN / edge DDoS layer | Amazon CloudFront + Shield | Azure Front Door + DDoS | Cloud CDN + Cloud Armor | OCI CDN / edge |
| Global load / DNS resilience | Route 53 + Global Accelerator | Azure Traffic Manager / Front Door | Cloud DNS + Global LB | OCI Traffic Management / Flexible LB |
| Expert response team | AWS Shield Response Team (SRT) | Azure DDoS Rapid Response (DRR) | Google Cloud Armor Enterprise support | Oracle security/support team |

> **⚠️ Important**: Service equivalence does NOT mean feature parity. Cost-protection models, response-
> team SLAs, and L7 integration differ materially between providers — always validate against current
> provider documentation before an architecture decision. Non-AWS rows are directional mappings for
> orientation, not AWS-sourced claims.

---

## Reference Architecture

**Canonical DDoS-resilient AWS architecture (edge-fronted, private origin, org-wide Shield/WAF)**
- AWS Source: AWS DDoS Resiliency Best Practices (AWS WAF Dev Guide) + Well-Architected Security Pillar
  SEC05 (Protecting networks).
- Context: Production internet-facing web/API workload requiring L3/L4 + L7 DDoS resilience, centralized
  governance, and cost protection across a multi-account AWS Organizations estate.
- Request path: `Amazon Route 53` (health-checked, failover/latency routing) → `Amazon CloudFront`
  (edge absorption, `AWS WAF` web ACL) → `Application Load Balancer` (regional, `AWS WAF` web ACL) →
  `Amazon EC2` / `Amazon ECS` tasks in **private subnets** (origin not internet-exposed; security groups
  restrict ingress to the CloudFront/ALB path).
- Services Composition:

  | Layer | Service | Purpose | Notes |
  |-------|---------|---------|-------|
  | DNS / global | Amazon Route 53 (health checks) | Resilient DNS + failover; health-based detection input | Health checks required for proactive engagement |
  | Edge | Amazon CloudFront + AWS WAF | Absorb volumetric attacks at edge; L7 filtering + rate-based rules | Lowest DTO rate ($0.025/GB) under Shield Advanced |
  | Regional entry | Application Load Balancer + AWS WAF | Regional L7 routing + filtering | Keep origin private; ALB behind CloudFront |
  | Compute | Amazon EC2 / Amazon ECS (private subnets) | Application origin | No public IPs; SG restricted to edge path |
  | DDoS protection | AWS Shield Advanced (on CloudFront, Route 53, ALB, Global Accelerator, EIPs) | L3/L4 auto-mitigation + L7 automatic mitigation | Explicitly protect every public resource |
  | Governance | AWS Firewall Manager (Shield Advanced policy) | Org-wide auto-protection + WAF rule deployment | No extra charge for Shield policies |
  | Response | Shield Response Team (SRT) + proactive engagement | Expert mitigation during attacks | Requires SRT IAM role + Business/Enterprise Support |
  | Visibility | Amazon CloudWatch + AWS Security Hub + Amazon SNS | Real-time DDoS metrics, findings, alerting | Firewall Manager routes findings to Security Hub/SNS |

- Key Decisions: Shield Standard vs Advanced; CloudFront vs ALB entry; managed vs custom WAF rules;
  per-resource vs Firewall Manager org-wide enablement (see Architectural Decisions).
- Attack-time behavior: AWS auto-mitigates L3/L4; for EC2, Shield Advanced deploys your VPC network ACLs
  to the AWS network border during an attack; L7 is alarmed by default and mitigated automatically only
  if you enable automatic application layer DDoS mitigation (or via SRT/proactive engagement).
- Scaling Path: Add OUs + a Firewall Manager Shield policy so new accounts/resources are auto-protected;
  use protection groups to detect cross-resource attacks on multi-resource applications.
- Cost Baseline: $3,000/month Shield Advanced (covers the billing family) + DTO fees (CloudFront
  $0.025/GB; ELB/EC2/Global Accelerator $0.050/GB) + WAF beyond the covered 1,500-WCU / 50-billion-
  request ceiling; DDoS cost protection credits offset attack-driven spikes on protected resources.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-edge-services.html
        https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-networks.html
        (accessed 2026-07-31)

---

## Scenario Coverage

**Standard Case**: Multi-account production estate with revenue-bearing web/API workloads.
- Approach: Shield Advanced at the org payer level; Firewall Manager Shield policy auto-protecting all
  internet-facing resources; CloudFront + ALB fronting private origins; AWS WAF (managed + rate-based
  rules) with automatic L7 mitigation; Route 53 health-based detection; SRT access + proactive
  engagement; CloudWatch + Security Hub dashboards.

**Edge Case**: Non-cacheable regional TCP/UDP service (e.g., gaming/real-time) that cannot sit behind
CloudFront.
- Approach: Front with `AWS Global Accelerator` (standard accelerator) + Shield Advanced; protect the
  `Elastic IP`/`Network Load Balancer`; enable health-based detection; note Global Accelerator/ELB DTO
  is $0.050/GB. L7 WAF applies only to HTTP(S) resources (CloudFront/ALB), so pair with app-level rate
  limiting for non-HTTP protocols.

**Anti-Pattern Case**: A team requests exposing an EC2 instance with a public IP "temporarily" for a
launch, protected only by Shield Standard.
- Clarification: Refuse direct exposure. Front with CloudFront + ALB, move the instance to a private
  subnet, attach AWS WAF, and enable Shield Advanced on the public entry points before launch.

---

## Source Bibliography

### Primary Sources (Official AWS documentation — all accessed 2026-07-31; living/`latest` docs)
- AWS WAF Dev Guide — AWS Shield (chapter) — https://docs.aws.amazon.com/waf/latest/developerguide/shield-chapter.html
- AWS WAF Dev Guide — How AWS Shield and Shield Advanced work — https://docs.aws.amazon.com/waf/latest/developerguide/ddos-overview.html
- AWS WAF Dev Guide — AWS Shield Advanced overview — https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary.html
- AWS WAF Dev Guide — List of AWS resources that Shield Advanced protects — https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-protected-resources.html
- AWS WAF Dev Guide — Shield Advanced capabilities and options — https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html
- AWS WAF Dev Guide — Responding to DDoS events in AWS — https://docs.aws.amazon.com/waf/latest/developerguide/ddos-responding.html
- AWS WAF Dev Guide — Setting up SRT support (authorize SRT) — https://docs.aws.amazon.com/waf/latest/developerguide/authorize-srt.html
- AWS WAF Dev Guide — AWS DDoS Resiliency Best Practices (edge services) — https://docs.aws.amazon.com/waf/latest/developerguide/ddos-edge-services.html
- Well-Architected Security Pillar — Protecting networks (SEC05-BP01…BP04) — https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-networks.html

### Validation / Supporting Sources
- AWS Shield Pricing — https://aws.amazon.com/shield/pricing/ (Shield Advanced $3,000/mo, 1-year commitment; DTO fees by resource type; Shield Standard free)
- AWS WAF Pricing — https://aws.amazon.com/waf/pricing/ (standard WAF fees, WCU, Bot Control/CAPTCHA extras)
- AWS Business Support — https://aws.amazon.com/premiumsupport/business-support/ (SRT prerequisite)
- AWS Enterprise Support — https://aws.amazon.com/premiumsupport/enterprise-support/ (SRT prerequisite)

> ⚠️ Currency: AWS Shield docs are living (`latest`) with no semantic version, so `TARGET_EDITION`
> pins to the current (2025) published guide and pricing page. Pricing ($3,000/month; DTO
> $0.025/GB CloudFront, $0.050/GB ELB/EC2/Global Accelerator) is from the AWS Shield pricing page and
> should be re-verified before contracting. Re-verify all pages above by **2027-07-31**. No source used
> here is a dated blog older than 12 months; all primary material is current official documentation.

---

## Agent Operation Notes (for downstream skill authoring)

- **High confidence (autonomous)**: All Mandatory Patterns and Anti-Patterns above — each maps to an
  explicit official Shield/WAF capability or SEC05 best practice with a live URL.
- **Ask-First that was NOT fully resolvable from the invocation** (surface before authoring a
  prescriptive skill):
  1. **Support plan** — SRT features assume a Business or Enterprise Support plan. Confirm the account's
     plan; on Basic/Developer, SRT-dependent patterns are unavailable.
  2. **AWS Organizations scope** — Firewall Manager org-wide enablement and consolidated Shield Advanced
     billing assume an Organizations estate. Confirm single- vs multi-account before prescribing.
  3. **Workload protocol** — L7/WAF patterns assume HTTP(S) via CloudFront/ALB. For non-HTTP (TCP/UDP)
     workloads behind Global Accelerator/NLB, WAF does not apply; adjust guidance accordingly.
  4. **Pricing exactness** — Dollar figures are from the AWS Shield pricing page (marketing/pricing
     surface, current). Treat as directional and re-verify at contracting time.
- **Not covered (out of scope for this pass)**: detailed AWS WAF rule authoring (WCU math, Bot Control,
  CAPTCHA), Global Accelerator internals, and CloudFront cache/behavior design — flag as follow-up
  research if the downstream skill needs them.
