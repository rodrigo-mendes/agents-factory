# Standalone container hand-off

Back to [SKILL.md](../SKILL.md). Next.js 16.4.3 `output: 'standalone'`; research date 2026-10-30. Image build, push by digest and promotion belong to `publishing-container-images-github-actions`; this blueprint covers only the Next.js side.

## Configuration and output

`output: 'standalone'` creates `.next/standalone`, deployable without installing `node_modules`, with a minimal `server.js`. That server does not copy `public` or `.next/static`, so copy them in or serve them from a CDN. `PORT` and `HOSTNAME` configure the listener. In a monorepo the build needs `outputFileTracingRoot`, and missing files are added with `outputFileTracingIncludes`.

`_node-build.yml` with `mode: standalone` already copies `public` and `.next/static` into `.next/standalone` and uploads it ([build blueprint](./workflow-node-build.md)). Use it when the image is built from a ready bundle; otherwise build inside the image with the official example.

## Runner stage from the official example (tag v16.4.3)

The example has stages `dependencies`, `builder` and `runner`. Its `ARG NODE_VERSION=24.13.0-slim` is older than the 24 line in the Version Context; set it from a current LTS tag.

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

## Runtime values

- The example README says never pass secrets as build arguments, and its `.dockerignore` excludes `.env`.
- `NEXT_PUBLIC_*` values are frozen in the image at build time. One image promoted through environments needs server values read at request time after `await connection()`, supplied as container environment at run time.

```tsx
// Next.js 16.4 server component: read at request time in each environment
import { connection } from 'next/server'
export default async function Page() {
  await connection()
  return <p>{process.env.API_BASE_URL}</p>
}
```

## Caller sketch

```yaml
# Representative — adapt to your environment
jobs:
  build:
    uses: ./.github/workflows/_node-build.yml
    with: { mode: standalone, retention-days: 7 }
  image:
    needs: build
    # Hand-off: image build, push by digest, promotion, tags -> publishing-container-images-github-actions
    # Pass the bundle with the optional `artifact-name` input of _image-publish.yml
    uses: ./.github/workflows/_image-publish.yml
    with:
      artifact-name: ${{ needs.build.outputs.artifact-name }}
      # other inputs exactly as publishing-container-images-github-actions defines them
```

## Checks

- `grep -n "output:" next.config.*` shows `'standalone'`.
- The image runs as `USER node`; the Dockerfile has no `ARG` or `ENV` holding a secret.
- Image deploys follow family rule build once, promote the digest: never rebuild per environment.
