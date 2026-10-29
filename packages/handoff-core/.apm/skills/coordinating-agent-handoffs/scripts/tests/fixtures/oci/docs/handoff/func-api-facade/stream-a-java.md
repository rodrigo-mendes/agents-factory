---
kind: work-order
from: "@oci-serverless-architect"
to: "@oci-functions-java"
capability: func-api-facade
stream: a-java
dependsOn: none
status: completed
createdAt: 2026-07-02T10:00:00Z
---

## Scope
Create the `services/func-api-facade/` Java project (handler + DTOs + tests).

## Components
- [x] `ApiFacadeHandler` - API Gateway event handler
- [x] Unit tests (FnTestingRule)

## Constraints
- Handler must implement the initError pattern.

## Dependencies
- None.

## Acceptance Criteria
- [x] `mvn test` passes
