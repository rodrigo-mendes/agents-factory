# P2 Inventory and design

Back to [SKILL.md](../../SKILL.md).

1. Needs -> map each to candidate frameworks/extensions with an official source; no source = declared gap.
2. Build the go/no-go table: unit, source item, official docs URL, skill name (`<gerund>-<noun>-v<MAJOR>-<MINOR>`), research worker, scope boundary, overlap notes.
3. Design the package: skills, structure skill, orchestrator-style skill, agent kind, rules (+globs; two rules may share a glob only on purpose), package slug, root apm.yml rule (transitive dependencies are not listed twice).
4. Seed `_family_facts` (facts used by >= 2 units, verified by YOU against official pages) and `_family_rules` (from [policy](../policy/evidence-rule.md) plus domain decisions).
5. Legacy source (if any): read-only inventory of what to migrate and what to drop.

**Done when:** table + design + family files written. **Gate: G1** (scope, version, units, names) via the question tool; record the verbatim answer.
