# Author brief — aws-terraform unit (P4 fan-out)

Approval relay (PIPELINE_STATE.md#approvals): G1 "26 skills, uma por serviço"; G2 "Aprovar fan-out completo (Recomendado)" / "Manter `-v6` (Recomendado)".

## Hard rules
- Do not spawn agents, do not use plan mode. Write only under `c:\agents\agents-factory\packages\aws-terraform\.apm\skills\provisioning-aws-<unit>-v6\`. Never write into `.claude/`, never edit `apm.yml`/`README.md` (the orchestrator does).
- **Grounding rule: every sentence of a ✅/🚫 bullet, Ask First row and Quick Reference row must be stated in the unit research or in the family facts. If it is not, REMOVE it — do not paraphrase from memory and do not soften it with a tag unless it genuinely matters; never state an unsourced claim as fact. Line counts: do not estimate, count with the Read tool line numbers.**
- **Never Do rule: a 🚫 row (SKILL.md, blueprint entry and hub row) must be a High-confidence, sourced fact. NEVER make a Never row out of (a) absence of evidence ("the docs don't mention X", research "unsupported" / "legacy claim wrong" items), (b) a medium-confidence or (unverified) item, (c) a best-practice inference. Those go to Ask First or a blueprint note, tagged. Never rows must equal blueprint WRONG entries one-to-one.**
- **Always Do bullets contain only High-confidence claims — no (medium confidence)/(unverified) tags inside them (move those to Ask First).**
- **Do not state a Security Hub default or an AWS quota as a rule ("90-day ceiling") — say what the control/page says.**
- **Never cite F#/M# ids or workspace paths in shipped text; cite URLs. Mark every example value (names, ARNs, TTLs, emails) `# example`. Cite each statement to the page that states it (provider page vs Terraform docs vs AWS docs).**
- The ONLY technical sources: the unit research file + `c:\agents\agents-factory\workspace\aws-terraform\_family_facts_v6.md`. No facts from memory; anything else is `(unverified)` and registered.

## Template — mirror EXACTLY
The validated pilot `c:\agents\agents-factory\packages\aws-terraform\.apm\skills\provisioning-aws-vpc-v6\` (read SKILL.md and every blueprint first). Same frontmatter shape (knowledge skill: only `name` + quoted `description`), same SKILL.md sections (Version Context, version-lock note "-v6 = 6.x major line, reference patch from the unit research (6.69.0/6.70.0), Terraform ~> 1.16; mention 1.17.0 stable (2026-10-21) under Version-lifetime risk, v7 = new skill", Quick Navigation, Blueprints & Guardrails ✅/⚠️ table/🚫 ❌✅ table, Quick Reference with FULL URLs, "5.x → 6.x Migration (<Service>)", External Resources).

Blueprints:
- `always-do-patterns.md` and `never-do-patterns.md` are **index hubs** (table → topic file#anchor), exactly like the pilot.
- Topic files `always-do-<topic>.md` / `never-do-<topic>.md` hold the HCL (complete, idiomatic, each section cites its URL). Use as many topic files as needed; split only when a file would exceed 160 lines. Small services may need just one topic file each.
- `unverified-and-risks.md`: Version-lifetime risk, Unverified Items (U#), Medium-Confidence Items (M#), Coverage Limits (L#), Tag to register mapping (every tag in the skill → U#/M#, with real file + section), Source Bibliography.
- `evaluation-scenarios.md`: ≥ 4 scenarios (canonical, edge, misuse rejection, anti-pattern trap) in the pilot's JSON format with `success_criteria: {must_pass, must_not}`.

## Limits (checked by script `verify_skill.py`)
- `description` < 300 chars: what + "Use when…" + short "Not for…" (name sibling skills).
- SKILL.md < 500 lines (target 120–150); every blueprint ≤ 160 lines; every link and #anchor must resolve (GitHub-style anchors).
- Tags in plain parentheses: `(unverified)`, `(medium confidence)`. No bold, no `[UNVERIFIED]`.

## Report back (short)
Files + line counts, ungrounded facts (tagged), anything ambiguous.
