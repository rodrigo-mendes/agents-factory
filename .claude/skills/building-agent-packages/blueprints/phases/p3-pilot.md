# P3 Pilot

Back to [SKILL.md](../../SKILL.md).

Pick the unit with the most shared facts or the highest risk (core/foundation first).
1. Research ([researcher brief](../worker-briefs/researcher.md)) -> verify file exists.
2. Author ([skill author brief](../worker-briefs/skill-author-hybrid.md)) -> `scripts/verify_skill.py`.
3. One validate round on the pilot only ([validator brief](../worker-briefs/validator.md)).
4. Add the decisions the pilot revealed to `_family_rules` and fix `_family_facts` if a fact moved.
5. Measure tokens/time per stage; extrapolate to all units.

**Done when:** pilot VALIDATED with no HIGH. **Gate: G2** — show name, structure, score, findings, measured cost and total estimate; proceed only on an explicit yes.
