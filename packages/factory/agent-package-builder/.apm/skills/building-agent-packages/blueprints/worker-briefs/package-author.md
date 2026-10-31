# Brief: package author (artifact-author)

Back to [README](README.md). Used in P5 for the agent, rules, structure skill, orchestrator-style skill and README.

```
Agent: artifact-author (one artifact per message, parallel allowed)
Spec: agent -> packages/factory/artifact-authoring/.apm/skills/agent-creator/SKILL.md (+ assets);
  rules -> .claude/rules/instructions-frontmatter conventions; skill -> skill-creator.
Inputs: the list of VERIFIED skills (names + one-line scope), family facts/rules, brief deliverables.
Approval line + Hard constraints: <paste from README>
Write to: packages/<package>/.apm/{agents,instructions,skills}/ ; apm.yml and README.md of the package.
Rules: agent description has "Use when"; tools minimal; executor agents are non-interactive and return
  questions instead of assuming; every skill name referenced must exist (scripts/verify_package.py).
Root apm.yml: add the package only if no other listed package already depends on it.
Done when: scripts/verify_package.py <package> exits 0.
```
