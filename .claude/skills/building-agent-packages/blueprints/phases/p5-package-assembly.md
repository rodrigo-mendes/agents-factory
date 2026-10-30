# P5 Package assembly

Back to [SKILL.md](../../SKILL.md).

Parallel [package author briefs](../worker-briefs/package-author.md) for: agent, rules, structure skill, orchestrator-style skill, package README, package `apm.yml`.
Then the orchestrator: add the package to the root `apm.yml` only if no listed package depends on it, under `shared-lock` + `touch apm.yml` ([shared files](../policy/shared-files.md)); run `scripts/verify_package.py packages/<package>`.

Install rehearsal (scoped, seconds): `scripts/scoped_install.py --package <pkg> --slug <slug>`. It installs ONLY this package and its local dependencies into the throwaway `workspace/.sbx`, checks that every deployed skill, agent and rule equals the source and that no deployed path reaches the Windows 260-character limit, logs the result and deletes the sandbox. It never touches the root `apm.yml`, the lock or `.claude/`, so it needs no `shared-lock`. Fix any mismatch before P6. Also run `scripts/preflight_apm.py --slug <slug>` now, while there is time to fix what it finds for the full install in P8 (CRLF-only copies, a duplicated root entry, another run's files).

Do NOT run the full root `apm install` in P5: it takes 12-40 min on Windows and, when a remote dependency fails, deletes committed `.claude/` files and drops other packages from the lock (seen in the github-actions-cicd run, 2026-10-30; recovery in [known failures](../known-failures.md)). The full install happens once, in P8.

**Done when:** verify_package.py and scoped_install.py exit 0; P6 starts right away and tests the source ([P6](p6-quality-loop.md)). **Gate:** none.
