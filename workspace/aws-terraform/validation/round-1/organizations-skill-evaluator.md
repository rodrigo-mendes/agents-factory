# Evaluation Report: provisioning-aws-organizations-v6 (round 1)

Method: no subagents. Each response was written from SKILL.md and its blueprints only, then judged. Skill dir: packages/aws-terraform/.apm/skills/provisioning-aws-organizations-v6/

## Summary

| Scenario | must_pass | must_not violated | Verdict |
|---|---|---|---|
| 1 Canonical org/OU/account/SCP | 7/7 | 0/4 | PASS |
| 2 Account closure on destroy | 4/5 | 0/2 | PARTIAL |
| 3 Region misuse rejection | 3/3 | 0/2 | PASS |
| 4 SCP limits / skip_destroy | 4/4 | 0/2 | PASS |
| 5 CONSOLIDATED_BILLING to ALL | 4/4 | 0/2 | PASS |

Overall: 22/23 must_pass (95.7%), 0 must_not violations. 4 PASS, 1 PARTIAL, 0 FAIL.

## Scenario 1 - PASS
- `required_version = "~> 1.16"` and aws `~> 6.69`: PASS (always-do-foundation.md §1 HCL).
- `use_lockfile = true`, no `dynamodb_table`: PASS (foundation §1; SKILL.md Always Do).
- `feature_set = "ALL"`: PASS (foundation §2).
- `roots[0].id` as top-level parent_id: PASS (foundation §3 `workloads`).
- Account `parent_id` set explicitly, plus `ignore_changes = [role_name]`: PASS (foundation §4).
- Policy attachment to the root, FullAWSAccess kept: PASS (policies §5 `aws_organizations_policy_attachment.root`; SKILL.md says "keep `FullAWSAccess`").
- No `region` on `aws_organizations_*`: PASS. Only the backend and provider blocks carry region.
- must_not: all four OK. The response reads `.state`, not `.status`.

## Scenario 2 - PARTIAL
- Default destroy only removes the account from the org: PASS (foundation §4: "By default destroy only removes the account from the organization").
- close_on_deletion closes the account, not supported for GovCloud: FAIL. The skill says close_on_deletion closes the account (SKILL.md Ask First). The word GovCloud appears nowhere in the skill. grep found it only in evaluation-scenarios.md.
- CLOSE_ACCOUNT_QUOTA_EXCEEDED, then close manually: PASS (SKILL.md Ask First row).
- Quota is 20% of members or 250, whichever is higher, max 1,000 per 30 days: PASS (Quick Reference; Never Do row).
- Asks before enabling close_on_deletion: PASS ("Should destroying this resource close the AWS account?").
- must_not: OK. The response does not say 10%, and it does not say destroy closes by default.

Failure location: the criterion is unsourced. SKILL.md, the Ask First row for `close_on_deletion`, and foundation §4 never state the GovCloud limitation. This is a criterion bug, or a skill gap if the research did fetch it from the organizations_account page. Verify the page.

## Scenario 3 - PASS
- Rejects the request because Organizations is global: PASS (never-do-organization §1; SKILL.md Never Do row 1).
- Import ID `ou-1234567` with no @region: PASS (never-do-organization §1 CORRECT block).
- Cites the enhanced-region-support guide: PASS (URL in both places).
- must_not: OK. No region is added and no @region suffix is used.

## Scenario 4 - PASS
- SCP limits are 10,240 characters and 10 attached per root/OU/account: PASS (never-do-organization §3).
- 5120 characters and 5 attached are the RCP limits: PASS (same section; Quick Reference).
- skip_destroy only removes the policy from state and does not delete it: PASS (never-do-organization §6).
- AWS requires at least one attached SCP, and the last SCP cannot be removed: PASS (never-do-organization §3, "minimum 1; the last SCP cannot be removed").
- must_not: OK. The response accepts neither claim.

## Scenario 5 - PASS
- Approval needed only from invited members: PASS (Ask First table; the "joined by invitation" wording).
- Owner finalizes in the Console: PASS.
- Perpetual diff, because the API keeps reporting CONSOLIDATED_BILLING: PASS.
- Asks before applying: PASS (the table's Ask column: "Are all invited accounts ready to approve...?").
- must_not: OK. The response does not say all members must accept, and it does not say the change completes immediately.

## Flagged criteria
- S2 GovCloud: unsourced in the skill (see above).
- S1 "does not remove FullAWSAccess" is covered only by guidance. The skill gives no HCL for FullAWSAccess, so the check depends on the response not detaching it. This is acceptable but weak.
- S4 "last SCP cannot be removed": the skill states it only inside the never-do §3 prose. It is not in the SKILL.md body.

## Fixes needed
1. Check the organizations_account doc for the GovCloud note on close_on_deletion. If it is there, add it to the SKILL.md Ask First row. If it is not, drop that must_pass from Scenario 2.
2. Optional: add "min 1 attached SCP; last cannot be removed" to the SKILL.md Never Do skip_destroy row. It is only partly there now ("AWS requires at least one attached SCP"), so the gap is minor.
