# openspec-core

Reusable **OpenSpec 1.15.0** knowledge, split out of `handoff-core` so any family can use the spec
format without the handoff protocol.

| Kind | Name | Purpose |
|---|---|---|
| skill | `specifying-changes-with-openspec-v1-15` | OpenSpec 1.15.0 format and CLI (layout, ADDED/MODIFIED/REMOVED/RENAMED deltas, tasks.md, validate/archive, non-interactive use and Windows) |

The skill name did not change when it moved, so references by name in other packages still work.

Depends on: factory-core. Used by: handoff-core (and, transitively, the packages that depend on it) and openspec-github.

## Project layout rule

| Kind | Name | Purpose |
|---|---|---|
| rule | `openspec-project-layout` (`applyTo: openspec/**`) | Factory convention for `openspec/`: `architecture/`, `design/`, `infrastructure/` with their own `adr/`, `design.md` as index of `design/<flow>.md`, `infra-design.md`, `handoff/`. Separates what is official OpenSpec 1.15 from the convention; the author/reviewer principle and ADR numbering per folder (each flow keeps its own area-to-author table) |
