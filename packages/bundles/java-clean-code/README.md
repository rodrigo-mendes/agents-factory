# java-clean-code

Java Clean Code: behaviour-preserving refactoring skills for Quarkus and OCI Functions Java and the two clean code rules (small methods, SRP by package, DRY, records, facades). Each rule targets one stack: keep only the rule of your stack in a project.

**Who it is for:** Java teams that want behavior-preserving refactoring guidance for Quarkus or OCI Functions code.

## Contents

<!-- BEGIN GENERATED:contents -->
**Packages included:** [`clean-code-quarkus`](../../java/clean-code/clean-code-quarkus/README.md), [`clean-code-oci`](../../java/clean-code/clean-code-oci/README.md)
**Also installed as dependencies:** [`factory-core`](../../factory/factory-core/README.md)

| Type | Entry point or agent | Package |
|---|---|---|

Plus 2 knowledge skills that Claude loads by description. Each package manual lists them.
<!-- END GENERATED:contents -->

## Installation

From the folder of the project that should receive the bundle:

```bash
apm install <path-to-agents-factory>/packages/bundles/java-clean-code --target claude
```

Add `--dry-run` to preview. APM installs the packages listed above and their dependencies into `.claude/`.

To produce the folder and zip that are sold or shared, export the bundle from this repository:

```bash
python scripts/export-bundle.py java-clean-code           # dry run
python scripts/export-bundle.py java-clean-code --apply   # writes dist/java-clean-code/ and the zip
```

The export holds the `.claude/` folder and a `docs/` folder with the usage manuals of the packages it
includes.

## Quick Start

This bundle has no commands. Ask Claude to refactor; the skill for your stack loads by description.

```text
Refactor this handler for readability without changing its behavior.
```

(illustrative request, not from an evaluation scenario)

## Documentation

The usage manuals cover installation, quick start, usage scenarios, a command or skill reference,
agents and limits:

- [`clean-code-quarkus`](../../java/clean-code/clean-code-quarkus/README.md): usage manual.
- [`clean-code-oci`](../../java/clean-code/clean-code-oci/README.md): usage manual.

See also the [package catalog](../../../docs/packages/README.md) and the
[entry points](../../../docs/entry-points/README.md).
