# Decisions (short ADRs)

Written only by `scripts/state_event.py <slug> decide ...`. One row per domain or process decision;
`_family_rules.md` cites the ID instead of restating the reason. A user decision must also exist as
verbatim words in a gate file or the chat; this register is not an approval.

| Timestamp | ID | Gate | Who | Actor | Decision | Reason |
|---|---|---|---|---|---|---|
| 2026-10-29T21:05:59 | DEC-001 | none | user | migrate_state | pre-G1: Quarkus line | verbatim (legacy): "3.40 LTS (Recommended)" |
| 2026-10-29T21:05:59 | DEC-002 | none | user | migrate_state | pre-G1: IaC | verbatim (legacy): "Terraform (Recommended)" |
| 2026-10-29T21:05:59 | DEC-003 | none | user | migrate_state | pre-G1: Frontend | verbatim (legacy): "Map existing CDN skills" |
| 2026-10-29T21:05:59 | DEC-004 | none | user | migrate_state | pre-G1: Deliverables | verbatim (legacy): "Skills + map + agent + rules (Recommended)" |
| 2026-10-29T21:05:59 | DEC-005 | none | user | migrate_state | pre-G1: LLM providers | verbatim (legacy): "OpenAI + Anthropic + Bedrock (Recommended)" |
| 2026-10-29T21:05:59 | DEC-006 | none | user | migrate_state | pre-G1: Agents | verbatim (legacy): "Inline orchestrator skill, quarkus-lambda-integrator, aws-lambda-deployer, aws-lambda-debugger, para el interview hacer uso de SDD ( spec driven developtment), proponer skills, o r |
| 2026-10-29T21:05:59 | DEC-007 | none | user | migrate_state | pre-G1: Handoff design | verbatim (legacy): "Skill + scripts + sync agent (Recommended)" |
| 2026-10-29T21:05:59 | DEC-008 | none | user | migrate_state | pre-G1: Sync triggers | verbatim (legacy): "At every handoff step, Before archive/commit (gate), On demand command, Claude Code hook" |
| 2026-10-29T21:05:59 | DEC-009 | none | user | migrate_state | plan: Plan comments (verbatim) | verbatim (legacy): "adicionad como integrag stripe com quarkus e tambem com integrar langchain4j"; "me ajudara a propor agentes, para a execuçc>ao do desenvolvimento utilizando aws + quarkus"; "extare |
| 2026-10-29T21:05:59 | DEC-010 | none | user | migrate_state | plan: Plan approved | verbatim (legacy): ExitPlanMode approved by the user |
| 2026-10-29T21:05:59 | DEC-011 | none | user | migrate_state | P5: Record file names (subagent write guard blocks report*) | verbatim (legacy): "result-NN-<role>.md (Recommended)" |
| 2026-10-29T21:05:59 | DEC-012 | none | user | migrate_state | P5: OCI record names | verbatim (legacy): "Rename OCI too" |
| 2026-10-29T21:05:59 | DEC-013 | none | user | migrate_state | P5: Phase gating | verbatim (legacy): "wait for my aprroval, before next phase" (no phase transition without an explicit user OK) |
| 2026-10-29T21:06:00 | DEC-014 | none | user | migrate_state | P6: Start P6 quality loop | verbatim (legacy): "continue" |
| 2026-10-29T21:06:00 | DEC-015 | none | user | migrate_state | P6-extend: quality loop rounds 4 and 5 (P7/P8 still wait for approval) | verbatim (legacy): "do more 2 rounds of quality loop" |
| 2026-10-29T21:06:00 | DEC-016 | none | user | migrate_state | P6-extend-2: after round 5: 2 more rounds (6, 7) scoped to validation groups D and E | verbatim (legacy): "do 2 more round after in groups D and E, after round 5" |
| 2026-10-29T21:06:00 | DEC-017 | none | user | migrate_state | P6-r5-high: fix the HIGHs of round-5 groups A, B, C (incl. the validate-observability.sh default, previously docs-only) | verbatim (legacy): "from groups a, b, c, fix the high too" |
| 2026-10-29T21:06:00 | DEC-018 | none | user | migrate_state | P6-r67-scope: rounds 6-7: fix HIGH findings from all groups A-E (validation still focused on D+E, plus a HIGH-only check of A-C) | verbatim (legacy): "in round 6 and 7, fix high from all groups" |
| 2026-10-29T21:06:00 | DEC-019 | none | user | migrate_state | P6-add: add U8 integrating-quarkus-langchain4j-v1-15 to the pipeline (was deferred at G1) and convert all `.sh` scripts to Python | verbatim (legacy): "adding on pipeline, integrating-quarkus-langchain4j-v1-15 and convert all `.sh`into python scripts" |
| 2026-10-29T21:06:00 | DEC-020 | none | user | migrate_state | P6-add-U8: U8 locks to quarkus-langchain4j 1.15.0.CR1 (Quarkus 3.40.0, LangChain4j 1.21.0; no 1.15.0 final on Central 2026-10-28), every fact flagged pre-release | verbatim (legacy): "1.15.0.CR1, flagged (Recommended)" |
| 2026-10-29T21:06:00 | DEC-021 | none | user | migrate_state | P6-add-py: convert all 27 .sh in packages/ to Python (incl. OCI packages and the scaffolding-oci-function asset) | verbatim (legacy): "All 27 in packages/" |
| 2026-10-29T21:06:00 | DEC-022 | none | user | migrate_state | P6-cleanup: oci-cleanup.py: empty identity filters (OCI_COMPARTMENT_NAME / OCID / project filter) match nothing instead of every tenancy policy (deliberate behaviour change vs bash) | verbatim (legacy): "Skip empty filters (Recommended)" |
| 2026-10-29T21:06:00 | DEC-023 | none | user | migrate_state | P6-oci-M1: OCI forked agents: AWS-style approval relay (stop at plan with sha256, relaunch with approve=tfplan sha256=...) | verbatim (legacy): "AWS-style relay (Recommended)" |
| 2026-10-29T21:06:00 | DEC-024 | none | user | migrate_state | P6-oci-M2: oci-serverless-stack user-mediated per-stream hand-offs + --integrate | verbatim (legacy): "User-mediated (Recommended)" |
| 2026-10-29T21:06:00 | DEC-025 | none | user | migrate_state | P7-P8: proceed to P7 (fact sweep) and P8 (mechanical close), then stop at G3 | verbatim (legacy): "Proceed to P7 + P8 (Recommended)" |
