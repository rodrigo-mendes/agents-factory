# Unverified Claims and Risks — AWS SAM with Terraform (hashicorp/aws 6.x)

Sources read 2026-10-23 (Terraform 1.17.0 CHANGELOG read 2026-10-22). See SKILL.md for inline source URLs per claim.

## Version-lifetime risk

- **Terraform 1.17.0 is stable (2026-10-21).** This skill targets `~> 1.16`; the newest 1.16.x is 1.16.7
  (released 2026-10-22). Re-verify when starting new work. Sources: https://releases.hashicorp.com/terraform/ ;
  https://raw.githubusercontent.com/hashicorp/terraform/v1.17/CHANGELOG.md
- **hashicorp/aws 6.x** — latest is 6.70.0 (2026-10-21); this skill uses `~> 6.69`.
  Source: https://releases.hashicorp.com/terraform-provider-aws/
- **6.57.0 is withdrawn** from GitHub and the Registry — never pin it.
  Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
- **v7 is planned** — the 6.0 upgrade guide says "`s3_us_east_1_regional_endpoint` will be removed in `v7.0.0`";
  no 7.x release exists. Sources:
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown ;
  https://releases.hashicorp.com/terraform-provider-aws/ (2026-10-23). When v7 ships, create a new skill `provisioning-aws-sam-v7`.
- **SAM CLI moves independently of the provider.** Latest stable v1.170.0 (2026-10-22); the last Terraform-related
  note is v1.166.2 (2026-09-11). Source: https://github.com/aws/aws-sam-cli/releases

## Unverified Items

| Tag | Item | Status |
|---|---|---|
| U1 | Hard minimum Terraform version for the SAM CLI hook (only a v1.6.0 recommendation for Terraform Cloud) | (unverified) — ask which Terraform version is used |
| U2 | Formal GA status of SAM CLI Terraform support (no label either way on the pages read) | (unverified) |
| U3 | Exhaustive list of API Gateway v1/v2 Terraform resource types supported by the hook | (unverified) |
| U4 | Whether the provider creates stacks through a reviewed change set (decides whether `CAPABILITY_AUTO_EXPAND` is needed on `aws_cloudformation_stack`); also whether `CAPABILITY_IAM` is needed for SAM-generated roles | (unverified, inference) |
| U5 | Drift detection behaviour of `aws_cloudformation_stack` for resources inside the stack | (unverified) |
| U6 | Any "do not mix with stacks deployed by `sam deploy`" warning — not on the provider page | (unverified) |
| U7 | SAM transform support in stack sets | (unverified) |
| U8 | Any AWS page comparing SAM and Terraform for provisioning; the decision guide for which resource carries SAM content is an inference | (unverified) |
| U9 | CloudFormation.4 outcome for SAR-created stacks (no role argument on the resource page) | (unverified) |
| U10 | Attribute name used for stack set template parameters in `ignore_changes` (`parameters` in the HCL examples) | (unverified) |
| U11 | Pinning `semantic_version` explicitly as a reproducibility practice | (unverified, inference) |
| U12 | Whether anything uploads `CodeUri` artifacts before apply (Terraform does not run `sam package`) | (unverified, inference) |

## Medium-Confidence Items

| Tag | Item | Status |
|---|---|---|
| M1 | No CHANGELOG entries for `aws_cloudformation_stack`, `aws_cloudformation_stack_set` or `aws_serverlessapplicationrepository_application` in 6.48.0–6.70.0; the 6.55.0 section was only partly covered | (medium confidence, absence of evidence) |
| M2 | `aws_cloudformation_stack` has no termination-protection argument on the page as read, so CloudFormation.3 may not be satisfiable from that resource alone | (medium confidence, absence of evidence) |
| M3 | `sam deploy`, `sam sync` and `sam validate` show no `--hook-name` or Terraform option on their reference pages | (medium confidence, absence of evidence) |

## Coverage Limits

| Tag | Item |
|---|---|
| L1 | Lambda and API Gateway resource arguments are out of scope — see `provisioning-aws-lambda-v6` and `provisioning-aws-api-gateway-v6` |
| L2 | No Security Hub controls page for Serverless Application Repository was found or reviewed |
| L3 | `aws_cloudformation_stack_set_instance` (6.0: `region` deprecated, use `stack_set_instance_region`) is not covered |
| L4 | IAM, Step Functions and S3 resources are out of scope — see `provisioning-aws-iam-v6`, `provisioning-aws-step-functions-v6`, `provisioning-aws-s3-v6` |

## Tag to Register Mapping

| Tag text | Where | Register id |
|---|---|---|
| (unverified) | SKILL.md Ask First — SAM vs Terraform for provisioning | U8 |
| (unverified, inference) | SKILL.md Ask First — which resource carries SAM content | U8 |
| (unverified) | SKILL.md Ask First — minimum Terraform version for the hook | U1 |
| (medium confidence, absence of evidence) | SKILL.md Ask First — hook status | U2 |
| (medium confidence, absence of evidence) | SKILL.md Ask First — `sam deploy`/`sync`/`validate` | M3 |
| (unverified, inference) | SKILL.md Ask First — capabilities for a SAM template in `aws_cloudformation_stack` | U4 |
| (unverified) | always-do-cloudformation.md §5 — provider use of change sets | U4 |
| (medium confidence, absence of evidence) | SKILL.md Version Context — newest SAM CLI releases list no Terraform change; minimum Terraform not stated; hook status label | U1, U2 |
| (unverified, inference) | SKILL.md Ask First — pin `semantic_version` | U11 |
| (unverified, inference) | SKILL.md Ask First — `CodeUri` artifacts | U12 |
| (unverified) | SKILL.md Ask First — drift detection and mixing with `sam deploy` stacks | U5, U6 |
| (unverified) | SKILL.md Ask First — SAM transform in stack sets | U7 |
| (unverified) | SKILL.md Ask First — API Gateway resource types supported by the hook | U3 |
| (medium confidence, absence of evidence) | SKILL.md Ask First — CloudFormation.3 termination protection | M2 |
| (unverified) | SKILL.md Ask First — CloudFormation.4 for SAR stacks | U9 |
| (medium confidence, absence of evidence) | SKILL.md 5.x → 6.x Migration (SAM) — no CHANGELOG entries 6.48.0–6.70.0 | M1 |
| (unverified) | always-do-cloudformation.md §5 — `CodeUri` artifacts | U12 |
| (unverified) | always-do-cloudformation.md §6 — transform in stack sets | U7 |
| (unverified) | always-do-cloudformation.md header — `ignore_changes` attribute name (never-do-cloudformation.md §2 refers to it) | U10 |

## Source Bibliography

All read 2026-10-23 unless stated.

1. https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html — SAM definition; comparisons with CloudFormation and CDK
2. https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/terraform-support.html — local debugging/testing scope; workflow; supported local commands
3. https://github.com/aws/aws-sam-cli/releases — v1.170.0; v1.166.2 Terraform hook fix
4. https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/gs-terraform-support.html — prerequisites; `sam build` with IDs; Terraform Cloud; sam metadata
5. https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-build.html — `--hook-name`, `--terraform-project-root-path`, incompatible flags
6. https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-local-start-api.html — `--terraform-plan-file`, `--skip-prepare-infra`
7. https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/terraform-reference.html — commands with Terraform
8. https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/using-samcli-terraform.html — limitations; prepare hook
9. https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/transform-aws-serverless.html — transform declaration and expansion
10. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/serverlessapplicationrepository_cloudformation_stack.html.markdown — SAR stack
11. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/serverlessapplicationrepository_application.html.markdown — SAR data source
12. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudformation_stack.html.markdown — `aws_cloudformation_stack`
13. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudformation_stack_set.html.markdown — `aws_cloudformation_stack_set`
14. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown — upgrade path; v7 planned
15. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md — 6.52.0 SAR stack entries; 6.57.0 withdrawn
16. https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-deploy.html — `sam deploy`
17. https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-sync.html — `sam sync`
18. https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-validate.html — `sam validate`
19. https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/terraform-sam-metadata.html — `sam metadata` resource
20. https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_CreateStack.html — `CAPABILITY_AUTO_EXPAND`; `RoleARN`
21. https://docs.aws.amazon.com/securityhub/latest/userguide/cloudformation-controls.html — CloudFormation.1–4
22. https://releases.hashicorp.com/terraform/ and https://releases.hashicorp.com/terraform-provider-aws/ — Terraform and provider releases
23. https://raw.githubusercontent.com/hashicorp/terraform/v1.17/CHANGELOG.md — 1.17.0 (read 2026-10-22)
24. https://developer.hashicorp.com/terraform/language/backend/s3 — `use_lockfile`; `dynamodb_table` deprecated
25. https://developer.hashicorp.com/terraform/language/expressions/version-constraints — `~>` for root modules
