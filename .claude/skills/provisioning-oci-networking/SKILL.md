---
name: provisioning-oci-networking
description: Provisions OCI networking resources (VCN, Subnets, Gateways, Route Tables, NSGs) with Terraform OCI Provider v6.x+. Use when provisioning network infrastructure for serverless architectures.
---

## Version Context

**Technology**: Terraform OCI Provider — Core Networking (`oci_core_*`)
**Terraform Version**: >= 1.7
**Provider Version**: oracle/oci >= 6.0, < 9.0
**Provider Registry**: https://registry.terraform.io/providers/oracle/oci/latest/docs
**Target Services**: `oci_core_vcn`, `oci_core_subnet`, `oci_core_internet_gateway`, `oci_core_nat_gateway`, `oci_core_service_gateway`, `oci_core_route_table`, `oci_core_security_list`, `oci_core_network_security_group`, `oci_core_drg`
**Support Status**: Active

**Breaking Changes / Deprecations**:
- `cidr_block` (singular) on `oci_core_vcn` — **DEPRECATED**. Use `cidr_blocks` (list). Cannot revert once migrated.
- `cidr_block` in `route_rules` — **DEPRECATED**. Use `destination` + `destination_type`.
- AD-specific subnets — **NOT RECOMMENDED**. Oracle mandates regional subnets (omit `availability_domain`).

**Critical Limits**:
| Resource | Limit | Scope |
|----------|-------|-------|
| VCNs per region | 50 | Tenancy |
| Subnets per VCN | 300 | VCN |
| NSGs per VCN | 1000 | VCN |
| Rules per NSG | 120 | NSG |
| NSGs per VNIC | 5 | VNIC |
| Rules per Security List | 200 | Security List |
| IGW / NAT GW / SGW per VCN | 1 each | VCN |
| CIDRs per VCN | 5 | VCN |

⚠️ **CRITICAL — Agent Warning**:
This skill targets Terraform OCI Provider v6.x+ for networking resources. Always use `cidr_blocks` (list, not singular), `destination` + `destination_type` in route rules, regional subnets (omit `availability_domain`), and NSGs as primary security mechanism. Reject deprecated arguments.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — Mandatory implementation patterns
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — Architectural decisions requiring context
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — Anti-patterns with alternatives
- **[Integration Patterns](./blueprints/integration-patterns.md)** — Module interface, cross-module wiring, import commands
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — Canonical, edge case, and misuse test cases
- **[Verification Loop](#verification-loop)** — Validation commands and expected outputs
- **[Quick Reference](#quick-reference)** — Most used patterns at a glance
- **[External Resources](#external-resources)** — Official documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

For complete patterns with code examples, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**Summary of mandatory patterns**:
- **Provider Version Constraint** — Pin `>= 6.0, < 9.0`. Networking is foundational for all services
- **VCN with `cidr_blocks` (list)** — Singular `cidr_block` is deprecated. DNS label required for internal resolution
- **Regional Subnets** — Omit `availability_domain` for cross-AD HA. Private subnets MUST set `prohibit_internet_ingress = true`
- **Three-Gateway Topology** — IGW (public ingress), NAT GW (private egress), SGW (Oracle Services). Functions need SGW for OCIR, Vault, Logging
- **Route Tables with `destination` + `destination_type`** — `cidr_block` in route_rules is deprecated. Use `SERVICE_CIDR_BLOCK` for SGW routes
- **NSGs as Primary Security** — VNIC-level microsegmentation with inter-NSG references. Separate NSGs per service (API GW, Functions)
- **Minimal Security Lists** — Baseline only. NSGs + Security Lists use UNION logic (most permissive wins)

---

### ⚠️ Ask First

For complete decision matrices with code examples, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

**Summary of decision points**:
- **NAT Gateway** — Required only if Functions call external (non-OCI) APIs. SGW alone suffices for OCI Services
- **NSG vs Security List vs Network Firewall** — NSG primary + SL baseline (recommended). Network Firewall for DPI/IDS/IPS compliance
- **DRG (Dynamic Routing Gateway)** — Only for hybrid/on-premises connectivity or multi-VCN peering
- **VCN Flow Logs** — Production/compliance environments. Storage cost consideration for dev/test

---

### 🚫 Never Do

For complete anti-patterns with code examples, see [Never Do Patterns](./blueprints/never-do-patterns.md).

**Summary of prohibited patterns**:
- **`cidr_block` (singular) on VCN** — Deprecated, no multi-CIDR support, will be removed
- **Deprecated `cidr_block` in route_rules** — Use `destination` + `destination_type`
- **AD-specific subnets** — Eliminates cross-AD HA. Always use regional (omit `availability_domain`)
- **Private subnet without `prohibit_internet_ingress`** — Defaults to false, making "private" subnets public
- **Service Gateway with only Object Storage** — Functions need OCIR, Vault, Streaming, Logging. Use "All Services"
- **Security List `0.0.0.0/0` all protocols** — Catastrophic blast radius. Restrict to TCP/443
- **Stateless NSG rules without matching pair** — Return traffic silently dropped. Use stateful (default)

---

## Verification Loop

The agent MUST execute after each network infrastructure generation:

### 1. Validate Configuration
```bash
terraform validate
# Exit code: 0 (valid) | 1 (invalid configuration)
```
**Expected output**: `Success! The configuration is valid.`
**Exit code**: 0

### 2. Plan with Detailed Output
```bash
terraform plan -out=plan.tfplan
# Exit code: 0 (no changes) | 1 (error) | 2 (changes pending)
```
**Expected output**: Resource creation plan with no errors
**Exit code**: 0

### 3. Verify VCN
```bash
oci network vcn list \
  --compartment-id $COMPARTMENT_OCID \
  --query 'data[*].{"name":"display-name","cidr":"cidr-blocks","state":"lifecycle-state"}' \
  --output table
# Exit code: 0 (success) | 1 (auth/network error)
```

### 4. Verify Subnets
```bash
oci network subnet list \
  --compartment-id $COMPARTMENT_OCID \
  --vcn-id $VCN_OCID \
  --query 'data[*].{"name":"display-name","cidr":"cidr-block","prohibit-ingress":"prohibit-internet-ingress"}' \
  --output table
# Exit code: 0 (success) | 1 (auth/network error)
```

### 5. Verify Gateways
```bash
oci network internet-gateway list --compartment-id $COMPARTMENT_OCID --vcn-id $VCN_OCID --output table
oci network nat-gateway list --compartment-id $COMPARTMENT_OCID --vcn-id $VCN_OCID --output table
oci network service-gateway list --compartment-id $COMPARTMENT_OCID --vcn-id $VCN_OCID --output table
# Exit code: 0 (success) | 1 (auth/network error)
```

### 6. Verify NSGs and Rules
```bash
oci network nsg list --compartment-id $COMPARTMENT_OCID --vcn-id $VCN_OCID --output table
oci network nsg rules list --nsg-id $NSG_OCID --output table
# Exit code: 0 (success) | 1 (auth/network error)
```

### 7. Verify Route Tables
```bash
oci network route-table list \
  --compartment-id $COMPARTMENT_OCID \
  --vcn-id $VCN_OCID \
  --query 'data[*].{"name":"display-name","rules":"route-rules[*].destination"}' \
  --output table
# Exit code: 0 (success) | 1 (auth/network error)
```

### 8. State Verification
```bash
terraform state list | grep "module.network"
# Exit code: 0 (success) | 1 (error)
```

**Troubleshooting**:
- **Functions timeout calling external APIs** → NAT Gateway missing or `block_traffic = true`. Create NAT GW, verify route rule `0.0.0.0/0 → NAT GW`.
- **Functions can't pull Docker images** → Service Gateway not configured with "All Services". Use `"All .* Services In Oracle Services Network"` filter.
- **API Gateway returns 502** → NSG missing egress to Functions or Functions NSG missing ingress from APIGW NSG. Add inter-NSG rules.
- **Terraform wants to destroy/recreate VCN** → Changed `cidr_block` → `cidr_blocks` or modified DNS label (immutable). Use `moved` block for CIDR migration.
- **Route table conflict** → Multiple rules for same destination. Ensure no overlapping `destination` in route_rules.
- **Subnet destroy fails** → Resources still attached (Functions, API GW). Destroy dependent resources first.

---

## Quick Reference

**Protocol numbers for NSG/Security List rules**:
| Protocol | Number |
|----------|--------|
| TCP | `"6"` |
| UDP | `"17"` |
| ICMP | `"1"` |
| All | `"all"` |

**Resource naming convention**:
```
vcn-{project}-{env}
sn-public-{project}-{env}
sn-private-{project}-{env}
igw-{project}-{env}
natgw-{project}-{env}
sgw-{project}-{env}
rt-public-{project}-{env}
rt-private-{project}-{env}
nsg-apigw-{project}-{env}
nsg-functions-{project}-{env}
sl-public-{project}-{env}
sl-private-{project}-{env}
```

**Essential data sources**:
```hcl
# All Oracle Services for Service Gateway
data "oci_core_services" "all" {
  filter {
    name   = "name"
    values = ["All .* Services In Oracle Services Network"]
    regex  = true
  }
}
```

---

## Deployment Workflow

```
Provisioning Progress:
- [ ] terraform init -upgrade
- [ ] terraform fmt -recursive -check (exit 0)
- [ ] terraform validate (exit 0)
- [ ] terraform plan -out=tfplan (review)
- [ ] terraform apply tfplan
- [ ] Verify resources via OCI CLI
- [ ] Validate NSG rules (no 0.0.0.0/0 on private ingress)
- [ ] Verify Service Gateway route present in private route table
- [ ] Commit state and tag release
```

## External Resources

### Official Documentation
- [OCI Provider Registry — Networking](https://registry.terraform.io/providers/oracle/oci/latest/docs) (verified 2026-07-26)
- [oci_core_vcn](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/core_vcn) (verified 2026-07-26)
- [oci_core_subnet](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/core_subnet) (verified 2026-07-26)
- [oci_core_internet_gateway](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/core_internet_gateway) (verified 2026-07-26)
- [oci_core_nat_gateway](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/core_nat_gateway) (verified 2026-07-26)
- [oci_core_service_gateway](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/core_service_gateway) (verified 2026-07-26)
- [oci_core_route_table](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/core_route_table) (verified 2026-07-26)
- [oci_core_security_list](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/core_security_list) (verified 2026-07-26)
- [oci_core_network_security_group](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/core_network_security_group) (verified 2026-07-26)
- [oci_core_network_security_group_security_rule](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/core_network_security_group_security_rule) (verified 2026-07-26)
- [oci_core_drg](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/core_drg) (verified 2026-07-26)

### Architecture & Best Practices
- [OCI Networking Overview](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/overview.htm) (verified 2026-07-26)
- [OCI VCN Best Practices](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/bestpractices.htm) (verified 2026-07-26)
- [OCI Security Lists vs NSGs](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/networksecuritygroups.htm) (verified 2026-07-26)
