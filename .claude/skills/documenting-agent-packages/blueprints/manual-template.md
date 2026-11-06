# Manual template

The layout every package manual follows. `scripts/check_manual.py` enforces the headings marked **checked**.
Back to [SKILL.md](../SKILL.md). Empty starting file: [TEMPLATE.PACKAGE-README.md](../assets/TEMPLATE.PACKAGE-README.md).

## Contents

- [Sections in order](#sections-in-order)
- [Command sections](#command-sections)
- [Skills Reference](#skills-reference)
- [Scenarios](#scenarios)
- [Generated blocks](#generated-blocks)
- [Bundle README](#bundle-readme)

## Sections in order

| # | Heading | Checked | What goes in it |
|---|---|---|---|
| 1 | `# <package-folder-name>` | title | The folder name of the package. |
| 2 | Opening paragraph | yes | Three plain sentences: what it is, who it is for, when you need it. A `> ` line may follow for a version lock. |
| 3 | `## Contents` | no | The generated `contents` block. |
| 4 | `## Installation` | yes | The generated `installation` block, then prerequisites the sources state (Node, Python, JDK, cloud CLIs). |
| 5 | `## Quick Start` | yes, needs a code block | The shortest real invocation; for a package with no command, two or three plain-text requests. |
| 6 | `## Usage Scenarios` | yes, needs a code block somewhere | Workflows by intent, see [scenarios](#scenarios). |
| 7 | `## Commands Reference` or `## Skills Reference` | yes | Per entry point, or per skill. |
| 8 | A heading containing `Pipeline` or `Architecture` | yes | One valid diagram of how entry points, agents and skills connect. |
| 9 | `## Agents Reference` | yes | The generated `agents-reference` block, then a note per agent. |
| 10 | `## Output structure` | no | The file tree the package writes, when it writes files. |
| 11 | A heading containing `Limits` or `Constraints` | yes | Concrete values the sources state. |
| 12 | `## Related` | yes | Links to the guide page, the architecture page and the dependencies. |

Out-of-order required sections only warn.

## Command sections

One level-3 section per command or inline orchestrator, inside the Commands Reference.

**The heading is exactly** ``### `/name` `` for a command and ``### `name` `` for an orchestrator, with
nothing after it. GitHub builds the anchor from the whole heading, so a title after the name
(``### `/name` — Title``) would turn the anchor into `#name--title` and break every link to `#name`.
Put the one-line title on the line below, in italics.

Inside, in this order:

| Part | Content |
|---|---|
| Title line | `*Writes the table of contents only.*` |
| **Syntax** | A fenced block with the invocation exactly as the argument-hint shows it. |
| **Parameters** | A table `\| Parameter \| Required \| Default \| Description \|`. |
| **Prerequisites** | What must exist first. |
| **What it does** | The steps or phases, from the skill. |
| **What is updated and what is not** | Both sides. |
| **Output files** | A tree or list. |
| **Examples** | Two or three real invocations. |
| **Next** | The usual next command, when there is one. |

The parameter table must contain every `key=` and every `--flag` of the entry point's `argument-hint`,
spelled as in the hint, each **in a table row**. Naming it only in the Syntax block is not enough.
Positional arguments get a row too. Required or optional comes from the brackets (`<...>` required, `[...]`
optional); a default comes from the skill, otherwise write "not stated". Three entry points of this repository
have no hint; their parameters come from the Arguments section of the skill body.

For packages with many near-identical commands, keep each section short: Syntax, Parameters, one example, and
what differs from the others.

## Skills Reference

For a package with no entry point. Up to about twelve skills: one level-3 subsection per skill with *when it
loads*, *what it locks*, *what it never does* and *an example request*. More than that: one table grouped by
theme with the columns Skill, Loads when, Locks, Never.

## Scenarios

Four to ten, each ``### Scenario N - <title>``: when to use it (one sentence), the exact invocation in a code
block, and what you get. Cover at least:

- the fastest default run;
- input that is incomplete (what comes back and how to answer);
- a misuse or out-of-scope request, and which command or package to use instead;
- chaining to the next command.

Take them from the skill's `blueprints/evaluation-scenarios.md` (canonical, edge and misuse cases) and quote
`query:` lines exactly. A chaining or misuse scenario may be prose; the check only warns.

## Generated blocks

Leave each pair empty between its markers; `docs_catalog.py` fills them:

```text
<!-- BEGIN GENERATED:contents -->
<!-- END GENERATED:contents -->
```

Ids on a package README: `contents`, `installation`, `agents-reference`. Never type counts of skills, agents
or rules in prose; counts belong in a generated block.

## Bundle README

An intro, a line on who it is for, the generated `contents` block, an Installation section with the install and
export commands, a Quick Start from the first command or request of its packages, and a Documentation section
that links to the manual of each package. Empty starting file: [TEMPLATE.BUNDLE-README.md](../assets/TEMPLATE.BUNDLE-README.md).
