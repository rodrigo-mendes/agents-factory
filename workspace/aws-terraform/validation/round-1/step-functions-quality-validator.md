# Quality validation, round 1: provisioning-aws-step-functions-v6

Target: packages/aws-terraform/.apm/skills/provisioning-aws-step-functions-v6/ (SKILL.md 151 lines, all blueprints under 160 lines, frontmatter valid, description about 271 chars with "Use when").
Method: read all 10 files, the research, facts and policy. About 40 claims sampled. The WebFetch spot-check was NOT done, because no WebFetch tool was available to this run. Verdicts rest on the research text only. `scripts/verify_skill.py` was not run.
Not reported, per brief: the -v6 suffix and the page-from-main confidence convention.

Counts: HIGH 1, MEDIUM 9, LOW 8.

## HIGH

H1. Never row "States.ALL alone and last" has an unsupported scope. Files: SKILL.md:104; never-do-iam-asl.md:39-56.
- The research (line 79) says only "`States.ALL` must be alone and last". It does not say whether that means the `ErrorEquals` array or the retrier list.
- SKILL.md:104 writes "in the error lists", which is a third formulation.
- The WRONG example puts `States.ALL` first in a Retry list, inside its own single-element array. That is a retrier-ordering claim the recorded evidence does not state, so it fails the "Never = High, sourced" rule. The same ordering claim is in evaluation-scenarios.md:93, "Rejects States.ALL not alone and last; moves it last".
- Fix: re-read concepts-error-handling and quote the exact sentence. If it covers both array and ordering, state both separately: alone in `ErrorEquals`, and the last Retrier/Catcher. If it cannot be confirmed, move the row to Ask First as `(medium confidence)` and register it as an M-id. Also keep the `States.DataLimitExceeded` / `States.Runtime` exclusion, which is sourced.

## MEDIUM

M1. The Quick Reference states absence claims as bare facts. Per the evidence rule they should read `(medium confidence, absence of evidence)`.
- SKILL.md:120: "no `aws_sfn_state_machine_version` page exists (404)". The cited source is the data-source page, which does not say that. The 404 URL is cited nowhere.
- SKILL.md:121: "no `definition_substitutions` argument".
- SKILL.md:130-132: "the 6.0.0 upgrade guide has no entry mentioning aws_sfn_*".
- evaluation-scenarios.md:69-70 requires the model to assert these absences as certain.
- None of these has a tag or a register id.

M2. SKILL.md:134-136 (upgrade path "move to the latest 5.x, get a clean plan, set `~> 6.69`") is unsourced and untagged. The research has no such claim, and the cited dependency-lock page only supports `init -upgrade`. Fix: drop it, or tag it `(unverified)` and register it.

M3. SKILL.md:86 and SKILL.md:121 cite the wrong page, and the page behind the `templatefile` claim was never re-read.
- The "editable in Workflow Studio" claim has no source in the research.
- The templatefile page is cited but was not re-read (research bibliography item 17).
- SKILL.md:121 attributes "build the string with `templatefile()` or `jsonencode()`" to the sfn_state_machine page, which does not state it.
- Fix: cite the function pages, tagged medium, and drop the Workflow Studio claim or tag it `(unverified)`.

M4. Always Do bullet 12 (SKILL.md:73) cites the wrong page. "Tag state machines and activities" is cited only to Security Hub, which covers activities only (StepFunctions.2). The state-machine tagging claim comes from sfn-best-practices. Fix: cite the best-practices page for state machines, or reduce the bullet to activities.

M5. The CMK logging policy example is wrong in practice. always-do-encryption-testing.md:57-60 uses `StringEquals` on `kms:EncryptionContext:SourceArn` with a value ending in `:*`. `StringEquals` does not wildcard-match, so that value matches nothing. The `(unverified) operator` tag does not make a misleading example safe. It also contradicts line 15, which says the value is "the log group ARN"; the research only says `arn:aws:logs:...`. Fix: use `ArnLike`, or a concrete log group ARN with `StringEquals`, and tag or soften "log group ARN".

M6. The canary alias example (always-do-state-machine.md:95-112) is misleading, which answers your check (7).
- The comment says `var.previous_version_arn` is "taken from" the data source, but nothing wires the two. The `data` block is declared and never used.
- The 10% leg is `main.state_machine_version_arn`. Per U1, that attribute may only be the creation-time version, so it is not necessarily the "new" version. The example reads as new=10% and old=90% without evidence.
- Fix: remove the unused data block, or show that the second ARN comes from an input and say its provenance is not guaranteed. Add a note pointing to U1.

M7. Orphan register row M5 (unverified-and-risks.md:46). It is never used as an inline tag, and SKILL.md:90 states the immutability claim untagged. Either tag that Ask First row `(medium confidence)` and map it, or delete M5. The mapping table header also differs from the required column "Tag text used in the skill" (unverified-and-risks.md:58).

M8. The "Pages that state the opposite of common claims" table is misplaced (unverified-and-risks.md:19-27), which answers your check (6) placement question.
- The register schema defines fixed sections, and this is not one of them.
- It mixes sourced corrections with absence claims (rows 1 and 2) that carry no tag.
- The "Claim seen elsewhere" wording is vague, and the section is not covered by the tag mapping.
- Fix: move the corrections into a short topic blueprint (for example `legacy-corrections.md`) or into never-do. Tag the absence rows. Keep the register to U/I/M/L/mapping/bibliography.

M9. Always Do bullet 15 (SKILL.md:79) is a best-practice recommendation, not a page-stated fact. The mocking page (facts F10) says `command = plan|apply` is allowed, not that `plan` is required. It is not High under the evidence rule. Fix: demote to Ask First or blueprint, or limit it to the page-stated fact that `mock_provider` avoids real AWS calls.

## LOW

L1. Always Do bullets are not one claim each. Bullets 4 (SKILL.md:57), 5 (59), 8 (65) and 10 (69) carry a second clause after the em dash. Bullet 13 (75) omits the Sync Express exception (`kms:Decrypt` only), so it overstates. Note: I count 15 Always Do bullets, not 16.

L2. Bare "medium" used as a severity word at SKILL.md:59 ("medium severity") and :126 ("Medium"). The notation policy wants low|moderate|high. Strictly this rule covers headings only.

L3. SKILL.md:12 cites the generic enhanced-region guide. The research bases "these resources take `region`" on the four resource and data-source pages. The import `<arn>@<region>` claim at :133 has no inline source.

L4. always-do-foundation.md:43 ("IAM role is global") sits under the procedure-create-iam-role citation. The fact comes from the enhanced-region-support page (F14). always-do-foundation.md:111-113 cites connect-to-resource for the "specific action on the specific ARN" half, which the research sources to connect-lambda and the IAM page.

L5. SKILL.md:8 says "reference patch 6.69.0/6.70.0", two patches for one version lock. Quick Reference line 117 (encryption type) does not say it is the state-machine enum, and it conflicts with the activity enum covered by M4.

L6. The `(unverified)` scaffolding tags are used inconsistently (answers your check 3). The trust-policy `StringEquals`/`ArnLike` and every Never-block IAM JSON are untagged, while the CMK `StringEquals` is tagged. SKILL.md:41 `Parameters shape` is genuinely unverified per the research. Scaffolding is a legitimate unverified item, but not as repeated inline tags: the file header note plus U4 already say it. Keep one coverage-style item and drop the repeated comments. Tag only claims a reader could act on wrongly (M5 above). `Version = "2012-10-17"` is noise.

L7. never-do-configuration.md section 3 WRONG example only shows an alias ARN, not the unpublished-revision case. never-do-iam-asl.md:13 uses an invented `kms:ViaService` value. It is marked example, but add the alias-case CORRECT value check.

L8. The unverified-and-risks.md "Tag to Register Mapping" heading casing and column name differ from the policy text.

## Rule-by-rule answers

1. Never rows. Ten rows map one-to-one across SKILL.md, never-do-patterns.md and the two blueprint files. No sub-High row is used except H1.
   - `kms:ViaService`: High, sourced to encryption-at-rest, and the Instead value is sourced. OK. The wording "can break executions" is the page's own.
   - Unqualified Lambda ARN: sourced to connect-lambda. OK.
   - Logging actions on a log group: sourced to cw-logs. OK. It duplicates Always Do bullet 4.
   - Alias to alias or unpublished revision: sourced to the alias page. OK.
   - `.sync`/`.waitForTaskToken` in Express: sourced to connect-to-resource. OK. The Instead is also sourced.
   - `name` + `name_prefix`: High, from the page. OK.
   - `States.ALL`: see H1.
2. Always Do bullets: see M4, M9 and L1. One inline URL each is met.
3. No F#/M#/U# ids, "the research" or "WebFetch" appear in shipped prose. Register ids U/M/L appear only in the register. The "Claim seen elsewhere" wording is mildly internal (M8). Tags use plain parentheses. Tag/register consistency: M7. Header counts match.
4. Example values are marked consistently with `# example` and `# fragment`. Two untagged values: always-do-encryption-testing.md:49, which hard-codes "order-workflow", and never-do-iam-asl.md:13.
5. Citation fidelity: M3 and M4 plus L3 and L4. Not re-read in the research: templatefile (M3).
6. Legacy claims were not reproduced as facts. There is no `aws_sfn_state_machine_version` resource and no `definition_substitutions`. The trust principal is `states.amazonaws.com`. `delivery.logs` appears only in the key policy, with `kms:Decrypt`. `logs:CreateLogStream` is included. Placement of the corrections table: M8.
7. Canary alias: M6.
