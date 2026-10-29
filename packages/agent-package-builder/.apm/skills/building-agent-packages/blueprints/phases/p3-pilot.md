# P3 Pilot

Back to [SKILL.md](../../SKILL.md).

Pick the unit with the most shared facts or the highest risk (core/foundation first).
1. Research ([researcher brief](../worker-briefs/researcher.md)) -> verify file exists.
2. Author ([skill author brief](../worker-briefs/skill-author-hybrid.md)) -> `scripts/verify_skill.py`.
3. One validate round on the pilot only ([validator brief](../worker-briefs/validator.md)).
4. Add the decisions the pilot revealed to `_family_rules` (each as a `decide` row) and fix `_family_facts` if a fact moved.
5. Measure tokens/time per stage (`state_event.py ... metric <stage> actual --tokens N --minutes M`); extrapolate to all units (`metric run estimate --tokens N`).

**Done when:** pilot VALIDATED with no HIGH. **Gate: G2** — show name, structure, score, findings, measured cost and total estimate; proceed only on an explicit yes. With the yes, the user fixes `token_budget` and `max_rounds`: write them in `PACKAGE_BRIEF.md` (the only edit allowed after G1) and `decide --gate G2 --who user --text "token_budget=<n>, max_rounds=<n>"`.
