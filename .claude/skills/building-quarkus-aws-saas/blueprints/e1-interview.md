# E1 - SDD interview (8 blocks)

Back to [SKILL.md](../SKILL.md). Only the orchestrator talks to the user. Plan source: design plan section 3.2 (approved 2026-10-28).

## Rules of the interview

- **At most 10 questions per round.** If the question tool limits questions per call, split the round without exceeding 10 in total.
- Concrete options whenever possible, plus "other / not blocking" so the user is never forced into a guess.
- **Ask only what is missing.** First read: `openspec/specs/**`, `proposal.md` of the change, previous answers in `## Approvals`. Do not re-ask.
- **Playback after each block:** "I understood: ... Confirm?" The user's confirmation (verbatim) goes to `## Approvals` as `gate=E1-B<n>`.
- **Open questions are recorded, never assumed.** An open question may stay open only if the user marks it "does not block"; mark it in `proposal.md` under an open-questions heading (heading names per the openspec skill's doc-vs-validator conflicts blueprint).
- First change of the project: all 8 blocks. Later changes: only blocks the change affects (state which ones and why, let the user add).
- Never answer a technical question from memory inside the interview: say which skill covers it ([knowledge map](knowledge-map.md)) or that it is not available.

## The 8 blocks

| Block | Central question | Example options to offer | Goes to |
|---|---|---|---|
| B1 Vision | What problem does the SaaS solve, for whom? | value proposition, success metric | `proposal.md` |
| B2 Actors | Who uses it, in which role? | end user, tenant admin, platform admin, external system (Stripe) | E3 actors, E2 authorization model |
| B3 Features | What does each actor do? | journeys, use cases, MoSCoW priority | E3 |
| B4 Business rules | What is allowed or forbidden? | plan limits, subscription lifecycle | E3 requirements + negative scenarios |
| B5 Data | What data exists and who owns it? | entities, owner (tenant), retention, personal data (LGPD) | E2 data model, E3 |
| B6 Non-functional | How fast, secure, cheap, available? | latency p95, RPO/RTO, cost per tenant, tenant isolation | E2 measurable targets |
| B7 Technical constraints | What is already decided? | region, AWS account, domain, AI providers, budget | E2 ADRs |
| B8 Acceptance | How do we know it is done? | demo, acceptance scenarios, out of scope | E3 scenarios, acceptance criteria |

## Block question seeds (pick only what is missing)

- **B1**: who pays, what is the first paying use case, what would make the first release a success (number + date)?
- **B2**: roles and what each can never do; is there an admin who sees across tenants; any machine caller (Stripe webhook)?
- **B3**: for each actor, the 3 most important journeys; which are Must for the first release?
- **B4**: limits per plan, what happens at the limit, what happens on payment failure, cancellation, downgrade?
- **B5**: entities and their tenant owner; deletion and retention rules; personal data and legal basis; export needs?
- **B6**: p95 latency target, availability, RPO/RTO, expected tenants and requests, monthly cost ceiling per tenant, isolation level.
- **B7**: region(s), existing AWS account/organization, domain and certificates, IaC = Terraform (already decided), LLM providers (OpenAI, Anthropic, Bedrock; LangChain4j on Quarkus exists only as a pre-release-locked skill, `integrating-quarkus-langchain4j-v1-15`: tell the user and ask), SPA frontend hosting.
- **B8**: acceptance scenarios in WHEN/THEN form, demo path, explicitly out of scope.

## Definition of Ready (DoR) to leave E1

All must hold, else stay in E1:

1. All required blocks answered, each playback confirmed (verbatim in `## Approvals`).
2. Open questions are either answered or marked "does not block" by the user.
3. Every B7 constraint is stated in a form that can become an ADR (decision, reason).
4. B6 targets have a number and a unit, or are marked "to be decided in E2" by the user.
5. `spec-synchronizer` review (mode A, see [brief](worker-briefs.md#spec-synchronizer-review)) returned `pass` with no HIGH gap or contradiction; saved as `verify-E1.md`.

If the review returns HIGH findings: show them, ask the missing questions (new round), do not edit answers yourself.

## Outputs

- `openspec/changes/<id>/proposal.md` (B1 + scope + open questions); other blocks feed E2/E3 directly, not a separate interview file.
- `status.md` approvals (confirmations). Before the first approval is appended, create `openspec/changes/<id>/handoff/` and run `board.py` once so `status.md` exists (preflight item 6). Work-orders for E1-E4 (`wo-NN-sync`, `wo-NN-architect`) use `task: spec` and are set `done` once their verify record is accepted. Create the change folder with `openspec new change <id> --description "..." --json` or by writing the folder (cli-lifecycle blueprint of the openspec skill). Run `openspec validate <id> --type change --strict --json --no-interactive` once `specs/` exist (E3).
