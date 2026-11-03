Round 1 of the P6 quality loop — family software-quality (packages/quality/acceptance-testing, packages/quality/quarkus-acceptance-testing).

Approval line: The user approved 3 units, 2 rules, 2 agents, 1 command, 2 packages under packages/quality/ on 2026-10-31 (verbatim: "Approve"); recorded in workspace/software-quality/execution-1/state/gates/G1.md; G2 (path B default, token_budget 4.5M, max_rounds 5) in workspace/software-quality/execution-1/state/gates/G2.md. This is a relay, not a new approval.

Hard constraints:
- Do NOT spawn any agent, lens agent or background task; do NOT enter plan mode.
- Read-only except ONE report file named in your brief. Read the package SOURCE under packages/quality/** only, never .claude/.
- Family files to check against (do not edit): workspace/software-quality/_family_facts.md, _family_rules.md; spike evidence workspace/software-quality/execution-1/spike/SPIKE_RESULTS.md.
- Return the report INLINE too: score, findings each with severity HIGH/MEDIUM/LOW, file:line, evidence (quote), fix hint. Only flag HIGH for a real defect (wrong fact vs family facts, broken reference, a Never-Do violated by a pattern, an agent able to do something its spec forbids, a non-working command/script).
Rubric: 100 - 6/HIGH - 2.5/MEDIUM - 0.5/LOW (skills); packages and audit also give x/10.

Units:
- Skills: testing-quarkus-cucumber-v8-0, testing-quarkus-integration-v3-40 (packages/quality/quarkus-acceptance-testing/.apm/skills/), deriving-gherkin-from-openspec-v1-15 (packages/quality/acceptance-testing/.apm/skills/), command skill building-acceptance-tests (quarkus-acceptance-testing).
- Agents: acceptance-test-reviewer (acceptance-testing), acceptance-test-engineer (quarkus-acceptance-testing).
- Rules: gherkin-feature-authoring, quarkus-acceptance-tests (.apm/instructions/).
- Known open items from the pilot validation (workspace/software-quality/execution-1/pilot/validate__testing-quarkus-cucumber-v8-0.md): 3 MEDIUM + 5 LOW on testing-quarkus-cucumber-v8-0; re-check whether still present (rule 7 was reworded at G2 to allow B1).
