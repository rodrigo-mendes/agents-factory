# Integration Patterns — provisioning-oci-networking

## Module Interface

### Variables (variables.tf)

```hcl
variable "compartment_ocid" {
  description = "OCID of the compartment for network resources"
  type        = string
}

variable "vcn_cidr_block" {
  description = "CIDR block for the VCN (e.g., 10.0.0.0/16)"
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.vcn_cidr_block, 0))
    error_message = "vcn_cidr_block must be a valid CIDR."
  }
}

variable "vcn_dns_label" {
  description = "DNS label for the VCN (alphanumeric, max 15 chars)"
  type        = string
}

variable "subnet_public_cidr" {
  description = "CIDR block for the public subnet"
  type        = string
  default     = "10.0.0.0/24"
}

variable "subnet_private_cidr" {
  description = "CIDR block for the private subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "create_nat_gateway" {
  description = "Whether to create a NAT Gateway for private subnet internet egress"
  type        = bool
  default     = true
}

variable "create_drg" {
  description = "Whether to create a DRG for hybrid/multi-VCN connectivity"
  type        = bool
  default     = false
}

variable "use_nsg" {
  description = "Whether to create NSGs for API Gateway and Functions"
  type        = bool
  default     = true
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "project_name" {
  description = "Project name for naming convention"
  type        = string
}

variable "tags" {
  description = "Freeform tags for all resources"
  type        = map(string)
  default     = {}
}
```

### Outputs (outputs.tf)

```hcl
output "vcn_id" {
  description = "OCID of the VCN"
  value       = oci_core_vcn.main.id
}

output "subnet_public_id" {
  description = "OCID of the public subnet"
  value       = oci_core_subnet.public.id
}

output "subnet_private_id" {
  description = "OCID of the private subnet"
  value       = oci_core_subnet.private.id
}

output "nsg_apigw_id" {
  description = "OCID of the API Gateway NSG"
  value       = var.use_nsg ? oci_core_network_security_group.apigw[0].id : null
}

output "nsg_functions_id" {
  description = "OCID of the Functions NSG"
  value       = var.use_nsg ? oci_core_network_security_group.functions[0].id : null
}

output "internet_gateway_id" {
  description = "OCID of the Internet Gateway"
  value       = oci_core_internet_gateway.main.id
}

output "nat_gateway_id" {
  description = "OCID of the NAT Gateway"
  value       = var.create_nat_gateway ? oci_core_nat_gateway.main[0].id : null
}

output "service_gateway_id" {
  description = "OCID of the Service Gateway"
  value       = oci_core_service_gateway.main.id
}
```

---

## Cross-Module Integration

### Network → API Gateway Module

```hcl
# Network module provides public subnet and APIGW NSG to API Gateway module
module "network" {
  source = "./modules/network"
  # ... variables
}

module "api_gateway" {
  source = "./modules/api-gateway"

  compartment_ocid = var.compartment_ocid
  subnet_id        = module.network.subnet_public_id    # Public subnet
  nsg_ids          = [module.network.nsg_apigw_id]      # APIGW NSG
}
```

### Network → Function App Module

```hcl
# Network module provides private subnet and Functions NSG to function-app module
module "app_api_handler" {
  source = "./modules/function-app"

  compartment_ocid = var.compartment_ocid
  subnet_id        = module.network.subnet_private_id   # Private subnet
  nsg_ids          = [module.network.nsg_functions_id]  # Functions NSG
}
```

### Network → IAM (Implicit Dependency)

```hcl
# IAM policies reference network resources implicitly via compartment.
# Functions in private subnet get Resource Principal via Dynamic Group.
# No direct Terraform dependency, but operational dependency exists:
# - Dynamic Group matches Functions in the compartment
# - IAM Policy grants Functions access to network-adjacent services (Vault, Streaming)
```

---

## Terraform Import Commands

```bash
# Import existing VCN
terraform import module.network.oci_core_vcn.main "<vcn_ocid>"

# Import Subnet
terraform import module.network.oci_core_subnet.public "<subnet_ocid>"

# Import Internet Gateway
terraform import module.network.oci_core_internet_gateway.main "<igw_ocid>"

# Import NAT Gateway
terraform import 'module.network.oci_core_nat_gateway.main[0]' "<natgw_ocid>"

# Import Service Gateway
terraform import module.network.oci_core_service_gateway.main "<sgw_ocid>"

# Import Route Table
terraform import module.network.oci_core_route_table.public "<rt_ocid>"

# Import NSG
terraform import 'module.network.oci_core_network_security_group.apigw[0]' "<nsg_ocid>"

# Import Security List
terraform import module.network.oci_core_security_list.public "<sl_ocid>"
```
