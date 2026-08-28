# AWS VPC — Networking Architecture Knowledge Base

---

## Metadata

```yaml
Full_Name: "AWS VPC — Networking Architecture"
Cloud_Provider: "AWS"
Architecture_Domain: "Networking-Architecture"
Target_Edition: "AWS VPC 2024"
Architecture_Context: "Production cloud workloads requiring secure, scalable, and highly available network infrastructure — covering multi-account topologies, hybrid connectivity, service mesh, microservices communication, network segmentation, and zero-trust networking"
Official_Source_URL: "https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-05-28"
Currency_Threshold: "2027-05-28 — review required after this date due to VPC feature evolution, new endpoint types, and pricing changes (public IPv4 charging)"
```

---

## Executive Summary

Amazon Virtual Private Cloud (Amazon VPC) is the foundational network isolation layer for all AWS workloads. Every compute, data, and application service deployed in AWS operates within a VPC — either a customer-managed VPC or an AWS-managed service VPC. A VPC provides a logically isolated virtual network that closely resembles a traditional data center network, with the benefits of AWS's scalable, globally interconnected infrastructure. VPCs support both IPv4 and IPv6 addressing, span all Availability Zones within a Region, and provide software-defined networking primitives (subnets, route tables, gateways, security groups, network ACLs) that compose into arbitrarily complex network topologies.

The 2024 edition's most architecturally significant advances are: (1) **Public IPv4 address charging** (effective February 2024) — all public IPv4 addresses now incur $0.005/hour ($3.60/month) charges, fundamentally changing cost optimization strategies toward IPv6 adoption, NAT consolidation, and PrivateLink usage; (2) **Regional NAT Gateways** — automatic multi-AZ expansion eliminating the need for per-AZ NAT gateway provisioning and route table management; (3) **VPC Lattice GA** — application-layer service-to-service networking that abstracts away VPC boundaries, enabling service mesh without sidecar proxies; (4) **Security Group VPC Association** — ability to associate security groups across VPCs in the same Region, simplifying multi-VPC security management; (5) **Transit Gateway Encryption Control** — enforced encryption-in-transit for all traffic on VPCs attached to the transit gateway; (6) **AWS Cloud WAN integration maturity** — global network management with automated routing policies across Regions; (7) **VPC Block Public Access (BPA)** — account-level control that prevents internet gateway routing from any VPC in the account without explicit exception.

The three most critical networking architecture guardrails are: (1) **Plan IP addressing before creating any VPC** — CIDR overlaps are irrecoverable without migration; use Amazon VPC IPAM for hierarchical IP allocation across accounts, Regions, and environments; (2) **Deploy subnets across at minimum 3 Availability Zones for production workloads** — single-AZ or dual-AZ designs create unacceptable blast radius for AZ failures; (3) **Never expose resources directly to the internet without defense-in-depth** — layer security groups, NACLs, WAF, Shield, and Network Firewall; the default-deny posture at every boundary is the only defensible architecture for production workloads.

---

## Cloud Architecture Glossary

```
Term: Virtual Private Cloud (VPC)
Definition: A logically isolated virtual network dedicated to an AWS account within a single AWS Region. A VPC spans all Availability Zones in the Region. You define the VPC's IPv4 CIDR block (between /16 and /28) and optionally one or more IPv6 CIDR blocks. A VPC provides DNS resolution, DHCP options, and a main route table. Up to 5 VPCs per Region by default (adjustable via quota).
Provider Docs Section: https://docs.aws.amazon.com/vpc/latest/userguide/configure-your-vpc.html
Architect Usage: One VPC per workload per environment is the recommended isolation pattern. VPCs in the same account can peer without additional routing hops. Use separate VPCs for production, staging, and development to enforce blast radius isolation.
Common Confusion: A VPC is NOT a subnet — it spans the entire Region (all AZs). Subnets are AZ-scoped subdivisions within a VPC. A VPC is NOT an account boundary — multiple VPCs can exist in one account, and VPCs in different accounts can be connected via peering, Transit Gateway, or PrivateLink.

Term: Subnet
Definition: A range of IP addresses (IPv4 CIDR block) within a VPC, scoped to a single Availability Zone. Subnets are classified as public (route table has a route to an Internet Gateway), private (no internet gateway route, typically routes through NAT Gateway), or isolated (no internet route at all). Each subnet must reside entirely within one AZ.
Provider Docs Section: https://docs.aws.amazon.com/vpc/latest/userguide/configure-subnets.html
Architect Usage: Create at minimum one public subnet, one private subnet, and optionally one isolated subnet per AZ. Size subnets to accommodate growth — AWS reserves 5 IP addresses per subnet (first 4 + last 1). A /24 yields 251 usable IPs. For EKS workloads, size private subnets at /19 or larger to accommodate pod IP consumption.
Common Confusion: "Public subnet" does NOT mean its instances are public. A subnet is public because its route table routes 0.0.0.0/0 to an Internet Gateway. Instances in a public subnet still require a public IP (or EIP) AND security group rules to be reachable from the internet. Confusing subnet type with instance accessibility is the most common networking misconfiguration.

Term: Route Table
Definition: A set of rules (routes) that determine where network traffic is directed. Each route specifies a destination CIDR and a target (IGW, NAT GW, TGW, VPC Peering, VPC Endpoint, Network Interface, etc.). Every subnet must be associated with exactly one route table. The VPC has a main route table (implicit association for subnets without explicit association) plus custom route tables.
Provider Docs Section: https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Route_Tables.html
Architect Usage: Never use the main route table for production routing — create explicit route tables per subnet tier (public, private, isolated). This prevents accidental exposure if a new subnet is created without explicit association. Use route table propagation with Transit Gateway and VPN connections to automatically learn routes.
Common Confusion: Route tables evaluate the most specific route (longest prefix match), not rule order. A route to 10.0.1.0/24 takes precedence over 10.0.0.0/16 for traffic destined to 10.0.1.5. This is different from NACLs which use numbered rule order.

Term: Internet Gateway (IGW)
Definition: A horizontally scaled, redundant, and highly available VPC component that allows communication between instances in a VPC and the internet. An IGW serves two purposes: providing a target in route tables for internet-routable traffic and performing NAT (network address translation) for instances with public IPv4 addresses. One IGW per VPC. No bandwidth constraints.
Provider Docs Section: https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Internet_Gateway.html
Architect Usage: Attach an IGW to VPCs that require internet access (public-facing load balancers, NAT gateways). For VPCs hosting only backend services, consider NOT attaching an IGW at all — use Transit Gateway for egress via a centralized inspection VPC. The presence of an IGW alone does NOT expose any resource; routes and security groups must also permit traffic.
Common Confusion: An IGW does NOT charge for data transfer. Data transfer charges come from EC2, NAT Gateway, or other services. The IGW is a logical construct with no per-hour cost. However, as of 2024, any public IPv4 address assigned (whether used with IGW or not) costs $0.005/hr.

Term: NAT Gateway
Definition: A managed, highly available Network Address Translation service that enables instances in private subnets to connect to the internet (public NAT) or other VPCs/on-premises networks (private NAT) while preventing inbound connections. Supports up to 55,000 simultaneous connections to each unique destination. Throughput scales from 5 Gbps to 100 Gbps per gateway. Regional NAT Gateways (2024) automatically expand across AZs.
Provider Docs Section: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html
Architect Usage: Deploy one NAT Gateway per AZ for high availability (or use Regional NAT Gateway for automatic multi-AZ). Associate sufficient Elastic IPs for high-throughput workloads to avoid port exhaustion (55,000 connections per EIP per destination). Use private NAT gateways for non-overlapping CIDR communication between VPCs without public IPs.
Common Confusion: NAT Gateway is NOT free — charges apply per hour ($0.045/hr in us-east-1) PLUS per-GB processed ($0.045/GB). For high-throughput workloads communicating with AWS services, VPC endpoints (Interface or Gateway) are cheaper than routing through NAT. A common cost mistake is routing S3/DynamoDB traffic through NAT when free Gateway endpoints exist.

Term: Security Group
Definition: A stateful virtual firewall that controls inbound and outbound traffic at the network interface level (ENI). Rules specify allowed traffic only (no deny rules). Return traffic is automatically allowed regardless of rules. Security groups can reference other security groups as sources/destinations (enabling service-tier isolation). Up to 5 security groups per network interface; up to 60 inbound + 60 outbound rules per security group (adjustable).
Provider Docs Section: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html
Architect Usage: Use security groups as the primary access control mechanism. Reference security groups (not CIDR blocks) when defining service-to-service communication — this ensures rules remain valid as instances scale. Create one security group per application tier/role (web-sg, app-sg, db-sg). Default-deny-all-inbound is the initial state and the correct baseline.
Common Confusion: Security groups are STATEFUL (return traffic automatically allowed). NACLs are STATELESS (must explicitly allow return traffic). Security groups operate at the instance/ENI level; NACLs operate at the subnet level. They are complementary layers, not alternatives.

Term: Network Access Control List (NACL)
Definition: A stateless firewall that controls inbound and outbound traffic at the subnet level. Rules are evaluated in numbered order (lowest first); first matching rule applies. Supports both allow and deny rules. Each subnet is associated with exactly one NACL. The default NACL allows all inbound and outbound traffic. Custom NACLs deny all traffic by default.
Provider Docs Section: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-network-acls.html
Architect Usage: Use NACLs as a coarse-grained subnet boundary defense — block known malicious CIDR ranges, enforce port restrictions at the subnet perimeter, or create an emergency "kill switch" for a compromised subnet. NACLs are your second line of defense after security groups. Keep NACL rules minimal and well-documented; overly complex NACLs are operationally brittle.
Common Confusion: NACLs are STATELESS — you MUST create rules for both inbound AND outbound traffic (including ephemeral port ranges 1024-65535 for return traffic). Forgetting outbound ephemeral port rules is the #1 cause of "security group allows it but traffic still doesn't work" issues.

Term: Transit Gateway (TGW)
Definition: A regional network transit hub that interconnects VPCs, VPN connections, Direct Connect gateways, and other Transit Gateways (inter-Region peering). Supports up to 5,000 attachments per TGW. Uses route tables for traffic routing between attachments. Supports 50 Gbps per VPC attachment (burstable). Supports encryption control for enforced encryption-in-transit. Charged per attachment per hour + per-GB data processed.
Provider Docs Section: https://docs.aws.amazon.com/vpc/latest/tgw/what-is-transit-gateway.html
Architect Usage: Use Transit Gateway as the central routing hub for multi-VPC and hybrid architectures (replaces full-mesh VPC peering which doesn't scale beyond ~10 VPCs). Create multiple route tables on TGW for network segmentation (shared services, production, development). Enable route propagation for VPN/Direct Connect and use static routes for VPC attachments that require isolation.
Common Confusion: Transit Gateway is REGIONAL — for cross-Region connectivity, you need Transit Gateway inter-Region peering (or AWS Cloud WAN for global policy-based routing). TGW does NOT transit traffic between VPC peering connections (peering is non-transitive by design). TGW supports an MTU of 8500 bytes for VPC-to-VPC traffic but only 1500 bytes for VPN.

Term: VPC Endpoint
Definition: A private connection between a VPC and a supported AWS service (or VPC endpoint service) that does not traverse the internet. Two types: Gateway Endpoints (S3, DynamoDB — free, route-table-based) and Interface Endpoints (powered by AWS PrivateLink — ENI with private IP in subnet, charged per hour + per GB). Gateway Load Balancer Endpoints route traffic to network virtual appliances.
Provider Docs Section: https://docs.aws.amazon.com/vpc/latest/privatelink/privatelink-access-aws-services.html
Architect Usage: ALWAYS use Gateway Endpoints for S3 and DynamoDB (free, reduces NAT costs). Use Interface Endpoints for all other AWS services in production workloads that should not traverse the internet. Interface Endpoints create an ENI in your subnet — ensure security groups on the endpoint allow traffic from your resources. Use VPC endpoint policies to restrict which actions/resources are accessible through the endpoint.
Common Confusion: Gateway Endpoints are free but only work for S3 and DynamoDB. Interface Endpoints cost $0.01/hr per AZ + $0.01/GB but work for 100+ AWS services. Gateway Endpoints use route table entries; Interface Endpoints use DNS resolution to private IPs (enable Private DNS for transparent integration).

Term: AWS PrivateLink
Definition: A networking technology that provides private connectivity between VPCs, AWS services, and on-premises networks without exposing traffic to the public internet. PrivateLink powers Interface VPC Endpoints, Resource VPC Endpoints, and VPC Endpoint Services (customer-hosted services exposed to other accounts via NLB or GWLB). Traffic does not traverse the internet and is not subject to internet routing risks.
Provider Docs Section: https://docs.aws.amazon.com/vpc/latest/privatelink/what-is-privatelink.html
Architect Usage: Use PrivateLink to expose internal services to consumers in other VPCs/accounts without VPC peering (avoids CIDR overlap issues and limits blast radius). PrivateLink is unidirectional — the consumer initiates connections to the provider. Use for B2B SaaS integrations, shared services platforms, and inter-account service exposure.
Common Confusion: PrivateLink ≠ VPC Peering. Peering connects entire VPCs bidirectionally (all IPs routable). PrivateLink exposes a single service endpoint unidirectionally. PrivateLink works across accounts, Regions (via inter-Region endpoints), and even across overlapping CIDRs — something VPC peering cannot do.

Term: VPC Flow Logs
Definition: A feature that captures information about IP traffic going to and from network interfaces in a VPC. Flow logs can be published to CloudWatch Logs, S3, or Kinesis Data Firehose. Can be created at VPC level (all ENIs), subnet level, or individual ENI level. Captures accepted traffic, rejected traffic, or all traffic. Supports custom log format with 20+ fields including TCP flags, traffic path, and metadata.
Provider Docs Section: https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html
Architect Usage: Enable VPC Flow Logs at the VPC level for all production VPCs — publish to S3 for long-term analysis (Athena queries) and to CloudWatch for real-time alerting on rejected traffic patterns. Use custom format to include traffic-path fields for troubleshooting asymmetric routing. Flow logs do NOT capture packet payloads — use Traffic Mirroring or Network Firewall for deep packet inspection.
Common Confusion: Flow logs are NOT real-time — there is an aggregation window (typically 1 minute, configurable to 10 minutes). They capture metadata (5-tuple + bytes/packets) NOT payload content. Flow logs do NOT capture traffic to/from link-local addresses, DHCP, DNS to the VPC resolver, or instance metadata service.

Term: AWS Network Firewall
Definition: A managed, stateful network firewall and intrusion detection/prevention service for VPCs. Deploys firewall endpoints in dedicated subnets. Supports Suricata-compatible IPS rules, domain-based filtering (allow/deny lists), protocol-level inspection, and TLS inspection. Integrates with AWS Firewall Manager for multi-account policy management. Charged per firewall endpoint per AZ per hour + per GB processed.
Provider Docs Section: https://docs.aws.amazon.com/network-firewall/latest/developerguide/what-is-aws-network-firewall.html
Architect Usage: Deploy Network Firewall in a centralized inspection VPC (connected via Transit Gateway) for east-west and north-south traffic inspection. Use domain allow-lists for egress filtering (prevent data exfiltration to unauthorized domains). Combine with Gateway Load Balancer for inline inspection architectures. Network Firewall is the AWS-native alternative to third-party virtual appliances (Palo Alto, Fortinet).
Common Confusion: Network Firewall is NOT the same as security groups or NACLs. It operates at Layer 3-7 with stateful inspection, IPS signatures, and domain filtering. It requires dedicated firewall subnets and route table engineering to steer traffic through the firewall endpoints. Incorrect route table configuration is the #1 deployment failure mode.

Term: VPC Peering
Definition: A networking connection between two VPCs that enables routing traffic using private IPv4 or IPv6 addresses. Peering can be established between VPCs in the same account, different accounts, or different Regions (inter-Region peering). Peering is non-transitive — traffic cannot transit through a peered VPC to reach a third VPC. No single point of failure, no bandwidth bottleneck.
Provider Docs Section: https://docs.aws.amazon.com/vpc/latest/peering/what-is-vpc-peering.html
Architect Usage: Use VPC peering for low-latency, high-bandwidth connections between a small number of VPCs (typically ≤10). Peering works well for tightly-coupled services that need maximum throughput without per-GB processing charges. For architectures with >10 VPCs, migrate to Transit Gateway (which scales better and provides centralized routing). Peering does NOT support overlapping CIDRs.
Common Confusion: VPC peering is NON-TRANSITIVE. If VPC-A peers with VPC-B, and VPC-B peers with VPC-C, VPC-A CANNOT reach VPC-C through VPC-B. This is by design for security. For transitive routing, use Transit Gateway. Also: peering does NOT support edge-to-edge routing through gateways (IGW, VPN, Direct Connect of the peer VPC).

Term: AWS Direct Connect
Definition: A dedicated network connection from on-premises to AWS. Provides consistent network performance (1 Gbps, 10 Gbps, 100 Gbps physical connections) with lower per-GB data transfer costs compared to internet-based VPN. Supports private virtual interfaces (VPC access), public virtual interfaces (AWS public services), and transit virtual interfaces (Transit Gateway access). Does NOT encrypt traffic by default — use MACsec (Layer 2) or VPN over Direct Connect (Layer 3) for encryption.
Provider Docs Section: https://docs.aws.amazon.com/directconnect/latest/UserGuide/Welcome.html
Architect Usage: Use Direct Connect for production hybrid connectivity when latency consistency, bandwidth guarantees, or data transfer cost reduction are requirements. Always deploy with redundancy — either dual connections to different Direct Connect locations or Direct Connect + VPN failover. A single Direct Connect connection is a single point of failure and violates HA requirements.
Common Confusion: Direct Connect is NOT encrypted by default (unlike Site-to-Site VPN which always uses IPsec). For compliance-sensitive workloads, layer MACsec encryption (supported on dedicated connections) or IPsec VPN on top of Direct Connect. Direct Connect does NOT traverse the internet — traffic stays on the AWS private backbone from the Direct Connect location.

Term: VPC Lattice
Definition: An application networking service that consistently connects, monitors, and secures communications between services. Operates at Layer 7 (HTTP/HTTPS/gRPC). Provides service discovery, traffic management (weighted routing), and auth policies (IAM-based) without requiring VPC peering, Transit Gateway, or sidecar proxies. Services register with a Service Network that spans VPCs and accounts.
Provider Docs Section: https://docs.aws.amazon.com/vpc-lattice/latest/ug/what-is-vpc-lattice.html
Architect Usage: Use VPC Lattice for east-west service-to-service communication in microservices architectures where services span multiple VPCs or accounts. VPC Lattice replaces the need for complex Transit Gateway routing + internal ALBs for service discovery. Supports IAM auth policies for zero-trust service-to-service authentication. Ideal for platform teams providing shared services to application teams.
Common Confusion: VPC Lattice is NOT a replacement for Transit Gateway. TGW provides Layer 3/4 network connectivity between VPCs. VPC Lattice provides Layer 7 application connectivity between services. They can coexist — TGW for bulk network connectivity, Lattice for application-level service mesh. Lattice also does NOT require overlapping CIDR workarounds since it uses its own link-local address space.

Term: Amazon VPC IPAM (IP Address Manager)
Definition: A VPC feature that helps plan, track, and monitor IP addresses for AWS workloads. IPAM provides IP address pools that can be organized hierarchically (Region → Environment → VPC), automatic CIDR allocation to VPCs using business rules, and overlap detection. Integrates with AWS Organizations for multi-account IP management. Supports both public and private IP address management.
Provider Docs Section: https://docs.aws.amazon.com/vpc/latest/ipam/what-is-it-ipam.html
Architect Usage: Deploy IPAM as the authoritative source of IP truth in multi-account environments. Define top-level pools per Region, sub-pools per environment (prod/staging/dev), and let IPAM auto-allocate non-overlapping CIDRs to new VPCs. IPAM prevents the most common and painful networking error: CIDR overlap between VPCs that need to communicate.
Common Confusion: IPAM does NOT automatically remediate existing CIDR overlaps — it prevents future ones. If VPCs already have overlapping CIDRs, migration (re-IP) or PrivateLink workarounds are required. IPAM's value is in governance and prevention, not remediation.
```

---

## Architecture Guardrails

### ✅ Mandatory Patterns

**Multi-AZ Subnet Deployment**
- Pillar Alignment: Reliability
- Why: "Distribute workloads across multiple AZs to maintain availability during AZ impairment" — AWS Well-Architected Framework, Reliability Pillar (REL02-BP01)
- AWS Services: Amazon VPC (Subnets), Elastic Load Balancing, Auto Scaling Groups
- Architecture Decision:
  Create subnets in at minimum 3 Availability Zones per VPC. Each tier (public, private, isolated) should have one subnet per AZ. Route tables should be per-tier, not per-subnet (unless AZ-specific routing is required for NAT). Auto Scaling Groups and ELBs should span all AZs to enable automatic failover.
- Verification:
  ```bash
  aws ec2 describe-subnets --filters "Name=vpc-id,Values=vpc-xxx" \
    --query "Subnets[].{AZ:AvailabilityZone,CIDR:CidrBlock,Public:MapPublicIpOnLaunch}" --output table
  ```
  Verify at least 3 distinct AZs are represented with subnets in each tier.
- Trade-offs: More subnets increase IPAM complexity, require larger VPC CIDR allocations, and consume NAT Gateway costs (one per AZ for HA). Cross-AZ data transfer costs $0.01/GB.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/use-fault-isolation-to-protect-your-workload.html

**VPC CIDR Planning with IPAM**
- Pillar Alignment: Operational Excellence, Reliability
- Why: "IP address overlap prevents VPC connectivity and is irrecoverable without workload migration" — AWS Prescriptive Guidance, Network Architecture
- AWS Services: Amazon VPC IPAM, AWS Organizations, AWS RAM (Resource Access Manager)
- Architecture Decision:
  Allocate non-overlapping CIDR blocks using hierarchical IPAM pools. Top-level pool per Region (e.g., 10.0.0.0/8 for cloud, 172.16.0.0/12 for on-premises). Sub-pools per environment. VPC CIDRs of /16 for production (65,536 IPs), /20 for development (4,096 IPs). Reserve secondary CIDR capability for future growth. Never use 172.31.0.0/16 (default VPC CIDR) for production.
- Verification:
  ```bash
  aws ec2 describe-ipam-pools --query "IpamPools[].{Name:Description,CIDR:PoolId}" --output table
  aws ec2 get-ipam-pool-cidrs --ipam-pool-id ipam-pool-xxx
  ```
- Trade-offs: IPAM adds governance overhead but prevents the catastrophic cost of CIDR overlap remediation. Upfront planning effort vs. future re-architecture cost is asymmetric — always plan first.
- Source: https://docs.aws.amazon.com/vpc/latest/ipam/what-is-it-ipam.html

**Security Groups as Primary Access Control**
- Pillar Alignment: Security
- Why: "Control traffic at all layers using defense in depth. Apply security groups as the primary mechanism for controlling network access to resources" — AWS Well-Architected Framework, Security Pillar (SEC05-BP01)
- AWS Services: VPC Security Groups, Amazon EC2, ELB, RDS, Lambda
- Architecture Decision:
  Create security groups per application role/tier (web-sg, app-sg, db-sg, cache-sg). Reference security groups as sources in rules rather than CIDR blocks where possible (e.g., db-sg allows inbound 5432 from app-sg). Default deny all inbound. Allow only required outbound (avoid 0.0.0.0/0 outbound unless necessary). Never open 0.0.0.0/0 on SSH (22) or RDP (3389) for production.
- Verification:
  ```bash
  aws ec2 describe-security-groups --group-ids sg-xxx \
    --query "SecurityGroups[].IpPermissions[?IpRanges[?CidrIp=='0.0.0.0/0']]"
  ```
  Use AWS Config rule `restricted-ssh` and `restricted-common-ports` for continuous compliance.
- Trade-offs: Security group reference-based rules are more maintainable but create implicit dependencies that complicate teardown. Security groups are limited to 60 rules by default; highly granular rules may require quota increases or prefix lists.
- Source: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html

**VPC Flow Logs for All Production VPCs**
- Pillar Alignment: Security, Operational Excellence
- Why: "Enable logging of network traffic and DNS queries for visibility and incident investigation" — AWS Well-Architected Framework, Security Pillar (SEC04-BP02)
- AWS Services: VPC Flow Logs, Amazon S3, Amazon CloudWatch Logs, Amazon Athena
- Architecture Decision:
  Enable VPC-level flow logs (captures all ENIs in all subnets). Publish to S3 for cost-effective long-term storage and Athena analysis. Optionally publish to CloudWatch Logs for real-time metric filters and alarms (rejected traffic spikes). Use custom log format including: `${version} ${account-id} ${interface-id} ${srcaddr} ${dstaddr} ${srcport} ${dstport} ${protocol} ${packets} ${bytes} ${start} ${end} ${action} ${log-status} ${traffic-path}`.
- Verification:
  ```bash
  aws ec2 describe-flow-logs --filter "Name=resource-id,Values=vpc-xxx" \
    --query "FlowLogs[].{ID:FlowLogId,Status:FlowLogStatus,Dest:LogDestinationType}"
  ```
- Trade-offs: Flow logs generate significant data volume (cost). A busy VPC can produce TB/month of flow log data. Use S3 Intelligent-Tiering for storage, and configure max aggregation interval (10 min) for non-security-critical VPCs to reduce volume.
- Source: https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html

**Gateway Endpoints for S3 and DynamoDB**
- Pillar Alignment: Cost Optimization, Security
- Why: "Use VPC endpoints to access AWS services without requiring NAT or internet gateway — reduces cost and attack surface" — AWS Well-Architected Framework, Cost Optimization Pillar
- AWS Services: VPC Gateway Endpoints, Amazon S3, Amazon DynamoDB
- Architecture Decision:
  Create Gateway Endpoints for S3 and DynamoDB in every VPC that accesses these services. Gateway endpoints are free (no per-hour or per-GB charge). Apply VPC Endpoint Policies to restrict access to specific buckets/tables (defense in depth). Add the endpoint to all route tables in private subnets.
- Verification:
  ```bash
  aws ec2 describe-vpc-endpoints --filters "Name=vpc-id,Values=vpc-xxx" \
    --query "VpcEndpoints[?VpcEndpointType=='Gateway'].{Service:ServiceName,State:State}"
  ```
- Trade-offs: None significant. Gateway endpoints are free and reduce NAT processing costs. The only consideration is that Gateway endpoint routes are propagated to route tables — ensure on-premises routes to S3 (if using Direct Connect public VIF) don't conflict.
- Source: https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints-s3.html

**Private Subnet Default for Workloads**
- Pillar Alignment: Security
- Why: "Place workloads in private subnets by default. Only resources that must receive inbound internet traffic should be in public subnets" — AWS Security Best Practices
- AWS Services: VPC Subnets, NAT Gateway, Application Load Balancer, Network Load Balancer
- Architecture Decision:
  All compute (EC2, ECS, EKS pods, Lambda VPC), databases (RDS, ElastiCache, DynamoDB DAX), and application services deploy in private subnets. Only load balancers, bastion hosts (if required), and NAT gateways reside in public subnets. Use NAT Gateway or VPC endpoints for outbound connectivity from private subnets.
- Verification:
  ```bash
  aws ec2 describe-route-tables --filters "Name=association.subnet-id,Values=subnet-xxx" \
    --query "RouteTables[].Routes[?DestinationCidrBlock=='0.0.0.0/0'].GatewayId"
  ```
  If result contains `igw-*`, the subnet is public. Private subnets should show `nat-*` or no default route.
- Trade-offs: Private subnets require NAT Gateway ($0.045/hr + $0.045/GB) or VPC endpoints for outbound connectivity. IPv6-only architectures with egress-only internet gateways are an emerging cost-optimization alternative.
- Source: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-best-practices.html

**Encryption in Transit via TLS Everywhere**
- Pillar Alignment: Security
- Why: "Enforce encryption in transit to protect data confidentiality and integrity" — AWS Well-Architected Framework, Security Pillar (SEC09-BP02)
- AWS Services: AWS Certificate Manager (ACM), Application Load Balancer (TLS termination), VPC Transit Gateway (encryption control), AWS PrivateLink
- Architecture Decision:
  Terminate TLS at the load balancer (ALB) with ACM-managed certificates. Re-encrypt between ALB and backend instances (end-to-end TLS) for sensitive workloads. Use Transit Gateway encryption control for VPC-to-VPC traffic encryption. All internal service communication should use TLS 1.2+ minimum. Configure security groups to only allow HTTPS (443) for application traffic.
- Verification:
  ```bash
  aws elbv2 describe-listeners --load-balancer-arn arn:aws:elasticloadbalancing:... \
    --query "Listeners[].{Port:Port,Protocol:Protocol,SSLPolicy:SslPolicy}"
  ```
- Trade-offs: TLS adds latency (handshake overhead) and CPU cost. For internal east-west traffic between trusted services in the same VPC, the TLS overhead may be acceptable depending on performance requirements. Transit Gateway encryption control adds ~10% throughput overhead.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-data-in-transit.html

---

### ⚠️ Architectural Decisions

**Network Topology: Hub-Spoke vs Mesh vs Full VPC Peering**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|------------|-----------|------------|-----------|
  | Full Mesh VPC Peering | VPC Peering | Bandwidth (no per-GB charge), Latency | Scalability (n*(n-1)/2 connections) | ≤5 VPCs, high-bandwidth inter-VPC communication |
  | Hub-Spoke via Transit Gateway | AWS Transit Gateway | Scalability, Centralized routing/inspection | Cost ($0.05/hr per attachment + $0.02/GB), Minor latency | >5 VPCs, multi-account, centralized security |
  | AWS Cloud WAN | AWS Cloud WAN | Global policy-based routing, Multi-Region | Complexity, Cost (higher than TGW) | Global multi-Region with automated routing policies |
  | VPC Lattice (Layer 7) | Amazon VPC Lattice | Service-to-service auth, Simplicity | Layer 3/4 connectivity (only HTTP/gRPC) | Microservices needing app-layer routing |

- Cost Profile: VPC Peering = $0/attachment, $0.01/GB cross-AZ only | Transit Gateway = $0.05/hr per attachment + $0.02/GB processed | Cloud WAN = similar to TGW with global management premium
- Lock-in Assessment: All options are AWS-specific. Transit Gateway concepts map to other clouds (Azure Virtual WAN, GCP Network Connectivity Center). VPC Lattice is most AWS-specific.
- Architect Instruction: "Ask whether the architecture requires >10 VPC interconnections, centralized traffic inspection, or cross-Region connectivity before choosing topology"
- Source: https://docs.aws.amazon.com/whitepapers/latest/building-scalable-secure-multi-vpc-network-infrastructure/welcome.html

**NAT Strategy: Per-AZ NAT Gateway vs Regional NAT Gateway vs IPv6-Only**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|------------|-----------|------------|-----------|
  | Per-AZ NAT Gateway | NAT Gateway (Public) | AZ independence, Blast radius | Cost (N × $0.045/hr), Route table complexity | Production workloads needing AZ-level HA |
  | Regional NAT Gateway | NAT Gateway (Regional) | Operational simplicity, Auto multi-AZ | Less control over AZ-specific routing | Production workloads accepting AWS-managed HA |
  | Centralized NAT (Hub VPC) | TGW + NAT Gateway | Cost (fewer NAT GWs) | Single point of failure, Cross-AZ charges | Development/staging environments |
  | IPv6-Only + Egress-Only IGW | Egress-Only Internet Gateway | Cost (free), No NAT needed | Requires IPv6 capability everywhere | Greenfield architectures, modern workloads |

- Cost Profile: Per-AZ NAT = 3 × $32.40/month (us-east-1) + $0.045/GB | Regional = similar total cost, simpler management | Centralized = 1-2 × $32.40/month + TGW costs | IPv6 egress-only = $0
- Scaling Characteristics: NAT Gateway supports 55,000 simultaneous connections per EIP. For high-throughput, assign multiple EIPs (up to 8) per NAT Gateway. Port allocation errors indicate exhaustion.
- Architect Instruction: "Ask the team's IPv6 readiness and whether all downstream dependencies support IPv6 before recommending IPv6-only egress"
- Source: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html

**Hybrid Connectivity: Site-to-Site VPN vs Direct Connect vs Both**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|------------|-----------|------------|-----------|
  | Site-to-Site VPN | AWS VPN | Encryption (IPsec), Quick setup, Cost | Bandwidth consistency (internet-dependent) | Proof of concept, backup connectivity, ≤1 Gbps |
  | Direct Connect (Dedicated) | AWS Direct Connect | Bandwidth (1/10/100 Gbps), Latency consistency | Setup time (weeks-months), Cost, NOT encrypted by default | Production hybrid with consistent latency/throughput needs |
  | Direct Connect + VPN Overlay | Direct Connect + VPN | Encryption + Bandwidth | Complexity, VPN throughput limited to 1.25 Gbps per tunnel | Compliance requiring encryption over dedicated links |
  | Direct Connect with MACsec | Direct Connect + MACsec | Line-rate encryption (Layer 2) | Requires dedicated (not hosted) connection + MACsec-capable router | High-throughput encrypted hybrid (10/100 Gbps) |

- Cost Profile: VPN = $0.05/hr per connection + data transfer | Direct Connect = port-hour ($0.30/hr for 1Gbps) + data transfer (lower than internet rates) | Both = combined
- Lock-in Assessment: Direct Connect involves physical infrastructure at AWS locations (long-term commitment). VPN is portable to any IPsec-compatible cloud.
- Architect Instruction: "Ask about bandwidth requirements, latency SLAs, encryption compliance needs, and acceptable setup timeline before recommending hybrid connectivity"
- Source: https://docs.aws.amazon.com/directconnect/latest/UserGuide/Welcome.html

**Service Connectivity: PrivateLink vs VPC Peering vs Transit Gateway**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|------------|-----------|------------|-----------|
  | AWS PrivateLink | Interface/Resource Endpoints | Security (unidirectional), CIDR overlap tolerance | Cost ($0.01/hr + $0.01/GB), Uni-directional only | Exposing specific services to consumers, SaaS integration |
  | VPC Peering | VPC Peering Connection | Bandwidth, No per-GB charge | CIDR cannot overlap, Non-transitive, Scales poorly | Tight coupling between 2 specific VPCs |
  | Transit Gateway | AWS Transit Gateway | Scalability, Transitive routing | Per-GB charge ($0.02/GB), Slightly higher latency | Many-to-many VPC communication, centralized routing |

- Cost Profile: PrivateLink = $0.01/hr/AZ + $0.01/GB | Peering = $0 (only cross-AZ transfer) | TGW = $0.05/hr/attachment + $0.02/GB
- Lock-in Assessment: All AWS-specific patterns. PrivateLink concept exists in Azure (Private Link) and GCP (Private Service Connect).
- Architect Instruction: "Ask whether communication is bidirectional or unidirectional, whether CIDRs overlap, and how many VPCs need connectivity"
- Source: https://docs.aws.amazon.com/vpc/latest/privatelink/what-is-privatelink.html

**DNS Architecture: Route 53 Resolver vs On-Premises DNS vs Hybrid**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|------------|-----------|------------|-----------|
  | Route 53 Private Hosted Zones | Route 53 | Native AWS integration, Auto registration | On-premises resolution without endpoints | Pure-cloud workloads |
  | Route 53 Resolver Endpoints | Route 53 Resolver (Inbound/Outbound) | Hybrid DNS resolution | Cost ($0.125/hr per endpoint per direction) | Hybrid with on-premises DNS authority |
  | R53 Resolver DNS Firewall | Route 53 Resolver DNS Firewall | DNS-layer security (block malicious domains) | Rule management overhead | All production VPCs (defense-in-depth) |
  | Third-Party DNS (in-VPC) | EC2-hosted DNS (CoreDNS, BIND) | Full control, Multi-cloud | Operational burden, HA management | Multi-cloud with unified DNS namespace |

- Cost Profile: Private Hosted Zones = $0.50/month/zone + $0.40/million queries | Resolver Endpoints = $0.125/hr per ENI (min 2 per direction) | DNS Firewall = $0.0005/query inspected
- Architect Instruction: "Ask whether on-premises systems need to resolve AWS private hostnames, and whether AWS workloads need to resolve on-premises DNS names"
- Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver.html

**Traffic Inspection: Network Firewall vs Third-Party NVA vs Gateway Load Balancer**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|------------|-----------|------------|-----------|
  | AWS Network Firewall | AWS Network Firewall | AWS-native, Managed, Suricata IPS | Feature parity with enterprise firewalls | AWS-only shops needing L3-L7 inspection |
  | Third-Party NVA (via GWLB) | Gateway Load Balancer + EC2 NVA | Feature richness (Palo Alto, Fortinet, Check Point) | Cost, Operational complexity, Licensing | Existing security tool investment, compliance requirements |
  | Network Firewall + GWLB combined | Both services | Layered inspection | Cost (both charged) | Defense-in-depth with specific compliance requirements |
  | Security Groups + NACLs only | VPC native | Simplicity, No per-GB cost | No L7 inspection, No IPS/IDS | Low-risk internal workloads, development environments |

- Cost Profile: Network Firewall = $0.395/hr per endpoint + $0.065/GB | GWLB = $0.0125/hr + $0.004/GB (plus NVA EC2 costs) | SG+NACL = $0
- Architect Instruction: "Ask about compliance requirements (PCI-DSS, HIPAA), existing security tooling investments, and whether Layer 7 inspection is mandated"
- Source: https://docs.aws.amazon.com/network-firewall/latest/developerguide/what-is-aws-network-firewall.html

---

### 🚫 Anti-Patterns

**Single-AZ Deployment for Production Stateful Workloads**
- Risk Level: CRITICAL
- Why: Violates Reliability Pillar (REL02) — "Use multiple Availability Zones to maintain availability during AZ-level failures." Single-AZ eliminates the fundamental redundancy that makes cloud architectures resilient.
- Instead:
  Deploy across minimum 3 AZs. Use Multi-AZ RDS, ElastiCache with multi-AZ replication, EFS (inherently multi-AZ). For compute, use Auto Scaling Groups spanning all AZs with health checks.
- Detection:
  ```bash
  aws ec2 describe-subnets --filters "Name=vpc-id,Values=vpc-xxx" \
    --query "Subnets[].AvailabilityZone" | sort | uniq -c
  ```
  AWS Config rule: `multi-az-rds-check`, custom Config rule for EC2/ASG AZ distribution.
- Impact: Complete service outage during AZ failure (AZ failures occur multiple times per year across Regions). Data loss if backups are also single-AZ.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/use-fault-isolation-to-protect-your-workload.html

**Overly Permissive Security Groups (0.0.0.0/0 on Management Ports)**
- Risk Level: CRITICAL
- Why: Violates Security Pillar (SEC05) — "Control traffic at all layers." Unrestricted SSH (22) or RDP (3389) inbound from 0.0.0.0/0 exposes instances to brute-force attacks and exploitation of management protocol vulnerabilities.
- Instead:
  Use AWS Systems Manager Session Manager for shell access (no open ports needed). If SSH is required, restrict to corporate CIDR ranges or use EC2 Instance Connect (temporary SSH keys). For RDP, use AWS Fleet Manager or restrict to VPN CIDR. NEVER allow 0.0.0.0/0 on ports 22, 3389, or any management port.
- Detection:
  ```bash
  aws ec2 describe-security-groups \
    --query "SecurityGroups[].IpPermissions[?contains(IpRanges[].CidrIp, '0.0.0.0/0') && (FromPort==`22` || FromPort==`3389`)]"
  ```
  AWS Config rules: `restricted-ssh`, `restricted-common-ports`. Security Hub: `EC2.13`, `EC2.14`.
- Impact: Unauthorized access, credential compromise, lateral movement, data exfiltration, cryptomining, ransomware deployment.
- Source: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-best-practices.html

**Overlapping CIDR Blocks Between Connected VPCs**
- Risk Level: CRITICAL
- Why: Violates Operational Excellence and Reliability — overlapping CIDRs prevent VPC peering, Transit Gateway routing, and Direct Connect connectivity. Once deployed, remediation requires workload migration (re-IP).
- Instead:
  Use Amazon VPC IPAM to allocate non-overlapping CIDRs from a centrally managed pool. Define a supernet per Region/environment. For unavoidable overlaps (mergers, acquisitions), use AWS PrivateLink (does not require CIDR uniqueness) or private NAT Gateways for address translation.
- Detection:
  ```bash
  aws ec2 describe-vpcs --query "Vpcs[].CidrBlockAssociationSet[].CidrBlock" --output text | sort
  ```
  IPAM provides built-in overlap detection across the organization.
- Impact: Inability to connect VPCs, broken hybrid connectivity, routing black holes, forced migration of production workloads.
- Source: https://docs.aws.amazon.com/whitepapers/latest/building-scalable-secure-multi-vpc-network-infrastructure/ip-address-planning-and-management.html

**Routing All Traffic Through NAT Gateway (Including AWS Service Traffic)**
- Risk Level: HIGH
- Why: Violates Cost Optimization Pillar — NAT Gateway charges $0.045/GB processed. S3 and DynamoDB Gateway Endpoints are free. Interface Endpoints for other services cost $0.01/GB (less than half NAT cost). Routing AWS service traffic through NAT wastes money and adds unnecessary internet dependency.
- Instead:
  Deploy Gateway Endpoints for S3 and DynamoDB in every VPC (free). Deploy Interface Endpoints for frequently-used AWS services (CloudWatch, STS, ECR, KMS, Secrets Manager). Only route genuinely internet-bound traffic through NAT Gateway.
- Detection:
  ```bash
  # Check for missing S3 gateway endpoint
  aws ec2 describe-vpc-endpoints --filters "Name=vpc-id,Values=vpc-xxx" "Name=service-name,Values=com.amazonaws.*.s3" \
    --query "VpcEndpoints[?VpcEndpointType=='Gateway']"
  ```
  If empty result for production VPCs, this anti-pattern is present.
- Impact: Excessive NAT Gateway costs (can be thousands/month for data-intensive workloads), unnecessary internet path dependency for AWS API calls, potential NAT Gateway throttling under load.
- Source: https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints-s3.html

**Using Default VPC for Production Workloads**
- Risk Level: HIGH
- Why: Violates Security Pillar and Operational Excellence — default VPCs have public subnets with auto-assign public IP enabled, permissive default security groups (allow all inbound from same group), and cannot be managed with IPAM or proper CIDR planning. The default VPC CIDR (172.31.0.0/16) is identical in every account, preventing peering.
- Instead:
  Create purpose-built VPCs with planned CIDR blocks, explicit subnet types (public/private/isolated), custom route tables, and restrictive default security groups. Delete or disable default VPCs in production accounts (after ensuring no dependencies).
- Detection:
  ```bash
  aws ec2 describe-vpcs --filters "Name=is-default,Values=true" \
    --query "Vpcs[].{VpcId:VpcId,CIDR:CidrBlock}"
  aws ec2 describe-instances --filters "Name=vpc-id,Values=vpc-xxx" \
    --query "Reservations[].Instances[].InstanceId"
  ```
  If instances exist in the default VPC, this anti-pattern is present.
- Impact: Unintended public exposure of resources, inability to peer VPCs (CIDR overlap with other accounts' default VPCs), inability to implement proper network segmentation, compliance failures.
- Source: https://docs.aws.amazon.com/vpc/latest/userguide/default-vpc.html

**No VPC Flow Logs Enabled**
- Risk Level: HIGH
- Why: Violates Security Pillar (SEC04) — "Record network activity for detection and investigation." Without flow logs, security incidents cannot be investigated, lateral movement cannot be detected, and compliance audits fail.
- Instead:
  Enable VPC-level flow logs for all production VPCs. Publish to S3 in a centralized security account for cross-account analysis. Set retention policies appropriate for compliance requirements (minimum 90 days, typically 1 year for regulated industries).
- Detection:
  ```bash
  # List VPCs without flow logs
  for vpc in $(aws ec2 describe-vpcs --query "Vpcs[].VpcId" --output text); do
    logs=$(aws ec2 describe-flow-logs --filter "Name=resource-id,Values=$vpc" --query "FlowLogs[].FlowLogId" --output text)
    [[ -z "$logs" ]] && echo "NO FLOW LOGS: $vpc"
  done
  ```
  AWS Config rule: `vpc-flow-logs-enabled`.
- Impact: Blind spot for security monitoring, inability to perform forensic investigation during incidents, compliance violations (PCI-DSS 10.x, SOC2 CC7.x).
- Source: https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html

**Direct Internet Egress from Private Subnets Without NAT Gateway**
- Risk Level: HIGH
- Why: Violates Security Pillar — placing an Internet Gateway route in what should be a private subnet route table turns private instances into publicly-addressable resources (if they have public IPs). This eliminates the network boundary that private subnets provide.
- Instead:
  Private subnet route tables should NEVER have a route to an Internet Gateway. Use NAT Gateway (for internet-bound traffic) or VPC Endpoints (for AWS service traffic). If internet egress is needed, route through NAT Gateway in a public subnet.
- Detection:
  ```bash
  aws ec2 describe-route-tables --filters "Name=association.subnet-id,Values=subnet-private-xxx" \
    --query "RouteTables[].Routes[?GatewayId!=null && starts_with(GatewayId,'igw-')]"
  ```
  Non-empty result on a subnet intended to be private indicates misconfiguration.
- Impact: Unintended public exposure, compliance violations, data exfiltration risk, loss of network boundary isolation.
- Source: https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Internet_Gateway.html

**Monolithic VPC Without Network Segmentation**
- Risk Level: MEDIUM
- Why: Violates Security Pillar (SEC05) — "Control traffic at all layers." A single flat VPC without subnet tiers or security group segmentation allows unrestricted lateral movement after initial compromise.
- Instead:
  Implement at minimum 3 subnet tiers: public (load balancers), private (application), isolated (databases). Use security groups to restrict inter-tier communication to only required ports/protocols. Consider separate VPCs per workload/team with Transit Gateway connectivity for strong isolation.
- Detection:
  Review subnet count and route table diversity per VPC. A VPC with only one subnet type (all public or all using same route table) indicates missing segmentation.
- Impact: Lateral movement after compromise, blast radius covers entire environment, inability to apply principle of least privilege at network layer.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-networks.html

---

## Cloud-Native Design Patterns

**Hub-and-Spoke Network Architecture**
- Category: Scalability | Communication
- Problem: Multi-account organizations need VPC interconnection that scales beyond full-mesh peering while providing centralized security inspection and shared services access.
- Solution on AWS:
  Deploy a Transit Gateway as the central hub. Attach spoke VPCs (workload accounts) via TGW attachments. Create a shared services VPC (DNS, Active Directory, CI/CD) attached to TGW. Create an inspection VPC with AWS Network Firewall for centralized egress/ingress inspection. Use TGW route tables for segmentation (production route table, development route table, shared services route table).
- Services Used: AWS Transit Gateway (hub router), Amazon VPC (spokes), AWS Network Firewall (inspection), AWS RAM (share TGW across accounts), Route 53 Resolver (DNS forwarding)
- When to Apply: Multi-account environments with >5 VPCs, centralized security requirements, shared services that must be accessible from all workload VPCs.
- When NOT to Apply: Single-VPC architectures, applications that can use VPC Lattice for service connectivity (simpler), or when per-GB TGW costs are prohibitive for very high-bandwidth internal traffic.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Scalability | 5,000 attachments per TGW, centralized routing | Each attachment costs $0.05/hr + $0.02/GB |
  | Security | Single inspection point for all traffic | Inspection VPC becomes a critical path — must be HA |
  | Operational | Centralized route management | Route table complexity grows with segmentation needs |
  | Latency | Additional hop through TGW | ~microseconds added (negligible for most workloads) |

- Complements: Centralized Egress Pattern, Shared Services Pattern, DNS Forwarding Pattern
- Source: https://docs.aws.amazon.com/whitepapers/latest/building-scalable-secure-multi-vpc-network-infrastructure/transit-gateway.html

**Centralized Egress with Inspection**
- Category: Security | Communication
- Problem: Each VPC independently managing internet egress (with its own NAT Gateways) creates inconsistent security posture, prevents centralized traffic inspection, and increases NAT Gateway costs.
- Solution on AWS:
  Create a dedicated egress/inspection VPC with NAT Gateways and AWS Network Firewall (or third-party NVAs via Gateway Load Balancer). Route all spoke VPC internet-bound traffic through Transit Gateway to the inspection VPC. Network Firewall inspects traffic (domain filtering, IPS rules) before it reaches NAT Gateway and Internet Gateway. Return traffic flows back through the same path.
- Services Used: AWS Transit Gateway, AWS Network Firewall, NAT Gateway, Internet Gateway, VPC Route Tables
- When to Apply: Organizations requiring centralized egress filtering (domain allow-lists), compliance mandates for traffic inspection, or multi-account environments wanting consistent egress security policy.
- When NOT to Apply: Single-VPC architectures, latency-sensitive workloads where the additional hop is unacceptable, or development environments where inspection overhead is unnecessary.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Security | All egress inspected, domain filtering, IPS | Single point of inspection becomes critical path |
  | Cost | Fewer NAT Gateways (centralized) | Network Firewall + TGW per-GB charges add up |
  | Complexity | Consistent egress policy across all VPCs | Complex route table engineering required |
  | Availability | Must be multi-AZ in inspection VPC | Inspection VPC failure blocks all egress |

- Complements: Hub-and-Spoke Pattern, DNS Firewall Pattern, VPC Endpoint Pattern (reduces egress volume)
- Source: https://docs.aws.amazon.com/network-firewall/latest/developerguide/arch-igw-ngw.html

**VPC Endpoint Strategy (Service Access Without Internet)**
- Category: Security | Cost Optimization
- Problem: Private subnet workloads accessing AWS services (S3, ECR, KMS, CloudWatch, STS) via NAT Gateway incur per-GB NAT processing charges, introduce internet path dependency, and expand attack surface.
- Solution on AWS:
  Deploy Gateway Endpoints for S3 and DynamoDB (free, route-table-based). Deploy Interface Endpoints (PrivateLink) for frequently-used services: ECR (ecr.api + ecr.dkr), CloudWatch Logs, CloudWatch Monitoring, STS, KMS, Secrets Manager, SSM, EC2 Messages. Apply VPC Endpoint Policies to restrict access to authorized resources only. Enable Private DNS for transparent endpoint resolution.
- Services Used: VPC Gateway Endpoints (S3, DynamoDB), VPC Interface Endpoints (AWS PrivateLink), VPC Endpoint Policies
- When to Apply: All production VPCs. Any workload in private subnets that calls AWS APIs. EKS clusters (pull images from ECR without NAT). Lambda functions in VPC (reduce cold start by avoiding NAT path).
- When NOT to Apply: Development environments with minimal traffic where NAT cost is negligible. Ephemeral workloads where endpoint setup cost (time) outweighs NAT savings.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Cost | Eliminates NAT per-GB charges for AWS traffic | Interface Endpoints cost $0.01/hr/AZ (~$7.20/month per endpoint per AZ) |
  | Security | Traffic stays within AWS network, never touches internet | More endpoints to manage and secure |
  | Reliability | Removes internet dependency for AWS API calls | Endpoint ENI availability (multi-AZ deployment recommended) |

- Complements: Private Subnet Default Pattern, Centralized Egress Pattern, Zero-Trust Network Pattern
- Source: https://docs.aws.amazon.com/vpc/latest/privatelink/privatelink-access-aws-services.html

**Multi-Account Landing Zone Network**
- Category: Scalability | Security
- Problem: Growing organizations need a scalable, secure network foundation across dozens or hundreds of AWS accounts with consistent connectivity, DNS resolution, and security controls.
- Solution on AWS:
  Deploy AWS Control Tower for organizational governance. Create a Network account (in Infrastructure OU) that owns the Transit Gateway, shared network resources, and centralized inspection. Use AWS RAM to share Transit Gateway across organization. Define VPC CIDR allocations via IPAM (delegated to Network account). Create shared services VPC for DNS resolvers, AD connectors, and common tools. Use Service Control Policies (SCPs) to prevent creation of Internet Gateways in workload accounts.
- Services Used: AWS Organizations, AWS Control Tower, AWS Transit Gateway, AWS RAM, Amazon VPC IPAM, Route 53 Resolver, AWS Network Firewall, Service Control Policies
- When to Apply: Any organization with >3 AWS accounts, regulatory compliance requirements, or multiple development teams requiring network isolation with controlled connectivity.
- When NOT to Apply: Single-account startups, proof-of-concept environments, or teams without dedicated network/platform engineering capacity.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Governance | Centralized network control, consistent policies | Platform team required to manage network account |
  | Scalability | New accounts automatically connected via TGW | IPAM + TGW attachment automation required |
  | Security | Prevent workload teams from creating internet access | May slow down developer velocity (need to request connectivity) |
  | Cost | Shared Transit Gateway is cost-effective | Network account infrastructure has fixed overhead |

- Complements: Hub-and-Spoke Pattern, Centralized Egress Pattern, IPAM Pattern
- Source: https://docs.aws.amazon.com/whitepapers/latest/building-scalable-secure-multi-vpc-network-infrastructure/welcome.html

**Private Service Exposure via PrivateLink**
- Category: Communication | Security
- Problem: Internal platform services need to be consumed by workloads in other VPCs/accounts without exposing them to the internet, requiring VPC peering (CIDR constraints), or opening overly broad security groups.
- Solution on AWS:
  Create a VPC Endpoint Service backed by a Network Load Balancer (NLB) in the provider VPC. Consumers create Interface VPC Endpoints in their VPCs to access the service. Traffic flows over PrivateLink (AWS backbone) without traversing the internet. Provider controls which accounts can create endpoints (allowlist). Consumer only sees a private IP (ENI) in their subnet — no routing changes needed.
- Services Used: AWS PrivateLink (VPC Endpoint Service), Network Load Balancer, VPC Interface Endpoints
- When to Apply: B2B SaaS service exposure, shared platform services (API gateways, ML inference, data services), inter-account service consumption where VPC peering is impractical (CIDR overlaps or scale).
- When NOT to Apply: Services that require bidirectional communication (PrivateLink is consumer-initiated only). High-bandwidth services where $0.01/GB PrivateLink cost exceeds VPC peering (free) economics.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Security | Unidirectional, no CIDR exposure, endpoint policies | More complex than VPC peering for simple use cases |
  | CIDR Flexibility | Works with overlapping CIDRs | N/A — this is purely beneficial |
  | Scalability | Supports thousands of consumers per service | NLB must handle all consumer traffic |
  | Cost | No TGW attachment needed | $0.01/hr/AZ + $0.01/GB |

- Complements: Service Mesh Pattern, API Gateway Pattern, Zero-Trust Pattern
- Source: https://docs.aws.amazon.com/vpc/latest/privatelink/privatelink-share-your-services.html

**Resilient Hybrid Connectivity**
- Category: Resilience | Communication
- Problem: Single hybrid connection (one VPN or one Direct Connect) creates a single point of failure for on-premises-to-cloud communication.
- Solution on AWS:
  Deploy two Direct Connect connections from different Direct Connect locations (or different routers in the same location). Configure BGP with appropriate AS-path prepending for active/passive or ECMP for active/active. Add Site-to-Site VPN over the internet as tertiary failover (lower bandwidth but diverse path). Terminate connections on Transit Gateway for centralized routing. Monitor via CloudWatch metrics on Direct Connect and VPN tunnels.
- Services Used: AWS Direct Connect (2+ connections), AWS Site-to-Site VPN (backup), AWS Transit Gateway (termination point), CloudWatch (monitoring), Route 53 Health Checks
- When to Apply: Production hybrid architectures where on-premises connectivity is business-critical. Any workload with RTO < 1 hour for hybrid communication.
- When NOT to Apply: Development environments, fully cloud-native architectures with no on-premises dependencies.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Availability | Survives single connection failure | 2× Direct Connect port costs |
  | Bandwidth | Active/active doubles available bandwidth | 2× data transfer costs if both active |
  | Complexity | Automated failover via BGP | BGP tuning, route preference management |
  | Diverse Routing | VPN backup provides internet-diverse path | VPN limited to 1.25 Gbps per tunnel |

- Complements: Hub-and-Spoke Pattern, DNS Forwarding Pattern, Zero-Trust Pattern
- Source: https://docs.aws.amazon.com/directconnect/latest/UserGuide/getting_started.html

---

## Security Architecture

**Network Segmentation and Defense-in-Depth**
- AWS Services: VPC Subnets, Security Groups, Network ACLs, AWS Network Firewall, VPC Flow Logs, AWS WAF, AWS Shield
- Architecture:
  Layer 1 (Perimeter): AWS WAF + Shield on ALB/CloudFront for L7/DDoS protection.
  Layer 2 (Subnet boundary): NACLs with deny rules for known-bad CIDRs and restricted ephemeral ports.
  Layer 3 (Instance boundary): Security groups with principle of least privilege — only required ports from required sources.
  Layer 4 (East-West): Network Firewall for inter-VPC traffic inspection via Transit Gateway.
  Layer 5 (Data plane): VPC Flow Logs + GuardDuty for detection and response.
  Each layer operates independently — compromise of one layer is contained by the next.
- Configuration Essentials:
  - Security groups: Reference other SGs as sources (not CIDRs) for service-tier rules
  - NACLs: Rule 100-level increments, deny before allow, explicit ephemeral port allowance
  - Network Firewall: Stateful rules with Suricata syntax, domain allow-lists for egress
  - WAF: OWASP Top 10 managed rules, rate limiting, geo-blocking
- Verification:
  ```bash
  # Check for overly permissive security groups
  aws ec2 describe-security-groups --query "SecurityGroups[?IpPermissions[?IpRanges[?CidrIp=='0.0.0.0/0']]]" --output table
  # Verify Network Firewall is deployed and logging
  aws network-firewall describe-firewall --firewall-name xxx --query "Firewall.FirewallStatus.Status"
  ```
  Use AWS Security Hub with CIS AWS Foundations Benchmark for continuous compliance monitoring.
- Compliance Alignment: PCI-DSS Requirement 1 (Install and maintain a firewall), SOC2 CC6.1 (Logical access security), HIPAA §164.312(e) (Transmission security)
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-networks.html

**Zero-Trust Network Architecture**
- AWS Services: VPC Lattice (service-to-service auth), AWS Verified Access (user-to-app without VPN), IAM (identity-based access), Security Groups (micro-segmentation), AWS PrivateLink (private connectivity), AWS Certificate Manager (mTLS)
- Architecture:
  Eliminate implicit trust based on network location. Every service-to-service call authenticated via IAM (SigV4) or mTLS. VPC Lattice auth policies define which services can communicate (regardless of VPC boundary). AWS Verified Access provides identity-aware application access without VPN (replaces traditional VPN for user access). PrivateLink ensures traffic never traverses public internet. Security groups restrict to minimum required connectivity even within the same subnet.
- Configuration Essentials:
  - VPC Lattice: Define service networks with IAM auth policies per target group
  - Verified Access: Configure trust provider (IAM Identity Center, Okta, etc.) and access policies
  - Security Groups: Deny all inbound by default, allow only from specific SGs
  - PrivateLink: VPC Endpoint Policies restrict to specific actions/resources
- Verification:
  Test that services cannot communicate without proper authentication. Attempt cross-service calls without credentials — should fail. Verify VPC Lattice auth policy denies unauthorized callers.
- Compliance Alignment: NIST SP 800-207 (Zero Trust Architecture), PCI-DSS 4.0 Requirement 1.2 (Network security controls)
- Source: https://docs.aws.amazon.com/vpc-lattice/latest/ug/what-is-vpc-lattice.html

**VPC Block Public Access (Account-Level)**
- AWS Services: VPC Block Public Access, AWS Organizations (SCPs), Internet Gateway, NAT Gateway
- Architecture:
  Enable VPC Block Public Access at the account level to prevent any VPC from routing traffic to/from the internet via Internet Gateways. Create explicit exclusions only for designated public-facing VPCs (e.g., the edge/DMZ VPC hosting public load balancers). Combine with SCPs that prevent IAM users from disabling BPA. This creates an account-level "no internet by default" posture that must be explicitly overridden.
- Configuration Essentials:
  - Enable BPA at account level via VPC console or API
  - Define exclusion list for VPCs that require internet gateway routing
  - SCP: Deny `ec2:ModifyVpcBlockPublicAccessOptions` except from network admin role
  - Monitor: CloudTrail events for BPA modification attempts
- Verification:
  ```bash
  aws ec2 describe-vpc-block-public-access-options \
    --query "VpcBlockPublicAccessOptions.{State:InternetGatewayBlockMode}"
  ```
- Compliance Alignment: CIS AWS Foundations Benchmark, SOC2 CC6.6 (System boundaries), any framework requiring network perimeter controls
- Source: https://docs.aws.amazon.com/vpc/latest/userguide/security-vpc-bpa.html

---

## Operational Patterns

**Network Observability Stack**
- AWS Services: VPC Flow Logs (network metadata), CloudWatch Metrics (NAT GW, TGW metrics), AWS Network Manager (topology visualization), Reachability Analyzer (connectivity testing), Network Access Analyzer (unintended access detection), Traffic Mirroring (packet capture)
- Cost Profile: Medium — Flow logs to S3 ($0.50/GB ingestion + storage), CloudWatch ($0.30/GB ingestion), Network Manager (included with TGW/Cloud WAN). Optimize with S3 Intelligent-Tiering and CloudWatch log class selection.
- Architecture:
  Publish VPC Flow Logs to centralized S3 bucket (security account) for Athena analysis. Create CloudWatch metric filters for rejected traffic spikes. Monitor NAT Gateway metrics (ErrorPortAllocation, PacketsDropCount, BytesOutToDestination). Use Reachability Analyzer for proactive connectivity validation after changes. Deploy Traffic Mirroring (to ENI or NLB) for deep packet inspection during incident investigation.
- Automation:
  - Auto-enable flow logs on new VPCs via AWS Config auto-remediation
  - CloudWatch Alarms on NAT GW port allocation errors → SNS → PagerDuty
  - Reachability Analyzer scheduled runs after Terraform/CloudFormation deploys
  - Network Access Analyzer periodic scans → Security Hub findings
- Runbook Skeleton:
  1. **Detection**: CloudWatch alarm triggers on rejected traffic spike or NAT GW error
  2. **Triage**: Query flow logs in Athena for source/destination/port patterns
  3. **Diagnosis**: Use Reachability Analyzer to identify routing or security group blocks
  4. **Resolution**: Apply security group/NACL/route table fix, verify with Reachability Analyzer
  5. **Post-mortem**: Document root cause, update automation/alerting
- Source: https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html

**High Availability Network Architecture**
- RTO/RPO: Seconds (multi-AZ) | Minutes (multi-Region)
- AWS Services: Multi-AZ Subnets, NAT Gateway (one per AZ or Regional), Elastic Load Balancing (cross-zone), Transit Gateway (multi-AZ attachments), Direct Connect (redundant connections), Route 53 (DNS failover)
- Cost Profile: Medium-High — multi-AZ NAT Gateways (3× cost), redundant Direct Connect (2× port costs), cross-AZ data transfer ($0.01/GB)
- Architecture:
  Deploy subnets in 3+ AZs. NAT Gateways in each AZ (or Regional NAT Gateway). ELB cross-zone load balancing enabled. Transit Gateway attachments in all AZs (subnet per AZ). Direct Connect with redundant connections from diverse locations. Route 53 health checks with failover routing for multi-Region active-passive. Auto-healing via Auto Scaling Group health checks replacing unhealthy instances.
- Automation:
  - Auto Scaling Groups with ELB health checks (automatic instance replacement)
  - Route 53 health checks → automatic DNS failover to secondary Region
  - Direct Connect BGP failover (automatic via routing protocol)
  - CloudWatch Composite Alarms for multi-signal failure detection
- Runbook Skeleton:
  1. **Detection**: CloudWatch alarm, Route 53 health check failure, or ELB unhealthy targets
  2. **Triage**: Identify scope — single instance, AZ-wide, or Region-wide
  3. **Automated Response**: ASG replaces instances, Route 53 fails over DNS, BGP reroutes Direct Connect
  4. **Manual Escalation**: If automated recovery fails within 5 minutes, engage on-call
  5. **Recovery Validation**: Confirm service restoration, verify data consistency
- Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/plan-for-disaster-recovery-dr.html

**Network Cost Optimization (FinOps)**
- AWS Services: VPC IPAM (IP planning), Gateway Endpoints (free S3/DynamoDB access), IPv6 (avoid public IPv4 charges), NAT Gateway metrics, Cost Explorer, VPC Flow Logs (traffic analysis)
- Cost Profile: Focus areas: Public IPv4 ($3.60/instance/month as of 2024), NAT Gateway ($32.40/month + $0.045/GB), Transit Gateway ($0.02/GB), Cross-AZ data transfer ($0.01/GB), Interface Endpoints ($7.20/month/AZ)
- Architecture:
  1. Eliminate unnecessary public IPv4 addresses (use IPv6 where possible, private endpoints)
  2. Deploy Gateway Endpoints for S3/DynamoDB (eliminates NAT costs for these services)
  3. Monitor NAT Gateway per-GB usage — move high-volume AWS API traffic to Interface Endpoints
  4. Evaluate cross-AZ data transfer — co-locate communicating services in same AZ where HA permits
  5. Right-size VPC endpoints — don't deploy endpoints in AZs without consumer traffic
  6. Use VPC Flow Logs + Athena to identify top traffic flows and optimize accordingly
- Automation:
  - AWS Budgets alert on NAT Gateway spending exceeding threshold
  - Cost Explorer anomaly detection for network services
  - Monthly review of cross-AZ data transfer by service (CUR report)
- Runbook Skeleton:
  1. **Monthly Review**: Pull Cost Explorer data for VPC, NAT Gateway, Data Transfer line items
  2. **Flow Analysis**: Query VPC Flow Logs for top-N byte-volume flows
  3. **Optimize**: Deploy endpoints for high-volume AWS service traffic, consolidate NAT where safe
  4. **IPv6 Migration**: Identify workloads that can drop public IPv4 (save $3.60/month each)
  5. **Track**: Compare month-over-month network costs, validate savings
- Source: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/cost-effective-resources.html

---

## Reference Architectures

**Three-Tier Web Application Network Architecture**
- Context: Classic web application with public-facing load balancer, application tier, and database tier requiring internet-facing entry point with defense-in-depth.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Edge | CloudFront + AWS WAF + Shield | DDoS protection, L7 filtering, caching |
  | Public Subnet | Application Load Balancer | TLS termination, request routing |
  | Private Subnet (App) | ECS/EKS/EC2 + Auto Scaling | Application compute |
  | Private Subnet (Data) | RDS Multi-AZ + ElastiCache | Persistent storage + caching |
  | Network Security | Security Groups (per-tier) + NACLs | Traffic isolation between tiers |
  | Outbound | NAT Gateway + Gateway Endpoints (S3) | Internet egress + AWS service access |

- Key Decisions: Whether to use ALB vs NLB (HTTP routing vs TCP passthrough), whether to add Network Firewall for egress inspection, NAT per-AZ vs Regional.
- Scaling Path: Add more AZs → Add auto-scaling for NAT throughput → Move to Transit Gateway when additional VPCs needed → Add CloudFront for global distribution.
- Cost Baseline: ~$200-500/month for networking components (ALB $20 + NAT 3×$32 + cross-AZ transfer)
- Source: https://docs.aws.amazon.com/architecture/

**Multi-Account Hub-and-Spoke Network**
- Context: Enterprise with 20+ AWS accounts requiring centralized connectivity, DNS resolution, egress inspection, and shared services.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Governance | AWS Organizations + Control Tower | Account structure, SCPs |
  | Connectivity Hub | Transit Gateway (shared via RAM) | Central routing between all VPCs |
  | IP Management | VPC IPAM | Non-overlapping CIDR allocation |
  | Shared Services VPC | Route 53 Resolver + AD Connector | DNS + directory services |
  | Inspection VPC | Network Firewall + NAT Gateway + IGW | Centralized egress + inspection |
  | Workload VPCs (Spokes) | Private subnets only, TGW attachment | Application hosting |
  | Hybrid | Direct Connect + VPN (backup) → TGW | On-premises connectivity |
  | DNS | Route 53 Resolver Rules (shared via RAM) | Hybrid DNS resolution |

- Key Decisions: TGW route table segmentation strategy (production vs non-production), whether to centralize NAT or distribute per-spoke, Direct Connect placement (network account vs dedicated DX account).
- Scaling Path: Add spoke VPCs via automation → Add Regions with TGW inter-Region peering → Graduate to AWS Cloud WAN for global policy-based routing → Add VPC Lattice for service mesh.
- Cost Baseline: ~$1,500-5,000/month for core network infrastructure (TGW attachments + Network Firewall + NAT + Direct Connect port)
- Source: https://docs.aws.amazon.com/whitepapers/latest/building-scalable-secure-multi-vpc-network-infrastructure/welcome.html

**Serverless Application Network Architecture**
- Context: Event-driven serverless application using Lambda, API Gateway, DynamoDB, and SQS requiring minimal network management with secure AWS service access.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | API Entry | API Gateway (Regional/Edge) | Request routing, auth, throttling |
  | Compute | Lambda (VPC-connected if needed) | Application logic |
  | Data | DynamoDB + S3 | Storage (no VPC required) |
  | Messaging | SQS + EventBridge | Async communication |
  | VPC (if needed) | Private subnets + VPC Endpoints | RDS access, ENI-based services |
  | Security | IAM execution roles + Resource policies | Fine-grained access control |

- Key Decisions: Whether Lambda needs VPC connectivity (only if accessing VPC resources like RDS). If VPC-connected, deploy Interface Endpoints for AWS services to avoid NAT dependency and cold start penalty. Use Hyperplane ENI (shared across Lambda functions) to reduce IP consumption.
- Scaling Path: Start without VPC → Add VPC connectivity when RDS/ElastiCache needed → Deploy endpoints to eliminate NAT dependency → Add VPC Lattice if service-to-service auth needed.
- Cost Baseline: ~$10-50/month for networking (Gateway Endpoints free, Interface Endpoints $7.20/AZ/month if VPC-connected)
- Source: https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html

---

## Service Equivalence Map

| Category | AWS | Google Cloud | Azure | Oracle Cloud (OCI) |
|----------|-----|-------------|-------|--------------------|
| **Virtual Network** | VPC | VPC (global) | VNet | VCN |
| **Subnet** | Subnet (AZ-scoped) | Subnet (Regional) | Subnet (VNet-scoped) | Subnet (AD-scoped) |
| **Internet Gateway** | Internet Gateway | Cloud NAT / Default route | Internet routing | Internet Gateway |
| **NAT** | NAT Gateway | Cloud NAT | NAT Gateway | NAT Gateway |
| **Firewall (L3-L7)** | AWS Network Firewall | Cloud Firewall (Next-Gen) | Azure Firewall | OCI Network Firewall |
| **Security Groups** | Security Groups (stateful) | Firewall Rules (stateful) | NSGs (stateful) | Security Lists / NSGs |
| **Network ACLs** | NACLs (stateless, subnet) | Firewall Rules (priority) | NSG rules | Security Lists (subnet) |
| **Transit Hub** | Transit Gateway | Network Connectivity Center | Virtual WAN / vHub | DRG (Dynamic Routing Gateway) |
| **VPC Peering** | VPC Peering | VPC Peering (global) | VNet Peering (global) | Local/Remote Peering |
| **Private Link** | AWS PrivateLink | Private Service Connect | Azure Private Link | OCI Private Endpoint |
| **VPN** | Site-to-Site VPN | Cloud VPN | VPN Gateway | IPSec VPN |
| **Dedicated Connect** | Direct Connect | Cloud Interconnect | ExpressRoute | FastConnect |
| **Load Balancer (L7)** | ALB | Global HTTP(S) LB | Application Gateway | Load Balancer (L7) |
| **Load Balancer (L4)** | NLB | TCP/UDP LB | Azure Load Balancer | Network Load Balancer |
| **DNS** | Route 53 | Cloud DNS | Azure DNS | OCI DNS |
| **Flow Logs** | VPC Flow Logs | VPC Flow Logs | NSG Flow Logs | VCN Flow Logs |
| **DDoS Protection** | AWS Shield | Cloud Armor | DDoS Protection | OCI WAF / DDoS |
| **WAF** | AWS WAF | Cloud Armor | Azure WAF | OCI WAF |
| **Service Mesh (L7)** | VPC Lattice | Traffic Director | — | — |
| **Global Network Mgmt** | AWS Cloud WAN | Network Connectivity Center | Virtual WAN | — |
| **IP Management** | VPC IPAM | — (manual) | IPAM (preview) | — (manual) |

> **⚠️ Important**: Service equivalence does NOT mean feature parity. AWS VPC subnets are AZ-scoped (GCP subnets are regional). AWS NACLs are subnet-level stateless firewalls (no direct GCP equivalent). AWS Transit Gateway is regional (Azure Virtual WAN is global). Always validate against provider-specific documentation.

---

## Provider Differentiators

**AWS Transit Gateway with Encryption Control**
- Category: Network Security
- Unique Value: Enforces encryption-in-transit for ALL traffic between VPCs attached to the Transit Gateway at the network layer — without application-level TLS configuration. Ensures VPC attachments must have encryption control enabled, preventing unencrypted east-west traffic.
- Architecture Impact: Provides a single enforcement point for in-transit encryption across all connected VPCs. Eliminates the need to trust that every application correctly implements TLS for internal communication.
- When to Leverage: Compliance-driven environments (HIPAA, PCI-DSS) requiring provable encryption of all network traffic, even between internal services.
- Caveat: Slight throughput overhead (~10%). Only for VPC attachments (not VPN which is already encrypted). Requires all attached VPCs to opt-in to encryption control.
- Source: https://docs.aws.amazon.com/vpc/latest/tgw/what-is-transit-gateway.html

**Amazon VPC Lattice**
- Category: Application Networking
- Unique Value: Layer 7 service-to-service networking that operates across VPC boundaries without requiring VPC peering, Transit Gateway, or sidecar proxies. Provides IAM-based service authentication, weighted traffic routing, and observability — all managed by AWS. No equivalent managed service exists in other clouds at this abstraction level.
- Architecture Impact: Eliminates the need for internal ALBs + service discovery (Cloud Map) + Transit Gateway for service communication. Platform teams define service networks; application teams register services. Dramatically simplifies microservices networking.
- When to Leverage: Microservices architectures spanning multiple VPCs/accounts where service-to-service authentication and traffic management are required without the operational burden of a service mesh (Istio, App Mesh).
- Caveat: HTTP/HTTPS/gRPC only (no TCP/UDP passthrough). Regional only (no cross-Region). Relatively new service — evaluate feature completeness for your use case.
- Source: https://docs.aws.amazon.com/vpc-lattice/latest/ug/what-is-vpc-lattice.html

**AWS Network Firewall with Suricata IPS**
- Category: Network Security
- Unique Value: AWS-native managed firewall with Suricata-compatible intrusion prevention rules, domain-based filtering, and TLS inspection — fully integrated with AWS Firewall Manager for multi-account policy deployment. Eliminates the need for third-party virtual appliance licensing and management.
- Architecture Impact: Enables centralized egress inspection architecture without managing EC2-based firewall appliances. Firewall rules can reference AWS Managed Rule Groups (updated automatically for known threats).
- When to Leverage: Organizations needing L3-L7 stateful inspection, IPS/IDS, and domain filtering without existing investment in third-party firewall vendors.
- Caveat: Feature set is narrower than enterprise firewalls (Palo Alto, Fortinet). No built-in URL categorization database. TLS inspection requires certificate management. Charges per endpoint per AZ per hour + per GB.
- Source: https://docs.aws.amazon.com/network-firewall/latest/developerguide/what-is-aws-network-firewall.html

**Regional NAT Gateway (Multi-AZ Automatic Expansion)**
- Category: Networking Simplification
- Unique Value: NAT Gateway that automatically spans multiple AZs without requiring separate NAT Gateways and route tables per AZ. AWS manages AZ placement and failover. Reduces the operational burden of the most common VPC networking pattern.
- Architecture Impact: Eliminates the need for per-AZ NAT Gateway provisioning, per-AZ route tables for private subnets, and custom automation for NAT Gateway health monitoring. Single route table entry works for all AZs.
- When to Leverage: Any new VPC deployment where per-AZ NAT management complexity is undesirable. Production workloads that benefit from AWS-managed HA without per-AZ infrastructure.
- Caveat: Less control over AZ-specific routing behavior. Cross-AZ data transfer charges still apply (traffic may cross AZ boundaries within the regional NAT). Verify availability in your Region.
- Source: https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateways-regional.html

**VPC Block Public Access (Account-Level Internet Gateway Blocking)**
- Category: Security
- Unique Value: Account-level control that prevents ANY VPC from routing traffic through Internet Gateways unless explicitly excluded. Provides a "no internet by default" security posture at the account level — a preventive control that cannot be bypassed by individual VPC configurations.
- Architecture Impact: Forces all internet access through designated egress VPCs (via Transit Gateway). Prevents accidental internet exposure from misconfigured route tables or newly created VPCs.
- When to Leverage: All production and regulated accounts. Only the edge/DMZ account should have internet gateway access. Workload accounts should have BPA enabled with no exclusions.
- Caveat: Must explicitly exclude VPCs that legitimately need internet gateway routing. Can break existing workloads if enabled without audit. Combine with SCPs to prevent disabling.
- Source: https://docs.aws.amazon.com/vpc/latest/userguide/security-vpc-bpa.html

---

## Scenario Coverage

**Standard Case**: Production three-tier web application with public internet access, private application tier, and isolated database tier in a single Region.
- Approach: VPC with /16 CIDR, 3 AZs, 3 subnet tiers (public/private/isolated). ALB in public subnets. App servers in private subnets with NAT Gateway per AZ (or Regional NAT). RDS Multi-AZ in isolated subnets (no internet route). Gateway Endpoints for S3/DynamoDB. Security groups per tier with SG-reference rules. VPC Flow Logs to S3.
- Key Decisions: NAT strategy (per-AZ vs Regional), whether to add Network Firewall for egress inspection, IPv4 vs dual-stack, number of AZs (2 vs 3).

**Edge Case**: Multi-Region active-active deployment with on-premises hybrid connectivity and overlapping CIDRs from M&A integration.
- Approach: Use AWS PrivateLink for cross-VPC service exposure (handles CIDR overlap). Deploy Transit Gateway per Region with inter-Region peering. Use private NAT Gateways for CIDR translation between overlapping networks. Direct Connect with Transit VIF for on-premises connectivity. Route 53 with latency-based routing for global traffic distribution. Long-term: re-IP overlapping VPCs using IPAM-managed non-overlapping pools.
- Key Decisions: PrivateLink vs private NAT for overlap handling, active-active vs active-passive across Regions, Direct Connect redundancy level, data replication strategy.

**Anti-Pattern Case**: Developer requests opening security group 0.0.0.0/0 on port 22 for SSH access to production instances.
- Clarification: "What is the business justification for direct SSH access? AWS Systems Manager Session Manager provides shell access without opening any inbound ports and provides full audit logging. If SSH is specifically required (e.g., for SCP file transfer), access should be restricted to the corporate VPN CIDR range and time-limited using temporary security group rules via automation."
