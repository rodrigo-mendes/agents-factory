# Evaluation scenarios

Back to [SKILL.md](../SKILL.md). Each scenario lists the prompt, expected behaviour and fail signals. Judge against GitHub.com Actions docs as of 2026-10-30.

## Scenario 1: Canonical, monorepo with a ci-gate

**Prompt:** "We have apps/web (Next.js) and services/api (Java) in one private repo on the Team plan. I want replaceable blocks and PR checks that must pass before merge, but I do not want to run everything for every change."

**Expected:**
- Blocks in the same repository: `_node-build.yml` and `_java-build.yml` at the workflows folder root, a composite `./.github/actions/repo/changes`, caller `ci-monorepo.yml` without path filters.
- A `changes` job, per-app jobs with `if:` on its outputs, and an `if: always()` `ci-gate` job that accepts only success or skipped; only `ci-gate` is the required check.
- Typed inputs, explicit outputs, named secrets, `permissions` on the calling jobs, `timeout-minutes` on every job, PR concurrency group with `cancel-in-progress: true`.
- Action pins are the facts-file SHAs with tag comments; the PR workflow does not deploy.

**Fail signals:** path filters on the required workflow; several required checks per app; `secrets: inherit`; version tags instead of SHAs; a missing `always()` on the gate.

## Scenario 2: Edge, central blocks repository pinned by SHA

**Prompt:** "Twelve repositories in our organization should use the same _node-build workflow. Put it in a central repo called ci-blocks."

**Expected:**
- Keeps same-repository blocks as the default and explains the central option as a choice; asks whether sharing across repositories is really required.
- Uses `my-org/ci-blocks/.github/workflows/_node-build.yml@<full SHA>` with a tag comment, explains the safest ref is the commit SHA, and gives versioning guidance (tags, new file name for breaking input changes, coordinated bumps).
- Mentions the private repository access setting for the organization and that outside collaborators may indirectly see logs; says the personal-account equivalent was not found.
- Keeps named secrets even inside one organization.

**Fail signals:** branch name as ref without comment; no pin; claims Dependabot behaviour for composites as fact; `secrets: inherit` as the default.

## Scenario 3: Rejection, `secrets: inherit` across repositories

**Prompt:** "Just use secrets: inherit when calling the shared workflow from the other repos, so I do not have to list the secrets."

**Expected:**
- Declines: `secrets: inherit` works only inside the same organization or enterprise, reaches only the directly called workflow, and hides what a block needs.
- Offers named secrets under `secrets:` on the calling job and a declared `secrets:` section in the block.
- Offers a short script or table to list the secrets once if the number is the real concern.

**Fail signals:** complies; passes inherit to a nested chain and says it works at every level; stores deploy credentials as repository secrets to avoid the list.

## Scenario 4: Trap, `environment:` on the calling job and path filter on a required workflow

**Prompt:** "In cd-web.yml, put environment: prod on the job that uses _deploy-s3-cf.yml so the secrets work. And restrict ci-web.yml with paths: apps/web/** and make it a required check."

**Expected:**
- Rejects `environment:` on the calling job (a job that calls a reusable workflow cannot use it) and moves it to a string input read by the deploying job inside the block.
- Rejects the required path-filtered workflow: skipped means Pending and merges block; proposes job-level detection with one `ci-gate`.
- Asks the GitHub plan; states that Free private repositories have no environments and points to the Free variant with its risks, and that required reviewers on environments are not available on Pro/Team private repositories.

**Fail signals:** accepts either request; says the Pending check clears itself; promises required reviewers on a private Team repository.

## Scenario 5: Ask First, composite action or reusable workflow

**Prompt:** "I need to install Node and run npm ci in five workflows, and one of them also needs an NPM token. Should this be a composite action or a reusable workflow?"

**Expected:**
- Asks whether the block needs its own runner, a secret, an environment or several jobs; recommends a composite action for the repeated step sequence.
- Passes the token as an input because the secrets context is unavailable in composite actions, and sets `shell` on every `run` step.

**Fail signals:** reads `secrets.NPM_READ_TOKEN` inside `action.yml`; omits `shell`; uses the `INPUT_` environment variables.
