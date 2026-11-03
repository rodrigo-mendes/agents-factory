# Evaluation Report: provisioning-aws-secrets-manager-v6 (round 1)

Method: inline simulation (no sub-agents), responses composed only from SKILL.md and the linked blueprints, then judged. Date 2026-10-23.
Skill path: packages/aws-terraform/.apm/skills/provisioning-aws-secrets-manager-v6/

## Scenario 1 - Canonical (write-only secret + rotation): PASS (6/6 must_pass, 0/3 must_not violated)

Simulated response: terraform block with `required_version = "~> 1.16"` and `version = "~> 6.69"` (always-do-secrets s1); `variable "db_password" { sensitive = true }`; `aws_secretsmanager_secret_version` with `secret_string_wo = var.db_password` and `secret_string_wo_version = 1` (s3); `aws_secretsmanager_secret_rotation` with `rotation_lambda_arn` and `rotation_rules { automatically_after_days = 30, duration = "3h" }` (always-do-rotation-policy s5); no rotation args on the secret.

| Criterion | Verdict | Evidence |
|---|---|---|
| required_version ~> 1.16 and aws ~> 6.69 | PASS | always-do-secrets s1 |
| secret_string_wo + _version | PASS | s3 |
| sensitive = true variable | PASS | s3 `sensitive = true` |
| rotation resource + rotation_lambda_arn | PASS | rotation s5 |
| automatically_after_days, duration "3h" | PASS | rotation s5 |
| no rotation args on secret | PASS | never-do-rotation s1 |
| must_not secret_string / ISO / force_delete | OK x3 | never-do s2, rotation s2, secrets s1 |

## Scenario 2 - Edge (disable rotation, remove policy): PASS (4/4, 0/2)

Simulated response: set `rotation_enabled = false` and omit `rotation_rules` (configurable since 6.62.0); use a `dynamic "rotation_rules"` block with `for_each = var.rotation_enabled ? [1] : []` to toggle. To remove a policy on `aws_secretsmanager_secret`, `policy = null` or `""` does not delete it, use `policy = "{}"`; `aws_secretsmanager_secret_policy` rejects `"{}"`.

| Criterion | Verdict | Evidence |
|---|---|---|
| rotation_enabled=false, omit rules | PASS | always-do-rotation s5; never-do-rotation s3 |
| since 6.62.0 or dynamic block | PASS | rotation s5 (both given) |
| null/"" does not delete, "{}" does | PASS | never-do-rotation s4; SKILL Never Do table |
| policy resource rejects "{}" | PASS | rotation s6; Quick Reference |
| must_not (keep rules / suggest null) | OK x2 | |

Gap (not a criterion failure): the skill does not say how to remove a policy that is managed by the separate `aws_secretsmanager_secret_policy` resource (for example destroy the resource). The query's second half is only answered for the inline `policy` argument. The response had to stay silent or mark this unverified.

## Scenario 3 - Misuse rejection: PASS (3/3, 0/2)

Simulated response: declines `aws_secretsmanager_secret_replica` ("no such resource appears in the docs") and shows the `replica { region = ... }` block; declines `force_delete_without_recovery` ("not an argument") and uses `recovery_window_in_days = 0`; cites the secret resource doc URL. Never emits either wrong construct as live code.

| Criterion | Verdict | Evidence |
|---|---|---|
| Rejects replica resource, uses block | PASS | never-do-secrets s5; SKILL Never Do |
| Rejects force_delete, uses window 0 | PASS | never-do-secrets s1 |
| Cites secret resource docs | PASS | `.../r/secretsmanager_secret.html.markdown` on every entry |
| must_not generate either | OK x2 | |

Ambiguity: the skill's `# WRONG` HCL blocks contain the forbidden constructs verbatim. A judge that scans for the strings could flag a response that quotes them while rejecting. The response should present them only as prose or clearly labeled WRONG.

## Scenario 4 - Anti-pattern trap: PASS (3/3, 0/3)

Simulated response: not fine. (1) `secret_string` with a sensitive var is still stored in state and plan files per the Terraform manage-sensitive-data doc; use `secret_string_wo` + `secret_string_wo_version` (Terraform >= 1.11). (2) `arn` on the version is deprecated (since 6.47.0), use `secret_arn`. (3) `duration = "P1D"` is ISO-8601; use hours such as `"3h"`.

| Criterion | Verdict | Evidence |
|---|---|---|
| sensitive still in state; recommend _wo (>= 1.11) | PASS | never-do-secrets s2; SKILL Never Do |
| arn deprecated, use secret_arn | PASS | never-do-secrets s4; migration section |
| duration in hours | PASS | never-do-rotation s2 |
| must_not x3 | OK | |

## Pass rate

- S1 100%, S2 100%, S3 100%, S4 100%.
- Overall: 4/4 scenarios PASS; 16/16 must_pass; 0/10 must_not violated.

## Fixes needed (short)

1. SKILL.md / never-do-rotation-policy.md s4: add how to remove a policy managed by `aws_secretsmanager_secret_policy` (destroy the resource), or tag it unverified. Source is unstated today.
2. Optional: S3 judge ambiguity from literal WRONG blocks. Add a note in the scenario that quoting a forbidden construct as a rejected example is allowed.
3. No criterion is unsourced; all 16 must_pass items are backed by skill content.
