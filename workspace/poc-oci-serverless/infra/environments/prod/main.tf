# ==============================================================================
# Environment: prod — Shared Infrastructure
# ==============================================================================
# Same structure as dev. Adjust variables in terraform.tfvars.
# ==============================================================================

locals {
  tags = merge(var.freeform_tags, {
    "Environment" = var.environment
    "Project"     = var.project_name
    "ManagedBy"   = "terraform"
  })
}

# ------------------------------------------------------------------------------
# Network
# ------------------------------------------------------------------------------

module "network" {
  source = "../../modules/network"

  compartment_ocid    = var.compartment_ocid
  vcn_cidr_block      = var.vcn_cidr_block
  subnet_public_cidr  = var.subnet_public_cidr
  subnet_private_cidr = var.subnet_private_cidr
  create_nat_gateway  = var.create_nat_gateway
  use_nsg             = var.use_nsg
  environment         = var.environment
  project_name        = var.project_name
  tags                = local.tags
}

# ------------------------------------------------------------------------------
# IAM
# ------------------------------------------------------------------------------

module "iam" {
  source = "../../modules/iam"

  tenancy_ocid     = var.tenancy_ocid
  compartment_ocid = var.compartment_ocid
  compartment_name = var.compartment_name
  environment      = var.environment
  project_name     = var.project_name
  tags             = local.tags
}

# ------------------------------------------------------------------------------
# Vault (KMS + Object Storage)
# ------------------------------------------------------------------------------

module "vault" {
  source = "../../modules/vault"

  compartment_ocid    = var.compartment_ocid
  project_name        = var.project_name
  environment         = var.environment
  key_protection_mode = "HSM"
  create_bucket       = true
  bucket_name         = "api-facade"
  tags                = local.tags
}

# ------------------------------------------------------------------------------
# Observability
# ------------------------------------------------------------------------------

module "observability" {
  source = "../../modules/observability"

  compartment_ocid         = var.compartment_ocid
  api_deployment_id        = module.api_gateway.deployment_id
  enable_logging           = true
  enable_monitoring_alarms = true
  environment              = var.environment
  project_name             = var.project_name
  tags                     = local.tags

  functions_applications = {
    "api-handler"     = module.app_api_handler.application_id
    "func-api-facade" = module.app_api_facade.application_id
    "rest-proxy"      = module.app_rest_proxy.application_id
  }
}
