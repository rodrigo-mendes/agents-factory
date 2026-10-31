# Always-Do Patterns — provisioning-aws-sam-v6

Index of the always-do blueprints, split by topic. Each pattern has HCL or CLI examples and cites its
official source (read 2026-10-23). SAM is not a hashicorp/aws resource: sections 2–3 are SAM CLI patterns,
sections 4–6 are provider resources that deploy through CloudFormation.

| # | Pattern | Blueprint |
|---|---|---|
| 1 | Terraform block (`~> 1.16`, `~> 6.69`) and S3 backend with `use_lockfile` | [always-do-foundation](./always-do-foundation.md#1-terraform-block-and-s3-backend) |
| 2 | Local build and test with `--hook-name terraform` | [always-do-sam-cli](./always-do-sam-cli.md#2-local-build-and-test-with-the-terraform-hook) |
| 3 | The `sam metadata` resource (`sam_metadata_` name, `resource_type`) | [always-do-sam-cli](./always-do-sam-cli.md#3-the-sam-metadata-resource) |
| 4 | SAR stack, `sensitive()` for `NoEcho`, data source `required_capabilities` | [always-do-cloudformation](./always-do-cloudformation.md#4-serverless-application-repository-stack) |
| 5 | `aws_cloudformation_stack` with a SAM template (transform, `CAPABILITY_AUTO_EXPAND`, `iam_role_arn`, `template_url`) | [always-do-cloudformation](./always-do-cloudformation.md#5-cloudformation-stack-with-a-sam-template) |
| 6 | `aws_cloudformation_stack_set` parameters (configure or ignore) | [always-do-cloudformation](./always-do-cloudformation.md#6-cloudformation-stack-set) |
