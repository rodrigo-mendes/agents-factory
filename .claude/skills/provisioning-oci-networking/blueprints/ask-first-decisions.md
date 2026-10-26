### ⚠️ Ask First

**Decision Point**: NAT Gateway creation for private subnets

**Available Options**:
| Option | Optimizes For | Sacrifices | Choose When |
|--------|---------------|------------|-------------|
| NAT GW enabled | External API access from Functions | Cost (hourly + per-GB) | Functions call non-OCI external APIs |
| NAT GW disabled | Cost savings, security (no internet egress) | External connectivity | Functions only access OCI Services via SGW |
| NAT GW with `block_traffic = true` | Emergency kill-switch | Egress availability | Incident response — block all internet egress immediately |

**Agent Behavior**:
"Before configuring NAT Gateway, ask:
'Do your OCI Functions need to call external (non-OCI) APIs or services? If yes, a NAT Gateway is required for private subnet egress. If Functions only access OCI services (Object Storage, Vault, Streaming), the Service Gateway alone is sufficient.'"

**Decision Factors**:
- Whether Functions call third-party REST APIs
- Cost tolerance (NAT GW charges per hour + per GB)
- Security posture (zero internet egress vs. selective egress)

**Source**: [oci_core_nat_gateway](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/core_nat_gateway)

---

**Decision Point**: NSG vs Security List vs Network Firewall

**Available Options**:
| Option | Optimizes For | Sacrifices | Choose When |
|--------|---------------|------------|-------------|
| NSG (primary) + Security List (baseline) | Microsegmentation, inter-resource rules | Complexity | Most serverless architectures (recommended) |
| Security List only | Simplicity | Granularity | Simple/legacy workloads, PoCs |
| Network Firewall | DPI, IDS/IPS, URL filtering, TLS inspection | Cost (significant) | Compliance mandates (PCI-DSS, HIPAA) |

**Agent Behavior**:
"Before configuring network security, ask:
'Do you need deep packet inspection (DPI), IDS/IPS, or URL filtering? If yes, OCI Network Firewall is required. For standard serverless workloads, NSGs as primary with minimal Security Lists is the recommended pattern.'"

**Decision Factors**:
- Compliance requirements (PCI-DSS, HIPAA, SOC2)
- Budget for Network Firewall service
- Need for L7 inspection vs. L3/L4 port-based rules

**Source**: [oci_core_network_security_group](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/core_network_security_group)

---

**Decision Point**: DRG (Dynamic Routing Gateway) for hybrid connectivity

**Available Options**:
| Option | Optimizes For | Sacrifices | Choose When |
|--------|---------------|------------|-------------|
| No DRG | Simplicity, cost | On-premises connectivity | Cloud-native only, no hybrid |
| DRG with VPN | Encrypted tunnel to on-premises | Bandwidth (max ~1.25 Gbps per tunnel) | Dev/test hybrid connectivity |
| DRG with FastConnect | Dedicated low-latency link | Setup time, cost | Production hybrid with SLA requirements |
| DRG hub-and-spoke | Centralized transit routing | Complexity | Multi-VCN architectures |

**Agent Behavior**:
"Before creating a DRG, ask:
'Do you need connectivity to on-premises networks or peering between multiple VCNs? If this is a cloud-native serverless workload with no hybrid requirements, a DRG is unnecessary.'"

```hcl
# ⚠️ CONDITIONAL: DRG only when hybrid connectivity is needed
resource "oci_core_drg" "main" {
  count = var.create_drg ? 1 : 0

  compartment_id = var.compartment_ocid
  display_name   = "drg-${var.project_name}-${var.environment}"

  freeform_tags = var.tags
}

resource "oci_core_drg_attachment" "vcn" {
  count = var.create_drg ? 1 : 0

  drg_id       = oci_core_drg.main[0].id
  vcn_id       = oci_core_vcn.main.id
  display_name = "drg-att-vcn-${var.project_name}-${var.environment}"
}
```

**Source**: [oci_core_drg](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/core_drg)

---

**Decision Point**: VCN Flow Logs for network audit

**Available Options**:
| Option | Optimizes For | Sacrifices | Choose When |
|--------|---------------|------------|-------------|
| Flow Logs enabled | Audit trail, compliance, troubleshooting | Storage cost, log volume | Production, compliance environments (SOC2, PCI-DSS) |
| Flow Logs disabled | Cost savings | Visibility, audit capability | Dev/test environments |

**Agent Behavior**:
"Before enabling VCN Flow Logs, ask:
'Is this a production or compliance-regulated environment? Flow Logs provide network traffic audit trails but incur storage costs. For dev/test environments, they are typically unnecessary.'"

```hcl
# ⚠️ CONDITIONAL: Flow Logs for production/compliance environments
resource "oci_logging_log_group" "network" {
  compartment_id = var.compartment_ocid
  display_name   = "lg-network-${var.project_name}-${var.environment}"

  freeform_tags = var.tags
}

resource "oci_logging_log" "vcn_flow" {
  display_name = "flow-log-${var.project_name}-${var.environment}"
  log_group_id = oci_logging_log_group.network.id
  log_type     = "SERVICE"
  is_enabled   = true

  configuration {
    source {
      category    = "all"
      resource    = oci_core_subnet.private.id
      service     = "flowlogs"
      source_type = "OCISERVICE"
    }
  }

  freeform_tags = var.tags
}
```

**Source**: [OCI Logging](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/logging_log)

---

