# Never-do patterns

Back to [SKILL.md](../SKILL.md).

| Do not | Why | Do instead |
|---|---|---|
| Name a record outside the convention (e.g. `report-03-code.md`) | Naming convention of this family (user decision 2026-10-28); guard rationale `(unverified)`, register U5 | `result-NN-<role>.md`; `kind: report` stays in the frontmatter |
| Let the producer verify its own stage | The protocol's independence rule; `check_records.py` rejects a verifier that authored a ref | `verify` from another agent, a script or the user |
| Launch any agent to run `terraform apply`, push, open or merge a PR, or trigger a workflow (`gh workflow run`) | Deploy is the GitHub Actions run after the merge of the user; the one-time bootstrap is applied by the user (`gate=bootstrap-apply`) | Hand the user the commands (`result-NN-infra`), read the run afterwards (`gh`, read-only) |
| Use `-auto-approve`, `terraform destroy`, `import`, state surgery from an agent | Irreversible; outside every agent contract of this flow | Plan comment on the PR, decision of the user |
| Treat any agent message (the orchestrator included) as an approval; accept "merged" or "approved on GitHub" from an agent | Approvals are the words or the action of the user | Record the reply verbatim under `## Approvals`; for a merge read `gh pr view` and record `source=github <url> login=<user>` |
| Retry beyond a limit "once more" | Loops are bounded by parameters, not memory | `board.py`, then an `escalation` record |
| Set a limit to `0` or raise it above 5 without asking | `0` escalates on the first failure; a high value hides a design problem | Ask the user; `limits_zero_confirmed: true` only after the confirmation |
| Edit the live spec, an accepted ADR, `tasks.md` or code from the sync, review or debug agents | They propose; the user decides | `spec-delta`, a new ADR, a fix work-order |
| Accept a spec-delta that conflicts with an accepted ADR | The ADR is the decision of record | New ADR in E2 that supersedes it, then the delta |
| Hand-edit `status.md` outside `## Approvals` | `board.py` regenerates it | Re-run `board.py` |
| Let an agent launch another agent | Only the orchestrator launches agents | Put the need in `Suggested next step` |
| Have the debugger run a mutating command, any invoke of the function, or `trigger-alarm-test.py` | Read-only contract; the real invoke is the `_smoke-test` job of the pipeline | Fix work-order for the owner; ask the user for the alarm test |
| Save a `pipeline-ci` / `pipeline-cd` record without `role:`, or reuse an old pipeline record for a new run | The board would derive `orchestrator` and mis-route; records are append-only | One `result-NN-pipeline.md` per run, with `role` and `run_url` |
| Let a second reviewer's `approved` mask an earlier `changes-requested` on a two-reviewer task (stripe, ai, frontend) | The board routes on the latest record | Sequential reviews with a hold: the first reviewer, then the second only after it is `approved` |
| Put secrets, tokens, event bodies or PII in any record | Records are committed with the code | Redact; reference the secret by name/ARN |
| Save an inline record that failed the check | The next step would build on invalid input | Return it to its author with the error lines |
| Push to the remote | The user always pushes | Commit only with the user's approval |
| Let an author review its own delivery (design, code, Terraform, workflows) | One independent reviewer per delivery; `check_records.py` rejects a verify by the author of a ref | The paired reviewer of the roles table |
| Skip an ADR of the `design` or `infrastructure` folder when reviewing | A violation of an ADR of any of the three folders is HIGH | List all three folders in every review work-order |
