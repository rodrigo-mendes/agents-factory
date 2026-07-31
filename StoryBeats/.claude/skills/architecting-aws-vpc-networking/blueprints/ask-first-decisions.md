# Ask First Decisions — architecting-aws-vpc-networking

Four architectural crossroads where the correct answer depends on requirements that only the
project team can provide. Present the trade-off matrix and wait for a decision before proceeding.

Source: AWS VPC connectivity options whitepaper + VPC User Guide, verified 2026-07-31.

---

## Decision A — VPC-to-VPC Connectivity: VPC Peering vs Transit Gateway

**Ask before choosing**: "What is the expected total VPC count? Is transitive routing or centralized
egress/inspection required now or in the near future?"

| Dimension | VPC Peering | AWS Transit Gateway |
|-----------|-------------|---------------------|
| Routing | Non-transitive (A↔B, B↔C does NOT give A↔C) | Transitive hub-and-spoke |
| Scale | 1:1 mesh; grows as N·(N−1)/2 connections | Thousands of attachments; one connection per VPC |
| Cost | No per-hour charge; only cross-AZ/inter-Region data | Per-attachment-hour + per-GB processed |
| Latency | Lowest (direct) | One additional routing hop |
| Centralized egress/inspection | Not supported | Supported via inspection/egress VPC under TGW |
| Best when | Few VPCs (≤~5), stable topology, no transitive routing | Many VPCs, shared services, hybrid, centralized inspection |

**Cost profile**: Peering has no per-hour charge (only cross-AZ/inter-Region data fees). TGW adds
a per-attachment-hour charge plus per-GB processed.

**Lock-in**: Both are AWS-native routing constructs; migration between them is a routing/topology
change, not a data migration.

**Recommendation trigger**: Choose TGW if VPC count will exceed ~5, if any hub VPC (shared
services, DNS, inspection) needs to be reached transitively, or if a centralized egress model is
required.

**Source**: https://docs.aws.amazon.com/whitepapers/latest/aws-vpc-connectivity-options/introduction.html

---

## Decision B — Hybrid Connectivity: Site-to-Site VPN vs Direct Connect (± TGW)

**Ask before choosing**: "What is the required bandwidth, latency SLA, provisioning timeline, and
compliance requirement for traffic encryption?"

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| Site-to-Site VPN | AWS Site-to-Site VPN | Fast to stand up; encrypted over internet; low fixed cost | Internet-variable latency/throughput | Quick start, backup path, moderate bandwidth (<1 Gbps) |
| Direct Connect | AWS Direct Connect | Private consistent bandwidth/latency; reduced data-transfer-out rates | Weeks to provision; port + circuit cost | Sustained high throughput, predictable latency, compliance |
| DX + VPN (encrypted DX) | Direct Connect + S2S VPN | Private path + in-flight encryption | Highest complexity and cost | Encrypted private hybrid links (PCI-DSS, HIPAA scenarios) |
| TGW + DX/VPN | TGW + DX/VPN | Single regional hub for all hybrid + VPC routing | TGW attachment charges | Many VPCs sharing one hybrid entry point |

**Cost profile**: VPN has lowest fixed cost. DX has port-hour + data-transfer-out at reduced rates
(verify current pricing). TGW adds per-attachment-hour + per-GB.

**Lock-in**: DX requires a physical cross-connect commitment with a telco/APN partner; VPN is
portable. Both use standard IPsec or BGP/private VLAN.

**Provisioning timeline**: VPN can be active in minutes. DX typically takes weeks (physical circuit
ordering). Plan accordingly for project timelines.

**Source**: https://docs.aws.amazon.com/whitepapers/latest/aws-vpc-connectivity-options/introduction.html

---

## Decision C — IP Addressing: IPv4-Only vs Dual-Stack (IPv4 + IPv6)

**Ask before choosing**: "Does any downstream system require IPv6 reachability? Is the team
prepared to operate dual-stack (routing, SGs, NACLs, application code)?"

| Dimension | IPv4-Only | Dual-Stack (IPv4 + IPv6) |
|-----------|-----------|--------------------------|
| Address cost | Public IPv4 addresses incur an hourly charge | IPv6 addresses have no hourly charge |
| Egress cost | NAT gateway (paid per-hour + per-GB) for private subnets | IPv6 egress via egress-only internet gateway (free) |
| Address space | RFC 1918 + secondary CIDRs; exhaustion at large scale | Amazon-provided /56 per VPC, /64 per subnet — vast space |
| Operational maturity | Universal; every AWS service supports IPv4 | Not every AWS service/tool supports IPv6; requires team skill |
| Portability | N/A | Amazon-provided IPv6 blocks are AWS-assigned (BYOIPv6 possible) |
| Best when | Legacy/most existing workloads; simpler operations | New large-scale designs, IPv4-constrained environments, public-facing services needing no NAT |

**Cost driver**: AWS now charges for public IPv4 addresses per hour. For workloads with many
public-facing resources, dual-stack can reduce this cost by using IPv6 for public access.

**Architect note**: Do not enable dual-stack unless the team has confirmed IPv6 support across:
security groups and NACLs, application code, monitoring, and any third-party appliances.

**Source**: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-cidr-blocks.html (IPv6),
https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html (public IPv4 pricing)

---

## Decision D — Egress Control: Distributed NAT per VPC vs Centralized Egress via TGW

**Ask before choosing**: "Is centralized egress inspection a compliance requirement? How many
VPCs will share the egress path?"

| Dimension | Distributed NAT (per VPC per AZ) | Centralized Egress (TGW + inspection/egress VPC) |
|-----------|----------------------------------|--------------------------------------------------|
| Isolation | Each VPC fully independent | Shared central path; central blast radius |
| Cost | NAT cost multiplies across VPCs | Fewer NAT gateways; TGW data-processing + firewall costs |
| Inspection | Not possible without inline appliance | AWS Network Firewall at central point |
| Complexity | Simple; no transitive routing | Requires TGW + routing domains + inspection VPC design |
| Best when | Few VPCs, independent teams, cost per VPC acceptable | Many VPCs needing uniform egress policy, compliance/inspection |

**Cost modeling note**: Centralizing reduces NAT gateway count (major saving at scale) but
introduces TGW per-attachment-hour + per-GB and Network Firewall endpoint + data-processing charges.
Model both options against your traffic volume before deciding.

**Recommendation trigger**: Consider centralized egress when:
- Compliance requires all outbound traffic to be inspected/logged at a single point.
- You have ≥5 VPCs, each paying for per-AZ NAT gateways.
- Shared internet egress policy is required across business units.

**Source**: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html,
https://docs.aws.amazon.com/whitepapers/latest/aws-vpc-connectivity-options/introduction.html
