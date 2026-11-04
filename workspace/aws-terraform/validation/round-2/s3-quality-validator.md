# Quality validation, round 2: provisioning-aws-s3-v6

Target: `packages/aws-terraform/.apm/skills/provisioning-aws-s3-v6/` (SKILL.md plus 12 blueprints).
Date: 2026-10-14. Validator: quality-validator. Method: static read plus Grep/Glob. No shell was available, so `terraform fmt`, `terraform validate` and `verify_skill.py` were not run. Format and HCL validity were judged by reading.

Counts (open findings after round 2): HIGH 0, MEDIUM 6, LOW 16 (14 new, 2 carried from round 1).
Round-1 status: 19 of 21 items FIXED, 2 NOT FIXED (both LOW), plus 1 PARTIAL (M-7, residual tracked as N-M1 below). Zero regressions.

Structural re-checks: description is about 285 chars (under 300). SKILL.md is 161 lines. The largest blueprint is `never-do-resource-conflicts.md` at 133 lines. All 28 internal anchors resolve. No absolute paths (grep for a drive-letter path returned 0). No `.github/`.

## 1. Round-1 findings, one by one

| ID | Status | Evidence |
|---|---|---|
| H-1 | FIXED | `SKILL.md:102` now uses `data.aws_region.current.region`. `never-do-naming-endpoints.md:23` also uses `.region`. The only `.name` hits are the WRONG block (`never-do-provider-migration.md:58`), the Never Do row (`SKILL.md:106`) and the scenario `must_not`. |
| H-2 | FIXED | `always-do-bucket-foundation.md:55-57` now says use `bucket_regional_domain_name` (not deprecated `bucket_domain_name`) for CloudFront origins. This matches research §3 and `SKILL.md:130`. |
| M-1 | FIXED | `unverified-and-risks.md:65` is now "F1–F15 (aws-terraform family facts, verified by the orchestrator)". No path. |
| M-2 | FIXED | All tags are plain `(unverified)` or `(medium confidence)`. The grep shows only these forms (`SKILL.md:86,88,89,124`, `always-do-lifecycle-versioning.md:37`, `always-do-security-encryption.md:8,21`). The "(M3)", "(unverified cost figure — U2)" and "now F15" variants are gone. |
| M-3 | FIXED | `SKILL.md:88`: "`priority` (unique) is required for multiple destinations". This matches research §4 replication. |
| M-4 | FIXED | `SKILL.md:88` now says only "Versioning must be enabled on source and destination first". There is no SRR claim. |
| M-5 | FIXED | `SKILL.md:89` states only what the research supports (`mode`, exactly one of `days`/`years`, versioning side effects). The mode semantics are tagged `(unverified)` and mapped to U6 (`unverified-and-risks.md:27,53`). The COMPLIANCE and `BypassGovernanceRetention` text is gone. |
| M-6 | FIXED | The "reduces KMS API calls" claim is gone from `SKILL.md:67,86,124` and `always-do-security-encryption.md:8,21`. It now reads "turns on S3 Bucket Keys for SSE-KMS; cost effect (unverified)", mapped to U2. |
| M-7 | PARTIAL (NOT FIXED in one place) | `SKILL.md:28` and `unverified-and-risks.md:11-12` are fixed ("effect on init is not stated in the research"). The same unsupported claim survives at `never-do-provider-migration.md:99`: "A constraint resolving to it fails `terraform init`". See N-M1. |
| M-8 | FIXED | `always-do-objects-testing.md:50-69` asserts only top-level booleans of `aws_s3_bucket_public_access_block.main`. There is no `rule[0]` index. All of these are documented in research §4. |
| M-9 | FIXED | The `content` + `source_hash` pairing is gone. `always-do-objects-testing.md:34-38` uses `content` alone. `source_hash` appears only with `source` (`:17`, `always-do-lifecycle-versioning.md:103`, `never-do-resource-conflicts.md:104`). |
| M-10 | FIXED | The description (`SKILL.md:3`) lists only ownership, BPA, SSE, TLS policy, versioning, lifecycle, access logging and objects. Replication, notifications and Object Lock are Ask First rows marked "No HCL pattern in this skill" (`SKILL.md:88-89`). |
| M-11 | FIXED | `unverified-and-risks.md:48-55` has 6 rows. Every row maps to a tag that really exists in the text: U2 ×3 (`SKILL.md:86`, `SKILL.md:124`, `always-do-security-encryption.md:8,21`), U6 (`SKILL.md:89`), U4 (`always-do-lifecycle-versioning.md:37`), M2 (`SKILL.md:88`). M3 was closed per F15, with a note at `:57-58`. See section 3 for the full cross-check. |
| L-1 | FIXED | `SKILL.md:29` now quotes the guide as saying "will be removed in v7.0.0" for `s3_us_east_1_regional_endpoint`. |
| L-2 | FIXED | The "bucket policy or SCPs" alternative is gone. `SKILL.md:101` and `never-do-ownership-acl.md:39` now say "remove it". |
| L-3 | FIXED | The "perpetual drift" wording for `etag` is gone. See `always-do-objects-testing.md:8` and `never-do-resource-conflicts.md:86-87`. The one remaining "perpetual drift" hit is the research-backed 6.48.0 `mfa_delete` fix. |
| L-4 | FIXED | `always-do-lifecycle-versioning.md:9` now says only "Rule-level `prefix` is deprecated by S3; use `filter`". The V1-conflict claim is gone. |
| L-5 | NOT FIXED (partial) | The "no I items" statement was added (`unverified-and-risks.md:59`). The mapping header is still `Tag text`, `Where`, `Register id` (`:48`), not `Tag text used in the skill`. There is still no I section heading. |
| L-6 | FIXED (by reading) | Alignment in `always-do-lifecycle-versioning.md:36-37,100-104` is now consistent. A scan of all other attribute groups found no misalignment. This needs a real `terraform fmt -check` to confirm. |
| L-7 | FIXED (minor residual) | Placeholder notes were added for `aws_kms_key.s3` (`always-do-security-encryption.md:28`, `always-do-objects-testing.md:19`) and `aws_s3_bucket.access_logs` (`always-do-security-encryption.md:85`). `var.prefix` is still undeclared. See N-L10. |
| L-8a | FIXED | U4 and M2 are now tagged in place (`always-do-lifecycle-versioning.md:37`, `SKILL.md:88`) and mapped. |
| L-8b | NOT FIXED (accepted) | `provisioning-aws-cloudfront-v6` is still absent from `packages/aws-terraform/.apm/skills/`. Only vpc, kms, cloudwatch, iam and s3 exist. `PIPELINE_STATE.md:44` plans cloudfront in batch B2, so this is a forward reference. It is a dangling link until B2 lands (`SKILL.md:3,45`, `always-do-bucket-foundation.md:56`). |
| Minor: "SSE-S3 no extra cost" | Moved, not removed | Gone from `SKILL.md:86`. It reappears as "lower cost" at `always-do-security-encryption.md:31`. See N-M4. |
| Minor: `terraform providers lock -platform` | FIXED | Not present in the skill. |
| Evidence-rule caveats in Always Do | NOT FIXED (informational) | `SKILL.md:71` (same-Region and Object Lock caveat) and `:75` (~15 min) are still inside Always Do bullets. See N-L11. |

## 2. Fresh fact-fidelity pass (38 claims, none checked in round 1)

Confirmed against the research or F-facts (30):
1. `>= 6.0` for reusable modules, `~> 6.69` for roots (F6, F3). `SKILL.md:55`.
2. Inline-versus-standalone mixing is treated as drift (research §3). `SKILL.md:59,96`.
3. BucketOwnerEnforced disables ACLs, with access via policies (§4, §5). `SKILL.md:61`.
4. The account-level PAB has one per account, with a perpetual diff otherwise (§4). `SKILL.md:65`.
5. `sse_algorithm` can be `AES256`, `aws:kms` or `aws:kms:dsse`. `SKILL.md:67`.
6. TLS enforcement via `aws:SecureTransport` Deny is S3.5 Medium (§5). `SKILL.md:69`.
7. Logging bucket policy for `logging.s3.amazonaws.com` with `aws:SourceAccount` (§4). `always-do-security-encryption.md:98-101`.
8. Omitting `filter` and `prefix` applies the rule to all objects (§4). `SKILL.md:73`.
9. Objects that need a `version_id` must reference or `depends_on` the versioning resource (§4). `SKILL.md:75`.
10. `mock_provider` needs Terraform >= 1.7 (F10). `always-do-objects-testing.md:44`.
11. S3.17 passes only SSE-KMS and DSSE-KMS (§5 table). `SKILL.md:86`.
12. Versioning can be suspended but not disabled, and Object Lock makes it irreversible (§3, §4). `SKILL.md:87`.
13. `existing_object_replication` needs Support activation (M2). `SKILL.md:88`.
14. Object Lock `days`/`years` are exclusive, and for an existing bucket versioning goes first (§4). `SKILL.md:89`.
15. me-south-1 and me-central-1 are excluded from account-regional (§3). `SKILL.md:90`.
16. EventBridge for independent notification consumers (§4). `SKILL.md:97`.
17. `expected_bucket_owner` is deprecated and forces new (§4). `SKILL.md:101`.
18. `s3_us_east_1_regional_endpoint` is "removed in v7" (§2). `SKILL.md:104`.
19. `aws_s3_account_public_access_block` imports with `<account_id>` and is global (§4, F14). `SKILL.md:105`.
20. Lifecycle filter takes exactly one child, with `and` to combine (§4). `SKILL.md:126`.
21. Objects under 128 KB do not transition by default (§4). `SKILL.md:127`.
22. The upgrade path is latest 5.x, then `~> 6.0`, then `init -upgrade` (§2). `SKILL.md:142`.
23. 6.48 to 6.69 has no S3 breaking changes (§2). `SKILL.md:143`.
24. `skip_destroy` leaves the block unmanaged (§4). `always-do-bucket-foundation.md:77`.
25. `force_destroy` deletes all objects including locked ones, and only takes effect after apply (§3). `always-do-bucket-foundation.md:40-41`.
26. Account PAB `account_id` defaults to the caller account (§4). `always-do-bucket-foundation.md:90`.
27. `aws:kms` without a key ID uses `aws/s3` (§4). `always-do-security-encryption.md:19`.
28. `partitioned_prefix.partition_date_source = EventTime` (§4). `always-do-security-encryption.md:117-121`.
29. Lifecycle timeouts are 3m create and update (§4). `always-do-lifecycle-versioning.md:70`.
30. `checksum_algorithm` values, and the object `bucket_key_enabled` and `kms_key_id` arguments (§4). `always-do-objects-testing.md:20-24`.

Not in the research, contradicting it, or overstated (8 claims). Details are in section 4.
- `abort_incomplete_multipart_upload` recommended as Always Do (N-M2).
- "`PutBucketLifecycleConfiguration` and `PutBucketCors` replace the whole config, last apply wins" (N-M3).
- "SSE-S3 (lower cost)" (N-M4).
- "dynamodb_table ... will be removed" (N-M5).
- `noncurrent_days = 7` with `STANDARD_IA` (N-M6).
- Residual "fails `terraform init`" (N-M1).
- Smaller wording items (N-L3 to N-L6, N-L9).

## 3. Tag and register consistency

- Every `(unverified)` and `(medium confidence)` in the skill maps to a real register id:
  - `SKILL.md:86` and `:124` map to U2.
  - `always-do-security-encryption.md:8` and `:21` map to U2. Both are covered by the single mapping row "section 5 intro and HCL comment".
  - `SKILL.md:89` maps to U6, which exists at `unverified-and-risks.md:27`.
  - `always-do-lifecycle-versioning.md:37` maps to U4.
  - `SKILL.md:88` maps to M2.
  - `SKILL.md:9` is a generic mention of the tag convention, not a tag use.
- There are no orphan mapping rows. All 6 rows point to a tag instance that exists. No tag in the text lacks a row.
- Register-only items (U1, U3, U5, M1, M4, L1–L4) are listed explicitly at `unverified-and-risks.md:57`.
- M3 is closed by F15 and is not carried in the text. This is consistent with the Never Do and Quick Reference rows. The research register still lists M3 as open. That is acceptable, because F15 postdates it.
- U6 does not exist in research §7. It is a skill-side addition, and an honest one. It does not conflict with the research, which simply never stated the Object Lock mode semantics.
- IDs are well-formed and there are no duplicates. The M series skips M3, which is explained in the text.
- Remaining nit is L-5: the header text and the missing I heading.

## 4. Open findings (new in round 2)

### HIGH
None.

### MEDIUM
- **N-M1** `never-do-provider-migration.md:99`: "A constraint resolving to it fails `terraform init`." The research and F4 say only "withdrawn, never pin". This is the residual of M-7, left over after fixing the other two locations. Fix: "A constraint resolving to it is not supported; never pin it."
- **N-M2** `SKILL.md:73`, `always-do-patterns.md` row 8 and `always-do-lifecycle-versioning.md:10`: "add `abort_incomplete_multipart_upload`" is an Always Do rule. The research documents the action (§4) but never recommends it as a baseline. The value `7` is also an unsourced example. Fix: tag it as a general-practice recommendation, or move it to Ask First. Do not cite it as research-backed.
- **N-M3** `never-do-resource-conflicts.md:53-54` and `SKILL.md:97`: the claim that `PutBucketLifecycleConfiguration` and `PutBucketCors` each replace the whole configuration, with "last apply wins silently", is not in the research. Research says "last apply wins" only for the policy, and "replaces the whole config" for notification. For lifecycle and CORS it says only "multiple resources = perpetual diff". Fix: restate lifecycle and CORS as "perpetual diff" and keep the replace semantics for policy and notification.
- **N-M4** `always-do-security-encryption.md:31`: "For SSE-S3 (lower cost, no S3.17)". "Lower cost" is not in the research. This is the round-1 "no extra cost" claim in new words. Fix: "no S3.17 pass".
- **N-M5** `always-do-bucket-foundation.md:7`: "`dynamodb_table` is deprecated (will be removed)". F7 and the research say only "deprecated". "Will be removed" is unsourced. Fix: drop the parenthetical.
- **N-M6** `always-do-lifecycle-versioning.md:40-43`: `noncurrent_version_transition { noncurrent_days = 7, storage_class = "STANDARD_IA" }`. The 7-day value is not supported by the research, and AWS enforces a 30-day minimum before a transition to STANDARD_IA or ONEZONE_IA. I am recalling that AWS constraint from outside the research, so it is unverified here. If correct, `apply` would be rejected. Fix: use `noncurrent_days = 30` or drop the transition. Note that the sibling expiration uses 30 days.

### LOW (new)
- **N-L1** `unverified-and-risks.md:63,90-94`: the "Numbers match the research bibliography" claim is wrong for entries 25–30. The research bibliography stops at 24. Entry 30 (`/cli/commands/test`), and the `terraform test -filter=` flag in `always-do-objects-testing.md:88`, have no research or F-fact evidence. The 25–28 and 29 entries are covered by F5, F7, F9 and F10.
- **N-L2** Leaks of workspace and research wording into shipped text. `unverified-and-risks.md:23` says "(research section 4)". `always-do-objects-testing.md:50-51` has the HCL comment "the research does not document their schema shape". Rephrase these without "research".
- **N-L3** `SKILL.md:63` ("omitting any one leaves a gap") and `always-do-bucket-foundation.md:61-62` ("A missing setting re-exposes public access when a policy or ACL allows it"). The research says "set all four explicitly" and "removing a BPA setting re-exposes existing public policies/ACLs". The wording is slightly stronger than the source.
- **N-L4** `SKILL.md:77,98,129` and `never-do-resource-conflicts.md:86,95`: "etag is not MD5 for KMS". The research says `etag` is "not compatible with KMS" and "not MD5 for multipart > 16 MB". Align the wording.
- **N-L5** `never-do-ownership-acl.md:8`: "Setting it causes a `400 AccessControlListNotSupported` error". The research attributes the 400 to PUTs with ACLs other than `bucket-owner-full-control`, not specifically to `aws_s3_bucket_acl`.
- **N-L6** `SKILL.md:90`: "(default, first-claim)" is not in the research. Research §5 only says a global-namespace name can be re-registered.
- **N-L7** HCL extras that are valid but unsourced: backend `encrypt = true` (`always-do-bucket-foundation.md:24`), `source_policy_documents` (`never-do-resource-conflicts.md:70`), and `depends_on` the PAB on the policy (`always-do-security-encryption.md:72`).
- **N-L8** F4, F14 and F15 are cited in the skill text (`SKILL.md:28,65,105,106`). Nothing inside the skill defines them. Bibliography item 1 is just "F1–F15". Inline the fact where it is cited, or add a one-line gloss.
- **N-L9** `never-do-resource-conflicts.md:110-111`: "creates an unresolvable conflict" is an embellishment. The research says only that it conflicts.
- **N-L10** `var.prefix` is undeclared (`never-do-naming-endpoints.md:23`, `SKILL.md:102`). The other placeholders have notes. Add a one-line placeholder note.
- **N-L11** The evidence rule is still not applied: caveats remain inside Always Do bullets (`SKILL.md:71,75`). The same applies to the `blocked_encryption_types` explanation, which is only in the blueprint.
- **N-L12** Scenario 2 `must_pass` ("suffix counts toward the 63-char limit") is only in `never-do-naming-endpoints.md:8`, not in SKILL.md. Carried over from round 1.
- **N-L13** Scenario 1 `must_pass` requires `bucket_key_enabled = true` and `blocked_encryption_types = ["SSE-C"]`. These are blueprint-only, and the skill itself says the effect of Bucket Keys is unverified. Make the scenario criteria match the skill's own wording.
- **N-L14** The list shape of `blocked_encryption_types = ["SSE-C"]` (5 HCL sites, `always-do-security-encryption.md:22,37`, `never-do-resource-conflicts.md:42`) is not documented in the research. It documents only the values `SSE-C | NONE`. The list is probably right, but the author applied the "do not index undocumented shapes" caution to `rule[0]` and not here.

### LOW (carried from round 1, NOT FIXED)
- **L-5** The mapping header text (`Tag text`, not `Tag text used in the skill`) and the missing I section heading. A prose statement exists only.
- **L-8b** `provisioning-aws-cloudfront-v6` is a forward reference to a not-yet-created skill (planned in batch B2).

## 5. HCL correctness

- No removed or deprecated argument appears outside a `# WRONG` block. Inline `versioning`, `server_side_encryption_configuration`, `acl`, `dynamodb_table`, `expected_bucket_owner` and `.region` appear only in WRONG blocks, in Never Do rows, or as prose. The backend `region = "eu-west-1"` is the backend's own argument and is valid.
- `data.aws_region.current.region`, `bucket_region`, `use_lockfile`, `blocked_encryption_types` (6.40+), `bucket_namespace` (6.37+) and `source_hash` are all valid for `~> 6.69`.
- There is no `;` HCL separator. One-line `{ a = b, c = d }` forms use commas.
- The `.tftest.hcl` is valid. It has `mock_provider "aws" {}`, a `run` block with `command = plan`, and `assert { condition error_message }`. It asserts only top-level booleans that the research documents. The M-8 index risk is gone.
- N-M6 is the one HCL example whose value is questionable. See section 4.
- `terraform fmt` was not run. A manual scan found no misaligned groups.

## 6. Verdict

The skill has no HIGH findings, and 19 of the 21 round-1 items are fixed. The remaining MEDIUMs are unsourced or overstated statements, not contradictions of the research. Fixing N-M1 to N-M6 is a small edit pass: one line each, plus N-M6 which needs a value change in an HCL example. After that the skill is clean, apart from L-5 and L-8b.
