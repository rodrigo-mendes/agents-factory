# Never-Do — Function Arguments

hashicorp/aws 6.x · Terraform ~> 1.16 · Provider page read 2026-10-23. Every `# example` value is a
placeholder. All HCL here is a fragment (references defined elsewhere).

Function page: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_function.html.markdown

## 1. Multiple code sources on one function

Exactly one code source is allowed: `filename`, `s3_bucket` (+ `s3_key`), or `image_uri`; they conflict.

```hcl
# WRONG — fragment
resource "aws_lambda_function" "bad" {
  function_name = "orders-fn"        # example
  role          = aws_iam_role.lambda.arn
  filename      = "build/orders.zip" # example
  image_uri     = var.image_uri      # WRONG — second code source
}

# CORRECT — fragment
resource "aws_lambda_function" "good" {
  function_name = "orders-fn"        # example
  role          = aws_iam_role.lambda.arn
  filename      = "build/orders.zip" # example
  handler       = "app.handler"      # example
  runtime       = "python3.14"       # example
}
```

## 2. Source KMS key on an image function

`source_kms_key_arn` encrypts the zip package and conflicts with `image_uri`.

```hcl
# WRONG — fragment
resource "aws_lambda_function" "bad" {
  function_name      = "orders-image-fn" # example
  role               = aws_iam_role.lambda.arn
  package_type       = "Image"
  image_uri          = var.image_uri
  source_kms_key_arn = var.kms_key_arn   # WRONG — conflicts with image_uri
}

# CORRECT — fragment: drop source_kms_key_arn; kms_key_arn still encrypts environment variables
resource "aws_lambda_function" "good" {
  function_name = "orders-image-fn" # example
  role          = aws_iam_role.lambda.arn
  package_type  = "Image"
  image_uri     = var.image_uri
  kms_key_arn   = var.kms_key_arn
}
```

## 3. Relying on source_code_hash for out-of-band changes

The page says `source_code_hash` is a provider-only synthetic value and out-of-band changes to the source
code will not be captured. `code_sha256` is the Base64 SHA-256 of the zip (or the image digest; layers excluded).

```hcl
# WRONG — fragment
output "drift_check" {
  value = aws_lambda_function.orders.source_code_hash # WRONG — will not see out-of-band changes
}

# CORRECT — fragment
output "deployed_hash" {
  value = aws_lambda_function.orders.code_sha256
}
```

## 4. More than five layers

A function accepts up to 5 layer version ARNs in `layers`.

```hcl
# WRONG — fragment: six layer ARNs
resource "aws_lambda_function" "bad" {
  function_name = "orders-fn" # example
  role          = aws_iam_role.lambda.arn
  layers        = [var.l1, var.l2, var.l3, var.l4, var.l5, var.l6] # WRONG — more than 5
}

# CORRECT — fragment: at most five
resource "aws_lambda_function" "good" {
  function_name = "orders-fn" # example
  role          = aws_iam_role.lambda.arn
  layers        = [var.l1, var.l2, var.l3, var.l4, var.l5]
}
```
