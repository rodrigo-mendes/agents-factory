# Always-Do — State Machine, Alias, Activity

hashicorp/aws 6.x · Terraform ~> 1.16 · Pages read 2026-10-23.

Scaffolding note (unverified): ASL structure keys (`StartAt`, `States`, `Type`, `End`, `Parameters`,
`FunctionName`, `Payload.$`) are not quoted on the pages cited below. The task Resource
ARN, `TimeoutSeconds`, `Retry`/`Catch` fields and error names are the cited facts.

## 3. State Machine With Logging, Tracing and a Published Version

Arguments, defaults and attributes:
https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sfn_state_machine.html.markdown

- `definition` and `role_arn` are required; `definition` is an ASL JSON string.
- `publish = true` publishes a version at creation and exposes `state_machine_version_arn`.
- `log_destination` must end with `:*`.

Lambda optimized integration and its IAM note:
https://docs.aws.amazon.com/step-functions/latest/dg/connect-lambda.html
Retry/Catch fields: https://docs.aws.amazon.com/step-functions/latest/dg/concepts-error-handling.html
Transient Lambda errors, `TimeoutSeconds`, `/aws/vendedlogs/` prefix:
https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html

```hcl
# Fragment: aws_iam_role.sfn (see always-do-foundation), aws_cloudwatch_log_group.sfn (name starts
# with /aws/vendedlogs/states; see provisioning-aws-cloudwatch-v6) and aws_lambda_function.worker
# (see provisioning-aws-lambda-v6) are defined elsewhere.
resource "aws_sfn_state_machine" "main" {
  name     = "order-workflow" # example
  role_arn = aws_iam_role.sfn.arn
  type     = "STANDARD"
  publish  = true

  definition = jsonencode({
    StartAt = "InvokeWorker"
    States = {
      InvokeWorker = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = aws_lambda_function.worker.arn
          "Payload.$"  = "$"
        }
        TimeoutSeconds = 60 # example
        Retry = [{
          ErrorEquals = [
            "Lambda.ServiceException", "Lambda.AWSLambdaException",
            "Lambda.SdkClientException", "Lambda.ClientExecutionTimeoutException"
          ]
          IntervalSeconds = 2 # example
          MaxAttempts     = 6 # example
          BackoffRate     = 2 # example
        }]
        Catch = [{ ErrorEquals = ["States.ALL"], Next = "Failed" }]
        End   = true
      }
      Failed = { Type = "Fail" }
    }
  })

  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.sfn.arn}:*"
    include_execution_data = true    # example
    level                  = "ERROR" # example; ALL, ERROR, FATAL or OFF (default OFF)
  }

  tracing_configuration {
    enabled = true
  }

  tags = { Environment = "dev" } # example
}
```

## 4. Alias With Weighted Routing

An alias points to up to two versions; weights must total 100; aliases point only to versions
(https://docs.aws.amazon.com/step-functions/latest/dg/concepts-state-machine-alias.html).
Alias arguments: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sfn_alias.html.markdown
Versions data source (`statemachine_arn` in, `statemachine_versions` list out):
https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/sfn_state_machine_versions.html.markdown

```hcl
# Fragment: aws_sfn_state_machine.main is defined in section 3.
resource "aws_sfn_alias" "live" {
  name        = "live"                      # example
  description = "Production traffic alias"  # example

  routing_configuration {
    state_machine_version_arn = aws_sfn_state_machine.main.state_machine_version_arn
    weight                    = 100
  }
}

# Fragment: weighted split between two versions. var.other_version_arn is a placeholder input you
# fill with a published version ARN, for example one listed by the data source
# aws_sfn_state_machine_versions (statemachine_arn -> statemachine_versions); the wiring is not shown.
resource "aws_sfn_alias" "canary" {
  name = "canary" # example

  routing_configuration {
    # version published when the state machine was created (publish = true)
    state_machine_version_arn = aws_sfn_state_machine.main.state_machine_version_arn
    weight                    = 10 # example
  }
  routing_configuration {
    state_machine_version_arn = var.other_version_arn # placeholder input
    weight                    = 90                    # example
  }
}
```

## 5. Activity With Tags

Security Hub StepFunctions.2 (low severity) checks that activities are tagged
(https://docs.aws.amazon.com/securityhub/latest/userguide/stepfunctions-controls.html). AWS best
practices say to tag state machines and activities
(https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html).
Activity arguments: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sfn_activity.html.markdown

```hcl
resource "aws_sfn_activity" "worker" {
  name = "order-worker" # example
  tags = { Environment = "dev" } # example
}
```

Workers: AWS recommends at least 100 open `GetActivityTask` polls per activity ARN in production
(https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html).
