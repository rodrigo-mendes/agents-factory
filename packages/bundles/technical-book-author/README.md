# technical-book-author

Technical Book Author: the multi-agent technical book pipeline (TOC, chapters, code, diagrams, review, translation, EPUB 3.0).

**Who it is for:** Authors who want a technical book written, reviewed, translated and packaged as an EPUB.

## Contents

<!-- BEGIN GENERATED:contents -->
**Packages included:** [`book-writing`](../../content-generation/book-writing/README.md)
**Also installed as dependencies:** [`factory-core`](../../factory/factory-core/README.md)

| Type | Entry point or agent | Package |
|---|---|---|
| command | [`/enriching-book-chapter`](../../content-generation/book-writing/README.md#enriching-book-chapter) | `book-writing` |
| command | [`/formatting-book-epub`](../../content-generation/book-writing/README.md#formatting-book-epub) | `book-writing` |
| command | [`/rendering-mermaid-diagrams`](../../content-generation/book-writing/README.md#rendering-mermaid-diagrams) | `book-writing` |
| command | [`/repairing-book-epub`](../../content-generation/book-writing/README.md#repairing-book-epub) | `book-writing` |
| command | [`/rewriting-book-chapter`](../../content-generation/book-writing/README.md#rewriting-book-chapter) | `book-writing` |
| command | [`/rewriting-book-introduction`](../../content-generation/book-writing/README.md#rewriting-book-introduction) | `book-writing` |
| command | [`/switching-book-language`](../../content-generation/book-writing/README.md#switching-book-language) | `book-writing` |
| command | [`/translating-book`](../../content-generation/book-writing/README.md#translating-book) | `book-writing` |
| command | [`/writing-book-toc`](../../content-generation/book-writing/README.md#writing-book-toc) | `book-writing` |
| command | [`/writing-technical-book`](../../content-generation/book-writing/README.md#writing-technical-book) | `book-writing` |
| agent | [`book-formatter`](../../content-generation/book-writing/.apm/agents/book-formatter.agent.md) | `book-writing` |
| agent | [`book-orchestrator`](../../content-generation/book-writing/.apm/agents/book-orchestrator.agent.md) | `book-writing` |
| agent | [`book-translator`](../../content-generation/book-writing/.apm/agents/book-translator.agent.md) | `book-writing` |
| agent | [`chapter-assembler`](../../content-generation/book-writing/.apm/agents/chapter-assembler.agent.md) | `book-writing` |
| agent | [`chapter-enricher`](../../content-generation/book-writing/.apm/agents/chapter-enricher.agent.md) | `book-writing` |
| agent | [`chapter-writer`](../../content-generation/book-writing/.apm/agents/chapter-writer.agent.md) | `book-writing` |
| agent | [`code-illustrator`](../../content-generation/book-writing/.apm/agents/code-illustrator.agent.md) | `book-writing` |
| agent | [`code-validator`](../../content-generation/book-writing/.apm/agents/code-validator.agent.md) | `book-writing` |
| agent | [`diagram-illustrator`](../../content-generation/book-writing/.apm/agents/diagram-illustrator.agent.md) | `book-writing` |
| agent | [`epub-repairer`](../../content-generation/book-writing/.apm/agents/epub-repairer.agent.md) | `book-writing` |
| agent | [`expert-reviewer`](../../content-generation/book-writing/.apm/agents/expert-reviewer.agent.md) | `book-writing` |
| agent | [`mermaid-renderer`](../../content-generation/book-writing/.apm/agents/mermaid-renderer.agent.md) | `book-writing` |
| agent | [`skeptic-reviewer`](../../content-generation/book-writing/.apm/agents/skeptic-reviewer.agent.md) | `book-writing` |

Plus 0 knowledge skills that Claude loads by description. Each package manual lists them.
<!-- END GENERATED:contents -->

## Installation

From the folder of the project that should receive the bundle:

```bash
apm install <path-to-agents-factory>/packages/bundles/technical-book-author --target claude
```

Add `--dry-run` to preview. APM installs the packages listed above and their dependencies into `.claude/`.

To produce the folder and zip that are sold or shared, export the bundle from this repository:

```bash
python scripts/export-bundle.py technical-book-author           # dry run
python scripts/export-bundle.py technical-book-author --apply   # writes dist/technical-book-author/ and the zip
```

The export holds the `.claude/` folder and a `docs/` folder with the usage manuals of the packages it
includes.

## Quick Start

```text
/writing-book-toc "Distributed Systems" audience="senior backend engineers" chapters=12
/writing-technical-book "Distributed Systems" audience="senior backend engineers" context="cloud-native" chapters=12
```

The pipeline stops to show you the table of contents before it writes prose.

## Documentation

The usage manuals cover installation, quick start, usage scenarios, a command or skill reference,
agents and limits:

- [`book-writing`](../../content-generation/book-writing/README.md): usage manual.

See also the [package catalog](../../../docs/packages/README.md) and the
[entry points](../../../docs/entry-points/README.md).
