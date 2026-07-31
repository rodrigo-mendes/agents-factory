---
Full_Name: "AWS Networking Architecture (Connectivity, Edge, DNS, Hybrid, Egress, IPv6)"
Cloud_Provider: "AWS"
Architecture_Domain: "Networking Architecture (VPC design, subnetting, connectivity, hub-spoke/Transit Gateway, hybrid connectivity, DNS, edge/CDN, network security, egress control, IPv6)"
Target_Edition: "AWS Well-Architected Framework (publication date 2024-11-06, current stable) + AWS Networking & Content Delivery service documentation, verified live 2026-07-31"
Architecture_Context: "General multi-account production workloads on AWS (no single mandated compliance regime; compliance-specific items surfaced as Ask-First)"
Official_Source_URL: "https://docs.aws.amazon.com/wellarchitected/ , https://docs.aws.amazon.com/vpc/ , https://aws.amazon.com/architecture/networking-content-delivery/"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-07-31"
Currency_Threshold: "2027-07-31 (re-verify WAF edition, TGW/PrivateLink/Route 53 Resolver feature set, and service quotas after this date)"
---

> ⚠️ **Version / edition note (TARGET_EDITION):** AWS service documentation is continuously
> published rather than versioned by release number. Every service-doc claim below was verified live
> against the current AWS documentation on **2026-07-31**. The governing architecture edition is the
> **AWS Well-Architected Framework, publication date 2024-11-06** — the current stable edition, ~20
> months old at research time. It is accepted per the Source Hierarchy because it is the current
> stable, but re-verify pillar definitions if a newer edition ships.
>
> **Scope & cross-reference:** This document is the **broad networking-architecture** knowledge base
> (connectivity, hub-spoke, hybrid, DNS, edge/CDN, egress control, IPv6). For **intra-VPC internals**
> (subnet tiering mechanics, route-table semantics, NACL vs security-group behaviour, IGW/NAT
> plumbing, VPC CIDR sizing), see the complementary file
> `research_cloud_AWS_VPC_Networking_2026-07.md` in this same folder. Where the two overlap, this
> document cross-references rather than duplicates.

---

# Executive Summary

**AWS Networking Architecture** is the discipline of designing the connectivity substrate for
multi-account, multi-VPC AWS estates: how VPCs are addressed and segmented, how they interconnect
(hub-spoke via AWS Transit Gateway, VPC peering, AWS PrivateLink, Amazon VPC Lattice), how they reach
on-premises networks (AWS Direct Connect, AWS Site-to-Site VPN, AWS Cloud WAN), how DNS resolves
across the hybrid boundary (Amazon Route 53 VPC Resolver endpoints), how traffic reaches users at the
edge (Amazon CloudFront, AWS Global Accelerator), and how egress and inspection are centralized and
controlled (centralized NAT Gateway, AWS Network Firewall, Gateway Load Balancer). It sits one layer
above the single-VPC concerns covered in the companion VPC document, and its decisions have the
largest blast radius of any architecture domain: a CIDR-overlap or a full-mesh-peering choice made on
day one can permanently constrain the estate. (Source:
[Building a Scalable and Secure Multi-VPC AWS Network Infrastructure](https://docs.aws.amazon.com/whitepapers/latest/building-scalable-secure-multi-vpc-network-infrastructure/welcome.html),
publication date 2024-04-17, verified 2026-07-31.)

Because AWS ships networking features continuously, "what changed" is expressed as the load-bearing
capabilities that current guidance assumes: **AWS Transit Gateway** as the default hub-spoke fabric
(replacing full-mesh VPC peering at scale); **Amazon VPC IP Address Manager (IPAM)** for CIDR
governance across accounts and Regions; **AWS PrivateLink** and **Amazon VPC Lattice** for
service-to-service exposure without route-level connectivity or non-overlapping-CIDR constraints;
**AWS Network Firewall** with distributed / centralized / combined deployment models for stateful
inspection; **private NAT gateways** for VPC-to-VPC and on-prem egress; **AWS Cloud WAN** for managed
global WANs; and **dual-stack / IPv6** across VPC, PrivateLink, and VPC Lattice. Note one recent
naming change: **Amazon Route 53 Resolver was renamed "Route 53 VPC Resolver"** when Route 53 Global
Resolver was introduced (Source:
[What is Route 53 VPC Resolver?](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver.html),
verified 2026-07-31). Older material that says "EC2-Classic", "peer every VPC to every other VPC", or
"one NAT Gateway for the whole VPC" is treated as misinformation here.

The three most critical guardrails for general multi-account production workloads are: **(1)** plan
**non-overlapping, hierarchical CIDRs up front with IPAM** — overlaps permanently block Transit
Gateway, peering, and Direct Connect gateway attachment; **(2)** connect VPCs and on-premises through
a **Transit Gateway hub-spoke** (single regional hub, highly available by design) rather than a
full mesh; and **(3)** enforce **defense in depth at every layer** — least-privilege security groups
using security-group references (not wide CIDRs), VPC Flow Logs everywhere, centralized egress with
inspection, and edge protection (CloudFront + AWS WAF + AWS Shield) for internet-facing entry points.

---

# Cloud Architecture Glossary

```
Term: AWS Transit Gateway (TGW)
Definition: A regional network transit hub that interconnects VPCs, on-premises networks (via VPN or
  Direct Connect), and other transit gateways in a hub-and-spoke model. Highly available by design.
Provider Docs Section: Amazon VPC Transit Gateways — "Transit gateway design best practices"
Architect Usage: One TGW per Region as the default fabric for >2 VPCs. Attachments live in dedicated
  /28 attachment subnets; use TGW route tables for segmentation between environments.
Common Confusion: Confused with VPC peering (non-transitive, 1:1) and with Cloud WAN (managed global
  WAN abstraction that can orchestrate TGWs across Regions).
```
```
Term: AWS PrivateLink / Interface VPC endpoint / Endpoint service
Definition: Private, unidirectional connectivity to a specific service via an elastic network
  interface (interface endpoint) in the consumer VPC, fronted by a Network Load Balancer on the
  provider side (endpoint service). No route-level connectivity between the two VPCs.
Provider Docs Section: AWS PrivateLink — "Share your services through AWS PrivateLink"
Architect Usage: Expose one service across accounts/VPCs without peering, without route exchange, and
  even when CIDRs overlap. Consumer initiates; provider never routes into the consumer.
Common Confusion: Confused with VPC peering (bidirectional, route-based, no CIDR overlap allowed) and
  with Gateway endpoints (route-table prefix-list entries for S3/DynamoDB only).
```
```
Term: Gateway VPC endpoint
Definition: A route-table target (prefix list) that provides private access to Amazon S3 and Amazon
  DynamoDB without traversing the internet or a NAT Gateway. No hourly or data-processing charge.
Provider Docs Section: AWS PrivateLink — "Gateway endpoints"
Architect Usage: Always use for S3/DynamoDB private access — it is free and removes NAT data-processing
  cost for that traffic. Add the prefix list to the relevant subnet route tables.
Common Confusion: Confused with Interface endpoints (which are billed hourly + per GB and cover most
  other AWS services). Only S3 and DynamoDB support Gateway endpoints.
```
```
Term: Amazon VPC Lattice
Definition: A fully managed application-networking (service-to-service, layer-7) service that connects,
  secures, and monitors services and resources across VPCs and accounts, with IAM-based auth policies.
Provider Docs Section: Amazon VPC Lattice User Guide — "What is Amazon VPC Lattice?"
Architect Usage: Use for microservice-to-microservice connectivity with fine-grained auth, service
  discovery via DNS, and AZ affinity — including across overlapping CIDRs ("supports overlapping CIDR
  technology"). Complements, not replaces, TGW (network layer).
Common Confusion: Confused with TGW (L3 routing) and PrivateLink (single-service L4 exposure). Lattice
  is L7 service networking with built-in authZ.
```
```
Term: AWS Direct Connect (DX)
Definition: A dedicated, private physical network connection between an on-premises location and AWS,
  terminating at a Direct Connect location, carrying virtual interfaces (private/public/transit VIFs).
Provider Docs Section: AWS Direct Connect User Guide — "Direct Connect Resiliency Toolkit"
Architect Usage: Use for consistent bandwidth/latency to on-prem. For resiliency use ≥2 connections at
  separate DX locations (Maximum/High Resiliency models); back up with Site-to-Site VPN.
Common Confusion: Confused with Site-to-Site VPN (encrypted tunnel over the public internet, faster to
  provision, lower/variable bandwidth). DX is not encrypted by itself.
```
```
Term: AWS Site-to-Site VPN
Definition: A managed IPsec VPN connection between on-premises customer gateway equipment and AWS
  (virtual private gateway or Transit Gateway), over the public internet.
Provider Docs Section: AWS VPC Connectivity Options — "AWS Site-to-Site VPN"
Architect Usage: Primary connectivity for lower bandwidth/quick setup, or as encrypted backup to
  Direct Connect. Use BGP; enable multipath if the customer gateway supports it.
Common Confusion: Confused with AWS Client VPN (remote-user software access to a VPC), which is a
  different service.
```
```
Term: AWS Transit Gateway attachment
Definition: The connection object linking a VPC, VPN, Direct Connect gateway, peering, or Connect to a
  Transit Gateway. VPC attachments place an ENI in one subnet per Availability Zone.
Provider Docs Section: Amazon VPC Transit Gateways — "Transit gateway design best practices"
Architect Usage: Use a dedicated /28 attachment subnet per AZ; attach in every AZ where workloads run
  so traffic stays in-AZ. Associate one route table + open NACL with attachment subnets.
Common Confusion: Confused with the TGW itself. The attachment (per-VPC, per-AZ) is where AZ-affinity
  and blast radius are actually determined.
```
```
Term: Centralized egress / centralized inspection VPC
Definition: A shared "egress" or "inspection" VPC (spoke off the TGW) that concentrates internet
  egress (NAT Gateway) and/or stateful inspection (AWS Network Firewall, Gateway Load Balancer) for
  many workload VPCs.
Provider Docs Section: Multi-VPC whitepaper — "Network security / centralized egress points"
Architect Usage: Route spoke VPC 0.0.0.0/0 through the TGW to the egress/inspection VPC. Reduces NAT
  Gateway sprawl and gives one policy enforcement point.
Common Confusion: Confused with distributed egress (a NAT Gateway per workload VPC) — a real
  Ask-First trade-off (cost/latency/blast-radius vs. central control), see Ask-First §2.
```
```
Term: Amazon Route 53 VPC Resolver (formerly Route 53 Resolver)
Definition: The recursive DNS resolver available by default in every VPC at the "VPC+2" address,
  answering VPC-internal, private-hosted-zone, and public queries. Inbound/outbound Resolver endpoints
  plus forwarding rules enable hybrid DNS.
Provider Docs Section: Amazon Route 53 Developer Guide — "What is Route 53 VPC Resolver?"
Architect Usage: Outbound endpoint + forwarding rules to resolve on-prem zones from AWS; inbound
  endpoint so on-prem resolvers can resolve private AWS zones. Share rules across accounts via RAM.
Common Confusion: Was renamed from "Route 53 Resolver"; also confused with Route 53 public/private
  hosted zones (authoritative) vs. the Resolver (recursive).
```
```
Term: Amazon CloudFront
Definition: A content delivery network (CDN) that caches and accelerates HTTP/HTTPS content (static and
  dynamic) at edge locations, integrating with AWS WAF and AWS Shield.
Provider Docs Section: AWS Global Accelerator FAQs — "CloudFront vs Global Accelerator"
Architect Usage: Default for cacheable web assets, API acceleration, and dynamic site delivery over
  HTTP(S); the edge attach point for WAF and Shield Advanced.
Common Confusion: Confused with AWS Global Accelerator — CloudFront is HTTP-centric/caching; Global
  Accelerator is TCP/UDP proxying with static anycast IPs.
```
```
Term: AWS Global Accelerator
Definition: A networking service providing static anycast IP addresses at the edge that proxy TCP/UDP
  traffic over the AWS backbone to application endpoints in one or more Regions, with fast regional
  failover.
Provider Docs Section: AWS Global Accelerator FAQs
Architect Usage: Use for non-HTTP protocols (gaming/UDP, MQTT/IoT, VoIP) or HTTP cases needing static
  IPs / deterministic fast regional failover. Not a cache.
Common Confusion: Confused with CloudFront (caching CDN). Note: Network Firewall does NOT inspect
  Global Accelerator traffic.
```
```
Term: AWS Network Firewall
Definition: A managed, stateful network firewall and IPS/IDS for VPC traffic, deployable in
  distributed, centralized, or combined models, with Suricata-compatible rules.
Provider Docs Section: AWS Network Firewall Developer Guide — "Example architectures with routing"
Architect Usage: Centralized model = inspection VPC behind TGW; distributed = firewall endpoints in
  each VPC. Route traffic through the firewall endpoint subnet via route tables.
Common Confusion: Confused with security groups/NACLs (instance/subnet allow-lists). Network Firewall
  adds L3–L7 stateful inspection. It does NOT support VPC peering paths or Global Accelerator traffic.
```
```
Term: Amazon VPC IP Address Manager (IPAM)
Definition: A managed service to plan, allocate, track, and monitor IP address space (IPv4 and IPv6)
  hierarchically across accounts and Regions, with automatic CIDR allocation by business rules.
Provider Docs Section: Multi-VPC whitepaper — "IP address planning and management"
Architect Usage: The system of record for CIDR planning. Enforces hierarchy, prevents overlaps, and
  auto-allocates VPC CIDRs; share pools org-wide.
Common Confusion: Confused with a spreadsheet-based IPAM. IPAM actively allocates and monitors, and
  integrates with AWS Control Tower / Organizations.
```
```
Term: VPC Flow Logs
Definition: A feature that captures metadata about IP traffic to and from network interfaces in a VPC,
  publishable to CloudWatch Logs, Amazon S3, or Amazon Data Firehose.
Provider Docs Section: Amazon VPC User Guide — "Logging IP traffic using VPC Flow Logs"
Architect Usage: Enable at VPC scope for all VPCs (network visibility, incident forensics, and to feed
  detection). See companion VPC document for record-format details.
Common Confusion: Confused with Network Firewall/DNS Firewall logs (policy logs). Flow Logs are
  connection metadata, not packet payloads.
```
```
Term: Non-routable / routable CIDR (overlapping-network egress)
Definition: A design where each VPC keeps a non-routable original CIDR plus an assigned routable range;
  a private NAT gateway translates non-routable sources to the routable range for TGW transit.
Provider Docs Section: Amazon VPC User Guide — "NAT gateway use cases / overlapping networks"
Architect Usage: Use a private NAT gateway + TGW to connect VPCs that must retain overlapping CIDRs
  (mergers, isolated tenants) without re-IPing.
Common Confusion: Treated as a legitimate exception; the default remains non-overlapping CIDRs planned
  via IPAM. Overlap is a conscious, documented decision only.
```

---

# 1. Framework Pillars — How the WAF Governs Networking

> **TARGET_EDITION:** AWS Well-Architected Framework, publication date **2024-11-06** (current
> stable). Source: [AWS Well-Architected Framework — welcome](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html),
> verified 2026-07-31.

The Framework defines six pillars — Operational Excellence, Security, Reliability, Performance
Efficiency, Cost Optimization, Sustainability (Source: WAF welcome page and Multi-VPC whitepaper "Are
you Well-Architected?", verified 2026-07-31). The five that most directly govern networking:

```
Pillar: Reliability
Definition (2024-11-06 edition): The ability of a workload to perform its intended function correctly
  and consistently when it's expected to, including the ability to operate and test the workload
  through its total lifecycle.
Key Design Principles (networking manifestation): Automatically recover from failure; scale
  horizontally; stop guessing capacity — applied to networks: distribute subnets and NAT/egress across
  multiple Availability Zones; rely on services that are highly available by design (Transit Gateway,
  internet gateway); design multi-connection Direct Connect resiliency with VPN backup.
Applies To (multi-account production): Per-AZ NAT gateways and per-AZ TGW attachments so an AZ failure
  never severs a whole VPC's egress or transit; single TGW per Region for DR (TGW is HA by design).
Assessment Questions: How do you design your workload service architecture / how do you plan network
  topology to withstand component and AZ failures? How do you back up dedicated connectivity?
Source: https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html (2024-11-06);
  https://docs.aws.amazon.com/vpc/latest/tgw/tgw-best-design-practices.html (verified 2026-07-31)
```
```
Pillar: Security
Definition (2024-11-06 edition): The ability to protect data, systems, and assets to take advantage of
  cloud technologies to improve your security.
Key Design Principles (networking manifestation): Apply security at all layers; enforce least
  privilege; protect network in transit and at rest. Applied to networks: security-group referencing
  instead of wide CIDRs, private subnets + centralized egress/inspection, VPC Flow Logs, AWS Network
  Firewall / Route 53 Resolver DNS Firewall, PrivateLink for private service access, edge WAF/Shield.
Applies To (multi-account production): Defense in depth — SG references between tiers, NACL backstops,
  centralized inspection VPC, encryption in transit, no 0.0.0.0/0 on management ports.
Assessment Questions: How do you control traffic within your network layers? How do you protect your
  networks? How do you protect data in transit?
Source: https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html (2024-11-06);
  https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html (verified 2026-07-31)
```
```
Pillar: Performance Efficiency
Definition (2024-11-06 edition): The ability to use computing resources efficiently to meet system
  requirements, and to maintain that efficiency as demand changes and technologies evolve.
Key Design Principles (networking manifestation): Use the AWS global infrastructure and edge to reduce
  latency; select the right connectivity primitive. Applied to networks: CloudFront/Global Accelerator
  at the edge, AZ-affinity routing (VPC Lattice, zonal endpoints), placement of PrivateLink endpoints
  in every AZ, intra-Region over cross-Region service access.
Applies To (multi-account production): Edge acceleration for global users; keep east-west traffic
  in-AZ to avoid inter-AZ latency and data-transfer cost.
Assessment Questions: How do you select the best-performing network features? How do you use edge
  services to reduce latency for end users?
Source: https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html (2024-11-06);
  https://aws.amazon.com/global-accelerator/faqs/ (verified 2026-07-31)
```
```
Pillar: Cost Optimization
Definition (2024-11-06 edition): The ability to run systems to deliver business value at the lowest
  price point.
Key Design Principles (networking manifestation): Adopt a consumption model; measure efficiency.
  Applied to networks: Gateway endpoints (free) for S3/DynamoDB to avoid NAT data-processing charges;
  centralized egress to reduce NAT Gateway count; keep traffic in-AZ to avoid inter-AZ transfer;
  right-size Direct Connect vs VPN. NOTE: any specific pricing is Ask-First — see Guardrails.
Applies To (multi-account production): NAT Gateway hourly + per-GB and inter-AZ transfer are common
  cost surprises; centralization and Gateway endpoints are the primary levers.
Assessment Questions: How do you evaluate cost when selecting services? How do you monitor data-transfer
  and egress cost?
Source: https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html (2024-11-06);
  https://docs.aws.amazon.com/whitepapers/latest/aws-privatelink/what-are-vpc-endpoints.html
  (verified 2026-07-31)
```
```
Pillar: Operational Excellence
Definition (2024-11-06 edition): The ability to support development and run workloads effectively, gain
  insight into their operations, and continuously improve supporting processes and procedures.
Key Design Principles (networking manifestation): Perform operations as code; make frequent, small,
  reversible changes; anticipate failure. Applied to networks: IPAM-governed CIDR allocation as code,
  Flow Logs + Network Firewall logs for observability, centralized route/policy management on TGW,
  Direct Connect failover testing.
Applies To (multi-account production): Network changes are high-blast-radius; codify CIDR/route/policy
  and test DX/VPN failover before relying on it.
Assessment Questions: How do you reduce defects and improve flow into production for network changes?
  How do you understand the health of your network operations?
Source: https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html (2024-11-06);
  https://docs.aws.amazon.com/directconnect/latest/UserGuide/high_resiliency.html (verified 2026-07-31)
```

> Sustainability is the sixth pillar (Source: WAF welcome, 2024-11-06); its networking manifestation
> (Region selection near users, right-sizing to reduce provisioned network resources) is secondary for
> this domain and folded into Performance Efficiency / Cost Optimization above.

---

# 2. Always-Do Patterns (Mandatory)

> **TARGET_EDITION applies:** WAF 2024-11-06 + AWS networking service docs verified 2026-07-31.

### AD-1 — Plan non-overlapping, hierarchical CIDRs up front with Amazon VPC IPAM
- **Why + Pillar:** Operational Excellence & Reliability. A good IP scheme must cover on-prem + cloud
  + future growth and *proactively prevent overlaps*; overlaps break routing at scale. AWS: "Plan your
  IP addressing scheme (both public and private IPs) up front and select an IP address management tool
  … Proactively prevent and track overlapping IP CIDRs."
- **Provider Service:** Amazon VPC IP Address Manager (IPAM).
- **Architecture Decision:** Define a hierarchical, summarized IPv4/IPv6 scheme; allocate distinct
  CIDRs per environment/Region/business unit; designate separate ranges for on-prem vs cloud; enable
  IPv6/dual-stack to reduce IPv4 depletion; auto-allocate VPC CIDRs from IPAM pools shared org-wide.
- **Verification (CLI/console):** `aws ec2 describe-ipam-pools` and `aws ec2 get-ipam-pool-allocations
  --ipam-pool-id <id>`; in console, IPAM → Pools → allocations shows overlap monitoring.
- **Trade-offs:** Upfront planning effort and governance process for exceptions; pays back by making
  TGW/peering/DX attachment possible without re-IPing.
- **Source:** [Multi-VPC whitepaper — IP address planning and management](https://docs.aws.amazon.com/whitepapers/latest/building-scalable-secure-multi-vpc-network-infrastructure/ip-address-planning-and-management.html)
  (2024-04-17, verified 2026-07-31). > ⚠️ Source dated 2024-04; verify currency.

### AD-2 — Distribute subnets across multiple Availability Zones (multi-AZ by default)
- **Why + Pillar:** Reliability. A subnet is pinned to one AZ; HA requires ≥2 subnets in ≥2 AZs.
- **Provider Service:** Amazon VPC subnets, Availability Zones.
- **Architecture Decision:** For every tier (public/private/isolated), create one subnet per AZ across
  ≥2 (typically 3) AZs; place load balancers, NAT, and endpoints per-AZ. (Mechanics/route-table detail
  in companion VPC doc.)
- **Verification:** `aws ec2 describe-subnets --filters Name=vpc-id,Values=<vpc>` and confirm distinct
  `AvailabilityZone` values per tier.
- **Trade-offs:** More subnets/route tables to manage; small inter-AZ transfer cost when traffic
  crosses AZs (mitigate with AZ-affinity, see AD-11).
- **Source:** [Amazon VPC User Guide — NAT gateway use cases (multi-AZ resiliency)](https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-scenarios.html)
  (verified 2026-07-31).

### AD-3 — Private subnets with per-AZ NAT Gateway for controlled egress
- **Why + Pillar:** Reliability & Security. A NAT gateway is AZ-scoped; AWS: "improve resiliency by
  creating a NAT gateway in each Availability Zone that contains resources that require internet
  access." Private subnets get outbound-only internet, no unsolicited inbound.
- **Provider Service:** NAT Gateway (public), internet gateway, route tables.
- **Architecture Decision:** One public NAT Gateway per AZ; each private subnet's route table sends
  `0.0.0.0/0` to the NAT Gateway *in its own AZ* (not a single shared NAT Gateway).
- **Verification:** `aws ec2 describe-nat-gateways`; confirm one per AZ and that each private route
  table's default route targets the same-AZ NAT gateway.
- **Trade-offs:** NAT Gateway hourly + per-GB processing cost multiplied per AZ; centralized egress
  (Ask-First §2) trades this against a shared egress VPC.
- **Source:** [Amazon VPC User Guide — NAT gateway use cases](https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-scenarios.html)
  (verified 2026-07-31).

### AD-4 — Use VPC endpoints for AWS-service traffic (Gateway for S3/DynamoDB, Interface for the rest)
- **Why + Pillar:** Security & Cost. Keeps AWS API traffic off the public internet; Gateway endpoints
  for S3/DynamoDB are free and remove NAT data-processing cost for that traffic; Interface endpoints
  (PrivateLink) provide private access to most other services.
- **Provider Service:** Gateway VPC endpoints (Amazon S3, Amazon DynamoDB); Interface VPC endpoints
  (AWS PrivateLink).
- **Architecture Decision:** Add the S3/DynamoDB Gateway endpoint prefix list to private route tables;
  create Interface endpoints per-AZ with a least-privilege security group and enable private DNS so SDK
  calls to the public endpoint resolve to the VPC endpoint. Attach endpoint policies to scope access.
- **Verification:** `aws ec2 describe-vpc-endpoints`; for interface endpoints confirm `PrivateDnsEnabled`
  and one ENI per AZ. Interface endpoints don't answer ping — use `nc`/`nmap`.
- **Trade-offs:** Interface endpoints bill hourly + per-GB (Gateway endpoints do not). Interface
  endpoint security group must allow inbound HTTPS from workloads.
- **Source:** [AWS PrivateLink — access an AWS service using an interface VPC endpoint](https://docs.aws.amazon.com/vpc/latest/privatelink/create-interface-endpoint.html)
  (verified 2026-07-31).

### AD-5 — Least-privilege security groups using security-group references (not wide CIDRs)
- **Why + Pillar:** Security. Security groups are stateful allow-lists with no deny rules; referencing
  another security group as the source scopes tier-to-tier access to the *members* of that group
  regardless of IP, instead of a broad CIDR.
- **Provider Service:** Amazon VPC security groups.
- **Architecture Decision:** LB SG allows 80/443 from `0.0.0.0/0`; web SG allows 80/443 *from the LB
  SG*; DB SG allows the DB port *from the web SG*. SG references work within a VPC, across peering, and
  across a Transit Gateway (inbound).
- **Verification:** `aws ec2 describe-security-groups`; confirm rule sources are `sg-...` IDs, not wide
  CIDRs, for east-west tiers.
- **Trade-offs:** SG-reference limits (rules-per-SG accounting); stale rules appear if a referenced SG
  in a peered/shared VPC is deleted. Middlebox routing requires IP/CIDR sources, not SG references.
- **Source:** [Amazon VPC User Guide — Security group rules (referencing)](https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html)
  (verified 2026-07-31).

### AD-6 — Enable VPC Flow Logs on every VPC
- **Why + Pillar:** Security & Operational Excellence (Apply security at all layers; observability).
  Flow Logs are the baseline for connection visibility, incident forensics, and detection.
- **Provider Service:** VPC Flow Logs → Amazon CloudWatch Logs / Amazon S3 / Amazon Data Firehose.
- **Architecture Decision:** Create flow logs at VPC scope (covers all ENIs) for ALL traffic; retain in
  S3 for cost, stream to CloudWatch/Firehose for near-real-time detection.
- **Verification:** `aws ec2 describe-flow-logs --filter Name=resource-id,Values=<vpc-id>` returns an
  active log for each VPC.
- **Trade-offs:** Log storage/ingestion cost; Flow Logs are metadata, not payload (pair with Network
  Firewall logging for L7 visibility). (Record-format detail: companion VPC doc.)
- **Source:** Referenced by [Multi-VPC whitepaper — network security](https://docs.aws.amazon.com/whitepapers/latest/building-scalable-secure-multi-vpc-network-infrastructure/welcome.html)
  (2024-04-17); Amazon VPC User Guide "Logging IP traffic using VPC Flow Logs" (verified 2026-07-31).
  > ⚠️ Whitepaper dated 2024-04; verify currency.

### AD-7 — Connect VPCs and on-prem through an AWS Transit Gateway hub-spoke
- **Why + Pillar:** Reliability & Operational Excellence. TGW is a regional hub that interconnects VPCs,
  VPN, and Direct Connect in a hub-and-spoke model and is "highly available by design" — no extra TGW
  needed for HA; "use a single transit gateway in each Region for disaster recovery."
- **Provider Service:** AWS Transit Gateway + TGW route tables + TGW attachments.
- **Architecture Decision:** One TGW per Region; dedicated **/28 attachment subnet per AZ** per VPC;
  associate one open NACL and one route table with attachment subnets; enable route propagation for
  Direct Connect gateway and BGP VPN attachments; segment environments via multiple TGW route tables
  only when required.
- **Verification:** `aws ec2 describe-transit-gateways` / `describe-transit-gateway-attachments`;
  confirm one attachment per AZ and a dedicated attachment subnet.
- **Trade-offs:** TGW data-processing per-GB; a central fabric to govern (route tables, ASNs). For
  global scale, consider inter-Region peering or AWS Cloud WAN (Ask-First §7).
- **Source:** [Amazon VPC — Transit gateway design best practices](https://docs.aws.amazon.com/vpc/latest/tgw/tgw-best-design-practices.html)
  (verified 2026-07-31).

### AD-8 — Centralize internet egress and inspection where scale warrants
- **Why + Pillar:** Security & Cost. AWS documents building "centralized egress points for accessing the
  internet and endpoints" (NAT Gateway, VPC endpoints, PrivateLink, AWS Network Firewall, Gateway Load
  Balancers) as a core multi-VPC network-security practice.
- **Provider Service:** Egress/inspection VPC + AWS Network Firewall / Gateway Load Balancer + NAT
  Gateway, reached via AWS Transit Gateway.
- **Architecture Decision:** Route spoke-VPC `0.0.0.0/0` via the TGW to a shared egress/inspection VPC
  that hosts per-AZ NAT Gateways and Network Firewall endpoints; apply one stateful policy centrally.
- **Verification:** TGW route tables direct spoke default routes to the inspection/egress attachment;
  `aws network-firewall describe-firewall` shows endpoints per AZ.
- **Trade-offs:** Adds an inspection hop (latency) and a shared blast radius; centralized-vs-distributed
  is a real decision — see Ask-First §2. Network Firewall does **not** inspect VPC peering paths or
  Global Accelerator traffic (design around it).
- **Source:** [Multi-VPC whitepaper — welcome / network security](https://docs.aws.amazon.com/whitepapers/latest/building-scalable-secure-multi-vpc-network-infrastructure/welcome.html)
  (2024-04-17, verified 2026-07-31); [AWS Network Firewall — example architectures](https://docs.aws.amazon.com/network-firewall/latest/developerguide/architectures.html)
  (verified 2026-07-31). > ⚠️ Whitepaper dated 2024-04; verify currency.

### AD-9 — Implement hybrid DNS with Amazon Route 53 VPC Resolver endpoints
- **Why + Pillar:** Reliability & Operational Excellence. Hybrid workloads must resolve names both ways;
  Resolver endpoints + conditional forwarding rules provide it over VPN or Direct Connect.
- **Provider Service:** Amazon Route 53 VPC Resolver — inbound endpoint, outbound endpoint, Resolver
  rules; private hosted zones; AWS RAM to share rules.
- **Architecture Decision:** Outbound endpoint + forwarding rules to send on-prem zones (e.g.,
  `internal.example.com`) to on-prem resolvers; inbound endpoint so on-prem resolvers can resolve
  private AWS zones; share Resolver rules across accounts via AWS RAM. Deploy endpoints in ≥2 AZs.
- **Verification:** `aws route53resolver list-resolver-endpoints` (Inbound + Outbound) and
  `list-resolver-rules`; test resolution from an EC2 instance and from on-prem.
- **Trade-offs:** Resolver endpoints bill per ENI/hour + queries; security groups cannot block the
  VPC+2 resolver — use Route 53 Resolver DNS Firewall to filter DNS.
- **Source:** [Amazon Route 53 — What is Route 53 VPC Resolver?](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver.html)
  (verified 2026-07-31).

### AD-10 — Design Direct Connect for resiliency and back it with Site-to-Site VPN
- **Why + Pillar:** Reliability. The Direct Connect Resiliency Toolkit offers Maximum / High Resiliency
  models using connections at **separate DX locations**; AWS documents a Direct Connect + Site-to-Site
  VPN option for a private/encrypted path with VPN as backup.
- **Provider Service:** AWS Direct Connect (Resiliency Toolkit, LAGs, Direct Connect gateway) + AWS
  Site-to-Site VPN (BGP).
- **Architecture Decision:** For production, use ≥2 DX connections across ≥2 DX locations/devices (High
  or Maximum Resiliency); terminate on a Direct Connect gateway to a TGW; add a BGP Site-to-Site VPN as
  encrypted backup; run the toolkit's failover test.
- **Verification:** `aws directconnect describe-connections` (≥2 across locations); run the console
  "Direct Connect Failover Test"; `aws ec2 describe-vpn-connections` for the backup tunnel.
- **Trade-offs:** DX is not encrypted by itself (use MACsec or a VPN-over-DX for encryption); multiple
  DX connections/locations cost more; provisioning can take days/weeks.
- **Source:** [AWS Direct Connect — high resiliency](https://docs.aws.amazon.com/directconnect/latest/UserGuide/high_resiliency.html)
  and [AWS VPC Connectivity Options — Direct Connect + Site-to-Site VPN](https://docs.aws.amazon.com/whitepapers/latest/aws-vpc-connectivity-options/introduction.html)
  (verified 2026-07-31).

### AD-11 — Keep east-west traffic in-AZ (AZ affinity) and prefer intra-Region service access
- **Why + Pillar:** Performance Efficiency & Cost. In-AZ routing lowers latency and avoids inter-AZ
  transfer charges; AWS recommends intra-Region over cross-Region service access ("lower latency and
  lower costs").
- **Provider Service:** Amazon VPC Lattice (AZ affinity, no inter-AZ data-transfer charge), PrivateLink
  zonal endpoints, per-AZ interface endpoints.
- **Architecture Decision:** Use Lattice AZ-affinity or zonal PrivateLink endpoints for chatty
  east-west traffic; deploy endpoints in every AZ workloads run; for PrivateLink prefer intra-Region.
- **Verification:** Confirm interface endpoints exist in each workload AZ; for Lattice, verify service
  network association and AZ-affinity behaviour in metrics.
- **Trade-offs:** Zonal endpoints reduce cross-AZ resilience if that AZ fails; Lattice adds a managed
  L7 hop (cost/latency) in exchange for auth + discovery.
- **Source:** [AWS PrivateLink — share your services (cross-Region considerations, zonal endpoints)](https://docs.aws.amazon.com/vpc/latest/privatelink/privatelink-share-your-services.html)
  and [Amazon VPC Lattice — AZ affinity](https://docs.aws.amazon.com/vpc-lattice/latest/ug/what-is-vpc-lattice.html)
  (verified 2026-07-31).

### AD-12 — Protect internet-facing entry points at the edge (CloudFront + AWS WAF + AWS Shield)
- **Why + Pillar:** Security & Performance Efficiency. Terminate and filter internet traffic at the
  edge before it reaches origins; CloudFront is the edge attach point for WAF and Shield.
- **Provider Service:** Amazon CloudFront (HTTP/HTTPS), AWS WAF, AWS Shield; AWS Global Accelerator for
  non-HTTP/static-IP cases.
- **Architecture Decision:** Front HTTP(S) origins with CloudFront + AWS WAF web ACL + Shield; keep
  origins private (origin access control, private-subnet ALB). For TCP/UDP or static-IP needs, use
  Global Accelerator (note: Network Firewall does not inspect Global Accelerator traffic).
- **Verification:** `aws cloudfront list-distributions`; `aws wafv2 list-web-acls --scope CLOUDFRONT`;
  confirm origin is not directly reachable from the internet.
- **Trade-offs:** CDN/WAF request + data costs; caching semantics require correct cache policies; Global
  Accelerator is not a cache.
- **Source:** [AWS Global Accelerator FAQs — CloudFront vs Global Accelerator](https://aws.amazon.com/global-accelerator/faqs/)
  (verified 2026-07-31).

---

# 3. Ask-First Decisions (Architectural Crossroads)

> **TARGET_EDITION applies:** WAF 2024-11-06 + AWS networking service docs verified 2026-07-31.
> Cost figures are relative (order of magnitude); exact pricing/quotas are Ask-First (see Guardrails).

### AF-1 — Inter-VPC connectivity: Transit Gateway vs VPC peering vs VPC Lattice
| Option | AWS Service | Optimizes | Sacrifices | Best When |
|---|---|---|---|---|
| Full-mesh peering | VPC peering | Lowest per-connection cost, lowest latency (direct) | Non-transitive; O(n²) connections; no overlap | 2–3 VPCs, stable, non-overlapping CIDRs |
| Hub-spoke transit | AWS Transit Gateway | Transitive routing, central policy, scales to hundreds of VPCs + hybrid | Per-GB processing; central fabric to govern | Many VPCs / on-prem / segmentation needed |
| Service networking | Amazon VPC Lattice | L7 service-to-service with IAM auth, discovery, AZ affinity, overlapping CIDR support | Managed L7 hop cost; app-layer only | Microservices needing authZ + discovery, incl. overlapping CIDRs |
- **Cost Profile:** Peering cheapest at tiny scale; TGW adds per-GB but removes mesh sprawl; Lattice
  bills provisioning + data + requests.
- **Scaling:** Peering is non-transitive and O(n²) — untenable past a handful of VPCs; TGW scales to
  the estate; Lattice scales at the service layer independent of L3.
- **Operational Burden:** Peering = many point-to-point links; TGW = one fabric + route tables; Lattice
  = service/auth-policy management.
- **Lock-in:** All AWS-specific; Lattice highest (app-layer coupling); peering lowest.
- **Ask The Architect:** "How many VPCs will interconnect within 18 months, do any CIDRs overlap, and
  do you need L3 routing (TGW), one-to-one links (peering), or authenticated L7 service calls (Lattice)?"
- **Source:** [AWS VPC Connectivity Options — VPC-to-VPC](https://docs.aws.amazon.com/whitepapers/latest/aws-vpc-connectivity-options/introduction.html);
  [Amazon VPC Lattice — overview](https://docs.aws.amazon.com/vpc-lattice/latest/ug/what-is-vpc-lattice.html)
  (verified 2026-07-31).

### AF-2 — Egress model: centralized (inspection/egress VPC) vs distributed (per-VPC NAT)
| Option | AWS Service | Optimizes | Sacrifices | Best When |
|---|---|---|---|---|
| Distributed | NAT Gateway per VPC (per AZ) | Simplicity, no TGW hop, isolated blast radius | NAT sprawl cost; policy duplicated per VPC | Few VPCs; strict per-VPC isolation |
| Centralized | Egress VPC + AWS Network Firewall + NAT Gateway via TGW | One policy/inspection point, fewer NAT Gateways | Extra hop latency; shared blast radius; TGW cost | Many VPCs; central inspection/compliance |
- **Cost Profile:** Centralized reduces NAT Gateway count but adds TGW per-GB + inspection cost;
  distributed multiplies NAT hourly/per-GB across VPCs.
- **Scaling:** Centralized scales policy management; distributed scales isolation.
- **Operational Burden:** Centralized = one firewall policy to run well; distributed = N policies.
- **Lock-in:** Both AWS-native.
- **Ask The Architect:** "Do you need a single inspection/egress policy point (centralized) or maximum
  per-VPC isolation and minimal latency (distributed)? How many VPCs and what compliance posture?"
- **Source:** [Multi-VPC whitepaper — centralized egress](https://docs.aws.amazon.com/whitepapers/latest/building-scalable-secure-multi-vpc-network-infrastructure/welcome.html)
  (2024-04-17). > ⚠️ Source dated 2024-04; verify currency.

### AF-3 — Hybrid connectivity: Direct Connect vs Site-to-Site VPN vs both
| Option | AWS Service | Optimizes | Sacrifices | Best When |
|---|---|---|---|---|
| VPN only | AWS Site-to-Site VPN | Fast provisioning, encrypted, low cost | Bandwidth/latency variability (public internet) | Quick start, lower/variable bandwidth, encryption required |
| DX only | AWS Direct Connect | Consistent bandwidth/latency, private | Lead time; not encrypted alone; single path risk | Steady high-throughput/low-latency to on-prem |
| DX + VPN | Direct Connect + Site-to-Site VPN | Private path + encrypted backup/failover | Highest cost/complexity | Production requiring resiliency and encryption |
- **Cost Profile:** VPN cheapest; DX has port + data cost; DX+VPN highest.
- **Scaling:** DX scales with LAGs/multiple connections/locations (Resiliency Toolkit); VPN scales with
  tunnels/ECMP via TGW.
- **Operational Burden:** DX = physical provisioning + BGP; VPN = customer-gateway config; both = BGP.
- **Lock-in:** AWS-native connectivity; portable BGP concepts.
- **Ask The Architect:** "What bandwidth/latency SLA and encryption requirements apply, and what
  resiliency (single vs Maximum Resiliency) does the workload need?"
- **Source:** [AWS VPC Connectivity Options](https://docs.aws.amazon.com/whitepapers/latest/aws-vpc-connectivity-options/introduction.html);
  [Direct Connect Resiliency Toolkit](https://docs.aws.amazon.com/directconnect/latest/UserGuide/high_resiliency.html)
  (verified 2026-07-31).

### AF-4 — Region strategy: single-region vs multi-region active-passive vs active-active
| Option | AWS Service | Optimizes | Sacrifices | Best When |
|---|---|---|---|---|
| Single-region | Multi-AZ VPC | Simplicity, lowest cost | Region-level outage exposure | Most workloads; RTO/RPO tolerant of AZ-only HA |
| Active-passive | TGW inter-Region peering + Route 53 failover | Lower cost than active-active; DR path | Failover time; idle standby | Business-critical with hours-minutes RTO |
| Active-active | Global Accelerator / Route 53 latency routing + multi-Region | Lowest RTO, global latency | Highest cost/complexity; data consistency | Mission-critical/global, near-zero RTO |
- **Cost Profile:** Rises steeply single → active-active.
- **Scaling:** Active-active scales globally; single-region bounded by one Region.
- **Operational Burden:** Multi-region multiplies data replication, routing, and testing complexity.
- **Lock-in:** Routing (Route 53 / Global Accelerator) AWS-native.
- **Ask The Architect:** "What are the RTO/RPO targets and is a Region-level outage in scope? What is
  the data-replication/consistency model?" (Compliance/data-residency → escalate, see Guardrails.)
- **Source:** [AWS Global Accelerator FAQs](https://aws.amazon.com/global-accelerator/faqs/);
  [TGW design best practices — DR/inter-Region](https://docs.aws.amazon.com/vpc/latest/tgw/tgw-best-design-practices.html)
  (verified 2026-07-31).

### AF-5 — Service exposure: AWS PrivateLink vs VPC peering
| Option | AWS Service | Optimizes | Sacrifices | Best When |
|---|---|---|---|---|
| PrivateLink | Interface endpoint + endpoint service (NLB) | One-way, single-service exposure; overlapping CIDRs OK; no route exchange | Per-endpoint cost; NLB fronting required | Expose one service across accounts/tenants, incl. overlapping CIDRs |
| Peering | VPC peering | Full bidirectional route-level connectivity, low latency | Non-transitive; no overlap; broad exposure | Trusted 1:1 VPCs needing broad connectivity |
- **Cost Profile:** PrivateLink bills per endpoint/hour + per-GB; peering has no hourly charge (data
  transfer applies).
- **Scaling:** PrivateLink scales per-service and cross-Region; peering non-transitive.
- **Operational Burden:** PrivateLink = NLB + endpoint-service management; peering = route tables + SGs.
- **Lock-in:** Both AWS-native.
- **Ask The Architect:** "Do you need to expose exactly one service unidirectionally (possibly with
  overlapping CIDRs) — PrivateLink — or full network reachability between two trusted VPCs — peering?"
- **Source:** [AWS PrivateLink — share your services](https://docs.aws.amazon.com/vpc/latest/privatelink/privatelink-share-your-services.html)
  (verified 2026-07-31).

### AF-6 — Inspection: AWS Network Firewall vs third-party appliances (Gateway Load Balancer)
| Option | AWS Service | Optimizes | Sacrifices | Best When |
|---|---|---|---|---|
| AWS Network Firewall | AWS Network Firewall | Managed, HA, Suricata rules, native routing integration | Feature set vs specialized NGFW; no peering/GA inspection | Standard stateful FW/IPS with least ops |
| 3rd-party via GWLB | Gateway Load Balancer + partner appliance | Existing vendor features/licensing/parity | Appliance ops, scaling, licensing cost | Mandated vendor or advanced NGFW features |
- **Cost Profile:** Network Firewall = endpoint/hour + per-GB; GWLB = LB + appliance licensing/compute.
- **Scaling:** Network Firewall auto-scales; GWLB scales appliance fleet you manage.
- **Operational Burden:** Network Firewall lowest; appliances require patching/HA/scaling.
- **Lock-in:** Network Firewall AWS-native; GWLB path preserves vendor portability.
- **Ask The Architect:** "Do managed AWS Network Firewall capabilities meet the requirement, or is a
  specific vendor NGFW/licensing mandated? Remember Network Firewall can't inspect VPC-peering paths or
  Global Accelerator traffic."
- **Source:** [AWS Network Firewall — example architectures](https://docs.aws.amazon.com/network-firewall/latest/developerguide/architectures.html)
  (verified 2026-07-31).

### AF-7 — Global topology: single-Region TGW hub-spoke vs multi-Region (inter-Region peering) vs AWS Cloud WAN
| Option | AWS Service | Optimizes | Sacrifices | Best When |
|---|---|---|---|---|
| Single-Region hub-spoke | AWS Transit Gateway | Simplicity, one fabric | No global reach | One primary Region |
| Inter-Region peering | TGW inter-Region peering (unique ASN per TGW) | Global reach reusing TGW | Manual multi-TGW/route management | A few Regions, hands-on network team |
| Managed global WAN | AWS Cloud WAN | Central policy, global segmentation, monitoring | Newer abstraction; cost | Many Regions/branches needing unified policy |
- **Cost Profile:** Rises single-Region → inter-Region → Cloud WAN (managed premium).
- **Scaling:** Cloud WAN designed for large global estates; inter-Region peering for moderate scale.
- **Operational Burden:** Cloud WAN centralizes policy; manual inter-Region peering is more hands-on.
- **Lock-in:** All AWS-native; Cloud WAN highest abstraction.
- **Ask The Architect:** "How many Regions/branches and do you need centralized global segmentation
  policy (Cloud WAN) or is inter-Region TGW peering sufficient?"
- **Source:** [TGW design best practices (inter-Region, unique ASN)](https://docs.aws.amazon.com/vpc/latest/tgw/tgw-best-design-practices.html);
  [AWS VPC Connectivity Options — AWS Cloud WAN](https://docs.aws.amazon.com/whitepapers/latest/aws-vpc-connectivity-options/introduction.html)
  (verified 2026-07-31).

### AF-8 — Edge entry point: Amazon CloudFront vs AWS Global Accelerator
| Option | AWS Service | Optimizes | Sacrifices | Best When |
|---|---|---|---|---|
| CloudFront | Amazon CloudFront | HTTP(S) caching, dynamic/API acceleration, WAF/Shield attach | HTTP-centric; not for arbitrary TCP/UDP | Cacheable web content, API/dynamic HTTP delivery |
| Global Accelerator | AWS Global Accelerator | Static anycast IPs, TCP/UDP, deterministic fast regional failover | No caching | Gaming/UDP, IoT/MQTT, VoIP, or HTTP needing static IPs/fast failover |
- **Cost Profile:** Both edge-priced (requests/data); different models — validate against pricing docs.
- **Scaling:** Both use the AWS global edge; Global Accelerator emphasizes multi-Region failover.
- **Operational Burden:** CloudFront = cache-policy management; Global Accelerator = endpoint-group
  configuration.
- **Lock-in:** Both AWS-native.
- **Ask The Architect:** "Is the workload cacheable HTTP(S) (CloudFront) or non-HTTP / static-IP /
  fast-regional-failover (Global Accelerator)? Note Network Firewall can't inspect GA traffic."
- **Source:** [AWS Global Accelerator FAQs — CloudFront vs Global Accelerator](https://aws.amazon.com/global-accelerator/faqs/)
  (verified 2026-07-31).

---

# 4. Never-Do Anti-Patterns

> **TARGET_EDITION applies:** WAF 2024-11-06 + AWS networking service docs verified 2026-07-31.
> Every entry includes a side-by-side ❌ Wrong / ✅ Correct with exact AWS service names.

### ND-1 — 0.0.0.0/0 inbound on management ports (SSH/RDP)
- **Risk Level:** CRITICAL. **Pillar:** Security (apply security at all layers; least privilege).
- **Blast Radius:** Any instance with the SG → full internet-facing brute-force/exploit surface.
- ❌ **Wrong:** Security group inbound rule `TCP 22 (or 3389) from 0.0.0.0/0`.
- ✅ **Correct:** No public management ports — use **AWS Systems Manager Session Manager** (no inbound
  port), or restrict to a corporate prefix list / bastion **security-group reference**; SG source
  = `sg-<bastion>` or a managed prefix list, never `0.0.0.0/0`.
- **Detection:** AWS Config `restricted-ssh` / `restricted-common-ports`; AWS Security Hub; `aws
  ec2 describe-security-groups --filters Name=ip-permission.cidr,Values=0.0.0.0/0`.
- **Impact:** Data breach / instance compromise / lateral movement.
- **Source:** [Amazon VPC User Guide — security group rules](https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html)
  (verified 2026-07-31).

### ND-2 — Overlapping CIDRs across accounts/VPCs (unplanned)
- **Risk Level:** HIGH. **Pillar:** Reliability & Operational Excellence.
- **Blast Radius:** Permanently blocks Transit Gateway attachment, VPC peering, and Direct Connect
  gateway routing between the affected VPCs.
- ❌ **Wrong:** Two production VPCs both `10.0.0.0/16`, later required to interconnect via **AWS Transit
  Gateway** — attachment/routing fails.
- ✅ **Correct:** Allocate non-overlapping, hierarchical CIDRs from **Amazon VPC IPAM** pools up front;
  if overlap is unavoidable (merger/isolation), make it a conscious exception and bridge via a
  **private NAT Gateway + Transit Gateway** (routable/non-routable ranges).
- **Detection:** IPAM overlap monitoring; `aws ec2 describe-vpcs` CIDR audit across accounts.
- **Impact:** Cascading failure of interconnect plans; costly re-IP projects.
- **Source:** [Multi-VPC whitepaper — IP address planning](https://docs.aws.amazon.com/whitepapers/latest/building-scalable-secure-multi-vpc-network-infrastructure/ip-address-planning-and-management.html)
  (2024-04-17); [NAT gateway use cases — overlapping networks](https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-scenarios.html)
  (verified 2026-07-31). > ⚠️ Whitepaper dated 2024-04; verify currency.

### ND-3 — Data stores in public subnets
- **Risk Level:** CRITICAL. **Pillar:** Security.
- **Blast Radius:** Databases/caches directly reachable from the internet.
- ❌ **Wrong:** Amazon RDS / self-managed database on EC2 in a **public subnet** (route table has
  `0.0.0.0/0 → internet gateway`) with a public IP.
- ✅ **Correct:** Place data stores in **private/isolated subnets** (no IGW route); reach the internet
  (patching) only via **NAT Gateway** outbound; expose to app tier via **security-group reference**
  from the app SG; access AWS APIs via **VPC endpoints**.
- **Detection:** AWS Config `rds-instance-public-access-check`; audit route tables for IGW default route
  on data subnets; `aws ec2 describe-route-tables`.
- **Impact:** Data breach / exfiltration.
- **Source:** [NAT gateway use cases (public vs private subnet routing)](https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-scenarios.html)
  (verified 2026-07-31).

### ND-4 — No VPC Flow Logs
- **Risk Level:** HIGH. **Pillar:** Security & Operational Excellence (observability).
- **Blast Radius:** No connection-level visibility across the entire VPC; blind incident response.
- ❌ **Wrong:** VPCs created with **no VPC Flow Logs** configured.
- ✅ **Correct:** Enable **VPC Flow Logs** at VPC scope for ALL traffic to **Amazon S3** and/or
  **CloudWatch Logs / Amazon Data Firehose** on every VPC (ideally enforced by SCP/Config rule).
- **Detection:** AWS Config `vpc-flow-logs-enabled`; `aws ec2 describe-flow-logs`.
- **Impact:** Undetected exfiltration; failed forensics/compliance.
- **Source:** [Multi-VPC whitepaper — network security](https://docs.aws.amazon.com/whitepapers/latest/building-scalable-secure-multi-vpc-network-infrastructure/welcome.html)
  (2024-04-17); Amazon VPC User Guide "VPC Flow Logs" (verified 2026-07-31). > ⚠️ Whitepaper dated
  2024-04; verify currency.

### ND-5 — Full-mesh VPC peering at scale
- **Risk Level:** HIGH. **Pillar:** Operational Excellence & Reliability.
- **Blast Radius:** O(n²) non-transitive links become unmanageable; route-table and SG sprawl.
- ❌ **Wrong:** Peer every VPC to every other VPC (e.g., 20 VPCs → 190 **VPC peering** connections),
  each needing route entries and stale-SG-rule risk.
- ✅ **Correct:** Interconnect through an **AWS Transit Gateway** hub-spoke (one attachment per VPC,
  transitive routing, TGW route tables for segmentation); "highly available by design."
- **Detection:** `aws ec2 describe-vpc-peering-connections | length`; flag > small N with growth.
- **Impact:** Operational failure; connectivity gaps; MTU-mismatch packet drops during migration.
- **Source:** [TGW design best practices (incl. peering-to-TGW migration/MTU)](https://docs.aws.amazon.com/vpc/latest/tgw/tgw-best-design-practices.html)
  (verified 2026-07-31).

### ND-6 — Over-broad security groups referencing wide CIDRs instead of SG references
- **Risk Level:** HIGH. **Pillar:** Security (least privilege).
- **Blast Radius:** East-west lateral movement across an entire CIDR range.
- ❌ **Wrong:** Web/DB tier SG allows the app port `from 10.0.0.0/8` (or `0.0.0.0/0`).
- ✅ **Correct:** DB SG allows the DB port **from the web-tier security group** (`sg-...`), web SG
  allows 80/443 **from the load-balancer security group** — SG referencing scopes access to group
  members, not IP ranges (works within VPC, across peering, across Transit Gateway inbound).
- **Detection:** `aws ec2 describe-security-groups` — flag east-west rules whose source is a wide CIDR
  rather than a `sg-` reference; AWS Config custom rule.
- **Impact:** Cascading compromise / lateral movement.
- **Source:** [Amazon VPC User Guide — security group referencing](https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html)
  (verified 2026-07-31).

### ND-7 — Private subnets with unmanaged / missing egress control
- **Risk Level:** HIGH. **Pillar:** Security & Cost.
- **Blast Radius:** Either no egress (broken workloads) or uncontrolled egress (exfiltration path, cost
  surprises).
- ❌ **Wrong:** Private subnets with a direct `0.0.0.0/0 → internet gateway` route (making them public),
  OR no egress path and no inspection at all.
- ✅ **Correct:** Private subnets route `0.0.0.0/0` to a per-AZ **NAT Gateway**; for AWS APIs use
  **Gateway/Interface VPC endpoints**; at scale, route egress through a **centralized egress/inspection
  VPC** (AWS Network Firewall) via **Transit Gateway** and filter DNS with **Route 53 Resolver DNS
  Firewall**.
- **Detection:** `aws ec2 describe-route-tables` (IGW route on "private" subnets); AWS Config; Network
  Firewall/Flow Logs for egress destinations.
- **Impact:** Data exfiltration / cost overrun / outage.
- **Source:** [NAT gateway use cases](https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-scenarios.html);
  [Multi-VPC whitepaper — centralized egress](https://docs.aws.amazon.com/whitepapers/latest/building-scalable-secure-multi-vpc-network-infrastructure/welcome.html)
  (2024-04-17, verified 2026-07-31). > ⚠️ Whitepaper dated 2024-04; verify currency.

### ND-8 — No hybrid DNS strategy
- **Risk Level:** MEDIUM. **Pillar:** Reliability & Operational Excellence.
- **Blast Radius:** Name-resolution failures between AWS and on-prem; brittle hard-coded IPs.
- ❌ **Wrong:** Hard-coding IPs, or relying on default VPC DNS with no way to resolve on-prem zones
  (and no way for on-prem to resolve private AWS zones).
- ✅ **Correct:** Deploy **Amazon Route 53 VPC Resolver** outbound endpoint + forwarding rules for
  on-prem zones, an inbound endpoint for on-prem→AWS resolution, **private hosted zones** for internal
  names, and share **Resolver rules** across accounts via **AWS RAM**; endpoints in ≥2 AZs.
- **Detection:** `aws route53resolver list-resolver-endpoints` / `list-resolver-rules`; test both
  directions.
- **Impact:** Service outage / fragile integrations.
- **Source:** [Amazon Route 53 — What is Route 53 VPC Resolver?](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver.html)
  (verified 2026-07-31).

### ND-9 — Single-AZ NAT Gateway (or single-AZ egress dependency) for production
- **Risk Level:** HIGH. **Pillar:** Reliability.
- **Blast Radius:** All private subnets routed through one AZ's NAT lose internet egress if that AZ
  fails.
- ❌ **Wrong:** One **NAT Gateway** in AZ-A; private subnets in AZ-A **and** AZ-B both default-route to
  it.
- ✅ **Correct:** One **NAT Gateway per AZ**; each private subnet routes `0.0.0.0/0` to the NAT Gateway
  **in its own AZ** — AWS: "improve resiliency by creating a NAT gateway in each Availability Zone that
  contains resources that require internet access." (Same principle applies to per-AZ TGW attachments.)
- **Detection:** `aws ec2 describe-nat-gateways` (count vs AZ count); cross-check private route tables
  point to same-AZ NAT.
- **Impact:** AZ-scoped outage of all egress-dependent workloads.
- **Source:** [Amazon VPC User Guide — NAT gateway use cases](https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-scenarios.html)
  (verified 2026-07-31).

---

# 5. Service Equivalence Map (Networking Service Classes)

> ⚠️ **Important:** Equivalence ≠ feature parity. Each service has distinct capabilities, limits,
> pricing, and regional availability. Validate against each provider's current docs before deciding.
> AWS column verified against AWS docs 2026-07-31; GCP/Azure/OCI columns are class-level mappings for
> orientation (see Provider Differentiators) and should be re-verified against those providers' docs.

| Networking Class | AWS | Google Cloud | Azure | Oracle Cloud (OCI) |
|---|---|---|---|---|
| Virtual network | Amazon VPC | VPC network | Virtual Network (VNet) | Virtual Cloud Network (VCN) |
| Subnet / AZ construct | VPC subnet (per-AZ) | Subnet (regional) | Subnet | Subnet (regional/AD) |
| Application load balancing (L7) | Application Load Balancer | Cloud Load Balancing (HTTP(S)) | Application Gateway | Load Balancer (L7) |
| Network load balancing (L4) | Network Load Balancer | Cloud Load Balancing (TCP/UDP) | Load Balancer (L4) | Network Load Balancer |
| DNS (authoritative) | Amazon Route 53 (hosted zones) | Cloud DNS | Azure DNS | OCI DNS |
| DNS resolver / hybrid | Route 53 VPC Resolver (in/out endpoints) | Cloud DNS inbound/outbound forwarding | Azure DNS Private Resolver | OCI DNS (private views/resolvers) |
| CDN | Amazon CloudFront | Cloud CDN / Media CDN | Azure Front Door / CDN | OCI CDN |
| Global anycast acceleration | AWS Global Accelerator | (Global external LB anycast) | Azure Front Door (anycast) | (Global LB) |
| Private service connectivity | AWS PrivateLink (interface endpoints) | Private Service Connect | Azure Private Link | OCI Private Endpoint / Service Gateway |
| Object-store private path | Gateway VPC endpoint (S3, DynamoDB) | Private Google Access / PSC | Service Endpoints / Private Endpoint | Service Gateway |
| Transit / hub | AWS Transit Gateway | Network Connectivity Center | Virtual WAN / VNet peering hub | OCI DRG (Dynamic Routing Gateway) |
| Managed global WAN | AWS Cloud WAN | Network Connectivity Center | Azure Virtual WAN | OCI DRG + FastConnect fabric |
| Service-to-service (L7) mesh | Amazon VPC Lattice | (Traffic Director / service mesh) | (Service mesh add-ons) | (Service mesh add-ons) |
| Network firewall (managed) | AWS Network Firewall | Cloud NGFW / firewall policies | Azure Firewall | OCI Network Firewall |
| Instance/subnet allow-lists | Security Groups + Network ACLs | Firewall rules | Network Security Groups (NSGs) | Security Lists + Network Security Groups |
| NAT (outbound) | NAT Gateway (public/private) | Cloud NAT | NAT Gateway | NAT Gateway |
| VPN (IPsec) | AWS Site-to-Site VPN | Cloud VPN | VPN Gateway | OCI Site-to-Site VPN |
| Dedicated interconnect | AWS Direct Connect | Cloud Interconnect | ExpressRoute | OCI FastConnect |
| Global routing/traffic mgmt | Route 53 (latency/failover/geo) | Cloud DNS routing policies | Traffic Manager / Front Door | OCI Traffic Management |
| WAF (edge/app) | AWS WAF | Cloud Armor | Azure WAF | OCI WAF |
| DDoS protection | AWS Shield / Shield Advanced | Cloud Armor (DDoS) | Azure DDoS Protection | OCI DDoS protection |
| Flow logging | VPC Flow Logs | VPC Flow Logs | NSG flow logs / VNet flow logs | VCN Flow Logs |
| IP address management | Amazon VPC IPAM | (IPAM via tooling) | Azure IPAM (Virtual Network Manager) | (IPAM via tooling) |

---

# 6. Provider Differentiators (Networking-relevant)

- **AWS Transit Gateway + AWS Cloud WAN** — a mature regional hub (HA by design, inter-Region peering,
  unique-ASN multi-TGW) plus a managed global WAN with central segmentation policy. Decisive for large
  multi-account/multi-Region estates.
  (Source: [TGW design best practices](https://docs.aws.amazon.com/vpc/latest/tgw/tgw-best-design-practices.html),
  verified 2026-07-31.)
- **Amazon VPC Lattice** — L7 service networking with IAM auth policies, DNS-based discovery, **AZ
  affinity with no inter-AZ data-transfer charge**, and **overlapping-CIDR support** — differentiates
  from pure L3 fabrics for microservice connectivity.
  (Source: [VPC Lattice overview](https://docs.aws.amazon.com/vpc-lattice/latest/ug/what-is-vpc-lattice.html),
  verified 2026-07-31.)
- **AWS PrivateLink cross-Region access** — expose an endpoint service in supported Regions with
  `vpce:AllowMultiRegion`, while AWS manages AZ failover (not cross-Region failover).
  (Source: [PrivateLink — share your services / cross-Region](https://docs.aws.amazon.com/vpc/latest/privatelink/privatelink-share-your-services.html),
  verified 2026-07-31.)
- **AWS Global Accelerator** — static anycast IPs proxying TCP/UDP over the AWS backbone with
  deterministic fast regional failover — a distinct edge primitive from the CloudFront CDN.
  (Source: [Global Accelerator FAQs](https://aws.amazon.com/global-accelerator/faqs/), verified 2026-07-31.)
- **Amazon VPC IPAM** — actively allocates/tracks/monitors IPv4+IPv6 hierarchically across accounts and
  Regions with business-rule auto-allocation and Control Tower integration.
  (Source: [Multi-VPC whitepaper — IPAM](https://docs.aws.amazon.com/whitepapers/latest/building-scalable-secure-multi-vpc-network-infrastructure/ip-address-planning-and-management.html),
  2024-04-17, verified 2026-07-31.) > ⚠️ Source dated 2024-04; verify currency.

---

# Scenario Coverage

**Standard Case — three-tier web app in a multi-account estate.** Workload VPC with public
(ALB), private (app), isolated (RDS) subnets across ≥2 AZs; per-AZ NAT Gateway; S3/DynamoDB Gateway
endpoints + interface endpoints for other AWS APIs; SG referencing between tiers; VPC Flow Logs on;
CloudFront + AWS WAF + Shield at the edge; the VPC is a **spoke off a regional AWS Transit Gateway**;
CIDRs allocated from IPAM. *Key decisions:* centralized vs distributed egress (AF-2), and whether the
app is exposed to other accounts via PrivateLink or Lattice (AF-1, AF-5).

**Edge Case — overlapping CIDRs after an acquisition.** Two VPCs both `10.0.0.0/16` must
interoperate. *Approach:* keep original ranges non-routable, assign routable ranges, and bridge with a
**private NAT Gateway + Transit Gateway** (per the documented overlapping-networks pattern), or expose
only specific services via **AWS PrivateLink** / **Amazon VPC Lattice** (both tolerate overlapping
CIDRs) — avoiding a full re-IP.

**Anti-Pattern Case — "just peer everything and open the SGs."** Refuse/flag: full-mesh VPC
peering and wide-CIDR SG rules (ND-5, ND-6). *Clarify before proceeding:* expected VPC count and growth,
whether CIDRs overlap, segmentation/compliance needs, and the egress/inspection model — then route to
TGW hub-spoke with SG references and (if warranted) centralized inspection.

---

# Compliance & Cost — Deferred to Ask-First (Guardrails)

Per the skill contract and CLAUDE.md principles, the following were **not** asserted and are surfaced
for the user/architect to confirm:

- **Compliance regimes (PCI-DSS, HIPAA, GDPR, data residency).** No single regime was assumed. If one
  applies, it changes region strategy (AF-4), egress/inspection (AF-2/AF-6), encryption-in-transit
  requirements, and logging retention. Escalate before adding compliance-specific constraints.
- **Exact pricing and service quotas.** No specific NAT Gateway/TGW/PrivateLink/Direct Connect prices
  or numeric quotas were invented. Where a decision needs a number (e.g., rules-per-SG, endpoints-per-VPC,
  DX bandwidth tiers), verify against the current AWS pricing / service-quotas pages before committing.
- **Cost-optimization commitments** (Savings Plans, committed use, reserved capacity) are
  organization-specific — Ask-First.

---

# Source Bibliography

All URLs accessed/verified **2026-07-31** unless noted. Sources > 12 months flagged.

### Primary — Official AWS Documentation (current, continuously published)
- AWS Well-Architected Framework — welcome / pillars — **publication date 2024-11-06** (current stable).
  https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html
  > ⚠️ Edition dated 2024-11; current stable — re-verify if a newer edition ships.
- Amazon VPC — Transit gateway design best practices.
  https://docs.aws.amazon.com/vpc/latest/tgw/tgw-best-design-practices.html
- Amazon VPC — NAT gateway use cases (multi-AZ, private NAT, overlapping networks).
  https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-scenarios.html
- Amazon VPC — Security group rules (referencing, size, stale rules).
  https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html
- AWS PrivateLink — Share your services (endpoint services, cross-Region, IPv6, zonal endpoints).
  https://docs.aws.amazon.com/vpc/latest/privatelink/privatelink-share-your-services.html
- AWS PrivateLink — Access an AWS service using an interface VPC endpoint.
  https://docs.aws.amazon.com/vpc/latest/privatelink/create-interface-endpoint.html
- Amazon VPC Lattice — What is Amazon VPC Lattice? (service networking, AZ affinity, overlapping CIDR).
  https://docs.aws.amazon.com/vpc-lattice/latest/ug/what-is-vpc-lattice.html
- Amazon Route 53 — What is Route 53 VPC Resolver? (renamed; inbound/outbound endpoints, hybrid DNS).
  https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver.html
- AWS Direct Connect — Configure high resiliency (Resiliency Toolkit).
  https://docs.aws.amazon.com/directconnect/latest/UserGuide/high_resiliency.html
- AWS Network Firewall — Example architectures with routing (distributed/centralized; unsupported paths).
  https://docs.aws.amazon.com/network-firewall/latest/developerguide/architectures.html

### Primary — Official AWS Whitepapers
- Building a Scalable and Secure Multi-VPC AWS Network Infrastructure — **publication date 2024-04-17**.
  https://docs.aws.amazon.com/whitepapers/latest/building-scalable-secure-multi-vpc-network-infrastructure/welcome.html
  https://docs.aws.amazon.com/whitepapers/latest/building-scalable-secure-multi-vpc-network-infrastructure/ip-address-planning-and-management.html
  > ⚠️ Source dated 2024-04 (~27 months at research time); current published version — verify currency.
- Amazon VPC Connectivity Options (network-to-VPC and VPC-to-VPC options; Cloud WAN).
  https://docs.aws.amazon.com/whitepapers/latest/aws-vpc-connectivity-options/introduction.html
  > Note: publication date not shown on the fetched page; treated as current continuously-published
  > whitepaper, verified 2026-07-31.
- AWS PrivateLink whitepaper — What are VPC endpoints (gateway vs interface).
  https://docs.aws.amazon.com/whitepapers/latest/aws-privatelink/what-are-vpc-endpoints.html

### Primary — Official AWS Service Pages
- AWS Global Accelerator FAQs (CloudFront vs Global Accelerator positioning).
  https://aws.amazon.com/global-accelerator/faqs/

### Companion Research (this repository)
- research_cloud_AWS_VPC_Networking_2026-07.md — VPC internals (subnets, route tables, NACL/SG
  mechanics, IGW/NAT plumbing, CIDR sizing). Cross-referenced throughout; not duplicated here.

---

# Verification Loop (self-check performed)

- [x] TARGET_EDITION (WAF 2024-11-06 + docs verified 2026-07-31) in metadata and each major section.
- [x] All 6 mandatory sections present: Framework Pillars, Always-Do, Ask-First, Never-Do, Service
      Equivalence Map, Source Bibliography (+ Executive Summary, Glossary, Differentiators, Scenarios).
- [x] Every Always-Do and Never-Do cites an official AWS URL with access/verification date.
- [x] Every Never-Do (ND-1..ND-9) has side-by-side ❌ Wrong / ✅ Correct with exact AWS service names.
- [x] All sources dated; sources > 12 months (WAF 2024-11, Multi-VPC whitepaper 2024-04) flagged with
      ⚠️; VPC Connectivity Options undated flagged explicitly.
- [x] Service Equivalence Map covers all researched classes (VPC, LB, DNS, CDN, private connectivity,
      transit/hub, firewall, NAT, global routing, VPN, dedicated interconnect, + more).
- [x] Exact AWS service names used throughout; no generic terms where a canonical name exists.
- [x] Compliance and exact pricing/quotas deferred to Ask-First (not asserted).
- Recommended next step: run `/skill-best-practices-validator` on this output.
