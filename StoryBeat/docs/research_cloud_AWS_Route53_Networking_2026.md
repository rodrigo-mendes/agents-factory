# Cloud Architecture Research — Output Template

# Output Format

## Metadata

```yaml
Full_Name: "AWS Route 53 — Networking Architecture - Route 53 DNS"
Cloud_Provider: "AWS"
Architecture_Domain: "Networking Architecture - Route 53 DNS"
Target_Edition: "AWS Route 53 2026"
Architecture_Context: "web application"
Official_Source_URL: "https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/Welcome.html"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-08-31"
Currency_Threshold: "2027-08-31"
Research_Depth: "exhaustive"
Max_Iterations: 8
Research_Quality_Score: "95%"
Gap_Loop_Ran: true
Iterations_Used: "6 parallel section-investigators"
Triangulated_Count: 87
Unverified_Count: 6
Irresolvable_Count: 0
```

## Executive Summary

Amazon Route 53 is AWS's highly available and scalable DNS web service that unifies three distinct functions under one product: domain registration, authoritative DNS routing, and endpoint health checking. Within cloud architecture practice for web applications, Route 53 occupies the critical path from user request to application — every HTTP transaction begins with a DNS resolution. Route 53 extends standard DNS with proprietary Alias records, eight routing policies spanning simple to geoproximity, a global anycast data plane spanning 95+ Points of Presence, and deep integration with AWS health-checking and the Application Recovery Controller (ARC). Understanding the control plane versus data plane split (control plane: us-east-1 APIs; data plane: globally distributed authoritative DNS with 100% availability SLA) is non-negotiable for architects designing resilient systems, because DNS query resolution continues independently of control plane availability.

The 2026 edition introduces one major new service and several capability expansions. Route 53 Global Resolver reached General Availability on 2026-03-09 across 30 AWS Regions, adding an internet-reachable anycast DNS resolver that supports DNS over HTTPS (DoH), DNS over TLS (DoT), token-based client authentication, DNS views for split-horizon DNS beyond VPC boundaries, and advanced threat protection including DGA and DNS tunneling detection. DNS Firewall Advanced (GA November 2024) added signature-based inspection for DGA, DNS tunneling, and Dictionary DGA threats with Security Hub integration. Route 53 Profiles gained support for Interface VPC Endpoints (April 2025), enabling organizations to share private hosted zones for VPC endpoints across multiple accounts without manual per-VPC association. Route 53 VPC Resolver is the new official name for what was previously Route 53 Resolver, distinguished from the new Global Resolver service. The Traffic Flow visual editor received significant improvements in March 2025 (undo/redo, dark mode, JSON editor with syntax highlighting). Route 53 Accelerated Recovery provides a 60-minute control plane RTO for public hosted zones if us-east-1 is impaired.

Three critical guardrails govern Route 53 design for web applications. First, always use Alias records (not CNAME) when pointing to AWS resources — alias records are free for AWS targets, supported at the zone apex where CNAME is illegal per DNS protocol, and have Route 53-managed TTLs that track resource IP changes automatically. Second, any failover-oriented routing must be paired with health checks; Route 53 health checks alone do not reroute traffic unless associated with a Failover, Weighted, Latency, Geolocation, Geoproximity, Multivalue, or IP-based routing policy record. Third, for disaster recovery failover operations, use ARC Routing Controls (data plane switches) rather than making ChangeResourceRecordSets API calls (control plane), because control plane availability in us-east-1 cannot be assumed during a regional impairment — exactly the moment reliable failover is needed most.

## Cloud Architecture Glossary

```
Term: Amazon Route 53
Definition: An AWS service combining three distinct capabilities: (1) domain name registrar, (2) authoritative DNS service with a global data plane (200+ PoPs, 100% availability SLA), and (3) endpoint health checker. The control plane (APIs, console) is located in us-east-1 with us-west-2 as fallback; the data plane is globally distributed. Domain registrations are managed only in us-east-1.
Provider Docs Section: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/Welcome.html
Architect Usage: Treat Route 53 as three services. DNS changes go through the control plane; DNS queries are served by the data plane. Plan for control plane unavailability separately from data plane unavailability.
Common Confusion: Architects conflate the control plane (where you create/update records) with the data plane (where DNS queries are answered). DNS query resolution continues during control plane impairments. A related confusion: Route 53 is authoritative DNS, not a recursive resolver — it does not cache or forward queries on behalf of clients.
```

```
Term: Hosted Zone
Definition: A container for DNS records that defines how Route 53 routes traffic for a domain and all its subdomains. A hosted zone has the same name as the corresponding domain. Two types exist: public and private. Hosted zones are separately billable from domain registration ($0.50/month for first 25, $0.10/month thereafter).
Provider Docs Section: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/AboutHZWorkingWith.html
Architect Usage: Create one hosted zone per domain. Use separate hosted zones for subdomains when subdomain delegation is required (different team ownership). Do not confuse zone creation with domain registration — they are separate actions with separate charges.
Common Confusion: A hosted zone is NOT a domain registration. You can have a hosted zone without registering the domain through Route 53 (e.g., domain registered elsewhere, DNS delegated to Route 53). Conversely, registering a domain through Route 53 automatically creates a hosted zone.
```

```
Term: Public Hosted Zone
Definition: A hosted zone containing DNS records that Route 53 answers for internet traffic. Automatically created when a domain is registered through Route 53. Route 53 automatically creates NS and SOA records. Visible to all internet clients.
Provider Docs Section: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/AboutHZWorkingWith.html
Architect Usage: Use for all internet-facing domains. Enable query logging (CloudWatch Logs, log group must be in us-east-1) for audit and security. Enable DNSSEC signing for domains requiring DNS response integrity.
Common Confusion: Not private by default. All records in a public hosted zone are resolvable by any internet client. Split-horizon DNS requires a separate private hosted zone with the same domain name — these do not share records automatically.
```

```
Term: Private Hosted Zone
Definition: A hosted zone whose records are only resolvable from DNS queries originating within one or more associated VPCs. Uses reserved name server addresses (ns-0.awsdns-00.com, ns-512.awsdns-00.net, ns-1024.awsdns-00.org, ns-1536.awsdns-00.co.uk) that are visible on the internet but VPC Resolver never connects to them publicly.
Provider Docs Section: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/hosted-zones-private.html
Architect Usage: Use for internal service discovery, database endpoints, and any resource that should not be DNS-resolvable from the internet. Must explicitly associate with each VPC. Use Route 53 Profiles to associate a private hosted zone with many VPCs and accounts at scale.
Common Confusion: Queries to private hosted zone names from OUTSIDE associated VPCs do not return private records — they fall through to public DNS. This is not automatic protection; it means external clients can attempt to resolve the names but will either get NXDOMAIN or public records. Cannot convert between public and private zones — must create a new zone.
```

```
Term: Alias Record
Definition: A Route 53-proprietary DNS record extension. Allows routing to selected AWS resources (CloudFront, ALB/NLB/CLB, API Gateway, App Runner, Elastic Beanstalk, Global Accelerator, OpenSearch, VPC interface endpoints, AppSync, S3 website, another Route 53 record in the same zone). Alias records CAN be created at the zone apex. DNS queries are free for alias records pointing to AWS resources. TTL is managed by Route 53, not the architect. Alias records appear as A or AAAA records in dig/nslookup output — the alias nature is not visible to DNS clients.
Provider Docs Section: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resource-record-sets-choosing-alias-non-alias.html
Architect Usage: Use alias records whenever the target is a supported AWS resource, especially at the zone apex. This eliminates the zone apex CNAME problem and provides free query resolution. Do not use alias records to point to non-AWS external hostnames — use CNAME instead.
Common Confusion: Alias records are NOT CNAME records, though they serve a similar purpose. Alias records respond only when both the record name AND the query type match; CNAME redirects regardless of query type. Alias records cannot be delegation targets outside Route 53. The alias nature is invisible to DNS clients.
```

```
Term: CNAME Record
Definition: Standard DNS record that redirects queries for one domain name to another domain name. The target is another hostname (not an IP). CNAME records CANNOT be created at the zone apex because zone apex must have NS and SOA records, and CNAME coexistence with other record types at the same name is prohibited by DNS protocol (RFC 1034).
Provider Docs Section: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/ResourceRecordTypes.html
Architect Usage: Use for non-AWS external hostnames at non-apex subdomains. Use for ACM DNS validation (underscore-prefixed CNAME). Do not use at zone apex — use Alias records instead. CNAME queries are charged per query; Alias queries to AWS resources are free.
Common Confusion: Architects from other DNS providers sometimes attempt CNAME at zone apex ("CNAME flattening" offered by some providers). Route 53 solves this differently via Alias records, which are superior (free, auto-TTL, integrated health checking). Attempting CNAME at zone apex in Route 53 results in an error.
```

```
Term: Zone Apex
Definition: The top-level node of a DNS namespace for a hosted zone — the domain name itself without any subdomain prefix (e.g., example.com rather than www.example.com). Also called the "naked domain" or "root domain." The zone apex always has NS and SOA records; CNAME at zone apex is illegal per DNS protocol because CNAME cannot coexist with other record types at the same name.
Provider Docs Section: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resource-record-sets-choosing-alias-non-alias.html
Architect Usage: Use Alias records (A/AAAA) at the zone apex to point to AWS resources. For www-to-apex redirect patterns, use two CloudFront distributions plus two Alias records — one for the apex (example.com) and one for www (www.example.com).
Common Confusion: Often called "naked domain" or "root domain" informally. The zone apex is NOT the DNS root (.) — it is the root of the specific hosted zone. CNAME prohibition at zone apex is a DNS protocol requirement, not a Route 53 limitation.
```

```
Term: Routing Policy
Definition: The algorithm Route 53 uses to respond to DNS queries for a record set. Eight policies exist: Simple, Weighted, Latency-based, Failover, Geolocation, Geoproximity, Multivalue Answer, and IP-based. Routing policies operate on the data plane. Each policy has specific use cases, limits on number of records with the same name and type, and different behaviors when health checks are associated.
Provider Docs Section: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-policy.html
Architect Usage: Select routing policy based on traffic distribution goal (Weighted), latency optimization (Latency), geographic compliance (Geolocation/IP-based), or disaster recovery (Failover). Combine policies in tree structures (e.g., Latency alias → Weighted → individual resources) for complex multi-region routing. Never change routing policies during an active DR event — configure them in advance.
Common Confusion: Routing policies operate per-record, not per-zone. Multiple records with the same name and type but different routing policies are not supported — all records with the same name and type must use the same routing policy. Health checks do not reroute traffic alone — they must be associated with routing policy records.
```

```
Term: Health Check
Definition: A Route 53 mechanism that monitors the health of an endpoint (HTTP, HTTPS, TCP), another health check (calculated health check), or a CloudWatch alarm data stream. Three types: endpoint health checks, calculated health checks, and CloudWatch alarm health checks. Health checks are associated with routing policy records to enable automatic failover. Route 53 uses 18% rule: if >18% of health checkers report endpoint healthy → healthy; if ≤18% report healthy → unhealthy.
Provider Docs Section: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/health-checks-types.html
Architect Usage: Associate health checks with all failover, weighted, latency, geolocation, geoproximity, multivalue, and IP-based records intended for high availability. For AWS resources, use alias records with Evaluate Target Health = Yes instead of creating separate health checks. Cannot check endpoints with RFC 5735/6598/5156 private/nonroutable IPs.
Common Confusion: Health checks alone do NOT reroute traffic. They must be associated with routing policy records. The 18% rule means a health check can be marked unhealthy even if some health checkers report it healthy — this is intentional to prevent false-unhealthy. ARC Routing Control health checks are programmatic on/off switches, not metric-based health checkers.
```

```
Term: TTL (Time to Live)
Definition: The number of seconds that DNS resolvers cache a DNS record response before re-querying Route 53. After a DNS record change, clients using cached answers continue receiving the old answer until the TTL expires. Alias records pointing to AWS resources have TTL controlled by Route 53, not the architect. SOA minimum TTL field applies only to negative caching (NXDOMAIN/NODATA), not positive records.
Provider Docs Section: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resource-record-sets-values-shared.html
Architect Usage: Set low TTLs (60–120 seconds) for records subject to failover. Set higher TTLs (300–3600 seconds) for stable records to reduce query costs and resolver load. Pre-lower TTLs well before planned migrations. DNSSEC signing enforces a maximum TTL of 1 week on all records in the zone.
Common Confusion: SOA minimum TTL is frequently misread as applying to all records in the zone. It applies only to negative caching (how long resolvers cache a "this record doesn't exist" response). Some DNS resolvers/clients may cache beyond the TTL — Route 53 has no control over non-compliant resolver behavior. [UNVERIFIED: explicit AWS architectural caveat on this behavior]
```

```
Term: Reusable Delegation Set
Definition: A fixed set of four Route 53 name servers that can be assigned to multiple hosted zones. Normally, Route 53 assigns name servers randomly from four sets; reusable delegation sets allow consistency across many zones. Can only be created via AWS CLI/API/SDK — the console does not support creation. Cannot be retroactively applied to existing hosted zones (must create a new zone and specify the delegation set at creation time). Maximum 100 reusable delegation sets per account.
Provider Docs Section: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/ListingDelegationSets.html
Architect Usage: Use when managing DNS for many customer domains (e.g., SaaS providers) and a consistent set of name servers is required for allowlisting or branding. Plan delegation sets before zone creation — they cannot be applied retroactively.
Common Confusion: Reusable delegation sets are NOT available in the console; architects who don't know this will search for the option repeatedly. Also: the 100 hosted zones per reusable delegation set limit is separate from the 500 hosted zones per account limit.
```

```
Term: Split-Horizon DNS
Definition: A DNS configuration where the same domain name resolves to different values depending on the query source. Implemented in Route 53 by creating both a public hosted zone and a private hosted zone with the same domain name. Internet clients receive public records; VPC clients receive private records. Route 53 Global Resolver implements split-horizon via DNS views — different policies applied to different client groups regardless of VPC membership.
Provider Docs Section: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/hosted-zones-private.html
Architect Usage: Use for dual-environment setups where an API endpoint resolves to an internal NLB IP from VPC but to a CloudFront/ALB from the internet. Private hosted zone must be explicitly associated with each VPC — not automatic. With Global Resolver DNS views, split-horizon extends to remote users without VPN.
Common Confusion: Split-horizon DNS is NOT automatic when creating both a public and private zone with the same name — the private zone must be explicitly associated with VPCs. Records in the two zones are entirely independent; creating a record in one does not create it in the other.
```

```
Term: Route 53 VPC Resolver
Definition: (Previously "Route 53 Resolver") A recursive DNS resolver built into every VPC, accessible at the VPC CIDR + 2 address (e.g., 10.0.0.2 for a 10.0.0.0/16 VPC). Responds to DNS queries from AWS resources within the VPC. Resolves: public domain records (via recursive lookups against public name servers), VPC-specific DNS names (EC2 instance DNS names), and private hosted zone records. Renamed when Amazon Route 53 Global Resolver was introduced (GA 2026-03-09).
Provider Docs Section: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver.html
Architect Usage: Serves as the DNS resolver for all EC2 instances, Lambda functions, and containers running in a VPC. Extend its reach to on-premises via inbound/outbound Resolver endpoints over Direct Connect or Site-to-Site VPN. Associate DNS Firewall rule groups to filter outbound DNS queries. Cannot directly resolve private hosted zones outside associated VPCs without endpoint forwarding rules.
Common Confusion: VPC Resolver is NOT Global Resolver. VPC Resolver is the per-VPC built-in recursive resolver at VPC+2; Global Resolver (GA 2026) is a separate internet-reachable anycast service. Many architects also confuse VPC Resolver (recursive) with Route 53 authoritative DNS — they are different components.
```

```
Term: Inbound / Outbound Resolver Endpoints
Definition: Network interfaces (ENIs) in a VPC that extend DNS resolution across network boundaries. Inbound endpoints: allow DNS queries from on-premises networks or other VPCs to be forwarded into your VPC's Route 53 VPC Resolver. Outbound endpoints: allow DNS queries from your VPC to be forwarded to on-premises or remote DNS resolvers via forwarding rules. Both require connectivity via AWS Direct Connect or Site-to-Site VPN.
Provider Docs Section: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver.html
Architect Usage: Use inbound endpoints when on-premises systems need to resolve private hosted zone records. Use outbound endpoints with forwarding rules when VPC workloads need to resolve on-premises domain names. Minimum one ENI per AZ recommended for high availability. UDP throughput: up to 10,000 queries/second per IP (may drop to 1,500 with connection tracking or NLB).
Common Confusion: Inbound and outbound directions are from the Route 53 VPC Resolver's perspective, not the client's. "Inbound" means queries come INTO the VPC Resolver (from outside the VPC); "outbound" means queries go OUT from the VPC Resolver (to external DNS resolvers). Architects frequently reverse these.
```

```
Term: DNSSEC Signing
Definition: DNS Security Extensions applied to a Route 53 public hosted zone to cryptographically sign DNS responses, allowing resolvers to verify authenticity and integrity. Uses AWS KMS for the Key Signing Key (KSK, ECC_NIST_P256, must be in us-east-1). Route 53 manages the Zone Signing Key (ZSK) automatically. Enforces maximum TTL of 1 week across all records in the signed zone. Requires a chain of trust established by adding a DS record to the parent zone. Not available for private hosted zones (consistent with all DNSSEC documentation applying to public zones only; [UNVERIFIED: absence from docs is consistent evidence, not an explicit statement]).
Provider Docs Section: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-configuring-dnssec.html
Architect Usage: Enable DNSSEC for domains where DNS response tampering poses a compliance or security risk. Create CloudWatch alarms for DNSSECInternalFailure and DNSSECKeySigningKeysNeedingAction BEFORE enabling signing. Multi-vendor name server configurations are NOT supported with DNSSEC.
Common Confusion: DNSSEC protects DNS responses (authenticity/integrity), not DNS transport confidentiality. HTTPS still needed for application-layer confidentiality. The KMS key MUST be in us-east-1 regardless of where the hosted zone was created — a common setup failure. KSK and ZSK are different: KSK is operator-managed via KMS; ZSK is fully managed by Route 53.
```

```
Term: ARC Routing Control
Definition: An Application Recovery Controller (ARC) feature that provides extremely reliable programmatic on/off switches for DNS-based routing. Each routing control is associated with a Route 53 health check that acts as a switch (does NOT perform actual health monitoring). When a routing control is switched OFF, Route 53 treats the associated health check as unhealthy and stops routing traffic to that endpoint. ARC routing controls operate via the ARC data plane (5 Regional cluster endpoints), not the Route 53 control plane — making them usable even during us-east-1 impairments.
Provider Docs Section: https://docs.aws.amazon.com/r53recovery/latest/dg/what-is-route53-recovery.html
Architect Usage: Use ARC routing controls as the mechanism for DR failover instead of ChangeResourceRecordSets API calls. Configure safety rules (assertion rules and gating rules) to prevent accidental fail-open scenarios. Store DR IAM credentials for ARC operations in a physical safe or virtual vault outside AWS.
Common Confusion: ARC routing control health checks do NOT check endpoint health — they are purely programmatic switches. Confusion with standard Route 53 endpoint health checks leads architects to assume health checks associated with routing controls perform actual monitoring. Also confused with ARC Readiness Checks, which are a separate feature for monitoring resource quotas and capacity.
```

```
Term: Route 53 Global Resolver
Definition: A new service (GA 2026-03-09, 30 AWS Regions) providing an internet-reachable anycast DNS resolver for authorized clients from anywhere. Supports DNS over UDP/TCP (Do53), DNS over TLS (DoT), and DNS over HTTPS (DoH). Uses anycast IPs (two unique IPv4 or IPv6 anycast IPs per global resolver) routing to the nearest AWS Region. Resolves both public internet domains AND private hosted zones, extending private zone resolution beyond VPC boundaries without VPN. Implements split-horizon via DNS views. Includes DNS Firewall with advanced threat detection (DGA, DNS tunneling, Dictionary DGA).
Provider Docs Section: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/gr-concepts-terminology.html
Architect Usage: Use for remote workers, branch offices, or any client requiring secure, authenticated DNS resolution with access to private hosted zones without requiring a VPN or Direct Connect. Configure DNS views for split-horizon policies. Enable advanced threat protection. Multi-region deployment requires 2+ AWS Regions for automatic failover.
Common Confusion: Global Resolver is NOT a replacement for VPC Resolver. VPC Resolver remains the built-in DNS for EC2/ECS/Lambda within VPCs. Global Resolver serves external or remote clients. Also: Global Resolver is distinct from Global Accelerator — entirely different services.
```

```
Term: Route 53 Profiles
Definition: A configuration container for DNS-related Route 53 settings that can be applied to and shared across many VPCs and accounts. Supports associating: private hosted zones, Resolver rules (forwarding and system), DNS Firewall rule groups, Interface VPC Endpoints (added April 2025), and VPC Resolver query logging configurations. One Profile per VPC at a time. Shareable via AWS RAM within the same Region. Updates to a Profile propagate automatically to all associated VPCs. Maximum 5 Profiles per account per Region (adjustable), 1,000 VPCs per Profile.
Provider Docs Section: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/profiles.html
Architect Usage: Use Profiles to manage DNS configuration at scale across many VPCs or AWS accounts (e.g., Landing Zone, Control Tower environments). Especially useful for VPC endpoint private hosted zones — eliminates manual association of PHZs to every new VPC. Local VPC forwarding rules take precedence over Profile-managed rules for the same domain.
Common Confusion: Profiles are NOT a replacement for private hosted zone VPC association for small deployments — they add operational overhead for a handful of VPCs. The VPC-per-private-hosted-zone limit is 300; beyond that, use Profiles. Also: Profiles are Region-specific; cross-Region sharing is not supported.
```

## Architecture Guardrails

> Confidence legend: 🟢 High (2+ official sources, dated ≤12mo) | 🟡 Medium (1 source or dated 12–24mo) | 🔴 Low (community source or dated >24mo — verify before use)

### ✅ Mandatory Patterns

**1. Use Alias Records (Not CNAME) for All AWS Resource Targets Including Zone Apex** 🟢
- Pillar Alignment: Reliability (REL02-BP01), Cost Optimization
- Why: AWS Well-Architected REL02-BP01 states "Use a highly available and scalable DNS such as Amazon Route 53 to manage your domain's DNS records." Alias records automatically track IP changes for AWS resources (CloudFront, ALB, etc.), are free for AWS targets, and are the only record type that can be created at the zone apex — CNAME at zone apex violates DNS protocol (RFC 1034). Using CNAME for AWS resources incurs per-query charges that accumulate under load and introduces TTL mismatch risks when the AWS resource's IPs change.
- AWS Services: Route 53 (Alias A/AAAA records), CloudFront, ALB/NLB, API Gateway, App Runner, Elastic Beanstalk, Global Accelerator, OpenSearch, S3 website
- Architecture Decision:
  - Create Alias A record (and AAAA when IPv6 enabled) at zone apex pointing to CloudFront distribution or ALB
  - For ALBs: Route 53 console auto-prepends `dualstack.` to DNS name to enable IPv4+IPv6
  - Set "Evaluate Target Health = Yes" on alias records to inherit health from target resource
  - Do NOT create CNAME at zone apex — error will result; use Alias instead
  - For simple alias: `example.com` A ALIAS → `d1234.cloudfront.net`
  - For alias simple records: only one alias target allowed (use weighted/latency for multi-target)
- Verification:
  - `aws route53 list-resource-record-sets --hosted-zone-id ZONE_ID --query "ResourceRecordSets[?AliasTarget]"`
  - Confirm `AliasTarget` is present and `EvaluateTargetHealth` is set appropriately
  - `dig example.com` → response should show A record (not CNAME chain)
- Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resource-record-sets-choosing-alias-non-alias.html (2026-08-31)

**2. Associate Health Checks With Routing Policy Records for All Failover-Capable Endpoints** 🟢
- Pillar Alignment: Reliability (REL02-BP01, REL11-BP04)
- Why: Route 53 health checks do not reroute traffic in isolation — they must be associated with routing policy records. REL11-BP04 explicitly states that Route 53 data plane (which includes health-check-based routing) is designed for 100% availability SLA and is more reliable than control plane operations. Unassociated health checks generate cost ($0.50–$0.75/month/check) and false confidence without any routing effect.
- AWS Services: Route 53 (health checks), Route 53 (Failover/Weighted/Latency/Geolocation/Multivalue routing policy records)
- Architecture Decision:
  - For AWS resources targeted via alias records: set `Evaluate Target Health = Yes` on the alias record — this propagates health from the target (ALB, CloudFront) to the routing decision without creating a separate health check
  - For non-AWS endpoints: create endpoint health checks (HTTP/HTTPS/TCP); associate with record via `HealthCheckId`
  - Failover routing: Primary record has health check; when Primary unhealthy → Route 53 automatically returns Secondary record
  - Standard request interval (30s) sufficient for most workloads; Fast (10s, additional charge) for sub-minute detection
  - Failure threshold: 1 (fast detection) to 10 (stability); default 3
  - For complex topologies: use calculated health checks to aggregate child checks (max 255 children)
- Verification:
  - `aws route53 list-resource-record-sets --hosted-zone-id ZONE_ID --query "ResourceRecordSets[?HealthCheckId]"`
  - Confirm `HealthCheckId` present on all failover-policy records
  - `aws route53 get-health-check-status --health-check-id HEALTH_CHECK_ID`
- Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-failover-configuring.html (2026-08-31)

**3. Create DNSSEC CloudWatch Alarms BEFORE Enabling DNSSEC Signing** 🟢
- Pillar Alignment: Security (SEC08–SEC09 Data Protection, SEC04 Detective Controls)
- Why: AWS documentation strongly recommends creating alarms on `DNSSECInternalFailure` and `DNSSECKeySigningKeysNeedingAction` before enabling DNSSEC. KSK problems (key expiry, permission errors) silently break DNSSEC validation for the entire zone — resolvers performing DNSSEC validation will return SERVFAIL for the zone, making the domain unreachable for all validating clients. AWS's instruction is "Create the alarms BEFORE enabling DNSSEC."
- AWS Services: Route 53 (DNSSEC signing, KMS CMK), CloudWatch (alarms), AWS KMS (ECC_NIST_P256 CMK in us-east-1)
- Architecture Decision:
  - CloudWatch namespace: `AWS/Route53`; metrics must be queried in us-east-1 (published every 4 hours)
  - Alarm 1: `DNSSECInternalFailure` ≥ 1 (any zone in INTERNAL_FAILURE state)
  - Alarm 2: `DNSSECKeySigningKeysNeedingAction` ≥ 1 (any KSK in ACTION_NEEDED state)
  - Alarm 3 (optional): `DNSSECKeySigningKeyMaxNeedingActionAge` > 0 (time since KSK entered ACTION_NEEDED)
  - Alarm 4 (optional): `DNSSECKeySigningKeyAge` — monitor KSK age for rotation planning
  - KMS key: asymmetric, ECC_NIST_P256, Region MUST be us-east-1; key policy must grant `dnssec-route53.amazonaws.com` permissions to `kms:DescribeKey`, `kms:GetPublicKey`, `kms:Sign`, `kms:CreateGrant`
  - Enable confused deputy protection in key policy (see Security Architecture section)
  - Three-step enable process: (1) prepare zone (lower TTLs, enable query logging), (2) enable signing via API, (3) establish chain of trust by adding DS record to parent zone
- Verification:
  - `aws cloudwatch describe-alarms --alarm-name-prefix DNSSEC --region us-east-1`
  - `aws --region us-east-1 route53 get-dnssec --hosted-zone-id ZONE_ID`
  - `aws --region us-east-1 route53 list-key-signing-keys --hosted-zone-id ZONE_ID`
- Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/monitoring-hosted-zones-with-cloudwatch.html (2026-08-31)

**4. Enable Route 53 Resolver DNS Firewall for All VPCs Handling Sensitive Workloads** 🟢
- Pillar Alignment: Security (SEC05 Infrastructure Protection, SEC10 Incident Response)
- Why: DNS tunneling is a documented exfiltration technique that uses DNS queries to bypass network egress controls. Route 53 VPC Resolver DNS Firewall filters outbound DNS queries from VPC resources before they are resolved, enabling block/allow/alert actions. AWS Well-Architected SEC05 cites DNS Firewall explicitly as an infrastructure protection control. DNS Firewall Advanced (GA November 2024) adds signature-based detection of DGA, DNS tunneling, and Dictionary DGA threats.
- AWS Services: Route 53 DNS Firewall, Route 53 VPC Resolver, AWS Firewall Manager (org-wide), AWS RAM (rule group sharing), Security Hub (DNS Firewall Advanced findings)
- Architecture Decision:
  - Choose strategy: deny-listing (allow all, block known-bad) for lower operational burden; allow-listing (block all, allow trusted) for high-security environments
  - Create rule groups with rules referencing domain lists; associate rule groups with VPCs
  - Use AWS Managed domain lists (Foundational Rules) as baseline; supplement with custom domain lists for organization-specific allows/blocks
  - Enable DNS Firewall Advanced for DGA/tunneling detection (confidence threshold: High recommended to minimize false positives)
  - Use AWS Firewall Manager for organization-wide rule group enforcement
  - Share rule groups across accounts via AWS RAM (single management point)
  - False positive handling: identify blocking rule from VPC Resolver logs → create ALLOW rule with lower priority number
  - Maximum 5 rule groups per VPC per account per Region (non-adjustable)
- Verification:
  - `aws route53resolver list-firewall-rule-group-associations --region REGION`
  - Confirm each sensitive VPC has at least one rule group associated
  - Check VPC Resolver query logs for DNS Firewall action fields (BLOCK/ALLOW/ALERT)
- Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-dns-firewall-rule-groups.html (2026-08-31)

**5. Enable Query Logging for All Public Hosted Zones and VPC Resolver** 🟢
- Pillar Alignment: Security (SEC04 Detective Controls), Operational Excellence
- Why: Query logging is the foundational detective control for DNS. AWS Well-Architected SEC04 mandates detective controls. Public zone query logs capture: query timestamp, hosted zone ID, query name/type, response code, edge location, resolver IP, EDNS client subnet. VPC Resolver query logs capture: per-query data for all VPC resources including on-premises via endpoints, and DNS Firewall rule match events (including BLOCK/ALERT actions).
- AWS Services: Route 53 (query logging), CloudWatch Logs (public zone — must be in us-east-1), S3/Kinesis Data Firehose/CloudWatch Logs (VPC Resolver — choose one per configuration)
- Architecture Decision:
  - Public hosted zone query logging: log group MUST be in us-east-1; one stream per edge location per hosted zone; no Route 53 charge, CloudWatch Logs charges apply
  - VPC Resolver query logging: VPC Resolver caches responses — only unique (non-cached) queries logged; choose destination based on use case:
    - CloudWatch Logs: real-time alerting and dashboards
    - S3 + Athena: long-term retention and ad hoc analysis (lower cost)
    - Kinesis Data Firehose: streaming to SIEM
  - Global Resolver (if used): centralized query logging in OCSF v1.2.0 format; destinations: S3, CloudWatch Logs
  - Maximum 20 query log configurations per Region (VPC Resolver); 100 VPC associations per configuration
- Verification:
  - `aws route53 list-query-logging-configs --hosted-zone-id ZONE_ID`
  - `aws route53resolver list-resolver-query-log-configs --region REGION`
  - Verify log group region is us-east-1 for public zones
- Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/query-logs.html (2026-08-31)

**6. Use ARC Routing Controls (Data Plane) for DR Failover, Not ChangeResourceRecordSets (Control Plane)** 🟢
- Pillar Alignment: Reliability (REL11-BP04)
- Why: REL11-BP04 explicitly states Route 53 data plane answers DNS and health checks at 100% availability SLA; "do NOT rely on control plane for recovery." ChangeResourceRecordSets is a control plane API routed through us-east-1 — the exact Region most likely to be impaired during a large-scale incident that triggers DR. ARC Routing Controls operate on the ARC data plane (5 Regional cluster endpoints), making failover decisions achievable even during us-east-1 impairment.
- AWS Services: Application Recovery Controller (routing controls, safety rules), Route 53 (health checks acting as routing control switches), ARC (cluster, Region switch)
- Architecture Decision:
  - Pre-create ARC routing controls for each endpoint/Region pair
  - Associate each routing control with a Route 53 health check (on/off switch — not an actual health monitor)
  - Configure Failover routing policy records with health checks tied to routing controls
  - Configure safety rules: assertion rules (at least one routing control in a set stays ON) to prevent fail-open; gating rules for master switch control
  - For automated DR: use ARC Region switch plans (orchestrates routing controls across accounts/Regions)
  - Store ARC cluster endpoint IPs and DR IAM credentials in on-premises physical safe or virtual vault
  - Weighted routing changes (control plane) = unreliable during regional impairments; avoid for DR
- Verification:
  - `aws route53-recovery-control-config list-routing-controls --control-panel-arn ARN`
  - `aws route53-recovery-cluster get-routing-control-state --routing-control-arn ARN`
  - Verify safety rules configured on all routing control sets
- Source: https://docs.aws.amazon.com/r53recovery/latest/dg/what-is-route53-recovery.html (2026-08-31)

---

### ⚠️ Architectural Decisions

**Decision 1: Route 53 vs Global Accelerator for Multi-Region Traffic Management**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Route 53 DNS routing | Route 53 (latency, failover, weighted policies) | Rich routing semantics (geo, latency, weighted, geoproximity, failover) | TTL caching extends effective RTO; no static IPs | Web apps needing geographic, latency, or weighted routing; cost-conscious workloads; DNS-based traffic management |
  | Global Accelerator | AWS Global Accelerator | Consistent anycast IPs; network-layer (non-DNS) routing; AWS backbone ingress; no TTL sensitivity | Simpler traffic policy (% traffic dial only); higher baseline cost | UDP/TCP non-HTTP workloads; latency-sensitive gaming/IoT; fixed IP requirements (allowlisting); true sub-second failover without TTL |

- Cost Profile: Route 53 alias queries to AWS resources are free; latency/geo queries $0.60–$0.80/million. Global Accelerator charges per accelerator plus data transfer premium. For high-volume web traffic, Route 53 is typically lower cost.
- Lock-in Assessment: Route 53 routing policies are AWS-proprietary; migrating to another DNS provider requires recreating routing logic. Global Accelerator static IPs must be retired on migration. Both have significant operational lock-in.
- Architect Instruction: "Ask whether the application requires sub-second failover without TTL delay AND static IPs — when yes for both, use Global Accelerator. Otherwise Route 53 with ARC routing controls and low TTLs delivers sufficient reliability at lower cost."
- Source: https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html (2026-08-31)

**Decision 2: Active-Active vs Active-Passive Multi-Region Architecture**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Active-Active | Route 53 Latency/Weighted/Geolocation routing + health checks | RTO (near-zero for infrastructure failure); capacity utilization; user latency | Cost (full multi-region infrastructure); data consistency complexity; data corruption RTO still > 0 | High-traffic web apps; global user base; RPO near-zero requirement; budget allows full multi-region |
  | Active-Passive (warm standby) | Route 53 Failover policy + health checks + ARC | Cost (scaled-down standby); simpler data model | RTO minutes (scale-out needed); standby capacity risk under traffic spike | Internal apps; regulated workloads with defined RTO minutes; limited budget for DR |
  | Active-Passive (pilot light) | Route 53 Failover policy + health checks + ARC | Cost (only data infra running); simplest standby | RTO tens of minutes (provision + start app servers); RPO dependent on replication lag | Workloads with RTO tolerance of 15–60 minutes; startup budget constraints |

- Cost Profile: Active-Active = highest (double infrastructure); warm standby = medium (scaled-down second Region); pilot light = low-medium (data infrastructure only).
- Lock-in Assessment: Route 53 Failover and ARC routing controls are AWS-specific; the multi-region pattern itself is provider-agnostic. Data replication services (Aurora Global, DynamoDB global tables) create additional lock-in.
- Architect Instruction: "Ask the business RTO/RPO requirement first. If RTO < 15 minutes, recommend active-active or warm standby with ARC routing controls. If RTO 15–60 minutes, pilot light with ARC is viable. If RTO hours, backup-and-restore with Route 53 record update post-recovery."
- Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-failover-types.html (2026-08-31)

**Decision 3: DNS Firewall Deny-List vs Allow-List Strategy**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Deny-listing | Route 53 DNS Firewall (BLOCK known-bad, ALLOW rest) | Operational simplicity; developer productivity; lower false positive rate | Security posture (allows unlisted domains by default) | General-purpose VPCs; internal tooling; workloads with broad internet access needs |
  | Allow-listing | Route 53 DNS Firewall (BLOCK all except trusted domains) | Strictest security posture; DNS exfiltration prevention | High operational overhead (all new domains require allow rule); developer friction | High-security environments; PCI/HIPAA workloads; VPCs with defined external access patterns |

- Cost Profile: DNS Firewall pricing is per rule group association per VPC-hour (not per query). Both strategies have similar costs; allow-listing may require more rules and custom domain lists.
- Lock-in Assessment: DNS Firewall rule groups are AWS-specific; migration to another provider requires recreating domain lists and rules.
- Architect Instruction: "Ask the security classification of the workload and the set of external domains required. If external domain access is bounded and well-known, allow-listing provides stronger protection. If the workload has broad external dependencies (package managers, third-party APIs), start with deny-listing plus AWS Managed domain lists and tighten over time."
- Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-dns-firewall-domain-lists.html (2026-08-31)

**Decision 4: Routing Policy Selection for Web Application Traffic Distribution**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Simple | Route 53 Simple routing | Simplicity; lowest cost | No health checking on individual values; no traffic shaping | Single-resource endpoints; dev/test environments |
  | Weighted | Route 53 Weighted routing | Gradual traffic shifting (blue/green, canary) | Requires managing weights across records | A/B testing; phased deployments; active-passive standby (weight=0) |
  | Latency-based | Route 53 Latency routing | User-perceived latency reduction | Higher query cost ($0.60/million); latency based on resolver location, not user location | Global web apps with multiple regional deployments |
  | Failover | Route 53 Failover routing | Active-passive DR; clear primary/secondary | Single active endpoint only (Active-passive only) | DR patterns requiring hard primary/secondary designation |
  | Geolocation | Route 53 Geolocation routing | Geographic compliance; content localization | Requires default record for unmapped IPs; $0.70/million | Legal/regulatory geographic data residency; localized content delivery |
  | IP-based | Route 53 IP-based routing | CIDR-specific routing without inferring location | Public zones only; complex CIDR management | ISP-level routing; enterprise network-specific endpoints |
  | Multivalue | Route 53 Multivalue routing | Client-side load balancing (up to 8 healthy records returned) | Not a load balancer substitute; max 8 values | Simple load distribution without ALB; small sets of equivalent endpoints |
  | Geoproximity | Route 53 Geoproximity (Traffic Flow required) | Physical proximity with bias control | Requires Traffic Flow (visual editor); limited to 30 records | Shifting traffic between regions by adjusting bias without fixed thresholds |

- Cost Profile: Simple = lowest; Weighted/Failover/Multivalue/IP-based = standard ($0.40/million); Latency = $0.60/million; Geolocation/Geoproximity = $0.70/million.
- Lock-in Assessment: All routing policies are Route 53-specific; the underlying patterns (weighted, latency, geo) exist in other DNS providers with different APIs.
- Architect Instruction: "Ask what the routing goal is: lowest latency (Latency-based), geographic compliance (Geolocation), gradual rollout (Weighted), DR failover (Failover), or physical proximity control (Geoproximity). For complex multi-region patterns, combine: Latency alias → Weighted → individual resources."
- Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-policy.html (2026-08-31)

**Decision 5: DR Tier Selection — Cost vs RTO/RPO**
- Options:

  | Option | AWS Services | RTO | RPO | Cost |
  |--------|-------------|-----|-----|------|
  | Backup and Restore | Route 53 (record update post-recovery), S3, CloudFormation | Hours | Hours–days | Lowest |
  | Pilot Light | Route 53 Failover + ARC, Aurora Global/DynamoDB global tables | Tens of minutes | Minutes–near-zero | Low-medium |
  | Warm Standby | Route 53 Failover + ARC, Auto Scaling, Aurora Global | Minutes | Near-zero | Medium |
  | Multi-Site Active/Active | Route 53 Latency/Weighted + health checks + ARC, full multi-region | Near-zero (infra failure) | Near-zero (infra failure) | Highest |

- Cost Profile: Cost scales with standby infrastructure. Backup/Restore: storage + backup costs only. Active/Active: near 2x infrastructure cost.
- Lock-in Assessment: ARC, Aurora Global, DynamoDB global tables are AWS-specific. Higher tiers introduce more service-specific lock-in.
- Architect Instruction: "Ask the documented RTO/RPO business requirement. Translate to tier: RTO hours → Backup/Restore; RTO tens of minutes → Pilot Light; RTO minutes → Warm Standby; RTO near-zero → Active/Active. Validate cost of each tier against the business value of reduced RTO/RPO before recommending."
- Source: https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html (2026-08-31)

**Decision 6: DNSSEC Adoption for Public Hosted Zones**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Enable DNSSEC | Route 53 + KMS (ECC_NIST_P256, us-east-1) | DNS response integrity; protection against cache poisoning | Operational complexity (KSK rotation, DS record management); max TTL 1 week; KMS costs; multi-vendor name servers incompatible | High-security domains; financial services; government; domains handling sensitive data; compliance requirements |
  | Do not enable DNSSEC | — | Operational simplicity; no TTL constraint; multi-vendor name servers supported | No DNS integrity protection; susceptible to cache poisoning | General-purpose web apps; domains without strict DNS integrity requirements |

- Cost Profile: KMS charges apply for KSK operations ($0.03/10,000 signature requests). DNSSEC enforces max 1 week TTL, potentially increasing DNS query volume and cost.
- Lock-in Assessment: DNSSEC signing is portable (DS record standard); however KSK management via AWS KMS creates operational dependency.
- Architect Instruction: "Ask whether the organization has compliance requirements mandating DNSSEC (FedRAMP, DoD, financial regulation) or whether the domain handles credentials/financial data. If yes, enable DNSSEC — but confirm KMS key setup in us-east-1 and pre-configure CloudWatch alarms first."
- Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-configuring-dnssec.html (2026-08-31)

**Decision 7: Route 53 Global Resolver vs VPC Resolver for External Client DNS**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Route 53 Global Resolver | Route 53 Global Resolver (GA 2026-03-09) | Internet-reachable; DoH/DoT support; no VPN required; token-based auth; private zone access from anywhere; advanced threat protection | Cost (charges apply after 30-day trial); newer service (less operational history) | Remote workers; branch offices; clients needing private zone access without VPN; DoH/DoT encrypted DNS requirement |
  | VPC Resolver + Inbound/Outbound Endpoints | Route 53 VPC Resolver + Resolver endpoints + DX/VPN | Established service; integrates with Direct Connect/VPN architecture | Requires network connectivity (DX or VPN); higher setup complexity for on-premises | On-premises servers with existing DX/VPN connectivity; workloads where all DNS clients are network-connected |

- Cost Profile: Global Resolver: 30-day free trial then charged. VPC Resolver endpoints: $0.125/ENI/hour + $0.40/million queries. For large query volumes with existing DX/VPN, endpoints may be more cost-effective.
- Lock-in Assessment: Global Resolver is AWS-specific. Resolver endpoints with forwarding rules are conceptually portable (other DNS providers offer similar split-DNS).
- Architect Instruction: "Ask whether the external clients have existing network connectivity (DX/VPN) to AWS. If yes and connectivity is stable, VPC Resolver endpoints are simpler. If clients are remote workers, mobile, or branch offices without network connectivity, Global Resolver with DoH/DoT is the correct choice."
- Source: https://aws.amazon.com/about-aws/whats-new/2026/03/amazon-route-53-global-resolver (2026-08-31)

---

### 🚫 Anti-Patterns

**Anti-Pattern 1: CNAME Record at Zone Apex**
- Risk Level: CRITICAL
- Why: DNS protocol (RFC 1034) prohibits CNAME at the zone apex because the apex must contain NS and SOA records, and CNAME cannot coexist with other record types at the same name. Attempting this breaks zone delegation and results in DNS resolution failure for the root domain. This violates Reliability pillar — the domain becomes unreachable for clients requesting the zone apex directly.
- Wrong:
  - `example.com. CNAME www.example.com.` (invalid — CNAME at zone apex)
  - `example.com. CNAME d1234.cloudfront.net.` (invalid — CNAME at zone apex)
  - Creating a CNAME for `example.com` in Route 53 returns an error; attempting workarounds via raw API calls produces malformed zones
- Correct:
  - `example.com. A ALIAS → d1234.cloudfront.net` (Route 53 Alias record — valid at zone apex)
  - `example.com. AAAA ALIAS → d1234.cloudfront.net` (for IPv6)
  - Both A and AAAA Alias records when CloudFront IPv6 is enabled
- Detection: `aws route53 list-resource-record-sets --hosted-zone-id ZONE_ID --query "ResourceRecordSets[?Name=='example.com.' && Type=='CNAME']"` — this should return empty for zone apex; if non-empty, the zone is misconfigured
- Impact: Outage (root domain unreachable); zone delegation breaks
- Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resource-record-sets-choosing-alias-non-alias.html (2026-08-31)

**Anti-Pattern 2: Relying on Route 53 Control Plane (ChangeResourceRecordSets) for DR Failover**
- Risk Level: CRITICAL
- Why: REL11-BP04 explicitly states "do NOT rely on control plane for recovery." ChangeResourceRecordSets is a control plane API routed through us-east-1. A regional impairment in us-east-1 (the most likely trigger for a multi-Region DR event) can make this API unavailable — precisely when you need to execute failover. This directly violates Reliability pillar by making recovery dependent on the component most likely to be impaired during a disaster.
- Wrong:
  - DR runbook that executes `aws route53 change-resource-record-sets` to switch traffic from primary to secondary Region
  - Lambda-based automation that calls ChangeResourceRecordSets on CloudWatch alarm
  - Weighted routing weight changes (from 100/0 to 0/100) via console or API as the failover mechanism
- Correct:
  - Pre-configure ARC Routing Controls with associated Route 53 health checks (on/off switches)
  - DR runbook calls `aws route53-recovery-cluster update-routing-control-state` (ARC data plane — 5 Regional cluster endpoints, extremely reliable)
  - ARC Region switch plans automate the routing control state changes with safety rules
  - Store ARC cluster endpoint IPs and DR IAM credentials offline (physical safe or virtual vault)
- Detection: Review DR runbooks for any use of `change-resource-record-sets` or `route53 change-*` as the primary failover mechanism. Check whether ARC routing controls exist for all critical endpoints.
- Impact: Outage (failover cannot be executed during regional impairment — when DR is most needed)
- Source: https://docs.aws.amazon.com/r53recovery/latest/dg/what-is-route53-recovery.html (2026-08-31)

**Anti-Pattern 3: High TTL on Failover-Capable Records**
- Risk Level: HIGH
- Why: TTL is the primary determinant of effective DNS failover time from the client perspective. After Route 53 detects an endpoint as unhealthy and stops returning its address, clients with cached DNS answers continue routing to the failed endpoint until their cached TTL expires. A 3600-second TTL means clients can route to a failed endpoint for up to one hour after Route 53 has detected the failure — extending the actual RTO far beyond what health check intervals suggest. Violates Reliability pillar RTO expectations.
- Wrong:
  - Failover routing records with TTL = 300–3600 seconds
  - Using default TTL values for records that are also subject to health-check-based routing
  - Alias record TTLs are Route 53-managed, but CNAME/A records for secondary resources can have architect-set TTLs
- Correct:
  - Set TTL to 60–120 seconds for all records subject to health-check-based routing
  - Pre-lower TTLs at least 2x the current TTL value before planned failover events (e.g., before scheduled DR tests)
  - Accept that some non-compliant resolvers may cache beyond TTL [UNVERIFIED: explicit AWS architectural caveat; implicitly acknowledged in Global Accelerator comparison docs]
  - For sub-TTL failover: use AWS Global Accelerator (not DNS-based) for the endpoint
- Detection: `aws route53 list-resource-record-sets --hosted-zone-id ZONE_ID --query "ResourceRecordSets[?HealthCheckId && TTL > '120']"`
- Impact: Extended outage duration (RTO extended by TTL caching); SLA violations
- Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-failover-types.html (2026-08-31)

**Anti-Pattern 4: Querying Private Hosted Zone Names From Outside Associated VPCs and Expecting Private Records**
- Risk Level: HIGH
- Why: Private hosted zones are resolvable only from DNS queries originating within explicitly associated VPCs. Queries from the internet, from non-associated VPCs, or from on-premises systems without forwarding rules configured will either fall through to public DNS (returning the public record or NXDOMAIN) rather than the private record. This creates a false security assumption — architects may believe private DNS provides a security boundary when it does not for unassociated clients. Violates Security pillar (SEC01).
- Wrong:
  - Assuming `api.internal.example.com` in a private hosted zone is inaccessible from the internet (it is — but NXDOMAIN or public record is returned, not an error revealing internal structure)
  - On-premises systems querying VPC private zone names without configuring inbound Resolver endpoints and forwarding rules
  - Expecting that creating a private hosted zone automatically prevents the domain from being resolved externally
- Correct:
  - Explicitly associate private hosted zones with all VPCs that need private resolution
  - For on-premises access: configure inbound Resolver endpoints in the VPC; configure on-premises DNS forwarding rules to send the private domain to inbound endpoint IPs
  - For cross-account: use Route 53 Profiles or AWS RAM to share private hosted zones; explicitly associate with each target VPC
  - Verify association: `aws route53 list-vpc-association-authorizations --hosted-zone-id ZONE_ID`
- Detection: `aws route53 get-hosted-zone --id ZONE_ID` — verify `VPCs` list includes all expected VPCs; query from outside associated VPC and confirm behavior
- Impact: Incorrect routing (internal services unreachable from on-premises); false security posture (expecting private DNS to hide internal addresses when it does not)
- Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/hosted-zones-private.html (2026-08-31)

**Anti-Pattern 5: Multi-Vendor Name Servers With DNSSEC Signing**
- Risk Level: HIGH
- Why: Route 53 DNSSEC signing is incompatible with multi-vendor name server configurations. When a zone is signed, all authoritative name servers must return identical DNSSEC-signed responses. Multi-vendor configurations (Route 53 + another DNS provider serving the same zone) create inconsistent DNSSEC responses, causing SERVFAIL for DNSSEC-validating resolvers — which means the entire zone becomes unreachable for clients performing DNSSEC validation.
- Wrong:
  - Enabling DNSSEC signing on a Route 53 hosted zone that also has name servers from another provider (e.g., Cloudflare, Azure DNS) added at the domain registrar
  - Expecting DNSSEC to work when NS record delegation includes both Route 53 name servers and third-party name servers
- Correct:
  - Enable DNSSEC only on zones served exclusively by Route 53 name servers
  - If multi-vendor DNS is required for resilience, do not enable DNSSEC (choose one capability)
  - For DNS resilience without multi-vendor name servers: use Route 53's 200+ PoP data plane and 100% availability SLA; ARC routing controls for control plane DR
- Detection: Check NS records at domain registrar; confirm only Route 53 name servers (*.awsdns-*.com/net/org/co.uk) are delegated before enabling DNSSEC
- Impact: Outage (zone unreachable for all DNSSEC-validating resolvers after signing)
- Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-configuring-dnssec.html (2026-08-31)

**Anti-Pattern 6: Using the Same Domain Name as the Health-Checked Endpoint for the Health Check Domain Name Spec**
- Risk Level: MEDIUM
- Why: Route 53 resolves the health check domain name using an A record (IPv4 only). If the health check's domain name spec is the same domain as the record being health-checked, and that record is unhealthy, Route 53 may use a cached or stale IP to attempt the health check — creating a circular dependency. AWS documentation explicitly advises: "Do NOT use the same domain as the records being health-checked" as the domain name in the health check configuration.
- Wrong:
  - Health check domain name: `api.example.com` (the same record being health-checked)
  - Health check domain name: same as the primary record in a Failover routing policy
- Correct:
  - Health check domain name: specify the actual endpoint DNS name or IP address directly
  - For AWS resources (ALB, CloudFront): use alias records with `Evaluate Target Health = Yes` rather than endpoint health checks with domain name resolution
  - For EC2 instances: specify the instance's IP address directly in the health check
- Detection: Compare health check domain name configuration against the record set names they are associated with; flag any matches
- Impact: False health check results; incorrect failover behavior
- Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/health-checks-creating-values.html (2026-08-31)

## Cloud-Native Design Patterns

**Pattern 1: Canonical Zone Apex + www Routing via CloudFront Alias**
- Category: Resilience, Scalability
- Problem: Web application must be reachable at both `example.com` (zone apex) and `www.example.com` without DNS protocol violations, while serving HTTPS with ACM certificate and maintaining CloudFront CDN benefits.
- Solution on AWS:
  - Public hosted zone for `example.com`
  - CloudFront distribution with `example.com` and `www.example.com` as Alternate Domain Names (CNAME)
  - ACM certificate in us-east-1 (required for CloudFront) with DNS validation: one-click "Create records in Route 53" inserts underscore-prefixed CNAME automatically [UNVERIFIED: us-east-1 ACM requirement not confirmed in fetched pages — consistent with all CloudFront docs but not directly verified]
  - Route 53 Alias A + AAAA records at zone apex pointing to CloudFront distribution
  - Route 53 Alias A + AAAA records for `www.example.com` pointing to same CloudFront distribution
  - ACM CNAME validation record remains in zone permanently for auto-renewal
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Cost | Alias queries to CloudFront are free; HTTPS via ACM is free | CloudFront distribution cost; ACM KMS if using CMK |
  | Simplicity | Single CloudFront distribution serves both hostnames | ACM CNAME records must remain; CloudFront alternate domain name must be set BEFORE alias record creation |
  | HTTPS enforcement | CloudFront handles TLS termination; HTTP→HTTPS redirect configurable | ACM cert rotation is automatic as long as CNAME stays and cert is in use |
  | IPv6 | ALB console auto-prepends dualstack.; create both A and AAAA alias records | Must remember to create both A and AAAA records when IPv6 enabled |

- Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-to-cloudfront-distribution.html (2026-08-31)

**Pattern 2: www-to-Apex HTTPS Redirect**
- Category: Communication, Resilience
- Problem: Users accessing `www.example.com` must be redirected to `example.com` (or vice versa) over HTTPS, without exposing a non-TLS redirect endpoint.
- Solution on AWS:
  - Two S3 buckets: `www.example.com` (content) and `example.com` (redirect only — configured to redirect all requests to `www.example.com`)
  - Two CloudFront distributions: one for `www.example.com` (serving content from S3/ALB), one for `example.com` (serving redirects from S3 redirect bucket)
  - Two ACM certificates (or one wildcard cert) for each distribution (both in us-east-1)
  - Route 53: Alias A for `www.example.com` → first CloudFront distribution; Alias A for `example.com` (zone apex) → second CloudFront distribution
  - All redirect traffic served via CloudFront + ACM → HTTPS throughout, no HTTP redirect exposure
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Security | HTTPS redirect without any HTTP exposure | Two CloudFront distributions required |
  | Cost | S3 redirect bucket has minimal cost; alias queries free | Marginal CloudFront cost for redirect distribution |
  | User Experience | Seamless HTTPS redirect with correct HTTP 301/302 | One additional DNS round-trip for redirect |

- Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/getting-started-cloudfront-overview.html (2026-08-31)

**Pattern 3: Split-Horizon DNS (Public + Private Hosted Zone)**
- Category: Communication, Resilience
- Problem: Same domain name must resolve to different addresses for internet clients (public CloudFront endpoint) and VPC clients (internal ALB or private endpoint), without separate DNS infrastructure.
- Solution on AWS:
  - Create public hosted zone for `example.com`: `api.example.com` A ALIAS → CloudFront distribution (internet clients)
  - Create private hosted zone for `example.com` (same domain name): `api.example.com` A → internal ALB DNS name via alias, or direct private IP
  - Associate private hosted zone explicitly with all VPCs that need private resolution
  - VPC Resolver automatically prefers private hosted zone records for associated VPCs; internet clients receive public zone records
  - Records in public and private zones are entirely independent — creating one does not affect the other
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Architecture | Single domain name, two resolution paths — no split DNS management complexity of maintaining two different domain names | Two hosted zones to maintain; records must be synchronized manually if needed |
  | Security | VPC clients never route through internet for internal services | Private hosted zone must be explicitly associated with EACH VPC; not automatic |
  | Scalability | Route 53 Profiles scale private zone association to hundreds of VPCs | Profile limit: 5 per account per Region (adjustable) |

- Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/hosted-zones-private.html (2026-08-31)

**Pattern 4: Hybrid DNS — On-Premises to VPC Private Zone Resolution**
- Category: Migration, Communication
- Problem: On-premises servers need to resolve VPC-internal DNS names (private hosted zones, EC2 DNS names) without managing a separate DNS server.
- Solution on AWS:
  - Create inbound Resolver endpoint in VPC: 2+ ENIs (one per AZ recommended) in VPC subnets; security group permits UDP/TCP port 53 from on-premises CIDR
  - Configure on-premises DNS server (Windows DNS, BIND, Unbound) forwarding rules: `example.com` → inbound endpoint IP addresses
  - Connectivity: AWS Direct Connect (preferred for reliability) or Site-to-Site VPN
  - On-premises queries for `api.internal.example.com` → on-premises DNS → inbound endpoint → VPC Resolver → private hosted zone → response to on-premises DNS → response to on-premises client
  - For VPC-to-on-premises resolution: create outbound Resolver endpoint + forwarding rule for on-premises domains → target IPs of on-premises DNS resolvers
  - Share forwarding rules via AWS RAM for multi-account environments; or use Route 53 Profiles
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Availability | Inbound endpoint redundancy across AZs | Resolver endpoint: $0.125/ENI/hour; $0.40/million queries |
  | Simplicity | No separate DNS server needed in AWS | On-premises DNS server config change required; DX/VPN prerequisite |
  | Scalability | Up to 10,000 queries/second per IP per endpoint (may drop with connection tracking) | UDP throughput limit; increase IPs per endpoint for higher load |

- Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-getting-started.html (2026-08-31)

**Pattern 5: Multi-Region Latency Routing Tree (Latency Alias → Weighted → Resource)**
- Category: Resilience, Scalability
- Problem: Multi-region web application must route users to the lowest-latency Region, with weighted distribution across multiple resources within each Region, while maintaining health-check-based failover at each level.
- Solution on AWS:
  - Tier 1 (top): Latency alias records per Region — `api.example.com` Latency A ALIAS → Region-specific weighted record set (no direct resource target)
  - Tier 2 (middle): Weighted routing records per Region — weight distributes traffic across resources (e.g., 50/50 blue/green, or 100/0 with zero-weight standby)
  - Tier 3 (bottom): Individual resource records with health checks (endpoint or alias with Evaluate Target Health = Yes)
  - Health check propagation: when all weighted records in a Region become unhealthy → latency alias for that Region becomes unhealthy → Route 53 routes to next-best Region automatically
  - Zero-weight standby: weighted record with weight=0 and health check; serves traffic only when all nonzero-weight records in the Region are unhealthy (last resort within Region before inter-Region failover)
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Resilience | Automatic multi-tier failover without ARC (sufficient for non-DR routing) | DNS query cost higher (latency queries $0.60/million) |
  | Flexibility | Blue/green deployments at weighted tier; geographic optimization at latency tier | Complex record tree to manage; 3 tiers of record updates for resource changes |
  | Observability | Each tier independently health-checkable | More health checks = higher health check cost |

- Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-failover-configuring.html (2026-08-31)

## Security Architecture

**DNSSEC Signing Pipeline**
- AWS Services: Route 53 (hosted zone DNSSEC), AWS KMS (ECC_NIST_P256 CMK, us-east-1 only), CloudWatch (DNSSEC alarms), AWS IAM
- Architecture:
  - KMS CMK: asymmetric, ECC_NIST_P256, Region us-east-1; key policy grants `dnssec-route53.amazonaws.com` permissions: `kms:DescribeKey`, `kms:GetPublicKey`, `kms:Sign`, `kms:CreateGrant`
  - Confused deputy protection in key policy:
    ```json
    "Condition": {
        "StringEquals": { "aws:SourceAccount": "111122223333" },
        "ArnEquals": { "aws:SourceArn": "arn:aws:route53:::hostedzone/HOSTED_ZONE_ID" }
    }
    ```
  - KSK: based on CMK; operator manages; Route 53 uses it to sign DNSKEY records
  - ZSK: fully Route 53-managed; used to sign all other zone records
  - Maximum 2 KSKs per hosted zone (for KSK rotation with zero downtime)
  - DNSSEC enforces maximum TTL of 1 week on all zone records
  - Three-step enable: (1) prepare zone (lower TTLs to ≤1 hour, enable query logging, lower SOA TTL + minimum); (2) `aws --region us-east-1 route53 create-key-signing-key` then `enable-hosted-zone-dnssec`; verify GetChange status = INSYNC; monitor 2 weeks; (3) add DS record to parent zone (algorithm ECDSAP256SHA256, type 13; DS TTL recommended 300s for faster rollback)
  - DS record value retrieval: `aws --region us-east-1 route53 get-dnssec --hosted-zone-id ZONE_ID`
  - Pre-create CloudWatch alarms (us-east-1, every 4 hours): `DNSSECInternalFailure` ≥ 1; `DNSSECKeySigningKeysNeedingAction` ≥ 1
- Compliance Alignment: SEC08–SEC09 Data Protection (AWS Well-Architected Security Pillar, updated November 6, 2024); FedRAMP DNS integrity requirements; NIST SP 800-81-2 DNSSEC
- Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-configuring-dnssec-enable-signing.html (2026-08-31)

**DNS Firewall Layered Defense (VPC Resolver)**
- AWS Services: Route 53 DNS Firewall, Route 53 VPC Resolver, AWS Managed Domain Lists, AWS RAM, AWS Firewall Manager, Security Hub
- Architecture:
  - Rule groups contain rules; rules reference domain lists; domain lists contain domain names
  - Rule evaluation order: lower priority number evaluated first
  - Actions: BLOCK (return REFUSED or NODATA/NXDOMAIN), ALLOW (explicitly permit), ALERT (log but allow)
  - To allow a domain blocked by managed list: create ALLOW rule with priority number lower (higher priority) than the blocking rule
  - AWS Managed domain lists (Foundational Rules): AWS-maintained threat intelligence for malware, botnet C2, etc. [UNVERIFIED: specific list identifiers not confirmed in fetched pages]
  - Custom domain lists: up to 100,000 domains per list; reusable across rules and VPCs; updates auto-propagate to all rules referencing the list
  - One rule group can be associated with multiple VPCs; shareable across accounts via AWS RAM
  - Firewall Manager: enforces mandatory rule group associations across organization accounts
  - DNS Firewall Advanced (GA November 2024): signature-based threat detection; threat types:
    - DGA (Domain Generation Algorithms): randomized domain names for malware C2
    - DNS Tunneling: data exfiltration via DNS queries/responses
    - Dictionary DGA: DGA variant using dictionary words to evade threat intelligence
  - Confidence thresholds: High (fewest false positives) / Medium / Low (most detections)
  - Security Hub integration: DNS Firewall Advanced findings published as Security Hub findings
  - False positive remediation: identify blocking rule from VPC Resolver query logs → create ALLOW rule with lower priority number
- Compliance Alignment: SEC05 Infrastructure Protection; SEC10 Incident Response (AWS Well-Architected Security Pillar, updated November 6, 2024)
- Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/firewall-advanced-protections.html (2026-08-31)

**Query Logging for Detective Controls**
- AWS Services: Route 53 (public zone query logging), Route 53 VPC Resolver (query logging), CloudWatch Logs, Amazon S3, Kinesis Data Firehose, Amazon Athena
- Architecture:
  - Public hosted zone query logging: log group MUST be in us-east-1; one log stream per edge location per hosted zone (`{hosted-zone-id}/{edge-location-ID}`); fields: log format version, query timestamp (ISO 8601 UTC), hosted zone ID, query name, query type, response code, L4 protocol (TCP/UDP), edge location, resolver IP, EDNS client subnet; no Route 53 charge; CloudWatch Logs charges apply
  - VPC Resolver query logging: logs queries from VPC instances + on-premises via inbound endpoint + outbound endpoint + DNS Firewall rule matches (BLOCK/ALLOW/ALERT); only unique (non-cached) queries logged; destination: CloudWatch Logs (real-time) OR S3 (long-term + Athena) OR Kinesis Data Firehose (streaming to SIEM) — choose one per config
  - Global Resolver query logging: OCSF v1.2.0 format; includes: action (Allowed/Denied), query info, client source IP + port, firewall rule ID, DNS view ID, token ID/name, access source CIDR, response code, trace/correlation info; blocked queries return `rcode: REFUSED`; destinations: S3, CloudWatch Logs
  - IAM privilege separation: query logging enable/disable is a zone-owner privilege (not record-owner)
- Compliance Alignment: SEC04 Detective Controls (AWS Well-Architected Security Pillar); SOC 2 audit logging; PCI DSS network monitoring
- Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/query-logs.html (2026-08-31)

**IAM Privilege Separation — Zone Owner vs Record Owner**
- AWS Services: AWS IAM, Route 53
- Architecture:
  - Zone owner permissions: `route53:CreateHostedZone`, `route53:DeleteHostedZone`, `route53:UpdateHostedZoneComment`, DNSSEC settings actions, query logging enable/disable, delegation set management
  - Record owner permissions: `route53:ChangeResourceRecordSets`, traffic policy actions, health check management, `route53:List*`, `route53:Get*` — explicitly NOT zone create/delete, NOT DNSSEC, NOT query logging enable/disable
  - Private hosted zone additional requirements: `ec2:DescribeVpcs`, `ec2:DescribeRegions`
  - Resolver endpoint creation requires: `route53resolver:CreateResolverEndpoint`, `ec2:CreateNetworkInterface`, `ec2:DescribeAvailabilityZones`, `ec2:DescribeNetworkInterfaces`, `ec2:DescribeSecurityGroups`, `ec2:DescribeSubnets`, `ec2:DescribeVpcs`
  - Apply confused deputy protection to KMS key policy for DNSSEC (see DNSSEC section above)
- Compliance Alignment: SEC01–SEC03 IAM (AWS Well-Architected Security Pillar, updated November 6, 2024); principle of least privilege
- Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/access-control-managing-permissions.html (2026-08-31)

## Operational Patterns

**Disaster Recovery Tiers — DNS Routing Perspective**
- RTO/RPO (if applicable): Tier 1 (Backup/Restore): RTO hours, RPO hours–days; Tier 2 (Pilot Light): RTO tens of minutes, RPO minutes–near-zero; Tier 3 (Warm Standby): RTO minutes, RPO near-zero; Tier 4 (Active/Active): RTO near-zero (infra failure), RPO near-zero (infra failure)
- AWS Services: Route 53 (Failover/Weighted/Latency routing policies, health checks), ARC (routing controls, safety rules, Region switch, zonal shift, zonal autoshift, readiness checks), AWS Resilience Hub, Aurora Global, DynamoDB global tables, S3 replication, Auto Scaling
- Cost Profile: Tier 1 = Low (storage + backup); Tier 2 = Low-medium (data infra only); Tier 3 = Medium (scaled-down second Region); Tier 4 = High (full second Region)
- Automation:
  - Tier 2–3: ARC routing controls automate failover trigger; ARC Region switch orchestrates multi-account/Region recovery; manual decision for scaling up compute (pilot light) or validating readiness (all tiers)
  - Tier 4: routing inherent; use ARC Region switch for DR test isolation; AWS Resilience Hub validates RTO/RPO continuously
  - All tiers: DR IAM credentials (long-lived) stored offline; ARC cluster endpoints stored offline; tested regularly (only regularly-tested paths should be trusted)
  - Health check detection time: 10s interval + 1 failure threshold = sub-10s detection; add TTL caching time for effective client-side RTO
- Source: https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html (2026-08-31)

**ARC Routing Controls — Programmatic DR Failover**
- RTO/RPO (if applicable): RTO: time to execute routing control state change (seconds) + TTL caching time (configured per record)
- AWS Services: Application Recovery Controller (routing controls, safety rules, cluster, Region switch), Route 53 (health checks as routing control switches, Failover routing policy records)
- Cost Profile: ARC has separate pricing; routing controls backed by 5 Regional cluster endpoints
- Automation:
  - Pre-configure: routing controls created per endpoint/Region pair; associated Route 53 health checks created; Failover records reference health check IDs; safety rules configured (assertion + gating)
  - Failover execution: `aws route53-recovery-cluster update-routing-control-state --routing-control-arn ARN --routing-control-state On/Off` — operates on ARC data plane (NOT Route 53 control plane)
  - ARC Region switch plans automate sequences of routing control changes with execution blocks; observable and auditable
  - Manual decision: capacity validation in target Region before completing failover; data replication lag assessment
  - Safety rule override: available for emergency scenarios when guardrails must be bypassed
  - Readiness checks: continuous monitoring (not for critical path during active failover; informational for planning)
- Source: https://docs.aws.amazon.com/r53recovery/latest/dg/routing-control.safety-rules.html (2026-08-31)

**Route 53 Accelerated Recovery (Control Plane DR)**
- RTO/RPO (if applicable): Control plane RTO: approximately 60 minutes if us-east-1 is unavailable; data plane RTO: 0 (continues normally)
- AWS Services: Route 53 (Accelerated Recovery, public hosted zones), us-west-2 (failover control plane Region)
- Cost Profile: Additional feature; must be enabled per hosted zone
- Automation:
  - AWS initiates control plane failover automatically on sustained us-east-1 impairment (~60 minutes)
  - Supported APIs during failover: `ChangeResourceRecordSets`, `GetChange`, `GetHostedZone`, `ListResourceRecordSets`, related read/list APIs
  - Not supported during failover: create/delete hosted zones, DNSSEC modifications, AWS PrivateLink
  - "Stranded changes" (submitted during failover) must be resubmitted after control plane restoration
  - Manual decision: choose between Accelerated Recovery (wait up to 60 min, AWS-managed) vs ARC routing controls (data plane, immediate, architect-managed); ARC docs state: use ARC if you cannot wait for AWS to initiate failover
  - Limitations: public hosted zones only; must enable before outage; setup takes hours; zones with feature enabled cannot be deleted without first disabling
- Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/accelerated-recovery.html (2026-08-31)

**ARC Zonal Shift and Autoshift**
- RTO/RPO (if applicable): Zonal shift RTO: minutes (traffic moves to other AZs in same Region); Autoshift: sub-minute (AWS-initiated)
- AWS Services: Application Recovery Controller (zonal shift, zonal autoshift), Route 53 (supporting DNS for shifted resources), ALB, NLB, EKS
- Cost Profile: No additional ARC cost; existing resource costs remain during shift
- Automation:
  - Zonal shift (manual): `aws arc-zonal-shift start-zonal-shift --resource-identifier RESOURCE_ARN --away-from AVAILABILITY_ZONE --expires-in "3 Days"` — specify expiration (max 3 days, extendable)
  - Zonal autoshift: authorize AWS to initiate zonal shift based on internal telemetry (network, EC2, ELB metrics); AWS ends autoshift when telemetry clears
  - Manual decision: zonal shift initiation when AZ impairment detected before AWS telemetry triggers autoshift; expiration extension if AZ remains impaired
- Source: https://docs.aws.amazon.com/r53recovery/latest/dg/what-is-route53-recovery.html (2026-08-31)

**Health Check Monitoring and TTL Management**
- RTO/RPO (if applicable): Detection time: ≥1 × request interval (10s fast, 30s standard); effective client-side RTO: detection time + TTL
- AWS Services: Route 53 (health checks — endpoint, calculated, CloudWatch alarm), CloudWatch (metric streams for alarm-based checks)
- Cost Profile: AWS endpoint health checks: $0.50/month; non-AWS: $0.75/month; HTTPS/string matching/fast interval add-ons: +$1.00/month (AWS) or +$2.00/month (non-AWS); first 50 AWS endpoint checks free for new customers
- Automation:
  - Endpoint health check: Route 53 health checkers probe endpoint; 18% rule determines health status
  - Calculated health check: automates aggregation of N child checks (up to 255 children) without manual evaluation
  - CloudWatch alarm health check: monitors alarm data stream (not alarm state) — proactively detects before CloudWatch transitions to ALARM; `SetAlarmState` API has NO effect on Route 53 health check status
  - ARC Routing Control health checks: on/off switches — must be toggled manually (or via ARC Region switch automation); NOT metric-based
  - Manual decision: health checker region selection (minimum 3 required; removed regions continue checking up to 1 hour); failure threshold (1 for speed, up to 10 for stability)
- Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-failover-determining-health-of-endpoints.html (2026-08-31)

## Reference Architectures

**Reference Architecture 1: Canonical Web Application — Public Hosted Zone + Alias + CloudFront + ACM**
- Context: Public-facing web application requiring global CDN, HTTPS, and zone apex resolution
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | DNS | Route 53 Public Hosted Zone | Authoritative DNS for domain |
  | DNS Records | Alias A + AAAA (zone apex, www) | Route traffic to CloudFront; free; zone apex capable |
  | CDN | Amazon CloudFront | Global content delivery; TLS termination; HTTP→HTTPS redirect |
  | Certificate | ACM (us-east-1) [UNVERIFIED: us-east-1 requirement not confirmed in fetched pages] | HTTPS certificate; auto-renewed via DNS validation CNAME |
  | DNS Validation | Route 53 CNAME record (underscore-prefixed) | ACM certificate domain validation; must remain in zone |
  | Origin (dynamic) | Application Load Balancer | Dynamic content routing to EC2/ECS/Lambda |
  | Origin (static) | Amazon S3 (website endpoint) | Static assets; alias-targetable by Route 53 |
  | Health Checks | ALB (Evaluate Target Health = Yes on alias) | Inherits ALB health; no separate health check needed |

- Key Decisions:
  - CloudFront distribution MUST include custom domain as Alternate Domain Name BEFORE Route 53 alias record is created
  - Enable IPv6 on CloudFront → create BOTH A and AAAA alias records
  - ACM certificate: "Create records in Route 53" button inserts CNAME automatically; CNAME must remain for auto-renewal
  - CNAME chain must be ≤5 CNAMEs for ACM DNS validation; if longer, use email validation
- Scaling Path: S3 origin → CloudFront → ALB (current); ALB → ECS Fargate → Aurora for database tier; Global Aurora for multi-region; ARC routing controls for DR
- Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-to-cloudfront-distribution.html (2026-08-31)

**Reference Architecture 2: Multi-Region Active-Passive DR**
- Context: Web application requiring sub-15-minute RTO with near-zero RPO for a regional failure
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | DNS | Route 53 Failover routing policy | Active-passive record designation |
  | Health Check | Route 53 endpoint or alias health check (Primary) | Detects primary Region failure |
  | DR Control | ARC Routing Controls + safety rules | Programmatic, data-plane failover switch |
  | DR Automation | ARC Region switch plans | Orchestrated multi-Region recovery |
  | Primary compute | ALB + ECS/EC2 (Region A) | Production traffic |
  | Secondary compute | ALB + ECS/EC2 (Region B, scaled down) | Warm standby (pre-deployed, smaller fleet) |
  | Data replication | Aurora Global Database | Near-zero RPO; cross-Region read replica promoted on failover |
  | Readiness | ARC Readiness Checks | Continuous quota/capacity monitoring |
  | Monitoring | AWS Resilience Hub | Continuous RTO/RPO target validation |

- Key Decisions:
  - Failover records: TTL 60–120 seconds (minimize caching extension of RTO)
  - ARC Routing Controls as the failover execution mechanism (data plane, not control plane)
  - Pre-provision compute in secondary Region (warm standby) — ARC Region switch does not guarantee compute capacity
  - Aurora Global: promote secondary Region cluster on failover; DNS update for DB connection string required (separate from Route 53 web traffic routing)
  - DR IAM credentials stored offline with ARC cluster endpoint IPs
  - Regular DR tests using ARC Region switch (validates the recovery path actually works)
- Scaling Path: Warm standby → Active-Active (deploy full fleet in secondary; switch Route 53 from Failover to Latency routing policy); add additional Regions
- Source: https://docs.aws.amazon.com/r53recovery/latest/dg/best-practices.region-switch.html (2026-08-31)

**Reference Architecture 3: Hybrid DNS — On-Premises + VPC Private Zone Resolution**
- Context: Enterprise with existing on-premises infrastructure requiring bidirectional DNS resolution with AWS VPC private hosted zones
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Connectivity | AWS Direct Connect (preferred) or Site-to-Site VPN | Network path for DNS traffic |
  | VPC DNS | Route 53 VPC Resolver (VPC+2) | Recursive DNS within VPC |
  | Private Zones | Route 53 Private Hosted Zone | Internal service discovery |
  | On-premises → VPC | Route 53 Inbound Resolver Endpoint (2+ ENIs) | Entry point for on-premises DNS queries |
  | VPC → On-premises | Route 53 Outbound Resolver Endpoint + Forwarding Rules | Exits point for VPC-to-on-premises DNS queries |
  | Multi-account scale | Route 53 Profiles + AWS RAM | Shared DNS config across many VPCs/accounts |
  | Security | Route 53 DNS Firewall | Filter outbound DNS from VPC |
  | On-premises DNS | Customer-managed (BIND, Windows DNS, Unbound) | Forwards to inbound endpoint for AWS domains |

- Key Decisions:
  - Inbound endpoint: minimum 2 ENIs (one per AZ) for high availability; configure source IP-preserving security group rules
  - On-premises DNS forwarding: forward only the AWS private domain(s) to inbound endpoint IPs (not all DNS)
  - Forwarding rules for on-premises domains: create per domain; share via AWS RAM to associated VPCs
  - Route 53 Profiles: use when private hosted zones and forwarding rules must be applied to 10+ VPCs consistently
  - Throughput: 10,000 UDP queries/second per IP per endpoint; add more IPs for higher load (max 6 per endpoint)
- Scaling Path: Single VPC + single account → Multi-account via Route 53 Profiles + AWS RAM; add Global Resolver for remote client resolution without VPN
- Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-getting-started.html (2026-08-31)

## Service Equivalence Map

| Capability | AWS (Route 53) | Azure DNS | Google Cloud DNS | Notes |
|------------|----------------|-----------|------------------|-------|
| Authoritative DNS | Route 53 Public Hosted Zone | Azure DNS Zone | Google Cloud DNS Zone | AWS: 200+ PoPs; 100% data plane SLA |
| Private DNS | Route 53 Private Hosted Zone | Azure Private DNS Zone | Cloud DNS Private Zone | AWS: explicit VPC association required |
| Zone apex alias | Route 53 Alias record | Azure Alias record | Not natively supported (workaround required) | AWS proprietary; Azure similar; GCP lacks native support |
| Geo routing | Route 53 Geolocation policy | Azure Traffic Manager (geographic) | Cloud DNS Geo policy | AWS: most specific match; requires default record |
| Latency routing | Route 53 Latency policy | Azure Traffic Manager (performance) | Cloud DNS (no native equivalent) | AWS: based on resolver latency, not geography |
| Weighted routing | Route 53 Weighted policy | Azure Traffic Manager (weighted) | Cloud DNS (no native equivalent) | |
| DNS Firewall | Route 53 DNS Firewall (VPC) + DNS Firewall Advanced | Azure DNS Private Resolver (DNS filtering) | Cloud DNS Response Policy Zones | AWS: advanced threat detection (DGA/tunneling) at GA Nov 2024 |
| DNS over HTTPS/TLS | Route 53 Global Resolver (GA 2026) | Azure DNS Private Resolver (DoH on roadmap) | Cloud DNS (DoH/DoT GA) | AWS Global Resolver newest; most feature-complete |
| Hybrid DNS | Route 53 Resolver Endpoints | Azure DNS Private Resolver | Cloud DNS DNS Peering + forwarding zones | All require Direct Connect/ExpressRoute/VPN equivalent |
| DNSSEC signing | Route 53 + KMS | Azure DNS (preview in some regions) | Cloud DNS DNSSEC | AWS: KMS CMK in us-east-1 required |
| DR routing control | ARC Routing Controls | Azure Traffic Manager (manual endpoint enable/disable) | No direct equivalent | ARC data plane highly resilient; most sophisticated DR integration |

## Provider Differentiators

**1. Alias Records — Zone Apex + Free + Auto IP Tracking**
Route 53 Alias records are proprietary DNS extensions that solve three problems simultaneously: (a) zone apex CNAME prohibition (Alias A/AAAA can be created at zone apex), (b) per-query cost (Alias queries to AWS resources are free vs CNAME charges per query), and (c) IP address tracking (Route 53 automatically resolves CloudFront/ALB/etc. DNS names and returns current IPs — no stale IP risk when AWS resource IPs change). No equivalent behavior exists as a standard DNS record type; Azure has a similar feature, Google Cloud DNS requires workarounds for zone apex.
[Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resource-record-sets-choosing-alias-non-alias.html, 2026-08-31]

**2. Eight Routing Policies + Traffic Flow Visual Editor**
No other major DNS provider offers the breadth of traffic routing semantics natively within the DNS layer: Simple, Weighted, Latency-based, Failover, Geolocation, Geoproximity, Multivalue Answer, and IP-based (CIDR). Geoproximity with bias control (adjustable routing radius) and the visual Traffic Flow editor (with undo/redo, JSON syntax highlighting, dark mode — updated March 2025) enable sophisticated traffic engineering without external traffic management services. Routing policies can be composed in tree structures (Latency → Weighted → resource) for multi-tier routing logic at the DNS layer.
[Source: https://aws.amazon.com/about-aws/whats-new/2025/03/amazon-route-53-traffic-flow-visual-editor-improve-dns-policy-editing, 2026-08-31]

**3. Deep ARC Integration for DR Failover**
Route 53 is natively integrated with Application Recovery Controller (ARC) routing controls. ARC routing controls act as highly reliable on/off switches that toggle Route 53 health check status via the ARC data plane (5 Regional cluster endpoints), bypassing the Route 53 control plane entirely. This means DR failover can be executed programmatically during regional impairments that affect the Route 53 control plane — the scenario where failover is most critical. No other major DNS provider has an equivalent data-plane DR control mechanism.
[Source: https://docs.aws.amazon.com/r53recovery/latest/dg/what-is-route53-recovery.html, 2026-08-31]

**4. DNSSEC Signing with AWS KMS**
Route 53 DNSSEC signing uses AWS KMS for Key Signing Key management, providing: hardware security module (HSM) backing for the KSK, IAM-based access control with confused deputy protection, CloudTrail audit logging of all key operations, and automatic KSK rotation capability without zone downtime (using 2 KSK slots). The integration with CloudWatch for DNSSEC-specific metrics (`DNSSECInternalFailure`, `DNSSECKeySigningKeysNeedingAction`) enables proactive monitoring before zone health is impacted.
[Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-configuring-dnssec.html, 2026-08-31]

**5. Global Footprint — 95+ Points of Presence**
Route 53 data plane operates across 95+ Points of Presence globally (North America: 24, Europe: 32, Asia: 18, South America: 7, Australia/NZ: 5, Middle East/Africa: 9). This global footprint provides sub-millisecond DNS resolution for users near PoPs, and the distributed architecture enables the 100% availability SLA for the DNS query resolution data plane — independent of the control plane (us-east-1/us-west-2).
[Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/Welcome.html, 2026-08-31]

**6. Route 53 Global Resolver — Anycast Secure DNS (GA 2026)**
Global Resolver (GA 2026-03-09, 30 Regions) is the only AWS-native DNS resolver supporting encrypted DNS (DoH, DoT) with token-based client authentication for remote/mobile clients, access to Route 53 private hosted zones without VPN, DNS views for split-horizon DNS beyond VPC boundaries, and advanced threat protection (DGA, DNS tunneling, Dictionary DGA detection) integrated with Security Hub. This positions Route 53 as an end-to-end DNS solution for both network-connected enterprise clients (VPC Resolver + endpoints) and internet-connected remote clients (Global Resolver).
[Source: https://aws.amazon.com/about-aws/whats-new/2026/03/amazon-route-53-global-resolver, 2026-08-31]

**7. Route 53 Profiles for Multi-VPC/Account DNS Management**
Route 53 Profiles enable consistent DNS configuration (private hosted zones, forwarding rules, DNS Firewall rule groups, VPC endpoint PHZs) to be applied and updated across thousands of VPCs and multiple accounts in an organization from a single control point. VPC endpoint support (added April 2025) eliminates the manual PHZ-to-VPC association burden that historically made centralized VPC endpoint management in multi-account organizations operationally painful.
[Source: https://aws.amazon.com/about-aws/whats-new/2025/04/amazon-route-53-profiles-vpc-endpoints, 2026-08-31]

## Scenario Coverage

**Standard Case: Simple Web Application (Zone Apex + www + HTTPS via ACM)**
- Approach:
  - Register domain (or transfer to Route 53); Route 53 auto-creates public hosted zone with NS + SOA
  - Request ACM certificate in us-east-1 for `example.com` and `*.example.com` (wildcard covers www); DNS validation via "Create records in Route 53" (one click inserts underscore CNAME)
  - Create CloudFront distribution: origin = ALB DNS name; Alternate Domain Names = `example.com`, `www.example.com`; SSL certificate = ACM cert
  - Route 53 records: Alias A (zone apex, `example.com`) → CloudFront; Alias A (`www.example.com`) → CloudFront; AAAA versions if IPv6 enabled; ACM validation CNAME (auto-created)
  - Enable query logging: CloudWatch log group in us-east-1
- Key Decisions:
  - Wildcard cert vs individual cert (wildcard simplifies future subdomain additions)
  - IPv6 enable/disable on CloudFront (if enabled, must create AAAA alias records)
  - ALB vs S3 origin (S3 for static sites only; ALB for dynamic content)
  - CloudFront HTTPS redirect setting (Redirect HTTP to HTTPS vs HTTPS only)

**Standard Case: Multi-Region Active-Passive DR (Failover Routing + ARC)**
- Approach:
  - Deploy identical infrastructure in primary (e.g., us-east-1) and secondary (e.g., us-west-2) Regions
  - Configure Route 53 Failover routing: Primary record (alias to primary ALB, `Evaluate Target Health = Yes`); Secondary record (alias to secondary ALB)
  - Pre-create ARC routing controls; associate with Route 53 health checks (on = healthy, off = unhealthy)
  - Configure ARC safety rules: assertion rule ensures at least one routing control stays ON
  - Set record TTL to 60–120 seconds
  - Configure Aurora Global Database for near-zero RPO data replication
  - Enable Route 53 Accelerated Recovery (optional: 60-min control plane RTO if us-east-1 impaired)
  - Store ARC cluster endpoints and DR IAM credentials offline
  - Test DR annually (at minimum) using ARC Region switch
- Key Decisions:
  - Health check interval (30s standard vs 10s fast — cost vs detection speed)
  - Failure threshold (1 for fastest detection, 3 default, up to 10 for stability)
  - Whether to enable Accelerated Recovery (additional operational overhead but useful if ARC not pre-configured)
  - RTO target: if sub-minute required → lower TTL + fast health checks + ARC; if minutes acceptable → standard settings

**Edge Case: All Health Checks Failing (Route 53 Last-Resort Behavior)**
- Approach: When ALL records in a Multivalue routing set are unhealthy, Route 53 returns up to 8 unhealthy records as a last resort. When ALL nonzero-weight records in a Weighted set are unhealthy, Route 53 serves zero-weight records. When ALL primary failover records are unhealthy → traffic switches to Secondary. When ALL health checks in a Failover setup are unhealthy (including secondary), Route 53 returns the last known values. Architects must design for this: secondary endpoint must be provisioned and reachable, or a static "maintenance page" endpoint must be designated as the final secondary.
- Approach: Configure a guaranteed-available secondary endpoint (e.g., S3 static maintenance page accessible even during full compute failure); test the all-unhealthy scenario explicitly during DR exercises; use ARC safety rules to prevent simultaneous disabling of all routing controls.

**Anti-Pattern Case: CNAME at Zone Apex**
- Clarification: Ask "Are you trying to point your root domain (e.g., example.com without www) to a CloudFront, ALB, or other AWS resource DNS name?" If yes, the correct solution is a Route 53 Alias A record (and AAAA if IPv6), not a CNAME. Ask "Are you aware that CNAME at zone apex is illegal per DNS protocol and that Route 53 returns an error if attempted?" Document that Alias records are free for AWS resource targets, eliminate the zone apex restriction, and auto-track resource IP changes — there is no valid reason to use CNAME for AWS-hosted web applications at the zone apex.

## Research Iteration Changelog

> Mandatory when `RESEARCH_DEPTH` is `standard`, `deep`, or `exhaustive`. Omit for `quick`.

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Core Concepts | Alias record target list (complete) | Added — confirmed 10 supported alias targets | https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resource-record-sets-choosing-alias-non-alias.html (2026-08-31) |
| 1 | Core Concepts | Control plane vs data plane distinction | Added — us-east-1 control plane, global data plane, 100% SLA | https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/route-53-concepts.html (2026-08-31) |
| 2 | Routing Policies | All 8 routing policies with limits and behavior | Added — complete coverage including IP-based (added in prior years) | https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-policy.html (2026-08-31) |
| 2 | Routing Policies | Traffic Flow visual editor 2025 improvements | Added — sidebar config, undo/redo, JSON editor, dark mode; available globally except GovCloud/China | https://aws.amazon.com/about-aws/whats-new/2025/03/amazon-route-53-traffic-flow-visual-editor-improve-dns-policy-editing (2026-08-31) |
| 2 | Routing Policies | Traffic Flow monthly charge per traffic policy record | ⚠️ UNVERIFIED — exact dollar amount not confirmed in fetched pages | — |
| 2 | Health Checks | 18% rule for health check status determination | Added — critical operational detail | https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-failover-determining-health-of-endpoints.html (2026-08-31) |
| 2 | Health Checks | CloudWatch alarm health check monitors data stream, not alarm state | Added — `SetAlarmState` has no effect on Route 53 health check status | https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/health-checks-types.html (2026-08-31) |
| 3 | DNS Security | DNSSEC KMS key requirements (us-east-1, ECC_NIST_P256) | Added — critical configuration detail | https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-configuring-dnssec-cmk-requirements.html (2026-08-31) |
| 3 | DNS Security | DNSSEC CloudWatch metrics (4 metrics, every 4 hours, us-east-1 only) | Added — complete metric names and alarm thresholds | https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/monitoring-hosted-zones-with-cloudwatch.html (2026-08-31) |
| 3 | DNS Security | DNS Firewall Advanced — GA November 2024 | Added — three threat types, confidence thresholds, Security Hub integration | https://aws.amazon.com/about-aws/whats-new/2024/11/amazon-route-53-resolver-dns-firewall-advanced (2026-08-31) |
| 3 | DNS Security | DNSSEC explicitly unavailable for private hosted zones | ⚠️ UNVERIFIED — absent from docs; consistent with all DNSSEC docs applying to public zones only; not an explicit statement | — |
| 3 | DNS Security | Specific AWS Managed domain list identifiers | ⚠️ UNVERIFIED — not confirmed in fetched pages | — |
| 3 | DNS Security | ACM cert must be in us-east-1 for CloudFront | ⚠️ UNVERIFIED — not confirmed in fetched pages; consistent with all CloudFront ACM integration docs | — |
| 4 | Resolver | Route 53 Resolver renamed to Route 53 VPC Resolver | Added — naming change coincident with Global Resolver GA (2026-03-09) | https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver.html (2026-08-31) |
| 4 | Resolver | Route 53 Global Resolver GA 2026-03-09 | Added — complete coverage: protocols, authentication, DNS views, threat protection, quotas | https://aws.amazon.com/about-aws/whats-new/2026/03/amazon-route-53-global-resolver (2026-08-31) |
| 4 | Resolver | Route 53 Profiles + VPC endpoint support (April 2025) | Added — PHZ association for interface endpoints across many VPCs/accounts | https://aws.amazon.com/about-aws/whats-new/2025/04/amazon-route-53-profiles-vpc-endpoints (2026-08-31) |
| 4 | Resolver | VPC Resolver on Outposts — feature availability matrix | Added — health checks unavailable on Outposts; DNS Firewall unavailable on Outposts | https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/outpost-resolver.html (2026-08-31) |
| 5 | DR / ARC | ARC safety rules — assertion vs gating | Added — prevents fail-open scenarios; gating rule as master switch | https://docs.aws.amazon.com/r53recovery/latest/dg/routing-control.safety-rules.html (2026-08-31) |
| 5 | DR / ARC | Route 53 Accelerated Recovery — 60-minute control plane RTO | Added — public zones only; us-west-2 failover; supported/unsupported APIs | https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/accelerated-recovery.html (2026-08-31) |
| 5 | DR / ARC | "Clients ignore TTL" as explicit AWS architectural caveat | ⚠️ UNVERIFIED — implicitly acknowledged in Global Accelerator comparison; no explicit statement found | — |
| 5 | DR / ARC | Accelerated recovery feature introduction year | ⚠️ UNVERIFIED — year not confirmed in fetched pages | — |
| 6 | Web App / Quotas | Complete quota table — 30+ entities | Added — consolidated from all sections | https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/DNSLimitations.html (2026-08-31) |
| 6 | Web App / Quotas | Global Resolver quotas | Added — separate from VPC Resolver quotas | https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/gr-load-balancer-limits.html (2026-08-31) |
| 6 | Web App / Cost | Alias query free for AWS resource targets | Verified — key cost differentiator | https://aws.amazon.com/route53/pricing/ (2026-08-31) |
| 6 | Web App / Cost | Traffic Flow monthly charge per traffic policy record | ⚠️ UNVERIFIED — exact dollar amount not confirmed in fetched pages | — |
