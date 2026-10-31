# Never-Do Patterns — provisioning-aws-sam-v6

Index of the never-do blueprints, split by topic. Each entry has a `# WRONG` block, the documented reason with
its source (read 2026-10-23), and the correct alternative. One row per row of the SKILL.md Never Do table.

| Anti-pattern | Blueprint |
|---|---|
| `sam build --hook-name` with `--build-in-source`, `--parameter-overrides` or `--template-file` | [never-do-sam-cli](./never-do-sam-cli.md#1-incompatible-flags-with-hook-name) |
| `--terraform-project-root-path` / `--terraform-plan-file` without `--hook-name terraform` | [never-do-sam-cli](./never-do-sam-cli.md#2-terraform-only-flags-without-hook-name) |
| `sam metadata` resource name without the `sam_metadata_` prefix | [never-do-sam-cli](./never-do-sam-cli.md#3-sam-metadata-name-without-the-prefix) |
| `--skip-prepare-infra` after adding functions or API endpoints | [never-do-sam-cli](./never-do-sam-cli.md#4-skip-prepare-infra-after-adding-resources) |
| Referencing a Lambda function that is not yet created | [never-do-sam-cli](./never-do-sam-cli.md#5-referencing-a-function-not-yet-created) |
| Assuming SAR `NoEcho` values are masked in state | [never-do-cloudformation](./never-do-cloudformation.md#1-assuming-sar-noecho-values-are-masked-in-state) |
| Stack set `NoEcho` parameters left unignored | [never-do-cloudformation](./never-do-cloudformation.md#2-stack-set-noecho-parameters-left-unignored) |
| `on_failure` together with `disable_rollback` | [never-do-cloudformation](./never-do-cloudformation.md#3-on_failure-together-with-disable_rollback) |
| Inline template over 51,200 bytes in `template_body` | [never-do-cloudformation](./never-do-cloudformation.md#4-inline-template-over-the-template_body-limit) |
| Pinning withdrawn provider 6.57.0 | [never-do-provider-migration](./never-do-provider-migration.md#1-pinning-version-6570) |
| S3 backend with `dynamodb_table` (deprecated) | [never-do-provider-migration](./never-do-provider-migration.md#2-s3-backend-with-dynamodb_table) |
