---
kind: deploy-report
id: deploy-report-<nn>       # optional; must equal the file name without .md (generic default file deploy-report.md has id deploy-report)
from: <deployer-agent>
to: <debugger-or-orchestrator-agent>
change: <change-id>          # profile scope_key: `change` or `capability`
refs: [<report-id-of-each-artifact-deployed>]
outcome: success             # success | partial | failed | needs-input
createdAt: <ISO 8601 UTC>
---

## Deployed

- Artifact / image / version deployed, plan summary (adds, changes, destroys), identifiers of the
  resources touched (ARNs, OCIDs, endpoints).

## Validation

- Smoke test per happy-path scenario -> status and body (trimmed). Command -> result.
- Post-deploy checks required by the spec (cold start, observability).

## Next step

<role + one-line why>. On `failed`: the symptom as seen, not a guess at the cause. Context: this file.
