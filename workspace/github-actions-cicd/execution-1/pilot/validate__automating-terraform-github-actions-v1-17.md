# Validation: automating-terraform-github-actions-v1-17

Validator: quality-validator (skill-best-practices-validator rubric). Date: 2026-10-30.
Target: packages/github-actions-cicd/.apm/skills/automating-terraform-github-actions-v1-17/ (SKILL.md 119 lines + 8 blueprints, all read in full).
Checked against: _family_facts.md (F1, F2, F10, F23, F24), _family_rules.md (1-12), research_Terraform_GitHubActions_v1.17.md.
Known and not reported: `uses: ./<repo-workflows-dir>/...` placeholder (D-001).

## Score: 91.0 / 100  (0 HIGH, 2 MEDIUM, 8 LOW)

Rubric: 100 - 6x0 - 2.5x2 - 0.5x8 = 91.0. Verdict: PASS, no blocking issues.

## Official criteria (A-C)

| Crit | Status | Note |
|---|---|---|
| A1 frontmatter | pass | name 41 chars, matches folder; description about 265 chars, third person, has "Use when" |
| A2 conciseness | pass | SKILL.md 119 lines (< 500) |
| A3 progressive disclosure | improve | L1: blueprints over 100 lines have no TOC |
| A4 content | pass | version-anchored dates only; defaults given for each Ask First |
| A5 workflows | pass | sequential plan, review, apply; exit-code capture loop |
| A6 paths | pass | forward slashes, no absolute paths |
| B scripts | pass | inline shell handles rc explicitly; no standalone scripts |
| C scenarios | pass | 5 scenarios (canonical, edge, rejection, trap, ask-first) |

## Team criteria (D1-D7)

| Crit | Status | Note |
|---|---|---|
| D1 naming | pass | gerund-noun plus -v1-17 |
| D2 three tiers | pass | all populated |
| D3 version context | pass | |
| D4 verification loop | improve | M1 |
| D5 anti-patterns | pass | every Never Do has an alternative |
| D6 links | pass | all internal links and anchors resolve (8 blueprints confirmed by Glob) |
| D7 external resources | pass | |

## Fact and SHA check

All SHAs and versions match the facts file: setup-terraform v4.0.1 `dfe3c3f8...` (F2), checkout v7.0.1 `3d3c42e5...` (F10), upload-artifact v7.0.2 `cf430e03...` (F23), download-artifact v8.0.2 `9000827c...` (F24), Terraform 1.17.1 (F1). Rule 4 (SHA with tag comment) holds in every example. Rules 5, 6, 7, 8, 11 and 12 pass. Always/Never claims trace to the research file (A1-A11, N1-N9). No contradictions.

## Findings

### MEDIUM

**M1 (D4/A5)** SKILL.md, no verification section anywhere. The research file has a "Quality Control" block of checks that was not carried over, for example:
`grep -rn "auto-approve" .github/workflows/` and `grep -n "use_lockfile *= *true" infra/*/backend.tf`.
Fix: add a `## Verification Loop` to always-do-patterns.md (or a new blueprint) with these commands and expected output, and link it from Quick Navigation.

**M2 (security gap, family rules 7 and 10)** workflow-callers.md:30-43 and workflow-tf-plan.md:42. The PR preview runs `terraform init/test/plan` on branch code with `environment: prod-plan` (prod read credentials). Same-repo PR code can run during plan (for example `data "external"`, local modules). Neither Always Do, Ask First nor Never Do mentions this. The "PR plan and state access" Ask First row covers only fork secrets.
Fix: add an Ask First row or Never Do entry such as "restrict `<env>-plan` to a trusted branch or use a separate PR-only read role". Source it first, since rule 1 applies. Mark it (unverified) until then, and cross-link `limiting-blast-radius-github-actions-deploys`.

### LOW

**L1 (A3)** TOC missing on the blueprints over 100 lines: always-do-patterns.md (152 lines), never-do-patterns.md (135), workflow-tf-plan.md (132), workflow-callers.md (146), unverified-and-risks.md (126). Fix: add a 3-6 line contents list at the top.

**L2 (family rule 3)** SKILL.md:52 packs two claims in one bullet ("Pass `-input=false` and set `TF_IN_AUTOMATION`"), and "every pipeline step" overstates the source. SKILL.md:59 also has two ("job waits for approval and its environment secrets stay locked"). Fix: split into one claim per bullet.

**L3 (family rule 2)** Tag forms are not plain `(medium confidence)` or `(unverified)`:
- SKILL.md:72 "merge-queue safety unverified"
- SKILL.md:74 "equivalence unverified"
- SKILL.md:72 and 74 "(default, medium confidence)" (combined tag)
- never-do-patterns.md:135 nests a tag inside another parenthesis
- evaluation-scenarios.md:46 and 24 use bare prose "unverified"
Fix: use separate tags `(unverified)` and `(medium confidence)`, not nested.

**L4 (rule 1, citation fit)**
- SKILL.md:17 gives the upgrade-guides page as source for the 1.17.1 and 2026-10-21/28 dates. Those come from the CHANGELOG and releases (F1). Cite https://github.com/hashicorp/terraform/blob/v1.17/CHANGELOG.md.
- always-do-patterns.md:27-28 cites the plan page for "anyone with repository read access can download artifacts"; that comes from the download-workflow-artifacts page.
- never-do-patterns.md:20 and 34 cite only the plan page for the 90-day default and read access.
Fix: add the correct URLs.

**L5 (rule 1, policy not doc)** SKILL.md:58 ("one state key per environment and component") and Never Do N7 (SKILL.md:93, never-do-patterns.md:93-104) are family/design decisions. The cited pages (S3 backend `key`, plan command) do not state them. The research rates N7 High only on "brief scope". Fix: label them "(family decision)" or cite the sentence that supports them.

**L6 (rule 6)** workflow-tf-plan.md:23 and workflow-tf-apply.md:25 declare `cloud` as an input, but nothing in either workflow body reads it (login is a placeholder). It is a free string with no validation. Fix: use it in `if:` on the login steps, or note it is reserved.

**L7 (design)** workflow-callers.md:91-141 `ops-drift.yml` is outside the `terraform-prod-network` concurrency group, so a drift plan can overlap an apply. Lock behaviour is U3 (unverified). It also opens a new issue on every run (acknowledged at line 146). Fix: reuse the caller group with `cancel-in-progress: false`, and look up an open issue by label before `gh issue create`.

**L8 (unverified by me, not from the research)** Artifact name `tfplan-<env>-<component>-${{ github.sha }}` (workflow-tf-plan.md:98) is the same across run attempts. Uploading the same name again in a re-run of the same run may fail, because artifact names must be unique within a run. Confirm against the upload-artifact docs. Fix if confirmed: add `${{ github.run_attempt }}`, or set `overwrite: true`.

## Recommendations by priority

1. M1 add verification loop.
2. M2 PR-plan untrusted-code and credentials guardrail.
3. L2 and L3 tag and bullet hygiene; L4 and L5 citations.
4. L1 TOCs; L6, L7, L8 workflow tidy-ups.
