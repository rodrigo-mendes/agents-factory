terraform {
  required_version = ">= 1.5"

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 6.0, < 9.0"
    }
  }

  # Backend remoto (OCI Object Storage via S3-compat)
  # backend "s3" {
  #   bucket                      = "terraform-state"
  #   key                         = "serverless/prod/terraform.tfstate"
  #   region                      = "sa-saopaulo-1"
  #   endpoint                    = "https://<namespace>.compat.objectstorage.sa-saopaulo-1.oraclecloud.com"
  #   encrypt                     = true
  #   skip_region_validation      = true
  #   skip_credentials_validation = true
  #   skip_metadata_api_check     = true
  #   force_path_style            = true
  # }
}

provider "oci" {
  auth                = "APIKey"
  config_file_profile = "prod"
  region              = var.region
}
