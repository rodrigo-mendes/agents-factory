---
Full_Name: "AWS Amazon VPC — Networking Architecture"
Cloud_Provider: "AWS"
Architecture_Domain: "Networking Architecture (Amazon VPC)"
Target_Edition: "Amazon VPC User Guide (current, verified 2026-07-31) + AWS Well-Architected Framework (publication date 2024-11-06)"
Architecture_Context: "General-purpose production workloads (multi-tier applications requiring public + private isolation, multi-AZ HA, and private access to AWS services)"
Official_Source_URL: "https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-07-31"
Currency_Threshold: "2027-07-31 (review after this date; re-verify VPC feature availability and WAF edition)"
---

> ⚠️ **Version note**: AWS documentation is continuously published rather than versioned by release
> number. All pattern claims below were verified live against the current Amazon VPC User Guide on
> **2026-07-31**. The governing AWS Well-Architected Framework edition is dated **2024-11-06**
> (~20 months old at research time). It is the **current stable edition**, so it is accepted per the
> Source Hierarchy, but re-verify the pillar set and networking guidance if a newer edition ships.

# Executive Summary

Amazon VPC (Virtual Private Cloud) is the network isolation boundary for AWS resources: a logically
isolated virtual network you define within an AWS Region, resembling a traditional data-center network
but built on AWS's scalable infrastructure (Source: [What is Amazon VPC?](https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html), verified 2026-07-31). Every AWS account receives a **default VPC per Region**; production designs almost always create purpose-built VPCs with explicit CIDR planning, subnet tiering, routing, and gateways. VPC networking is the substrate on which every other guardrail (security groups, private service access, egress control, hybrid connectivity) is layered, so networking mistakes have the largest blast radius of any single architectural decision.

There is no separately versioned "VPC edition." The service evolves feature-by-feature; the load-bearing recent additions relevant to architecture decisions are **IPv6 / dual-stack support**, **AWS IP Address Manager (IPAM)** for CIDR governance, **private NAT gateways** (for VPC-to-VPC / on-prem egress without an internet gateway), **AWS Network Firewall** and **Network Access Analyzer** for inspection/validation, and **Regional NAT gateways for automatic multi-AZ expansion** (a newer resiliency option alongside the long-standing one-NAT-gateway-per-AZ pattern). Architecture guidance is anchored by the **AWS Well-Architected Framework** (Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, Sustainability — Source: [WAF welcome, 2024-11-06](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html)).

The three most critical networking guardrails for a general-purpose production context are: **(1)** deploy subnets across **multiple Availability Zones** and place NAT capacity per-AZ (Reliability); **(2)** enforce a **public/private/isolated subnet tier model** with security groups as the primary control and NACLs as a coarse subnet-level backstop (Security); and **(3)** plan **non-overlapping CIDR ranges up front** (VPC is `/16`–`/28`; blocks cannot be resized, and overlaps permanently block peering, Transit Gateway, and Direct Connect gateway attachment). These three are addressed in the Mandatory Patterns and Anti-Patterns sections below.

---

# Cloud Architecture Glossary

```
Term: VPC (Virtual Private Cloud)
Definition: A logically isolated virtual network within an AWS Region, defined by one or more CIDR blocks; the top-level network boundary for AWS resources.
Provider Docs Section: VPC User Guide — "What is Amazon VPC?"
Architect Usage: One VPC = one Region isolation boundary. Choose VPC count per environment/account, not per app, unless isolation or CIDR-scale demands otherwise.
Common Confusion: Confused with a subnet (a VPC spans AZs; a subnet is pinned to exactly one AZ). Also confused with an account boundary — a VPC lives inside one account.
```
```
Term: Subnet
Definition: A range of IP addresses in a VPC that resides in a single Availability Zone.
Provider Docs Section: VPC User Guide — "Subnets" / "Subnet CIDR blocks"
Architect Usage: Subnet = AZ placement + routing-table association. "Public" vs "private" is defined by the route table, not by an attribute of the subnet itself.
Common Confusion: There is no such thing as a multi-AZ subnet. HA requires ≥2 subnets in ≥2 AZs.
```
```
Term: Route table
Definition: A set of rules (routes) that determine where network traffic from a subnet or gateway is directed.
Provider Docs Section: VPC User Guide — "Route tables"
Architect Usage: A subnet is "public" only if its route table sends 0.0.0.0/0 to an internet gateway. Attach one route table per tier.
Common Confusion: Confused with security groups — route tables decide reachability/pathing; security groups decide allow/deny.
```
```
Term: Internet gateway (IGW)
Definition: A horizontally scaled, redundant, highly available VPC component that allows communication between the VPC and the internet.
Provider Docs Section: VPC User Guide — "Internet gateways"
Architect Usage: One IGW per VPC. Presence of an IGW does NOT make resources public; a public route + public IP are also required.
Common Confusion: Confused with NAT gateway — IGW enables inbound+outbound public IPv4; NAT gateway enables outbound-only for private subnets.
```
```
Term: NAT gateway
Definition: A managed Network Address Translation service letting instances in a private subnet reach services outside the VPC while blocking unsolicited inbound connections.
Provider Docs Section: VPC User Guide — "NAT gateways"
Architect Usage: Public NAT gateway (in a public subnet, needs an EIP) for internet egress; private NAT gateway for VPC-to-VPC / on-prem egress via TGW/VGW.
Common Confusion: Confused with IGW. Also, one NAT gateway is AZ-scoped — a single NAT gateway is a single-AZ dependency for every subnet routed through it.
```
```
Term: Security group
Definition: A stateful virtual firewall attached to an elastic network interface (ENI) controlling inbound and outbound traffic.
Provider Docs Section: VPC User Guide — "Security groups"
Architect Usage: Primary, instance-level control. Stateful (return traffic auto-allowed). Reference other security groups as sources for tier-to-tier rules.
Common Confusion: Confused with NACLs (stateless, subnet-level, support explicit deny). Security groups have no deny rules — only allows.
```
```
Term: Network ACL (NACL)
Definition: A stateless firewall controlling inbound and outbound traffic at the subnet boundary.
Provider Docs Section: VPC User Guide — "Control subnet traffic with network access control lists"
Architect Usage: Coarse subnet-level backstop; supports explicit deny (e.g., block a bad CIDR). Remember to allow ephemeral return ports (stateless).
Common Confusion: Treated as a replacement for security groups — it is a complement, not a substitute.
```
```
Term: VPC endpoint / AWS PrivateLink
Definition: A component that connects a VPC to AWS services (or to endpoint services) privately, without an internet gateway or NAT device. Gateway endpoints (S3, DynamoDB) use route tables; interface endpoints (PrivateLink) create an ENI.
Provider Docs Section: VPC User Guide / PrivateLink Guide — "VPC endpoints"
Architect Usage: Use to keep AWS-service traffic off the public internet and to cut NAT data-processing cost for high-volume S3/DynamoDB access (gateway endpoints are free).
Common Confusion: Gateway endpoint (route-table based, S3/DynamoDB only, free) vs interface endpoint (ENI + hourly + data charges, most other services).
```
```
Term: VPC Flow Logs
Definition: A feature that captures information about the IP traffic going to and from network interfaces in a VPC, subnet, or ENI.
Provider Docs Section: VPC User Guide — "VPC Flow Logs"
Architect Usage: Enable at VPC scope to CloudWatch Logs or S3; feeds GuardDuty threat detection and audit/forensics.
Common Confusion: Flow logs capture metadata (5-tuple, action, bytes) — NOT packet payloads. Use Traffic Mirroring for payload/deep packet inspection.
```
```
Term: Transit Gateway (TGW)
Definition: A regional network hub that routes traffic between VPCs, VPN connections, and Direct Connect connections in a hub-and-spoke model.
Provider Docs Section: VPC connectivity options whitepaper — "AWS Transit Gateway"
Architect Usage: Default choice once you exceed a handful of VPCs or need transitive routing / centralized egress and inspection.
Common Confusion: Confused with VPC peering — peering is non-transitive and 1:1; TGW is transitive and hub-and-spoke.
```
```
Term: AWS IP Address Manager (IPAM)
Definition: A VPC feature for planning, tracking, and monitoring IP address usage across accounts and Regions.
Provider Docs Section: VPC User Guide — "What is IPAM?"
Architect Usage: Use as the source of truth for CIDR allocation in multi-account landing zones to prevent overlap before it happens.
Common Confusion: Not a routing or DHCP service; it is an allocation/governance layer.
```
```
Term: Availability Zone (AZ)
Definition: One or more discrete data centers with redundant power, networking, and connectivity within an AWS Region.
Provider Docs Section: VPC User Guide — "Security best practices for your VPC"
Architect Usage: Spread subnets across ≥2 (ideally 3) AZs; this is AWS's primary fault-isolation boundary for HA.
Common Confusion: AZ IDs (use-az1) are account-independent; AZ names (us-east-1a) are randomized per account and do not line up across accounts.
```

---

# Architecture Guardrails

## ✅ Mandatory Patterns

**1. Multi-AZ subnet layout for every tier**
- Pillar Alignment: Reliability
- Why: AWS explicitly directs, "When you add subnets to your VPC to host your application, create them in multiple Availability Zones… Using multiple Availability Zones makes your production applications highly available, fault tolerant, and scalable." (Source: [VPC security best practices](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-best-practices.html), verified 2026-07-31)
- AWS Services: VPC, Subnets, Availability Zones
- Architecture Decision: For each tier (public/private/isolated) create one subnet per AZ across ≥2 (prefer 3) AZs. A subnet lives in exactly one AZ, so HA is impossible without duplicating subnets across AZs.
- Verification: `aws ec2 describe-subnets --filters Name=vpc-id,Values=<vpc-id> --query "Subnets[].AvailabilityZone" --output text | tr '\t' '\n' | sort -u` → expect ≥2 distinct AZs per tier.
- Source: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-best-practices.html

**2. Public / private / isolated subnet tier model driven by route tables**
- Pillar Alignment: Security, Reliability
- Why: A subnet is public only because its route table sends `0.0.0.0/0` to an internet gateway; databases and internal services must never sit in a subnet with a public default route. AWS's reference VPC uses public subnets (IGW route) plus private subnets (NAT/no public route).
- AWS Services: VPC, Route tables, Internet Gateway, NAT Gateway
- Architecture Decision: Public tier (ALB/NAT only) routes `0.0.0.0/0` → IGW. Private/app tier routes `0.0.0.0/0` → NAT gateway. Isolated/data tier has no default route to internet at all (only `local` + VPC endpoints).
- Verification: `aws ec2 describe-route-tables --filters Name=vpc-id,Values=<vpc-id>` and confirm no data-tier route table contains an `igw-` target.
- Source: https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Route_Tables.html

**3. Plan non-overlapping RFC 1918 CIDR blocks; size for growth**
- Pillar Alignment: Reliability, Operational Excellence
- Why: A VPC IPv4 block is `/16`–`/28`; **you cannot increase or decrease the size of an existing CIDR block**, and overlapping ranges permanently block VPC peering, Transit Gateway, and Direct Connect gateway associations. AWS recommends RFC 1918 ranges (10/8, 172.16/12, 192.168/16). (Source: [VPC CIDR blocks](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-cidr-blocks.html), verified 2026-07-31)
- AWS Services: VPC, IP Address Manager (IPAM)
- Architecture Decision: Allocate each VPC a distinct non-overlapping block from a central plan (use IPAM in multi-account landing zones). Avoid `172.17.0.0/16` (used by Cloud9/SageMaker). Reserve headroom for secondary CIDRs rather than starting at `/24`.
- Verification: `aws ec2 describe-vpcs --query "Vpcs[].CidrBlockAssociationSet[].CidrBlock"` across accounts; confirm no overlaps.
- Source: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-cidr-blocks.html

**4. NAT capacity per Availability Zone for private-subnet egress**
- Pillar Alignment: Reliability, Cost Optimization
- Why: A NAT gateway is AZ-scoped. Routing all private subnets through a single NAT gateway makes every AZ depend on one AZ; if that AZ fails, all egress fails. AWS's resilient pattern is a NAT gateway per AZ with each AZ's private route table pointing to its local NAT gateway. (A newer alternative, Regional NAT gateways for automatic multi-AZ expansion, is documented as a topic under NAT gateways.)
- AWS Services: NAT Gateway, Elastic IP, Route tables
- Architecture Decision: Deploy one public NAT gateway per AZ (each in that AZ's public subnet with its own EIP); route each AZ's private subnets to the same-AZ NAT gateway. Cross-AZ NAT routing also incurs cross-AZ data charges.
- Verification: `aws ec2 describe-nat-gateways --filter Name=vpc-id,Values=<vpc-id> --query "NatGateways[].SubnetId"` → confirm distinct AZs match the private route tables.
- Source: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html

**5. Private access to AWS services via VPC endpoints (PrivateLink)**
- Pillar Alignment: Security, Cost Optimization
- Why: A VPC endpoint connects to AWS services "privately, without the use of an internet gateway or NAT device," keeping traffic off the public internet and (for S3/DynamoDB gateway endpoints) removing NAT data-processing charges for that traffic. (Source: [What is Amazon VPC? — Gateways and endpoints](https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html), verified 2026-07-31)
- AWS Services: Gateway VPC endpoints (S3, DynamoDB), Interface VPC endpoints / PrivateLink
- Architecture Decision: Add gateway endpoints for S3/DynamoDB (free) to relevant route tables; add interface endpoints for services accessed from isolated subnets (e.g., Secrets Manager, KMS, ECR, CloudWatch Logs) so data-tier subnets need no NAT/IGW at all.
- Verification: `aws ec2 describe-vpc-endpoints --filters Name=vpc-id,Values=<vpc-id> --query "VpcEndpoints[].ServiceName"`.
- Source: https://docs.aws.amazon.com/vpc/latest/privatelink/privatelink-access-aws-services.html

**6. Enable VPC Flow Logs at the VPC scope**
- Pillar Alignment: Security, Operational Excellence
- Why: AWS lists Flow Logs as a security best practice to monitor IP traffic to/from a VPC, subnet, or interface; GuardDuty's foundational threat detection consumes VPC Flow Logs. (Source: [VPC security best practices](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-best-practices.html), verified 2026-07-31)
- AWS Services: VPC Flow Logs, CloudWatch Logs / S3, GuardDuty
- Architecture Decision: Create a Flow Log at VPC scope (captures all ENIs, including future ones) delivering to CloudWatch Logs and/or S3; retain per compliance policy. Note: flow logs are metadata (5-tuple + action + bytes), not packet payloads — use Traffic Mirroring for deep packet inspection.
- Verification: `aws ec2 describe-flow-logs --filter Name=resource-id,Values=<vpc-id>` → expect at least one ACTIVE flow log.
- Source: https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html

**7. Security groups as primary control, NACLs as subnet backstop**
- Pillar Alignment: Security
- Why: AWS best practice: "Use security groups to control traffic to EC2 instances" and "Use network ACLs to control inbound and outbound traffic at the subnet level." Security groups are stateful and instance-scoped (allow-only); NACLs are stateless and subnet-scoped (support explicit deny). (Source: [VPC security best practices](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-best-practices.html), verified 2026-07-31)
- AWS Services: Security groups, Network ACLs
- Architecture Decision: Write tier-to-tier rules by referencing security groups as sources (e.g., app SG allows 5432 only from the web SG). Keep NACLs coarse (e.g., deny known-bad CIDRs); remember ephemeral return ports because NACLs are stateless.
- Verification: `aws ec2 describe-security-groups` — confirm no `0.0.0.0/0` on management ports; use Network Access Analyzer to find unintended paths.
- Source: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-best-practices.html

## ⚠️ Architectural Decisions

**A. VPC-to-VPC connectivity: VPC Peering vs Transit Gateway**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | VPC Peering | VPC Peering | Lowest cost, lowest latency, simple | Non-transitive; 1:1 mesh explodes as N grows (N·(N-1)/2 links) | Few VPCs (≤ ~5), stable topology, no transitive routing needed |
  | Transit Gateway | AWS Transit Gateway | Transitive hub-and-spoke, centralized egress/inspection, scales to thousands of attachments | Hourly + per-GB attachment/data charges; added hop | Many VPCs, shared services, centralized inspection, hybrid |

- Cost Profile: Peering has no per-hour charge (only cross-AZ/inter-Region data); TGW adds per-attachment-hour + per-GB processed.
- Lock-in Assessment: Both are AWS-native constructs; migration between them is a routing change, not a data migration.
- Architect Instruction: "Ask about expected VPC count and whether transitive routing or centralized egress/inspection is required before choosing peering vs Transit Gateway."
- Source: https://docs.aws.amazon.com/whitepapers/latest/aws-vpc-connectivity-options/introduction.html

**B. Hybrid connectivity: Site-to-Site VPN vs Direct Connect (± Transit Gateway)**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Site-to-Site VPN | AWS Site-to-Site VPN | Fast to stand up, encrypted over internet, low fixed cost | Internet-variable latency/throughput | Quick start, backup path, moderate bandwidth |
  | Direct Connect | AWS Direct Connect | Private consistent bandwidth/latency | Weeks to provision, port + circuit cost | Sustained high throughput, predictable latency, compliance |
  | DX + VPN | Direct Connect + S2S VPN | Private path + encryption | Highest complexity/cost | Encrypted private hybrid links |
  | + Transit Gateway | TGW + DX/VPN | Single regional hub for all hybrid + VPC routing | TGW charges | Many VPCs sharing one hybrid entry point |

- Cost Profile: VPN lowest fixed cost; DX has port-hour + data-transfer-out at reduced rates; TGW adds attachment charges.
- Lock-in Assessment: DX requires physical cross-connect commitment; VPN is portable.
- Architect Instruction: "Ask for required bandwidth, latency SLA, and provisioning timeline before choosing VPN vs Direct Connect."
- Source: https://docs.aws.amazon.com/whitepapers/latest/aws-vpc-connectivity-options/introduction.html

**C. IP addressing: IPv4-only vs Dual-stack (IPv4 + IPv6)**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | IPv4-only | VPC IPv4 CIDR | Simplicity, universal compatibility | Public IPv4 addresses are now charged per hour; RFC 1918 exhaustion at scale | Legacy/most existing workloads |
  | Dual-stack | VPC IPv4 + Amazon-provided IPv6 | Vast address space; IPv6 egress via egress-only IGW at no NAT cost; reduces public IPv4 spend | Operational maturity; not every service supports IPv6 | New large-scale or IPv4-constrained designs |

- Cost Profile: Public IPv4 addresses incur an hourly charge; IPv6 addresses are not charged and IPv6 egress uses a free egress-only internet gateway (vs paid NAT gateway).
- Lock-in Assessment: Amazon-provided IPv6 blocks (`/56`, subnets `/64`) are AWS-assigned and not portable; BYOIPv6 is possible.
- Architect Instruction: "Ask whether IPv6 is required by downstream systems and whether the team is ready to operate dual-stack before enabling it."
- Source: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-cidr-blocks.html (IPv6) and https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html (public IPv4 pricing)

**D. Egress control: distributed NAT per VPC vs centralized egress via Transit Gateway**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Distributed NAT | NAT gateway per VPC per AZ | Simplicity, isolation, no shared bottleneck | NAT cost multiplies across VPCs; no central inspection | Few VPCs, independent teams |
  | Centralized egress | TGW + inspection/egress VPC (Network Firewall) | Central inspection, fewer NAT gateways, unified policy | Central bottleneck/blast radius; TGW + firewall cost | Many VPCs needing uniform egress control/inspection |

- Cost Profile: Centralizing reduces NAT gateway count but adds TGW data-processing + firewall costs; model both.
- Lock-in Assessment: Both AWS-native; changing is a routing/topology change.
- Architect Instruction: "Ask whether centralized egress inspection is a compliance requirement before consolidating NAT."
- Source: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html and https://docs.aws.amazon.com/whitepapers/latest/aws-vpc-connectivity-options/introduction.html

## 🚫 Anti-Patterns

**AP-1. Single-AZ subnet layout for production**
- Risk Level: CRITICAL
- Why: Violates Reliability. A subnet is pinned to one AZ; a single-AZ deployment fails entirely on one AZ impairment.
- ❌ Wrong: All app/EC2 instances and the RDS primary in one subnet in `us-east-1a`; no subnets in other AZs.
- ✅ Correct: Private subnets in `us-east-1a`, `us-east-1b`, `us-east-1c`; Auto Scaling group across all three; RDS Multi-AZ with a standby in a second AZ.
- Detection: `aws ec2 describe-subnets ... --query "Subnets[].AvailabilityZone" | sort -u` returns a single AZ.
- Impact: Service outage.
- Source: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-best-practices.html

**AP-2. Overlapping or unplanned CIDR ranges**
- Risk Level: HIGH
- Why: Violates Reliability/Operational Excellence. Overlapping VPC CIDRs cannot be peered, attached to a Transit Gateway route domain, or associated to the same Direct Connect gateway; and a VPC CIDR block cannot be resized after creation.
- ❌ Wrong: Every VPC created as `10.0.0.0/16`; two are later required to peer.
- ✅ Correct: Central IPAM plan assigning `10.0.0.0/16`, `10.1.0.0/16`, `10.2.0.0/16` to distinct VPCs from disjoint ranges; avoid `172.17.0.0/16`.
- Detection: `aws ec2 describe-vpcs --query "Vpcs[].CidrBlockAssociationSet[].CidrBlock"` across accounts; check for overlaps (or use IPAM).
- Impact: Cascading failure — blocks future connectivity, forces VPC rebuild.
- Source: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-cidr-blocks.html

**AP-3. Databases / internal services in a public subnet**
- Risk Level: CRITICAL
- Why: Violates Security. A subnet whose route table sends `0.0.0.0/0` to an IGW exposes any resource with a public IP to the internet.
- ❌ Wrong: RDS instance launched in a subnet whose route table has `0.0.0.0/0 → igw-xxxx`, with a public IP assigned.
- ✅ Correct: RDS in an isolated subnet (route table has only `local` + VPC endpoints, no IGW/NAT default route); reachable only from the app-tier security group on port 5432.
- Detection: Cross-check data-store ENIs' subnets against route tables containing an `igw-` target; Network Access Analyzer scope.
- Impact: Data breach.
- Source: https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Route_Tables.html

**AP-4. Wide-open security group ingress on management ports**
- Risk Level: CRITICAL
- Why: Violates Security. `0.0.0.0/0` on SSH (22) / RDP (3389) exposes management surface to the entire internet.
- ❌ Wrong: Security group inbound rule `TCP 22, Source 0.0.0.0/0`.
- ✅ Correct: No public SSH/RDP; use AWS Systems Manager Session Manager (no inbound port). If direct access is unavoidable, restrict source to a corporate CIDR or a bastion security group reference.
- Detection: `aws ec2 describe-security-groups --query "SecurityGroups[?IpPermissions[?ToPort==\`22\` && contains(IpRanges[].CidrIp, '0.0.0.0/0')]]"`.
- Impact: Data breach / instance compromise.
- Source: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-best-practices.html

**AP-5. VPC Flow Logs disabled**
- Risk Level: HIGH
- Why: Violates Security/Operational Excellence. Without flow logs there is no network traffic record for forensics, and GuardDuty loses a foundational data source.
- ❌ Wrong: VPC created with no flow log; no network telemetry retained.
- ✅ Correct: VPC-scoped flow log to CloudWatch Logs and/or S3, retained per policy; GuardDuty enabled.
- Detection: `aws ec2 describe-flow-logs --filter Name=resource-id,Values=<vpc-id>` returns empty.
- Impact: Compliance violation / undetectable intrusion.
- Source: https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html

**AP-6. Single NAT gateway serving all AZs (single-AZ egress dependency)**
- Risk Level: HIGH
- Why: Violates Reliability/Cost. All private subnets routing through one NAT gateway create a single-AZ failure point and cross-AZ data-transfer charges.
- ❌ Wrong: One NAT gateway in `us-east-1a`; private route tables in all AZs point `0.0.0.0/0` to it.
- ✅ Correct: One NAT gateway per AZ (or Regional NAT gateway with automatic multi-AZ expansion); each AZ's private route table targets its same-AZ NAT gateway.
- Detection: `aws ec2 describe-nat-gateways` shows one NAT gateway while private route tables span multiple AZs pointing to it.
- Impact: AZ-scoped outage + avoidable cross-AZ cost.
- Source: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html

**AP-7. Relying solely on NACLs (or solely on stateless rules) for instance security**
- Risk Level: MEDIUM
- Why: Violates Security. NACLs are stateless and subnet-coarse; using them as the primary control leads to overly broad rules and broken return traffic.
- ❌ Wrong: Permissive security groups plus hand-tuned NACLs attempting per-flow control (and forgetting ephemeral ports).
- ✅ Correct: Security groups (stateful, instance-scoped, SG-referencing) as primary control; NACLs as a coarse deny backstop only.
- Detection: Review for NACLs with complex per-app rules and security groups with broad `0.0.0.0/0` allows.
- Impact: Broken connectivity or over-exposure.
- Source: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-best-practices.html

---

# Cloud-Native Design Patterns

**Three-tier VPC (web / app / data)**
- Category: Scalability / Resilience
- Problem: Isolate internet-facing, application, and data layers with least exposure while keeping HA.
- Solution on AWS: Public subnets (ALB + NAT gateway) per AZ; private app subnets (compute) per AZ routing egress via same-AZ NAT; isolated data subnets (RDS/ElastiCache) per AZ with no internet route, reached only via security-group references and VPC endpoints.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Security | Data tier has no internet path | More subnets/route tables to manage |
  | Reliability | Per-AZ redundancy at every tier | More NAT gateways (cost) |
  | Cost | Gateway endpoints remove NAT cost for S3/DynamoDB | Interface endpoints add hourly charges |

- Source: https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Route_Tables.html

**Hub-and-spoke with Transit Gateway**
- Category: Communication / Scalability
- Problem: Connect many VPCs (and hybrid links) with transitive routing and central control.
- Solution on AWS: A Transit Gateway as regional hub; each VPC, VPN, and Direct Connect attaches once; TGW route tables segment which spokes can reach which (e.g., isolate prod from dev, route all egress through an inspection VPC).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Scalability | Thousands of attachments, transitive | Per-attachment-hour + per-GB processed |
  | Operability | Central routing and inspection | Central blast radius |

- Source: https://docs.aws.amazon.com/whitepapers/latest/aws-vpc-connectivity-options/aws-transit-gateway.html

---

# Security Architecture

**Network segmentation & private service access**
- AWS Services: Security groups, Network ACLs, VPC endpoints (gateway + interface / PrivateLink), AWS Network Firewall, Network Access Analyzer, GuardDuty
- Architecture: Security groups enforce stateful, least-privilege, SG-referenced tier-to-tier rules; NACLs give a coarse subnet deny backstop; VPC endpoints keep AWS-service traffic private (no IGW/NAT); AWS Network Firewall filters inbound/outbound at defined inspection points; Network Access Analyzer validates there are no unintended paths; GuardDuty consumes Flow Logs for threat detection.
- Compliance Alignment: Supports network-isolation and monitoring controls common to SOC 2 / PCI-DSS / HIPAA (structure only — confirm certification scope with the organization; not legal advice).
- Source: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-best-practices.html

---

# Operational Patterns

**Network observability & egress cost control**
- RTO/RPO: N/A (network is stateless infra; recovery is via re-provisioning IaC + multi-AZ redundancy).
- AWS Services: VPC Flow Logs → CloudWatch Logs / S3, NAT gateway CloudWatch metrics, Network Access Analyzer, Reachability Analyzer
- Cost Profile: Medium — primary drivers are NAT gateway hourly + per-GB data processing, interface-endpoint hours, cross-AZ data transfer, and (now) public IPv4 address hours. Reduce with gateway endpoints (S3/DynamoDB), per-AZ NAT to avoid cross-AZ charges, and IPv6/egress-only IGW where supported.
- Automation: Provision all VPC constructs as IaC (CloudFormation/CDK/Terraform); automate Flow Log enablement and security-group drift detection; use Reachability Analyzer in change pipelines to prove connectivity before/after changes.
- Source: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html and https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html

---

# Reference Architectures

**Production three-tier VPC (3 AZs)**
- Context: Internet-facing multi-tier web application requiring HA and a private data tier.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Ingress | Internet Gateway + Application Load Balancer (public subnets) | Public entry, TLS termination |
  | Egress | NAT gateway per AZ (public subnets) | Outbound-only for private tiers |
  | Compute | EC2/ECS in private app subnets per AZ | Application logic |
  | Data | RDS Multi-AZ / ElastiCache in isolated subnets | Stateful stores, no internet route |
  | Private AWS access | Gateway endpoints (S3, DynamoDB) + interface endpoints (KMS, Secrets Manager, ECR, Logs) | AWS-service access without NAT/IGW |
  | Telemetry | VPC Flow Logs → CloudWatch/S3, GuardDuty | Monitoring & threat detection |

- Key Decisions: AZ count (2 vs 3), CIDR size + IPAM allocation, dual-stack vs IPv4-only, which interface endpoints to add, per-VPC NAT vs centralized egress.
- Scaling Path: Add secondary CIDR blocks for more subnet space; move from VPC peering to Transit Gateway as VPC count grows; introduce a centralized egress/inspection VPC (Network Firewall) under TGW.
- Source: https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html

---

# Service Equivalence Map

Networking-service equivalence across providers (aids architects comparing designs). Equivalence is **not** feature parity — validate against each provider's current docs.

| Category | AWS | Google Cloud | Azure | Oracle Cloud (OCI) |
|----------|-----|--------------|-------|--------------------|
| Virtual network | VPC | VPC network | Virtual Network (VNet) | VCN |
| Subnet | Subnet (single AZ) | Subnet (regional) | Subnet | Subnet (regional or AD-specific) |
| Internet egress (NAT) | NAT gateway | Cloud NAT | NAT gateway | NAT gateway |
| Internet ingress gateway | Internet gateway | (default internet gateway) | (Public IP / gateway) | Internet gateway |
| Instance firewall | Security group (stateful) | Firewall rules (VPC-level) | Network Security Group (NSG) | Security list / Network security group |
| Subnet ACL | Network ACL (stateless) | Hierarchical firewall policies | NSG (subnet-associated) | Security list |
| VPC-to-VPC peering | VPC Peering | VPC Network Peering | VNet Peering | Local/Remote VCN Peering |
| Transit hub | Transit Gateway | Network Connectivity Center | Virtual WAN / VNet hub | DRG (Dynamic Routing Gateway) |
| Private service access | VPC endpoints / PrivateLink | Private Service Connect | Private Link / Private Endpoint | Service Gateway / Private Endpoint |
| Dedicated interconnect | Direct Connect | Cloud Interconnect | ExpressRoute | FastConnect |
| Site-to-site VPN | Site-to-Site VPN | Cloud VPN | VPN Gateway | Site-to-Site VPN |
| Flow logs | VPC Flow Logs | VPC Flow Logs | NSG Flow Logs / VNet flow logs | VCN Flow Logs |
| Managed network firewall | AWS Network Firewall | Cloud NGFW | Azure Firewall | OCI Network Firewall |
| DNS | Route 53 (private hosted zones) | Cloud DNS | Azure Private DNS | OCI DNS / Private DNS |

> ⚠️ Service equivalence does NOT mean feature parity (e.g., AWS subnets are AZ-scoped while GCP subnets are regional; AWS security groups are stateful, GCP firewall rules are VPC-level). Validate specifics before cross-provider decisions.

---

# Provider Differentiators (AWS networking)

```
Differentiator: AWS PrivateLink + Gateway/Interface VPC endpoints
Category: Security / Networking
Unique Value: Private, in-network access to AWS services and third-party SaaS via an ENI in your VPC, with gateway endpoints (S3/DynamoDB) offered at no charge.
Architecture Impact: Enables truly isolated data-tier subnets with zero internet route.
When to Leverage: Regulated workloads that must keep AWS-service traffic off the public internet.
Caveat: Interface endpoints incur hourly + data-processing charges; gateway endpoints are limited to S3 and DynamoDB.
Source: https://docs.aws.amazon.com/vpc/latest/privatelink/privatelink-access-aws-services.html
```
```
Differentiator: AWS Transit Gateway + AWS Cloud WAN
Category: Networking
Unique Value: Regional transitive hub (TGW) and a managed global WAN (Cloud WAN) for building/monitoring global interconnections across VPCs, data centers, and branches.
Architecture Impact: Replaces N-squared peering meshes and DIY transit VPCs with managed routing domains.
When to Leverage: Many-VPC / multi-Region / hybrid topologies needing centralized segmentation and inspection.
Caveat: Per-attachment and data-processing charges; adds a routing hop.
Source: https://docs.aws.amazon.com/whitepapers/latest/aws-vpc-connectivity-options/introduction.html
```

---

# Scenario Coverage

**Standard Case**: Internet-facing three-tier web app.
- Approach: 3-AZ VPC with public/private/isolated tiers, ALB + per-AZ NAT, RDS Multi-AZ in isolated subnets, gateway + interface endpoints, VPC Flow Logs + GuardDuty.
- Key Decisions: AZ count, CIDR/IPAM allocation, which interface endpoints, IPv4-only vs dual-stack, per-VPC vs centralized egress.

**Edge Case**: RFC 1918 exhaustion / many overlapping legacy VPCs needing to interconnect.
- Approach: Adopt IPAM as source of truth; use secondary CIDRs (incl. `100.64.0.0/10`) for growth; where overlaps already exist, use private NAT gateway + PrivateLink to bridge overlapping VPCs without re-IP; plan dual-stack IPv6 for large new footprints.

**Anti-Pattern Case**: A request to "put the database in the public subnet so developers can connect directly," or to open SSH `0.0.0.0/0`.
- Clarification: Refuse and flag (AP-3, AP-4). Ask: what access pattern is actually needed? Offer Session Manager (no inbound port), a bastion in a public subnet with SG-referenced access, or client VPN — keeping the data tier isolated.

---

# Source Bibliography

### Primary Sources (official AWS documentation — verified 2026-07-31)
- [What is Amazon VPC?](https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html) — core components, features, public IPv4 pricing
- [Security best practices for your VPC](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-best-practices.html) — multi-AZ, SG/NACL, Flow Logs, Network Firewall, GuardDuty
- [VPC CIDR blocks](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-cidr-blocks.html) — /16–/28, RFC 1918, no-resize rule, association restrictions, IPv6 /44–/60
- [Subnet CIDR blocks](https://docs.aws.amazon.com/vpc/latest/userguide/subnet-sizing.html) — /28–/16, five reserved IPs per subnet, IPv6 /44–/64
- [NAT gateways](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html) — public vs private NAT, per-AZ resiliency, Regional NAT gateway topic
- [VPC connectivity options whitepaper](https://docs.aws.amazon.com/whitepapers/latest/aws-vpc-connectivity-options/introduction.html) — peering, TGW, VPN, Direct Connect, PrivateLink, Cloud WAN
- [AWS PrivateLink — access AWS services](https://docs.aws.amazon.com/vpc/latest/privatelink/privatelink-access-aws-services.html) — VPC endpoints

### Governing Framework
- [AWS Well-Architected Framework — welcome](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html) — publication date 2024-11-06; six pillars (Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, Sustainability). ⚠️ ~20 months old; current stable edition — re-verify on next review.

### Referenced (linked from primary sources; not independently re-fetched this session — verify before load-bearing use)
- Route tables: https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Route_Tables.html
- VPC Flow Logs: https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html
- IP addressing (IPv4/IPv6): https://docs.aws.amazon.com/vpc/latest/userguide/vpc-ip-addressing.html
- Amazon VPC quotas: https://docs.aws.amazon.com/vpc/latest/userguide/amazon-vpc-limits.html

---

# Agent Operation Notes (for downstream skill authoring)

- **High confidence (verified live 2026-07-31)**: VPC/subnet CIDR ranges and reserved-IP rules, no-resize constraint, five reserved IPs per subnet, RFC 1918 recommendation + restricted ranges, multi-AZ best practice, SG (stateful) vs NACL (stateless), Flow Logs + GuardDuty, VPC endpoint privacy, NAT public/private + per-AZ resiliency, connectivity-option set (peering/TGW/VPN/DX/PrivateLink/Cloud WAN).
- **Medium confidence (verify before use)**: Exact current pricing figures (public IPv4 hourly rate, NAT per-GB), and the maturity/limits of "Regional NAT gateways for automatic multi-AZ expansion" — documented as a topic but not deep-fetched this session.
- **Must ask user (Low confidence per skill guardrails)**: compliance certification scope (SOC2/HIPAA/PCI-DSS/GDPR specifics), organization CIDR plan/IPAM ownership, and any cost commitments (DX contracts, savings plans).
- **Recommended next step**: run `/skill-best-practices-validator` on any SKILL.md authored from this research.
```