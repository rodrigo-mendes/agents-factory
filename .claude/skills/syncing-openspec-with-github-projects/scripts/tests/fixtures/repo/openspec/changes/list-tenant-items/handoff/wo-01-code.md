---
kind: work-order
id: wo-01-code
from: building-quarkus-aws-saas
to: quarkus-lambda-integrator
change: list-tenant-items
task: T1
requirements: [R1]
status: done
createdAt: 2026-11-04T09:00:00Z
---

## Scope

Implement GET /tenants/{id}/items (resource + repository).

## Skills

- developing-quarkus-amazon-lambda-http-v3-40

## Requirements

- R1: the system SHALL list only the items of the caller's tenant.

## Constraints

- No cross-tenant reads (ADR-003).

## Acceptance criteria

- [x] Every scenario of R1 has a green test.
