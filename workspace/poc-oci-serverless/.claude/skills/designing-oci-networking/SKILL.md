---
name: designing-oci-networking
description: Designs and troubleshoots OCI networking (VCN, Subnets, NSGs, Gateways, DRG) for serverless architectures. Use when making network architecture decisions following OCI Best Practices (current stable).
---

## Version Context

**Technology**: Oracle Cloud Infrastructure (OCI) — Networking Architecture
**Cloud Provider**: Oracle Cloud Infrastructure (OCI)
**Architecture Domain**: VCN, Subnets, NSGs, Gateways (IGW, NAT, SGW), DRG v2, Route Tables
**Architecture Context**: Serverless API architecture with OCI Functions, API Gateway, and IAM
**Target Edition**: OCI Best Practices Framework (current stable)
**Support Status**: Active — continuously updated by Oracle

**Key Capabilities (current stable)**:
- **DRG v2**: Unified transit hub — supports VCN attachments, FastConnect, VPN, cross-region peering (up to 300 attachments)
- **Network Firewall**: OCI-native L3-L7 inspection (Palo Alto NGFW-based)
- **IPv6**: Native support in VCNs and subnets
- **Path Analyzer**: Configuration-based connectivity validation (no real traffic)
- **Private Endpoints**: Expanded for Object Storage, Autonomous DB, Functions
- **VTAP**: Virtual packet capture for troubleshooting and compliance

**Critical Limits**:
- NSGs per VNIC: **5** (hard limit)
- Rules per NSG: **120** (ingress + egress combined, hard limit)
- CIDRs per VCN: **5** (non-overlapping)
- IGW / NAT GW / SGW per VCN: **1** each (hard limits)
- DRG attachments: **300** (VCN + FastConnect + VPN + RPC)

⚠️ **CRITICAL — Agent Warning**:
This skill covers **network architecture and design decisions**. For Terraform implementation, use the skill `provisioning-oci-networking`. Always use **regional subnets** (not AD-specific), **NSGs** (not Security Lists) as primary firewall, and **Service Gateway** for OCI-to-OCI traffic. NSGs and Security Lists are evaluated with **UNION logic** — the most permissive rule wins.

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — Always Do, Ask First, Never Do summaries
  - [Always Do Patterns](./blueprints/always-do-patterns.md) — 5 mandatory patterns
  - [Ask First Decisions](./blueprints/ask-first-decisions.md) — 4 architecture decisions
  - [Never Do Patterns](./blueprints/never-do-patterns.md) — 5 anti-patterns with detection
  - [Evaluation Scenarios](./blueprints/evaluation-scenarios.md) — 5 scenarios: private subnet topology, NSG limit, OCIR pull failure, NSG vs Security List, IGW misuse
- **[Design Patterns](#design-patterns)** (inline section) — Architecture patterns and blueprints
- **[Verification Loop](#verification-loop)** — Validation commands and expected outputs
- **[Quick Reference](#quick-reference)** — Most used patterns at a glance
- **[External Resources](#external-resources)** — Official documentation links

---

## Blueprints & Guardrails

### ✅ Always Do
5 mandatory patterns for VCN architecture, gateways, and NSG security — see [Always Do Patterns](./blueprints/always-do-patterns.md):
1. **VCN with Public/Private Subnet Separation** — public for API Gateway, private for Functions
2. **Service Gateway for Oracle Services Access** — free, keeps OCI-to-OCI traffic on backbone
3. **NSGs as Primary Security Mechanism** — micro-segmentation with inter-NSG references
4. **NAT Gateway for Private Subnet Egress** — unidirectional egress, no public IP needed
5. **VCN Flow Logs Enabled** — security monitoring and compliance auditing

### ⚠️ Ask First
4 architecture decisions requiring user input — see [Ask First Decisions](./blueprints/ask-first-decisions.md):
1. **Network Security Model** — NSGs Only vs Security Lists+NSGs vs Network Firewall vs WAF
2. **Multi-VCN Topology** — Single VCN vs Hub-Spoke (DRG v2) vs Mesh
3. **On-Premises Connectivity** — FastConnect vs Site-to-Site VPN vs both
4. **Load Balancing** — API Gateway vs Flexible LB vs Network LB vs combined

### 🚫 Never Do
5 anti-patterns with detection commands — see [Never Do Patterns](./blueprints/never-do-patterns.md):
1. Security List with `0.0.0.0/0` ingress on all ports
2. Private subnet with route to Internet Gateway
3. Missing Service Gateway (OCI traffic via NAT)
4. NSG with unrestricted egress (all protocols, `0.0.0.0/0`)
5. VCN with insufficient or overlapping CIDR blocks

---

## Design Patterns

### Pattern: Private Subnet Serverless API

**Problem**: Functions must receive requests from internet clients without direct exposure. Functions must not have public IPs.

**Solution** (OCI Best Practices (current stable)):
```
Internet → IGW → [Public Subnet: API Gateway + NSG (443)] → [Private Subnet: Functions + NSG (from APIGW NSG only)]
                                                               ↕ Service Gateway → OCI Services (Vault, Object Storage)
                                                               ↕ NAT Gateway → External APIs (optional)
```

**Route Tables**:
- Public: `0.0.0.0/0 → Internet Gateway`
- Private: `0.0.0.0/0 → NAT Gateway` + `Service CIDR → Service Gateway`

**When to apply**: REST/HTTP APIs exposed to internet with serverless backend.
**When NOT to apply**: Long-lived WebSocket (>120s), compute-intensive batch jobs.
**Complements**: Resource Principals (IAM), WAF (DDoS protection), OCI Vault (secrets injection).
**Source**: https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsconfiguringnetworking.htm

---

### Pattern: Hub-Spoke with DRG v2

**Problem**: Multiple workloads/teams need network isolation (separate VCNs) but also controlled connectivity.

**Solution** (OCI Best Practices (current stable)):
- DRG v2 as central routing hub (free, supports 300 attachments)
- Hub VCN: shared services (DNS forwarder, Network Firewall, centralized egress)
- Spoke VCNs: one per workload or environment
- DRG Route Tables + Import Route Distributions for selective routing

**When to apply**: Enterprise multi-workload, shared services, compliance-mandated isolation.
**When NOT to apply**: Single-team projects with low isolation requirements.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/managingDRGs.htm

---

## Verification Loop

The agent MUST verify after each network configuration change:

### 1. Subnet Isolation Check
```bash
# Verify private subnet prohibits public IPs
oci network subnet get --subnet-id <ocid> | jq '.data["prohibit-public-ip-on-vnic"]'
# Exit code: 0 (success) | 1 (auth/network error)
# Expected: true

# Verify no IGW in private route table
oci network route-table get --rt-id <private-rt-ocid> | jq '.data["route-rules"][].["network-entity-id"]'
# Exit code: 0 (success) | 1 (auth/network error)
# Expected: only NAT GW and SGW OCIDs
```

### 2. Gateway Presence
```bash
# Verify three gateways exist in VCN
oci network internet-gateway list --compartment-id <ocid> --vcn-id <vcn-ocid>
# Exit code: 0 (success) | 1 (auth/network error)
oci network nat-gateway list --compartment-id <ocid> --vcn-id <vcn-ocid>
# Exit code: 0 (success) | 1 (auth/network error)
oci network service-gateway list --compartment-id <ocid> --vcn-id <vcn-ocid>
# Exit code: 0 (success) | 1 (auth/network error)
```

### 3. NSG Rule Audit
```bash
# Verify Functions NSG has no 0.0.0.0/0 ingress
oci network nsg rules list --nsg-id <functions-nsg-ocid> --direction INGRESS | \
# Exit code: 0 (success) | 1 (auth/network error)
  jq '.data[] | select(.source=="0.0.0.0/0")'
  # Exit code: 0 (success) | 1 (parse error) | 5 (no output)
# Expected: empty

# Verify no unrestricted egress
oci network nsg rules list --nsg-id <functions-nsg-ocid> --direction EGRESS | \
# Exit code: 0 (success) | 1 (auth/network error)
  jq '.data[] | select(.protocol=="all" and .destination=="0.0.0.0/0")'
  # Exit code: 0 (success) | 1 (parse error) | 5 (no output)
# Expected: empty
```

### 4. Connectivity Validation
```bash
# Use Path Analyzer for configuration-based validation
oci vn path-analyzer-test create --compartment-id <ocid> \
  --protocol TCP --source-endpoint '{"type":"SUBNET","address":"10.0.0.10","subnetId":"<pub-subnet>"}' \
  --destination-endpoint '{"type":"SUBNET","address":"10.0.1.10","subnetId":"<priv-subnet>"}' \
  --destination-port 443
```

**Troubleshooting**:
- Functions timeout on external API calls → missing NAT Gateway route
- Functions fail to pull Docker images from OCIR → missing Service Gateway
- API Gateway unreachable from internet → missing Internet Gateway or NSG 443 rule
- Functions receive traffic from unexpected sources → Functions NSG too permissive

---

## Quick Reference

### Critical Limits

| Resource | Limit | Scope |
|----------|-------|-------|
| VCNs per region | 50 | Tenancy |
| Subnets per VCN | 300 | VCN |
| NSGs per VCN | 1000 | VCN |
| Rules per NSG | 120 | NSG |
| NSGs per VNIC | 5 | VNIC |
| IGW / NAT GW / SGW per VCN | 1 each | VCN |
| CIDRs per VCN | 5 | VCN |
| DRG attachments | 300 | DRG |

### Cost Reference

| Component | Cost |
|-----------|------|
| VCN, Subnets, NSGs | Free |
| Internet Gateway | Free |
| Service Gateway | Free (data transfer free) |
| NAT Gateway | ~$0.013/hr (~$9.50/month) + $0.0085/GB data |
| Network Firewall | ~$580/month + $0.01/GB |
| DRG | Free |

---

## Skill Cross-References

| Need | Use Skill |
|------|-----------|
| Terraform provisioning of VCN, Subnets, Gateways, NSGs | `provisioning-oci-networking` |
| Terraform provisioning of IAM policies for network access | `provisioning-oci-iam` |
| API Gateway architecture and design decisions | `designing-oci-api-gateway` |
| Serverless architecture patterns | `architecting-oci-serverless` |

---

## Architecture Review Checklist

```
Architecture Validation:
- [ ] Verify network topology (VCN, subnets, NSGs)
- [ ] Verify IAM policies (dynamic groups, least-privilege)
- [ ] Verify security controls (encryption, auth, CORS)
- [ ] Verify observability (logging, monitoring, alerts)
- [ ] Verify cost controls (rate limiting, scaling limits)
```

## External Resources

### Official Documentation
- [VCN Overview](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/overview.htm) (verified 2026-07-26)
- [Subnets](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/Overview_of_VCNs_and_Subnets.htm) (verified 2026-07-26)
- [Network Security Groups](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/networksecuritygroups.htm) (verified 2026-07-26)
- [Security Lists](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/securitylists.htm) (verified 2026-07-26)
- [Internet Gateway](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/managingIGs.htm) (verified 2026-07-26)
- [NAT Gateway](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/NATgateway.htm) (verified 2026-07-26)
- [Service Gateway](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/servicegateway.htm) (verified 2026-07-26)
- [DRG v2](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/managingDRGs.htm) (verified 2026-07-26)
- [Route Tables](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/managingroutetables.htm) (verified 2026-07-26)
- [Functions Networking](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsconfiguringnetworking.htm) (verified 2026-07-26)
- [FastConnect](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/fastconnect.htm) (verified 2026-07-26)
- [Network Firewall](https://docs.oracle.com/en-us/iaas/Content/network_firewall/overview.htm) (verified 2026-07-26)
- [VCN Flow Logs](https://docs.oracle.com/en-us/iaas/Content/Logging/Reference/details_for_vcn_flow_logs.htm) (verified 2026-07-26)
- [Path Analyzer](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/path_analyzer.htm) (verified 2026-07-26)
- [Load Balancing](https://docs.oracle.com/en-us/iaas/Content/Balance/home.htm) (verified 2026-07-26)
