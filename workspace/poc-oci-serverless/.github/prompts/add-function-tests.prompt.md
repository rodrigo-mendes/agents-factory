---
description: 'Add Junit 5 unit and integration tests to OCI Java Functions using FnTestingRule and Mockito SDK mocking'
agent: oci-functions-java
argument-hint: 'Target function path, event triggers, and mocked OCI SDK dependencies'
---

# Add Function Tests

**Skill**: `testing-oci-functions-java`

## What this does

Creates a robust JUnit 5 unit and integration test class for an existing OCI Java Function. It instruments testing using the FDK `FnTestingRule` framework and mocks all OCI SDK resource interactions via Mockito.

## Required information

1. **Target Function**: Which existing Java function in the workspace needs tests?
2. **Function Input/Output**: What is the entry event type (e.g., API Gateway request, Service Connector Hub, raw JSON, plain text)?
3. **External Dependencies**: What OCI SDK dependencies are used (e.g., ObjectStorage, Vault, Streaming)?
4. **Mocks Required**: What external REST API calls or OCI client calls do we need to mock?
5. **Expected Scenarios**: Which test scenarios should be covered (e.g., happy path, cold-start initialization error, timeouts, upstream exception, 400 Bad Request mapping)?

## What will be generated

- Testing dependencies (`fn-testing-junit5`, `mockito-core`) in `pom.xml`
- A JUnit 5 test class under `src/test/java/` using the FDK `FnTestingRule`
- Test cases validating the FDK `@FnConfiguration` constructor/configure lifecycle
- Mockito mock definitions for cached OCI SDK client providers and external REST dependencies
- Input event deserialization and output assertion tests (e.g., `APIGatewayResponseEvent` assertions)
- Edge-case logging verification and exception handler test scenarios
- A local validation command block to execute the tests via Maven
