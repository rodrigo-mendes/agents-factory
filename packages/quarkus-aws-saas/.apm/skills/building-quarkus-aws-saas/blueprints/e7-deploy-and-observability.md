# E7 - Deploy and observability verification

Back to [SKILL.md](../SKILL.md). Precondition: board says all code and infra tasks `done` (`NEXT: deploy`). Technical procedure belongs to skills
`deploying-aws-lambda`, `debugging-aws-lambda`, `validating-aws-observability`; this blueprint is only the orchestration.

Order of E7 (one producer, one independent verifier):
**deploy (`aws-lambda-deployer`) -> `aws-observability` Mode C writes `result-NN-observability.md` (kind `report`) -> `aws-lambda-debugger` mode B writes `verify-E7.md` (kind `verify`, role `debug` derived from `from`, `pass|fail`, Criteria/Evidence) -> board prints `NEXT: final-gate`.**
`aws-observability` in E2/E6 only reviews the spec (Mode A) and writes observability Terraform (Mode B); it never verifies.

## Sequence

1. **Deploy work-order** `wo-NN-deploy.md`: `artifact` (path from the code result, with SHA-256 I compute myself), `terraform_dir` (from the `result-NN-infra` record), `function_name`, `alias`,
   `region`, AWS profile/identity name (never credentials), `limits.deploy_cycles`, `smoke` (payload + expected `StatusCode`, no `FunctionError`, expected body),
   optional `traffic_strategy`, `upload_path`, rollback authorisation. Ask the user for every item the work-order template cannot fill (Ask First of `deploying-aws-lambda`).
2. **Launch `aws-lambda-deployer` WITHOUT an approval line** (first launch, work-order `wo-NN-deploy.md`). It stops after `terraform plan -out` and returns `outcome: needs-input` with the plan summary, plan file name,
   plan SHA-256 and `PREV` (alias target before the release). I save it as `result-NN-deploy.md`; this first `needs-input` deploy-report **is kept** as the plan-gate evidence (records are append-only: never overwrite or edit it).
3. **Show the plan to the user** (counts of add/change/destroy, anything unexpected, `PREV`) **together with the smoke payload** (file and sha256) and ask the user to approve both. Unexpected destroys, replacements, role or reserved-concurrency changes: ask first, no approval implied.
4. **Relay the approvals.** Only after the user's own message approves *this* plan and *this* smoke payload: append to `## Approvals` (`gate=E7-apply, subject=<planfile> sha256=<hash>`; `gate=E7-smoke, subject=<payload sha256>`), then add the lines to
   a **new work-order** `wo-MM-deploy.md` (next free number; same fields as the first, `refs` = the first deploy-report, plus the relayed approval lines) and relaunch the deployer on it; its record is `result-MM-deploy.md`. Every deployer launch gets its own work-order number and result; none is rewritten (exact formats in [worker briefs](worker-briefs.md#approval-line)):
   `approval: apply plan=<planfile> sha256=<hash> by=<user> at=<UTC timestamp> relayed-by=building-quarkus-aws-saas`
   `approval: smoke payload=<file/sha256> by=<user> at=<UTC timestamp> relayed-by=building-quarkus-aws-saas`
   One apply line covers exactly one apply of that exact plan. **Relaunch rule:** a relaunch that carries an approval for an existing planfile skips re-planning and goes straight to apply. A re-plan (new artifact hash, drift) voids the line: show the new summary and ask again. Canary steps need one line each.
   Rollback that moves the alias needs `approval: rollback alias=<alias> to=<PREV version> by=<user> at=<UTC timestamp> relayed-by=building-quarkus-aws-saas`.
5. Deployer finishes (waiters, publish, alias, smoke; the real invoke is its smoke step, authorised by `approval: smoke`). Save/check `result-MM-deploy.md` (kind `deploy-report`), `check_records.py`, `detect_drift.py`, `board.py`.
6. `outcome: failed` -> `NEXT: debug`: `wo-NN-debug.md` mode A (limits `debug_rounds`, skills, symptom, window, deploy-report ref); launch `aws-lambda-debugger`; save its inline answer as
   `diagnosis-NN.md`; route the fix work-order to the **owner it names** (code -> integrator, infra -> terraform engineer, deploy -> deployer) as a new task; next deploy is a new `wo-NN-deploy.md` that needs a new plan and a new approval.
   `limits.deploy_cycles` (default 2) reached -> escalate; **no new apply without the user**.
7. `outcome: success` -> `NEXT: observability`: write `wo-NN-observability.md` (mode C) with `smoke start` = `smoke_start_epoch` from the deploy-report Evidence, then launch `aws-observability` **Mode C** (post-deploy; brief in [worker briefs](worker-briefs.md#aws-observability)). It collects what exists in the deployed account (log groups, alarms, X-Ray groups, dashboards) and writes `result-NN-observability.md` (kind `report`, frontmatter `role: observability-live`; that field is what makes `board.py` print `NEXT: debug` for `success` or `partial`). It does not verify.
8. Then the independent verification (below): `wo-NN-debug.md` mode B (same work-order name as mode A, field `mode: B`) -> `aws-lambda-debugger` -> I save `verify-E7.md`. Before running `board.py` on it, set `status: done` on every `wo-*-deploy.md` (first and relaunch), `wo-NN-observability.md` and `wo-NN-debug.md` (all `task: deploy`) once their records are saved; the final-gate rule requires `all_tasks: done`, so a pending deploy-task work-order sends a `pass` to the fallback instead of `final-gate`.

## Observability verification (5 pillars)

`aws-observability` provisioned what E2 listed (log groups + retention, alarms with thresholds, X-Ray groups/sampling, dashboards) as an infra task in E6 **before** the deploy (Mode B) and, after the deploy, documents the live state in `result-NN-observability.md` (Mode C).
The **independent** acceptance runs after it; the debugger executes the read-only scripts of `validating-aws-observability` (`check-logs`, `check-metrics`, `check-traces`, `check-alarms`, `check-dashboards`):

| Pillar | Check (read-only) | Verifier |
|---|---|---|
| Logs | JSON, `requestId` + `tenantId`, no PII | `aws-lambda-debugger` mode B using the `validating-aws-observability` scripts |
| Metrics | business metrics published | same |
| Traces | end-to-end trace (check the segment destination first; with Transaction Search enabled `BatchGetTraces` cannot find traces, use the Logs path) | same |
| Alarms | exist and in a valid state (not stuck in `INSUFFICIENT_DATA`) | same |
| Dashboards | render data | same |

Launch the debugger in mode B (brief in [worker briefs](worker-briefs.md#aws-lambda-debugger)); save its inline answer as `verify-E7.md` (gap-acceptance relaunch: `verify-E7-<nn>`) (`from: aws-lambda-debugger`, `kind: verify`, `stage: E7`, role `debug` derived from `from`, outcome `pass|fail`, sections Criteria + Evidence;
keep its Checklist/Gaps/Verdict as extra headings, `refs` = deploy-report and `result-NN-observability.md`). The producers (`aws-observability`, integrator) never write the acceptance.
Scripts that start read actions with a cost (Logs Insights queries, X-Ray trace retrieval) need relayed approval lines, one per scope: `approval: logs-insights scope=<log-group> window=<minutes> by=<user> at=<UTC timestamp> relayed-by=building-quarkus-aws-saas` for the logs and `approval: logs-insights scope=xray window=<minutes> ...` for the traces, in the `wo-NN-debug.md` (and in the Mode C work-order). Without them pass no approval flag: no billable call is made, retention and the trace destination are still checked, and the gated checks are `not verified` (WARN).
**Alarm firing test**: never by default; only with the user's explicit approval of that action (`approval: alarm-test ...`), by a worker that is allowed to run it (the debugger never runs `trigger-alarm-test.py`). **The debugger never invokes the function**: a real invoke belongs to the deployer's smoke step (`approval: smoke`); if the pillars need fresh traffic, the user approves a smoke payload for the deployer, not an invoke by the debugger.

## Acceptance (Deploy ready + Observability ready)

1. `terraform plan` had no unexpected destroy; apply approved by the user (line recorded).
2. Smoke test of each happy scenario OK with the approved payload; cold start within the E2 NFR target (value from the evidence).
3. `result-NN-observability.md` exists; the latest E7 verify (`verify-E7.md`, or `verify-E7-<nn>.md` with `id: verify-E7-<nn>` after a gap-acceptance relaunch; the first `fail` is kept) = `pass` for all 5 pillars, or every `not verified` pillar listed in Gaps and accepted by the user. Gap acceptance: the debugger first returns `fail`; I show the pillars and reasons, and only after the user's own message accepts them I write `gate=E7-gap` under `## Approvals` and relaunch the debugger with a new `wo-NN-debug.md` (mode B) carrying `approval: e7-gaps pillars=<comma list> by=<user> at=<UTC timestamp> relayed-by=building-quarkus-aws-saas`. It then emits `pass` with those pillars under `## Gaps` as "accepted by the user (approval line ...)"; I save it unchanged. A pillar not on the line keeps `fail`.
4. `board.py` -> `NEXT: final-gate` only with drift 0 and no pending delta; otherwise follow `NEXT:` ([E8](e8-reverse-sync.md)). Run `detect_drift.py --include-worktree` before this check (code stays uncommitted until E9).

## Failures worth stating to the user plainly

- Deployer `needs-input` without a plan = the work-order is incomplete: ask, do not guess.
- Debugger `not determined` at `debug_rounds`: escalate with what each round eliminated.
- A rollback leaves Terraform state behind the alias (drift risk named in `deploying-aws-lambda`): tell the user and plan a reconcile task.

A `## Cleanup proposal` in a successful deploy-report is not a blocker: E7 continues; after E9 the orchestrator shows the proposal to the user; the deployer never runs `delete-function`, so the user runs the listed commands themselves if they want.
