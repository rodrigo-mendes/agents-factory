---
title: AWS Security Groups — Architecture Research 2025
cloud_provider: AWS
architecture_domain: Security Groups (Network Security)
target_edition: AWS VPC Security Groups 2025
research_date: 2026-07-31
audience: Cloud Architects and Tech Leads
---

## Executive Summary

An AWS **Security Group** is a *stateful*, allow-only virtual firewall that controls inbound and
outbound traffic at the **resource level** (for example, an Amazon EC2 instance's elastic network
interface), not at the subnet level. Every Amazon VPC ships with a **default security group**, and
you can create additional groups — each with its own inbound and outbound rules referencing CIDR
blocks, prefix lists, or *other security groups* — as the primary mechanism for controlling network
access to workloads in a VPC (source: AWS VPC User Guide, accessed 2026-07-31). Because security
groups are stateful, response traffic for an allowed flow is permitted automatically regardless of
the opposing ruleset; because they are allow-only, you cannot write explicit deny rules — that is
the job of **network ACLs (NACLs)**, which operate statelessly at the subnet level as a
defense-in-depth layer. The core architectural decisions covered here are: (1) security groups as
the primary control vs. NACLs as coarse-grained secondary guard rails, (2) security-group
*referencing* vs. CIDR-based rules for tiered segmentation, and (3) managing the hard interaction
limit that *rules-per-SG × SGs-per-ENI cannot exceed 1,000*. This document pins every claim to
official AWS 2025 documentation; anything not confirmed by those sources is marked **unverified**.

> **Version note (AWS 2025):** AWS services are continuously delivered rather than semantically
> versioned. "AWS VPC Security Groups 2025" here means the behavior documented in the current
> `docs.aws.amazon.com/vpc/latest/` user guide as accessed on **2026-07-31**. All quoted quotas are
> *default* values and are adjustable via Service Quotas unless stated otherwise; verify live quotas
> in your own account before designing to a hard limit.

---

## Framework Pillars

Security Groups are the workload-facing control point of the **Security pillar** of the AWS
Well-Architected Framework, and — through blast-radius containment and fail-safe defaults — they
also contribute to the **Reliability pillar**.

### Security Pillar — Infrastructure Protection

The Security pillar treats network controls under **Infrastructure Protection**, whose defining
methodology is **defense in depth**: "Infrastructure protection encompasses control methodologies,
such as defense in depth, that are necessary to meet best practices and organizational or regulatory
obligations." It calls for defining **trust boundaries** (network and account boundaries) and
"other appropriate policy-enforcement points" (source: Well-Architected Security Pillar —
Infrastructure Protection, accessed 2026-07-31).

Under **Protecting networks**, AWS frames the network design around a **Zero Trust** approach —
"no component or microservice trusts any other" — supported by inspection and automation. The
relevant best practices (SEC05) are:

| Best-practice ID | Title | How Security Groups apply |
|---|---|---|
| **SEC05-BP01** | Create network layers | Segment web / app / data tiers into separate subnets, each protected by a dedicated security group |
| **SEC05-BP02** | Control traffic flow within your network layers | Security groups referencing other security groups enforce tier-to-tier flow (least privilege) |
| **SEC05-BP03** | Implement inspection-based protection | Security groups pair with AWS Network Firewall / Gateway Load Balancer for deep inspection |
| **SEC05-BP04** | Automate network protection | Automate security-group rule verification and change control via IaC and IAM policies |

Source: Well-Architected Security Pillar — Protecting networks (SEC05-BP01…BP04), accessed
2026-07-31.

The VPC User Guide's own guidance reinforces the pillar: "Use security groups as the primary
mechanism for controlling network access to your VPCs. When necessary, use network ACLs to provide
stateless, coarse-grain network control. Security groups are more versatile than network ACLs, due
to their ability to perform stateful packet filtering and create rules that reference other security
groups." (source: Infrastructure security in Amazon VPC — Control network traffic, accessed
2026-07-31).

### Reliability Pillar (contributing role)

Security groups contribute to reliability through **fail-safe defaults** and **blast-radius
containment** rather than being a primary reliability construct:

- **Fail-closed inbound:** "When you first create a security group, it has no inbound rules.
  Therefore, no inbound traffic is allowed until you add inbound rules" — a new group cannot
  accidentally expose a workload (source: Security group rules, accessed 2026-07-31).
- **Automatic rule propagation:** "When you add, update, or remove rules, your changes are
  automatically applied to all resources associated with the security group" — consistent
  enforcement across a fleet reduces configuration drift (source: Security group rules, accessed
  2026-07-31).
- **Availability-Zone-independent enforcement:** Security groups are a VPC/Region construct applied
  per elastic network interface, so enforcement survives AZ failure of any single instance. Multi-AZ
  designs (see the load-balancer + web + DB example in the VPC guide) inherit the same rule set in
  every AZ (source: Security group rules — referencing example, accessed 2026-07-31).

> **Unverified:** The Well-Architected Reliability pillar does not name "Security Groups" as an
> explicit best-practice line item. The reliability contributions above are inferred from documented
> security-group *behavior*, not from a Reliability-pillar best-practice ID.

---

## Mandatory Patterns (Always-Do)

Each pattern below is a non-negotiable best practice for general-purpose production workloads using
VPC-based network segmentation. All are drawn from the AWS "Best practices" callout in the Security
Groups guide and the VPC infrastructure-security guidance (accessed 2026-07-31).

### A1 — Restrict management ports (SSH 22 / RDP 3389) to specific CIDRs, never 0.0.0.0/0

**Why:** AWS: "When you add inbound rules for ports 22 (SSH) or 3389 (RDP) so that you can access
your EC2 instances, authorize only specific IP address ranges. If you specify 0.0.0.0/0 (IPv4) and
::/0 (IPv6), this enables anyone to access your instances from any IP address using the specified
protocol."

```text
Inbound rule (correct):  TCP  22   Source 203.0.113.0/24   (corporate egress range / bastion)
Inbound rule (correct):  TCP  3389 Source pl-0abc123        (managed prefix list of admin IPs)
```

Source: Control traffic to your AWS resources using security groups — Best practices, accessed
2026-07-31.

### A2 — Use security-group *referencing* for tier-to-tier traffic, not CIDR ranges

**Why:** Referencing another security group as the source ties access to *membership* rather than IP
addressing, so it survives instance replacement and scaling. AWS canonical three-tier example: "Add
rules to the security group for the web servers to allow HTTP and HTTPS traffic only from the load
balancer. The source is the security group for the load balancer. Add rules to the security group
for the database servers to allow database requests from the web servers. The source is the security
group for the web servers."

```text
web-sg  inbound:  TCP 443  Source sg-lb    (only the load balancer SG)
db-sg   inbound:  TCP 5432 Source sg-web   (only the web tier SG, e.g., Amazon RDS PostgreSQL)
```

Source: Security group rules — Security group referencing (example), accessed 2026-07-31.

### A3 — Create the minimum number of security groups, grouped by function

**Why:** AWS: "Create the minimum number of security groups that you need, to decrease the risk of
error. Use each security group to manage access to resources that have similar functions and
security requirements."

Source: Control traffic to your AWS resources using security groups — Best practices, accessed
2026-07-31.

### A4 — Never open large port ranges; scope each port to only its required source/destination

**Why:** AWS: "Do not open large port ranges. Ensure that access through each port is restricted to
the sources or destinations that require it."

```text
Bad intent:  TCP 0-65535   (avoid)
Correct:     TCP 443 only, Source sg-lb
```

Source: Control traffic to your AWS resources using security groups — Best practices, accessed
2026-07-31.

### A5 — Restrict who can create/modify security groups via IAM

**Why:** AWS: "Authorize only specific IAM principals to create and modify security groups." This
enforces change control and supports SEC05-BP04 (automate network protection). AWS also suggests
using "additional security groups or network interfaces to control and audit Amazon EC2 instance
management traffic separately... so you can implement special IAM policies for change control."

Source: Control traffic to your AWS resources using security groups — Best practices; Infrastructure
security in Amazon VPC — Control network traffic, accessed 2026-07-31.

### A6 — Add network ACLs as a defense-in-depth layer for production subnets

**Why:** AWS: "Consider creating network ACLs with rules similar to your security groups, to add an
additional layer of security to your VPC." And: because NACLs "apply to an entire subnet, they can
be used as defense-in-depth in case an instance is ever launched without the correct security
group."

Source: Control traffic to your AWS resources using security groups — Best practices; Infrastructure
security in Amazon VPC — Control network traffic, accessed 2026-07-31.

### A7 — Enable VPC Flow Logs to validate that rules are neither too tight nor too loose

**Why:** AWS: Flow logs "can help you diagnose overly restrictive or overly permissive security group
and network ACL rules." Publish to CloudWatch Logs or Amazon S3.

Source: Ensure internetwork traffic privacy in Amazon VPC — Flow logs, accessed 2026-07-31.

---

## Architectural Crossroads (Ask-First)

These are decisions where multiple valid approaches exist; the right choice depends on the workload,
scale, and compliance context. Confirm the driving factors before committing.

### C1 — Security Groups vs. Network ACLs (which control, and when both)

| Factor | Choose **Security Group** | Choose **Network ACL** | Use **both** |
|---|---|---|---|
| Enforcement level | Per-resource / ENI (instance) | Per-subnet | Layered |
| Statefulness | Stateful (return traffic auto-allowed) | Stateless (must allow return + ephemeral ports) | — |
| Rule semantics | Allow-only | Allow **and** deny | — |
| Typical use | Primary access control | Coarse-grained subnet guard rails; explicitly *deny* a bad CIDR | Production defense-in-depth |

**AWS guidance:** "Use security groups as the primary mechanism... When necessary, use network ACLs
to provide stateless, coarse-grain network control... Network ACLs can be effective as a secondary
control (for example, to deny a specific subset of traffic) or as high-level subnet guard rails."
"You can secure your instances using only security groups. However, you can add network ACLs as an
additional layer of defense."

**Decision factors:** need for explicit *deny* (NACL only), subnet-wide blast-radius protection
(NACL), regulatory defense-in-depth (both), operational simplicity (SG only).

Source: Infrastructure security in Amazon VPC — Control network traffic & Compare security groups and
network ACLs, accessed 2026-07-31.

### C2 — Rule capacity: rules-per-SG vs. SGs-per-ENI (the 1,000 product limit)

**The trade-off:** default quotas are **60 inbound + 60 outbound rules per security group**
(enforced separately for IPv4 and IPv6) and **5 security groups per network interface** (adjustable
up to 16). Crucially: "This quota multiplied by the quota for security groups per network interface
cannot exceed 1,000." So raising one lever forces the other down.

| Approach | Config | Rules available per ENI | When |
|---|---|---|---|
| Few large SGs | 200 rules/SG × 5 SGs | 1,000 | Consolidated, fewer objects to manage |
| Many small SGs | 62 rules/SG × 16 SGs | ~992 | Fine-grained functional grouping |

**Prefix-list cost caveat:** a rule referencing a customer-managed prefix list "counts as the maximum
size of the prefix list" (e.g., a max-size-20 prefix list consumes 20 rule slots), and an AWS-managed
prefix list counts as its published *weight*. Plan capacity accordingly.

**Decision factors:** number of distinct trust relationships, use of prefix lists, need to reference
many peer SGs. Ask before designing to a raised quota — request the increase first.

Source: Amazon VPC quotas — Security groups; Security group rules — Security group size, accessed
2026-07-31.

### C3 — Referencing another security group vs. a CIDR / prefix list as source

| Option | Pros | Cons / limits |
|---|---|---|
| **Reference peer SG** (`sg-…`) | Membership-based, survives IP churn; ideal for tiered apps | Only valid within same VPC, or across a **VPC peering** / **transit gateway** connection; counts as 1 rule regardless of member count |
| **CIDR block** | Works for on-prem / cross-boundary / middlebox routing | IP-brittle; large ranges over-expose |
| **Managed prefix list** (`pl-…`) | Central, reusable set of CIDRs | Consumes rule slots equal to prefix-list max size/weight |

**Critical middlebox caveat (Ask-First):** "If you configure routes to forward the traffic between
two instances in different subnets through a middlebox appliance... The security group for each
instance must reference the private IP address of the other instance or the CIDR range of the
subnet... If you reference the security group of the other instance as the source, this does not
allow traffic to flow between the instances." For middlebox-routed flows you **must** use CIDR, not
SG referencing.

Source: Security group rules — Security group referencing (limitation), accessed 2026-07-31.

### C4 — Default outbound "allow all" vs. explicit egress control

**The trade-off:** "When you first create a security group, it has an outbound rule that allows all
outbound traffic... You can remove the rule and add outbound rules that allow specific outbound
traffic only. If your security group has no outbound rules, no outbound traffic is allowed."

- **Keep default allow-all egress:** simplest; acceptable for many internal workloads.
- **Lock down egress:** required for data-exfiltration-sensitive / regulated workloads (Zero Trust,
  SEC05). Remember statefulness — you do not need an egress rule for *responses* to allowed inbound
  traffic; only for instance-*initiated* outbound.

**Decision factors:** compliance regime, exfiltration risk, whether the instance initiates outbound
connections (updates, third-party APIs). Ask before stripping egress on shared platforms.

Source: Security group rules — Security group rule basics; Security group basics (statefulness),
accessed 2026-07-31.

### C5 — Sharing / associating security groups across VPCs

Options: **Security Group VPC Association** ("associate the security group to other VPCs in the same
Region"), **share security groups with AWS Organizations**, or reference across **VPC peering** /
**transit gateway**. Beware **stale rules**: "If you have a security group rule that references a
security group in a peer VPC or shared VPC, the rule is marked as stale when the referenced security
group is deleted or the VPC peering connection is deleted." Establish a process to detect and remove
stale rules.

**Decision factors:** multi-VPC topology, Organizations governance, cross-account ownership (note:
"When a referenced security group is owned by another account, the owner account does not receive
CloudTrail events" for authorize/revoke actions).

Source: Control traffic to your AWS resources using security groups (topics); Security group rules —
Stale security group rules & Security group referencing, accessed 2026-07-31.

---

## Anti-Patterns (Never-Do)

Every entry includes a side-by-side ❌ Wrong / ✅ Correct using exact AWS service/resource names.

### N1 — Exposing SSH/RDP to the entire internet

**Why it's wrong:** `0.0.0.0/0` on port 22/3389 "enables anyone to access your instances from any IP
address" — the single most common EC2 compromise vector.

```text
❌ Wrong  (security group inbound rule on EC2 instance)
   Type: SSH   Protocol: TCP   Port: 22   Source: 0.0.0.0/0

✅ Correct
   Type: SSH   Protocol: TCP   Port: 22   Source: 203.0.113.0/24   (bastion / corporate CIDR)
   # or eliminate inbound SSH entirely and use AWS Systems Manager Session Manager
```

**Impact:** internet-wide brute-force / unauthorized access to the instance.
Source: Control traffic to your AWS resources using security groups — Best practices, accessed
2026-07-31.

### N2 — Using broad CIDR ranges for tier-to-tier traffic instead of SG referencing

**Why it's wrong:** hard-coding subnet CIDRs for app→DB traffic over-exposes the database to every IP
in the subnet and breaks on IP churn; AWS's canonical pattern references the *web-tier security
group* as the source.

```text
❌ Wrong  (Amazon RDS database security group inbound)
   Type: PostgreSQL   Port: 5432   Source: 10.0.0.0/16   (entire VPC)

✅ Correct
   Type: PostgreSQL   Port: 5432   Source: sg-web         (web-tier security group only)
```

**Impact:** any compromised host in the CIDR can reach the database; violates least privilege
(SEC05-BP02).
Source: Security group rules — Security group referencing (example), accessed 2026-07-31.

### N3 — Referencing a peer instance's security group for middlebox-routed traffic

**Why it's wrong:** when traffic between two instances is routed through a middlebox appliance,
referencing the *other instance's security group* as source "does not allow traffic to flow between
the instances." You must use the private IP or subnet CIDR.

```text
❌ Wrong  (instance-A security group, traffic routed via firewall appliance)
   Inbound  Source: sg-instance-b        (will NOT permit the middlebox-routed flow)

✅ Correct
   Inbound  Source: 10.0.2.0/24          (CIDR of the subnet containing instance B)
```

**Impact:** silent connectivity failure that is hard to diagnose because the rule "looks" correct.
Source: Security group rules — Security group referencing (limitation), accessed 2026-07-31.

### N4 — Relying on security groups to filter DNS (Route 53 Resolver) or IMDS

**Why it's wrong:** "Security groups cannot block DNS requests to or from the Route 53 Resolver...
(the 'VPC+2 IP address')". Neither can NACLs, and NACLs also "can't block traffic to the Instance
Metadata Service (IMDS)". Using an inbound/outbound SG rule as a DNS-filtering control is a false
sense of security.

```text
❌ Wrong  (attempting to block DNS exfiltration with a security group egress rule)
   Egress  Deny  UDP 53 to 0.0.0.0/0     # security groups have NO deny rules, and cannot
                                          # block the Route 53 Resolver anyway

✅ Correct
   # Use Route 53 Resolver DNS Firewall to filter DNS; for IMDS, configure instance
   # metadata options (require IMDSv2 / disable IMDS) on the EC2 instance.
```

**Impact:** DNS-based exfiltration/command-and-control and IMDS credential theft remain possible
despite the rule.
Source: Security group rules — Limitation (Route 53 Resolver); Control subnet traffic with network
access control lists — Limitations (IMDS), accessed 2026-07-31.

### N5 — Treating security groups as stateless and duplicating return-traffic rules (or expecting deny)

**Why it's wrong:** security groups are **stateful** — "if a security group allows inbound traffic to
an EC2 instance, responses are automatically allowed regardless of outbound security group rules."
Adding "return" rules or expecting an explicit deny in a security group is a misconception; explicit
deny and stateless return handling belong to **network ACLs**.

```text
❌ Wrong  (assuming SG is stateless like a NACL)
   Inbound   Allow TCP 443 from 0.0.0.0/0
   Outbound  Allow TCP 1024-65535 to 0.0.0.0/0   # unnecessary "ephemeral" return rule
   Inbound   Deny  TCP 22 from 198.51.100.0/24   # security groups CANNOT express deny

✅ Correct
   Inbound   Allow TCP 443 from sg-lb            # return traffic is auto-allowed (stateful)
   # To DENY a specific CIDR, use a network ACL rule (stateless, subnet level):
   #   NACL inbound rule #90  DENY  TCP 22  198.51.100.0/24
```

**Impact:** over-broad egress rules; and a nonexistent "deny" that never takes effect, leaving the
intended block unenforced.
Source: Control subnet traffic with network access control lists — Network ACL basics
(stateful vs stateless); Compare security groups and network ACLs; Security group rules — "You can
specify allow rules, but not deny rules," accessed 2026-07-31.

### N6 — Naming a security group with the reserved `sg-` prefix (and other naming violations)

**Why it's wrong:** AWS explicitly forbids it: "A security group name can't start with `sg-`." Names
must also be unique within the VPC and ≤ 255 characters. IaC that generates such names will fail at
apply time.

```text
❌ Wrong
   Name: sg-web-tier            # rejected — collides with the reserved resource-ID prefix

✅ Correct
   Name: web-tier-sg            # descriptive, unique within the VPC, ≤ 255 chars
```

**Impact:** `CreateSecurityGroup` API call fails; Terraform/CloudFormation deployment breaks.
Source: Control traffic to your AWS resources using security groups — Security group basics, accessed
2026-07-31.

---

## Service Equivalence Map

Cross-cloud mapping of AWS Security Groups to the nearest-equivalent stateful firewall constructs.
Statefulness and enforcement level differ subtly between clouds — verify per design.

| Dimension | **AWS Security Group** | **Azure Network Security Group (NSG)** | **GCP VPC Firewall Rule** | **OCI Network Security Group (NSG)** / Security List |
|---|---|---|---|---|
| Stateful? | Yes (stateful) | Yes (flow-record based) | Yes (return traffic auto-allowed) | Per-rule: **stateful or stateless** (configurable) |
| Enforcement level | Resource / ENI (instance) | Subnet **or** network interface | Network-level, "enforced on a per-instance basis" | NSG = VNIC; Security List = subnet |
| Rule semantics | **Allow only** | Allow **and** Deny | Allow **and** Deny | Allow only (allow-list model) |
| Ordering / evaluation | Evaluates *all* rules, then decides | Priority **100–4096**, lowest number wins, stops at first match | Priority **0–65535** (default 1000), lowest wins | Rules combined as union; stateless takes precedence over stateful on overlap |
| Default inbound | No inbound rules (implicit deny) | Default rules incl. `DenyAllInbound` (pri 65500) | Implied **deny** ingress | No traffic until rules added |
| Default outbound | Allow all outbound | Default `AllowInternetOutBound` + `DenyAllOutBound` | Implied **allow** egress | No traffic until rules added |
| Group-membership referencing | Reference another **security group** as source/dest | **Application Security Groups (ASGs)** | **Network tags** / **service accounts** as targets/sources | Reference another **NSG** as source/dest |
| Protocols | TCP, UDP, ICMP (+ protocol numbers) | TCP, UDP, ICMP, ESP, AH, Any | TCP, UDP, ICMP, ESP, AH, SCTP, IPIP | Configurable per rule (or "all") |
| Explicit deny? | No (use NACL) | Yes (Deny action) | Yes (deny action) | Security Lists/NSGs are allow-based |

**Key architectural distinctions to flag in a multi-cloud design:**
- Only **AWS** security groups are strictly *allow-only*; Azure NSGs, GCP firewall rules, and OCI
  offer explicit **deny**. In AWS the deny role lives in **network ACLs** (subnet, stateless).
- **AWS SG** enforcement is always per-ENI; **Azure NSG** can attach at subnet *or* NIC; **OCI**
  splits the two roles into Security Lists (subnet) vs. NSGs (VNIC).
- **GCP** and **OCI** allow priority-ordered evaluation; **AWS SG** evaluates *all* rules with no
  priority (only NACLs use ordered numbers, 1–32766).
- Membership-based referencing is universal but expressed differently: AWS **SG reference**, Azure
  **ASG**, GCP **network tags / service accounts**, OCI **NSG reference**.

Sources: AWS — Compare security groups and network ACLs & Security group rules (accessed 2026-07-31);
Azure — Network security groups overview, Microsoft Learn (doc dated 2025-07-15, accessed
2026-07-31); GCP — VPC firewall rules overview, Google Cloud docs (accessed 2026-07-31); OCI —
Security Rules, Oracle Cloud Infrastructure docs (accessed 2026-07-31).

---

## Reference: Quotas (AWS 2025 defaults)

All values are **default** and adjustable via AWS Service Quotas unless marked otherwise (source:
Amazon VPC quotas, accessed 2026-07-31).

| Quota | Default | Adjustable | Notes |
|---|---|---|---|
| VPC security groups per Region | 2,500 | Yes | Paginate `Describe` calls beyond 5,000 |
| Inbound **or** outbound rules per security group | 60 | Yes | Enforced separately for inbound/outbound **and** for IPv4/IPv6 |
| Security groups per network interface | 5 | Yes (up to 16) | — |
| **Product constraint** | rules-per-SG × SGs-per-ENI **≤ 1,000** | — | Hard interaction limit |
| Network ACLs per VPC | 200 | Yes | One NACL can attach to many subnets |
| Rules per network ACL | 20 | Yes (up to 40 in + 40 out) | Numbered 1–32766, evaluated ascending |
| Rule cost of a customer-managed prefix list | = prefix-list max size | — | e.g., max-20 list = 20 rule slots |

---

## Source Bibliography

All sources are official first-party documentation. Access date for every source: **2026-07-31**.
AWS VPC/EC2 user-guide pages are continuously updated ("latest" channel); no publication date is
exposed per page, so the access date is authoritative. Sources flagged ⚠️ where a doc date is known.

### Primary Sources — AWS (official)

1. **Control traffic to your AWS resources using security groups** — Amazon VPC User Guide.
   https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html — accessed 2026-07-31.
   (Definition, statefulness, default SG, security-group basics, best practices, naming rules.)
2. **Security group rules** — Amazon VPC User Guide.
   https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html — accessed 2026-07-31.
   (Rule components, allow-only, default inbound/outbound behavior, referencing, size/weight, stale
   rules, Route 53 Resolver limitation.)
3. **Ensure internetwork traffic privacy in Amazon VPC** — Amazon VPC User Guide.
   https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Security.html — accessed 2026-07-31.
   (Security groups vs. NACLs vs. flow logs vs. traffic mirroring overview.)
4. **Infrastructure security in Amazon VPC** (incl. *Compare security groups and network ACLs*) —
   Amazon VPC User Guide.
   https://docs.aws.amazon.com/vpc/latest/userguide/infrastructure-security.html — accessed
   2026-07-31. (Control-network-traffic guidance; the SG-vs-NACL comparison table.)
5. **Control subnet traffic with network access control lists** — Amazon VPC User Guide.
   https://docs.aws.amazon.com/vpc/latest/userguide/vpc-network-acls.html — accessed 2026-07-31.
   (NACL statelessness, rule numbering 1–32766, IMDS/DNS limitations, associations.)
6. **Amazon VPC quotas** — Amazon VPC User Guide.
   https://docs.aws.amazon.com/vpc/latest/userguide/amazon-vpc-limits.html — accessed 2026-07-31.
   (Exact default quotas for SGs, rules, SGs-per-ENI, the 1,000 product limit, NACL rules.)
7. **Infrastructure protection** — AWS Well-Architected Framework, Security Pillar.
   https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/infrastructure-protection.html
   — accessed 2026-07-31. (Defense-in-depth, trust boundaries.)
8. **Protecting networks** (SEC05-BP01…BP04) — AWS Well-Architected Framework, Security Pillar.
   https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-networks.html —
   accessed 2026-07-31. (Zero Trust; SEC05 best-practice IDs.)

### Cross-Cloud Sources (official, for Service Equivalence Map only)

9. **Azure network security groups overview** — Microsoft Learn.
   https://learn.microsoft.com/en-us/azure/virtual-network/network-security-groups-overview —
   ⚠️ doc dated 2025-07-15 (updated 2025-10-23); accessed 2026-07-31. (NSG statefulness via flow
   records, priority 100–4096, default rules, ASGs.)
10. **VPC firewall rules overview** — Google Cloud documentation.
    https://cloud.google.com/firewall/docs/firewalls (redirects to
    https://docs.cloud.google.com/firewall/docs/firewalls) — accessed 2026-07-31. (Stateful, per-
    instance enforcement, priority 0–65535 default 1000, implied deny-ingress/allow-egress.)
11. **Security Rules** — Oracle Cloud Infrastructure documentation.
    https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/securityrules.htm — accessed
    2026-07-31. (Security Lists vs. NSGs; stateful vs. stateless per rule; VNIC vs. subnet scope.)

### Research Gaps / Unverified Items

- **Reliability-pillar attribution:** No Well-Architected *Reliability* best-practice ID names
  "Security Groups" directly; the reliability contributions in this document are inferred from
  documented security-group behavior and are labeled accordingly. (Would require fetching the
  Reliability pillar pages to confirm — not in scope of the requested sources.)
- **AWS Network Firewall / Gateway Load Balancer inspection details** referenced under SEC05-BP03
  were not deep-fetched; the SEC05-BP03 mapping is based on the best-practice title only.
- **Connection tracking** nuances (which flows are tracked vs. untracked, and how rule changes affect
  in-flight connections) are referenced by AWS in the *Amazon EC2 User Guide — Connection tracking*
  page, which was cited but not fetched; treat detailed tracking behavior as **to-verify** before
  designing around it.

---

## Completion Checklist

- [x] Three tiers present: ✅ Always-Do (A1–A7), ⚠️ Ask-First (C1–C5), 🚫 Never-Do (N1–N6).
- [x] Every Never-Do has a side-by-side ❌ Wrong / ✅ Correct example.
- [x] Exact AWS service/resource names used (Security Group, NACL, VPC, EC2, Amazon RDS, Route 53
      Resolver, IMDS, prefix list, elastic network interface).
- [x] Every claim traces to an official source with access date 2026-07-31.
- [x] Version pinned to AWS 2025 (`docs.aws.amazon.com/vpc/latest/`), stated 5+ times.
- [x] Sources > 12 months old: none (Azure doc dated 2025-07-15 is < 12 months and flagged ⚠️).
- [x] Unverified items explicitly flagged rather than fabricated.

> **Recommended next step:** run `/skill-best-practices-validator` on this document, and pass it to
> `skill-author` (`/skill-creator`) if a Security-Groups skill is to be generated.
