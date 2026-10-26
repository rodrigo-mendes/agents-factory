# Unverified Claims and Risks — hashicorp/aws 6.x X-Ray

Read date 2026-10-23 (Terraform 1.17.0 CHANGELOG read 2026-10-22). See SKILL.md for inline source URLs per claim.

## Version-lifetime risk

- **Terraform 1.17.0 is stable** (2026-10-21; no breaking changes noted for validate, S3 backend, lock file or
  `required_version`). It is not the target of this skill (`~> 1.16`; newest 1.16.x is 1.16.7, 2026-10-22).
  Sources: https://releases.hashicorp.com/terraform/ ; https://raw.githubusercontent.com/hashicorp/terraform/v1.17/CHANGELOG.md
- **hashicorp/aws 6.x**: latest 6.70.0 (2026-10-21); this skill uses `~> 6.69`; no 7.x release.
  Source: https://releases.hashicorp.com/terraform-provider-aws/
- **6.57.0 is withdrawn** from GitHub and the Registry — never pin it.
  Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
- **v7 is planned**: the 6.0 upgrade guide says "`s3_us_east_1_regional_endpoint` will be removed in `v7.0.0`" (https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown).
  When v7 ships, create a new skill `provisioning-aws-xray-v7`.
- **2026 X-Ray change**: the X-Ray SDKs and Daemon entered maintenance mode on 2026-02-25 (security fixes only,
  "will not receive new feature enhancements"). AWS: "X-Ray is transitioning to OpenTelemetry (OTel) as its primary
  instrumentation standard", and recommends OpenTelemetry SDKs / ADOT with the OpenTelemetry Collector or CloudWatch
  agent for new and existing applications. Sources: https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html ;
  https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-daemon-timeline.html
- No change to the default sampling rule was found on official pages read (medium confidence, absence of evidence).

## Unverified Items

| Tag | Item | Status |
|---|---|---|
| U1 | Whether sampling-rule priorities must be unique, or what happens on ties — the AWS pages read give the 1–9999 range and ascending evaluation only | (unverified) — treat unique priorities as a defensive convention |
| U2 | How Terraform handles the `Default` sampling rule — not documented on the provider page | (unverified) — ask before managing it |
| U3 | KMS key-policy statements needed for `xray.amazonaws.com` on a customer managed key | (unverified) — confirm against the AWS encryption page |

## Medium-Confidence Items

| Tag | Item | Status |
|---|---|---|
| M1 | Rule name/priority cannot be changed per the Step Functions guide; provider ForceNew behaviour is not stated on the provider page | (medium confidence) |
| M2 | One encryption config per account per region — inferred from `id` = region name | (medium confidence) |
| M3 | The 6.0 upgrade guide has no X-Ray / `aws_xray_*` entries | (medium confidence, absence of evidence) |
| M4 | The provider CHANGELOG 6.48.0 to 6.70.0 has no `aws_xray_*` entries | (medium confidence, absence of evidence) |
| M5 | Security Hub controls reference has no `XRay.*` controls | (medium confidence, absence of evidence) |
| M6 | No change to the default sampling rule found on the official pages read | (medium confidence, absence of evidence) |

## Coverage Limits

| Tag | Item |
|---|---|
| L1 | `aws_xray_indexing_rule`, `aws_xray_trace_segment_destination` and `aws_xray_resource_policy` are not covered (the first two are new resources in provider 6.46.0 per the CHANGELOG) |
| L2 | `SamplingRateBoost` exists in the AWS API; the provider page lists no corresponding argument at read time |
| L3 | Data sources were not checked; CloudWatch Application Signals provisioning is out of scope |

## Tag to Register Mapping

| Tag text | Where | Register id |
|---|---|---|
| (unverified) | SKILL.md Ask First — KMS key-policy statements | U3 |
| (unverified) | SKILL.md Ask First — Priority uniqueness | U1 |
| (unverified) | SKILL.md Ask First — Managing the `Default` sampling rule | U2 |
| (medium confidence) | SKILL.md Ask First — One encryption config per region; always-do-foundation.md §2 | M2 |
| (medium confidence) | SKILL.md Ask First — Changing a rule's name or priority | M1 |
| (medium confidence, absence of evidence) | SKILL.md Migration section — 6.0 guide entries | M3 |
| (medium confidence, absence of evidence) | SKILL.md Migration section — CHANGELOG entries | M4 |
| (medium confidence, absence of evidence) | unverified-and-risks.md Version-lifetime risk — default sampling rule | M6 |
| (medium confidence, absence of evidence) | SKILL.md Quick Reference (Security Hub); always-do-cross-service.md §5 | M5 |

## Source Bibliography

All read 2026-10-23.

1. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/xray_sampling_rule.html.markdown
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/xray_group.html.markdown
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/xray_encryption_config.html.markdown
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
6. https://docs.aws.amazon.com/xray/latest/devguide/xray-console-sampling.html
7. https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-migration.html
8. https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-daemon-timeline.html
9. https://docs.aws.amazon.com/xray/latest/api/API_SamplingRule.html
10. https://docs.aws.amazon.com/general/latest/gr/xray.html
11. https://docs.aws.amazon.com/xray/latest/devguide/xray-api-configuration.html
12. https://docs.aws.amazon.com/step-functions/latest/dg/concepts-xray-tracing.html
13. https://docs.aws.amazon.com/xray/latest/devguide/xray-console-groups.html
14. https://docs.aws.amazon.com/xray/latest/devguide/security_iam_id-based-policy-examples.html
15. https://docs.aws.amazon.com/xray/latest/devguide/xray-console-encryption.html
16. https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html
17. https://docs.aws.amazon.com/xray/latest/devguide/xray-services-apigateway.html
18. https://docs.aws.amazon.com/securityhub/latest/userguide/securityhub-controls-reference.html
19. https://releases.hashicorp.com/terraform/ ; https://releases.hashicorp.com/terraform-provider-aws/
20. https://raw.githubusercontent.com/hashicorp/terraform/v1.17/CHANGELOG.md (read 2026-10-22)
21. https://developer.hashicorp.com/terraform/language/backend/s3 ; https://developer.hashicorp.com/terraform/language/expressions/version-constraints
22. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown
