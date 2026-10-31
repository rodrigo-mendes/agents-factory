# Always Do Patterns — OCI Networking Architecture

## 1. VCN with Public/Private Subnet Separation

Resources receiving internet traffic (API Gateway, Load Balancer) MUST be in public subnets. Backend resources (Functions, DB, Compute) MUST be in private subnets with no public IP.

**Required topology**:
- **Public subnet**: `prohibit_public_ip_on_vnic = false`, route table with Internet Gateway, hosts API Gateway
- **Private subnet**: `prohibit_public_ip_on_vnic = true`, `prohibit_internet_ingress = true`, route table with NAT Gateway + Service Gateway, hosts Functions
- **Both subnets**: Regional (omit `availability_domain`), use DNS labels for internal resolution

**Verification**:
```bash
# Validate private subnet prohibits public IPs
oci network subnet get --subnet-id <ocid> | jq '.data["prohibit-public-ip-on-vnic"]'
# Expected: true

# Validate private subnet route table has NO IGW rule
oci network route-table get --rt-id <private-rt-ocid> | jq '.data["route-rules"][].["network-entity-id"]'
# Expected: only NAT GW and SGW OCIDs — no IGW
```

**Why it is mandatory**: OCI Best Practices Framework requires segregation of internet-facing and backend tiers. Functions in public subnets is a security violation.
**Failure if omitted**: Direct exposure of backend resources to internet traffic — data breach risk.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/overview.htm

> 📎 **Implementation**: For Terraform provisioning of VCN, Subnets, and Route Tables, use the skill `provisioning-oci-networking`.

---

## 2. Service Gateway for Oracle Services Access

All VCNs with private subnets MUST have a Service Gateway. Traffic to OCI services (Object Storage, Vault, OCIR, Autonomous DB) stays on Oracle backbone — never traverses internet.

**Required configuration**:
- Service Gateway with "All Services In Oracle Services Network"
- Route rule in private route table: destination = Service CIDR → Service Gateway
- Service Gateway is **FREE** — no cost for data transferred

**Verification**:
```bash
# Verify Service Gateway exists and is AVAILABLE
oci network service-gateway list --compartment-id <ocid> --vcn-id <vcn-ocid>

# Verify private route table has Service CIDR rule
oci network route-table get --rt-id <private-rt-ocid> | \
  jq '.data["route-rules"][] | select(.["destination-type"]=="SERVICE_CIDR_BLOCK")'
```

**Why it is mandatory**: Without Service Gateway, OCI-to-OCI traffic goes via NAT Gateway → internet → back to OCI. This is insecure (traverses public internet), slower (extra hops), and costly (NAT data processing at $0.0085/GB).
**Failure if omitted**: Security risk (data in transit over internet), increased latency, unnecessary NAT costs.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/servicegateway.htm

---

## 3. NSGs as Primary Network Security Mechanism

Use Network Security Groups (not Security Lists) for micro-segmentation. NSGs attach to individual VNICs and support inter-NSG references for granular tier-to-tier control.

**Required NSG architecture for serverless**:
- **NSG for API Gateway**: Ingress TCP 443 from `0.0.0.0/0`; Egress TCP to Functions NSG
- **NSG for Functions**: Ingress TCP only from API Gateway NSG (inter-NSG reference); Egress TCP 443 to Service CIDR + optionally to `0.0.0.0/0` for external APIs
- Use separate `oci_core_network_security_group_security_rule` resources for each rule (not inline)

**Verification**:
```bash
# List NSG rules — verify no 0.0.0.0/0 on Functions NSG ingress
oci network nsg rules list --nsg-id <functions-nsg-ocid> --direction INGRESS | \
  jq '.data[] | select(.source=="0.0.0.0/0")'
# Expected: empty (no results)
```

**Why it is mandatory**: NSGs are more granular than Security Lists — associated per VNIC, support inter-NSG references, and enable zero-trust micro-segmentation. Security Lists are subnet-wide and overly broad.
**Failure if omitted**: Using Security Lists alone allows any resource in the subnet to communicate, breaking blast-radius containment.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/networksecuritygroups.htm

> 📎 **Implementation**: For Terraform provisioning of NSGs and security rules, use the skill `provisioning-oci-networking`.

---

## 4. NAT Gateway for Private Subnet Egress

Private subnets that need internet egress (pull container images, call external APIs) MUST use NAT Gateway — never Internet Gateway.

**Key properties**:
- NAT Gateway is unidirectional — provides Source NAT for egress, no inbound from internet
- Route in private route table: `0.0.0.0/0 → NAT Gateway`
- `block_traffic = true` can be used as emergency kill-switch
- Cost: ~$0.013/hr (~$9.50/month) + $0.0085/GB data processing

**Verification**:
```bash
# Verify NAT Gateway exists and is AVAILABLE
oci network nat-gateway list --compartment-id <ocid> --vcn-id <vcn-ocid>

# Verify private route table has 0.0.0.0/0 → NAT GW
oci network route-table get --rt-id <private-rt-ocid> | \
  jq '.data["route-rules"][] | select(.destination=="0.0.0.0/0")'
```

**Why it is mandatory**: Functions in private subnets cannot reach external registries or APIs without NAT Gateway. Internet Gateway requires public IP for ingress and violates private subnet isolation.
**Failure if omitted**: Functions in private subnets cannot reach external registries or APIs.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/NATgateway.htm

---

## 5. VCN Flow Logs Enabled

Flow Logs MUST be enabled on all subnets with sensitive traffic for security monitoring, troubleshooting, and compliance auditing.

**Verification**:
```bash
# Verify flow logs are enabled for subnet
oci logging log list --log-group-id <ocid> --log-type SERVICE
oci logging log-group list --compartment-id <ocid> | \
  jq '.data[] | select(."display-name" | contains("flow"))'
```

**Why it is mandatory**: Without Flow Logs, there is zero visibility into network traffic — impossible to detect unauthorized access attempts, validate security rules, or troubleshoot connectivity.
**Failure if omitted**: Security blind spot, inability to diagnose connectivity issues, compliance gap (audit trail missing).
**Cost**: First 10GB/month free; ~$0.05/GB after. Volume can be high in busy VCNs.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Logging/Reference/details_for_vcn_flow_logs.htm
