# Maintaining the docs

This page explains what is generated, what you write by hand, how the checks work, and what a package
manual must contain.

## What is generated

The generator lives in the `documenting-agent-packages` skill (`packages/factory/package-docs`), together with the manual check and the link check. `scripts/gen-docs-catalog.py` is a thin wrapper that runs it for this repository, so the commands below keep working. It reads `packages/` and rewrites only the text between markers:

```
<!-- BEGIN GENERATED:<id> -->
...generated...
<!-- END GENERATED:<id> -->
```

| Marker id | Where | Content |
|---|---|---|
| `totals` | `README.md` | Package, skill, command, agent and rule counts. |
| `packages-by-family` | `docs/packages/README.md` | One table per family with counts per package. |
| `bundles` | `docs/packages/README.md` | Each bundle, its packages, and whether the export is a subset. |
| `entry-points` | `docs/entry-points/README.md` | Every command and inline orchestrator, linked to its manual section. |
| `agents-roster`, `agents-tools` | `docs/agents/README.md` | Every agent, what starts it, and its tools. |
| `contents` | every package README and every bundle README | Skills, agents, rules, dependencies and who uses the package. |
| `installation` | every package README | Package name, version, how it is installed, and the `apm install` command. |
| `agents-reference` | every package README | Model, tools, whether it can start agents, and what starts it. |

Everything outside the markers is hand-written. Counts in prose are not allowed; put them inside a
marker instead.

## Commands

```
python scripts/gen-docs-catalog.py                 # rewrite the generated blocks
python scripts/gen-docs-catalog.py --check         # exit 1 if any block is stale
python scripts/gen-docs-catalog.py --check-manuals # print manual coverage; exit 1 on gaps
python -m unittest scripts/tests/test_gen_docs_catalog.py scripts/tests/test_export_bundle_docs.py
```

Run both checks before committing. Neither writes anything. To write or repair manuals, use `/documenting-agent-packages` (see [Authoring commands](../entry-points/factory-authoring.md)). It also ships `check_manual.py` (structure and presence of every manual, and the hook that runs when a README is saved) and `check_links.py` (every relative link and anchor).

## What a package manual must contain

Every `packages/**/README.md` follows the layout of the
[`book-writing` manual](../../packages/content-generation/book-writing/README.md). `--check-manuals`
enforces these level-2 headings:

| Heading | Content |
|---|---|
| `## Installation` | The generated `installation` block, then runtime prerequisites the sources state. |
| `## Quick Start` | The shortest real invocation, or plain-text requests for packages without commands. |
| `## Usage Scenarios` | Workflows by intent, each with the exact invocation and what you get. |
| `## Commands Reference` or `## Skills Reference` | One subsection per entry point, or per skill. |
| a heading with `Pipeline` or `Architecture` | A diagram of how the pieces connect. |
| `## Agents Reference` | The generated `agents-reference` block, plus a note per agent. |
| a heading with `Limits` or `Constraints` | The concrete values the sources state. |
| `## Related` | Links to the guide page, the architecture page and the dependencies. |

Each command or inline orchestrator gets a heading that is exactly ``### `/name` `` (or ``### `name` ``
for an orchestrator), so its anchor is `#name`. Under it: a fenced Syntax block and a parameter table
that names every `key=` and `--flag` in the entry point's `argument-hint`. The check fails if one is
missing.

## Bundles and exports

Each bundle has a README with an intro, a Quick Start and a generated `contents` block that links to
the manuals of its packages.

`python scripts/export-bundle.py <bundle> --apply` also writes a `docs/` folder next to `.claude/`
in the exported package. It holds the manual of every package that owns an exported file, with:

- links between included manuals kept, and every other relative link turned into plain text;
- the installation block replaced by a note to copy the bundle's `.claude/` folder;
- table rows for skills, agents and rules that were filtered out removed;
- a banner on a manual when the bundle ships only part of that package;
- the sensitive-data detectors run over every doc file, so a finding blocks the bundle.

`docs/commercial/` is never exported.

## When you change a package

1. Edit files under `packages/<family>/<package>/.apm/`.
2. Update that package's `README.md` if its commands, parameters, agents or limits changed.
3. Regenerate `.claude/` and the catalog (see [Getting started](../getting-started.md#3-change-something)).
4. Run `--check` and `--check-manuals`.

## Writing rules

- Every statement comes from a file in `packages/` (a `SKILL.md`, an agent file, an `apm.yml` or a
  script). Anything not found there is marked *unverified* or left out.
- Use task-first headings and a real example before the explanation.
- Link to the glossary the first time a term appears on a page.
