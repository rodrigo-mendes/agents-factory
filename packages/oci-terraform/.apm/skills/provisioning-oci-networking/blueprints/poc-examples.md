# Worked Examples — provisioning-oci-networking

Source: `workspace/poc-oci-serverless/infra/modules/network/`

---

## Worked example (from the reference PoC)

### VCN, Subnets, Gateways, Route Tables, NSGs — `infra/modules/network/main.tf`

The PoC uses a two-subnet model: a public subnet for the API Gateway and a private subnet for
Functions. NSGs enforce least-privilege east-west traffic between gateway and functions.

```hcl
# from infra/modules/network/main.tf

resource "oci_core_vcn" "this" {
  compartment_id = var.compartment_ocid
  cidr_blocks    = [var.vcn_cidr_block]   # list — not the deprecated cidr_block string
  display_name   = "vcn-${var.project_name}-${var.environment}"
  dns_label      = "serverless"
  freeform_tags  = var.tags
}

# Route Tables: public (via IGW) and private (via NAT + Service GW)
resource "oci_core_route_table" "public" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.this.id
  display_name   = "rt-public-${var.environment}"
  route_rules {
    network_entity_id = oci_core_internet_gateway.this.id
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
  }
  freeform_tags = var.tags
}

resource "oci_core_route_table" "private" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.this.id
  display_name   = "rt-private-${var.environment}"
  dynamic "route_rules" {
    for_each = var.create_nat_gateway ? [1] : []
    content {
      network_entity_id = oci_core_nat_gateway.this[0].id
      destination       = "0.0.0.0/0"
      destination_type  = "CIDR_BLOCK"
    }
  }
  route_rules {
    network_entity_id = oci_core_service_gateway.this.id
    destination       = data.oci_core_services.all_services.services[0].cidr_block
    destination_type  = "SERVICE_CIDR_BLOCK"
  }
  freeform_tags = var.tags
}

# Subnets
resource "oci_core_subnet" "public" {
  compartment_id             = var.compartment_ocid
  vcn_id                     = oci_core_vcn.this.id
  cidr_block                 = var.subnet_public_cidr
  display_name               = "subnet-apigw-public-${var.environment}"
  dns_label                  = "apigw"
  prohibit_public_ip_on_vnic = false
  route_table_id             = oci_core_route_table.public.id
  security_list_ids          = [oci_core_security_list.public.id]
  freeform_tags              = var.tags
}

resource "oci_core_subnet" "private" {
  compartment_id             = var.compartment_ocid
  vcn_id                     = oci_core_vcn.this.id
  cidr_block                 = var.subnet_private_cidr
  display_name               = "subnet-functions-private-${var.environment}"
  dns_label                  = "functions"
  prohibit_public_ip_on_vnic = true
  route_table_id             = oci_core_route_table.private.id
  security_list_ids          = [oci_core_security_list.private.id]
  freeform_tags              = var.tags
}

# NSG: API Gateway — allows HTTPS from internet, egress to Functions subnet only
resource "oci_core_network_security_group" "apigw" {
  count          = var.use_nsg ? 1 : 0
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.this.id
  display_name   = "nsg-apigw-${var.project_name}-${var.environment}"
  freeform_tags  = var.tags
}

# NSG: Functions — ingress only from API Gateway NSG (source_type = NETWORK_SECURITY_GROUP)
resource "oci_core_network_security_group" "functions" {
  count          = var.use_nsg ? 1 : 0
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.this.id
  display_name   = "nsg-functions-${var.project_name}-${var.environment}"
  freeform_tags  = var.tags
}

resource "oci_core_network_security_group_security_rule" "functions_ingress_apigw" {
  count                     = var.use_nsg ? 1 : 0
  network_security_group_id = oci_core_network_security_group.functions[0].id
  direction                 = "INGRESS"
  protocol                  = "6"
  source                    = oci_core_network_security_group.apigw[0].id
  source_type               = "NETWORK_SECURITY_GROUP"   # NSG-to-NSG reference
  stateless                 = false
  description               = "Allow traffic from API Gateway NSG only"
  tcp_options {
    destination_port_range { min = 443; max = 443 }
  }
}
```

**Key patterns from this example:**
- `cidr_blocks` (list) is used instead of the deprecated `cidr_block` string on `oci_core_vcn`.
- NAT gateway is conditional (`var.create_nat_gateway`) — private subnets without outbound access use Service GW only.
- NSG rules use `source_type = "NETWORK_SECURITY_GROUP"` for east-west restrictions (preferred over CIDR-based security lists for dynamic architectures).
- Regional subnets (no `availability_domain`) — Oracle's recommended approach.
