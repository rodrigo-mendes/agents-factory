# vercel-frontend

A package that only points to Vercel's official agent skills for front-end work. The skill list comes from
<https://vercel.com/docs/agent-resources/skills> (page last updated 2026-09-15). The package copies no skill
content. Every entry in [`apm.yml`](apm.yml) points to a whole GitHub repository, pinned to a commit SHA, and
`apm install` copies all the skills that repository publishes into `.claude/skills/`.

## Repositories (SHAs resolved 2026-10-29)

| Repository | SHA | License | Skills installed |
|---|---|---|---|
| vercel-labs/agent-skills | `1a2c79d4` | none declared | react-best-practices, composition-patterns, web-design-guidelines, react-native-skills, react-view-transitions, deploy-to-vercel, vercel-cli-with-tokens, vercel-optimize, writing-guidelines |
| vercel/next.js | `4c6a3fa4` | MIT | next-dev-loop, next-cache-components-adoption, next-cache-components-optimizer, next-bundle-optimizer, next-partial-prefetching-adoption, next-partial-prefetching-optimizer |
| vercel/ai-elements | `ca8be600` | Apache-2.0 | ai-elements |
| vercel/streamdown | `7dcabc64` | Apache-2.0 | streamdown |
| vercel/components.build | `ba727450` | Apache-2.0 | building-components |
| vercel/turborepo | `e158e859` | MIT | turborepo |
| vercel-labs/agent-browser | `1453dd37` | Apache-2.0 | agent-browser |

Root install result (2026-10-29): 20 skills installed, none with the same name as an existing factory skill. Full SHAs and paths are in
`workspace/vercel-frontend/provenance.md`.

## Left out

- **vercel/ai** (use-ai-sdk, migrate-ai-sdk-v6-to-v7). On Windows its checkout aborts with `local changes would be
  overwritten` (`packages/tool-bash/*`, `tool-web-fetch/*`), even from a clean cache. The entry is commented out in `apm.yml`.
- **json-render-react, cra-to-next-migration, before-and-after.** These three can only be installed from a
  subfolder (`path:`), and with APM 0.35.0 on Windows that fails with `Unable to prepare Git clone
  configuration probe`. Installing the whole json-render repository would work, but it brings in its own
  `skill-creator`, which would overwrite the factory's. before-and-after also uses the PolyForm Shield
  license, which is not an open source license.

## Prerequisites and costs

- **Windows long paths.** On Windows, run `git config --global core.longpaths true` first. Without it, next.js
  fails with `Filename too long`. To revert: `git config --global --unset core.longpaths`.
- **Install time.** A first install takes about 25-40 minutes, almost all of it cloning next.js.
- **Network.** `apm install` needs network access to GitHub.

## Exceptions to the factory rules

Upstream skills are not changed here. Their deviations from the factory's rules (gerund-noun names, no version
suffix, `SKILL.md` files over 500 lines) are accepted as they are.

## Updating

1. Pick the new SHA: `gh api repos/<owner>/<repo>/commits/<branch> --jq .sha`.
2. Change `ref:` in `apm.yml`.
3. Test the install in an isolated folder, `workspace/vercel-frontend/execution-N/`.
4. Run `apm install --target claude` at the repo root, then `scripts/restore-rule-metadata.py` and
   `scripts/fix-cross-package-links.py`.
