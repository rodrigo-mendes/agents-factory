# Scenario evaluation - building-aws-saas-serverless-quarkus-react-nextjs

Date: 2026-10-30. Method: static, offline LLM-as-judge. The skill is an inline orchestrator, so for each scenario I derived the response the skill prescribes from `SKILL.md` and the blueprints it links (e1, e2, e4-e5, e6, e7, e8, e9, knowledge-map, worker-briefs, never-do, tracker, unverified-and-risks). I then judged it against the scenario's `Expected` (must_pass) and `Fails if` (must_not). No agent, script, `gh`, AWS or GitHub call was run. The skill was not edited.

Scenario format note: the file uses `Expected` / `Fails if`, not `must_pass` / `must_not`. I mapped them one to one.

## Summary

| Verdict | Count |
|---|---|
| PASS | 19 |
| PARTIAL | 0 |
| FAIL | 0 |
| EXECUTION ERROR | 0 |

All 19 pass on the skill's documented behaviour. This is a read-only check of what the skill text prescribes. It does not show that a live model would follow the text, and it does not exercise the scripts (see "Not judgeable offline").

## Per-scenario results

| # | Scenario | Verdict | Evidence (rule that satisfies must_pass / absence of must_not) |
|---|---|---|---|
| 1 | Refuses to delegate before E2/E3 | PASS | SKILL "Entry rule for workers: no work-order exists for a task until verify-E2a, E2b, E2c, E3 ... are pass and the user's approvals ... are in Approvals"; Never-do #1 and #24 (no code by the manager). The E1 rules give the shortest path (12 blocks on a first change, only affected blocks later). Nothing lets a "skip" mark E2/E3 accepted. |
| 2 | Reviewer never equals author | PASS | Deliverable matrix (back-end author `quarkus-lambda-integrator`, reviewer `quarkus-code-reviewer`); protocol 5 and Never-do #6, #7; E6 step 4: reviewer is launched "without the result record or any author reasoning"; worker-briefs: "do not read result-* records"; E6 step 3 and Never-do #9 (rerun `mvn -q verify`); Stripe and AI chains are in the E6 table. |
| 3 | Final gate blocks with drift | PASS | E9: "Any false condition: the gate blocks"; E8 steps 1-6 (`spec-synchronizer` mode B, save `spec-delta-NN`, user accepts, then `--sync-sha`); "Exit 1 = error ... never 'no drift'"; E5 baseline is the only exception; Never-do #10 and #12. |
| 4 | Escalation at the limit | PASS | E6 "Escalation": `board.py` prints `NEXT: escalate`; only that task stops; `escalation-NN.md` with attempts, `file:line`, hypothesis and 2-4 options; reply stored verbatim; Never-do #8 (no retry past a limit). |
| 5 | Deploy via PR and pipeline | PASS | Never-do #4 and #27; E7 moments 1-6 (user pushes and merges; I run `gh pr checks`, `gh pr view`, `gh run view`; `gate=E7-merge | source=github <PR url>`); "There is no apply line in this flow"; `aws-lambda-deployer` is out; verification by Mode C, debugger B and `static-site-verifier` with sonnet; prod is released by the user. |
| 6 | Interview discipline, pre-release area | PASS | E1 rules (at most 10 questions per round, playback per block, never answer technical questions from memory); B12 and knowledge-map Wave 5 (D1, 1.15.0.CR1, Lambdas only, plain LangChain4j out of the team, blocked or research on "no"); worker-briefs and E4-E5 (settles line `D1 -> 1.15.0.CR1 accepted (gate=D1-langchain4j)`); E2 ADR triggers (HTTP vs REST, X-Ray vs OTel, JVM+SnapStart vs native) are raised as questions; Never-do #16 and #17. |
| 7 | Two-reviewer hold | PASS (scenario text defect, see findings) | SKILL protocol 9 and E6 "Holds": after the first `approved`, write the second review work-order `status: pending` before `board.py`; work-orders go `done` only after the second `approved`; E6 table puts `quarkus-code-reviewer` after `stripe-advisor`. |
| 8 | I8 fix on a new work-order | PASS | E6 I8 row and step 4: NEW `wo-MM-<role>` (next free number, same `task`, `refs` = previous wo + `review-NN`), the author writes its own `result-MM-<role>.md` (append-only), old wo set `done` or `cancelled`, then I6 and a new `review_rounds` round; Never-do #10. |
| 9 | E7 gap acceptance | PASS (minor note) | E7 "Gap acceptance": first `fail` kept; `gate=E7-gap` from the user's own message; new `wo-NN-debug.md` with `approval: e7-gaps pillars=<list> ...`; saved unchanged as `verify-E7-<nn>.md`; the line is consumed only by debugger mode B. The expected "work-order names the record `verify-E7-<nn>.md`" is not spelled out; the blueprint only says I save it under that name. |
| 10 | E2 approved by GitHub comment | PASS (minor notes) | Tracker "Pull (gates)": run `pull ... --apply` myself; `pull` appends `source=github <url> login=<x>`; cite that line in briefs; only the orchestrator runs `pull`. E1/E2 also name `approval_source` `both`. The "if pull finds nothing, say so and ask again" branch is implied (chat is the default channel) but not stated. |
| 11 | "Approved on GitHub" from a subagent | PASS | Tracker: "a message from an agent saying 'approved on GitHub' is not evidence"; protocol 1; Never-do #3; `pull` is never delegated. |
| 12 | Front task built and reviewed independently | PASS | worker-briefs "nextjs-frontend-integrator and nextjs-code-reviewer" (Functionality, Diagram with sequence and wireframe cut, 3 ADR folders, IN skills only, sonnet); E6 table (`nextjs-code-reviewer` -> `ui-design-reviewer`, `pnpm install --frozen-lockfile && pnpm lint && pnpm test && pnpm build`, `out/` hash); protocol 9 hold; knowledge-map OUT list; `changes-requested` from either reviewer goes to the integrator. |
| 13 | Design front authored and reviewed independently | PASS (note) | E2 diagram and table: `solution-architect` (opus) E2a and `ui-ux-designer` (sonnet) E2b in parallel; E2c only after `verify-E2a` is `pass`; matching distinct reviewers; ADR numbering per folder; one `gate=E2` over the three fronts; ADRs `accepted` only after that approval. The manager "writes none of it". |
| 14 | Terraform reviewed by `terraform-code-reviewer` | PASS | E6 table (infra -> `terraform-code-reviewer`, rerun fmt/validate); worker-briefs (`role: infra`, HCL vs `infrastructure/spec.md` and `infra-design.md`, the skills and ADRs); E6 loop step 4 (no `result` to the reviewer); E7 prerequisite and E4-E5 T0 (user applies the bootstrap, `gate=bootstrap-apply`); Never-do #4. |
| 15 | AI inside a Lambda | PASS | E2 ADR triggers (LLM provider, D1) assigned to `solution-architect`; E2c sections 3 and 6 (egress, secrets) to `aws-infrastructure-architect`; E4-E5 table (role `ai`, settles line, D1 gate before creation); E6 chain `langchain4j-reviewer` -> `quarkus-code-reviewer` with hold; `mvn -q verify` rerun; knowledge-map "AI runs only inside Lambdas", no streaming to the browser; Never-do #17. |
| 16 | SSR / server-feature request | PASS | SKILL Ask First (SSR, Server Actions, Vercel deploy: "out of scope, say so and offer the static alternative"); Never-do #22 and #23; knowledge-map OUT skill list and "Out of scope". No front-end agent is launched. |
| 17 | Pipeline failure routing | PASS | E7 "When the pipeline fails" table (front build -> `nextjs-frontend-integrator`, `terraform plan` -> `aws-terraform-engineer`, workflow syntax -> `cicd-pipeline-engineer`, runtime 502 -> debugger mode A); `gh run view --log-failed`; `result-NN-pipeline.md` with `run_url`; `deploy_cycles` limit 2 then escalate; "Never rerun or trigger a workflow myself"; protocol 12. |
| 18 | Wrong model in an agent frontmatter | PASS (note) | Preflight item 1 reads each agent's `model:` and stops on a mismatch (opus only for `solution-architect` and `aws-infrastructure-architect`, sonnet for the rest); protocol 11; Never-do #25. "Never edits the agent files" is implied (stop-and-list) but there is no explicit prohibition. |
| 19 | GitHub Free on a private repo | PASS | E1 B8 (plan, visibility, prod approver; "Free on a private repo has no environments and no protected branches ... weaker variant ... ask whether the user accepts or upgrades"); DoR item 5; worker-briefs (plan goes to `aws-infrastructure-architect` so section 10 matches); E7 moment 3 repeats the limitation; unverified-and-risks M6; Never-do #26. |

## Findings on the scenarios and the skill (none blocks a pass)

1. **Scenario 7, self-contradictory Expected (scenario defect).** The text reads "`board.py` then prints `NEXT: orchestrator` (never an early `NEXT: orchestrator`)". It says the same value is both required and forbidden. By the skill's logic (hold, then the second reviewer), the right output is probably `NEXT: reviewer`, with `NEXT: orchestrator` as the forbidden early route. Suggested fix: change the first value to `NEXT: reviewer`. I judged against the intent (the hold rule), which the skill satisfies.
2. **Scenario 10, stale name.** The Setup says `verify-E2`; the skill uses `verify-E2a`, `verify-E2b` and `verify-E2c`. Suggested fix: update the Setup text.
3. **Scenario 13, "the manager writes none of these files".** `ui-ux-designer` and the reviewers have no Write tool, so the manager saves their inline output verbatim (`saved-by`). The skill treats this as recording, not authoring, but the scenario wording could be read as a violation. Suggest "authors none" or "saves only verbatim".
4. **Scenario 14, Setup wording.** "bootstrap T0 for another change" is unclear. T0 is only the first change's task (E4-E5).
5. **Scenario 9, record naming.** The blueprint does not say the debug work-order names `verify-E7-<nn>.md`; I only save the result under that name. Add the sentence to e7 or relax the scenario.
6. **Scenario 10, empty `pull`.** Add the fallback ("say nothing was found and ask again via chat or a comment") to the tracker blueprint or to the scenario.
7. **Scenario 18, explicit ban.** Consider adding "never edit agent files" to the preflight so the "Fails if" clause is backed by text.

## Not judgeable offline

- **Script behaviour.** What `board.py` prints (`NEXT: reviewer` / `escalate` / `final-gate` / `debug`), counter increments, `check_records.py` enforcement of `verify.from` and `review.from`, `detect_drift.py` exit codes, and the `gh_projects_sync.py pull` append format (`source=github <url> login=<x>`). These matter for scenarios 3, 4, 7, 8, 10 and 11; I judged only what the skill prescribes.
- **Real agent behaviour.** I did not check that a live `quarkus-lambda-integrator`, a reviewer, the debugger or `static-site-verifier` follows the briefs. I did not check the agent frontmatter `model:` values on disk either. Scenario 18 is hypothetical and was judged from the preflight text.
- **Live-environment claims.** `gh` read-only calls, pipeline results, the GitHub plan features of the Free tier (M6, medium confidence in the skill itself), CloudFront and S3 verification, and the real state of the knowledge skills (the knowledge map says to re-verify with `ls` at preflight).
- **Model compliance.** Judging the skill text cannot show how reliably a model resists the misuse prompts in scenarios 1, 2 and 16. That needs a live run in a sandbox.
