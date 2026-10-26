---
name: debug-oci-function
description: "Debugs a deployed OCI Function via the oci-debugger agent (P0-P4 diagnostic workflow: classify symptom, investigate infra, query logs, systematic elimination, propose fix). Use when a deployed function returns HTTP 502/503/504/500 or fails to initialize."
argument-hint: "Function name and symptom (e.g. 'func-rr-rest-proxy returns 502', 'event-producer 503 OAuth 401')"
context: fork
agent: oci-debugger
disable-model-invocation: true
---

Routes to the `oci-debugger` agent for systematic runtime diagnosis of deployed OCI Functions.

The agent executes a 5-step workflow (P0-P4): classify symptom by HTTP status code,
investigate infrastructure config via OCI CLI, query OCI Logging, perform systematic
elimination, and produce a targeted fix with a `diagnosis-report.md`.

## What This Command Does

Delegates runtime diagnosis to `oci-debugger`:

- Reads any existing `docs/handoff/<capability>/deploy-report.md` to skip rediscovery
- Invokes the problematic endpoint to capture current HTTP status and response body
- Queries OCI infrastructure (application config, function config, Vault secrets)
- Queries OCI Logging for container crash output
- Follows per-status elimination paths (502 → Dockerfile; 503 → Vault/OAuth; 504 → timeout budget; 500 → code error)
- Writes `docs/handoff/<capability>/diagnosis-report.md` with exact fix (file + change)

## What This Command Does NOT Do

- Make code changes directly (proposes fixes; delegates code changes to `/deploy-oci-function`)
- Diagnose telemetry gaps (HTTP 2xx but logs/metrics/traces missing → use `validating-oci-observability` skill)

## Skills the agent loads

| Situation | Skill |
|---|---|
| Always | `debugging-deployed-functions` |
| 2xx but telemetry missing | `validating-oci-observability` (external) |
| Code fix needed | `developing-oci-functions-java` |
| RMS/webhook errors | `integrating-oracle-rms-webhooks` |

## Evaluation Scenarios

See [blueprints/evaluation-scenarios.md](./blueprints/evaluation-scenarios.md)
