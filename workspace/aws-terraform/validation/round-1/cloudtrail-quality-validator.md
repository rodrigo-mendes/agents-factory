# Quality validation — provisioning-aws-cloudtrail-v6 (round 1)

Date: 2026-10-23. Target: `packages/aws-terraform/.apm/skills/provisioning-aws-cloudtrail-v6/` (9 files). Rubric: hybrid-format-checklist, tag-notation-and-registers, evidence-rule, skill-frontmatter. Research: `research_AWS_CloudTrail_tf-aws-v6.md`; facts `_family_facts_v6.md`. No sources were re-fetched (WebFetch not used); grounding is judged against the research and facts files plus the validated siblings.

## Verdict

HIGH 0 | MEDIUM 3 | LOW 9. No wrong facts found. Ready to ship after the MEDIUM fixes.

## Format checks

| Check | Result |
|---|---|
| Frontmatter: only name + description, quoted, "Use when", < 300 chars, name = folder | pass (description about 265 chars; name matches folder) |
| SKILL.md length 100-200 | pass (155 lines) |
| Blueprint files <= 160 lines | pass (largest always-do-trail.md = 160, at the limit) |
| Required blueprints (always-do/never-do patterns, topics, unverified-and-risks, evaluation-scenarios) | pass |
| Links and anchors (checked by hand for all index and Quick Navigation anchors) | pass |
| No absolute paths, `.github/`, relative dates, F#/M# internal ids in shipped text (grep) | pass |
| Tag notation plain parentheses | pass |
| Tag to register mapping covers every tag in text | pass (9 rows; every tag occurrence has a row) |

## Known-risk verdicts

| Risk | Verdict |
|---|---|
| (a) `aws_s3_bucket_public_access_block` args (4 booleans, `bucket`) | grounded-by-sibling: provisioning-aws-s3-v6 always-do-bucket-foundation.md section 3 (cites the provider page). Not sourced in this skill. LOW-1 |
| (a) `aws_s3_bucket_logging` `target_bucket`/`target_prefix` | grounded-by-sibling: s3 always-do-security-encryption.md section 7 (cites the provider page). LOW-1 |
| (a) `aws_s3_bucket` `bucket` | grounded-by-sibling: s3 always-do-bucket-foundation.md line 39. LOW-1 |
| (a) `aws_cloudwatch_log_group` `name` | grounded-by-sibling: cloudwatch always-do-alarms.md line 70 (`/aws/cloudtrail/management`), always-do-foundation.md line 52. LOW-1 |
| (a) `aws_iam_policy_document` statement/principals/condition syntax | grounded-by-sibling: s3 always-do-security-encryption.md lines 47-70 and 87-107 |
| (a) `mock_provider "aws" {}` | grounded by `_family_facts_v6.md` F10 and siblings s3 (always-do-objects-testing.md line 48) and cloudwatch (always-do-security.md line 96) |
| (b) No default log encryption asserted | pass. SKILL.md line 103 and never-do-trail section 3 name the disagreement and assert neither default; eval scenario 3 enforces it |
| (c) Retention 2555 per provider page, tagged | pass. Tagged (medium confidence) at SKILL.md lines 91 and 125 and kms-lake line 98; mapped to M2. See LOW-4 |
| (d) No HCL for `aws_cloudtrail_channel` | pass. Only never-do prose and Ask First; no resource block |
| (e) Service-principal `kms:Decrypt` with `aws:SourceArn` | confirmed in research section 10 ("[8] documents both"). Research section 5 states only that the principal gets `kms:Decrypt` and does not mention the condition. See LOW-6 |
| (f) Delegated admin is global, no `region` | pass in SKILL.md lines 20, 79, 107, 127 and kms-lake section 6. Consistent with F14 and research [4] |
| (g) Never mixing selector types | pass. The only mix is the labelled WRONG block (never-do-trail lines 11-24); the correct blocks use `advanced_event_selector` alone |
| (h) Tags vs register | no orphan tags; one register row without a tag (U3, LOW-5). No F#/M# ids in text. Research section 10 legacy claims not reproduced as fact (the "destructive basic-to-advanced" claim is absent, consistent with U3) |
| Eval file: 5 scenarios judgeable | pass. Each has concrete, checkable must_pass/must_not. Scenario 4's "cites docs" criterion is soft but judgeable |

## Grounding sample (36 claims)

| # | Claim (location) | Result |
|---|---|---|
| 1 | Trail required args name, s3_bucket_name (SKILL 122) | grounded, research s3 |
| 2 | Trail defaults (SKILL 123) | grounded, research s3 |
| 3 | `kms_key_id` always; CT.2 fails if KmsKeyId undefined (SKILL 47) | grounded, research s9 |
| 4 | `is_multi_region_trail` default false; CT.1 (SKILL 49) | grounded; the CT.1 half is cited to the provider URL (LOW-2) |
| 5 | `enable_log_file_validation` default false (SKILL 51) | grounded; recommendation rests on CT.4 and AWS best practice, which the bullet does not cite (LOW-2) |
| 6 | `:*` suffix (SKILL 53, never-do 2) | grounded, research s3 |
| 7 | depends_on bucket policy (SKILL 55) | grounded, research s3 |
| 8 | aws:SourceArn best practice (SKILL 57) | grounded, research s4 |
| 9 | Prefix must match `s3_key_prefix` (SKILL 59) | grounded, research s4 |
| 10 | Four BPA settings, CT.6 Critical (SKILL 61) | grounded, research s9 |
| 11 | Access logging CT.7 (SKILL 63) | grounded, research s9 |
| 12 | Key policy encrypt/decrypt/describe (SKILL 65) | grounded, research s5 |
| 13 | CT.9 requiredTagKeys (SKILL 67) | grounded, research s9 |
| 14 | Org trail management account only (SKILL 69) | grounded, research s3 |
| 15 | EDS KMS key cannot be removed or changed (SKILL 71, never-do 6) | grounded, research s6 [10] |
| 16 | EDS key-policy conditions after creation (SKILL 73) | grounded, research s5 |
| 17 | `.region` replaces `.name` (SKILL 75) | grounded, F15 and research s2 |
| 18 | `use_lockfile`; dynamodb_table deprecated (SKILL 77, 111) | grounded, F7 |
| 19 | Delegated admin global (SKILL 79) | grounded, F14 |
| 20 | mock_provider with command = plan (SKILL 81) | grounded, F10 |
| 21 | Ask First selector types (SKILL 88) | grounded, research s3 |
| 22 | Org trail extra statement on `AWSLogs/<o-organizationID>/*` (SKILL 89) | grounded, research s4 |
| 23 | Lake closed to new customers 2026-05-31 (SKILL 21, 90) | grounded, research s1 and s6 |
| 24 | Retention 2555 and billing_mode values (SKILL 91) | grounded; default vs maximum wording copied from research, tagged |
| 25 | Termination protection default true (SKILL 92) | grounded, research s6 |
| 26 | Insight types (SKILL 93) | grounded, research s3 |
| 27 | `sns_topic_name` ARN if cross-region (SKILL 94) | grounded, research s3 |
| 28 | `suspend` 0/1 rejected (SKILL 109) | grounded, research s2 |
| 29 | Withdrawn 6.57.0 (SKILL 112, 18) | grounded, F4 |
| 30 | Timeouts 5m, EDS import ARN (SKILL 126) | grounded, research s6 |
| 31 | `identity { arn }` needs >= 1.12 (SKILL 131) | grounded, F11 |
| 32 | Trail HCL comments (always-do-trail 123-126) | grounded, research s3 |
| 33 | KMS HCL statements, including EncryptionContext and Null conditions (kms-lake 12-80) | grounded, research s5 and s10 |
| 34 | AES256 bucket-policy snippet (always-do-trail 111-113) | grounded, research s4 [9] |
| 35 | CI exit codes (kms-lake 157) | grounded, F9 |
| 36 | "default selectors (management events)" (always-do-trail 152) | partly grounded, MEDIUM-2 |

Not in the research: the advanced selector values `Data` and `AWS::S3::Object` (MEDIUM-3), the `insight_selector` in the canonical trail (MEDIUM-1), and the "30 days" re-verify interval (LOW-7).

## Findings

### HIGH

None.

### MEDIUM

- MEDIUM-1: always-do-trail.md lines 135-137 enable `insight_selector { ApiCallRateInsight }` in the canonical hardened trail. SKILL.md line 93 makes Insights an Ask First decision. The research gives no basis for enabling it by default, and the trail adds a feature the user never asked for. Fix: remove the block from the canonical HCL and keep it as an Ask First option, or comment it as optional.
- MEDIUM-2: always-do-trail.md lines 152-153 say that with no selectors the trail "uses the default selectors (management events)". Research section 3 does not state the trail default; only section 9 mentions "default selectors" for CT.1. Fix: reword to "default selectors (see Security Hub CloudTrail.1)", or tag it (medium confidence) and map it to a register row.
- MEDIUM-3: never-do-trail.md lines 32-41 (CORRECT block) use `field = "eventCategory"` with `equals = ["Data"]` and `resources.type` with `AWS::S3::Object`. The research documents the field names and the `equals` rule, but not the value `Data`. It lists `AWS::S3::Object` only for `event_selector` `data_resource`. Fix: add a source, tag the values, or drop the `eventCategory` selector and use only documented fields.

### LOW

- LOW-1: The S3, logging, log group, IAM policy document and mock_provider HCL in always-do-trail.md (lines 40-102, 145-147) and kms-lake.md (line 140) is grounded only by sibling skills, and the file's Source comments cite only AWS pages. Fix: add `# Source:` lines with the provider page URLs the siblings use, or a pointer such as "argument names: see provisioning-aws-s3-v6".
- LOW-2: SKILL.md lines 49 and 51 each combine a provider-page default with a Security Hub or AWS recommendation, but cite only the provider URL. The Always Do rule is one claim and one URL per bullet. Fix: cite the Security Hub page for CT.1 and CT.4, or drop the second claim.
- LOW-3: Never Do rows at SKILL.md lines 103 and 106 are tagged (medium confidence) and (unverified). The evidence rule says Never Do holds High rows only. Fix: keep them in Ask First (the channel row already exists, and a default-encryption Ask First row could be added), or accept the exception explicitly.
- LOW-4: SKILL.md line 91 and line 125 call 2555 the "default" and the "provider page maximum" in one phrase. Research section 6 also lists both. Fix: state the default and the documented maximum as separate facts.
- LOW-5: unverified-and-risks.md line 24 lists U3, but no tag in the skill refers to it and the mapping table has no row for it. Fix: add a one-line note that the skill makes no claim, or drop U3 if no tag will use it.
- LOW-6: kms-lake.md lines 59-64 and 75-79 put `aws:SourceArn` on the service-principal `kms:Decrypt` and on `kms:DescribeKey`. The support is research section 10 only (section 5 omits the condition on Decrypt). Fix: cite section-10-equivalent text from the AWS key-policy page, which the research marks as documenting both.
- LOW-7: unverified-and-risks.md line 8 says "Re-verify ... after 30 days". The interval has no source. Fix: use "when starting new work".
- LOW-8: SKILL.md line 104 says "Never write a bucket policy without `aws:SourceArn`". Research section 4 says `aws:SourceArn` is a best practice and that `aws:SourceAccount` is a documented alternative in the troubleshooting section. Fix: soften to "prefer `aws:SourceArn`", or keep the Never Do row and add the alternative.
- LOW-9: Illustrative HCL is not self-contained. The variables `access_log_bucket_id`, `trail_kms_key_arn`, `cwl_delivery_role_arn`, `log_reader_principal_arns`, `eds_kms_key_arn` and `delegated_account_id` are never declared. The test at kms-lake.md lines 138-155 would prompt for them. The trail-key statements data source is never attached to a key. Also, the register column header says "Tag text" where the spec says "Tag text used in the skill" (unverified-and-risks.md line 45). Fix: add a note that the variables are placeholders, add `variables {}` to the test, and rename the column.
