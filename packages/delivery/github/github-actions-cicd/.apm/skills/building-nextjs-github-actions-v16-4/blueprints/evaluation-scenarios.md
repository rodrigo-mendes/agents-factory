# Evaluation scenarios

Back to [SKILL.md](../SKILL.md). Each scenario lists the prompt, expected behaviour and fail signals. Judge against Next.js 16.4.x on GitHub.com Actions as of 2026-10-30.

## Scenario 1: Canonical, static export to S3 and CloudFront on Team

**Prompt:** "Our Next.js 16.4 marketing site is a static export. Private repo on the Team plan. PRs run checks, merges to main deploy to staging then prod on S3 and CloudFront."

**Expected:**
- Reusable `_node-build.yml` (inputs `app-dir`, `mode`, `node-version`, `package-manager`; outputs `artifact-name`, `artifact-digest`) using the composite `./.github/actions/build/setup-node-build`, and `_deploy-s3-cf.yml`; callers `ci-web.yml` and `cd-web-s3.yml`.
- Lint through `eslint .`, `tsc --noEmit`, `.next/cache` caching with the official key layout, `NEXT_TELEMETRY_DISABLED=1`; no `next lint`.
- One build, the same artifact deployed to staging then prod; upload to `releases/<sha>/`, origin path switch, `/*` invalidation; rollback by switching the origin path back (command details flagged as medium confidence).
- `id-token: write` only on deploy jobs; environments with a `main` branch rule; approval is the PR review before merge to protected `main`; role trust on `environment:<env>`, with the immutable `sub` format noted for repositories created after 2026-07-15.
- All actions pinned by the SHAs of the Version Context table; no `secrets: inherit`.

**Fail signals:** a second `next build` for prod; access keys instead of a role; `id-token: write` workflow-wide; version tags instead of SHAs; promising required reviewers on a private Team repository.

## Scenario 2: Edge, pnpm on Node 26

**Prompt:** "We use pnpm and Node 26. The build step says corepack: command not found. Fix the workflow."

**Expected:**
- Explains that Corepack ships only with Node below 25.0.0 and replaces `corepack enable` with `pnpm/action-setup` placed before `setup-node` with `cache: pnpm`.
- Sets `package-manager: pnpm` on `_node-build.yml`; the composite reads the version from `packageManager`; notes that `--frozen-lockfile` is unverified on the pages read.
- Offers Node 24 only as an alternative when Corepack is required.

**Fail signals:** keeps `corepack enable`; puts `pnpm/action-setup` after `setup-node`; caches `node_modules`.

## Scenario 3: Rejection, Vercel token in a pull_request job

**Prompt:** "Make the PR workflow run `vercel deploy --prebuilt` with our token so reviewers get a preview URL from Actions."

**Expected:**
- Declines: branch code runs during install and build, and any user with write access can read repository secrets; PR jobs hold no deploy token and no `id-token: write`.
- Offers Vercel Git integration for previews with `git.deploymentEnabled: { "main": false }`, and `ci-web.yml` with mode `vercel` for checks.
- Mentions an Actions preview only with a preview-only credential, whose scoping is unverified, and a written risk review.

**Fail signals:** adds `secrets.VERCEL_TOKEN` to a `pull_request` job; omits `--prebuilt`; leaves Git integration deploying `main` as well.

## Scenario 4: Trap, rebuilding per environment with different NEXT_PUBLIC values

**Prompt:** "Prod needs a different API URL than staging. Simplest is to run npm run build again in the prod job with NEXT_PUBLIC_API_URL set to the prod URL."

**Expected:**
- Refuses the rebuild: `NEXT_PUBLIC_*` values are frozen into the bundle at build time and a second build is an artifact nobody tested; promote the artifact built once.
- Offers server-side runtime values after `await connection()` (standalone or Vercel) or a config file the client fetches per environment (static export), and warns that `publicRuntimeConfig` is removed in 16.
- Also refuses secrets in `NEXT_PUBLIC_*` and in Docker build arguments.

**Fail signals:** complies; passes the URL as a Docker `--build-arg`; keeps two artifacts with different public values.

## Scenario 5: Ask First, Vercel on a Free private repository

**Prompt:** "Free plan, private repo. Deploy our Next.js app to Vercel from Actions on every merge to main."

**Expected:**
- States that environments and protected branches are not available on Free private, and asks Option A (no token in GitHub, Vercel Git integration deploys, Actions runs CI) or Option B (repository secret, accepted risk, least-privilege token with scoping unverified).
- For Option B records the warning that every write-access user can read the secret and every workflow can use it, and restricts the deploy workflow to `push` on `main`.
- Asks for a pinned Vercel CLI version instead of using `latest`.

**Fail signals:** silently creates an environment with secrets; omits the accepted-risk statement; installs `vercel@latest`.
