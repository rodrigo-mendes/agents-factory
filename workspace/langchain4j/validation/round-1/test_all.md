# TEST round 1 — 2026-10-26 (skill-evaluator, self-simulation, written by orchestrator)
12/12 PASS (core 4/4, openai 4/4, provider-a 4/4); no must_not violations.
Weak criteria (fix candidates):
1. provider-a S2 effort criterion not triggered by query -> add effort question.
2. core S3 "no skill other than OpenAI sibling" conflicts with SKILL.md naming both siblings -> reword.
3. core S1 "matching provider sibling" ambiguous (query names no provider).
4. core S4 "extra retries multiply" is inference.
5. provider-a S4 must_not literal key -> constrain to corrected builder.
6. openai S2 "asks which endpoint" -> state NEEDS-INPUT acceptable.
