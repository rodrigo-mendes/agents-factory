# spec-driven-delivery

Spec-Driven Delivery: OpenSpec 1.15, the file-based agent handoff protocol and the OpenSpec to GitHub Projects bridge.

**Who it is for:** Teams that keep OpenSpec specs in git and mirror them to a GitHub Project.

## Contents

<!-- BEGIN GENERATED:contents -->
**Packages included:** [`openspec-github`](../../delivery/specs/openspec-github/README.md)
**Also installed as dependencies:** [`factory-core`](../../factory/factory-core/README.md), [`openspec-core`](../../delivery/specs/openspec-core/README.md), [`handoff-core`](../../delivery/protocol/handoff-core/README.md), [`github-core`](../../delivery/github/github-core/README.md)

| Type | Entry point or agent | Package |
|---|---|---|
| command | [`/syncing-openspec-to-github`](../../delivery/specs/openspec-github/README.md#syncing-openspec-to-github) | `openspec-github` |
| agent | [`openspec-github-syncer`](../../delivery/specs/openspec-github/.apm/agents/openspec-github-syncer.agent.md) | `openspec-github` |
| command | [`/syncing-spec-from-code`](../../delivery/protocol/handoff-core/README.md#syncing-spec-from-code) | `handoff-core` |
| agent | [`spec-synchronizer`](../../delivery/protocol/handoff-core/.apm/agents/spec-synchronizer.agent.md) | `handoff-core` |

Plus 5 knowledge skills that Claude loads by description. Each package manual lists them.
<!-- END GENERATED:contents -->

## Installation

From the folder of the project that should receive the bundle:

```bash
apm install <path-to-agents-factory>/packages/bundles/spec-driven-delivery --target claude
```

Add `--dry-run` to preview. APM installs the packages listed above and their dependencies into `.claude/`.

To produce the folder and zip that are sold or shared, export the bundle from this repository:

```bash
python scripts/export-bundle.py spec-driven-delivery           # dry run
python scripts/export-bundle.py spec-driven-delivery --apply   # writes dist/spec-driven-delivery/ and the zip
```

The export holds the `.claude/` folder and a `docs/` folder with the usage manuals of the packages it
includes.

## Quick Start

```text
/syncing-openspec-to-github list-tenant-items --profile <your-profile.yaml>
```

This is a dry run. Add `--apply` after you check the preview.

## Documentation

The usage manuals cover installation, quick start, usage scenarios, a command or skill reference,
agents and limits:

- [`openspec-github`](../../delivery/specs/openspec-github/README.md): usage manual.

See also the [package catalog](../../../docs/packages/README.md) and the
[entry points](../../../docs/entry-points/README.md).
