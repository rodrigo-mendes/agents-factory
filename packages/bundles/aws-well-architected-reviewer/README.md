# aws-well-architected-reviewer

AWS Well-Architected Reviewer: 40 AWS architecture skills (six pillars, serverless and SaaS lenses) and the read-only aws-architect advisor and reviewers.

**Who it is for:** Teams that review AWS architectures against the Well-Architected pillars and the serverless and SaaS lenses.

## Contents

<!-- BEGIN GENERATED:contents -->
**Packages included:** [`aws-architect`](../../cloud/provider/aws/aws-architect/README.md)
**Also installed as dependencies:** [`aws-skills`](../../cloud/provider/aws/aws-skills/README.md), [`factory-core`](../../factory/factory-core/README.md), [`handoff-core`](../../delivery/protocol/handoff-core/README.md), [`openspec-core`](../../delivery/specs/openspec-core/README.md)

| Type | Entry point or agent | Package |
|---|---|---|
| command | [`/aws-architecture-advisor`](../../cloud/provider/aws/aws-architect/README.md#aws-architecture-advisor) | `aws-architect` |
| agent | [`aws-architect-reviewer`](../../cloud/provider/aws/aws-architect/.apm/agents/aws-architect-reviewer.agent.md) | `aws-architect` |
| agent | [`aws-architect`](../../cloud/provider/aws/aws-architect/.apm/agents/aws-architect.agent.md) | `aws-architect` |
| agent | [`aws-infrastructure-architect`](../../cloud/provider/aws/aws-architect/.apm/agents/aws-infrastructure-architect.agent.md) | `aws-architect` |
| command | [`/syncing-spec-from-code`](../../delivery/protocol/handoff-core/README.md#syncing-spec-from-code) | `handoff-core` |
| agent | [`spec-synchronizer`](../../delivery/protocol/handoff-core/.apm/agents/spec-synchronizer.agent.md) | `handoff-core` |

Plus 42 knowledge skills that Claude loads by description. Each package manual lists them.
<!-- END GENERATED:contents -->

## Installation

From the folder of the project that should receive the bundle:

```bash
apm install <path-to-agents-factory>/packages/bundles/aws-well-architected-reviewer --target claude
```

Add `--dry-run` to preview. APM installs the packages listed above and their dependencies into `.claude/`.

To produce the folder and zip that are sold or shared, export the bundle from this repository:

```bash
python scripts/export-bundle.py aws-well-architected-reviewer           # dry run
python scripts/export-bundle.py aws-well-architected-reviewer --apply   # writes dist/aws-well-architected-reviewer/ and the zip
```

The export holds the `.claude/` folder and a `docs/` folder with the usage manuals of the packages it
includes.

## Quick Start

```text
/aws-architecture-advisor assess WAF security posture
```

## Documentation

The usage manuals cover installation, quick start, usage scenarios, a command or skill reference,
agents and limits:

- [`aws-architect`](../../cloud/provider/aws/aws-architect/README.md): usage manual.

See also the [package catalog](../../../docs/packages/README.md) and the
[entry points](../../../docs/entry-points/README.md).
