# camel-quarkus-integration

Camel Quarkus Integration: 10 Camel Quarkus 3.40 LTS skills, the project-structure skill and the camel-quarkus-integrator agent.

**Who it is for:** Teams that build integration routes on Camel Quarkus 3.40 LTS.

## Contents

<!-- BEGIN GENERATED:contents -->
**Packages included:** [`camel-quarkus-integrator`](../../java/quarkus/camel-quarkus-integrator/README.md)
**Also installed as dependencies:** [`factory-core`](../../factory/factory-core/README.md), [`camel-quarkus-skills`](../../java/quarkus/camel-quarkus-skills/README.md), [`quarkus-core`](../../java/quarkus/quarkus-core/README.md), [`clean-code-quarkus`](../../java/clean-code/clean-code-quarkus/README.md)

| Type | Entry point or agent | Package |
|---|---|---|
| inline orchestrator | [`integrating-camel-quarkus`](../../java/quarkus/camel-quarkus-integrator/README.md#integrating-camel-quarkus) | `camel-quarkus-integrator` |
| agent | [`camel-quarkus-integrator`](../../java/quarkus/camel-quarkus-integrator/.apm/agents/camel-quarkus-integrator.agent.md) | `camel-quarkus-integrator` |

Plus 15 knowledge skills that Claude loads by description. Each package manual lists them.
<!-- END GENERATED:contents -->

## Installation

From the folder of the project that should receive the bundle:

```bash
apm install <path-to-agents-factory>/packages/bundles/camel-quarkus-integration --target claude
```

Add `--dry-run` to preview. APM installs the packages listed above and their dependencies into `.claude/`.

To produce the folder and zip that are sold or shared, export the bundle from this repository:

```bash
python scripts/export-bundle.py camel-quarkus-integration           # dry run
python scripts/export-bundle.py camel-quarkus-integration --apply   # writes dist/camel-quarkus-integration/ and the zip
```

The export holds the `.claude/` folder and a `docs/` folder with the usage manuals of the packages it
includes.

## Quick Start

```text
/integrating-camel-quarkus
```

The orchestrator interviews you, then loads only the Camel Quarkus skills it needs.

## Documentation

The usage manuals cover installation, quick start, usage scenarios, a command or skill reference,
agents and limits:

- [`camel-quarkus-integrator`](../../java/quarkus/camel-quarkus-integrator/README.md): usage manual.

See also the [package catalog](../../../docs/packages/README.md) and the
[entry points](../../../docs/entry-points/README.md).
