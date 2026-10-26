# Unverified Claims and Risks — hashicorp/aws 6.x IAM

Research date 2026-10-14. See SKILL.md for inline source URLs per claim.

## Version-lifetime risk

- **hashicorp/aws 6.x is the current stable major** as of 2026-10-14 (reference 6.69.0). Re-verify when
  starting new work or after 30 days. Source: https://github.com/hashicorp/terraform-provider-aws/releases
- **Terraform 1.16.6** is the current stable CLI. **1.17.0-rc2** exists — do not target it.
  Source: https://releases.hashicorp.com/terraform/
- **6.57.0 is permanently withdrawn** from GitHub and the Registry. Any constraint resolving to it
  fails `terraform init`.
- **v7 is planned** — upgrade guide already documents items "removed in v7.0.0". When v7 ships,
  create a new skill `provisioning-aws-iam-v7`.
- **`inline_policy` and `managed_policy_arns`** are deprecated (since 5.68.0 / 5.72.0) and remain
  in 6.x — they may be removed in a future major. Prefer separate resources now.

## Unverified Items

| Tag | Item | Status |
|---|---|---|
| U1 | `aws_iam_role` `path` default — not stated on the provider page; AWS default `/` is assumed but not verified | (unverified) — always set `path = "/"` explicitly if relying on it |
| U2 | `aws_iam_policy_attachment` import — not documented on the resource page; resource identity was added in 6.54.0 | (unverified) — import behavior via identity block not fully confirmed |
| U3 | Whether `aws_iam_openid_connect_provider.url` forces new — not stated on the provider page | (unverified) — treat `url` as force-new; plan before changing |
| U4 | `aws_iam_account_password_policy` defaults and valid ranges — not on the provider page; AWS ranges used from the AWS docs page | (unverified on provider page) — use AWS documented ranges: length 6–128, expiry 1–1095 days, reuse 1–24 |
| U5 | `aws_iam_account_password_policy` destroy behavior — not documented; may revert to AWS default or leave the policy unchanged | (unverified) — do not rely on destroy to reset the policy |
| U6 | Release year of 5.68.0 and 5.72.0 — GitHub pages show "19 September" and "15 October" without a year; 2024 inferred from adjacent 5.71.0 date | (unverified year) — the version numbers and deprecation facts are confirmed |

## Medium-Confidence Items

| Tag | Item | Status |
|---|---|---|
| M1 | `ses_smtp_password_v4` state storage — inferred to be plaintext like `secret`; not explicitly stated on the access-key resource page | (medium confidence) — treat the SES password the same as `secret`: plaintext in state |
| M2 | Role-delegation boundary actions (`iam:CreateRole`, `iam:PutRolePermissionsBoundary`) — extrapolated from the AWS user-boundary example; the role equivalents were not explicitly shown on the boundaries page | (medium confidence) — apply the same delegation pattern for roles; verify against official IAM docs before production use |
| M3 | "CIS-safe" password policy combination — derived from Security Hub IAM.15/16/17 controls, not from a single authoritative statement | (medium confidence) — the individual control requirements are confirmed; their combination as a single preset was not found on one page |
| M4 | Verbatim wording of provider warnings — WebFetch paraphrases; substance was confirmed on raw markdown | (medium confidence) — use raw markdown source URLs to verify exact wording |

## Coverage Limits

| Tag | Item |
|---|---|
| L1 | CHANGELOG [8] was read in two chunks; 6.54.0 straddled the boundary and was only partly visible |
| L2 | Registry pages are JS-only; raw `main` branch used — may run slightly ahead of 6.69.0 |
| L3 | Not covered: `aws_iam_saml_provider`, `aws_iam_virtual_mfa_device`, `aws_iam_user_login_profile`, `aws_iam_signing_certificate`, `aws_iam_organizations_features`, `aws_iam_outbound_web_identity_federation`, `aws_iam_principal_policy_simulation`, Access Analyzer resources, and IRSA/EKS Pod Identity |

## Tag to Register Mapping

| Tag text | Where | Register id |
|---|---|---|
| (unverified) | always-do-oidc-users.md §8 — password policy destroy behavior | U5 |
| (unverified) | always-do-oidc-users.md §8 — password policy defaults not on provider page | U4 |
| (medium confidence) | never-do-identity.md §5 — ses_smtp_password_v4 plaintext | M1 |
| (medium confidence) | SKILL.md Version Context — `inline_policy`/`managed_policy_arns` release year | U6 |

## Source Bibliography

All fetched 2026-10-14. Numbers match the original research bibliography.

1. Shared version and region facts: the Terraform and provider pages cited inline, read 2026-10-23.
2. https://releases.hashicorp.com/terraform/ — Terraform 1.16.6 stable; 1.17.0-rc2 pre-release
3. https://github.com/hashicorp/terraform-provider-aws/releases — 6.69.0 current
4. https://developer.hashicorp.com/terraform/language/backend/s3 — use_lockfile; dynamodb_table deprecated
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown — data.aws_region.name deprecated; aws_redshift_service_account removed
6. https://github.com/hashicorp/terraform-provider-aws/releases/tag/v5.68.0 — inline_policy deprecated; aws_iam_role_policies_exclusive added
7. https://github.com/hashicorp/terraform-provider-aws/releases/tag/v5.72.0 — managed_policy_arns deprecated; aws_iam_role_policy_attachments_exclusive added
8. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md — 6.57.0 withdrawn; IAM changes 6.48–6.69
9. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown — global services list; non-region-aware resources
10. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_role.html.markdown
11. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_role_policy.html.markdown
12. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_role_policy_attachment.html.markdown
13. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_role_policies_exclusive.html.markdown
14. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_role_policy_attachments_exclusive.html.markdown
15. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_instance_profile.html.markdown
16. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_service_linked_role.html.markdown
17. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_policy.html.markdown
18. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_policy_attachment.html.markdown
19. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/iam_policy_document.html.markdown
20. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_user.html.markdown
21. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_group.html.markdown
22. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_group_membership.html.markdown
23. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_user_policies_exclusive.html.markdown
24. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_group_policies_exclusive.html.markdown
25. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_user_policy_attachments_exclusive.html.markdown
26. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_group_policy_attachments_exclusive.html.markdown
27. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_access_key.html.markdown
28. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_openid_connect_provider.html.markdown
29. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/iam_account_password_policy.html.markdown
30. https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html
31. https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html
32. https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_oidc.html
33. https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_passwords_account-policy.html
34. https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html
35. https://docs.aws.amazon.com/securityhub/latest/userguide/iam-controls.html
36. https://developer.hashicorp.com/terraform/language/expressions/version-constraints
37. https://developer.hashicorp.com/terraform/language/terraform
38. https://developer.hashicorp.com/terraform/language/files/dependency-lock
39. https://developer.hashicorp.com/terraform/language/tests
40. https://developer.hashicorp.com/terraform/cli/commands/plan
