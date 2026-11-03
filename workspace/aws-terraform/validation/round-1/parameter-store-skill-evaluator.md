# Evaluation Report: provisioning-aws-parameter-store-v6 (round 1)

Method: no sub-agents. Each response was written from SKILL.md and its blueprints only, then judged. Skill path: packages/aws-terraform/.apm/skills/provisioning-aws-parameter-store-v6/

## Scenario 1: Canonical (config + secret)
Response: a terraform block with `required_version = "~> 1.16"` and aws `~> 6.69` (always-do-foundation §1). `/myapp/prod/db/host` is a String with `insecure_value`. `/myapp/prod/db/password` is a SecureString with `value_wo` + `value_wo_version = 1` and `key_id` set to a CMK arn (always-do-secrets §4). I also asked whether key-policy control is needed.

must_pass:
- Version constraints: PASS. Evidence: `required_version = "~> 1.16"`, `version = "~> 6.69"`.
- Names start with `/` and use a hierarchy: PASS.
- `value_wo` + `value_wo_version`: PASS.
- `insecure_value` for the non-secret String: PASS.
- `key_id` set to a CMK, or the user is asked: PASS. The skill's "set key_id to a CMK when you need key-policy control" plus the §4 example cover it.

must_not:
- `value` on the SecureString while claiming a clean state: OK.
- `insecure_value` on the SecureString: OK.
- Pin 6.57.0: OK.

Verdict: PASS (5/5, 3/3).

Note: the §4 example uses `aws_kms_key.params`, which is out of scope (KMS sibling skill), so the response must either reference an existing key or stub one. Its `value_wo` source (`ephemeral.random_password`) is tagged unverified (U2). For this query a `var.db_password_wo` input would be cleaner.

## Scenario 2: Tiers and Intelligent-Tiering
Response (from the Ask First rows):
- Intelligent-Tiering is a default-tier setting. It creates Standard unless the request needs Advanced, then upgrades automatically and one-way.
- Advanced to Standard in Terraform recreates the resource, and AWS says downgrade is not possible.
- Advanced is charged.
- I asked: "Is Advanced needed? May parameters silently become billable Advanced?"

must_pass: all 4 PASS. Evidence: the Intelligent-Tiering and Tier rows in SKILL.md Ask First.
must_not: both OK. The skill does not describe a third tier or a persistent error / `state rm`.

Verdict: PASS (4/4, 2/2).

## Scenario 3: Misuse rejection
Response: reject `insecure_value` on a SecureString because it "cannot be used with that type" (never-do-secrets §1, with the WRONG block quoted). Offer `value_wo` + `value_wo_version`. Say the ephemeral resource requires `arn`, not `name` (never-do §4), and show `arn = aws_ssm_parameter.x.arn`.

must_pass: all 3 PASS.
must_not: both OK. The `name` in the WRONG block was quoted as a rejected example only.

Verdict: PASS (3/3, 2/2).

## Scenario 4: Ephemeral does not protect writes
Response:
- No. Writing a SecureString with `value` stores the plaintext in state, and the ephemeral resource only reads (always-do-secrets, line after §4).
- Use `value_wo` + `value_wo_version` (Terraform >= 1.11).
- The minimum CLI version for ephemeral resources is not stated on the page (unverified, U1). The semantics are medium confidence (M1).

must_pass: all 4 PASS.
must_not: both OK.

Verdict: PASS (4/4, 2/2).

Note: always-do-secrets §5 shows `value_wo = ephemeral...value`, which is the correct pattern. A reader could confuse this with the user's `value` pattern, so the §5 text should say it explicitly.

## Scenario 5: Legacy claims
Response:
- `overwrite` is documented on the current resource page: default `false` on create, `true` afterward. It is an Ask First decision: adopt by overwrite or import? The page points to lifecycle rules such as `ignore_changes`.
- None of Security Hub SSM.1-SSM.7 evaluates Parameter Store parameters (as of 2026-10-23).
- I stated no name-length or character limits (unverified, U3).

must_pass:
- Overwrite documented, default false then true: PASS (weak). The default behavior is explicit in the Ask First row. "No deprecation marker" is not stated anywhere in the skill, so I had to infer it from the page being cited as current.
- Ask First, adopt vs import: PASS.
- Security Hub: PASS (Quick Reference row).

must_not: all 3 OK.

Verdict: PASS, with a caveat on criterion 1 (see fixes).

## Summary
| Scenario | must_pass | must_not | Verdict |
|---|---|---|---|
| 1 | 5/5 | 3/3 OK | PASS |
| 2 | 4/4 | 2/2 OK | PASS |
| 3 | 3/3 | 2/2 OK | PASS |
| 4 | 4/4 | 2/2 OK | PASS |
| 5 | 3/3 (one weak) | 3/3 OK | PASS |

Overall: 5/5 scenarios PASS; must_pass is 19/19 and must_not is 12/12.

## Fixes needed (minor)
1. **S5 criterion 1 is partly unsourced.** SKILL.md (Ask First, `overwrite` row) never says the current page has no deprecation marker, and never addresses the "deprecated since v5.0 / perpetual diffs" claim. Either add a sentence ("the resource page shows no deprecation notice for `overwrite`, checked 2026-10-23") or relax the criterion to "does not claim overwrite is deprecated".
2. **S1 example dependency.** The §4 example references `aws_kms_key.params` and an unverified `ephemeral.random_password`. Consider a `var`-based `value_wo` example. The existing pattern tags U2 as unverified, but the example is not copy-ready.
3. **S4 clarity.** Add a one-line note in always-do-secrets §5 that `value_wo = ephemeral...` is the safe write, and `value =` is not.
