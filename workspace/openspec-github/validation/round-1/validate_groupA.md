# Validation round 1, group A (skill-best-practices-validator rubric)

Score = 100 - 6/HIGH - 2.5/MEDIUM - 0.5/LOW. Date 2026-10-29. Read-only review; no HIGH findings.

| # | Target | Score |
|---|---|---|
| 1 | github-core/automating-github-repos-with-actions | 99.0 |
| 2 | openspec-github/syncing-openspec-with-github-projects | 90.5 |
| 3 | openspec-github/syncing-openspec-to-github | 99.0 |
| 4 | openspec-github/agents/openspec-github-syncer.agent.md | 99.0 |
| 5 | openspec-github/instructions/openspec-github-state.instructions.md | 97.0 |

## Findings

### Target 1
- LOW SKILL.md:81, :83 Ask First rows "Concurrency", "Runner pin" have no source or tag.
- LOW SKILL.md:78 "Never guess from the login" has no source. Tag as family decision.
OK: SHA pins equal F7; register counts 3+5 match the tag-to-register table; 122 lines.

### Target 2
- MEDIUM (doc vs code) blueprints/workflows.md:20 claims `_vendor.py verify` is the first step after checkout. False in all four templates (gate.yml:69, archive.yml:64 after token mint; ci.yml:56, board-sync.yml:73 inside a later step). Fix: reword, or move the step.
- MEDIUM (doc vs code) SKILL.md:72 and approvals-and-trust.md:87 say exact `bot_login` only. `_model.py:104-113 trusted_author` also trusts `approvers` (adoption, gate issue trust). Fix: state both, and say pull accepts bot_login only.
- MEDIUM hybrid checklist: unverified-and-risks.md has no tag-to-register mapping. Tags at SKILL.md:26, :27, :86, :98 are not traceable. Counts are correct (16 = 7+7+2).
- LOW SKILL.md:74-75 Always items have no source or tag.
- LOW SKILL.md:28 and cli-contract.md:93 say 77 tests; `def test_` count is 80.
- LOW openspec-ci.yml:56 verify runs from the PR's own copy (no integrity value). Document it.
- LOW openspec-archive.yml:100 the default-branch guard can never fire. Harmless.

### Target 3
- LOW SKILL.md:59-61 Always Do has one item.
- LOW SKILL.md:57 guardrails come after Output; move them below Quick Navigation.

### Target 4
- LOW agent.md:65-76 guardrail headings lack ✅ ⚠️ 🚫.
- LOW agent.md:34 Bash restriction is prompt-only (stated honestly).

### Target 5
- MEDIUM instructions:20 says the verify step is first; same mismatch as workflows.md:20.
- LOW claims unsourced, but deferred to the skill.
