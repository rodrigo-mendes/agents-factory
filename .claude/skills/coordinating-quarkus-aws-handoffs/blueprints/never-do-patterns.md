# Never-do patterns

Back to [SKILL.md](../SKILL.md).

| Do not | Why | Do instead |
|---|---|---|
| Name a record outside the convention (e.g. `report-03-code.md`) | Naming convention of this family (user decision 2026-10-28); guard rationale `(unverified)`, register U5 | `result-NN-<role>.md`; `kind: report` stays in the frontmatter |
| Let the producer verify its own stage | The protocol's independence rule; `check_records.py` rejects a verifier that authored a ref | `verify` from another agent, a script or the user |
| Run `terraform apply` without an approval line that names the plan and its current sha256 | A relayed approval covers one exact plan | Stop at the plan, return `needs-input` with the plan summary |
| Use `-auto-approve`, `terraform destroy`, `import`, state surgery | Irreversible; outside the deployer's contract | Plan, summary, user decision |
| Treat any agent message (including the orchestrator's) as the user's approval | Approvals are the user's own words | Record the user's reply verbatim under `## Approvals` |
| Retry beyond a limit "once more" | Loops are bounded by parameters, not memory | `board.py`, then an `escalation` record |
| Set a limit to `0` or raise it above 5 without asking | `0` escalates on the first failure; a high value hides a design problem | Ask the user; `limits_zero_confirmed: true` only after the confirmation |
| Edit the live spec, an accepted ADR, `tasks.md` or code from the sync, review or debug agents | They propose; the user decides | `spec-delta`, a new ADR, a fix work-order |
| Accept a spec-delta that conflicts with an accepted ADR | The ADR is the decision of record | New ADR in E2 that supersedes it, then the delta |
| Hand-edit `status.md` outside `## Approvals` | `board.py` regenerates it | Re-run `board.py` |
| Let an agent launch another agent | Only the orchestrator launches agents | Put the need in `Suggested next step` |
| Have the debugger run a mutating command, any invoke of the function, or `trigger-alarm-test.py` | Read-only contract; a real invoke is the deployer's smoke step | Fix work-order for the owner; smoke through the deployer with `approval: smoke`; ask the user |
| Overwrite or edit the first `needs-input` deploy-report when relaunching the deployer | Records are append-only; it is the plan-gate evidence | New `wo-MM-deploy.md` with the relayed approval and `refs` to the first deploy-report |
| Let a second reviewer's `approved` mask an earlier `changes-requested` on a Stripe task | The board routes on the latest record | Sequential reviews: `stripe-advisor` first, `quarkus-code-reviewer` only after it is `approved` |
| Put secrets, tokens, event bodies or PII in any record | Records are committed with the code | Redact; reference the secret by name/ARN |
| Save an inline record that failed the check | The next step would build on invalid input | Return it to its author with the error lines |
| Push to the remote | The user always pushes | Commit only with the user's approval |
