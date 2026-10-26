# Never-Do — CloudFormation-based resources

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources read 2026-10-23. All values are examples.

## 1. Assuming SAR NoEcho values are masked in state

CloudFormation hides `NoEcho` values in API responses, but Terraform still stores them in state; since 6.52.0 they are
stored in plaintext rather than `****`. The page says to wrap them with `sensitive()` to mask them in plan and
`terraform show`.

```hcl
# WRONG — fragment, var.api_key declared elsewhere: value neither masked nor is the state backend secured
resource "aws_serverlessapplicationrepository_cloudformation_stack" "app" {
  name           = "example-app" # example
  application_id = "arn:aws:serverlessrepo:us-east-1:123456789012:applications/example-app" # example
  parameters = {
    ApiKey = var.api_key # NoEcho parameter, plaintext in state
  }
}

# CORRECT
resource "aws_serverlessapplicationrepository_cloudformation_stack" "app" {
  name           = "example-app" # example
  application_id = "arn:aws:serverlessrepo:us-east-1:123456789012:applications/example-app" # example
  parameters = {
    ApiKey = sensitive(var.api_key) # plus a secured state backend
  }
}
```

Sources: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/serverlessapplicationrepository_cloudformation_stack.html.markdown ;
https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md

## 2. Stack set NoEcho parameters left unignored

The `aws_cloudformation_stack_set` page: "All `NoEcho` template parameters must be ignored with the `lifecycle`
configuration block `ignore_changes` argument."

```hcl
# WRONG — fragment: template has a NoEcho parameter, nothing ignored
resource "aws_cloudformation_stack_set" "example" {
  name                    = "example-stack-set" # example
  administration_role_arn = aws_iam_role.stackset_admin.arn # defined elsewhere
  template_url            = "https://example-bucket.s3.amazonaws.com/template.yaml" # example
}

# CORRECT
resource "aws_cloudformation_stack_set" "example" {
  name                    = "example-stack-set" # example
  administration_role_arn = aws_iam_role.stackset_admin.arn # defined elsewhere
  template_url            = "https://example-bucket.s3.amazonaws.com/template.yaml" # example

  lifecycle {
    ignore_changes = [parameters] # example attribute; see always-do-cloudformation.md header
  }
}
```

Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudformation_stack_set.html.markdown

## 3. on_failure together with disable_rollback

On `aws_cloudformation_stack`, `on_failure` (`DO_NOTHING` / `ROLLBACK` / `DELETE`) conflicts with `disable_rollback`.

```hcl
# WRONG — fragment, conflicting arguments
resource "aws_cloudformation_stack" "bad" {
  name             = "example-sam-app" # example
  template_url     = "https://example-bucket.s3.amazonaws.com/template.yaml" # example
  # capabilities omitted: see Ask First in SKILL.md
  on_failure       = "ROLLBACK"
  disable_rollback = true
}

# CORRECT — one of the two
resource "aws_cloudformation_stack" "good" {
  name         = "example-sam-app" # example
  template_url = "https://example-bucket.s3.amazonaws.com/template.yaml" # example
  on_failure   = "ROLLBACK"
}
```

Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudformation_stack.html.markdown

## 4. Inline template over the template_body limit

`template_body` is limited to 51,200 bytes; `template_url` to 460,800 bytes.

```hcl
# WRONG — fragment: local.large_sam_template is defined elsewhere and is larger than 51,200 bytes (example)
resource "aws_cloudformation_stack" "bad" {
  name          = "example-sam-app" # example
  template_body = local.large_sam_template
}

# CORRECT
resource "aws_cloudformation_stack" "good" {
  name         = "example-sam-app" # example
  template_url = "https://example-bucket.s3.amazonaws.com/template.yaml" # example, up to 460,800 bytes
}
```

Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudformation_stack.html.markdown
