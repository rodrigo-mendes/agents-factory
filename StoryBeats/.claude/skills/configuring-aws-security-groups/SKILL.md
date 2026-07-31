---
name: configuring-aws-security-groups
description: "Configures AWS VPC Security Groups for production workloads using defense-in-depth and least-privilege patterns (AWS VPC 2025, docs accessed 2026-07-31). Use when designing or reviewing VPC network access controls, security group rules, NACL defense-in-depth layering, quota planning, or egress restriction strategies."
---

## Function
Specialist in AWS VPC Security Groups — rule design, tier-to-tier segmentation via SG referencing, NACL defense-in-depth layering, quota capacity planning, and Well-Architected SEC05 compliance for production workloads.

## Version Context

**Technology**: AWS VPC Security Groups
**Target version**: AWS VPC 2025 (continuously delivered; docs channel: `docs.aws.amazon.com/vpc/latest/`)
**Research date**: 2026-07-31
**Support status**: Active (no deprecation; continuously updated)

**Core behavioral properties**:
- **Stateful** — return traffic for an allowed flow is automatically permitted; no egress rule is needed for responses to allowed inbound
- **Allow-only** — explicit deny is impossible in a security group; that role belongs exclusively to network ACLs
- **Default inbound**: none (fail-closed on creation)
- **Default outbound**: allow all (explicit egress rule exists on creation; removable)
- Rule changes propagate immediately to all attached resources

**Hard interaction limit (non-adjustable)**: `rules-per-SG × SGs-per-ENI ≤ 1,000`

> CRITICAL — Agent Warning: This skill targets AWS VPC Security Groups as documented 2026-07-31.
> Reject any pattern that describes security groups as stateless, claims SGs support deny rules,
> or treats NACLs as the primary control. These are incorrect for AWS.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — 7 mandatory patterns with config examples (A1–A7)
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — 5 architectural crossroads with decision matrices (C1–C5)
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — 6 anti-patterns with wrong/correct examples (N1–N6)
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 3 test cases (canonical, edge, misuse)
- **[Verification Loop](#verification-loop)** — AWS CLI validation commands with expected output
- **[Quick Reference](#quick-reference)** — Quota table at a glance
- **[External Resources](#external-resources)** — Official AWS documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

For full configuration examples, see [Always Do Patterns](./blueprints/always-do-patterns.md).

- **A1 — Restrict management ports to specific CIDRs** — SSH (22) and RDP (3389) must never use `0.0.0.0/0` as source. Use a bastion CIDR, corporate egress range, or a managed prefix list. Preferred: eliminate inbound SSH entirely using AWS Systems Manager Session Manager.
- **A2 — Use SG referencing for tier-to-tier traffic** — Use the peer security group ID (`sg-…`) as the source/destination for ALB→web, web→app, and app→DB flows. Ties access to group membership, not IP addresses; survives instance replacement and Auto Scaling.
- **A3 — Create the minimum number of groups, one per functional role** — Load balancer, web tier, app tier, and data tier each get a dedicated security group. Avoid multi-purpose catch-all groups that accumulate unrelated rules.
- **A4 — Never open large port ranges** — Each rule must specify the exact single port required. Ranges like `0–65535` or `1024–65535` are prohibited; scope every rule to the single port (or protocol) the flow actually requires.
- **A5 — Restrict SG create/modify to specific IAM principals** — Enforce change control via IAM policies and SCPs; aligns with Well-Architected SEC05-BP04. Use separate security groups or network interfaces for management traffic to enable distinct IAM change-control policies.
- **A6 — Add NACLs as a defense-in-depth layer for production subnets** — Create NACL rules that mirror security group intent. NACLs are the only control that applies if an instance is accidentally launched without the correct security group attached.
- **A7 — Enable VPC Flow Logs** — Publish to CloudWatch Logs or Amazon S3. Flow logs are the primary mechanism to validate that rules are neither over-permissive nor overly restrictive, and to support incident response.

### ⚠️ Ask First

For full decision matrices and tradeoff tables, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

- **C1 — Security Group vs. NACL (or both)** — Security groups are the primary control (stateful, per-resource). NACLs provide subnet-wide coarse-grained protection and are the *only* mechanism for explicit deny. Confirm: does the workload need to deny a specific CIDR? Are there compliance requirements for defense-in-depth?
- **C2 — Rule capacity planning** — Defaults are 60 inbound rules + 60 outbound rules per SG, and 5 SGs per ENI. The product cannot exceed 1,000. Prefix-list rules consume slots equal to the list's max size. Before designing to raised quotas, confirm the number of distinct trust relationships and prefix-list sizes.
- **C3 — SG referencing vs. CIDR/prefix list as rule source** — SG referencing is preferred for same-VPC tiered flows. CIDR or prefix list is required for on-premises access, cross-boundary flows, and — critically — for any traffic that passes through a middlebox appliance (see N3).
- **C4 — Default allow-all egress vs. explicit egress restriction** — Keep the default for simple internal workloads. Lock down egress for data-exfiltration-sensitive or regulated workloads. Remember: egress rules govern only instance-*initiated* outbound; stateful return traffic for allowed inbound does not need an egress rule.
- **C5 — Cross-VPC SG sharing or association** — Options: Security Group VPC Association (same-Region), AWS Organizations sharing, or VPC peering/Transit Gateway references. Confirm: is there a process to detect and remove stale rules after peering deletion? Note: cross-account SG references do not generate CloudTrail events on the owner account.

### 🚫 Never Do

For wrong/correct examples side-by-side, see [Never Do Patterns](./blueprints/never-do-patterns.md).

- **N1 — SSH/RDP open to `0.0.0.0/0`** — Single most common EC2 compromise vector; exposes the instance to internet-wide brute force. Use a specific CIDR or managed prefix list, or replace inbound SSH with Systems Manager Session Manager.
- **N2 — CIDR-based rules for intra-VPC tier-to-tier flows** — Hard-coding the VPC CIDR (`10.0.0.0/16`) for app→DB traffic over-exposes the database to every host in the range. Use SG referencing (`sg-web` as source on the DB security group).
- **N3 — SG referencing when traffic routes through a middlebox** — If a firewall appliance sits in the path between two instances, referencing the peer's security group will silently fail. Use the subnet CIDR of the peer instance instead.
- **N4 — SG rules to filter Route 53 Resolver DNS or EC2 Instance Metadata (IMDS)** — Security groups cannot block VPC+2 DNS queries or IMDS traffic (`169.254.169.254`). NACLs have the same limitation for IMDS. Use Route 53 Resolver DNS Firewall for DNS and EC2 instance metadata options (enforce IMDSv2) for IMDS.
- **N5 — Adding ephemeral-return egress rules or expecting SG deny** — Security groups are stateful; return traffic is auto-allowed. Redundant "return" egress rules are noise. Attempting a deny in a security group has no effect — use a NACL deny rule instead.
- **N6 — Naming a security group with the `sg-` prefix** — AWS rejects `CreateSecurityGroup` calls where the name starts with `sg-`. Convention: `<function>-sg` (e.g., `web-tier-sg`, `db-tier-sg`).

---

## Integration Patterns

- **SG ↔ Amazon EC2** — Attach at instance launch or via `ModifyNetworkInterfaceAttribute`; rule changes propagate immediately to all attached ENIs without instance restart.
- **SG ↔ Amazon RDS** — RDS uses the same ENI-based SG model as EC2; the DB-tier inbound rule references the application-tier SG ID (`sg-app-tier`).
- **SG ↔ Application Load Balancer** — Create a dedicated ALB SG; web-tier instances restrict inbound to `sg-alb` only (not to `0.0.0.0/0`).
- **SG ↔ AWS Lambda (VPC-attached)** — Lambda functions in a VPC receive an ENI; apply the same functional-grouping principle.
- **SG ↔ Network ACL** — SGs and NACLs coexist; inbound traffic must pass both. SG = per-ENI stateful allow; NACL = per-subnet stateless allow+deny with numbered rules (1–32766).

**Common problems**:
- Connectivity failure after adding middlebox appliance → Rule uses SG reference; replace with subnet CIDR source (N3).
- `CreateSecurityGroup` API call fails in IaC → Name starts with `sg-`; rename (N6).
- Quota exhaustion error → Review `rules-per-SG × SGs-per-ENI`; consolidate into prefix lists or reduce SG count per ENI (C2).
- Stale-rule warning in peered VPC → Remove the stale reference; establish automated detection via AWS Config rule.

---

## Verification Loop

Run after each security group create or modify operation.

### 1. Audit for management ports open to the internet
```bash
# Find SG inbound rules allowing SSH from the internet (IPv4)
aws ec2 describe-security-groups \
  --filters "Name=ip-permission.from-port,Values=22" \
             "Name=ip-permission.cidr,Values=0.0.0.0/0" \
  --query 'SecurityGroups[*].{ID:GroupId,Name:GroupName}' \
  --output table
# Expected: empty result set
```

### 2. Confirm VPC Flow Logs are active
```bash
aws ec2 describe-flow-logs \
  --filter "Name=resource-id,Values=<vpc-id>" \
  --query 'FlowLogs[*].{Status:FlowLogStatus,Dest:LogDestination}' \
  --output table
# Expected: at least one row with Status=ACTIVE
```

### 3. Validate the rules × groups product for an ENI
```bash
# List SGs attached to an ENI
aws ec2 describe-network-interfaces \
  --filters "Name=network-interface-id,Values=<eni-id>" \
  --query 'NetworkInterfaces[0].Groups[*].GroupId' \
  --output text
# For each SG ID returned, count rules:
aws ec2 describe-security-groups --group-ids <sg-id> \
  --query 'SecurityGroups[0].{Inbound:length(IpPermissions),Outbound:length(IpPermissionsEgress)}'
# Verify: sum(rules_per_SG) × count(SGs_per_ENI) ≤ 1,000
```

**Troubleshooting**:
- SSH open to `0.0.0.0/0` detected → Replace source with a managed prefix list or corporate CIDR; evaluate eliminating inbound SSH via Systems Manager Session Manager.
- Flow logs not ACTIVE → `aws ec2 create-flow-logs --resource-ids <vpc-id> --resource-type VPC --traffic-type ALL --log-destination-type cloud-watch-logs --log-group-name /vpc/flow-logs`
- Product near or at 1,000 → Consolidate CIDR rules into customer-managed prefix lists; reduce SG count per ENI by merging groups with the same trust boundary.

---

## Quick Reference

**Default quotas — all adjustable via AWS Service Quotas unless noted**:

| Resource | Default | Max (if adjustable) | Notes |
|---|---|---|---|
| Security groups per Region | 2,500 | Yes | Paginate `Describe` calls beyond 5,000 |
| Inbound rules per SG | 60 | Yes | Enforced separately for IPv4 and IPv6 |
| Outbound rules per SG | 60 | Yes | Enforced separately for IPv4 and IPv6 |
| SGs per network interface | 5 | 16 | — |
| **Rules × SGs product per ENI** | — | **1,000 (hard, not adjustable)** | Raising one lever forces the other down |
| Customer-managed prefix list slot cost | = max size | — | max-20 list = 20 rule slots |
| NACLs per VPC | 200 | Yes | One NACL can attach to many subnets |
| Rules per NACL | 20 | 40 in + 40 out | Numbered 1–32766, evaluated ascending |

**Naming constraint**: SG names must not start with `sg-` and must be unique within the VPC (≤ 255 chars).
**Naming convention**: `<function>-sg` (e.g., `web-tier-sg`, `db-tier-sg`, `alb-sg`).

Source: Amazon VPC quotas — accessed 2026-07-31.

---

## Blueprints Directory Structure

```
.claude/skills/configuring-aws-security-groups/
├── SKILL.md                              ← This file (summary + guardrails)
└── blueprints/
    ├── always-do-patterns.md             ← A1–A7 with full config examples
    ├── ask-first-decisions.md            ← C1–C5 decision matrices and tradeoff tables
    ├── never-do-patterns.md              ← N1–N6 wrong/correct side-by-sides
    └── evaluation-scenarios.md           ← 3 test scenarios (canonical, edge, misuse)
```

---

## External Resources

### Official AWS Documentation (all accessed 2026-07-31)

- [Control traffic using security groups](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html) — Definition, statefulness, best practices, naming constraints
- [Security group rules](https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html) — Rule components, allow-only model, SG referencing, quota/size, stale rules, Route 53 Resolver limitation
- [Infrastructure security in Amazon VPC](https://docs.aws.amazon.com/vpc/latest/userguide/infrastructure-security.html) — SG vs. NACL comparison; control-network-traffic primary guidance
- [Network ACLs](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-network-acls.html) — Stateless behavior, rule numbering 1–32766, IMDS/DNS limitations
- [Amazon VPC quotas](https://docs.aws.amazon.com/vpc/latest/userguide/amazon-vpc-limits.html) — All SG and NACL default limits; the 1,000 product constraint
- [Well-Architected SEC05: Protecting networks](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-networks.html) — SEC05-BP01–BP04 (Zero Trust, network layers, inspection, automation)
- [Well-Architected Infrastructure Protection](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/infrastructure-protection.html) — Defense-in-depth, trust boundaries
