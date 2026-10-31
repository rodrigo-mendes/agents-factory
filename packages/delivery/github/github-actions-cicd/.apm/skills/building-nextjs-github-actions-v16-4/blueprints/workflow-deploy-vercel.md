# Vercel prebuilt deploy

Back to [SKILL.md](../SKILL.md). Vercel CLI build output deployed with `--prebuilt`; research date 2026-10-30. Commands are representative, adapt to your environment. CLI and token handling details are owned by `vercel-cli-with-tokens`.

Contents: [Project settings](#project-settings) | [Reusable deploy](#reusable-workflow-githubworkflows_deploy-vercelyml) | [Plan variants](#plan-variants) | [Notes](#notes)

## Project settings

`vercel.json` stops the Git integration from also deploying `main`; it keeps building previews for other branches, so no Vercel token is ever exposed to pull-request code.

```json
{ "$schema": "https://openapi.vercel.sh/vercel.json", "git": { "deploymentEnabled": { "main": false } } }
```

`git.deploymentEnabled` accepts a Boolean or an object of branch patterns. The default is `true`, and a branch that matches several rules deploys if any rule is `true`.

## Reusable workflow `./.github/workflows/_deploy-vercel.yml`

Pull, build and deploy share one job because all three read `.vercel/`. This job does not lint or test: those checks run in `_node-build.yml` (mode `vercel`), called first by the caller.

```yaml
# Representative — adapt to your environment
name: _deploy-vercel
on:
  workflow_call:
    inputs:
      environment:        { type: string, default: "", description: "prod; empty on Free Option B (no environment)" }
      node-version:       { type: string, default: "24" }
      vercel-cli-version: { type: string, required: true, description: "Pinned Vercel CLI version, no default" }
      app-dir:            { type: string, default: "." }
    outputs:
      deployment-url:
        description: URL printed by vercel deploy
        value: ${{ jobs.deploy.outputs.deployment-url }}
    secrets:
      VERCEL_TOKEN:      { required: false }
      VERCEL_ORG_ID:     { required: false }
      VERCEL_PROJECT_ID: { required: false }
permissions:
  contents: read
jobs:
  deploy:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    environment: ${{ inputs.environment }}      # empty string = no environment (Option B on Free)
    concurrency: { group: "deploy-vercel-${{ inputs.environment || 'prod' }}", cancel-in-progress: false }
    outputs:
      deployment-url: ${{ steps.deploy.outputs.url }}
    env:
      VERCEL_CLI_VERSION: ${{ inputs.vercel-cli-version }}
      NEXT_TELEMETRY_DISABLED: "1"
    defaults:
      run:
        working-directory: ${{ inputs.app-dir }}
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: actions/setup-node@949feb2413d6458794dcd2491c4babbbce0c15c1 # v7.1.0
        with:
          node-version: ${{ inputs.node-version }}
          package-manager-cache: false        # credentials in this job
      - run: npm install --global "vercel@${VERCEL_CLI_VERSION}"
      # The credentials are in env: of these three steps only, not of the job; the CLI reads VERCEL_TOKEN itself
      - run: vercel pull --yes --environment=production
        env:
          VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
          VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
          VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}
      - run: vercel build --prod
        env:
          VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
          VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
          VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}
      - id: deploy
        run: echo "url=$(vercel deploy --prebuilt --prod)" >> "$GITHUB_OUTPUT"
        env:
          VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
          VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
          VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}
```

`vercel build --prod` uses Production environment variables (Preview is the default), and `vercel deploy --prebuilt` deploys the output of a previous build in `.vercel/output`. `stdout` of `vercel deploy` is always the deployment URL. For custom environments use `--target=<env>` on all three commands. System environment variables are missing at build time with `--prebuilt`.

Whether a job's own environment secrets resolve inside a reusable workflow, without being passed by the caller, is unverified. The declared `secrets:` cover the Free variant (repository secrets passed by the caller); on Pro/Team, if environment secrets do not resolve, inline the job in `cd-web-vercel.yml`.

## Plan variants

| Item | Pro / Team private (default) | Free private (weaker, accepted risk) |
|---|---|---|
| `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID` | Environment secrets on `prod`, limited to `main` by the deployment branch rule | Option A: none in GitHub; Vercel Git integration deploys and Actions runs CI only. Option B: repository secrets |
| Approval | PR review before merge to protected `main` | None enforceable: protected branches are not listed for Free private |
| Residual risk | Secrets stay in the environment and are released only to jobs on `main` | Option B: every user with write access can read the secret and every workflow on every branch can use it |
| Mitigation | Token scoping (unverified), owned by `vercel-cli-with-tokens` | Least-privilege token (scoping unverified), deploy workflow triggered only by `push` to `main`, written risk acceptance |
| Upgrade path | Required reviewers on `prod` (public repo or Enterprise) | Move to Pro/Team |

Option A on Free removes `_deploy-vercel.yml` from the repository entirely; delete `git.deploymentEnabled` then, or Vercel will not deploy `main`.

## Notes

- Ask which plan applies before choosing Option A or B, and record the accepted risk in the repository README when B is chosen. For Option B the caller leaves `environment` empty (an empty `environment:` value being accepted is unverified, see U8); otherwise drop the `environment:` line in an inlined job.
- No Vercel CLI version is pinned by this skill (unverified): `vercel-cli-version` has no default so a missing value fails the call instead of installing `latest`.
- Splitting `vercel build` and `vercel deploy --prebuilt` across jobs with an artifact of `.vercel/output` was not shown in an official example (medium confidence).
- Promoting an existing preview build instead of rebuilding (`vercel promote`) belongs to `vercel-cli-with-tokens`.
- Preview deployments from Actions put the token in a job that runs branch code; keep them on Vercel Git integration unless a preview-only credential exists.
- Docs examples show older action majors; only the pins from the Version Context table are used.
