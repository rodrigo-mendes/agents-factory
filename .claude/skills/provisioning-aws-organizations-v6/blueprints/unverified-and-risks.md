# Unverified Claims and Risks — hashicorp/aws 6.x Organizations

Research date 2026-10-23. See SKILL.md for inline source URLs per claim.

## Version-lifetime risk

- **Terraform 1.17.0 is stable since 2026-10-21** (no breaking changes to validate, S3 backend, lock file or
  `required_version`). This skill targets `~> 1.16` (1.16.6); re-verify before moving the constraint.
  Source: https://releases.hashicorp.com/terraform/
- **hashicorp/aws 6.70.0 is the latest** (CHANGELOG dates it 2026-10-21); constraint `~> 6.69` allows 6.70.x.
  Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
- **6.57.0 is withdrawn** from GitHub and the Registry — never pin it.
- **v7 is planned**, not released. When it ships, create `provisioning-aws-organizations-v7`.
- Raw `main` docs may run slightly ahead of 6.70.0 (L2).

## Unverified Items

| Tag | Item | Status |
|---|---|---|
| U1 | Whether changing `aws_organizations_organizational_unit.parent_id` forces replacement — not stated on the page | (unverified) — treat as unknown; plan before applying |
| U2 | Why `aws_organizations_policies_for_target.filter` lists 7 types while the resource lists 12 | (unverified) — docs may lag real validation |
| U3 | Security Hub `organizations-controls` page returned no controls | (unverified) — only Account.1 and Account.2 are cited |
| U4 | ServiceCatalog.1 severity and details — seen only in search results | (unverified) — registered only; not cited in this skill |
| U5 | Legacy claim that `depends_on` is often required between Organizations resources | (unverified) — registered only; no source read supports it, so the skill makes no claim either way |
| U6 | Legacy claim that RCPs and declarative policies apply to the management account — RCP page not read | (unverified) — registered only; not stated in this skill |

## Medium-Confidence Items

| Tag | Item | Status |
|---|---|---|
| M1 | `prevent_destroy` on foundational accounts — Terraform-generic lifecycle, not prescribed by the resource page | (medium confidence) |
| M2 | Build non-IAM policy types with `jsonencode`, not `aws_iam_policy_document` — inferred from per-type syntax links | (medium confidence) |
| M3 | Terraform-created organizations do not get the automatic Leave/Close SCP — inferred (Terraform calls the API, not the console path) | (medium confidence) |
| M4 | No Organizations entries found in the 6.0.0 upgrade guide or the CHANGELOG 6.48.0 to 6.70.0 — absence of evidence, main-branch pages | (medium confidence) |
| M5 | A delegated administrator can be the provider's identity where AWS allows it — inferred; the account page only says management must be done from the root account | (medium confidence) |

## Coverage Limits

| Tag | Item |
|---|---|
| L1 | Tag, backup and declarative policy syntax pages were not fetched |
| L2 | Registry pages are JS-only; raw `main` branch used |
| L3 | The 6.x release that added each newer policy type was not traced (outside 6.48.0 to 6.70.0) |
| L4 | Root access management / centralized root credentials not researched |
| L5 | Integrations with CloudTrail, Config, SSO and S3 are out of scope (see provisioning-aws-cloudtrail-v6 for org trails) |

## Tag to Register Mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) | always-do-foundation.md §3 Organizational Units — `parent_id` replacement | U1 |
| (unverified) | always-do-policies.md §8 Policies for Target and Terraform Test — filter values | U2 |
| (medium confidence) | always-do-foundation.md §4 Accounts — `prevent_destroy` | M1 |
| (medium confidence) | always-do-policies.md §6 Policy Types and Non-SCP Policies — `jsonencode` | M2 |
| (medium confidence) | always-do-policies.md §5 Deny-list SCP and Attachment — Terraform-created organizations | M3 |
| (medium confidence) | SKILL.md Ask First table, `prevent_destroy` row | M1 |
| (medium confidence) | SKILL.md Ask First table, root SCP Leave/Close row (Terraform-created organizations) | M3 |
| (medium confidence) | SKILL.md Ask First table, provider identity row (delegated administrator) | M5 |
| (medium confidence, absence of evidence) | SKILL.md 5.x to 6.x Migration, 6.0.0 guide and CHANGELOG bullets | M4 |
| (unverified: absence of evidence) | SKILL.md Quick Reference, Security Hub org controls page row | U3 |

Registered only (no tag used in the skill text): U4, U5, U6; listed for traceability.

## Source Bibliography

All fetched 2026-10-23.

1. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown — Organizations global; no `region`
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown — no Organizations entries
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md — 6.48.0 to 6.70.0 no Organizations entries; 6.57.0 withdrawn
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_organization.html.markdown
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_account.html.markdown
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_policy.html.markdown
7. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_organizational_unit.html.markdown
8. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_policy_attachment.html.markdown
9. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_delegated_administrator.html.markdown
10. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_resource_policy.html.markdown
11. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/organizations_policies_for_target.html.markdown
12. https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html
13. https://docs.aws.amazon.com/organizations/latest/userguide/orgs_reference_limits.html
14. https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps_evaluation.html
15. https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices_mgmt-acct.html
16. https://docs.aws.amazon.com/securityhub/latest/userguide/account-controls.html — Account.1 moderate severity, Account.2 High
17. https://docs.aws.amazon.com/securityhub/latest/userguide/organizations-controls.html — fetched; no control content
18. https://releases.hashicorp.com/terraform/ — 1.16.6, 1.17.0 stable
19. https://developer.hashicorp.com/terraform/language/backend/s3 — `use_lockfile`; `dynamodb_table` deprecated
20. https://developer.hashicorp.com/terraform/language/expressions/version-constraints — `~>` in root modules
21. https://developer.hashicorp.com/terraform/language/tests — `.tftest.hcl`, `mock_provider`
