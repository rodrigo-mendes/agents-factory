# Test round 1 - securing-supply-chain-github-actions

Method: simulated in the evaluator's own context from SKILL.md plus blueprints (no agent spawned, DEC-014). 2026-10-30. SHAs and versions match F8-F10, F23, F4, F40, F41, F42 (checkov c10e24..., trivy-action ed142f... v0.36.0, Trivy v0.76.1, codeql 9b3254, dep-review a1d282, advisory IDs).

Verdict: 5/5 scenarios PASS, 3 findings (one medium).

| # | Scenario | Verdict | Evidence |
|---|---|---|---|
| 1 | PR gate on Team, no Code Security | PASS | `_security-scan.yml` inputs `targets,image-ref,fail-on`, output `blocking-findings`, no `secrets: inherit`; ci-api `permissions: {}` + `gate` job; Checkov `framework: terraform,github_actions` hard fail; Trivy fs `exit-code: "1"`, `version: v0.76.1`; SARIF as artifact `retention-days: 14`; licensed jobs gated `vars.CODE_SECURITY_ENABLED == 'true'`; dependabot-config.md github-actions/maven/gradle/terraform/docker with terraform 1.15.x risk; plan variants "protected main, required status check gate, PR review (F39)". |
| 2 | Code Security licensed | PASS | workflow-licensed-jobs.md matrix `java-kotlin`,`javascript-typescript`, `category`, `security-events: write` on the codeql job, "With none, Kotlin code is not analysed", manual setup-java path, `allow-licenses` ("deny-licenses is deprecated"), JavaScript `none` "(unverified)". |
| 3 | Mutable/legacy Trivy refs | PASS | Never Do rows 1-3; SHA ed142fd... `# v0.36.0`, `version: v0.76.1`, `exit-code: "1"`; always-do-patterns.md line 118 rotate + cosign. The "ask whether the old tags ever ran" is only a conditional instruction there (no Ask First row), so the question depends on the agent. |
| 4 | SARIF/red check assumed to protect | PASS | table "Free private, Pro private cannot be purchased -> variable stays unset"; callers.md "Free private accepted risk: a pull request can be merged with a red gate ... deploy gate re-scans the exact digest"; `continue-on-error` is used on scanner steps but the `verdict` step fails the job, so it does not hide failures (a strict judge could still raise the fail signal; wording would help). |
| 5 | gh attestation verify on private Team | PASS | Never Do row "Gate on gh attestation verify for Team, Pro or Free private"; Quick Reference "Attestations on private repos: GitHub Enterprise Cloud only"; callers.md notes. |

## Findings

### S-1 (medium) PR caller grants write permissions by default, against its own Always Do
Canonical `ci-api.yml` passes `security-events: write` and `pull-requests: write` to the `security` job unconditionally (comment: "only needed when CODE_SECURITY_ENABLED is true"). On the Scenario 1 repository (no Code Security) these write scopes are granted for nothing. SKILL.md Always Do: "Grant security-events: write only to jobs that upload SARIF or run CodeQL" and "Run pull-request scan jobs with read-only permissions". Generated output for scenario 1 would therefore violate two Always Do bullets (and family rule 7 spirit). Skill text: blueprints/workflow-callers.md PR gate `permissions:` block. Fix: show the read-only caller as default and a second variant that adds the two scopes when the variable is true.

### S-2 (medium) Image hand-off names do not match the images skill
cd-api excerpt: `uses: ./.github/workflows/_images-build.yml  # placeholder` with outputs `image` and `digest` and `image-ref: ${{ needs.build.outputs.image }}@${{ needs.build.outputs.digest }}`. The images skill's workflow is `_image-publish.yml` with outputs `digest` and `image-ref` (already `repo@sha256:...`). Wired as written, the ref is wrong or the reusable workflow is not found. This is the cross-skill contract the brief asked to check; catalog drift (F-012) hides it because the catalog marks both "indicative".

### S-3 (low) Deploy-gate pull credential is a repository secret on Pro/Team
`REGISTRY_PULL_USER/TOKEN` are repository secrets in the default (Pro/Team) design while family rule 10 wants environment-scoped secrets for anything in a deploy path. The text calls it a "family decision" with read-only scope, but rule 10 is not mentioned; add one sentence or move it to the environment.

## Known/tracked, not re-reported
F-012; pilot findings do not recur (no placeholder `<repo-workflows-dir>`, tags in plain parentheses, no secrets: inherit).
