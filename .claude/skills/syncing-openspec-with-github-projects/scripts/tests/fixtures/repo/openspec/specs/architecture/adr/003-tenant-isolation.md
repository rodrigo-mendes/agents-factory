# ADR-003: Tenant isolation

Status: accepted

## Context

Items belong to exactly one tenant.

## Decision

Every query filters by the caller's tenant id.
