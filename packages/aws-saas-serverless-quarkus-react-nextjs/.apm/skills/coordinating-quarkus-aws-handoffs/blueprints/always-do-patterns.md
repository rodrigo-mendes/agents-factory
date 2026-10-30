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
serve; E1-E4 work-orders use `task: spec`; E7 work-orders (observability mode C, debug, site verify) use `task: E7`. The I8 fix is a new
work-order `wo-MM-<role>.md` (same `task`, `refs`: previous wo + `review-NN`) that repeats the settles line (e.g. `D1 -> 1.15.0.CR1 accepted (gate=D1-langchain4j)`)
and writes its own `result-MM-<role>.md`; the review work-order copies the same line. Mark a work-order `done` only after its output record is accepted;
set every superseded work-order (an I8 or relaunch replaced it) `done` or `cancelled`, otherwise `all_tasks` never becomes done. Construction work-orders
(`code`, `ai`, `stripe`, `frontend`, `infra`) carry `## Functionality` and `## Diagram`; the scripts do not check them, the orchestrator does.

## 5. Spec impact in every author result

`spec_impact:` in the frontmatter and `## Spec impact` with Implemented / Divergences / Ambiguities /
Files. The board uses the field; `detect_drift.py` uses the Files list (front-end and `.github/` paths included).

## 6. Independent verification per stage

Write `verify-<stage>.md` from an agent or script that authored none of its `refs`. Stage ids: `E1`, `E2a`, `E2b`, `E2c`, `E3`, `E3b`,
`E4-<flow>` (one per design), `E4-index` (every R* owned by exactly one design), `E4-infra`, `E5`, `E7`, `E7-site` (no per-task verify in E6).
`verify-E7.md` is written by `aws-lambda-debugger` mode B (kind `verify`, role `debug`, `outcome: pass|fail`, sections Criteria + Evidence) after
`aws-observability` mode C produced `result-NN-observability.md`; `verify-E7-site.md` by `static-site-verifier` when the change has a front. The producer never verifies its own
result. Criteria come from the stage blueprints `e1`..`e9` of `building-aws-saas-serverless-quarkus-react-nextjs`, one `[x]`/`[ ]` line each.

## 7. Escalate by record

On `NEXT: escalate limit=<n> task=<t>`: copy `assets/escalation.template.md`, fill attempts with the record
ids, evidence with command output or `file:line`, a hypothesis, 2-4 options with impact; show it; record the
reply verbatim under `## Answer`; set `status: answered` and `answeredAt`.

## 8. Record the pipeline, never run it

After the user pushes and opens the PR, read the CI with `gh pr checks <pr>` and write `result-NN-pipeline.md` from `assets/result-pipeline.template.md`
with `role: pipeline-ci`. Only after the user merges (read `gh pr view`), write the gate `gate=E7-merge | source=github <PR url> | login=<user>` under `## Approvals`.
Read the CD run with `gh run view <id>` (add `--log-failed` for a failure) and write another `result-NN-pipeline.md` with `role: pipeline-cd`, the `run_url`, and the
`smoke_start_epoch` for the observability window. A failed job is routed to its owner (the failure table of the E7 blueprint) as a new work-order with the log excerpt.
The words of the user (or the own GitHub action of the user) are the only approvals; the live-check lines `approval: alarm-test`, `logs-insights` and `e7-gaps` are relayed
verbatim, one line each (same tail `by=<user> at=<UTC> relayed-by=building-aws-saas-serverless-quarkus-react-nextjs`; exact forms in [approval lines](./approval-lines.md)).

## 9. Put `role:` where the board needs it

`role: pipeline-ci | pipeline-cd` on pipeline records; `role: observability-live` (mode C) and `observability-review` (mode A) on observability records;
`role: ai` on AI results; on every review the `role` of the author to return to (`stripe`, `ai`, `frontend`, `infra`, `observability`, `cicd`; none for plain `code`).
After saving an inline record, re-run `check_records.py` and read the `NEXT:` line: a missing `role` shows up as a wrong or generic `NEXT`.
