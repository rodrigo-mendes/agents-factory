terraform {
  required_version = ">= 1.5"

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 6.0, < 9.0"
    }
  }

  # Backend remoto (OCI Object Storage via S3-compat)
  # Descomente e configure para produção:
  # backend "s3" {
  #   bucket                      = "terraform-state"
  #   key                         = "serverless/dev/terraform.tfstate"
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
  auth                = "SecurityToken"
  config_file_profile = "poc"
  region              = var.region
}
