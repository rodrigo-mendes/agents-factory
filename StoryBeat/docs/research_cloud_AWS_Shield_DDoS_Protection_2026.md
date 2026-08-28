# AWS Shield — Security Architecture: DDoS Protection (AWS Shield 2026)

## Metadata
```yaml
Full_Name: "AWS Security Architecture — DDoS Protection (AWS Shield)"
Cloud_Provider: "AWS"
Architecture_Domain: "Security Architecture - DDoS Protection Shield"
Target_Edition: "AWS Shield 2026"
Architecture_Context: "Internet-facing production workloads (general); ARCHITECTURE_CONTEXT not supplied by caller — patterns are written provider-canonical, not tenant-specific"
Official_Source_URL: "https://docs.aws.amazon.com/waf/latest/developerguide/ddos-overview.html"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-08-26"
Currency_Threshold: "2027-08-26"
Research_Depth: "exhaustive"
Max_Iterations: 5
```

> **⚠️ Scope note:** `ARCHITECTURE_CONTEXT` was not provided in the arguments. This research is written to be provider-canonical (valid for any internet-facing production workload on AWS). Before applying compliance-specific (SOC2/HIPAA/PCI-DSS) or cost-committed guidance, re-scope with the architect (see Ask-First section).

---

## Executive Summary

**AWS Shield 2026** is AWS's managed Distributed Denial of Service (DDoS) protection family, spanning three distinct offerings that architects must not conflate: (1) **AWS Shield Standard** — always-on, no-cost protection against the most common network- and transport-layer (L3/L4) attacks, enabled automatically for all AWS customers; (2) **AWS Shield Advanced** — a paid subscription ($3,000/month, 1-year commitment) adding L7 (application-layer) mitigation, cost protection, 24/7 Shield Response Team (SRT) access, enhanced visibility, and centralized management via AWS Firewall Manager; and (3) **AWS Shield network security director** — a newer capability (preview, announced June 2025) that analyzes network posture, maps topology, and recommends remediation across accounts, integrated with Amazon Q Developer. All three protect against L3/L4 and L7 attack classes as described in the official overview. [Source: [How AWS Shield and Shield Advanced work](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-overview.html), accessed 2026-08-26]

**What changed in the 2026 edition** is dominated by one architectural shift: the **AWS WAF Anti-DDoS Managed Rule Group** (`AWSManagedRulesAntiDDoSRuleSet`, GA June 2025) is replacing the legacy Shield Advanced **Layer 7 Automatic Mitigation (L7AM)** as the application-layer defense. As of **March 26, 2026** the Anti-DDoS AMR is the default solution for HTTP request flood protection. Shield Advanced then automatically deploys it in **Count mode** to eligible web ACLs starting **July 27, 2026** (free evaluation through **September 30, 2026**), auto-upgrades eligible web ACLs beginning **October 1, 2026**, and **retires legacy L7AM on January 1, 2027**. The new rule group detects and mitigates within seconds (vs. minutes), adds a **Challenge** action (silent browser verification) alongside Block/Count, offers Low/Medium/High sensitivity, and consumes **50 WCUs** instead of the legacy **150 WCUs**. [Source: [AWS Shield Advanced is embracing the AWS WAF Anti-DDoS managed rule group](https://aws.amazon.com/blogs/security/aws-shield-advanced-is-embracing-the-aws-waf-anti-ddos-managed-rule-group-what-changes-and-how-to-prepare/), accessed 2026-08-26] `[✓✓ Triangulated | Security Blog + AWS re:Post DDoS Resilience article]`

**The three most critical architecture guardrails** for internet-facing production workloads are: (1) **terminate traffic at edge/regional services Shield protects** — front applications with CloudFront, Global Accelerator, ALB, or Route 53 rather than exposing raw EC2/EIP origins; (2) **pair Shield Advanced with AWS WAF web ACLs** — L7 mitigation is delivered *through* AWS WAF, so a protected resource without an associated web ACL has no application-layer defense; and (3) **enable Route 53 health-based detection** — it is a prerequisite for SRT proactive engagement and reduces false positives. All Shield Advanced protections are **opt-in per resource** (or via Firewall Manager policy) — Shield Advanced never auto-protects resources. [Source: [List of AWS resources that AWS Shield Advanced protects](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-protected-resources.html), accessed 2026-08-26]

---

## Cloud Architecture Glossary

```
Term: AWS Shield Standard
Definition: Always-on, no-additional-cost DDoS protection against common L3/L4 attack vectors, provided automatically to all AWS customers.
Provider Docs Section: ddos-overview / ddos-standard-summary
Architect Usage: Assume as baseline for every AWS resource; do not design as if unprotected at L3/L4, but do not rely on it for L7 or attack visibility/reporting.
Common Confusion: Frequently confused with Shield Advanced — Standard has NO SRT access, NO cost protection, NO L7 automatic mitigation, and NO attack diagnostics.
```
```
Term: AWS Shield Advanced
Definition: Paid subscription adding L7 automatic mitigation, cost protection credits, SRT access, enhanced visibility, protection groups, and Firewall Manager integration.
Provider Docs Section: ddos-advanced-summary-capabilities
Architect Usage: Subscribe when availability of internet-facing apps is business-critical, or when cost-spike protection / SRT support is required.
Common Confusion: Confused with AWS WAF — WAF is the delivery mechanism for L7 protection; Shield Advanced orchestrates and funds it, but is not a substitute for authoring WAF rules.
```
```
Term: AWS Shield network security director
Definition: Capability that discovers network/compute/security resources, evaluates configuration against AWS best practices and threat patterns, visualizes topology, and recommends remediation.
Provider Docs Section: aws.amazon.com/shield (Network Posture Analysis)
Architect Usage: Use for continuous network posture assessment and misconfiguration detection; multi-account via delegated administrator (Dec 2025).
Common Confusion: Not a DDoS mitigation engine — it is a posture/advisory tool. It is NOT included in a Shield Advanced subscription and is billed/available separately (preview).
```
```
Term: AWS WAF Anti-DDoS Managed Rule Group (AWSManagedRulesAntiDDoSRuleSet)
Definition: AWS Managed Rule group (GA June 2025) that auto-detects and mitigates L7 HTTP flood DDoS within seconds; supports Block/Count/Challenge actions and Low/Medium/High sensitivity; consumes 50 WCUs.
Provider Docs Section: aws-managed-rule-groups-anti-ddos
Architect Usage: Adopt as the go-forward L7 DDoS defense; enable Challenge for browser-based clients. Default HTTP-flood solution as of 2026-03-26.
Common Confusion: Confused with the legacy Shield Advanced L7 Automatic Mitigation (L7AM) it replaces — L7AM is retired 2027-01-01.
```
```
Term: Layer 7 Automatic Mitigation (L7AM)
Definition: Legacy Shield Advanced feature that added/managed custom AWS WAF rules automatically in response to detected L7 attacks; required baseline periods measured in hours and consumed 150 WCUs.
Provider Docs Section: ddos-automatic-app-layer-response
Architect Usage: Do not build new designs on L7AM — migrate to the Anti-DDoS AMR before 2027-01-01 retirement.
Common Confusion: Conflated with the new Anti-DDoS AMR; they differ in speed (minutes vs seconds), actions (no Challenge in L7AM), and WCU cost (150 vs 50).
```
```
Term: Shield Response Team (SRT)
Definition: AWS team available 24/7 to Shield Advanced subscribers for assistance during DDoS attacks and to build/manage custom mitigations.
Provider Docs Section: ddos-srt-support
Architect Usage: Requires Business or Enterprise Support plan in addition to Shield Advanced. Grant SRT access proactively — do not wait until an active attack.
Common Confusion: Assumed available with Shield Standard or without a Business/Enterprise Support plan — it is not.
```
```
Term: Proactive engagement
Definition: SRT contacts you directly when a Route 53 health check associated with a protected resource becomes unhealthy during a Shield-detected event.
Provider Docs Section: ddos-srt-proactive-engagement
Architect Usage: Enable for tier-1 endpoints; requires health-based detection to be configured first.
Common Confusion: Confused with plain SRT support — proactive engagement is only available for resources with health-based detection enabled.
```
```
Term: Health-based detection
Definition: Use of Amazon Route 53 health checks to inform Shield Advanced event detection/mitigation; reduces false positives and speeds detection when a resource is unhealthy.
Provider Docs Section: ddos-advanced-health-checks
Architect Usage: Enable for all protected resource types EXCEPT Route 53 hosted zones (unsupported there). Prerequisite for proactive engagement.
Common Confusion: Believed optional for proactive engagement — it is a hard prerequisite.
```
```
Term: Protection group
Definition: Logical grouping of Shield Advanced protected resources for enhanced detection/mitigation of the group as a whole, with membership criteria for auto-inclusion of new resources.
Provider Docs Section: ddos-protection-groups
Architect Usage: Group resources that serve one application so correlated multi-resource attacks are detected holistically; a resource may belong to multiple groups.
Common Confusion: Confused with Firewall Manager policies — protection groups are a detection construct, not a deployment/governance construct.
```
```
Term: Cost protection (service credits)
Definition: Shield Advanced credits offsetting AWS bill spikes (e.g., data transfer out) caused by a DDoS attack against protected resources.
Provider Docs Section: ddos-request-service-credit
Architect Usage: Factor into DR/cost planning; credits are requested after an attack, not automatic — file a request.
Common Confusion: Assumed to be automatic reimbursement — it must be requested and applies to protected resources only.
```
```
Term: Web ACL Capacity Unit (WCU)
Definition: AWS WAF's unit for measuring the compute cost of rules in a web ACL. Shield Advanced covers standard WAF costs up to 1,500 WCUs per protected web ACL.
Provider Docs Section: aws-waf-capacity-units
Architect Usage: Budget WCUs — Anti-DDoS AMR uses 50 WCUs (vs legacy 150); exceeding 1,500 WCUs incurs non-standard WAF cost not covered by Shield Advanced.
Common Confusion: Confused with request pricing — WCUs measure rule complexity, not request volume.
```
```
Term: AWS Firewall Manager (Shield Advanced policy)
Definition: Central governance service that auto-applies Shield Advanced protections and deploys WAF rules across accounts in an AWS Organization.
Provider Docs Section: shield-policies / fms-chapter
Architect Usage: Use to enforce Shield Advanced coverage on new accounts/resources org-wide; Shield Advanced protection policies are included at no extra charge for subscribers.
Common Confusion: Confused with Shield itself — Firewall Manager is the org-wide deployment plane, not the mitigation engine.
```

---

## Architecture Guardrails

### ✅ Mandatory Patterns

**Front internet-facing workloads with Shield-protectable edge/regional services**
- Pillar Alignment: Security; Reliability (AWS Well-Architected)
- Why: Shield Advanced only protects a fixed set of resource types. Placing CloudFront / Global Accelerator / ALB in front of origins moves the attack surface to services with the deepest, always-on mitigation capacity and continuous inspection (CloudFront and Route 53 receive continuous-inspection mitigation logic).
- AWS Services: Amazon CloudFront, AWS Global Accelerator (standard accelerators), Application Load Balancer, Amazon Route 53, Amazon EC2 Elastic IP.
- Architecture Decision: Terminate public traffic at CloudFront or Global Accelerator; keep EC2/origin private. Protectable types: CloudFront distributions (incl. staging distributions in continuous deployment), Route 53 hosted zones, Global Accelerator standard accelerators, EC2 Elastic IPs (and associated EC2 instances / NLBs), Application Load Balancers, Classic Load Balancers.
- Verification: `aws shield list-protections` — confirm each internet-facing resource ARN is present. Console: Shield → Protected resources.
- Source: [List of AWS resources that AWS Shield Advanced protects](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-protected-resources.html), accessed 2026-08-26. `[✓✓ Triangulated | Protected-resources doc + ddos-event-mitigation logic pages]`

**Associate an AWS WAF web ACL with every Shield Advanced L7 resource and enable the Anti-DDoS AMR**
- Pillar Alignment: Security
- Why: Shield Advanced application-layer protection is delivered *through* AWS WAF web ACLs, rules, and rule groups. A protected CloudFront/ALB with no web ACL has no L7 defense. As of 2026-03-26 the Anti-DDoS AMR is the default HTTP-flood solution.
- AWS Services: AWS WAF (web ACL + `AWSManagedRulesAntiDDoSRuleSet`), AWS Shield Advanced.
- Architecture Decision: Attach a web ACL to each L7 resource; add the Anti-DDoS AMR (50 WCUs). Shield Advanced covers standard WAF costs up to 1,500 WCUs and up to 50 billion requests/month to protected resources. Choose Block or Challenge action and Low/Medium/High sensitivity.
- Verification: `aws wafv2 get-web-acl` and confirm the rule group `AWSManagedRulesAntiDDoSRuleSet` is present; check the AWS WAF Anti-DDoS dashboard during the evaluation window.
- Source: [AWS Shield Advanced capabilities and options](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html) + [Anti-DDoS AMR migration blog](https://aws.amazon.com/blogs/security/aws-shield-advanced-is-embracing-the-aws-waf-anti-ddos-managed-rule-group-what-changes-and-how-to-prepare/), accessed 2026-08-26. `[✓✓ Triangulated | Capabilities doc + Security Blog]`

**Enable Route 53 health-based detection and SRT proactive engagement for tier-1 endpoints**
- Pillar Alignment: Reliability; Operational Excellence
- Why: Health checks reduce false positives, speed detection when a resource is unhealthy, and are a hard prerequisite for SRT proactive engagement (the SRT calls you when your health check goes unhealthy during a detected event).
- AWS Services: Amazon Route 53 health checks, AWS Shield Advanced, Shield Response Team.
- Architecture Decision: Associate a health check with each protected resource (all types except Route 53 hosted zones); enable proactive engagement and provide contacts. Requires Business or Enterprise Support for SRT.
- Verification: Shield console → protected resource → Health check associated = yes; Proactive engagement = Enabled. `aws shield describe-emergency-contact-settings`.
- Source: [Shield Advanced capabilities and options — Health-based detection / Proactive engagement](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html), accessed 2026-08-26.

**Centralize Shield Advanced coverage and WAF rules via AWS Firewall Manager across the Organization**
- Pillar Alignment: Operational Excellence; Security
- Why: Manual per-resource enrollment drifts; Firewall Manager auto-applies Shield Advanced protections to new accounts/resources and deploys WAF rules org-wide. Shield Advanced protection policies carry no extra Firewall Manager charge for subscribers.
- AWS Services: AWS Firewall Manager, AWS Organizations, AWS Shield Advanced, AWS Security Hub CSPM / Amazon SNS (monitoring).
- Architecture Decision: Designate a Firewall Manager admin account; create a Shield Advanced policy scoped to the OU; route findings to SNS/Security Hub.
- Verification: `aws fms list-policies`; confirm a Shield Advanced policy exists and its compliance status shows resources in-scope as compliant.
- Source: [Shield Advanced capabilities — Centralized management by AWS Firewall Manager](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html), accessed 2026-08-26.

**Run continuous network posture analysis with Shield network security director (multi-account)**
- Pillar Alignment: Security; Operational Excellence
- Why: Discovers compute/networking/security resources across accounts+regions, evaluates against AWS best practices and known threat patterns, and returns prioritized findings with remediation — closing the gap between "protected" and "correctly configured."
- AWS Services: AWS Shield network security director, AWS Organizations (delegated administrator), Amazon Q Developer.
- Architecture Decision: From a delegated administrator account, start continuous network analysis for OUs; review topology, findings, and remediation centrally; query via Amazon Q Developer. (Preview; availability includes Ireland, Frankfurt, Hong Kong, Singapore, Sydney among added regions as of Dec 2025.)
- Verification: Shield console → Network security director → confirm accounts enrolled and findings populated.
- Source: [AWS Shield network security director multi-account analysis (What's New, 2025-12-12)](https://aws.amazon.com/about-aws/whats-new/2025/12/aws-shield-network-security-director-multi-account-analysis) + [AWS Shield product page](https://aws.amazon.com/shield/), accessed 2026-08-26. `[✓✓ Triangulated | What's-New announcement + product page]`
  > ⚠️ network security director is in **preview** and is **not included** in a Shield Advanced subscription. Confirm GA status and pricing before production dependence.

### ⚠️ Architectural Decisions

**Shield Standard vs Shield Advanced**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Shield Standard | AWS Shield Standard (free) | Cost (zero), zero-touch | No L7 auto-mitigation, no SRT, no cost protection, no attack diagnostics | Non-critical / internal / low-exposure workloads |
  | Shield Advanced | AWS Shield Advanced ($3,000/mo, 1-yr) | L7 mitigation, cost protection credits, SRT, visibility, Firewall Manager | $36k+/yr floor; requires Business/Enterprise Support for SRT | Business-critical internet-facing apps; regulated/high-value targets |

- Cost Profile: Advanced = fixed $3,000/month per payer account (billed where the payer or any linked account subscribes) + data-transfer-out fees ($0.025/GB CloudFront; $0.050/GB ELB, EC2, Global Accelerator). Standard = $0.
- Lock-in Assessment: Both are AWS-native and non-portable; Advanced adds contractual 1-year commitment with automatic annual renewal.
- Architect Instruction: "Ask whether the workload's availability is revenue/mission-critical and whether cost-spike protection or SRT support is required, when deciding to subscribe to Shield Advanced."
- Source: [AWS Shield Pricing](https://aws.amazon.com/shield/pricing/), accessed 2026-08-26.

**Anti-DDoS AMR action: Block vs Challenge vs Count**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Count | Anti-DDoS AMR | Zero user impact; observability | No active mitigation | Evaluation window (through 2026-09-30) / tuning |
  | Challenge | Anti-DDoS AMR | Blocks bots via silent browser verification; preserves legit browser users | Non-browser/API clients may fail the challenge | Browser-facing web apps |
  | Block | Anti-DDoS AMR | Hard stop on attack sources | Risk of false-positive blocking of legit clients | APIs / when Challenge is infeasible |

- Cost Profile: Rule group consumes 50 WCUs (covered up to 1,500 WCUs); no extra charge on up to 50B requests/month to protected resources.
- Lock-in Assessment: AWS-native managed rule group; toggling actions is configuration-only.
- Architect Instruction: "Ask whether protected endpoints serve browsers (favor Challenge) or programmatic/API clients (favor Block), and validate in Count mode before enforcing."
- Source: [Anti-DDoS AMR migration blog](https://aws.amazon.com/blogs/security/aws-shield-advanced-is-embracing-the-aws-waf-anti-ddos-managed-rule-group-what-changes-and-how-to-prepare/), accessed 2026-08-26.

**Migration timing off legacy L7AM**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Let auto-migration run (Oct 1, 2026) | Shield Advanced | Zero effort | Less control over cutover timing/config | Low-risk web ACLs |
  | Proactively adopt Anti-DDoS AMR now | AWS WAF + Shield Advanced | Full control, early tuning in Count mode | Requires IaC + policy changes now | Tier-1 / regulated endpoints |

- Cost Profile: Free evaluation 2026-07-27 → 2026-09-30; new rule group 50 WCUs vs legacy 150 WCUs (net WCU reduction).
- Lock-in Assessment: Legacy L7AM retires 2027-01-01 — migration is mandatory, not optional.
- Architect Instruction: "Ask whether the team can validate the Anti-DDoS AMR in Count mode before Oct 1, 2026; if tier-1, migrate proactively and update IaC to declare protection via AWS WAF rather than Shield L7AM APIs."
- Source: [Anti-DDoS AMR migration blog](https://aws.amazon.com/blogs/security/aws-shield-advanced-is-embracing-the-aws-waf-anti-ddos-managed-rule-group-what-changes-and-how-to-prepare/), accessed 2026-08-26.

### 🚫 Anti-Patterns

**Exposing raw EC2/Elastic IP origins directly to the internet**
- Risk Level: HIGH
- Why: Security/Reliability — origins without an edge/regional fronting service receive only Elastic-IP-level mitigation and no L7 defense or continuous inspection; blast radius is the origin instance itself.
- ❌ Wrong: EC2 instance with a public Elastic IP serving HTTPS directly to 0.0.0.0/0, no CloudFront/ALB, no WAF.
- ✅ Correct: CloudFront (or Global Accelerator) → ALB (Shield Advanced protected) → private EC2 in private subnets; AWS WAF web ACL with Anti-DDoS AMR attached at the edge/ALB.
- Detection: `aws shield list-protections` shows no CloudFront/ALB fronting; Security Group has 0.0.0.0/0 on 443 to an instance with a public IP.
- Impact: Service outage; L7 flood reaches origin; no cost protection on unprotected paths.
- Source: [ddos-overview](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-overview.html) + [protected resources](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-protected-resources.html), accessed 2026-08-26.

**Subscribing to Shield Advanced but leaving resources un-enrolled**
- Risk Level: HIGH
- Why: Security/Cost — Shield Advanced does NOT auto-protect; unprotected resources get no L7 mitigation and no cost protection, so you pay $3,000/month with gaps.
- ❌ Wrong: Shield Advanced subscribed; new production ALB created via a pipeline never added to Shield → unprotected.
- ✅ Correct: AWS Firewall Manager Shield Advanced policy scoped to the OU auto-enrolls every new ALB/CloudFront/EIP; compliance dashboard shows 100% coverage.
- Detection: Firewall Manager policy compliance report lists non-compliant resources; `aws shield list-protections` count < internet-facing resource count.
- Impact: Cost overrun (paying without coverage); service outage on the unprotected resource.
- Source: [Shield Advanced capabilities — Firewall Manager](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html) + [protected resources](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-protected-resources.html), accessed 2026-08-26.

**Protecting an L7 resource without an associated AWS WAF web ACL**
- Risk Level: HIGH
- Why: Security — Shield Advanced L7 protection is delivered through AWS WAF; without a web ACL there is no application-layer mitigation and the Anti-DDoS AMR cannot run.
- ❌ Wrong: CloudFront distribution added to Shield Advanced but with no web ACL attached.
- ✅ Correct: CloudFront distribution with a web ACL containing `AWSManagedRulesAntiDDoSRuleSet` (Challenge action), attached and enforcing.
- Detection: `aws wafv2 list-web-acls` shows no ACL for the distribution; Anti-DDoS dashboard has no data for the resource.
- Impact: HTTP flood reaches application; SRT has no L7 controls to tune.
- Source: [Shield Advanced capabilities and options](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html), accessed 2026-08-26.

**Depending on the retiring L7AM feature for new designs**
- Risk Level: MEDIUM
- Why: Reliability — legacy Layer 7 Automatic Mitigation is retired 2027-01-01; new architecture built on it incurs forced rework and slower (minutes vs seconds) mitigation in the interim.
- ❌ Wrong: New IaC enabling Shield Advanced L7AM via the automatic-application-layer-response Shield API as the L7 defense.
- ✅ Correct: IaC declaring an AWS WAF web ACL with the Anti-DDoS AMR (50 WCUs, Challenge/Block, sensitivity tuned) as the L7 defense.
- Detection: IaC/config references `ddos-automatic-app-layer-response` / L7AM enablement instead of the Anti-DDoS managed rule group.
- Impact: Compliance/operational rework before 2027-01-01; degraded mitigation latency.
- Source: [Anti-DDoS AMR migration blog](https://aws.amazon.com/blogs/security/aws-shield-advanced-is-embracing-the-aws-waf-anti-ddos-managed-rule-group-what-changes-and-how-to-prepare/), accessed 2026-08-26.

**Enabling proactive engagement without health-based detection**
- Risk Level: MEDIUM
- Why: Operational Excellence — proactive engagement is only available for resources with health-based detection enabled; without it the SRT cannot proactively reach you.
- ❌ Wrong: Proactive engagement "enabled" on a protected ALB with no Route 53 health check associated.
- ✅ Correct: Route 53 health check associated with the ALB, health-based detection on, proactive engagement enabled, emergency contacts set.
- Detection: Shield console shows proactive engagement enabled but no health check associated; `aws shield describe-emergency-contact-settings` empty.
- Impact: Delayed expert engagement during an attack.
- Source: [Shield Advanced capabilities — Health-based detection / Proactive engagement](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html), accessed 2026-08-26.

---

## Cloud-Native Design Patterns

**Edge-terminated defense-in-depth for L7 DDoS**
- Category: Resilience
- Problem: HTTP request floods (L7) that are valid-looking and bypass L3/L4 controls.
- Solution on AWS: CloudFront (edge termination + continuous inspection) → AWS WAF web ACL with Anti-DDoS AMR (Challenge/Block, sensitivity-tuned) → ALB (Shield Advanced protected) → private origins; Route 53 health-based detection feeding Shield event logic.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Latency | Edge absorbs/mitigates near source; seconds-scale L7 mitigation | Extra hop through CloudFront/WAF |
  | Security | L3/L4 (Standard) + L7 (AMR) + SRT | $3,000/mo + WCU/request budgeting |
  | Ops | Managed rule group auto-updates | Tuning sensitivity to avoid false positives |

- Source: [How AWS Shield and Shield Advanced work](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-overview.html) + [Anti-DDoS AMR blog](https://aws.amazon.com/blogs/security/aws-shield-advanced-is-embracing-the-aws-waf-anti-ddos-managed-rule-group-what-changes-and-how-to-prepare/), accessed 2026-08-26.

**Correlated multi-resource protection via protection groups**
- Category: Resilience
- Problem: An application spans many resources (multiple ALBs/CloudFront distributions); per-resource detection misses distributed, correlated attacks.
- Solution on AWS: Define a Shield Advanced protection group with membership criteria so new resources auto-join; Shield detects/mitigates the group as a whole.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Detection | Holistic, correlated attack detection | Requires deliberate grouping strategy |
  | Ops | Auto-inclusion of new resources | Membership criteria maintenance |

- Source: [Shield Advanced capabilities — Protection groups](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html), accessed 2026-08-26.

---

## Security Architecture

**Network & application-layer DDoS defense**
- AWS Services: Shield Standard (L3/L4 baseline), Shield Advanced (L3/L4/L7 + SRT + cost protection), AWS WAF (Anti-DDoS AMR delivery), Route 53 (health-based detection), Global Accelerator / CloudFront (edge mitigation), Firewall Manager (org enforcement), network security director (posture).
- Architecture: Standard mitigates L3/L4 automatically for all resources; Advanced layers L7 mitigation through WAF web ACLs, adds SRT/visibility/cost protection; Firewall Manager enforces coverage org-wide; network security director continuously assesses posture.
- Compliance Alignment: Supports AWS Well-Architected Security pillar (protecting network/application layers, incident response via SRT). Framework reference only — not legal/compliance certification advice; re-scope for SOC2/PCI-DSS/HIPAA before asserting control coverage.
- Source: [ddos-overview](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-overview.html) + [capabilities](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html), accessed 2026-08-26.

---

## Operational Patterns

**DDoS visibility, alerting, and response**
- RTO/RPO: N/A (availability protection, not data recovery) — target sub-minute L7 mitigation with Anti-DDoS AMR (seconds-scale detection).
- AWS Services: Shield Advanced metrics/reports (API + console), Amazon CloudWatch metrics, AWS WAF Anti-DDoS dashboard, Amazon SNS / AWS Security Hub CSPM (via Firewall Manager), Shield Response Team.
- Cost Profile: Medium — $3,000/month fixed + data-transfer-out fees; cost protection credits offset attack-driven spikes on protected resources.
- Automation: Automate — Firewall Manager enrollment, CloudWatch alarms on DDoSDetected metrics, Anti-DDoS AMR auto-mitigation. Manual decision points — action mode (Block/Challenge), sensitivity level, engaging SRT for custom mitigations, filing cost-protection credit requests.
- Source: [Shield Advanced capabilities — Enhanced visibility / Firewall Manager / Cost protection](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html), accessed 2026-08-26.

---

## Reference Architectures

**Internet-facing web application with full Shield Advanced coverage**
- Context: Business-critical, browser-facing production web app on AWS.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | DNS | Amazon Route 53 (protected hosted zone + health checks) | Resolution + health-based detection |
  | Edge | Amazon CloudFront (Shield Advanced protected) | Edge termination, continuous-inspection mitigation |
  | L7 firewall | AWS WAF web ACL + `AWSManagedRulesAntiDDoSRuleSet` | HTTP flood mitigation (Challenge), rate limiting |
  | Regional entry | Application Load Balancer (Shield Advanced protected) | Regional load balancing |
  | Compute | Private EC2 / containers (no public IP) | Application origin |
  | Governance | AWS Firewall Manager Shield Advanced policy | Org-wide auto-enrollment |
  | Posture | Shield network security director | Continuous misconfiguration detection |
  | Response | Shield Response Team + proactive engagement | 24/7 expert mitigation |

- Key Decisions: Anti-DDoS AMR action/sensitivity; which resources join protection groups; proactive engagement contacts; Firewall Manager policy scope.
- Scaling Path: Add Global Accelerator for multi-region anycast entry; expand protection groups as the app fans out; extend Firewall Manager policy to new OUs.
- Cost Baseline: High fixed floor ($3,000/mo) amortized across all protected resources under one payer account; DTO fees scale with traffic.
- Source: [protected resources](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-protected-resources.html) + [capabilities](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html), accessed 2026-08-26.

---

## Service Equivalence Map

Included as a cross-provider aid for architects evaluating DDoS defenses (feature parity is NOT implied).

| Category | AWS | Google Cloud | Azure | Oracle Cloud (OCI) |
|----------|-----|--------------|-------|--------------------|
| **DDoS Protection (baseline, free)** | AWS Shield Standard | Cloud Armor (always-on for Google front ends) | Azure DDoS Network/IP Protection (Basic tier baseline) | OCI DDoS Protection (Layer 3/4, always-on) |
| **DDoS Protection (managed, paid)** | AWS Shield Advanced | Cloud Armor Managed Protection Plus | Azure DDoS Protection (Standard) | OCI DDoS (enhanced) |
| **L7 Web App Firewall** | AWS WAF (+ Anti-DDoS AMR) | Cloud Armor security policies | Azure WAF (on Front Door / App Gateway) | OCI WAF |
| **Edge / CDN termination** | Amazon CloudFront | Cloud CDN / Media CDN | Azure Front Door | OCI CDN |
| **Global anycast entry** | AWS Global Accelerator | Global External Load Balancer | Azure Front Door / Cross-region LB | OCI Global Load Balancer |
| **Managed rule sets** | AWS Managed Rules (Anti-DDoS AMR) | Cloud Armor preconfigured WAF rules | Azure-managed WAF rule sets | OCI protection rules |

> **⚠️ Important**: Service equivalence does NOT mean feature parity. AWS Shield's SRT, cost-protection credits, protection groups, and the Anti-DDoS AMR have no exact 1:1 counterpart on other providers. Validate against `AWS Shield 2026` documentation before architectural decisions.
[Sources: AWS rows verified in this research; other-provider rows are directional mappings — verify against each provider's current docs before use.]

---

## Provider Differentiators

```
Differentiator: AWS Shield Response Team (SRT) + proactive engagement
Category: Security
Unique Value: 24/7 human expert team that builds/manages custom mitigations and proactively calls you when a health check goes unhealthy during a detected attack.
Architecture Impact: Enables a managed incident-response arm without staffing a 24/7 DDoS team; drives the health-based-detection requirement into the design.
When to Leverage: Tier-1 revenue/mission-critical internet-facing apps.
Caveat: Requires Shield Advanced + Business or Enterprise Support; proactive engagement needs health-based detection.
Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html (accessed 2026-08-26)
```
```
Differentiator: Shield Advanced cost protection (service credits)
Category: Security / Cost
Unique Value: Credits offsetting DDoS-driven bill spikes (e.g., data transfer out) on protected resources.
Architecture Impact: Removes the "attack = runaway bill" risk from cost modeling for protected paths.
When to Leverage: Elastic, traffic-priced architectures (CloudFront/ELB) where a volumetric attack could spike DTO.
Caveat: Credits are requested after an attack, not automatic; apply only to protected resources.
Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html (accessed 2026-08-26)
```
```
Differentiator: AWS Shield network security director
Category: Security / Posture
Unique Value: Cross-account discovery + best-practice/threat-pattern evaluation + topology visualization + remediation guidance, queryable via Amazon Q Developer.
Architecture Impact: Shifts DDoS/network security from point mitigation to continuous posture management across an Organization.
When to Leverage: Multi-account AWS Organizations needing centralized network security posture.
Caveat: Preview (as of 2026-08); NOT included in Shield Advanced; regional availability limited (Ireland, Frankfurt, Hong Kong, Singapore, Sydney among added regions Dec 2025).
Source: https://aws.amazon.com/about-aws/whats-new/2025/12/aws-shield-network-security-director-multi-account-analysis (accessed 2026-08-26)
```

---

## Scenario Coverage

**Standard Case**: Internet-facing production web app.
- Approach: Route 53 (health checks) → CloudFront (Shield Advanced) → WAF web ACL with Anti-DDoS AMR (Challenge) → ALB (Shield Advanced) → private origins; Firewall Manager enforces enrollment; SRT proactive engagement on.
- Key Decisions: Anti-DDoS AMR action/sensitivity, protection-group strategy, Firewall Manager scope, whether Shield Advanced's $3,000/mo floor is justified.

**Edge Case**: Non-browser/API-only endpoint under L7 flood.
- Approach: Anti-DDoS AMR **Challenge** may break programmatic clients — use **Block** with tuned sensitivity plus rate-based rules; validate in Count mode during the 2026-07-27→2026-09-30 evaluation window before enforcing.

**Anti-Pattern Case**: Team wants to keep legacy L7 Automatic Mitigation "because it works."
- Clarification: Explain that L7AM is retired 2027-01-01 and must migrate to the Anti-DDoS AMR (faster, Challenge action, 50 vs 150 WCUs). Ask whether to migrate proactively (tier-1) or let the Oct 1, 2026 auto-upgrade run.

---

## Source Bibliography

| # | Source | Type | Date accessed | Currency |
|---|--------|------|---------------|----------|
| 1 | [How AWS Shield and Shield Advanced work](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-overview.html) | Official docs | 2026-08-26 | Current |
| 2 | [AWS Shield Advanced capabilities and options](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html) | Official docs | 2026-08-26 | Current |
| 3 | [List of AWS resources that AWS Shield Advanced protects](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-protected-resources.html) | Official docs | 2026-08-26 | Current |
| 4 | [AWS Shield Advanced is embracing the AWS WAF Anti-DDoS managed rule group](https://aws.amazon.com/blogs/security/aws-shield-advanced-is-embracing-the-aws-waf-anti-ddos-managed-rule-group-what-changes-and-how-to-prepare/) | Official security blog | 2026-08-26 | Current (2026) |
| 5 | [AWS Shield product page — Network Posture Analysis & Managed DDoS Protection](https://aws.amazon.com/shield/) | Official product page | 2026-08-26 | Current |
| 6 | [AWS Shield Pricing](https://aws.amazon.com/shield/pricing/) | Official pricing | 2026-08-26 | Current |
| 7 | [AWS Shield network security director multi-account analysis (What's New)](https://aws.amazon.com/about-aws/whats-new/2025/12/aws-shield-network-security-director-multi-account-analysis) | Official What's New | 2026-08-26 | Current (2025-12) |
| 8 | [AWS Shield network security director (preview)](https://aws.amazon.com/about-aws/whats-new/2025/06/aws-shield-network-security-director-preview) | Official What's New | 2026-08-26 | Current (2025-06) |
| 9 | [Automating application layer DDoS mitigation with Shield Advanced (legacy L7AM)](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-automatic-app-layer-response.html) | Official docs | 2026-08-26 | Legacy (retires 2027-01-01) |

---

## §7 — Research Iteration Changelog

| Iteration | Item | Action | Resolution | Source added |
|-----------|------|--------|------------|--------------|
| 1 | Conflicting Anti-DDoS AMR "default" date (2026-03-26) vs auto-migration dates (Jul/Oct 2026) | Targeted WebSearch to disambiguate | Resolved: both are correct and distinct — 2026-03-26 = AMR becomes default HTTP-flood solution; 2026-07-27 Count-mode deploy; 2026-10-01 auto-upgrade; 2027-01-01 L7AM retirement | Source #4 + AWS re:Post DDoS Resilience article |

**Unverified / irresolvable items:** None. All Always-Do patterns cite official AWS documentation with access dates; ⚠️ Migration Notes tag features tied to the L7AM→Anti-DDoS AMR change; network security director items flagged as preview.

> ⚠️ **Migration Note (applies throughout):** Any pattern referencing Layer 7 Automatic Mitigation (L7AM) is affected by the 2027-01-01 retirement. Go-forward L7 defense is the AWS WAF Anti-DDoS Managed Rule Group (`AWSManagedRulesAntiDDoSRuleSet`).
