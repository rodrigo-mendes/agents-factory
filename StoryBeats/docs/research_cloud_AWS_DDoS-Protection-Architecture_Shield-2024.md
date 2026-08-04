# AWS Shield — DDoS Protection Architecture Knowledge Base

---

## Metadata

```yaml
Full_Name: "AWS Security Architecture — AWS Shield (DDoS Protection)"
Cloud_Provider: "AWS"
Architecture_Domain: "Security Architecture — DDoS Protection"
Target_Edition: "AWS Shield 2024–2025"
Architecture_Context: "Internet-facing applications requiring DDoS resilience across infrastructure (L3/L4) and application (L7) layers"
Official_Source_URL: "https://docs.aws.amazon.com/waf/latest/developerguide/shield-chapter.html"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-05-28"
Currency_Threshold: "2027-05-28 — review required after this date due to Shield feature evolution and pricing changes"
```

---

## Executive Summary

AWS Shield is AWS's managed DDoS protection service that operates at two tiers: **Shield Standard** (automatic, free for all AWS customers) and **Shield Advanced** (paid subscription with enhanced detection, mitigation, response, and cost protection). Shield Standard protects all AWS resources against the most common network and transport layer (L3/L4) DDoS attacks without any configuration. Shield Advanced extends this to include tailored detection based on application traffic patterns, automatic application layer (L7) DDoS mitigation via AWS WAF integration, access to the AWS Shield Response Team (SRT), proactive engagement, DDoS cost protection credits, and enhanced visibility into attacks. The service operates at over 100 Tbps mitigation capacity across all AWS Regions and edge locations.

The 2024–2025 edition introduced the **AWS Shield network security director** (preview) — a new capability that analyzes resource configurations to visualize network topology, identify security misconfigurations, and provide actionable remediation recommendations. Shield Advanced now includes access to the **Layer 7 Anti-DDoS Amazon Managed Rule group** as part of the subscription, with up to 50 billion WAF requests per calendar month included. The subscription covers standard AWS WAF costs (web ACLs, rules, and request fees up to 1,500 WCUs) for Shield-protected resources — a significant cost bundling change. Automatic application layer DDoS mitigation was strengthened with rate-based rules that enforce limits on known DDoS sources before attacks reach detectable thresholds.

The three most critical architecture guardrails for DDoS-resilient applications are: (1) **always use CloudFront and/or Route 53 as the application perimeter** — these services benefit from continuous inline mitigation at AWS edge locations without requiring a detection signal; (2) **associate Route 53 health checks with every Shield Advanced–protected resource** — health-based detection eliminates false positives and enables proactive engagement from the SRT; (3) **enable automatic application layer DDoS mitigation for all CloudFront distributions and Application Load Balancers** — manual response is too slow for L7 floods that can impact availability within seconds.

---

## Cloud Architecture Glossary

```
Term: DDoS (Distributed Denial of Service)
Definition: An attack in which multiple compromised systems flood a target with traffic, preventing legitimate end users from accessing the target and potentially causing the target to crash due to overwhelming traffic volume.
Provider Docs Section: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-overview.html
Architect Usage: The primary threat model that Shield addresses. Understand the three classes: network volumetric (L3), network protocol (L4), and application layer (L7) attacks.
Common Confusion: DDoS is not the same as a brute-force attack or vulnerability exploitation. DDoS targets availability through volume, not through credential guessing or code exploitation.

Term: Shield Standard
Definition: Automatic DDoS protection provided to all AWS customers at no additional charge, defending against the most common, frequently occurring network and transport layer DDoS attacks.
Provider Docs Section: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-standard-summary.html
Architect Usage: Baseline protection — always active, no configuration needed. Provides comprehensive L3/L4 protection for CloudFront, Route 53, and Global Accelerator. Regional resources get border-level protection.
Common Confusion: Shield Standard does NOT provide application layer (L7) protection, health-based detection, SRT access, or DDoS cost protection. Those require Shield Advanced.

Term: Shield Advanced
Definition: A paid managed DDoS protection subscription ($3,000/month + DTO fees) providing enhanced detection, automatic L7 mitigation, SRT access, proactive engagement, protection groups, DDoS cost protection, and included AWS WAF costs for protected resources.
Provider Docs Section: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary.html
Architect Usage: Required for applications with SLAs, regulatory requirements, or where DDoS-induced cost spikes are unacceptable. One subscription covers all accounts in an AWS Organizations consolidated billing family.
Common Confusion: Shield Advanced does NOT automatically protect all resources — you must explicitly add each resource to Shield Advanced protection or use Firewall Manager policies.

Term: Shield Response Team (SRT)
Definition: A team of AWS security engineers with deep DDoS protection expertise who can assist during active DDoS events, create custom mitigations, and provide architectural guidance. Requires Business or Enterprise Support plan.
Provider Docs Section: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-srt-support.html
Architect Usage: The SRT is your escalation path during attacks. They can modify WAF rules, place network-level mitigations, and create custom protections. Available 24/7 during active attacks.
Common Confusion: SRT access requires BOTH Shield Advanced subscription AND Business/Enterprise Support plan. Having only one is insufficient.

Term: Proactive Engagement
Definition: A Shield Advanced feature where the SRT proactively contacts you when a Route 53 health check associated with your protected resource becomes unhealthy during a detected event, without waiting for you to open a support case.
Provider Docs Section: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-srt-proactive-engagement.html
Architect Usage: Reduces MTTR by eliminating the time between attack detection and expert engagement. Requires health-based detection enabled on the protected resource.
Common Confusion: Proactive engagement is not available for resources without associated Route 53 health checks. You must configure health checks first.

Term: Health-Based Detection
Definition: Shield Advanced integration with Route 53 health checks that uses application health status to inform DDoS detection thresholds and reduce false positives. When a resource is unhealthy, Shield Advanced lowers detection sensitivity.
Provider Docs Section: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-health-checks.html
Architect Usage: Always associate health checks with Shield Advanced-protected resources. This is a prerequisite for proactive engagement and significantly improves detection accuracy.
Common Confusion: Available for all protected resource types EXCEPT Route 53 hosted zones (which have inherent high availability).

Term: Automatic Application Layer DDoS Mitigation
Definition: A Shield Advanced capability that automatically responds to detected L7 DDoS attacks by enforcing WAF rate limiting on known DDoS sources and deploying custom WAF protections, without manual intervention.
Provider Docs Section: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-automatic-app-layer-response.html
Architect Usage: Enable for all CloudFront distributions and ALBs protected by Shield Advanced. Adds a Shield-managed rule group (150 WCUs) to your web ACL. Can be configured to count or block.
Common Confusion: Only works with CloudFront distributions and Application Load Balancers — NOT with EC2 instances, NLBs, or Global Accelerator directly.

Term: Protection Group
Definition: A logical grouping of Shield Advanced-protected resources that enables aggregate detection and mitigation across multiple resources in an application, improving detection of distributed attacks.
Provider Docs Section: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-protection-groups.html
Architect Usage: Group resources that serve the same application to detect attacks distributed across multiple entry points. Resources can belong to multiple protection groups.
Common Confusion: Protection groups don't replace individual resource protections — they add aggregate-level detection on top.

Term: DDoS Cost Protection
Definition: A Shield Advanced feature that provides service credits for scaling charges on protected resources (CloudFront, ELB, EC2, Route 53, Global Accelerator) that result from a DDoS attack, preventing unexpected bill spikes.
Provider Docs Section: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-request-service-credit.html
Architect Usage: Only applies to protected resources where the scaling was directly caused by a DDoS attack detected by Shield Advanced. Must file a credit request after the event.
Common Confusion: DDoS cost protection is NOT automatic — you must request a credit after the attack. It only covers the cost spike, not the baseline cost.

Term: Network Volumetric Attack (Layer 3)
Definition: Infrastructure layer attack vectors that attempt to saturate the capacity of the targeted network or resource by flooding with traffic volume (e.g., UDP reflection/amplification attacks).
Provider Docs Section: https://docs.aws.amazon.com/waf/latest/developerguide/types-of-ddos-attacks.html
Architect Usage: Shield Standard provides baseline protection. Using CloudFront, Route 53, or Global Accelerator as the edge significantly improves resilience because mitigation is inline and continuous at edge locations.
Common Confusion: Volumetric attacks target bandwidth capacity, not connection state. A TCP SYN flood is a protocol (L4) attack, not a volumetric (L3) attack, even if it generates high PPS.

Term: Network Protocol Attack (Layer 4)
Definition: Infrastructure layer attack vectors that abuse a protocol to exhaust connection state on targets (e.g., TCP SYN floods, ACK floods). Can be both stateful and volumetric simultaneously.
Provider Docs Section: https://docs.aws.amazon.com/waf/latest/developerguide/types-of-ddos-attacks.html
Architect Usage: Shield mitigates at the network border. For EC2/ELB targets, ensure instances are in private subnets behind ALB/NLB or use Elastic IPs with Shield Advanced for enhanced mitigation.
Common Confusion: Protocol attacks can be volumetric. A large TCP SYN flood intends to both saturate bandwidth AND exhaust connection state — it is classified as protocol attack, not volumetric.

Term: Application Layer Attack (Layer 7)
Definition: Attack vectors that deny service to legitimate users by flooding an application with valid-looking queries (e.g., HTTP GET/POST floods that bypass network-level defenses because they appear as legitimate requests).
Provider Docs Section: https://docs.aws.amazon.com/waf/latest/developerguide/types-of-ddos-attacks.html
Architect Usage: Requires AWS WAF + Shield Advanced automatic application layer mitigation. Rate-based rules are the first line of defense. Shield Advanced can isolate attack signatures and deploy targeted blocks.
Common Confusion: L7 attacks use valid protocols and often valid URLs — they cannot be detected by network-layer inspection alone. Requires application-aware analysis.

Term: AWS Shield Network Security Director (Preview)
Definition: A new Shield capability that performs analysis of your AWS resources to visualize network topology, identify security configuration issues, and provide actionable remediation recommendations.
Provider Docs Section: https://aws.amazon.com/shield/features/
Architect Usage: Use for continuous posture assessment of network security configurations. Currently in preview — not yet GA. Separate from Shield Standard and Shield Advanced.
Common Confusion: This is NOT a DDoS mitigation service — it is a network security posture management tool that happens to be part of the Shield product family.

Term: Mitigation Capacity
Definition: AWS Shield maintains DDoS mitigation systems at all points of ingress from the internet, providing a combined mitigation capacity of more than 100 Terabits Per Second (Tbps) across all AWS Regions and edge locations.
Provider Docs Section: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-event-mitigation.html
Architect Usage: Unlike third-party scrubbing services, Shield mitigates inline at the same location as your traffic ingress — no rerouting to external scrubbing centers, no additional latency.
Common Confusion: The 100 Tbps is the aggregate capacity across all of AWS, not per-customer or per-resource. Individual resources still need proper architecture for resilience.
```

---

## Architecture Guardrails

### ✅ Mandatory Patterns

**CloudFront + Route 53 as Application Perimeter**
- Pillar Alignment: Reliability, Security
- Why: "Applications that use Amazon CloudFront and Amazon Route 53 receive comprehensive availability protection against all known network and transport layer attacks. DDoS attacks are immediately mitigated at edge locations without requiring a signal from Shield detection." — AWS Shield documentation
- AWS Services: Amazon CloudFront, Amazon Route 53, AWS Shield Standard
- Architecture Decision:
  Place CloudFront in front of all internet-facing web applications. Use Route 53 for DNS with alias records pointing to CloudFront distributions. This architecture benefits from continuous inline inspection and mitigation at AWS edge locations — attacks are mitigated before they reach your origin.
- Verification:
  - `aws cloudfront list-distributions` — verify all public-facing apps have CloudFront distributions
  - `aws route53 list-hosted-zones` — verify DNS is managed through Route 53
  - Check that origin access is restricted to CloudFront only (Origin Access Control or VPC security groups)
- Trade-offs: Adds CloudFront cost per request, requires cache invalidation strategy, introduces slight latency for non-cacheable dynamic content (offset by edge proximity)
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-standard-summary.html

---

**AWS WAF Web ACL on All Internet-Facing Resources**
- Pillar Alignment: Security
- Why: "When you enable protection, you associate an AWS WAF web ACL with the resource, to enable web application layer detection." — Shield Advanced documentation. WAF is prerequisite for L7 DDoS detection and mitigation.
- AWS Services: AWS WAF, AWS Shield Advanced
- Architecture Decision:
  Associate an AWS WAF web ACL with every CloudFront distribution and ALB that serves internet traffic. At minimum, include rate-based rules, AWS Managed Rules (Core Rule Set, Known Bad Inputs), and the Shield Advanced automatic mitigation rule group (if subscribed). Set a baseline rate limit that reflects legitimate peak traffic plus headroom.
- Verification:
  - `aws wafv2 list-web-acls --scope REGIONAL` and `--scope CLOUDFRONT`
  - `aws wafv2 get-web-acl` — verify rate-based rules are present
  - Shield console → Protections → verify each resource has an associated web ACL
- Trade-offs: WAF request inspection adds ~1ms latency. Overly restrictive rate limits can block legitimate traffic spikes. Requires tuning per application.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html

---

**Health Check Association for Shield Advanced Resources**
- Pillar Alignment: Reliability, Operational Excellence
- Why: "Using health checks with Shield Advanced helps prevent false positives and provides faster detection and mitigation when a protected resource is unhealthy. Shield Advanced proactive engagement is available only for resources that have health-based detection enabled." — AWS documentation
- AWS Services: Amazon Route 53 (Health Checks), AWS Shield Advanced
- Architecture Decision:
  Create Route 53 health checks for every Shield Advanced-protected resource. Health checks should monitor the application endpoint (not just TCP port), use a low threshold (e.g., 3 consecutive failures), and check from multiple regions. Associate each health check with the corresponding Shield Advanced protection.
- Verification:
  - `aws shield list-protections` — list all protections
  - `aws shield describe-protection --resource-arn <arn>` — verify HealthCheckIds field is populated
  - `aws route53 list-health-checks` — verify health checks exist and are configured
- Trade-offs: Route 53 health check cost (per health check/month). Requires maintaining health check endpoints. Poorly configured health checks can cause unnecessary SRT engagement.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-health-checks.html

---

**Enable Automatic Application Layer DDoS Mitigation**
- Pillar Alignment: Security, Reliability
- Why: "With automatic mitigation, Shield Advanced enforces AWS WAF rate limiting on requests from known DDoS sources, and it automatically adds and manages custom AWS WAF protections in response to detected DDoS attacks." — Manual response is too slow for L7 attacks.
- AWS Services: AWS Shield Advanced, AWS WAF
- Architecture Decision:
  Enable automatic application layer mitigation for all Shield Advanced-protected CloudFront distributions and ALBs. Start in `Count` mode to validate detection accuracy, then switch to `Block` once confident. The Shield-managed rule group consumes 150 WCUs from your web ACL capacity.
- Verification:
  - `aws shield describe-protection --resource-arn <arn>` — verify ApplicationLayerAutomaticResponseConfiguration is enabled
  - `aws wafv2 get-web-acl` — verify ShieldMitigationRuleGroup is present in the rule list
  - CloudWatch metric `DDoSDetected` — monitor for detected events
- Trade-offs: Consumes 150 WCUs from web ACL capacity (max 5,000 default). Count mode provides visibility without blocking. Block mode may have false positives during initial deployment.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-automatic-app-layer-response.html

---

**Explicit Resource Protection in Shield Advanced**
- Pillar Alignment: Security, Operational Excellence
- Why: "Shield Advanced protections are only enabled for resources that you have explicitly specified in Shield Advanced or that you protect through an AWS Firewall Manager Shield Advanced policy. Shield Advanced doesn't automatically protect your resources." — AWS documentation
- AWS Services: AWS Shield Advanced, AWS Firewall Manager
- Architecture Decision:
  Explicitly add every internet-facing resource to Shield Advanced protection. Use Firewall Manager Shield Advanced policies to automatically protect new resources as they are created. Verify protection coverage quarterly. Resources to protect: CloudFront distributions, Route 53 hosted zones, Global Accelerator accelerators, ELB (ALB, CLB, NLB via EIP), EC2 Elastic IP addresses.
- Verification:
  - `aws shield list-protections` — compare against known internet-facing resources
  - Firewall Manager compliance dashboard — check for non-compliant resources
  - `aws shield describe-subscription` — verify subscription is active
- Trade-offs: Each protected resource incurs DTO-based Shield Advanced fees. Firewall Manager has its own per-policy per-Region fee. Over-protecting internal resources wastes money.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-protected-resources.html

---

**Multi-AZ Architecture for DDoS Resilience**
- Pillar Alignment: Reliability
- Why: DDoS attacks can saturate single-AZ capacity. Distributed architecture across multiple availability zones ensures that traffic can be absorbed and load-balanced even during volumetric attacks.
- AWS Services: Elastic Load Balancing (ALB/NLB), Amazon EC2 Auto Scaling, Amazon RDS Multi-AZ
- Architecture Decision:
  Deploy all internet-facing compute across a minimum of 2 AZs (ideally 3). Use ALB/NLB with cross-zone load balancing. Configure Auto Scaling with policies that can absorb traffic spikes (both legitimate and attack-induced). Ensure origins can scale horizontally to handle traffic that passes through edge mitigation.
- Verification:
  - `aws elbv2 describe-load-balancers` — verify subnets span multiple AZs
  - `aws autoscaling describe-auto-scaling-groups` — verify AZ distribution and scaling policies
  - Load test at 2–3x normal peak to validate scaling capacity
- Trade-offs: Multi-AZ increases infrastructure cost. Cross-AZ data transfer fees apply. Requires application-level session management (no sticky AZ).
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-resiliency.html

---

### ⚠️ Architectural Decisions

**Shield Standard vs Shield Advanced**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|------------|-----------|------------|-----------|
  | Shield Standard | AWS Shield Standard (free) | Cost — $0 | L7 detection, SRT access, proactive engagement, cost protection, visibility | Non-critical workloads, dev/staging, apps without SLAs |
  | Shield Advanced | AWS Shield Advanced ($3,000/mo + DTO) | Protection depth, visibility, response time, cost predictability | Budget — significant fixed cost | Production apps with SLAs, regulatory requirements, high-value targets |

- Cost Profile: Standard = $0. Advanced = $3,000/month flat fee (one per consolidated billing family) + $0.025–$0.050/GB DTO on protected resources. Includes AWS WAF costs for protected resources (up to 1,500 WCUs, 50B requests/month).
- Lock-in Assessment: Shield Advanced requires 1-year commitment with auto-renewal. 30-day cancellation notice window before renewal. No alternative AWS service provides SRT access or DDoS cost protection.
- Architect Instruction: "Ask 'Does this application have an availability SLA with customers, or is it a high-value target for DDoS attacks?' when evaluating whether Shield Advanced is justified."
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-deciding.html

---

**Automatic Mitigation Mode: Count vs Block**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|------------|-----------|------------|-----------|
  | Count Mode | Shield Advanced Automatic Mitigation (Count) | Visibility, safety — no false-positive impact | Response time — attacks still reach origin | Initial deployment, high false-positive risk applications, apps with sensitive availability requirements |
  | Block Mode | Shield Advanced Automatic Mitigation (Block) | Response time — immediate automated blocking | Risk of false positives blocking legitimate traffic | Established baselines, apps that can tolerate brief false positives, high-volume targets |

- Cost Profile: Same cost for both modes — the Shield Advanced rule group uses 150 WCUs regardless of action.
- Lock-in Assessment: Mode is instantly switchable via API or console. No commitment required.
- Architect Instruction: "Ask 'Has this application been in Count mode long enough to validate detection accuracy with zero false positives?' before switching to Block mode."
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-automatic-app-layer-response.html

---

**DDoS Resilient Architecture: Edge-First vs Origin-Only**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|------------|-----------|------------|-----------|
  | Edge-First (CloudFront + WAF + Shield) | CloudFront, Route 53, AWS WAF, Shield | Maximum mitigation (inline continuous), global distribution, edge caching absorbs attack volume | Complexity, CloudFront cost, cache management | Public web apps, APIs, any internet-facing service |
  | Origin-Only (ALB/NLB + Shield Advanced) | ALB/NLB, Shield Advanced, AWS WAF | Simpler architecture, lower cost for low-traffic apps | No edge mitigation, attacks reach region, slower detection for L3/L4 | Internal-facing services with limited public exposure, non-HTTP protocols |
  | Hybrid (CloudFront + ALB with direct access restricted) | CloudFront + ALB + Security Groups + Shield Advanced | Defense in depth, edge AND regional protection | Maximum complexity, dual WAF management | Mission-critical applications, regulated industries |

- Cost Profile: Edge-first adds CloudFront per-request costs but reduces origin scaling costs during attacks. Origin-only has lower baseline but higher scaling risk during attack.
- Lock-in Assessment: CloudFront is AWS-specific. Architecture patterns are portable conceptually (any CDN + WAF), but specific configuration is AWS-locked.
- Architect Instruction: "Ask 'What percentage of traffic is cacheable, and what is the acceptable latency budget for uncacheable requests?' when choosing between edge-first and origin-only."
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-event-mitigation.html

---

**Protection Scope: Individual Resources vs Protection Groups**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|------------|-----------|------------|-----------|
  | Individual Resource Protection | Shield Advanced per-resource | Granular per-resource visibility and alerting | May miss distributed attacks across resources | Single-resource applications, independent services |
  | Protection Groups | Shield Advanced Protection Groups | Aggregate detection across related resources, detects distributed attacks | Additional configuration, group-level metrics may mask per-resource details | Multi-resource applications, microservices, distributed architectures |
  | Both (recommended) | Individual + Protection Groups | Maximum detection coverage | Configuration overhead | All production applications with Shield Advanced |

- Cost Profile: No additional cost for protection groups — included in Shield Advanced subscription.
- Lock-in Assessment: No additional commitment. Groups are logical constructs that can be created/deleted at any time.
- Architect Instruction: "Ask 'Are there multiple entry points that serve the same application and could be targeted simultaneously?' when deciding on protection groups."
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-protection-groups.html

---

### 🚫 Anti-Patterns

**Exposing Origins Directly Without Edge Protection**
- Risk Level: CRITICAL
- Why: Security pillar violation. "Applications that use Amazon CloudFront and Amazon Route 53 receive comprehensive availability protection against all known network and transport layer attacks" — bypassing the edge forfeits this free, inline protection.
- Instead: Place CloudFront in front of all internet-facing web applications. Restrict origin access using Origin Access Control (OAC) for S3, or security groups that only allow CloudFront IP ranges for ALB/EC2 origins.
- Detection: `aws ec2 describe-security-groups` — check for security groups allowing 0.0.0.0/0 on port 80/443 to EC2/ALB without CloudFront restriction. `aws cloudfront list-distributions` — verify all public apps are fronted.
- Impact: Service outage — volumetric attacks hit regional resources directly without edge mitigation. L3/L4 protection at the region is reactive (requires detection signal), not inline.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-event-mitigation-logic-continuous-inspection.html

---

**Relying on Shield Advanced Without WAF Web ACL**
- Risk Level: HIGH
- Why: Security pillar violation. Shield Advanced application layer detection requires a web ACL associated with the resource. Without WAF, there is no L7 DDoS detection, no automatic mitigation, and no rate-based rule protection.
- Instead: Associate a WAF web ACL with every Shield Advanced-protected CloudFront distribution and ALB. At minimum, add rate-based rules and the AWS Managed Rules Core Rule Set.
- Detection: `aws shield list-protections` → for each resource, `aws wafv2 get-web-acl-for-resource --resource-arn <arn>` — any resource returning empty has no WAF protection.
- Impact: Service outage — L7 floods bypass Shield Advanced because there is no application-layer inspection capability without WAF.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html

---

**Shield Advanced Without Health Checks**
- Risk Level: HIGH
- Why: Reliability pillar violation. Without health checks, Shield Advanced cannot differentiate between legitimate traffic spikes and DDoS attacks, leading to false positives or missed detections. Proactive engagement is unavailable.
- Instead: Create Route 53 health checks for every Shield Advanced-protected resource (except Route 53 hosted zones). Associate health checks with Shield protections. Configure health checks to monitor application-level endpoints.
- Detection: `aws shield list-protections` — for each protection, check if `HealthCheckIds` is empty. Flag all protections with no associated health check.
- Impact: Delayed detection, false positives blocking legitimate traffic, no proactive SRT engagement during real attacks. Significantly degrades Shield Advanced value.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-health-checks.html

---

**Single-AZ Deployment for Internet-Facing Resources**
- Risk Level: HIGH
- Why: Reliability pillar violation. DDoS attacks can exhaust single-AZ capacity. Resources in a single AZ cannot absorb volumetric attacks that exceed the AZ's network capacity, even with Shield protection.
- Instead: Deploy across multiple AZs with ALB/NLB. Use Auto Scaling groups spanning 2–3 AZs. Design for horizontal scaling — Shield mitigates the attack traffic, but legitimate traffic still needs capacity.
- Detection: `aws elbv2 describe-load-balancers` — check AvailabilityZones count. `aws autoscaling describe-auto-scaling-groups` — verify multiple AZs in AvailabilityZones field.
- Impact: Service outage — single point of failure at AZ level. Shield cannot protect against outage caused by insufficient origin capacity in a single AZ.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-resiliency.html

---

**No Rate-Based Rules in WAF Configuration**
- Risk Level: HIGH
- Why: Security pillar violation. Rate-based rules are the first line of L7 defense. "A rate-based rule in your web ACL can mitigate an attack before it reaches a detectable level" — without them, attacks must grow large enough for signature detection.
- Instead: Configure rate-based rules in every WAF web ACL. Set baseline rate limits based on application peak traffic (e.g., 2–5x normal peak per IP). Use multiple rate-based rules for different paths (API endpoints, login pages).
- Detection: `aws wafv2 get-web-acl --id <id> --scope <scope>` — check rules for type `RATE_BASED`. Flag web ACLs with zero rate-based rules.
- Impact: Slow detection — attacks must grow to significant volume before Shield Advanced detects them. Origin resources may be overwhelmed before mitigation activates.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-event-detection-application.html

---

**Assuming Shield Advanced Protects All Resources Automatically**
- Risk Level: MEDIUM
- Why: Operational Excellence violation. "Shield Advanced protections are only enabled for resources that you have explicitly specified in Shield Advanced or that you protect through an AWS Firewall Manager Shield Advanced policy." — new resources are NOT automatically protected.
- Instead: Use Firewall Manager to automatically apply Shield Advanced protections to new resources. Implement quarterly audits comparing protected resources against actual internet-facing resources. Tag resources with protection status.
- Detection: Compare `aws shield list-protections` output against all internet-facing resources (CloudFront distributions, Route 53 zones, ELBs, EIPs, Global Accelerator). Flag gaps.
- Impact: Unprotected resources — paying for Shield Advanced subscription but not receiving its benefits for newly created resources. False sense of security.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-protected-resources.html

---

**Using Shield Advanced Without Business/Enterprise Support Plan**
- Risk Level: MEDIUM
- Why: Operational Excellence violation. SRT access — one of Shield Advanced's primary value propositions — requires Business or Enterprise Support plan. Without it, you pay $3,000/month but cannot access DDoS experts during attacks.
- Instead: Ensure at least Business Support plan is active on all accounts with Shield Advanced. For organizations with high-value targets, Enterprise Support provides 15-minute response time for critical cases.
- Detection: `aws support describe-severity-levels` — if this returns an error, support plan may not be sufficient. Check AWS Support Center → Support Plan.
- Impact: Wasted investment — Shield Advanced subscription without SRT access eliminates the human expert response capability. Automated protections still work, but manual escalation is unavailable.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-srt-support.html

---

## Cloud-Native Design Patterns

**Edge-First DDoS Resilient Architecture**
- Category: Resilience
- Problem: Internet-facing applications need to absorb DDoS attacks without impacting legitimate user availability. Regional resources have limited inline protection capability.
- Solution on AWS:
  CloudFront (edge distribution) → AWS WAF (L7 inspection + rate limiting) → Shield Advanced (detection + automatic mitigation) → ALB (origin) → Auto Scaling Group (capacity). Route 53 handles DNS with health checks feeding into Shield Advanced health-based detection. Origin security groups restrict access to CloudFront IP ranges only.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Mitigation Speed | Inline continuous at edge — zero latency to detect and mitigate | CloudFront per-request pricing |
  | Capacity | 100+ Tbps aggregate across all edge locations | Cache miss path still hits origin |
  | Complexity | Full L3/L4/L7 protection stack | Multi-service configuration, WAF rule management |
  | Visibility | Shield Advanced metrics, CloudWatch integration | Requires dashboard/alerting setup |

- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-event-mitigation-logic-continuous-inspection.html

---

**Rate-Based Defense in Depth**
- Category: Resilience
- Problem: Application layer DDoS attacks use legitimate-looking requests that bypass network-level mitigations. Single rate limits can be circumvented by distributing across many IPs.
- Solution on AWS:
  Layer multiple rate-based controls: (1) CloudFront request rate limits at edge, (2) WAF rate-based rules per IP (e.g., 2,000 requests/5min), (3) WAF rate-based rules per URI path for sensitive endpoints (login, API), (4) Shield Advanced automatic mitigation for known DDoS source IPs, (5) Application-level throttling (API Gateway throttling, Lambda concurrency limits) as last resort.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Detection Speed | Rate-based rules mitigate before Shield detection threshold | Requires careful tuning to avoid blocking legitimate bursts |
  | Coverage | Multiple layers prevent single-point bypass | Complex rule management across WAF + application |
  | Accuracy | Path-specific rules target vulnerable endpoints | More rules = higher WCU consumption |

- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-event-detection-application.html

---

**Elastic Scaling as DDoS Absorption**
- Category: Scalability
- Problem: Even with edge mitigation, some attack traffic passes through (especially sophisticated L7 attacks). Origin must absorb residual attack load without degrading service for legitimate users.
- Solution on AWS:
  Auto Scaling Groups with target tracking policies based on request count per target. Pre-warm ALB during anticipated attack windows. Use SQS/Lambda for queue-based load leveling of backend processing. Set CloudFront origin request policies to reduce origin load. Use CloudFront caching aggressively to serve cached responses even during attacks.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Availability | Origin remains available under residual attack load | Higher EC2/compute costs during attack |
  | Recovery | Automatic scale-in after attack subsides | Scale-out lag (2–5 minutes) may cause brief degradation |
  | Cost Control | Shield Advanced DDoS cost protection credits offset scaling costs | Must file credit request post-attack |

- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-resiliency.html

---

**Proactive SRT Engagement Architecture**
- Category: Resilience
- Problem: Manual escalation during DDoS attacks introduces unacceptable delay. Security teams may not detect attacks until significant impact occurs.
- Solution on AWS:
  Configure Route 53 health checks → Associate with Shield Advanced protections → Enable proactive engagement → SRT contacts you when health check fails during a detected event. Pair with: CloudWatch alarms on Shield metrics (`DDoSDetected`, `DDoSAttackBitsPerSecond`, `DDoSAttackPacketsPerSecond`, `DDoSAttackRequestsPerSecond`) → SNS notifications → security team alerting.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Response Time | SRT proactively engages without support case | Requires Business/Enterprise Support plan |
  | Accuracy | Health-based detection reduces false positives | Must maintain health check endpoints |
  | Expertise | AWS DDoS experts handle mitigation | Requires pre-authorized SRT access to WAF/Route 53 |

- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-srt-proactive-engagement.html

---

## Security Architecture

**DDoS Protection — Network Layer (L3/L4)**
- AWS Services:
  - AWS Shield Standard (automatic for all customers)
  - AWS Shield Advanced (enhanced detection and mitigation for subscribed resources)
  - Amazon CloudFront (edge-level inline mitigation)
  - Amazon Route 53 (DNS-level inline mitigation)
  - AWS Global Accelerator (anycast-level mitigation)
  - Elastic Load Balancing (absorbs and distributes traffic)
  - Amazon VPC (security groups, NACLs for access control)
- Architecture:
  Internet traffic → AWS Edge (CloudFront/Route 53/Global Accelerator with inline Shield mitigation) → Regional border (Shield mitigation systems) → VPC (NACLs, security groups) → ALB/NLB → Private subnet targets. Shield mitigation systems operate at every ingress point, rerouting traffic through DDoS mitigation systems in the same location without latency impact. Combined capacity exceeds 100 Tbps.
- Compliance Alignment: SOC 1/2/3, ISO 27001, PCI DSS (infrastructure layer), HIPAA BAA eligible, FedRAMP
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-event-mitigation.html

---

**DDoS Protection — Application Layer (L7)**
- AWS Services:
  - AWS Shield Advanced (detection, automatic mitigation)
  - AWS WAF (web ACL, rate-based rules, managed rules, custom rules)
  - Amazon CloudFront (edge WAF inspection)
  - Application Load Balancer (regional WAF inspection)
  - Shield Advanced Layer 7 Anti-DDoS Managed Rule Group
- Architecture:
  HTTP/HTTPS traffic → CloudFront/ALB → AWS WAF web ACL inspection: (1) Rate-based rules enforce per-IP limits, (2) Shield Advanced managed rule group blocks known DDoS sources, (3) Automatic mitigation deploys custom rules during active attacks, (4) AWS Managed Rules block known attack patterns. Shield Advanced detects L7 attacks by comparing request patterns against historical baseline, accounting for health check status.
- Compliance Alignment: PCI DSS 6.6 (web application firewall requirement), SOC 2
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-app-layer-protections.html

---

**Centralized DDoS Protection Management**
- AWS Services:
  - AWS Firewall Manager (centralized policy management)
  - AWS Shield Advanced (multi-account protection)
  - AWS Organizations (account hierarchy)
  - Amazon SNS (event notifications)
  - AWS Security Hub (findings aggregation)
- Architecture:
  AWS Organizations → Firewall Manager (delegated admin account) → Shield Advanced policies auto-apply to resources matching criteria across all member accounts. Shield events → CloudWatch metrics + SNS notifications → Security Hub findings. One Shield Advanced subscription covers all accounts in the consolidated billing family. Firewall Manager automatically applies Shield protection to new resources matching policy criteria.
- Compliance Alignment: SOC 2 (centralized security monitoring), ISO 27001 (information security management)
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/shield-policies.html

---

## Operational Patterns

**DDoS Event Detection and Response**
- RTO/RPO: Detection: seconds (L3/L4 at edge), minutes (L7). Mitigation: automatic (inline for edge), seconds-minutes (automatic L7), minutes-hours (manual SRT engagement)
- AWS Services:
  - AWS Shield Advanced (detection, metrics, events)
  - Amazon CloudWatch (DDoSDetected metric, alarms)
  - Amazon SNS (notifications)
  - AWS Shield Response Team (expert engagement)
  - Route 53 Health Checks (health-based detection)
- Cost Profile: Medium — Shield Advanced subscription ($3,000/mo) + CloudWatch alarms (per-alarm cost) + SNS notifications (negligible). SRT access requires Business/Enterprise Support ($100+/mo).
- Automation:
  - **Automate**: Shield detection → CloudWatch alarm → SNS → security team notification. Shield automatic L7 mitigation (no human needed).
  - **Manual decision points**: Switching from Count to Block during active attack. Engaging SRT for custom mitigations. Filing DDoS cost protection credit requests post-attack. Deciding to add new protection rules.
- Runbook Skeleton:
  1. **Detection**: CloudWatch alarm fires on `DDoSDetected` metric or Shield event notification received
  2. **Triage**: Check Shield console → Events tab. Identify attack vector (L3/L4/L7), volume, source distribution, targeted resource
  3. **Automatic Response**: Verify automatic mitigation is active (check Shield-managed rule group actions in WAF logs). If Count mode, evaluate switching to Block.
  4. **Escalation**: If automatic mitigation insufficient → Contact SRT via AWS Support (Sev 1 case). Pre-authorize SRT access to WAF/Route 53 before attacks occur.
  5. **Resolution**: Attack subsides → verify health checks return healthy → review WAF logs for blocked legitimate traffic (false positives)
  6. **Post-mortem**: Document attack vectors, peak volume, mitigation effectiveness. File DDoS cost protection credit if applicable. Adjust rate limits and rules based on lessons learned.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-viewing-events.html

---

**DDoS Visibility and Monitoring**
- AWS Services:
  - Amazon CloudWatch (Shield Advanced metrics):
    - `DDoSDetected` — 1 during active attack, 0 otherwise
    - `DDoSAttackBitsPerSecond` — attack traffic volume
    - `DDoSAttackPacketsPerSecond` — attack packet rate
    - `DDoSAttackRequestsPerSecond` — L7 attack request rate
  - AWS Shield Console (Events tab — real-time and historical attack data)
  - AWS CloudTrail (Shield API actions audit trail)
  - Amazon SNS (event notifications)
- Cost Profile: Low — CloudWatch metrics are included in Shield Advanced. Alarm costs per metric. Dashboard costs are negligible.
- Automation:
  - CloudWatch alarms on all DDoS metrics with appropriate thresholds
  - SNS topic subscriptions to security team (email, Slack via Lambda, PagerDuty)
  - CloudWatch dashboard with Shield metrics for SOC visibility
  - EventBridge rules to capture Shield events and route to incident management
- Runbook Skeleton:
  1. Create CloudWatch alarms: `DDoSDetected >= 1` for 1 datapoint in 1 minute
  2. Create CloudWatch dashboard showing: attack metrics, health check status, WAF request counts, origin health
  3. Configure SNS notifications to security team channels
  4. Review Shield Events weekly for patterns and trends
  5. Monthly report: number of detected events, mitigation effectiveness, false positive rate
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/shield-metrics.html

---

**DDoS Cost Optimization (FinOps)**
- AWS Services:
  - AWS Shield Advanced (DDoS cost protection credits)
  - AWS Budgets (cost alerting)
  - AWS Cost Explorer (cost analysis)
  - Firewall Manager (consolidated policy management)
- Cost Profile: Shield Advanced = $3,000/month per consolidated billing family (not per account). DTO fees = $0.025/GB (CloudFront) to $0.050/GB (Regional). Includes WAF costs for protected resources up to 1,500 WCUs and 50B requests/month.
- Automation:
  - AWS Budgets alerts on Shield DTO costs exceeding baseline by >50%
  - Quarterly review: protected resources vs actual internet-facing inventory (avoid over-protection)
  - Post-attack: file DDoS cost protection credit request within 7 days
  - Use consolidated billing to share single subscription across all org accounts
- Runbook Skeleton:
  1. **Subscription optimization**: Verify all accounts are under one consolidated billing family → single $3,000/month
  2. **Resource optimization**: Protect only internet-facing resources. Do not protect internal ALBs or unused EIPs.
  3. **WAF cost optimization**: Shield Advanced covers WAF costs for protected resources — avoid duplicating WAF on unprotected resources
  4. **Post-attack credits**: Document attack in Shield Events → file credit request → track credit application
  5. **Monthly review**: DTO costs per resource, identify cost outliers, right-size protection scope
- Source: https://aws.amazon.com/shield/pricing/

---

## Reference Architectures

**DDoS-Resilient Web Application**
- Context: Public-facing web application requiring high availability during DDoS attacks
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | DNS | Route 53 + Health Checks | DNS resolution, health monitoring, Shield detection input |
  | Edge / CDN | CloudFront | Inline L3/L4 mitigation, caching to absorb L7 floods, global distribution |
  | Web Application Firewall | AWS WAF | L7 inspection, rate limiting, managed rules, Shield automatic mitigation |
  | DDoS Protection | Shield Advanced | Enhanced detection, automatic L7 mitigation, SRT, cost protection |
  | Load Balancing | ALB (private subnets) | Origin traffic distribution, Multi-AZ |
  | Compute | EC2 Auto Scaling or ECS/Fargate | Application logic, elastic scaling |
  | Data | RDS Multi-AZ or DynamoDB | Persistent storage, isolated from internet |
  | Monitoring | CloudWatch + SNS | DDoS metrics, health alarms, team notifications |
  | Management | Firewall Manager | Centralized protection policies |

- Key Decisions: (1) CloudFront cache TTLs — longer TTLs absorb more attack traffic but serve staler content. (2) Rate limit thresholds — too low blocks legitimate users, too high allows attacks. (3) Auto Scaling capacity — over-provision increases cost, under-provision risks degradation during attacks.
- Scaling Path: Start with single-region CloudFront + ALB + ASG. Scale to: Protection Groups for aggregate detection → multi-region origins for DR → Global Accelerator for non-HTTP workloads.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-resiliency.html

---

**DDoS-Resilient API Architecture**
- Context: REST/GraphQL API endpoints exposed to the internet, serving mobile and web clients
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | DNS | Route 53 | API domain resolution, latency-based routing |
  | Edge | CloudFront | API acceleration, edge WAF inspection |
  | WAF | AWS WAF (rate-based + API-specific rules) | Per-endpoint rate limiting, request validation |
  | DDoS | Shield Advanced | L7 DDoS detection and automatic mitigation |
  | API Gateway | Amazon API Gateway | Throttling, quotas, API key management |
  | Compute | Lambda or ECS/Fargate | API logic, auto-scaling |
  | Auth | Cognito + WAF token validation | Authenticated endpoint protection |

- Key Decisions: (1) API Gateway throttling vs WAF rate limits — both provide rate limiting at different layers. (2) Per-API-key rate limits in API Gateway for authenticated traffic. (3) CAPTCHA challenge for unauthenticated endpoints under attack.
- Scaling Path: Start with CloudFront + WAF + API Gateway (built-in throttling). Scale to: Shield Advanced for enhanced detection → Custom WAF rules per endpoint → Protection Groups across multiple APIs.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-app-layer-protections.html

---

## Service Equivalence Map

| Category | AWS | Google Cloud | Azure | Oracle Cloud (OCI) |
|----------|-----|-------------|-------|--------------------|
| **DDoS — Basic** | Shield Standard (free, automatic) | Cloud Armor Standard (free, automatic) | DDoS Protection Basic (free, automatic) | OCI DDoS Protection (free, automatic) |
| **DDoS — Advanced** | Shield Advanced ($3,000/mo + DTO) | Cloud Armor Enterprise ($3,000/mo) | DDoS Protection Standard ($2,944/mo) | OCI WAF + DDoS Protection (included) |
| **WAF** | AWS WAF | Cloud Armor (WAF + DDoS combined) | Azure WAF (Application Gateway / Front Door) | OCI WAF |
| **CDN / Edge** | CloudFront | Cloud CDN | Azure Front Door / CDN | OCI CDN |
| **DDoS Expert Team** | Shield Response Team (SRT) | Cloud Armor Managed Protection Plus (DDoS Response Team) | Azure DDoS Rapid Response (DRR) | Oracle Security Response |
| **Network Firewall** | AWS Network Firewall | Cloud Firewall | Azure Firewall | OCI Network Firewall |
| **Security Posture** | Security Hub + Shield | Security Command Center + Cloud Armor | Defender for Cloud + DDoS Protection | Cloud Guard |

> **⚠️ Important**: OCI bundles DDoS protection into the platform at no additional cost for most attack types. AWS and GCP/Azure charge premium subscriptions for advanced capabilities. Service equivalence does NOT mean feature parity — especially around L7 automatic mitigation, expert team access, and cost protection credits.

---

## Provider Differentiators

```
Differentiator: Inline Continuous Mitigation at Edge
Category: Security
Unique Value: CloudFront and Route 53 receive continuous inline DDoS mitigation without requiring a detection signal. Unlike scrubbing services that detect-then-redirect, AWS mitigates immediately at the edge location where traffic ingresses.
Architecture Impact: Eliminates the detection-to-mitigation gap that exists with traditional DDoS providers. Attacks are mitigated at the same location as legitimate traffic processing — no rerouting, no latency penalty.
When to Leverage: Always — any web application using CloudFront/Route 53 automatically benefits. This is the primary reason to use AWS edge services as the application perimeter.
Caveat: Only applies to CloudFront distributions, Route 53 hosted zones, and Global Accelerator. Regional resources (ALB, EC2) use detection-triggered mitigation.
Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-event-mitigation-logic-continuous-inspection.html

Differentiator: DDoS Cost Protection Credits
Category: Security / FinOps
Unique Value: Shield Advanced provides service credits for AWS bill spikes caused by DDoS attacks on protected resources. No other major provider offers financial protection against DDoS-induced scaling costs as a standard subscription benefit.
Architecture Impact: Enables aggressive auto-scaling policies during attacks without fear of runaway costs. Architects can design for maximum availability knowing that DDoS-induced scaling costs will be credited.
When to Leverage: When cost predictability is essential and auto-scaling is the preferred absorption strategy. Particularly valuable for EC2/ELB architectures that scale compute during attacks.
Caveat: Credits must be requested manually after the attack. Only covers costs directly caused by DDoS (Shield must detect an event). Does not cover costs from non-DDoS traffic spikes.
Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-request-service-credit.html

Differentiator: Shield Advanced Subscription Covers WAF Costs
Category: Cost Optimization
Unique Value: Shield Advanced subscription includes AWS WAF costs (web ACLs, rules, requests up to 1,500 WCUs and 50B requests/month) for protected resources. This bundling eliminates separate WAF billing for most workloads.
Architecture Impact: Simplifies cost modeling — WAF and DDoS protection become a single line item. Removes the trade-off between "more WAF rules = more cost" for Shield-protected resources.
When to Leverage: When protecting multiple resources with WAF — the included WAF coverage (50B requests) exceeds most individual application needs. Most cost-effective when protecting resources that would otherwise incur significant WAF fees.
Caveat: Does not cover Bot Control, CAPTCHA actions, WCUs above 1,500, body inspection above default size, or WAF on non-Shield-protected resources.
Source: https://aws.amazon.com/shield/pricing/

Differentiator: 100+ Tbps Mitigation Capacity (No Traffic Rerouting)
Category: Security
Unique Value: AWS Shield provides over 100 Terabits Per Second of mitigation capacity distributed across all ingress points, without rerouting traffic to external scrubbing centers. Mitigation happens at the same location where traffic is received.
Architecture Impact: No additional latency during mitigation. No dependency on third-party scrubbing capacity. No BGP rerouting delays. Protection scales with AWS infrastructure expansion.
When to Leverage: When latency during DDoS mitigation is unacceptable (real-time applications, financial services, gaming). When avoiding vendor lock-in to specialized DDoS scrubbing providers.
Caveat: 100 Tbps is aggregate across all AWS — not dedicated per-customer. Individual resources still need appropriate architecture for resilience.
Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-event-mitigation.html

Differentiator: Shield Network Security Director (Preview)
Category: Security
Unique Value: Automated network topology analysis, security configuration issue identification, and actionable remediation recommendations. Integrates with Amazon Q Developer for natural language security queries.
Architecture Impact: Enables continuous posture assessment without manual network audits. Can identify misconfigurations (open security groups, missing NACLs, unprotected public endpoints) before they are exploited.
When to Leverage: Large-scale deployments with complex network topologies where manual audit is impractical. Currently in preview — evaluate but do not depend on for production security posture.
Caveat: Preview status — not GA, may change. Separate from Shield Standard and Advanced (not a DDoS mitigation feature). Feature availability and pricing not finalized.
Source: https://aws.amazon.com/shield/features/
```

---

## Scenario Coverage

**Standard Case**: Public-facing web application with SLA requirements
- Approach: CloudFront → WAF (rate-based rules + Managed Rules + Shield automatic mitigation in Block mode) → Shield Advanced → ALB (Multi-AZ) → Auto Scaling Group. Route 53 health checks associated with all Shield protections. Proactive engagement enabled. Protection groups defined per application.
- Key Decisions: (1) Rate limit thresholds per endpoint type (API vs static). (2) Auto Scaling max capacity (cost vs availability trade-off during attack). (3) Whether to enable Bot Control (additional WAF cost, not covered by Shield subscription).

**Edge Case**: Non-HTTP workload requiring DDoS protection (TCP/UDP gaming server, custom protocol)
- Approach: AWS Global Accelerator → Shield Advanced on Accelerator → NLB with Elastic IPs → EC2 instances in private subnets. Shield Advanced provides enhanced L3/L4 detection on Global Accelerator. Cannot use CloudFront/WAF for L7 since it's non-HTTP.
- Architecture: Global Accelerator provides anycast IP addresses that absorb volumetric attacks at AWS edge. Shield Advanced on EIPs provides custom mitigation profiles. SRT can create protocol-specific mitigations.
- Key Decisions: (1) Over-provision EC2 instances — without L7 WAF, all valid-protocol traffic reaches origin. (2) Network ACLs as coarse-grained blocklists during attack. (3) SRT pre-engagement to create custom mitigation profiles for non-standard protocols.

**Anti-Pattern Case**: Customer requests removing CloudFront "to reduce costs" while maintaining DDoS SLA
- Clarification: "Removing CloudFront eliminates inline continuous DDoS mitigation at the edge. Regional resources rely on detection-triggered mitigation with inherent delay. What is the acceptable detection-to-mitigation latency for your SLA? Are you prepared to accept that L3/L4 attacks will hit your regional infrastructure directly? What is the cost comparison: CloudFront per-request fee vs potential DDoS cost protection credit claims and scaling costs during attacks?"
