# Evaluation Report: provisioning-aws-step-functions-v6 (round 1)

Method: no subagents. Each response was written from SKILL.md and its blueprints only, then judged. Scenarios come from `blueprints/evaluation-scenarios.md`.

## Summary

| Scenario | must_pass | must_not | Verdict |
|---|---|---|---|
| 1 Canonical (Standard + logging + tracing + alias) | 8/8 | 3/3 OK | PASS |
| 2 Customer managed key + logging | 5/6 | 2/2 OK | PARTIAL |
| 3 Misuse rejection (version resource, definition_substitutions) | 3/3 | 2/2 OK | PASS |
| 4 Anti-pattern trap (Express .sync, ARN, States.ALL, dynamodb_table) | 4/4 | 3/3 OK | PASS |
| 5 Unverified handling | 3/3 | 2/2 OK | PASS |

Overall: 23/24 must_pass (96%), 12/12 must_not OK. 4 PASS, 1 PARTIAL, 0 FAIL.

## Scenario 1: PASS
Response built from always-do-foundation §1-2 and always-do-state-machine §3-4.
- `required_version = "~> 1.16"` and `version = "~> 6.69"`: PASS (foundation §1).
- Trust principal `states.amazonaws.com` with `sts:AssumeRole`: PASS (`Principal = { Service = "states.amazonaws.com" }`).
- `log_destination` ends with `:*`: PASS (`"${aws_cloudwatch_log_group.sfn.arn}:*"`).
- `logs:CreateLogStream` on `Resource = "*"`: PASS (foundation §2 logging policy).
- `tracing_configuration { enabled = true }` plus the four X-Ray actions: PASS (`sfn_xray` policy).
- `publish = true` with the alias on `state_machine_version_arn`, weight 100: PASS (§4 `aws_sfn_alias.live`).
- Definition uses `jsonencode()`: PASS.
- Example values and fragments marked: PASS (`# example`, `# Fragment: ... defined elsewhere`).
- must_not: no `aws_sfn_state_machine_version`, no `definition_substitutions`, and `delivery.logs` is not in the trust policy. All OK.

## Scenario 2: PARTIAL
- `encryption_configuration` with `CUSTOMER_MANAGED_KMS_KEY` and `kms_key_id`: PASS (§6).
- Key policy lets `delivery.logs.amazonaws.com` do `kms:Decrypt`: PASS (`sfn_logs_key_statement`). The word "only" is implied by the skill's one-action statement and the "opposite claims" table. It is never stated outright.
- Role gets `kms:Decrypt` and `kms:GenerateDataKey` scoped by `kms:EncryptionContext:aws:states:stateMachineArn`: PASS.
- Role gets `kms:GenerateDataKey` with `kms:EncryptionContext:SourceArn` for logging: PASS (second statement in `sfn_kms`).
- Notes that a disabled or deleted key makes running executions fail: FAIL. No file in the skill says this. Searched SKILL.md, always-do-encryption-testing.md and unverified-and-risks.md. Under the rules, a response limited to skill content cannot satisfy it.
- Refers key policy authoring to `provisioning-aws-kms-v6`: PASS (always-do-encryption-testing.md header and the §6 fragment comment).
- must_not: no `kms:ViaService` on the role, and no Encrypt or GenerateDataKey for `delivery.logs`. Both OK.

## Scenario 3: PASS
- States that no `aws_sfn_state_machine_version` page exists (404) and that versions come from `publish = true` or the `aws_sfn_state_machine_versions` data source: PASS (SKILL.md Quick Reference "Versions" row; unverified-and-risks "opposite claims" table).
- States that `definition_substitutions` is not an argument and offers `templatefile()` or `jsonencode()`: PASS (Quick Reference "Definition substitution" row).
- Shows an alias on version ARNs: PASS (§4 `live` and `canary`, plus the data source).
- must_not: nothing emitted. The only mentions are rejections, which the brief allows. OK.

## Scenario 4: PASS
- Rejects `.sync` on Express and recommends Standard: PASS (never-do-iam-asl §7).
- Rejects the bare log group ARN and shows `"${...arn}:*"`: PASS (never-do-configuration §1).
- Moves `States.ALL` to alone and last: PASS (never-do-iam-asl §8).
- Rejects `dynamodb_table` as deprecated and shows `use_lockfile = true`: PASS (never-do-configuration §4).
- must_not: none of the three is accepted. OK.

## Scenario 5: PASS
- Says the page documents publishing "during creation" and that publishing on each update is (unverified): PASS (Ask First row "Definition changes and versions", U1).
- Says perpetual diffs from definition formatting are (unverified): PASS (Ask First row "Definition formatting diffs", U2).
- Suggests a `terraform plan` check: PASS (both Ask First rows).
- must_not: neither behavior is asserted. OK.

## Findings and fixes needed

1. Scenario 2 must_pass #5 (disabled or deleted key fails running executions) is an unsourced criterion. The research never gives this advice. Two fixes are possible:
   - Preferred: drop the criterion from `blueprints/evaluation-scenarios.md`.
   - Alternative: add a sourced sentence to `blueprints/always-do-encryption-testing.md` §6, if AWS `encryption-at-rest.html` documents it. The sentence needs a dated source and must not be written from memory.
2. Scenario 2 must_pass #2 uses "only kms:Decrypt". Make it explicit in `always-do-encryption-testing.md` §6, for example "the key policy grants `delivery.logs.amazonaws.com` only `kms:Decrypt`". Alternatively, loosen the criterion to "allows kms:Decrypt".
3. No other defects found. The skill's `(unverified)` and `(medium confidence)` tagging is consistent with the register in unverified-and-risks.md.
