# Unverified and risks register

Back to [SKILL.md](../SKILL.md). Research date 2026-10-30. Tags are plain parentheses: (unverified) and (medium confidence).

Contents: [Version-lifetime risk](#version-lifetime-risk) | [Unverified (11)](#unverified-11) | [Irresolvable (0)](#irresolvable-0) | [Medium confidence (9)](#medium-confidence-9) | [Coverage limits (4)](#coverage-limits-4) | [Tag to register mapping](#tag-to-register-mapping) | [Source Bibliography](#source-bibliography)

## Version-lifetime risk

As of 2026-10-30.

- Trivy v0.76.1 (published 2026-10-21 by asset timestamps) is a security release, and trivy-action had an active supply-chain incident in 2026; re-read the Trivy advisories before moving any pin. Source: https://github.com/aquasecurity/trivy/releases
- trivy-action v0.36.0 defaults to Trivy v0.70.0; leaving `version` unset runs an older scanner. Source: https://github.com/aquasecurity/trivy-action/blob/v0.36.0/README.md
- `bridgecrewio/checkov-action` v12.3136.0 is a tag only (no GitHub Release); the Releases page is stale. Re-read the tags page before bumping. Source: https://github.com/bridgecrewio/checkov-action/tags
- `dependency-review-action` v5.0.0 runs on node24 and needs runner v2.327.1 or later; `deny-licenses` may be removed in the next major. Source: https://github.com/actions/dependency-review-action/releases/tag/v5.0.0
- `codeql-action` v4.39.1 is the current line; v3 is still listed as supported with no end date. Source: https://github.com/github/codeql-action/blob/v4.39.1/README.md
- Dependabot lists Terraform support up to 1.15.x while the family pins Terraform 1.17.1; the gap may widen. Source: https://docs.github.com/en/code-security/dependabot/working-with-dependabot/dependabot-options-reference
- Pinned SHAs were resolved on 2026-10-30; re-run `git ls-remote` before every bump.

## Unverified (11)

| ID | Claim | Impact | Workaround |
|---|---|---|---|
| U1 | `upload-sarif` input name is `sarif_file`; `upload-sarif/action.yml` was not opened | upload step fails on a wrong input | read `upload-sarif/action.yml` at v4.39.1 before shipping |
| U2 | trivy-action filesystem input is named `scan-ref`; not in the README table read | `fs` scan fails or scans the wrong path | read `action.yml` at v0.36.0 |
| U3 | `build-mode: none` is right for `javascript-typescript` in the advanced setup | wrong build mode for JS and TS | read the CodeQL supported-languages page |
| U4 | Checkov severity-based soft or hard fail works without a platform API key | severity thresholds may need Prisma Cloud metadata | gate by check ID or full hard fail |
| U5 | CodeQL CLI licence terms for private code without Code Security | no licence-free SAST fallback is offered | none proposed; ask the user |
| U6 | Dependabot parses Terraform 1.16 and 1.17 syntax (documented support ends at 1.15.x) | modules skipped or mis-parsed | keep the entry, watch logs, bump providers by hand |
| U7 | Checkov inline suppression comment syntax | wrong comment syntax suppresses nothing | skip by check ID with `skip_check` |
| U8 | the Checkov action needs a Linux runner; a pinned PyPI Checkov version was not resolved | wrong runner or version | ask about runners before offering `pip install` |
| U9 | the `vars` context is readable inside a called workflow and returns the caller repository variables | licensed jobs never run | adopted: `vars.CODE_SECURITY_ENABLED` is evaluated in the caller-side `if` |
| U10 | `TRIVY_USERNAME` and `TRIVY_PASSWORD` set on the action step reach Trivy (values come from environment secrets `REGISTRY_PULL_USER` and `REGISTRY_PULL_TOKEN`) | private image pull fails | log in to the registry in the same job |
| U11 | a called workflow can only narrow the caller job's token permissions | called jobs lack permissions | grant the union of required permissions in the caller job |

## Irresolvable (0)

None recorded. Open gaps are listed as unverified items above.

## Medium confidence (9)

| ID | Claim | Why medium | Check |
|---|---|---|---|
| M1 | Dependabot updates the `# vX` comment when it updates a SHA-pinned action | only a 2022-10-31 changelog, older than 12 months | open a Dependabot pull request on a pinned action |
| M2 | the glob `/.github/actions/*/*` matches the composite-action layout | docs confirm globbing, not this depth | check the first Dependabot run |
| M3 | Trivy `fs` is an acceptable stand-in for dependency review although it reports all lockfile vulnerabilities | equivalence is a design judgement | state the limitation to the user |
| M4 | `image-ref` accepts the `repo@sha256:<digest>` form | README shows tag references only | run once against a known digest |
| M5 | `framework: terraform,github_actions` as a comma list in the action | CLI documents the values, the action input does not | run on a fixture |
| M6 | `.trivyignore` entries with `exp:` dates and the `.trivyignore.yaml` fields | the filtering page states no version | read the page for Trivy v0.76.1 |
| M7 | red checks cannot block merges on Free private repositories | absence of evidence: F39 does not list protected branches for Free private, and the rulesets page read was partial | confirm in the repository settings |
| M8 | scanners are tested with fixtures on `workflow_dispatch` in a sandbox repository | no official page; practice only | run once in a sandbox |
| M9 | one always-running `ci-gate` job as the only required check | F27 documents the pending behaviour, the design is judgement | protect `main` with that check |

## Coverage limits (4)

| ID | Limit |
|---|---|
| L1 | Pages were fetched with a tool that passes the page text through an extraction model; quoted strings are what that model returned |
| L2 | Doc examples show stale majors (`upload-sarif@v2` and `checkov-action@v12` in the checkov-action README, `checkout@v4` in the trivy-action README, `checkout@v6` in the dependency-review README); this skill uses only facts-file pins |
| L3 | The user's GitHub plan and Code Security status are unknown at authoring time; the skill asks |
| L4 | The Dependabot options reference (182383 characters) was read in three overlapping windows; the checkov-action README and action.yml were read at the tag, the Releases page only for comparison |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) | always-do-patterns.md SARIF handling; workflow-licensed-jobs.md notes | U1 |
| (unverified) | workflow-security-scan.md notes | U2 |
| (unverified) | workflow-licensed-jobs.md notes; evaluation-scenarios.md scenario 2 | U3 |
| (unverified) | SKILL.md Ask First (Checkov skips) | U4 |
| (unverified) | SKILL.md Ask First (SAST without a licence) | U5 |
| (unverified) | SKILL.md Ask First (Dependabot terraform); dependabot-config.md ecosystem notes | U6 |
| (unverified) | SKILL.md Ask First (Checkov skips) | U7 |
| (unverified) | SKILL.md Ask First (Checkov invocation) | U8 |
| (unverified) | workflow-security-scan.md notes (vars context) | U9 |
| (unverified) | workflow-security-scan.md notes (registry credentials) | U10 |
| (unverified) | workflow-security-scan.md notes (permissions) | U11 |
| (medium confidence) | SKILL.md Ask First (Dependabot SHA comments); dependabot-config.md ecosystem notes | M1 |
| (medium confidence) | dependabot-config.md ecosystem notes | M2 |
| (medium confidence) | SKILL.md Ask First (dependency stand-in); workflow-security-scan.md notes; workflow-callers.md PR gate | M3 |
| (medium confidence) | workflow-security-scan.md notes | M4 |
| (medium confidence) | workflow-security-scan.md notes | M5 |
| (medium confidence) | SKILL.md Ask First (ignore policy) | M6 |
| (medium confidence) | SKILL.md Ask First (Free private); workflow-callers.md notes | M7 |
| (medium confidence) | SKILL.md Verification Loop | M8 |
| (medium confidence) | SKILL.md Ask First (gate job); workflow-callers.md notes | M9 |

## Source Bibliography

All fetched 2026-10-30.

**docs.github.com**
- https://docs.github.com/en/get-started/learning-about-github/about-github-advanced-security
- https://docs.github.com/en/code-security/getting-started/github-security-features
- https://docs.github.com/en/get-started/learning-about-github/githubs-plans
- https://docs.github.com/en/code-security/code-scanning/creating-an-advanced-setup-for-code-scanning/codeql-code-scanning-for-compiled-languages
- https://docs.github.com/en/code-security/code-scanning/creating-an-advanced-setup-for-code-scanning/customizing-your-advanced-setup-for-code-scanning
- https://docs.github.com/en/code-security/code-scanning/integrating-with-code-scanning/uploading-a-sarif-file-to-github
- https://docs.github.com/en/code-security/dependabot/working-with-dependabot/dependabot-options-reference
- https://docs.github.com/en/code-security/dependabot/working-with-dependabot/keeping-your-actions-up-to-date-with-dependabot

**Repositories, releases and advisories**
- https://github.com/github/codeql-action/blob/v4.39.1/README.md
- https://github.com/actions/dependency-review-action/blob/v5.0.0/README.md
- https://github.com/bridgecrewio/checkov-action/tags
- https://raw.githubusercontent.com/bridgecrewio/checkov-action/v12.3136.0/action.yml
- https://github.com/aquasecurity/trivy-action/blob/v0.36.0/README.md
- https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23
- https://github.com/aquasecurity/trivy-action/security/advisories/GHSA-9p44-j4g5-cfx5
- https://github.com/aquasecurity/trivy/releases
- SHA verification: `git ls-remote https://github.com/<owner>/<repo> refs/tags/<tag>`

**Other**
- https://trivy.dev/latest/docs/configuration/filtering/ (project docs, no version stated)
- https://www.checkov.io/2.Basics/CLI%20Command%20Reference.html (project docs)
- https://github.blog/changelog/2022-10-31-dependabot-now-updates-comments-in-github-actions-workflows-referencing-action-versions/ (official changelog, older than 12 months)

**Community (classification only, not used for any Always Do or Never Do claim)**
- Barracuda and Kudelski write-ups of the Trivy compromise (located via search, superseded by GHSA-69fq-xp46-6x23)
