# Reusable build and composite setup

Back to [SKILL.md](../SKILL.md). Next.js 16.4.x; research date 2026-10-30. Commands are representative, adapt to your environment.

Contents: [Reusable workflow](#reusable-workflow) | [Composite action](#composite-action) | [Notes](#notes)

## Reusable workflow

File: `./.github/workflows/_node-build.yml`

No secrets, own minimal permissions, typed inputs and explicit outputs. Mode `vercel` runs checks only: the Vercel build needs the project settings pulled with a token, so it lives in [`_deploy-vercel.yml`](./workflow-deploy-vercel.md).

```yaml
# Representative — adapt to your environment. Next.js 16.4.x
name: _node-build
on:
  workflow_call:
    inputs:
      app-dir:         { type: string, default: ".", description: "Folder holding package.json" }
      mode:            { type: string, required: true, description: "static | standalone | vercel" }
      node-version:    { type: string, default: "24", description: "An LTS line, 20.9.0 or newer" }
      package-manager: { type: string, default: "npm", description: "npm | pnpm" }
      retention-days:  { type: number, default: 14 }
    outputs:
      artifact-name:
        description: Name of the uploaded build artifact (empty in mode vercel)
        value: ${{ jobs.build.outputs.artifact-name }}
      artifact-digest:
        description: Digest reported by upload-artifact (empty in mode vercel)
        value: ${{ jobs.build.outputs.artifact-digest }}
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    outputs:
      artifact-name: ${{ steps.meta.outputs.name }}
      artifact-digest: ${{ steps.upload.outputs.artifact-digest }}
    env:
      NEXT_TELEMETRY_DISABLED: "1"
      PM: ${{ inputs.package-manager }}
      MODE: ${{ inputs.mode }}
    defaults:
      run:
        working-directory: ${{ inputs.app-dir }}
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - id: meta
        working-directory: .
        run: echo "name=web-${MODE}-${GITHUB_SHA}" >> "$GITHUB_OUTPUT"
      - uses: ./.github/actions/build/setup-node-build
        with:
          node-version: ${{ inputs.node-version }}
          package-manager: ${{ inputs.package-manager }}
          app-dir: ${{ inputs.app-dir }}
      - run: ${PM} run lint            # package.json: "lint": "eslint ."
      - run: npx next typegen && npx tsc --noEmit    # typegen first (medium confidence)
      - run: ${PM} test                # remove if the project has no test script
      - if: inputs.mode != 'vercel'
        run: npx next build
      - if: inputs.mode == 'standalone'
        run: cp -r public .next/standalone/ && cp -r .next/static .next/standalone/.next/
      - id: upload
        if: inputs.mode != 'vercel'
        uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2
        with:
          name: ${{ steps.meta.outputs.name }}
          path: ${{ inputs.app-dir }}/${{ inputs.mode == 'static' && 'out' || '.next/standalone' }}
          retention-days: ${{ inputs.retention-days }}
          include-hidden-files: true    # standalone holds .next/ (input name unverified)
```

## Composite action

File: `./.github/actions/build/setup-node-build/action.yml`

Order matters: `pnpm/action-setup` runs before `setup-node` so `cache: pnpm` can find pnpm. The `privileged` input switches off every cache restore for jobs that hold credentials.

```yaml
# Representative — adapt to your environment
name: setup-node-build
description: Node, optional pnpm, dependency and .next/cache caches, install
inputs:
  node-version:    { description: "Node LTS line", required: true }
  package-manager: { description: "npm | pnpm", default: "npm" }
  app-dir:         { description: "Folder holding package.json", default: "." }
  privileged:      { description: "true when the job holds credentials", default: "false" }
runs:
  using: composite
  steps:
    - if: inputs.package-manager == 'pnpm'
      uses: pnpm/action-setup@ea17c68df8912ef543352723c149a84f56e3d413 # v6.1.0
      with:
        package_json_file: ${{ inputs.app-dir }}/package.json
    - if: inputs.privileged != 'true'
      uses: actions/setup-node@949feb2413d6458794dcd2491c4babbbce0c15c1 # v7.1.0
      with:
        node-version: ${{ inputs.node-version }}
        cache: ${{ inputs.package-manager }}
        cache-dependency-path: ${{ inputs.app-dir }}/${{ inputs.package-manager == 'pnpm' && 'pnpm-lock.yaml' || 'package-lock.json' }}
    - if: inputs.privileged == 'true'
      uses: actions/setup-node@949feb2413d6458794dcd2491c4babbbce0c15c1 # v7.1.0
      with:
        node-version: ${{ inputs.node-version }}
        package-manager-cache: false
    - if: inputs.privileged != 'true'
      uses: actions/cache@55cc8345863c7cc4c66a329aec7e433d2d1c52a9 # v6.1.0
      with:
        path: ${{ github.workspace }}/${{ inputs.app-dir }}/.next/cache
        key: ${{ runner.os }}-nextjs-${{ hashFiles('**/package-lock.json', '**/pnpm-lock.yaml') }}-${{ hashFiles('**/*.js', '**/*.jsx', '**/*.ts', '**/*.tsx') }}
        restore-keys: |
          ${{ runner.os }}-nextjs-${{ hashFiles('**/package-lock.json', '**/pnpm-lock.yaml') }}-
    - shell: bash
      working-directory: ${{ inputs.app-dir }}
      env:
        PM: ${{ inputs.package-manager }}
      run: |
        if [ "$PM" = "pnpm" ]; then pnpm install --frozen-lockfile; else npm ci; fi
```

## Notes

- The cache key layout comes from the official CI build caching guide, which uses the npm lockfile; adding `pnpm-lock.yaml` to the lockfile hash is a family decision.
- `pnpm install --frozen-lockfile` was not on a page read (unverified).
- The `actions/cache` major in the Next.js guide is older than the pin above; use only the pin.
- `include-hidden-files` is needed because `.next/` is a hidden folder inside the standalone bundle; whether v7.0.2 excludes hidden files by default and the input name are unverified.
- `artifact-digest` as an upload-artifact output name is unverified; if absent, the output stays empty and nothing else breaks.
- Node 26 has no Corepack, so the pnpm path never calls `corepack`.
- Two builds in one checkout in parallel are blocked by a Next.js lockfile; the workflow runs one build per job.
- A custom `webpack` config fails the Turbopack default build; add `--webpack` to the build step or migrate (see Ask First).
