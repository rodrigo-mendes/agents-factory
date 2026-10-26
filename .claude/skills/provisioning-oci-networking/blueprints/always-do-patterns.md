### ✅ Always Do

## Contents
1. Provider Configuration with Version Constraints
2. VCN with cidr_blocks (List), DNS Label, and Tags
3. Regional Subnets with Public/Private Separation
4. Gateways: Internet Gateway + NAT Gateway + Service Gateway
5. Route Tables with destination + destination_type
6. NSGs as Primary Security Mechanism
7. Security Lists as Minimal Baseline

---

**Provider Configuration with Version Constraints**: Networking is foundational — all services depend on VCN/Subnet. Pin the provider version to avoid breaking changes.

```hcl
# ✅ CORRECT: Provider version constrained for networking stability (OCI Provider v6.x+)
terraform {
  required_version = ">= 1.7"

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 6.0, < 9.0"
    }
  }
}
```
**Why it is mandatory**: Networking resources are foundational; unconstrained provider upgrades can introduce breaking changes that destroy infrastructure.
**Failure if omitted**: Terraform may pull a major version with incompatible schema, causing plan failures or unintended resource recreation.
**Source**: [OCI Provider Registry](https://registry.terraform.io/providers/oracle/oci/latest/docs)

---

**VCN with `cidr_blocks` (List), DNS Label, and Tags**: The singular `cidr_block` is deprecated and does not support multi-CIDR. DNS label is required for internal hostname resolution.

```hcl
# ✅ CORRECT: cidr_blocks as LIST (not singular) — required since OCI Provider v6.x
resource "oci_core_vcn" "main" {
  compartment_id = var.compartment_ocid
  cidr_blocks    = [var.vcn_cidr_block]  # LIST format, supports multi-CIDR
  display_name   = "vcn-${var.project_name}-${var.environment}"
  dns_label      = var.vcn_dns_label      # Required for internal DNS resolution

  freeform_tags = var.tags
}
```
**Why it is mandatory**: `cidr_block` (singular) is deprecated, does not support multi-CIDR, and will be removed. Once migrated to `cidr_blocks`, reverting is impossible.
**Failure if omitted**: Terraform plan may report constant diff; future provider versions will reject `cidr_block` entirely.
**Source**: [oci_core_vcn](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/core_vcn)

---

**Regional Subnets with Public/Private Separation**: Subnets MUST be regional (omit `availability_domain`) for cross-AD HA. Private subnets MUST enforce `prohibit_internet_ingress = true`.

```hcl
# ✅ CORRECT: Regional subnets (no availability_domain) with public/private separation
# Public Subnet — API Gateway, Load Balancers
resource "oci_core_subnet" "public" {
  compartment_id             = var.compartment_ocid
  vcn_id                     = oci_core_vcn.main.id
  cidr_block                 = var.subnet_public_cidr
  display_name               = "sn-public-${var.project_name}-${var.environment}"
  dns_label                  = "pub"
  prohibit_internet_ingress  = false
  prohibit_public_ip_on_vnic = false
  route_table_id             = oci_core_route_table.public.id
  security_list_ids          = [oci_core_security_list.public.id]

  freeform_tags = var.tags
}

# Private Subnet — Functions, Compute, DB
resource "oci_core_subnet" "private" {
  compartment_id             = var.compartment_ocid
  vcn_id                     = oci_core_vcn.main.id
  cidr_block                 = var.subnet_private_cidr
  display_name               = "sn-private-${var.project_name}-${var.environment}"
  dns_label                  = "priv"
  prohibit_internet_ingress  = true   # MANDATORY for private subnet
  prohibit_public_ip_on_vnic = true   # MANDATORY for private subnet
  route_table_id             = oci_core_route_table.private.id
  security_list_ids          = [oci_core_security_list.private.id]

  freeform_tags = var.tags
}
```
**Why it is mandatory**: AD-specific subnets eliminate cross-AD failover. Without `prohibit_internet_ingress`, private subnets can receive public IPs, negating their "private" classification.
**Failure if omitted**: Single-AD failure takes down all resources; private subnets become publicly accessible.
**Source**: [oci_core_subnet](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/core_subnet)

---

**Gateways: Internet Gateway + NAT Gateway + Service Gateway**: Three-gateway topology for serverless: IGW (public ingress), NAT GW (private egress), SGW (Oracle Services access without internet).

```hcl
# ✅ CORRECT: Internet Gateway for public subnet (OCI Provider v6.x+)
resource "oci_core_internet_gateway" "main" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id
  display_name   = "igw-${var.project_name}-${var.environment}"
  enabled        = true

  freeform_tags = var.tags
}

# ✅ CORRECT: NAT Gateway for private subnet egress
resource "oci_core_nat_gateway" "main" {
  count = var.create_nat_gateway ? 1 : 0

  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id
  display_name   = "natgw-${var.project_name}-${var.environment}"
  block_traffic  = false  # true = emergency kill-switch

  freeform_tags = var.tags
}

# ✅ CORRECT: Service Gateway with "All Services" — required for Functions (OCIR, Vault, Logging)
data "oci_core_services" "all" {
  filter {
    name   = "name"
    values = ["All .* Services In Oracle Services Network"]
    regex  = true
  }
}

resource "oci_core_service_gateway" "main" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id
  display_name   = "sgw-${var.project_name}-${var.environment}"

  services {
    service_id = data.oci_core_services.all.services[0].id
  }

  freeform_tags = var.tags
}
```
**Why it is mandatory**: Functions in private subnets need NAT GW for external API calls and SGW for Oracle Services (OCIR image pull, Vault secrets, Logging). API Gateway in public subnet needs IGW for internet ingress.
**Failure if omitted**: Functions timeout on external API calls (no NAT GW), fail to pull Docker images from OCIR (no SGW), API Gateway unreachable (no IGW).
**Source**: [oci_core_internet_gateway](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/core_internet_gateway), [oci_core_nat_gateway](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/core_nat_gateway), [oci_core_service_gateway](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/core_service_gateway)

---

**Route Tables with `destination` + `destination_type`**: The `cidr_block` argument in route_rules is deprecated. Always use `destination` + `destination_type`.

```hcl
# ✅ CORRECT: Route Table for public subnet — IGW route (OCI Provider v6.x+)
resource "oci_core_route_table" "public" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id
  display_name   = "rt-public-${var.project_name}-${var.environment}"

  route_rules {
    network_entity_id = oci_core_internet_gateway.main.id
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    description       = "Internet access via IGW"
  }

  freeform_tags = var.tags
}

# ✅ CORRECT: Route Table for private subnet — NAT GW + Service GW
resource "oci_core_route_table" "private" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id
  display_name   = "rt-private-${var.project_name}-${var.environment}"

  dynamic "route_rules" {
    for_each = var.create_nat_gateway ? [1] : []
    content {
      network_entity_id = oci_core_nat_gateway.main[0].id
      destination       = "0.0.0.0/0"
      destination_type  = "CIDR_BLOCK"
      description       = "Internet egress via NAT GW"
    }
  }

  route_rules {
    network_entity_id = oci_core_service_gateway.main.id
    destination       = data.oci_core_services.all.services[0].cidr_block
    destination_type  = "SERVICE_CIDR_BLOCK"
    description       = "Access Oracle Services via SGW"
  }

  freeform_tags = var.tags
}
```
**Why it is mandatory**: `cidr_block` in route_rules is deprecated. `destination_type` supports both `CIDR_BLOCK` and `SERVICE_CIDR_BLOCK`, required for Service Gateway routes.
**Failure if omitted**: Terraform plan warnings, eventual removal in future provider versions, inability to route to Oracle Services.
**Source**: [oci_core_route_table](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/core_route_table)

---

**NSGs as Primary Security Mechanism**: NSGs operate at VNIC level (resource-level microsegmentation), superior to Security Lists (subnet-level). Use separate `oci_core_network_security_group_security_rule` resources for granular management.

```hcl
# ✅ CORRECT: NSG for API Gateway with inter-NSG rules (OCI Provider v6.x+)
resource "oci_core_network_security_group" "apigw" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id
  display_name   = "nsg-apigw-${var.project_name}-${var.environment}"

  freeform_tags = var.tags
}

# Allow HTTPS ingress from internet to API Gateway
resource "oci_core_network_security_group_security_rule" "apigw_ingress_https" {
  network_security_group_id = oci_core_network_security_group.apigw.id
  direction                 = "INGRESS"
  protocol                  = "6"  # TCP
  source                    = "0.0.0.0/0"
  source_type               = "CIDR_BLOCK"
  description               = "Allow HTTPS from internet"
  stateless                 = false

  tcp_options {
    destination_port_range {
      min = 443
      max = 443
    }
  }
}

# Allow egress from API Gateway to Functions NSG
resource "oci_core_network_security_group_security_rule" "apigw_egress_functions" {
  network_security_group_id = oci_core_network_security_group.apigw.id
  direction                 = "EGRESS"
  protocol                  = "6"  # TCP
  destination               = oci_core_network_security_group.functions.id
  destination_type          = "NETWORK_SECURITY_GROUP"
  description               = "Allow traffic to Functions"
  stateless                 = false

  tcp_options {
    destination_port_range {
      min = 443
      max = 443
    }
  }
}

# ✅ CORRECT: NSG for Functions with ingress restricted to API Gateway NSG
resource "oci_core_network_security_group" "functions" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id
  display_name   = "nsg-functions-${var.project_name}-${var.environment}"

  freeform_tags = var.tags
}

# Allow ingress ONLY from API Gateway NSG
resource "oci_core_network_security_group_security_rule" "functions_ingress_apigw" {
  network_security_group_id = oci_core_network_security_group.functions.id
  direction                 = "INGRESS"
  protocol                  = "6"  # TCP
  source                    = oci_core_network_security_group.apigw.id
  source_type               = "NETWORK_SECURITY_GROUP"
  description               = "Allow HTTPS from API Gateway"
  stateless                 = false

  tcp_options {
    destination_port_range {
      min = 443
      max = 443
    }
  }
}

# Allow egress to Oracle Services (Object Storage, OCIR, Vault, etc.)
resource "oci_core_network_security_group_security_rule" "functions_egress_services" {
  network_security_group_id = oci_core_network_security_group.functions.id
  direction                 = "EGRESS"
  protocol                  = "6"  # TCP
  destination               = data.oci_core_services.all.services[0].cidr_block
  destination_type          = "SERVICE_CIDR_BLOCK"
  description               = "Allow egress to Oracle Services"
  stateless                 = false

  tcp_options {
    destination_port_range {
      min = 443
      max = 443
    }
  }
}
```
**Why it is mandatory**: NSGs enable VNIC-level firewall rules with inter-NSG references (source/destination = another NSG). Security Lists cannot achieve this granularity.
**Failure if omitted**: Overly broad subnet-level rules, inability to restrict Functions ingress to API Gateway only, violation of least-privilege.
**Source**: [oci_core_network_security_group](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/core_network_security_group), [oci_core_network_security_group_security_rule](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/core_network_security_group_security_rule)

---

**Security Lists as Minimal Baseline**: When NSGs are the primary mechanism, Security Lists should be minimal (baseline only). NSGs and Security Lists use UNION logic — the most permissive rule wins.

```hcl
# ✅ CORRECT: Minimal public Security List — NSGs handle specifics
resource "oci_core_security_list" "public" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id
  display_name   = "sl-public-${var.project_name}-${var.environment}"

  egress_security_rules {
    destination = "0.0.0.0/0"
    protocol    = "all"
    stateless   = false
    description = "Allow all egress"
  }

  ingress_security_rules {
    source      = "0.0.0.0/0"
    protocol    = "6"  # TCP
    stateless   = false
    description = "Allow HTTPS from internet"

    tcp_options {
      min = 443
      max = 443
    }
  }

  freeform_tags = var.tags
}

# ✅ CORRECT: Private Security List — only VCN-internal traffic
resource "oci_core_security_list" "private" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id
  display_name   = "sl-private-${var.project_name}-${var.environment}"

  egress_security_rules {
    destination = "0.0.0.0/0"
    protocol    = "all"
    stateless   = false
    description = "Allow all egress"
  }

  ingress_security_rules {
    source      = var.vcn_cidr_block
    protocol    = "6"  # TCP
    stateless   = false
    description = "Allow traffic from within VCN"

    tcp_options {
      min = 443
      max = 443
    }
  }

  freeform_tags = var.tags
}
```
**Why it is mandatory**: Security Lists provide baseline subnet-wide rules. They must remain minimal to avoid conflicting with NSG-level microsegmentation (UNION logic).
**Source**: [oci_core_security_list](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/core_security_list)

---

