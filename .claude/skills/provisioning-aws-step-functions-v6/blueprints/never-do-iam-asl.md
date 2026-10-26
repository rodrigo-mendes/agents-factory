# Never-Do — IAM and State Machine Definition

hashicorp/aws 6.x · Terraform ~> 1.16 · Pages read 2026-10-23. Scaffolding (unverified): ASL
structure and IAM JSON form are not quoted on the cited pages.

## 6. kms:ViaService on the execution role

AWS: do not put `kms:ViaService` on the execution role; it can break executions
(https://docs.aws.amazon.com/step-functions/latest/dg/encryption-at-rest.html).

```hcl
# WRONG — fragment of a role policy statement
# condition key kms:ViaService in the execution role's KMS statement (operator and value omitted)

# CORRECT — condition key kms:EncryptionContext:aws:states:stateMachineArn instead, with the
# state machine ARN as value (operator not given on the page), for example
#   arn:aws:states:eu-west-1:123456789012:stateMachine:order-workflow # example
```

## 7. .sync or .waitForTaskToken in an EXPRESS state machine

Express supports only the Request Response pattern; `.sync` and `.waitForTaskToken` are for Standard
(https://docs.aws.amazon.com/step-functions/latest/dg/connect-to-resource.html).

```hcl
# WRONG — fragment of a definition under type = "EXPRESS"
Resource = "arn:aws:states:::ecs:runTask.sync"

# CORRECT — Standard type for Run a Job / Wait for Callback
resource "aws_sfn_state_machine" "job" {
  type = "STANDARD"
  # ... name, role_arn, definition ...
}
```

## 8. States.ALL that is not alone and last

AWS: `States.ALL` in a retrier's or catcher's `ErrorEquals` "must appear alone in the `ErrorEquals`
array and must appear in the last retrier in the `Retry` array" (same for the last catcher in the
`Catch` array). It does not catch `States.DataLimitExceeded` or `States.Runtime`
(https://docs.aws.amazon.com/step-functions/latest/dg/concepts-error-handling.html).

```hcl
# WRONG — fragment of a state: States.ALL mixed with another name, and in a non-last retrier
Retry = [
  { ErrorEquals = ["States.ALL", "Lambda.ServiceException"], MaxAttempts = 2 }, # example
  { ErrorEquals = ["States.Timeout"], MaxAttempts = 6 }                         # example
]

# CORRECT — specific errors in earlier retriers, States.ALL alone in the last retrier
Retry = [
  { ErrorEquals = ["Lambda.ServiceException"], MaxAttempts = 6 }, # example
  { ErrorEquals = ["States.ALL"], MaxAttempts = 2 }               # example
]
```

## 9. Unqualified Lambda ARN in IAM when invoking a version or alias

With a `Qualifier`, version or alias, the policy must include it or `:*`; the unqualified function ARN
alone gives Access Denied (https://docs.aws.amazon.com/step-functions/latest/dg/connect-lambda.html).

```hcl
# WRONG — fragment of a role policy statement, function invoked with a qualifier
Action   = "lambda:InvokeFunction"
Resource = "arn:aws:lambda:eu-west-1:123456789012:function:worker" # example

# CORRECT — qualifier or :* included
Action   = "lambda:InvokeFunction"
Resource = [
  "arn:aws:lambda:eu-west-1:123456789012:function:worker",   # example
  "arn:aws:lambda:eu-west-1:123456789012:function:worker:*"  # example
]
```

## 10. Scoping logging delivery actions to a log group

The logging actions (`logs:CreateLogDelivery` and the others listed in the foundation blueprint) do
not support resource scoping (https://docs.aws.amazon.com/step-functions/latest/dg/cw-logs.html).

```hcl
# WRONG — fragment of a role policy statement
Action   = ["logs:CreateLogDelivery", "logs:PutResourcePolicy"]
Resource = "arn:aws:logs:eu-west-1:123456789012:log-group:/aws/vendedlogs/states/order:*" # example

# CORRECT
Action   = ["logs:CreateLogDelivery", "logs:PutResourcePolicy"] # full list in always-do-foundation section 2
Resource = "*"
```
