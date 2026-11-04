# Research: Supply-chain security in GitHub Actions CI/CD (github/codeql-action v4.39.1, actions/dependency-review-action v5.0.0, Dependabot, artifact attestations, Checkov, Trivy) on GitHub Team / Pro / Free private repositories

> Unit: `securing-supply-chain-github-actions`. Source item: scope C8; G1 scanner choice "Checkov + Trivy".
> Spec: `researching-technical-frameworks` (default depth = exhaustive, MAX_ITERATIONS = 5).
> Brief: `workspace/github-actions-cicd/execution-1/briefs/P4-research-securing-supply-chain-github-actions.md`.
> Every page was read on 2026-10-30. Family facts F1-F39 and family rules 1-16
> (`workspace/github-actions-cicd/_family_facts.md`, `_family_rules.md`) are applied as given.
> This document is provenance for the skill author; the shipped skill must not read it (brief constraint).
>
> Section-order note: the brief requires the file to END with `## Source Bibliography`, so that section
> moves from its template position to the end, after `## Pages read` and `## Facts requested`.
> All 15 template sections are present.
>
> Version note: `github/codeql-action` v4.39.1 (F8), `actions/dependency-review-action` v5.0.0 (F9),
> `actions/checkout` v7.0.1 (F10), `actions/setup-java` v6.1.0 (F4), `actions/upload-artifact` v7.0.2 (F23)
> and `actions/attest` v4.2.2 (F33) are in the facts file. `bridgecrewio/checkov-action` and
> `aquasecurity/trivy-action` are NOT; they were resolved from their GitHub release/tag pages and are
> listed under `## Facts requested` (FR1, FR2). Examples use the placeholders `<FR1-sha>` / `<FR2-sha>`
> until the orchestrator adds them to the facts file (rules 4 and 11). Doc examples show stale majors
> (`upload-sarif@v2` and `checkov-action@v12` in the checkov-action README, `checkov-action@master` and
> `actions/checkout@v2` on checkov.io, `actions/checkout@v4` in the trivy-action README,
> `actions/checkout@v6` in the dependency-review README, `actions/attest@v4` on docs.github.com). None is used (brief lesson 1).
>
> Tool note: pages were fetched with WebFetch, which passes the page text to an extraction model;
> quotes below are the verbatim strings that model returned. No `git ls-remote` was available to this
> researcher, so FR1/FR2 SHAs come from commit links on the release/commit pages (see Facts requested).

## Metadata

```yaml
Full_Name: Supply-chain security controls for GitHub Actions pipelines (SAST, dependency gating, dependency updates, IaC scanning, image scanning, provenance) on GitHub.com
Target_Version:
  - github/codeql-action v4.39.1 (F8; init declares runs.using node24)
  - actions/dependency-review-action v5.0.0 (F9; release "08 May", node24, needs runner >= v2.327.1)
  - Dependabot (service, dependabot.yml schema as documented 2026-10-30)
  - actions/attest v4.2.2 (F33; verification only in this unit)
  - bridgecrewio/checkov-action v12.3136.0 (tag dated Oct 28, 2026; pins ghcr.io/bridgecrewio/checkov:3.4.0) -> FR1
  - aquasecurity/trivy-action v0.36.0 (Apr 22, 2026, immutable release; default Trivy v0.70.0) -> FR2
  - Trivy CLI latest v0.76.1 ("21 Oct", 2026 per asset timestamps) -> FR3
Release_Dates: see each row above; GitHub release headers omit years, tag pages show them
Support_Status: codeql-action supported lines "v4 (latest)" and "v3"; all other tags are newest on 2026-10-30
Primary_Docs:
  - https://docs.github.com/en/get-started/learning-about-github/about-github-advanced-security
  - https://docs.github.com/en/code-security/getting-started/github-security-features
  - https://docs.github.com/en/code-security/code-scanning/creating-an-advanced-setup-for-code-scanning/codeql-code-scanning-for-compiled-languages
  - https://github.com/actions/dependency-review-action/blob/v5.0.0/README.md
  - https://docs.github.com/en/code-security/dependabot/working-with-dependabot/dependabot-options-reference
  - https://raw.githubusercontent.com/bridgecrewio/checkov-action/v12.3136.0/action.yml
  - https://github.com/aquasecurity/trivy-action/blob/v0.36.0/README.md
  - https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23
Integration_Partners: GitHub Code Security (licence), code scanning SARIF ingestion, Maven/Gradle (java-kotlin), npm/pnpm (javascript-typescript), Terraform (Checkov), container registries GHCR/ECR/OCIR (Trivy on digest)
Neighbour_Units (by name only, rule 12): automating-github-repos-with-actions (github-core: SHA pinning, injection, tokens), publishing-container-images-github-actions (attestation generation), composing-github-actions-pipelines (gate job, F27)
Target_Plan: GitHub Team / Pro / Free with PRIVATE repositories (rule 16)
Research_Date: 2026-10-30
Domain_Complexity: Complex (licensing-dependent features, security gating, third-party action compromise history)
Research_Depth: exhaustive (default)
Max_Iterations: 5
Gap_Loop_Ran: true
Iterations_Used: 4 of 5
Triangulated_Count: 7
Unverified_Count: 7
Irresolvable_Count: 0
Research_Quality_Score: 88%   # ~75 claims, 7 unverified, 2 medium confidence
```

## Executive Summary

Supply-chain controls in GitHub Actions split into two groups with very different availability on
private repositories. **Free on every plan, public and private**: dependency graph, SBOM export,
Dependabot alerts, Dependabot security updates and Dependabot version updates
([github-security-features](https://docs.github.com/en/code-security/getting-started/github-security-features), 2026-10-30).
**Licensed for private repositories**: code scanning (CodeQL and any SARIF upload, including Checkov and
Trivy SARIF) and dependency review are part of **GitHub Code Security**, which "You must be on a GitHub
Team or GitHub Enterprise plan in order to purchase"
([about-github-advanced-security](https://docs.github.com/en/get-started/learning-about-github/about-github-advanced-security), 2026-10-30).
So on Free and Pro private repos these features cannot be bought at all; on Team they are an add-on.
**Artifact attestations** on Free/Pro/Team are "only available for public repositories"; private repos
need GitHub Enterprise Cloud (same security-features page; matches F33).

Consequently the default design (rule 16) is: Dependabot everywhere; Checkov (IaC) and Trivy (images
and lockfiles) as **job-level gates that fail by exit code**, independent of any licence, with their
SARIF kept as a workflow artifact; CodeQL, dependency review and SARIF upload to the Security tab are an
**opt-in for Team + Code Security** (or public repos). Required status checks that make a failing
scanner actually block a merge need protected branches, which on private repos are Pro/Team (F39); on
Free private a scanner failure is visible but advisory (accepted risk, stated, never silent).

Three critical patterns: (1) pin `aquasecurity/trivy-action` by full SHA and never use its un-prefixed
legacy tags: in March 2026 76 of 77 tags were repointed to malicious code (GHSA-69fq-xp46-6x23,
CVE-2026-33634; safe trivy-action from 0.35.0); (2) set Trivy's `version` input explicitly, because
trivy-action v0.36.0 defaults to Trivy v0.70.0 while the latest Trivy is v0.76.1 (security release);
(3) resolve checkov-action from its **tags** page, not the Releases page: the "Latest" release there is
v12.1347.0, which pins Checkov 2.0.930, while the current tag v12.3136.0 (Oct 28, 2026) pins Checkov 3.4.0.
Domain tier: Complex.

## Architectural Guardrails

> Confidence legend: High (2+ official sources, dated <=12mo) | Medium (1 source or dated 12-24mo) | Low (community or older; verify before use)

### ✅ Mandatory Patterns

**A1. Decide features from the plan/licence matrix, not from the docs examples**
> Confidence: High | [✓✓ Triangulated | about-github-advanced-security + github-security-features + about-dependency-review + about-code-scanning (all 2026-10-30)]
- Why: code scanning and dependency review on private repos need GitHub Code Security; Code Security is purchasable only on Team/Enterprise; Dependabot features are on all plans; attestations on private repos need GHEC.
- Matrix (private repositories unless stated):

  | Feature | Free private | Pro private | Team private, no Code Security | Team + Code Security | Public (any plan) |
  |---|---|---|---|---|---|
  | Dependency graph, SBOM export | yes | yes | yes | yes | yes |
  | Dependabot alerts / security updates / version updates | yes | yes | yes | yes | yes |
  | Code scanning (CodeQL default/advanced, SARIF upload) | no (cannot buy) | no (cannot buy) | no | yes | yes |
  | Dependency review (UI and action) | no (cannot buy) | no (cannot buy) | no | yes | yes (action) |
  | Artifact attestations | no (GHEC only) | no (GHEC only) | no (GHEC only) | no (GHEC only) | yes |
  | Checkov / Trivy as exit-code gates | yes | yes | yes | yes | yes |
  | Required status checks enforcing the gate | no (F39) | yes (F39) | yes (F39) | yes | yes |

- Sources: https://docs.github.com/en/get-started/learning-about-github/about-github-advanced-security (2026-10-30) ("Some of these are included in all plans, such as dependency graph and Dependabot alerts"; "To run the feature on your private or internal repositories, you must purchase the relevant" product); https://docs.github.com/en/code-security/getting-started/github-security-features (2026-10-30) (all-plans list; attestation note); https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/about-dependency-review (2026-10-30); F33, F39.

**A2. Every scanner job gets minimal explicit permissions; `security-events: write` only where SARIF is uploaded**
> Confidence: High | [✓✓ Triangulated | codeql-action v4.39.1 README + uploading-a-sarif-file docs + trivy-action/checkov-action READMEs]
- Why: "All advanced setup code scanning workflows must have the `security-events: write` permission." and "Workflows in private repositories must additionally have the `contents: read` permission." (codeql-action README v4.39.1). The SARIF upload doc adds `actions: read` "only required for workflows in private repositories".
- Code:
  ```yaml
  permissions: {}            # workflow default: nothing
  jobs:
    codeql:
      permissions:
        contents: read
        actions: read          # private repos (upload)
        security-events: write # only jobs that upload SARIF
  ```
- Sources: https://github.com/github/codeql-action/blob/v4.39.1/README.md (2026-10-30); https://docs.github.com/en/code-security/code-scanning/integrating-with-code-scanning/uploading-a-sarif-file-to-github (2026-10-30).

**A3. CodeQL advanced setup for Java/Kotlin + JS/TS: `java-kotlin` with explicit build mode; Kotlin needs a build**
> Confidence: High | [✓✓ Triangulated | compiled-languages doc + customizing-advanced-setup doc + init/action.yml v4.39.1]
- Why: identifiers are `java-kotlin` and `javascript-typescript` (customizing doc). Build modes `none`, `autobuild`, `manual` (init/action.yml). Default setup uses `none` for Java; if Kotlin is present "Kotlin analysis requires a build" and with `none` "the Kotlin code will not be analyzed and a warning will be produced". `none` "may produce less accurate results" when dependencies cannot be inferred or code is generated during the build. Use `manual` when the build needs a specific JDK/Gradle setup.
- Code (Team + Code Security, or public; SHAs F8, F10, F4):
  ```yaml
  # .github/workflows/_security-codeql.yml  (reusable, rule 5/6)
  on:
    workflow_call:
      inputs:
        java-build-mode: { type: string, default: "none" }   # none | autobuild | manual
  permissions: {}
  jobs:
    analyze:
      runs-on: ubuntu-latest
      permissions: { contents: read, actions: read, security-events: write }
      strategy:
        fail-fast: false
        matrix:
          include:
            - language: java-kotlin
              build-mode: ${{ inputs.java-build-mode }}
            - language: javascript-typescript
              build-mode: none          # (medium confidence) see gap G3
      steps:
        - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        - uses: github/codeql-action/init@9b3254085494b55a0f7c4c2b3d2d52cc712ce370 # v4.39.1
          with:
            languages: ${{ matrix.language }}
            build-mode: ${{ matrix.build-mode }}
            queries: security-extended
        - if: matrix.build-mode == 'manual'
          uses: actions/setup-java@b843ebf9b913146b38da2eaa7aeddf76074ae1ad # v6.1.0
          with: { distribution: temurin, java-version: "21" }
        - if: matrix.build-mode == 'manual'
          run: ./mvnw -B -DskipTests package
        - uses: github/codeql-action/analyze@9b3254085494b55a0f7c4c2b3d2d52cc712ce370 # v4.39.1
          with:
            category: "/language:${{ matrix.language }}"
  ```
- Sources: https://docs.github.com/en/code-security/code-scanning/creating-an-advanced-setup-for-code-scanning/codeql-code-scanning-for-compiled-languages (2026-10-30); https://docs.github.com/en/code-security/code-scanning/creating-an-advanced-setup-for-code-scanning/customizing-your-advanced-setup-for-code-scanning (2026-10-30); https://raw.githubusercontent.com/github/codeql-action/v4.39.1/init/action.yml (2026-10-30).

**A4. Dependency review on `pull_request` with an explicit severity threshold and licence allow-list**
> Confidence: High | [✓✓ Triangulated | dependency-review-action v5.0.0 README + about-dependency-review]
- Why: defaults are `fail-on-severity: low`, `fail-on-scopes: runtime`, `comment-summary-in-pr: never`, `license-check: true`; `allow-licenses` and `deny-licenses` are mutually exclusive and `deny-licenses` is "deprecated for possible removal in the next major release". `comment-summary-in-pr` requires `pull-requests: write`. v5.0.0 runs on node24 and "requires a minimum Actions Runner version v2.327.1".
- Code (SHA F9, F10):
  ```yaml
  # inside ci-<app>.yml (pull_request)
  dependency-review:
    if: vars.CODE_SECURITY_ENABLED == 'true'   # Team + Code Security, or public repo
    runs-on: ubuntu-latest
    permissions: { contents: read, pull-requests: write }
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: actions/dependency-review-action@a1d282b36b6f3519aa1f3fc636f609c47dddb294 # v5.0.0
        with:
          fail-on-severity: high
          fail-on-scopes: runtime, development
          allow-licenses: MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC
          comment-summary-in-pr: on-failure
  ```
- Sources: https://github.com/actions/dependency-review-action/blob/v5.0.0/README.md (2026-10-30); https://github.com/actions/dependency-review-action/releases/tag/v5.0.0 (2026-10-30); https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/about-dependency-review (2026-10-30).

**A5. One `.github/dependabot.yml` covering every ecosystem in the repo, with grouping**
> Confidence: High | [✓✓ Triangulated | dependabot-options-reference + keeping-your-actions-up-to-date + github-security-features]
- Why: the file lives "in the `.github` directory of your repository"; GitHub Actions uses `directory: "/"` and Dependabot then searches `/.github/workflows` and root `action.yml`; `directories` "supports globbing and the wildcard character `*`"; YAML values are `github-actions`, `maven`, `gradle`, `npm` (also for pnpm/yarn), `terraform`, `docker`; groups combine matching updates in one PR, first matching group wins, `update-types` accepts `minor`/`patch`/`major`; `open-pull-requests-limit` defaults to five; a default cooldown of 3 days applies to version updates (not security updates); reusable workflows are also kept up to date.
- Code:
  ```yaml
  # .github/dependabot.yml
  version: 2
  updates:
    - package-ecosystem: github-actions
      directories: ["/", "/.github/actions/*/*"]   # composite actions per rule 5
      schedule: { interval: weekly }
      groups:
        actions-minor-patch: { patterns: ["*"], update-types: [minor, patch] }
    - package-ecosystem: maven
      directory: "/services/api"
      schedule: { interval: weekly }
      groups:
        maven-minor-patch: { patterns: ["*"], update-types: [minor, patch] }
    - package-ecosystem: gradle
      directory: "/services/worker"
      schedule: { interval: weekly }
    - package-ecosystem: npm
      directory: "/apps/web"
      schedule: { interval: weekly }
      groups:
        npm-dev: { dependency-type: development, update-types: [minor, patch] }
    - package-ecosystem: terraform
      directories: ["/infra/modules/*", "/infra/envs/*"]
      schedule: { interval: weekly }
    - package-ecosystem: docker
      directories: ["/services/*", "/apps/web"]
      schedule: { interval: weekly }
  ```
- Sources: https://docs.github.com/en/code-security/dependabot/working-with-dependabot/dependabot-options-reference (2026-10-30); https://docs.github.com/en/code-security/dependabot/working-with-dependabot/keeping-your-actions-up-to-date-with-dependabot (2026-10-30). The `/.github/actions/*/*` glob depth is (medium confidence): the doc confirms globbing, not this exact layout.

**A6. Checkov as an exit-code gate on IaC and workflows; SARIF kept as artifact, uploaded only when licensed**
> Confidence: High | [✓✓ Triangulated | checkov-action v12.3136.0 action.yml + README + Checkov CLI reference]
- Why: `soft_fail` "do not return an error code if there are failed checks" (default unset = hard fail); `hard_fail_on` / `soft_fail_on` take check IDs; CLI `--framework` includes `terraform`, `terraform_plan`, `github_actions`, `dockerfile`; `output_format` default `sarif` and `output_file_path` "needs to end with a comma for a single output format". The action is a Docker action pinning `ghcr.io/bridgecrewio/checkov:3.4.0`. README's SARIF example uses `if: success() || failure()` because "Results are generated only on a success or failure".
- Code (SHA placeholder FR1; F10, F23):
  ```yaml
  checkov:
    runs-on: ubuntu-latest
    permissions: { contents: read }
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: bridgecrewio/checkov-action@<FR1-sha> # v12.3136.0
        with:
          directory: .
          framework: terraform,github_actions
          output_format: cli,sarif
          output_file_path: console,checkov.sarif
          quiet: true
          # soft_fail not set -> any failed check fails the job (blocking)
      - if: success() || failure()
        uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2
        with: { name: checkov-sarif, path: checkov.sarif, retention-days: 14 }
  ```
- Sources: https://raw.githubusercontent.com/bridgecrewio/checkov-action/v12.3136.0/action.yml (2026-10-30); https://github.com/bridgecrewio/checkov-action/blob/v12.3136.0/README.md (2026-10-30); https://www.checkov.io/2.Basics/CLI%20Command%20Reference.html (2026-10-30). The comma-list form of `framework` in the action is (medium confidence): the CLI documents the values, the action input says only "run only on a specific infrastructure".

**A7. Trivy on the image DIGEST that will be promoted, with explicit Trivy version, severity gate and exit code**
> Confidence: High | [✓✓ Triangulated | trivy-action v0.36.0 README + trivy releases + GHSA-69fq-xp46-6x23]
- Why: inputs `scan-type` (default `image`), `image-ref`, `exit-code` (default `0`, i.e. never fails unless set), `severity` (default all), `ignore-unfixed` (default `false`), `version` (default `v0.70.0`), `trivyignores`, `limit-severities-for-sarif` (default `false`: SARIF otherwise includes all severities), `scanners` (default `vuln,secret`). Latest Trivy is v0.76.1, a security release ("includes mitigations for the eMudhra intermediate CA key compromise"). The 2026 compromise advisory says to "pin GitHub Actions to full, immutable commit SHA hashes".
- Code (SHA placeholder FR2; digest comes from the build job output, see publishing-container-images-github-actions):
  ```yaml
  trivy-image:
    needs: build
    runs-on: ubuntu-latest
    permissions: { contents: read }   # + registry read login per cloud unit
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: aquasecurity/trivy-action@<FR2-sha> # v0.36.0
        with:
          version: v0.76.1                     # FR3; do not rely on the v0.70.0 default
          scan-type: image
          image-ref: ${{ needs.build.outputs.image }}@${{ needs.build.outputs.digest }}
          severity: CRITICAL,HIGH
          ignore-unfixed: true
          exit-code: "1"
          trivyignores: .trivyignore
          format: sarif
          output: trivy-image.sarif
          limit-severities-for-sarif: true
      - if: always()
        uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2
        with: { name: trivy-image-sarif, path: trivy-image.sarif, retention-days: 14 }
  ```
- Sources: https://github.com/aquasecurity/trivy-action/blob/v0.36.0/README.md (2026-10-30); https://github.com/aquasecurity/trivy/releases (2026-10-30); https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23 (2026-10-30). Scanning `repo@sha256:` as `image-ref` is (medium confidence): the README shows tag refs only.

**A8. SARIF upload to the Security tab only when Code Security is enabled (or public repo)**
> Confidence: High | [✓✓ Triangulated | uploading-a-sarif-file docs + about-code-scanning + codeql-action README]
- Why: "If you want to use code scanning on private repositories, you need a GitHub Code Security license." Private uploads without it fail with "GitHub Code Security or GitHub Advanced Security must be enabled for this repository to use code scanning." Use `category` to separate result sets per tool.
- Code (F8):
  ```yaml
  - if: (success() || failure()) && vars.CODE_SECURITY_ENABLED == 'true'
    uses: github/codeql-action/upload-sarif@9b3254085494b55a0f7c4c2b3d2d52cc712ce370 # v4.39.1
    with:
      sarif_file: trivy-image.sarif
      category: trivy-image
  ```
- Sources: https://docs.github.com/en/code-security/code-scanning/integrating-with-code-scanning/uploading-a-sarif-file-to-github (2026-10-30); https://docs.github.com/en/code-security/code-scanning/introduction-to-code-scanning/about-code-scanning (2026-10-30). The input name `sarif_file` is (unverified) in this research: `upload-sarif/action.yml` was not opened; confirm before shipping (gap G4).

**A9. Blocking policy: PR gates vs deploy gates**
> Confidence: High (gate semantics) | Medium (enforcement on Free private, depends on F39)
- PR (pull_request, `ci-<app>.yml`): Checkov (IaC + workflows) hard fail; Trivy `fs` on lockfiles (fallback for dependency review) with `exit-code: 1` on CRITICAL,HIGH; dependency review and CodeQL when licensed. All PR jobs are read-only (rule 7, rule 13). The single always-running gate job (F27) is the required check (Pro/Team, F39).
- Deploy (`cd-<app>.yml`): Trivy on the exact digest before it is promoted; failure stops promotion (rule 8: no rebuild, the same digest is rescanned at each promotion if the policy says so); attestation verification with `gh attestation verify` only where attestations exist (public or GHEC).
- Dependabot alerts never block by themselves; they produce PRs that pass through the same PR gates.
- Free private: no protected branches (F39), so a failing gate does not technically block a merge; CD must re-run the Trivy digest gate so a vulnerable image cannot deploy even if the PR was merged red. State this as accepted risk (rule 16).
- Sources: F27, F39; trivy-action README `exit-code` (2026-10-30); dependency-review README "the dependency review action check will fail if it discovers any vulnerable packages" (about-dependency-review, 2026-10-30).

### ⚠️ Conditional Patterns

**C1. Code Security on Team: buy and enable CodeQL + dependency review, or stay on the free stack**
> Confidence: High
- Options: A) Team + Code Security: CodeQL (default or advanced), dependency review, SARIF in Security tab. B) Any plan without it: Checkov + Trivy exit-code gates, Trivy `fs` for lockfiles, Dependabot; no SAST.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |---|---|---|---|
  | A | SAST coverage, PR annotations, central alert triage | licence cost; Team only | org on Team handling sensitive code |
  | B | zero licence, works on Free/Pro | no SAST, no licence-policy check, findings only in logs/artifacts | Free/Pro private repos, small teams |

- Agent: "Ask the user: plan (Free/Pro/Team) and whether GitHub Code Security is enabled; set repo variable `CODE_SECURITY_ENABLED`."
- Source: https://docs.github.com/en/get-started/learning-about-github/about-github-advanced-security (2026-10-30).

**C2. CodeQL default setup vs advanced setup**
> Confidence: High
- Options: default setup (UI, no workflow; `none` build for Java; switches to autobuild when Kotlin exists) vs advanced setup (workflow above, custom queries, manual build).
- Tradeoffs: default is recommended to start ("We recommend that you start using code scanning with default setup") but "default setup will override existing code scanning configurations" and "will disable the existing workflow file and block any CodeQL analysis API uploads". Advanced gives build control and versioned config.
- Agent: "Ask: does the Java build need a specific JDK/Gradle/Maven setup or generated sources? If yes, advanced + manual."
- Source: https://docs.github.com/en/code-security/code-scanning/enabling-code-scanning/configuring-default-setup-for-code-scanning (2026-10-30).

**C3. Checkov invocation: Docker action vs `pip install checkov`**
> Confidence: Medium
- Options: A) `bridgecrewio/checkov-action` (Docker, pinned image 3.4.0 in v12.3136.0); B) `pip install checkov==<version>` then `checkov -d . --framework terraform -o sarif`.
- Tradeoffs: A is the method checkov.io recommends ("Check out our pre-made action") and needs a Linux runner (Docker container action; (unverified) in this research); B lets you pin the PyPI version directly but the PyPI version and hash were not resolved here (unverified).
- Agent: "Ask whether runners are Linux and whether a PyPI-pinned install is preferred."
- Sources: https://www.checkov.io/4.Integrations/GitHub%20Actions.html (2026-10-30); action.yml v12.3136.0.

**C4. Severity threshold and ignore policy**
> Confidence: High (mechanics) / Medium (threshold choice)
- Options: CRITICAL only, CRITICAL+HIGH (proposed default), all. `ignore-unfixed` on or off. Exceptions via `.trivyignore` (one ID per line, example `CVE-2019-14697 exp:2023-01-01`) or `.trivyignore.yaml` (EXPERIMENTAL; `expired_at`, `statement`, sections vulnerabilities/misconfigurations/secrets/licenses); Checkov via `skip_check`, `baseline`, or inline suppressions (inline syntax not read, unverified).
- Agent: "Ask the risk owner for the threshold and require an expiry on every ignore entry."
- Sources: https://trivy.dev/latest/docs/configuration/filtering/ (2026-10-30; page version not stated, links to v0.67.2, medium confidence); checkov-action README v12.3136.0.

**C5. Free private variant (rule 16)**
> Confidence: High
- No environments (F25), no protected branches (F39), no Code Security, no attestations. Keep Checkov/Trivy/Dependabot; CD re-gates the digest; document that merge is not blocked by red checks.
- Source: F25, F39, A1 sources.

### 🚫 Forbidden Patterns

**N1. Referencing trivy-action by a mutable or un-prefixed legacy tag**
> Severity: Critical
> Confidence: High
- Why: on 2026-03-19/20 "trivy-action (GitHub Action)" versions "Below 0.35.0" were affected; 76 of 77 tags were repointed; old versions were republished with a `v` prefix and un-prefixed tags (except `0.35.0`, kept intact) must be treated as compromised.
- Impact: secret exfiltration from every pipeline that ran it; advisory says to rotate all secrets reachable by affected pipelines.
- ❌ Wrong:
  ```yaml
  - uses: aquasecurity/trivy-action@0.33.1
  - uses: aquasecurity/trivy-action@master
  ```
- ✅ Correct:
  ```yaml
  - uses: aquasecurity/trivy-action@<FR2-sha> # v0.36.0
  ```
- Sources: https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23 (2026-10-30); https://github.com/aquasecurity/trivy-action/releases (2026-10-30). General SHA-pinning guidance: link `automating-github-repos-with-actions` (rule 4).

**N2. Using trivy-action 0.31.0-0.34.0 (script injection CVE-2026-26189)**
> Severity: High
> Confidence: High
- Why: GHSA-9p44-j4g5-cfx5 "script injection via sourced env file in composite action", affected ">= 0.31.0, <= 0.34.0", patched ">=0.34.1".
- Impact: untrusted input (e.g. PR title) passed into an input can execute shell code.
- ❌ Wrong:
  ```yaml
  - uses: aquasecurity/trivy-action@v0.34.0
  ```
- ✅ Correct:
  ```yaml
  - uses: aquasecurity/trivy-action@<FR2-sha> # v0.36.0
  ```
- Source: https://github.com/aquasecurity/trivy-action/security/advisories/GHSA-9p44-j4g5-cfx5 (2026-10-30).

**N3. Relying on Trivy's default `exit-code` / `severity`**
> Severity: High
> Confidence: High
- Why: default `exit-code` is `0`, so findings never fail the job; default `severity` includes UNKNOWN and LOW.
- Impact: a "green" scan that gates nothing.
- ❌ Wrong:
  ```yaml
  with: { image-ref: "ghcr.io/org/app:latest" }
  ```
- ✅ Correct:
  ```yaml
  with: { image-ref: "ghcr.io/org/app@sha256:<digest>", severity: CRITICAL,HIGH, exit-code: "1", ignore-unfixed: true }
  ```
- Source: https://github.com/aquasecurity/trivy-action/blob/v0.36.0/README.md (2026-10-30).

**N4. Taking checkov-action's version from the Releases page "Latest" badge**
> Severity: High
> Confidence: High
- Why: Releases shows v12.1347.0 ("09 Mar") as Latest; its commit pins `docker://bridgecrew/checkov:2.0.930`. The tags page shows v12.3136.0 (Oct 28, 2026) pinning `ghcr.io/bridgecrewio/checkov:3.4.0`.
- Impact: a years-old Checkov (2.0.x) missing current checks and frameworks.
- ❌ Wrong:
  ```yaml
  - uses: bridgecrewio/checkov-action@v12.1347.0
  ```
- ✅ Correct:
  ```yaml
  - uses: bridgecrewio/checkov-action@<FR1-sha> # v12.3136.0
  ```
- Sources: https://github.com/bridgecrewio/checkov-action/releases ; https://github.com/bridgecrewio/checkov-action/tags ; commit pages 99bb2ca / c10e243 (all 2026-10-30).

**N5. Unconditional `upload-sarif` / dependency review / CodeQL on an unlicensed private repo**
> Severity: Medium
> Confidence: High
- Why: private repos need Code Security; Free/Pro cannot buy it.
- Impact: red pipelines for reasons unrelated to findings; teams then disable the job or add `continue-on-error`, hiding real failures.
- ❌ Wrong:
  ```yaml
  - uses: github/codeql-action/upload-sarif@9b3254085494b55a0f7c4c2b3d2d52cc712ce370 # v4.39.1
  ```
- ✅ Correct:
  ```yaml
  - if: vars.CODE_SECURITY_ENABLED == 'true'
    uses: github/codeql-action/upload-sarif@9b3254085494b55a0f7c4c2b3d2d52cc712ce370 # v4.39.1
  # else: upload SARIF as a workflow artifact (actions/upload-artifact F23)
  ```
- Sources: about-github-advanced-security; uploading-a-sarif-file-to-github (2026-10-30).

**N6. Claiming artifact attestations / `gh attestation verify` as a control on Team/Pro/Free private repos**
> Severity: Medium
> Confidence: High
- Why: "artifact attestations are only available for public repositories" on Free/Pro/Team; private needs GHEC (F33).
- ❌ Wrong: a CD gate `gh attestation verify oci://... -R org/private-repo` on a Team plan.
- ✅ Correct: gate on the Trivy digest scan + digest promotion (rule 8); list attestations as the Enterprise/public upgrade path (rule 16).
- Source: https://docs.github.com/en/code-security/getting-started/github-security-features (2026-10-30).

**N7. Using `deny-licenses` in new dependency-review configs**
> Severity: Medium
> Confidence: High
- Why: "deprecated for possible removal in the next major release"; mutually exclusive with `allow-licenses`.
- ❌ Wrong: `deny-licenses: GPL-3.0, AGPL-3.0`
- ✅ Correct: `allow-licenses: MIT, Apache-2.0, BSD-3-Clause, ISC`
- Source: https://github.com/actions/dependency-review-action/blob/v5.0.0/README.md (2026-10-30).

**N8. Running scanners with deployable-environment credentials on pull requests**
> Severity: High
> Confidence: High
- Why: family rules 7 and 13: branch code runs during PR jobs. Registry pulls for scanning a PR image use a PR-only read role.
- ❌ Wrong: `environment: prod` on the PR Trivy job.
- ✅ Correct: `environment: prod-pr` (Pro/Team) or a read-only role trusting `pull_request` (Free), per the cloud units.
- Source: `_family_rules.md` rules 7, 13 (2026-10-30).

## Migration Guide

> Confidence: High | Sources: dependency-review-action v5.0.0 release (2026-10-30) + GHSA-69fq-xp46-6x23 (2026-10-30) + checkov-action tags (2026-10-30)

**Breaking Changes**:
- dependency-review-action v5.0.0: runtime node24, requires runner >= v2.327.1. No removed inputs listed.
- codeql-action v4: init runs on node24 (init/action.yml v4.39.1); v3 still listed as supported in the README, no end date given.
- trivy-action: all historical tags re-published with `v` prefix after the March 2026 compromise; `v0.0.10`, `v0.34.1`, `v0.34.2` "have not been restored yet" (advisory).
- checkov-action v12.3136.0 moves the image from `bridgecrew/checkov` on Docker Hub (old releases) to `ghcr.io/bridgecrewio/checkov:3.4.0`.
- Dependabot: default 3-day cooldown for version updates (options reference).

**Upgrade Steps**:
1. Replace any trivy-action reference with the FR2 SHA; search logs for runs on 2026-03-19/20 and rotate secrets if found (advisory).
2. Replace checkov-action refs with the FR1 SHA.
3. Bump dependency-review-action to the F9 SHA; confirm self-hosted runners are >= v2.327.1.
4. Bump codeql-action to the F8 SHA on all three sub-actions (init, analyze, upload-sarif).
5. Add `.github/dependabot.yml` with `github-actions` so the SHAs above stay current.

**Compatibility Matrix**:

| Dependency | Min | Max | Notes |
|---|---|---|---|
| Actions runner (self-hosted) | v2.327.1 | - | node24 actions (dependency-review v5) |
| Dependabot `terraform` | >= 0.13 | <= 1.15.x | Family pins Terraform 1.17.1 (F1): files using 1.16/1.17-only syntax may not parse (unverified risk) |
| Dependabot `npm` | v7 | v12 | pnpm/yarn also use `npm` |
| Trivy CLI via trivy-action | v0.70.0 default | v0.76.1 latest | set `version` |

## Implementation Blueprint

> Confidence: High | [✓✓ Triangulated | official READMEs + docs.github.com]

**Lifecycle** (per PR, then per deploy):
```yaml
# .github/workflows/ci-api.yml  (pull_request)  - representative, adapt
name: ci-api
on: { pull_request: { branches: [main] } }
permissions: {}
jobs:
  checkov:          { uses: ./.github/workflows/_security-checkov.yml }
  trivy-fs:         { uses: ./.github/workflows/_security-trivy-fs.yml }
  codeql:
    if: vars.CODE_SECURITY_ENABLED == 'true'
    uses: ./.github/workflows/_security-codeql.yml
    permissions: { contents: read, actions: read, security-events: write }
  dependency-review:
    if: vars.CODE_SECURITY_ENABLED == 'true'
    runs-on: ubuntu-latest
    permissions: { contents: read, pull-requests: write }
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: actions/dependency-review-action@a1d282b36b6f3519aa1f3fc636f609c47dddb294 # v5.0.0
        with: { fail-on-severity: high, comment-summary-in-pr: on-failure }
  gate:             # the single required check (F27)
    if: always()
    needs: [checkov, trivy-fs, codeql, dependency-review]
    runs-on: ubuntu-latest
    permissions: {}
    steps:
      - run: |
          echo '${{ toJSON(needs) }}' | grep -Eq '"result": "(failure|cancelled)"' && exit 1 || exit 0
```

**Trivy filesystem scan as dependency-review fallback** (licence-free):
```yaml
# .github/workflows/_security-trivy-fs.yml
on: { workflow_call: {} }
permissions: {}
jobs:
  fs:
    runs-on: ubuntu-latest
    permissions: { contents: read }
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: aquasecurity/trivy-action@<FR2-sha> # v0.36.0
        with:
          version: v0.76.1
          scan-type: fs
          scan-ref: .            # (unverified) input name not in the README table read
          scanners: vuln,secret
          severity: CRITICAL,HIGH
          ignore-unfixed: true
          exit-code: "1"
```
Note: Trivy fs scans all lockfile vulnerabilities, not only those introduced by the PR (dependency review diffs base vs head); this equivalence is (medium confidence) and must be stated in the skill.

**Integration**: deploy gate (cd-<app>.yml) runs A7 against `needs.build.outputs.digest`, then promotion uses the same digest (rule 8). Attestation verification (public/GHEC only):
```bash
# Representative - adapt to your environment
gh attestation verify oci://ghcr.io/ORG/IMAGE@sha256:<digest> -R ORG/REPO
```
Source: https://docs.github.com/en/actions/security-for-github-actions/using-artifact-attestations/using-artifact-attestations-to-establish-provenance-for-builds (2026-10-30).

## Quality Control

**Verification Commands**:
```bash
# Representative - adapt to your environment
# 1. Every third-party action pinned by 40-char SHA (rule 4)
grep -rEn 'uses: [^.][^@]+@' .github/workflows | grep -vE '@[0-9a-f]{40} # v' 
# Expected: no output

# 2. No trivy-action un-prefixed / mutable refs
grep -rEn 'aquasecurity/trivy-action@(master|main|[0-9])' .github/workflows
# Expected: no output

# 3. Trivy gates actually fail
grep -rn -A12 'aquasecurity/trivy-action@' .github/workflows | grep -c 'exit-code: "1"'
# Expected: equals the number of trivy-action steps

# 4. Checkov not soft-failing silently
grep -rn 'soft_fail: true' .github/workflows
# Expected: no output (or a documented exception)

# 5. dependabot.yml present and covers github-actions
grep -n 'package-ecosystem: github-actions' .github/dependabot.yml
# Expected: one match

# 6. SARIF uploads are licence-gated
grep -rn -B2 'codeql-action/upload-sarif@' .github/workflows | grep -c 'CODE_SECURITY_ENABLED'
# Expected: equals the number of upload-sarif steps

# 7. Local Checkov dry run (if checkov installed)
checkov -d . --framework terraform,github_actions --compact
# Expected: "Failed checks: 0" or the known baseline
```

**Mocking**: scanners are tested against fixtures: a Terraform fixture with a known-bad resource must make Checkov fail; an old base image (known CVE) must make the Trivy step exit 1. Run on `workflow_dispatch` in a sandbox repo (representative; no official doc for this practice, medium confidence).

## Production Readiness

- **Performance**: trivy-action caching "is turned on by default", and "we recommend keeping it enabled to avoid rate limiting issues" (README v0.36.0). CodeQL `none` build mode avoids a build at some accuracy cost.
- **Scalability**: Dependabot `open-pull-requests-limit` default 5 per ecosystem entry; use groups to reduce PR volume; `registries` needed for private registries ("default behavior is to raise pull requests only to update dependencies stored in publicly accessible registries").
- **Monitoring**: Dependabot alerts (all plans); Security tab only with Code Security; otherwise SARIF artifacts with `retention-days`.
- **Security**: SHA-pin scanners (N1); explicit Trivy version (A7); rotate secrets after any compromised-action run (advisory); PR scanners read-only (N8); `.trivyignore` entries with `exp:` dates.

## Reference Implementations

- codeql-action README v4.39.1: https://github.com/github/codeql-action/blob/v4.39.1/README.md
- dependency-review-action README v5.0.0: https://github.com/actions/dependency-review-action/blob/v5.0.0/README.md
- checkov-action README/action.yml v12.3136.0: https://github.com/bridgecrewio/checkov-action/blob/v12.3136.0/README.md
- trivy-action README v0.36.0: https://github.com/aquasecurity/trivy-action/blob/v0.36.0/README.md
- Trivy compromise advisory: https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23
- Community (not used for claims, listed for the reader): Barracuda and Kudelski write-ups of the Trivy compromise (search results 2026-10-30).

## Research Gaps

```
Gap G1: Dependabot updating SHA-pinned action refs and their "# vX" comment
Impact: rule 4 relies on Dependabot to keep SHA pins current
Workaround: only official statement is the 2022-10-31 changelog ("Dependabot will now update the semver version in comments when updating Actions workflows with a commit SHA version") - older than 12 months -> (medium confidence)
Follow-up: docs.github.com Dependabot GitHub Actions page in a later revision
§7-ref: Iteration 3 - Resolved (medium confidence)

Gap G2: Dependabot terraform ecosystem supports ">= 0.13, <= 1.15.x" while family uses Terraform 1.17.1 (F1)
Impact: Dependabot may skip or mis-parse modules using newer syntax (unverified)
Workaround: keep the entry; watch Dependabot logs; fall back to manual provider bumps
Follow-up: dependabot-options-reference supported-versions column
§7-ref: Iteration 2 - Documented as risk

Gap G3: build-mode for javascript-typescript in CodeQL advanced setup
Impact: example uses `none` (medium confidence); compiled-languages page covers only compiled languages
Follow-up: CodeQL starter workflow / supported-languages page
§7-ref: Iteration 4 - open (unverified)

Gap G4: upload-sarif input name (`sarif_file`) and trivy-action `scan-ref` input not read in action.yml
Follow-up: https://github.com/github/codeql-action/blob/v4.39.1/upload-sarif/action.yml ; trivy-action action.yml at v0.36.0
§7-ref: open (unverified)

Gap G5: Checkov severity-based soft/hard fail without a platform API key
Impact: severities may require Prisma Cloud metadata (unverified); examples use check IDs / full hard fail
§7-ref: open (unverified)

Gap G6: Whether rulesets / required status checks are available on Free private repos
Impact: decides whether gates can block merges on Free; F39 says protected branches are Pro/Team for private; about-rulesets fetch returned only "for customers on GitHub Team and GitHub Enterprise plans"
§7-ref: Iteration 4 - partially resolved (F39 governs)

Gap G7: CodeQL CLI licence terms for private code without Code Security
Impact: no licence-free SAST fallback is proposed (CodeQL CLI is listed inside the Code Security product)
§7-ref: open (unverified)
```

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|---|---|---|---|---|
| 1 | Guardrails A1 | Dependabot availability on private repos | Resolved: all plans | https://docs.github.com/en/code-security/getting-started/github-security-features (2026-10-30) |
| 1 | Guardrails A1 | Attestations on private repos | Resolved: GHEC only (confirms F33) | same page (2026-10-30) |
| 2 | Metadata | checkov-action latest | Updated: Releases "Latest" stale; tags page gives v12.3136.0 | https://github.com/bridgecrewio/checkov-action/tags (2026-10-30) |
| 2 | Migration | Dependabot terraform version range | Added as risk G2 | dependabot-options-reference (2026-10-30) |
| 3 | Guardrails N1 | trivy-action 2026 compromise | Resolved with official advisory | https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23 (2026-10-30) |
| 3 | Gap G1 | SHA comment updates by Dependabot | Resolved (medium confidence, 2022 changelog) | https://github.blog/changelog/2022-10-31-dependabot-now-updates-comments-in-github-actions-workflows-referencing-action-versions/ (2026-10-30) |
| 4 | Guardrails A7 | Trivy latest version | Resolved v0.76.1; default in action is v0.70.0 | https://github.com/aquasecurity/trivy/releases (2026-10-30) |
| 4 | Gap G6 | Rulesets on Free private | Partially resolved; F39 governs | about-rulesets (2026-10-30) |

## Completion Checklist

- [x] Domain complexity tier assessed and documented (Complex)
- [x] All scope areas cited (availability, CodeQL, dependency review, Dependabot, Checkov, Trivy, blocking policy)
- [x] Pattern counts driven by domain needs
- [x] Every anti-pattern has alternative
- [x] All CLI commands marked as representative
- [x] Integration examples complete
- [x] Sources dated and linked
- [x] Security documented
- [x] 1+ copy-paste working example (placeholders FR1/FR2 pending facts file)
- [x] Confidence badge applied to every pattern entry
- [x] Always-Do patterns triangulated or downgraded
- [x] Research Iteration Changelog present
- [x] Research_Quality_Score calculated
- [x] Every Research Gap cross-referenced

## Agent Operation Notes

- **High Confidence**: A1-A8 matrix and inputs; N1-N8.
- **Medium Confidence**: Dependabot SHA-comment update (2022 source); `/.github/actions/*/*` glob; Trivy fs as dependency-review substitute; digest `image-ref`; Checkov comma-list `framework` in the action; trivy.dev filtering page version.
- **Low Confidence / unverified**: G3, G4, G5, G7; Docker-action-requires-Linux statement; PyPI Checkov version.
- **Edge Cases**: Trivy v0.76.1 is a security release from "21 Oct" (<30 days); trivy-action supply chain had an active incident in 2026 - pin by SHA, re-check advisories before shipping.
- **Emergency Stop**: none triggered.

## Pages read

| URL | read on | official | prompt-injection-like instructions found |
|---|---|---|---|
| https://docs.github.com/en/get-started/learning-about-github/about-github-advanced-security | 2026-10-30 | yes | no |
| https://docs.github.com/en/code-security/code-scanning/introduction-to-code-scanning/about-code-scanning | 2026-10-30 | yes | no |
| https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/about-dependency-review | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/security-for-github-actions/using-artifact-attestations/using-artifact-attestations-to-establish-provenance-for-builds | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/concepts/security/artifact-attestations | 2026-10-30 | yes | no |
| https://docs.github.com/en/code-security/dependabot/dependabot-alerts/about-dependabot-alerts | 2026-10-30 | yes | no |
| https://docs.github.com/en/code-security/dependabot/working-with-dependabot/dependabot-options-reference | 2026-10-30 (182383 chars, read in three windows 0-100000, 40000-140000, 100000-end) | yes | no |
| https://docs.github.com/en/code-security/code-scanning/creating-an-advanced-setup-for-code-scanning/codeql-code-scanning-for-compiled-languages | 2026-10-30 | yes | no |
| https://docs.github.com/en/get-started/learning-about-github/githubs-plans | 2026-10-30 | yes | no |
| https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/about-dependabot-version-updates | 2026-10-30 | yes | no |
| https://docs.github.com/en/code-security/dependabot/working-with-dependabot/keeping-your-actions-up-to-date-with-dependabot | 2026-10-30 | yes | no |
| https://docs.github.com/en/code-security/dependabot/dependabot-security-updates/about-dependabot-security-updates | 2026-10-30 | yes | no |
| https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/about-the-dependency-graph | 2026-10-30 | yes | no |
| https://docs.github.com/en/code-security/getting-started/github-security-features | 2026-10-30 | yes | no |
| https://docs.github.com/en/code-security/code-scanning/integrating-with-code-scanning/uploading-a-sarif-file-to-github | 2026-10-30 | yes | no |
| https://docs.github.com/en/code-security/code-scanning/enabling-code-scanning/configuring-default-setup-for-code-scanning | 2026-10-30 | yes | no |
| https://docs.github.com/en/code-security/code-scanning/creating-an-advanced-setup-for-code-scanning/customizing-your-advanced-setup-for-code-scanning | 2026-10-30 | yes | no |
| https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets | 2026-10-30 | yes | no |
| https://github.com/github/codeql-action/blob/v4.39.1/README.md | 2026-10-30 | yes | no |
| https://raw.githubusercontent.com/github/codeql-action/v4.39.1/init/action.yml | 2026-10-30 | yes | no |
| https://github.com/actions/dependency-review-action/blob/v5.0.0/README.md | 2026-10-30 | yes | no |
| https://github.com/actions/dependency-review-action/releases/tag/v5.0.0 | 2026-10-30 | yes | no |
| https://github.com/bridgecrewio/checkov-action/releases | 2026-10-30 | yes | no |
| https://github.com/bridgecrewio/checkov-action/releases/tag/v12.1347.0 | 2026-10-30 | yes | no |
| https://github.com/bridgecrewio/checkov-action/commit/99bb2caf247dfd9f03cf984373bc6043d4e32ebf | 2026-10-30 | yes | no |
| https://github.com/bridgecrewio/checkov-action/tags | 2026-10-30 | yes | no |
| https://github.com/bridgecrewio/checkov-action/commit/c10e243 | 2026-10-30 | yes | no |
| https://github.com/bridgecrewio/checkov-action/blob/v12.3136.0/README.md | 2026-10-30 | yes | no |
| https://raw.githubusercontent.com/bridgecrewio/checkov-action/v12.3136.0/action.yml | 2026-10-30 | yes | no |
| https://www.checkov.io/2.Basics/CLI%20Command%20Reference.html | 2026-10-30 | yes (Checkov project docs) | no |
| https://www.checkov.io/4.Integrations/GitHub%20Actions.html | 2026-10-30 | yes (Checkov project docs) | no |
| https://github.com/aquasecurity/trivy-action/releases | 2026-10-30 | yes | no |
| https://github.com/aquasecurity/trivy-action/releases/tag/v0.36.0 | 2026-10-30 | yes | no |
| https://github.com/aquasecurity/trivy-action/tags | 2026-10-30 | yes | no |
| https://github.com/aquasecurity/trivy-action/security/advisories | 2026-10-30 | yes | no |
| https://github.com/aquasecurity/trivy-action/security/advisories/GHSA-9p44-j4g5-cfx5 | 2026-10-30 | yes | no |
| https://github.com/aquasecurity/trivy-action/blob/v0.36.0/README.md | 2026-10-30 | yes | no |
| https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23 | 2026-10-30 | yes | no |
| https://github.com/aquasecurity/trivy/releases | 2026-10-30 | yes | no |
| https://trivy.dev/latest/docs/configuration/filtering/ | 2026-10-30 | yes (Trivy project docs) | no |
| https://github.blog/changelog/2022-10-31-dependabot-now-updates-comments-in-github-actions-workflows-referencing-action-versions/ | 2026-10-30 | yes (official changelog, >12 months old) | no |
| WebSearch: trivy-action compromise 2026 (results: Barracuda, Kudelski, GitLab advisory DB, GCVE, NHS) | 2026-10-30 | no (used only to locate GHSA-69fq-xp46-6x23) | no |
| WebSearch: Dependabot SHA pinned comment (results: community blogs) | 2026-10-30 | no (used only to locate the 2022 changelog) | no |

## Facts requested

| ID | Repo | Tag | SHA | Source | Notes |
|---|---|---|---|---|---|
| FR1 | bridgecrewio/checkov-action | v12.3136.0 (Oct 28, 2026; floating `v12` points to the same commit) | `c10e2438743528f9e4549758fad8b7a62052541d` (from the "Browse files" link on the commit page for c10e243; not verified with `git ls-remote`) | https://github.com/bridgecrewio/checkov-action/tags ; https://github.com/bridgecrewio/checkov-action/commit/c10e243 (2026-10-30) | Releases page "Latest" is stale (v12.1347.0 = `99bb2caf247dfd9f03cf984373bc6043d4e32ebf`, Checkov 2.0.930) - do not use. v12.3136.0 action.yml pins `ghcr.io/bridgecrewio/checkov:3.4.0`. Tag is not a GitHub Release, so no release page exists for it. |
| FR2 | aquasecurity/trivy-action | v0.36.0 (Apr 22, 2026, "Immutable release") | `ed142fd0673e97e23eac54620cfb913e5ce36c25` (from the commit link on the release page; not verified with `git ls-remote`) | https://github.com/aquasecurity/trivy-action/releases/tag/v0.36.0 (2026-10-30) | Default Trivy `version` v0.70.0. Never use un-prefixed legacy tags (GHSA-69fq-xp46-6x23). |
| FR3 | aquasecurity/trivy (CLI, set via trivy-action `version`) | v0.76.1 ("21 Oct", 2026 per asset timestamps; Latest) | n/a (binary version, not an action) | https://github.com/aquasecurity/trivy/releases (2026-10-30) | Security release (eMudhra CA mitigation). |

Orchestrator: please confirm FR1/FR2 with `git ls-remote https://github.com/<repo> refs/tags/<tag>` (peeled `^{}` if annotated) before adding them to `_family_facts.md`.

## Source Bibliography

**Primary (all read 2026-10-30)**:
- GitHub Advanced Security products and plans: https://docs.github.com/en/get-started/learning-about-github/about-github-advanced-security
- GitHub security features by plan: https://docs.github.com/en/code-security/getting-started/github-security-features
- GitHub plans: https://docs.github.com/en/get-started/learning-about-github/githubs-plans
- About code scanning: https://docs.github.com/en/code-security/code-scanning/introduction-to-code-scanning/about-code-scanning
- CodeQL compiled languages / build modes: https://docs.github.com/en/code-security/code-scanning/creating-an-advanced-setup-for-code-scanning/codeql-code-scanning-for-compiled-languages
- Customizing advanced setup: https://docs.github.com/en/code-security/code-scanning/creating-an-advanced-setup-for-code-scanning/customizing-your-advanced-setup-for-code-scanning
- Default setup: https://docs.github.com/en/code-security/code-scanning/enabling-code-scanning/configuring-default-setup-for-code-scanning
- Uploading SARIF: https://docs.github.com/en/code-security/code-scanning/integrating-with-code-scanning/uploading-a-sarif-file-to-github
- codeql-action v4.39.1 README and init/action.yml: https://github.com/github/codeql-action/blob/v4.39.1/README.md ; https://raw.githubusercontent.com/github/codeql-action/v4.39.1/init/action.yml
- About dependency review: https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/about-dependency-review
- dependency-review-action v5.0.0 README and release: https://github.com/actions/dependency-review-action/blob/v5.0.0/README.md ; https://github.com/actions/dependency-review-action/releases/tag/v5.0.0
- Dependabot options reference: https://docs.github.com/en/code-security/dependabot/working-with-dependabot/dependabot-options-reference
- Dependabot for actions: https://docs.github.com/en/code-security/dependabot/working-with-dependabot/keeping-your-actions-up-to-date-with-dependabot
- Dependabot version / security updates, alerts, dependency graph: https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/about-dependabot-version-updates ; https://docs.github.com/en/code-security/dependabot/dependabot-security-updates/about-dependabot-security-updates ; https://docs.github.com/en/code-security/dependabot/dependabot-alerts/about-dependabot-alerts ; https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/about-the-dependency-graph
- Dependabot SHA comment changelog (2022-10-31, medium confidence): https://github.blog/changelog/2022-10-31-dependabot-now-updates-comments-in-github-actions-workflows-referencing-action-versions/
- Artifact attestations: https://docs.github.com/en/actions/concepts/security/artifact-attestations ; https://docs.github.com/en/actions/security-for-github-actions/using-artifact-attestations/using-artifact-attestations-to-establish-provenance-for-builds
- Rulesets: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets
- checkov-action: https://github.com/bridgecrewio/checkov-action/tags ; https://github.com/bridgecrewio/checkov-action/releases ; https://github.com/bridgecrewio/checkov-action/blob/v12.3136.0/README.md ; https://raw.githubusercontent.com/bridgecrewio/checkov-action/v12.3136.0/action.yml ; commits 99bb2caf247dfd9f03cf984373bc6043d4e32ebf and c10e243
- Checkov docs: https://www.checkov.io/2.Basics/CLI%20Command%20Reference.html ; https://www.checkov.io/4.Integrations/GitHub%20Actions.html
- trivy-action: https://github.com/aquasecurity/trivy-action/releases ; https://github.com/aquasecurity/trivy-action/tags ; https://github.com/aquasecurity/trivy-action/releases/tag/v0.36.0 ; https://github.com/aquasecurity/trivy-action/blob/v0.36.0/README.md
- Advisories: https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23 (CVE-2026-33634, published Mar 21, 2026) ; https://github.com/aquasecurity/trivy-action/security/advisories/GHSA-9p44-j4g5-cfx5 (CVE-2026-26189, published Feb 18, 2026)
- Trivy releases and filtering docs: https://github.com/aquasecurity/trivy/releases ; https://trivy.dev/latest/docs/configuration/filtering/

**Family facts used**: F1, F4, F8, F9, F10, F23, F25, F27, F33, F39 (`workspace/github-actions-cicd/_family_facts.md`, 2026-10-30).

**Validation (community, not used for claims)**: Barracuda trust notice and Kudelski Security write-up on the Trivy tag compromise (located via WebSearch 2026-10-30; superseded by GHSA-69fq-xp46-6x23).
