---
description: Create a new OCI Function or modify an existing function structure using FDK v1.1.x patterns
argument-hint: Function name and type (API Gateway handler / event-driven / scheduled)
context: fork
agent: oci-functions-java
background: false
disable-model-invocation: true
---

Execute this task now for the OCI serverless project. Read the referenced skill below for the canonical patterns, gather the "Required information", then carry the task through to completion. If the target below is empty, ask for the required information before proceeding.

**Request / target (from the user):** $ARGUMENTS

# Add OCI Function

**Skill**: `developing-oci-functions-java`

## What this does

Creates a new OCI Function project or modifies an existing function's core structure (handler class, func.yaml, pom.xml, Dockerfile).

## Required information

1. **Function name**: Name for the function (e.g., `process-orders`)
2. **Handler type**:
   - API Gateway handler (HTTP request/response)
   - Event-driven (triggered by events)
   - Scheduled (timer-based invocation)
3. **Existing project?**: Is there already a pom.xml and func.yaml, or create from scratch?
4. **If modifying**: Which existing function class to modify?

## What will be generated

- Handler Java class with proper FDK signatures
- `func.yaml` with runtime, memory, and timeout configuration
- `pom.xml` with FDK dependencies (or updates to existing)
- Dockerfile (if creating from scratch)
- Test class skeleton
