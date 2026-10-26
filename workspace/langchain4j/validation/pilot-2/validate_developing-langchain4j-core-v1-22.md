# Validate iteration 2 — developing-langchain4j-core-v1-22 — 2026-10-26
Written by orchestrator from inline report. Score 90/100 — 0 HIGH, 3 MEDIUM, 5 LOW.
- M-1 API-key claim cites beta open-ai-official page (SKILL.md:52,74; always-do:73; never-do:62; register:113) -> stable open-ai page.
- M-2 error sample catches only NonRetriable/Retriable; InvalidRequestException class is U7 -> add tagged catch / scope note.
- M-3 evaluation scenarios: S1 key assertion untestable, S1 CompletableFuture prescriptive, S3 "routes nothing" ambiguous + gpt-6 temperature uncovered, S2 judge substance not tag text.
- L-1 SKILL.md 99 lines (info). L-2 L2 + "(medium confidence, absence of evidence)" unmapped. L-3 garbled errors-and-retry:14. L-4 undeclared chatRequest streaming:12. L-5 logRequests correct form as code.
