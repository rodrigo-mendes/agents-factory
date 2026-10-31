# Always-Do — SQS Event Source Mapping, Layers, Code Signing

hashicorp/aws 6.x · Terraform ~> 1.16 · Provider pages read 2026-10-23; AWS pages read 2026-10-23.
Every `# example` value is a placeholder. All HCL here is a fragment (references defined elsewhere).

## 12. SQS event source mapping

`batch_size` defaults to 10 for SQS (100 for Kinesis, DynamoDB, MQ, MSK); `enabled` defaults to `true`.
`scaling_config { maximum_concurrency }` is SQS-only and must be ≥ 2; values above 1000 need a quota
request. Do not set `starting_position` for SQS. `function_response_types = ["ReportBatchItemFailures"]`
enables partial batch response on SQS and streams.
Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_event_source_mapping.html.markdown

With partial batch response, Lambda does not scale down polling on failures; an exception without it fails
the whole batch. The function timeout must not exceed the queue visibility timeout.
Sources: https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html ,
https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html

```hcl
# fragment — queue is defined elsewhere (provisioning-aws-sqs-v6)
resource "aws_lambda_event_source_mapping" "orders" {
  function_name           = aws_lambda_function.orders.arn
  event_source_arn        = var.queue_arn # placeholder (unverified: required event-source identifier)
  batch_size              = 10            # default for SQS
  function_response_types = ["ReportBatchItemFailures"]
  scaling_config {
    maximum_concurrency = 10 # example; must be >= 2
  }
}
```

Mapping timeouts: create 10m, update 10m, delete 5m; `use_resource_timeout_for_propagation` was added in
6.54.0 (https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md).
Import uses the mapping UUID.

## 13. Layer version

Required `layer_name`; `filename` or `s3_bucket`/`s3_key` (bucket in the same region);
`compatible_runtimes` (up to 15) and `compatible_architectures`. Without `skip_destroy = true`, changing
almost any argument deletes the old version and creates a new one; with `true`, old versions stay as
"intentional dangling resources" that may incur extra expense. A function takes up to 5 layer version ARNs.
Sources: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_layer_version.html.markdown ,
https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_function.html.markdown

```hcl
# fragment
resource "aws_lambda_layer_version" "deps" {
  layer_name          = "orders-deps"       # example
  filename            = "build/deps.zip"    # example
  compatible_runtimes = ["python3.14"]      # example
}

resource "aws_lambda_function" "with_layer" {
  function_name = "orders-layered-fn" # example
  role          = aws_iam_role.lambda.arn
  filename      = "build/orders.zip"  # example
  handler       = "app.handler"       # example
  runtime       = "python3.14"        # example
  layers        = [aws_lambda_layer_version.deps.arn]
}
```

## 14. Code signing config

`allowed_publishers { signing_profile_version_arns }` is required (up to 20);
`policies { untrusted_artifact_on_deployment }` is `Warn` (default) or `Enforce`. Attach with
`code_signing_config_arn` on the function.
Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_code_signing_config.html.markdown

```hcl
# fragment
resource "aws_lambda_code_signing_config" "main" {
  allowed_publishers {
    signing_profile_version_arns = [var.signing_profile_version_arn] # placeholder
  }
  policies {
    untrusted_artifact_on_deployment = "Enforce"
  }
}
# on the function: code_signing_config_arn = aws_lambda_code_signing_config.main.arn
```
