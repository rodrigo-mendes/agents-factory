# Quality validation round 2 - provisioning-aws-eventbridge-v6

Counts: HIGH 0, MEDIUM 3, LOW 5. About 34 new claims sampled against the research file and the facts file. WebFetch was not available, so claims were checked against the research and facts files, not live pages.

## Round-1 status

| Id | Status | Evidence |
|---|---|---|
| H1 | FIXED | Never row SKILL.md:90 now reads "no permission path - neither a resource-based policy nor a role_arn with an execution role" and cites the provider and AWS pages. Instead = resource-based policy OR role_arn. This matches research sec. 6 (provider note) and sec. 7 (AWS "either role or resource-based policy"), so it is a documented fact. Consistent with Always bullet SKILL.md:60, hub never-do-patterns.md:14, anchor `#4-lambda-or-sns-target-with-no-permission-path` (heading never-do-targets.md:78 matches), blueprint never-do-targets.md:78-106, rules-targets.md:36-38, and eval scenario 1 (evaluation-scenarios.md:22, :28). Never rows: SKILL.md:84-94 = 11; blueprints = 3 (bus-and-rules) + 5 (targets) + 3 (scheduler-and-versions) = 11; hub lists 11. Count 11=11 confirmed. |
| H2 | PARTLY FIXED | Correct per row: S3 backend, version-constraints, enhanced-region, vpc = 2026-10-14 (SKILL.md:21,22,113,140; bibliography 23-26). Provider releases = 2026-10-22 (SKILL.md:19; bibliography 22). Unit pages = 2026-10-23. Blueprint headers are correct (foundation:3-4, never-do-scheduler:3-4). Remaining defect: see M-A. |
| M1 | FIXED | SKILL.md:50-51 split into two bullets, and the second says these are the skill's targets, not a page claim. |
| M2 | FIXED | SKILL.md:59 cites the DLQ page for "console does it automatically, not through the API". The "Terraform calls the API" inference is gone from the shipped text. |
| M3 | FIXED | SKILL.md:60 cites the AWS resource-based policies page for `events.amazonaws.com`. |
| M4 | FIXED | never-do-targets.md:94-95 explains the minimal CORRECT block and points to the rules-targets pattern that sets `source_arn`. |
| M5 | FIXED | "breaks installation" removed (SKILL.md:24-27). |
| M6 | FIXED | SKILL.md:123 now says "absence of evidence, not a guarantee" and names the ranges read (6.48.0-6.70.0, matches research sec. 2). |
| M7 | NOT FIXED (new sourcing gap) | SKILL.md:125 now cites the upgrade guide, but "move to the latest 5.x, get a clean plan, set `~> 6.0`" appears nowhere in the research or facts files, so it cannot be traced. See M-B. |
| M8 | FIXED | always-do-scheduler-integrations.md:13-14 tags the https claim (unverified, U6); register row U6 exists. |
| M9 | FIXED | always-do-scheduler-integrations.md:10-11 tags the connection inconsistency (unverified, U1); mapping rows exist. |
| L1 | FIXED | Rule-target retry row maps to U7 (unverified-and-risks.md:24, :54); L1 stays a coverage limit. |
| L2 | FIXED | No "U3" mention remains in the shipped skill. |
| L3 | NOT FIXED | evaluation-scenarios.md:102 now says "Cite a Security Hub control other than EventBridge.2, .3 or .4". It is off-topic for the scenario query, which mentions no Security Hub controls. |
| L4 | FIXED | `retention_days = 0` no longer appears (grep: 0 matches). |
| L5 | FIXED | `rate(2 hours)` now used (never-do-scheduler-and-versions.md:16, :27). |
| L6 | FIXED | "non-withdrawn patch" no longer appears (grep: 0 matches). |
| L7 | FIXED | SKILL.md:63 is now "Consider ... choose policy vs permission first, see Ask First". |
| L8 | PARTLY FIXED | `is_enabled` speculation removed; `encrypt = true` is now labelled "placeholder" (foundation.md:25) but is still not backed by a source. SNS is still not shown in HCL (acceptable, row text is sourced). |

## HIGH

None.

## MEDIUM

- M-A (H2 residue). The claim "Terraform 1.17.0 is stable since 2026-10-21" (SKILL.md:25; unverified-and-risks.md:9) cannot have been read on 2026-10-14. Bibliography item 21 (unverified-and-risks.md:84) says "1.16.6, 1.17.0" and the header at :62 dates item 21 as 2026-10-14. The facts file (F2) shows the 1.17.0 reading is 2026-10-22. Fix: date item 21 as read 2026-10-14 (1.16.6) and 2026-10-22 (1.17.0), or drop the date from the 1.17.0 bullet.
- M-B (M7 residue). SKILL.md:125 upgrade steps ("latest 5.x", "clean plan", `~> 6.0`) are not in the research or facts files, and "then run `terraform init -upgrade`" belongs to a different page (dependency-lock, F8) than the one cited. Fix: re-read the upgrade guide and record the quote in research, or remove the sentence.
- M-C. "aws v7 is planned" is cited to the upgrade guide (SKILL.md:27; unverified-and-risks.md:13). Research does not take that statement from the guide; the facts file (F3) gives "v7 planned" with a releases-page source and no quote. Fix: quote the guide in research, or cite the actual source, or soften to "no 7.x released" (which F3 does support).

## LOW

- SKILL.md:51 Always bullet has no URL (rule: one claim + one URL). It is a skill decision, so either add the constraints-page link for `~>` or move it to the version block.
- SKILL.md:63 bullet packs two statements (check + choose first). Acceptable, but could be split.
- Eval scenario 4 last must_not (L3) is vague and unrelated to the query.
- always-do-foundation.md:25 `encrypt = true` has no source (placeholder label only).
- unverified-and-risks.md:7 "re-verify after 30 days" has no source (a skill policy, but not marked as such). Bibliography item 17 (:80) attributes the console https statement to the scheduled-rules page; research sec. 10 does the same, tagged U6, so the attribution is only as good as the research.

## Always Do check (13 bullets, SKILL.md:50-63)

High-only, no tags in bullets, one claim each. All carry one URL except bullet 51 (see LOW). Bullet 63 refers to Ask First, which is acceptable. No orphan tags: U1, U2, U4, U5, U6, U7, M1, M2, M3 each appear in a mapped location; no unregistered tags in shipped text. The register mapping table (unverified-and-risks.md:44-58) matches the in-file tags. No F#/G#/M# ids or internal wording in the shipped files (grep). Plain notation holds.

## Grounding sample (all new this round)

Confirmed against research or facts (about 30): Terraform 1.16.6 date (F1); 6.70.0 latest and no 7.x (F3); 6.57.0 withdrawn (F4); region guide statement (F5); `~>` vs minimum (F6); `use_lockfile`/`dynamodb_table` (F7); identity needs Terraform 1.12 (F11); formerly CloudWatch Events (research sec. 1); bus name cannot contain `/` and `kms_key_identifier` forms (sec. 3); bus DLQ notes (sec. 3); archive name <= 48 and retention omitted = indefinite (sec. 9); event_pattern 2048/4096 (sec. 5); `state` values and the CloudTrail value restriction (sec. 5); `input_paths` <= 100 pairs, dot notation, "AWS" prefix (sec. 6); `role_arn` required list (sec. 6); Logs target role rule and principals (sec. 7); rule ARN forms (sec. 7); retry default 24 h / 185 (sec. 8); direct-to-DLQ error types (sec. 8); FIFO/same-Region DLQ (sec. 8); scheduler defaults and ranges (sec. 11); `group_name` forces new; universal target ARN form (sec. 11); pipe required args, `desired_state`, kms default (sec. 12); log levels; 6.54.0 and 6.66.0 entries (sec. 2); Security Hub EventBridge.2/.3/.4 (sec. 13); 5 targets per rule (sec. 13); permission `principal = "*"` with `aws:PrincipalOrgID` (sec. 4); API destination rate default 300 (sec. 10); Pipes without resource policies (sec. 7). Unsourced or untraceable: M-B and M-C above, plus the LOW items.

## Result

No HIGH. Round-1 items not fixed: M7 (upgrade-path sourcing, now M-B) and L3 (eval scenario 4 must_not). H2 partly fixed (M-A), L8 partly fixed.
