---
name: securing-vpc-network-access
description: "Secures AWS VPC network access using Security Groups and Network ACLs with defense-in-depth layering. Use when designing tier-to-tier traffic rules, enforcing least-privilege network access, implementing subnet guard rails, or reviewing VPC security posture for production AWS workloads."
---

## Function

Specialist in AWS VPC network segmentation using Security Groups (per-ENI, stateful, allow-only) and Network ACLs (per-subnet, stateless, allow+deny) — aligned with Well-Architected Security Pillar SEC05-BP01/BP02.

## Version Context

**Technology**: AWS Security Groups and Network ACLs (Amazon VPC)
**Target version**: 2026 edition (Amazon VPC User Guide, accessed 2026-08-26)
**Release date**: 2026-08-26 (research date)
**Support status**: Active
**Currency threshold**: Re-verify against Amazon VPC User Guide after 2027-08-26

**Important changes (current as of 2026)**:
- **Security Group VPC Associations** (GA Oct 2024): Associate one SG with multiple VPCs in the same Region/account — eliminates per-VPC SG duplication.
- **Shared Security Groups** (GA Oct 2024): Share SGs across AWS Organizations accounts in a shared VPC via Resource Access Manager.
- **SG Referencing on AWS Transit Gateway** (GA Sep 2024): SG rules can now reference another SG across a Transit Gateway — not only within a VPC or peering connection.
- **Nitro v6 TCP idle timeout**: TCP established idle timeout dropped from 432,000s to **350s** — breaking operational change for long-lived connections (DB pools, persistent HTTP, streaming).

**Deprecated**: No SG/NACL features deprecated in this cycle.

⚠️ **CRITICAL — Agent Warning**:
This skill targets the 2026 AWS VPC security baseline.
Reject pre-2024 patterns that assume SG referencing does not work across Transit Gateway.
Do not apply Azure NSG deny-rule patterns to AWS Security Groups — SGs are allow-only.

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — ✅⚠️🚫 three-tier rules
- **[Integration Patterns](#integration-patterns)** — Three-tier web app, multi-VPC, Transit Gateway
- **[Verification Loop](#verification-loop)** — AWS CLI validation commands
- **[Quick Reference](#quick-reference)** — Quotas and essential CLI commands
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 6 test cases for skill evaluation
- **[External Resources](#external-resources)** — Official documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

**1. Layer SGs as primary control; NACLs as secondary defense-in-depth**
Attach purpose-built SGs to every workload ENI. Attach a custom NACL per subnet tier as a coarse guard rail. AWS positions SGs as *the primary mechanism* and NACLs as *the stateless backstop* — both layers must be active (SEC05-BP01/BP02). A subnet bound to the default NACL (allow-all) has no guard-rail effect.

**2. Use SG referencing for all east-west (tier-to-tier) traffic**
Reference a security group ID (`sg-xxxx`) as the source/destination of a rule — never hardcode a VPC CIDR for intra-VPC service-to-service traffic. Rules follow instances as they autoscale. Pattern: ALB-SG allows 443 from `0.0.0.0/0`; web-SG allows 443 from ALB-SG; db-SG allows the DB port from web-SG. Referencing works across VPC peering and AWS Transit Gateway (GA Sep 2024).

**3. Least-privilege inbound rules — no management-port exposure to `0.0.0.0/0`**
Restrict TCP 22 (SSH) and TCP 3389 (RDP) to a corporate CIDR or a managed prefix list. Preferred: remove those inbound rules entirely and use AWS Systems Manager Session Manager. Detect violations with AWS Config managed rules `restricted-ssh` and `restricted-common-ports`.

**4. Make every NACL stateless-aware — always add the ephemeral-port return rule**
For each inbound ALLOW on a service port, add a corresponding outbound ALLOW for ephemeral ports (1024-65535) back to the client CIDR. NACLs are stateless; omitting this rule silently breaks return traffic. Number NACL rules in increments of 10 or 100 to allow future inserts without renumbering.

**5. Enable VPC Flow Logs on all in-scope subnets or VPCs**
Flow Logs provide ACCEPT/REJECT records per ENI — the audit trail confirming SG/NACL policy matches observed traffic. Publish to CloudWatch Logs or S3; alert on unexpected REJECTs and unexpected ACCEPTs to sensitive ports.

**6. Create purpose-built SGs per tier; leave the default SG unused with no rules**
A newly created SG has no inbound rules — this is the correct least-privilege baseline. Assign descriptive names and resource tags per tier (`sg-alb-prod`, `sg-web-prod`, `sg-db-prod`). Strip all rules from the VPC default SG and do not assign it to workloads.

**7. Associate custom NACLs (deny-by-default) to every workload subnet**
The default NACL allows ALL inbound and outbound traffic. A custom NACL is deny-by-default until allow rules are added. Associate a custom NACL before placing workloads in a subnet. Verify with: `aws ec2 describe-network-acls --filters Name=association.subnet-id,Values=subnet-xxxx`.

### ⚠️ Ask First

**1. Where to enforce a block: SG (allow-only) vs NACL (allow+deny)**
Ask: "Is the requirement an explicit *deny* or an immediate connection cut — if yes, use a NACL; otherwise default to a security group."

| Option | Control | Optimizes | Sacrifices | Best When |
|--------|---------|-----------|------------|-----------|
| Security group | Per-ENI, stateful, allow-only | Precision, SG referencing, auto return traffic | Cannot express deny | Primary access control for all workloads |
| Network ACL | Per-subnet, stateless, allow+deny | Explicit DENY, subnet-wide, immediate connection cut | Stateless (return rules required), low rule quota | Blocking a specific CIDR, subnet guard rail, fast session termination |

**2. Rule quota: accept defaults vs request a quota increase**
Ask: "Can large allow-lists be collapsed into a prefix list before requesting a quota increase?"
Note: a prefix-list rule counts as its MAX entry count against the rule quota.

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| Default limits (60 SG rules/direction, 5 SGs/ENI) | Simplicity, predictable performance | May be tight for large east-west meshes | Most workloads |
| Raise SG rules or SGs/ENI (rules × SGs/ENI ≤ 1,000) | More granularity | Cap at 1,000 rules×SGs/ENI | Complex east-west meshes |
| Raise NACL rules (default 20, max ~40+40) | More explicit deny entries | Performance may be impacted beyond default | Subnets needing many discrete denies |
| Prefix list in SG/NACL rule | One update fans out to all rules | Counts as MAX list size vs rule quota | Many partner or managed CIDRs |

**3. SG centralization model: per-VPC vs SG VPC Associations vs Shared Security Groups**
Ask: "Are the VPCs in the same account, or across accounts in a shared VPC?"

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| One SG per VPC (classic) | Isolation, simplicity | Duplicated policy across VPCs | Few VPCs, low sharing |
| SG VPC Associations (Oct 2024) | Single SG reused across VPCs | Same-Region/account only; default SG excluded | Many VPCs, same account |
| Shared Security Groups (Oct 2024) | Cross-account reuse in shared VPC | Requires RAM + AWS Organizations + shared VPC | Multi-account org, shared VPC |

**4. Transit Gateway SG referencing vs CIDR-based rules**
Ask: "Does the east-west route traverse a middlebox appliance?"
SG referencing works across TGW (GA Sep 2024) — but NOT through a middlebox appliance route (use IP/CIDR there). Confirm the TGW configuration supports SG referencing before designing east-west rules on it.

### 🚫 Never Do

| Anti-pattern | Why Prohibited | Correct Alternative |
|---|---|---|
| SG inbound TCP 22/3389 from `0.0.0.0/0` | CRITICAL — exposes management ports; enables instance compromise and lateral movement | Restrict to corporate CIDR / managed prefix list, or remove 22/3389 and use SSM Session Manager |
| Use the default SG for workload ENIs | HIGH — default SG allows all traffic between its members and all outbound; violates least privilege | Create purpose-built SGs per tier; strip all rules from the default SG and leave it unused |
| Use the default NACL for workload subnets | HIGH — default NACL rule 100 allows ALL inbound and outbound; no guard-rail effect | Associate a custom (deny-by-default) NACL to every workload subnet before adding instances |
| Write NACL rules without the ephemeral return rule | HIGH — NACLs are stateless; missing return rule breaks connectivity in intermittent, hard-to-diagnose ways | For every inbound ALLOW on a service port, add outbound ALLOW TCP 1024-65535 to the client CIDR |
| All-traffic wildcard SG rule (protocol=-1, ports 0-65535, source 0.0.0.0/0) | HIGH — removes least-privilege AND creates untracked flows; sessions drop immediately on any rule edit | Scope protocol/port/source narrowly so connections are tracked and survive change windows |
| Hardcode VPC CIDR as source for intra-VPC east-west rules | Brittle — overexposes every tier to the whole CIDR; rules do not follow autoscaling instances | Use SG referencing (source = `sg-xxxx`) so rules follow instances by SG membership |

---

## Integration Patterns

**Three-tier web application (canonical pattern)**
```
ALB-SG    — inbound TCP 443/80 from 0.0.0.0/0
Web-SG    — inbound TCP 443/80 from ALB-SG (sg-alb-prod) via SG referencing
DB-SG     — inbound TCP 5432 (or 3306/1433) from Web-SG (sg-web-prod) via SG referencing
NACLs     — custom per subnet tier; coarse allow matching SG policy + explicit deny for known-bad CIDRs
Flow Logs — VPC or subnet level; alert on unexpected REJECT
Admin     — no inbound 22/3389; access via SSM Session Manager only
```

**Multi-VPC / multi-account (2024 patterns)**
- Same-account, same-Region: Use **SG VPC Associations** — one SG associated to N VPCs.
- Cross-account in shared VPC: Use **Shared Security Groups** via RAM + AWS Organizations.
- East-west across Transit Gateway: Use **SG referencing on TGW** (GA Sep 2024) — not valid through a middlebox appliance route.

**Prefix-list-driven allow-lists**
Reference a customer-managed or AWS-managed prefix list in SG/NACL rules for large sets of partner CIDRs. Update the list once; all referencing rules inherit it. Watch the quota weight: a prefix-list rule counts as the list's MAX entry count.

**Known SG/NACL filtering gaps**
Neither control filters: Amazon DNS, DHCP, EC2 instance metadata (IMDS), ECS task metadata, Windows license activation, Time Sync, or reserved VPC-router IPs. To filter DNS: use Route 53 Resolver DNS Firewall. To restrict IMDS: configure instance metadata options (`--metadata-options`).

---

## Verification Loop

Run after each SG/NACL configuration to validate the security posture:

### 1. Inventory controls
```bash
aws ec2 describe-security-groups \
  --query "SecurityGroups[*].{ID:GroupId,Name:GroupName,VPC:VpcId}"
aws ec2 describe-network-acls \
  --query "NetworkAcls[*].{ID:NetworkAclId,VPC:VpcId,Default:IsDefault}"
# Expected: every workload SG has a descriptive name; no workload subnet uses IsDefault:true NACL
```

### 2. Detect management-port exposure
```bash
aws ec2 describe-security-groups \
  --filters "Name=ip-permission.from-port,Values=22" \
            "Name=ip-permission.cidr,Values=0.0.0.0/0" \
  --query "SecurityGroups[*].GroupId"
# Expected: empty list — no SG allows SSH from 0.0.0.0/0
```

### 3. Detect stale cross-VPC rules
```bash
aws ec2 describe-stale-security-groups --vpc-id <vpc-id>
# Expected: empty StaleSecurityGroupSet
```

### 4. Confirm Flow Logs active
```bash
aws ec2 describe-flow-logs \
  --query "FlowLogs[*].{Resource:ResourceId,Status:FlowLogStatus}"
# Expected: each VPC or target subnet shows FlowLogStatus ACTIVE
```

### 5. AWS Config / Security Hub posture checks
```
AWS Config managed rules: restricted-ssh, restricted-common-ports, vpc-flow-logs-enabled
Security Hub control: EC2.2 (SG must not allow unrestricted access to high-risk ports)
# Expected: all COMPLIANT
```

**Troubleshooting**:
- Return-traffic failures on NACL subnets → Missing ephemeral-port outbound rule (TCP 1024-65535 to client CIDR).
- Sessions dropping on SG rule edit → All-traffic wildcard rule creating untracked flows; narrow the rule scope.
- Nitro v6 DB connection drops after ~6 min → TCP established timeout is now 350s; enable TCP keepalive or set `TcpEstablishedTimeout` at instance launch.
- SG rule quota exceeded → Collapse CIDRs into a prefix list; request quota increase (rules × SGs/ENI ≤ 1,000).

---

## Quick Reference

**Essential CLI commands**:
```bash
# Inspect SG rules
aws ec2 describe-security-group-rules --filter "Name=group-id,Values=sg-xxxx"

# Check NACL rules for a subnet
aws ec2 describe-network-acls --filters "Name=association.subnet-id,Values=subnet-xxxx"

# Check SG VPC Associations (2024)
aws ec2 describe-security-group-vpc-associations --security-group-id sg-xxxx

# Enable VPC Flow Logs
aws ec2 create-flow-logs --resource-type VPC --resource-ids vpc-xxxx \
  --traffic-type ALL --log-destination-type cloud-watch-logs \
  --log-group-name /aws/vpc/flowlogs --deliver-logs-permission-arn <role-arn>
```

**Critical quotas (per Region/account, defaults)**:

| Resource | Default | Adjustable |
|----------|---------|------------|
| Security groups per Region | 2,500 | Yes |
| Inbound OR outbound rules per SG | 60 (per direction, per IP version) | Yes |
| Security groups per ENI | 5 | Yes (max 16; rules × SGs/ENI ≤ 1,000) |
| Network ACLs per VPC | 200 | Yes |
| Rules per NACL (inbound or outbound) | 20 | Yes (max ~40+40; may impact performance) |
| NACL rule number range | 1-32766 | N/A |

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/securing-vpc-network-access/
├── SKILL.md                          ← This file (guardrails + patterns)
└── blueprints/
    └── evaluation-scenarios.md       ← 6 test cases for skill-evaluator
```

---

## External Resources

### Official Documentation (all accessed 2026-08-26)
- [VPC User Guide — Control traffic using security groups](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html)
- [VPC User Guide — Security group rules (components, referencing, size, stale rules)](https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html)
- [VPC User Guide — Network ACLs](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-network-acls.html)
- [VPC User Guide — SG VPC Associations (2024)](https://docs.aws.amazon.com/vpc/latest/userguide/security-group-assoc.html)
- [VPC User Guide — Infrastructure Security / SG vs NACL comparison](https://docs.aws.amazon.com/vpc/latest/userguide/infrastructure-security.html)
- [EC2 User Guide — SG Connection Tracking (stateful, untracked, Nitro v6)](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/security-group-connection-tracking.html)
- [VPC User Guide — Ephemeral Ports / NACL Examples](https://docs.aws.amazon.com/vpc/latest/userguide/nacl-examples.html)
- [VPC User Guide — Amazon VPC Quotas](https://docs.aws.amazon.com/vpc/latest/userguide/amazon-vpc-limits.html)

### Security & Best Practices
- [AWS Well-Architected Security Pillar — SEC05 Protect Networks](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-networks.html) — accessed 2026-08-26
- [AWS What's New — SG Sharing Features GA (Oct 2024)](https://aws.amazon.com/about-aws/whats-new/2024/10/amazon-virtual-private-cloud-security-group-sharing/) — verify currency before 2027-08-26
- [AWS What's New — TGW SG Referencing GA (Sep 2024)](https://aws.amazon.com/about-aws/whats-new/2024/09/general-availability-security-group-referencing-aws-transit-gateway) — verify currency before 2027-08-26
