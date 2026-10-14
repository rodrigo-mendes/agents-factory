# ==============================================================================
# Module: Network
# ==============================================================================
# VCN, Subnets, Gateways, Route Tables, Security Lists, NSGs
# ==============================================================================

# ------------------------------------------------------------------------------
# DATA SOURCES
# ------------------------------------------------------------------------------

data "oci_core_services" "all_services" {
  filter {
    name   = "name"
    values = ["All .* Services In Oracle Services Network"]
    regex  = true
  }
}

# ------------------------------------------------------------------------------
# VCN
# ------------------------------------------------------------------------------

resource "oci_core_vcn" "this" {
  compartment_id = var.compartment_ocid
  cidr_blocks    = [var.vcn_cidr_block]
  display_name   = "vcn-${var.project_name}-${var.environment}"
  dns_label      = "serverless"

  freeform_tags = var.tags
}

# ------------------------------------------------------------------------------
# Internet Gateway
# ------------------------------------------------------------------------------

resource "oci_core_internet_gateway" "this" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.this.id
  display_name   = "igw-${var.project_name}-${var.environment}"
  enabled        = true

  freeform_tags = var.tags
}

# ------------------------------------------------------------------------------
# NAT Gateway
# ------------------------------------------------------------------------------

resource "oci_core_nat_gateway" "this" {
  count = var.create_nat_gateway ? 1 : 0

  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.this.id
  display_name   = "natgw-${var.project_name}-${var.environment}"

  freeform_tags = var.tags
}

# ------------------------------------------------------------------------------
# Service Gateway
# ------------------------------------------------------------------------------

resource "oci_core_service_gateway" "this" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.this.id
  display_name   = "sgw-${var.project_name}-${var.environment}"

  services {
    service_id = data.oci_core_services.all_services.services[0].id
  }

  freeform_tags = var.tags
}

# ------------------------------------------------------------------------------
# Route Tables
# ------------------------------------------------------------------------------

resource "oci_core_route_table" "public" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.this.id
  display_name   = "rt-public-${var.environment}"

  route_rules {
    network_entity_id = oci_core_internet_gateway.this.id
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    description       = "Internet access via IGW"
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
      description       = "Internet access via NAT GW"
    }
  }

  route_rules {
    network_entity_id = oci_core_service_gateway.this.id
    destination       = data.oci_core_services.all_services.services[0].cidr_block
    destination_type  = "SERVICE_CIDR_BLOCK"
    description       = "OCI services via Service GW"
  }

  freeform_tags = var.tags
}

# ------------------------------------------------------------------------------
# Security Lists
# ------------------------------------------------------------------------------

resource "oci_core_security_list" "public" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.this.id
  display_name   = "sl-public-${var.environment}"

  ingress_security_rules {
    protocol    = "6"
    source      = "0.0.0.0/0"
    source_type = "CIDR_BLOCK"
    description = "HTTPS from internet"
    tcp_options {
      min = 443
      max = 443
    }
  }

  egress_security_rules {
    protocol         = "all"
    destination      = "0.0.0.0/0"
    destination_type = "CIDR_BLOCK"
    description      = "All egress"
  }

  freeform_tags = var.tags
}

resource "oci_core_security_list" "private" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.this.id
  display_name   = "sl-private-${var.environment}"

  ingress_security_rules {
    protocol    = "6"
    source      = var.subnet_public_cidr
    source_type = "CIDR_BLOCK"
    description = "HTTPS from API Gateway subnet"
    tcp_options {
      min = 443
      max = 443
    }
  }

  egress_security_rules {
    protocol         = "all"
    destination      = "0.0.0.0/0"
    destination_type = "CIDR_BLOCK"
    description      = "All egress (via NAT/Service GW)"
  }

  freeform_tags = var.tags
}

# ------------------------------------------------------------------------------
# Subnets
# ------------------------------------------------------------------------------

resource "oci_core_subnet" "public" {
  compartment_id             = var.compartment_ocid
  vcn_id                     = oci_core_vcn.this.id
  cidr_block                 = var.subnet_public_cidr
  display_name               = "subnet-apigw-public-${var.environment}"
  dns_label                  = "apigw"
  prohibit_public_ip_on_vnic = false
  route_table_id             = oci_core_route_table.public.id
  security_list_ids          = [oci_core_security_list.public.id]

  freeform_tags = var.tags
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

  freeform_tags = var.tags
}

# ------------------------------------------------------------------------------
# Network Security Groups (NSGs)
# ------------------------------------------------------------------------------

resource "oci_core_network_security_group" "apigw" {
  count = var.use_nsg ? 1 : 0

  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.this.id
  display_name   = "nsg-apigw-${var.project_name}-${var.environment}"

  freeform_tags = var.tags
}

resource "oci_core_network_security_group_security_rule" "apigw_ingress_https" {
  count = var.use_nsg ? 1 : 0

  network_security_group_id = oci_core_network_security_group.apigw[0].id
  direction                 = "INGRESS"
  protocol                  = "6"
  source                    = "0.0.0.0/0"
  source_type               = "CIDR_BLOCK"
  stateless                 = false
  description               = "Allow HTTPS from internet"

  tcp_options {
    destination_port_range {
      min = 443
      max = 443
    }
  }
}

resource "oci_core_network_security_group_security_rule" "apigw_egress_functions" {
  count = var.use_nsg ? 1 : 0

  network_security_group_id = oci_core_network_security_group.apigw[0].id
  direction                 = "EGRESS"
  protocol                  = "6"
  destination               = var.subnet_private_cidr
  destination_type          = "CIDR_BLOCK"
  stateless                 = false
  description               = "Allow traffic to Functions subnet"

  tcp_options {
    destination_port_range {
      min = 443
      max = 443
    }
  }
}

resource "oci_core_network_security_group" "functions" {
  count = var.use_nsg ? 1 : 0

  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.this.id
  display_name   = "nsg-functions-${var.project_name}-${var.environment}"

  freeform_tags = var.tags
}

resource "oci_core_network_security_group_security_rule" "functions_ingress_apigw" {
  count = var.use_nsg ? 1 : 0

  network_security_group_id = oci_core_network_security_group.functions[0].id
  direction                 = "INGRESS"
  protocol                  = "6"
  source                    = oci_core_network_security_group.apigw[0].id
  source_type               = "NETWORK_SECURITY_GROUP"
  stateless                 = false
  description               = "Allow traffic from API Gateway NSG only"

  tcp_options {
    destination_port_range {
      min = 443
      max = 443
    }
  }
}

resource "oci_core_network_security_group_security_rule" "functions_ingress_self" {
  count = var.use_nsg ? 1 : 0

  network_security_group_id = oci_core_network_security_group.functions[0].id
  direction                 = "INGRESS"
  protocol                  = "6"
  source                    = oci_core_network_security_group.functions[0].id
  source_type               = "NETWORK_SECURITY_GROUP"
  stateless                 = false
  description               = "Allow intra-NSG HTTPS (Functions -> Stream Pool private endpoint on same NSG)"

  tcp_options {
    destination_port_range {
      min = 443
      max = 443
    }
  }
}

resource "oci_core_network_security_group_security_rule" "functions_egress_all" {
  count = var.use_nsg ? 1 : 0

  network_security_group_id = oci_core_network_security_group.functions[0].id
  direction                 = "EGRESS"
  protocol                  = "all"
  destination               = "0.0.0.0/0"
  destination_type          = "CIDR_BLOCK"
  stateless                 = false
  description               = "Allow all egress (routed via NAT/Service GW)"
}
