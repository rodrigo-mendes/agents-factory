# Evaluation Report: provisioning-aws-cloudwatch-v6 (round 1)

Method: inline simulation (no sub-agents). Each answer was composed using only SKILL.md and the linked blueprints, then judged. Source path: `packages/aws-terraform/.apm/skills/provisioning-aws-cloudwatch-v6/`.

## Summary

| Scenario | must_pass | must_not OK | Verdict |
|---|---|---|---|
| 1 Canonical log group + CIS alarm | 9/9 | 5/5 | PASS |
| 2 Composite lifecycle | 5/5 | 3/3 | PASS (thin on rename recipe) |
| 3 INFREQUENT_ACCESS misuse | 5/5 | 3/3 | PASS (M1 hedge) |
| 4 Composite vs CloudWatch.15 + heredoc | 5/5 | 3/3 | PASS |
| **Overall** | **24/24 (100%)** | **14/14** | **4/4 PASS** |

## Scenario 1 - Canonical

Simulated response: a terraform block with `required_version = "~> 1.16"` and aws `~> 6.69`. The S3 backend uses `use_lockfile = true` and no `dynamodb_table`. The log group has `retention_in_days = 365` and `deletion_protection_enabled = false`. A metric filter (root usage) has a transformation with no `default_value` or `dimensions`. A metric alarm uses `statistic = "Sum"` only, `treat_missing_data = "notBreaching"`, `actions_enabled = true`, and `alarm_actions = [aws_sns_topic.security_alerts.arn]`. The answer also states that default encryption is server-side AES-256-GCM, not a KMS CMK.

must_pass:
- Version constraints: PASS. Evidence: foundation §1 `required_version = "~> 1.16"`, `version = "~> 6.69"`.
- `use_lockfile`: PASS. Foundation §1 `use_lockfile = true`, with the note that `dynamodb_table` is deprecated.
- `retention_in_days = 365`: PASS. Foundation §2 and alarms §5.
- Explicit `deletion_protection_enabled = false`: PASS. Foundation §2 and the alarms §5 log group.
- `alarm_actions` set to an SNS ARN: PASS. Alarms §5 `alarm_actions = [aws_sns_topic.security_alerts.arn]`.
- `actions_enabled = true`: PASS. Alarms §5.
- `treat_missing_data = "notBreaching"`: PASS. Alarms §5 comment "error-only metric".
- No `statistic` plus `extended_statistic`: PASS. Alarms §5 uses `statistic = "Sum"` only.
- No `default_value` plus `dimensions`: PASS. Alarms §5 comment "do not combine".

must_not: all 5 OK. Nothing violated; Quick Reference line 110 gives the encryption fact correctly.

Skill defects seen while simulating:
- always-do-alarms §5 references `aws_sns_topic.security_alerts`, which is not defined in that snippet. `aws_sns_topic.alerts` is defined in §3 instead. A copy-paste would not plan.
- The §5 metric filter has no `default_value`. This is fine, but it never shows a filter pattern for a custom log group.

## Scenario 2 - Composite alarm lifecycle

Simulated response: destroying a child alarm while a composite depends on it will fail (Ask-First row, composite lifecycle). Use a two-stage update or `depends_on`. `alarm_rule` must have no leading or trailing whitespace, so wrap it in `trimspace()` and avoid bare heredocs. Changing `actions_enabled` on a composite forces a new resource, so set it once.

must_pass:
- Destroying a child fails: PASS. SKILL.md Ask First: "Destroying a child alarm while a composite depends on it will fail".
- Two-stage update or `depends_on`: PASS. Same row: "two-stage updates or `depends_on` may be needed".
- No leading or trailing whitespace: PASS. Always Do and alarms §4.
- `trimspace()`: PASS. Alarms §4 code.
- `actions_enabled` forces a new resource: PASS. Alarms §4 and Quick Reference.

must_not: all 3 OK. The skill gives the model no basis for recommending a bare heredoc or an unsafe destroy.

Weakness: the skill only says "two-stage updates or `depends_on` may be needed". It gives no concrete rename recipe, such as creating the new-named child, updating the composite rule, then removing the old child. It also does not mention `create_before_destroy`. The response is correct but generic. The "may be needed" hedge could weaken an LLM answer on a stricter judge.

## Scenario 3 - INFREQUENT_ACCESS with metric filter

Simulated response: no. IA does not support metric filters, subscription filters, Live Tail, or anomaly detection, and a metric filter fails at apply. Use STANDARD for any group that needs filters. The class is immutable after creation, so treat a change as destroy and recreate.

must_pass:
- Explicit rejection: PASS. never-do-logs §2 and the Never Do table row.
- Metric filters unsupported: PASS. "do **not** support metric filters".
- Subscription filters unsupported: PASS. Same line.
- STANDARD recommended: PASS. "`STANDARD` class for groups requiring filters".
- Immutable: PASS. never-do-logs §3: "its log class can't be changed ... Treat any change as destroy and recreate".

must_not: all 3 OK.

Notes:
- The immutability claim carries an M1 caveat (medium confidence): the Terraform provider page is silent on ForceNew. A judge may read the hedge as weakening "cannot be changed". The skill's guidance is still clear.
- The skill does not say that INFREQUENT_ACCESS lacks metric filters because of cost-driven feature limits. It does not offer cost alternatives for the user's underlying goal (ingestion cost), such as retention tuning or filtering what is logged. This is optional.

## Scenario 4 - Anti-pattern trap

Simulated response: not compliant. The child `alarm_actions = []` fails CloudWatch.15 (High), which evaluates metric alarms independently. The composite's `alarm_actions = [sns_arn]` does not satisfy it for children. The heredoc `alarm_rule` keeps a trailing newline and violates the no-whitespace rule. Fix: `alarm_actions = [aws_sns_topic.alerts.arn]` on the metric alarm, `alarm_rule = trimspace("ALARM(...) ...")`, and keep `actions_enabled = true`.

must_pass:
- Rejects `[]` and cites independent evaluation: PASS. never-do-alarms §1.
- Composite actions do not satisfy children: PASS. never-do-alarms §1 and alarms §3.
- Heredoc rejected for trailing newline: PASS. never-do-alarms §2.
- `trimspace()` or one-line alternative: PASS.
- `alarm_actions = [sns_arn]` on the metric alarm: PASS. never-do-alarms §1 CORRECT block.

must_not: all 3 OK.

## Ambiguous criteria

- S1 `treat_missing_data = "notBreaching"` is conditional ("or acknowledges"), which is fine. The scenario does not say whether the root-usage metric is error-only. The skill makes that call.
- S2 "recommends a two-stage update ... or depends_on" is satisfied by a mention alone. The criterion does not require a rename procedure.
- S3 "cannot be changed without destroy/recreate" conflicts with the skill's own M1 uncertainty about ForceNew. Reword the criterion to "AWS does not allow class change after creation; treat as destroy and recreate".
- S1 and S4 must_not items duplicate must_pass items. This is harmless but inflates counts.

## Fixes needed (short, none blocking)

1. `blueprints/always-do-alarms.md` §5: define `aws_sns_topic.security_alerts`, or reuse `alerts`. Add a note that the `aws_sns_topic` is declared in §3.
2. `blueprints/always-do-alarms.md` §4 or `never-do-alarms.md`: add a concrete child-rename recipe (create new child, update composite rule, then remove old child; `create_before_destroy`). The SKILL.md Ask First row currently says only "may be needed".
3. `blueprints/evaluation-scenarios.md` S3: reword the immutability criterion, as noted above.
4. `blueprints/always-do-patterns.md` and `never-do-patterns.md` exist but are not linked from SKILL.md's Quick Navigation. Check whether they are stale duplicates of the foundation/alarms/security and never-do-logs/alarms splits; link them or remove them. I did not read them.
