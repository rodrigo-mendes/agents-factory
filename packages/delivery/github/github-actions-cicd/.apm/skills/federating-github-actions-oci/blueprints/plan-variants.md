# Plan variants: Pro/Team and Free

Back to [SKILL.md](../SKILL.md). Research date 2026-10-30. Family rule 16 sets the model; the executor asks which plan owns the repository before generating any CD workflow.

## Contents

- Default: Pro or Team private repository
- Weaker variant: Free private repository
- Upgrade path

## Default: Pro or Team private repository

Facts: environment secrets and deployment branch or tag policies work on private repos for Pro or Team; protected branches and required pull request reviewers are Pro and Team features; required reviewers, wait timers and custom protection rules are public-repo only.
Sources: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments and https://docs.github.com/en/get-started/learning-about-github/githubs-plans

| Piece | Setting |
|---|---|
| Environments | `<env>` (deploy) and `<env>-pr` (pull request), for example `dev`, `dev-pr`, `prod`, `prod-pr`, each with its own CI user's secrets |
| Variable | `OCI_CLI_REGION` (environment variable, not a secret) |
| Branch policy | `<env>` environments: selected branches and tags = `main` |
| Branch protection | `main` protected, pull request review required |
| Approval (family decision) | review of the rendered plan or diff in the PR before merge; the merge triggers the deploy |
| Path A trust rule | `sub eq repo:...:environment:prod` (format per [path A](./path-a-token-exchange.md)) |

Secrets per environment: `OCI_CLI_USER`, `OCI_CLI_TENANCY`, `OCI_CLI_FINGERPRINT`, `OCI_CLI_KEY_CONTENT`, `OCIR_AUTH_TOKEN` (only where images are pushed).

## Weaker variant: Free private repository

> Warning: weaker than the default and never silent. Free private repositories have no environments (environment secrets and creation need Pro or Team, "Users with GitHub Free plans can only configure environments for public repositories") and no protected branches or required PR reviewers (not listed for Free). Deployment protection rules for private repos are Enterprise.

Consequences the executor must state to the user:

- Every OCI credential is a repository secret, readable by any workflow on any branch that can edit workflows. Accepted risk, stated, not hidden.
- The static secrets are unavoidable even on Path A (the app client secret) and for OCIR (auth token). Keep each one a least-privilege repository secret.
- Separate dev and prod by distinct OCI users and compartments with distinct secret names (`OCI_DEV_*`, `OCI_PROD_*`), or by repository.
- Pull request jobs use only the read-only user's secrets (`OCI_PR_*`), never a deployable user's.
- Where Path A is chosen, the trust rule uses `sub eq repo:...:ref:refs/heads/main` instead of an environment subject (the ref form for repositories created after 2026-07-15 is the immutable format, unverified; see [path A](./path-a-token-exchange.md)).
- Approval has no enforcement point: nothing prevents a merge or workflow edit without review. Say so.

```yaml
# Free private variant: repository secrets, deploy only from main (representative)
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    permissions:
      contents: read
    env:
      OCI_CLI_USER: ${{ secrets.OCI_PROD_USER }}
      OCI_CLI_TENANCY: ${{ secrets.OCI_PROD_TENANCY }}
      OCI_CLI_FINGERPRINT: ${{ secrets.OCI_PROD_FINGERPRINT }}
      OCI_CLI_KEY_CONTENT: ${{ secrets.OCI_PROD_KEY_CONTENT }}
```

The `push` trigger on `main` limits when the job runs; it does not stop another branch's workflow from reading the same repository secrets.

## Upgrade path

Required reviewers, wait timers and artifact attestations are the upgrade path only: public repositories or Enterprise. Artifact attestations on private repos need GitHub Enterprise Cloud.
