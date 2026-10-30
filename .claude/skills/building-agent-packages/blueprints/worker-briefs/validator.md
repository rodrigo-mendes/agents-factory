# Brief: validator / evaluator / auditor

Back to [README](README.md). One round of the P6 loop, three kinds of worker.

```
VALIDATE  quality-validator   spec: .claude/skills/skill-best-practices-validator/SKILL.md
  target: groups of <= 5 skills, then the package; rubric 100 - 6/HIGH - 2.5/MEDIUM - 0.5/LOW
TEST      skill-evaluator     spec: .claude/skills/evaluating-skill-scenarios/SKILL.md
  target: each skill's blueprints/evaluation-scenarios.md; load the skill's SKILL.md into your own
  context and judge it there (do NOT spawn agents)
AUDIT     architecture-auditor  spec: .claude/skills/audit-cc-architecture-consensus/SKILL.md
  target: the package source packages/<pkg>/.apm/ ; runs in parallel with VALIDATE and TEST;
  apply the scope, flow and engine lenses yourself in sequence (never spawn lens agents)
Common: Hard constraints block; read-only except one report file. Read the package SOURCE under
  packages/<pkg>/ only, never .claude/ (it may be mid-regeneration by a background apm install).
Return the report INLINE (findings with severity, file, evidence, fix hint) and also try to write
  <workspace>/execution-<N>/rounds/round-<k>/<kind>__<target>.md  (kind lowercase: validate|test|audit;
  target = skill name or `package`). If the write is refused, the orchestrator writes it verbatim.
```

The orchestrator never trusts a score without the findings list, and re-checks every HIGH against the file before it enters a fix brief (validators over-flag; see [known-failures](../known-failures.md)).
