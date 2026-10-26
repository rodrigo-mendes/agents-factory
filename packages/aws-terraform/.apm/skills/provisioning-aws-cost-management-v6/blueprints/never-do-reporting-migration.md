# Never-Do — Reporting and Migration (s3_prefix, ATHENA, Savings Plan, Withdrawn Version, Backend)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources read 2026-10-23. Values marked `# example` are placeholders.

## 1. CUR without s3_prefix

`s3_prefix` is required on `aws_cur_report_definition` since 6.0.

```hcl
# WRONG — fragment, s3_prefix missing
resource "aws_cur_report_definition" "bad" {
  report_name = "cost-and-usage" # example
  s3_bucket   = "my-cur-bucket"  # example
  s3_region   = "eu-west-1"      # example
  # WRONG: no s3_prefix (other required arguments omitted)
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown

# CORRECT — fragment
resource "aws_cur_report_definition" "good" {
  report_name = "cost-and-usage" # example
  s3_bucket   = "my-cur-bucket"  # example
  s3_region   = "eu-west-1"      # example
  s3_prefix   = "cur"            # example
  # other required arguments as in always-do-reporting-commitments §10
}
```

## 2. ATHENA artifact misuse

On the resource page: `ATHENA` must be the only `additional_artifacts` value and needs
`report_versioning = "OVERWRITE_REPORT"`.

```hcl
# WRONG — fragment
additional_artifacts = ["ATHENA", "QUICKSIGHT"] # WRONG: ATHENA must be alone
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cur_report_definition.html.markdown

# CORRECT — fragment
additional_artifacts = ["ATHENA"]
report_versioning    = "OVERWRITE_REPORT"
```

## 3. Destroying an active Savings Plan

An active plan "cannot be cancelled or deleted"; only `queued` plans can be deleted. Destroying an active plan
only removes it from state. A post-purchase cancellation path is not documented on the page (unverified).

```hcl
# WRONG — assuming terraform destroy cancels the commitment
# $ terraform destroy -target=aws_savingsplans_savings_plan.compute   # WRONG: only removes it from state
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/savingsplans_savings_plan.html.markdown

# CORRECT — review the commitment before apply
resource "aws_savingsplans_savings_plan" "compute" {
  savings_plan_offering_id = "00000000-0000-0000-0000-000000000000" # example placeholder
  commitment               = "1.0"                                    # example, hourly USD
}
```

## 4. Pinning version 6.57.0

6.57.0 was withdrawn from GitHub and the Registry.

```hcl
# WRONG — withdrawn release
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "= 6.57.0" }
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

## 5. S3 backend with dynamodb_table

`dynamodb_table` is deprecated; use `use_lockfile = true` (native S3 locking).

```hcl
# WRONG — deprecated
terraform {
  backend "s3" {
    bucket         = "my-tf-state"                       # example
    key            = "cost-management/terraform.tfstate" # example
    region         = "eu-west-1"                         # example
    dynamodb_table = "terraform-locks"                   # WRONG — deprecated
  }
}
# Source: https://developer.hashicorp.com/terraform/language/backend/s3

# CORRECT
terraform {
  backend "s3" {
    bucket       = "my-tf-state"                       # example
    key          = "cost-management/terraform.tfstate" # example
    region       = "eu-west-1"                         # example
    use_lockfile = true
  }
}
```
