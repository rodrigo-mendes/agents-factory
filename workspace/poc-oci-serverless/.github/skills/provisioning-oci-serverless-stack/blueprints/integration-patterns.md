## Integration Patterns

### Terraform ↔ OCI Functions

**Resources**: `oci_functions_application`, `oci_functions_function`, `oci_functions_invoke_function`
**Data Sources**: `data.oci_functions_application`, `data.oci_functions_functions`
**Dependencies**: VCN subnet, NSG, OCIR image

```hcl
# Complete Function provisioning with application + function
resource "oci_functions_application" "app" {
  compartment_id             = var.compartment_ocid
  display_name               = "app-${var.project_name}-${var.environment}"
  subnet_ids                 = [var.subnet_private_id]
  shape                      = "GENERIC_X86"
  network_security_group_ids = [oci_core_network_security_group.functions.id]
  freeform_tags              = local.common_tags
}

resource "oci_functions_function" "handler" {
  application_id     = oci_functions_application.app.id
  display_name       = "fn-${var.function_name}"
  image              = "${var.ocir_url}/${var.ocir_namespace}/${var.ocir_repo}:${var.image_tag}"
  memory_in_mbs      = var.function_memory_in_mbs
  timeout_in_seconds = var.function_timeout_in_seconds
  freeform_tags      = local.common_tags
}
```

**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/functions_application

### Terraform ↔ OCI API Gateway

**Resources**: `oci_apigateway_gateway`, `oci_apigateway_deployment`, `oci_apigateway_certificate`
**Data Sources**: `data.oci_apigateway_gateways`, `data.oci_apigateway_deployments`
**Dependencies**: VCN subnet, NSG, Function OCID (for `ORACLE_FUNCTIONS_BACKEND`)

```hcl
# API Gateway with deployment routing to OCI Functions backend
resource "oci_apigateway_gateway" "this" {
  compartment_id             = var.compartment_ocid
  display_name               = "gw-${var.project_name}-${var.environment}"
  endpoint_type              = var.api_gateway_endpoint_type
  subnet_id                  = var.subnet_public_id
  network_security_group_ids = [oci_core_network_security_group.apigw.id]
  freeform_tags              = local.common_tags
}

resource "oci_apigateway_deployment" "api" {
  compartment_id = var.compartment_ocid
  gateway_id     = oci_apigateway_gateway.this.id
  display_name   = "deploy-${var.project_name}-api-${var.environment}"
  path_prefix    = "/api/v1"

  specification {
    routes {
      path    = "/health"
      methods = ["GET"]

      backend {
        type        = "ORACLE_FUNCTIONS_BACKEND"
        function_id = oci_functions_function.handler.id
      }
    }
  }

  freeform_tags = local.common_tags
}
```

**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/apigateway_gateway

### Terraform ↔ OCI IAM

**Resources**: `oci_identity_dynamic_group`, `oci_identity_policy`, `oci_identity_compartment`
**Data Sources**: `data.oci_identity_compartment`, `data.oci_identity_tenancy`
**Note**: Dynamic Groups and Policies are defined at tenancy level (root compartment)

```hcl
# Dynamic Group for API Gateway + least-privilege policy
resource "oci_identity_dynamic_group" "apigw" {
  compartment_id = var.tenancy_ocid
  name           = "dg-${var.project_name}-apigw-${var.environment}"
  description    = "Dynamic group for ${var.project_name} API Gateway"

  matching_rule = "ALL {resource.type = 'ApiGateway', resource.compartment.id = '${var.compartment_ocid}'}"

  freeform_tags = local.common_tags
}

resource "oci_identity_policy" "apigw_invoke_functions" {
  compartment_id = var.compartment_ocid
  name           = "policy-${var.project_name}-apigw-invoke-${var.environment}"
  description    = "Allow API Gateway to invoke Functions"

  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.apigw.name} to use fn-invocation in compartment ${var.compartment_name}",
  ]

  freeform_tags = local.common_tags
}
```

**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/identity_dynamic_group

### Terraform ↔ OCI Networking (VCN)

**Resources**: `oci_core_vcn`, `oci_core_subnet`, `oci_core_internet_gateway`, `oci_core_nat_gateway`, `oci_core_service_gateway`, `oci_core_route_table`, `oci_core_network_security_group`

```hcl
# Minimal VCN setup for serverless: public subnet (API GW) + private subnet (Functions)
resource "oci_core_vcn" "this" {
  compartment_id = var.compartment_ocid
  display_name   = "vcn-${var.project_name}-${var.environment}"
  cidr_blocks    = [var.vcn_cidr]
  dns_label      = var.project_name
  freeform_tags  = local.common_tags
}
```

**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/core_vcn

---

