# Decisions (short ADRs)

Written only by `scripts/state_event.py <slug> decide ...`. One row per domain or process decision;
`_family_rules.md` cites the ID instead of restating the reason. A user decision must also exist as
verbatim words in a gate file or the chat; this register is not an approval.

| Timestamp | ID | Gate | Who | Actor | Decision | Reason |
|---|---|---|---|---|---|---|
| 2026-10-29T21:05:52 | DEC-001 | none | user | migrate_state | intake: Stack | verbatim (legacy): "Plain LangChain4j (Recommended)" |
| 2026-10-29T21:05:52 | DEC-002 | none | user | migrate_state | intake: Scope | verbatim (legacy): "Chat + streaming" |
| 2026-10-29T21:05:52 | DEC-003 | none | user | migrate_state | intake: Agent | verbatim (legacy): "Executor, English (Recommended)" |
| 2026-10-29T21:05:52 | DEC-004 | none | user | migrate_state | intake: Research first, then review before design | verbatim (legacy): "2" (option: plan starts with research of core, OpenAI, Anthropic; skills only after user review) |
| 2026-10-29T21:05:52 | DEC-005 | none | user | migrate_state | review: Gap research round | verbatim (legacy): "Rodar mais uma rodada (Recomendado)" |
| 2026-10-29T21:05:52 | DEC-006 | none | user | migrate_state | review: open-ai-official beta module | verbatim (legacy): "Opção Ask-First" |
| 2026-10-29T21:05:52 | DEC-007 | none | user | migrate_state | rename: anthropic skill renamed (reserved word) | verbatim (legacy): "integrating-langchain4j-provider-a-v1-22" |
| 2026-10-29T21:05:52 | DEC-008 | none | user | migrate_state | apm-hash: user investigates apm cache (install failed: hash mismatch microsoft/apm autopilot-pr-merge-worker @280b8a7) | verbatim (legacy): "Eu investigo o cache" |
