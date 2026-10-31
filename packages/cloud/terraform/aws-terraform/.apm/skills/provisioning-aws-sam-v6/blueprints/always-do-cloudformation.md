# Always-Do — CloudFormation-based resources (SAR stack, SAM template stack, stack set)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources read 2026-10-23. CloudFormation, not Terraform, runs the SAM
transform (https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/transform-aws-serverless.html).
The attribute named in the stack set `ignore_changes` example (`parameters`) is not confirmed on the provider page (unverified).

## 4. Serverless Application Repository stack

`aws_serverlessapplicationrepository_cloudformation_stack`: `application_id` and `name` required; AWS prefixes the
deployed stack with `serverlessrepo-`; `semantic_version` defaults to latest; create/update/delete timeouts 30m
(https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/serverlessapplicationrepository_cloudformation_stack.html.markdown).
The data source `aws_serverlessapplicationrepository_application` is "useful for finding the capabilities an
application requires" and feeds `required_capabilities` into the stack
(https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/serverlessapplicationrepository_application.html.markdown).

```hcl
# Fragment: var.api_key is declared elsewhere. All values are examples.
data "aws_serverlessapplicationrepository_application" "app" {
  application_id   = "arn:aws:serverlessrepo:us-east-1:123456789012:applications/example-app" # example
  semantic_version = "1.0.0"                                                                  # example
}

resource "aws_serverlessapplicationrepository_cloudformation_stack" "app" {
  name             = "example-app" # example; AWS prefixes the stack with serverlessrepo-
  application_id   = data.aws_serverlessapplicationrepository_application.app.application_id
  semantic_version = data.aws_serverlessapplicationrepository_application.app.semantic_version
  capabilities     = data.aws_serverlessapplicationrepository_application.app.required_capabilities

  parameters = {
    ApiKey = sensitive(var.api_key) # example NoEcho parameter, masked in plan and terraform show
  }

  tags = {
    Environment = "dev" # example
  }
}
```

`NoEcho` values: CloudFormation hides them in API responses but Terraform still stores them in state; since 6.52.0
they are stored in plaintext rather than as `****` (page above and the CHANGELOG,
https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md). Secure the state backend.
Import: `import` block (Terraform 1.5.0 or newer) or `terraform import`, with the stack name (with or without the
`serverlessrepo-` prefix) or the stack ID (resource page above).

## 5. CloudFormation stack with a SAM template

The transform is declared at the template top level; its value must be the literal `AWS::Serverless-2016-10-31`
(no parameter or function), and CloudFormation expands the SAM syntax when it creates the change set (transform page above).
`aws_cloudformation_stack`: `capabilities` accepts `CAPABILITY_IAM`, `CAPABILITY_NAMED_IAM`,
`CAPABILITY_AUTO_EXPAND`; `template_body` up to 51,200 bytes; `template_url` up to 460,800 bytes; timeouts 30m;
import by stack `name`
(https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudformation_stack.html.markdown).
The CreateStack API page says `CAPABILITY_AUTO_EXPAND` is required when a template with macros, including the
`AWS::Serverless` transform, is created without first reviewing a change set, and that the `RoleARN` role is used
for all future operations on the stack, so it must grant least privilege
(https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_CreateStack.html).
Whether the provider creates stacks through a reviewed change set is not stated (unverified), so which
`capabilities` this resource needs for a SAM template is an Ask First item in SKILL.md.

```yaml
# Fragment: top of the SAM template (template.yaml)
Transform: AWS::Serverless-2016-10-31
```

```hcl
# Fragment: aws_iam_role.cfn_service is defined elsewhere (least privilege). Values are examples.
resource "aws_cloudformation_stack" "sam_app" {
  name         = "example-sam-app"                                       # example
  template_url = "https://example-bucket.s3.amazonaws.com/template.yaml" # example; use when over 51,200 bytes
  # capabilities: see Ask First — capabilities depend on whether a change set is reviewed
  iam_role_arn = aws_iam_role.cfn_service.arn
  on_failure   = "ROLLBACK"                                              # do not combine with disable_rollback

  tags = {
    Environment = "dev" # example
  }
}
```

`CodeUri` inside the template points to artifacts already uploaded to S3 in the transform page's example
(`s3://…/MySourceCode.zip`); whether anything uploads them for you is (unverified) — see Ask First in SKILL.md.
Security Hub CloudFormation.4 maps to `iam_role_arn`; CloudFormation.2 checks stack tags
(https://docs.aws.amazon.com/securityhub/latest/userguide/cloudformation-controls.html).

## 6. CloudFormation stack set

`aws_cloudformation_stack_set`: `permission_model` is `SELF_MANAGED` (default) or `SERVICE_MANAGED`;
`administration_role_arn` must be set for `SELF_MANAGED`; `execution_role_name` defaults to
`AWSCloudFormationStackSetExecutionRole` for `SELF_MANAGED` and must not be set for `SERVICE_MANAGED`;
`template_body` (51,200 bytes) or `template_url` (S3, 460,800 bytes). NOTE on the page: all template parameters,
including those with a `Default`, must be configured or ignored via `lifecycle { ignore_changes }`; all `NoEcho`
template parameters must be ignored that way
(https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudformation_stack_set.html.markdown).

```hcl
# Fragment: aws_iam_role.stackset_admin is defined elsewhere. Values are examples.
resource "aws_cloudformation_stack_set" "example" {
  name                    = "example-stack-set"                                    # example
  permission_model        = "SELF_MANAGED"
  administration_role_arn = aws_iam_role.stackset_admin.arn
  template_url            = "https://example-bucket.s3.amazonaws.com/template.yaml" # example

  lifecycle {
    ignore_changes = [parameters] # example attribute
  }
}
```

Whether stack sets accept the `AWS::Serverless` transform is not stated on the page (unverified). Import: `name`,
or `name,DELEGATED_ADMIN` for delegated administrators (page above).
