# Always-do patterns

Back to [SKILL.md](../SKILL.md). Commands assume the variables of the SKILL's Verification Loop
(`GEN`, `ME`, `H`).

## 1. Write the work-order from the template, with effective limits

Use the matching template in `assets/`. Fill `task`, `requirements`, the ADR paths, the skills (see
[roles-and-skills](./roles-and-skills.md)) and `## Limits` with the **effective** values from the
last `status.md` (source shown there), then validate:

```bash
python $GEN/scripts/check_records.py $H --profile $ME/assets/handoff-profile.yaml   # expect OK
```

## 2. After every record: check, drift, board, act

```bash
python $GEN/scripts/check_records.py $H --profile $ME/assets/handoff-profile.yaml
python $GEN/scripts/detect_drift.py . --change $H --include-worktree     # exit 2 -> re-run board.py with --args drift=true
python $GEN/scripts/board.py $H --profile $ME/assets/handoff-profile.yaml [--override openspec/handoff-profile.yaml] [--args limits.review_rounds=4]
```

Follow the single `NEXT:` line. `--args` goes last. Non-zero from `check_records.py`: return the error
lines to the author and write `rejections: <n>` on the record.

## 3. Per-run limits

Pass them as arguments of the orchestrator command and as `--args limits.<name>=<int>`; the board
records `args` as the source. A project-wide change goes in `openspec/handoff-profile.yaml`
(`limits:` / `quality:` only). `0` only with `limits_zero_confirmed: true` after the user confirms.

## 4. Task discipline

Every work-order has `task:`. Review, debug and verify work-orders reuse the task of the work they
serve; deploy uses `task: deploy`. The I8 fix is a new work-order `wo-MM-code.md` (same `task`, `refs`: previous wo + `review-NN`) that repeats the settles line (e.g. `D1 -> 1.15.0.CR1 accepted (gate=D1-langchain4j)`) and writes its own `result-MM-code.md`; the review work-order copies the same line. Mark a work-order `done` only after its output record is accepted;
set every superseded work-order (an I8 or relaunch replaced it) `done` or `cancelled`, otherwise `all_tasks` never becomes done; mark a failed deploy work-order `cancelled` once its diagnosis is routed (a redeploy, or the relaunch after the plan gate, is a new work-order).

## 5. Spec impact in every code or infra result

`spec_impact:` in the frontmatter and `## Spec impact` with Implemented / Divergences / Ambiguities /
Files. The board uses the field; `detect_drift.py` uses the Files list.

## 6. Independent verification per stage

Write `verify-<stage>.md` from an agent or script that authored none of its `refs`. Stage ids: `E1`..`E4`,
`E7` (no `verify-E5`, no per-task verify). `verify-E7.md` is written by `aws-lambda-debugger` mode B
(kind `verify`, role `debug`, `outcome: pass|fail`, sections Criteria + Evidence) after
`aws-observability` mode C produced `result-NN-observability.md`; the producer never verifies its own
result. Criteria come from the stage blueprints `e1`..`e9` of `building-quarkus-aws-saas`, one
`[x]`/`[ ]` line each.

## 7. Escalate by record

On `NEXT: escalate limit=<n> task=<t>`: copy `assets/escalation.template.md`, fill attempts with the record
ids, evidence with command output or `file:line`, a hypothesis, 2-4 options with impact; show it; record the
reply verbatim under `## Answer`; set `status: answered` and `answeredAt`.

## 8. Relay the apply approval verbatim

When the user approves a plan, paste their approval into `## Approvals` of `status.md` and into the deploy
work-order as `approval: apply plan=<planfile> sha256=<hash> by=<user> at=<UTC> relayed-by=building-quarkus-aws-saas`.
One line per apply; a regenerated plan voids the old line. The relaunch is a new `wo-MM-deploy.md`
(append-only; `refs` the first deploy-report); a work-order carrying an apply approval for
an existing planfile skips re-planning; the deployer re-verifies its `sha256` now.

The user's own words also pre-authorise, one line each (same tail `by=<user> at=<UTC>
relayed-by=building-quarkus-aws-saas`): `approval: smoke payload=<file or sha256>` (asked together with
the plan), `approval: alarm-test alarm=<name>`, `approval: logs-insights scope=<log-group or "xray">
window=<minutes>` (billable Insights queries and X-Ray retrieval in E7, one line per scope). Exact forms: SKILL.md, "Apply-approval line contract".
