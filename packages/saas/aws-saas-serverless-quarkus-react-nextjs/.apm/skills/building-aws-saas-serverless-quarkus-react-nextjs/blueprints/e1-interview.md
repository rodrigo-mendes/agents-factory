# E1 - SDD interview (12 blocks)

Back to [SKILL.md](../SKILL.md). Only the manager (this skill) talks to the user.

## Rules of the interview

- **At most 10 questions per round.** If the question tool limits questions per call, split the round without exceeding 10 in total.
- Concrete options whenever possible, plus "other / not blocking" so the user is never forced into a guess.
- **Ask only what is missing.** First read: `openspec/specs/**`, `proposal.md` of the change, previous answers in `## Approvals`. Do not re-ask.
- **Playback after each block:** "I understood: ... Confirm?" The user's confirmation (verbatim) goes to `## Approvals` as `gate=E1-B<n>`.
- **Open questions are recorded, never assumed.** An open question may stay open only if the user marks it "does not block"; mark it in `proposal.md` under an open-questions heading (heading names per the openspec skill's doc-vs-validator conflicts blueprint).
- First change of the project: all 12 blocks. Later changes: only blocks the change affects (state which ones and why, let the user add). B9-B11 are skipped for a change with no UI; B12 for a change with no AI.
- Never answer a technical question from memory inside the interview: say which skill covers it ([knowledge map](knowledge-map.md)) or that it is not available.
- I interview and write the playback; I never design (no architecture, no screens, no infrastructure choices): open choices become questions for the architects in E2.

## The 12 blocks

| Block | Central question | Example options to offer | Goes to |
|---|---|---|---|
| B1 Vision | What problem does the SaaS solve, for whom? | value proposition, success metric | `proposal.md` |
| B2 Actors | Who uses it, in which role? | end user, tenant admin, platform admin, external system (Stripe) | E3 actors, E2a authorization model |
| B3 Features | What does each actor do? | journeys, use cases, MoSCoW priority | E3 |
| B4 Business rules | What is allowed or forbidden? | plan limits, subscription lifecycle | E3 requirements + negative scenarios |
| B5 Data | What data exists and who owns it? | entities, owner (tenant), retention, personal data (LGPD) | E2a data model, E3 |
| B6 Non-functional | How fast, secure, cheap, available? | latency p95, RPO/RTO, cost per tenant, tenant isolation | E2a measurable targets |
| B7 Technical constraints | What is already decided? | region, domain, AI providers, budget, existing accounts | E2a / E2c ADRs |
| B8 Operation and delivery | Environments, observability, who releases, **GitHub plan** | dev + prod, SLO/alarm needs; **GitHub plan (Free / Pro / Team / Enterprise), repo visibility (private / public), who approves prod** | E2c (`infrastructure/spec.md` sections 1, 8, 10), E7 gates |
| B9 Screens and journeys | Which screens, which journeys on each? | list, detail, form; entry and exit points | E3b wireframes, E3 |
| B10 Brand and presentation | Brand, audience, dark mode, languages | brand colors/logo, light only / light + dark / follow system, one language / several | E2b design ADRs |
| B11 Accessibility | Which level? | WCAG AA (default) / AAA on critical screens | E2b design ADR |
| B12 AI use | What does AI decide or generate, with which provider, what if it fails? | classification, summary, extraction; OpenAI / Anthropic / Bedrock; fallback value | E2a ADR (provider), E4 design section 9, Ask First D1 |

## Block question seeds (pick only what is missing)

- **B1**: who pays, what is the first paying use case, what would make the first release a success (number + date)?
- **B2**: roles and what each can never do; is there an admin who sees across tenants; any machine caller (Stripe webhook)?
- **B3**: for each actor, the 3 most important journeys; which are Must for the first release?
- **B4**: limits per plan, what happens at the limit, what happens on payment failure, cancellation, downgrade?
- **B5**: entities and their tenant owner; deletion and retention rules; personal data and legal basis; export needs?
- **B6**: p95 latency target, availability, RPO/RTO, expected tenants and requests, monthly cost ceiling per tenant, isolation level.
- **B7**: region(s), existing AWS accounts/organization, domain and certificates, IaC = Terraform (already decided), budget. Browser login with Cognito: tell the user it has no skill `(unverified)` and ask.
- **B8**: environments (dev, prod, others), one AWS account per environment or not, SLOs and alarms wanted; **GitHub plan, repo private or public, who approves a production release** (Free on a private repo has no environments and no protected branches: say it is a weaker variant and ask whether the user accepts or upgrades); acceptance scenarios and demo path (WHEN/THEN), explicitly out of scope.
- **B9**: for each journey, which screens; what must a user see when the list is empty, loading, failing, or not allowed (4 states)?
- **B10**: brand assets, tone, target devices, dark mode, languages (and whether the language changes in the UI).
- **B11**: accessibility level, keyboard-only support, screen reader support, minimum contrast.
- **B12**: what the AI does and what it never decides; provider and model preference (LangChain4j on Quarkus exists only as a pre-release-locked skill, `integrating-quarkus-langchain4j-v1-15`: tell the user and ask, D1); latency tolerance (sync vs queue); what the user sees when the AI fails; cost ceiling; data allowed to leave to the provider. Chat/streaming in the browser is out of scope: say so.

## Optional: GitHub Projects tracker (ask once, off by default)

Ask after B12, in the same playback round: tracker on or off? If on: `owner`, `owner_type` (`organization` | `user`), `project_number`, `repo` (`owner/name`), `approval_source` (`chat` default | `github` | `both`), `bot_login` (always; not an approver) and, when not `chat`, `approvers` (logins). Details and Ask First list: [tracker](tracker-github-projects.md).

- Write `openspec/github-tracker.yaml` only after the playback is confirmed; record the yes as `gate=E1-tracker` in `## Approvals`.
- Run `gh_projects_sync.py bootstrap ... ` as a dry-run, show the PLAN, run `--apply` only after an explicit yes.
- `--install-workflows` and `--vendor` are separate yeses. `owner_type: user`: give the classic-PAT risk warning first.
- Answer off: change nothing; the profile keeps `tracker.kind: none`.

## Definition of Ready (DoR) to leave E1

All must hold, else stay in E1:

1. All required blocks answered, each playback confirmed (verbatim in `## Approvals`).
2. Open questions are either answered or marked "does not block" by the user.
3. Every B7 constraint is stated in a form that can become an ADR (decision, reason).
4. B6 targets have a number and a unit, or are marked "to be decided in E2" by the user.
5. The GitHub plan, repo visibility and prod approver (B8) are recorded; Free-plan risks were shown and the user's choice recorded.
6. `spec-synchronizer` review (mode A, see [brief](worker-briefs.md#spec-synchronizer-review)) returned `pass` with no HIGH gap or contradiction across B1-B12; saved as `verify-E1.md`.

If the review returns HIGH findings: show them, ask the missing questions (new round), do not edit answers yourself.

## Outputs

- `openspec/changes/<id>/proposal.md` (B1 + scope + open questions); other blocks feed E2/E3/E3b directly, not a separate interview file.
- `status.md` approvals (confirmations). Before the first approval is appended, create `openspec/changes/<id>/handoff/` and run `board.py` once so `status.md` exists (preflight item 6). Work-orders for E1-E5 (`wo-NN-sync`, `wo-NN-solution-architect`, ...) use `task: spec` and are set `done` once their verify record is accepted. Create the change folder with `openspec new change <id> --description "..." --json` or by writing the folder (cli-lifecycle blueprint of the openspec skill). Run `openspec validate <id> --type change --strict --json --no-interactive` once `specs/` exist (E3).
