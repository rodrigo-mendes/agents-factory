Approval line: The user approved 3 units, 2 rules, 2 agents (acceptance-test-engineer executor, acceptance-test-reviewer read-only), 1 command (/building-acceptance-tests), 2 packages under packages/quality/ on 2026-10-31 (verbatim: "Approve"); recorded in workspace/software-quality/execution-1/state/gates/G1.md; G2 (path B default: Cucumber 8 inside @QuarkusIntegrationTest; quarkus-cucumber Ask-First) in workspace/software-quality/execution-1/state/gates/G2.md. This is a relay, not a new approval.

Hard constraints:
- Do NOT spawn any agent or background task; do NOT enter plan mode or wait for a gate.
- Write only the files listed under "Write to". Report paths and anything unverified.
- Apply workspace/software-quality/_family_facts.md and _family_rules.md; do not edit them. Read the VERIFIED skills listed in your brief and state no technical fact that is not in them: reference the skill by name instead.
- Never make a shipped artifact READ workspace/; installed skills are referenced as .claude/skills/<skill>/...
- Do not edit shared files (root apm.yml, apm.lock.yaml, CLAUDE.md, docs/, other packages, the existing skills).

Specs:
- Agent: packages/factory/artifact-authoring/.apm/skills/agent-creator/SKILL.md (+ its assets). Frontmatter: name, description (">" block; non-interactive; returns numbered questions; "Use when ... (e.g. ...)"), tools (minimal), model: sonnet. Body: inputs, workflow steps, skills to load (by name), Always / Ask First / Never, output record format, stop conditions.
- Rules: .claude/rules/rules-frontmatter.md conventions; written as .apm/instructions/<name>.instructions.md with frontmatter name, description ("... Use when ..."), applyTo (comma-separated globs).
- Command skill: mirror packages/cloud/terraform/terraform/.apm/skills/provision-aws-terraform/ (frontmatter name, description, argument-hint, context: fork, agent: <agent>, disable-model-invocation: true; plus blueprints/evaluation-scenarios.md with >= 3 scenarios).
- Reference packages to mirror (apm.yml shape, README sections, agent/rule style): packages/java/libs/langchain4j/ and packages/delivery/specs/openspec-poc/.

Done when: the orchestrator runs verify_package.py on the package and it exits 0 (you have no Bash).
