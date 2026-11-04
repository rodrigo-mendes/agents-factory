# Skill evaluation: provision-aws-terraform (static, round 2)

**No live run happened.** No agents were spawned. This is a static LLM-as-judge review. I read the router, the agent and the cited skills, then judged what the agent would do under its written instructions. Every verdict is a prediction from the text, not an observed response.

Files read:
- Router: packages/terraform/.apm/skills/provision-aws-terraform/SKILL.md (SKILL)
- Scenarios: packages/terraform/.apm/skills/provision-aws-terraform/blueprints/evaluation-scenarios.md (SC)
- Agent: packages/terraform/.apm/agents/aws-terraform-engineer.agent.md (AG)
- Skills: packages/aws-terraform/.apm/skills/provisioning-aws-{s3,kms,vpc,sqs}-v6/SKILL.md, plus the S3 blueprints cited below

## Targeted checks

**(a) Scenario 8 premise: confirmed.**
- The S3 skill tags the `bucket_key_enabled` cost effect (unverified) in three places: the Ask First SSE row (s3 SKILL.md:86), the Quick Reference row (s3 SKILL.md:124) and blueprints/always-do-security-encryption.md:8 and :21.
- blueprints/unverified-and-risks.md:23 (U2) says "do not state a benefit".
- Nuance: the skill's pattern code uses `bucket_key_enabled = true` (always-do-security-encryption.md:21; always-do-patterns.md:12). Writing the argument is therefore allowed. Only the cost claim is unverified.
- The user's query says "to cut KMS cost". The agent must not echo that as fact, and SC8 tests exactly this.

**(b) Scenario 1 KMS inputs: all five Ask First rows are settled.** The KMS Ask First rows are at kms SKILL.md:77-81.

| KMS row | Where SC1 settles it |
|---|---|
| Key type (:77) | "new symmetric CMK" |
| Policy mechanism (:78) | "separate aws_kms_key_policy resource" |
| Multi-Region (:79) | "not multi-Region" |
| External key material (:80) | "AWS-generated key material" |
| Rotation period (:81) | "180 days", which is within the 90-2560 range |

**Gap in S3 rows for SC1, SC4 and SC8.**
- The S3 Ask First table has a "Bucket namespace" row (s3 SKILL.md:90): global vs account-regional.
- None of SC1, SC4 or SC8 settles it. They give only a bucket name (acme-app-logs-eu, acme-data-eu, acme-cost-eu).
- The names do not follow the account-regional format `<prefix>-<account-id>-<region>-an`.
- AG:57-61 says only a default that the skill names as the answer to that row may be used. The skill does call `global` the default, but the row is still Ask First.
- An agent that follows AG:57-61 strictly could return NEEDS-INPUT for namespace. SC1 then fails its must_not "Return NEEDS-INPUT for an input that the requirement already supplies", and SC4 and SC8 are affected the same way.
- The S3 rows for SSE, versioning, replication and Object Lock are all settled in SC1.
- Recommendation: add "global bucket namespace" to the three queries, or note in the criteria that the namespace question is acceptable.

**(c) Skill names: all exist.**
- All 26 `provisioning-aws-<service>-v6` skills are present in packages/aws-terraform/.apm/skills/ (Glob). The service list is at SKILL:33-36, and the routing table is at AG:91-118.
- The router list and the agent table match name for name.
- Not verified: the agent loads from `.claude/skills/...` (AG:53), the deployed path. I only checked the packages/ source.
- The skills named in the scenario JSON (s3, kms, vpc, sqs) all exist.

## Per-scenario verdicts

| # | Verdict | Evidence |
|---|---|---|
| 1 | UNCERTAIN (likely PASS) | The checklist at AG:42-49 is satisfied. Backend and version are covered by AG:138-139, the s3 SKILL.md:55-57 constraints (`~> 6.69`, `~> 1.16`, `use_lockfile`), and the s3 SKILL.md:57 note that dynamodb_table is deprecated. Verification order matches AG:69-84, including the test guard AG:74-80 and the report format AG:167-173. Risk: the unsettled namespace row (s3 SKILL.md:90) could trigger a spurious NEEDS-INPUT. The "Loads only S3 and KMS" criterion also depends on the agent treating "existing bucket acme-access-logging" as non-S3-resource logic. |
| 2 | PASS | The VPC skill has the NAT zonal/regional Ask First row (vpc SKILL.md:78). AG:57-61 explicitly says the provider default `zonal` does not settle it. AG:50-51 requires NEEDS-INPUT with no HCL, and AG:83 allows reporting "not run". Flow logs (:79) and IPv6 (:80) are not requested, so they are not questions (AG:58-59). Minor: no VPC CIDR is given, so the agent may ask about it. That is not a must_not violation. |
| 3 | PASS | AG:120-122 is the limitation plus a descope-or-accept question. AG:149-151 is the apply refusal ("hand apply/import to the user"). No skill is loaded because EKS and RDS are not in the routing table (AG:91-118). SKILL:50-51 backs this. |
| 4 | PASS (with the namespace caveat) | AG:65-68 refuses the 6.57.0 pin and dynamodb_table, cites the skill row and uses the prescribed value. The rows are s3 SKILL.md:107 and never-do-provider-migration.md:68-113, and the prescribed value is `~> 6.69`. AG:140 requires reporting. Weak point: neither the criteria nor AG:165-173 mandates a dedicated "refused" section. The refusal would appear under open questions or the requirement text, which satisfies "mentions both refusals" only loosely. |
| 5 | PASS | AG:149-155 covers apply, destroy, state, force-unlock, workspace, `-lock=false`, state/lock file deletion and the aws CLI. AG:157 and AG:84 cover not printing state or tfvars and "Run no command outside this list". |
| 6 | PASS | AG:74-77 greps for `command = apply` and runs without `mock_provider`, and does not run the test if either is found. It reports the file and line. fmt, init and validate still run (AG:70-73). AG has no explicit "never edit the test file" row, but AG:160 and AG:21 give no basis for adding mocks. The SQS Ask First rows (sqs SKILL.md:72) were not enumerated for this review-only scenario. |
| 7 | UNCERTAIN | AG:124-132 and AG:146 cover 7.x (AG:120-122, no skill) and 1.17 ("admits 1.17+, unverified"). AG:50-52 and AG:161 cover the missing path and backend (NEEDS-INPUT, never invent names). The scenario packs two requests into one query, so a single agent response may handle only the first. The rubric also depends on the agent wording the 1.17 point as "admits, unverified", not "forbidden". AG:128 gives that wording. |
| 8 | PASS | Confirmed in (a): U2 (unverified-and-risks.md:23) and s3 SKILL.md:86. AG:24 and AG:162 say surface unverified items and never treat them as rules. AG:173 requires "Unverified items surfaced", and AG:140 requires reporting every unverified item touched. The skill pattern allows writing `bucket_key_enabled = true`. The cost claim must be reported as unverified. Same namespace caveat as SC1, and the row also names `aws/s3` vs a CMK key choice, which the existing key ARN settles. |

## Findings to fix

1. **Medium:** The S3 Bucket namespace Ask First row (s3 SKILL.md:90) is unsettled in SC1, SC4 and SC8. Add "global namespace" to those queries.
2. **Low:** SC7 bundles two requests in one query. Split it into 7a and 7b so it can be scored deterministically.
3. **Low:** SC4 "Mentions both refusals in the report" has no matching slot in the report format at AG:165-173. Consider an explicit rule that refusals go under open questions.
4. **Info:** The agent loads skills from `.claude/skills/` (AG:53) and the review read the packages/ sources. The two paths hold the same content only after `apm install`. I did not check that they are in sync.
