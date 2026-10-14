# Brief: skill author (artifact-author)

Back to [README](README.md).

```
Agent: artifact-author (batches of <= 4 in one message)
Spec: follow packages/artifact-authoring/.apm/skills/skill-creator/SKILL.md and the hybrid template
  packages/artifact-authoring/.apm/skills/skill-creator/assets/TEMPLATE.KNOWLEDGE-SKILL.HYBRID.md
Input: <workspace>/research_<...>.md ; facts: _family_facts_<ver>.md ; rules: _family_rules_<ver>.md
Skill name: <name>-v<MAJOR>-<MINOR>
Approval line: <exact form from README>   Hard constraints: <paste block>
Write to: packages/<package>/.apm/skills/<name>/   (NOT .claude/skills/; .claude/ is generated)
Format: hybrid knowledge skill; checklist in blueprints/policy/hybrid-format-checklist.md;
  evidence rule in blueprints/policy/evidence-rule.md.
Done when: scripts/verify_skill.py <dir> exits 0 (run it yourself if you have Bash, else the
  orchestrator runs it) and the register header counts equal the listed items.
```

Orchestrator then: run `scripts/verify_skill.py`, set unit to VERIFIED or send ONE fix brief with the script output.
