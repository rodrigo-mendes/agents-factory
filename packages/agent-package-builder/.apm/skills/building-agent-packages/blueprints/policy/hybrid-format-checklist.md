# Hybrid knowledge skill checklist

Back to [SKILL.md](../../SKILL.md). Template: `skill-creator/assets/TEMPLATE.KNOWLEDGE-SKILL.HYBRID.md`; schema: `.claude/rules/skill-structure.md`.

- Frontmatter: only `name` + `description`; description quoted, < 300 chars, contains "Use when"; name equals folder; version suffix `-vMAJOR-MINOR` when version-locked.
- SKILL.md 100-200 lines: Version Context table (Source column), Quick Navigation, Blueprints & Guardrails (✅ Always / ⚠️ Ask First / 🚫 Never), Quick Reference.
- Blueprints: `always-do-patterns.md`, `never-do-patterns.md`, topic blueprints, `unverified-and-risks.md`, `evaluation-scenarios.md` (>= 3-4 scenarios: canonical, edge, rejection, trap).
- Blueprint files <= 160 lines each; split by topic when longer.
- No absolute paths, no `.github/`, no relative dates ("2 weeks ago"), no BOM; links and anchors resolve.
- Run `scripts/verify_skill.py <dir>`: exit 0 required before a unit is VERIFIED.
