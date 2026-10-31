# Always-Do — Connection, API Destination, Scheduler, Pipe

hashicorp/aws 6.x · Terraform ~> 1.16 · Pages read 2026-10-23. All names, ARNs, endpoints and numbers
are `# example` values.

## 5. Connection and API Destination

Connection: `authorization_type` is `API_KEY`, `BASIC` or `OAUTH_CLIENT_CREDENTIALS`;
`auth_parameters` takes at most one block. The service stores secrets in Secrets Manager. The
connection page has internal inconsistencies about `connectivity_parameters` placement (unverified), so the
`auth_parameters` contents are not reproduced here — read the current page before filling them in.
API destination: `name`, `invocation_endpoint`, `http_method`, `connection_arn` are required;
`invocation_rate_limit_per_second` defaults to 300. That the endpoint must start with https is (unverified):
only an AWS console page is known to state it, not the provider page.

```hcl
# FRAGMENT — the auth_parameters block is intentionally left out; fill it from the connection page.
resource "aws_cloudwatch_event_connection" "partner" {
  name               = "partner-api"       # example
  authorization_type = "API_KEY"           # API_KEY | BASIC | OAUTH_CLIENT_CREDENTIALS
  # auth_parameters { ... }  # see the connection page; never put secrets in plain text in the repo
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_connection.html.markdown

resource "aws_cloudwatch_event_api_destination" "partner" {
  name                             = "partner-webhook"                    # example
  invocation_endpoint              = "https://api.example.com/events"     # example
  http_method                      = "POST"                               # example
  connection_arn                   = aws_cloudwatch_event_connection.partner.arn
  invocation_rate_limit_per_second = 100                                  # example; default is 300
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudwatch_event_api_destination.html.markdown
```

## 6. Scheduler Schedule and Group

AWS: "Scheduled rules are a legacy feature of EventBridge … We recommend that you use Scheduler to
invoke targets on a schedule." Schedule requires `flexible_time_window`, `schedule_expression` and
`target { arn, role_arn }`. `schedule_expression_timezone` defaults to `UTC`. `group_name` defaults to
`default` and forces a new resource. Target `retry_policy`: `maximum_event_age_in_seconds` 60–86400
(default 86400), `maximum_retry_attempts` 0–185 (default 185). Universal targets use
`arn:aws:scheduler:::aws-sdk:<service>:<apiAction>` with the payload in `input`.

```hcl
# FRAGMENT — references aws_iam_role.scheduler and aws_sqs_queue.sched_dlq, defined elsewhere
# (see provisioning-aws-iam-v6, provisioning-aws-sqs-v6) and a target ARN supplied by var.target_arn.
resource "aws_scheduler_schedule_group" "batch" {
  name = "batch-jobs"                                   # example
}

resource "aws_scheduler_schedule" "nightly" {
  name       = "nightly-job"                            # example
  group_name = aws_scheduler_schedule_group.batch.name

  flexible_time_window {
    mode = "OFF"                                        # OFF | FLEXIBLE
  }
  schedule_expression          = "cron(0 2 * * ? *)"    # example
  schedule_expression_timezone = "Europe/Madrid"        # example; default UTC

  target {
    arn      = var.target_arn
    role_arn = aws_iam_role.scheduler.arn               # required
    retry_policy {
      maximum_event_age_in_seconds = 3600               # example; 60-86400
      maximum_retry_attempts       = 5                  # example; 0-185
    }
    dead_letter_config {
      arn = aws_sqs_queue.sched_dlq.arn
    }
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/scheduler_schedule.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/scheduler_schedule_group.html.markdown
# Source (legacy statement): https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-create-rule-schedule.html
```

## 7. Pipe (Brief)

`aws_pipes_pipe` requires `role_arn`, `source` and `target`. `desired_state` is `RUNNING` or
`STOPPED` (the page states no default). If `kms_key_identifier` is omitted, data is encrypted with an
AWS owned key. `log_configuration.level` is `OFF`, `ERROR`, `INFO` or `TRACE`. Pipes does not support
resource-based policies. 6.66.0 fixed `UpdatePipe` failing on an unset `server_root_ca_certificate`.

```hcl
# FRAGMENT — references aws_iam_role.pipe, aws_sqs_queue.source and aws_sqs_queue.sink,
# defined elsewhere; source/target types are examples.
resource "aws_pipes_pipe" "orders" {
  name          = "orders-pipe"                  # example
  role_arn      = aws_iam_role.pipe.arn
  source        = aws_sqs_queue.source.arn
  target        = aws_sqs_queue.sink.arn
  desired_state = "RUNNING"
  log_configuration {
    level = "ERROR"
    # destinations: CloudWatch Logs / Firehose / S3 — argument names are on the pipe page
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/pipes_pipe.html.markdown
```
