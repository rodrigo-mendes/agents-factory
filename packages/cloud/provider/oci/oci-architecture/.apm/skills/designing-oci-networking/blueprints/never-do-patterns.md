# Never Do Anti-Patterns — OCI Networking Architecture

## 1. Anti-Pattern: Security List with 0.0.0.0/0 ingress on all ports

Exposing ALL resources in a subnet to ALL internet traffic on ALL protocols is a critical violation of least-privilege (CIS OCI Benchmark, SOC2 CC6.1).

**Correct approach**: Use NSGs with specific port and source restrictions. API Gateway: allow ONLY TCP 443 from internet. Functions: allow ONLY from API Gateway NSG.

**Detection**:
```bash
oci network security-list list --compartment-id <ocid> --all | \
  jq '.data[]["ingress-security-rules"][] | select(.source=="0.0.0.0/0" and .protocol=="all")'
# Expected: empty (no results)
```

**Source**: https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/securitylists.htm

---

## 2. Anti-Pattern: Private subnet with route to Internet Gateway

Internet Gateway is for PUBLIC subnets only. Private subnets MUST use NAT Gateway for egress.

**Correct approach**: Private route table routes `0.0.0.0/0 → NAT Gateway` and `Service CIDR → Service Gateway`.

**Detection**:
```bash
# Find private subnets (prohibit-public-ip=true) then check their route tables for IGW
oci network subnet list --compartment-id <ocid> --all | \
  jq '.data[] | select(.["prohibit-public-ip-on-vnic"]==true) | .["route-table-id"]'
```

**Source**: https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/managingroutetables.htm

---

## 3. Anti-Pattern: Missing Service Gateway — OCI services traffic via NAT

Without Service Gateway, traffic for Object Storage, Vault, and OCIR traverses public internet unnecessarily. Service Gateway is **free** and strictly better.

**Correct approach**: Add Service Gateway route for OCI services alongside NAT Gateway route for external traffic.

**Detection**:
```bash
# Check if VCN has a Service Gateway
oci network service-gateway list --compartment-id <ocid> --vcn-id <vcn-ocid>
# If empty → anti-pattern present
```

**Actual impact**: Cost overrun (NAT data charges at $0.0085/GB), increased latency, security risk.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/servicegateway.htm

---

## 4. Anti-Pattern: NSG with unrestricted egress (all protocols, 0.0.0.0/0)

Unrestricted egress allows a compromised resource to exfiltrate data to any destination.

**Correct approach**: Restrict egress by destination and protocol — Service CIDR for OCI services, TCP 443 for external HTTPS only.

**Detection**:
```bash
oci network nsg rules list --nsg-id <ocid> --direction EGRESS | \
  jq '.data[] | select(.protocol=="all" and .destination=="0.0.0.0/0")'
# Expected: empty (no results)
```

**Source**: https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/networksecuritygroups.htm

---

## 5. Anti-Pattern: VCN with insufficient or overlapping CIDR blocks

A `/24` VCN has only 254 IPs — insufficient for production growth. Overlapping CIDRs prevent VCN peering and DRG connectivity.

**Correct approach**: Use `/16` VCN for production (~65,534 IPs). Plan CIDRs at 4x estimated usage. Verify non-overlap with on-premises and other VCNs.

**Source**: https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/Overview_of_VCNs_and_Subnets.htm
