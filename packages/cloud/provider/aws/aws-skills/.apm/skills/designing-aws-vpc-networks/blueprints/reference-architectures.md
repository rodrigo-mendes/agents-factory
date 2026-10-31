# Reference Architectures — designing-aws-vpc-networks

Canonical 3-tier VPC and multi-account landing zone designs. Summary in [../SKILL.md](../SKILL.md).
Source: research_cloud_AWS_VPC_Networking_2026.md (research date 2026-08-30).

Note: the research file contains no Terraform/CDK code. IaC examples referenced from SKILL.md are not provided here (unverified; author from the Verification Loop in SKILL.md and the official docs linked below).

---

## 1. Canonical Multi-AZ Three-Tier Web Application VPC

**Context**: production web app with public frontend, stateful application tier and managed database; minimum viable production architecture for most web workloads.

| Layer | Service | Purpose |
|---|---|---|
| Edge, public subnets (2+ AZs) | Internet Gateway | Bidirectional internet connectivity |
| Edge, public subnets (2+ AZs) | ALB + WAF | L7 routing, WAF filtering, L3/4 DDoS absorption |
| Edge, public subnets (2+ AZs) | NAT Gateway (1 per AZ) | Outbound internet for private tiers |
| App, private subnets (2+ AZs) | EC2 Auto Scaling / ECS / EKS | No public IP; inbound only from ALB SG |
| App, private subnets (2+ AZs) | S3 Gateway Endpoint | S3 without NAT; free |
| Data, isolated subnets (2+ AZs) | RDS Multi-AZ | `publicly_accessible = false`; reachable only from App SG |
| Data, isolated subnets (2+ AZs) | ElastiCache | Session store/cache; App SG inbound only |
| Observability | VPC Flow Logs to S3 + Athena | Out-of-path traffic audit trail |
| Security | Security Hub + Config | Continuous compliance (EC2.13/14/18/19/21) |
| DNS | Route 53 Private Hosted Zone | Internal service discovery |

**Key decisions**:
1. Subnet CIDR sizing: /24 minimum per tier per AZ.
2. Whether to add CloudFront upstream of the ALB for caching and global latency.
3. Single vs multi-Region for DR.
4. Whether VPC Lattice replaces the ALB for east-west calls.

**Security group chain**: ALB SG (80/443 from `0.0.0.0/0`) to App SG (app port from ALB SG) to DB SG (DB port from App SG). NACLs are secondary; include ephemeral ports 1024-65535.

**Standard-case approach** (research): VPC /16 across 2-3 AZs; ALB with WAF plus NAT GW per AZ in public subnets; Auto Scaling/ECS in private subnets; RDS Multi-AZ in isolated subnets; S3 Gateway endpoint; CloudFront upstream of ALB; VPC Flow Logs to S3 + Athena; Security Hub + Config with EC2 network controls; VPC BPA enforced at account level; VPC Encryption Controls in monitor mode first, then enforce.

**Scaling path**:

| Stage | Pattern |
|---|---|
| Single account, single VPC | 3-tier VPC (this design) |
| Multiple workloads or small multi-account | VPC peering or shared VPC via RAM |
| Enterprise, many accounts | TGW hub-and-spoke + dedicated Network Services account |
| Enterprise + egress/compliance control | TGW + centralized egress/inspection VPC + Network Firewall |
| Global multi-Region | AWS Cloud WAN + TGW per Region |
| Multicloud | AWS Interconnect (GA for Google Cloud April 2026; Azure/OCI in preview later 2026) |

Source: [VPC example: private subnets and NAT](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-example-private-subnets-nat.html) (accessed 2026-08-30)

---

## 2. Multi-Account Landing Zone Networking (AWS Control Tower)

**Context**: enterprise landing zone with centralized networking, security tooling and workload account isolation.

| Account | Service | Purpose |
|---|---|---|
| Network Services | Transit Gateway | Regional hub for workload VPCs and hybrid links |
| Network Services | Centralized NAT Gateways | Consolidated egress; one per AZ in egress VPC |
| Network Services | AWS Network Firewall | Egress inspection, domain filtering, IDS/IPS |
| Network Services | Direct Connect / Site-to-Site VPN | DX primary + VPN backup |
| Network Services | AWS IPAM | Org-wide CIDR allocation and non-overlap |
| Security Tooling | Security Hub (aggregated) | Org-wide EC2 network controls |
| Security Tooling | AWS Config (aggregated) | Config rules across accounts |
| Workload | Spoke VPCs | Isolated per workload; TGW attachment via /28 subnet |
| Workload | VPC Interface Endpoints | Private AWS service access |
| Workload | Route 53 Resolver (centralized) | DNS to central PHZ and on-premises |
| Management | VPC Block Public Access Declarative Policy | Org-wide BPA |
| Management | VPC Encryption Controls Declarative Policy | Org-wide in-transit encryption (July 2026) |

**Key decisions**:
1. Centralized vs distributed egress: centralized simplifies control; distributed reduces TGW charges.
2. Shared VPC via RAM vs per-account VPCs: shared reduces endpoint cost; per-account improves isolation.
3. TGW vs Cloud WAN: Cloud WAN for global multi-Region SD-WAN unification.

**Scaling path**: TGW hub-and-spoke, then inspection VPC, then Cloud WAN for multi-Region, then AWS Interconnect for multicloud.

Source: [Control Tower landing zone networking](https://docs.aws.amazon.com/prescriptive-guidance/latest/designing-control-tower-landing-zone/networking-integration.html) (accessed 2026-08-30)

---

## 3. TGW Hub-and-Spoke with Centralized Egress Inspection

- Deploy Transit Gateway in the Network Services account; attach spoke VPCs and DX/VPN.
- Use multiple TGW route tables for segmentation (for example prod vs non-prod).
- Inspection VPC with Network Firewall and **Appliance Mode enabled**; route spoke-to-spoke and egress traffic through it.
- Centralized egress VPC holds NAT Gateways and Network Firewall (domain allow/deny lists); TGW Flow Logs give central visibility.

| Dimension | Benefit | Cost |
|---|---|---|
| Scalability | One attachment per VPC; no mesh | Per-attachment + per-GB TGW charges |
| Security | Central inspection point | Extra latency hop |
| Availability | TGW is managed regional HA | Cross-Region needs TGW peering |
| Operations | Central policy via Firewall Manager | Route table complexity |

Sources: [Hub-and-spoke topology (Well-Architected)](https://docs.aws.amazon.com/wellarchitected/latest/framework/rel_planning_network_topology_prefer_hub_and_spoke.html); [Control Tower networking](https://docs.aws.amazon.com/prescriptive-guidance/latest/designing-control-tower-landing-zone/networking-integration.html) (accessed 2026-08-30)

---

## 4. CloudFront + ALB + WAF Edge

Internet to CloudFront (CDN, Shield Standard) to ALB in public subnets (WAF attached for SQLi, XSS, rate limiting, geo-block, IP reputation) to Auto Scaling EC2/ECS/EKS in private subnets. Shield Advanced optional. CloudFront-to-origin transfer from AWS origins is free. CloudFront supports WebSocket to private VPC origins since May 2026.

| Dimension | Benefit | Cost |
|---|---|---|
| Latency | Cached content from 600+ PoPs | Origin latency on cache miss |
| Security | Shield, WAF, ALB layers | WAF charges per rule and request |
| Cost | Free AWS-origin to CloudFront transfer | Viewer transfer, WAF, Shield Advanced |

Sources: [CloudFront introduction](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Introduction.html); [CloudFront WebSocket for VPC origins](https://aws.amazon.com/about-aws/whats-new/2026/05/amazon-cloudfront-websockets-vpc-origins/) (accessed 2026-08-30)

---

## 5. VPC Lattice East-West Service Mesh

- Create a service network, associate VPCs, define services and target groups per microservice.
- IAM auth policies for zero-trust; NAT64 handles overlapping IPs.
- Weighted target groups for blue/green. WebSocket TLS and AI agent zero-trust added August 2026 (verify regional availability).

Source: [VPC Lattice (multi-VPC whitepaper)](https://docs.aws.amazon.com/whitepapers/latest/building-scalable-secure-multi-vpc-network-infrastructure/vpc-lattice.html) (accessed 2026-08-30)

---

## 6. Operational Notes

- **NAT Gateway**: monitor `BytesOutToDestination`, `PacketsOutToDestination`, `ErrorPortAllocation` (namespace `AWS/NATGateway`); alarm on `ErrorPortAllocation > 0`. Limit 55,000 simultaneous connections per unique destination; split private subnets across NAT GWs to scale. Bandwidth auto-scales 5 to 100 Gbps.
- **NAU**: monitor `NetworkAddressUsage` and `NetworkAddressUsagePeered` (namespace `AWS/EC2`, every 24h); alarm at 70% of quota.
- **Diagnostics**: Reachability Analyzer (hop-by-hop; usable in CI/CD) and Network Access Analyzer (internet-accessibility audits).
- **Hybrid DNS**: Route 53 inbound resolver endpoints (on-premises to VPC), outbound endpoints with forwarding rules (VPC to on-premises), DNS Firewall for malicious domains.

Sources: [VPC CloudWatch metrics](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-cloudwatch.html); [Reachability Analyzer](https://docs.aws.amazon.com/vpc/latest/reachability/what-is-reachability-analyzer.html) (accessed 2026-08-30)
