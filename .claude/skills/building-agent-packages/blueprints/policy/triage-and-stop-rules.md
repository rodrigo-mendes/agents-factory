# Triage and stop rules (P6 loop)

Back to [SKILL.md](../../SKILL.md).

## Scoring

Per skill: `100 - 6 per HIGH - 2.5 per MEDIUM - 0.5 per LOW`. Package and audit: 0-10 as reported by the worker.

## Exit criteria (all)

No HIGH anywhere (validate, test, audit) · every skill >= 90 · package >= 8/10 · audit >= 8/10 · 100% of evaluation scenarios pass.

## Triage

| Finding | Action |
|---|---|
| HIGH | fix in the next round |
| MEDIUM, cheap and mechanical (tag, count, link, wording) | fix in the same pass |
| MEDIUM needing a judgement call, LOW | decision list for the user at G3; never fixed silently |
| Finding that contradicts `_family_facts` | the orchestrator re-verifies the fact first; fix the skill or the fact, not both blindly |

## Stop rules

- Stop when the exit criteria hold or `rounds` is exhausted; leftovers go to the G3 decision list.
- Regression (score drops vs previous round): stop and show the diff instead of fixing further.
- Later rounds re-evaluate only changed skills; re-audit only when agent, rules or routing changed.
- A worker "fix" is accepted only after the mechanical scripts pass again.
