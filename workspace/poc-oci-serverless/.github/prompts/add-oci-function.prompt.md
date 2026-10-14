---
description: 'Create a new OCI Function or modify an existing function structure using FDK v1.1.x patterns'
agent: oci-functions-java
argument-hint: 'Function name and type (API Gateway handler / event-driven / scheduled)'
---

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
