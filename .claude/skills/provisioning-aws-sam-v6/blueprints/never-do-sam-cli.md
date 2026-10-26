# Never-Do — SAM CLI with Terraform projects

SAM CLI v1.170.0 · Sources read 2026-10-23. File and resource names are examples.

## 1. Incompatible flags with hook-name

The `sam build` reference page lists `--build-in-source`, `--parameter-overrides` and `--template-file` as
incompatible with `--hook-name`.

```bash
# WRONG — incompatible with --hook-name
sam build --hook-name terraform --template-file template.yaml   # example file name

# CORRECT
sam build --hook-name terraform
```

Source: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-build.html

## 2. Terraform-only flags without hook-name

`--terraform-project-root-path` (build) "requires that `--hook-name` be set to `terraform`"; `--terraform-plan-file`
requires `--hook-name terraform`.

```bash
# WRONG — no --hook-name
sam build --terraform-project-root-path ../infra            # example path
sam local start-api --terraform-plan-file plan.json         # example file name

# CORRECT
sam build --hook-name terraform --terraform-project-root-path ../infra
sam local start-api --hook-name terraform --terraform-plan-file plan.json
```

Sources: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-build.html ;
https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-local-start-api.html

## 3. sam metadata name without the prefix

The `sam metadata` resource is a `null_resource` whose name starts with `sam_metadata_`.

```hcl
# WRONG — name does not start with sam_metadata_ (fragment, local values defined elsewhere)
resource "null_resource" "lambda_meta" {
  triggers = {
    resource_name = "aws_lambda_function.publish_book_review" # example
    resource_type = "ZIP_LAMBDA_FUNCTION"
  }
}

# CORRECT
resource "null_resource" "sam_metadata_aws_lambda_function_publish_book_review" { # example name
  triggers = {
    resource_name = "aws_lambda_function.publish_book_review" # example
    resource_type = "ZIP_LAMBDA_FUNCTION"
  }
}
```

Source: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/terraform-sam-metadata.html
(the full trigger set is in [always-do-sam-cli §3](./always-do-sam-cli.md#3-the-sam-metadata-resource)).

## 4. Skip-prepare-infra after adding resources

`--skip-prepare-infra` "Skips the preparation stage if no infrastructure changes have been made"; use it only
when no new functions or API endpoints were added.

```bash
# WRONG — a new function or API endpoint was just added to the configuration
sam local start-api --hook-name terraform --skip-prepare-infra

# CORRECT — let the preparation stage run
sam local start-api --hook-name terraform
```

Sources: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-local-start-api.html ;
https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/gs-terraform-support.html

## 5. Referencing a function not yet created

The limitations page lists "referencing a Lambda function that is not yet created", including functions defined in
the `body` attribute of the REST API resource. Mitigation stated: run `terraform apply` when a new resource is added.

```bash
# WRONG — new aws_lambda_function added to the configuration and referenced by the API,
# but never applied
sam local start-api --hook-name terraform

# CORRECT
terraform apply
sam local start-api --hook-name terraform
```

Source: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/using-samcli-terraform.html
