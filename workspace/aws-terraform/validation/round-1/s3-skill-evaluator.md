# Evaluation Report - provisioning-aws-s3-v6 (round 1)

Method: no sub-agents spawned (per caller instruction). Each response was written by the evaluator using ONLY SKILL.md and its linked blueprints, then judged. Source: packages/aws-terraform/.apm/skills/provisioning-aws-s3-v6/.

## Summary

| Scenario | must_pass | must_not | Verdict |
|---|---|---|---|
| 1 Canonical secure bucket | 10/10 | 5/5 OK | PASS |
| 2 Account-regional namespace | 6/6 | 2/2 OK | PASS |
| 3 mfa_delete + lifecycle | 4/5 | 2/2 OK | PARTIAL |
| 4 6.0 breaking changes trap | 5/5 | 3/3 OK | PASS |

Overall: 25/26 must_pass (96%), 12/12 must_not OK. 3 PASS, 1 PARTIAL, 0 FAIL.

## Scenario 1 - Canonical (PASS)

Evidence, by criterion (all from skill content):
- required_version / provider: foundation s1 `required_version = "~> 1.16"`, `version = "~> 6.69"`. PASS
- use_lockfile, no dynamodb_table: foundation s1 `use_lockfile = true`. PASS
- ownership_controls BucketOwnerEnforced: foundation s2. PASS
- Four BPA booleans true: foundation s3. PASS
- Account PAB without region: foundation s4 ("No region attribute - this resource is global (F14)"). PASS
- Satellite SSE, aws:kms, bucket_key_enabled: security s5. PASS
- blocked_encryption_types = ["SSE-C"]: security s5. PASS
- TLS Deny on aws:SecureTransport=false: security s6. PASS
- aws_s3_bucket_versioning standalone: lifecycle s9. PASS
- Lifecycle with `filter {}` + noncurrent_version_expiration (noncurrent_days = 30): lifecycle s8 (Rule 2). PASS

must_not: no inline blocks, no dynamodb_table, no region on account PAB, no etag, no expected_bucket_owner. All OK.

Notes: the skill has no single end-to-end example; the assistant must assemble it from four blueprints. The KMS key is delegated to provisioning-aws-kms-v6 (`aws_kms_key.s3` is referenced but not defined). Acceptable.

## Scenario 2 - Account-regional namespace (PASS)

- bucket_namespace = "account-regional": never-do-naming s1. PASS
- Suffix pattern `-<account-id>-<region>-an`: s1 and SKILL.md Never Do row. PASS
- data.aws_caller_identity.current.account_id: s1. PASS
- data.aws_region.current.region (not .name): s1 (F15). PASS
- Not available in Bahrain (me-south-1) / UAE (me-central-1): never-do-naming s1 line 8 gives both codes. SKILL.md Ask First row says only "Bahrain/UAE" without region codes. PASS (via blueprint)
- 63-char limit: "The suffix counts toward the 63-char limit." PASS

must_not: no arbitrary name, no `.name`. All OK.

Notes: the skill gives no prefix-length budget (63 minus 12-digit id, region, `-an`, separators). Not required by the criterion.

## Scenario 3 - mfa_delete + lifecycle (PARTIAL, 4/5)

- Explicitly rejects combining: SKILL.md Never Do row ("Choose one: MFA delete or lifecycle - not both"); conflicts s4 ("unresolvable conflict"). PASS
- AWS docs explicitly prohibit: SKILL.md ("AWS explicitly states MFA delete cannot be used with a lifecycle configuration", Security Hub source). PASS
- S3.20 vs S3.10/S3.13 conflict, choose one: conflicts s4 and lifecycle s9 comment. PASS
- Only root user can enable MFA delete: lifecycle s9 and conflicts s4 comments. PASS
- Recommends lifecycle (S3.10/S3.13) as the practical choice: FAIL. The skill says "choose one" and gives no preference. Its CORRECT example happens to omit mfa_delete and keep lifecycle, but there is no explicit recommendation. An assistant limited to skill content would have to infer it.

must_not: both OK.

Fix: add to never-do-resource-conflicts.md s4 (and the SKILL.md Never Do row) one line such as "Default recommendation: keep lifecycle rules (S3.10/S3.13); MFA delete needs root credentials and blocks lifecycle. Ask the user only if MFA delete is a hard compliance requirement." Alternatively, relax the criterion.

Ambiguity flagged: the criterion asks for a recommendation the skill does not make. Decide whether the skill or the scenario should change. Also, S3.10 only applies to versioned buckets; "satisfy both" framing is fine.

## Scenario 4 - 6.0 breaking changes (PASS)

- Rejects inline versioning alongside satellite, states drift: conflicts s1 and SKILL.md Never Do row 1. PASS
- Deprecated but not removed in 6.0; drift not provider error: conflicts s1 note ("the failure mode is perpetual drift, not a provider error"); SKILL.md migration section. PASS
- Rejects `.region`, gives `.bucket_region`: SKILL.md Never Do row 8 and migration section. PASS
- Rejects s3_us_east_1_regional_endpoint = "legacy" (deprecated 6.0, removed v7): never-do-naming s2. PASS
- Recommends removing inline block, keep satellite only: SKILL.md Never Do row 1 "Instead". PASS

must_not: all 3 OK.

## Fixes needed (short)

1. never-do-resource-conflicts.md s4 and SKILL.md Never Do mfa_delete row: add an explicit default recommendation for lifecycle rules (S3.10/S3.13). This fixes the only failed criterion in S3.
2. Optional: add the region codes (me-south-1 / me-central-1) to the SKILL.md Ask First "Bucket namespace" row. Today they appear only in the blueprint.
3. Optional: add the prefix-length budget for the 63-char limit in never-do-naming s1.
