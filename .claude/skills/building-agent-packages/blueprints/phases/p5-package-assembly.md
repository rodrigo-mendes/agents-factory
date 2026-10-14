# P5 Package assembly

Back to [SKILL.md](../../SKILL.md).

Parallel [package author briefs](../worker-briefs/package-author.md) for: agent, rules, structure skill, orchestrator-style skill, package README, package `apm.yml`.
Then the orchestrator: add the package to the root `apm.yml` only if no listed package depends on it; run `scripts/verify_package.py <package>`.

**Done when:** verify_package.py exits 0. **Gate:** none.
