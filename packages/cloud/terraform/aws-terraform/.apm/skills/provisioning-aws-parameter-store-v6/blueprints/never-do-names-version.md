# Never-Do — Names and Provider Version

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-23.

## 1. Path Name Without a Leading Slash

The resource page: names with a path must start with `/`.

```hcl
# WRONG
resource "aws_ssm_parameter" "bad" {
  name           = "myapp/prod/db/host"   # WRONG — path without leading slash; example
  type           = "String"
  insecure_value = "db.internal.example"  # example
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ssm_parameter.html.markdown

# CORRECT
resource "aws_ssm_parameter" "good" {
  name           = "/myapp/prod/db/host"  # example
  type           = "String"
  insecure_value = "db.internal.example"  # example
}
```

## 2. Pinning Version 6.57.0

6.57.0 was withdrawn from GitHub and the Registry.

```hcl
# WRONG
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "6.57.0" }   # WRONG — withdrawn
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md

# CORRECT
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.69" }
  }
}
```
