# VALIDATE round 2 — packages/langchain4j — 2026-10-26 (written by orchestrator)
0 HIGH, 0 MEDIUM, 7 LOW. Round-1 HIGH/MEDIUM all fixed, no regressions.
Scores: core 99.0 · openai 98.5 · provider-a 99.5 · agent 99.5 · code rule 99.5 · config rule 100 · README 99.5 · apm.yml 100
LOW: L1 core register:46 "family-facts sources" not in bibliography; L2 registers name non-shipped research files ("gap research", quality score); L3 core SKILL.md:49 multi-claim; L4 openai Ask First rows 64-68 are notes; L5 agent 80-87 restates skill facts (Ask-First list, BOM version); L6 openai S2 must_pass states medium fact as fact; L7 README:41-42 packages/ path outside provenance.
Obs: code rule "OpenAI reasoning models" -> GPT-6, add top_logprobs.
