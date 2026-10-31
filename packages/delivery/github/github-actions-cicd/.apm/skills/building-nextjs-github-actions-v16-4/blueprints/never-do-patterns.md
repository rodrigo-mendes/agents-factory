# Never-do patterns with examples

Back to [SKILL.md](../SKILL.md). Next.js 16.4.x; research date 2026-10-30. Every alternative below is High confidence.

Contents: [N1 next lint](#n1-next-lint-in-ci) | [N2 Rebuild per environment](#n2-rebuilding-per-environment-with-different-next_public-values) | [N3 Secrets in public vars](#n3-secrets-in-next_public-or-build-args) | [N4 deploy without prebuilt](#n4-vercel-deploy-without---prebuilt) | [N5 double deploy](#n5-git-integration-deploying-the-branch-actions-deploys) | [N6 PR credentials](#n6-deploy-credentials-in-pull-request-jobs) | [N7 AWS keys](#n7-long-lived-aws-keys) | [N8 ignoreBuildErrors](#n8-ignorebuilderrors-without-a-type-check) | [N9 Corepack](#n9-corepack-on-node-26) | [N10 docs majors](#n10-copying-action-majors-from-docs-examples)

## N1 next lint in CI

The command is removed in Next.js 16 and `next build` does not lint.

- ❌ `- run: npx next lint`
- ✅ `- run: npm run lint` with `"lint": "eslint ."`

Impact: the step fails, or linting silently stops once the script was removed and nothing replaced it. Source: https://nextjs.org/docs/app/guides/upgrading/version-16

## N2 Rebuilding per environment with different NEXT_PUBLIC values

A second `next build` is a different artifact from the one tested; public values are inlined at build.

- ❌ `NEXT_PUBLIC_API_URL=https://api.example.com npm run build && aws s3 sync out/ s3://prod-bucket/`
- ✅ Download the artifact built once and deploy it; per-environment values come from server env (standalone) or a config the client fetches (static).

```yaml
- uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333 # v8.0.2
  with: { name: "${{ inputs.artifact-name }}", path: out }
```

Impact: production runs untested code and values drift between environments. Source: https://nextjs.org/docs/app/guides/environment-variables

## N3 Secrets in NEXT_PUBLIC or build args

`NEXT_PUBLIC_` values are inlined into JavaScript sent to the browser; the official Docker example says never pass secrets as build arguments.

- ❌ `NEXT_PUBLIC_STRIPE_SECRET_KEY=${{ secrets.STRIPE_KEY }} npm run build`, or `docker build --build-arg API_KEY=...`
- ✅ A server-only variable with no prefix, read after `await connection()` and passed to the container at run time.

Impact: the secret is published in static JavaScript or image layers. Source: https://github.com/vercel/next.js/blob/v16.4.3/examples/with-docker/README.md

## N4 Vercel deploy without --prebuilt

Vercel builds again on its side; the deployed output is not the artifact built and tested in Actions, and build minutes double.

- ❌ `vercel deploy --prod --token="$VERCEL_TOKEN"`
- ✅ `vercel build --prod --token="$VERCEL_TOKEN" && vercel deploy --prebuilt --prod --token="$VERCEL_TOKEN"`

Source: https://vercel.com/kb/guide/how-can-i-use-github-actions-with-vercel

## N5 Git integration deploying the branch Actions deploys

- ❌ No `git.deploymentEnabled` in `vercel.json` while `cd-web-vercel.yml` deploys `main`.
- ✅ `"git": { "deploymentEnabled": { "main": false } }`, or `false` for all branches.

Impact: two production deployments per push, racing for the domain. Source: https://vercel.com/docs/project-configuration/git-configuration

## N6 Deploy credentials in pull-request jobs

Branch code runs during install and build; anyone with write access can read repository secrets, and forks get none, which does not protect same-repo branches.

- ❌ A job under `on: pull_request` with `permissions: { id-token: write }` or `--token=${{ secrets.VERCEL_TOKEN }}`.
- ✅ `ci-web.yml` with `contents: read` only; previews from Vercel Git integration; deploys in `cd-web-*.yml` on `push` to `main`.

Impact: branch code can exfiltrate a production-capable token. Source: https://docs.github.com/en/actions/reference/security/secure-use

## N7 Long-lived AWS keys

- ❌ `aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}` with `aws-secret-access-key`
- ✅ `role-to-assume` and `aws-region` on a job with `id-token: write`; trust design lives in `federating-github-actions-aws-oidc`.

Source: https://docs.github.com/en/actions/reference/security/oidc

## N8 ignoreBuildErrors without a type check

The docs warn that disabling the build's type check ships code with errors unless checks run elsewhere.

- ❌ `typescript: { ignoreBuildErrors: true }` and no `tsc` step
- ✅ Keep the default and add `npx next typegen && npx tsc --noEmit` before the build.

Source: https://nextjs.org/docs/app/api-reference/config/typescript

## N9 Corepack on Node 26

- ❌ `node-version: 26` then `corepack enable && pnpm install`
- ✅ `pnpm/action-setup` before `setup-node` with `cache: pnpm`, or Node 24 if Corepack is required.

Impact: `corepack: command not found`; Corepack ships only with Node below 25.0.0. Source: https://github.com/nodejs/corepack#readme

## N10 Copying action majors from docs examples

The Next.js CI guide shows `actions/cache@v4`; the Vercel guide shows `checkout@v4`, `setup-node@v4`, `upload-artifact@v4` and `pnpm/action-setup@v3`. All are older than the pins in the Version Context table.

- ❌ `uses: actions/setup-node@v4`
- ✅ `uses: actions/setup-node@949feb2413d6458794dcd2491c4babbbce0c15c1 # v7.1.0`

SHA pinning and injection rules: `automating-github-repos-with-actions`. Sources: https://nextjs.org/docs/app/guides/ci-build-caching ; https://vercel.com/kb/guide/how-can-i-use-github-actions-with-vercel

## Trap: a migrated v4 workflow starts caching npm

Workflows written for setup-node v4 that never set `cache` get automatic npm caching from v5 on when `packageManager` names npm. A credentialed job must set `package-manager-cache: false` (see Always Do). Source: https://github.com/actions/setup-node/blob/v7.1.0/README.md
