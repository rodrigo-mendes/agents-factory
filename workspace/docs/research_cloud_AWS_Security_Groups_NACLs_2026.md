# AWS Networking Architecture — Security Groups & Network ACLs

## Metadata
```yaml
Full_Name: "AWS Networking Architecture - Security Groups & NACLs"
Cloud_Provider: "AWS"
Architecture_Domain: "Networking Architecture - Security Groups & NACLs"
Target_Edition: "AWS Security Groups 2026 (Amazon VPC User Guide, accessed 2026-08-26)"
Architecture_Context: "General-purpose VPC network segmentation for production workloads (not scoped to a single vertical)"
Official_Source_URL: "https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-08-26"
Currency_Threshold: "2027-08-26 — re-verify against the Amazon VPC User Guide after this date"
Research_Depth: "exhaustive"
Max_Iterations: 5
```

> **Scope note:** `ARCHITECTURE_CONTEXT` was not supplied in the invocation. This research is written
> for general-purpose VPC segmentation. Where a decision depends on workload vertical (e.g.,
> regulated finance, multi-tenant SaaS), the ⚠️ Ask-First section flags it explicitly.

---

## Executive Summary

**Security groups** and **network ACLs (NACLs)** are the two native, complementary packet-filtering
controls inside an Amazon VPC. A **security group** operates at the **elastic network interface
(instance) level**, is **stateful** (return traffic is automatically allowed via connection
tracking), supports **allow rules only**, and **evaluates all rules** before deciding to allow
traffic. A **network ACL** operates at the **subnet level**, is **stateless** (return traffic must be
explicitly allowed), supports **both allow and deny rules**, and **evaluates rules in ascending
numeric order until a match is found**. AWS positions security groups as *the primary mechanism for
controlling network access*, with NACLs as a *stateless, coarse-grain secondary control* and
defense-in-depth backstop [1][6].

**What is current in the 2026 edition.** Two governance features have moved the operating model
beyond the classic "one SG per VPC" constraint: **Security Group VPC Associations** (associate a
single security group with multiple VPCs in the same Region and account) and **Shared Security
Groups** (share a security group across AWS Organizations accounts in a shared VPC), both announced
Oct 2024 and now GA across commercial, GovCloud (US), and China Regions [4][7]. Also current:
**Security Group Referencing on AWS Transit Gateway** (GA Sep 2024), which lets an SG rule reference
another SG across a transit gateway, not only within a VPC or across a peering connection [8][2].
Connection-tracking defaults changed on **Nitro v6** instances — the idle **TCP established timeout
dropped to 350 seconds** (from 432000s on prior generations), a breaking operational change for
long-lived connections [5].

**Three most critical guardrails.** (1) Never expose management ports (SSH 22 / RDP 3389) to
`0.0.0.0/0` — restrict to specific CIDRs or, better, use SSM Session Manager [1]. (2) Prefer
**security-group referencing** over hardcoded CIDRs for intra-VPC service-to-service traffic so rules
follow instances as they scale [2]. (3) Layer NACLs beneath security groups as a subnet guard rail so
that a misconfigured or missing SG cannot silently expose an instance — this is the AWS-recommended
defense-in-depth posture [1][6], triangulated by Well-Architected SEC05-BP01/BP02 [10].

---

## Cloud Architecture Glossary

```
Term: Security group
Definition: A virtual firewall that controls the traffic allowed to reach and leave the resources
  it is associated with; operates at the network-interface level and is stateful.
Provider Docs Section: VPC User Guide — "Control traffic to your AWS resources using security groups"
Architect Usage: Attach to ENIs/instances/managed-service endpoints as the primary access control.
Common Confusion: Confused with NACLs (subnet-level, stateless) and with Azure NSGs (which can also
  carry deny rules — AWS security groups cannot).
Source: [1]
```
```
Term: Network ACL (NACL)
Definition: A stateless allow/deny filter evaluated at the subnet boundary when traffic enters or
  leaves the subnet (not when routed within a subnet).
Provider Docs Section: VPC User Guide — "Control subnet traffic with network access control lists"
Architect Usage: Use as a coarse-grain, subnet-wide secondary control and defense-in-depth backstop.
Common Confusion: Assumed stateful like a security group — it is not; return traffic needs an
  explicit rule using ephemeral port ranges.
Source: [6]
```
```
Term: Stateful (connection tracking)
Definition: Security groups track connection state so responses to allowed traffic are permitted
  regardless of the rules in the opposite direction.
Provider Docs Section: EC2 User Guide — "Amazon EC2 security group connection tracking"
Architect Usage: You do not write return-traffic rules for security groups.
Common Confusion: Assuming ALL flows are tracked — "untracked" flows (all-traffic 0.0.0.0/0 both
  directions) are not, and are interrupted immediately on rule change.
Source: [5]
```
```
Term: Stateless
Definition: NACLs do not retain information about prior traffic; each packet is evaluated
  independently against inbound and outbound rules.
Provider Docs Section: VPC User Guide — "Network ACL basics"
Architect Usage: You MUST add explicit outbound rules for return traffic (ephemeral ports).
Common Confusion: Forgetting the ephemeral-port return rule, which silently breaks connections.
Source: [6]
```
```
Term: Ephemeral ports
Definition: The high-numbered source ports a client uses for the return leg of a connection; NACL
  outbound (or inbound for responses) rules must allow this range because NACLs are stateless.
Provider Docs Section: VPC User Guide — "Example: Control access to instances in a subnet"
Architect Usage: Allow 1024-65535 for return traffic; exact range varies by client OS / NAT gateway.
Common Confusion: Using the service port (e.g., 443) for the return rule instead of the ephemeral range.
Source: [9]
```
```
Term: Security group referencing
Definition: Specifying a security group ID as the source/destination of a rule, so the rule applies
  to all instances associated with the referenced SG via their private IPs.
Provider Docs Section: VPC User Guide — "Security group rules > Security group referencing"
Architect Usage: The idiomatic way to allow tier-to-tier traffic (ALB SG -> web SG -> db SG).
Common Confusion: Believing referenced-SG rules are copied in — they are not; only the reference
  is stored, and no rules from the referenced group are added.
Source: [2]
```
```
Term: Default security group
Definition: The SG that every VPC ships with; it allows all traffic between resources assigned to
  it and allows all outbound traffic. It cannot be deleted or associated across VPCs.
Provider Docs Section: VPC User Guide — "Default security groups"
Architect Usage: Do not use it for workloads — create purpose-built SGs and strip the default.
Common Confusion: Assuming a new SG behaves like the default (a NEW SG has no inbound rules).
Source: [1][7]
```
```
Term: Default network ACL
Definition: The NACL every VPC ships with; configured to ALLOW all inbound and outbound traffic
  (rule 100 ALLOW, rule * DENY). Custom NACLs instead DENY all until you add allow rules.
Provider Docs Section: VPC User Guide — "Default network ACL for a VPC"
Architect Usage: Understand that a custom NACL is deny-by-default; a default NACL is allow-by-default.
Common Confusion: Expecting a newly created custom NACL to allow traffic like the default one does.
Source: [3]
```
```
Term: Security Group VPC Association
Definition: A 2024 feature to associate one security group with multiple VPCs in the same Region
  and account, centralizing SG management.
Provider Docs Section: VPC User Guide — "Associate security groups with multiple VPCs"
Architect Usage: Manage shared network policy once; the default SG cannot be associated this way.
Common Confusion: Confusing it with VPC peering SG referencing — association makes the SG usable
  in another VPC; referencing allows traffic between SGs.
Source: [7]
```
```
Term: Untracked connection
Definition: A flow that security-group connection tracking does not track because an all-traffic
  (0.0.0.0/0, ports 0-65535) rule exists in both directions.
Provider Docs Section: EC2 User Guide — "Untracked connections"
Architect Usage: Be aware such flows drop immediately when the enabling rule is changed/removed.
Common Confusion: Assuming existing sessions survive an SG edit — untracked ones do not.
Source: [5]
```
```
Term: Stale security group rule
Definition: A rule referencing an SG in a peer/shared VPC that becomes invalid when the referenced
  SG or the peering connection is deleted.
Provider Docs Section: VPC User Guide — "Stale security group rules"
Architect Usage: Audit and delete stale rules; they indicate broken cross-VPC references.
Common Confusion: Treating stale rules as active controls.
Source: [2]
```
```
Term: Prefix list (managed)
Definition: A named set of CIDR blocks (customer-managed or AWS-managed) referenced by SG/NACL/route
  rules; a customer-managed list counts as its MAXIMUM size against rule quotas.
Provider Docs Section: VPC User Guide — "Managed prefix lists" / "Security group size"
Architect Usage: Reference a prefix list to fan out one rule to many CIDRs; watch the quota weight.
Common Confusion: Assuming a prefix-list rule counts as one rule — it counts as its max entries/weight.
Source: [2]
```

---

## Architecture Guardrails

### ✅ Mandatory Patterns

**Use security groups as the primary control; NACLs as the secondary/defense-in-depth layer**
- Pillar Alignment: Security (SEC05 — Protect networks)
- Why: AWS states: "Use security groups as the primary mechanism for controlling network access to
  your VPCs. When necessary, use network ACLs to provide stateless, coarse-grain network control...
  because network ACLs apply to an entire subnet, they can be used as defense-in-depth in case an
  instance is ever launched without the correct security group." [1]
- AWS Services: Security groups (per-ENI), Network ACLs (per-subnet)
- Architecture Decision: Attach purpose-built SGs to every workload ENI; associate a custom NACL
  per subnet tier that mirrors the coarse allow policy and denies known-bad ranges.
- Verification: `aws ec2 describe-security-groups`, `aws ec2 describe-network-acls`; AWS Security Hub
  CSPM checks for unintended network accessibility [1].
- Source: [1][6]; triangulated by Well-Architected SEC05-BP01 "Create network layers" and SEC05-BP02
  "Control traffic flow within your network layers" [10].
  `[✓✓ Triangulated | VPC User Guide infrastructure-security [1] + WAF Security Pillar SEC05 [10]]`

**Reference security groups instead of CIDRs for tier-to-tier (east-west) traffic**
- Pillar Alignment: Security + Operational Excellence
- Why: "When you specify a security group as the source or destination for a rule, the rule affects
  all instances that are associated with the security groups... using the private IP addresses" [2].
  Rules follow instances as they scale, eliminating brittle IP allow-lists.
- AWS Services: Security groups (referencing), works within a VPC, across VPC peering, and — since
  Sep 2024 GA — across AWS Transit Gateway [2][8].
- Architecture Decision: ALB-SG allows 443 from `0.0.0.0/0`; web-SG allows 443 from ALB-SG; db-SG
  allows 5432 from web-SG. No hardcoded instance IPs.
- Verification: Inspect rule sources for `sg-` IDs rather than CIDRs; confirm no stale rules
  (`aws ec2 describe-stale-security-groups`).
- Trade-offs: SG referencing does NOT work through a middlebox appliance route — there you must use
  the peer's private IP or subnet CIDR as source [2].
- Source: [2][8]
  `[✓✓ Triangulated | VPC User Guide SG referencing [2] + What's New TGW SG referencing GA [8]]`

**Least-privilege inbound rules — no wildcard management-port exposure**
- Pillar Alignment: Security
- Why: AWS best practice: "When you add inbound rules for ports 22 (SSH) or 3389 (RDP)... authorize
  only specific IP address ranges. If you specify 0.0.0.0/0... this enables anyone to access your
  instances from any IP address" and "Do not open large port ranges." [1]
- AWS Services: Security groups; prefer AWS Systems Manager Session Manager to remove inbound 22/3389
  entirely.
- Architecture Decision: Scope admin ports to a corporate CIDR / prefix list, or eliminate them via
  SSM. Keep the minimum number of SGs, grouping resources of similar function [1].
- Verification: Grep rules for `0.0.0.0/0` on ports 22/3389; AWS Config managed rules
  `restricted-ssh`, `restricted-common-ports`.
- Source: [1]

**Make NACLs explicit and stateless-aware — always add the ephemeral-port return rule**
- Pillar Alignment: Security + Reliability
- Why: "Network ACLs are stateless. Therefore, you must include a rule that allows responses to the
  inbound traffic." [9] Missing this silently breaks connectivity.
- AWS Services: Network ACLs
- Architecture Decision: For each inbound allow, add an outbound rule permitting the ephemeral range
  (1024-65535) to the appropriate destination; number rules in increments (10/100) to allow inserts [6][9].
- Verification: Confirm every service-port inbound rule has a matching ephemeral outbound rule.
- Trade-offs: Ephemeral ranges are broad (1024-65535), reducing the precision NACLs can offer for
  return traffic — one reason SGs are preferred as the primary control [9].
- Source: [6][9]

**Enable VPC Flow Logs on subnets/ENIs carrying these controls**
- Pillar Alignment: Operational Excellence + Security
- Why: AWS: "Use VPC Flow Logs to monitor the traffic that reaches your instances." [1] Flow Logs are
  the audit trail for whether SG/NACL policy matches reality (ACCEPT/REJECT records).
- AWS Services: VPC Flow Logs -> CloudWatch Logs or S3; analyze with Athena / CloudWatch Logs Insights.
- Architecture Decision: Capture at VPC or subnet level; alert on unexpected REJECTs and on
  unexpected ACCEPTs to sensitive ports.
- Verification: `aws ec2 describe-flow-logs` returns an active log for each in-scope resource.
- Source: [1]

### ⚠️ Architectural Decisions

**Where to enforce a given block: security group vs network ACL**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Security group (per-ENI, stateful, allow-only) | Security groups | Precision, auto return traffic, SG referencing, scales with instances | Cannot express deny; can't block a subnet-wide bad actor coarsely | Primary control for all workload access |
  | Network ACL (per-subnet, stateless, allow+deny) | Network ACLs | Explicit DENY, subnet-wide guard rail, breaks existing connections immediately | Stateless (needs return rules), coarse, low rule quota (20 default) | Denying a specific CIDR, subnet guard rail, immediate connection cut |

- Cost Profile: Both are free — "There is no additional charge for using security groups" [1] and
  "There is no additional charge for using network ACLs" [6]. Cost differences are operational only.
- Lock-in Assessment: Both are AWS-native constructs; conceptually portable (Azure NSG, GCP firewall
  rules) but not directly transferable — see Service Equivalence Map.
- Architect Instruction: "Ask whether the requirement is an explicit *deny* or an *immediate*
  connection cut — if yes, use a NACL; otherwise default to a security group."
- Source: [1][6]

**Rule quotas: default limits vs increase (network-performance trade-off)**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Default SG quotas (60 rules/SG each direction, 5 SGs/ENI) | Security groups | Simplicity, predictable performance | May be tight for large allow-lists | Most workloads |
  | Raise SG rules or SGs/ENI (rules × SGs ≤ 1000) | Security groups | More granularity | Rules×SGs/ENI capped at 1000; describe pagination advised | Complex east-west meshes |
  | Default NACL 20 rules -> up to 40+40 | Network ACLs | More explicit deny entries | "network performance might be impacted" beyond default [6] | Subnet with many discrete denies |

- Cost Profile: No charge; the cost is potential network-performance impact and management overhead.
- Lock-in Assessment: N/A (quota tuning, not architecture).
- Architect Instruction: "Ask whether large allow-lists can be collapsed into a prefix list before
  requesting a quota increase — but note a prefix-list rule counts as its MAX size against the quota." [2]
- Source: [11][2]

**Centralize SG management: per-VPC SGs vs Security Group VPC Associations vs Shared Security Groups**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | One SG per VPC (classic) | Security groups | Isolation, simplicity | Duplicated policy across VPCs | Few VPCs, low sharing |
  | Security Group VPC Associations | SG VPC Associations (2024) | Single SG reused across VPCs in same Region/account | Same-Region/account only; default SG excluded | Many VPCs, same account, shared policy [7] |
  | Shared Security Groups | Shared SGs via AWS Organizations + shared VPC | Cross-account reuse within a shared VPC | Requires RAM/Organizations + shared VPC | Multi-account org, shared VPC [4] |

- Cost Profile: No direct charge; reduces operational drift/duplication.
- Lock-in Assessment: AWS-specific governance model.
- Architect Instruction: "Ask whether the VPCs sharing policy are in the same account (use VPC
  Associations) or across accounts in a shared VPC (use Shared Security Groups)."
- Source: [7][4]

### 🚫 Anti-Patterns

**SSH/RDP open to 0.0.0.0/0**
- Risk Level: CRITICAL
- Why: Violates Security pillar least-privilege network access [10]; AWS explicitly warns against it [1].
- Instead: Restrict inbound 22/3389 to a corporate CIDR or prefix list, or remove them and use AWS
  Systems Manager Session Manager.
- Detection: AWS Config `restricted-ssh` / `restricted-common-ports`; Security Hub CSPM.
- Impact: Data breach / instance compromise / lateral movement.
- Source: [1][10]

**Relying on the default security group / default network ACL for production**
- Risk Level: HIGH
- Why: The default SG allows all traffic between its members and all outbound; the default NACL
  allows ALL inbound and outbound (rule 100 ALLOW) [3]. This is allow-by-default — the opposite of
  least privilege.
- Instead: Create purpose-built SGs (new SGs have NO inbound rules) [2]; use custom NACLs which are
  deny-by-default until you add allow rules [3].
- Detection: Check whether workload ENIs reference the VPC default SG; check subnets bound to the
  default NACL.
- Impact: Over-broad exposure / compliance violation.
- Source: [3][2]

**Treating a network ACL as stateful (missing ephemeral return rules)**
- Risk Level: HIGH
- Why: "Network ACLs are stateless. Therefore, you must include a rule that allows responses to the
  inbound traffic." [9] Omitting it breaks connectivity in confusing, intermittent ways.
- Instead: For every inbound allow, add the outbound ephemeral-port allow (1024-65535 to the client).
- Detection: Diff inbound service-port rules against outbound ephemeral-range rules per NACL.
- Impact: Service outage / broken return traffic.
- Source: [9][6]

**Wildcard all-traffic (0.0.0.0/0, all ports) SG rules on production**
- Risk Level: HIGH
- Why: Removes least-privilege benefit AND makes the flow "untracked" — meaning existing sessions
  drop immediately when the rule is edited [5], causing surprise outages during change windows.
- Instead: Scope protocol/port/source narrowly so connections are tracked and survive rule edits.
- Detection: Grep SG rules for protocol `-1` / ports `0-65535` with source `0.0.0.0/0`.
- Impact: Exposure + cascading connection drops on change.
- Source: [5]

**❌ Wrong / ✅ Correct examples (concrete, exact service names)**

| # | ❌ Wrong (exact AWS config) | ✅ Correct (exact AWS config) |
|---|---|---|
| 1 | Security group inbound rule: TCP 22 from `0.0.0.0/0` | Security group inbound rule: TCP 22 from corporate prefix list `pl-xxxx`, or no 22/3389 rule + AWS Systems Manager Session Manager |
| 2 | Web-tier SG allows TCP 5432 from `10.0.0.0/16` (whole VPC CIDR) | DB-tier security group allows TCP 5432 from web-tier SG (`sg-web`) via security-group referencing |
| 3 | Custom network ACL with only an inbound ALLOW TCP 443 rule (no outbound) | Network ACL inbound ALLOW TCP 443 from client CIDR + outbound ALLOW TCP 1024-65535 to client CIDR (ephemeral return) |
| 4 | Production ENIs attached to the VPC default security group | Purpose-built security groups per tier; default SG left unused with no rules |
| 5 | Subnets left on the default network ACL (rule 100 ALLOW all) | Custom network ACL per subnet tier (deny-by-default) mirroring SG allow policy as a guard rail |

---

## Cloud-Native Design Patterns

**Three-tier SG referencing chain (ALB -> web -> db)**
- Category: Communication / Security
- Problem: Allow only the intended tier-to-tier east-west flows without brittle IP allow-lists.
- Solution on AWS: ALB SG allows 80/443 from `0.0.0.0/0`; web SG allows 80/443 from ALB SG; db SG
  allows the DB port from web SG — all via security-group referencing over private IPs [2].
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Maintainability | Rules follow instances as they autoscale | Requires discipline naming SGs by role |
  | Security | No public DB exposure; least privilege | Does not traverse middlebox routes [2] |

- Source: [2]

**Subnet guard-rail NACL (defense-in-depth backstop)**
- Category: Resilience / Security
- Problem: A future instance may be launched without the correct security group.
- Solution on AWS: Attach a custom NACL per subnet that allows only the tier's coarse traffic and
  denies known-bad CIDRs — so subnet-level policy holds even if an SG is misapplied [1][6].
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Blast radius | Contains SG misconfiguration | Stateless — must manage ephemeral return rules |
  | Change safety | NACL deny cuts existing connections immediately | Same immediacy can cause outages if misconfigured |

- Source: [1][6]

**Prefix-list-driven allow-lists**
- Category: Scalability / Security
- Problem: Many discrete CIDRs (e.g., partner ranges) exceed manageable rule counts.
- Solution on AWS: Reference a customer-managed or AWS-managed prefix list in SG rules; update the
  list once and all referencing rules inherit it [2].
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Manageability | One update fans out to all rules | A prefix-list rule counts as its MAX size vs quota [2] |

- Source: [2]

---

## Security Architecture

**Network segmentation (Identity of traffic by SG/NACL layer)**
- AWS Services: Security groups (per-ENI), Network ACLs (per-subnet), VPC subnets (public/private/isolated)
- Architecture: Public subnets host only ingress (ALB/NAT); private subnets host compute; isolated
  subnets host data stores with no route to an internet gateway. SGs enforce per-tier allow-lists;
  NACLs backstop at the subnet boundary [1][6].
- Compliance Alignment: Well-Architected Security pillar SEC05-BP01 "Create network layers" and
  SEC05-BP02 "Control traffic flow within your network layers" [10] (framework reference, not legal advice).
- Source: [1][6][10]

**What SG/NACL do NOT filter (know the gaps)**
- AWS Services: Route 53 Resolver DNS Firewall, EC2 IMDS options
- Architecture: Neither SGs nor NACLs filter traffic to/from Amazon DNS, DHCP, EC2 instance metadata,
  ECS task metadata, Windows license activation, Time Sync, or reserved VPC-router IPs [1][6]. NACLs
  additionally cannot block Route 53 Resolver DNS (VPC+2) or IMDS [6]. To filter DNS, use Route 53
  Resolver DNS Firewall; to control IMDS, configure instance metadata options [6].
- Compliance Alignment: Defense-in-depth — do not assume SG/NACL cover these paths.
- Source: [1][6]

**Connection-tracking capacity as a security/availability concern**
- AWS Services: Security groups (conntrack), ENA metrics `conntrack_allowance_available` / `_exceeded`
- Architecture: Each instance has a max number of trackable connections; exhaustion drops packets.
  Monitor via ENA metrics and tune idle timeouts; note automatically tracked paths (NAT gateway, NLB,
  PrivateLink, Lambda Hyperplane ENIs, GWLB endpoints, Global Accelerator) [5].
- Compliance Alignment: Reliability + Security (availability under attack/scale).
- Source: [5]

---

## Operational Patterns

**Change safety for tracked vs untracked flows**
- {{AWS}} Services: Security groups, VPC Flow Logs
- Cost Profile: Low (Flow Logs storage only).
- Automation: Automate SG rule changes via IaC + code review; alert on rules that create untracked
  flows (0.0.0.0/0 both directions).
- Runbook skeleton: (1) Detect via Flow Logs / Config; (2) confirm whether the flow is tracked
  (narrow rule) or untracked (all-traffic); (3) for untracked flows, schedule changes in a window —
  edits drop existing sessions immediately [5]; (4) verify with `conntrack_allowance_exceeded`.
- Source: [5]

**Nitro v6 idle-timeout migration**
- RTO/RPO: N/A (connectivity operations)
- AWS Services: Security groups (idle connection tracking timeout on the ENI)
- Cost Profile: Low.
- Automation: Set `TcpEstablishedTimeout` at instance/launch-template creation for long-lived
  connections (DB pools, persistent HTTP, streaming); default dropped to 350s on Nitro v6 [5].
- Source: [5]

---

## Reference Architectures

**Three-tier web application VPC (SG + NACL layering)**
- Context: Internet-facing web app with private compute and isolated data tier.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Edge | ALB security group | Allow 80/443 from `0.0.0.0/0` |
  | Web | Web-tier security group | Allow 80/443 from ALB SG (referenced) |
  | Data | DB-tier security group | Allow DB port from web SG (referenced) |
  | Subnet guard rail | Custom network ACLs | Coarse allow per tier + deny known-bad CIDRs |
  | Audit | VPC Flow Logs | ACCEPT/REJECT record per ENI/subnet |

- Key Decisions: Use SG referencing (not CIDRs) for east-west; keep NACLs coarse; remove default SG usage.
- Scaling Path: Autoscaling instances inherit SG rules automatically; collapse partner CIDRs into
  prefix lists; adopt SG VPC Associations if the pattern spans multiple VPCs in one account [7].
- Source: [1][2][6][7]

---

## Service Equivalence Map

> Included because architects frequently port these VPC constructs across clouds. Equivalence does
> **not** imply feature parity — verify against each provider's current docs.

| Capability | AWS | Google Cloud | Azure | Oracle Cloud (OCI) |
|---|---|---|---|---|
| Instance/NIC-level stateful firewall | Security groups | VPC firewall rules (stateful) / hierarchical firewall policies | Network Security Groups (NSG, stateful) | Network Security Groups (NSG, stateful) |
| Subnet-level filter | Network ACLs (stateless, allow+deny) | VPC firewall rules (applied by target/tag; no separate stateless subnet ACL) | NSG applied at subnet scope (stateful) | Security Lists (stateful or stateless per rule) |
| Deny rules supported | NACL: yes; SG: no (allow-only) | Firewall rules: allow + deny (priority-ordered) | NSG: allow + deny (priority-ordered) | Security Lists / NSG: allow-only (order-independent) |
| Reference by group/tag | SG referencing (source = SG ID) | Source/target service accounts or network tags | Application Security Groups (ASG) | NSG as source/destination |
| Stateless option | NACLs | (rules are stateful) | (NSG stateful) | Security Lists stateless rules |

> ⚠️ AWS security groups are **allow-only**; Azure NSG, GCP firewall rules, and NACLs support explicit
> **deny** — a frequent source of cross-cloud design errors.

---

## Provider Differentiators

```
Differentiator: Security Group Referencing (source/destination = sg-ID) across VPC peering and Transit Gateway
Category: Security / Networking
Unique Value: Rules follow instances by SG membership over private IPs; extended across Transit
  Gateway GA Sep 2024 — broader than typical tag-based models.
Architecture Impact: Eliminates IP allow-list churn for east-west traffic at scale, including
  multi-VPC hub-and-spoke topologies.
When to Leverage: Any multi-tier or multi-VPC design with dynamic instance fleets.
Caveat: Does not work across a middlebox appliance route (must use IP/CIDR there) [2]; TGW
  referencing requires supported TGW configuration [8].
Source: [2][8]
```
```
Differentiator: Security Group VPC Associations + Shared Security Groups (2024)
Category: Security / Governance
Unique Value: One SG reused across multiple VPCs in a Region (same account) or shared across
  Organizations accounts in a shared VPC.
Architecture Impact: Centralizes network policy; reduces drift/duplication across a VPC estate.
When to Leverage: Multi-VPC or multi-account estates with common network requirements.
Caveat: Same Region required; default SG cannot be associated; cannot associate to a default VPC [7].
Source: [7][4]
```

---

## Scenario Coverage

**Standard Case**: Three-tier web app in one VPC.
- Approach: ALB-SG -> web-SG -> db-SG via SG referencing; custom NACL per subnet as guard rail;
  Flow Logs on. Admin access via SSM (no inbound 22/3389).
- Key Decisions: SG referencing vs CIDR; how coarse to make NACLs; prefix lists for partner CIDRs.

**Edge Case**: Estate of many VPCs / multiple accounts sharing one network policy.
- Approach: Security Group VPC Associations (same account) or Shared Security Groups via AWS
  Organizations + shared VPC (cross-account); SG referencing over Transit Gateway for east-west [7][4][8].

**Anti-Pattern Case**: Request to "just open the security group to 0.0.0.0/0 to unblock the app."
- Clarification: Ask which exact protocol/port/source is required; propose SG referencing or a scoped
  CIDR/prefix list. Refuse wildcard management-port exposure; note that all-traffic wildcard rules
  also create untracked flows that drop on the next edit [1][5].

---

## Source Bibliography

All sources are official AWS documentation unless noted; access date **2026-08-26**.

| # | Source | URL | Date/Currency |
|---|--------|-----|---------------|
| 1 | Amazon VPC User Guide — Control traffic using security groups (basics, best practices) | https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html | Accessed 2026-08-26 |
| 2 | Amazon VPC User Guide — Security group rules (components, referencing, size, stale rules) | https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html | Accessed 2026-08-26 |
| 3 | Amazon VPC User Guide — Default network ACL for a VPC | https://docs.aws.amazon.com/vpc/latest/userguide/default-network-acl.html | Accessed 2026-08-26 |
| 4 | AWS What's New — Amazon VPC launches new security group sharing features (Shared Security Groups) | https://aws.amazon.com/about-aws/whats-new/2024/10/amazon-virtual-private-cloud-security-group-sharing/ | Announced 2024-10; verify currency |
| 5 | Amazon EC2 User Guide — Security group connection tracking (stateful, untracked, timeouts) | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/security-group-connection-tracking.html | Accessed 2026-08-26 |
| 6 | Amazon VPC User Guide — Network ACLs + Infrastructure security / SG vs NACL comparison | https://docs.aws.amazon.com/vpc/latest/userguide/vpc-network-acls.html , https://docs.aws.amazon.com/vpc/latest/userguide/infrastructure-security.html | Accessed 2026-08-26 |
| 7 | Amazon VPC User Guide — Associate security groups with multiple VPCs (SG VPC Associations) | https://docs.aws.amazon.com/vpc/latest/userguide/security-group-assoc.html | Accessed 2026-08-26 |
| 8 | AWS What's New — GA: Security Group Referencing on AWS Transit Gateway | https://aws.amazon.com/about-aws/whats-new/2024/09/general-availability-security-group-referencing-aws-transit-gateway | Announced 2024-09; verify currency |
| 9 | Amazon VPC User Guide — Example: Control access to instances in a subnet (ephemeral ports) | https://docs.aws.amazon.com/vpc/latest/userguide/nacl-examples.html | Accessed 2026-08-26 |
| 10 | AWS Well-Architected Security Pillar — Infrastructure & network protection (SEC05-BP01/BP02) | https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-networks.html | Accessed 2026-08-26 |
| 11 | Amazon VPC User Guide — Amazon VPC quotas (SG and NACL limits) | https://docs.aws.amazon.com/vpc/latest/userguide/amazon-vpc-limits.html | Accessed 2026-08-26 |

### Key quotas captured (from [11], per Region/account, defaults)

| Resource | Default | Adjustable |
|---|---|---|
| VPC security groups per Region | 2,500 | Yes |
| Inbound OR outbound rules per security group | 60 (enforced separately per direction and per IPv4/IPv6) | Yes |
| Security groups per network interface | 5 | Yes (up to 16); rules × SGs per ENI ≤ 1,000 |
| Network ACLs per VPC | 200 | Yes |
| Rules per network ACL | 20 (max inbound and max outbound separately) | Yes — up to 40+40, may impact performance |
| NACL rule number range | 1–32766 | N/A |

---

## §7 Research Iteration Changelog

| Iteration | Item | Action | Result | Source |
|---|---|---|---|---|
| 0 (initial) | All core SG/NACL facts, quotas, comparison, connection tracking, ephemeral ports, 2024 features | Fetched official VPC/EC2 User Guide + WAF + What's New | Verified with dated official sources | [1]–[11] |
| — | Layered SG+NACL defense-in-depth (Always-Do #1) | Triangulation per P5.triangulate | Confirmed by 2 independent official sources | [1] + [10] |
| — | SG referencing (Always-Do #2) | Triangulation | Confirmed by 2 independent official sources | [2] + [8] |

> No items remain flagged "unverified" after iteration 0; the gap-filling loop (P5.gap-loop)
> terminated early per its stop-condition. No `⚠️ IRRESOLVABLE` items.

---

## Verification Loop — Self-Check Result

```
[x] TARGET_EDITION stated in metadata and throughout
[x] All 6 mandatory sections present: Framework Pillars (Guardrails), Always-Do, Ask-First,
    Never-Do, Service Equivalence Map, Source Bibliography
[x] Every pattern cites an official provider URL with access date
[x] Every Never-Do has ❌ Wrong / ✅ Correct with exact AWS service names (table of 5)
[x] All sources dated; 2024 What's New items flagged "verify currency"
[x] Service Equivalence Map covers the service classes researched (SG / NACL / equivalents)
[x] No generic cloud terms where AWS-specific names exist
```

> **Recommended next step:** run `/skill-best-practices-validator` (or `/evaluating-skill-scenarios`)
> against any skill generated from this research. Two secondary sources ([4],[8]) are 2024 AWS
> What's New posts describing GA features — re-confirm they have not been superseded before the
> 2027-08-26 currency threshold.
