# Ask-First Decisions — AWS VPC Security Groups (2025)

Source: AWS VPC User Guide + Well-Architected Security Pillar. All accessed 2026-07-31.

Confirm the driving factors for each decision before committing to an approach.

---

## C1 — Security Groups vs. Network ACLs (or both)

**Decision**: Which control layer(s) to use for a given workload?

| Factor | Security Group | Network ACL | Use both |
|---|---|---|---|
| Enforcement level | Per-resource / ENI (instance) | Per-subnet | Layered (defense-in-depth) |
| Statefulness | Stateful — return traffic auto-allowed | Stateless — must allow both directions + ephemeral ports | — |
| Rule semantics | Allow-only (no deny possible) | Allow **and** Deny | — |
| Primary use | Primary network access control for workloads | Coarse-grained subnet guard rail; only place to explicitly *deny* a CIDR | Production environments with compliance requirements |

**AWS guidance**: "Use security groups as the primary mechanism. When necessary, use network ACLs
to provide stateless, coarse-grain network control. Network ACLs can be effective as a secondary
control (for example, to deny a specific subset of traffic) or as high-level subnet guard rails."

**Ask before deciding**:
- Does the workload need to *deny* a specific source CIDR? (If yes: NACL required — SG cannot deny.)
- Is there a regulatory requirement for defense-in-depth network controls? (If yes: use both.)
- Is operational simplicity the primary constraint? (If yes: SG only is acceptable.)

**Source**: [Infrastructure security in Amazon VPC — Compare security groups and network ACLs](https://docs.aws.amazon.com/vpc/latest/userguide/infrastructure-security.html) — accessed 2026-07-31.

---

## C2 — Rule capacity: rules-per-SG vs. SGs-per-ENI (the 1,000 product limit)

**Decision**: How to allocate the 1,000-rule product budget across groups and interfaces?

Default quotas:
- 60 inbound rules per SG (enforced separately for IPv4 and IPv6)
- 60 outbound rules per SG
- 5 SGs per network interface

The product `rules-per-SG × SGs-per-ENI` cannot exceed 1,000.

| Approach | Config | Effective rules per ENI | When |
|---|---|---|---|
| Few large SGs | 200 rules/SG × 5 SGs | 1,000 | Consolidated; fewer objects to manage |
| Many small SGs | 62 rules/SG × 16 SGs | ~992 | Fine-grained functional grouping; requires quota increase for SGs-per-ENI |
| Hybrid | 100 rules/SG × 10 SGs | 1,000 | Moderate segmentation with some consolidation |

**Prefix-list cost caveat**: A rule referencing a customer-managed prefix list counts as the
*maximum size* of that list (e.g., a max-size-20 list = 20 rule slots). An AWS-managed prefix
list counts as its published weight. Plan quota usage before adding prefix-list rules.

**Ask before deciding**:
- How many distinct trust relationships (source→destination pairs) does the architecture require?
- Does the design use customer-managed prefix lists? What are their max sizes?
- Is the 5 SGs-per-ENI default sufficient, or will a quota increase be needed?

**Note**: Request a quota increase *before* designing an architecture that depends on it — quota
approvals are not guaranteed.

**Source**: [Amazon VPC quotas — Security groups](https://docs.aws.amazon.com/vpc/latest/userguide/amazon-vpc-limits.html); [Security group rules — Security group size](https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html) — accessed 2026-07-31.

---

## C3 — SG referencing vs. CIDR / prefix list as rule source

**Decision**: For a given inbound rule, should the source be a security group ID, a CIDR block, or a managed prefix list?

| Option | Pros | Cons / limits | Use when |
|---|---|---|---|
| **Reference peer SG** (`sg-…`) | Membership-based; survives IP churn; scales with Auto Scaling; counts as 1 rule regardless of member count | Valid only within the same VPC, or across VPC peering / Transit Gateway; **fails silently for middlebox-routed traffic** | Same-VPC tiered applications (preferred default) |
| **CIDR block** | Works across any boundary; required for middlebox-routed flows | IP-brittle; overly broad CIDRs over-expose the resource | On-premises connectivity; cross-boundary flows; middlebox-routed traffic |
| **Managed prefix list** (`pl-…`) | Reusable, centrally managed set of CIDRs; reduces rule count | Consumes rule slots equal to the list's max size / weight | Stable set of external CIDRs (e.g., corporate office ranges) |

**Critical middlebox caveat** (from AWS documentation):
> "If you configure routes to forward the traffic between two instances in different subnets through
> a middlebox appliance... The security group for each instance must reference the private IP address
> of the other instance or the CIDR range of the subnet... If you reference the security group of
> the other instance as the source, this does not allow traffic to flow between the instances."

**Ask before deciding**:
- Is there a network appliance (firewall, IDS/IPS, NAT gateway, custom routing) between the two instances? (If yes: CIDR required.)
- Are the instances in the same VPC or across a peering/Transit Gateway connection?
- How many CIDRs are in the source set? (If many and stable: managed prefix list.)

**Source**: [Security group rules — Security group referencing (limitation)](https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html) — accessed 2026-07-31.

---

## C4 — Default allow-all egress vs. explicit egress restriction

**Decision**: Should outbound traffic from the resource be restricted to specific destinations?

Default behavior: every new security group has one outbound rule — `Allow All` to `0.0.0.0/0`. You
can remove this rule and replace it with specific egress rules.

| Approach | When appropriate | Considerations |
|---|---|---|
| **Keep default allow-all egress** | Internal workloads, simple services, development environments | Simplest; lowest operational overhead; acceptable risk for many workloads |
| **Lock down egress to specific destinations** | Data-exfiltration-sensitive workloads, regulated environments (PCI-DSS, HIPAA), Zero Trust architecture | Instance can only reach declared endpoints; remember: *stateful* — no egress rule needed for response traffic to allowed inbound |

**Statefulness reminder**: Locking down egress does NOT affect return traffic for *inbound-allowed*
connections. Egress rules only govern connections *initiated by the instance*. Example: if inbound
HTTPS is allowed, responses leave automatically — no outbound TCP/443 rule required.

**Ask before deciding**:
- Does the instance initiate outbound connections (package updates, third-party API calls, S3 access)? If yes, explicit egress rules are needed for each destination.
- Is the workload subject to data-exfiltration compliance requirements?
- Will egress restriction be applied to a shared platform used by multiple teams? (Coordinate first — unexpected lock-down breaks other teams.)

**Source**: [Security group rules — Security group rule basics](https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html); [Security group basics (statefulness)](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html) — accessed 2026-07-31.

---

## C5 — Sharing / associating security groups across VPCs

**Decision**: How to share or reference security groups across a multi-VPC or multi-account topology?

| Option | Mechanism | Scope | Notes |
|---|---|---|---|
| **Security Group VPC Association** | Associate an existing SG to additional VPCs in the same Region | Same Region, multiple VPCs | Simplest for same-Region topologies |
| **AWS Organizations sharing** | Share SGs across accounts using AWS Resource Access Manager | Cross-account, same or cross-Region | Governance via Organizations; owner retains control |
| **VPC peering / Transit Gateway reference** | Reference a SG in a peered VPC as the rule source | Cross-VPC within Region | Introduces risk of **stale rules** (see below) |

**Stale rules**: "If you have a security group rule that references a security group in a peer VPC
or shared VPC, the rule is marked as stale when the referenced security group is deleted or the VPC
peering connection is deleted." Stale rules do not block traffic (they become no-ops), but they
represent dead configuration and create audit noise.

**Cross-account CloudTrail gap**: "When a referenced security group is owned by another account,
the owner account does not receive CloudTrail events" for authorize/revoke actions on that reference.
Plan your audit trail accordingly.

**Ask before deciding**:
- Is the topology same-Region (Security Group VPC Association is available) or cross-Region (requires peering/TGW)?
- Is there an automated process to detect and remove stale rules after peering deletion?
- Who owns the security groups — the consuming account or a central platform account? (Determines the CloudTrail audit gap.)

**Source**: [Control traffic using security groups (Security Group VPC Association, sharing)](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html); [Security group rules — Stale security group rules & Security group referencing](https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html) — accessed 2026-07-31.
