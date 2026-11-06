# Worker brief

The instructions every `package-manual-author` receives. The planner copies this file's rules into each
assignment ([TEMPLATE.WORK-ORDER.md](../assets/TEMPLATE.WORK-ORDER.md)). Back to [SKILL.md](../SKILL.md).

## Hard limits

- Edit only the files named in the assignment. Everything else is off limits: `.apm/` sources, `.claude/`,
  `apm.yml`, `docs/`, scripts, other packages.
- Do **not** run `docs_catalog.py` in write mode. It rewrites every README that carries markers and would
  overwrite another writer's file. `--check-manuals` and `check_manual.py` are read-only and allowed.
- Do not commit, push or start other agents.
- You cannot ask the user anything. If the assignment or the sources are incomplete, stop and return numbered
  questions (outcome `needs-input`) instead of guessing.

## Sourcing rules

- Every statement comes from files in the package: `apm.yml`, `.apm/skills/*/SKILL.md` and their
  `blueprints/`, `.apm/agents/*.md`, `.apm/instructions/*.md`, `scripts/` (including `--help`), or from the
  repository's own instruction file. If it is not there, leave it out or write *unverified*.
- Never invent a parameter, default, file path, exit code, number or behavior.
- Defaults and required/optional come from the skill's parameter table or the argument-hint brackets. If
  neither says, write "not stated".
- Keep accurate facts from the current README, re-verified against the sources. Drop what you cannot verify.
- Never write counts of skills, agents or rules in prose.
- If a source has a corrupted character, write the intended character and report the defect.

## How to work

1. For each package: read `apm.yml`, the current README, every entry point's `SKILL.md` and its
   `blueprints/`, the agents, the instructions and the scripts. Read before writing.
2. Write the README from [the manual template](manual-template.md), in the
   [writing style](writing-style.md). Replace the whole file with the Write tool.
3. Check it: `python <skill>/scripts/check_manual.py --root <repo> --file <README>`. Fix every problem it prints
   and run it again until it is quiet. The hooks run the same check when you save and when you try to finish.
4. Confirm every relative link resolves.

## What to report

Return, under 30 lines:

1. The README files written.
2. Entry points documented and the check result.
3. **Defects in the source files**: typos, broken characters, contradictions between a skill, its agent and
   its scenarios, missing evaluation scenarios, wrong descriptions, stale counts. One line each with the file.
4. Anything marked *unverified* or left out because the sources were silent.
5. If you could not finish: numbered questions.

## Size

As long as the content needs, no padding. A package with several commands is long; a package with a few
knowledge skills is typically 150 to 400 lines.
