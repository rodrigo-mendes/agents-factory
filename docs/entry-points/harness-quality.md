# Quality and audit commands

These commands check artifacts: an agent project's architecture, skills, rules, and how skills
behave when you run them. They write a report. The validators also have a `--fix` mode that edits
files; it is not listed in their argument hints (see the [validating manual](../../packages/harness-quality/validating/README.md)).

## Architecture audits

Two families exist. Use `audit-architecture-*` for a **GitHub Copilot** project and
`audit-cc-architecture-*` for a **Claude Code** project. Both have three lenses (scope, flow, engine) and a consensus command that runs all three.

| Lens | What it checks | Copilot command | Claude Code command |
|---|---|---|---|
| Scope | The scope hierarchy: what each piece is responsible for. | [`/audit-architecture-scope`](../../packages/harness-quality/auditing/README.md#audit-architecture-scope) | [`/audit-cc-architecture-scope`](../../packages/harness-quality/auditing/README.md#audit-cc-architecture-scope) |
| Flow | The invocation flow: how work reaches each piece. | [`/audit-architecture-flow`](../../packages/harness-quality/auditing/README.md#audit-architecture-flow) | [`/audit-cc-architecture-flow`](../../packages/harness-quality/auditing/README.md#audit-cc-architecture-flow) |
| Engine | The engine mechanics: how triggers and tools behave. | [`/audit-architecture-engine`](../../packages/harness-quality/auditing/README.md#audit-architecture-engine) | [`/audit-cc-architecture-engine`](../../packages/harness-quality/auditing/README.md#audit-cc-architecture-engine) |
| Consensus | All three lenses, run in parallel and merged. | [`/audit-architecture-consensus`](../../packages/harness-quality/auditing/README.md#audit-architecture-consensus) | [`/audit-cc-architecture-consensus`](../../packages/harness-quality/auditing/README.md#audit-cc-architecture-consensus) |

The argument is the agent or subagent name to audit, or the path to a project directory.

```
/audit-cc-architecture-consensus .claude/
/audit-cc-architecture-consensus framework-researcher
```

Use **consensus** when you want one prioritized report. Use a single lens when you want to look at
one concern.

> The Copilot audits are generic tools for auditing other projects that target Copilot. This
> repository is Claude Code only.

## Validators

| Command | Checks | Argument |
|---|---|---|
| [`/skill-best-practices-validator`](../../packages/harness-quality/validating/README.md#skill-best-practices-validator) | Skills against the skill conventions. | Directory of skills, for example `.claude/skills/`. |
| [`/instructions-best-practices-validator`](../../packages/harness-quality/validating/README.md#instructions-best-practices-validator) | Rules and instructions. | Directory of rules. |
| [`/agent-router-pattern-validator`](../../packages/harness-quality/validating/README.md#agent-router-pattern-validator) | Command-to-subagent routing. | Project directory, for example `.claude/`. |
| [`/project-analysis-validator`](../../packages/harness-quality/validating/README.md#project-analysis-validator) | Structure and quality of a whole agent project. | Root directory, for example `.claude/`. |
| [`/copilot-compatibility-review`](../../packages/harness-quality/validating/README.md#copilot-compatibility-review) | Copilot compatibility of a Copilot assets directory. | Copilot assets path. |

Start with the project-level validator when you want the big picture, and with the skill or rule
validator when you are fixing one artifact.

```
/project-analysis-validator .claude/
/skill-best-practices-validator .claude/skills/
```

## Behavior evaluation

`/evaluating-skill-scenarios <skill-name>` runs the scenarios written in the skill's
`evaluation-scenarios.md`. It sends each query to the skill and judges the answer against the
must-pass and must-not criteria. Use it after you change a skill's behavior, not just its text.

```
/evaluating-skill-scenarios cloud-architecture-researcher
```

## Common mistakes

- Running an audit on a directory that is not an agent project. The audit then has nothing to check.
- Reading a validator's score as a verdict. Fix the high-priority items first and re-run.

## Related

- Packages: [`auditing`](../../packages/harness-quality/auditing/README.md),
  [`validating`](../../packages/harness-quality/validating/README.md),
  [`evaluating`](../../packages/harness-quality/evaluating/README.md).
- Agents: `architecture-auditor`, `quality-validator`, `skill-evaluator` ([subagents](../agents/README.md)).
