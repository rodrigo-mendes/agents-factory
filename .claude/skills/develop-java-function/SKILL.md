---
name: develop-java-function
description: "Develops Java OCI Functions via the oci-functions-java agent (P0-P5 workflow: classify, scaffold, implement, compile, validate). Use when creating or modifying a Java OCI Function handler, integrations, or project configuration."
argument-hint: "Capability name or description (e.g. 'event-producer', 'add Object Storage write to func-api-facade')"
context: fork
agent: oci-functions-java
disable-model-invocation: true
---

Routes to the `oci-functions-java` agent for Java OCI Function development.

The agent executes a 6-step workflow (P0-P5): classify function type, analyze existing
project files, consult the relevant skills, propose a plan, implement, and validate.

## What This Command Does

Delegates the full development lifecycle to `oci-functions-java`:

- Classifies the function type (API Gateway handler, event-driven, scheduled)
- Identifies required integrations (Object Storage, REST API, Streaming, event handling)
- Loads the relevant skill SKILL.md files for the task
- Proposes a plan (class structure, handler signature, pom.xml changes, func.yaml changes)
- Implements Java code following FDK v1.1.x patterns
- Validates with `mvn compile` and ✅/🚫 rule checks

## Skills the agent loads

| Trigger | Skill |
|---|---|
| Any function | `developing-oci-functions-java` |
| Object Storage | `integrating-oci-functions-objectstorage` |
| REST API calls | `invoking-rest-apis-from-oci-functions` |
| Event publishing | `publishing-events-from-oci-functions` |
| Event consuming | `implementing-oci-functions-events` |
| Refactor | `refactoring-oci-java` |
| RMS/webhook | `integrating-oracle-rms-webhooks` |

## Evaluation Scenarios

See [blueprints/evaluation-scenarios.md](./blueprints/evaluation-scenarios.md)
