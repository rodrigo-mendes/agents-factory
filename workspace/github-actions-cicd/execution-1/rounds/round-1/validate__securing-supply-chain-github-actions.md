# Validate: securing-supply-chain-github-actions (P6 round 1, validator B, 2026-10-30)

Score: 93.0 (0 HIGH, 2 MEDIUM, 4 LOW). SKILL.md 156 lines, frontmatter valid, three tiers, Version Context, Verification Loop (rule 14), 5 scenarios. Pins match facts F8, F9, F10, F23, F4, F40, F41; Trivy incident details (76 of 77 tags, 2026-03-19/20) traced to research_GitHubActions_SupplyChain_2026-10.md lines 88, 349 and to F42.

Base path: packages/github-actions-cicd/.apm/skills/securing-supply-chain-github-actions/

## MEDIUM
- M1 (composing SKILL.md:58, own note `blueprints/workflow-security-scan.md:125`): `blueprints/workflow-callers.md:57-60` calls `_security-scan.yml` for the deploy gate with `permissions: { contents: read }`, while the same reusable file carries jobs needing `security-events: write` / `pull-requests: write` (`workflow-licensed-jobs.md:23,66`) and an optional SARIF step needing `security-events: write` (`:93`). The PR gate grants the union (`workflow-callers.md:19-23`), the deploy gate does not, so with `CODE_SECURITY_ENABLED` true the deploy gate may fail at startup. Fix hint: grant the union in `scan-image` or split licensed jobs into a second reusable workflow.
- M2 (cross-skill contract, rule pr-ci:18): the required check is the job `gate` (`workflow-callers.md:27`, `evaluation-scenarios.md:11,15`) while the family names it `ci-gate` (composing, README, rule github-workflows-pr-ci, blast-radius isolation-matrix). Rename to `ci-gate`.

## LOW
- L1: `blueprints/workflow-licensed-jobs.md:83` says the step publishes "Checkov and Trivy results" but `:89` uploads only `trivy-image.sarif`.
- L2 (composing :64): no `timeout-minutes` on scan, codeql or dependency-review jobs (`workflow-security-scan.md:40-42`, `workflow-licensed-jobs.md:20,61`).
- L3 (A3): `blueprints/unverified-and-risks.md` is 117 lines with no contents list.
- L4 (pr-ci rule 2, composing :65): `ci-api.yml` (`workflow-callers.md:12-26`) grants `pull-requests: write` and `security-events: write` to the scan job although the rule limits `pull-requests: write` to the plan-comment job, and has no PR concurrency group.

Checked and clean: Trivy never-do rows each carry an alternative; `exit-code: "1"`, explicit `version`, SHA pins; Free-variant risk stated (red check does not block, deploy gate re-scans digest); register counts (11/9/4) match; anchor `#unverified-11` resolves.
