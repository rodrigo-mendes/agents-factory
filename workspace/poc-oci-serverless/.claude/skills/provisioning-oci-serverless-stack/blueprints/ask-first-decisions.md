### ⚠️ Ask First

**Decision Point**: Terraform State Backend — Local vs. Remote (OCI Object Storage)

**Available Options**:

| Option | Optimizes For | Sacrifices | Choose When |
|--------|--------------|-----------|-------------|
| **Local backend** | Simplicity, offline access | Sharing, locking, safety | Solo dev, learning, prototypes |
| **OCI Object Storage (S3-compat)** | Team sharing, versioning, encryption | Configuration complexity | Team development, production |
| **OCI Resource Manager** | SaaS ease, audit, approval workflows | Flexibility, vendor lock-in | Enterprise governance, compliance |

**Agent Behavior**:
"Before configuring the Terraform backend, ask:
'How many people are on the team? Is this production infrastructure or a prototype?'"

```hcl
# Option: OCI Object Storage backend (production)
terraform {
  backend "s3" {
    bucket                      = "terraform-state"
    key                         = "serverless/prod/terraform.tfstate"
    region                      = "sa-saopaulo-1"
    endpoint                    = "https://<namespace>.compat.objectstorage.sa-saopaulo-1.oraclecloud.com"
    encrypt                     = true
    skip_region_validation      = true
    skip_credentials_validation = true
    skip_metadata_api_check     = true
    force_path_style            = true
  }
}
```

**Decision Factors**:
- Team size and collaboration needs
- Production vs. development environment
- Compliance and audit requirements
- Need for state locking (OCI S3-compat does NOT support DynamoDB-style locking)

**Source**: https://developer.hashicorp.com/terraform/language/settings/backends/s3

---

**Decision Point**: Provisioned Concurrency vs. On-Demand Execution

**Available Options**:

| Option | Optimizes For | Sacrifices | Choose When |
|--------|--------------|-----------|-------------|
| **On-Demand (default)** | Cost (pay-per-use only) | Latency (cold start 2–5s) | Low traffic, batch workloads, tolerant SLAs |
| **Provisioned (CONSTANT)** | Latency P99 < 200ms | Cost (25% idle cost) | APIs with latency SLAs, constant traffic |

**Agent Behavior**:
"Before configuring function concurrency, ask:
'What is the required P99 latency SLA? Is traffic constant or spiky?'"

```hcl
# Option: Provisioned Concurrency (OCI Provider v6.x+)
resource "oci_functions_function" "api" {
  application_id = oci_functions_application.app.id
  display_name   = "fn-api-handler"
  image          = "${var.ocir_url}/${var.ocir_namespace}/${var.ocir_repo}:${var.image_tag}"
  memory_in_mbs  = var.function_memory_in_mbs
  timeout_in_seconds = var.function_timeout_in_seconds

  provisioned_concurrency_config {
    strategy = "CONSTANT"
    count    = 5  # Number of pre-warmed instances
  }

  freeform_tags = local.common_tags
}
```

**Decision Factors**:
- P99 latency requirements
- Traffic pattern (steady vs. spiky)
- Cost sensitivity (provisioned charges even when idle)

**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/functions_function

---

