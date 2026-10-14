---
name: designing-multi-cloud-network-topology
description: "Designs and evaluates multi-cloud network topology (hub-spoke vs mesh) across AWS, Azure, and Google Cloud using managed transit services (Transit Gateway, Virtual WAN, Network Connectivity Center). Use when an architect must choose or validate an enterprise hybrid network topology, compare provider-specific networking primitives, or assess topology lock-in and scaling constraints across two or more cloud providers."
---

## Function

Specialist in multi-cloud networking topology design — hub-spoke vs mesh — targeting AWS Well-Architected Framework 2024, Azure Cloud Adoption Framework (November 2024), and Google Cloud Architecture Framework 2024.

## Version Context

**Technology domain**: Multi-Cloud Networking Architecture
**Target editions**:
- AWS: Well-Architected Framework 2024
- Azure: Cloud Adoption Framework (CAF), November 2024
- Google Cloud: Architecture Framework 2024
**Research date**: 2026-08-28
**Currency threshold**: Review after 2027-08-28 (service quotas evolve quarterly)

**Provider service name map** (hub-spoke vs mesh):

| Topology | AWS | Azure | Google Cloud |
|----------|-----|-------|--------------|
| **Hub-spoke transit** | AWS Transit Gateway | Azure Virtual WAN | GCP Network Connectivity Center |
| **Mesh peering** | AWS VPC Peering | Azure VNet Peering | GCP VPC Network Peering |

**Critical structural difference — GCP**: A GCP VPC network is **global** (subnets are regional). A single VPC can span regions without a transit hub for intra-VPC traffic. This reduces hub-spoke requirements on GCP vs AWS/Azure where VPC/VNet are regional.

**Known residual item requiring human verification**: Azure Virtual WAN maximum spokes per hub — published guidance cites both ~500 (with VPN Gateway) and ~600 (massive-scale); the exact value is SKU/configuration-dependent. Verify against the current Azure Virtual WAN limits page before committing a capacity design.

⚠️ **CRITICAL — Agent Warning**:
Use the exact provider service names above. Do not substitute generic terms ("transit VPC", "hub VNet") where the managed service names apply. Reject patterns that assume native peering is transitive — it is non-transitive on all three providers.

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — ✅⚠️🚫 topology decision patterns
- **[Service Equivalence & Lock-in](./blueprints/service-equivalence-lock-in.md)** — Full networking primitives map + lock-in assessment per topology per provider
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 5 test scenarios (canonical, edge, anti-pattern, capacity, cross-provider)
- **[Verification Loop](#verification-loop)** — CLI commands to confirm topology state
- **[Quick Reference](#quick-reference)** — Critical quotas at a glance
- **[External Resources](#external-resources)** — Official documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

**Plan a non-overlapping global CIDR before creating any hub attachment** — Transitive hubs (TGW, Virtual WAN, NCC) propagate routes across all attachments; overlapping IP ranges cannot be routed transitively and cannot be remediated without re-addressing. Allocate a single enterprise supernet, carve per-cloud and per-region blocks, and reserve on-prem ranges before creating any spoke or attachment.
- Verification: AWS `aws ec2 search-transit-gateway-routes`; Azure `az network vhub get-effective-routes`; GCP `gcloud network-connectivity hubs describe` + effective routes on spoke VPC.
- Source: [AWS TGW quotas](https://docs.aws.amazon.com/vpc/latest/tgw/transit-gateway-quotas.html); [Azure VWAN topology](https://learn.microsoft.com/en-us/azure/networking/design-guide/virtual-wan); [GCP VPC spokes overview](https://cloud.google.com/network-connectivity/docs/network-connectivity-center/concepts/vpc-spokes-overview). Accessed 2026-08-28. 🟢

**Use the managed hub for transitive routing, not self-managed transit VMs** — Managed hubs (AWS Transit Gateway, Azure Virtual WAN, GCP Network Connectivity Center) provide native transitive routing without the operational burden and single-point-of-failure risk of self-run router appliances. Attach each workload network as a spoke to the regional managed hub; centralize hybrid connectivity and egress inspection at the hub.
- Verification: Confirm spoke attachment status is `active`/`associated` in each provider's console/CLI.
- Source: [Azure hub-spoke via VWAN](https://learn.microsoft.com/en-us/azure/architecture/networking/architecture/hub-spoke-virtual-wan-architecture); [GCP NCC overview](https://cloud.google.com/network-connectivity/docs/network-connectivity-center/concepts/overview); [AWS TGW](https://docs.aws.amazon.com/vpc/latest/tgw/what-is-transit-gateway.html). Accessed 2026-08-28. 🟢

**Default to hub-spoke for enterprise hybrid networks** — Centralized egress, inspection, and on-prem connectivity (Direct Connect / ExpressRoute / Cloud Interconnect) attach naturally at the hub. Hub-spoke scales linearly (O(n) attachments) vs mesh's O(n²) peerings. Treat mesh as a point optimization, not a baseline topology.

**Apply confidence labels on cross-provider comparisons** — Single-provider facts are 🟢 High Confidence. Cross-provider comparisons are 🟡 Medium Confidence. Mark outputs accordingly; do not present cross-provider equivalence as guaranteed feature parity.

### ⚠️ Ask First

**Hub-spoke vs mesh topology choice** 🟡 Medium Confidence (cross-provider) — Ask whether the use case requires: (a) spoke-to-spoke transitive routing, (b) centralized egress inspection, (c) hybrid on-prem connectivity. If any of these are required → hub-spoke. If only a few named high-throughput, latency-sensitive pairs need direct connectivity with no central inspection → mesh (or hybrid: hub-spoke baseline plus selective peering shortcuts).

| Option | Optimizes | Sacrifices | Lock-in |
|--------|-----------|------------|---------|
| Hub-spoke (TGW / Virtual WAN / NCC) | Transitive routing, centralized inspection, O(n) scaling, hybrid attach | Per-GB transit/data-processing cost, extra hop latency | Medium-High (AWS/GCP), High (Azure VWAN) |
| Mesh (VPC/VNet/VPC Peering) | Lowest latency (direct), no transit-processing charge | Non-transitive → O(n²) peerings, no central inspection | Low-Medium (all providers) |

For full lock-in assessment per provider, see [Service Equivalence & Lock-in](./blueprints/service-equivalence-lock-in.md).

**Hybrid topology (hub-spoke + selective peering shortcuts)** — Ask before adding direct peering shortcuts on top of a hub-spoke baseline. Identify the specific high-throughput pairs that justify the shortcut; confirm the pair count will not grow into a de facto full mesh over time.

**Azure Virtual WAN vs customer-managed hub VNet** — Both are valid CAF topologies. Azure Virtual WAN is the managed evolution (higher lock-in, lower ops burden). A customer-managed hub VNet is the traditional pattern (lower lock-in, higher ops). Confirm which CAF pattern the customer has adopted before prescribing Virtual WAN.

**GCP single global VPC vs NCC hub-spoke** — On GCP, a single global VPC can host subnets across all regions in one network boundary. Ask whether project isolation requirements actually mandate separate VPCs before recommending NCC hub-spoke on GCP.

### 🚫 Never Do

**Never assume spoke-to-spoke reachability through plain peering to a hub** — Native peering is non-transitive on AWS, Azure, and GCP. A spoke peered to a hub VNet/VPC cannot reach another spoke via that peering.

```
# 🚫 WRONG — two spoke VPCs each peered to a "hub" VPC via AWS VPC Peering
# Expecting spoke-A ↔ spoke-B connectivity will silently fail.

# ✅ CORRECT — attach both spokes to AWS Transit Gateway (transitive)
# On GCP: use NCC VPC spokes. On Azure: use Virtual WAN hub routing.
```

Detection: Effective-routes check on the spoke shows no route to the other spoke's CIDR.
Impact: Silent connectivity failure / service outage.
Source: [GCP VPC Peering — no transitive routing](https://cloud.google.com/vpc/docs/vpc-peering); [Azure VNet peering + spoke-to-spoke](https://learn.microsoft.com/en-us/azure/architecture/reference-architectures/hybrid-networking/virtual-network-peering). Accessed 2026-08-28. 🟢

**Never propose a full mesh at enterprise scale** — n(n-1)/2 non-transitive peerings become unmanageable and hit per-network peering quotas (e.g., 40 VNets → 780 VNet peerings, no central inspection).

```
# 🚫 WRONG — 40 VNets each peered to every other VNet (780 Azure VNet Peerings)

# ✅ CORRECT — attach all 40 VNets as spokes to Azure Virtual WAN;
# add selective VNet Peering only for the specific high-throughput pairs needing direct paths.
```

Detection: Peering count per network approaching provider limits; route-table sprawl.
Impact: Operational overload / change-failure risk. 🟡
Source: [Azure massive-scale VWAN](https://learn.microsoft.com/en-us/azure/architecture/networking/architecture/massive-scale-azure-architecture). Accessed 2026-08-28.

**Never create overlapping CIDRs across spokes or clouds** — Transitive hubs cannot route overlapping ranges; remediation requires re-addressing the affected networks.

```
# 🚫 WRONG — two spokes both using 10.0.0.0/16 attached to the same transit hub

# ✅ CORRECT — unique blocks from a planned enterprise supernet per spoke and per cloud
# e.g., 10.1.0.0/16 (AWS us-east-1 workloads), 10.2.0.0/16 (Azure East US), 10.3.0.0/16 (GCP us-central1)
```

Detection: Route-conflict / attachment-rejection errors at the hub.
Impact: Cascading connectivity failure across the hybrid network. 🟢
Source: [AWS TGW quotas](https://docs.aws.amazon.com/vpc/latest/tgw/transit-gateway-quotas.html); [GCP VPC spokes overview](https://cloud.google.com/network-connectivity/docs/network-connectivity-center/concepts/vpc-spokes-overview). Accessed 2026-08-28.

**Never ship a full-mesh enterprise design without explicit acknowledgment of non-transitivity consequences** — Confirm that the architect understands O(n²) peering growth, loss of central inspection, and per-network quota exposure. Document that acknowledgment before proceeding.

---

## Integration Patterns

**Hub-spoke + on-premises (standard enterprise)**:
- AWS: Direct Connect gateway attached to Transit Gateway → all spoke VPCs reach on-prem via TGW.
- Azure: ExpressRoute circuit attached to Virtual WAN hub → all spoke VNets reach on-prem via hub.
- GCP: Cloud Interconnect via hybrid spoke attached to NCC hub → spoke VPCs reach on-prem via NCC.

**Centralized egress inspection at hub**:
- AWS: Deploy AWS Network Firewall in the hub VPC; route spoke egress through the hub via TGW.
- Azure: Azure Firewall deployed in the Virtual WAN secured hub; policies applied centrally.
- GCP: Cloud NGFW / firewall policies at hub; traffic steered via NCC routing.

**Selective mesh peering shortcuts (hybrid)**:
- Establish direct peering between two spokes that require maximum throughput / minimum latency.
- Keep the hub-spoke baseline for all other traffic and for hybrid connectivity.
- Document each shortcut as a named pair; review quarterly to prevent silent growth into full mesh.

**Common problems**:
- **Problem**: Route asymmetry after adding a peering shortcut → **Solution**: Audit spoke route tables; ensure shortcut routes are more specific or explicitly preferred.
- **Problem**: Hub quota approaching limit → **Solution**: Check current attachment count against provider-specific quotas in [Quick Reference](#quick-reference); plan additional regional hubs early.
- **Problem**: Azure VWAN spoke ceiling uncertainty → **Solution**: Verify exact current limit against Azure Virtual WAN limits page for target subscription/SKU before capacity planning.

---

## Verification Loop

The agent MUST verify topology state after any design or configuration change:

### 1. Hub attachment state
```bash
# AWS — list TGW attachments
aws ec2 describe-transit-gateway-attachments \
  --filters Name=transit-gateway-id,Values=<tgw-id>
# Expected: all spoke attachments in "available" state

# Azure — list Virtual WAN connections
az network vhub connection list --resource-group <rg> --vhub-name <hub-name>
# Expected: all connections in "Succeeded" provisioning state

# GCP — list NCC spokes
gcloud network-connectivity spokes list --hub=<hub-name>
# Expected: all spokes in "ACTIVE" state
```

### 2. Effective route check (confirm transitive reachability)
```bash
# AWS
aws ec2 search-transit-gateway-routes \
  --transit-gateway-route-table-id <rtb-id> \
  --filters Name=type,Values=propagated

# Azure
az network vhub get-effective-routes \
  --resource-group <rg> --name <hub-name> \
  --resource-type HubVirtualNetworkConnection --resource-id <conn-id>

# GCP
gcloud network-connectivity hubs describe <hub-name>
# Then check effective routes on each spoke VPC
```

### 3. CIDR overlap check (run before any new attachment)
```bash
# AWS — check existing TGW route table for conflicting prefixes
aws ec2 get-transit-gateway-route-table-associations \
  --transit-gateway-route-table-id <rtb-id>
```

**Troubleshooting**:
- Spoke attachment stuck in `pending` → verify CIDR uniqueness; check route table propagation is enabled.
- No route to another spoke → peering is non-transitive; use the managed hub for spoke-to-spoke routing.
- Azure VWAN hub routing not propagating → confirm route table association and propagation settings on the hub connection.

---

## Quick Reference

**Critical quotas**:

| Provider | Service | Limit | Notes |
|----------|---------|-------|-------|
| AWS | Transit Gateway | 5,000 attachments per TGW | Adjustable via Service Quotas; regional resource |
| Azure | Virtual WAN | ~500–600 spoke VNet connections per hub | SKU/config-dependent — verify per subscription 🟡 |
| GCP | Network Connectivity Center | 250 active VPC spokes per hub; 1,000 total (active + inactive) | Per-project count is adjustable quota |

**Non-transitivity rule** (applies to all three providers):
- AWS VPC Peering: non-transitive
- Azure VNet Peering: non-transitive (Gateway Transit is a scoped exception)
- GCP VPC Network Peering: non-transitive

**Scaling law**: Full mesh = n(n-1)/2 peerings. Hub-spoke = n attachments.

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/designing-multi-cloud-network-topology/
├── SKILL.md                              <- This file
└── blueprints/
    ├── service-equivalence-lock-in.md    <- Full networking primitives map + lock-in tables
    └── evaluation-scenarios.md           <- 5 test scenarios
```

---

## External Resources

### AWS
- [AWS Transit Gateway — What is a transit gateway](https://docs.aws.amazon.com/vpc/latest/tgw/what-is-transit-gateway.html) — Primary hub service reference (accessed 2026-08-28)
- [AWS Transit Gateway Quotas](https://docs.aws.amazon.com/vpc/latest/tgw/transit-gateway-quotas.html) — 5,000 attachments limit (accessed 2026-08-28)
- [AWS VPC Peering — What is VPC peering](https://docs.aws.amazon.com/vpc/latest/peering/what-is-vpc-peering.html) (accessed 2026-08-28)

### Azure
- [Hub-spoke topology using Azure Virtual WAN](https://learn.microsoft.com/en-us/azure/architecture/networking/architecture/hub-spoke-virtual-wan-architecture) (accessed 2026-08-28)
- [Azure Virtual WAN network topology design guide](https://learn.microsoft.com/en-us/azure/networking/design-guide/virtual-wan) (accessed 2026-08-28)
- [Massive-scale Azure VWAN architecture](https://learn.microsoft.com/en-us/azure/architecture/networking/architecture/massive-scale-azure-architecture) (accessed 2026-08-28)
- [Azure Virtual Network peering overview](https://learn.microsoft.com/en-us/azure/virtual-network/virtual-network-peering-overview) (accessed 2026-08-28)

### Google Cloud
- [Network Connectivity Center overview](https://cloud.google.com/network-connectivity/docs/network-connectivity-center/concepts/overview) (accessed 2026-08-28)
- [NCC VPC spokes overview](https://cloud.google.com/network-connectivity/docs/network-connectivity-center/concepts/vpc-spokes-overview) (accessed 2026-08-28)
- [NCC Quotas and limits](https://docs.cloud.google.com/network-connectivity/docs/network-connectivity-center/quotas) — 250 active / 1,000 total VPC spokes per hub (accessed 2026-08-28)
- [VPC Network Peering — non-transitive](https://cloud.google.com/vpc/docs/vpc-peering) (accessed 2026-08-28)
