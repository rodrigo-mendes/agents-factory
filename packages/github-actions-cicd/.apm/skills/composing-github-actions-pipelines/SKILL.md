---
name: composing-github-actions-pipelines
description: "Composes GitHub Actions CI/CD from replaceable building blocks: caller workflows, reusable workflows, composite actions, a single ci-gate required check for monorepos. Use when structuring, splitting or reviewing pipelines. Not for cloud login or deploy logic."
---

# Composing GitHub Actions pipelines from building blocks

> Version lock: GitHub.com Actions docs as read on **2026-10-30** (no product semver). Third-party action pins come only from the family facts, never from doc examples.
> Claims tagged unverified or medium confidence were not fully confirmed against an official page; each tag maps to the [register](./blueprints/unverified-and-risks.md#tag-to-register-mapping).
> Scope: the base skill of the family. It owns the building-block model and the block contract; the sibling skills own what runs inside each block (see the [catalog](./blueprints/catalog-reference.md)). SHA pinning and injection-safe scripting belong to `automating-github-repos-with-actions`.
> Provenance: the dated research file for this unit under the factory workspace; this skill never reads it at run time.

## Version Context

| Item | Value | Source (fetched 2026-10-30) |
|---|---|---|
| Reusable workflow limits | 10 connected levels, 50 unique reusable workflows per workflow file | https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations |
| Composite action nesting | up to 10 composite actions in one workflow | https://docs.github.com/en/actions/concepts/workflows-and-actions/reusing-workflow-configurations |
| Matrix | up to 256 jobs per run; a matrix job can call a reusable workflow | https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax |
| `actions/checkout` | v7.0.1 = `3d3c42e5aac5ba805825da76410c181273ba90b1` | https://github.com/actions/checkout/releases |
| `actions/setup-node` | v7.1.0 = `949feb2413d6458794dcd2491c4babbbce0c15c1` | https://github.com/actions/setup-node/releases |
| `actions/upload-artifact` | v7.0.2 = `cf430e030ddbb5b0abf93d22962f4752f3646cd9` | https://github.com/actions/upload-artifact/releases |
| `actions/download-artifact` | v8.0.2 = `9000827ccba6bdab643e8b6fd33ac0654aef8333` | https://github.com/actions/download-artifact/releases |

**Version-lifetime risk** (as of 2026-10-30; details in [register](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- Limits (50 workflows, matrix calls, `concurrency.queue`) changed recently; older guides and Enterprise Server pages state other numbers.
- Pinned action SHAs go stale; re-resolve them with `git ls-remote` before every bump.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Composite actions](./blueprints/composite-actions.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Monorepo with a ci-gate](./blueprints/monorepo-ci-gate.md)
- [Family block catalog](./blueprints/catalog-reference.md)
- [Plan variants: Pro/Team default and Free](./blueprints/plan-variants.md)
- [Central blocks repository option](./blueprints/central-blocks-repo.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [Verification Loop](#verification-loop)
- [External Resources](#external-resources)

## Blueprints & Guardrails

Model: three levels. **Callers** hold triggers and wiring (`ci-<app>.yml` on pull_request, `cd-<app>.yml` on merge or release, `ops-<task>.yml` on schedule or dispatch). **Reusable workflows** `_<domain>-<name>.yml` are whole stages with their own jobs. **Composite actions** `.github/actions/<domain>/<name>/action.yml` are repeated step sequences. Default location is the same repository with `./` paths (family decision); a [central repository](./blueprints/central-blocks-repo.md) is an option.

Contract of a block: typed `inputs`, explicit `outputs`, each secret by name, its own minimal `permissions`. Choosing the level: if the block needs its own runner, a secret, an environment or several jobs, use a reusable workflow; otherwise a composite action.

### ✅ Always Do

- **Place reusable workflows directly in `.github/workflows`**; subdirectories are not supported ([reuse workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows)).
- **Name reusable workflows `_<domain>-<name>.yml`** (family decision, not a GitHub feature); callers use `ci-`, `cd-`, `ops-`.
- **Give every workflow input a `type` of `boolean`, `number` or `string`** ([workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)).
- **Map each workflow output to a job output** with `value: ${{ jobs.<job>.outputs.<name> }}` ([workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)).
- **Pass secrets by name** under `secrets:` on the calling job ([reuse workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows)).
- **Set `permissions` on the calling job**; the called workflow can only keep or reduce them ([reference](https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations)).
- **Read results of a called workflow only through `needs.<job>.outputs`** ([reference](https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations)).
- **Pass values to a block only through `with:`**; the caller's `env` is not propagated ([reference](https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations)).
- **Set `shell` on every `run` step of a composite action** ([metadata syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/metadata-syntax)).
- **Pass secrets to a composite action as inputs**; the `secrets` context is unavailable there ([contexts](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts)).
- **Pass the environment name as a string input** ([reuse workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows)).
- **Set `environment:` on the deploying job inside the called workflow**, never on the calling job ([reuse workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows)).
- **Require only an `if: always()` aggregate job** that lists the other jobs in `needs` ([required checks](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/troubleshooting-required-status-checks)).
- **Set `timeout-minutes` on every job**; the default is 360 ([workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)).
- **Group PR CI by `github.head_ref || github.run_id`** with `cancel-in-progress: true` ([control concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)).
- **Call same-repository blocks with `./` paths** (family decision); they run at the caller's commit.

Code for each rule: [always-do patterns](./blueprints/always-do-patterns.md) and [composite actions](./blueprints/composite-actions.md).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Composite action or reusable workflow | Composite: shares the job, no secrets context, one log step. Reusable: own runner, secrets, environments, separate logs | "Does this block need its own runner, a secret, an environment or several jobs?" |
| Blocks in this repo or a central repo | Same repo (default): one PR, no ref bumps. Central: one source, but SHA bumps and access settings | "Must blocks be shared across repositories?" |
| Monorepo detection | Path filters per caller (cannot be required checks) vs one caller with change detection and `ci-gate` (default, medium confidence) | "Must per-app checks block merge?" |
| GitHub plan | Pro/Team private (default) vs Free private (weaker, no environments); see [plan variants](./blueprints/plan-variants.md) | "Which plan owns the repository?" |
| Deploy concurrency | `cancel-in-progress: false` per environment (medium confidence) vs `queue: max` when every pending deploy must run | "May a newer deploy replace a pending one?" |
| Dependabot scope | `directory: "/"` only vs `directories` globs over composite actions (scan behaviour unverified) | "Do composite actions use third-party actions?" |
| Built-in dependency cache | `setup-node` cache inputs (input names unverified) vs `actions/cache` (v6.1.0, SHA in [composite actions](./blueprints/composite-actions.md)) | "Is a cache wanted, and for which path?" |
| Block testing | Throwaway `ops-test-<block>.yml` with `workflow_dispatch` (medium confidence) | "Where may a test run happen?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Put a reusable workflow in a subfolder of `.github/workflows` ([reuse workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows)) | `_<domain>-<name>.yml` at the folder root |
| Use `secrets: inherit` toward a block ([reuse workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows)) | Named secrets per block |
| Rely on caller `env` or `GITHUB_ENV` across the call boundary ([reference](https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations)) | `with:` inputs and `needs` outputs |
| Put `environment:` on the job that calls a reusable workflow ([reuse workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows)) | `environment` string input, set inside the called workflow |
| Use `secrets.X` inside a composite action ([contexts](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts)) | An input the caller fills |
| Omit `shell` on a composite `run` step ([metadata syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/metadata-syntax)) | `shell: bash` |
| Require a check from a path-filtered workflow ([required checks](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/troubleshooting-required-status-checks)) | Job-level detection plus `ci-gate` |
| Raise permissions inside the called workflow ([reference](https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations)) | Grant on the calling job |
| Combine `paths` and `paths-ignore` on one event ([workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)) | `paths` with `!` negation |
| Cache credential files ([dependency caching](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching)) | Inject tokens at run time through inputs |

Examples with alternatives: [never-do patterns](./blueprints/never-do-patterns.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| Reusable workflow location | `.github/workflows`, no subfolders | https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows |
| Nesting and uniqueness | 10 levels; 50 unique reusable workflows per file | https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations |
| `secrets: inherit` reach | only the directly called workflow | https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations |
| Job outputs | 1 MB per job, 50 MB per run | https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations |
| Concurrency | one running plus one pending per group; `queue: max` up to 100, not with `cancel-in-progress: true` | https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax |
| Job timeout | default 360 minutes | https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax |
| `needs.<job>.result` values | success, failure, cancelled, skipped | https://docs.github.com/en/actions/reference/workflows-and-actions/contexts |
| Skipped required workflow | check stays Pending, merge blocked | https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/troubleshooting-required-status-checks |

## Verification Loop

Run from the repository root; each command states the expected result (representative, adapt to your shell).

```bash
find .github/workflows -mindepth 2 -name '*.yml'         # expect: no output (no subfolder workflows)
grep -L 'workflow_call' .github/workflows/_*.yml         # expect: no output (every _ file is reusable)
grep -rn 'secrets: inherit' .github/                     # expect: no output
grep -rn 'secrets\.' .github/actions/                    # expect: no output
grep -rn 'environment:' .github/workflows/ci-*.yml       # expect: no output on jobs that use a reusable workflow
grep -c 'timeout-minutes:' .github/workflows/*.yml       # expect: one per job that has runs-on
```

For composite actions, the count of `shell:` lines per `action.yml` must be at least its count of `run:` lines. Lint with actionlint when available (community tool, version not in the facts file) (unverified).

## External Resources

All fetched 2026-10-30.

- [Reuse workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows)
- [Reusing workflow configurations (reference)](https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations)
- [Metadata syntax for composite actions](https://docs.github.com/en/actions/reference/workflows-and-actions/metadata-syntax)
- [Full bibliography](./blueprints/unverified-and-risks.md#source-bibliography)
