---
kind: report
from: "@oci-deployer"
to: "@oci-debugger"
refs: result-java.md
capability: func-api-facade
outcome: failed
createdAt: 2026-07-02T10:40:00Z
---

## What changed
- Built and pushed `func-api-facade:0.0.1`; terraform apply -> 1 change.

## Validation
- Smoke test -> HTTP 500 `Function init failed`.

## Next action
Hand off: run `/debug-oci-function` (`@oci-debugger`) - init failure needs diagnosis.
