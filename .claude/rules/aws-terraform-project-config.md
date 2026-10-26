---
name: aws-terraform-project-config
description: "AWS Terraform project configuration: Terraform and provider constraints, S3 backend locking, dependency lock file, upgrade path from provider 5.x. Use when editing versions.tf, backend blocks or .terraform.lock.hcl."
paths:
  - "**/versions.tf"
  - "**/backend.tf"
  - "**/providers.tf"
  - "**/terraform.tf"
  - "**/.terraform.lock.hcl"
---

# AWS Terraform Project Config (hashicorp/aws 6.x, Terraform ~> 1.16)

## Version targets

- The skills' target constraint is Terraform `~> 1.16` (>= 1.16 and < 2.0). It also admits 1.17+,
  which the skills have not been verified against. Terraform 1.17.0 has been stable since
  2026-10-21; the newest 1.16.x is 1.16.7 (2026-10-22). Sources:
  https://releases.hashicorp.com/terraform/ ;
  https://raw.githubusercontent.com/hashicorp/terraform/v1.17/CHANGELOG.md
- hashicorp/aws `~> 6.69`; latest is 6.70.0 (2026-10-21), allowed by the constraint. No 7.x
  exists. Source: https://releases.hashicorp.com/terraform-provider-aws/

## Always

1. **Declare `required_version = "~> 1.16"` in root modules**; reusable modules set a minimum only.
   Source: https://developer.hashicorp.com/terraform/language/expressions/version-constraints
2. **Declare the aws provider `version = "~> 6.69"` in root modules.** Same source as rule 1.
3. **S3 backend: `use_lockfile = true`** (native locking, `<key>.tflock`).
   Source: https://developer.hashicorp.com/terraform/language/backend/s3
4. **Commit `.terraform.lock.hcl`.** It records providers only; move versions with
   `terraform init -upgrade`. Source: https://developer.hashicorp.com/terraform/language/files/dependency-lock
5. **Run `terraform init -backend=false` before `terraform validate` in CI.**
   Source: https://developer.hashicorp.com/terraform/cli/commands/validate
6. **Read `terraform plan -detailed-exitcode` as 0 = no changes, 1 = error, 2 = changes.**
   Source: https://developer.hashicorp.com/terraform/cli/commands/plan
7. **Upgrading from provider 5.x: first upgrade to the latest 5.x** and get a plan with no errors,
   no unexpected changes and no deprecation warnings related to the guide.
   Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
8. **Then update constraints to allow the 6.x series and run `terraform init -upgrade`.** The guide
   states no minimum Terraform version (same source as rule 7).

## Never

9. **Never use `dynamodb_table` in the S3 backend** (deprecated). Use `use_lockfile = true`.
10. **Never pin aws provider 6.57.0** (withdrawn from GitHub and the Registry).
    Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
11. **Never target provider 7.x with these skills.** v7 is planned (the 6.0 guide says
    `s3_us_east_1_regional_endpoint` "will be removed in `v7.0.0`"); a new major needs new skills
    (same source as rule 7).

## Not rules (confirm first)

- Terraform 1.17+ is admitted by `~> 1.16` but not verified by the skills: confirm with the user
  before targeting it (sources in "Version targets").

## Verify

- `grep -rnE '^\s*dynamodb_table\s*=' --include='*.tf' .` returns nothing.
- `grep -rnE '6\.57\.0' --include='*.tf' --include='.terraform.lock.hcl' .` returns nothing.
- Glob for `.terraform.lock.hcl` next to each root module and confirm it is not git-ignored.
