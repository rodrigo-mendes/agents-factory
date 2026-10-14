# Multi-Cloud Networking Architecture — Hub-Spoke vs Mesh Topology

## Metadata

```yaml
Full_Name: "Multi-Cloud Networking Architecture — Hub-Spoke vs Mesh Topology"
Cloud_Provider: "Multi-Cloud (AWS, Azure, Google Cloud)"
Architecture_Domain: "Networking Architecture"
Target_Edition:
  AWS: "AWS Well-Architected Framework 2024"
  Azure: "Azure Cloud Adoption Framework (CAF), November 2024"
  Google_Cloud: "Google Cloud Architecture Framework 2024"
Architecture_Context: "Hybrid enterprise network"
Output_Format: "Comparison matrix"
Primary_Audience: "Cloud Architects evaluating topology"
Research_Date: "2026-08-28"
Currency_Threshold: "2027-08-28 — review after this date; several cited service quotas evolve quarterly"
Confidence_Note: "All CROSS-PROVIDER comparisons are marked 🟡 Medium Confidence per skill guardrail. Single-provider facts sourced to official docs are 🟢 High Confidence."
```

> ⚠️ **Scope confirmation (Ask-First resolved):** Multi-cloud scope was pre-confirmed as **comparison matrix** format. No further scoping question required. This document does **not** issue compliance-specific or billing-specific prescriptions (those remain Low Confidence / Ask-First per skill).

> ⚠️ Several sources below are dated 2025 (GA announcements). They reflect the **current stable** state of the services and are retained per the source-hierarchy rule (current stable overrides the 12-month flag). Individual dated notes appear inline.

---

## Executive Summary

Enterprise hybrid networks converge on two canonical intra-cloud topologies: **hub-spoke** (a centralized transit/inspection hub that all workload networks attach to) and **mesh** (direct network-to-network peering with no central transit). Each of AWS, Azure, and Google Cloud provides a **managed hub service** that supersedes self-managed transit VMs, and a **native peering primitive** for mesh. This document maps those services by exact provider name, assesses lock-in per topology, and surfaces the provider-specific constraints (quotas, GA status) that decide topology at enterprise scale.

The decisive architectural fact across all three providers is that **native peering is non-transitive** — AWS VPC Peering, Azure VNet Peering, and Google Cloud VPC Network Peering all require an explicit peering per communicating pair. A full mesh therefore grows as O(n²) connections, which is why the managed hub services (AWS Transit Gateway, Azure Virtual WAN, GCP Network Connectivity Center) exist: they provide transitive routing through a central hub, reducing an n-network topology from ~n²/2 peerings to n attachments. For a **hybrid enterprise network** the hub service is also the natural attachment point for on-premises connectivity (Direct Connect / ExpressRoute / Cloud Interconnect), which is why all three vendors position hub-spoke as the default enterprise landing-zone topology.

The three most critical guardrails for a hybrid enterprise network are: (1) plan a **non-overlapping global CIDR** across every cloud and on-prem before any attachment is created — overlapping ranges cannot be routed through a hub; (2) prefer the **managed hub** over self-managed transit appliances for transitive routing and centralized inspection; and (3) treat mesh peering as a **point optimization** for a small number of high-throughput, latency-sensitive network pairs, not as a scaling topology.

---

## Cloud Architecture Glossary

```
Term: Transit Gateway (TGW)
Definition: AWS regional network transit hub that interconnects VPCs and on-premises networks
  with transitive routing; attachments include VPC, VPN, Direct Connect gateway, TGW Connect, peering.
Provider Docs Section: Amazon VPC — Transit Gateways
Architect Usage: The AWS hub-spoke transit primitive. One TGW per region; peer TGWs across regions.
Common Confusion: Often confused with Azure Virtual WAN (a broader managed WAN service, not a bare hub)
  and with GCP Network Connectivity Center (a control-plane hub, not a data-plane appliance).
```
```
Term: Azure Virtual WAN (Virtual WAN)
Definition: Microsoft-managed networking service that unifies hub-spoke, branch (site-to-site VPN),
  point-to-site VPN, ExpressRoute, and inter-hub transit into managed virtual hubs.
Provider Docs Section: Azure Virtual WAN documentation; CAF network topology and connectivity.
Architect Usage: The Azure managed hub-spoke primitive; the hub is Microsoft-managed (vs a self-built hub VNet).
Common Confusion: Confused with a customer-managed "hub VNet" hub-spoke (the traditional CAF pattern that
  predates Virtual WAN). Both are valid CAF topologies; Virtual WAN is the managed evolution.
```
```
Term: Network Connectivity Center (NCC)
Definition: Google Cloud hub-and-spoke connectivity management service; a hub resource with VPC spokes,
  hybrid spokes (VPN/Interconnect/Router appliance), and producer VPC spokes for transitive data-plane routing.
Provider Docs Section: Network Connectivity Center — VPC spokes overview.
Architect Usage: The GCP managed hub-spoke primitive. VPC spokes give transitive routing between spoke VPCs.
Common Confusion: Confused with plain VPC Network Peering (non-transitive mesh) and with Shared VPC
  (a single VPC shared across projects — not a hub-spoke of separate VPCs).
```
```
Term: Non-transitive peering
Definition: A peering relationship where traffic is exchanged only between the two directly peered networks;
  a network reachable via an intermediate peer is NOT reachable. A↔B and B↔C does not yield A↔C.
Provider Docs Section: AWS VPC Peering; Azure Virtual Network peering; GCP VPC Network Peering.
Architect Usage: Governs mesh scaling — full mesh needs n(n-1)/2 peerings. Drives the choice of a hub.
Common Confusion: Architects assume a "peered-to-the-hub" spoke can reach other spokes via plain peering — it cannot;
  transitive routing requires a transit service (TGW / Virtual WAN / NCC), not peering.
```
```
Term: Hub-spoke topology
Definition: A star topology where all workload networks (spokes) attach to a central transit/inspection network (hub);
  spoke-to-spoke traffic transits the hub.
Architect Usage: Default enterprise landing-zone topology; centralizes egress, inspection, and hybrid connectivity.
Common Confusion: Confused with mesh; the distinguishing property is the presence of a transit hub with transitive routing.
```
```
Term: Mesh topology
Definition: A topology where networks connect directly to one another (typically via native peering) with no central transit.
Architect Usage: Minimizes hop count/latency and per-GB transit cost for a small set of high-traffic pairs.
Common Confusion: "Full mesh" is frequently proposed at enterprise scale where it becomes unmanageable (O(n²) peerings).
```

---

## Architecture Guardrails

### ✅ Mandatory Patterns

**Non-overlapping global CIDR plan before any attachment** 🟢 High Confidence (per-provider docs)
- Pillar Alignment: Reliability / Operational Excellence (all three frameworks)
- Why: Hubs perform route propagation across attachments; overlapping IP ranges cannot be routed transitively and cannot be remediated without re-addressing. AWS TGW, Azure Virtual WAN, and GCP NCC all require unique, non-overlapping ranges across attached networks.
- Services: AWS Transit Gateway route tables; Azure Virtual WAN hub routing; GCP NCC hub routing.
- Architecture Decision: Allocate a single enterprise supernet, carve per-cloud and per-region blocks, reserve on-prem ranges — before creating spokes.
- Verification: AWS `aws ec2 search-transit-gateway-routes`; Azure `az network vhub get-effective-routes`; GCP `gcloud network-connectivity hubs describe` + effective routes on spoke VPC.
- Source: [AWS TGW quotas/routing](https://docs.aws.amazon.com/vpc/latest/tgw/transit-gateway-quotas.html); [Azure Virtual WAN network topology](https://learn.microsoft.com/en-us/azure/networking/design-guide/virtual-wan); [GCP VPC spokes overview](https://cloud.google.com/network-connectivity/docs/network-connectivity-center/concepts/vpc-spokes-overview). Accessed 2026-08-28.

**Use the managed hub for transitive routing (not self-managed transit VMs)** 🟢 High Confidence (per-provider docs)
- Pillar Alignment: Operational Excellence, Reliability.
- Why: Managed hubs remove the operational burden and single-point-of-failure risk of self-run router appliances and provide native transitive routing.
- Services: AWS Transit Gateway; Azure Virtual WAN (virtual hub); GCP Network Connectivity Center (VPC spokes).
- Architecture Decision: Attach each workload network as a spoke to the regional managed hub; centralize hybrid connectivity and egress inspection at the hub.
- Verification: Confirm spoke attachment status is active/associated in each provider's console/CLI.
- Source: [Azure hub-spoke via Virtual WAN](https://learn.microsoft.com/en-us/azure/architecture/networking/architecture/hub-spoke-virtual-wan-architecture); [GCP NCC hubs & spokes](https://cloud.google.com/network-connectivity/docs/network-connectivity-center/concepts/overview); [AWS TGW](https://docs.aws.amazon.com/vpc/latest/tgw/what-is-transit-gateway.html). Accessed 2026-08-28.

### ⚠️ Architectural Decisions

**Hub-spoke vs Mesh (the core decision this document scopes)** 🟡 Medium Confidence (cross-provider)

- Options:

  | Option | AWS Service | Azure Service | GCP Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|---------------|-------------|-----------|------------|-----------|
  | **Hub-spoke** | AWS Transit Gateway | Azure Virtual WAN | GCP Network Connectivity Center | Transitive routing, centralized inspection/egress, hybrid attach, O(n) scaling | Per-GB transit/data-processing cost, extra hop latency | Enterprise scale, hybrid on-prem, centralized security |
  | **Mesh** | AWS VPC Peering | Azure VNet Peering | GCP VPC Network Peering | Lowest latency (direct), no transit data-processing charge | Non-transitive → O(n²) peerings, no central inspection | Few high-throughput, latency-sensitive network pairs |

- Cost Profile (🟡 Medium, relative — not a billing prescription): Hub-spoke adds a per-hour hub/attachment charge plus a per-GB data-processing charge on transit traffic. Mesh peering typically avoids the transit-processing charge but still incurs inter-AZ/inter-region data transfer where applicable. Confirm current rates against each provider's pricing page before committing.
- Scaling Characteristics: Mesh grows as n(n-1)/2 peerings (non-transitive on all three providers). Hub-spoke grows linearly with spokes but is bounded by per-hub quotas (see Provider-Specific Constraints below).
- Operational Burden: Hub-spoke centralizes route management at the hub; mesh distributes route-table maintenance across every network pair.
- Lock-in Assessment: see the dedicated **Lock-in Assessment** section below.
- Architect Instruction: "Ask whether spoke-to-spoke transitive routing and centralized egress inspection are required. If yes → hub-spoke. If only a few named network pairs need direct high-throughput low-latency paths and no central inspection is required → mesh (or a hybrid: hub-spoke baseline plus selective peering shortcuts)."
- Source: per-provider links in the table above + [GCP VPC Network Peering (non-transitive)](https://cloud.google.com/vpc/docs/vpc-peering). Accessed 2026-08-28.

### 🚫 Anti-Patterns

**Assuming spoke-to-spoke reachability through plain peering to a hub** 🟢 High Confidence
- Risk Level: HIGH
- Why: Native peering is non-transitive on AWS, Azure, and GCP. A spoke peered to a hub VNet/VPC cannot reach another spoke via that peering.
- ❌ Wrong: Two spoke VPCs each peered to a "hub" VPC via AWS VPC Peering and expecting spoke-A ↔ spoke-B connectivity.
- ✅ Correct: Attach both spokes to an **AWS Transit Gateway** (transitive) — or on GCP use **NCC VPC spokes**, on Azure use **Virtual WAN** hub routing.
- Detection: Effective-routes check on the spoke shows no route to the other spoke's CIDR.
- Impact: Service outage / silent connectivity failure.
- Source: [GCP VPC Network Peering — no transitive routing](https://cloud.google.com/vpc/docs/vpc-peering); [Azure VNet peering + spoke-to-spoke](https://learn.microsoft.com/en-us/azure/architecture/reference-architectures/hybrid-networking/virtual-network-peering). Accessed 2026-08-28.

**Full mesh at enterprise scale** 🟡 Medium Confidence (cross-provider generalization)
- Risk Level: MEDIUM
- Why: n(n-1)/2 non-transitive peerings become unmanageable and hit per-network peering quotas.
- ❌ Wrong: 40 VNets each peered to every other VNet (780 VNet peerings) with no central inspection.
- ✅ Correct: Attach the 40 VNets as spokes to **Azure Virtual WAN**; add selective VNet Peering only for the few pairs needing a direct low-latency shortcut.
- Detection: Peering count per network approaching provider limits; route-table sprawl.
- Impact: Operational overload / change-failure risk.
- Source: [Azure Virtual WAN massive-scale design](https://learn.microsoft.com/en-us/azure/architecture/networking/architecture/massive-scale-azure-architecture). Accessed 2026-08-28.

**Overlapping CIDR across spokes / clouds** 🟢 High Confidence
- Risk Level: CRITICAL
- Why: Transitive hubs cannot route overlapping ranges; remediation requires re-addressing.
- ❌ Wrong: Two spokes both using 10.0.0.0/16 attached to the same hub.
- ✅ Correct: Unique blocks from a planned enterprise supernet per spoke and per cloud.
- Detection: Route-conflict / attachment-rejection errors at the hub.
- Impact: Cascading connectivity failure across the hybrid network.
- Source: [AWS TGW quotas](https://docs.aws.amazon.com/vpc/latest/tgw/transit-gateway-quotas.html); [GCP VPC spokes overview](https://cloud.google.com/network-connectivity/docs/network-connectivity-center/concepts/vpc-spokes-overview). Accessed 2026-08-28.

---

## Required Output 1 & 2 — Exact Service Names by Topology

🟡 **Medium Confidence** (cross-provider comparison — per-provider source links included)

### Hub-Spoke transit services (Output 1)

| Provider | Exact Service Name | Role | Source |
|----------|--------------------|------|--------|
| **AWS** | **AWS Transit Gateway** | Regional transitive transit hub for VPC/VPN/Direct Connect attachments | [docs](https://docs.aws.amazon.com/vpc/latest/tgw/what-is-transit-gateway.html) |
| **Azure** | **Azure Virtual WAN** | Managed virtual hub unifying spoke VNets, VPN, ExpressRoute, inter-hub transit | [docs](https://learn.microsoft.com/en-us/azure/architecture/networking/architecture/hub-spoke-virtual-wan-architecture) |
| **Google Cloud** | **GCP Network Connectivity Center** | Hub resource with VPC spokes providing transitive routing | [docs](https://cloud.google.com/network-connectivity/docs/network-connectivity-center/concepts/overview) |

### Mesh peering services (Output 2)

| Provider | Exact Service Name | Role | Source |
|----------|--------------------|------|--------|
| **AWS** | **AWS VPC Peering** | Direct, non-transitive VPC-to-VPC connection | [docs](https://docs.aws.amazon.com/vpc/latest/peering/what-is-vpc-peering.html) |
| **Azure** | **Azure VNet Peering** (Virtual Network peering) | Direct, non-transitive VNet-to-VNet connection | [docs](https://learn.microsoft.com/en-us/azure/virtual-network/virtual-network-peering-overview) |
| **Google Cloud** | **GCP VPC Peering** (VPC Network Peering) | Direct, non-transitive VPC-to-VPC connection | [docs](https://cloud.google.com/vpc/docs/vpc-peering) |

---

## Required Output 3 — Service Equivalence Map (Networking Primitives)

🟡 **Medium Confidence** — equivalence ≠ feature parity. Validate each against its target edition before deciding.

| Networking Primitive | AWS | Azure | Google Cloud |
|----------------------|-----|-------|--------------|
| **Virtual network** | VPC (Virtual Private Cloud) | Virtual Network (VNet) | VPC network (global) |
| **Hub-spoke transit hub** | AWS Transit Gateway | Azure Virtual WAN (virtual hub) | Network Connectivity Center (hub + VPC spokes) |
| **Mesh peering** | AWS VPC Peering | Azure VNet Peering | GCP VPC Network Peering |
| **Cross-region transit** | Transit Gateway peering (inter-region) | Virtual WAN hub-to-hub (any-to-any) | NCC hub (VPC network is global) |
| **Dedicated hybrid link** | AWS Direct Connect | Azure ExpressRoute | Cloud Interconnect |
| **Site-to-site VPN** | AWS Site-to-Site VPN | Azure VPN Gateway (S2S) | Cloud VPN (HA VPN) |
| **Private service access** | AWS PrivateLink | Azure Private Link | Private Service Connect |
| **Managed NAT egress** | NAT Gateway | Azure NAT Gateway | Cloud NAT |
| **Network firewall (hub inspection)** | AWS Network Firewall | Azure Firewall (in Virtual WAN secured hub) | Cloud NGFW / firewall policies |
| **Route table (transit)** | Transit Gateway route table | Virtual WAN hub route table | NCC hub routing / VPC routes |
| **Global load balancer** | CloudFront + Global Accelerator / ALB | Azure Front Door / Application Gateway | Cloud Load Balancing (global) |
| **DNS (private)** | Route 53 Private Hosted Zones | Azure Private DNS | Cloud DNS (private zones) |

> ⚠️ Key non-parity note: A GCP **VPC network is global** (subnets are regional), so a single VPC can span regions without a hub for intra-VPC traffic — a structural difference from AWS/Azure where VPC/VNet are regional. This changes when a hub is actually needed on GCP.

---

## Required Output 4 — Lock-in Assessment per Topology, per Provider

🟡 **Medium Confidence** (cross-provider comparison)

### Hub-Spoke lock-in

| Provider | Service | Lock-in Level | Rationale / Portability Notes |
|----------|---------|---------------|-------------------------------|
| **AWS** | Transit Gateway | Medium-High | TGW route tables, attachment model, and TGW peering are AWS-specific constructs. Migrating to another cloud means rebuilding the transit design; IaC (CloudFormation/Terraform) eases in-cloud rebuild but not cross-cloud portability. |
| **Azure** | Virtual WAN | High | Virtual WAN is a Microsoft-managed abstraction (managed hubs, hub routing, integrated VPN/ExpressRoute). Moving off Virtual WAN even within Azure (to customer-managed hub VNet) is a redesign; cross-cloud migration is a full re-architecture. |
| **Google Cloud** | Network Connectivity Center | Medium-High | NCC hub/spoke resource model is GCP-specific. GCP's global VPC can reduce hub dependence for intra-VPC cases, slightly lowering lock-in vs a mandatory hub, but NCC constructs do not port across clouds. |

### Mesh lock-in

| Provider | Service | Lock-in Level | Rationale / Portability Notes |
|----------|---------|---------------|-------------------------------|
| **AWS** | VPC Peering | Low-Medium | Peering is a thin, standard construct; the *concept* ports across clouds (all three have equivalent peering). Route-table entries are per-cloud but the mesh design pattern is transferable. |
| **Azure** | VNet Peering | Low-Medium | Same as AWS — standard 1:1 peering concept; Gateway Transit feature is Azure-specific but optional. |
| **Google Cloud** | VPC Network Peering | Low-Medium | Standard peering; global-VPC model means fewer peerings needed intra-region. Custom route import/export is a GCP-specific nuance. |

> Summary: **Mesh is lower lock-in than hub-spoke on every provider** because the peering primitive is conceptually portable, whereas each managed hub (TGW / Virtual WAN / NCC) is a proprietary transit abstraction. Azure Virtual WAN carries the highest hub lock-in of the three due to its managed, all-in-one design.

---

## Required Output 5 — Provider-Specific Constraints (limits, GA status, regional availability)

🟢 **High Confidence** where sourced to a single provider's official docs; per-provider, not cross-provider.

### AWS Transit Gateway

- **Max attachments per Transit Gateway: 5,000** (all attachment types combined). Quota is region-scoped; adjustable via Service Quotas.
- Transit Gateway is a **regional** resource (GA). Cross-region uses **inter-region TGW peering**.
- Source: [AWS Transit Gateway Quotas — Amazon VPC](https://docs.aws.amazon.com/vpc/latest/tgw/transit-gateway-quotas.html). Accessed 2026-08-28. 🟢

### Azure Virtual WAN

- A single hub with VPN Gateway supports up to **~500 spoke (VNet) peerings** and up to **30 site-to-site connections** per typical published guidance; massive-scale designs cite a spoke ceiling around **600**. Confirm the exact current limit against the Virtual WAN limits page for your subscription/SKU.
- Virtual WAN and virtual hubs are **GA**; hub-to-hub any-to-any transit is a managed capability.
- Source: [Azure Virtual WAN network topology](https://learn.microsoft.com/en-us/azure/networking/design-guide/virtual-wan); [Massive-scale VWAN architecture](https://learn.microsoft.com/en-us/azure/architecture/networking/architecture/massive-scale-azure-architecture). Accessed 2026-08-28. 🟡 (spoke ceiling figure varies by SKU/config — verify per subscription)

### GCP Network Connectivity Center (VPC spokes)

- **Active VPC spokes per hub: 250**. **Total VPC spokes (active + inactive) per hub: 1,000**. Per-project VPC-spoke count is an adjustable quota.
- NCC and VPC spokes are **GA**; feature GA milestones continue to land (e.g., IPv4/IPv6 range filtering GA 2025-08-25; static routes GA 2025-08-29; privately-used public IPv4 GA 2025-12-17 — dated notes retained as current stable).
- Source: [NCC Quotas and limits](https://docs.cloud.google.com/network-connectivity/docs/network-connectivity-center/quotas); [NCC release notes](https://docs.cloud.google.com/network-connectivity/docs/network-connectivity-center/release-notes). Accessed 2026-08-28. 🟢

> ⚠️ Sources dated 2025 above reflect the current stable GA state and are retained per the source-hierarchy "current stable overrides 12-month flag" rule.

---

## Scenario Coverage

**Standard Case** — Hybrid enterprise, dozens of workload networks per region, centralized egress/inspection and on-prem connectivity required.
- Approach: **Hub-spoke** using AWS Transit Gateway / Azure Virtual WAN / GCP NCC as the regional hub; attach on-prem via Direct Connect / ExpressRoute / Cloud Interconnect at the hub.
- Key Decisions: global CIDR plan; per-region hub; which spokes need centralized egress vs local egress.

**Edge Case** — A small set of network pairs needs maximum throughput / minimum latency with no inspection (e.g., data-replication pair).
- Approach: **Hybrid** — keep the hub-spoke baseline, add selective AWS VPC Peering / Azure VNet Peering / GCP VPC Peering shortcuts only for those pairs. On GCP, evaluate whether a single global VPC removes the need entirely.

**Anti-Pattern Case** — Architect proposes a full mesh across all enterprise networks "to avoid hub cost."
- Clarification: Confirm spoke-to-spoke and hybrid transit requirements. Because peering is non-transitive on all three providers, full mesh becomes O(n²) peerings and loses central inspection. Recommend hub-spoke with selective peering. Do **not** ship a full-mesh enterprise design without explicit acknowledgment of the non-transitivity and quota consequences.

---

## Source Bibliography (per-provider official documentation)

### AWS
- AWS Transit Gateway — What is a transit gateway: https://docs.aws.amazon.com/vpc/latest/tgw/what-is-transit-gateway.html (accessed 2026-08-28)
- AWS Transit Gateway Quotas (5,000 attachments): https://docs.aws.amazon.com/vpc/latest/tgw/transit-gateway-quotas.html (accessed 2026-08-28)
- AWS VPC Peering — What is VPC peering: https://docs.aws.amazon.com/vpc/latest/peering/what-is-vpc-peering.html (accessed 2026-08-28)
- AWS Well-Architected Framework: https://docs.aws.amazon.com/wellarchitected/ (accessed 2026-08-28)

### Azure
- Hub-spoke network topology using Azure Virtual WAN: https://learn.microsoft.com/en-us/azure/architecture/networking/architecture/hub-spoke-virtual-wan-architecture (accessed 2026-08-28)
- Azure Virtual WAN network topology (design guide): https://learn.microsoft.com/en-us/azure/networking/design-guide/virtual-wan (accessed 2026-08-28)
- Massive-scale VWAN architecture design: https://learn.microsoft.com/en-us/azure/architecture/networking/architecture/massive-scale-azure-architecture (accessed 2026-08-28)
- Azure Virtual Network peering overview: https://learn.microsoft.com/en-us/azure/virtual-network/virtual-network-peering-overview (accessed 2026-08-28)
- VNet connectivity options and spoke-to-spoke: https://learn.microsoft.com/en-us/azure/architecture/reference-architectures/hybrid-networking/virtual-network-peering (accessed 2026-08-28)
- Azure Cloud Adoption Framework: https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ (accessed 2026-08-28)

### Google Cloud
- Network Connectivity Center overview: https://cloud.google.com/network-connectivity/docs/network-connectivity-center/concepts/overview (accessed 2026-08-28)
- NCC VPC spokes overview: https://cloud.google.com/network-connectivity/docs/network-connectivity-center/concepts/vpc-spokes-overview (accessed 2026-08-28)
- NCC Quotas and limits (250 active / 1,000 total VPC spokes per hub): https://docs.cloud.google.com/network-connectivity/docs/network-connectivity-center/quotas (accessed 2026-08-28)
- NCC release notes: https://docs.cloud.google.com/network-connectivity/docs/network-connectivity-center/release-notes (accessed 2026-08-28)
- VPC Network Peering (non-transitive): https://cloud.google.com/vpc/docs/vpc-peering (accessed 2026-08-28)
- Google Cloud Architecture Framework: https://cloud.google.com/architecture/framework (accessed 2026-08-28)

---

## §7 — Research Iteration Changelog

| Iteration | Gap identified | Action | Resolution | Source added |
|-----------|----------------|--------|-------------|--------------|
| 0 (initial) | Verify exact hub service names per provider | WebSearch ×3 | Resolved — TGW / Virtual WAN / NCC confirmed | Per-provider docs |
| 1 | AWS TGW max attachments | WebSearch | Resolved — 5,000 attachments/TGW | AWS TGW quotas |
| 1 | GCP NCC exact per-hub spoke limits | WebFetch quotas page | Resolved — 250 active / 1,000 total per hub | NCC quotas |
| 1 | Peering transitivity across 3 providers | WebSearch | Resolved — non-transitive on AWS/Azure/GCP (Azure Gateway Transit is a scoped exception) | GCP VPC peering; Azure peering docs |
| 1 | GCP NCC / VPC spokes GA status | WebSearch release notes | Resolved — GA; dated feature milestones recorded | NCC release notes |
| — | Azure Virtual WAN exact spoke ceiling (500 vs 600) | WebSearch | Partially resolved — figure varies by SKU/config | ⚠️ Marked Medium Confidence; verify per subscription |

### Residual items requiring human verification
- ⚠️ **Azure Virtual WAN exact maximum spokes per hub** — published guidance cites both ~500 (with VPN Gateway) and ~600 (massive-scale). Exact value is SKU/configuration-dependent. **Human verification required** against the current Azure Virtual WAN limits page for the target subscription before committing a capacity design.

---

## Verification Loop — Self-Check Result

```
[x] TARGET_EDITION stated in metadata and per-provider throughout
[x] All 6 mandatory sections present: Framework/Guardrails, Always-Do, Ask-First (Architectural Decisions),
    Never-Do Anti-patterns, Service Equivalence Map, Source Bibliography
[x] Every pattern cites an official provider URL with access date (2026-08-28)
[x] Every Never-Do entry has side-by-side ❌ Wrong / ✅ Correct with exact service names
[x] Sources dated; 2025 GA sources flagged and retained as current stable
[x] Service Equivalence Map covers networking primitives across all 3 providers
[x] No generic terms where provider-specific names exist (Transit Gateway, Virtual WAN, NCC, etc.)
[x] All 7 required scenario outputs present (exact hub names, exact mesh names, equivalence map,
    lock-in assessment, provider constraints, all cross-provider comparisons marked Medium Confidence,
    per-provider Source Bibliography)
```

> **Recommended next step:** run `/skill-best-practices-validator` on this output, and resolve the one residual Azure Virtual WAN spoke-ceiling item with human verification before it informs a capacity decision.
