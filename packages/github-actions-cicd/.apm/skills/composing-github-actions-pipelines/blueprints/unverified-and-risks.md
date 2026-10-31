# Unverified and risks register

Back to [SKILL.md](../SKILL.md). Research date 2026-10-30. Tags are plain parentheses: (unverified) and (medium confidence).

Contents: [Version-lifetime risk](#version-lifetime-risk) | [Unverified](#unverified-6) | [Irresolvable](#irresolvable-3) | [Medium confidence](#medium-confidence-5) | [Coverage limits](#coverage-limits-4) | [Tag mapping](#tag-to-register-mapping) | [Bibliography](#source-bibliography)

## Version-lifetime risk

As of 2026-10-30.

- Limits changed recently: 50 unique reusable workflows per file (older Enterprise Server pages say 20) and matrix jobs may call reusable workflows (older pages say not supported). Re-read the reuse pages before relying on a number. Source: https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations
- `concurrency.queue` (`single` default, `max` up to 100 pending) is new; `queue: max` with `cancel-in-progress: true` is a validation error. Source: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
- A `$/` self-repository reference exists next to `./` (not on Enterprise Server); this skill keeps `./` in examples. Source: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
- Pinned SHAs (checkout v7.0.1, setup-node v7.1.0, upload-artifact v7.0.2, download-artifact v8.0.2, cache v6.1.0) were resolved on 2026-10-30; re-run `git ls-remote` before bumping. Source: https://github.com/actions/upload-artifact/releases
- Artifacts are immutable from upload-artifact v4: re-uploading a name needs a new name. Source: https://docs.github.com/en/actions/tutorials/store-and-share-data
- OIDC subject format changed for repositories created after 2026-07-15 (immutable default). Source: https://docs.github.com/en/actions/reference/security/oidc

## Unverified (6)

| ID | Claim | Impact | Workaround |
|---|---|---|---|
| U1 | `setup-node` cache input names (`cache`, `cache-dependency-path`) | a cache step with a wrong input name | read the action README at the pinned SHA before adding it |
| U2 | `actions/checkout` input `fetch-depth` | the diff in the `changes` job lacks the base commit | read the README at the pinned SHA; fetch the base commit explicitly if needed |
| U3 | actionlint as a lint step; version not in the facts file | no automated workflow lint | run only the grep checks of the Verification Loop |
| U4 | An empty `environment:` expression is accepted on the Free variant | the deploy job fails to start | use a block copy without the `environment` key |
| U5 | How `./` paths inside a centrally hosted block resolve to composite actions | the shared block cannot find its composites | keep composites in the caller repository or test one block end to end |
| U6 | The exact immutable `sub` string for an `environment:` claim | a cloud trust policy that never matches | read the real `sub` from a token of a test run; the documented immutable example uses `ref:` |

## Irresolvable (3)

| ID | Claim | Note |
|---|---|---|
| I1 | Official status-check context name for jobs in a called reusable workflow | only community sources report `<caller job> / <called job>`; require only `ci-gate` |
| I2 | Dependabot scans composite actions under `.github/actions/<domain>/<name>` through `directories` globs | not stated on three official pages; list the directories and confirm on the first Dependabot run |
| I3 | Access setting wording for a personal Pro account's private blocks repository | the organization wording was found, the user-account one was not |

## Medium confidence (5)

| ID | Claim | Why medium | Check |
|---|---|---|---|
| M1 | Job-level change detection plus an `always()` gate is the right monorepo design | each part documented; the combination is composed from official pieces | open a PR that touches one app only and confirm the merge button enables |
| M2 | Deploy concurrency should use `cancel-in-progress: false` | semantics documented; the policy is design inference | two quick merges to the same environment |
| M3 | Dependabot updates remote reusable-workflow references on `jobs.<id>.uses` | the page speaks of reusable workflows in general | run Dependabot once on a pinned reference |
| M4 | An environment secret the caller does not supply resolves to an empty string unless declared `required: true` | summarised wording of the how-to page | test a deploy with the secret missing |
| M5 | A throwaway `ops-test-<block>.yml` with `workflow_dispatch` is the way to test a block | no official local runner was found; design inference | run it on a branch |

## Coverage limits (4)

| ID | Limit |
|---|---|
| L1 | Pages were read through a fetch tool that returns a summarised extraction; quoted strings are the tool's extracts |
| L2 | GitHub docs examples show older action majors; this skill uses only the pinned versions of the family facts |
| L3 | The GitHub plan of the user is unknown; Free versus Pro/Team limits were read on the deployments and plans pages |
| L4 | Enterprise Server pages were rejected as a different version and used for no claim |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| unverified (prose form) | SKILL.md Ask First (built-in dependency cache) | U1 |
| (unverified) | composite-actions.md setup-node cache note | U1 |
| (unverified) | monorepo-ci-gate.md checkout `fetch-depth` note | U2 |
| (unverified) | SKILL.md Verification Loop (actionlint) | U3 |
| (unverified) | plan-variants.md Free variant (empty environment) | U4 |
| (unverified) | central-blocks-repo.md versioning item 4 | U5 |
| (unverified) | plan-variants.md Default section (`sub` for environments) | U6 |
| unverified (prose form) | monorepo-ci-gate.md check names; SKILL.md Ask First (Dependabot scope) | I1, I2 |
| (unverified) | central-blocks-repo.md access section (personal account) | I3 |
| (medium confidence) | SKILL.md Ask First (monorepo detection); monorepo-ci-gate.md intro | M1 |
| (medium confidence) | SKILL.md Ask First (deploy concurrency); always-do-patterns.md A5 | M2 |
| (medium confidence) | central-blocks-repo.md versioning item 3 | M3 |
| (medium confidence) | always-do-patterns.md A4 | M4 |
| (medium confidence) | SKILL.md Ask First (block testing) | M5 |

## Source Bibliography

All fetched 2026-10-30 (GitHub.com docs; Enterprise Server pages rejected).

**docs.github.com**
- https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations
- https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows
- https://docs.github.com/en/actions/concepts/workflows-and-actions/reusing-workflow-configurations
- https://docs.github.com/en/actions/reference/workflows-and-actions/metadata-syntax
- https://docs.github.com/en/actions/creating-actions/creating-a-composite-action
- https://docs.github.com/en/actions/how-tos/reuse-automations/share-with-your-organization
- https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
- https://docs.github.com/en/actions/reference/workflows-and-actions/contexts
- https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/run-job-variations
- https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching
- https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency
- https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments
- https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments
- https://docs.github.com/en/actions/tutorials/store-and-share-data
- https://docs.github.com/en/actions/reference/security/oidc
- https://docs.github.com/en/get-started/learning-about-github/githubs-plans
- https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/troubleshooting-required-status-checks
- https://docs.github.com/en/code-security/dependabot/working-with-dependabot/keeping-your-actions-up-to-date-with-dependabot
- https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference
- https://docs.github.com/en/code-security/dependabot/ecosystems-supported-by-dependabot/supported-ecosystems-and-repositories

**Repositories and releases**
- https://github.com/actions/checkout/releases
- https://github.com/actions/setup-node/releases
- https://github.com/actions/upload-artifact/releases
- https://github.com/actions/download-artifact/releases
- https://github.com/actions/cache/releases
- SHA verification: `git ls-remote https://github.com/<owner>/<repo> refs/tags/<tag>`

**Community (classification only, not used for any Always Do or Never Do claim)**
- Community posts and pull requests that report the status-check name format of called workflows; not linked because they are not evidence.
