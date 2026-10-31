# oci-core

Shared core for the **OCI agent family**. Holds the cross-agent **handoff protocol**
(`coordinating-oci-handoffs` skill) and its report templates, migrated from
`poc-oci-serverless/docs/handoff/`.

The OCI domain packages (`oci-functions-java`, `oci-terraform`, `oci-observability`,
`oci-architecture`) depend on this package so their agents share one protocol definition instead of
duplicating it.

## Contents

- `coordinating-oci-handoffs` — knowledge skill: the OCI profile of the generic handoff protocol
  (`coordinating-agent-handoffs`, protocol v1): OCI specifics in `blueprints/handoff-protocol.md`,
  `assets/handoff-profile.yaml` and templates (`assets/*.template.md`). Result records are
  `result-*.md` (no record file name starts with `report`).

## Dependencies

- `../factory-core`
- `../handoff-core` (generic protocol, scripts, `spec-synchronizer`)
