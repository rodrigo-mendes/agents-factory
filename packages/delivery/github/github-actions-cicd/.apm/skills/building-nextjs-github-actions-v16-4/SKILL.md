---
name: building-nextjs-github-actions-v16-4
description: "Builds Next.js 16.4 CI/CD on GitHub Actions: reusable node build, static export to S3 and CloudFront, standalone container hand-off, Vercel prebuilt deploys, pnpm on Node 26. Use when writing or reviewing Next.js pipelines or when next lint is gone. Not for Azure DevOps."
---

# Next.js 16.4 on GitHub Actions (S3 + CloudFront, container, Vercel)

> Version lock: every claim applies to **Next.js 16.4.x (latest stable 16.4.3)** built with `actions/setup-node` v7.1.0 on GitHub.com Actions. Research date **2026-10-30**.
> Claims tagged unverified or medium confidence were not fully confirmed against an official page; each tag maps to the [register](./blueprints/unverified-and-risks.md#tag-to-register-mapping).
> Scope: the Next.js pieces only. How `workflow_call` works belongs to `composing-github-actions-pipelines`; AWS login and role trust belong to `federating-github-actions-aws-oidc`; image build, push and promotion belong to `publishing-container-images-github-actions`; Vercel CLI and token handling belong to `vercel-cli-with-tokens`; SHA pinning and injection-safe scripting belong to `automating-github-repos-with-actions`; deploy blast radius belongs to `limiting-blast-radius-github-actions-deploys`.
> Provenance: the dated research file for this unit under the factory workspace; this skill never reads it at run time.

## Version Context

| Item | Value | Source (fetched 2026-10-30) |
|---|---|---|
| Next.js | 16.4.3 latest stable (23 Oct); 16.4.0 on 07 Oct; Node.js 20.9.0 minimum | https://github.com/vercel/next.js/releases |
| Node.js LTS lines | 26 (26.13.0), 24 (24.22.2), 22 (22.23.4) | https://nodejs.org/en/about/previous-releases |
| `actions/setup-node` | v7.1.0 = `949feb2413d6458794dcd2491c4babbbce0c15c1` | https://github.com/actions/setup-node/releases |
| `actions/checkout` | v7.0.1 = `3d3c42e5aac5ba805825da76410c181273ba90b1` | https://github.com/actions/checkout/releases |
| `actions/cache` | v6.1.0 = `55cc8345863c7cc4c66a329aec7e433d2d1c52a9` | https://github.com/actions/cache/releases |
| `pnpm/action-setup` | v6.1.0 = `ea17c68df8912ef543352723c149a84f56e3d413` | https://github.com/pnpm/action-setup/releases |
| `actions/upload-artifact` | v7.0.2 = `cf430e030ddbb5b0abf93d22962f4752f3646cd9` | https://github.com/actions/upload-artifact/releases |
| `actions/download-artifact` | v8.0.2 = `9000827ccba6bdab643e8b6fd33ac0654aef8333` | https://github.com/actions/download-artifact/releases |
| `aws-actions/configure-aws-credentials` | v6.3.0 = `e1253824e5c10ff9df46874f81ed3ec929e19cfd` | https://github.com/aws-actions/configure-aws-credentials/releases |
| Vercel CLI | no pinned version resolved; the Vercel guide installs `vercel@latest` | https://vercel.com/kb/guide/how-can-i-use-github-actions-with-vercel |

**Version-lifetime risk** (as of 2026-10-30; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- Next.js 16.4.0 was released on 2026-10-07; re-read the upgrade guide before moving the minor line.
- Pinned action SHAs go stale; re-resolve them with `git ls-remote` before every bump.
- Vercel CLI has no pin in this skill; a pipeline using `@latest` is not reproducible.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Verification Loop](#verification-loop)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Reusable build `_node-build.yml` and composite `setup-node-build`](./blueprints/workflow-node-build.md)
- [Reusable `_deploy-s3-cf.yml`, origin-path switch, rollback](./blueprints/workflow-deploy-s3-cf.md)
- [Reusable `_deploy-vercel.yml` and Free variants](./blueprints/workflow-deploy-vercel.md)
- [Callers: ci-web, cd-web-s3, cd-web-vercel](./blueprints/workflow-callers.md)
- [Standalone container hand-off](./blueprints/standalone-container.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

Shape: `_node-build.yml` (checks + build once, uploads one artifact) feeds `_deploy-s3-cf.yml` or `_deploy-vercel.yml`; the composite `./.github/actions/build/setup-node-build` holds Node, pnpm and cache setup. Thin callers `ci-web.yml` (pull_request, never deploys), `cd-web-s3.yml` and `cd-web-vercel.yml` (push to main) wire them. The container path reuses the `standalone` artifact and hands off to `publishing-container-images-github-actions`.

### ✅ Always Do

- **Lint with the ESLint CLI as its own step**; `next lint` is removed and `next build` no longer lints ([upgrade guide](https://nextjs.org/docs/app/guides/upgrading/version-16)).
- **Type-check with `tsc --noEmit` before the build** ([TypeScript reference](https://nextjs.org/docs/app/api-reference/config/typescript)).
- **Persist `.next/cache` between runs**, keyed on the lockfile and source hashes ([CI build caching](https://nextjs.org/docs/app/guides/ci-build-caching)).
- **Set `NEXT_TELEMETRY_DISABLED=1` at workflow or job level** (family decision; opt-out mechanism on the [telemetry page](https://nextjs.org/telemetry)).
- **Set `package-manager-cache: false` in jobs that hold credentials** ([setup-node README](https://github.com/actions/setup-node/blob/v7.1.0/README.md)).
- **Use `pnpm/action-setup` instead of Corepack on Node 26**; Corepack ships only with Node below 25.0.0 ([Corepack README](https://github.com/nodejs/corepack#readme)).
- **Keep `NEXT_PUBLIC_*` values identical in every environment of one artifact**; they are inlined at build time ([environment variables](https://nextjs.org/docs/app/guides/environment-variables)).
- **Read per-environment values on the server after `await connection()`** ([environment variables](https://nextjs.org/docs/app/guides/environment-variables)).
- **Build once, upload the output, deploy by downloading the same artifact** (family decision; artifact actions in the table above).
- **Set `retention-days` on every uploaded artifact**; default retention is 90 days ([store and share data](https://docs.github.com/en/actions/tutorials/store-and-share-data)).
- **Grant `id-token: write` only on the AWS deploy job** ([OIDC reference](https://docs.github.com/en/actions/reference/security/oidc)).
- **Upload each static release to `releases/<git-sha>/`** (family decision; versioning rationale on the [CloudFront invalidation page](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Invalidation.html)).
- **Invalidate with one `/*` path after a switch** ([create-invalidation](https://docs.aws.amazon.com/cli/latest/reference/cloudfront/create-invalidation.html)).
- **Run `vercel pull`, `vercel build`, then `vercel deploy --prebuilt` with the same target** ([Vercel guide](https://vercel.com/kb/guide/how-can-i-use-github-actions-with-vercel)).
- **Set `git.deploymentEnabled` to `{ "main": false }` when Actions deploys main** ([Vercel guide](https://vercel.com/kb/guide/how-can-i-use-github-actions-with-vercel)).
- **Give pull_request workflows `contents: read` only** ([secure use](https://docs.github.com/en/actions/reference/security/secure-use)).
- **Copy `public` and `.next/static` into a standalone image and run as `USER node`** ([output reference](https://nextjs.org/docs/app/api-reference/config/next-config-js/output)).

Code for each rule: [always-do patterns](./blueprints/always-do-patterns.md).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| GitHub plan and privacy | Pro/Team private (default): environments with secrets and variables, branch policy `main`, protected `main` with required PR reviewers. Free private (weaker, say so): no environments, AWS role trusts `ref:refs/heads/main`, Vercel token only as a repository secret. Required reviewers and wait timers need a public repo or Enterprise | "Which GitHub plan owns this repository, and is it private?" |
| Deploy target | Static export (no server features, `next/image` needs a custom loader), standalone container, or Vercel | "Does the app use Server Actions, ISR, rewrites, Proxy or default image optimization?" |
| Vercel on Free | Option A: no token in GitHub, Vercel Git integration deploys, Actions runs CI only. Option B: repository secret, accepted risk, least-privilege token (scoping unverified) | "Option A or B? Record the accepted risk if B." |
| Vercel CLI version | No pin resolved (unverified); required input of `_deploy-vercel.yml` | "Which Vercel CLI version should be pinned?" |
| S3 promotion | Origin-path switch to `releases/<sha>` (default, medium confidence) vs `sync --delete` to a live prefix | "Is a distribution config change per release acceptable?" |
| Static routing | Subpath pages on an S3 REST origin with OAC need a viewer rewrite (unverified) vs S3 website endpoint without OAC | "Do deep links such as /blog/post-1 need to work?" |
| Package manager | npm (no extra action), pnpm (needs `pnpm/action-setup`), Yarn (not templated here) | "npm or pnpm?" |
| Custom webpack config | `next build --webpack`, `--turbopack`, or migrate; Turbopack is the default and a webpack config fails the build | "Does the project or a plugin define `webpack`?" |
| Typecheck order | `next typegen` before `tsc` (medium confidence) | "Is `next-env.d.ts` committed?" |
| Vercel previews | Vercel Git integration for non-main branches (default) vs Actions previews that put the token in branch code | "Is there a preview-only credential?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Call `next lint` ([upgrade guide](https://nextjs.org/docs/app/guides/upgrading/version-16)) | `npm run lint` running `eslint .` |
| Rebuild for production with production `NEXT_PUBLIC_*` values ([environment variables](https://nextjs.org/docs/app/guides/environment-variables)) | Promote the artifact built once; per-environment values from server env or a fetched config |
| Put secrets in `NEXT_PUBLIC_*` or Docker build args ([with-docker README](https://github.com/vercel/next.js/blob/v16.4.3/examples/with-docker/README.md)) | Server-only variable passed at run time |
| Run `vercel deploy` without `--prebuilt` from Actions ([Vercel guide](https://vercel.com/kb/guide/how-can-i-use-github-actions-with-vercel)) | `vercel build` then `vercel deploy --prebuilt` |
| Leave Git-integration deploys on for the branch Actions deploys ([git configuration](https://vercel.com/docs/project-configuration/git-configuration)) | `deploymentEnabled: { "main": false }` |
| Put a deploy token or `id-token: write` in a pull_request job ([secure use](https://docs.github.com/en/actions/reference/security/secure-use)) | PR workflow with `contents: read`; previews from Vercel Git integration |
| Use long-lived AWS access keys for S3 and CloudFront ([OIDC reference](https://docs.github.com/en/actions/reference/security/oidc)) | `role-to-assume` on a job with `id-token: write` |
| Set `typescript.ignoreBuildErrors: true` without a `tsc` step ([TypeScript reference](https://nextjs.org/docs/app/api-reference/config/typescript)) | Keep the default and add `tsc --noEmit` |
| Run `corepack enable` on Node 26 ([Corepack README](https://github.com/nodejs/corepack#readme)) | `pnpm/action-setup` before `setup-node` |

Examples with alternatives: [never-do patterns](./blueprints/never-do-patterns.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| Static export output | `out/` with `output: 'export'` | https://nextjs.org/docs/app/guides/static-exports |
| Standalone output | `.next/standalone` plus `server.js`; `public` and `.next/static` not copied | https://nextjs.org/docs/app/api-reference/config/next-config-js/output |
| Turbopack build cache | on by default since 16.3.0, in `.next/cache/turbopack` | https://nextjs.org/docs/app/api-reference/config/next-config-js/turbopackFileSystemCache |
| Vercel build output | `.vercel/output` consumed by `deploy --prebuilt` | https://vercel.com/docs/cli/build |
| Invalidation cost | wildcard = one path; 1,000 paths free per month per account | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/PayingForInvalidation.html |
| Environments on private repos | secrets and variables need Pro/Team; reviewers need public or Enterprise | https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments |
| Reusable workflow location | the workflows folder, no subfolders | https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows |

## Verification Loop

Offline, run in the repository that received the generated files (representative, adapt to your environment).

```bash
grep -rn "next lint" package.json .github/workflows/                  # Expected: no output
grep -rn "uses: .*@v[0-9]" .github/workflows/ .github/actions/        # Expected: no output (all SHA-pinned)
grep -rn "VERCEL_TOKEN\|id-token: write" .github/workflows/ci-*.yml  # Expected: no output
grep -n "deploymentEnabled" vercel.json                               # Expected: a match when cd-web-vercel.yml exists
grep -n "output:" next.config.*                                       # Expected: 'export' or 'standalone' matching the mode
npm run lint && npx next typegen && npx tsc --noEmit && npx next build  # Expected: exit 0; out/ or .next/standalone exists
```

## External Resources

All fetched 2026-10-30.

- [Upgrading to Next.js 16](https://nextjs.org/docs/app/guides/upgrading/version-16)
- [Static exports](https://nextjs.org/docs/app/guides/static-exports)
- [How can I use GitHub Actions with Vercel](https://vercel.com/kb/guide/how-can-i-use-github-actions-with-vercel)
- [Full bibliography](./blueprints/unverified-and-risks.md#source-bibliography)
