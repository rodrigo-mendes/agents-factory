# Evaluation Report: provisioning-aws-cloudtrail-v6 (round 1)

Method: no sub-agents. Each response was written by the evaluator using only SKILL.md and the linked blueprints (always-do-trail, always-do-kms-lake, never-do-trail, never-do-provider-migration, unverified-and-risks). Then each criterion was judged.

## Summary

| Scenario | must_pass | must_not OK | Verdict |
|---|---|---|---|
| 1 Hardened multi-region trail | 8/8 | 4/4 | PASS |
| 2 Org trail + delegated admin | 5/5 | 2/2 | PASS |
| 3 Channel + default encryption | 3/3 | 3/3 | PASS |
| 4 Flawed snippet review | 5/5 | 3/3 | PASS |
| 5 Lake EDS retention + key | 4/4 | 3/3 | PASS |

Overall: 5/5 scenarios PASS (25/25 must_pass, 15/15 must_not OK).

## Evidence per scenario

**S1.** always-do-trail.md covers each criterion.
- Section 1: `required_version = "~> 1.16"`, `version = "~> 6.69"`, `data.aws_region.current.region`, and a backend with `use_lockfile = true`.
- Section 3: `is_multi_region_trail = true`, `enable_log_file_validation = true`, `kms_key_id = var.trail_kms_key_arn`, `cloud_watch_logs_group_arn = "${...arn}:*"`, and `depends_on = [aws_s3_bucket_policy.trail]`.
- Section 2: `GetBucketAcl` and `PutObject` statements for `cloudtrail.amazonaws.com`, both with `aws:SourceArn = local.trail_arn`, plus a public access block with all four settings.
- must_not: none violated. The response uses no `.name`, no `dynamodb_table`, and no selector blocks.

**S2.**
- always-do-trail.md section 2 and the SKILL.md Always Do list say "creatable only in the organization's management account".
- Section 2 says to "add a third `s3:PutObject` statement on `.../AWSLogs/<o-organizationID>/*`", keep the account-level statement, and use a `aws:SourceArn` "owned by the management account".
- always-do-kms-lake.md section 6 gives `account_id` with no `region`, and says "Global resource: no `region` argument and no `@region` import (import by account ID only)".
- must_not: none violated.

**S3.**
- never-do-trail.md section 5 and the SKILL.md Never Do table: no provider doc page (HTTP 404), existence in 6.x is (unverified), no HCL, so the response asks the user how they integrate with Lake.
- Section 3 and M3: "Two AWS pages disagree... Do not assert either; set `kms_key_id`".
- The response may name which page says what, but must not present either as the default.
- must_not: none violated.

**S4.**
- Selector mixing: never-do-trail.md section 1, "use only one".
- Log group ARN: section 2, corrected to `"${...arn}:*"`.
- `suspend = 1`: never-do-provider-migration.md section 2, only `""`, `true` or `false`.
- Missing SourceArn: never-do-trail.md section 4, trail ARN condition.
- Citations: each section carries a `# Source:` line.
- must_not: none violated.

**S5.**
- Lake closed since 2026-05-31: SKILL.md Ask First and always-do-kms-lake.md section 5. The response asks "Is this account already onboarded to CloudTrail Lake?"
- `retention_period = 2555  # provider page maximum (medium confidence)`.
- `kms_key_id` is set, with "cannot be removed or changed once associated".
- Key-policy conditions: "Add these conditions after the store is created", using `aws:SourceAccount` and `aws:SourceArn` with the store ID.
- must_not: none violated.

## Ambiguities and criterion issues

1. **S5 must_pass 2 ("tags it (medium confidence) because AWS states different maximums").** The SKILL.md and blueprint inline tags carry only "(medium confidence)". The reason (AWS Lake page says 3,653 or 2,557 days) lives only in unverified-and-risks.md M2. A response that follows the skill faithfully must read that file to give the reason. That is traceable, but easy to miss.
2. **S5 must_not "State 3653 as the provider maximum".** The response mentions 3,653 as an AWS-stated figure, which M2 supports. A strict judge might misread this as a violation, so the criterion should say "as the provider maximum or as the value to set".
3. **S2 query "where can I create these?".** The skill states where the trail can be created (management account only). For the delegated admin it says only "Organizations setup belongs to provisioning-aws-organizations-v6" and does not say which account creates it. No must_pass requires this, so there is no criterion bug. It is a minor skill gap for the query.
4. **S2 "third s3:PutObject statement".** The base policy has one GetBucketAcl and one PutObject statement, so the org statement is the third statement overall but the second PutObject. The wording matches the skill text ("third `s3:PutObject` statement"), but it is slightly imprecise.

## Fixes needed (all optional, none block a pass)

- evaluation-scenarios.md S5: reword the 3653 must_not as above, and either drop "because AWS states different maximums" or note that M2 in unverified-and-risks.md is the source for it.
- SKILL.md or always-do-kms-lake.md section 6: add one sentence on which account creates the delegated admin, with a source, or mark it (unverified).
- always-do-trail.md section 2: say "third statement, second `s3:PutObject`" for clarity.
