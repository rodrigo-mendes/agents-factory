# Always-Do — Observability and Testing (Flow Logs, terraform test, CI)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-14.

## 9. Flow Logs

`log_group_name` was removed in 6.0 — use `log_destination` (ARN) + `log_destination_type`.
IAM role must trust `vpc-flow-logs.amazonaws.com` with `aws:SourceAccount`/`aws:SourceArn`
conditions. Security Hub EC2.6 checks that REJECT traffic is logged.

```hcl
resource "aws_cloudwatch_log_group" "flow_logs" {
  name              = "/aws/vpc/flow-logs"
  retention_in_days = 30
}

data "aws_caller_identity" "current" {}

resource "aws_iam_role" "flow_logs" {
  name = "vpc-flow-logs-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "vpc-flow-logs.amazonaws.com" }
      Action    = "sts:AssumeRole"
      Condition = {
        StringEquals = { "aws:SourceAccount" = data.aws_caller_identity.current.account_id }
        ArnLike = {
          "aws:SourceArn" = "arn:aws:ec2:eu-west-1:${data.aws_caller_identity.current.account_id}:vpc-flow-log/*"
        }
      }
    }]
  })
}

resource "aws_iam_role_policy" "flow_logs" {
  role = aws_iam_role.flow_logs.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents",
                  "logs:DescribeLogGroups", "logs:DescribeLogStreams"]
      Resource = "*"
    }]
  })
}

resource "aws_flow_log" "vpc" {
  vpc_id                   = aws_vpc.main.id
  traffic_type             = "ALL"
  iam_role_arn             = aws_iam_role.flow_logs.arn
  log_destination_type     = "cloud-watch-logs"
  log_destination          = aws_cloudwatch_log_group.flow_logs.arn   # ARN, not name
  max_aggregation_interval = 60   # 60s for faster detection; default 600
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/flow_log.html.markdown
# Source: https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs-iam-role.html
# Source: https://docs.aws.amazon.com/securityhub/latest/userguide/ec2-controls.html (EC2.6)
```

For S3/parquet destination use `log_destination_type = "s3"` + `log_destination` (bucket ARN) +
`destination_options { file_format = "parquet" ... }`. No IAM role needed for S3.

## 10. Terraform Test and CI

Use `mock_provider "aws"` with `command = plan` for CI-safe unit tests (no AWS credentials needed).

```hcl
# tests/vpc.tftest.hcl
mock_provider "aws" {}

variables { vpc_cidr = "10.1.0.0/16" }

run "vpc_has_dns_hostnames" {
  command = plan
  assert {
    condition     = aws_vpc.main.enable_dns_hostnames == true
    error_message = "VPC must have enable_dns_hostnames = true"
  }
}

run "public_subnets_map_public_ip" {
  command = plan
  assert {
    condition     = alltrue([for s in aws_subnet.public : s.map_public_ip_on_launch])
    error_message = "All public subnets must map public IPs on launch"
  }
}

run "eip_domain_is_vpc" {
  command = plan
  assert {
    condition     = alltrue([for e in aws_eip.nat : e.domain == "vpc"])
    error_message = "EIPs must use domain = 'vpc'"
  }
}
```

CI pipeline:
```bash
terraform init -backend=false          # no credentials needed
terraform validate -json               # syntax + internal consistency
terraform plan -detailed-exitcode -input=false -out=tfplan  # 0=no changes, 1=error, 2=changes
terraform test -test-directory=tests   # mock-based unit tests
```
# Source: https://developer.hashicorp.com/terraform/language/tests
# Source: https://developer.hashicorp.com/terraform/cli/commands/test
# Source: https://developer.hashicorp.com/terraform/language/tests/mocking
# Source: https://developer.hashicorp.com/terraform/cli/commands/plan
# Source: https://developer.hashicorp.com/terraform/cli/commands/validate
