---
description: Diagnose runtime errors (502/503/504/500) in deployed OCI Functions using systematic elimination
argument-hint: HTTP status code, function name, error symptoms
context: fork
agent: oci-debugger
background: false
disable-model-invocation: true
---

Execute this task now for the OCI serverless project. Read the referenced skill below for the canonical patterns, gather the "Required information", then carry the task through to completion. If the target below is empty, ask for the required information before proceeding.

**Request / target (from the user):** $ARGUMENTS

# Debug Function

**Skill**: `debugging-deployed-functions`

## What this does

Diagnoses runtime issues in deployed OCI Functions using systematic elimination by HTTP status code, OCI CLI investigation, and a common root cause database.

## Required information

1. **HTTP status code**: What error are you seeing? (502, 503, 504, 500)
2. **Function name**: Which function is failing?
3. **When it started**: Did it work before? What changed?
4. **Invoke method**: Via API Gateway, fn CLI, or OCI Console?
5. **Error message**: Any error body returned?

## Diagnostic workflow (P0-P4)

1. **P0**: Classify by HTTP status code
   - **502**: Function crash (OOM, init error, unhandled exception)
   - **503**: Function unavailable (image pull failure, subnet issues)
   - **504**: Timeout (function exceeded deadline)
   - **500**: Internal error (SDK auth, permission denied)
2. **P1**: Investigate with OCI CLI (fn invoke, logs)
3. **P2**: Check common root causes database
4. **P3**: Apply fix or recommend remediation
5. **P4**: Verify fix with test invocation
