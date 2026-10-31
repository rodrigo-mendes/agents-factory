---
name: provisioning-aws-sam-v6
description: "SAM with Terraform (aws 6.x): SAM CLI with Terraform projects, SAR, CloudFormation-deployed SAM transform; not a provider resource. Use when mixing SAM and Terraform. Not for plain Lambda, API Gateway."
---

# Provisioning AWS SAM with Terraform — hashicorp/aws 6.x

> Version lock: `-v6` = the **hashicorp/aws 6.x** major line (reference patch 6.69.0 / 6.70.0) +
> **Terraform ~> 1.16** only. Sources read **2026-10-23** unless a row says otherwise. Claims tagged
> (unverified) or (medium confidence) were not fully confirmed against an official page.

**SAM is not a hashicorp/aws resource.** It is the AWS Serverless Application Model: a CloudFormation
transform (`AWS::Serverless-2016-10-31`) plus the SAM CLI
([source](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html)).
This skill covers the two places where SAM and Terraform meet:

- **(a) SAM CLI with Terraform projects** — `sam build`, `sam local invoke`, `sam local start-api`,
  `sam local start-lambda` with `--hook-name terraform`, for **local debugging and testing only**. Terraform
  still does plan and apply.
- **(b) Provider resources that deploy SAM or SAR content through CloudFormation** —
  `aws_serverlessapplicationrepository_cloudformation_stack` (+ data source) and `aws_cloudformation_stack` /
  `aws_cloudformation_stack_set` with the SAM transform. CloudFormation runs the transform, not Terraform.

## Version Context

| Item | Value | Source |
|---|---|---|
| Terraform CLI | `~> 1.16`; newest 1.16.x is **1.16.7** (released 2026-10-22) | https://releases.hashicorp.com/terraform/ |
| hashicorp/aws | latest **6.70.0** (2026-10-23); this skill uses `~> 6.69`; no 7.x release | https://releases.hashicorp.com/terraform-provider-aws/ |
| 6.57.0 | **Withdrawn** — never pin | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md |
| SAM CLI | latest stable **v1.170.0** (2026-10-22) | https://github.com/aws/aws-sam-cli/releases |
| Last Terraform-related SAM CLI note | v1.166.2 (2026-09-11): "fix(terraform-hook): improve Makefile generation"; the five newest releases list no Terraform change (medium confidence, absence of evidence) | https://github.com/aws/aws-sam-cli/releases |
| Minimum Terraform for the SAM CLI hook | **Not stated** (medium confidence, absence of evidence); only a recommendation of v1.6.0 or newer for Terraform Cloud | https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/gs-terraform-support.html |
| Hook status label | No preview/beta/deprecation label on the pages read; no 2026 status change stated (medium confidence, absence of evidence) | https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/terraform-support.html |
| Provider constraint | `~> 6.69` (root modules); `>=` minimum only in reusable modules | https://developer.hashicorp.com/terraform/language/expressions/version-constraints |

**Version-lifetime risk** (details in [unverified-and-risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)):
- Terraform 1.17.0 is stable (2026-10-21) and is not the target of this skill; re-verify when starting new work.
- 6.57.0 is withdrawn; a constraint that resolves to it breaks installs.
- v7 is planned (the 6.0 upgrade guide says "`s3_us_east_1_regional_endpoint` will be removed in `v7.0.0`",
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown);
  no 7.x release exists (https://releases.hashicorp.com/terraform-provider-aws/, 2026-10-23).
  A new major is a new skill.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [5.x → 6.x Migration (SAM)](#5x--6x-migration-sam)
- Foundation: [terraform block + backend](./blueprints/always-do-foundation.md)
- SAM CLI patterns: [local build/test, `sam metadata`](./blueprints/always-do-sam-cli.md)
- CloudFormation patterns: [SAR stack, SAM template stack, stack set](./blueprints/always-do-cloudformation.md)
- Never-do SAM CLI: [flags, metadata names, limitations](./blueprints/never-do-sam-cli.md)
- Never-do CloudFormation: [NoEcho, rollback args, template size](./blueprints/never-do-cloudformation.md)
- Never-do provider/migration: [withdrawn version, deprecated backend](./blueprints/never-do-provider-migration.md)
- [Unverified claims and risks](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Constrain providers in root modules with `~>`** (this skill's targets are `~> 1.16` for Terraform and `~> 6.69` for the provider).
  See [foundation §1](./blueprints/always-do-foundation.md#1-terraform-block-and-s3-backend).
  https://developer.hashicorp.com/terraform/language/expressions/version-constraints
- **Use `use_lockfile = true` on the S3 backend** — `dynamodb_table` is deprecated.
  See [foundation §1](./blueprints/always-do-foundation.md#1-terraform-block-and-s3-backend).
  https://developer.hashicorp.com/terraform/language/backend/s3
- **Use the SAM CLI with a Terraform project for local debugging and testing only** — AWS describes the
  workflow as write, test and debug, plan, apply, with Terraform managing the application.
  See [sam-cli §2](./blueprints/always-do-sam-cli.md#2-local-build-and-test-with-the-terraform-hook).
  https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/terraform-support.html
- **Pass `--hook-name terraform` to `sam local invoke`, `sam local start-api` and `sam local start-lambda`.**
  See [sam-cli §2](./blueprints/always-do-sam-cli.md#2-local-build-and-test-with-the-terraform-hook).
  https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/terraform-support.html
- **Pass `--hook-name terraform` to `sam build`** — accepted value is `terraform`.
  See [sam-cli §2](./blueprints/always-do-sam-cli.md#2-local-build-and-test-with-the-terraform-hook).
  https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-build.html
- **Have Docker installed for local testing.**
  See [sam-cli §2](./blueprints/always-do-sam-cli.md#2-local-build-and-test-with-the-terraform-hook).
  https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/gs-terraform-support.html
- **Add one `sam metadata` resource per Lambda function or layer** when the artifacts are built inside the Terraform project.
  See [sam-cli §3](./blueprints/always-do-sam-cli.md#3-the-sam-metadata-resource).
  https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/gs-terraform-support.html
- **Make the `sam metadata` resource a `null_resource` whose name starts with `sam_metadata_`**, with its properties in `triggers`.
  See [sam-cli §3](./blueprints/always-do-sam-cli.md#3-the-sam-metadata-resource).
  https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/terraform-sam-metadata.html
- **Set `resource_type` to `ZIP_LAMBDA_FUNCTION`, `IMAGE_LAMBDA_FUNCTION` or `LAMBDA_LAYER`.**
  See [sam-cli §3](./blueprints/always-do-sam-cli.md#3-the-sam-metadata-resource).
  https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/terraform-sam-metadata.html
- **Wrap SAR stack parameters that map to `NoEcho` template parameters in `sensitive()`** — CloudFormation hides them in API responses but Terraform still stores them in state.
  See [cloudformation §4](./blueprints/always-do-cloudformation.md#4-serverless-application-repository-stack).
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/serverlessapplicationrepository_cloudformation_stack.html.markdown
- **Secure the state backend for SAR stacks** — since 6.52.0 `NoEcho` parameter values are stored in state in plaintext.
  See [cloudformation §4](./blueprints/always-do-cloudformation.md#4-serverless-application-repository-stack).
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
- **Use the `required_capabilities` attribute of `aws_serverlessapplicationrepository_application` to find the capabilities an application requires.**
  See [cloudformation §4](./blueprints/always-do-cloudformation.md#4-serverless-application-repository-stack).
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/serverlessapplicationrepository_application.html.markdown
- **Declare the transform at the template top level with the literal value `AWS::Serverless-2016-10-31`.**
  See [cloudformation §5](./blueprints/always-do-cloudformation.md#5-cloudformation-stack-with-a-sam-template).
  https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/transform-aws-serverless.html
- **Remember that CloudFormation, not Terraform, expands the SAM syntax** when it creates the change set.
  See [cloudformation §5](./blueprints/always-do-cloudformation.md#5-cloudformation-stack-with-a-sam-template).
  https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/transform-aws-serverless.html
- **Know when AWS requires `CAPABILITY_AUTO_EXPAND`:** the CreateStack page says it is required when a template that uses a macro, including the `AWS::Serverless` transform, is created without first reviewing the resulting changes in a change set.
  See [cloudformation §5](./blueprints/always-do-cloudformation.md#5-cloudformation-stack-with-a-sam-template).
  https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_CreateStack.html
- **Give `iam_role_arn` a role with least privilege** — CloudFormation always uses that role for all future operations on the stack.
  See [cloudformation §5](./blueprints/always-do-cloudformation.md#5-cloudformation-stack-with-a-sam-template).
  https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_CreateStack.html
- **Use `template_url` (up to 460,800 bytes) when the template exceeds the 51,200-byte `template_body` limit.**
  See [cloudformation §5](./blueprints/always-do-cloudformation.md#5-cloudformation-stack-with-a-sam-template).
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudformation_stack.html.markdown
- **Configure every stack set template parameter, including those with a `Default`, or ignore it with `lifecycle { ignore_changes }`.**
  See [cloudformation §6](./blueprints/always-do-cloudformation.md#6-cloudformation-stack-set).
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudformation_stack_set.html.markdown

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| SAM vs Terraform for provisioning (unverified) | The AWS pages read compare SAM with CloudFormation and CDK, not with Terraform; AWS positions the SAM CLI as the local debug/test tool alongside Terraform ([what-is-sam](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html), [terraform-support](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/terraform-support.html)). | "Does Terraform own provisioning (SAM CLI only for local testing), or is a SAM template being reused?" |
| Which resource carries SAM content (unverified, inference) | Inference, not an AWS recommendation: `aws_serverlessapplicationrepository_cloudformation_stack` to consume a published SAR application; `aws_cloudformation_stack` to reuse an existing SAM template under Terraform; Lambda/API Gateway resources for Terraform-native work. | "Is this a published SAR app, an existing SAM template, or new Terraform-native code?" |
| Minimum Terraform version for the SAM CLI hook (unverified) | No hard minimum is stated; for Terraform Cloud the guide recommends v1.6.0 or newer and older versions must generate a local plan file. | "Which Terraform version and runner (local or Terraform Cloud) will the SAM CLI use?" |
| Hook status (medium confidence, absence of evidence) | The pages carry no preview or GA label either way and no 2026 status change is stated. | "Is a formally GA feature required for this project?" |
| `sam deploy`, `sam sync`, `sam validate` with a Terraform project (medium confidence, absence of evidence) | Their reference pages show no `--hook-name` or Terraform option; Terraform still provides `terraform plan`, `apply` and `validate`. | "Is someone expecting SAM CLI to deploy this Terraform project?" |
| Capabilities for a SAM template in `aws_cloudformation_stack` (unverified, inference) | Whether the provider creates stacks through a reviewed change set is not stated, so whether `CAPABILITY_AUTO_EXPAND` is needed on this resource is open; the transform example shows an `AWS::IAM::Role` being generated, which may call for `CAPABILITY_IAM` or `CAPABILITY_NAMED_IAM`. | "Is the stack created without a reviewed change set? Does the SAM template create IAM roles? Confirm the `capabilities` list." |
| Pin `semantic_version` on the SAR stack (unverified, inference) | The page says it defaults to latest; an explicit pin avoids a changing input at apply time. | "Which application version should be pinned?" |
| `CodeUri` artifacts (unverified, inference) | The transform example points to an uploaded S3 object; nothing read says Terraform runs `sam package`. | "Where are the SAM artifacts uploaded before `terraform apply`?" |
| Drift detection and mixing with `sam deploy` stacks (unverified) | The `aws_cloudformation_stack` page says nothing about drift inside the stack or about stacks deployed by `sam deploy`. | "Will the same stack also be touched by the SAM CLI or the console?" |
| SAM transform in stack sets (unverified) | The `aws_cloudformation_stack_set` page does not say whether the transform is accepted. | "Is a SAM template going into a stack set? Test it first." |
| API Gateway resource types supported by the hook (unverified) | Examples show `aws_api_gateway_authorizer` and a Terraform Cloud sample `api_gateway_v2_tf_cloud`; no exhaustive list is stated. | "Which API Gateway resource types must work with `sam local start-api`?" |
| Security Hub CloudFormation.3 termination protection (medium confidence, absence of evidence) | The `aws_cloudformation_stack` page as read has no termination-protection argument, so this resource alone may not satisfy it. | "Is CloudFormation.3 in scope? Confirm how termination protection will be set." |
| Security Hub CloudFormation.4 for SAR stacks (unverified) | The SAR stack page shows no role argument, so stacks created by it are expected to fail the control. | "Is CloudFormation.4 enforced for stacks created through SAR?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Combine `sam build --hook-name` with `--build-in-source`, `--parameter-overrides` or `--template-file` — the page lists them as incompatible. ([source](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-build.html)) | Run `sam build --hook-name terraform` without those flags |
| Use `--terraform-project-root-path` or `--terraform-plan-file` without `--hook-name terraform` — both require it. ([build](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-build.html), [start-api](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-local-start-api.html), [getting started](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/gs-terraform-support.html)) | Add `--hook-name terraform` to the same command |
| Name the `sam metadata` `null_resource` without the `sam_metadata_` prefix. ([source](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/terraform-sam-metadata.html)) | Start the resource name with `sam_metadata_` |
| Use `--skip-prepare-infra` after adding new functions or API endpoints — it skips the preparation stage. ([source](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-local-start-api.html)) | Omit `--skip-prepare-infra` so the preparation stage runs |
| Reference a Lambda function that is not yet created, including one defined in the `body` of the REST API resource — the page lists it as a limitation. ([source](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/using-samcli-terraform.html)) | Run `terraform apply` when a new resource is added |
| Assume `NoEcho` values of an SAR stack are masked in state — Terraform stores them, in plaintext since 6.52.0. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md)) | Wrap values in `sensitive()` and secure the state backend |
| Leave `NoEcho` template parameters of a stack set unignored — the page says all of them must be ignored. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudformation_stack_set.html.markdown)) | Ignore them with the `lifecycle` block `ignore_changes` argument |
| Set `on_failure` and `disable_rollback` together on `aws_cloudformation_stack` — they conflict. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudformation_stack.html.markdown)) | Set only one of them |
| Inline a template larger than 51,200 bytes in `template_body`. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudformation_stack.html.markdown)) | Use `template_url` (up to 460,800 bytes) |
| Pin `version = "6.57.0"` — withdrawn from GitHub and the Registry. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md)) | `~> 6.69` or any non-withdrawn patch |
| Configure the S3 backend with `dynamodb_table` — deprecated. ([source](https://developer.hashicorp.com/terraform/language/backend/s3)) | `use_lockfile = true` |

## Quick Reference

Sources read 2026-10-23.

| Aspect | Value | Source |
|---|---|---|
| SAM CLI commands with Terraform | `sam build`, `sam local invoke`, `sam local start-api`, `sam local start-lambda` | https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/terraform-reference.html |
| Hook option | `--hook-name terraform` ("Accepted values: `terraform`"); `hook_name = "terraform"` can go in the SAM CLI configuration file | https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/gs-terraform-support.html |
| `sam build` extra option | `--terraform-project-root-path` (path to the Terraform configuration or function source when outside the root-module directory) | https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-build.html |
| Terraform Cloud option | `--terraform-plan-file` (requires `--hook-name terraform`) | https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-local-start-api.html |
| Build-inside prerequisites | Python 3.8 or newer, GNU Make, build logic in a `null_resource`, one `sam metadata` resource per function or layer | https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/gs-terraform-support.html |
| Stated limitations | Lambda functions with multiple layers; Terraform local variables that define links between resources; functions not yet created | https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/using-samcli-terraform.html |
| SAR stack | `application_id` and `name` required; AWS prefixes the stack with `serverlessrepo-`; `semantic_version` defaults to latest; timeouts 30m | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/serverlessapplicationrepository_cloudformation_stack.html.markdown |
| SAR `capabilities` | Optional/Computed since 6.52.0 (was Required) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md |
| `aws_cloudformation_stack` | `template_body` up to 51,200 bytes; `template_url` up to 460,800 bytes; `capabilities` `CAPABILITY_IAM` / `CAPABILITY_NAMED_IAM` / `CAPABILITY_AUTO_EXPAND` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudformation_stack.html.markdown |
| Stack set | `permission_model` `SELF_MANAGED` (default) or `SERVICE_MANAGED`; import `name`, or `name,DELEGATED_ADMIN` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudformation_stack_set.html.markdown |
| Security Hub CloudFormation.1 | Stacks should be integrated with SNS — low severity; retired April 2024 | https://docs.aws.amazon.com/securityhub/latest/userguide/cloudformation-controls.html |
| Security Hub CloudFormation.2 | Stacks should be tagged — low severity | https://docs.aws.amazon.com/securityhub/latest/userguide/cloudformation-controls.html |
| Security Hub CloudFormation.3 | Stacks should have termination protection enabled — medium severity | https://docs.aws.amazon.com/securityhub/latest/userguide/cloudformation-controls.html |
| Security Hub CloudFormation.4 | Stacks should have associated service roles — medium severity (`iam_role_arn`) | https://docs.aws.amazon.com/securityhub/latest/userguide/cloudformation-controls.html |

## 5.x → 6.x Migration (SAM)

Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown (2026-10-23).

- The 6.0 upgrade guide does not mention `aws_cloudformation_stack`, `aws_cloudformation_stack_set` or any
  `serverlessapplicationrepository` resource. Its only CloudFormation item is `aws_cloudformation_stack_set_instance`
  ("`region` has been deprecated. Use `stack_set_instance_region` instead."), which this skill does not cover.
- 6.52.0 (2026-06-24) SAR stack entries in the
  [CHANGELOG](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md):
  `NoEcho` values are now stored in state in plaintext; existing resources whose state holds `****` for `NoEcho`
  parameters, or lacks default-matching `parameters` keys, need a one-time manual state reconciliation after
  upgrading; `capabilities` changed from Required to Optional/Computed; a change-set error ("unexpected state
  'FAILED', wanted target 'CREATE_COMPLETE'") on subsequent applies was fixed.
- No `aws_cloudformation_stack`, `aws_cloudformation_stack_set` or `aws_serverlessapplicationrepository_application`
  entries appear in 6.48.0–6.70.0 (medium confidence, absence of evidence; the 6.55.0 section was only partly covered).
- Upgrade path (exact wording of the guide): "Before upgrading to version `6.0.0`, first upgrade to the latest
  available `5.x` version of the provider." Then get a plan that completes "without errors or unexpected changes",
  "update [version constraints] to allow the `6.x` series", and run `terraform init -upgrade` "to download the new
  version". This skill uses `~> 6.69`.
- v7 is planned; no 7.x release exists (guide above and https://releases.hashicorp.com/terraform-provider-aws/).

## External Resources

All read 2026-10-23.

- SAM CLI with Terraform: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/terraform-support.html
- Getting started: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/gs-terraform-support.html
- Terraform reference: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/terraform-reference.html
- `sam metadata` resource: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/terraform-sam-metadata.html
- SAM transform: https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/transform-aws-serverless.html
- CreateStack API: https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_CreateStack.html
- Security Hub CloudFormation controls: https://docs.aws.amazon.com/securityhub/latest/userguide/cloudformation-controls.html
- Provider CHANGELOG: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
- SAM CLI releases: https://github.com/aws/aws-sam-cli/releases
- Full bibliography: [unverified-and-risks](./blueprints/unverified-and-risks.md#source-bibliography)
