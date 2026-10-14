# Evidence rule

Back to [SKILL.md](../../SKILL.md). Applies to every skill in the family; copy it into `_family_rules`.

## Confidence by evidence

| Evidence | Max confidence |
|---|---|
| Versioned official page (docs for the exact target version, source at the release tag, registry POM/manifest) read in full by the researcher | High |
| Unversioned/"latest" official page, main-branch example, partly read page | medium |
| Tool summary, community post, memory, inference | (unverified) |
| Absence of evidence ("no build is known") | (medium confidence, absence of evidence) |

Being a single source does NOT lower a versioned claim to medium.

## Tier rules

- **Always Do**: one High claim per bullet, one inline URL, no caveats inside the bullet (move them to Ask First).
- **Never Do**: High rows only, and the alternative (✅) is High too.
- Medium and unverified items live in Ask First or blueprints, tagged `(medium confidence)` / `(unverified)`.
- Partly read pages are recorded as coverage limits ("first 100k of 108k characters"), never "read in full".
- The same claim carries the same tag in SKILL.md, blueprints and register.

## Orchestrator-verified facts

A fact used by more than one skill is verified by the orchestrator against an official page, written in `_family_facts_<ver>.md` with source and read date, and only then handed to authors. Authors never edit that file; a disputed fact goes back to the orchestrator.
