---
name: configuring-aws-route53-dns
description: "Configures Amazon Route 53 DNS for web applications on AWS, covering hosted zones, routing policies, health checks, DNSSEC signing, DNS Firewall, VPC/Global Resolver, and ARC-based disaster recovery. Use when designing or implementing DNS architecture for AWS-hosted web applications, multi-region routing, hybrid DNS, or secure DNS with DNSSEC."
---

## Function
Specialist in AWS Route 53 DNS architecture for web applications — authoritative DNS, eight routing policies, health checks, DNSSEC signing, DNS Firewall, VPC Resolver, Global Resolver (GA 2026), and ARC-integrated disaster recovery.

## Version Context

**Technology/Framework**: Amazon Route 53
**Target version**: AWS Route 53 2026
**Release date**: 2026-03-09 (Global Resolver GA); 2025-04-01 (Profiles + VPC Endpoints); 2024-11-01 (DNS Firewall Advanced GA)
**Support status**: Active

**Important changes in this version**:
- Route 53 Global Resolver reached GA on 2026-03-09 (30 AWS Regions) — internet-reachable anycast resolver with DoH/DoT, token-based auth, DNS views, and advanced threat protection
- Route 53 Resolver renamed to **Route 53 VPC Resolver** to distinguish from the new Global Resolver
- Route 53 Profiles added Interface VPC Endpoint support (April 2025) — share private hosted zones for VPC endpoints across accounts at scale
- DNS Firewall Advanced reached GA November 2024 — DGA, DNS tunneling, and Dictionary DGA detection with Security Hub integration
- Traffic Flow visual editor improved March 2025 — undo/redo, dark mode, JSON editor with syntax highlighting

**Deprecated**: Route 53 Resolver is the old name; use Route 53 VPC Resolver in all new architecture diagrams and code.

⚠️ **CRITICAL — Agent Warning**:
Route 53 Global Resolver (GA 2026-03-09) and the VPC Resolver naming change are 2026 features. DNS Firewall Advanced (GA November 2024) is distinct from basic DNS Firewall. Do not apply pre-2024 DNSSEC, Resolver naming, or DR failover patterns.

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — ✅⚠️🚫 pattern summaries
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 6 test cases for skill-evaluator
- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — 6 mandatory patterns with full code examples
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — 7 decision matrices with tradeoff tables
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — 6 anti-patterns with ❌/✅ code pairs
- **[Integration Patterns](#integration-patterns)** — Canonical reference architectures
- **[Verification Loop](#verification-loop)** — Validation CLI commands and expected outputs
- **[Quick Reference](#quick-reference)** — Service limits and essential commands
- **[External Resources](#external-resources)** — Official documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

For complete code examples and CLI sequences, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**Mandatory patterns** (Complex domain — 6 patterns):

- **Use Alias records (not CNAME) for all AWS resource targets including zone apex** — Alias records are free for AWS targets, auto-track resource IP changes, and are the only record type valid at the zone apex. CNAME at zone apex violates RFC 1034 and returns an error in Route 53. For ALBs, Route 53 auto-prepends `dualstack.`; create both A and AAAA alias records when IPv6 is enabled.

- **Associate health checks with routing policy records for all failover-capable endpoints** — Health checks do NOT reroute traffic in isolation; they must be attached to Failover/Weighted/Latency/Geolocation/Geoproximity/Multivalue/IP-based records. For alias records targeting ALB or CloudFront, set `Evaluate Target Health = Yes` — this propagates resource health without creating a separate check. Standard interval (30s) for most workloads; Fast (10s, extra charge) for sub-minute detection.

- **Create DNSSEC CloudWatch alarms BEFORE enabling DNSSEC signing** — KSK failures silently break DNSSEC validation for the entire zone; validating resolvers return SERVFAIL, making the domain unreachable. Pre-create alarms on `DNSSECInternalFailure ≥ 1` and `DNSSECKeySigningKeysNeedingAction ≥ 1` in us-east-1. The KMS key MUST be asymmetric, ECC_NIST_P256, in us-east-1 regardless of where the hosted zone was created.

- **Enable Route 53 Resolver DNS Firewall for all VPCs handling sensitive workloads** — DNS tunneling is a documented exfiltration vector that bypasses network egress controls. Use AWS Managed domain lists (Foundational Rules) as baseline. Enable DNS Firewall Advanced (GA November 2024) for signature-based DGA/tunneling/Dictionary-DGA detection with Security Hub integration. Enforce organization-wide with AWS Firewall Manager. Maximum 5 rule groups per VPC per account per Region (non-adjustable).

- **Enable query logging for all public hosted zones and VPC Resolver** — Foundational detective control (Well-Architected SEC04). Public zone log group MUST be in us-east-1. VPC Resolver logs only unique (non-cached) queries; choose one destination per config: CloudWatch Logs (real-time), S3+Athena (long-term), or Kinesis Data Firehose (SIEM streaming). Global Resolver logs in OCSF v1.2.0 format.

- **Use ARC Routing Controls (data plane) for DR failover, not ChangeResourceRecordSets (control plane)** — `ChangeResourceRecordSets` routes through us-east-1, which may be impaired during the exact regional event that triggers DR (REL11-BP04 explicitly prohibits relying on control plane for recovery). ARC Routing Controls operate on 5 Regional cluster endpoints, independent of the Route 53 control plane. Store ARC cluster endpoint IPs and DR IAM credentials offline before any outage.

### ⚠️ Ask First

For complete tradeoff tables and decision code, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

**Decision points** (7 architectural crossroads):

- **Route 53 vs Global Accelerator for multi-region traffic** — Ask: does the app require sub-second failover WITHOUT TTL delay AND static IPs? Both → use Global Accelerator. Otherwise → Route 53 with ARC and low TTLs at lower cost.

- **Active-Active vs Active-Passive multi-region architecture** — Ask the documented RTO/RPO business requirement first. RTO < 15 min → active-active or warm standby + ARC. RTO 15–60 min → pilot light + ARC. RTO hours → backup-and-restore.

- **DNS Firewall deny-list vs allow-list strategy** — Ask: is the external domain access set bounded and well-known? Yes → allow-listing (stronger posture). No (broad package manager or third-party API access) → deny-listing with Managed domain lists; tighten incrementally.

- **Routing policy selection for traffic distribution** — Ask the routing goal: lowest latency (Latency-based), geographic compliance (Geolocation/IP-based), gradual rollout (Weighted), DR failover (Failover), physical proximity control (Geoproximity). For complex multi-region: compose Latency alias → Weighted → individual health-checked resources.

- **DR tier selection — cost vs RTO/RPO** — Translate business RTO to tier: hours → Backup/Restore; tens of minutes → Pilot Light; minutes → Warm Standby; near-zero → Active/Active. Validate tier cost against business value before recommending.

- **DNSSEC adoption for public hosted zones** — Ask: compliance requirement (FedRAMP, DoD, financial regulation) or domain handles credentials/financial data? Yes → enable DNSSEC with pre-configured CloudWatch alarms and us-east-1 KMS key. Otherwise: operational simplicity of unsigned zone may be preferred (DNSSEC enforces max 1-week TTL and incompatible with multi-vendor name servers).

- **Route 53 Global Resolver vs VPC Resolver for external client DNS** — Ask: do external clients have existing DX/VPN connectivity? Yes → VPC Resolver endpoints (established, cheaper at high volume). No (remote workers, mobile, branch offices without VPN) → Global Resolver with DoH/DoT (GA 2026-03-09).

### 🚫 Never Do

For complete wrong/correct code examples, see [Never Do Patterns](./blueprints/never-do-patterns.md).

**Prohibited patterns** (6 anti-patterns, each with a direct ✅ alternative):

- **CNAME at zone apex** [CRITICAL] — Violates RFC 1034; Route 53 returns an error. ✅ Use `Alias A/AAAA` record at zone apex. Detection: `aws route53 list-resource-record-sets ... --query "ResourceRecordSets[?Name=='example.com.' && Type=='CNAME']"` — result must be empty for the apex.

- **ChangeResourceRecordSets as DR failover mechanism** [CRITICAL] — Routes through us-east-1 control plane; unavailable during the regional impairment that triggers DR. ✅ Pre-configure ARC Routing Controls; execute failover via `aws route53-recovery-cluster update-routing-control-state` (ARC data plane). Audit all DR runbooks for `route53 change-*` calls.

- **High TTL on failover-capable records** [HIGH] — A 3600s TTL means clients route to a failed endpoint for up to 1 hour after Route 53 detects failure, extending the actual RTO far beyond health check detection time. ✅ Set TTL = 60–120 seconds on all health-check-associated records. Pre-lower TTLs at least 2× the current value before planned DR tests.

- **Expecting private hosted zone names to resolve from outside associated VPCs** [HIGH] — PHZs resolve only from DNS queries originating within explicitly associated VPCs; on-premises and unassociated VPCs receive NXDOMAIN or public records. ✅ Explicitly associate PHZs with all required VPCs; for on-premises access configure inbound Resolver endpoints + on-premises DNS forwarding rules.

- **Multi-vendor name servers with DNSSEC signing enabled** [HIGH] — Inconsistent DNSSEC responses across DNS providers cause SERVFAIL for all validating resolvers, making the entire zone unreachable. ✅ Enable DNSSEC only on zones served exclusively by Route 53 name servers (`*.awsdns-*.com/net/org/co.uk`). Verify NS records at registrar before enabling signing.

- **Same domain as health-checked record for the health check domain name** [MEDIUM] — Creates a circular dependency; Route 53 may use a stale or cached IP. ✅ For AWS resources (ALB, CloudFront), use alias records with `Evaluate Target Health = Yes`. For EC2 instances, specify the instance IP address directly in the health check configuration.

---

## Integration Patterns

For complete service composition tables, see reference architectures in the research file.

**Canonical reference architectures**:
- **Zone apex + www + CloudFront + ACM** — Public hosted zone → Alias A+AAAA (zone apex + www) → CloudFront. ACM cert in us-east-1; DNS validation CNAME must remain permanently for auto-renewal. CloudFront Alternate Domain Name MUST be set before the alias record is created.
- **Multi-region active-passive DR** — Route 53 Failover routing + ARC Routing Controls + safety rules + Aurora Global. TTL 60–120s. ARC cluster endpoints and DR IAM credentials stored offline. Test DR annually minimum using ARC Region switch.
- **Hybrid DNS (on-premises ↔ VPC)** — Inbound Resolver endpoint (2+ ENIs, one per AZ) + on-premises DNS forwarding rules for private domains + outbound endpoint for VPC-to-on-premises resolution. Route 53 Profiles for 10+ VPCs/accounts. Direct Connect preferred over VPN for reliability.
- **Split-horizon DNS** — Same domain name in both a public and private hosted zone. Private zone explicitly associated with each target VPC — records in each zone are entirely independent (no automatic sync). Use Route 53 Profiles + DNS views (Global Resolver) to extend split-horizon beyond VPC boundaries.
- **Multi-region latency tree** — Latency alias → Weighted (blue/green, canary) → individual resource records (health-checked). Zero-weight standby serves as last resort within a Region before inter-Region failover propagates.

**Common problems**:
- **Private zone not resolving from on-premises** → Configure inbound Resolver endpoint ENIs; add on-premises forwarding rules for the private domain; verify VPC association via `aws route53 list-vpc-association-authorizations`
- **DNSSEC SERVFAIL after enabling** → Confirm KMS key is ECC_NIST_P256 in us-east-1; check `DNSSECInternalFailure` alarm; verify DS record added to parent zone
- **DNS changes taking effect slowly after failover** → TTL was high pre-change; pre-lower TTL to 60–120s before DR events; for sub-TTL failover use Global Accelerator
- **DNS Firewall blocking legitimate traffic** → Check VPC Resolver query logs for `action = BLOCK`; create ALLOW rule with lower priority number than the blocking rule

---

## Verification Loop

The agent MUST execute after each Route 53 configuration:

### 1. Validate Alias Records (Not CNAME for AWS Targets)
```bash
# All AWS-resource alias records present
aws route53 list-resource-record-sets --hosted-zone-id ZONE_ID \
  --query "ResourceRecordSets[?AliasTarget]"
# Expected: all AWS resource targets listed here; exit code: 0

# No CNAME at zone apex (must return empty)
aws route53 list-resource-record-sets --hosted-zone-id ZONE_ID \
  --query "ResourceRecordSets[?Name=='example.com.' && Type=='CNAME']"
# Expected: empty list; exit code: 0
```

### 2. Validate Health Check Associations
```bash
# All routing-policy records have HealthCheckId
aws route53 list-resource-record-sets --hosted-zone-id ZONE_ID \
  --query "ResourceRecordSets[?HealthCheckId]"
# Expected: Failover/Weighted/Latency/Geo records show HealthCheckId; exit code: 0

aws route53 get-health-check-status --health-check-id HEALTH_CHECK_ID
# Expected: HealthCheckObservations show Healthy; exit code: 0
```

### 3. Validate Query Logging
```bash
aws route53 list-query-logging-configs --hosted-zone-id ZONE_ID
# Expected: at least one config; CloudWatchLogsLogGroupArn ends in region=us-east-1

aws route53resolver list-resolver-query-log-configs --region REGION
# Expected: at least one config associated with each sensitive VPC; exit code: 0
```

### 4. Validate DNSSEC (if enabled)
```bash
aws --region us-east-1 route53 get-dnssec --hosted-zone-id ZONE_ID
# Expected: Status = SIGNING; exit code: 0

aws cloudwatch describe-alarms --alarm-name-prefix DNSSEC --region us-east-1
# Expected: DNSSECInternalFailure and DNSSECKeySigningKeysNeedingAction alarms present
```

### 5. Validate ARC Routing Controls (DR configuration)
```bash
aws route53-recovery-control-config list-routing-controls \
  --control-panel-arn CONTROL_PANEL_ARN
# Expected: routing controls present for each critical endpoint; exit code: 0

aws route53-recovery-cluster get-routing-control-state \
  --routing-control-arn ROUTING_CONTROL_ARN
# Expected: RoutingControlState = On (primary active); exit code: 0
```

**Troubleshooting**:
- DNSSEC SERVFAIL → confirm KMS key Region is us-east-1; check alarm state; verify DS record at parent zone is correct (algorithm 13)
- Private zone NXDOMAIN from on-premises → verify inbound endpoint ENIs are active; verify on-premises DNS forwarding rules point to inbound endpoint IPs; verify VPC association
- ARC failover not executing → confirm routing controls are associated with Route 53 health checks; confirm safety rules are not blocking; verify offline DR IAM credentials are valid

---

## Quick Reference

**Essential CLI commands**:
```bash
# List all hosted zones
aws route53 list-hosted-zones

# List all records in a zone
aws route53 list-resource-record-sets --hosted-zone-id ZONE_ID

# Check DNSSEC signing status
aws --region us-east-1 route53 get-dnssec --hosted-zone-id ZONE_ID

# Check DNS Firewall rule group associations for a VPC
aws route53resolver list-firewall-rule-group-associations --region REGION

# DR failover: toggle ARC routing control (data plane — safe during regional impairment)
aws route53-recovery-cluster update-routing-control-state \
  --routing-control-arn ARN --routing-control-state Off

# Check routing control state
aws route53-recovery-cluster get-routing-control-state --routing-control-arn ARN
```

**Critical limits**:

| Resource | Limit | Adjustable |
|----------|-------|-----------|
| Hosted zones per account | 500 | Yes |
| Health checks per account | 200 | Yes |
| Reusable delegation sets per account | 100 | No |
| DNS Firewall rule groups per VPC | 5 per VPC/account/Region | No |
| VPCs per private hosted zone | 300 | Use Profiles beyond this |
| VPCs per Route 53 Profile | 1,000 | Yes |
| Profiles per account per Region | 5 | Yes |
| Query log configs per Region (VPC Resolver) | 20 | No |
| Resolver endpoint IPs | 6 max per endpoint | — |
| Resolver endpoint throughput | 10,000 qps per IP | Add IPs for more |
| Calculated health check children | 255 max | No |
| DNSSEC KSKs per hosted zone | 2 max | No (sufficient for rotation) |
| Route 53 data plane SLA | 100% availability | — |

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/configuring-aws-route53-dns/
├── SKILL.md                          <- This file (summary + guardrails)
└── blueprints/
    ├── always-do-patterns.md         <- 6 mandatory patterns with full code examples
    ├── ask-first-decisions.md        <- 7 decision matrices with tradeoff tables
    ├── never-do-patterns.md          <- 6 anti-patterns with wrong/correct code pairs
    └── evaluation-scenarios.md       <- 6 test scenarios for skill-evaluator
```

**When to consult blueprints**:
- Full CLI/API code for alias record creation, DNSSEC pipeline, ARC setup → `always-do-patterns.md`
- Complete tradeoff tables for DR tier, routing policy selection, DNSSEC adoption → `ask-first-decisions.md`
- Exact ❌ wrong vs ✅ correct code for CNAME-at-apex, control-plane DR, high-TTL → `never-do-patterns.md`

---

## External Resources

### Official Documentation
- [Route 53 Developer Guide](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/Welcome.html) — Primary reference (2026-08-31)
- [Routing Policy Reference](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-policy.html) — All 8 routing policies (2026-08-31)
- [Alias vs CNAME Records](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resource-record-sets-choosing-alias-non-alias.html) — Alias record guide (2026-08-31)
- [DNS Failover Configuration](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-failover-configuring.html) — Health check + failover patterns (2026-08-31)
- [DNSSEC Configuration](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-configuring-dnssec.html) — DNSSEC signing guide (2026-08-31)
- [Route 53 Quotas](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/DNSLimitations.html) — All service limits (2026-08-31)
- [Private Hosted Zones](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/hosted-zones-private.html) — PHZ guide (2026-08-31)
- [Route 53 Resolver](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver.html) — VPC Resolver + endpoints (2026-08-31)

### Disaster Recovery & ARC
- [ARC Developer Guide](https://docs.aws.amazon.com/r53recovery/latest/dg/what-is-route53-recovery.html) — Routing controls, safety rules, Region switch (2026-08-31)
- [ARC Safety Rules](https://docs.aws.amazon.com/r53recovery/latest/dg/routing-control.safety-rules.html) — Assertion + gating rules (2026-08-31)
- [Disaster Recovery Workloads on AWS](https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html) — DR tiers whitepaper (2026-08-31)
- [Route 53 Accelerated Recovery](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/accelerated-recovery.html) — Control plane DR (2026-08-31)

### Security & DNS Firewall
- [DNS Firewall Rule Groups](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-dns-firewall-rule-groups.html) — DNS Firewall configuration (2026-08-31)
- [DNS Firewall Advanced GA (Nov 2024)](https://aws.amazon.com/about-aws/whats-new/2024/11/amazon-route-53-resolver-dns-firewall-advanced) — DGA/tunneling detection
- [Route 53 Global Resolver GA (Mar 2026)](https://aws.amazon.com/about-aws/whats-new/2026/03/amazon-route-53-global-resolver) — Anycast secure DNS
- [Route 53 Profiles + VPC Endpoints (Apr 2025)](https://aws.amazon.com/about-aws/whats-new/2025/04/amazon-route-53-profiles-vpc-endpoints) — Interface endpoint support
- [Query Logging Guide](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/query-logs.html) — Public zone + VPC Resolver logging (2026-08-31)
- [IAM Permissions Reference](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/access-control-managing-permissions.html) — Zone-owner vs record-owner permissions (2026-08-31)
