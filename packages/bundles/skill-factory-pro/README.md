# skill-factory-pro

Skill Factory Pro: research a technology from official sources, then author version-locked skills, subagents and rules and run the full research -> authoring -> quality chain.

**Who it is for:** Teams that create version-locked skills, agents and rules from official sources.

## Contents

<!-- BEGIN GENERATED:contents -->
**Packages included:** [`agent-package-builder`](../../factory/agent-package-builder/README.md), [`package-docs`](../../factory/package-docs/README.md), [`artifact-authoring`](../../factory/artifact-authoring/README.md), [`researching-frameworks`](../../factory/researching-frameworks/README.md)
**Also installed as dependencies:** [`factory-core`](../../factory/factory-core/README.md), [`research-core`](../../factory/research-core/README.md)

| Type | Entry point or agent | Package |
|---|---|---|
| inline orchestrator | [`building-agent-packages`](../../factory/agent-package-builder/README.md#building-agent-packages) | `agent-package-builder` |
| inline orchestrator | [`documenting-agent-packages`](../../factory/package-docs/README.md#documenting-agent-packages) | `package-docs` |
| agent | [`package-manual-author`](../../factory/package-docs/.apm/agents/package-manual-author.agent.md) | `package-docs` |
| command | [`/agent-creator`](../../factory/artifact-authoring/README.md#agent-creator) | `artifact-authoring` |
| command | [`/architecture-approaches-skill-generator`](../../factory/artifact-authoring/README.md#architecture-approaches-skill-generator) | `artifact-authoring` |
| command | [`/methodologies-skill-generator`](../../factory/artifact-authoring/README.md#methodologies-skill-generator) | `artifact-authoring` |
| command | [`/skill-creator`](../../factory/artifact-authoring/README.md#skill-creator) | `artifact-authoring` |
| agent | [`artifact-author`](../../factory/artifact-authoring/.apm/agents/artifact-author.agent.md) | `artifact-authoring` |
| command | [`/architecture-methodology-researcher`](../../factory/researching-frameworks/README.md#architecture-methodology-researcher) | `researching-frameworks` |
| command | [`/business-domain-researcher`](../../factory/researching-frameworks/README.md#business-domain-researcher) | `researching-frameworks` |
| command | [`/cloud-architecture-researcher`](../../factory/researching-frameworks/README.md#cloud-architecture-researcher) | `researching-frameworks` |
| command | [`/requirements-methodology-researcher`](../../factory/researching-frameworks/README.md#requirements-methodology-researcher) | `researching-frameworks` |
| command | [`/researching-technical-frameworks`](../../factory/researching-frameworks/README.md#researching-technical-frameworks) | `researching-frameworks` |
| agent | [`framework-researcher`](../../factory/research-core/.apm/agents/framework-researcher.agent.md) | `research-core` |
| agent | [`research-synthesizer`](../../factory/research-core/.apm/agents/research-synthesizer.agent.md) | `research-core` |
| agent | [`section-investigator`](../../factory/research-core/.apm/agents/section-investigator.agent.md) | `research-core` |

Plus 1 knowledge skills that Claude loads by description. Each package manual lists them.
<!-- END GENERATED:contents -->

## Installation

From the folder of the project that should receive the bundle:

```bash
apm install <path-to-agents-factory>/packages/bundles/skill-factory-pro --target claude
```

Add `--dry-run` to preview. APM installs the packages listed above and their dependencies into `.claude/`.

To produce the folder and zip that are sold or shared, export the bundle from this repository:

```bash
python scripts/export-bundle.py skill-factory-pro           # dry run
python scripts/export-bundle.py skill-factory-pro --apply   # writes dist/skill-factory-pro/ and the zip
```

The export holds the `.claude/` folder and a `docs/` folder with the usage manuals of the packages it
includes.

## Quick Start

```text
/researching-technical-frameworks FastAPI 0.115
/skill-creator workspace/research_FastAPI_v0.115.md
```

For the whole chain from a brief to a committed package, run `/building-agent-packages`.

To write or check the manuals of the packages you build, run `/documenting-agent-packages mode=check`.

## Documentation

The usage manuals cover installation, quick start, usage scenarios, a command or skill reference,
agents and limits:

- [`researching-frameworks`](../../factory/researching-frameworks/README.md): usage manual.
- [`artifact-authoring`](../../factory/artifact-authoring/README.md): usage manual.
- [`agent-package-builder`](../../factory/agent-package-builder/README.md): usage manual.

See also the [package catalog](../../../docs/packages/README.md) and the
[entry points](../../../docs/entry-points/README.md).
