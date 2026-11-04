Fix cycle after round 1 (spec: packages/factory/agent-package-builder/.apm/skills/building-agent-packages/blueprints/worker-briefs/fix-cycle.md).

Approval line: The user approved 3 units, 2 rules, 2 agents, 1 command, 2 packages under packages/quality/ on 2026-10-31 (verbatim: "Approve"); recorded in workspace/software-quality/execution-1/state/gates/G1.md; G2 in .../gates/G2.md. This is a relay, not a new approval.

Hard constraints:
- Do NOT spawn agents or background tasks; no plan mode.
- Change ONLY what a listed finding names; edit only the files under your target folder. Never edit _family_* files or other packages.
- Keep: SKILL.md <= 200 lines, other files <= 160 lines; no absolute paths, no relative dates; tags exactly `(medium confidence)` / `(unverified)`; register header counts must equal the listed items after your edits.
- Family facts: workspace/software-quality/_family_facts.md (F2 Cucumber Java 17; F5 Quarkus/JUnit/Testcontainers; F11 tag convention; F13 RestAssured 6.0.1; F14 WireMock spike). Spike: workspace/software-quality/execution-1/spike/SPIKE_RESULTS.md (Surefire/Failsafe 3.5.4 used).
- Round reports with full findings: workspace/software-quality/execution-1/rounds/round-1/{validate__skills,validate__packages,test__skills,audit__package}.md and the pilot report workspace/software-quality/execution-1/pilot/validate__testing-quarkus-cucumber-v8-0.md.
Return: a list "finding -> what changed (file:line)"; anything you chose not to change and why.
