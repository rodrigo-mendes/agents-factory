# Always-Do — Foundation (Terraform Block, Names, Import)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-23.

## 1. Terraform Block and Version Constraints

Root modules use `~>` for providers; the CLI constraint is `~> 1.16`. The 6.58.0/6.59.0
`aws_ssm_parameter` import and name fixes need provider >= 6.59.0 (`~> 6.69` includes them).

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.69"
    }
  }
}
# Source: https://developer.hashicorp.com/terraform/language/expressions/version-constraints
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
```

## 2. Hierarchical Names and Non-Secret Values

Names with a path must start with `/`. Hierarchies use `/` with a maximum of 15 levels
(`/Environment/Type/Application/Data` is a suggested shape). `insecure_value` is never marked
sensitive and cannot be used with `SecureString`.

```hcl
resource "aws_ssm_parameter" "db_host" {
  name           = "/myapp/prod/db/host"            # example
  type           = "String"
  insecure_value = aws_db_instance.main.address     # example: declared elsewhere; non-secret, readable diff
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ssm_parameter.html.markdown
# Source: https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-paramstore-hierarchies.html
```

## 3. Import

The `identity` block requires Terraform >= 1.12.0 (`account_id` and `region` optional).
The resource page also lists `id = "<parameter name>"` and the CLI form
`terraform import aws_ssm_parameter.x /app/prod/x`.

```hcl
import {
  to = aws_ssm_parameter.db_host
  identity = {
    name = "/myapp/prod/db/host"   # example
  }
}

import {
  to = aws_ssm_parameter.db_port
  id = "/myapp/prod/db/port"       # example
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc.html.markdown (identity requires Terraform >= 1.12.0)
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ssm_parameter.html.markdown
```
