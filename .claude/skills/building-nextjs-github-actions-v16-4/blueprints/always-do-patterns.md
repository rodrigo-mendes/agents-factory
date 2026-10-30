# Always-do patterns with code

Back to [SKILL.md](../SKILL.md). Next.js 16.4.x; research date 2026-10-30. Full workflows: [build](./workflow-node-build.md), [S3](./workflow-deploy-s3-cf.md), [Vercel](./workflow-deploy-vercel.md), [callers](./workflow-callers.md).

Contents: [Lint and typecheck](#lint-and-typecheck) | [Cache and telemetry](#cache-and-telemetry) | [Credentialed jobs and pnpm](#credentialed-jobs-and-pnpm) | [Build once](#build-once-and-runtime-values) | [S3 and CloudFront](#s3-and-cloudfront) | [Vercel](#vercel) | [Pull requests](#pull-requests) | [Standalone](#standalone)

## Lint and typecheck

`next lint` is gone and `next build` does not lint. `package.json` carries `"lint": "eslint ."` with a flat `eslint.config.mjs` using `eslint-config-next/core-web-vitals`.

```yaml
- run: npm run lint
- run: npx next typegen && npx tsc --noEmit   # typegen first (medium confidence)
```

`next build` fails on type errors; `tsc --noEmit` is the documented CI check. `next-env.d.ts` is generated and ignored by Git, so a fresh checkout lacks it until `next typegen` runs.
Sources: https://nextjs.org/docs/app/guides/upgrading/version-16 ; https://nextjs.org/docs/app/api-reference/config/typescript

## Cache and telemetry

```yaml
env:
  NEXT_TELEMETRY_DISABLED: "1"
steps:
  - uses: actions/cache@55cc8345863c7cc4c66a329aec7e433d2d1c52a9 # v6.1.0
    with:
      path: ${{ github.workspace }}/.next/cache
      key: ${{ runner.os }}-nextjs-${{ hashFiles('**/package-lock.json') }}-${{ hashFiles('**/*.js', '**/*.jsx', '**/*.ts', '**/*.tsx') }}
      restore-keys: |
        ${{ runner.os }}-nextjs-${{ hashFiles('**/package-lock.json') }}-
```

Without persistence CI prints the "No Cache Detected" message. Since 16.3.0 the Turbopack build cache is on by default in `.next/cache/turbopack`, so the restore speeds up the bundler. If the environment never keeps the cache, set `experimental.turbopackFileSystemCacheForBuild: false` to skip writing it. Telemetry collects whether a command ran in CI; the opt-out is a family decision, and it changing no build output is unverified.
Sources: https://nextjs.org/docs/app/guides/ci-build-caching ; https://nextjs.org/docs/app/api-reference/config/next-config-js/turbopackFileSystemCache ; https://nextjs.org/telemetry

## Credentialed jobs and pnpm

```yaml
- uses: actions/setup-node@949feb2413d6458794dcd2491c4babbbce0c15c1 # v7.1.0
  with:
    node-version: 24
    package-manager-cache: false      # job holds a deploy secret or id-token: write
```

Automatic npm caching runs when `packageManager` names npm and no `cache` input is set. The README advises disabling it for elevated-privilege workflows; a poisoned cache may expose credentials, OIDC tokens included. Better: deploy jobs install no packages and download the artifact.

On Node 26 Corepack is not bundled (it ships below 25.0.0). `pnpm/action-setup` goes before `setup-node`; it reads the version from `packageManager` when `version` is omitted and does not set up Node.

```yaml
- uses: pnpm/action-setup@ea17c68df8912ef543352723c149a84f56e3d413 # v6.1.0
- uses: actions/setup-node@949feb2413d6458794dcd2491c4babbbce0c15c1 # v7.1.0
  with: { node-version: 26, cache: pnpm }
```

Sources: https://github.com/actions/setup-node/blob/v7.1.0/README.md ; https://github.com/actions/setup-node/blob/v7.1.0/docs/advanced-usage.md ; https://github.com/nodejs/corepack#readme

## Build once and runtime values

Next.js inlines `NEXT_PUBLIC_` values into the browser bundle at build time; one image built once and promoted keeps the build-time value everywhere. Per-environment values come from server code after `await connection()`, or from a config file the client fetches (static export). `publicRuntimeConfig` is removed in 16.

```tsx
import { connection } from 'next/server'
export default async function Page() {
  await connection()
  return <p>{process.env.API_BASE_URL}</p>
}
```

Upload once, deploy by download, set retention (default is 90 days):

```yaml
- uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2
  with: { name: web-static-${{ github.sha }}, path: out, retention-days: 30 }
```

Sources: https://nextjs.org/docs/app/guides/environment-variables ; https://docs.github.com/en/actions/tutorials/store-and-share-data

## S3 and CloudFront

```yaml
permissions: { contents: read, id-token: write }     # deploy job only
steps:
  - uses: ./.github/actions/cloud/login-aws     # composite owned by federating-github-actions-aws-oidc
    with: { role-arn: "${{ vars.AWS_DEPLOY_ROLE_ARN }}", region: "${{ vars.AWS_REGION }}" }
  - run: aws s3 sync out/ "s3://${BUCKET}/releases/${GITHUB_SHA}/" --no-progress
  - run: aws cloudfront create-invalidation --distribution-id "$DIST_ID" --paths "/*"
```

AWS recommends versioning for frequent updates because it simplifies rolling forward and back. A wildcard path counts as one path however many files it covers; the first 1,000 paths a month are free.
Sources: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Invalidation.html ; https://docs.aws.amazon.com/cli/latest/reference/cloudfront/create-invalidation.html ; https://docs.github.com/en/actions/reference/security/oidc

## Vercel

```bash
# VERCEL_TOKEN, VERCEL_ORG_ID, VERCEL_PROJECT_ID set in env: of these three steps only
vercel pull --yes --environment=production
vercel build --prod
vercel deploy --prebuilt --prod
```

```json
{ "git": { "deploymentEnabled": { "main": false } } }
```

Source: https://vercel.com/kb/guide/how-can-i-use-github-actions-with-vercel

## Pull requests

```yaml
on: pull_request
permissions:
  contents: read
```

Any user with write access can read repository secrets; branch code runs during install and build.
Source: https://docs.github.com/en/actions/reference/security/secure-use

## Standalone

Copy `public` and `.next/static` next to `server.js`, set `PORT` and `HOSTNAME`, run as `USER node`. Full Dockerfile: [standalone container](./standalone-container.md).
Source: https://nextjs.org/docs/app/api-reference/config/next-config-js/output
