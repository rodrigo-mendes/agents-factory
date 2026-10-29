# Always-Do Patterns (protocol v1)

Back to [SKILL.md](../SKILL.md). Each pattern: the rule, why, and the concrete command or snippet.

## 1. Read before analysing

Read the existing records of the scope and their `refs` before doing any analysis; skip what is
already recorded. Context comes from the files, never from the conversation.

```bash
ls <handoff-dir>                       # what exists
python scripts/board.py <handoff-dir> --profile <profile.yaml>   # state + NEXT line
```

## 2. One output record per step, from the template

Copy the matching template from `assets/` ([work-order](../assets/work-order.template.md),
[result](../assets/result.template.md), [review](../assets/review.template.md),
[verify](../assets/verify.template.md), [spec-delta](../assets/spec-delta.template.md),
[escalation](../assets/escalation.template.md)). Every `report` record carries `## Spec impact`
(or the profile's replacement section) so drift can be computed.

## 3. Name report records `result-<nn>-<role>.md`

Factory convention: the `kind` stays `report`, the **file name** is `result-<nn>-<role>.md` (or the
profile's `records:` pattern). `deploy-report.md` and `diagnosis-report.md` are the generic
defaults for their kinds.

## 4. Validate after every record

```bash
python scripts/check_records.py <handoff-dir> --profile <profile.yaml>   # exit 0 = OK
python scripts/detect_drift.py <repo> --change <handoff-dir>             # spec.kind openspec, after the baseline: exit 0 none, 2 drift; 1 = error / no lastSyncedSha
python scripts/board.py <handoff-dir> --profile <profile.yaml>           # prints NEXT:
```

On a non-zero `check_records.py`, return the error lines to the author (and bump the record's
`rejections` field); then act on `NEXT:` only.

## 5. Independent verification

Each acceptance needs a `verify` record whose `from` is not the author of the work (another agent,
a script or the user). See [record kinds](./record-kinds.md#kinds).

## 6. Escalate at the limit, record the reply verbatim

When `board.py` prints `NEXT: escalate`, write an `escalation` record (attempts, evidence,
hypothesis, 2-4 options with impact), show it to the user, then store the user's reply verbatim
and set `status: answered`. Counters restart after the answer; independent tasks continue.

## 7. Limits as parameters

Pass per-run limits as arguments, keep project overrides in the override file:

```bash
python scripts/board.py <dir> --profile <p.yaml> --override openspec/handoff-profile.yaml \
  --args limits.review_rounds=4
```

Precedence: profile default < project override < run arguments. Values are integers >= 1.

## 8. Single hand-off line

End every agent step with one line: `Hand off: run /<command> (@<agent>) - <why>. Context: <root>/<record>.md`
(user-mediated mode), or return the record path to the orchestrator (orchestrated mode).
