# Decisions (short ADRs)

Written only by `scripts/state_event.py <slug> decide ...`. One row per domain or process decision;
`_family_rules.md` cites the ID instead of restating the reason. A user decision must also exist as
verbatim words in a gate file or the chat; this register is not an approval.

| Timestamp | ID | Gate | Who | Actor | Decision | Reason |
|---|---|---|---|---|---|---|
| 2026-10-31T23:11:10 | DEC-001 | none | user | orchestrator | Cucumber runtime: research both paths, decide at G2 | AskUserQuestion answer 2026-10-31: Research both, decide at G2 |
| 2026-10-31T23:11:10 | DEC-002 | none | user | orchestrator | Scope: OpenSpec->Gherkin, Cucumber+Quarkus, Integration tests, Gherkin authoring rules | AskUserQuestion answer 2026-10-31 |
| 2026-10-31T23:11:11 | DEC-003 | none | user | orchestrator | Agents: executor + read-only reviewer | AskUserQuestion answer: Executor + reviewer (Recommended) |
| 2026-10-31T23:11:11 | DEC-004 | none | user | orchestrator | Location: packages/quality/ family, 2 packages | AskUserQuestion answer: packages/quality/ (Recommended) |
| 2026-10-31T23:11:12 | DEC-005 | none | user | orchestrator | Research depth exhaustive | User rejected first plan: 'pesquisa exaustiva das skills e aprofundar mais no plano' |
| 2026-10-31T23:13:19 | DEC-006 | none | orchestrator | orchestrator | Root apm.yml lists only quarkus-acceptance-testing | acceptance-testing is transitive; double listing fails apm audit --ci |
| 2026-10-31T23:13:20 | DEC-007 | none | orchestrator | orchestrator | Pilot = U1 testing-quarkus-cucumber-v8-0 | highest risk and most shared facts |
| 2026-11-01T00:12:11 | DEC-008 | G2 | user | orchestrator | token_budget=4500000, max_rounds=5; path B default, A Ask-First | G2 answer |
| 2026-11-01T00:17:39 | DEC-009 | none | orchestrator | orchestrator | check_feature_coverage.py is stdlib-only (regex parse of spec.md and .feature); optional --strict uses gherkin-official 42.x if importable | plan: stdlib like poc_inventory.py; parser needs pip + Python>=3.10/3.11 |
| 2026-11-01T00:45:23 | DEC-010 | none | user | orchestrator | Run full apm install despite preflight BLOCK; the 27 pre-existing .claude files go in a separate commit 'chore(.claude): regenerate from packages' | user answer: Install + separate commit (Recommended); orchestrator check: 23 identical to source, 3 rules differ only by applyTo->paths, 1 stale |
