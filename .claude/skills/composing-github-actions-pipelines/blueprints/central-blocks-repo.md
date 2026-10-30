# Central blocks repository option

Back to [SKILL.md](../SKILL.md). GitHub.com docs as of 2026-10-30. Default is the same repository with `./` paths; use this option only when many repositories of one organization share blocks.

## Syntax and pinning

```yaml
jobs:
  build:
    uses: my-org/ci-blocks/.github/workflows/_node-build.yml@0123456789abcdef0123456789abcdef01234567
    permissions:
      contents: read
    with:
      app-dir: apps/web
      mode: static
```

- The reference form is `{owner}/{repo}/.github/workflows/{filename}@{ref}`; `{ref}` can be a SHA, a release tag or a branch name. The commit SHA is the safest option for stability and security (https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows).
- Pin by full 40-character commit SHA with the tag in a comment; the SHA above is an illustrative placeholder, resolve the real one with `git ls-remote`.
- A private caller can use blocks from private and public repositories; a public caller only from public ones. GitHub does not redirect renamed actions or reusable workflows.
- A re-run of failed jobs uses the reusable workflow from the commit SHA of the first attempt.
- `secrets: inherit` works only within the same organization or enterprise and still only for the directly called workflow; keep named secrets.

## Versioning guidance (family decision)

1. Release the blocks repository with tags; consumers pin the SHA of a tag.
2. A breaking change to an input, output or secret name gets a new tag and a new block file name (`_node-build-2.yml`) or a coordinated bump in every consumer.
3. Dependabot ignores local references but updates `owner/repo@<commit>` references; it updates a version comment only when the comment is on the same line (https://docs.github.com/en/code-security/dependabot/working-with-dependabot/keeping-your-actions-up-to-date-with-dependabot). That Dependabot also updates remote reusable-workflow references on `jobs.<id>.uses` is stated in general terms only (medium confidence).
4. How a `./` path inside a centrally hosted block resolves to composite actions was not confirmed on a page read for this unit (unverified); keep composite actions the block needs in the caller repository or test one block end to end before sharing it.

## Access

For a private blocks repository, its Actions access setting must allow repositories of the organization ("Accessible from repositories in the 'ORGANIZATION-NAME' organization"). Outside collaborators of caller repositories can then indirectly view workflow logs of the private repository. The equivalent setting for a personal account's private repository was not found (unverified).

Source: https://docs.github.com/en/actions/how-tos/reuse-automations/share-with-your-organization

## Tradeoffs

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| Same repository (default) | Block and caller change in one PR, run at one commit, no access settings | Duplication across repositories | One repository or monorepo |
| Central repository | One source for many repositories | SHA bumps, access settings, log visibility | Many repositories in one organization |

Ask: "Must blocks be shared across repositories?" Default to the same repository.
