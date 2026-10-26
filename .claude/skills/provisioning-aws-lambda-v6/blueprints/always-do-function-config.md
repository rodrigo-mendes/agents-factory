# Always-Do — Image, VPC, Environment/KMS, Tracing, Dead-Letter Config

hashicorp/aws 6.x · Terraform ~> 1.16 · Provider page read 2026-10-23; AWS pages read 2026-10-23.
Every `# example` value is a placeholder to replace. All HCL here is a fragment (references defined elsewhere).

Function page: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_function.html.markdown

## 4. Container image function

`package_type = "Image"` with `image_uri`; `image_config` accepts `command`, `entry_point`,
`working_directory`. `source_kms_key_arn` conflicts with `image_uri`. Lambda sends no deprecation
notifications for container images; rebuild from the latest base image
(https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html).

```hcl
# fragment — references aws_iam_role.lambda
resource "aws_lambda_function" "image" {
  function_name = "orders-image-fn"                 # example
  role          = aws_iam_role.lambda.arn
  package_type  = "Image"
  image_uri     = "<account>.dkr.ecr.<region>.amazonaws.com/orders:1.0" # placeholder
  image_config {
    command = ["app.handler"] # example
  }
}
```

## 5. VPC attachment

`vpc_config { subnet_ids, security_group_ids, ipv6_allowed_for_dual_stack }` (default `false`); all-empty
lists are treated as unset. Security Hub Lambda.5 expects VPC functions in at least 2 AZs, so spread
`subnet_ids` across AZs (https://docs.aws.amazon.com/securityhub/latest/userguide/lambda-controls.html).

The VPC needs `ec2:CreateNetworkInterface`, `DescribeNetworkInterfaces`, `DescribeSubnets`,
`DeleteNetworkInterface`, `AssignPrivateIpAddresses`, `UnassignPrivateIpAddresses` on `"*"`
(`AWSLambdaVPCAccessExecutionRole` or custom). Use private subnets; internet access needs NAT. Removing the
VPC config can take up to 20 minutes to delete the ENI, and **deleting the execution role before ENI
deletion prevents cleanup** — keep the role and its VPC policy attachment until the function is destroyed
(https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html).

`replace_security_groups_on_destroy` (default `false`): when `true`, `replacement_security_group_ids` is
required, so the original security group can be deleted.

```hcl
# fragment — subnet and SG ids come from provisioning-aws-vpc-v6
resource "aws_lambda_function" "private" {
  function_name = "orders-private-fn" # example
  role          = aws_iam_role.lambda.arn
  filename      = "build/orders.zip"  # example
  handler       = "app.handler"       # example
  runtime       = "python3.14"        # example
  vpc_config {
    subnet_ids         = var.private_subnet_ids # spread across >= 2 AZs
    security_group_ids = [var.lambda_sg_id]
  }
}
```

## 6. Environment variables and KMS

`environment { variables = {...} }`; `kms_key_arn` encrypts environment variables (default: AWS service
key); `source_kms_key_arn` encrypts the zip package. If Lambda reports it was unable to decrypt the
environment variables, the page says it usually means the role was recreated — switch the role away and
back, or taint and re-apply. Key design belongs to `provisioning-aws-kms-v6`.

```hcl
# fragment
resource "aws_lambda_function" "secure" {
  function_name = "orders-secure-fn" # example
  role          = aws_iam_role.lambda.arn
  filename      = "build/orders.zip" # example
  handler       = "app.handler"      # example
  runtime       = "python3.14"       # example
  kms_key_arn   = var.kms_key_arn    # placeholder
  environment {
    variables = { STAGE = "prod" }   # example
  }
}
```

## 7. Tracing and dead-letter queue

`tracing_config { mode }` is `Active` or `PassThrough`; Security Hub Lambda.7 checks for active tracing
(https://docs.aws.amazon.com/securityhub/latest/userguide/lambda-controls.html).
`dead_letter_config { target_arn }` takes an SNS topic or SQS queue ARN.

```hcl
# fragment
resource "aws_lambda_function" "traced" {
  function_name = "orders-traced-fn" # example
  role          = aws_iam_role.lambda.arn
  filename      = "build/orders.zip" # example
  handler       = "app.handler"      # example
  runtime       = "python3.14"       # example
  tracing_config {
    mode = "Active"
  }
  dead_letter_config {
    target_arn = var.dlq_arn # placeholder: SQS queue or SNS topic ARN
  }
}
```
