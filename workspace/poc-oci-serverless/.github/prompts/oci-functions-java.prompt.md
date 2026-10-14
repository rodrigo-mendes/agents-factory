---
description: 'Generic entry point for OCI Functions Java development. Collects function type, integrations, and I/O formats, then routes to the oci-functions-java agent.'
agent: oci-functions-java
argument-hint: 'Describe the function you want to create or modify'
---

# OCI Functions Java Development

## Context Collection

Before starting, I need to understand your function requirements.

**Answer these questions:**

1. **What do you need?**
   - Create a new function from scratch
   - Add a capability to an existing function
   - Modify an existing function's behavior

2. **Function type** (for new functions):
   - API Gateway handler (receives HTTP requests)
   - Event-driven (triggered by Service Connector Hub, Notifications, or Events)
   - Scheduled (invoked by timer or external trigger)

3. **Integrations needed**:
   - Object Storage (read/write files)
   - External REST APIs (invoke third-party or OCI service APIs)
   - Event publishing (send to Streaming, Notifications, Queue, Monitoring)
   - None (standalone function)

4. **Existing project**: Is there an existing pom.xml and func.yaml, or is this a new function project?

## Workflow

Once I have your answers, I will follow the P0–P5 workflow:
- **P0**: Classify function type and load the right skill(s)
- **P1**: Analyze existing project files (pom.xml, func.yaml, Java classes)
- **P2**: Consult skill patterns (✅/🚫 rules)
- **P3**: Propose class structure and dependencies for your approval
- **P4**: Generate Java code, update pom.xml and func.yaml
- **P5**: Validate with `mvn compile` and pattern checks
