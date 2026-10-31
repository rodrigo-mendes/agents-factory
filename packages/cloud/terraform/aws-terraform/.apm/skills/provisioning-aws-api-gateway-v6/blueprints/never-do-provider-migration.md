# Never-Do — Provider 6.0 removals, backend, withdrawn version

hashicorp/aws 6.x · Terraform ~> 1.16 · Per-source read dates: see the bibliography in unverified-and-risks.md. Blocks referencing resources defined
elsewhere are fragments; `# example` values are not from the docs.

## 1. Removed arguments on aws_api_gateway_deployment

`stage_name`, `stage_description` and `canary_settings` were removed from `aws_api_gateway_deployment` in
6.0, as were the `invoke_url` and `execution_arn` attributes. Declare an `aws_api_gateway_stage`; to adopt an
existing stage run `terraform import aws_api_gateway_stage.prod rest_api_id/stage_name`.

```hcl
# WRONG — removed in 6.0
resource "aws_api_gateway_deployment" "bad" {
  rest_api_id = aws_api_gateway_rest_api.example.id
  stage_name  = "prod"                   # WRONG — removed
  # canary_settings / stage_description — also removed
}
output "url" { value = aws_api_gateway_deployment.bad.invoke_url } # WRONG — removed

# CORRECT — fragment, deployment and REST API defined elsewhere
resource "aws_api_gateway_deployment" "good" {
  rest_api_id = aws_api_gateway_rest_api.example.id
}
resource "aws_api_gateway_stage" "prod" {
  rest_api_id   = aws_api_gateway_rest_api.example.id
  deployment_id = aws_api_gateway_deployment.good.id
  stage_name    = "prod" # example
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
```

## 2. reset_on_delete on aws_api_gateway_account

`reset_on_delete` was removed in 6.0; destroy now always resets the account settings. A `removed` block keeps
the old (keep-settings) behaviour.

```hcl
# WRONG — removed in 6.0
resource "aws_api_gateway_account" "bad" {
  cloudwatch_role_arn = var.cloudwatch_role_arn # placeholder
  reset_on_delete     = true                    # WRONG — removed
}

# CORRECT — drop the argument; to keep settings on removal use a removed block
resource "aws_api_gateway_account" "good" {
  cloudwatch_role_arn = var.cloudwatch_role_arn # placeholder
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
```

## 3. S3 backend with dynamodb_table

```hcl
# WRONG — deprecated
terraform {
  backend "s3" {
    bucket         = "example-tf-state" # example
    key            = "api-gateway/terraform.tfstate" # example
    region         = "eu-west-1"        # example
    dynamodb_table = "tf-locks"         # WRONG — deprecated
  }
}

# CORRECT
terraform {
  backend "s3" {
    bucket       = "example-tf-state" # example
    key          = "api-gateway/terraform.tfstate" # example
    region       = "eu-west-1"        # example
    use_lockfile = true
  }
}
# Source: https://developer.hashicorp.com/terraform/language/backend/s3
```

## 4. Pinning version 6.57.0

aws 6.57.0 was withdrawn from GitHub and the Registry.

```hcl
# WRONG
required_providers { aws = { source = "hashicorp/aws", version = "6.57.0" } } # WRONG — withdrawn

# CORRECT
required_providers { aws = { source = "hashicorp/aws", version = "~> 6.69" } }
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
# Source (`~>` constraint): https://developer.hashicorp.com/terraform/language/expressions/version-constraints
```
