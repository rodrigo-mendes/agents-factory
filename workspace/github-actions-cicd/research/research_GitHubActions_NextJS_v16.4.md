# Research: Next.js 16.4 CI/CD on GitHub Actions (actions/setup-node v7.1.0): Vercel, S3 + CloudFront static export, standalone container

> Unit: `building-nextjs-github-actions-v16-4`. Source item: "Next.js: Vercel, S3+CloudFront, container, CI only".
> Spec: `researching-technical-frameworks` (default depth = exhaustive, MAX_ITERATIONS = 5). Brief:
> `workspace/github-actions-cicd/execution-1/briefs/P4-research-building-nextjs-github-actions-v16-4.md`.
> Every page was read on 2026-10-30 by this researcher. No agents or investigators were spawned and
> plan mode was not entered: the scope approval is the G1/G2 relay quoted in the brief (a relay, not a
> new approval). Family facts F1-F24 and family rules 1-16 are applied as given.
>
> Section-order note: the brief requires the file to END with `## Source Bibliography`, so that
> section moves from its template position to the end, after `## Pages read`. All 15 template
> sections are present. A `## Facts requested` section is added before `## Pages read`.
>
> Version note: nextjs.org pages carry a `lastUpdated` date in their front matter and describe the
> current major (16.x, current stable 16.4.3 per F15); that date is recorded per claim. docs.github.com
> and AWS pages carry no version or publish date; the read date is recorded. Vercel pages carry a
> `last_updated` date. Action facts come only from release pages or `_family_facts.md`, never from
> documentation examples (brief lesson 1).
>
> Tool note: pages were fetched with WebFetch, which returns a model-processed rendering. Where the
> rendering refused to return a page verbatim (quote limit), only the parts it quoted are used as
> evidence; those pages are marked "summarised" in `## Pages read`.

## Metadata

```yaml
Full_Name: Next.js 16.4 build, check and deploy pipelines on GitHub Actions
Target_Version: Next.js 16.4.x (latest stable 16.4.3, F15); actions/setup-node v7.1.0 = 949feb2413d6458794dcd2491c4babbbce0c15c1 (F6)
Node_Runtime: Node.js LTS lines 26 / 24 / 22 (F14); Next.js 16 minimum Node.js 20.9.0
Release_Date: Next.js 16.4.0 on 07 Oct (year not on page; 2026 by order); 16.4.3 on 23 Oct (F15); setup-node v7.1.0 on 08 Oct
Support_Status: Next.js 16.4.3 is the latest stable (F15); setup-node v7.1.0 is the newest release on its releases page
Primary_Docs:
  - https://nextjs.org/docs/app/guides/upgrading/version-16          # lastUpdated 2026-10-15
  - https://nextjs.org/docs/app/guides/ci-build-caching              # lastUpdated 2025-04-22
  - https://nextjs.org/docs/app/guides/static-exports                # lastUpdated 2026-08-09
  - https://nextjs.org/docs/app/api-reference/config/next-config-js/output   # lastUpdated 2026-09-18
  - https://nextjs.org/docs/app/guides/environment-variables         # lastUpdated 2026-08-25
  - https://vercel.com/kb/guide/how-can-i-use-github-actions-with-vercel     # last updated 2026-10-16
Official_Repos:
  - https://github.com/vercel/next.js
  - https://github.com/actions/setup-node
Integration_Partners: Vercel CLI (build/deploy --prebuilt), AWS S3 + CloudFront via aws-actions/configure-aws-credentials v6.3.0 (F3), Docker standalone image (hand-off), pnpm/action-setup (Facts requested), actions/cache (Facts requested)
Target_Plan: GitHub Team / Pro / Free with PRIVATE repositories (family rule 16, G2 DEC-011)
Research_Date: 2026-10-30
Domain_Complexity: Complex (three deploy targets, credentials, build-time env inlining)
Research_Depth: exhaustive (default)
Max_Iterations: 5
Gap_Loop_Ran: true
Iterations_Used: 3 of 5
Triangulated_Count: 8
Unverified_Count: 9
Irresolvable_Count: 0
Research_Quality_Score: 87%   # ~70 claims, 9 unverified
```

## Executive Summary

Next.js 16.4 is the current stable line of the React framework (16.4.3, F15). A CI pipeline for it on
GitHub Actions installs Node.js with `actions/setup-node` v7.1.0 (F6), installs dependencies, lints,
type-checks, tests and runs `next build`, persisting `.next/cache` between runs. The deploy then takes
one of three shapes: (1) a static export (`output: 'export'`, output folder `out`) synced to S3 and served
by CloudFront after an OIDC login to AWS; (2) a `standalone` output (`.next/standalone` plus a minimal
`server.js`) packaged into a container image; (3) a Vercel deployment built in Actions with
`vercel build` and uploaded with `vercel deploy --prebuilt`.

What changed for the target versions. Next.js 16 removed the `next lint` command and `next build` no
longer runs linting, so CI must call the ESLint CLI (or Biome) itself. Turbopack is the default bundler
for `next build`; a custom `webpack` config makes the build fail unless `--webpack` or `--turbopack` is
passed. Minimum Node.js is 20.9.0. `serverRuntimeConfig` and `publicRuntimeConfig` are removed. Since
16.3.0 the Turbopack filesystem cache is on by default for builds and lives in `.next/cache/turbopack`, so
caching `.next/cache` now speeds up the bundler itself. 16.4.0 added ESLint 10 support in
`eslint-config-next`. On the action side, setup-node v5 moved to the node24 runtime and enabled
automatic caching; v6 limited automatic caching to npm (when `package.json` declares npm in
`packageManager`); v7 migrated to ESM and removed the dummy `NODE_AUTH_TOKEN` fallback.

Three critical patterns. (a) Lint and type-check explicitly. `next lint` no longer exists, and
`next build` fails on type errors but does not lint. (b) Build once and promote. `NEXT_PUBLIC_*` values
are inlined into the browser bundle at `next build` time, so the artifact that reaches production must
be built with environment-agnostic public values. Per-environment values must come from server runtime
env (container) or a runtime config the client fetches. Rebuilding for production is forbidden (family
rule 8). (c) Keep deploy credentials out of pull-request jobs. The Vercel token and the AWS deploy role
belong only to jobs on the protected branch, scoped by environment on Pro/Team. On Free private repos
there are no environment secrets: the AWS role uses OIDC trust on `ref:refs/heads/main` (no stored
secret), and the Vercel token is either a repository secret with accepted residual risk or kept out of
GitHub entirely by letting Vercel's Git integration deploy.

## Architectural Guardrails

### ✅ Mandatory Patterns

**A1. Pin `actions/setup-node` v7.1.0 by SHA and choose a Node LTS line at or above Next.js 16's minimum**
> Confidence: High [✓✓ Triangulated | setup-node releases + action.yml v7.1.0 + Next.js 16 upgrade guide]
- Why: v7.1.0 is the newest release (08 Oct). Its `action.yml` declares `runs.using: node24`, inputs `node-version`, `node-version-file`, `check-latest` (default `false`), `cache` (npm, yarn, pnpm), `package-manager-cache` (default `true`), `cache-dependency-path`, and outputs `cache-hit`, `cache-primary-key`, `cache-matched-key`, `node-version`. Next.js 16 requires "Node.js 20.9+ ... Node.js 18 no longer supported". Use an F14 LTS line (26, 24 or 22).
- Code:
  ```yaml
  - uses: actions/setup-node@949feb2413d6458794dcd2491c4babbbce0c15c1 # v7.1.0
    with:
      node-version: 24        # an F14 LTS line; Next.js 16 needs >= 20.9.0
      cache: npm              # explicit; see A2
  ```
- Source: https://github.com/actions/setup-node/releases (2026-10-30); https://raw.githubusercontent.com/actions/setup-node/v7.1.0/action.yml (2026-10-30); https://nextjs.org/docs/app/guides/upgrading/version-16 (lastUpdated 2026-10-15, read 2026-10-30)

**A2. Set the `cache` input explicitly in unprivileged jobs and turn automatic caching off in privileged jobs**
> Confidence: High [✓✓ Triangulated | setup-node README v7.1.0 + advanced-usage v7.1.0]
- Why: automatic npm caching runs when `package.json` has `packageManager` set to npm and no `cache` input is given ("This behavior is controlled by the `package-manager-cache` input, which defaults to `true`"). The README warns: "For workflows with elevated privileges or access to sensitive information, we recommend disabling automatic caching for npm." advanced-usage adds that "a poisoned cache may expose credentials (including OIDC tokens) to attacker-controlled code." Yarn and pnpm caching is off unless `cache` is set, and "The action does not cache `node_modules`."
- Code: privileged job (holds a deploy secret or `id-token: write`) that must still install packages:
  ```yaml
  - uses: actions/setup-node@949feb2413d6458794dcd2491c4babbbce0c15c1 # v7.1.0
    with:
      node-version: 24
      package-manager-cache: false   # no cache restore next to credentials
  ```
- Better: deploy jobs do not install packages at all; they download the built artifact (A7).
- Source: https://raw.githubusercontent.com/actions/setup-node/v7.1.0/README.md (2026-10-30); https://raw.githubusercontent.com/actions/setup-node/v7.1.0/docs/advanced-usage.md (2026-10-30)

**A3. Lint with the ESLint CLI (or Biome); never rely on `next build` or `next lint`**
> Confidence: High [✓✓ Triangulated | Next.js 16 upgrade guide + ESLint plugin reference]
- Why: "The `next lint` command has been removed. Use Biome or ESLint directly. `next build` no longer runs linting." The ESLint reference shows the flat config `eslint.config.mjs` with `eslint-config-next/core-web-vitals` and the run command `npx eslint .` (`pnpm exec eslint .`, `yarn eslint .`). `eslint-config-next` supports ESLint 9 and 10; ESLint 10 needs Node `^20.19.0`, `^22.13.0` or `>=24`. Codemod: `npx @next/codemod@canary next-lint-to-eslint-cli .`. The upgrade checklist states "Scripts and CI no longer invoke `next lint`".
- Code: `package.json` `"lint": "eslint ."`, then in CI `- run: npm run lint`.
- Source: https://nextjs.org/docs/app/guides/upgrading/version-16 (lastUpdated 2026-10-15); https://nextjs.org/docs/app/api-reference/config/eslint (lastUpdated 2026-10-15); read 2026-10-30

**A4. Type-check as its own step before `next build`; keep the build's type check on**
> Confidence: High (build fails on type errors; `tsc --noEmit` in CI) / (medium confidence) (running `next typegen` first)
- Why: "Next.js fails your production build (`next build`) when TypeScript errors are present." The docs add: "You can run `tsc --noEmit` to check for TypeScript errors yourself before building. This is useful for CI/CD pipelines." `next-env.d.ts` is generated, should be in `.gitignore`, must be in `tsconfig.json` `include`, and is regenerated by `next dev`, `next build` or `next typegen`. A fresh CI checkout therefore lacks it until `next typegen` runs. Running `next typegen` before `tsc` is an inference from those statements (medium confidence).
- Code:
  ```yaml
  - run: npx next typegen      # generates next-env.d.ts and route type helpers
  - run: npx tsc --noEmit
  ```
- Source: https://nextjs.org/docs/app/api-reference/config/typescript (lastUpdated 2026-08-25, read 2026-10-30)

**A5. Persist `.next/cache` between CI runs, keyed on the lockfile and source hashes**
> Confidence: High [✓✓ Triangulated | CI build caching guide + turbopackFileSystemCache reference]
- Why: "Next.js saves a cache to `.next/cache` that is shared between builds." Without persistence CI shows the "No Cache Detected" message. Since v16.3.0 the Turbopack build cache is on by default in `.next/cache/turbopack`, and "Builds only get faster when that directory is restored before each build." The official GitHub Actions example keys on `hashFiles('**/package-lock.json')` plus source globs, with a lockfile-only `restore-keys` fallback. The guide's example pins `actions/cache@v4`. That major is not used here (lesson 1); the release-page version is Facts request FR-1.
- Code: the key layout is copied from the guide; the action pin waits for FR-1.
  ```yaml
  - uses: actions/cache@<FR-1 SHA> # v6.1.0 (pending _family_facts row, see Facts requested)
    with:
      path: ${{ github.workspace }}/.next/cache
      key: ${{ runner.os }}-nextjs-${{ hashFiles('**/package-lock.json') }}-${{ hashFiles('**/*.js', '**/*.jsx', '**/*.ts', '**/*.tsx') }}
      restore-keys: |
        ${{ runner.os }}-nextjs-${{ hashFiles('**/package-lock.json') }}-
  ```
- If the build environment never preserves the cache: set `experimental.turbopackFileSystemCacheForBuild: false` ("to skip writing a cache that will not be read").
- Source: https://nextjs.org/docs/app/guides/ci-build-caching (lastUpdated 2025-04-22; older than 12 months but it is the current page for the current stable, kept); https://nextjs.org/docs/app/api-reference/config/next-config-js/turbopackFileSystemCache (lastUpdated 2026-10-06); read 2026-10-30

**A6. Treat `NEXT_PUBLIC_*` as build-time constants: keep public values environment-agnostic in the promoted artifact**
> Confidence: High [✓✓ Triangulated | environment-variables guide + Next.js 16 upgrade guide (runtime config removal)]
- Why: Next.js inlines `NEXT_PUBLIC_` values "at build time, into the js bundle". "If you ... build and deploy a single Docker image to multiple environments, all `NEXT_PUBLIC_` variables will be frozen with the value evaluated at build time." For per-environment values, "you'll have to set up your own API to provide them to the client". Server code can read env at runtime after `await connection()`, and the docs say "This allows you to use a singular Docker image that can be promoted through multiple environments with different values." `publicRuntimeConfig` is removed in 16. Together with family rule 8: the promoted artifact contains no environment-specific `NEXT_PUBLIC_` value.
- Code:
  ```tsx
  // Next.js 16.4 server component: value read at request time in each environment
  import { connection } from 'next/server'
  export default async function Page() {
    await connection()
    return <p>{process.env.API_BASE_URL}</p>
  }
  ```
- Source: https://nextjs.org/docs/app/guides/environment-variables (lastUpdated 2026-08-25); https://nextjs.org/docs/app/guides/upgrading/version-16 (lastUpdated 2026-10-15); read 2026-10-30

**A7. Build once in a job without deploy credentials, upload the output as an artifact, deploy by downloading the same artifact**
> Confidence: High (artifact actions F23/F24, family rule 8) | single official source for the Vercel variant (Vercel guide: "Build once in Actions, deploy the artifact to Vercel")
- Why: family rule 8. The output per target is `out/` (static export), `.next/standalone` + `.next/static` + `public` (standalone), or `.vercel/output` (Vercel `vercel build`, consumed by `vercel deploy --prebuilt`). Default artifact retention is 90 days, so set `retention-days` (F23).
- Code: see Implementation Blueprint `_nextjs-build.yml`.
- Source: `_family_facts.md` F23, F24; https://vercel.com/docs/cli/build (last_updated 2026-10-07); https://vercel.com/kb/guide/how-can-i-use-github-actions-with-vercel (last updated 2026-10-16); read 2026-10-30

**A8. Static export to S3: log in with OIDC only in the deploy job and upload into an immutable versioned prefix**
> Confidence: High (OIDC, F3; `aws s3 sync` behaviour; CloudFront origin path) | design default from the brief
- Why: family rule 9 (keyless AWS). `aws s3 sync` "Recursively copies new and updated files from the source directory to the destination"; `--delete` removes destination files absent from the source. A CloudFront origin path makes CloudFront "request your content from a directory in your origin" (format `/production`, no trailing slash). AWS recommends versioning over invalidation for frequent updates because it "simplifies rolling forward and back between file revisions". Each release goes to `releases/<git-sha>/`, and promotion or rollback points the origin path at a prefix.
- Code:
  ```yaml
  permissions:
    contents: read
    id-token: write          # this job only (family rule 7)
  steps:
    - uses: aws-actions/configure-aws-credentials@e1253824e5c10ff9df46874f81ed3ec929e19cfd # v6.3.0
      with:
        role-to-assume: ${{ vars.AWS_DEPLOY_ROLE_ARN }}
        aws-region: ${{ vars.AWS_REGION }}
    - run: aws s3 sync out/ "s3://${{ vars.SITE_BUCKET }}/releases/${{ github.sha }}/" --no-progress
  ```
- Source: https://docs.aws.amazon.com/cli/latest/reference/s3/sync.html (AWS CLI 2.39.2); https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/DownloadDistValuesOrigin.html#DownloadDistValuesOriginPath; https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Invalidation.html; F3; read 2026-10-30. Role trust design is owned by `federating-github-actions-aws-oidc` (reference by name, rule 12).

**A9. Invalidate CloudFront after switching what the distribution serves, with one wildcard path**
> Confidence: High (single source family: CloudFront developer guide + CLI reference)
- Why: `aws cloudfront create-invalidation --distribution-id <id> --paths ...` (paths space-separated). "A path that includes the `*` wildcard counts as one path even if it causes CloudFront to invalidate thousands of files". The first 1,000 paths per month are free, across all distributions of the account. Origin-path changes do not empty edge caches: CloudFront "continues to serve objects that are already in an edge cache until the TTL" expires (stated for origin domain changes; applying it to origin-path changes is (medium confidence)).
- Code: `aws cloudfront create-invalidation --distribution-id "$DIST_ID" --paths "/*"`
- Source: https://docs.aws.amazon.com/cli/latest/reference/cloudfront/create-invalidation.html; https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/PayingForInvalidation.html; https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/DownloadDistValuesOrigin.html; read 2026-10-30

**A10. Standalone output: enable `output: 'standalone'`, ship `public` and `.next/static` with it, run `server.js` as non-root**
> Confidence: High [✓✓ Triangulated | `output` reference + official with-docker example at tag v16.4.3]
- Why: `output: 'standalone'` creates `.next/standalone`, "which can then be deployed on its own without installing `node_modules`", plus a minimal `server.js`. That server "does not copy the `public` or `.next/static` folders by default", so copy them in (or serve them from a CDN). `PORT` and `HOSTNAME` configure the listener. The official Dockerfile (tag v16.4.3) has stages `dependencies`, `builder` and `runner`. The runner copies `public`, `.next/standalone` and `.next/static` with `--chown=node:node`, sets `PORT=3000` and `HOSTNAME="0.0.0.0"`, switches to `USER node` and runs `CMD ["node", "server.js"]`. Its `ARG NODE_VERSION=24.13.0-slim` is older than the 24.x line in F14 (24.22.2), so set it from F14. The example README says "Never pass secrets as build arguments" and its `.dockerignore` "excludes `.env`".
- Code: Dockerfile runner stage, copied from the official example:
  ```dockerfile
  FROM node:${NODE_VERSION} AS runner
  WORKDIR /app
  ENV NODE_ENV=production
  ENV PORT=3000
  ENV HOSTNAME="0.0.0.0"
  COPY --from=builder --chown=node:node /app/public ./public
  RUN mkdir .next
  RUN chown node:node .next
  COPY --from=builder --chown=node:node /app/.next/standalone ./
  COPY --from=builder --chown=node:node /app/.next/static ./.next/static
  USER node
  EXPOSE 3000
  CMD ["node", "server.js"]
  ```
- Image build, push, digest and promotion belong to `publishing-container-images-github-actions` (by name, rule 12).
- Source: https://nextjs.org/docs/app/api-reference/config/next-config-js/output (lastUpdated 2026-09-18); https://raw.githubusercontent.com/vercel/next.js/v16.4.3/examples/with-docker/Dockerfile; https://raw.githubusercontent.com/vercel/next.js/v16.4.3/examples/with-docker/README.md; read 2026-10-30

**A11. Vercel from Actions: `vercel pull` then `vercel build`, then `vercel deploy --prebuilt`, with the same target on all three**
> Confidence: High [✓✓ Triangulated | Vercel KB guide + CLI `build` and `deploy` references]
- Why: `vercel build` writes `.vercel/output` (Build Output API). "It is recommended to run the `vercel pull` command before invoking `vercel build`" so project settings and environment variables are local. `vercel build --prod` uses Production environment variables; Preview is the default. `--prebuilt` deploys "the results of a previous `vc build` execution located in the .vercel/output directory". `--prod` targets the production domain. `stdout` "is always the Deployment URL". The guide warns that deploying without `--prebuilt` builds twice. For custom environments, use `--target=<env>` on all three commands. Caveat from the deploy reference: with `--prebuilt`, "System Environment Variables will be missing at build time".
- Code: the production sequence from the guide, with the CLI pin left as Facts request FR-3:
  ```bash
  vercel pull --yes --environment=production --token="$VERCEL_TOKEN"
  vercel build --prod --token="$VERCEL_TOKEN"
  vercel deploy --prebuilt --prod --token="$VERCEL_TOKEN"
  ```
- Source: https://vercel.com/kb/guide/how-can-i-use-github-actions-with-vercel (last updated 2026-10-16); https://vercel.com/docs/cli/build (2026-10-07); https://vercel.com/docs/cli/deploy (2026-09-18); read 2026-10-30. CLI token handling details belong to `vercel-cli-with-tokens` (by name).

**A12. When Actions deploys a branch to Vercel, turn off Git-integration deployments for that branch**
> Confidence: High [✓✓ Triangulated | Vercel KB guide + git-configuration reference]
- Why: the guide says to set `"git": { "deploymentEnabled": false }` when deploying through Actions, otherwise both deploy on the same push. `git.deploymentEnabled` accepts a Boolean or an object of branch patterns (minimatch). The default is `true`, and "If a branch matches multiple rules and at least one rule is `true`, a deployment will occur." The object form lets Vercel keep building previews for feature branches while Actions owns `main` (see C3).
- Code:
  ```json
  { "$schema": "https://openapi.vercel.sh/vercel.json", "git": { "deploymentEnabled": { "main": false } } }
  ```
- Source: https://vercel.com/kb/guide/how-can-i-use-github-actions-with-vercel (2026-10-16); https://vercel.com/docs/project-configuration/git-configuration (last_updated 2026-08-25); read 2026-10-30

**A13. Pull-request workflows only check and build: `contents: read`, no deploy secret, no `id-token: write`**
> Confidence: High (family rules 7 and 13; GitHub docs on secrets)
- Why: "Any user with write access to your repository has read access to all secrets configured in your repository". Branch code runs during install and build, so a PR job must hold no deploy credential. Secrets other than `GITHUB_TOKEN` "are not passed to the runner when a workflow is triggered from a forked repository". That protects forks, not same-repo branches. When a PR job needs a cloud read, it uses the PR-only read role (rule 13); this unit's CI needs none.
- Source: https://docs.github.com/en/actions/reference/security/secure-use (2026-10-30); https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets (2026-10-30)

### ⚠️ Conditional Patterns

**C1. Credential placement by GitHub plan (target: Team / Pro / Free with PRIVATE repos)**
> Confidence: High (plan statements read 2026-10-30) | design default = family rules 10 and 16
- Availability for private repositories:

  | Feature | Free (private) | Pro / Team (private) | Public repo or Enterprise | Source |
  |---|---|---|---|---|
  | Configure environments | No ("Users with GitHub Free plans can only configure environments for public repositories") | Yes | Yes | manage-environments |
  | Environment secrets | No ("you must use GitHub Pro, GitHub Team, or GitHub Enterprise") | Yes | Yes | deployments-and-environments |
  | Environment variables | No | Yes | Yes | deployments-and-environments |
  | Deployment branches and tags | No | Yes | Yes | deployments-and-environments |
  | Required reviewers | No | No ("only available for public repositories") | Yes (upgrade path) | deployments-and-environments |
  | Wait timer / custom protection rules | No | No | Yes (upgrade path) | deployments-and-environments |

- Handling per plan:

  | Credential | Pro / Team private (default) | Free private | Public repo / Enterprise (upgrade path) |
  |---|---|---|---|
  | AWS deploy role (S3/CloudFront) | Environment `prod` with deployment branch rule "Selected branches and tags" = `main`. Role trust `sub` = `repo:ORG/REPO:environment:prod`. Role ARN in an environment variable. No stored secret | No environments. Role trust `sub` = `repo:ORG/REPO:ref:refs/heads/main`. Role ARN in a repository variable. No stored secret. Any job on `main` gets that `sub`, so dev/prod separation needs separate roles per workflow or account (see `federating-github-actions-aws-oidc`) | Add required reviewers on `prod` |
  | `VERCEL_TOKEN` (+ `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`) | Environment secret on `prod`, limited to `main` by the deployment branch rule. Human approval = required PR review before merge to `main` (rule 16). The Vercel guide's "required-reviewer approval step" is not available here | Option F1: no token in GitHub. Vercel Git integration builds and deploys; Actions runs CI only. Option F2: repository secret. Every user with write access can read it, and every workflow on every branch can use it. Accept this only with a least-privilege token (token scoping (unverified), owned by `vercel-cli-with-tokens`) and deploy workflows triggered only by `push` to `main` | Environment secret + required reviewers: the job "cannot access environment secrets until one of the required reviewers approves it" |

- Agent: "Ask which plan the repository is on and whether it is private. Pro/Team: environment secrets + branch rule. Free: AWS via OIDC `ref` trust; for Vercel ask F1 vs F2 and record the accepted risk if F2."
- Whether branch protection / rulesets are available for private repos on Free and Pro is (unverified) (the protected-branches and rulesets pages read did not state it). On Free, "PR review before merge" may therefore not be enforceable.
- Source: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments; https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments; https://docs.github.com/en/actions/reference/security/oidc; https://docs.github.com/en/actions/reference/security/secure-use; read 2026-10-30

**C2. Package manager: npm vs pnpm vs Yarn (and Corepack)**
> Confidence: High (setup-node docs, pnpm/action-setup README, Corepack README)
- Options: (a) npm: `cache: npm`, `npm ci`. (b) pnpm: `pnpm/action-setup` before `setup-node` with `cache: pnpm` (setup-node advanced-usage order; "pnpm caching support requires pnpm version >= 6.10.0"). `pnpm/action-setup` reads the version from `packageManager` or `devEngines.packageManager` when `version` is omitted, and "does not set up Node.js". (c) Yarn: `cache: yarn` ("handles both Yarn Classic (v1) and Yarn Berry"). The v7 README notes Yarn Classic may fail without `NODE_AUTH_TOKEN`. (d) Corepack: "distributed with Node.js from version 14.19.0 up to (but not including) 25.0.0". It is therefore not bundled with Node 26 (F14), so prefer `pnpm/action-setup` on 26.
- Tradeoffs: npm needs no extra action. pnpm needs a third-party action (Facts request FR-2). Corepack avoids an action only on Node 22/24.
- Source: https://raw.githubusercontent.com/actions/setup-node/v7.1.0/docs/advanced-usage.md; https://raw.githubusercontent.com/pnpm/action-setup/v6.1.0/README.md; https://github.com/nodejs/corepack#readme; read 2026-10-30

**C3. Vercel preview deployments: Git integration (default) vs Actions**
> Confidence: High (mechanisms) | default = family rules 7 and 13
- Options: (a) Default: Vercel Git integration keeps building previews for non-`main` branches (`deploymentEnabled: { "main": false }`), and Actions only checks PRs. No Vercel token is ever exposed to PR code. (b) Actions previews as in the guide (push on non-`main` branches with `vercel pull --environment=preview`, `vercel build`, `vercel deploy --prebuilt`). Branch code then runs in a job that holds `VERCEL_TOKEN`, which conflicts with rule 13 unless the token cannot deploy production. Whether a Vercel token can be restricted that way is (unverified).
- Agent: "Default (a). Choose (b) only if the user supplies a preview-only credential and accepts the rule-13 review."
- Source: https://vercel.com/kb/guide/how-can-i-use-github-actions-with-vercel; https://vercel.com/docs/project-configuration/git-configuration; read 2026-10-30

**C4. S3 promotion strategy: origin-path switch vs sync to a live prefix**
> Confidence: High (CloudFront/S3 behaviour) / (medium confidence) (`update-distribution` mechanics; CLI page not read)
- Options: (a) Default: upload to `releases/<sha>/`, then update the distribution origin path to `/releases/<sha>`, then invalidate `/*`. Rollback = set the origin path to the previous sha and invalidate. (b) `aws s3 sync out/ s3://bucket/live/ --delete`, then invalidate, keeping `releases/<sha>/` copies to re-sync on rollback.
- Tradeoffs: (a) promotion and rollback copy no files and the release is immutable, but each switch is a distribution config change. The ETag handling for `aws cloudfront update-distribution` was not read. (b) uses simple commands but has a window where `live/` mixes old and new files, and rollback re-uploads.
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/DownloadDistValuesOrigin.html; https://docs.aws.amazon.com/cli/latest/reference/s3/sync.html; https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Invalidation.html; read 2026-10-30

**C5. Static export routing on an S3 REST origin with origin access control**
> Confidence: High (problem statement) / (unverified) (CloudFront Functions fix)
- Problem: export writes `/out/blog/post-1.html` (or `/blog/post-1/index.html` with `trailingSlash: true`). CloudFront's default root object applies to the root only: for `/install/` "CloudFront does not return the default root object even if a copy of `index.html` appears in the `install` directory". S3 website endpoints do serve subdirectory index documents, but origin access control applies only to S3 REST origins ("not using the S3 static website endpoint").
- Options: (a) S3 REST origin + OAC (recommended by CloudFront) + a viewer-request URL rewrite that appends `.html` or `index.html` (CloudFront Functions page not read: (unverified)). (b) S3 website endpoint (public bucket, no OAC). (c) Use only routes whose URLs map to files.
- Source: https://nextjs.org/docs/app/guides/static-exports (lastUpdated 2026-08-09); https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/DefaultRootObject.html; https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/DownloadDistValuesOrigin.html; read 2026-10-30

**C6. Static export vs standalone vs Vercel (choose the target)**
> Confidence: High (feature limits)
- Static export does not support: dynamic routes with `dynamicParams: true` or without `generateStaticParams()`, Route Handlers that rely on Request, cookies, rewrites, redirects, headers, Proxy, ISR, default-loader image optimization, Draft Mode, Server Actions, intercepting routes. `next/image` needs a custom loader. If the app needs any of these, use standalone (container) or Vercel.
- Per-environment values: static export has no server, so per-environment values need a runtime config the client fetches per environment (A6). Standalone can read server env at request time (A6).
- Source: https://nextjs.org/docs/app/guides/static-exports (lastUpdated 2026-08-09, read 2026-10-30)

**C7. Telemetry opt-out in CI**
> Confidence: High (mechanism) | policy decision
- Options: set `NEXT_TELEMETRY_DISABLED=1` at workflow or job `env`, or run `next telemetry disable`. Telemetry collects "whether or not the command was run within CI". The official Dockerfile carries `# ENV NEXT_TELEMETRY_DISABLED=1` commented out.
- Agent: "Ask whether org policy requires opt-out; when unsure, set the variable (it changes no build output)." (The "no build output change" part is (unverified).)
- Source: https://nextjs.org/telemetry (2026-10-30); with-docker Dockerfile v16.4.3 (2026-10-30)

**C8. Custom webpack config under Turbopack-default builds**
> Confidence: High
- If the project (or a plugin) defines `webpack`, `next build` fails. Options: `next build --webpack` (keep Webpack), `next build --turbopack` (ignore the webpack config), or migrate to `turbopack` options.
- Source: https://nextjs.org/docs/app/guides/upgrading/version-16 (lastUpdated 2026-10-15, read 2026-10-30)

### 🚫 Forbidden Patterns

**N1. Calling `next lint` in CI on Next.js 16.4**
> Confidence: High
- Why: the command is removed in 16; `next build` does not lint either.
- ❌ Wrong:
  ```yaml
  - run: npx next lint
  ```
- ✅ Correct:
  ```yaml
  - run: npx eslint .        # eslint.config.mjs with eslint-config-next/core-web-vitals
  ```
- Impact: the step fails, or linting silently stops when the script was removed and nothing replaced it.
- Source: https://nextjs.org/docs/app/guides/upgrading/version-16; https://nextjs.org/docs/app/api-reference/config/eslint; read 2026-10-30

**N2. Rebuilding for production with production `NEXT_PUBLIC_*` values**
> Confidence: High (family rule 8; env inlining)
- Why: a second `next build` is a different artifact from the one tested. Public values are inlined at build.
- ❌ Wrong:
  ```yaml
  # cd-web.yml, prod job
  - run: NEXT_PUBLIC_API_URL=https://api.example.com npm run build && aws s3 sync out/ s3://prod-bucket/
  ```
- ✅ Correct:
  ```yaml
  # prod job downloads the artifact built once on main; per-env values come from /config.json (static) or server env (standalone)
  - uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333 # v8.0.2
    with: { name: web-out, path: out }
  ```
- Impact: production runs untested code; values drift between environments.
- Source: https://nextjs.org/docs/app/guides/environment-variables (2026-08-25); family rule 8; read 2026-10-30

**N3. Secrets in `NEXT_PUBLIC_*` variables or Docker build arguments**
> Confidence: High
- Why: `NEXT_PUBLIC_` values are "inlined into any JavaScript sent to the browser". The official Docker example says "Never pass secrets as build arguments."
- ❌ Wrong: `NEXT_PUBLIC_STRIPE_SECRET_KEY=${{ secrets.STRIPE_KEY }} npm run build` or `docker build --build-arg API_KEY=...`
- ✅ Correct: server-only variable (no prefix) read at runtime after `await connection()`, passed to the container at run time.
- Impact: secret published in static JS or image layers.
- Source: https://nextjs.org/docs/app/guides/environment-variables; https://raw.githubusercontent.com/vercel/next.js/v16.4.3/examples/with-docker/README.md; read 2026-10-30

**N4. `vercel deploy` from Actions without `--prebuilt`**
> Confidence: High
- Why: Vercel builds again on its side. The guide warns of duplicate builds and doubled minutes, and the deployed output is not the artifact built and tested in Actions.
- ❌ Wrong: `vercel deploy --prod --token="$VERCEL_TOKEN"`
- ✅ Correct: `vercel build --prod --token="$VERCEL_TOKEN" && vercel deploy --prebuilt --prod --token="$VERCEL_TOKEN"`
- Source: https://vercel.com/kb/guide/how-can-i-use-github-actions-with-vercel; https://vercel.com/docs/cli/deploy; read 2026-10-30

**N5. Leaving Git-integration deployments on for the branch Actions deploys**
> Confidence: High
- ❌ Wrong: no `git.deploymentEnabled` in `vercel.json`, while `cd-web-vercel.yml` deploys `main`.
- ✅ Correct: `"git": { "deploymentEnabled": { "main": false } }` (or `false` for all branches).
- Impact: two production deployments per push, racing for the domain.
- Source: https://vercel.com/kb/guide/how-can-i-use-github-actions-with-vercel; https://vercel.com/docs/project-configuration/git-configuration; read 2026-10-30

**N6. Deploy credentials in pull-request jobs**
> Confidence: High (family rules 7 and 13)
- ❌ Wrong:
  ```yaml
  on: pull_request
  jobs:
    preview:
      permissions: { id-token: write, contents: read }
      steps:
        - run: vercel deploy --prebuilt --token=${{ secrets.VERCEL_TOKEN }}
  ```
- ✅ Correct: PR workflow `ci-web.yml` with `permissions: contents: read` only. Previews come from Vercel Git integration (C3). Deploys run in `cd-web-*.yml` on `push` to `main`.
- Impact: branch code with write-access authorship can exfiltrate a production-capable token.
- Source: https://docs.github.com/en/actions/reference/security/secure-use; family rules 7 and 13; read 2026-10-30

**N7. Copying action majors from documentation examples**
> Confidence: High (brief lesson 1)
- Why: the Next.js CI guide shows `actions/cache@v4`. The Vercel guide shows `actions/checkout@v4`, `actions/setup-node@v4`, `actions/upload-artifact@v4` and `pnpm/action-setup@v3`. All are older than the release pages and the facts file (F6 = setup-node v7.1.0, F10 = checkout v7.0.1, F23 = upload-artifact v7.0.2).
- ❌ Wrong: `uses: actions/setup-node@v4`
- ✅ Correct: `uses: actions/setup-node@949feb2413d6458794dcd2491c4babbbce0c15c1 # v7.1.0`
- Source: https://nextjs.org/docs/app/guides/ci-build-caching; https://vercel.com/kb/guide/how-can-i-use-github-actions-with-vercel; `_family_facts.md`; read 2026-10-30

**N8. Long-lived AWS access keys for the S3/CloudFront deploy**
> Confidence: High (family rule 9; F3)
- ❌ Wrong: `aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}` with `aws-secret-access-key`.
- ✅ Correct: `role-to-assume` + `aws-region` with `permissions: id-token: write` on the deploy job only (A8). Trust design in `federating-github-actions-aws-oidc`.
- Source: F3; https://docs.github.com/en/actions/reference/security/oidc; read 2026-10-30

**N9. `typescript.ignoreBuildErrors: true` without a separate type-check step**
> Confidence: High
- Why: the docs call this "dangerously" producing production code with errors: "If disabled, be sure you are running type checks as part of your build or deploy process".
- ❌ Wrong: `typescript: { ignoreBuildErrors: true }` and no `tsc` step.
- ✅ Correct: keep the default; add `npx next typegen && npx tsc --noEmit` before the build (A4).
- Source: https://nextjs.org/docs/app/api-reference/config/typescript (2026-08-25, read 2026-10-30)

**N10. Relying on bundled Corepack with Node 26**
> Confidence: High
- ❌ Wrong: `node-version: 26` then `- run: corepack enable && pnpm install`
- ✅ Correct: `pnpm/action-setup` (FR-2) before `setup-node` with `cache: pnpm`, or Node 24 if Corepack is required.
- Impact: `corepack: command not found` (Corepack ships only with Node < 25.0.0).
- Source: https://github.com/nodejs/corepack#readme (2026-10-30)

## Migration Guide

**Next.js 15 → 16 (applies to 16.4), CI-relevant items** (source: https://nextjs.org/docs/app/guides/upgrading/version-16, lastUpdated 2026-10-15, read 2026-10-30):

| Change | CI/CD impact |
|---|---|
| `next lint` removed; `next build` no longer lints; `eslint` config option removed | Add an explicit ESLint/Biome step. Codemod `next-lint-to-eslint-cli` |
| Node.js minimum 20.9.0; TypeScript minimum 5.1.0 | `node-version` must be ≥ 20.9; pick an F14 LTS line |
| Turbopack default for `next build`; custom `webpack` config fails the build | Use `--webpack` or `--turbopack`, or migrate (C8) |
| `experimental.turbopack` → top-level `turbopack` | Config edit |
| Turbopack FS cache on for builds (doc history: v16.3.0) in `.next/cache/turbopack` | Persist `.next/cache` (A5) |
| `next dev` writes to `.next/dev`; lockfile prevents concurrent `next build` on the same project | Do not run two builds in one checkout in parallel |
| `size` / `First Load JS` removed from `next build` output | Scripts parsing build output break |
| `serverRuntimeConfig` / `publicRuntimeConfig` removed | Use env vars; runtime values via `connection()` (A6) |
| Async Request APIs only (sync access removed) | Type-check catches leftovers; codemod `next-async-request-api` |
| `middleware` → `proxy` (Node runtime only) | Edge middleware must not be blindly renamed |
| Parallel route slots require `default.js` | Builds fail without them |
| `next/image` defaults (`qualities` `[75]`, `minimumCacheTTL` 4 h, local IP blocked, max 3 redirects) | Runtime behaviour, not CI |
| AMP removed | Build fails if used |

**Next.js 16.4.0 release notes** (https://github.com/vercel/next.js/releases/tag/v16.4.0, 07 Oct, partially read): `eslint-config-next` supports ESLint 10. Turbopack export name mangling is on by default for builds. "Support immutable static assets with `output: 'export'`". "Preserve configured output directories during static export". "Enable strict route matching by default". "Error when app pages do not match any route". There is no breaking-changes section.

**actions/setup-node v4 → v7.1.0** (releases page + README v7.1.0, read 2026-10-30):
- v5.0.0: node24 runtime ("runner is on version v2.327.1 or later"). Automatic caching enabled when `packageManager` is valid. Disable with `package-manager-cache: false`.
- v6.0.0: "Limit automatic caching to npm". `always-auth` input removed.
- v6.3.0: with `node-version-file: package.json`, `devEngines.runtime` is preferred over `engines.node`.
- v7.0.0: ESM migration; outputs `cache-primary-key` and `cache-matched-key`; "The dummy `NODE_AUTH_TOKEN` fallback has been removed" (Yarn Classic and older npm may fail without it).
- v7.1.0: `mise.toml` support, absolute paths in `node-version-file`, version validation, manifest fetch retries.
- Upgrade: replace `@v4`/`@v5`/`@v6` with the F6 SHA. Remove `always-auth`. Decide `package-manager-cache` per job (A2). Set `NODE_AUTH_TOKEN` explicitly where a registry needs it.

⚠️ Migration Note (A2): workflows written for v4 that never set `cache` now get automatic npm caching (v5+) if `packageManager` names npm. Set `package-manager-cache: false` in privileged jobs.

## Implementation Blueprint

Layout (family rules 5 and 15): callers `ci-web.yml`, `cd-web-s3.yml`, `cd-web-vercel.yml`; reusable workflow `./.github/workflows/_nextjs-build.yml`. Commands are `# Representative — adapt to your environment`. SHAs: F10, F6, F3, F23, F24. FR-1 and FR-2 placeholders stay until the facts file gains those rows.

**1. Reusable build: `./.github/workflows/_nextjs-build.yml`** (no secrets, rule 6)

```yaml
# Representative — adapt to your environment. Next.js 16.4.x, setup-node v7.1.0
name: _nextjs-build
on:
  workflow_call:
    inputs:
      node-version: { type: string, default: "24", description: "F14 LTS line, >= 20.9.0 for Next.js 16" }
      output-kind:  { type: string, required: true, description: "export | standalone" }
      artifact-name: { type: string, required: true }
      retention-days: { type: number, default: 14 }
    outputs:
      artifact-name:
        description: Name of the uploaded build artifact
        value: ${{ jobs.build.outputs.artifact-name }}
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      artifact-name: ${{ inputs.artifact-name }}
    env:
      NEXT_TELEMETRY_DISABLED: "1"          # C7 (policy)
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: actions/setup-node@949feb2413d6458794dcd2491c4babbbce0c15c1 # v7.1.0
        with:
          node-version: ${{ inputs.node-version }}
          cache: npm
      - uses: actions/cache@<FR-1 SHA> # v6.1.0 (pending fact FR-1)
        with:
          path: ${{ github.workspace }}/.next/cache
          key: ${{ runner.os }}-nextjs-${{ hashFiles('**/package-lock.json') }}-${{ hashFiles('**/*.js', '**/*.jsx', '**/*.ts', '**/*.tsx') }}
          restore-keys: |
            ${{ runner.os }}-nextjs-${{ hashFiles('**/package-lock.json') }}-
      - run: npm ci
      - run: npx eslint .
      - run: npx next typegen && npx tsc --noEmit
      - run: npm test --if-present
      - run: npx next build
      - name: Assemble standalone bundle
        if: inputs.output-kind == 'standalone'
        run: cp -r public .next/standalone/ && cp -r .next/static .next/standalone/.next/
      - uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2
        with:
          name: ${{ inputs.artifact-name }}
          path: ${{ inputs.output-kind == 'export' && 'out' || '.next/standalone' }}
          retention-days: ${{ inputs.retention-days }}
          include-hidden-files: true   # standalone contains .next/ (input name (unverified) for v7.0.2)
```

**2. PR caller: `ci-web.yml`** (rules 7, 13: no secrets, no deploy)

```yaml
name: ci-web
on: pull_request
permissions:
  contents: read
jobs:
  build:
    uses: ./.github/workflows/_nextjs-build.yml
    with:
      output-kind: export
      artifact-name: web-pr-${{ github.event.pull_request.number }}
      retention-days: 3
```

**3. Static export to S3 + CloudFront: `cd-web-s3.yml`** (Pro/Team default; Free variant noted)

```yaml
name: cd-web-s3
on:
  push:
    branches: [main]
permissions:
  contents: read
concurrency: { group: cd-web-s3-prod, cancel-in-progress: false }
jobs:
  build:
    uses: ./.github/workflows/_nextjs-build.yml
    with: { output-kind: export, artifact-name: web-out-${{ github.sha }}, retention-days: 30 }
  deploy-prod:
    needs: build
    runs-on: ubuntu-latest
    environment: prod              # Pro/Team: branch rule "Selected branches and tags" = main. Free private: delete this line; role trusts ref:refs/heads/main
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333 # v8.0.2
        with: { name: "${{ needs.build.outputs.artifact-name }}", path: out }
      - uses: aws-actions/configure-aws-credentials@e1253824e5c10ff9df46874f81ed3ec929e19cfd # v6.3.0
        with:
          role-to-assume: ${{ vars.AWS_DEPLOY_ROLE_ARN }}
          aws-region: ${{ vars.AWS_REGION }}
      - run: aws s3 sync out/ "s3://${{ vars.SITE_BUCKET }}/releases/${{ github.sha }}/" --no-progress
      - run: ./scripts/switch-origin-path.sh "${{ vars.CF_DISTRIBUTION_ID }}" "/releases/${{ github.sha }}"   # C4 (a); update-distribution mechanics (medium confidence)
      - run: aws cloudfront create-invalidation --distribution-id "${{ vars.CF_DISTRIBUTION_ID }}" --paths "/*"
```
Rollback: rerun `switch-origin-path.sh` with the previous sha and invalidate. No rebuild.

**4. Vercel: `cd-web-vercel.yml`** (build once in Actions, deploy prebuilt; `vercel.json` has `git.deploymentEnabled: { "main": false }`)

```yaml
name: cd-web-vercel
on:
  push:
    branches: [main]
permissions:
  contents: read
jobs:
  deploy-prod:
    runs-on: ubuntu-latest
    environment: prod             # Pro/Team: VERCEL_* are environment secrets. Free private: option F1 (no token; Vercel Git deploys) or F2 (repository secrets, accepted risk), see C1
    env:
      VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
      VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}
      NEXT_TELEMETRY_DISABLED: "1"
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: actions/setup-node@949feb2413d6458794dcd2491c4babbbce0c15c1 # v7.1.0
        with:
          node-version: 24
          package-manager-cache: false   # privileged job (A2)
      - run: npm install --global vercel@<FR-3 version>     # guide uses @latest; pin pending FR-3
      - run: vercel pull --yes --environment=production --token="${{ secrets.VERCEL_TOKEN }}"
      - run: vercel build --prod --token="${{ secrets.VERCEL_TOKEN }}"
      - run: vercel deploy --prebuilt --prod --token="${{ secrets.VERCEL_TOKEN }}" > deployment-url.txt
```
Note: build and deploy share one job because `vercel pull`, `vercel build` and `vercel deploy` all read
`.vercel/`. Splitting them with an artifact of `.vercel/output` is possible (A7) but was not shown in an
official example (medium confidence). Linting, tests and type-check ran on the PR. Promoting an
existing preview build to production instead (`vercel promote`) belongs to `vercel-cli-with-tokens`;
note that `vercel build` without `--prod` uses Preview environment variables.

**5. Container (standalone)**: call `_nextjs-build.yml` with `output-kind: standalone`, or build
directly with the official Dockerfile (A10). Image build, push by digest and promotion follow
`publishing-container-images-github-actions` (F7 `docker/build-push-action` v7.4.0 lives there).
Runtime values come from container env at run time (A6), never `--build-arg` (N3).

**6. pnpm variant** (C2):
```yaml
- uses: pnpm/action-setup@<FR-2 SHA> # v6.1.0 (pending fact FR-2); version read from packageManager
- uses: actions/setup-node@949feb2413d6458794dcd2491c4babbbce0c15c1 # v7.1.0
  with: { node-version: 24, cache: pnpm }
- run: pnpm install --frozen-lockfile    # flag (unverified) on the pages read
```

## Quality Control

- Static checks per PR: `npx eslint .`, `npx next typegen && npx tsc --noEmit`, unit tests, `npx next build` (fails on type errors). Sources: A3, A4.
- Test env: Next.js loads `.env.test` when `NODE_ENV=test`, and `.env.local` is not loaded in test. `@next/env` `loadEnvConfig` loads env the same way for Jest-style setups (https://nextjs.org/docs/app/guides/environment-variables, 2026-08-25).
- The test framework (Jest, Vitest, Playwright) is project-specific. The Vercel guide mentions `npx playwright test` without a pinned version. No version is asserted here (unverified).
- Workflow lint: run `actionlint` if available (tool not researched, (unverified)). SHA-pinning and injection checks follow `automating-github-repos-with-actions` (rule 4).

Verification Loop (offline, run in the repo):
```bash
# Representative — adapt to your environment
grep -rn "next lint" package.json .github/workflows/            # Expected: no output
grep -rn "uses: .*@v[0-9]" .github/workflows/                    # Expected: no output (all SHA-pinned)
grep -rn "secrets\.VERCEL_TOKEN\|id-token: write" .github/workflows/ci-*.yml   # Expected: no output
grep -n "deploymentEnabled" vercel.json                          # Expected: match when cd-web-vercel.yml exists
grep -n "output:" next.config.*                                  # Expected: 'export' or 'standalone' matching the cd-* workflow
npx eslint . && npx next typegen && npx tsc --noEmit && npx next build   # Expected: exit 0; out/ or .next/standalone/ exists
```

## Production Readiness

- Monitoring: Next.js 16 removed `size`/`First Load JS` from build output. The upgrade guide points to Lighthouse or Vercel Analytics for route performance (https://nextjs.org/docs/app/guides/upgrading/version-16).
- Error handling: `vercel deploy` exit code non-zero means failure; `stderr` carries the error and `stdout` the URL (https://vercel.com/docs/cli/deploy). CloudFront invalidation `Status` becomes `Completed` when finished (https://docs.aws.amazon.com/cli/latest/reference/cloudfront/create-invalidation.html).
- Scaling and cost: GitHub caches are evicted after 7 days unused, 10 GB per repository by default. PR caches are scoped to the merge ref and "cannot be restored by the base branch or other pull requests" (https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching). CloudFront: 1,000 free invalidation paths per month per account.
- Container: standalone in monorepos needs `outputFileTracingRoot`. Missing files are fixed with `outputFileTracingIncludes` (https://nextjs.org/docs/app/api-reference/config/next-config-js/output).
- Security checklist: OAC on the S3 origin (CloudFront "recommended"), no secrets in `NEXT_PUBLIC_*`, non-root container user, deploy credentials only on `main` jobs, `concurrency` per environment so deploys do not interleave. Blast-radius controls are in `limiting-blast-radius-github-actions-deploys`.

## Reference Implementations

- Next.js with-docker example at tag v16.4.3: https://github.com/vercel/next.js/tree/v16.4.3/examples/with-docker (Dockerfile + README read 2026-10-30)
- Next.js static export to GitHub Pages template (linked from the static exports guide, not read): https://github.com/nextjs/deploy-github-pages
- Vercel KB "How can I use GitHub Actions with Vercel" (official; examples use stale action majors, N7): https://vercel.com/kb/guide/how-can-i-use-github-actions-with-vercel
- setup-node advanced usage v7.1.0 (pnpm/yarn/restore-only examples): https://raw.githubusercontent.com/actions/setup-node/v7.1.0/docs/advanced-usage.md
- Community examples: none used.

## Research Gaps

```
Gap: G1 Branch protection / rulesets availability for private repos on Free and Pro
Impact: medium; on Free (and possibly Pro) "PR review before merge" may not be enforceable, weakening rule-16 approval
Follow-up: docs.github.com plan pages ("GitHub's plans" / protected branches "Who can use this feature")
§7-ref: Iteration 2 — still open (unverified)

Gap: G2 Vercel token scoping (can a token be limited to one project / preview only?)
Impact: medium; decides C1 option F2 risk and C3 option (b)
Follow-up: owned by neighbour unit vercel-cli-with-tokens
§7-ref: not pursued (out of scope)

Gap: G3 CloudFront origin-path switch mechanics (aws cloudfront get-distribution-config / update-distribution with --if-match ETag)
Impact: low-medium; C4 (a) script body
Follow-up: AWS CLI 2.39.2 reference for update-distribution
§7-ref: Iteration 3 — not read (medium confidence)

Gap: G4 CloudFront Functions URL rewrite for static export subpaths
Impact: medium for S3 REST + OAC; C5 (a)
Follow-up: CloudFront developer guide, CloudFront Functions examples
§7-ref: Iteration 3 — not read (unverified)

Gap: G5 upload-artifact v7.0.2 input `include-hidden-files` (needed for .next/ inside standalone)
Impact: medium; standalone artifact may lack .next/ if hidden files are excluded by default
Follow-up: actions/upload-artifact action.yml at v7.0.2
§7-ref: not read (unverified)

Gap: G6 Pinned Vercel CLI version (guide uses vercel@latest)
Impact: medium (version absolutism)
Follow-up: Facts request FR-3 (npm registry / vercel releases), neighbour unit vercel-cli-with-tokens
§7-ref: not resolved (unverified)

Gap: G7 Splitting vercel build and vercel deploy --prebuilt across jobs via artifact
Impact: low; single-job design works
Follow-up: Vercel Build Output API docs
§7-ref: inferred (medium confidence)

Gap: G8 `pnpm install --frozen-lockfile` flag and `next typegen` before `tsc` ordering
Impact: low
Follow-up: pnpm CLI docs; Next.js CLI reference
§7-ref: inferred (medium confidence / unverified)

Gap: G9 Whether NEXT_TELEMETRY_DISABLED changes build output
Impact: low
§7-ref: (unverified)
```

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Migration Guide | setup-node v5-v7 breaking changes | Resolved from releases page + README v7.1.0 | https://github.com/actions/setup-node/releases ; README v7.1.0 (2026-10-30) |
| 1 | A3 | `next lint` status in 16 | Resolved: removed; ESLint CLI | upgrade guide + ESLint reference (2026-10-30) |
| 1 | A5 | Turbopack build cache location | Resolved: `.next/cache/turbopack`, default since 16.3.0 | turbopackFileSystemCache reference (2026-10-30) |
| 2 | C1 | plan availability (env secrets, branch rules, reviewers) for private repos | Resolved: Free none; Pro/Team secrets + vars + branch rules; reviewers/wait timer public only | deployments-and-environments + manage-environments (2026-10-30) |
| 2 | C1 | repo secret exposure on Free | Resolved: "Any user with write access ... has read access to all secrets"; forks get none | secure-use + use-secrets (2026-10-30) |
| 2 | G1 | branch protection on Free/Pro private | Not resolved (pages read do not state it) | about-protected-branches, about-rulesets (2026-10-30) |
| 2 | C2 | Corepack with Node 26 | Resolved: bundled only < 25.0.0 | https://github.com/nodejs/corepack#readme (2026-10-30) |
| 3 | C5 | subdirectory index on S3 REST origin | Problem confirmed (default root object root-only); fix (CloudFront Functions) not read | DefaultRootObject (2026-10-30) |
| 3 | A9 | invalidation pricing | Resolved: wildcard = 1 path; 1,000 free / month / account | PayingForInvalidation (2026-10-30) |

## Completion Checklist

- [x] Domain complexity tier assessed (Complex)
- [x] All brief scope areas covered (setup-node v7, pnpm/corepack, lint/typecheck/test/build, `.next/cache`, telemetry, static export + S3/CloudFront + versioned prefix, standalone Dockerfile + hand-off, Vercel prebuilt + Git integration, NEXT_PUBLIC vs runtime)
- [x] Pattern counts driven by domain (13 / 8 / 10)
- [x] Every anti-pattern has a ✅ alternative
- [x] Commands marked representative
- [x] Sources dated and linked
- [x] Plan-dependent credential handling for Free / Pro-Team / public-Enterprise (C1)
- [x] PR jobs hold no deploy credentials (A13, N6)
- [x] Action pins only from facts file; missing ones listed under Facts requested
- [x] Research Iteration Changelog present; gaps cross-referenced
- [x] File ends with Source Bibliography

## Agent Operation Notes

- **High Confidence (execute without asking)**: A1-A3, A5-A8, A10-A13; N1-N10; C1 plan table; Next.js 16 migration items.
- **Medium Confidence (validate with user)**: A4 `next typegen` before `tsc`; A9 cache behaviour after origin-path switch; C4 `update-distribution` mechanics; splitting Vercel build/deploy across jobs.
- **Low Confidence (must ask human)**: G1 (branch protection on Free/Pro private), G2 (Vercel token scoping), G4 (CloudFront Functions rewrite), G5 (`include-hidden-files`), G6 (Vercel CLI pin).
- **Ask-First triggers for the skill**: plan + privacy (C1); Vercel on Free (F1 vs F2); package manager (C2); deploy target (C6); S3 promotion strategy (C4); telemetry policy (C7).
- **Never make a shipped skill read `workspace/`**: the skill must restate the facts it needs from `_family_facts.md` rows, not link to that file at runtime.

## Facts requested

These are actions and versions used by this unit that are not in `_family_facts.md`. They were resolved from release pages on 2026-10-30. The orchestrator should confirm the SHAs with `git ls-remote` (peeled `^{}` if annotated) before adding rows. Examples above use `<FR-n SHA>` placeholders until then.

| ID | Repo | Tag | SHA (from release page) | Source URL | Notes |
|---|---|---|---|---|---|
| FR-1 | actions/cache | v6.1.0 (Latest, 26 Jun, year not shown) | 55cc8345863c7cc4c66a329aec7e433d2d1c52a9 | https://github.com/actions/cache/releases | v5.0.0+ runs on Node 24, needs runner ≥ 2.327.1; v6.0.0 = ESM migration; v5.1.0 published the same day as v6.1.0 |
| FR-2 | pnpm/action-setup | v6.1.0 (Latest, 05 Sep, year not shown) | ea17c68df8912ef543352723c149a84f56e3d413 | https://github.com/pnpm/action-setup/releases | v6.1.0 adds pnpm v12 support; inputs `version`, `package_json_file`, `run_install`, `cache` per README v6.1.0 |
| FR-3 | vercel (npm CLI) | not resolved | n/a | (none read) | Vercel guide installs `vercel@latest`; a pinned version is needed (version absolutism); likely owned by `vercel-cli-with-tokens` |
| FR-4 | Next.js 16.4.0 release | v16.4.0 (07 Oct) | e273d5b (short, from release page) | https://github.com/vercel/next.js/releases/tag/v16.4.0 | Informational; F15 already pins 16.4.3 |

## Pages read

| URL | read on | official | prompt-injection-like instructions found |
|---|---|---|---|
| https://github.com/actions/setup-node/releases (page 1 of 7; summarised) | 2026-10-30 | yes | no |
| https://raw.githubusercontent.com/actions/setup-node/v7.1.0/action.yml (summarised) | 2026-10-30 | yes | no |
| https://raw.githubusercontent.com/actions/setup-node/v7.1.0/README.md (quoted sections) | 2026-10-30 | yes | no |
| https://raw.githubusercontent.com/actions/setup-node/v7.1.0/docs/advanced-usage.md (caching sections) | 2026-10-30 | yes | no |
| https://nextjs.org/docs/app/guides/ci-build-caching | 2026-10-30 | yes | no |
| https://nextjs.org/docs/app/guides/upgrading/version-16 | 2026-10-30 | yes | no |
| https://nextjs.org/docs/app/guides/static-exports | 2026-10-30 | yes | no |
| https://nextjs.org/docs/app/api-reference/config/next-config-js/output | 2026-10-30 | yes | no |
| https://nextjs.org/docs/app/guides/environment-variables | 2026-10-30 | yes | no |
| https://nextjs.org/docs/app/api-reference/config/typescript | 2026-10-30 | yes | no |
| https://nextjs.org/docs/app/api-reference/config/eslint | 2026-10-30 | yes | no |
| https://nextjs.org/docs/app/api-reference/config/next-config-js/turbopackFileSystemCache | 2026-10-30 | yes | no |
| https://nextjs.org/telemetry | 2026-10-30 | yes | no |
| https://github.com/vercel/next.js/releases/tag/v16.4.0 (partial: chars 0-100000 of 106008) | 2026-10-30 | yes | no |
| https://raw.githubusercontent.com/vercel/next.js/v16.4.3/examples/with-docker/Dockerfile (instruction lines only; summarised) | 2026-10-30 | yes | no |
| https://raw.githubusercontent.com/vercel/next.js/v16.4.3/examples/with-docker/README.md (summarised) | 2026-10-30 | yes | no |
| https://vercel.com/kb/guide/how-can-i-use-github-actions-with-vercel (two passes; summarised) | 2026-10-30 | yes | no (page contains "For AI agents" navigation notes; ordinary site navigation, not instructions to this agent) |
| https://vercel.com/docs/project-configuration/git-configuration | 2026-10-30 | yes | no (same "For AI agents: Follow these links" related-pages block; navigation only, not followed) |
| https://vercel.com/docs/cli/deploy | 2026-10-30 | yes | no (same navigation block) |
| https://vercel.com/docs/cli/build | 2026-10-30 | yes | no (same navigation block) |
| https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments (plan statements) | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments (plan statements) | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/concepts/security/secrets | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/reference/security/secure-use | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/reference/security/oidc (sub formats, id-token) | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching | 2026-10-30 | yes | no |
| https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches | 2026-10-30 | yes | no |
| https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets | 2026-10-30 | yes | no |
| https://github.com/pnpm/action-setup/releases | 2026-10-30 | yes (publisher's repo) | no |
| https://raw.githubusercontent.com/pnpm/action-setup/v6.1.0/README.md | 2026-10-30 | yes (publisher's repo) | no |
| https://github.com/actions/cache/releases | 2026-10-30 | yes | no |
| https://nodejs.org/api/corepack.html (308 redirect to the Corepack README, followed) | 2026-10-30 | yes | no |
| https://github.com/nodejs/corepack#readme | 2026-10-30 | yes | no |
| https://docs.aws.amazon.com/cli/latest/reference/s3/sync.html (AWS CLI 2.39.2) | 2026-10-30 | yes | no |
| https://docs.aws.amazon.com/cli/latest/reference/cloudfront/create-invalidation.html (AWS CLI 2.39.2) | 2026-10-30 | yes | no |
| https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Invalidation.html | 2026-10-30 | yes | no |
| https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/PayingForInvalidation.html | 2026-10-30 | yes | no |
| https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/DownloadDistValuesOrigin.html | 2026-10-30 | yes | no |
| https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/DefaultRootObject.html | 2026-10-30 | yes | no |

No web searches were used.

## Source Bibliography

**Primary — Next.js (nextjs.org, read 2026-10-30; lastUpdated in brackets)**:
- Upgrading to version 16 [2026-10-15]: https://nextjs.org/docs/app/guides/upgrading/version-16
- CI build caching [2025-04-22, current page]: https://nextjs.org/docs/app/guides/ci-build-caching
- Static exports [2026-08-09]: https://nextjs.org/docs/app/guides/static-exports
- `output` (standalone) [2026-09-18]: https://nextjs.org/docs/app/api-reference/config/next-config-js/output
- Environment variables [2026-08-25]: https://nextjs.org/docs/app/guides/environment-variables
- TypeScript [2026-08-25]: https://nextjs.org/docs/app/api-reference/config/typescript
- ESLint plugin [2026-10-15]: https://nextjs.org/docs/app/api-reference/config/eslint
- Turbopack FileSystem caching [2026-10-06]: https://nextjs.org/docs/app/api-reference/config/next-config-js/turbopackFileSystemCache
- Telemetry: https://nextjs.org/telemetry
- Release v16.4.0 (07 Oct): https://github.com/vercel/next.js/releases/tag/v16.4.0
- with-docker example at v16.4.3: https://raw.githubusercontent.com/vercel/next.js/v16.4.3/examples/with-docker/Dockerfile ; https://raw.githubusercontent.com/vercel/next.js/v16.4.3/examples/with-docker/README.md
- Family fact F15 (Next.js 16.4.3) and F14 (Node LTS lines): `workspace/github-actions-cicd/_family_facts.md`

**Primary — actions (read 2026-10-30)**:
- setup-node releases: https://github.com/actions/setup-node/releases
- setup-node v7.1.0 action.yml / README / advanced usage: https://raw.githubusercontent.com/actions/setup-node/v7.1.0/action.yml ; https://raw.githubusercontent.com/actions/setup-node/v7.1.0/README.md ; https://raw.githubusercontent.com/actions/setup-node/v7.1.0/docs/advanced-usage.md
- actions/cache releases (FR-1): https://github.com/actions/cache/releases
- pnpm/action-setup releases and README v6.1.0 (FR-2): https://github.com/pnpm/action-setup/releases ; https://raw.githubusercontent.com/pnpm/action-setup/v6.1.0/README.md
- Corepack README: https://github.com/nodejs/corepack#readme
- Family facts F3, F6, F10, F23, F24: `workspace/github-actions-cicd/_family_facts.md`

**Primary — Vercel (read 2026-10-30)**:
- KB guide, GitHub Actions with Vercel [published 2026-07-23, updated 2026-10-16]: https://vercel.com/kb/guide/how-can-i-use-github-actions-with-vercel
- Git configuration [2026-08-25]: https://vercel.com/docs/project-configuration/git-configuration
- `vercel deploy` [2026-09-18]: https://vercel.com/docs/cli/deploy
- `vercel build` [2026-10-07]: https://vercel.com/docs/cli/build

**Primary — GitHub (read 2026-10-30)**:
- Deployments and environments: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments
- Managing environments: https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments
- Secrets concept: https://docs.github.com/en/actions/concepts/security/secrets
- Using secrets: https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets
- Secure use reference: https://docs.github.com/en/actions/reference/security/secure-use
- OIDC reference: https://docs.github.com/en/actions/reference/security/oidc
- Dependency caching reference: https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching
- About protected branches: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
- About rulesets: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets

**Primary — AWS (read 2026-10-30)**:
- AWS CLI 2.39.2 `s3 sync`: https://docs.aws.amazon.com/cli/latest/reference/s3/sync.html
- AWS CLI 2.39.2 `cloudfront create-invalidation`: https://docs.aws.amazon.com/cli/latest/reference/cloudfront/create-invalidation.html
- CloudFront invalidation vs versioning: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Invalidation.html
- CloudFront invalidation pricing: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/PayingForInvalidation.html
- CloudFront origin settings (origin path, OAC): https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/DownloadDistValuesOrigin.html
- CloudFront default root object: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/DefaultRootObject.html

**Cross-package references (by name only, rule 12)**: `automating-github-repos-with-actions`, `federating-github-actions-aws-oidc`, `publishing-container-images-github-actions`, `limiting-blast-radius-github-actions-deploys`, `composing-github-actions-pipelines`, `vercel-cli-with-tokens`.

**Validation**: no community sources used.
