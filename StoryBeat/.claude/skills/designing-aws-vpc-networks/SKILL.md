---
name: designing-aws-vpc-networks
description: "Designs production-grade AWS VPC networking architectures for web applications. Use when architecting VPC topology, subnet tiers, security boundaries, NAT gateway HA patterns, hybrid connectivity, multi-account hub-and-spoke, or compliance-driven in-transit encryption on AWS."
---

## Function

Specialist in AWS VPC Networking and multi-tier web application network design for AWS 2026.

## Version Context

**Technology**: Amazon VPC — AWS Networking
**Target Edition**: AWS VPC Networking 2026
**Research Date**: 2026-08-30
**Currency Threshold**: 2027-08-30
**Support Status**: Active

**Key features introduced 2024–2026**:
- VPC Block Public Access (BPA) — GA November 2024; Declarative Policy via Organizations December 2024
- Security Group VPC Associations (cross-VPC SG reuse) — October 2024
- TGW Per-AZ CloudWatch Metrics — Late 2024
- VPC Route Server (BGP dynamic routing) — GA March 2025; 16 additional Regions January 2026
- Regional NAT Gateways with Auto Multi-AZ Expansion — November 2025
- VPC Encryption Controls (hardware AES-256 in-transit) — GA November 2025; paid from March 2026; Declarative via Organizations July 2026
- AWS Interconnect (Cloud WAN to Google Cloud) — GA April 2026; Azure/OCI preview later 2026
- VPC Lattice WebSocket TLS + AI agent zero-trust — August 2026
- CloudFront WebSocket for private VPC origins — May 2026

**Deprecated / avoid**:
- Manual BGP route-table management for dynamic routing (superseded by VPC Route Server)
- Manual CIDR tracking spreadsheets (superseded by AWS IPAM)
- O(n²) VPC peering mesh for 4+ VPCs (superseded by Transit Gateway)

⚠️ **CRITICAL — Agent Warning**:
This skill targets AWS VPC patterns as of 2026-08-30.
Reject guidance that predates VPC Block Public Access (November 2024) as the recommended preventive control baseline.
Do not recommend single NAT Gateway shared across AZs — this is a High-risk anti-pattern.

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — ✅⚠️🚫 operational patterns
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 6 test cases for this skill
- **[Integration Patterns](#integration-patterns)** — cross-service design summaries
- **[Reference Architectures](./blueprints/reference-architectures.md)** — canonical 3-tier and landing zone designs
- **[Verification Loop](#verification-loop)** — CLI validation commands
- **[Quick Reference](#quick-reference)** — critical limits at a glance
- **[External Resources](#external-resources)** — official AWS documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

**Multi-AZ Three-Tier Subnet Architecture** (Reliability REL02-BP01, REL02-BP03 / Security SEC05)
Deploy three subnet tiers per AZ, minimum 2 AZs for production:
- **Tier 1 — Public (Edge)**: Internet Gateway, ALB nodes, NAT Gateways (one per AZ). Route table: `0.0.0.0/0 → IGW`.
- **Tier 2 — Private (Application)**: EC2 / ECS / EKS. No public IP. Route table: `0.0.0.0/0 → same-AZ NAT GW`.
- **Tier 3 — Isolated (Data)**: RDS Multi-AZ, ElastiCache. No internet routes. Reachable only from Tier 2 SG.
- Add S3 and DynamoDB Gateway Endpoint routes in all private subnet route tables.

**Per-AZ NAT Gateway** (Reliability — NAT GW is redundant within a single AZ only)
Provision one NAT Gateway per AZ in that AZ's public subnet. Each AZ's private subnets route `0.0.0.0/0` to their own AZ's NAT GW. For IPv6 private subnets, add `::/0 → Egress-Only Internet Gateway`. Eliminates cross-AZ data transfer charges and AZ-failure cascades.

**Non-Overlapping CIDR Planning via AWS IPAM** (Reliability REL02-BP05 — Risk: Medium)
The initial VPC CIDR cannot be changed or deleted. Size at `/16`–`/20`; use `/24` minimum per tier per AZ. Avoid `172.17.0.0/16` (reserved by Cloud9 and SageMaker). Use AWS IPAM with an org-level → Region-level → account-level → VPC allocation hierarchy. Plan for 3× current fleet size. Monitor `NetworkAddressUsage` CloudWatch metric (namespace `AWS/EC2`, every 24h); alert at 70% of quota.

**Enable VPC Flow Logs for All Production VPCs** (Security / Compliance)
Enable at VPC level, capture `ALL` traffic (not just `REJECT`). Publish to S3 in Parquet format for cost-effective Athena querying; add CloudWatch Logs for real-time alerting. Required for PCI DSS, HIPAA, and SG rule troubleshooting. Flow Logs are out-of-path — zero impact on throughput or latency.

**Gateway Endpoints for S3 and DynamoDB** (Cost Optimization)
Always add Gateway VPC Endpoints for S3 and DynamoDB (free). Update private subnet route tables to route S3 and DynamoDB prefix lists to the Gateway endpoint. Eliminates NAT Gateway data-processing charges ($0.045/GB) for these traffic types and keeps data off the internet.

**Security Group Micro-Segmentation via SG Referencing** (Security SEC05)
Canonical 3-tier SG rule set:
- ALB SG: inbound TCP 80/443 from `0.0.0.0/0`; no inbound from any other source.
- App SG: inbound app port from `ALB SG ID` only.
- DB SG: inbound DB port from `App SG ID` only.
Never use CIDR ranges for tier-to-tier segmentation when SG referencing is available. Use NACLs only as secondary defence-in-depth (remember ephemeral ports 1024–65535 for return traffic).

**Enforce VPC Block Public Access (BPA) at Account / Org Level**
Apply BPA Declarative Policy via AWS Organizations (December 2024) to all accounts in secure environments. BPA is enforced by the VPC service plane and cannot be overridden by instance or subnet configurations. Combine with VPC Encryption Controls Declarative Policy (July 2026) for a complete preventive control baseline satisfying HIPAA and PCI DSS.

### ⚠️ Ask First

**VPC Peering vs Transit Gateway vs Cloud WAN**
Ask: "How many VPCs will this environment grow to in 24 months?"

| Option | Best When | Trade-off |
|--------|-----------|-----------|
| VPC Peering | ≤ 3 VPCs, cost/latency priority | Non-transitive; O(n²) connections at scale |
| Transit Gateway | 4+ VPCs, hybrid, multi-account, enterprise | Per-attachment/hr + per-GB charges; extra hop |
| Cloud WAN | Global multi-Region WAN unification | Higher baseline cost; primarily for global SD-WAN |

If the answer is more than 3 VPCs, design for TGW from day one — retrofitting is expensive.

**Load Balancer Selection**
Ask: "Is this HTTP/HTTPS traffic?"

| Option | Best When |
|--------|-----------|
| ALB | HTTP/HTTPS web apps, REST APIs, microservices — default |
| NLB | Non-HTTP (TCP/UDP/TLS), ultra-low latency, static IP required |
| Global Accelerator | Global gaming, IoT, VoIP, non-HTTP global anycast |

**VPC Endpoint Type Selection**
Ask: "Which AWS service are we connecting to?"

| Option | Best When |
|--------|-----------|
| Gateway Endpoint (S3, DynamoDB) | Always — free, route-table based |
| Interface Endpoint (PrivateLink) | All other AWS services from private subnets |

Note: Interface endpoints have per-AZ hourly charges plus data processing fees. Gateway endpoints are always free.

**Hybrid Connectivity: Direct Connect vs Site-to-Site VPN**
Ask: "What are the latency and bandwidth requirements for on-premises connectivity?"

| Option | Best When |
|--------|-----------|
| Direct Connect | Production, consistent SLA, high bandwidth |
| Site-to-Site VPN | Dev/sandbox, quick setup, encrypted backup path |
| DX + VPN | Enterprise production requiring HA with encryption |

**VPC Lattice vs ALB for East-West Service Mesh**
Ask: "Do services span multiple VPCs or accounts with overlapping IPs?"
If yes: VPC Lattice (IAM-native auth, NAT64 for IP overlap, no peering/PrivateLink per service pair, WebSocket TLS as of August 2026, AI agent zero-trust as of August 2026).
If no (single VPC, simple internal routing): ALB with internal scheme is sufficient.

### 🚫 Never Do

| Anti-Pattern | Why | Correct Alternative |
|---|---|---|
| Single NAT Gateway shared across all AZs | NAT GW is AZ-redundant only — AZ failure cascades to all private subnets; cross-AZ charges accrue | One NAT GW per AZ; route each AZ's private subnets to their own AZ's NAT GW |
| Public IP on application or database resources | Bypasses ALB and WAF; exposes app/data tier directly to internet; Security Hub EC2.9 / RDS.2 | ALB nodes in public subnets; EC2/ECS in private subnets (no public IP); RDS `publicly_accessible = false` |
| SSH/RDP inbound from `0.0.0.0/0` | Direct brute-force surface; Security Hub Critical EC2.19; violates PCI DSS/HIPAA/SOC2 | Remove all SSH/RDP inbound rules; use AWS Systems Manager Session Manager (no open ports required) |
| VPC CIDR /24 or smaller for a production workload | Initial CIDR cannot be changed; subnet exhaustion blocks Auto Scaling, NAT GW, Lambda, TGW attachments | Size VPC at /16–/20; /24 minimum per tier per AZ; enforce via AWS IPAM |
| NACLs as primary security mechanism without ephemeral port rules | NACLs are stateless — missing ephemeral ports (1024–65535) silently blocks all return TCP traffic | Use SGs as primary (stateful); NACLs only for secondary deny-by-CIDR defence; always include ephemeral port rules |
| Default "full access" VPC endpoint policies | Allows any principal in the account to call any API via the endpoint — violates zero-trust | Replace with restrictive endpoint policies using `aws:PrincipalArn` conditions; deny `aws:SourceVpc` bypass via SCPs |

---

## Integration Patterns

For complete architecture code and Terraform examples, see [Reference Architectures](./blueprints/reference-architectures.md).

**CloudFront + ALB + WAF Edge Architecture** (north-south, web apps)
Internet → CloudFront (CDN, Shield Standard, 600+ PoPs) → ALB in public subnets (WAF attached; SQLi, XSS, rate limiting, geo-block) → Auto Scaling EC2/ECS/EKS in private subnets. CloudFront-to-AWS-origin transfer is free. As of May 2026, CloudFront supports WebSocket connections to private VPC origins.

**TGW Hub-and-Spoke with Centralized Egress Inspection** (multi-account)
Transit Gateway in Network Services account → spoke VPC attachments → inspection VPC (Network Firewall with Suricata rules, Appliance Mode enabled) → centralized NAT GWs → IGW. TGW Flow Logs for cross-account visibility. VPC BPA Declarative Policy from Management account.

**VPC Lattice East-West Service Mesh** (container/serverless)
VPC Lattice service network → associate spoke VPCs → define per-microservice services + target groups → IAM auth policies (zero-trust). Handles overlapping IP spaces via NAT64. Weighted target groups for blue/green deployments.

**Route 53 Private DNS for Hybrid Environments**
Private Hosted Zones for internal service discovery. Inbound Resolver Endpoints (on-premises → Route 53 query forwarding). Outbound Resolver Endpoints with conditional forwarding rules (VPC → on-premises DNS). Route 53 Resolver DNS Firewall for malicious domain blocking.

**Common Problems**:
- **Subnet IP exhaustion during scaling** → Monitor `NetworkAddressUsage`; add secondary non-overlapping CIDR as interim; plan at /16–/20 from day one
- **Cannot create TGW attachment or peering** → Overlapping CIDRs; use IPAM to audit and resolve before provisioning
- **Cross-AZ data transfer costs unexpectedly high** → Private subnets routing to wrong AZ's NAT GW; audit route tables; add Gateway endpoints for S3/DynamoDB
- **Reachability issue after SG or NACL change** → Run VPC Reachability Analyzer for hop-by-hop diagnosis; use Network Access Analyzer for at-scale internet accessibility audit

---

## Verification Loop

Run after every VPC architecture change or Terraform/CDK apply:

### 1. Subnet and Route Table Audit
```bash
# List all route tables for a VPC
aws ec2 describe-route-tables --filters Name=vpc-id,Values=<vpc-id> \
  --query 'RouteTables[*].{ID:RouteTableId,Routes:Routes}'
# Expected: public subnets have 0.0.0.0/0 → igw-xxx; private subnets have 0.0.0.0/0 → nat-xxx
```

### 2. NAT Gateway HA Verification
```bash
# Verify one NAT GW per AZ
aws ec2 describe-nat-gateways --filter Name=state,Values=available \
  --query 'NatGateways[*].{ID:NatGatewayId,AZ:SubnetId,State:State}'
# Expected: count >= number of AZs used; each in a different AZ public subnet
```

### 3. VPC CIDR and NAU Monitoring
```bash
# Inspect VPC CIDRs
aws ec2 describe-vpcs --query 'Vpcs[*].[VpcId,CidrBlock,CidrBlockAssociationSet]'
# Check NetworkAddressUsage metric (CloudWatch namespace AWS/EC2, metric NetworkAddressUsage)
```

### 4. Security Hub VPC Controls
```bash
# Check critical EC2 network controls
aws securityhub get-findings \
  --filters '{"ComplianceControlId":[{"Value":"EC2.13","Comparison":"EQUALS"},{"Value":"EC2.14","Comparison":"EQUALS"},{"Value":"EC2.19","Comparison":"EQUALS"}]}' \
  --query 'Findings[*].{Title:Title,Severity:Severity.Label,Status:Compliance.Status}'
# Expected: no FAILED findings for EC2.13 (SSH), EC2.14 (RDP), EC2.19 (high-risk ports)
```

### 5. Flow Logs Active
```bash
aws ec2 describe-flow-logs --filter Name=resource-id,Values=<vpc-id> \
  --query 'FlowLogs[*].{Status:FlowLogStatus,Destination:LogDestinationType}'
# Expected: FlowLogStatus = ACTIVE; at least one S3 or CloudWatch Logs destination
```

**Troubleshooting**:
- No internet from private subnet → verify route table has `0.0.0.0/0 → nat-xxx` for correct AZ's NAT GW
- Return traffic blocked → check NACL for missing ephemeral port (1024–65535) rules
- TGW attachment fails → overlapping CIDRs; check IPAM allocations
- Cannot SSH → expected (use SSM Session Manager); verify `ssm`, `ssmmessages`, `ec2messages` Interface endpoints exist if no internet access

---

## Quick Reference

**Subnet sizing minimums**:

| Tier | CIDR | Usable IPs | Notes |
|------|------|-----------|-------|
| Public (Edge) | /28 minimum, /24 recommended | 11 minimum | NAT GW + ALB nodes consume IPs |
| Private (App) | /24 recommended | 251 | Auto Scaling needs headroom |
| Isolated (Data) | /28 minimum, /24 recommended | 11 minimum | RDS Multi-AZ needs 2+ IPs |

**Critical service limits**:

| Resource | Limit | Impact if Exceeded |
|----------|-------|---------------------|
| VPCs per Region | 5 (default, increasable) | Cannot create new VPCs |
| Subnets per VPC | 200 | Cannot add AZs or tiers |
| NAT GW connections per destination IP | 55,000 simultaneous | `ErrorPortAllocation` — split subnets for more NAT GWs |
| TGW VPC attachment bandwidth | 50 Gbps burst | Use multiple attachments for higher throughput |
| NAT Gateway bandwidth | 5 Gbps → 100 Gbps (auto-scale) | No action needed; auto-scales |

**AWS Config rules to enable**:
`restricted-ssh`, `restricted-rdp`, `restricted-common-ports`, `vpc-sg-open-only-to-authorized-ports`, `nacl-no-unrestricted-ssh-rdp`, `vpc-peering-dns-resolution-check`

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/designing-aws-vpc-networks/
├── SKILL.md                              ← This file (guardrails + quick reference)
└── blueprints/
    ├── evaluation-scenarios.md           ← 6 test scenarios for skill-evaluator
    └── reference-architectures.md        ← Canonical 3-tier VPC + landing zone designs
```

---

## External Resources

### Official Documentation
- [Amazon VPC User Guide](https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html) — Primary reference
- [VPC Example: Private Subnets + NAT](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-example-private-subnets-nat.html) — Canonical 3-tier reference
- [AWS Well-Architected Reliability Pillar — REL02](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/) — REL02-BP01/03/05
- [Building Scalable Secure Multi-VPC Network Infrastructure](https://docs.aws.amazon.com/whitepapers/latest/building-scalable-secure-multi-vpc-network-infrastructure/) — TGW, VPC Lattice, peering
- [AWS IPAM Documentation](https://docs.aws.amazon.com/vpc/latest/ipam/what-it-is-ipam.html) — CIDR management
- [VPC PrivateLink and Endpoints](https://docs.aws.amazon.com/vpc/latest/privatelink/gateway-endpoints.html) — Gateway vs Interface endpoints

### Security & Compliance
- [AWS Security Hub EC2 Controls](https://docs.aws.amazon.com/securityhub/latest/userguide/ec2-controls.html) — EC2.13/14/18/19/21
- [VPC Block Public Access](https://aws.amazon.com/about-aws/whats-new/2024/11/block-public-access-amazon-virtual-private-cloud/) — November 2024 GA
- [VPC Encryption Controls](https://aws.amazon.com/about-aws/whats-new/2025/11/aws-vpc-encryption-controls/) — November 2025 GA

### 2026 Feature Releases
- [AWS Interconnect GA (GCP)](https://aws.amazon.com/about-aws/whats-new/2026/04/aws-announces-ga-AWS-interconnect-multicloud/) — April 2026
- [CloudFront WebSocket for VPC Origins](https://aws.amazon.com/about-aws/whats-new/2026/05/amazon-cloudfront-websockets-vpc-origins/) — May 2026
- [VPC Route Server — New Regions](https://aws.amazon.com/about-aws/whats-new/2026/01/amazon-vpc-route-server-available-new-regions/) — January 2026
