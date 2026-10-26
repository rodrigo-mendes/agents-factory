# Unverified Claims and Risks — hashicorp/aws 6.x Step Functions

Pages read 2026-10-23 unless a source says otherwise. See SKILL.md for inline source URLs per claim.

## Version-lifetime risk

- **Terraform 1.17.0 is stable since 2026-10-21.** This skill targets `~> 1.16`; 1.17.0 is not the
  target. Source: https://releases.hashicorp.com/terraform/ (read 2026-10-23) and
  https://raw.githubusercontent.com/hashicorp/terraform/v1.17/CHANGELOG.md (read 2026-10-22).
  The newest 1.16.x is 1.16.7 (2026-10-22); `~> 1.16` is unchanged.
- **hashicorp/aws latest is 6.70.0**; the constraint stays `~> 6.69`; no 7.x released, v7 planned.
  Source: https://releases.hashicorp.com/terraform-provider-aws/
- **6.57.0 is withdrawn** — never pin. Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
- **v7 is planned**; the 6.0 upgrade guide is the authority for removals:
  https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
  When v7 ships, create `provisioning-aws-step-functions-v7`.
- 6.55.0 (2026-07-15) added a list resource for `aws_sfn_state_machine`
  (https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md).

Claims seen in older write-ups are in [corrections-and-limits](./corrections-and-limits.md).

## Unverified Items

| Tag | Item | Status |
|---|---|---|
| U1 | Whether `publish = true` publishes a new version on each update; the page says "during creation" | (unverified) |
| U2 | Whether definition whitespace or key order causes a permanent diff | (unverified) |
| U3 | Cross-account log destinations and whether an explicit log resource policy is needed | (unverified) |
| U4 | Scaffolding not quoted on the cited pages: ASL structure keys, IAM JSON `Version`/`Effect`/key-policy `Resource`, IAM resource types, and the condition operators in the trust-policy example (`StringEquals`, `ArnLike`) | (unverified) |

## Medium-Confidence Items

| Tag | Item | Status |
|---|---|---|
| M1 | Changing `type` forces replacement in Terraform; AWS says all versions share one type, exact ForceNew not quoted | (medium confidence) |
| M2 | `jsonencode` vs `templatefile` is a team convention; the research recorded no statement on the resource or function pages | (medium confidence) |
| M3 | `definition`, `role_arn`, logging and tracing changes are in-place updates, inferred from AWS `UpdateStateMachine` and the update timeout | (medium confidence) |
| M4 | Activity `encryption_configuration.type` documented as `AWS_KMS_KEY` while AWS documents `AWS_OWNED_KEY` | (medium confidence) |
| M5 | Activity encryption change forces replacement in Terraform (AWS says activity configuration is immutable) | (medium confidence) |
| M6 | No provider page found for `aws_sfn_state_machine_version`, `definition_substitutions`, or an `aws_sfn_*` entry in the 6.0 upgrade guide (absence of evidence) | (medium confidence, absence of evidence) |

## Coverage Limits

L1, L2 and L3 are listed in [corrections-and-limits](./corrections-and-limits.md#coverage-limits).

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (medium confidence) | SKILL.md, Ask First row "Definition authoring"; Quick Reference row "Definition substitution"; corrections-and-limits.md row on `definition_substitutions` | M2 |
| (medium confidence) | SKILL.md, Ask First row "Definition changes and versions" | M3 |
| (unverified) | SKILL.md, Ask First row "Definition changes and versions" | U1 |
| (unverified) | SKILL.md, Ask First row "Definition formatting diffs" | U2 |
| (medium confidence) | SKILL.md, Ask First row "Standard or Express" | M1 |
| (medium confidence) | SKILL.md, Ask First row "Activity encryption type" (enum discrepancy) | M4 |
| (medium confidence) | SKILL.md, Ask First row "Activity encryption type" (replacement behavior) | M5 |
| (unverified) | SKILL.md, Ask First row "Cross-account logging" | U3 |
| (medium confidence, absence of evidence) | SKILL.md, Quick Reference rows "Versions" and "Definition substitution"; "5.x → 6.x Migration"; corrections-and-limits.md table | M6 |
| (unverified) | one scaffolding note in the header of always-do-foundation.md, always-do-state-machine.md, always-do-encryption-testing.md, never-do-configuration.md, never-do-iam-asl.md | U4 |

## Source Bibliography

All read 2026-10-23.

1. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sfn_state_machine.html.markdown
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sfn_alias.html.markdown
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sfn_activity.html.markdown
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown — no `aws_sfn_*` entry
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/sfn_state_machine_versions.html.markdown
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
7. https://docs.aws.amazon.com/step-functions/latest/dg/service-quotas.html
8. https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html
9. https://docs.aws.amazon.com/step-functions/latest/dg/concepts-state-machine-version.html
10. https://docs.aws.amazon.com/step-functions/latest/dg/encryption-at-rest.html
11. https://docs.aws.amazon.com/step-functions/latest/dg/concepts-state-machine-alias.html
12. https://docs.aws.amazon.com/step-functions/latest/dg/connect-to-resource.html
13. https://docs.aws.amazon.com/step-functions/latest/dg/connect-lambda.html
14. https://docs.aws.amazon.com/step-functions/latest/dg/concepts-error-handling.html
15. https://docs.aws.amazon.com/step-functions/latest/dg/state-map-inline.html
16. https://docs.aws.amazon.com/scheduler/latest/UserGuide/managing-targets-templated.html
17. https://developer.hashicorp.com/terraform/language/functions/templatefile (medium confidence)
18. https://docs.aws.amazon.com/step-functions/latest/dg/procedure-create-iam-role.html
19. https://docs.aws.amazon.com/step-functions/latest/dg/cw-logs.html
20. https://docs.aws.amazon.com/step-functions/latest/dg/concepts-xray-tracing.html
21. https://docs.aws.amazon.com/securityhub/latest/userguide/stepfunctions-controls.html
22. https://developer.hashicorp.com/terraform/language/backend/s3
23. https://developer.hashicorp.com/terraform/language/expressions/version-constraints
24. https://developer.hashicorp.com/terraform/language/files/dependency-lock
25. https://developer.hashicorp.com/terraform/language/tests and https://developer.hashicorp.com/terraform/language/tests/mocking
26. https://developer.hashicorp.com/terraform/cli/commands/plan and https://developer.hashicorp.com/terraform/cli/commands/validate
