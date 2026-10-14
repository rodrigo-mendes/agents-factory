# oci-core

Shared core for the **OCI agent family**. Holds the cross-agent **handoff protocol**
(`coordinating-oci-handoffs` skill) and its report templates, migrated from
`poc-oci-serverless/docs/handoff/`.

The OCI domain packages (`oci-functions-java`, `oci-terraform`, `oci-observability`,
`oci-architecture`) depend on this package so their agents share one protocol definition instead of
duplicating it.

## Contents

- `coordinating-oci-handoffs` — knowledge skill: the handoff protocol spec
  (`blueprints/handoff-protocol.md`) + templates (`assets/*.template.md`).

## Dependencies

- `../factory-core`
