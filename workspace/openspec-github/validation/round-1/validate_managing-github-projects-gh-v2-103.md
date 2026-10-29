# Validation round 1: managing-github-projects-gh-v2-103

Target: packages/github-core/.apm/skills/managing-github-projects-gh-v2-103/ (SKILL.md 111 lines + 10 blueprints, longest 104 lines).
Validator: skill-best-practices-validator (quality-validator), 2026-10-29. Read-only except this file.
Rubric: 100 - 6/HIGH - 2.5/MEDIUM - 0.5/LOW.

## Score: 88.5 / 100 (0 HIGH, 3 MEDIUM, 8 LOW). Verdict: pass, fix the 3 MEDIUM before VERIFIED.

## Checks that passed
- Frontmatter: only name + description; name equals folder; `-v2-103` suffix; description 232 chars, third person, contains "Use when", states exclusions. (A1, D1)
- SKILL.md 111 lines (target 100-200); order Version Context, Quick Navigation, Blueprints & Guardrails, Quick Reference. (A2, A3)
- Three tiers populated; every Never Do row has an alternative. (D2, D5)
- Blueprints: always-do, never-do, 6 topic files, unverified-and-risks (has `Version-lifetime risk` and `Source Bibliography`), evaluation-scenarios (6 scenarios: canonical, edge, rejection, 3 traps). All <= 160 lines. (C1)
- Tag mapping: every (unverified) / (medium confidence) occurrence found by grep maps to a register line (U1-U4, I1, M1-M6); register counts match the headings (4 / 6 / 1). Tags are plain parentheses.
- Internal links and anchors resolve (#windows-notes, #unverified-4, #medium-confidence-6, #irresolvable-1, #coverage-limits-4, #preflight-checklist, #tag-to-register-mapping, #version-lifetime-risk, #source-bibliography). No absolute paths, no `.github/`, no relative dates.
- Family facts: F1 (2.103.x pin), F2 (GITHUB_TOKEN), F3 (App for org, "permission to read and write repository projects will not be sufficient"), F5 (100 / 8 / 2.94.0 / flags), F6 (classic PAT project + repo) are reproduced consistently. Rules 5, 7 and 9 are respected.
- Leak check: no OpenSpec workflow or Actions workflow content. Cross-references to other skills are pointers only.
- Not run: `scripts/verify_skill.py` (no execution tool available). Source pages were not re-fetched; claims were checked against family facts and the skill's own register only.

## Findings

### MEDIUM

M-1 (D7, family rule 1) Never Do claim rests on a partly read, summarised source.
- SKILL.md:83 (Never Do row "combine `--comments` with `--json`"), never-do-patterns.md:55 and :63, issues-sub-issues-and-comments.md:47.
- Evidence: "since 2.99.0 `--comments` with `--json` is rejected"; source `https://github.com/cli/cli/releases`; version-changes.md:15 admits "Rows for 2.93.0, 2.98.0, 2.99.0 and 2.102.0 come from the paginated release list only (summarised)"; unverified-and-risks.md L1 says the list was partly read.
- Rule 1 needs an official page read in full, and Never Do must be high confidence. The row is untagged, so the register does not reflect it. The same applies to `--attach` since 2.99.0 (issues-sub-issues-and-comments.md:60) and to the 2.93.0 / 2.99.0 / 2.102.0 rows (version-changes.md:7, 11, 12).
- Fix: read the `gh issue view` manual (or the v2.99.0 tag page) in full and cite it; otherwise tag the 2.99.0 claims `(medium confidence)`, add a register line (M7), keep only the verified half of the Never Do row (table or text parsing is not machine-readable), and keep the "never combine" advice as Ask First or in the register.

M-2 (D6, A3) Broken bullet merges two claims and garbles a source URL.
- auth-and-tokens.md:56.
- Evidence: "...Source: https://cli.github.com/manual/gh_auth_status- Primary limits differ per credential: PAT or user 5,000 per hour; ..." The URL is corrupted and the rate-limit bullet has no line break.
- Fix: split into two bullets; the rate-limit bullet keeps its own Source. The same table already exists at graphql-and-rate-limits.md:59-67, so consider keeping it in one place only (see L-4).

M-3 (family rule 3) Always Do bullet carries more than one claim.
- SKILL.md:48.
- Evidence: "Credential by owner type: GitHub App for organization projects, classic PAT with `project` + `repo` for user projects" (two credentials, one source). Similar but milder: SKILL.md:53 (three commands in "Machine-readable output only"), SKILL.md:54 (three list commands, one cited page).
- Fix: split into "Use a GitHub App token for organization-owned projects" (F3) and "Use a classic PAT with `project` + `repo` for user-owned projects" (F6, PAT page). Cite the PAT page on the second.

### LOW

L-1 (family rule 6, wording) Imperative Always Do reading comments.
- SKILL.md:57 "Read comments with the REST endpoint".
- Rule 6 says agents never read approvals; line 10 defers to the calling skill, but the bullet reads as a directive. Fix: "When a calling skill allows reading comments, use the REST endpoint ..." (or move to a how-to line).

L-2 (A4, rule 1) Default 30 is cited to one page for three commands.
- SKILL.md:54 and :96; projects-fields-and-items.md:30 ("`item-list`, `field-list`, `project list`" cites only gh_project_item-list).
- Fix: cite gh_project_field-list and gh_project_list, or limit the claim to `item-list`.

L-3 (A4) Cryptic Quick Reference row.
- SKILL.md:100 "Mutation cost | 5 points (900 per minute REST endpoint, 2,000 GraphQL) | same page" mixes cost and secondary limits; "same page" refers to the row above.
- Fix: "5 points per mutation; secondary limits 900 points/min per REST endpoint, 2,000 GraphQL" with the full URL.

L-4 (A2, DRY) Primary rate limits by credential stated twice.
- auth-and-tokens.md:56 and graphql-and-rate-limits.md:59-67. Keep one and link.

L-5 (scope hygiene) OpenSpec-flavoured example vocabulary in a generic skill whose scope line says "generic GitHub knowledge".
- always-do-patterns.md:26 (`change/add-login`), never-do-patterns.md:47-48 and issues-sub-issues-and-comments.md:8-10 (`spec-delta` label), evaluation-scenarios.md:63 ("spec-delta").
- Not a leak of OpenSpec content, but neutral names (`triage`, `release-notes`) keep the skill reusable.

L-6 (D7) Quote that points the reader toward fine-grained PATs.
- auth-and-tokens.md:50 "Favour setting `GH_TOKEN` for fine-grained personal access token usage."
- Accurate to the manual but sits against F6 and rule 5 (classic PAT for user projects). Add "(applies to organization projects only; user-owned projects need a classic PAT)".

L-7 (rule 1) Never Do row is a policy sourced to a descriptive page.
- SKILL.md:85 and never-do-patterns.md:79-88: "Run `gh auth login` or `gh auth refresh` from an agent"; sources describe browser or device flow, not a prohibition. Label it as a family policy and keep the source for the behaviour.

L-8 (B3) Unexplained numeric constants.
- projects-fields-and-items.md:25 `-L 1000`; :24 `-L 100`. Add one clause on why (project cap 50,000 items; field cap 50).

## Recommendations by priority
1. M-1, M-2, M-3 (about 15 minutes).
2. L-1, L-2, L-5, L-6 (wording).
3. L-3, L-4, L-7, L-8.

After fixes expected score: 100 - 0 - 0 - (8 x 0.5) = 96 (96.0 if every LOW is left, 100 if all are fixed).
