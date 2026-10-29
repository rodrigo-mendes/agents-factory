# Agent alignment

Back to [SKILL.md](../SKILL.md). What each agent emits (read from its definition on 2026-10-28)
against what `assets/handoff-profile.yaml` expects, the mismatches found (ids **A1-A13**, unique in
this skill; the register of unverified items uses U/M ids), and how the profile or the orchestrator
absorbs each. Rules 14-15 of the family decide the vocabulary: agents use the protocol's outcomes
(report family `success|partial|failed|needs-input`, verify `pass|fail`) and the profile carries no
`values:` override. Agents are not edited by this skill; list any needed agent change in the
hand-back. Re-check this page whenever an agent definition changes.

## Record names and fields per agent

| Agent | Saved as | Kind | Frontmatter it emits | Sections it emits | Aligned? |
|---|---|---|---|---|---|
| `quarkus-lambda-integrator` | `result-NN-code.md` (writes it) | `report` | kind, id, from, to, change, refs, requirements, outcome, `build_attempts`, `spec_impact`, `task`, createdAt | Done, Evidence, Spec impact (### Implemented/Divergences/Ambiguities), Suggested next step | yes, except A2 |
| `quarkus-code-reviewer` | `review-NN.md` (inline; orchestrator saves) | `review` | kind, id, from, to, change, refs `[wo-NN-review]`, requirements, outcome, `round`, createdAt | Summary, Traceability, Findings (F1..), Caveats | A3, A4 |
| `aws-lambda-deployer` | `result-NN-deploy.md` (writes it) | `deploy-report` | kind, id, from, to, change, refs, requirements, outcome (protocol 4 values), `deploy_cycles`, createdAt | Release, Artifact, Plan, Approval, Evidence, Rollback, Unconfirmed, Suggested next step | A5 |
| `aws-lambda-debugger` | mode A `diagnosis-NN.md`, mode B `verify-E7.md` (gap-acceptance relaunch: `verify-E7-<nn>`) (inline) | `diagnosis-report` / `verify` | kind, id, from, to, change, refs, requirements, outcome (A: 4 values; B: `pass\|fail`), `debug_rounds`, createdAt | A: Symptom, Verdict, Evidence, Confidence, Fix work-order proposal, Suggested next step; B: Criteria, Evidence (+ its own checklist sections) | A6 |
| `spec-synchronizer` | `verify-E1/E3.md`, `spec-delta-NN.md` (inline) | `verify` / `spec-delta` | per the generic templates | Criteria, Evidence / delta sections + Questions | A7 |
| `aws-architect` | `verify-E2/E4.md` (orchestrator writes; `result-NN-architect.md` only if a work-order asks for a non-verify answer) | `verify` (or `report`) | none defined (read-only, no handoff text) | none defined | A8 |
| `aws-terraform-engineer`, `stripe-integrator` | `result-NN-infra.md`, `result-NN-stripe.md` | `report` | none defined; native status DONE / PARTIAL / NEEDS-INPUT (outcome mapping in A9) | none defined (the engineer reports Requirement, Skills loaded, Files changed, Verification results, Open questions, Unverified items) | A9 |
| `stripe-advisor` | `review-NN.md` (orchestrator wraps; adds `role: stripe`) | `review` | none defined (read-only) | none defined | A9 |
| `aws-observability` | `result-NN-observability.md` (writes it; mode C returns it) | `report` | kind, id, from, to, (mode C: `role: observability-live`; mode A: `role: observability-review`; mode B: none), change, refs, requirements, outcome (protocol values), spec_impact, createdAt | per its Records table (mode C adds the live-results table) | A10 |

## Mismatches and how they are absorbed

| # | Mismatch | Absorbed by |
|---|---|---|
| A1 | Resolved: the integrator's frontmatter now carries `spec_impact` and `task` (agent file, record section). | No orchestrator action; `check_records.py` and the board read them directly. |
| A2 | Two counters for build attempts: the integrator counts failed I6 runs **inside one run** (`build_attempts` in its record, stops at the work-order limit); the board counts **reports** with outcome `failed`/`partial` per task. | Kept on purpose (bounded either way). Orchestrator rule: a result with `outcome: failed` and `build_attempts >=` the work-order limit is treated as exhausted: do not relaunch, write the escalation (`limit: build_attempts`) even if the board count is lower. The board's count remains the floor across relaunches. |
| A3 | The reviewer has no `task` and its `refs` point to the **review work-order**, not to the result. The review would then count as its own task and `review_rounds` would never accumulate per task. Its sections have no `ADR check` (the ADR verdict lives inside Findings and Summary). | The review work-order carries the **same `task`** as the code work-order, and the orchestrator adds `task:` to the saved review. Profile `required_sections.review: [Findings]` (replaces `Findings` + `ADR check`); the fixture `review-01` (Findings + ADR check) still validates. |
| A4 | The reviewer returns `changes-requested` for any HIGH; a MEDIUM blocks approval until it is fixed or justified in I8 (the generic rule plus the I8 justification step). | No conflict; `outcome` values are unchanged. |
| A5 | The deployer's sections differ from the generic `Deployed, Validation, Next step`. `needs-input` at the apply gate is the normal path without an approval line. | `required_sections.deploy-report: [Release, Approval, Evidence, Suggested next step]`; extra sections (Artifact, Plan, Rollback, Unconfirmed) are allowed. The protocol accepts the four outcomes for `deploy-report` (no profile override). `next` sends `partial`/`needs-input` to the orchestrator (who obtains the user's approval and writes a **new** work-order `wo-MM-deploy.md`; the first `needs-input` deploy-report is kept as plan-gate evidence, records are append-only) and `failed` to the debugger. Only `failed` counts toward `deploy_cycles`. |
| A6 | The debugger returns inline and has no Write tool. Mode A sections are listed in `required_sections.diagnosis-report`; its file names are `diagnosis-NN` / `verify-E7`; it emits no `task`, no `spec_impact`; `debug_rounds` is not a profile limit. | Mode A: protocol outcomes, six required sections. Mode B emits a real `verify` (`outcome: pass\|fail`, sections `Criteria` + `Evidence`), saved unchanged as `verify-E7.md` (`stage: E7`); the orchestrator only adds `task` and does **not** re-map the verdict. `needs-input` in mode B produces no verify record: answer the questions and relaunch. Mode B uses the same work-order name as mode A (`wo-NN-debug.md`, field `mode: B`); there is no `wo-NN-verify`. Gaps rule: a pillar `not verified` keeps `fail`; only a relayed `approval: e7-gaps pillars=<list> ...` line lets the debugger emit `pass`, with those pillars under `## Gaps` as "accepted by the user (approval line ...)" ([approval lines](./approval-lines.md)). `debug_rounds` is counted by the orchestrator from the number of `diagnosis-*` records for the same failure and capped at `deploy_cycles`. A diagnosis proposing a behaviour-changing fix gets `spec_impact: divergence` set by the orchestrator. |
| A7 | The synchronizer writes nothing; `delta_revisions: <n>` in its text is informational. A `spec-delta` only silences drift when its `refs` list the diverging record. | Orchestrator saves the delta and checks that `refs` names the divergent result or diagnosis; otherwise the board still shows drift. The board counts `status: revise` records itself. |
| A8 | `aws-architect` has no handoff conventions and cannot write. | The work-order for the architect (generic `work-order.template.md`) asks for the sections `Done`, `Evidence`, `Spec impact`, `Suggested next step` (or `Criteria`/`Evidence` for a verification); the orchestrator saves the answer as `verify-E2.md` / `verify-E4.md` with `from: aws-architect` (a `result-NN-architect.md` is produced only if a work-order asks for a non-verify answer; the current flow never does). |
| A9 | `aws-terraform-engineer` and `stripe-advisor` mention no records at all; `stripe-integrator` reads its work-order only for the extra skills to load, not for record names. | The work-order tells them the exact file and template (`result-<nn>-infra.md` / `result-<nn>-stripe.md` from `assets/result-code.template.md`); the brief names the frontmatter (kind `report`, outcome `success|partial|failed|needs-input`) and the mapping of their native status: DONE -> `success`, PARTIAL -> `partial`, NEEDS-INPUT -> `needs-input`, a failed build/validate -> `failed`. If the final message lacks the record or answers in the native form, the orchestrator wraps it from their output and marks no `success` it cannot support. `stripe-advisor` notes are wrapped into `review-NN.md` (`from: stripe-advisor`, plus `role: stripe` so the profile routes `changes-requested` to `stripe-integrator`, see the table below). Both get `task` from the work-order. |
| A10 | `aws-observability` (`packages/aws-observability/.apm/agents/aws-observability.agent.md`) names its record `result-NN-observability.md` and, in mode C, returns the live-validation result. Aligned: it emits protocol frontmatter and outcomes (rule 14), does **not** write the E7 verify, and in mode C adds `role: observability-live` to its record (the board reads `role` before `from`; modes A/B carry no field, default role `observability`). | Row of the table above. The E7 chain (rule 15): deploy `success` -> `aws-observability` mode C (`result-NN-observability.md`, kind `report`, `role: observability-live`) -> profile rule `{kind: report, role: observability-live, outcome: [success, partial]}` routes it to `debug` -> `aws-lambda-debugger` mode B writes `verify-E7.md` (kind `verify`, role `debug`) -> the final-gate rule keys on that verify. Re-check this row when the agent file changes: required frontmatter `kind: report`, `from: aws-observability`, `outcome` in the protocol set, `spec_impact`. |
| A11 | File-name drift: the design draft used `report-NN-*`; the user decision of 2026-10-28 forbids any name starting with `report` (guard rationale `(unverified)`, register U5). | Profile `records:` uses `result-NN-<role>.md`; `deploy-report`/`diagnosis-report` kinds are named `result-NN-deploy.md` / `diagnosis-NN.md`. `kind: report` stays. |
| A12 | `aws-architect` and `stripe-advisor` answer in a native verdict form (WAF pillar Pass/Fail, R-rules, CRITICAL/HIGH/MEDIUM findings), not in protocol outcomes. | The orchestrator maps it when saving: `aws-architect` -> verify `fail` on any CRITICAL or HIGH finding or any pillar Fail, else `pass`; `stripe-advisor` -> review `changes-requested` on any failing R-rule or any CRITICAL/HIGH finding, else `approved`. |
| A13 | `integrating-quarkus-langchain4j-v1-15` is listed by the orchestrator and the profile; the allowed set of `quarkus-lambda-integrator` (Step 1) and the skill list of `quarkus-code-reviewer` (procedure step 1) now include it, the integrator only when the work-order lists it after the user's yes to its Ask First D1 (1.15.0.CR1 pre-release). | The work-order lists the skill only after that yes. The user's yes to D1 is recorded under `## Approvals` as `gate=D1-langchain4j` (verbatim words) and written in the code work-order's "Ask-First items ... settles" line as `D1 -> 1.15.0.CR1 accepted (gate=D1-langchain4j)`. The integrator treats D1 as settled only if the settles line names it, otherwise `needs-input`; the review work-order carries the settles line copied from the code work-order; the reviewer reports a listed LangChain4j skill without that settles entry as HIGH and checks its Never Do items when the work-order lists it. Re-check both agent files when either list changes. |

## Routing details the profile expresses

- Event rules are first-match, after `limit_reached`, `drift: true` (-> `sync`) and
  `pending_deltas > 0` (-> `orchestrator`): a drift or an open delta is never shadowed by a later
  event rule (a code `success` with an open divergence goes to `sync` before the reviewer).
- Stripe: a code `success` from `stripe-integrator` (role `stripe`) goes to `reviewer`; the orchestrator
  runs the two reviews **sequentially** (the work-order type decides which of the two agents listed in
  the `NEXT:` line runs): `stripe-advisor` first, `quarkus-code-reviewer` only after the advisor's review
  is `approved`. Because the board routes on the latest record, an `approved` from the second reviewer
  must never mask an earlier `changes-requested`: any `changes-requested` returns to `stripe-integrator`
  before the other review runs. Every review record of a Stripe task (wrapped from `stripe-advisor` or from
  `quarkus-code-reviewer`) carries `role: stripe` in its frontmatter (the board reads a `role` field before deriving it from
  `from`), so the rule `{kind: review, role: stripe, outcome: changes-requested}` -> `stripe` fires and
  the fix goes back to `stripe-integrator`. If that field is missing the generic rule sends it to
  `code`: the orchestrator then relaunches `stripe-integrator` by hand. **Stripe hold:** right after
  `stripe-advisor`'s `approved`, and before running `board.py`, the orchestrator writes the
  `quarkus-code-reviewer` review work-order with `status: pending` (same `task`); the Stripe task's
  work-orders are set `done` only after the second reviewer's `approved`. Otherwise
  `{kind: review, outcome: approved, all_tasks: done}` fires `NEXT: deploy` after the first review. Each `changes-requested` is one
  `review_rounds` round (the counter counts review records with that outcome per task), so a project may
  raise `limits.review_rounds` for Stripe tasks via `openspec/handoff-profile.yaml`.
- E7: see A10; a failed `verify` of role `architect`, `sync` or `debug` goes to the orchestrator
  (the user decides the next move); a failed observability `report` falls to the fallback
  (`orchestrator`).

## What the profile does not enforce (orchestrator checks by hand)

- `spec_impact` consistent with the `## Spec impact` text (A1).
- `approval:` lines match the plan hash (the deployer checks; the orchestrator relays verbatim).
- Which of the two agents in the `reviewer` role runs (`NEXT: role=reviewer
  agent=quarkus-code-reviewer,stripe-advisor` lists both; the work-order type decides).
