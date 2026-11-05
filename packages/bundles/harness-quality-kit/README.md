# harness-quality-kit

Harness Quality Kit: audit agent architectures, validate skills/rules/router compliance and evaluate skill behaviour with LLM-as-judge scenarios.

**Who it is for:** Maintainers of agent projects who want to audit architecture, validate skills and rules, and evaluate skill behavior.

## Contents

<!-- BEGIN GENERATED:contents -->
**Packages included:** [`auditing`](../../harness-quality/auditing/README.md), [`validating`](../../harness-quality/validating/README.md), [`evaluating`](../../harness-quality/evaluating/README.md)
**Also installed as dependencies:** [`factory-core`](../../factory/factory-core/README.md)

| Type | Entry point or agent | Package |
|---|---|---|
| command | [`/audit-architecture-consensus`](../../harness-quality/auditing/README.md#audit-architecture-consensus) | `auditing` |
| command | [`/audit-architecture-engine`](../../harness-quality/auditing/README.md#audit-architecture-engine) | `auditing` |
| command | [`/audit-architecture-flow`](../../harness-quality/auditing/README.md#audit-architecture-flow) | `auditing` |
| command | [`/audit-architecture-scope`](../../harness-quality/auditing/README.md#audit-architecture-scope) | `auditing` |
| command | [`/audit-cc-architecture-consensus`](../../harness-quality/auditing/README.md#audit-cc-architecture-consensus) | `auditing` |
| command | [`/audit-cc-architecture-engine`](../../harness-quality/auditing/README.md#audit-cc-architecture-engine) | `auditing` |
| command | [`/audit-cc-architecture-flow`](../../harness-quality/auditing/README.md#audit-cc-architecture-flow) | `auditing` |
| command | [`/audit-cc-architecture-scope`](../../harness-quality/auditing/README.md#audit-cc-architecture-scope) | `auditing` |
| agent | [`architecture-auditor`](../../harness-quality/auditing/.apm/agents/architecture-auditor.agent.md) | `auditing` |
| command | [`/agent-router-pattern-validator`](../../harness-quality/validating/README.md#agent-router-pattern-validator) | `validating` |
| command | [`/copilot-compatibility-review`](../../harness-quality/validating/README.md#copilot-compatibility-review) | `validating` |
| command | [`/instructions-best-practices-validator`](../../harness-quality/validating/README.md#instructions-best-practices-validator) | `validating` |
| command | [`/project-analysis-validator`](../../harness-quality/validating/README.md#project-analysis-validator) | `validating` |
| command | [`/skill-best-practices-validator`](../../harness-quality/validating/README.md#skill-best-practices-validator) | `validating` |
| agent | [`quality-validator`](../../harness-quality/validating/.apm/agents/quality-validator.agent.md) | `validating` |
| command | [`/evaluating-skill-scenarios`](../../harness-quality/evaluating/README.md#evaluating-skill-scenarios) | `evaluating` |
| agent | [`skill-evaluator`](../../harness-quality/evaluating/.apm/agents/skill-evaluator.agent.md) | `evaluating` |

Plus 0 knowledge skills that Claude loads by description. Each package manual lists them.
<!-- END GENERATED:contents -->

## Installation

From the folder of the project that should receive the bundle:

```bash
apm install <path-to-agents-factory>/packages/bundles/harness-quality-kit --target claude
```

Add `--dry-run` to preview. APM installs the packages listed above and their dependencies into `.claude/`.

To produce the folder and zip that are sold or shared, export the bundle from this repository:

```bash
python scripts/export-bundle.py harness-quality-kit           # dry run
python scripts/export-bundle.py harness-quality-kit --apply   # writes dist/harness-quality-kit/ and the zip
```

The export holds the `.claude/` folder and a `docs/` folder with the usage manuals of the packages it
includes.

## Quick Start

```text
/audit-cc-architecture-consensus .claude/
/skill-best-practices-validator .claude/skills/
/evaluating-skill-scenarios cloud-architecture-researcher
```

## Documentation

The usage manuals cover installation, quick start, usage scenarios, a command or skill reference,
agents and limits:

- [`auditing`](../../harness-quality/auditing/README.md): usage manual.
- [`validating`](../../harness-quality/validating/README.md): usage manual.
- [`evaluating`](../../harness-quality/evaluating/README.md): usage manual.

See also the [package catalog](../../../docs/packages/README.md) and the
[entry points](../../../docs/entry-points/README.md).
