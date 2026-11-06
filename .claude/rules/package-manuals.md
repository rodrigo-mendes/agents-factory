---
name: package-manuals
description: "Rules for editing package and bundle README manuals: required sections, exact command headings, generated blocks, no typed counts. Use when writing or editing a package README."
paths:
  - "packages/**/README.md"
---

# Package manuals

Applies to the README of a package or a bundle. READMEs inside `.apm/` folders are not manuals.
Details: `.claude/skills/documenting-agent-packages/blueprints/manual-template.md`.

## Always

- Keep the sections in order: opening paragraph, Contents, Installation, Quick Start, Usage Scenarios, Commands
  Reference (or Skills Reference), a Pipeline or Architecture section, Agents Reference, Limits, Related.
- Give each command or inline orchestrator its own heading that is exactly ``### `/name` `` (``### `name` `` for an
  orchestrator) with nothing after it, so the anchor `#name` works. Put the title on the next line in italics.
- Under it, a Syntax block and a Parameters table that lists every `key=` and `--flag` of the argument-hint,
  each in a table row.
- Leave `<!-- BEGIN GENERATED:... -->` and `<!-- END GENERATED:... -->` pairs alone. They are filled by
  `docs_catalog.py`, never by hand.
- State only what the package's own files say. Write *unverified* or "not stated" for the rest.
- Open with what it is, who it is for and when you need it. Show an example before you explain it.

## Never

- Type counts of skills, agents or rules in prose; put counts in a generated block.
- Invent a parameter, a default, a path or an exit code.
- Add a title after a command name in its heading.
- Fix a problem in a skill or agent file from inside a manual; list it in the known-issues page instead.

## Check

`python .claude/skills/documenting-agent-packages/scripts/check_manual.py --root . --file <README>` explains each
problem in plain words. A hook runs the same check each time a README is saved.
