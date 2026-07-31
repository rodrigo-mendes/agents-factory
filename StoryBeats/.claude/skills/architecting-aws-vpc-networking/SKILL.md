---
name: architecting-aws-vpc-networking
description: "Architects Amazon VPC network topology for production workloads on AWS. Use when designing VPC CIDR plans, subnet tiering (public/private/isolated), routing, security groups, NAT capacity, private service access via PrivateLink, or hybrid connectivity."
---

## Function
Specialist in AWS VPC networking architecture for multi-tier, multi-AZ production workloads.

## Version Context

**Technology**: Amazon VPC (Virtual Private Cloud)
**Edition**: Amazon VPC User Guide (continuously published) — verified **2026-07-31**
**Governing Framework**: AWS Well-Architected Framework — edition **2024-11-06** (current stable)
**Currency Threshold**: Re-verify after **2027-07-31** (VPC feature availability, WAF edition)

**Key features in scope**:
- IPv6 / dual-stack support and Amazon-provided IPv6 blocks
- AWS IP Address Manager (IPAM) for CIDR governance
- Private NAT gateways (VPC-to-VPC / on-prem egress without IGW)
- Regional NAT gateways for automatic multi-AZ expansion
- AWS Network Firewall and Network Access Analyzer

⚠️ **Version Lock**: AWS VPC has no release version numbers. All patterns target the current service state verified on **2026-07-31**. Re-verify listed feature maturity on next review.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — 7 mandatory networking guardrails with CLI verification commands
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — 4 architectural crossroads with trade-off matrices
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — 7 anti-patterns with correct alternatives
- **[Integration Patterns](./blueprints/integration-patterns.md)** — VPC integrations with compute, storage, and monitoring services
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 3 test scenarios: canonical, edge, anti-pattern trap
- **[Verification Loop](#verification-loop)** — AWS CLI validation commands
- **[Quick Reference](#quick-reference)** — Critical limits and essential CLI
- **[External Resources](#external-resources)** — Official AWS documentation

---

## Blueprints & Guardrails

### ✅ Always Do

For complete patterns with CLI verification commands, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**All 7 mandatory patterns (Complex tier — security-critical, multi-layer)**:
- **Multi-AZ subnet layout for every tier** — Create ≥2 (prefer 3) subnets per tier across distinct AZs. A subnet is pinned to one AZ; single-AZ deployments fail entirely on one AZ impairment. (Reliability)
- **Public/private/isolated subnet model via route tables** — A subnet is "public" only by its route table (`0.0.0.0/0 → IGW`). Databases must never sit in a subnet with a public default route. (Security, Reliability)
- **Non-overlapping RFC 1918 CIDR blocks, sized for growth** — VPC CIDRs (`/16`–`/28`) cannot be resized after creation; overlapping ranges permanently block peering, Transit Gateway, and Direct Connect. Avoid `172.17.0.0/16`. Use IPAM in multi-account landing zones. (Reliability, Operational Excellence)
- **NAT gateway per AZ for private-subnet egress** — NAT gateways are AZ-scoped; one NAT gateway for all AZs is a single-AZ failure point and generates avoidable cross-AZ data charges. (Reliability, Cost)
- **Private AWS service access via VPC endpoints** — Add gateway endpoints for S3/DynamoDB (free, route-table-based). Add interface endpoints for services in isolated subnets (Secrets Manager, KMS, ECR, CloudWatch Logs) so data-tier subnets need no NAT/IGW. (Security, Cost)
- **VPC Flow Logs at VPC scope** — Create a flow log at VPC scope (covers all ENIs including future ones) to CloudWatch Logs or S3. Required for forensics and GuardDuty threat detection. (Security, Operational Excellence)
- **Security groups as primary control, NACLs as subnet backstop** — SGs are stateful, instance-scoped, allow-only. Write tier-to-tier rules by referencing SGs as sources. Use NACLs only for coarse subnet-level deny (e.g., block bad CIDRs); remember ephemeral return ports (NACLs are stateless). (Security)

### ⚠️ Ask First

For complete decision matrices with trade-off tables, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

**4 architectural crossroads — gather requirements before choosing**:
- **VPC-to-VPC connectivity: VPC Peering vs Transit Gateway** — Peering is optimal for few VPCs (≤~5), non-transitive, lowest cost. TGW is required for transitive routing, centralized inspection, or many VPCs. Ask: expected VPC count and whether transitive routing or centralized egress/inspection is required.
- **Hybrid connectivity: Site-to-Site VPN vs Direct Connect (± TGW)** — VPN is fast to stand up and encrypted over internet; DX gives private consistent bandwidth but takes weeks to provision. Ask: required bandwidth, latency SLA, and provisioning timeline.
- **IP addressing: IPv4-only vs dual-stack (IPv4 + IPv6)** — Public IPv4 addresses now incur an hourly charge; IPv6 uses egress-only IGW at no NAT cost but requires operational maturity. Ask: whether IPv6 is required by downstream systems and team readiness.
- **Egress control: distributed NAT per VPC vs centralized egress via TGW** — Centralizing reduces NAT gateway count but adds TGW data-processing and Network Firewall costs. Ask: whether centralized egress inspection is a compliance requirement.

### 🚫 Never Do

For complete anti-patterns with ❌ wrong / ✅ correct side-by-side examples and detection commands, see [Never Do Patterns](./blueprints/never-do-patterns.md).

**All 7 prohibited patterns (risk level in parentheses)**:
- **Single-AZ subnet layout for production** (CRITICAL) — Full service outage on one AZ impairment. Correct: spread each tier across ≥2 AZs, RDS Multi-AZ, Auto Scaling across all AZs.
- **Overlapping or unplanned CIDR ranges** (HIGH) — Cannot resize; permanently blocks peering/TGW/DX. Correct: central IPAM plan with disjoint RFC 1918 allocations.
- **Databases / internal services in a public subnet** (CRITICAL) — Any resource with a public IP in an IGW-routed subnet is internet-exposed. Correct: isolated subnets with `local` + VPC endpoint routes only.
- **Wide-open security group ingress on management ports** (CRITICAL) — `0.0.0.0/0` on SSH(22)/RDP(3389) is internet-exposed. Correct: Systems Manager Session Manager (no inbound port); restrict to corporate CIDR or bastion SG reference if unavoidable.
- **VPC Flow Logs disabled** (HIGH) — No forensics record; GuardDuty loses its foundational data source. Correct: VPC-scoped flow log to CloudWatch/S3 + GuardDuty enabled.
- **Single NAT gateway serving all AZs** (HIGH) — Single-AZ egress dependency + cross-AZ data-transfer charges. Correct: one NAT per AZ; each AZ's private route table targets its same-AZ NAT.
- **Relying solely on NACLs for instance security** (MEDIUM) — NACLs are stateless/subnet-coarse; complex per-app rules break return traffic (ephemeral ports). Correct: SGs as primary control, NACLs as coarse deny backstop only.

---

## Integration Patterns

For complete integration examples, see [Integration Patterns](./blueprints/integration-patterns.md).

**Core VPC integrations**:
- **VPC ↔ EC2 / ECS** — Compute in private app subnets per AZ; app SG allows ingress only from web SG on the required port.
- **VPC ↔ RDS / ElastiCache** — Data stores in isolated subnets (no default route); accessed only from app-tier SG on the DB port.
- **VPC ↔ S3 / DynamoDB** — Gateway endpoints added to route tables eliminate NAT data-processing cost for high-volume access (free).
- **VPC ↔ Transit Gateway** — Each VPC attaches once; TGW route tables segment prod/dev and route egress through an inspection VPC (Network Firewall).
- **VPC ↔ GuardDuty / CloudWatch Logs** — VPC Flow Logs at VPC scope deliver to CloudWatch Logs and/or S3; GuardDuty auto-consumes flow logs.

**Common problems**:
- **Problem**: RDS cannot reach Secrets Manager from isolated subnet → **Solution**: Add interface endpoint for `com.amazonaws.<region>.secretsmanager` and confirm its SG allows HTTPS from the data-tier SG.
- **Problem**: Cross-AZ data cost unexpectedly high → **Solution**: Verify private route tables route each AZ to its same-AZ NAT gateway; add gateway endpoints for S3/DynamoDB.
- **Problem**: VPC peering stuck in "failed" or attachment rejected → **Solution**: Verify CIDRs are non-overlapping; confirm both VPCs are in the same AWS partition; check requester/accepter account quotas.

---

## Verification Loop

Run after each VPC configuration change:

### 1. AZ spread — ≥2 AZs per subnet tier
```bash
aws ec2 describe-subnets \
  --filters Name=vpc-id,Values=<vpc-id> \
  --query "Subnets[].{AZ:AvailabilityZone,Tag:Tags[?Key=='Tier'].Value|[0]}" \
  --output table
# Expected: ≥2 distinct AZs for every tier tag (public/private/isolated)
```

### 2. Route tables — no data-tier subnet has IGW default route
```bash
aws ec2 describe-route-tables \
  --filters Name=vpc-id,Values=<vpc-id> \
  --query "RouteTables[?Routes[?GatewayId && starts_with(GatewayId,'igw-')]].RouteTableId"
# Expected: Only public-tier route tables listed — none tagged as data/isolated
```

### 3. NAT gateways — one per AZ, state available
```bash
aws ec2 describe-nat-gateways \
  --filter Name=vpc-id,Values=<vpc-id> \
  --query "NatGateways[?State=='available'].SubnetId" --output text
# Expected: One SubnetId per AZ used by private subnets
```

### 4. VPC Flow Logs — at least one active
```bash
aws ec2 describe-flow-logs \
  --filter Name=resource-id,Values=<vpc-id> \
  --query "FlowLogs[?FlowLogStatus=='ACTIVE'].[FlowLogId,DeliverLogsStatus]"
# Expected: At least one row; DeliverLogsStatus = SUCCESS
```

### 5. Security groups — no 0.0.0.0/0 on SSH or RDP
```bash
aws ec2 describe-security-groups \
  --query "SecurityGroups[?IpPermissions[?((ToPort==\`22\` || ToPort==\`3389\`) && contains(IpRanges[].CidrIp,'0.0.0.0/0'))]].GroupId"
# Expected: Empty list
```

**Troubleshooting**:
- Flow Logs returns empty → Create flow log via console/IaC; set `TrafficType=ALL`, destination CloudWatch Logs or S3.
- Data-tier subnet appears in IGW route table → Move subnet to a route table with only `local` + VPC endpoint routes; remove NAT/IGW default route.
- One AZ for a tier → Create the missing subnet(s); update Auto Scaling group, ECS cluster, or load balancer to cover all AZs.

---

## Quick Reference

**Essential AWS CLI**:
```bash
# List all VPC CIDRs in the Region
aws ec2 describe-vpcs --query "Vpcs[].{ID:VpcId,CIDR:CidrBlock}" --output table

# List VPC endpoints for a VPC
aws ec2 describe-vpc-endpoints --filters Name=vpc-id,Values=<vpc-id> \
  --query "VpcEndpoints[].ServiceName"

# List CIDR allocations via IPAM
aws ec2 describe-ipam-pools --query "IpamPools[].{ID:IpamPoolId,Cidrs:ProvisionedCidrs}"
```

**Critical limits**:

| Resource | Limit | Scope |
|----------|-------|-------|
| VPC CIDR size | `/16`–`/28` | Per VPC; cannot resize after creation |
| Secondary CIDRs per VPC | 4 (`/28`–`/16` each) | Expand address space without rebuild |
| Reserved IPs per subnet | 5 (first 4 + broadcast) | `/28` yields 11 usable IPs |
| Subnets per VPC | 200 (default soft limit) | Raise via Service Quotas |
| VPC endpoints per VPC | 50 (default soft limit) | Raise via Service Quotas |
| Security groups per ENI | 5 (default); hard max 16 | Plan SG structure accordingly |
| VPCs per Region | 5 (default soft limit) | Raise via Service Quotas |

---

## External Resources

### Official AWS Documentation (verified 2026-07-31)
- [What is Amazon VPC?](https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html) — core components, features, public IPv4 pricing
- [Security best practices for your VPC](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-best-practices.html) — multi-AZ, SG/NACL, Flow Logs, Network Firewall, GuardDuty
- [VPC CIDR blocks](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-cidr-blocks.html) — `/16`–`/28`, RFC 1918, no-resize rule, IPv6 blocks
- [NAT gateways](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html) — public vs private NAT, per-AZ resiliency, Regional NAT option
- [AWS PrivateLink — access AWS services](https://docs.aws.amazon.com/vpc/latest/privatelink/privatelink-access-aws-services.html) — VPC endpoints (gateway + interface)
- [VPC Flow Logs](https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html) — enablement, CloudWatch/S3 delivery
- [VPC connectivity options whitepaper](https://docs.aws.amazon.com/whitepapers/latest/aws-vpc-connectivity-options/introduction.html) — peering, TGW, VPN, Direct Connect, Cloud WAN

### Governing Framework
- [AWS Well-Architected Framework](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html) — edition 2024-11-06 (current stable; re-verify on next skill review)

### Research Input
- [research_cloud_AWS_VPC_Networking_2026-07.md](../../../docs/research_cloud_AWS_VPC_Networking_2026-07.md) — source-dated 2026-07-31; verified live against Amazon VPC User Guide
