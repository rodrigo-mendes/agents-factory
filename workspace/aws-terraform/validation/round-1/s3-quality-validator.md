# Quality validation, round 1: provisioning-aws-s3-v6

Target: `packages/aws-terraform/.apm/skills/provisioning-aws-s3-v6/` (SKILL.md plus 12 blueprints).
Date: 2026-10-14. Validator: quality-validator. Method: static read only. `verify_skill.py` was not run because no shell was available. The anchor, link, line-count and regex checks were done manually with Read and Grep.

Counts: HIGH 2, MEDIUM 9, LOW 8.

## 1. Hybrid-format checklist

| Item | Result |
|---|---|
| Frontmatter has only `name` and `description` | pass |
| `name` equals the folder name | pass |
| Description is quoted, contains "Use when", and is under 300 chars | pass: about 296 chars by hand count, margin is very thin |
| SKILL.md is 100-200 lines | pass: 160 lines |
| Version Context table with Source column | pass |
| Quick Navigation | pass |
| Blueprints & Guardrails with Always / Ask First / Never | pass |
| Quick Reference | pass |
| Required blueprints exist: `always-do-patterns`, `never-do-patterns`, topic blueprints, `unverified-and-risks`, `evaluation-scenarios` | pass |
| Each blueprint is 160 lines or fewer | pass: max 133 (`never-do-resource-conflicts.md`) |
| All 28 internal anchors and links resolve | pass: checked each heading slug |
| No `.github/` and no relative dates | pass |
| No absolute paths | FAIL, see M-1 |
| No BOM | not verifiable without a shell |
| Notation: plain `(unverified)` and `(medium confidence)` | FAIL, see M-2 |
| Register has sections U, I, M, L, Tag to register mapping, Source Bibliography | partial: no I section (see L-5) |
| Mapping table has columns `Tag text used in the skill`, `Where`, `Register id` | FAIL: columns are named `Tag text`, `Where`, `Register id` (L-5) |

## 2. Fact fidelity (33 claims sampled against the research)

Confirmed against the research (27):
1. Terraform 1.16.6, 1.17.0-rc2 pre-release, `~> 1.16`.
2. aws 6.69.0, `~> 6.69`, no 7.x released.
3. 6.57.0 withdrawn.
4. `bucket_namespace` added in 6.37.0.
5. `expected_bucket_owner` deprecated and dropped from identity in 6.31.0.
6. `blocked_encryption_types` is Optional+Computed since 6.40.0.
7. `blocked_encryption_types` is not supported in the inline SSE block.
8. Inline arguments were not removed in 6.0.
9. `bucket_region` replaces `region` for reading the home region.
10. `s3_us_east_1_regional_endpoint` is deprecated and will be removed in v7.
11. Account-regional naming `<prefix>-<12-digit-account-id>-<region>-an`, with the suffix counting toward the 63-char limit.
12. Account-regional is not available in me-south-1 or me-central-1.
13. Public access block booleans all default `false`.
14. The account-level resource allows one per account and applies to all Regions.
15. `use_lockfile = true`, with `dynamodb_table` deprecated.
16. BucketOwnerEnforced is the default for new buckets.
17. Lifecycle `transition_default_minimum_object_size` defaults to `all_storage_classes_128K`.
18. Single lifecycle, policy, notification and CORS resource per bucket.
19. `source_hash` is state-only, and `etag` is incompatible with KMS and multipart uploads over 16 MB.
20. About 15 min wait after enabling versioning.
21. The 6.48.0 `mfa_delete` drift fix.
22. The 6.62.0 account public access block eventual-consistency fix.
23. Security Hub S3.1 Medium, S3.2 and S3.3 Critical, S3.5 Medium, S3.8 High, S3.9 Medium, S3.10 Medium, S3.13 Low, S3.14 Low. S3.17 is KMS-only. S3.20 is the MFA delete control.
24. `mfa_delete` conflicts with a lifecycle configuration, and only root can enable it.
25. SSE-C is blocked since April 2026, with the Bahrain and UAE exception.
26. Logging target must be same-Region with no default Object Lock retention (S3.9).
27. Object-tag limit of 10, with the `override_provider` workaround.

Not in the research, or contradicting it:
- **H-1**: `SKILL.md:102` gives the corrected `bucket` expression with `data.aws_region.current.name`, the deprecated attribute (F15). The research and the other blueprints use `.region`. This is outside a `# WRONG` block. It contradicts SKILL.md:106, SKILL.md:122 and Scenario 2 `must_not`.
- **H-2**: `always-do-bucket-foundation.md:55-56` says "Do not use `bucket_regional_domain_name` for CloudFront origins ... Use it only for origin references". This is self-contradictory. The research §3 and `SKILL.md:130` say to use `bucket_regional_domain_name` for CloudFront origins.
- **M-3**: `SKILL.md:88` says "Priority required when multiple rules share a filter". The research says priority is required for multiple destinations (and pairs with `filter`). The claim is also not tagged.
- **M-4**: `SKILL.md:88` says "CRR or SRR both require versioning". SRR is not in the research. The research says only that versioning must be enabled on source and destination.
- **M-5**: `SKILL.md:89` says COMPLIANCE means "no one (not even root) can shorten" and GOVERNANCE is bypassed with `s3:BypassGovernanceRetention`. Neither statement is in the research. The cited Terraform page (research [19]) gives only `mode = COMPLIANCE|GOVERNANCE`. This is a High-confidence-style claim without evidence in the dossier.
- **M-6**: "`bucket_key_enabled` reduces KMS API calls" is stated as fact in `SKILL.md:67`, `SKILL.md:124`, `always-do-security-encryption.md:8` and `:21`. The research says only "S3 Bucket Keys for SSE-KMS", and U2 covers the cost figure. The behavioral claim is unsourced and sits inside an Always Do bullet, which should be High only (evidence-rule).
- **M-7**: Version-lifetime risk (`SKILL.md:28`, `unverified-and-risks.md:11-12`) says 6.57.0 "will fail `terraform init`" and that a pin "that includes it" fails. This is not in the research (F4 says only "withdrawn, never pin"). `~> 6.69` does not even include 6.57.0.
- **L-1**: `SKILL.md:29` says "breaking changes documented in the v6 upgrade guide". The research says the guide lists items "removed in v7.0.0". Rewording is needed.
- **L-2**: `SKILL.md:101` and `never-do-ownership-acl.md:39` alternative "use bucket policy or SCPs for cross-account enforcement" is not in the research.
- **L-3**: `always-do-objects-testing.md:8` and `never-do-resource-conflicts.md:87` say `etag` "will cause perpetual drift". The research says only "not compatible with KMS / not MD5 for multipart". The drift symptom is inferred.
- **L-4**: `always-do-lifecycle-versioning.md:8` says deprecated rule-level `prefix` "(V1) conflicts with `filter`". The research says that conflict only for replication V1 `prefix`. For lifecycle it says only "deprecated, use `filter`".
- Minor: "SSE-S3 ... no extra cost" (`SKILL.md:86`) and `terraform providers lock -platform=...` (`always-do-objects-testing.md:100`) are not in the research or the family facts.

## 3. HCL correctness

- Arguments checked against the research: no removed or deprecated argument appears outside a `# WRONG` block. The deprecated `versioning`, `server_side_encryption_configuration` and `expected_bucket_owner` appear only in WRONG blocks.
- No `;`-separated HCL (grep clean). The one-line `{ source = ..., version = ... }` forms use commas.
- **M-8**: `always-do-objects-testing.md:61` asserts `aws_s3_bucket_server_side_encryption_configuration.main.rule[0].bucket_key_enabled`. The research does not say whether `rule` is a list or a set. I recall the provider schema as a set with `MaxItems = 1`, which cannot be indexed with `[0]`. In that case the test fails with an invalid-index error. The test should be verified against the provider schema before the skill is marked VERIFIED. As a safer pattern, use `one(...rule)` or assert on `tolist(...)[0]`.
- **M-9**: `always-do-objects-testing.md:39` pairs `content` with `source_hash = sha256(...)`. The research documents `source_hash` only as the `etag` replacement for `source` files, with no pairing with `content` and no hash algorithm. This is unsupported and may be a no-op.
- **M-10**: `always-do-patterns` and the description advertise replication, notifications and object lock, but no HCL pattern exists for them. They appear only as Ask First rows. Either narrow the description or add blueprints. The research covers them fully (§4).
- `.tftest.hcl` structure is valid: `mock_provider "aws" {}`, `run` with `command = plan`, and `assert { condition error_message }`. The `terraform test -filter=` flag is valid.
- L-6: `terraform fmt` alignment is off in `always-do-lifecycle-versioning.md:36-37` (`noncurrent_days` and `newer_noncurrent_versions`) and `:102-104` (the `aws_s3_object` arguments). `fmt -check` would flag them.
- L-7: Snippets reference `aws_kms_key.s3`, `aws_s3_bucket.access_logs` and `var.prefix` without defining them. This is acceptable for patterns, but they should be noted as placeholders.

## 4. Tag and register consistency

- **M-2**: `SKILL.md:124` uses the non-standard form `(unverified cost figure — U2)`. `SKILL.md:102` uses a bare `(M3)` instead of `(medium confidence)`. `unverified-and-risks.md:34` uses `(medium confidence — now F15)`. All three break the plain-parenthesis rule that the same tag text appears in SKILL.md, blueprints and register.
- **M-11**: `unverified-and-risks.md:48-54` (Tag to Register Mapping) is inconsistent:
  - Row 1 maps a non-existent `(unverified)` tag at SKILL.md `.name`. The text says "Now resolved", so it is not a real register id.
  - Row 2 maps a non-existent tag on the `force_destroy` comment and says "No unverified tag".
  - Row 4 refers to a `(medium confidence)` tag in `never-do-naming-endpoints.md` §1 that does not exist. That section says "per F15".
  - Row 5 maps `(unverified)` to "U1-U5 above" rather than to a single id.
  - The real tag at `SKILL.md:124` has no row, and `SKILL.md:102` is not mapped correctly.
- M3 is carried as "medium confidence" while being "confirmed via F15". In the research it is open. Either keep it as M3 (medium confidence) in the text, or drop M3 and note the F15 resolution in the research mapping. Do not carry both.
- U1, U3, U5, M1 and M4 live only in the register and are never used in text. U4 (`newer_noncurrent_versions`, `always-do-lifecycle-versioning.md:37`) and M2 (`existing_object_replication`, `SKILL.md:88`) are used in text without a tag. U4 and M2 should be tagged in place (L-8).
- IDs are well-formed (U1-U5, M1-M4, L1-L4). Counts are consistent with the listed items. The register has no explicit counts in headers, so there is nothing to mismatch.

## 5. Scenarios

Four scenarios: canonical, edge, misuse rejection, anti-pattern trap. All use `must_pass` and `must_not`, and all are judgeable. Notes:
- Scenario 2 `must_pass` ("63-char suffix constraint") is only in `never-do-naming-endpoints.md`. It is not in SKILL.md, so the judge may not see it if only SKILL.md is loaded. This is cosmetic (L).
- Scenario 3 "Recommends lifecycle rules as the practical choice" is not backed by the research. It is subjective for a judge.
- The scenario set does not exercise any of the Ask First topics (replication, object lock, SSE choice).

## 6. Legacy-claims list (research §6)

Not reproduced: confirmed by grep for acme, 99%, `;`, `>= 1.7`, `~> 6.0` in constraints, and "v6.x". The old naming pattern and the `mfa_delete` plus lifecycle suggestion appear only as rejections. `~> 6.0` appears only in the migration recipe (upgrade path), as the research §2 states. This criterion passes.

## 7. Other findings

- **M-1**: `unverified-and-risks.md:60` bibliography entry 1 is the absolute Windows path `c:\agents\agents-factory\workspace\aws-terraform\_family_facts_v6.md`. This violates the "no absolute paths" rule, and the reference `provisioning-aws-vpc-v6` has none. Replace it with a non-path label such as "family facts v6 (F1-F15), verified by orchestrator".
- L-5: Register lacks an `Irresolvable (I1..)` section and the mapping header text differs from the policy. Add an empty or explicit "none" I section if the policy requires it.
- L-8: `provisioning-aws-cloudfront-v6` (named in the description as a redirect target) does not exist under `packages/aws-terraform/.apm/skills/`. `provisioning-aws-kms-v6` exists. Confirm the CloudFront skill is planned for this family before release.
- Evidence-rule: several Always Do bullets contain caveats inside the bullet. Examples: SKILL.md:71 (same-Region and no Object Lock caveat) and :75 (the ~15 min note). These should move to Ask First or blueprints (informational).

## HIGH list

1. H-1: `SKILL.md:102`, deprecated `data.aws_region.current.name` in the corrected expression of the naming Never Do row. Use `.region`.
2. H-2: `always-do-bucket-foundation.md:55-56`, a contradictory instruction on `bucket_regional_domain_name` for CloudFront origins. The research says to use it.

Recommended first fixes: H-1, H-2, M-1, M-2 and M-11 (mapping), then the tests (M-8, M-9) and the description scope (M-10).
