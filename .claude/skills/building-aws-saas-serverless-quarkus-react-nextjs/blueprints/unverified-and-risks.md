# Unverified items and risks

Back to [SKILL.md](../SKILL.md). Authoring date 2026-10-28. Tag notation: plain parentheses, `(unverified)` and `(medium confidence)`.

## Version-lifetime risk

| Risk | Effect | Mitigation |
|---|---|---|
| Quarkus 4.0.0 "Upcoming" (no date per https://quarkus.io/releases) | skills are locked to 3.40; the 3.40 community support ends 2027-09-30 | any Quarkus 4 request is Ask First and out of scope |
| quarkus-amazon-services 3.23.0 on Quarkus 3.40.0; pairing with patch 3.40.1.1 is not stated on a page (medium confidence) | build may need a BOM check | rely on the data/messaging skills' tags (M1) |
| OpenSpec 1.15.0; no 1.15.1+ as of 2026-10-28; CLI JSON shapes and docs conflict in places | validator may disagree with docs | validator/schema wins; cite both; see the openspec skill (M2) |
| `quarkus-langchain4j`: only a pre-release targets Quarkus 3.40 | AI features rely on a skill locked to 1.15.0.CR1; defaults may change at the final | adoption is Ask First; re-run the skill's defaults check when 1.15.0 final ships (I2) |
| X-Ray SDK/Daemon in maintenance since 2026-02-25 | default tracing choice may age | ADR, never default |

## Unverified items (U)

Count: 9.

- U1 (unverified): `openspec validate` may not tolerate extra headings such as an open-questions section in `proposal.md`. Check: run validate after writing (E1/E3).
- U2 (unverified): the openspec apply tracking and the checkbox convention in `tasks.md` may not accept task IDs in the text. Check: `openspec instructions apply --change <id> --json` once.
- U3 (unverified): behaviour of `openspec archive` with incomplete tasks (docs vs validator conflict). Check before asking the user to archive.
- U4 (unverified): parser strictness of `board.py` for a hand-made `## Approvals` line: it must keep the exact format of the SKILL protocol; check the `board.py` output after the first write.
- U5 (unverified): a subagent write guard on file names starting with `report` (user decision plus the generic protocol register U2; no dated official page). Handling: keep `result-<nn>-<role>.md`; never test the guard.
- U6 (unverified): browser login with Cognito (Hosted UI / OIDC PKCE) in a static-export front end has no skill. Handling: Ask First; offer research via `/researching-technical-frameworks`; never write it from memory.
- U7 (unverified): `openspec validate` may treat `design/` and `infrastructure/` under `openspec/specs/` as capabilities and ask for a `spec.md` in OpenSpec format, or reject extra files such as `design/<flow>.md` and `infra-design.md` in a change. Check: run validate once after E2/E4; if it complains, the rule `openspec-project-layout` gives the adjustment (a minimal `spec.md` per area).
- U8 (unverified): whether every Vercel IN skill works without a server in a static export; read each skill before listing it in a work-order (`next-dev-loop` and `react-view-transitions` need a check against `output: 'export'`).
- U9 (unverified): whether the `gh` token of the user can read branch protection, environments and the required check (admin scope); without it I cannot confirm the "user-must-add" list was applied and I say so.

## Irresolvable from documentation (I)

Count: 2.

- I1: the release date of Quarkus 4.0.0 is not published (https://quarkus.io/releases lists it as upcoming); only the 3.40 line is in scope. Handling: Ask First on any Quarkus 4 request.
- I2: `quarkus-langchain4j` has only a pre-release for Quarkus 3.40; `integrating-quarkus-langchain4j-v1-15` is locked to it. Handling: tell the user, ask before adopting; if declined, record the requirement as blocked.

## Medium confidence (M)

Count: 4 here, plus M3-M5 in the tracker section below.

- M1 (medium confidence): quarkus-amazon-services 3.23.0 is built on Quarkus 3.40.0 (High: parent POM, https://repo1.maven.org/maven2/io/quarkiverse/amazonservices/quarkus-amazon-services-parent/3.23.0/quarkus-amazon-services-parent-3.23.0.pom; releases https://github.com/quarkiverse/quarkus-amazon-services/releases); running it on patch 3.40.1.1 is not stated on a page, only that pairing is medium confidence. The data/messaging skills carry the tag.
- M2 (medium confidence): OpenSpec 1.15.0 docs and CLI JSON shapes disagree in places; the validator/schema wins.
- M6 (medium confidence): the weaker GitHub Free variant (private repo): no environments with required reviewers and no branch protection, so the role trusts `refs/heads/main`; the CI/CD skills carry the confidence tag; repeat it to the user at the merge.
- M7 (medium confidence): the exact set of CI/CD skills in `github-actions-cicd` and of the Vercel skills at install time; re-verify with `ls .claude/skills/` at preflight.

## Coverage limits (L)

Count: 6.

- L1: the team parallelism limit of 4 is a cost choice of this skill, not a platform limit (Protocol 2 says so).
- L2: `debug_rounds` is not a default board counter, so `board.py` does not enforce the debugger's limit. Handling: I count `diagnosis-*` records for the same failure and escalate at the work-order limit; or the profile adds a counter.
- L3: the board derives tasks from work-orders and does not read `tasks.md`; requirement coverage and dependency cycles in E5 are manual checks by me.
- L4: the Terraform engineer's verification uses a POSIX `env -u ... /dev/null` form; on Windows it needs a Bash shell. Say so to the user if the project runs on Windows without Bash.
- L5: `detect_drift.py` without `--include-worktree` sees only commits; agents leave code uncommitted until E9 (see [E6](e6-implementation-cycle.md), [E8](e8-reverse-sync.md)).
- L6: the E9 gate lists `verify-E1` to `verify-E4` as `pass`, but no script enforces them (the board's final-gate rule keys on `verify-E7`). Handling: I check them by `ls` and `check_records.py` before the gate.

## GitHub Projects tracker

Optional, off by default; items carried over from the bridge skill's register (`syncing-openspec-with-github-projects`). Count: 3 (all medium confidence).

- M3 (medium confidence): the project field-value `updatedAt` (F11) is not confirmed as a reliable change marker; `status` may report divergence that `push` cannot explain. Handling: git wins; run `push`.
- M4 (medium confidence): whether events created with an App token or PAT trigger the `openspec-archive` workflow (workflows triggered by `GITHUB_TOKEN` events do not). Handling: do not assume the Actions archive path works; verify once after `--install-workflows`, else use the local path.
- M5 (medium confidence): the Status field has no "Blocked" value by default, so blocked items rely on the `blocked` label. Handling: tell the user; never rely on Status alone.

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| `(medium confidence)` quarkus-amazon-services pairing with 3.40.1.1 | SKILL.md Version Context; Version-lifetime risk | M1 |
| parallel limit of 4 (cost choice) | SKILL.md Protocol 2 | L1 |
| `debug_rounds` not a board counter | SKILL.md Arguments and limits | L2 |
| `detect_drift.py` without `--include-worktree` sees only commits | SKILL.md Protocol 3; E9 gate | L5 |
| `(unverified)` openspec validate and extra headings | this register; e1/e3 flow | U1 |
| `(unverified)` task IDs in `tasks.md` | this register; e4-e5 | U2 |
| `(unverified)` archive with incomplete tasks | this register; e9 | U3 |
| `(unverified)` parser strictness of hand-written approvals | this register; SKILL.md Protocol 1 | U4 |
| `(unverified)` subagent write guard on `report*` names | SKILL.md Overview; never-do 11 | U5 |
| E9 verify-E1..E4 not script-enforced | e9 gate table | L6 |
| `(unverified)` / `(medium confidence)` tags of the knowledge skills, relayed as is | SKILL.md Version Context, briefs | register of the owning knowledge skill |
| LangChain4j pre-release-locked skill, adoption Ask First | SKILL.md Version Context and Ask First; knowledge map | I2 |
| Quarkus 4 out of scope | SKILL.md Version Context | I1 |
| Cognito browser login gap | knowledge map Wave 4; SKILL.md Ask First | U6 |
| `openspec validate` and `design/`, `infrastructure/`, extra files | e2, e4-e5; rule `openspec-project-layout` | U7 |
| Vercel IN skills under static export | knowledge map Wave 4 | U8 |
| `gh` token scope to read protections | e7 | U9 |
| Free-plan weaker variant | e1 B8; e7 | M6 |
| tracker field-value `updatedAt`; App/PAT events triggering archive; Status lacks "Blocked" (medium confidence) | tracker blueprint; E9 Actions path | M3, M4, M5 |

## Agent contract mismatches (read from the agent files, 2026-10-28; re-verify at preflight)

1. **Profile section names vs agent output.** Generic default required sections (record-kinds): review = `Findings, ADR check`; diagnosis-report = `Symptom, Root cause, Evidence, Exact fix, Classification, Next step`; verify = `Criteria, Evidence`.
   Agents emit: reviewer `Summary, Traceability, Findings, Caveats` (no `ADR check` heading); debugger A `Symptom, Verdict, Evidence, Confidence, Fix work-order proposal, Suggested next step`; debugger B (a `verify`) `Criteria, Evidence, Gaps, Unconfirmed, Suggested next step`. Resolution: the profile overrides `required_sections` only for review, deploy-report and diagnosis-report (`assets/handoff-profile.yaml`); the debugger's mode B sections are the generic verify sections `Criteria` + `Evidence` plus extra headings, so there is no profile override for `verify`. Verify with `check_records.py`.
2. **Record names.** Scripts classify by `kind:`, so names are free. This skill uses `result-NN-pipeline.md` (kind `report`, role `pipeline-ci|pipeline-cd`), `result-NN-infra.md`, `result-NN-observability.md` (kind `report`), `diagnosis-NN.md`, `verify-<stage>.md` (E7: `verify-E7.md`, role `debug`).
3. **Read-only agents cannot write**: `quarkus-code-reviewer`, `solution-architecture-reviewer`, `aws-architect-reviewer`, `ui-design-reviewer`, `langchain4j-reviewer`, `nextjs-code-reviewer`, `terraform-code-reviewer`, `cicd-pipeline-reviewer`, `static-site-verifier`, `aws-lambda-debugger`, `spec-synchronizer`, `stripe-advisor` return content inline; I save it (frontmatter `saved-by`). `from:` stays the agent.
4. **No handoff contract** in `stripe-integrator`, `aws-terraform-engineer`, `stripe-advisor`, `cicd-pipeline-engineer` (no record names in the agent files; `stripe-integrator` only loads the skills its work-order lists). The brief must carry the record contract. `stripe-integrator`, `stripe-advisor` and `aws-architect` read installed `.claude/skills/` paths first; the Stripe and AWS family rules now ship inside the skills (`integrate-stripe-java/references/`, `aws-architecture-advisor/references/`, since 2026-10-29), so no `workspace/` path is read; if a skill they name is not installed, they report it as not readable instead of guessing.
5. **Producer-verifier split in E7**: `aws-observability` Mode C writes only `result-NN-observability.md`; acceptance is `verify-E7.md` by the debugger (mode B, `role: debug`) so that producer != verifier.
6. **The debugger never invokes the function**: smoke is the pipeline's `_smoke-test` job. (`aws-lambda-deployer` and its `approval: apply|smoke` lines left this flow; the agent remains in package `aws-lambda`.)
7. **Pipeline records**: `result-NN-pipeline.md` (role `pipeline-ci|pipeline-cd`, `run_url`) are written by me from read-only `gh` output; append-only like every record.
8. **Two-reviewer tasks run sequentially** (Stripe: `stripe-advisor` -> `quarkus-code-reviewer`; AI: `langchain4j-reviewer` -> `quarkus-code-reviewer`; front: `nextjs-code-reviewer` -> `ui-design-reviewer`); each `changes-requested` is one `review_rounds` round.
9. **Model split**: the preflight reads the `model:` of every agent (opus only for the two architects); a different frontmatter stops the run. The launch always passes the model explicitly.

## Source Bibliography

Shipped sources (dated 2026-10-28):

- Quarkus releases https://quarkus.io/releases; API Gateway HTTP vs REST https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html; X-Ray timeline https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-daemon-timeline.html; SnapStart https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html; OpenSpec https://github.com/Fission-AI/OpenSpec
- Protocol and scripts: skill `coordinating-agent-handoffs` (SKILL.md, blueprints, `scripts/`); OpenSpec skill `specifying-changes-with-openspec-v1-15`.

Factory provenance (not shipped; do not cite in runtime briefs):

- Design plan: `workspace/quarkus-aws-saas/DESIGN_PLAN.md` (historical folder name, from before the rename to `aws-saas-serverless-quarkus-react-nextjs`)
- Family facts and rules: `workspace/quarkus-aws-saas/_family_facts_v3.40.md`, `workspace/quarkus-aws-saas/_family_rules_v3.40.md`
- Build state and approvals: `workspace/quarkus-aws-saas/PIPELINE_STATE.md`
- Agent contracts read from the factory sources: `packages/quarkus-aws/.apm/agents/`, `packages/aws-lambda/.apm/agents/`, `packages/handoff-core/.apm/agents/spec-synchronizer.agent.md`, `packages/stripe-java/.apm/agents/`, `packages/aws-architect/.apm/agents/`, `packages/terraform/.apm/agents/aws-terraform-engineer.agent.md`
- Model skills for this workflow shape: `packages/agent-package-builder/.apm/skills/building-agent-packages/`, `packages/camel-quarkus-integrator/.apm/skills/integrating-camel-quarkus/`
