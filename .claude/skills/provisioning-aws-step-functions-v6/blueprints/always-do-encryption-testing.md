# Always-Do — Customer Managed Key Encryption, Testing

hashicorp/aws 6.x · Terraform ~> 1.16 · Pages read 2026-10-23.

Scaffolding note (unverified): JSON policy structure (`Version`, `Effect`, `Resource` forms) is not
quoted on the cited pages, and condition operators are not given, so the conditions below are shown
as comments (key and value only). Key policy authoring belongs to `provisioning-aws-kms-v6`.

## 6. Customer Managed Key Encryption

Source for every statement below: https://docs.aws.amazon.com/step-functions/latest/dg/encryption-at-rest.html

- Execution role needs `kms:Decrypt` and `kms:GenerateDataKey`, scoped with
  `kms:EncryptionContext:aws:states:stateMachineArn` (activities: `aws:states:activityArn`).
- Sync Express workflows need only `kms:Decrypt` on the execution role.
- With a customer managed key and logging, the key policy allows `delivery.logs.amazonaws.com` only
  `kms:Decrypt`; the role needs `kms:GenerateDataKey` with `kms:EncryptionContext:SourceArn` set to
  an `arn:aws:logs:...` ARN.
- `kms_key_id` accepts alias, alias ARN, key ID or key ARN; an ARN is required cross-account
  (https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sfn_state_machine.html.markdown).

```hcl
# Fragment: aws_kms_key.sfn (see provisioning-aws-kms-v6), aws_sfn_state_machine.main and
# aws_iam_role.sfn are defined elsewhere. Only the changed block is shown.
resource "aws_sfn_state_machine" "main" {
  # ... name, role_arn, definition as in always-do-state-machine section 3 ...
  encryption_configuration {
    type                              = "CUSTOMER_MANAGED_KMS_KEY"
    kms_key_id                        = aws_kms_key.sfn.arn
    kms_data_key_reuse_period_seconds = 300 # example; AWS range 60-900 s, default 300
  }
}
```

Execution role statements:

```hcl
# Fragment: attaches to aws_iam_role.sfn; ARNs in the comments are example values.
resource "aws_iam_role_policy" "sfn_kms" {
  name = "kms" # example
  role = aws_iam_role.sfn.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["kms:Decrypt", "kms:GenerateDataKey"]
        Resource = aws_kms_key.sfn.arn
        # Condition (operator not given on the page): the key
        #   kms:EncryptionContext:aws:states:stateMachineArn
        # with the state machine ARN as value, for example
        #   arn:aws:states:eu-west-1:123456789012:stateMachine:order-workflow # example
      },
      {
        Effect   = "Allow"
        Action   = ["kms:GenerateDataKey"] # logging with a customer managed key
        Resource = aws_kms_key.sfn.arn
        # Condition (operator not given on the page): the key
        #   kms:EncryptionContext:SourceArn
        # with an arn:aws:logs:... value, for example
        #   arn:aws:logs:eu-west-1:123456789012:log-group:/aws/vendedlogs/states/order # example
      }
    ]
  })
}
```

Key policy statement to add (one statement of the key policy, not the whole policy):

```hcl
locals {
  sfn_logs_key_statement = {
    Effect    = "Allow"
    Principal = { Service = "delivery.logs.amazonaws.com" }
    Action    = "kms:Decrypt"
    Resource  = "*"
  }
}
```

The deploying principal needs `kms:DescribeKey` and `kms:GenerateDataKey`.

## 7. Terraform Test and CI

Source: https://developer.hashicorp.com/terraform/language/tests and
https://developer.hashicorp.com/terraform/language/tests/mocking

`.tftest.hcl` files live in `tests/`; `mock_provider` and `command = plan` are the documented building blocks.

```hcl
# tests/state_machine.tftest.hcl — fragment: assumes the root module declares aws_sfn_state_machine.main.
mock_provider "aws" {}

run "tracing_is_enabled" {
  command = plan

  assert {
    condition     = aws_sfn_state_machine.main.tracing_configuration[0].enabled
    error_message = "X-Ray tracing must be enabled."
  }
}
```

CI commands (https://developer.hashicorp.com/terraform/cli/commands/plan and
https://developer.hashicorp.com/terraform/cli/commands/validate):

```
terraform init -backend=false
terraform validate -json
terraform plan -detailed-exitcode -input=false -out=tfplan   # exit 0 no changes, 1 error, 2 changes
```
