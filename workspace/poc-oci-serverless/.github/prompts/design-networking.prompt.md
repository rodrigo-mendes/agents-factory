---
description: 'Design or review OCI network architecture (VCN, Subnets, NSGs, Gateways, DRG) for serverless workloads'
agent: oci-serverless-architect
argument-hint: 'Connectivity requirements, security zones, existing topology'
---

# Design Networking

**Skill**: `designing-oci-networking`

## What this does

Designs or reviews OCI network architecture for serverless workloads — VCN topology, subnet strategy, security groups, and gateway placement.

## Required information

1. **Connectivity requirements**:
   - Internet access (inbound, outbound, or both)
   - Cross-VCN communication (VCN peering or DRG)
   - On-premises connectivity (FastConnect or VPN)
   - OCI service access (Service Gateway)
2. **Security zones**: Any OCI Security Zone requirements?
3. **Existing topology**: Current VCN, subnets, gateways in place?
4. **Workload placement**: Which services go in public vs private subnets?
5. **Compliance**: Network isolation requirements? (PCI, HIPAA, etc.)

## What will be delivered

- VCN topology design with CIDR planning
- Subnet strategy (public/private, purpose-specific)
- NSG rules recommendation (least-privilege network access)
- Gateway placement (Internet, NAT, Service, DRG)
- Route table design
- Implementation guidance with `@oci-terraform` for provisioning
