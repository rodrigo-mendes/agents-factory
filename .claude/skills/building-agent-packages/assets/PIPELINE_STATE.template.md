# Pipeline state — <slug>

```yaml
slug: <slug>
mode: new            # new | from-research | resume
current_phase: P0
reconstructed: false # true when rebuilt from disk without a prior state file
rounds: 3
```

## Approvals
Only genuine user answers (question tool or explicit chat message). One line each, verbatim quote.

| Gate | Date | Scope approved | User words |
|---|---|---|---|
| G1 | | | |
| G2 | | | |
| G3 | | | |

G4 (push) is never recorded here: the push is always done by the user.

## Units
| Unit | Source item | Skill name | Research file | State | Score | Tokens |
|---|---|---|---|---|---|---|
| | | | | PLANNED | | |

State machine: `PLANNED -> RESEARCHED -> AUTHORED -> VERIFIED -> VALIDATED`.

## Quality loop
| Round | Validate | Test | Audit | HIGH | Decision |
|---|---|---|---|---|---|

## Log
One line per transition: `YYYY-MM-DD HH:MM  phase  event`.
