# Proposal: list-tenant-items

## Why

Tenants need to list their own items through the public API without seeing other tenants' data.

## What Changes

- Add `GET /tenants/{id}/items` backed by a Lambda handler.
- Enforce tenant isolation in the repository layer (ADR-003).

## Impact

- Affected specs: items
