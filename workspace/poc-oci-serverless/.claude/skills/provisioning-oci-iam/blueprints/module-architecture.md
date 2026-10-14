# Module Architecture — provisioning-oci-iam

## IAM Module Layout

### Minimal Module

```
modules/iam/
├── main.tf          # Dynamic Groups + Policies
├── variables.tf     # Input variables (tenancy_ocid, compartment_ocid, etc.)
└── outputs.tf       # Dynamic Group IDs and names for downstream modules
```

### Extended Module (Production)

```
modules/iam/
├── main.tf              # Core Dynamic Groups + Policies
├── compartments.tf      # Compartment hierarchy (optional)
├── network_sources.tf   # Network Sources for policy conditions
├── tags.tf              # Tag Namespaces and Defined Tags
├── variables.tf         # Input variables
├── outputs.tf           # Outputs for downstream modules
└── README.md            # Documentation
```

## Module Composition in Root

```hcl
# Root main.tf — IAM precedes all workload modules (OCI Provider v6.x+)
module "iam" {
  source           = "./modules/iam"
  tenancy_ocid     = var.tenancy_ocid
  compartment_ocid = var.compartment_ocid
  compartment_name = var.compartment_name
  environment      = var.environment
  project_name     = var.project_name
  tags             = local.tags
}

module "network" {
  source           = "./modules/network"
  compartment_ocid = var.compartment_ocid
}

module "app_api_handler" {
  source    = "./modules/function-app"
  subnet_id = module.network.subnet_private_id
  depends_on = [module.iam]  # CRITICAL: wait for policy propagation
}

module "api_gateway" {
  source      = "./modules/api-gateway"
  function_id = module.functions.function_id
  depends_on  = [module.iam]  # CRITICAL: fn-invocation policy needed
}
```

---

## State Management

### IAM State Isolation Strategy

```
terraform-state-bucket/
├── iam/shared/terraform.tfstate        # Shared IAM (tenancy-level policies)
├── serverless/dev/terraform.tfstate     # Dev workload
├── serverless/staging/terraform.tfstate
└── serverless/prod/terraform.tfstate
```

**Key decision**: Tenancy-level IAM (service policies, admin groups) should be in a SEPARATE state file from workload resources. This prevents accidental destroy of platform IAM during workload teardown.

### Lifecycle Rules for IAM Resources

```hcl
# Prevent accidental deletion of production IAM (OCI Provider v6.x+)
resource "oci_identity_policy" "critical" {
  # ...
  lifecycle {
    prevent_destroy = true
  }
}

resource "oci_identity_compartment" "prod" {
  # ...
  enable_delete = false  # Extra safety for production compartment
  lifecycle {
    prevent_destroy = true
  }
}
```

### Import Strategy for Existing IAM Resources

```bash
# Import existing compartment
terraform import oci_identity_compartment.project <compartment-ocid>

# Import existing dynamic group
terraform import oci_identity_dynamic_group.functions <dynamic-group-ocid>

# Import existing policy
terraform import oci_identity_policy.faas_network <policy-ocid>

# Post-import: verify state matches config
terraform plan
```

---

## Agent Operation Notes

### High Confidence (Execute without asking)
- Creating Dynamic Groups with compartment-scoped matching rules
- Creating least-privilege policies for Functions/API Gateway
- Adding service policies (FaaS, API Gateway) at tenancy level
- Variable validation for OCIDs
- Adding freeform_tags to all IAM resources
- Setting depends_on for downstream modules
- Terraform validate and fmt

### Medium Confidence (Validate with user)
- Compartment hierarchy structure
- Policy verb choice (use vs. manage for specific operations)
- Multiple Dynamic Groups vs. single broad DG
- Cross-compartment policy requirements
- Tag-based access control strategy

### Low Confidence (Must ask user)
- Identity Domain configuration and federation
- MFA enforcement policies
- Network Source restrictions
- Cross-tenancy access patterns
- Compliance-specific requirements (SOC2, HIPAA, PCI-DSS)

### Emergency Stop
- **HALT** if `manage all-resources in tenancy` found in workload policies
- **HALT** if Dynamic Group uses `ANY{}` without compartment constraint
- **HALT** if credentials found in provider configuration
- **HALT** if policy names have no environment/project qualifier (collision risk)
- **HALT** if `enable_delete = true` on production compartments without `prevent_destroy` lifecycle
