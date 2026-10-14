---
description: Add typed event handler to an existing OCI Function using fn-events v1.1.x (API Gateway, Service Connector Hub, Notifications)
argument-hint: Event source type and existing function class name
context: fork
agent: oci-functions-java
background: false
disable-model-invocation: true
---

Execute this task now for the OCI serverless project. Read the referenced skill below for the canonical patterns, gather the "Required information", then carry the task through to completion. If the target below is empty, ask for the required information before proceeding.

**Request / target (from the user):** $ARGUMENTS

# Add Event Handler

**Skill**: `implementing-oci-functions-events`

## What this does

Adds a typed event handler to an existing function, replacing raw InputEvent/OutputEvent with strongly-typed abstractions from fn-events v1.1.x.

## Required information

1. **Event source**: Where do events come from?
   - API Gateway (APIGatewayFunction)
   - Service Connector Hub (ConnectorHubFunction)
   - Notifications (NotificationFunction)
2. **Existing function class**: Which class to add the handler to?
3. **Request/response types**: What data does the event carry? (JSON structure or Java class)
4. **Idempotency**: Does this handler need idempotency guarantees?

## What will be generated

- Typed event handler method with proper fn-events abstractions
- Request/response model classes
- Event deserialization configuration
- Idempotency pattern (if requested)
- Updated pom.xml with fn-events dependency
