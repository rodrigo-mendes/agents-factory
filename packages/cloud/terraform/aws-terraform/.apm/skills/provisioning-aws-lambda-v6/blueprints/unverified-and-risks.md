# Unverified Claims and Risks — hashicorp/aws 6.x Lambda

All pages read 2026-10-23 (only the Terraform 1.17.0 CHANGELOG was read 2026-10-22).
See SKILL.md for inline source URLs per claim.

## Version-lifetime risk

- **Terraform 1.17.0 is stable since 2026-10-21** (read 2026-10-23); `~> 1.16` admits 1.17.x, but this skill
  was verified against 1.16.x only. Source: https://releases.hashicorp.com/terraform/
- **hashicorp/aws latest is 6.70.0** (read 2026-10-23); constraint `~> 6.69` admits every 6.x release from
  6.69 on; no 7.x released and v7 is
  planned — when it ships, create `provisioning-aws-lambda-v7`. The 6.0.0 upgrade guide already mentions
  v7 removals. Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
- **6.57.0 is withdrawn** — never pin. Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
- **Lambda runtime support is time-sensitive.** Read 2026-10-23 from https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html ;
  re-read the page before choosing a runtime:

| Item (as read 2026-10-23) | Value |
|---|---|
| Supported identifiers | `nodejs24.x`, `nodejs22.x`, `python3.14`, `python3.13`, `python3.12`, `python3.11`, `python3.10`, `java25`, `java21`, `java17.al2023`, `java11.al2023`, `java8.al2023`, `java17`, `java11`, `java8.al2`, `dotnet10`, `dotnet8`, `ruby4.0`, `ruby3.4`, `ruby3.3`, `provided.al2023` (`dotnet9` container-only) |
| Preview, not for production | `nodejs26.x`, `python3.15` (GA targeted November 2026) |
| Deprecating soon | `python3.10` on 2026-10-31; `dotnet8` and `dotnet9` on 2026-11-10 |
| Amazon Linux 2 runtimes | `python3.11`, `java17`, `java11`, `java8.al2` deprecate 2027-06-30 |
| Already deprecated | `provided.al2` (2026-07-31), `nodejs20.x` (2026-04-30), `ruby3.2`, `python3.9`, `nodejs18.x`, `dotnet6`, `python3.8`, `nodejs16.x`, `java8`, `go1.x`, `provided`, and older |
| Policy | Notice at least 180 days before deprecation; at deprecation no patches or support and console create/update is blocked (CLI/SAM/CloudFormation still allowed); block-create at least 30 days and block-update at least 60 days after |
| Architectures | All supported runtimes support `x86_64` and `arm64` |

  `dotnet8` deprecates 2026-11-10, so it is not a safe value to hard-code in an allow-list. `java11` stays
  supported until 2027-06-30 and `java11.al2023` is listed as supported to 2029 on the same page (it is not
  "approaching EOL"). Security Hub Lambda.2 keeps its own runtime list
  (https://docs.aws.amazon.com/securityhub/latest/userguide/lambda-controls.html).

## Unverified Items

| Tag | Item | Status |
|---|---|---|
| U1 | Whether `snap_start` supports runtimes beyond Java, and `arm64` — AWS SnapStart page not read | (unverified) — only the provider argument shape (`apply_on = "PublishedVersions"`) is documented |
| U2 | Defaults of `application_log_level` / `system_log_level`, and whether JSON is required — AWS advanced-logging page returned no content | (unverified) — set both levels explicitly |
| U3 | `aws_lambda_resource_policy` arguments and interaction with `aws_lambda_permission` — page not read (resource added in 6.65.0) | (unverified) — read the resource page before use |
| U4 | X-Ray IAM permissions for active tracing — page not read | (unverified) — check AWS docs before enabling |
| U5 | Default retention of Lambda-created log groups — not stated on pages read | (unverified) — manage the log group with `retention_in_days` |
| U7 | `event_source_arn` on `aws_lambda_event_source_mapping` is the required event-source identifier — not stated in the mapping page text read | (unverified) — shown as a placeholder |
| U6 | `aws_iam_role` / `aws_iam_role_policy` argument shapes and the IAM `Version` element in the execution-role HCL — no IAM page was read | (unverified) — see `provisioning-aws-iam-v6` |

## Medium-Confidence Items

| Tag | Item | Status |
|---|---|---|
| M1 | `aws_lambda_function.skip_destroy` description mentions "Lambda Layer"; likely a docs copy-paste, actual semantics not confirmed | (medium confidence) |
| M2 | `depends_on` on the log group appears in provider examples only; the page does not say it is required | (medium confidence) |
| M3 | Lambda.2 runtime list omits `provided.al2023`; custom-runtime functions may fail Lambda.2 (inference) | (medium confidence) |
| M4 | `vpc_config` and `capacity_provider_config` are listed as mutually exclusive, but the provider version that introduced `capacity_provider_config` is not pinned | (medium confidence) |
| M5 | How `source_account` on `aws_lambda_permission` maps to the `AWS:SourceAccount` condition checked by Lambda.1 — the permission page lists S3 among its uses but does not state the condition | (medium confidence) |
| M6 | Absence claims in the migration section: no Lambda items in the 6.0.0 upgrade guide and no BREAKING Lambda entries in CHANGELOG 6.48.0–6.70.0 (see L1) | (medium confidence, absence of evidence) |

## Coverage Limits

| Tag | Item |
|---|---|
| L1 | Part of the 6.55.0 CHANGELOG section was not read (coverage limit); no Lambda entries in the part that was read |
| L2 | Raw `main` docs may run slightly ahead of 6.70.0; the provider version that introduced `durable_config`, `tenancy_config`, `capacity_provider_config` and `publish_to` is not pinned |
| L3 | `aws_lambda_function_scaling_config` (new in 6.54.0) is noted but its arguments were not read |
| L4 | Registry pages are JS-only and unreadable; raw `main` markdown is used instead |

## Tag to Register Mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (medium confidence) | always-do-function.md section 3 — `depends_on` on the log group | M2 |
| (unverified) | always-do-function.md section 2 — IAM argument shapes and `Version` | U6 |
| (unverified) | always-do-events-layers.md section 12 — `event_source_arn` placeholder | U7 |
| (medium confidence) | SKILL.md Ask First — "Newer function blocks" row | L2 |
| (medium confidence) | SKILL.md Never Do — `source_account` Instead cell | M5 |
| (medium confidence) | SKILL.md Ask First — `vpc_config` with `capacity_provider_config` | M4 |
| (medium confidence) | SKILL.md Ask First — `source_account` for S3 invokers; never-do-access-provider.md section 2 | M5 |
| (medium confidence, absence of evidence) | SKILL.md 5.x → 6.x Migration (both absence bullets) | M6 |
| (unverified) | SKILL.md Ask First — SnapStart supported runtimes | U1 |
| (unverified) | SKILL.md Ask First — default log levels | U2 |
| (unverified) | SKILL.md Ask First — `aws_lambda_resource_policy` | U3 |
| (unverified) | SKILL.md Ask First — X-Ray permissions | U4 |
| (unverified) | SKILL.md Ask First — log group default retention | U5 |
| (medium confidence) | SKILL.md Ask First — `skip_destroy` description | M1 |
| (medium confidence) | SKILL.md Ask First — Lambda.2 and `provided.al2023` | M3 |

## Source Bibliography

Provider and AWS pages read 2026-10-23.

1. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_function.html.markdown
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_event_source_mapping.html.markdown
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_permission.html.markdown
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_function_url.html.markdown
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_alias.html.markdown
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_layer_version.html.markdown
7. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_provisioned_concurrency_config.html.markdown
8. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
9. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
10. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_function_event_invoke_config.html.markdown
11. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/lambda_code_signing_config.html.markdown
12. https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html
13. https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html
14. https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html
15. https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html
16. https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs.html
17. https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html
18. https://docs.aws.amazon.com/securityhub/latest/userguide/lambda-controls.html
19. https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-advanced.html — returned no usable content; not a source (see U2)
20. https://releases.hashicorp.com/terraform/ and https://releases.hashicorp.com/terraform-provider-aws/ — read 2026-10-23
21. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown — read 2026-10-23
22. https://developer.hashicorp.com/terraform/language/expressions/version-constraints — read 2026-10-23
