# Unverified Claims and Risks — hashicorp/aws 6.x SNS

Research date 2026-10-23. See SKILL.md for inline source URLs per claim.

## Version-lifetime risk

- **hashicorp/aws 6.x is the current stable major** as of 2026-10-23 (latest 6.70.0; constraint `~> 6.69`).
  Re-verify when starting new work. Source: https://releases.hashicorp.com/terraform-provider-aws/
- **Terraform 1.17.0 is stable since 2026-10-21** and is not the target of this skill (`~> 1.16`, reference
  patch 1.16.6). Re-verify before moving the constraint. Source: https://releases.hashicorp.com/terraform/
- **6.57.0 is withdrawn** from GitHub and the Registry — never pin it.
- **v7 is planned**, not released. When it ships, create a new skill `provisioning-aws-sns-v7`.

## Unverified Items

| Tag | Item | Status |
|---|---|---|
| U1 | Whether `fifo_topic` / `name` changes force replacement in Terraform (AWS says no conversion is possible; provider page silent) | (unverified) — plan and review before apply |
| U2 | Numeric FIFO/standard throughput quotas (SNS quotas page not fetched) | (unverified) — check the SNS quotas page |
| U3 | Required permissions of the Firehose `subscription_role_arn` role | (unverified) — check the SNS Firehose subscriber page |
| U4 | Inline `policy` on `aws_sns_topic` vs `aws_sns_topic_policy` conflict — inferred; neither provider page has a do-not-mix note | (unverified) — Ask First |
| U5 | `aws:SourceArn`/`aws:SourceAccount` on the topic policy — documented explicitly only for KMS key policies; the guidance page was not fetched | (unverified) — Ask First |
| U6 | How Terraform handles `archive_policy = jsonencode({})` (AWS: `{}` disables the policy and deletes the archive) | (unverified) — Ask First; review the plan |

## Medium-Confidence Items

| Tag | Item | Status |
|---|---|---|
| M1 | `AuthenticateOnUnsubscribe` — the subscription page documents no argument for it (absence of evidence) | (medium confidence, absence of evidence) — Ask First |

## Coverage Limits

| Tag | Item |
|---|---|
| L1 | CHANGELOG 6.55.0 read only in two partial windows (no SNS hit) |
| L2 | `aws_sns_platform_application` and `data.aws_sns_topic` are out of scope |
| L3 | Subscription filter-policy syntax pages were not fetched |

## Tag to Register Mapping

| Tag text | Where | Register id |
|---|---|---|
| (unverified) | SKILL.md Ask First, row "FIFO vs standard topic changes" | U1 |
| (unverified) | SKILL.md Ask First, row "`fifo_throughput_scope = "MessageGroup"`" — numeric quotas | U2 |
| (unverified) | always-do-access-delivery.md §9 Firehose and HTTPS Subscriptions — role permissions | U3 |
| (unverified) | SKILL.md Ask First, row "Inline `policy` on `aws_sns_topic` vs `aws_sns_topic_policy`" | U4 |
| (unverified) | SKILL.md Ask First, row "`aws:SourceArn`/`aws:SourceAccount` in the topic policy" | U5 |
| (unverified) | SKILL.md Ask First, row "Deactivating an archive with `archive_policy = jsonencode({})`" | U6 |
| (medium confidence, absence of evidence) | SKILL.md Ask First, row "`AuthenticateOnUnsubscribe=true`" | M1 |

## Source Bibliography

All fetched 2026-10-23.

1. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic.html.markdown
2. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic_subscription.html.markdown
3. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic_policy.html.markdown
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_topic_data_protection_policy.html.markdown
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sns_sms_preferences.html.markdown
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
7. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
8. https://docs.aws.amazon.com/sns/latest/dg/fifo-topic-code-examples.html
9. https://docs.aws.amazon.com/sns/latest/dg/fifo-message-delivery.html
10. https://docs.aws.amazon.com/sns/latest/dg/fifo-high-throughput.html
11. https://docs.aws.amazon.com/sns/latest/dg/message-archiving-and-replay-topic-owner.html
12. https://docs.aws.amazon.com/sns/latest/dg/sns-key-management.html
13. https://docs.aws.amazon.com/securityhub/latest/userguide/sns-controls.html
14. https://docs.aws.amazon.com/sns/latest/dg/sns-dead-letter-queues.html
15. https://docs.aws.amazon.com/sns/latest/dg/sns-firehose-as-subscriber.html
16. https://docs.aws.amazon.com/sns/latest/dg/sns-security-best-practices.html
17. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown
18. https://releases.hashicorp.com/terraform/ and https://releases.hashicorp.com/terraform-provider-aws/
19. https://developer.hashicorp.com/terraform/language/expressions/version-constraints
