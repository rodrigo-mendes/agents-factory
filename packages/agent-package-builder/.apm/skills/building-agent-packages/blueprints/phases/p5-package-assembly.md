# P5 Package assembly

Back to [SKILL.md](../../SKILL.md).

Parallel [package author briefs](../worker-briefs/package-author.md) for: agent, rules, structure skill, orchestrator-style skill, package README, package `apm.yml`.
Then the orchestrator: add the package to the root `apm.yml` only if no listed package depends on it, under `shared-lock` + `touch apm.yml` ([shared files](../policy/shared-files.md)); run `scripts/verify_package.py packages/<package>`.

Install rehearsal: `scripts/preflight_apm.py --slug <slug>` now, while there is time to fix what it finds (CRLF-only copies, a duplicated root entry, another run's files). Run `apm install --target claude` here only if it passes, followed by `scripts/after_install.py --package <pkg>`; otherwise log the BLOCK as `event P5 INCIDENT` and resolve it before P8. Release with `shared-unlock` after the rehearsal.

**Done when:** verify_package.py exits 0. **Gate:** none.
