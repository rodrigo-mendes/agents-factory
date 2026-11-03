# Research: GitHub Actions (GitHub.com, docs as of 2026-10-30) - Composing CI/CD pipelines from building blocks

Unit: `composing-github-actions-pipelines` (family `github-actions-cicd`, unit 1).
Source item: "need: replaceable building blocks; monorepo".
Spec followed: `.claude/skills/researching-technical-frameworks/SKILL.md` (default depth), brief
`workspace/github-actions-cicd/execution-1/briefs/P4-research-composing-github-actions-pipelines.md`.
Family facts F1-F24 and family rules 1-16 applied as given (not edited).

Note on section order: the brief requires the file to END with the Source Bibliography, so the
template sections `Research Gaps`, `Research Iteration Changelog`, `Completion Checklist`,
`Agent Operation Notes` and the `Pages read` table come before `## Source Bibliography`.

Tag convention (family rule 2): `(medium confidence)` and `(unverified)` in plain parentheses.
Every page below was read on 2026-10-30 with WebFetch. "Version" for GitHub.com docs means the
live GitHub.com (Free/Pro/Team/Enterprise Cloud) docs on that date; GitHub Enterprise Server
pages were rejected as a different version.

---

## Metadata

```yaml
Full_Name: GitHub Actions (GitHub.com) - reusable workflows, composite actions, matrix, caching, concurrency, environments, artifacts
Target_Version: GitHub.com docs live on 2026-10-30 (no product semver; action majors per _family_facts.md F10, F4, F6, F23, F24)
Release_Date: n/a (continuously deployed SaaS)
Support_Status: Active
Primary_Docs: https://docs.github.com/en/actions
Official_Repo: https://github.com/actions
Research_Date: 2026-10-30
Domain_Complexity: Complex (multi-layer composition, secrets/permissions crossing workflow boundaries, plan-dependent features)
Research_Depth: default per spec (exhaustive declared default; no sub-investigators per brief hard constraint)
Max_Iterations: 5
Gap_Loop_Ran: true
Iterations_Used: 3 of 5
Triangulated_Count: 6
Unverified_Count: 6
Irresolvable_Count: 3
Research_Quality_Score: 92%   # ~75 claims, 6 unverified (3 of them irresolvable)
Target_Plan: GitHub Team / Pro / Free with PRIVATE repositories (family rule 16, G2 DEC-011)
Blocks_Location: same repository as the callers (G1 "Pecas: No proprio repo")
```

---

## Executive Summary

GitHub Actions offers two official building-block mechanisms: **reusable workflows**
(`on: workflow_call`, called at job level with `jobs.<id>.uses`) and **composite actions**
(`runs.using: composite` in an `action.yml`, called as one step). Reusable workflows contain
jobs, choose their own runners, can use secrets and environments, and log every job and step
separately; composite actions bundle steps into a single step of the caller's job, cannot use
the `secrets` context, and can be nested up to 10 composite actions in one workflow
(https://docs.github.com/en/actions/concepts/workflows-and-actions/reusing-workflow-configurations, 2026-10-30).
Reusable workflows must sit directly in `.github/workflows` (no subdirectories, F16), can be
chained up to ten levels and at most 50 unique reusable workflows per caller file (F17); the
caller's workflow-level `env` is not propagated (F18) and `secrets: inherit` reaches only the
directly called workflow (F19).

Changes visible in the 2026-10-30 docs that older guides miss: (1) a `$/.github/workflows/{filename}`
self-repository reference exists next to `./.github/workflows/{filename}` (not on GHES), and in
composite steps `$/` "resolves to that repository at the running commit, so you do not need to
check out the repository first"; (2) the 50-workflow limit (older GHES pages say 20); (3) jobs
using `strategy.matrix` can call a reusable workflow (older GHES pages said `strategy` was not
supported); (4) `concurrency.queue: max` allows up to 100 pending runs and cannot be combined
with `cancel-in-progress: true` (https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax, 2026-10-30).

Three critical patterns for this family: (a) blocks live in the same repo and are called with
local `./` paths, so they run at the caller's commit and need no ref pinning (Dependabot ignores
local refs); (b) every required status check must come from a workflow that always runs - path
filters leave required checks "Pending" and block merge, so monorepo change detection belongs
at job level behind an always-running `ci-gate` job; (c) on Team/Pro private repos environments
give secret scoping and deployment branch policies but NOT required reviewers, wait timers or
custom protection rules, and on Free private repos not even environment secrets. Complexity
tier: Complex, because secrets, `GITHUB_TOKEN` permissions and environments cross the
caller/called boundary with non-obvious rules.

---

## Architectural Guardrails

> Confidence legend: High (2+ official sources or 1 official reference page read in full, dated <=12mo) | Medium (1 partial source, or inference from official pieces) | Low (community).
> All third-party action SHAs come from `_family_facts.md`; SHA-pinning and script-injection
> guidance is NOT restated here - see `automating-github-repos-with-actions` (github-core).

### ✅ Mandatory Patterns

**M1. Reusable workflows sit flat in `.github/workflows` and use the `_<domain>-<name>.yml` prefix**
> Confidence: High | ✓✓ Triangulated | reuse-workflows how-to (2026-10-30) + workflow-syntax `jobs.<job_id>.uses` (2026-10-30)
- Why: "Subdirectories of the `workflows` directory are not supported." (F16). The leading `_`
  (family rule 5) is a naming convention of this family, not a GitHub feature, used to separate
  blocks from triggerable callers (`ci-<app>.yml`, `cd-<app>.yml`, `ops-<task>.yml`).
- Code:
  ```text
  .github/
    workflows/
      ci-web.yml               # caller, on: pull_request
      cd-web.yml               # caller, on: push to main
      _node-build.yml          # reusable, on: workflow_call
      _node-test.yml           # reusable, on: workflow_call
    actions/
      node/setup/action.yml    # composite action
      repo/changes/action.yml  # composite action
  ```
- Source: https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows (2026-10-30)

**M2. Every reusable workflow declares typed inputs, explicit outputs, named secrets and its own minimal permissions**
> Confidence: High | ✓✓ Triangulated | workflow-syntax `on.workflow_call` + reuse-workflows how-to (2026-10-30)
- Why: input `type` must be `boolean`, `number` or `string`; without a `default`, booleans default
  to `false`, numbers to `0`, strings to `""`; a caller passing an undeclared input or secret is an
  error. Outputs must map a job output (`value: ${{ jobs.<job>.outputs.<name> }}`). `required: true`
  on a secret "only checks whether the caller workflow passes the secret. It doesn't check whether
  the secret has a value." Family rule 6 forbids `secrets: inherit` in examples (F19).
- Code (GitHub.com, 2026-10-30; SHAs from F10, F23):
  ```yaml
  # .github/workflows/_node-build.yml
  name: _node-build
  on:
    workflow_call:
      inputs:
        app-dir:
          type: string
          required: true
        node-version:
          type: string
          default: "24"
        run-tests:
          type: boolean
          default: true
      outputs:
        artifact-name:
          description: Name of the uploaded build artifact
          value: ${{ jobs.build.outputs.artifact-name }}
      secrets:
        NPM_READ_TOKEN:
          required: false
  permissions:
    contents: read
  jobs:
    build:
      runs-on: ubuntu-latest
      timeout-minutes: 20
      outputs:
        artifact-name: ${{ steps.meta.outputs.name }}
      steps:
        - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        - uses: ./.github/actions/node/setup
          with:
            node-version: ${{ inputs.node-version }}
            working-directory: ${{ inputs.app-dir }}
            npm-token: ${{ secrets.NPM_READ_TOKEN }}
        - name: Build
          working-directory: ${{ inputs.app-dir }}
          run: npm run build
        - id: meta
          name: Compute artifact name
          env:
            APP_DIR: ${{ inputs.app-dir }}
          run: echo "name=build-${APP_DIR//\//-}-${GITHUB_SHA}" >> "$GITHUB_OUTPUT"
        - uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2
          with:
            name: ${{ steps.meta.outputs.name }}
            path: ${{ inputs.app-dir }}/dist
            retention-days: 7
  ```
  The Node major "24" is from F14; authors may choose another line listed there.
- Source: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax (2026-10-30); https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows (2026-10-30)

**M3. Callers pass values through `with`/`secrets` and read results only through `needs.<job>.outputs`**
> Confidence: High | ✓✓ Triangulated | reusing-workflow-configurations reference + contexts reference (2026-10-30)
- Why: caller workflow-level `env` "are not propagated to the called workflow" and the called
  workflow's env "are not accessible in the `env` context of the caller"; "You cannot, therefore,
  use `GITHUB_ENV` to pass values to job steps in the caller workflow" (F18). `needs` only covers
  direct dependencies. Outputs: max 1 MB per job, 50 MB per run; outputs containing secrets are
  redacted and not sent.
- Code:
  ```yaml
  # .github/workflows/cd-web.yml (excerpt)
  jobs:
    build:
      uses: ./.github/workflows/_node-build.yml
      permissions:
        contents: read
      with:
        app-dir: apps/web
      secrets:
        NPM_READ_TOKEN: ${{ secrets.NPM_READ_TOKEN }}
    publish:
      needs: build
      runs-on: ubuntu-latest
      timeout-minutes: 10
      steps:
        - uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333 # v8.0.2
          with:
            name: ${{ needs.build.outputs.artifact-name }}
  ```
- Source: https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations (2026-10-30); https://docs.github.com/en/actions/reference/workflows-and-actions/contexts (2026-10-30)

**M4. Set `permissions` on the calling job; the called workflow can only keep or reduce them**
> Confidence: High | ✓✓ Triangulated | reusing-workflow-configurations reference + reuse-workflows how-to (2026-10-30)
- Why: "If `jobs.<job_id>.permissions` is not specified in the calling job, the called workflow
  will have the default permissions for the `GITHUB_TOKEN`." "The `GITHUB_TOKEN` permissions passed
  from the caller workflow can be only downgraded (not elevated) by the called workflow." In
  nested chains "permissions can only be maintained or reduced-not elevated". Family rule 7:
  `id-token: write` only on the job that logs in.
- Code: see M3 (`permissions: contents: read` on the calling job) and the called workflow's own
  top-level `permissions` in M2.
- Source: https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations (2026-10-30); https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows (2026-10-30)

**M5. Composite actions declare `shell` on every `run` step, read inputs via the `inputs` context and map outputs with `value`**
> Confidence: High | metadata-syntax reference read in full (2026-10-30); create-a-composite-action tutorial (2026-10-30)
- Why: `runs.using` "must set this value to `'composite'`"; `shell` is "Required if `run` is set";
  a composite action "will not automatically get `INPUT_<VARIABLE_NAME>`" - use the `inputs`
  context; outputs need `value`. "Actions using `required: true` will not automatically return an
  error if the input is not specified." The `secrets` context "is not available for composite
  actions due to security reasons" - pass secrets explicitly as inputs. GitHub recommends the
  `.github/actions` subfolder.
- Code:
  ```yaml
  # .github/actions/node/setup/action.yml
  name: node-setup
  description: Install Node.js and project dependencies for one app directory
  inputs:
    node-version:
      description: Node.js major
      required: true
    working-directory:
      description: App directory containing package-lock.json
      required: true
    npm-token:
      description: Optional read token for a private registry (passed by the caller)
      required: false
      default: ""
  outputs:
    node-path:
      description: Path of the node binary
      value: ${{ steps.which.outputs.path }}
  runs:
    using: composite
    steps:
      - uses: actions/setup-node@949feb2413d6458794dcd2491c4babbbce0c15c1 # v7.1.0
        with:
          node-version: ${{ inputs.node-version }}
          cache: npm   # setup-node input name not verified in this research (unverified)
          cache-dependency-path: ${{ inputs.working-directory }}/package-lock.json   # (unverified)
      - name: Fail fast on missing required input
        shell: bash
        env:
          WD: ${{ inputs.working-directory }}
        run: test -n "$WD" || { echo "working-directory is required"; exit 1; }
      - name: Install
        shell: bash
        working-directory: ${{ inputs.working-directory }}
        env:
          NODE_AUTH_TOKEN: ${{ inputs.npm-token }}
        run: npm ci
      - id: which
        shell: bash
        run: echo "path=$(command -v node)" >> "$GITHUB_OUTPUT"
  ```
- Source: https://docs.github.com/en/actions/reference/workflows-and-actions/metadata-syntax (2026-10-30); https://docs.github.com/en/actions/creating-actions/creating-a-composite-action (2026-10-30); https://docs.github.com/en/actions/reference/workflows-and-actions/contexts (2026-10-30)

**M6. Required status checks come only from workflows that always run; gate them with an `always()` aggregate job**
> Confidence: High | ✓✓ Triangulated | troubleshooting-required-status-checks (2026-10-30) + workflow-syntax path filters (2026-10-30)
- Why: if a workflow is skipped by path filtering, branch filtering or a commit message, "checks
  associated with that workflow will remain in a "Pending" state" and a PR requiring them "will be
  blocked from merging". GitHub's advice: "Avoid requiring workflows that can be skipped." A job
  skipped by an `if` conditional reports Success; a dependent job of a failed/skipped job "is
  skipped and may not block merging" - "Use `always()` with `needs` for required checks that depend
  on other jobs". `needs.<job_id>.result` is one of `success`, `failure`, `cancelled`, `skipped`.
- Code: see Implementation Blueprint, job `ci-gate`. Require only `ci-gate` in branch protection
  or the ruleset.
- Source: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/troubleshooting-required-status-checks (2026-10-30); https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax (2026-10-30); https://docs.github.com/en/actions/reference/workflows-and-actions/contexts (2026-10-30)

**M7. Set `timeout-minutes` on every job (default is 360)**
> Confidence: High | workflow-syntax reference read in full (2026-10-30)
- Why: job default "Default: 360"; step `timeout-minutes` "Maximum: 360 for both GitHub-hosted
  and self-hosted runners". A hung job otherwise burns up to 6 hours of private-repo minutes.
  The value chosen (e.g. 10-30) is a family choice, not a GitHub default.
- Code: `timeout-minutes: 20` on each job in M2/M3.
- Source: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax (2026-10-30)

**M8. Put `environment:` on a job inside the called workflow, never on the calling job**
> Confidence: High | reuse-workflows how-to (2026-10-30)
- Why: "The job that calls the reusable workflow can't use the `environment` keyword." Pass the
  environment name as a `string` input and set `environment: ${{ inputs.environment }}` on the
  deploying job of the reusable workflow. Environment secrets are then read inside that job; the
  how-to notes an environment secret the caller does not supply resolves to an empty string
  unless the secret is declared `required: true` (medium confidence - summarised wording).
- Code:
  ```yaml
  # .github/workflows/_deploy-static.yml (excerpt)
  on:
    workflow_call:
      inputs:
        environment:
          type: string
          required: true
        artifact-name:
          type: string
          required: true
  permissions:
    contents: read
  jobs:
    deploy:
      runs-on: ubuntu-latest
      timeout-minutes: 15
      environment: ${{ inputs.environment }}
      concurrency:
        group: deploy-${{ inputs.environment }}
        cancel-in-progress: false
      steps:
        - uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333 # v8.0.2
          with:
            name: ${{ inputs.artifact-name }}
        - name: Deploy
          run: echo "cloud-specific deploy is owned by the target skill (e.g. deploying-aws-lambda)"
  ```
- Source: https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows (2026-10-30)

### ⚠️ Conditional Patterns

**C1. Composite action vs reusable workflow**
> Confidence: High (comparison facts) | concepts/reusing-workflow-configurations (2026-10-30)
- Options: A) composite action, B) reusable workflow.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | Composite action | Runs inside the caller's job (shares workspace, no extra runner); up to 10 nested composite actions; publishable to Marketplace | No `secrets` context (inputs only); logged as one step; cannot pick a runner; no jobs/environments | Repeated step sequences: setup toolchain, install, lint, compute metadata |
  | Reusable workflow | Own jobs, own runners, separate logs per job/step, secrets, environments, permissions | New runner per job (artifacts needed to share files); 10-level nesting, 50 unique per caller (F17); no Marketplace | A whole stage: build, test matrix, deploy to an environment |

- Agent: "Ask: does the block need its own runner, a secret, an environment or several jobs? If any yes -> reusable workflow; else composite action."
- Source: https://docs.github.com/en/actions/concepts/workflows-and-actions/reusing-workflow-configurations (2026-10-30)

**C2. Blocks in the same repo (default) vs a central blocks repo**
> Confidence: High (mechanics) / Medium (Pro user-account wording)
- Options: A) local `./.github/workflows/_x.yml` and `./.github/actions/<domain>/<name>` (G1 decision);
  B) `{owner}/{repo}/.github/workflows/{filename}@{ref}` from a central repo.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A local | Block and caller change in one PR, run at the same commit; no access settings; no ref bumps | Duplication across repos | One repo or monorepo (this family's default) |
  | B central | One source for many repos | Private repo must allow access ("Accessible from repositories in the 'ORGANIZATION-NAME' organization"); callers must pin and bump refs; outside collaborators of caller repos can indirectly view the private repo's workflow logs | Many repos in one organization |

- B details: `{ref}` "can be a SHA, a release tag, or a branch name"; "Using the commit SHA is the
  safest option for stability and security." A `private` caller can use `private` and `public`
  workflow repos; a `public` caller only `public`. "GitHub Actions does not support redirects for
  actions or reusable workflows." Re-running failed jobs uses the reusable workflow "from the same
  commit SHA of the first attempt". `secrets: inherit` works only within the same org/enterprise
  (F19). Equivalent setting for a personal (Pro) account's private repo was not found (unverified).
- Agent: "Ask whether blocks must be shared across repositories; default A."
- Source: https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows (2026-10-30); https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations (2026-10-30); https://docs.github.com/en/actions/how-tos/reuse-automations/share-with-your-organization (2026-10-30)

**C3. Dependabot for blocks and actions**
> Confidence: High (local refs ignored, comment update) / Medium (remote reusable workflows)
- Facts: Dependabot `github-actions` needs `directory: "/"` to scan `.github/workflows` (and the
  root `action.yml`); `directories` supports globs. "Dependabot will ignore actions or reusable
  workflows referenced locally (for example, `./.github/actions/foo.yml`)." It supports
  `owner/repo@tag` and `owner/repo@<commit>`; "If the commit you use is not associated with any
  tag, Dependabot will update the GitHub Actions to the latest commit"; it "updates the version
  documentation of GitHub Actions when the comment is on the same line." The how-to page says
  "reusable workflows used inside workflows are kept up to date" (medium confidence: the page does
  not show the `jobs.<id>.uses` case explicitly). Whether Dependabot scans
  `.github/actions/<domain>/<name>/action.yml` through `directories` globs is (unverified).
- Options: A) `directory: "/"` only; B) `directories: ["/", "/.github/actions/*/*"]` (unverified scan behaviour).
- Agent: "Ask whether composite actions use third-party actions; if yes, prefer B and verify on the first Dependabot run."
- Source: https://docs.github.com/en/code-security/dependabot/working-with-dependabot/keeping-your-actions-up-to-date-with-dependabot (2026-10-30); https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference (2026-10-30); https://docs.github.com/en/code-security/dependabot/ecosystems-supported-by-dependabot/supported-ecosystems-and-repositories (2026-10-30)

**C4. Environment features available on the target plan (Team/Pro/Free, private repos)**
> Confidence: High | deployments-and-environments reference (2026-10-30)
- Facts:

  | Feature | Free, private | Pro / Team, private | Public repos / Enterprise |
  |---|---|---|---|
  | Environment secrets | No ("you must use GitHub Pro, GitHub Team, or GitHub Enterprise") | Yes | Yes |
  | Environment variables | not stated (unverified) | Yes | Yes |
  | Deployment branches and tags policy | not stated (unverified) | Yes | Yes |
  | Required reviewers (up to 6, one approval) | No | No ("only available for public repositories") | Yes |
  | Wait timer (1-43,200 min) | No | No | Yes |
  | Custom deployment protection rules | No | No | Yes |

  Policy options: no restriction, protected branches only, selected branches and tags.
- Options: A) Pro/Team: environment secrets + "selected branches and tags" policy, approval via a
  mechanism owned by `limiting-blast-radius-github-actions-deploys` (family rule 16);
  B) Free private: no environment secrets -> deploy credentials would have to be repository
  secrets, which family rule 10 forbids -> ask the user to move to Pro/Team or make the repo public.
- Agent: "Ask which plan the repo owner has (Free vs Pro/Team) before generating any deploy job."
- Source: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments (2026-10-30)

**C5. Monorepo change detection: per-app callers with path filters vs one caller with job-level detection**
> Confidence: High (path-filter facts) / Medium (job-level design, composed from official pieces)
- Options: A) one `ci-<app>.yml` per app with `on.pull_request.paths`; B) one `ci-monorepo.yml`
  without path filters, a `changes` job emitting outputs, per-app jobs with `if:`, and an
  `always()` `ci-gate` job (Implementation Blueprint).
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A path filters | Simple; zero runs for untouched apps | Skipped workflows leave required checks Pending -> cannot be required checks; diff >3,000 files may skip; tags not evaluated | Apps are not merge-gating, or checks are informational |
  | B job-level | One required check (`ci-gate`) that always reports; skipped jobs report Success | One small always-on job per PR; detection script to maintain | Merge-gating monorepo CI (default) |

- Path filter facts: cannot use `paths` and `paths-ignore` for the same event; use `!` negation in
  `paths`; pushes use two-dot and PRs three-dot diffs; >1,000 commits always runs; "Path filters
  are not evaluated for pushes of tags."
- Agent: "Ask whether per-app checks must block merge; if yes, B."
- Source: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax (2026-10-30); https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/troubleshooting-required-status-checks (2026-10-30)

**C6. Caching: setup-* built-in cache vs `actions/cache`**
> Confidence: High (cache semantics) / Medium (choice)
- Facts: setup-node, setup-python, setup-java, setup-ruby, setup-go, setup-dotnet offer caching with
  "minimal configuration". Restore order: exact `key`, then `restore-keys` in order (most recent
  partial match). Runs restore caches from the current branch or the default branch (PRs also the
  base branch); PR caches are created for the merge ref. Default limit 10 GB per repository;
  entries not accessed in 7 days are removed; caches are immutable; `cache-hit` reports an exact
  match. "Anyone with read access can create a pull request on a repository and access the
  contents of a cache" - never cache secrets.
- Options: A) built-in cache of setup-node (F6) / setup-java (F4); B) `actions/cache` for other
  paths (no SHA in facts file - see Facts requested).
- Agent: "Default A; ask before adding B."
- Source: https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching (2026-10-30)

**C7. Concurrency policy per workflow kind**
> Confidence: High
- Facts: at most one running and one pending run per group; a new run replaces the pending one;
  `cancel-in-progress: true` also cancels the running one; `github.head_ref` is only defined on
  `pull_request` (fallback `github.run_id`); group names must be unique across workflows (use
  `github.workflow`); group names are case-insensitive; `queue: max` keeps up to 100 pending runs and
  is invalid with `cancel-in-progress: true`. In a called workflow, `${{ github.workflow }}` is the
  caller's workflow name.
- Options: A) CI: `group: ${{ github.workflow }}-${{ github.head_ref || github.run_id }}`,
  `cancel-in-progress: true`; B) deploy: `group: deploy-<env>`, `cancel-in-progress: false`
  (never kill a deploy mid-way; medium confidence - design inference); C) `queue: max` when every
  pending deploy must run.
- Source: https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency (2026-10-30); https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax (2026-10-30); https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations (2026-10-30)

**C8. Matrix size and failure policy**
> Confidence: High
- Facts: max 256 jobs per workflow run; `fail-fast` defaults to `true` (cancels in-progress and
  queued jobs when a job with `continue-on-error: false` fails); `max-parallel` caps concurrency
  (default: as many as runners allow); `include` adds to or extends combinations; a matrix can be
  built from a previous job's output with `fromJSON(needs.<job>.outputs.<x>)`; a matrix job can call
  a reusable workflow, and the caller's output is "the output set by the last successful completing
  reusable workflow of the matrix which actually sets a value".
- Options: A) `fail-fast: true` for PR feedback; B) `fail-fast: false` for a full compatibility report.
- Source: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax (2026-10-30); https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/run-job-variations (2026-10-30); https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows (2026-10-30)

### 🚫 Forbidden Patterns

**F1. Reusable workflow in a subfolder of `.github/workflows`**
> Severity: High
> Confidence: High
- Why: subdirectories are not supported (F16).
- Impact: the call fails; the block cannot be used.
- ❌ Wrong:
  ```yaml
  uses: ./.github/workflows/node/build.yml
  ```
- ✅ Correct:
  ```yaml
  uses: ./.github/workflows/_node-build.yml
  ```
- Source: https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows (2026-10-30)

**F2. `secrets: inherit` to a block**
> Severity: High
> Confidence: High
- Why: passes all caller secrets, only one level deep (F19); hides which secrets a block needs;
  family rule 6.
- Impact: over-exposure of deploy secrets to every block; nested blocks silently get empty secrets.
- ❌ Wrong:
  ```yaml
  build:
    uses: ./.github/workflows/_node-build.yml
    secrets: inherit
  ```
- ✅ Correct:
  ```yaml
  build:
    uses: ./.github/workflows/_node-build.yml
    secrets:
      NPM_READ_TOKEN: ${{ secrets.NPM_READ_TOKEN }}
  ```
- Source: https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows (2026-10-30); https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax (2026-10-30)

**F3. Relying on caller `env` or `GITHUB_ENV` to reach or return from a reusable workflow**
> Severity: Medium
> Confidence: High
- Why: not propagated (F18).
- Impact: the called workflow sees empty values; the caller never sees results.
- ❌ Wrong:
  ```yaml
  env:
    APP_DIR: apps/web
  jobs:
    build:
      uses: ./.github/workflows/_node-build.yml   # expects env.APP_DIR
  ```
- ✅ Correct:
  ```yaml
  jobs:
    build:
      uses: ./.github/workflows/_node-build.yml
      with:
        app-dir: apps/web
  ```
- Source: https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations (2026-10-30)

**F4. `environment:` on the calling job**
> Severity: High
> Confidence: High
- Why: "The job that calls the reusable workflow can't use the `environment` keyword."
- Impact: invalid workflow; or teams fall back to repository secrets (breaks family rule 10).
- ❌ Wrong:
  ```yaml
  deploy:
    uses: ./.github/workflows/_deploy-static.yml
    environment: prod
  ```
- ✅ Correct:
  ```yaml
  deploy:
    uses: ./.github/workflows/_deploy-static.yml
    with:
      environment: prod
      artifact-name: ${{ needs.build.outputs.artifact-name }}
  ```
- Source: https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows (2026-10-30)

**F5. `secrets.X` inside a composite action**
> Severity: High
> Confidence: High
- Why: "The `secrets` context is not available for composite actions due to security reasons."
- Impact: the expression fails or is empty; the step runs without credentials.
- ❌ Wrong:
  ```yaml
  # .github/actions/node/setup/action.yml
  env:
    NODE_AUTH_TOKEN: ${{ secrets.NPM_READ_TOKEN }}
  ```
- ✅ Correct:
  ```yaml
  # action.yml declares inputs.npm-token; the caller passes it
  env:
    NODE_AUTH_TOKEN: ${{ inputs.npm-token }}
  ```
- Source: https://docs.github.com/en/actions/reference/workflows-and-actions/contexts (2026-10-30); https://docs.github.com/en/actions/concepts/workflows-and-actions/reusing-workflow-configurations (2026-10-30)

**F6. `run` step without `shell` in a composite action**
> Severity: Medium
> Confidence: High
- Why: `shell` is "Required if `run` is set".
- Impact: action metadata invalid; every caller fails.
- ❌ Wrong:
  ```yaml
  runs:
    using: composite
    steps:
      - run: npm ci
  ```
- ✅ Correct:
  ```yaml
  runs:
    using: composite
    steps:
      - run: npm ci
        shell: bash
  ```
- Source: https://docs.github.com/en/actions/reference/workflows-and-actions/metadata-syntax (2026-10-30)

**F7. Requiring a check from a path-filtered workflow**
> Severity: High
> Confidence: High
- Why: skipped workflow -> check stays Pending -> PR blocked.
- Impact: PRs that do not touch the app can never merge.
- ❌ Wrong:
  ```yaml
  # ci-web.yml, and "ci-web / build" set as required
  on:
    pull_request:
      paths: ["apps/web/**"]
  ```
- ✅ Correct:
  ```yaml
  # ci-monorepo.yml, no path filter; only "ci-gate" is required
  on:
    pull_request:
  jobs:
    ci-gate:
      if: always()
      needs: [changes, web]
  ```
- Source: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/troubleshooting-required-status-checks (2026-10-30)

**F8. Elevating permissions in the called workflow**
> Severity: High
> Confidence: High
- Why: the called workflow can only downgrade; elevation does not work and hides intent.
- Impact: the step fails with 403, or teams widen the default token for every workflow.
- ❌ Wrong:
  ```yaml
  # caller: permissions: contents: read
  # _x.yml:
  permissions:
    contents: write
  ```
- ✅ Correct:
  ```yaml
  # caller grants exactly what the block needs on the calling job
  publish:
    uses: ./.github/workflows/_x.yml
    permissions:
      contents: write
  ```
- Source: https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations (2026-10-30)

**F9. Using `paths` and `paths-ignore` on the same event**
> Severity: Medium
> Confidence: High
- Why: "You cannot use both the `paths` and `paths-ignore` filters for the same event in a workflow."
- Impact: invalid workflow.
- ❌ Wrong:
  ```yaml
  on:
    push:
      paths: ["apps/**"]
      paths-ignore: ["apps/**/*.md"]
  ```
- ✅ Correct:
  ```yaml
  on:
    push:
      paths:
        - "apps/**"
        - "!apps/**/*.md"
  ```
- Source: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax (2026-10-30)

**F10. Secrets or credentials in cache paths**
> Severity: Critical
> Confidence: High
- Why: anyone with read access can open a PR and read cache contents.
- Impact: credential leak.
- ❌ Wrong:
  ```yaml
  path: |
    ~/.npm
    ~/.npmrc        # contains a token
  ```
- ✅ Correct:
  ```yaml
  path: ~/.npm      # token provided at run time via NODE_AUTH_TOKEN input, never cached
  ```
- Source: https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching (2026-10-30)

---

## Migration Guide

> Confidence: High for items read on current pages; older behaviour seen only on rejected GHES mirrors (via search snippets, not used as evidence).

**Breaking / changed behaviour vs older guides**:
- Unique reusable workflows per caller file: now 50 (F17); older GHES pages said 20.
- `strategy.matrix` on a job that calls a reusable workflow: now supported ("Jobs using the matrix
  strategy can call a reusable workflow"); older GHES pages said not supported.
- New `$/` self-repository reference for `jobs.<id>.uses` and composite `steps[*].uses` (not on GHES);
  for composite steps it removes the need to check out first. Family rule 15 keeps `./` in examples.
- `concurrency.queue` (`single` default, `max` up to 100 pending) is new; `queue: max` +
  `cancel-in-progress: true` is a validation error.
- Artifacts are immutable from upload-artifact v4: re-uploading the same name needs a new name
  (store-and-share-data tutorial); action majors per F23/F24, never from doc examples (they show
  stale majors).

**Upgrade Steps**:
1. Move any `.github/workflows/<dir>/x.yml` to `.github/workflows/_<domain>-<name>.yml` and update `uses:`.
2. Replace `secrets: inherit` with named secrets per block.
3. Move `environment:` from calling jobs into the called workflow (input `environment`).
4. Replace path-filtered required workflows with the `ci-gate` pattern; update the required check list to `ci-gate`.
5. Add `timeout-minutes` to every job.

**Compatibility Matrix**:

| Dependency | Pin (from facts) | Notes |
|------------|------------------|-------|
| actions/checkout | v7.0.1 `3d3c42e5aac5ba805825da76410c181273ba90b1` | F10 |
| actions/setup-node | v7.1.0 `949feb2413d6458794dcd2491c4babbbce0c15c1` | F6 |
| actions/setup-java | v6.1.0 `b843ebf9b913146b38da2eaa7aeddf76074ae1ad` | F4 |
| actions/upload-artifact | v7.0.2 `cf430e030ddbb5b0abf93d22962f4752f3646cd9` | F23; default retention 90 days |
| actions/download-artifact | v8.0.2 `9000827ccba6bdab643e8b6fd33ac0654aef8333` | F24 |
| actions/cache | not in facts file | Facts requested |

---

## Implementation Blueprint

> Confidence: High for each keyword (sources per guardrail); Medium for the combined monorepo design (composition of official features, not an official example).

**Monorepo PR caller with job-level change detection and a single required gate (GitHub.com, 2026-10-30)**:
```yaml
# .github/workflows/ci-monorepo.yml
name: ci-monorepo
on:
  pull_request:
permissions:
  contents: read
concurrency:
  group: ${{ github.workflow }}-${{ github.head_ref || github.run_id }}
  cancel-in-progress: true
jobs:
  changes:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    outputs:
      web: ${{ steps.diff.outputs.web }}
      api: ${{ steps.diff.outputs.api }}
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          fetch-depth: 0   # checkout input not verified in this research (unverified)
      - id: diff
        uses: ./.github/actions/repo/changes
        with:
          base-sha: ${{ github.event.pull_request.base.sha }}
  web:
    needs: changes
    if: needs.changes.outputs.web == 'true'
    uses: ./.github/workflows/_node-build.yml
    permissions:
      contents: read
    with:
      app-dir: apps/web
  api:
    needs: changes
    if: needs.changes.outputs.api == 'true'
    uses: ./.github/workflows/_java-build.yml   # analogous block using setup-java (F4)
    permissions:
      contents: read
    with:
      app-dir: services/api
  ci-gate:
    if: always()
    needs: [changes, web, api]
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - name: Fail if any needed job failed or was cancelled
        env:
          R_CHANGES: ${{ needs.changes.result }}
          R_WEB: ${{ needs.web.result }}
          R_API: ${{ needs.api.result }}
        run: |
          for r in "$R_CHANGES" "$R_WEB" "$R_API"; do
            case "$r" in
              success|skipped) ;;
              *) echo "a required job ended with: $r"; exit 1 ;;
            esac
          done
```

```yaml
# .github/actions/repo/changes/action.yml
name: repo-changes
description: Emit true/false per app area from the PR diff
inputs:
  base-sha:
    description: Base commit of the pull request
    required: true
outputs:
  web:
    description: apps/web changed
    value: ${{ steps.calc.outputs.web }}
  api:
    description: services/api changed
    value: ${{ steps.calc.outputs.api }}
runs:
  using: composite
  steps:
    - id: calc
      shell: bash
      env:
        BASE_SHA: ${{ inputs.base-sha }}
      run: |
        files="$(git diff --name-only "$BASE_SHA"...HEAD)"
        has() { grep -Eq "$1" <<<"$files" && echo true || echo false; }
        shared="$(has '^(\.github/|package-lock\.json$)')"
        web="$(has '^apps/web/')"; api="$(has '^services/api/')"
        [ "$shared" = true ] && web=true && api=true
        { echo "web=$web"; echo "api=$api"; } >> "$GITHUB_OUTPUT"
```
Notes: the three-dot `git diff` mirrors how GitHub evaluates PR path filters (three-dot diffs);
changes under `.github/` re-run everything because blocks are local. Per family rule 7/13 this PR
workflow never deploys or uses deployable-environment credentials.

**Status check names produced by reusable workflows**: community sources report the check context
as `<caller job id or name> / <called job name>`; not confirmed on an official page (unverified).
The `ci-gate` design avoids depending on it because `ci-gate` is a normal job.

**Integration**: GitHub Actions <-> cloud deploy skills - the deploy step inside `_deploy-*.yml` is
owned by other skills (`deploying-aws-lambda`, `automating-terraform-github-actions-v1-17`,
`limiting-blast-radius-github-actions-deploys`); referenced by name only (family rule 12).

---

## Quality Control

**Verification Commands**:
```bash
# Representative - adapt to your environment
# 1. No reusable workflow in a subfolder (F16)
find .github/workflows -mindepth 2 -name '*.yml'          # Expected: no output
# 2. Every reusable workflow follows the _ prefix and declares workflow_call
grep -L 'workflow_call' .github/workflows/_*.yml           # Expected: no output
# 3. No secrets: inherit (family rule 6)
grep -rn 'secrets: inherit' .github/                        # Expected: no output, exit 1
# 4. Every composite run step has shell
grep -c 'run:' .github/actions/*/*/action.yml               # compare with:
grep -c 'shell:' .github/actions/*/*/action.yml             # Expected: shell count >= run count per file
# 5. No secrets context in composite actions
grep -rn 'secrets\.' .github/actions/                       # Expected: no output
# 6. Every job has a timeout (count jobs vs timeouts; reusable-calling jobs are exempt)
grep -c 'timeout-minutes:' .github/workflows/*.yml
# 7. Lint (actionlint is community tooling, version not in facts file)   (unverified)
```

**Mocking / testing**: GitHub provides no official local runner for workflows in the pages read;
test blocks by calling them from a throwaway `ops-test-<block>.yml` with `workflow_dispatch` on a
branch (medium confidence - design inference).

---

## Production Readiness

- **Performance**: composite actions avoid a new runner per block; reusable workflows add one job
  (and runner start) per called job; share files between jobs only via artifacts (store-and-share-data).
  Cache: 10 GB default per repo, 7-day eviction.
- **Scalability**: 256 matrix jobs per run; 10 nesting levels and 50 unique reusable workflows per
  caller (F17); 10 nested composite actions; outputs 1 MB/job, 50 MB/run; concurrency `queue: max` 100 pending.
- **Monitoring**: reusable workflows log each job/step separately; composite actions log as one step
  - keep composite actions short so failures are locatable.
- **Security**: minimal `permissions` on calling jobs (only downgrade possible downstream); named
  secrets; no secrets in caches; environment secrets for deploy jobs only on Pro/Team private
  repos; PR jobs never get deployable-environment credentials (family rule 13); injection and SHA
  pinning per `automating-github-repos-with-actions`.
- **Cost**: set `timeout-minutes` (default 360); `cancel-in-progress: true` for PR CI.

---

## Reference Implementations

- Reuse workflows how-to (examples of `workflow_call` inputs/secrets/outputs, matrix calls): https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows
- Composite action tutorial (`.github/actions` subfolder, outputs via `GITHUB_OUTPUT`): https://docs.github.com/en/actions/creating-actions/creating-a-composite-action
- Matrix examples incl. dynamic matrix from job output: https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/run-job-variations
- Concurrency examples: https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency
- Do NOT copy action versions from these examples (brief lesson 1); use `_family_facts.md`.

---

## Research Gaps

```
Gap: Exact status-check context name for jobs inside a called reusable workflow
Impact: Required-check rules may never match if written by hand
Workaround: Require only the plain `ci-gate` job; read the exact name from a PR's checks list
Follow-up: docs.github.com reusable workflows / status checks pages; GitHub changelog
§7-ref: Iteration 2 - IRRESOLVABLE
```
```
Gap: Whether Dependabot scans composite actions under .github/actions/<domain>/<name> via `directories` globs
Impact: Third-party actions inside composite actions may not get update PRs
Workaround: list the directories explicitly and confirm on the first Dependabot run
Follow-up: Dependabot options reference (github-actions directory notes)
§7-ref: Iteration 3 - IRRESOLVABLE
```
```
Gap: Environment variables and deployment branch policies on GitHub Free private repos; access setting wording for a personal (Pro) account's private blocks repo
Impact: Free-plan users may lack branch-policy scoping
Workaround: treat Free private as "no environment features" and ask the user (C4)
Follow-up: GitHub plans page; deployments-and-environments reference
§7-ref: Iteration 3 - IRRESOLVABLE
```
Other (unverified) items: setup-node `cache` / `cache-dependency-path` input names and checkout
`fetch-depth` (action READMEs not read in this unit); actionlint (community tool, no facts row).

---

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | C3 | Dependabot SHA refs and version comments | Resolved | https://docs.github.com/en/code-security/dependabot/ecosystems-supported-by-dependabot/supported-ecosystems-and-repositories (2026-10-30) |
| 1 | M6 | Required-check troubleshooting page (first URL 404) | Resolved via defining-the-mergeability path | https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/troubleshooting-required-status-checks (2026-10-30) |
| 1 | M7/C8 | timeout default, fail-fast default, 256 matrix limit | Resolved (workflow-syntax offsets 100000, 200000) | https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax (2026-10-30) |
| 1 | M6 | `needs.<job_id>.result` values | Resolved (contexts offset 100000) | https://docs.github.com/en/actions/reference/workflows-and-actions/contexts (2026-10-30) |
| 2 | Blueprint | Check name format for called jobs | ⚠️ IRRESOLVABLE - only community sources found | - |
| 3 | C3 | Dependabot scanning composite actions in subfolders | ⚠️ IRRESOLVABLE - not stated on 3 official pages | - |
| 3 | C4 | Free private: env variables / branch policies | ⚠️ IRRESOLVABLE - not stated on the environments reference | - |

---

## Completion Checklist

- [x] Domain complexity tier assessed and documented (Complex)
- [x] All scope areas cited (reusable workflows, composite actions, matrix, caching, concurrency, environments, path filters/change detection, artifacts, required checks, timeouts, versioning/Dependabot)
- [x] Pattern counts driven by domain needs
- [x] Every anti-pattern has alternative
- [x] All CLI commands marked as representative
- [x] Integration examples complete (deploy step delegated by name)
- [x] Sources dated and linked
- [x] Security documented
- [x] 1+ copy-paste working example (pins from facts file)
- [x] Confidence badge applied to every pattern entry
- [x] Always-Do patterns triangulated or marked single-source (M5, M7, M8 single official reference page read in full)
- [x] Research Iteration Changelog present
- [x] Research_Quality_Score in Metadata
- [x] Every Research Gap cross-referenced in changelog

---

## Agent Operation Notes

- **High Confidence**: M1-M8 facts, F1-F10, C1, C4 table rows marked yes/no, C6-C8 facts.
- **Medium Confidence**: combined monorepo design (C5 B / Blueprint), deploy concurrency `cancel-in-progress: false`, Dependabot updating remote reusable-workflow refs, environment-secret-empty-string wording, testing via `ops-test-*`.
- **Low / must ask**: plan of the repo owner (Free vs Pro/Team) before any deploy job; cross-repo sharing.
- **Facts requested** (not invented, for the orchestrator to add to `_family_facts.md` if wanted):
  - `actions/cache` - repo https://github.com/actions/cache, tag and SHA NOT resolved (no release page read), source https://github.com/actions/cache/releases. Only needed if a skill example uses `actions/cache` directly; the default (C6 A) avoids it.
- **Not requested on purpose**: third-party path-filter actions; the native `changes` composite action covers job-level detection.

---

## Pages read

| URL | read on | official | prompt-injection-like instructions found |
|---|---|---|---|
| https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/concepts/workflows-and-actions/reusing-workflow-configurations | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/reference/workflows-and-actions/metadata-syntax | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/creating-actions/creating-a-composite-action | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/how-tos/reuse-automations/share-with-your-organization | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax (3 passes: chars 0-100000, 100000-200000, 200000-235839 = full) | 2026-10-30 | yes | no (promotional tip only) |
| https://docs.github.com/en/actions/reference/workflows-and-actions/contexts (2 passes, 113682 chars = full) | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/run-job-variations | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/tutorials/store-and-share-data | 2026-10-30 | yes | no |
| https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/troubleshooting-required-status-checks | 2026-10-30 | yes | no |
| https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/troubleshooting-required-status-checks | 2026-10-30 | yes | n/a (HTTP 404) |
| https://docs.github.com/en/actions/how-tos/reuse-automations/create-actions/create-a-composite-action | 2026-10-30 | yes | n/a (HTTP 404) |
| https://docs.github.com/en/code-security/dependabot/working-with-dependabot/keeping-your-actions-up-to-date-with-dependabot | 2026-10-30 | yes | no |
| https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference (2 passes, 182383 chars = full) | 2026-10-30 | yes | no (HTML comment for doc editors) |
| https://docs.github.com/en/code-security/dependabot/ecosystems-supported-by-dependabot/supported-ecosystems-and-repositories (2 passes, 149980 chars = full) | 2026-10-30 | yes | no (HTML comments for doc editors) |
| WebSearch results: GHES troubleshooting-required-status-checks mirrors (3.0-3.4) | 2026-10-30 | yes, but GHES = rejected version | no |
| WebSearch results: keepiq PR #146, devactivity.com, oneuptime.com, archgate PR #131 (check-name format) | 2026-10-30 | no (community, rejected as evidence) | no |

All pages were read through WebFetch, which returns a model-summarised extraction; quoted strings
are the tool's verbatim extracts.

---

## Source Bibliography

**Primary (official, GitHub.com docs, read 2026-10-30)**:
- Reusing workflow configurations (reference) - limits, env, permissions, access, refs, re-runs: https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations
- Reuse workflows (how-to) - location, inputs, secrets, outputs, call syntax, nesting, matrix, environment restriction: https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows
- Reusing workflow configurations (concepts) - composite vs reusable comparison, workflow templates: https://docs.github.com/en/actions/concepts/workflows-and-actions/reusing-workflow-configurations
- Metadata syntax - composite actions: https://docs.github.com/en/actions/reference/workflows-and-actions/metadata-syntax
- Creating a composite action: https://docs.github.com/en/actions/creating-actions/creating-a-composite-action
- Sharing actions and workflows with your organization: https://docs.github.com/en/actions/how-tos/reuse-automations/share-with-your-organization
- Workflow syntax - workflow_call, uses/with/secrets, paths filters, timeouts, strategy, outputs, concurrency queue: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
- Contexts - needs result/outputs, inputs, secrets in composite actions: https://docs.github.com/en/actions/reference/workflows-and-actions/contexts
- Running variations of jobs (matrix): https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/run-job-variations
- Dependency caching reference: https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching
- Control workflow concurrency: https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency
- Deployments and environments reference - plan availability: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments
- Store and share data (artifacts): https://docs.github.com/en/actions/tutorials/store-and-share-data
- Troubleshooting required status checks: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/troubleshooting-required-status-checks
- Keeping your actions up to date with Dependabot: https://docs.github.com/en/code-security/dependabot/working-with-dependabot/keeping-your-actions-up-to-date-with-dependabot
- Dependabot options reference: https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference
- Dependabot supported ecosystems and repositories: https://docs.github.com/en/code-security/dependabot/ecosystems-supported-by-dependabot/supported-ecosystems-and-repositories

**Family facts used (verified by orchestrator, 2026-10-30)**: F4, F6, F10, F14, F16, F17, F18, F19, F23, F24 in `workspace/github-actions-cicd/_family_facts.md`.

**Validation (community, NOT used as evidence; only to locate the check-name gap)**:
- https://github.com/ConductionNL/keepiq/pull/146
- https://devactivity.com/insights/streamlining-github-actions-resolving-required-status-check-mismatches-for-enhanced-productivity
- https://github.com/archgate/cli/pull/131
