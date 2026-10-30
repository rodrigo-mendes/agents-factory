# E7 - PR, pipeline, deploy and verification

Back to [SKILL.md](../SKILL.md). Precondition: board says all tasks `done` and prints `NEXT: orchestrator` (commit plan + PR text). **Agents never push, open PRs, merge, trigger workflows or apply**: the user does those; the pipeline `ci-app` / `cd-app` on GitHub does the build and the deploy; I only **read** the runs (`gh pr checks`, `gh pr view`, `gh run list|view`, all read-only) and record them. Technical procedure belongs to the CI/CD skills (`github-actions-cicd`), `debugging-aws-lambda` and `validating-aws-observability`.
The deploy agent `aws-lambda-deployer` and the approval lines (`approval: apply`, `approval: smoke`) left this flow: the plan commented on the PR and the PR review are the approval; smoke is the `_smoke-test` job of the pipeline (payload versioned and reviewed in the PR).

## Prerequisite: bootstrap (once per project)

Before the first pipeline: `aws-infrastructure-architect` designed it (`infrastructure/adr` for state and OIDC roles), `aws-terraform-engineer` wrote it (task T0), `terraform-code-reviewer` reviewed it. **The user applies it once, locally** with the commands in `result-NN-infra` (GitHub OIDC provider in AWS, roles `<env>-deploy` and `<env>-pr`, state bucket with lock) -> I record `gate=bootstrap-apply`. The user also configures on GitHub the "user-must-add" list returned by `cicd-pipeline-engineer`: branch protection of `main`, required check `ci-gate`, environments, variables with the role ARNs. I never apply and never create secrets.

## The 6 moments

```
1 PREPARE   I give the commit plan + PR text.            USER: git push, opens the PR on GitHub.
2 CI (PR)   ci-app.yml runs by itself: Java build, front build, tests, scans, terraform plan commented, ci-gate.
            I run `gh pr checks <pr>`; I write result-NN-pipeline (role pipeline-ci, run_url).
            failed -> the owner of the failed job fixes (back to E6, table below); the user pushes again.
3 MERGE     USER reviews code + the plan commented on the PR, approves and merges.
            I run `gh pr view <pr> --json state,mergedAt,url`; I record gate=E7-merge | source=github <PR url> | login=<user>.
4 CD (dev)  cd-app.yml runs by itself: build once -> apply dev -> Lambdas -> site on S3+CloudFront -> smoke (rollback on failure).
            I run `gh run list --branch main --limit 5` and `gh run view <id> --json conclusion,jobs,url`; result-NN-pipeline (role pipeline-cd).
5 VERIFY    independent, read-only, against the dev account:
            aws-observability Mode C -> result-NN-observability (role observability-live)
            aws-lambda-debugger mode B -> verify-E7        static-site-verifier -> verify-E7-site
6 PROD      USER releases prod (per the GitHub plan: environment reviewer / branch rule). The pipeline promotes the SAME artifact
            by digest -> apply prod -> deploy -> smoke. I repeat 4 and 5 for prod.
```

Without a protected `main` / environments (GitHub Free on a private repo) the user's approval is the merge itself and the role trusts `refs/heads/main`: the weaker variant accepted in E1 (B8) is repeated to the user at moment 3.
Records: a merge or a prod release approval is a `## Approvals` line citing the PR url or the run url; never an agent's text. Tracker on: `pull` may append `source=github <comment_url>` lines for gates ([tracker](tracker-github-projects.md)).

## `result-NN-pipeline.md`

`kind: report`, `role: pipeline-ci | pipeline-cd`, `from: building-aws-saas-serverless-quarkus-react-nextjs`, `outcome: success|failed`, frontmatter field `run_url`, and sections Done, Evidence (job names and conclusions from `gh`; for a failure the trimmed `--log-failed` excerpt), Suggested next step. `deploy_cycles` counts `pipeline-cd` records with `failed`. Next-step rules: ci -> `orchestrator` (success: user merges; failure: I route); cd success -> `observability` (Mode C); cd failed -> `orchestrator`.

## When the pipeline fails

I read the failed job with `gh run view <id> --log-failed` (read-only), copy the relevant excerpt into the new work-order, and count it in `deploy_cycles` (limit 2, then escalate).

| Where it failed | Who I route it to |
|---|---|
| Java build or tests | author of the task (`quarkus-lambda-integrator` / `stripe-integrator`) with the job log |
| Front build or tests | `nextjs-frontend-integrator` |
| Scan (Checkov / Trivy) | author of the file the scan names (infra, code or workflow) |
| `terraform plan` / `apply` | `aws-terraform-engineer` |
| Workflow syntax or permission | `cicd-pipeline-engineer` |
| Smoke or runtime error (502, timeout, ...) | `aws-lambda-debugger` mode A (diagnosis), then the owner of the fix |

Each fix is a new work-order -> normal E6 chain -> the user pushes again. Never rerun or trigger a workflow myself.

## Verification (moment 5) - orchestration only

Order: pipeline CD success -> `aws-observability` Mode C writes `result-NN-observability.md` (kind `report`, frontmatter `role: observability-live`; makes `board.py` print `NEXT: debug`) -> `aws-lambda-debugger` mode B writes `verify-E7.md` -> `static-site-verifier` writes `verify-E7-site.md` -> `board.py` prints `NEXT: final-gate` only with drift 0 and no pending delta.
All three are launched with `model: "sonnet"` and have read-only AWS access (read-only allowlists; no invoke, no alarm test, no apply).

| Check | Verifier | What |
|---|---|---|
| Logs, metrics, traces, alarms, dashboards (5 pillars) | `aws-lambda-debugger` mode B (scripts of `validating-aws-observability`) | JSON logs with `requestId` + `tenantId` and no PII; business metrics; end-to-end trace (check the segment destination first); alarms in a valid state; dashboards render data; the deployed Lambda matches the pipeline run |
| Site | `static-site-verifier` | routes return 200 over HTTPS; security and cache headers; CloudFront with OAC, minimum TLS, WAF; live content equals the run's artifact (hash); the content hash is `portable.py dirhash` (the same method as the integrator); no browser smoke here: the verifier has a Bash hook that allows none |

Work-orders: `wo-NN-observability.md` (mode C, with the smoke start time from the pipeline run), `wo-NN-debug.md` (`mode: B`, pillars, refs = pipeline result + observability result), `wo-NN-site-verify.md`. The debugger and verifier return records inline; I save `verify-E7.md` (`verify-E7-<nn>.md` after a gap acceptance) and `verify-E7-site.md` (`from: static-site-verifier`, `kind: verify`, `stage: E7-site`, Criteria + Evidence). Producers never write the acceptance.
Billable read actions (Logs Insights queries, X-Ray trace retrieval) need a relayed line (`approval: logs-insights scope=<log-group|xray> window=<minutes> by=<user> at=<UTC> relayed-by=building-aws-saas-serverless-quarkus-react-nextjs`) in the work-order; without it pass no flag: the gated checks are `not verified` (WARN). An alarm firing test only with the user's explicit `approval: alarm-test ...` and by a worker allowed to run it (the debugger never does).
**Gap acceptance:** the debugger first returns `fail`; I show the pillars and reasons; only after the user's own message accepts them I write `gate=E7-gap`, relaunch the debugger with a new `wo-NN-debug.md` carrying `approval: e7-gaps pillars=<list> by=<user> at=<UTC> relayed-by=building-aws-saas-serverless-quarkus-react-nextjs`; it emits `pass` with those pillars under `## Gaps`; I save it unchanged as `verify-E7-<nn>.md` (the first `fail` is kept).
Before running `board.py` on the debugger's verify, set `status: done` on every `wo-*-observability` and `wo-*-debug`. With a front end, create `wo-*-site-verify` (`status: pending`) at the START of E7 and set it `done` only after `verify-E7-site` exists and is saved: otherwise the debugger's pass plus `all_tasks: done` fires `final-gate` before the site is verified (audit finding S1). The final-gate rule requires `all_tasks: done`.

## Prod

After dev passes, the user releases prod as the GitHub plan allows; I read the prod run (`gh run view`) into `result-NN-pipeline.md` (`pipeline-cd`) and repeat moment 5 for prod. E9 needs the last prod `pipeline-cd` result to be `success`.

## Acceptance (Deploy ready + Observability ready)

1. CI result `success` and the user's merge recorded (`gate=E7-merge`); the plan commented on the PR had no unexpected destroy (I read it from the PR comment, I never run `terraform plan`).
2. CD dev `success` (apply, deploy and smoke jobs green; cold start within the E2a NFR from the evidence).
3. `result-NN-observability.md` exists; the latest `verify-E7` = `pass` for all 5 pillars, or every `not verified` pillar listed in Gaps and accepted by the user; `verify-E7-site` = `pass` when the change has a front end.
4. Same for prod. `board.py` -> `NEXT: final-gate` only with drift 0 and no pending delta (run `detect_drift.py --include-worktree` first).

## Failures worth stating to the user plainly

- Debugger `not determined` at `debug_rounds`: escalate with what each round eliminated.
- A rollback by the pipeline can leave Terraform state behind the alias/origin path (drift risk named in the CI/CD skills): tell the user and plan a reconcile task.
- Branch protection, the required check or environments missing on GitHub: the user must add them (list "user-must-add"); I cannot read all of this with `gh` without admin rights: say what I could not verify.
