---
kind: verify
id: verify-<stage>
from: <verifier - an agent, a script name or "user">
to: <orchestrator-agent>
change: <change-id>          # profile scope_key: `change` or `capability`
stage: <stage id, e.g. E3, task-T1, deploy>
refs: [<ids of the records being verified>]
outcome: pass                # pass | fail
createdAt: <ISO 8601 UTC>
---

## Criteria

One line per acceptance criterion of the stage: `[x]` met / `[ ]` not met, with the reason.

- [ ] <criterion 1>
- [ ] <criterion 2>

## Evidence

- Command or check -> output. The verifier re-runs checks; it does not copy the author's report.
- The verifier must differ from the author of every record in `refs` (check_records.py enforces it).
