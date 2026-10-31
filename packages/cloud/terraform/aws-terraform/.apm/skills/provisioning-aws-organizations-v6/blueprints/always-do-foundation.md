# Always-Do — Foundation (Terraform Block, Organization, OUs, Accounts)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-23. Organizations is global: no
resource below takes `region`.

## 1. Terraform Block and Provider

Root modules pin `~> 6.69`. Use `use_lockfile = true` (S3-native locking); `dynamodb_table` is
deprecated. The provider must authenticate into the management account (account management
must be done from the organization's root account). Organizations is hosted in `us-east-1`.

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.69"
    }
  }
  backend "s3" {
    bucket       = "my-tf-state"
    key          = "organizations/terraform.tfstate"
    region       = "us-east-1"
    use_lockfile = true   # S3-native lock; dynamodb_table is deprecated
    encrypt      = true   # example setting
  }
}

provider "aws" {
  region = "us-east-1"   # Organizations is hosted in us-east-1
  assume_role {
    role_arn = var.management_account_role_arn   # credentials must reach the management account
  }
}
# Source: https://developer.hashicorp.com/terraform/language/backend/s3
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_account.html.markdown
```

## 2. Organization

`feature_set = "ALL"` is the default and is required by `aws_service_access_principals` and
`enabled_policy_types`. AWS recommends enabling service integrations through each service's own
console or commands, because some services do not support enablement through this endpoint.

```hcl
resource "aws_organizations_organization" "this" {
  feature_set = "ALL"

  aws_service_access_principals = [
    "securityhub.amazonaws.com",   # example value; required by SECURITYHUB_POLICY
  ]

  enabled_policy_types = [
    "SERVICE_CONTROL_POLICY",
    "SECURITYHUB_POLICY",
  ]
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_organization.html.markdown
```

Set `return_organization_only = true` only when just `arn`, `feature_set`, `master_account_arn`,
`master_account_email` and `master_account_id` are needed; it avoids API throttling, and only
those attributes are populated (so `roots[0].id` is not available). Default is `false`.

## 3. Organizational Units

`parent_id` is the root or another OU. Use `roots[0].id` for the top level. Nesting is limited to
5 levels under the root (2000 OUs per organization).

```hcl
resource "aws_organizations_organizational_unit" "workloads" {
  name      = "workloads"
  parent_id = aws_organizations_organization.this.roots[0].id
  tags      = { Owner = "platform" }
}

resource "aws_organizations_organizational_unit" "prod" {
  name      = "prod"
  parent_id = aws_organizations_organizational_unit.workloads.id
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_organizational_unit.html.markdown
# Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_reference_limits.html
```

Whether changing `parent_id` forces replacement is not stated on the page (unverified).

## 4. Accounts

`email` must not belong to another AWS account. Set `parent_id` explicitly (needed for drift
detection). Organizations has no API to read `role_name` back, so ignore it. By default destroy
only removes the account from the organization. Read `state`; `status` is deprecated.

```hcl
variable "accounts" {
  type = map(object({
    email = string
    name  = string
  }))
}

resource "aws_organizations_account" "member" {
  for_each  = var.accounts
  name      = each.value.name
  email     = each.value.email
  parent_id = aws_organizations_organizational_unit.prod.id
  role_name = "OrganizationAccountAccessRole"   # example value only

  lifecycle {
    ignore_changes = [role_name]   # no API to read role_name back
    prevent_destroy = true         # (medium confidence) Terraform-generic protection
  }
}

output "member_states" {
  value = { for k, a in aws_organizations_account.member : k => a.state }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_account.html.markdown
```

Create/update/delete timeouts default to 10 minutes each. A created account must exist at least
4 days before it can be removed (https://docs.aws.amazon.com/organizations/latest/userguide/orgs_reference_limits.html).
