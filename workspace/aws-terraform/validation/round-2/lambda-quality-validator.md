# Quality validation, round 2: provisioning-aws-lambda-v6

Date: 2026-10-23. Target: `packages/aws-terraform/.apm/skills/provisioning-aws-lambda-v6/` (SKILL.md 153 lines + 11 blueprints).
Method: full re-read of all 12 files against the research file, family facts, the policy blueprints and the round-1 report. WebFetch was not available; provider-page facts (log_group = name, publish default false, provisioned_poller_config MSK/Kafka only) are the orchestrator-verified ones. Grounding verdicts are "matches the research file" unless stated.

Counts: HIGH 0, MEDIUM 4, LOW 13. Round-1: 15 FIXED (some with residuals), 8 NOT FIXED / partial, 0 REGRESSED. About 46 new claims sampled.

## Round-1 status

| Id | Status | Evidence |
|---|---|---|
| H1 | FIXED | always-do-function.md:92 `publish = true`; always-do-invocation.md:18 now says "which sets publish = true" and :32-33 restates default false. No `$LATEST` provisioned-concurrency rule asserted anywhere (always-do-invocation.md:8 only says `function_version` is `$LATEST` or a number, which is sourced). |
| M1 | FIXED, residual N1 | SKILL.md:20 (≥ 1.12, vpc page) and :21 (resources) split. |
| M2 | FIXED, residual N6 | Always bullet removed; Ask First row SKILL.md:76; Never row SKILL.md:102 now states the control ("Lambda.1 fails ... without AWS:SourceAccount"). |
| M3 | FIXED | Tracing is Ask First (SKILL.md:75); multi-AZ folded into VPC Ask First row (:74). Always blueprints still show both (N5). |
| M4 | FIXED | Split into two bullets, SKILL.md:47-50, one URL each. |
| M5 | FIXED | SKILL.md:16-17, :24; unverified-and-risks.md:8, :10 now say the constraint admits 1.17.x / every 6.x from 6.69. |
| M6 | FIXED | Register U6 (unverified-and-risks.md:42), tag at always-do-function.md:29-30, mapping row :69. `Version` still omitted from HCL but disclosed and tagged. |
| M7 | NOT FIXED | `event_source_arn` still untagged, no register id, not stated as required for SQS; always-do-events-layers.md:23 comment "this argument's name is not described in the page text read" is internal process wording. Used in never-do-events.md:16,23,37,46,62. MEDIUM. |
| M8 | FIXED | always-do-function.md:100 `.name`, comment cites the page example (orchestrator-verified). |
| M9 | FIXED | Register M4 "reconstructed" deleted; grep finds no "reconstructed"; the "will not be captured" phrase is now paraphrased without quotes (never-do-function.md:57, SKILL.md:94). |
| M10 | FIXED | SKILL.md:128-130 carry "(medium confidence, absence of evidence)" mapped to M6 (register :53, :72); upgrade-path bullet :134 has a URL. |
| M11 | NOT FIXED | "medium severity" still at SKILL.md:74 (Lambda.5, new in the moved Ask First row), :120 (Lambda.2), :122 (Lambda.5). Policy wording is low\|moderate\|high. MEDIUM. |
| M12 | FIXED | Pairing is now Ask First (SKILL.md:79) with M4 tag; no `capacity_provider_config` row in Never. |
| M13 | FIXED | SKILL.md:98 quotes the page sentence; never-do-events.md:55-56 same; consistent with orchestrator fact. |
| L1 | FIXED | SKILL.md:63 "When setting ... use at least 2"; "provider rejects" removed (never-do-events.md:31). |
| L2 | NOT FIXED | SKILL.md:61 still an unconditional Always rule; the function-code `batchItemFailures` contract is not stated. |
| L3 | NOT FIXED | never-do-access-provider.md:13-27 WRONG block is still a comment; CORRECT block references `aws_iam_role_policy.vpc_access` (now marked "placeholder", partial mitigation); always-do-function-config.md:44-56 still has no VPC policy or `depends_on`; "until the function is destroyed" still goes beyond the page (SKILL.md:59, :101). |
| L4 | NOT FIXED | SKILL.md:100 unchanged; never-do-events.md:98-99 "CreateFunction fails or duplicates occur on update" unchanged. |
| L5 | NOT FIXED | Runtime dates in 3 places (SKILL.md:72, unverified-and-risks.md:18-26, evaluation-scenarios.md:89-97); "supported to 2029" still has no date. Rules rows carry no dates (correct). |
| L6 | NOT FIXED | unverified-and-risks.md:28-31 still rebuts the legacy file ("it is not 'approaching EOL'"); scenario 4 still opens "Our standards say". |
| L7 | PARTIAL | Register column renamed (unverified-and-risks.md:66) FIXED; SKILL.md:86 "Newer function blocks" still has no tag although register L2 exists. |
| L8 | FIXED | always-do-function.md:109 closing paragraph has the URL. |

## Never-row count (counted with grep/read)

- SKILL.md Never table: rows at lines 92-103 = 12.
- never-do-patterns.md hub: rows at lines 8-19 = 12.
- Blueprints: never-do-function 4 + never-do-events 5 + never-do-access-provider 3 = 12.
- 12 = 12 = 12, order one-to-one. All hub and SKILL.md anchors resolve to existing headings (renumbering of never-do-access-provider sections 1-3 is consistent). Pass.
- Always Do: 10 bullets, High-only, no tags, one URL each, no runtime dates. Pass (see N7).
- Tags vs register: tags used in shipped text are (medium confidence) at SKILL.md:79, :84, :85, always-do-function.md:75, never-do-access-provider.md:33, plus the absence-of-evidence tag at SKILL.md:128-130; (unverified) at SKILL.md:75, :80-83, always-do-function.md:29-30. Mapping rows cover U1-U6 and M1-M6; no orphan register ids, no unmapped tag. Register M4/M5/M6 reuse is correct. Plain notation, no bold or brackets. Pass.

## New findings

MEDIUM
- N1. SKILL.md:21 "Documented on the function, event source mapping, permission, alias and layer version pages" cites only the function page. Four of five per-resource claims are uncited (research lines 17, 76, 85, 126 hold them). Cite all five pages or narrow the claim.
- N2. SKILL.md:130 "one chunk boundary was not fully visible" and unverified-and-risks.md:59 (L1) "read in two chunks" are research-process wording shipped to users. Say "the changelog was read only in part".
- (M7 and M11 above stay open at MEDIUM.)

LOW
- N3. Terraform releases page dated 2026-10-14 at SKILL.md:16 but "read 2026-10-22" at SKILL.md:24, unverified-and-risks.md:8 and :104 (item 20 merges Terraform and provider releases under 2026-10-22). Family facts F1/F2 support both dates; state per claim which read produced it.
- N4. SKILL.md:77 cites the runtimes page for "default is `x86_64`"; the default comes from the function page.
- N5. always-do-function-config.md:83-100 (§7 tracing) and §5 VPC remain in the Always blueprints while SKILL.md makes tracing and VPC Ask First. Add "optional, Ask First" to the headings.
- N6. SKILL.md:102 Never row ✅ prescribes `source_account`, whose mapping to `AWS:SourceAccount` is tagged medium (M5) only in Ask First and the blueprint. Add the tag on the row or soften the ✅.
- N7. SKILL.md:47-50 bullets carry the choice ("this skill's target") plus a URL that only supports `~>` semantics; the two bullets share one URL.
- N8. SKILL.md:134 says the 6.0 upgrade guide "uses `~> 6.0`"; this is not in the research.
- N9. Evaluation scenarios do not cover the moved rows (Ask First `source_account`, `vpc_config` + `capacity_provider_config`) and still fix dates in scenario 4.
- Plus the open round-1 LOWs L2-L7.

## Fresh grounding sample (46 claims, none checked in round 1)

Checked and matching the research: function defaults and ranges (SKILL.md:111), ephemeral storage, function timeouts, tracing modes, event invoke ranges, mapping defaults and timeouts, function URL defaults and max_age, code signing Warn/Enforce and 20 ARNs, Lambda.1/2/3/5/6/7 severities and "no Lambda.4" (SKILL.md:119-124), image_config arguments and no deprecation notices for images (always-do-function-config.md:10-13), vpc_config dual-stack default and all-empty rule, ENI permission list, private subnets and NAT, replace_security_groups_on_destroy, kms_key_arn default and decrypt note, dead_letter_config targets, alias name rule and routing weights, provisioned concurrency ≥ 1 and skip_destroy, permission statement_id rules, function URL NONE permissions, event invoke role permissions and generic error, partial-batch behaviour, mapping UUID import, layer compatible_runtimes ≤ 15 and same-region bucket, runtime list and deprecation policy (unverified-and-risks.md:20-26), 6.48/6.54/6.64/6.65 changelog entries, `aws_lambda_resource_policy` 6.65.0, durable_config/tenancy_config/publish_to on main, default log group name, Access Analyzer. 0 wrong, 0 unsourced-untagged beyond N1, N4, N8 and M7. Runtime dates appear only in Ask First (SKILL.md:72), Version-lifetime risk and the register, never in Always or Never rows. No F#/M#/U# ids or "research"/"legacy" process wording in shipped rules except N2 and L6.

## Verdict

0 HIGH. Four MEDIUM left (M7, M11, N1, N2), all cheap and mechanical. Close M7, M11, N1, N2 and the L-items before VERIFIED.
