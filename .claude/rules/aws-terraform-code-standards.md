---
name: aws-terraform-code-standards
description: "AWS Terraform code standards for hashicorp/aws 6.x: version constraints, per-resource region, global services, data.aws_region, identity import, terraform test. Use when editing or reviewing AWS Terraform HCL."
paths:
  - "**/aws/**/*.tf"
  - "**/aws/**/*.tf.json"
  - "**/aws/**/*.tfvars"
  - "**/aws/**/*.tftest.hcl"
  - "**/*aws*/**/*.tf"
  - "**/*aws*/**/*.tftest.hcl"
---

# AWS Terraform Code Standards (hashicorp/aws 6.x, Terraform ~> 1.16)

Service-level patterns live in the `provisioning-aws-<service>-v6` skills; this rule holds only the
cross-cutting facts. Tags `(unverified)` / `(medium confidence)` in a skill are not rules.

## Always

1. **Root modules set `required_version = "~> 1.16"` and the aws provider `version = "~> 6.69"`.**
   Source: https://developer.hashicorp.com/terraform/language/expressions/version-constraints
2. **Reusable modules declare only a minimum (`>=`), never `~>`.** Same source as rule 1.
3. **Set `region` on a regional resource only to override the provider region.** It defaults to the
   provider region.
   Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown
4. **Import a regional resource with `id@region` when its region differs from the provider region.**
   Same source as rule 3.
5. **Read the region with `data.aws_region.<name>.region`.** The `name` attribute is deprecated
   since 6.0. Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
6. **On `aws_s3_bucket`, use `bucket_region` for the bucket location.** There, `region` means
   Enhanced Region Support. Same source as rule 5.
7. **Use identity-based import (`identity` block) only with Terraform >= 1.12.0.**
   Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc.html.markdown
8. **Write tests as `.tftest.hcl` files in `tests/`** with `run` blocks and
   `assert { condition, error_message }`.
   Source: https://developer.hashicorp.com/terraform/language/tests
9. **Use `mock_provider` / `override_resource` (>= 1.7) for tests that must not reach AWS.**
   Source: https://developer.hashicorp.com/terraform/language/tests/mocking
10. **Check the 6.0 upgrade guide for removed or renamed arguments before copying an argument from
    5.x examples.** Source: the upgrade guide URL in rule 5.

## Never

11. **Never set `region` on a global-service resource** (no `region`, no `id@region` import).
    Global: all IAM resources (incl. Roles Anywhere, `aws_caller_identity`), CloudFront, Route 53
    (+ domains, ARC), Organizations, Shield Advanced, WAF Classic (`aws_waf_*`), Budgets, Billing,
    Cost Explorer, Cost Optimization Hub, CUR, Data Exports, Savings Plans, Account Management,
    Global Accelerator, Network Manager, `aws_s3_account_public_access_block`,
    `aws_canonical_user_id`, `aws_cloudtrail_organization_delegated_admin_account`,
    `aws_vpc_ipam_organization_admin_account`, `aws_fms_admin_account`,
    `aws_ram_sharing_with_organization`, `aws_backup_global_settings`, `aws_dx_gateway`.
    Source: enhanced-region guide (rule 3).
12. **Never treat `aws_route53_resolver_*` as global.** It documents an optional `region`.
    Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_resolver_endpoint.html.markdown
13. **Never treat `aws_wafv2_*` as global.** It documents an optional `region`; only `aws_waf_*`
    (Classic) is global. Source: enhanced-region guide (rule 3).
14. **Never use `data.aws_region.<name>.name`** (deprecated, rule 5).

## Not rules (confirm first)

- For WAFv2 `scope = "CLOUDFRONT"` the docs say the provider must target `us-east-1`. Setting
  `region = "us-east-1"` on the resource instead of a provider alias is an inference (medium
  confidence): confirm with the user before using it.

## Verify

- `grep -rnE 'data\.aws_region\.[A-Za-z0-9_-]+\.name\b' --include='*.tf' .` returns nothing.
- Grep each global resource type of rule 11 in `*.tf` and confirm no `region` argument appears in
  its block.
- `terraform fmt -check -recursive`, `terraform init -backend=false`, `terraform validate`.
