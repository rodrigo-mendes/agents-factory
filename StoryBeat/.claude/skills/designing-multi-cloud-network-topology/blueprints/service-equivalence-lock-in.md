# Service Equivalence Map & Lock-in Assessment

> Source: research_cloud_Multi_Cloud_Networking_Hub_Spoke_vs_Mesh_2024.md (Research date: 2026-08-28)
> 🟡 Medium Confidence — cross-provider equivalence does not imply feature parity. Validate each service against its target edition before committing.

---

## Networking Primitives — Cross-Provider Equivalence

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

> ⚠️ Key non-parity note: A GCP VPC network is **global** (subnets are regional), so a single VPC can span regions without a transit hub for intra-VPC traffic. This is a structural difference from AWS/Azure where VPC/VNet are regional and changes when a hub is actually required on GCP.

---

## Lock-in Assessment per Topology per Provider

### Hub-spoke lock-in

| Provider | Service | Lock-in Level | Rationale / Portability Notes |
|----------|---------|---------------|-------------------------------|
| **AWS** | Transit Gateway | Medium-High | TGW route tables, attachment model, and TGW peering are AWS-specific constructs. Migrating to another cloud means rebuilding the transit design; IaC (CloudFormation/Terraform) eases in-cloud rebuild but not cross-cloud portability. |
| **Azure** | Virtual WAN | High | Virtual WAN is a Microsoft-managed abstraction (managed hubs, hub routing, integrated VPN/ExpressRoute). Moving off Virtual WAN even within Azure (to customer-managed hub VNet) is a redesign; cross-cloud migration is a full re-architecture. |
| **Google Cloud** | Network Connectivity Center | Medium-High | NCC hub/spoke resource model is GCP-specific. GCP's global VPC can reduce hub dependence for intra-VPC cases, slightly lowering lock-in vs a mandatory hub, but NCC constructs do not port across clouds. |

### Mesh lock-in

| Provider | Service | Lock-in Level | Rationale / Portability Notes |
|----------|---------|---------------|-------------------------------|
| **AWS** | VPC Peering | Low-Medium | Peering is a thin, standard construct; the concept ports across clouds (all three have equivalent peering). Route-table entries are per-cloud but the mesh design pattern is transferable. |
| **Azure** | VNet Peering | Low-Medium | Standard 1:1 peering concept; Gateway Transit feature is Azure-specific but optional. |
| **Google Cloud** | VPC Network Peering | Low-Medium | Standard peering; global VPC model means fewer peerings needed intra-region. Custom route import/export is a GCP-specific nuance. |

> Summary: **Mesh is lower lock-in than hub-spoke on every provider** because the peering primitive is conceptually portable, whereas each managed hub (TGW / Virtual WAN / NCC) is a proprietary transit abstraction. Azure Virtual WAN carries the highest hub lock-in of the three due to its managed, all-in-one design.
