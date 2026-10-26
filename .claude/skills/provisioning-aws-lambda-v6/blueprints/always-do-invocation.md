# Always-Do — Alias, Provisioned Concurrency, Permission, Function URL, Event Invoke Config

hashicorp/aws 6.x · Terraform ~> 1.16 · Provider pages read 2026-10-23. Every `# example` value is a
placeholder. All HCL here is a fragment (references defined elsewhere).

## 8. Alias and provisioned concurrency

Alias requires `function_name`, `function_version` (`$LATEST` or a number) and `name` (not purely numeric);
`routing_config.additional_version_weights` keeps the remaining weight on `function_version`.
Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_alias.html.markdown

Provisioned concurrency requires `function_name`, `provisioned_concurrent_executions` (≥ 1) and
`qualifier` (version or alias). `skip_destroy` defaults to `false`; when `true` the configuration is left
dangling and billable.
Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_provisioned_concurrency_config.html.markdown

```hcl
# fragment — references aws_lambda_function.orders (always-do-function.md section 3, which sets publish = true)
resource "aws_lambda_alias" "live" {
  name             = "live" # example
  function_name    = aws_lambda_function.orders.function_name
  function_version = aws_lambda_function.orders.version
}

resource "aws_lambda_provisioned_concurrency_config" "live" {
  function_name                     = aws_lambda_function.orders.function_name
  qualifier                         = aws_lambda_alias.live.name
  provisioned_concurrent_executions = 2 # example
}
```

`publish` defaults to `false`; `version` and `qualified_arn` reflect the published version
(https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_function.html.markdown).

## 9. Permission

Required: `action`, `function_name`, `principal`. `source_arn` and `source_account` (cross-account, S3,
SES) narrow the caller; `statement_id` is generated when omitted and is exclusive with
`statement_id_prefix`. Security Hub Lambda.1 fails for S3 invokers without `AWS:SourceAccount`
(https://docs.aws.amazon.com/securityhub/latest/userguide/lambda-controls.html).
Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_permission.html.markdown

```hcl
# fragment — S3 bucket is defined elsewhere (see the S3 skill)
resource "aws_lambda_permission" "from_s3" {
  statement_id   = "AllowS3Invoke" # example
  action         = "lambda:InvokeFunction"
  function_name  = aws_lambda_function.orders.function_name
  principal      = "s3.amazonaws.com"
  source_arn     = var.bucket_arn        # placeholder
  source_account = var.bucket_account_id # placeholder
}
```

API Gateway invoker permissions belong to `provisioning-aws-api-gateway-v6`.

## 10. Function URL

`authorization_type` is required (`AWS_IAM` or `NONE`); `invoke_mode` defaults to `BUFFERED`
(`RESPONSE_STREAM` optional); `qualifier` is an alias or `$LATEST`. With `NONE`, the provider adds
`lambda:InvokeFunctionUrl` and `lambda:InvokeFunction` permissions at create and these policies are not
removed from AWS when the resource is destroyed.
Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_function_url.html.markdown

```hcl
# fragment
resource "aws_lambda_function_url" "live" {
  function_name      = aws_lambda_function.orders.function_name
  qualifier          = aws_lambda_alias.live.name
  authorization_type = "AWS_IAM"
}
```

## 11. Event invoke config

`maximum_retry_attempts` 0–2 (default 2); `maximum_event_age_in_seconds` 60–21600. In `destination_config`
set at least one of `on_success` / `on_failure`, otherwise remove the block. The function role needs, for
example, `sqs:SendMessage` or `sns:Publish`; otherwise the API returns a generic
`InvalidParameterValueException`.
Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_function_event_invoke_config.html.markdown

```hcl
# fragment
resource "aws_lambda_function_event_invoke_config" "orders" {
  function_name                = aws_lambda_function.orders.function_name
  maximum_retry_attempts       = 1     # example
  maximum_event_age_in_seconds = 3600  # example
  destination_config {
    on_failure {
      destination = var.failure_queue_arn # placeholder
    }
  }
}
```
