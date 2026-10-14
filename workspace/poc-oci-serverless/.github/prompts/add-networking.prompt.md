---
description: 'Provision OCI networking resources (VCN + Subnets + NSGs + Gateways + Route Tables) with Terraform'
agent: oci-terraform
argument-hint: 'CIDR blocks, public/private subnets, required gateways'
---

# Add Networking

**Skill**: `provisioning-oci-networking`

## What this does

Provisions OCI networking infrastructure (VCN, Subnets, Gateways, Route Tables, NSGs) with Terraform for serverless architectures.

## Required information

1. **New VCN or existing?**: Create a new VCN or add to existing?
2. **CIDR blocks**: VCN CIDR and subnet CIDRs
3. **Subnet type**: Public, private, or both?
4. **Gateways needed**:
   - Internet Gateway (public subnets)
   - NAT Gateway (private subnets with outbound internet)
   - Service Gateway (OCI service access)
5. **NSG rules**: Which ports/protocols to allow? (e.g., HTTPS 443 ingress)
6. **Compartment**: Target compartment OCID

## What will be generated

- `oci_core_vcn` resource (if new VCN)
- `oci_core_subnet` resources (public and/or private)
- Gateway resources (Internet, NAT, Service as needed)
- `oci_core_route_table` with proper route rules
- `oci_core_network_security_group` with ingress/egress rules
- Variables with CIDR and OCID validation
