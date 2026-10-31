# VALIDATE round 1 — packages/langchain4j — 2026-10-26 (written by orchestrator)
Scores: core 99.5 (0/0/1) · openai 93.5 (0/2/3) · provider-a 98.5 (0/0/3) · agent 87 (2/0/1) · code rule 96.5 (0/1/2) · config rule 99.5 (0/0/1) · README 100 · apm.yml 100
HIGH (re-checked by orchestrator against files: CONFIRMED)
- H1 agent:68 reads workspace/langchain4j/_family_rules_v1.22.md (does not ship) -> delete step, rely on Family checks / shipped rules.
- H2 agent:50,63 skills path packages/langchain4j/.apm/skills/... -> .claude/skills/<name>/SKILL.md (as camel-quarkus-integrator).
MEDIUM
- M1 openai Never Do #5 tools (out of scope, comment-only pair) -> drop / Ask-First only.
- M2 openai SKILL.md:63 vs :77 Sol contradiction (medium vs High).
- M3 code rule:62-63 maxTokens Never over-generalizes (U4 unverified) -> soften, limit to GPT-6.
LOW: agent:148 ".claude/" edit ambiguity; openai QR "page not recorded" (88,94), multi-claim bullet 51, verify row 95; provider-a Never #4 no source (75), multi-claim 53, non-decision Ask-First rows 65-67; core multi-claim 49 (leave); code rule glob noise, line 12 workspace cite; config rule glob.
