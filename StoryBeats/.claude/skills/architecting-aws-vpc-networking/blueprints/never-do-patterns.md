# Never Do Patterns — architecting-aws-vpc-networking

Seven anti-patterns with risk levels, detection commands, and correct alternatives.
Every ❌ wrong example has a ✅ correct alternative — never refuse without offering the fix.

Source: Amazon VPC User Guide + AWS Well-Architected Framework, verified 2026-07-31.

---

## AP-1 — Single-AZ Subnet Layout for Production
**Risk**: CRITICAL — full service outage on one AZ impairment
**WAF Pillar**: Reliability

❌ **Wrong**: All app instances and the RDS primary placed in subnets only in `us-east-1a`. No
subnets exist in other AZs.

✅ **Correct**: Private subnets in `us-east-1a`, `us-east-1b`, `us-east-1c`; Auto Scaling group
targeting all three AZs; RDS Multi-AZ with a standby in a second AZ.

```
# ❌ Wrong subnet layout
Subnet: subnet-app-only  →  AZ: us-east-1a  (single AZ)

# ✅ Correct subnet layout
Subnet: subnet-app-1a    →  AZ: us-east-1a
Subnet: subnet-app-1b    →  AZ: us-east-1b
Subnet: subnet-app-1c    →  AZ: us-east-1c
```

**Detection**:
```bash
aws ec2 describe-subnets \
  --filters Name=vpc-id,Values=<vpc-id> \
  --query "Subnets[].AvailabilityZone" --output text \
  | tr '\t' '\n' | sort -u
# Single line output = single-AZ violation
```

**Source**: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-best-practices.html

---

## AP-2 — Overlapping or Unplanned CIDR Ranges
**Risk**: HIGH — permanently blocks VPC peering, TGW attachment, Direct Connect gateway association
**WAF Pillar**: Reliability, Operational Excellence

❌ **Wrong**: Every VPC created with `10.0.0.0/16`. Two VPCs later need to peer — impossible.

✅ **Correct**: Central IPAM allocates disjoint blocks from a pre-planned range. Avoid
`172.17.0.0/16` (used by Cloud9/SageMaker).

```
# ❌ Wrong: identical CIDRs across VPCs
vpc-prod:    10.0.0.0/16
vpc-staging: 10.0.0.0/16   <-- overlap; peering permanently blocked

# ✅ Correct: disjoint allocations from IPAM plan
vpc-prod:    10.0.0.0/16
vpc-staging: 10.1.0.0/16
vpc-dev:     10.2.0.0/16
```

**Key constraint**: A VPC IPv4 CIDR block cannot be resized or deleted if resources exist in it.
Plan for growth; a `/16` gives 65,536 addresses; a `/24` gives 251 usable.

**Detection**:
```bash
aws ec2 describe-vpcs \
  --query "Vpcs[].{ID:VpcId,CIDR:CidrBlock}" --output table
# Cross-check each CIDR — no two should overlap (use IPAM to automate this)
```

**Source**: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-cidr-blocks.html

---

## AP-3 — Databases / Internal Services in a Public Subnet
**Risk**: CRITICAL — any resource with a public IP in an IGW-routed subnet is internet-exposed
**WAF Pillar**: Security

❌ **Wrong**: RDS instance launched in `subnet-pub-1a` (route table: `0.0.0.0/0 → igw-xxxx`),
with "Publicly Accessible" enabled.

✅ **Correct**: RDS in `subnet-data-1a` — a subnet whose route table has **only** `local` +
VPC endpoint routes. Reachable from app-tier SG only on port 5432; no internet path exists.

```
# ❌ Wrong route table for data subnet
Route:  0.0.0.0/0 → igw-xxxx   <-- ANY resource with a public IP is reachable from internet

# ✅ Correct route table for isolated/data subnet
Route:  10.0.0.0/16 → local           (VPC-local traffic only)
Route:  pl-xxxx (S3 prefix list) → vpce-xxxx  (gateway endpoint, optional)
# NO default route to IGW or NAT
```

**When developers ask to access RDS directly**: Offer instead:
- AWS Systems Manager Session Manager port forwarding (no inbound port)
- A bastion/jump host in a public subnet with SG-referenced access (not `0.0.0.0/0`)
- AWS Client VPN endpoint

**Detection**:
```bash
# Find ENIs in subnets that have an IGW default route — check if any are RDS/ElastiCache
aws ec2 describe-network-interfaces \
  --filters Name=subnet-id,Values=<suspect-subnet-ids> \
  --query "NetworkInterfaces[].{ENI:NetworkInterfaceId,Owner:Description,PublicIP:Association.PublicIp}"
```

**Source**: https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Route_Tables.html

---

## AP-4 — Wide-Open Security Group Ingress on Management Ports
**Risk**: CRITICAL — SSH (22) / RDP (3389) open to `0.0.0.0/0` exposes management surface to the
entire internet
**WAF Pillar**: Security

❌ **Wrong**: Security group inbound rule `TCP 22, Source 0.0.0.0/0` on any instance SG.

✅ **Correct**: No inbound SSH/RDP from the internet. Use AWS Systems Manager Session Manager for
shell access — requires no inbound port, uses IAM for authorization, and logs to CloudWatch/S3.

```
# ❌ Wrong SG rule (DO NOT create this)
{
  "IpProtocol": "tcp",
  "FromPort": 22,
  "ToPort": 22,
  "IpRanges": [{"CidrIp": "0.0.0.0/0"}]   <-- internet-wide SSH exposure
}

# ✅ Correct: no inbound SSH rule at all; use SSM Session Manager
# If direct SSH is unavoidable:
{
  "IpProtocol": "tcp",
  "FromPort": 22,
  "ToPort": 22,
  "IpRanges": [{"CidrIp": "<corporate-cidr>/32", "Description": "Corp VPN only"}]
}
```

**Prerequisite for SSM Session Manager**: Install SSM Agent on instances; attach IAM role with
`AmazonSSMManagedInstanceCore`; ensure interface endpoint for `com.amazonaws.<region>.ssm`.

**Detection**:
```bash
aws ec2 describe-security-groups \
  --query "SecurityGroups[?IpPermissions[?((FromPort==\`22\` || FromPort==\`3389\`) && contains(IpRanges[].CidrIp,'0.0.0.0/0'))]].{ID:GroupId,Name:GroupName}"
# Expected: Empty list
```

**Source**: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-best-practices.html

---

## AP-5 — VPC Flow Logs Disabled
**Risk**: HIGH — no network traffic record for forensics; GuardDuty loses foundational data source
**WAF Pillar**: Security, Operational Excellence

❌ **Wrong**: VPC created with no flow log configured; no network telemetry retained.

✅ **Correct**: VPC-scoped flow log (TrafficType ALL) delivering to CloudWatch Logs and/or S3;
retained per compliance policy; GuardDuty enabled and consuming flow logs automatically.

```bash
# ❌ Wrong: no flow log for VPC
aws ec2 describe-flow-logs --filter Name=resource-id,Values=<vpc-id>
# Returns: empty FlowLogs array

# ✅ Correct: create flow log at VPC scope
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids <vpc-id> \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name /vpc/flowlogs/<vpc-id> \
  --deliver-logs-permission-arn arn:aws:iam::<account>:role/VPCFlowLogsRole
```

**Note**: Flow logs capture metadata (5-tuple + action + bytes) NOT packet payloads. For deep
packet inspection, use Traffic Mirroring in addition to (not instead of) flow logs.

**Detection**:
```bash
aws ec2 describe-flow-logs \
  --filter Name=resource-id,Values=<vpc-id> \
  --query "FlowLogs[?FlowLogStatus=='ACTIVE'].FlowLogId"
# Expected: at least one active flow log ID
```

**Source**: https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html

---

## AP-6 — Single NAT Gateway Serving All AZs
**Risk**: HIGH — single-AZ egress dependency; cross-AZ data-transfer charges
**WAF Pillar**: Reliability, Cost Optimization

❌ **Wrong**: One NAT gateway in `us-east-1a`; private route tables in ALL AZs point
`0.0.0.0/0` to it.

✅ **Correct**: One NAT gateway per AZ, each in that AZ's public subnet with its own Elastic IP.
Each AZ's private route table routes `0.0.0.0/0` to its same-AZ NAT gateway.

```
# ❌ Wrong: all private route tables (1a, 1b, 1c) point to one NAT GW in 1a
rtb-private-1a:  0.0.0.0/0 → nat-gw-1a
rtb-private-1b:  0.0.0.0/0 → nat-gw-1a   <-- cross-AZ dependency + charges
rtb-private-1c:  0.0.0.0/0 → nat-gw-1a   <-- cross-AZ dependency + charges

# ✅ Correct: each AZ routes to its local NAT GW
rtb-private-1a:  0.0.0.0/0 → nat-gw-1a
rtb-private-1b:  0.0.0.0/0 → nat-gw-1b
rtb-private-1c:  0.0.0.0/0 → nat-gw-1c
```

**Cost note**: Cross-AZ traffic is charged per-GB in both directions. Routing 1b/1c through 1a's
NAT gateway doubles the cross-AZ data-transfer cost for that traffic.

**Detection**:
```bash
# More private subnets' AZs than NAT gateways = single-NAT pattern
aws ec2 describe-nat-gateways \
  --filter Name=vpc-id,Values=<vpc-id> \
  --query "NatGateways[?State=='available'].SubnetId" --output text | wc -w
# If count < number of AZs used by private subnets → single-NAT pattern in use
```

**Source**: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html

---

## AP-7 — Relying Solely on NACLs for Instance Security
**Risk**: MEDIUM — stateless NACLs as primary control leads to overly broad rules and broken return
traffic (ephemeral ports missed)
**WAF Pillar**: Security

❌ **Wrong**: Permissive security groups with `0.0.0.0/0` allows, relying on hand-tuned NACLs to
restrict per-app traffic — and forgetting to allow ephemeral return ports (1024–65535).

✅ **Correct**: Security groups (stateful, instance-scoped, SG-referencing) as the primary control.
NACLs used only as a coarse deny backstop (e.g., block a known-bad CIDR). Remember ephemeral
return ports in every NACL outbound rule.

```
# ❌ Wrong: NACL attempting to replace SG (forgetting ephemeral return ports)
NACL Inbound:  100 ALLOW TCP 0.0.0.0/0 443
NACL Outbound: 100 ALLOW TCP 0.0.0.0/0 443  <-- WRONG: return traffic uses ports 1024-65535

# ✅ Correct: NACL as coarse backstop; SG as primary control
# NACL
Inbound:  100 DENY  TCP <bad-cidr>/32 ALL  (explicit deny — only NACL supports this)
Inbound:  200 ALLOW ALL 0.0.0.0/0     ALL  (allow everything else — SG handles details)
Outbound: 100 ALLOW TCP 0.0.0.0/0    1024-65535  (ephemeral return ports)
Outbound: 200 ALLOW ALL 0.0.0.0/0     ALL

# SG (primary control)
Inbound: ALLOW TCP from app-sg 5432  (database port from app SG reference — precise, stateful)
```

**Key distinction**: Security groups can **only allow**; NACLs can **allow and explicitly deny**.
Use NACLs for the cases where an explicit deny is required — never as a replacement for SGs.

**Source**: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-best-practices.html
