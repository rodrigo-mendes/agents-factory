# Always Do Patterns — architecting-aws-vpc-networking

Seven mandatory patterns for every production VPC. Apply all seven; omitting any creates the risk
level shown in parentheses.

Source: Amazon VPC User Guide, verified 2026-07-31.

---

## Pattern 1 — Multi-AZ Subnet Layout for Every Tier
**Pillar**: Reliability
**Risk if omitted**: CRITICAL — full service outage on one AZ impairment

A subnet is pinned to exactly one AZ. HA is impossible without duplicating subnets across AZs.
AWS directive: "When you add subnets to your VPC to host your application, create them in multiple
Availability Zones."

```
Tier          | us-east-1a       | us-east-1b       | us-east-1c
--------------|------------------|------------------|------------------
Public        | subnet-pub-1a    | subnet-pub-1b    | subnet-pub-1c
Private/app   | subnet-app-1a    | subnet-app-1b    | subnet-app-1c
Isolated/data | subnet-data-1a   | subnet-data-1b   | subnet-data-1c
```

**Verification**:
```bash
aws ec2 describe-subnets \
  --filters Name=vpc-id,Values=<vpc-id> \
  --query "Subnets[].AvailabilityZone" --output text \
  | tr '\t' '\n' | sort -u
# Expected: ≥2 distinct AZs; ideally 3
```

**Source**: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-best-practices.html

---

## Pattern 2 — Public/Private/Isolated Subnet Model via Route Tables
**Pillar**: Security, Reliability
**Risk if omitted**: CRITICAL — databases exposed to internet if placed in IGW-routed subnet

A subnet is "public" or "private" solely by its **route table**, not by a subnet attribute.

| Tier | Route table default route | Internet-facing? |
|------|--------------------------|-----------------|
| Public (ALB, NAT GW) | `0.0.0.0/0 → igw-xxxx` | Yes (inbound + outbound) |
| Private/app (compute) | `0.0.0.0/0 → nat-xxxx` | Outbound only |
| Isolated/data (RDS, cache) | None (only `local` + VPC endpoint routes) | No |

**Verification**:
```bash
# Find all route tables with a public default route
aws ec2 describe-route-tables \
  --filters Name=vpc-id,Values=<vpc-id> \
  --query "RouteTables[?Routes[?GatewayId && starts_with(GatewayId,'igw-')]].{RT:RouteTableId,Assoc:Associations[].SubnetId}"
# Confirm none of the associated subnets belong to the private/isolated tiers
```

**Source**: https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Route_Tables.html

---

## Pattern 3 — Non-Overlapping RFC 1918 CIDR Blocks, Sized for Growth
**Pillar**: Reliability, Operational Excellence
**Risk if omitted**: HIGH — overlapping blocks permanently block peering, TGW, and Direct Connect

Rules:
- VPC IPv4 block must be `/16`–`/28`. **Cannot resize after creation.**
- Use RFC 1918: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`.
- Avoid `172.17.0.0/16` (used by Cloud9/SageMaker).
- Use IPAM in multi-account landing zones to prevent overlap before it happens.
- Reserve headroom for secondary CIDRs rather than starting at `/24`.

**Recommended allocation pattern (multi-account)**:
```
Account / VPC         | CIDR
----------------------|------------------
Prod VPC              | 10.0.0.0/16
Staging VPC           | 10.1.0.0/16
Dev VPC               | 10.2.0.0/16
Shared-services VPC   | 10.3.0.0/16
```

**Verification**:
```bash
aws ec2 describe-vpcs \
  --query "Vpcs[].{ID:VpcId,CIDR:CidrBlock}" --output table
# Manually confirm (or use IPAM) that no two blocks overlap
```

**Source**: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-cidr-blocks.html

---

## Pattern 4 — NAT Gateway Per Availability Zone
**Pillar**: Reliability, Cost Optimization
**Risk if omitted**: HIGH — single-AZ egress dependency; cross-AZ data charges

A NAT gateway is AZ-scoped. Routing all private subnets through one NAT gateway creates a
single point of failure **and** incurs cross-AZ data-transfer charges for traffic from subnets in
other AZs.

**Correct routing per AZ**:
```
AZ us-east-1a private subnets → route 0.0.0.0/0 → nat-gw-1a (in public subnet 1a)
AZ us-east-1b private subnets → route 0.0.0.0/0 → nat-gw-1b (in public subnet 1b)
AZ us-east-1c private subnets → route 0.0.0.0/0 → nat-gw-1c (in public subnet 1c)
```

Each NAT gateway requires its own Elastic IP. Alternative: use "Regional NAT gateways for
automatic multi-AZ expansion" (documented as a newer topic — verify current maturity).

**Verification**:
```bash
aws ec2 describe-nat-gateways \
  --filter Name=vpc-id,Values=<vpc-id> \
  --query "NatGateways[?State=='available'].{ID:NatGatewayId,Subnet:SubnetId}" --output table
# Count must equal the number of AZs used by private subnets
```

**Source**: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html

---

## Pattern 5 — Private AWS Service Access via VPC Endpoints
**Pillar**: Security, Cost Optimization
**Risk if omitted**: MEDIUM — AWS-service traffic leaves VPC via NAT/IGW; NAT cost for S3/DynamoDB

Two types:

| Endpoint type | Services | Cost | How it works |
|---------------|----------|------|-------------|
| Gateway endpoint | S3, DynamoDB | Free | Route-table entry; no ENI |
| Interface endpoint (PrivateLink) | Most other AWS services | Hourly + per-GB | ENI in your subnet |

**Gateway endpoint (add to relevant route tables)**:
```bash
aws ec2 create-vpc-endpoint \
  --vpc-id <vpc-id> \
  --service-name com.amazonaws.<region>.s3 \
  --route-table-ids <rtb-private-1a> <rtb-private-1b> <rtb-isolated-1a>
```

**Interface endpoint for isolated subnets (Secrets Manager example)**:
```bash
aws ec2 create-vpc-endpoint \
  --vpc-id <vpc-id> \
  --vpc-endpoint-type Interface \
  --service-name com.amazonaws.<region>.secretsmanager \
  --subnet-ids <subnet-data-1a> <subnet-data-1b> \
  --security-group-ids <sg-endpoint>  # allow HTTPS 443 from data-tier SG
```

**Verification**:
```bash
aws ec2 describe-vpc-endpoints \
  --filters Name=vpc-id,Values=<vpc-id> \
  --query "VpcEndpoints[?State=='available'].ServiceName"
# Must include S3 and DynamoDB gateway endpoints at minimum
```

**Source**: https://docs.aws.amazon.com/vpc/latest/privatelink/privatelink-access-aws-services.html

---

## Pattern 6 — VPC Flow Logs at VPC Scope
**Pillar**: Security, Operational Excellence
**Risk if omitted**: HIGH — no network telemetry for forensics; GuardDuty loses foundational data

Enable at **VPC scope** (not subnet or ENI) so all current and future ENIs are covered.
Flow logs capture metadata (5-tuple + action + bytes) — NOT packet payloads.
For payload inspection, use Traffic Mirroring separately.

**Create flow log to CloudWatch Logs**:
```bash
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids <vpc-id> \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name /vpc/flowlogs/<vpc-id> \
  --deliver-logs-permission-arn arn:aws:iam::<account>:role/VPCFlowLogsRole
```

**Verification**:
```bash
aws ec2 describe-flow-logs \
  --filter Name=resource-id,Values=<vpc-id> \
  --query "FlowLogs[?FlowLogStatus=='ACTIVE'].[FlowLogId,DeliverLogsStatus,LogDestinationType]"
# Expected: At least one row with ACTIVE status and SUCCESS delivery
```

**Source**: https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html

---

## Pattern 7 — Security Groups as Primary Control, NACLs as Subnet Backstop
**Pillar**: Security
**Risk if omitted**: MEDIUM — using NACLs as primary control leads to overly broad rules and broken
return traffic

| Property | Security Group | Network ACL |
|----------|---------------|-------------|
| State | Stateful (return traffic auto-allowed) | Stateless (must allow return explicitly) |
| Scope | Elastic Network Interface (instance) | Subnet boundary |
| Rule type | Allow only | Allow + explicit Deny |
| Best used for | Tier-to-tier and app-level rules | Coarse subnet deny (e.g., block bad CIDR) |

**SG rule using SG reference as source (preferred over CIDR)**:
```
# Allow app-tier EC2 to reach RDS on port 5432
Inbound rule on db-sg:
  Type: PostgreSQL
  Port: 5432
  Source: app-sg   <-- SG ID, not a CIDR
```

**NACL coarse deny example (stateless — must also allow ephemeral return ports 1024-65535)**:
```
Rule 100: DENY  TCP  <bad-cidr>/32  ALL PORTS  (inbound)
Rule 200: ALLOW TCP  0.0.0.0/0     443         (inbound)
Rule 300: ALLOW TCP  0.0.0.0/0     1024-65535  (outbound — ephemeral return)
```

**Verification**:
```bash
# Check for any SG with 0.0.0.0/0 on SSH or RDP
aws ec2 describe-security-groups \
  --query "SecurityGroups[?IpPermissions[?((ToPort==\`22\` || ToPort==\`3389\`) && contains(IpRanges[].CidrIp,'0.0.0.0/0'))]].{ID:GroupId,Name:GroupName}"
# Expected: Empty list

# Broader audit — use Network Access Analyzer
aws ec2 create-network-insights-access-scope ...  # configure scope for unintended paths
```

**Source**: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-best-practices.html
