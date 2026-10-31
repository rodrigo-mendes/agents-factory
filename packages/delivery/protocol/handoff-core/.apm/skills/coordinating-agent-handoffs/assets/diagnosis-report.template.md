---
kind: diagnosis-report
id: diagnosis-report-<nn>    # optional; must equal the file name without .md (generic default file diagnosis-report.md has id diagnosis-report)
from: <debugger-agent>
to: <owner-of-the-fix>
change: <change-id>          # profile scope_key: `change` or `capability`
refs: [<deploy-report-id>]
outcome: success             # success = root cause found | partial | failed = could not determine | needs-input
spec_impact: none            # none | divergence | ambiguity (a fix that changes behaviour = divergence)
createdAt: <ISO 8601 UTC>
---

## Symptom

What was observed (status, error text), copied from the deploy-report.

## Root cause

One paragraph. Say "hypothesis" when it is not proven by the evidence below.

## Evidence

- Command / log query -> output that supports the root cause.

## Exact fix

File + precise change, or the configuration value. The debugger never edits code itself.

## Classification

code | config | infra | spec

## Next step

<owner role> applies the fix via a new work-order. Context: this file.
