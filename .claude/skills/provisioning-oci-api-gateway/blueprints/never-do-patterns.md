### 🚫 Never Do

**Anti-Pattern**: Credentials Hardcoded in Provider Block

```hcl
# 🚫 WRONG: Credentials exposed in code — full tenancy compromise (OCI Provider v6.x+)
provider "oci" {
  tenancy_ocid = "ocid1.tenancy.oc1..aaaa..."
  user_ocid    = "ocid1.user.oc1..bbbb..."
  fingerprint  = "aa:bb:cc:dd:ee:ff:00:11:22:33:44:55:66:77:88:99"
  private_key  = "<PEM private key pasted here>"
  region       = "sa-saopaulo-1"
}

# ✅ CORRECT: Credentials via env vars or OCI config file (OCI Provider v6.x+)
provider "oci" {
  region = var.region
  # Dev: ~/.oci/config | CI/CD: OCI_TENANCY_OCID env vars | OCI: Instance/Resource Principal
}

# ✅ CORRECT: Resource Principal for OCI Functions / Resource Manager
provider "oci" {
  auth   = "ResourcePrincipal"
  region = var.region
}
```
**Why it is prohibited**: Hardcoded credentials in source files are committed to version control, exposed in CI logs, and compromise the entire OCI tenancy.
**Actual impact**: Full OCI tenancy compromise — attacker gains administrative access to all cloud resources.
**Severity**: CRITICAL
**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs#authentication

---

**Anti-Pattern**: API Gateway Without Rate Limiting

```hcl
# 🚫 WRONG: No rate limiting — unbounded invocations and cost (OCI Provider v6.x+)
resource "oci_apigateway_deployment" "this" {
  specification {
    request_policies {
      # Missing rate_limiting block — any client can make unlimited requests
    }
    routes {
      path    = "/users"
      methods = ["GET"]
      backend {
        type        = "ORACLE_FUNCTIONS_BACKEND"
        function_id = var.function_id
      }
    }
  }
}

# ✅ CORRECT: Rate limiting at deployment level (OCI Provider v6.x+)
resource "oci_apigateway_deployment" "this" {
  specification {
    request_policies {
      rate_limiting {
        rate_in_requests_per_second = 100
        rate_key                    = "CLIENT_IP"
      }
    }
    routes {
      path    = "/users"
      methods = ["GET"]
      backend {
        type        = "ORACLE_FUNCTIONS_BACKEND"
        function_id = var.function_id
      }
    }
  }
}
```
**Why it is prohibited**: Without rate limiting, a single client can trigger thousands of Function invocations. OCI Functions are billed per invocation and execution time — this directly causes cost explosion.
**Actual impact**: DDoS vulnerability, uncontrolled billing, service degradation for all consumers.
**Severity**: CRITICAL
**Source**: https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayaddingpolicies.htm

---

**Anti-Pattern**: Functions Exposed Directly Without API Gateway

```hcl
# 🚫 WRONG: Functions in public subnet, bypassing API Gateway (OCI Provider v6.x+)
resource "oci_core_subnet" "functions" {
  prohibit_public_ip_on_vnic = false  # Functions are publicly accessible
}
# Direct invocation: curl https://<invoke-endpoint>/20181201/functions/<ocid>/actions/invoke

# ✅ CORRECT: Functions in private subnet, accessible only via API Gateway (OCI Provider v6.x+)
resource "oci_core_subnet" "functions" {
  prohibit_public_ip_on_vnic = true  # No public IP — private only
}

resource "oci_apigateway_deployment" "this" {
  specification {
    routes {
      path = "/api/v1/resource"
      backend {
        type        = "ORACLE_FUNCTIONS_BACKEND"
        function_id = oci_functions_function.this.id
      }
    }
  }
}
```
**Why it is prohibited**: Direct Function invocation bypasses all API management — no rate limiting, no authentication, no CORS, no centralized logging.
**Actual impact**: No auth, no rate limit, no logging — cost explosion and unauthorized access.
**Severity**: CRITICAL
**Source**: https://docs.oracle.com/en-us/iaas/Content/APIGateway/Concepts/apigatewayoverview.htm

---

**Anti-Pattern**: SSL Verification Disabled on JWKS Endpoint

```hcl
# 🚫 WRONG: SSL verification disabled — Man-in-the-Middle attack (OCI Provider v6.x+)
public_keys {
  type                   = "REMOTE_JWKS"
  uri                    = var.jwks_uri
  is_ssl_verify_disabled = true  # Attacker can inject malicious public keys
}

# ✅ CORRECT: SSL verification always enabled (OCI Provider v6.x+)
public_keys {
  type                        = "REMOTE_JWKS"
  uri                         = var.jwks_uri
  is_ssl_verify_disabled      = false  # Default and correct
  max_cache_duration_in_hours = 24
}
```
**Why it is prohibited**: Disabling SSL verification on JWKS endpoints allows MITM attacks — an attacker can intercept the JWKS response and inject malicious public keys, enabling forged tokens to pass validation.
**Actual impact**: Complete authentication bypass via MITM on the JWKS fetch.
**Severity**: CRITICAL
**Source**: https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayaddingauthentication.htm

---

**Anti-Pattern**: Permissive Security List (0.0.0.0/0 all ports)

```hcl
# 🚫 WRONG: All protocols from all sources — full exposure (OCI Provider v6.x+)
resource "oci_core_security_list" "public" {
  ingress_security_rules {
    protocol    = "all"
    source      = "0.0.0.0/0"
    source_type = "CIDR_BLOCK"
  }
}

# ✅ CORRECT: Only HTTPS (443) from internet (OCI Provider v6.x+)
resource "oci_core_security_list" "public" {
  ingress_security_rules {
    protocol    = "6"           # TCP only
    source      = "0.0.0.0/0"
    source_type = "CIDR_BLOCK"
    description = "HTTPS from internet"
    tcp_options {
      min = 443
      max = 443
    }
  }
}
```
**Why it is prohibited**: Exposes all services in the subnet to arbitrary traffic. API Gateway requires only TCP 443 inbound.
**Actual impact**: Unauthorized access, port scanning, lateral movement exploitation.
**Severity**: CRITICAL
**Source**: https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/securitylists.htm

---

**Anti-Pattern**: State File Without Encryption

```hcl
# 🚫 WRONG: Unencrypted state — infrastructure exposure (Terraform)
backend "s3" {
  bucket   = "terraform-state"
  key      = "prod/terraform.tfstate"
  region   = "sa-saopaulo-1"
  endpoint = "https://namespace.compat.objectstorage.sa-saopaulo-1.oraclecloud.com"
  # Missing encrypt = true — state contains OCIDs, endpoints, sensitive configs
}

# ✅ CORRECT: Encrypted state file (Terraform)
backend "s3" {
  bucket                      = "terraform-state"
  key                         = "prod/terraform.tfstate"
  region                      = "sa-saopaulo-1"
  endpoint                    = "https://namespace.compat.objectstorage.sa-saopaulo-1.oraclecloud.com"
  encrypt                     = true
  skip_region_validation      = true
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  force_path_style            = true
}
```
**Why it is prohibited**: State files contain all resource attributes including endpoints, OCIDs, and complete configurations. Without encryption, any Object Storage access exposes entire infrastructure.
**Actual impact**: Full infrastructure exposure — OCIDs, endpoints, and configurations leaked.
**Severity**: CRITICAL
**Source**: https://developer.hashicorp.com/terraform/language/state/sensitive-data

---

