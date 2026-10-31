# Always-Do — SAM CLI with Terraform projects

SAM CLI v1.170.0 (2026-10-22) · Sources read 2026-10-23. This section is not a hashicorp/aws resource: Terraform
still does plan and apply; the SAM CLI only does local debugging and testing
(https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/terraform-support.html).

## 2. Local build and test with the Terraform hook

Supported commands: `sam build`, `sam local invoke`, `sam local start-api`, `sam local start-lambda`
(https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/terraform-reference.html).
Prerequisites: SAM CLI, Terraform and Docker for local testing; building Lambda artifacts inside the Terraform
project also needs Python 3.8 or newer and GNU Make
(https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/gs-terraform-support.html).

```bash
# Fragment: run from the directory containing the root module. Function IDs are examples.
sam build --hook-name terraform                                        # all functions
sam build --hook-name terraform aws_lambda_function.list_books         # example resource ID
sam local start-api --hook-name terraform
sam local start-lambda --hook-name terraform
sam local invoke --hook-name terraform                                 # function ID argument omitted
```

- `sam build` accepts the function name or full address as the ID, e.g.
  `module.list_book_function.aws_lambda_function.this[0]`, and creates `.aws-sam`
  (https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/gs-terraform-support.html).
- `hook_name = "terraform"` can be set in the SAM CLI configuration file instead of passing `--hook-name`
  (same page).
- `--terraform-project-root-path` (build): path to the top-level directory with the Terraform configuration or
  function source when it is outside the root-module directory; requires `--hook-name terraform`
  (https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-build.html).
- Terraform Cloud: `--terraform-plan-file` points to a local plan file and requires `--hook-name terraform`
  (https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-local-start-api.html).
  For Terraform Cloud the guide recommends Terraform v1.6.0 or newer; older versions must generate a local plan file.
- Container builds: build a custom image with Terraform, Python and Make, then
  `sam build --use-container --build-image <tag>` (gs-terraform-support page above).
- Stated limitations: Lambda functions linked to multiple layers; Terraform local variables that define links
  between resources; referencing a Lambda function not yet created, including functions defined in the `body`
  of the REST API resource — run `terraform apply` when a new resource is added
  (https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/using-samcli-terraform.html).

## 3. The sam metadata resource

A `sam metadata` resource is a `null_resource` (hashicorp/null) whose name starts with `sam_metadata_`, with
its properties in `triggers` and a `depends_on` on the build `null_resource`. Types: `ZIP_LAMBDA_FUNCTION`,
`IMAGE_LAMBDA_FUNCTION`, `LAMBDA_LAYER`. Other trigger fields: `original_source_code`, `built_output_path`,
`docker_context`, `docker_file` (default `Dockerfile`), `docker_build_args`, `docker_tag`
(https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/terraform-sam-metadata.html).

```hcl
# Fragment: references local.lambda_src_path, local.building_path, local.lambda_code_filename and
# null_resource.build_lambda_function, which are defined elsewhere. Names are examples.
resource "null_resource" "sam_metadata_aws_lambda_function_publish_book_review" { # example name
  triggers = {
    resource_name        = "aws_lambda_function.publish_book_review" # example
    resource_type        = "ZIP_LAMBDA_FUNCTION"
    original_source_code = local.lambda_src_path
    built_output_path    = "${local.building_path}/${local.lambda_code_filename}"
  }

  depends_on = [null_resource.build_lambda_function]
}
```

Source: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/gs-terraform-support.html and
the `sam metadata` page above. The hook runs `terraform init`, creates a plan JSON and generates a metadata
file; output may report "Unresolvable attributes discovered in project, run terraform apply to resolve them."
(using-samcli-terraform page above).
