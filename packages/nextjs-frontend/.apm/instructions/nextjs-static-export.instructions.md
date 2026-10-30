---
name: nextjs-static-export
description: "Guardrails for a Next.js front end deployed as a static export to S3 + CloudFront: output 'export', no server features, unoptimized images, no secrets in NEXT_PUBLIC_*, only contract endpoints. Use when editing front-end code or next.config of a project that publishes out/."
applyTo: "**/frontend/**,**/next.config.*"
---

# Next.js static export guardrails

Scope: front ends built with `output: 'export'` and published from `out/` to S3 behind CloudFront
(factory decision, architecture ADR `static-export`). Facts come from the skill
`building-nextjs-github-actions-v16-4` (package `github-actions-cicd`; sources: Next.js static
exports guide, environment variables guide, read 2026-08-09 in that skill) and from the Vercel
skills in `vercel-frontend`. Tags `(unverified)` mark facts the loaded skills do not state. Nothing
here replaces the work-order or an accepted ADR; the stricter rule wins.

## Always Do
- Set `output: 'export'` in `next.config.*` and build to `out/` (`pnpm build`).
- Serve images with `images.unoptimized: true` (unverified: not in a loaded skill; the skill only states that `next/image` needs a custom loader) or a custom loader: default image optimization needs a
  server (skill: "next/image needs a custom loader").
- Call only the endpoints listed in `openspec/specs/architecture/contracts/*.md`, with their method,
  input and error codes.
- Treat every `NEXT_PUBLIC_*` value as public: it is inlined at build time and identical in every
  environment of one artifact; fetch per-environment values from a config the client loads at runtime.
- Handle 401 (return to login), 403 (no-permission view) and network errors on every call.
- Keep the build reproducible: `pnpm install --frozen-lockfile`, lint as its own step (`next lint` is
  gone in 16), then test and build.

## Ask First
- Browser login with Cognito (Hosted UI / OIDC PKCE): no skill covers it `(unverified)`; ask before choosing.
- Deep links on an S3 REST origin with OAC need a viewer rewrite or a different origin
  `(unverified)` in the skill; ask which behavior is acceptable.
- A dependency that needs a server or a Node runtime at request time.

## Never Do
- Use Server Actions, ISR, rewrites, Proxy or default image optimization: the skill names these as the
  features a static export cannot use. Alternative: call the contract's API from the client.
- Add route handlers, `next/headers` or `cookies()` for request-time server logic `(unverified: the
  loaded skills name Server Actions, ISR, rewrites, Proxy and image optimization; confirm the rest
  against the Static exports guide before relying on it)`. Alternative: the API Gateway endpoint of the contract.
- Put a secret, token or key in `NEXT_PUBLIC_*`, source or tests: it ships in static JavaScript.
  Alternative: keep it server-side in AWS (Secrets Manager) behind the API.
- Call endpoints that are not in the contract. Alternative: ask the manager for a contract delta.
- Deploy from the agent or the laptop (`aws`, `vercel`): the GitHub pipeline publishes the artifact.
