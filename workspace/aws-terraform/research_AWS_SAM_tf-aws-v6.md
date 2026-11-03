# Research — AWS SAM with Terraform 1.16.x + hashicorp/aws 6.x

> Research date: **2026-10-23**. Status: **COMPLETE** (unit `sam`, scope approved by the user: "SAM com
> Terraform"; flat fan-out, no sub-agents).
> SAM is **not** a hashicorp/aws resource. It is the AWS Serverless Application Model: a CloudFormation
> transform (`AWS::Serverless-2016-10-31`) plus the SAM CLI [1][9]. This unit covers exactly how the two
> meet: (a) the SAM CLI Terraform hook, (b) the provider resources that deploy SAM/SAR content through
> CloudFormation, (c) what the pages say about choosing between them, (d) the Security Hub controls.
> Every statement is tagged: **[P]** provider-page fact, **[A]** SAM/AWS-page fact, **[I]** inference
> (by this researcher, not on a page). Registry pages render JS-only (F12) — raw markdown on `main` is used.
> Coverage reference only (not a source): `workspace/terraform/research_AWS_SAM_aws-v6.x.md`
> (6.47.0, Terraform 1.7 — EOL). Claims from it found wrong are listed in §9.

## 1. Version Context

| Item | Value | Tag / Source |
|---|---|---|
| Terraform CLI | `required_version = "~> 1.16"`; 1.16.7 newest 1.16.x | F1, F19 |
| Terraform 1.17.0 | Stable, NOT the target | F2 |
| hashicorp/aws | latest 6.70.0 (2026-10-21); constraint `~> 6.69`; no 7.x | F3, F18 |
| Withdrawn | 6.57.0 — never pin | F4 |
| SAM CLI latest stable | **v1.170.0, 22 Oct 2026** (marked "Latest"); v1.169.0 13 Oct 2026; v1.168.0 10 Oct 2026; v1.167.0 6 Oct 2026; nightly `v1.170.0.dev202610230901` 23 Oct 2026 is a pre-release | [A] [3] |
| Last Terraform-related SAM CLI note | v1.166.2 (11 Sep 2026): "fix(terraform-hook): improve Makefile generation" — the five newest releases mention no Terraform change | [A] [3] |
| SAM CLI minimum Terraform | **Not stated.** Prerequisites say only "Install Terraform" (`terraform -version`) [A] [4]. For **Terraform Cloud** the guide says "We recommend that you use Terraform v1.6.0 or newer"; older versions must generate a local plan file [A] [4] | (unverified) for a hard minimum — U1 |
| Feature status | The pages carry **no preview/beta/deprecation label** for Terraform support; `--hook-name` is listed as a regular option with "Accepted values: `terraform`" [A] [5][6]. No 2026 status change stated on any page read | [A] [2][4][5]; GA status itself (unverified) — U2 |
| Identity-based import | needs Terraform ≥ 1.12.0 | F11 |

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.69" }
  }
}
```

Root modules use `~>`, reusable modules `>=` only (F6). S3 backend: `use_lockfile = true`;
`dynamodb_table` deprecated (F7). Regional resources accept optional `region` (F5); none of the in-scope
resources are in the F14 global list, and all three pages read document `region` [P] [10][11][12].

## 2. Provider 6.x changes for the in-scope resources

- **6.0.0 upgrade guide (F13, F17):** no mention of `aws_cloudformation_stack`, `aws_cloudformation_stack_set`
  or any `serverlessapplicationrepository` resource. The only CloudFormation item is
  `aws_cloudformation_stack_set_instance`: "`region` has been deprecated. Use `stack_set_instance_region`
  instead." [P] [14] (out of scope here, listed for completeness — L3).
- **CHANGELOG 6.48.0 → 6.70.0** [P] [15] (read in two chunks: 6.71.0-Unreleased → 6.55.0, then 6.54.0 → 6.40.0):
  - **6.52.0 (June 24, 2026)** — `aws_serverlessapplicationrepository_cloudformation_stack` (#46748):
    - NOTE: `NoEcho` parameter values are **now stored in Terraform state in plaintext** rather than as
      `****` — secure the state backend.
    - NOTE: existing resources whose state contains `****` for `NoEcho` parameters, or is missing
      default-matching `parameters` keys, need a **one-time manual state reconciliation** after upgrading.
    - Enhancement: `capabilities` changed from **Required to Optional/Computed**.
    - Bug fix: "change set: unexpected state 'FAILED', wanted target 'CREATE_COMPLETE'" on subsequent applies.
  - No `aws_cloudformation_stack` / `aws_cloudformation_stack_set` /
    `aws_serverlessapplicationrepository_application` entries in 6.48.0–6.70.0 [P] [15].
  - Chunk boundary note: the 6.55.0 section straddled the two reads; the second read started before 6.54.0
    — treated as fully covered (medium confidence — M1).

## 3. SAM CLI support for Terraform projects [A]

### 3.1 What it is (scope stated by AWS)
- "Use the AWS SAM CLI with your Terraform projects or Terraform Cloud to perform **local debugging and
  testing** of: AWS Lambda Event Functions and layers; Amazon API Gateway APIs." [A] [2]
- Supported commands listed on the support page: `sam local invoke`, `sam local start-api`,
  `sam local start-lambda` [A] [2]; the Terraform reference page additionally lists **`sam build`** [A] [7].
- Workflow AWS describes: **Write** (Terraform) → **Test and debug** (SAM CLI) → **Plan** → **Apply** —
  "continuing to use your Terraform workflows to manage your applications on AWS" [A] [2]. Provisioning
  stays with Terraform.
- **`sam deploy`, `sam sync`, `sam validate`: no `--hook-name` / Terraform option** on their command
  reference pages [A] [16][17][18]. `sam deploy` "deploys an application to the AWS Cloud using AWS
  CloudFormation" [A] [16]; `sam validate` "verifies whether an AWS SAM template file is valid" [A] [18].
  [I] Therefore SAM CLI cannot deploy, sync or validate a Terraform project; use `terraform plan/apply`
  and `terraform validate` (F9) instead. The brief's "`sam sync`/`sam deploy` with Terraform" is **not
  supported per the pages**.

### 3.2 Prerequisites [A] [4]
- SAM CLI installed/upgraded; Terraform installed; **Docker** for local testing.
- Only if Lambda artifacts are built **inside** the Terraform project: **Python 3.8 or newer**, **GNU Make**
  (SAM CLI generates `makefiles` with Python commands), build logic in a `null_resource`, and one
  **`sam metadata` resource per Lambda function or layer**. "No additional setup is required if you build
  your AWS Lambda artifacts outside of your Terraform project."
- `hook_name = "terraform"` can be set in the SAM CLI configuration file instead of passing `--hook-name`.

### 3.3 Options [A]
| Option | Commands | Page text |
|---|---|---|
| `--hook-name terraform` | build, local invoke, start-api, start-lambda | "The name of the hook that is used to extend AWS SAM CLI functionality. Accepted values: `terraform`." [5][6] |
| `--terraform-project-root-path` | build | "relative or absolute path to the top-level directory containing your Terraform configuration files or function source code" when outside the root-module directory; "requires that `--hook-name` be set to `terraform`" [5] |
| `--terraform-plan-file` | start-api (and local invoke per the guide example) | "path to your local Terraform plan file when using the AWS SAM CLI with Terraform Cloud"; requires `--hook-name terraform` [6][4] |
| `--skip-prepare-infra` | build, start-api | "Skips the preparation stage if no infrastructure changes have been made. Use with the `--hook-name` option." Use only when no new functions/API endpoints were added [5][6][4] |
| Incompatible with `--hook-name` (build) | `--build-in-source`, `--parameter-overrides`, `--template-file` | [5] |

- `sam build --hook-name terraform [lambda-resource-id]` — the ID can be the function name or full address,
  e.g. `aws_lambda_function.list_books` or `module.list_book_function.aws_lambda_function.this[0]`; run
  from the directory containing the root module; creates `.aws-sam` [A] [4].
- Container builds: custom image with Terraform + Python + Make, then
  `sam build --use-container --build-image <tag>` [A] [4].
- The prepare hook runs `terraform init`, creates a plan JSON and generates a metadata file; output may
  report "Unresolvable attributes discovered in project, run terraform apply to resolve them." [A] [8]

### 3.4 `sam metadata` resource [A] [4][19]
- A `null_resource` (hashicorp/null) whose name **starts with `sam_metadata_`**; properties in `triggers`;
  `depends_on` the build `null_resource`.
- Fields: `resource_name` (e.g. `"aws_lambda_function.function_example"`), `resource_type`
  (**`ZIP_LAMBDA_FUNCTION` | `IMAGE_LAMBDA_FUNCTION` | `LAMBDA_LAYER`**), `original_source_code` (string,
  string array — only first value used — or JSON with `source_code_property`), `built_output_path`,
  `docker_context`, `docker_file` (default `Dockerfile`), `docker_build_args`, `docker_tag`.
- Resource types shown in examples: `aws_lambda_function`, `aws_lambda_layer_version` [A] [19]; API Gateway
  authorizers via `aws_api_gateway_authorizer` (Lambda authorizer auto-invoked by start-api) [A] [8];
  Terraform Cloud sample `api_gateway_v2_tf_cloud` [A] [4]. A complete list of supported Terraform API
  Gateway v1/v2 resource types is **not stated** (unverified — U3).

### 3.5 Limitations (stated) [A] [8]
- Lambda functions linked to **multiple layers**.
- Terraform **local variables** that define links between resources.
- Referencing a Lambda function **not yet created**, including functions defined in the `body` attribute of
  the REST API resource. Mitigation stated: "run `terraform apply` when a new resource is added."
- Environment/runner may inject additional logs into command output [A] [2].

```hcl
# [A] pattern from [4][19]: build logic + sam metadata for one ZIP function
resource "null_resource" "sam_metadata_aws_lambda_function_publish_book_review" {
  triggers = {
    resource_name        = "aws_lambda_function.publish_book_review"
    resource_type        = "ZIP_LAMBDA_FUNCTION"
    original_source_code = local.lambda_src_path
    built_output_path    = "${local.building_path}/${local.lambda_code_filename}"
  }
  depends_on = [null_resource.build_lambda_function]
}
```

## 4. `aws_serverlessapplicationrepository_cloudformation_stack` [P] [10]

| Argument | Req. | Notes |
|---|---|---|
| `application_id` | Required | ARN of the SAR application |
| `name` | Required | Stack name; AWS **prefixes** the deployed stack with `serverlessrepo-` |
| `capabilities` | Optional (Optional/Computed since 6.52.0 [15]) | IAM, named IAM, resource policy, auto-expand acknowledgements, needed when the app creates those resource types |
| `parameters` | Optional | map of input parameters |
| `semantic_version` | Optional | **defaults to latest** |
| `region` | Optional | F5 |
| `tags` | Optional | overrides `default_tags` on matching keys |

- Attributes: `id`, `outputs` (map), `tags_all`. Timeouts: create/update/delete **30m**.
- **Security note on page:** CloudFormation hides `NoEcho` values in API responses, but **Terraform still
  stores them in state**; wrap with `sensitive()` to mask them in plan/`terraform show` [P] [10]
  (plus the 6.52.0 plaintext-in-state note [P] [15]).
- **Import:** `import` block (Terraform ≥ 1.5.0) or `terraform import`, ID = stack **name with or without
  the `serverlessrepo-` prefix**, or the stack ID [P] [10].
- [I] Pin `semantic_version` explicitly; omitting it means "latest" at apply time, which is a
  non-reproducible input.

## 5. Data source `aws_serverlessapplicationrepository_application` [P] [11]
- Args: `application_id` (Required, ARN), `semantic_version` (Optional, default latest), `region` (Optional).
- Attributes: `application_id`, `name`, `required_capabilities`, `source_code_url`, `template_url`.
- Page purpose: "useful for finding the capabilities an application requires"; the example feeds
  `application_id`, `semantic_version`, `required_capabilities` into the stack resource [P] [11].

## 6. `aws_cloudformation_stack` with a SAM template [P] [12] + [A] [9][20]

| Argument | Notes |
|---|---|
| `name` | Required |
| `template_body` | inline, up to **51,200 bytes** |
| `template_url` | file location, up to **460,800 bytes** [P]; API allows S3 or SSM document, max 1 MB [A] [20] (provider limit is stricter — use the provider value) |
| `capabilities` | `CAPABILITY_IAM`, `CAPABILITY_NAMED_IAM`, `CAPABILITY_AUTO_EXPAND` |
| `on_failure` | `DO_NOTHING` / `ROLLBACK` / `DELETE`; conflicts with `disable_rollback` |
| `disable_rollback` | conflicts with `on_failure` |
| `iam_role_arn` | role CloudFormation assumes; if omitted uses previous stack role, else temporary session from your credentials |
| `parameters`, `notification_arns`, `timeout_in_minutes`, `policy_body`/`policy_url` (conflict), `tags`, `region` | as named |

- Attributes: `id`, `outputs`, `tags_all`. Timeouts create/update/delete **30m**. Import: stack **`name`**
  (import block ≥ 1.5.0 or CLI). The page has **no separate NOTE/WARNING section** [P] [12].
- **No `enable_termination_protection` argument** appears on the page as read (medium confidence — M2;
  page was returned summarised). [I] If confirmed, Security Hub CloudFormation.3 cannot be satisfied from
  this resource alone.
- **SAM transform facts [A] [9]:** declare at template top level; value must be the literal
  `AWS::Serverless-2016-10-31` (no parameter/function); "When creating a change set from the template,
  CloudFormation expands the AWS SAM syntax." **CloudFormation, not Terraform, runs the transform.**
- **`CAPABILITY_AUTO_EXPAND` [A] [20]:** required when a template with macros is created directly
  "without first reviewing the resulting changes in a change set" — "This includes the AWS::Include and
  AWS::Serverless transforms". Templates with macros *and* nested stacks must use it. AWS warns each macro
  relies on a Lambda function whose owner "can update the function operation without CloudFormation being
  notified." [I] A SAM template in `template_body` therefore needs `CAPABILITY_AUTO_EXPAND` (plus
  `CAPABILITY_IAM`/`CAPABILITY_NAMED_IAM` when SAM generates IAM roles, as the transform example shows an
  `AWS::IAM::Role` being generated [A] [9]); whether the provider uses change sets for this resource is
  not stated (U4).
- [I] `CodeUri` in the SAM template must point to already-uploaded S3 artifacts (example uses
  `s3://…/MySourceCode.zip` [A] [9]); Terraform does not run `sam package`.
- **Drift / "do not mix with CLI-deployed stacks":** the provider page states **nothing** about drift
  detection inside the stack or about mixing with `sam deploy`-managed stacks (unverified — U5, U6). Do
  not repeat the legacy claim as fact.

## 7. `aws_cloudformation_stack_set` [P] [13]
- `permission_model` `SELF_MANAGED` (default) | `SERVICE_MANAGED`; `auto_deployment` only with
  `SERVICE_MANAGED`; `administration_role_arn` must be set for `SELF_MANAGED`; `execution_role_name`
  defaults to `AWSCloudFormationStackSetExecutionRole` (SELF_MANAGED), must not be set for SERVICE_MANAGED.
- `capabilities` `CAPABILITY_IAM` | `CAPABILITY_NAMED_IAM` | `CAPABILITY_AUTO_EXPAND`; `template_body`
  (51,200 B) XOR `template_url` (S3, 460,800 B); `call_as` `SELF` | `DELEGATED_ADMIN`;
  `operation_preferences`; `managed_execution.active` (default false).
- **NOTEs (perpetual-diff guards):** all template parameters, including those with a `Default`, must be
  configured or ignored via `lifecycle { ignore_changes }`; "All `NoEcho` template parameters must be
  ignored with the `lifecycle` configuration block `ignore_changes` argument." Delegated admin needs
  `organizations:ListDelegatedAdministrators`.
- Timeouts: `update` 30m. Import: `name`, or `name,DELEGATED_ADMIN` for delegated administrators.
- Whether StackSets accept the `AWS::Serverless` transform is not stated on the provider page (U7).

## 8. Choosing SAM vs Terraform; AWS guidance; Security Hub

### 8.1 What the pages say [A]
- SAM is "an ideal IaC solution for scenarios where you want simplified serverless development with the
  full power of CloudFormation"; comparisons given are SAM vs CloudFormation and SAM vs/with AWS CDK
  [A] [1]. **No page read compares SAM with Terraform** for provisioning (U8).
- For Terraform users AWS positions SAM CLI as the **local debug/test** tool alongside Terraform
  ("Manage your Terraform serverless applications … perform local debugging and testing") [A] [1][2].
- [I] Decision guide derived from the facts above (not an AWS recommendation):
  Terraform-native (`aws_lambda_*`, `aws_apigateway*`) + SAM CLI hook for local testing → when Terraform
  owns provisioning; `aws_serverlessapplicationrepository_cloudformation_stack` → consuming a published SAR
  app; `aws_cloudformation_stack` with the SAM transform → reusing an existing SAM template under Terraform
  orchestration (CloudFormation executes the transform). Lambda/API Gateway resource details belong to the
  Lambda and API-Gateway units (L1).

### 8.2 Security Hub CSPM — CloudFormation controls [A] [21]
| ID | Title | Severity | Note |
|---|---|---|---|
| CloudFormation.1 | Stacks should be integrated with SNS | Low | **Retired April 2024** — do not target |
| CloudFormation.2 | Stacks should be tagged (`requiredTagKeys`, up to 6) | Low | `tags` on the stack resources; system `aws:` tags ignored |
| CloudFormation.3 | Stacks should have termination protection enabled | Medium | Nested stacks inherit from root (see M2) |
| CloudFormation.4 | Stacks should have associated service roles | Medium | → `iam_role_arn`; FAILED for stacks created by service-managed StackSets; role cannot be removed after creation and can be used by anyone able to operate on the stack — least privilege |

- [I] The SAR stack resource exposes no role argument [P] [10], so stacks it creates are expected to fail
  CloudFormation.4 (unverified — U9). No Security Hub controls page for Serverless Application Repository
  was consulted/found (L2).
- [A] RoleARN: "CloudFormation always uses this role for all future operations on the stack … Ensure that
  the role grants least privilege." [20]

## 9. Unverified, medium-confidence, coverage limits; legacy errors

- **U1** Hard minimum Terraform version for the SAM CLI hook (only a v1.6.0 recommendation for TF Cloud).
- **U2** Formal GA status of SAM CLI Terraform support (no label either way on current pages).
- **U3** Exhaustive list of supported API Gateway v1/v2 Terraform resource types.
- **U4** Whether the provider creates stacks via change sets (affects need for `CAPABILITY_AUTO_EXPAND`).
- **U5** Drift detection behaviour of `aws_cloudformation_stack` for resources inside the stack.
- **U6** Any "do not mix with SAM-CLI-deployed stacks" warning — not on the provider page.
- **U7** SAM transform support in StackSets.
- **U8** Any AWS page comparing SAM and Terraform for provisioning.
- **U9** CloudFormation.4 outcome for SAR-created stacks.
- **M1** CHANGELOG 6.55.0 section straddled two fetch chunks.
- **M2** Absence of a termination-protection argument on `aws_cloudformation_stack` (page summarised).
- **L1** Lambda/API Gateway resource arguments are out of scope (see Lambda and API-Gateway research files).
- **L2** No Serverless Application Repository Security Hub page reviewed.
- **L3** `aws_cloudformation_stack_set_instance` (6.0 `region` → `stack_set_instance_region`) not covered.

**Legacy-file claims found wrong or unsupported** (`workspace/terraform/research_AWS_SAM_aws-v6.x.md`):
1. `required_version = ">= 1.7"` / `version = "~> 6.0"` — superseded by F1/F3/F6.
2. S3 backend with `dynamodb_table` — deprecated (F7).
3. Treats SAR `capabilities` as mandatory input — Optional/Computed since 6.52.0 [15].
4. Omits that `NoEcho` parameters are stored in state (plaintext since 6.52.0) [10][15].
5. Says the SAR resource deploys "as a CloudFormation nested stack" — page says it deploys a
   CloudFormation stack prefixed `serverlessrepo-` [10]; "nested" unverified.
6. "Terraform cannot detect drift inside CF stack" — not stated on any page read (U5).
7. Completely omits the SAM CLI Terraform hook (`--hook-name terraform`, `sam metadata`), the core of
   this unit.

## 10. Security note
None observed: no instruction-like / prompt-injection text in fetched pages. The SAM support page's own
note that runners "may inject additional logs" refers to command output, not to prompt injection [2].

## Source Bibliography
All read 2026-10-23.
1. https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html
2. https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/terraform-support.html
3. https://github.com/aws/aws-sam-cli/releases
4. https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/gs-terraform-support.html
5. https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-build.html
6. https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-local-start-api.html
7. https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/terraform-reference.html
8. https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/using-samcli-terraform.html
9. https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/transform-aws-serverless.html
10. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/serverlessapplicationrepository_cloudformation_stack.html.markdown
11. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/serverlessapplicationrepository_application.html.markdown
12. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudformation_stack.html.markdown
13. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudformation_stack_set.html.markdown
14. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
15. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
16. https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-deploy.html
17. https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-sync.html
18. https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-validate.html
19. https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/terraform-sam-metadata.html
20. https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_CreateStack.html
21. https://docs.aws.amazon.com/securityhub/latest/userguide/cloudformation-controls.html
