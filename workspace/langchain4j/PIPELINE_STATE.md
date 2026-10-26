# Pipeline state — langchain4j

```yaml
slug: langchain4j
mode: new
current_phase: P9
reconstructed: false
rounds: 3
```

## Approvals
| Gate | Date | Scope approved | User words |
|---|---|---|---|
| intake | 2026-10-26 | Stack | "Plain LangChain4j (Recommended)" |
| intake | 2026-10-26 | Scope | "Chat + streaming" |
| intake | 2026-10-26 | Agent | "Executor, English (Recommended)" |
| intake | 2026-10-26 | Research first, then review before design | "2" (option: plan starts with research of core, OpenAI, Anthropic; skills only after user review) |
| review | 2026-10-26 | Gap research round | "Rodar mais uma rodada (Recomendado)" |
| review | 2026-10-26 | open-ai-official beta module | "Opção Ask-First" |
| G1 | 2026-10-26 | v1.22.0; skills developing-langchain4j-core-v1-22, integrating-langchain4j-openai-v1-22, integrating-langchain4j-anthropic-v1-22; agent langchain4j-integrator; scoped rules; packages/langchain4j | "Aprovo assim" |
| G2 (pending) | 2026-10-26 | interpreted: 2 more validate+fix iterations on pilot before P4 | "fazer mais duas interacoes" |
| rename | 2026-10-26 | anthropic skill renamed (reserved word) | "integrating-langchain4j-provider-a-v1-22" |
| apm-hash | 2026-10-26 | user investigates apm cache (install failed: hash mismatch microsoft/apm autopilot-pr-merge-worker @280b8a7) | "Eu investigo o cache" |
| G2 | 2026-10-26 | fan-out P4 (openai, anthropic skills) then P5, P6 rounds=3 | "Sim, seguir" |
| G3 (pending) | 2026-10-26 | fix LOWs before commit | "Corrigir LOWs antes" |
| G3 (pending) | 2026-10-26 | revert .gitignore workspace/ line | "Reverter o .gitignore" |
| G3 | 2026-10-26 | restore lock + autopilot files to committed; commit langchain4j groups 1-4 without lock | "Restaurar e commitar sem lock (Recomendado)" |

## Version gate (P1)
| Framework | Version | Released | Status | Source |
|---|---|---|---|---|
| langchain4j | 1.22.0 | 2026-10-08 | Latest stable | https://github.com/langchain4j/langchain4j/releases (read 2026-10-26) |
| langchain4j-open-ai | 1.22.0 | 2026-10-08 | release | https://repo1.maven.org/maven2/dev/langchain4j/langchain4j-open-ai/maven-metadata.xml (read 2026-10-26) |
| langchain4j-anthropic | 1.22.0 | 2026-10-08 | release | https://repo1.maven.org/maven2/dev/langchain4j/langchain4j-anthropic/maven-metadata.xml (read 2026-10-26) |

## Units
| Unit | Source item | Skill name | Research file | State | Score | Tokens |
|---|---|---|---|---|---|---|
| core | LangChain4j 1.22.0 | developing-langchain4j-core-v1-22 | research_LangChain4j_core_v1.22.0.md | VALIDATED | 90.5 -> 90 -> 95 (3 iterations), 0 HIGH | | |
| openai | langchain4j-open-ai 1.22.0 | integrating-langchain4j-openai-v1-22 | research_LangChain4j_openai_v1.22.0.md | VERIFIED | | |
| anthropic | langchain4j-anthropic 1.22.0 | integrating-langchain4j-provider-a-v1-22 | research_LangChain4j_anthropic_v1.22.0.md | VERIFIED | | |

## Quality loop
| Round | Validate | Test | Audit | HIGH | Decision |
|---|---|---|---|---|---|
| 1 | core 99.5, openai 93.5, provider-a 98.5, agent 87, rules 96.5/99.5 | 12/12 | 7.7/10 | 3 | fix -> round 2 |
| 2 | core 99.0, openai 98.5, provider-a 99.5, agent 99.5, rules 99.5/100 | 12/12 | 9.6/10 | 0 | exit criteria met; 9 LOW -> G3 |

## Log
2026-10-26  P0  preflight OK, workspace created
2026-10-26  P1  version gate: 1.22.0 verified
2026-10-26  P1-research  launching 3 researchers
2026-10-26  P1-research  anthropic research file received
2026-10-26  P1-research  core research file received
2026-10-26  P1-research  openai research file received; stopped for user review
2026-10-26  gap-research  launching 1 researcher for unverified items
2026-10-26  gap-research  gaps file received (10/10 at least partly resolved)
2026-10-26  P2  family facts/rules written; G1 approved
2026-10-26  P3  pilot authoring core skill
2026-10-26  P3  core skill authored, verify_skill OK; F8 upgraded to High (orchestrator re-read HttpRequestLogger)
2026-10-26  P3  validate round on pilot
2026-10-26  P3  pilot validate 90.5 (0H/3M/4L); fix brief sent
2026-10-26  P3  fixes applied, verify_skill OK, no workspace ids left; pilot VALIDATED; P6 note: API-key cite should use stable open-ai page, not open-ai-official
2026-10-26  P3  user asked 2 more pilot iterations; iteration 2 validate
2026-10-26  P3  iteration 2 validate 90 (0H/3M/5L); fix brief sent
2026-10-26  P3  iteration 2 fixes applied; iteration 3 validate
2026-10-26  P3  iteration 3 validate 95 PASS (0H/1M/5L); final fix brief
2026-10-26  P3  iteration 3 fixes applied; awaiting G2
2026-10-26  P4  G2 approved; fan-out openai + anthropic
2026-10-26  P4  openai + provider-a skills authored, verify_skill OK on all 3; anthropic skill renamed per user
2026-10-26  P5  agent, 2 rules, README, apm.yml written; verify_package OK (3 skills, 1 agent, 2 rules); added to root apm.yml
2026-10-26  P6  apm install: langchain4j installed (3 skills, agent, 2 rules); microsoft/apm dep failed integration -> autopilot-* content drift (5 files) NOT ours, CRLF-only noise elsewhere; G3 must exclude
2026-10-26  P6  round 1 TEST 12/12 PASS (6 weak criteria)
2026-10-26  P6  round 1 VALIDATE: 2 HIGH (agent, confirmed), 3 MEDIUM; next AUDIT
2026-10-26  P6  round 1 AUDIT 7.7/10; HIGH total 3 (K1,K2,N1) all confirmed; FIX round 1
2026-10-26  P6  round 1 fixes applied; verify OK; reinstall for round 2
2026-10-26  P6  reinstall FAILED (content hash mismatch, microsoft/apm); .claude stale; waiting user
2026-10-26  P6  user: delete lock and regenerate (verbatim: "apagar o lock e gerara todas vez para testar"); backup in scratchpad
2026-10-26  P6  no-lock install refused (unmanaged-file conflicts); lock restored identical; cleared apm_modules/microsoft cache; reinstall
2026-10-26  P6  conflict was own unrecorded langchain4j outputs; removed them (regenerable) and reinstall
2026-10-26  P6  langchain4j regenerated OK in .claude (paths fixed); microsoft/apm dep still fails (git checkout dirty in apm_modules, likely CRLF) - external, flag G3; lock unchanged; round 2 start
2026-10-26  P6  round 2 TEST 12/12 PASS (5 weak, non-blocking)
2026-10-26  P6  round 2 VALIDATE 0H/0M/7L; next AUDIT
2026-10-26  P6  exit criteria met after round 2 (core 99.5->99.0 = new LOWs from deeper read, not a content regression)
2026-10-26  P8  CLAUDE.md counts updated; G3: user asked LOW fixes first + revert .gitignore (done)
2026-10-26  P8  LOW fixes applied, verify OK, .claude copies identical; full install succeeded but dropped microsoft/apm (88 files) -> restored lock + .claude/skills to committed per user; new lock saved in scratchpad
2026-10-26  P9  commit groups 1-4 (no lock); CI apm --frozen will fail until lock regenerated with langchain4j
