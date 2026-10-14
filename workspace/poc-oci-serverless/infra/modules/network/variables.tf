variable "compartment_ocid" {
  type        = string
  description = "OCID do compartment"

  validation {
    condition     = can(regex("^ocid1\\.compartment\\.", var.compartment_ocid))
    error_message = "compartment_ocid deve ser um OCID válido (ocid1.compartment.*)."
  }
}

variable "vcn_cidr_block" {
  type        = string
  description = "CIDR block para a VCN"

  validation {
    condition     = can(cidrhost(var.vcn_cidr_block, 0))
    error_message = "vcn_cidr_block deve ser um CIDR válido (e.g., 10.0.0.0/16)."
  }
}

variable "subnet_public_cidr" {
  type        = string
  description = "CIDR block para a subnet pública (API Gateway)"

  validation {
    condition     = can(cidrhost(var.subnet_public_cidr, 0))
    error_message = "subnet_public_cidr deve ser um CIDR válido (e.g., 10.0.0.0/24)."
  }
}

variable "subnet_private_cidr" {
  type        = string
  description = "CIDR block para a subnet privada (Functions)"

  validation {
    condition     = can(cidrhost(var.subnet_private_cidr, 0))
    error_message = "subnet_private_cidr deve ser um CIDR válido (e.g., 10.0.1.0/24)."
  }
}

variable "create_nat_gateway" {
  type        = bool
  description = "Criar NAT Gateway"
  default     = true
}

variable "use_nsg" {
  type        = bool
  description = "Criar Network Security Groups"
  default     = true
}

variable "environment" {
  type        = string
  description = "Nome do ambiente"
}

variable "project_name" {
  type        = string
  description = "Nome do projeto"
}

variable "tags" {
  type        = map(string)
  description = "Tags para os recursos"
  default     = {}
}
