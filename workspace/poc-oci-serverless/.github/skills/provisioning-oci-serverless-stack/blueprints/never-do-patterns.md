### 🚫 Never Do

**Anti-Pattern**: Hardcoded credentials in provider block

```hcl
# 🚫 WRONG: Credentials exposed in VCS, CI/CD logs, and state file
# This violates OCI security best practices and Terraform OCI Provider v6.x+ guidelines
provider "oci" {
  tenancy_ocid = "ocid1.tenancy.oc1..aaaaaaaaa"
  user_ocid    = "ocid1.user.oc1..aaaaaaaaa"
  fingerprint  = "aa:bb:cc:dd:ee:ff:00:11:22:33:44:55:66:77:88:99"
  private_key  = "-----BEGIN RSA PRIVATE KEY-----\nMIIE..."
  region       = "sa-saopaulo-1"
}

# ✅ CORRECT: Instance Principal for production (Terraform OCI Provider v6.x+)
provider "oci" {
  auth   = "InstancePrincipal"
  region = var.region
}

# ✅ CORRECT: Environment variables for CI/CD
# OCI_TENANCY_OCID, OCI_USER_OCID, OCI_FINGERPRINT, OCI_PRIVATE_KEY_PATH
provider "oci" {
  region = var.region
}
```

**Why it is prohibited**: Credentials in code are the #1 cause of cloud tenancy compromise. They leak through git history, CI/CD logs, and unencrypted state files.
**Actual impact**: Complete tenancy compromise — attacker gains full administrative access to all OCI resources.
**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs#authentication

---

**Anti-Pattern**: Wildcard IAM policy (`manage all-resources in tenancy`)

```hcl
# 🚫 WRONG: Grants god-mode access — any compromised resource owns the tenancy
# Violates OCI IAM least-privilege principle (OCI Provider v6.x+)
resource "oci_identity_policy" "admin" {
  compartment_id = var.tenancy_ocid
  name           = "admin-access"
  statements     = ["Allow group developers to manage all-resources in tenancy"]
}

# ✅ CORRECT: Granular policies per resource type and compartment
resource "oci_identity_policy" "functions" {
  compartment_id = var.compartment_ocid
  name           = "policy-functions-access"
  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.functions.name} to use fn-invocation in compartment ${var.compartment_name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.functions.name} to read secret-bundles in compartment ${var.compartment_name}",
  ]
}
```

**Why it is prohibited**: Violates least-privilege. Any compromised identity with this policy gains unrestricted access to every resource in the tenancy.
**Actual impact**: Privilege escalation, unauthorized data access, regulatory non-compliance.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/commonpolicies.htm

---

**Anti-Pattern**: Security group rule with 0.0.0.0/0 on management ports

```hcl
# 🚫 WRONG: Exposes SSH to the entire internet (OCI Provider v6.x+)
resource "oci_core_network_security_group_security_rule" "ssh_open" {
  network_security_group_id = oci_core_network_security_group.app.id
  direction                 = "INGRESS"
  protocol                  = "6"  # TCP
  source                    = "0.0.0.0/0"
  source_type               = "CIDR_BLOCK"
  tcp_options {
    destination_port_range {
      min = 22
      max = 22
    }
  }
}

# ✅ CORRECT: Restrict to bastion/VPN CIDR only
resource "oci_core_network_security_group_security_rule" "ssh_restricted" {
  network_security_group_id = oci_core_network_security_group.app.id
  direction                 = "INGRESS"
  protocol                  = "6"
  source                    = var.bastion_cidr  # e.g., "10.0.10.0/24"
  source_type               = "CIDR_BLOCK"
  description               = "SSH from bastion subnet only"
  tcp_options {
    destination_port_range {
      min = 22
      max = 22
    }
  }
}
```

**Why it is prohibited**: Open management ports (SSH, RDP) to the internet expose the instance to brute-force attacks, automated exploitation, and credential stuffing.
**Actual impact**: Unauthorized server access, lateral movement, data exfiltration.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/networksecuritygroups.htm

---

**Anti-Pattern**: Unencrypted state file backend

```hcl
# 🚫 WRONG: State file contains OCIDs, config secrets, connection strings — unencrypted is a data leak
terraform {
  backend "s3" {
    bucket   = "my-tf-state"
    key      = "terraform.tfstate"
    endpoint = "https://namespace.compat.objectstorage.region.oraclecloud.com"
    # encrypt = false or missing entirely
  }
}

# ✅ CORRECT: Always enable encryption and use structured key paths (Terraform >= 1.7)
terraform {
  backend "s3" {
    bucket                      = "my-tf-state"
    key                         = "prod/serverless/terraform.tfstate"
    endpoint                    = "https://namespace.compat.objectstorage.sa-saopaulo-1.oraclecloud.com"
    encrypt                     = true
    skip_region_validation      = true
    skip_credentials_validation = true
    skip_metadata_api_check     = true
    force_path_style            = true
  }
}
```

**Why it is prohibited**: State files contain all resource OCIDs, configuration values, and potentially sensitive outputs. Without encryption, anyone with bucket access sees everything.
**Actual impact**: Complete infrastructure exposure — all OCIDs, subnets, security groups, and secrets visible in plaintext.
**Source**: https://developer.hashicorp.com/terraform/language/state/sensitive-data

---

