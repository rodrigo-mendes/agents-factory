---
name: documenting-agent-packages
description: "Finds missing or incomplete package and bundle manuals in an APM repository, plans the work with the user, runs package-manual-author writers in parallel, then fills the generated tables and checks structure, links and the presence of every manual. Use when a package or bundle has no usage manual, a command changed, or the docs must be rebuilt or audited. Not for writing the package's own skills, agents or rules, or for committing."
argument-hint: "mode=check|package|changed|all|bundles [package=<path>[,<path>]] [since=<git-ref>] [writers=<n>]"
---

# Documenting agent packages

> Orchestrator only: it holds the workflow, the gates and the protocols. Every statement in a manual comes
> from the package's own files, written by the `package-manual-author` workers it starts. It runs inline in
> your session (so it can ask you questions) and never commits or pushes.

## Overview

You type one command. The skill looks at the repository, reports what is missing, shows a plan, and after
your yes starts one writer per group of packages. When the writers are done it fills the generated tables,
runs every check, collects the problems the writers found in the package files, and reports before and
after. Two gates need your answer: **G1** the plan and **G2** the problem list.

```text
/documenting-agent-packages mode=check
/documenting-agent-packages mode=package package=java/libs/stripe-java
/documenting-agent-packages mode=changed since=master
```

## Quick Navigation

- [Modes](#modes)
- [Phases and gates](#phases-and-gates)
- [Protocols](#protocols)
- [Blueprints & Guardrails](#blueprints--guardrails)
- [Hooks](#hooks)
- [Quick Reference](#quick-reference)
- [External Resources](#external-resources)
- [Manual template](blueprints/manual-template.md) · [Writing style](blueprints/writing-style.md) · [Worker brief](blueprints/worker-brief.md)
- [Phases in detail](blueprints/phases.md) · [Lessons](blueprints/lessons.md)
- [Always-do patterns](blueprints/always-do-patterns.md) · [Never-do patterns](blueprints/never-do-patterns.md)
- [Evaluation scenarios](blueprints/evaluation-scenarios.md)

## Modes

| Option | Meaning | Example |
|---|---|---|
| `mode=check` | Report what is missing. Changes nothing. | `/documenting-agent-packages mode=check` |
| `mode=package package=<path>[,<path>]` | Write or update the manuals of the named packages (paths relative to the packages folder). | `... mode=package package=java/libs/stripe-java` |
| `mode=changed since=<git ref>` | Same, for every package with files changed since that commit or branch. | `... mode=changed since=master` |
| `mode=all` | Every package. | `... mode=all` |
| `mode=bundles` | Only the bundle READMEs. | `... mode=bundles` |
| `writers=<n>` | Most writers at the same time (default 6). | `... mode=all writers=4` |

With no mode the skill runs `mode=check` and asks what to do next. A package path that does not exist is
reported and never guessed.

## Phases and gates

| Phase | Does | Gate |
|---|---|---|
| **D0 Preflight** | Detect the layout (`docs-catalog.json` or the defaults), record `git status`. Before any phase that writes (D3), take the working-tree snapshot; `mode=check` takes none. | none |
| **D1 Coverage** | `scripts/docs_catalog.py --check-manuals`; list gaps per package and per entry point. | `mode=check` ends here |
| **D2 Plan** | Group the packages per writer (by family, at most `writers`), list the files each writer may touch, estimate effort. | **G1: the user approves the plan** |
| **D3 Fan-out** | One `package-manual-author` per group, started with the Agent tool in one message, with an assignment from [the template](assets/TEMPLATE.WORK-ORDER.md). | none |
| **D4 Generate and check** | Only after every writer has returned: `docs_catalog.py`, then `docs_catalog.py --check`, `check_manual.py --all`, `check_links.py`, and the repository's own sensitive-data check if it has one. A failure goes back to the writer that owns the file (2 rounds), then to the user. | none |
| **D5 Consolidate** | Merge the writers' problem reports into the known-issues page ([template](assets/TEMPLATE.KNOWN-SOURCE-ISSUES.md)), marking what was verified and what was only reported. | **G2: the user reviews the list** |
| **D6 Report** | Coverage before and after, files changed, items left *unverified*, and a proposed commit split. Never commits. | none |

Details, commands and "done when" for each phase are in [phases](blueprints/phases.md).

## Protocols

1. **Flat fan-out.** Only this skill starts writers. A writer cannot start another agent.
2. **Disjoint files.** Two writers never get the same file. The skill, not the writer, decides the groups.
3. **Nobody but D4 touches generated tables.** Writers leave the `<!-- BEGIN GENERATED:... -->`
   pairs empty. Only D4 runs the generator, and only after the last writer has returned, because the
   generator rewrites every README that carries markers and would overwrite a file still being written.
4. **Scripts decide.** Counts, coverage, link results and staleness come from the scripts, never from a
   writer's estimate.
5. **Relayed approval.** G1 and G2 count only when the user answers in their own words.
6. **Sources only.** A writer states only what the package's files say. Anything else is marked *unverified*
   or left out. Source defects are reported, never silently fixed.
7. **Snapshot before writing.** Before D3, build the working-tree snapshot (see [lessons](blueprints/lessons.md)) so
   nothing a writer does can lose uncommitted work. `mode=check` writes nothing, so it takes none.

## Blueprints & Guardrails

### ✅ Always Do

- **Check before writing.** Run D1 and show the gaps first. See [phases](blueprints/phases.md#d1-coverage).
- **Give each writer its own files and the brief.** The assignment names the packages, the files it may
  write and the checks it must pass. See [worker brief](blueprints/worker-brief.md).
- **Run the generator last, once.** After the final writer returns. See [lessons](blueprints/lessons.md).
- **Write for people.** Plain words, an example before the explanation, terms explained.
  See [writing style](blueprints/writing-style.md).
- **Keep command headings exact.** ``### `/name` `` with nothing after it, so `#name` links work.
- **Report problems found in package files** in the known-issues page instead of fixing them.
- **Show the commit split and stop.** The user decides on commits, merge and push.

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Plan size | `mode=all` is long and costly; `mode=changed` is cheap but misses unchanged packages that are already stale. | "Write all N manuals, or only the M that changed?" |
| Writers in parallel | More writers finish sooner but cost more at once. | "Run up to 6 writers at the same time?" |
| A package with no commands and no skills | A manual can still document agents or rules, or be skipped. | "This package only has rules. Document it anyway?" |
| Targets that include both Claude and Cursor | APM refuses to install the save-time hook for both (it would run twice), so one target gets it. | "Which of Claude or Cursor should get the save-time hook?" |
| A repository without `docs-catalog.json` | The defaults match one layout; a different layout needs the file. | "Create docs-catalog.json with these folder names?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Run `docs_catalog.py` (write mode) while a writer is running. | Wait for every writer, then run it once in D4. |
| Commit, push, merge or open a pull request. | Propose the commit split in D6 and let the user decide. |
| Edit `.apm/` sources, `.claude/` or package metadata to make a manual pass. | Report the source defect in the known-issues page. |
| Invent a parameter, default, path, exit code or count. | Write *unverified* or "not stated". |
| Start a writer before the user approves the plan (G1). | Show the plan and wait. |
| Let a writer touch a file outside its assignment. | Keep the assignment's file list exact and check `git status` after D3. |
| Use `git reset --hard`, `git clean` or `git checkout --` to recover. | Restore from the snapshot (see [lessons](blueprints/lessons.md)). |
| Type counts of skills, agents or rules in prose. | Put counts in a generated block. |

## Hooks

Two Claude Code hooks run `scripts/check_manual.py`, which explains each problem in plain words:

| Hook | Defined in | Effect |
|---|---|---|
| `PostToolUse`, matcher `Edit\|Write` | `.apm/hooks/check-manual.json`, in APM's hook format | After a README is written or edited, checks that one manual: sections, command sections, parameter tables, generated markers, links. Any other file exits 0 at once. A problem exits 2 and the agent sees the message. |
| `Stop` (a subagent's Stop is run as SubagentStop) | the header of `package-manual-author` | When a writer tries to finish, checks that every manual and required page exists and is linked, then the manuals changed in the working tree (`--skip-stale`, because a writer must not run the generator). It exits 0 when `stop_hook_active` is set, so it can never loop. Claude only: APM drops an agent's own `hooks:` for other targets. |

**The save-time hook is installed by APM, for each target.** `apm install` merges it into `.claude/settings.json`, writes
`.github/hooks/package-docs-check-manual.json` for Copilot, and does the same for Codex and Gemini, copying the shim
`.apm/hooks/manual_hook.py` next to each. The shim finds `check_manual.py` in whichever target folder the skill was
installed to (`.claude`, `.github`, `.cursor`, `.codex`, `.gemini`, `.windsurf`, `.kiro`, `.agents`), then in a source checkout
(`packages/**/.apm/skills`), forwards the hook JSON and the exit code, and exits 0 when the skill is not installed, so
a missing install never blocks editing. Nobody edits `settings.json` by hand.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [ { "type": "command", "command": "python ./manual_hook.py post-edit", "timeout": 30 } ]
      }
    ]
  }
}
```

APM limits (from its hooks page and an install test on 2026-11-06): it refuses to install hooks for Claude and Cursor
in the same project, because they would run twice, so a project picks one of the two; Grok and OpenCode are skipped;
`apm install --dry-run` does not preview hooks. Plain `./script` resolves relative to the hook file.

Claude Code contract, from the official docs (fetched 2026-11-06): hooks receive JSON on stdin with `tool_input.file_path`;
for PostToolUse, exit 2 shows stderr to Claude; for Stop and SubagentStop, exit 2 keeps the agent working and
sends stderr as the reason. After eight consecutive blocks Claude Code ends the turn anyway.
Sources: https://code.claude.com/docs/en/hooks, https://code.claude.com/docs/en/sub-agents and
https://microsoft.github.io/apm/producer/author-primitives/hooks-and-commands/.

## Quick Reference

| Item | Value |
|---|---|
| Entry point | `/documenting-agent-packages` (inline, no fork) |
| Writer | `package-manual-author` (sonnet; Read, Grep, Glob, Write, Edit, Bash; non-interactive) |
| Editing rule | `package-manuals`, applies to `packages/**/README.md` |
| Generator | `python scripts/docs_catalog.py --root <repo> [--check \| --check-manuals]` |
| Manual and presence check | `python scripts/check_manual.py --root <repo> --file <README> \| --all \| --hook post-edit \| --hook stop` |
| Link check | `python scripts/check_links.py --root <repo>` |
| Layout file | `<repo>/docs-catalog.json` (optional; keys in `docs_catalog.py`, `DEFAULT_CONFIG`) |
| Exit codes | generator: 0 done or current, 1 stale or gaps; check_manual: 0 fine, 2 problem; check_links: 0 fine, 1 broken |

## External Resources

- Claude Code hooks reference: https://code.claude.com/docs/en/hooks (fetched 2026-11-06)
- Subagent configuration: https://code.claude.com/docs/en/sub-agents (fetched 2026-11-06)
