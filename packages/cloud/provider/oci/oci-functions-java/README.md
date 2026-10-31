# oci-functions-java

Knowledge skills + agents for the **OCI Functions Java lifecycle** (OCI Functions FDK Java 1.1.x,
Java 17). Migrated from the authored `poc-oci-serverless` package and normalized to the APM house
standard. Part of the OCI family (siblings: `oci-terraform`, `oci-observability`, `oci-architecture`).

## Skills (11 migrated + 3 routing)

Develop / scaffold / test / refactor the function, plus event, Object Storage, REST, event-publishing
and RMS-webhook integrations, and deploy + debug:

`developing-oci-functions-java`, `scaffolding-oci-function`, `implementing-oci-functions-events`,
`integrating-oci-functions-objectstorage`, `invoking-rest-apis-from-oci-functions`,
`publishing-events-from-oci-functions`, `testing-oci-functions-java`,
`integrating-oracle-rms-webhooks`, `deploying-oci-functions`, `debugging-deployed-functions`.

`refactoring-oci-java` and the `java-functions-clean-code` rule live in the `java/clean-code/clean-code-oci` package
(a dependency of this one), so they still install with it.

Three action-command routing skills front the agents: `develop-java-function`, `deploy-oci-function`,
`debug-oci-function`.

## Agents

| Agent | Role |
|---|---|
| `oci-functions-java` | develops/modifies Java function code (FDK workflow) |
| `oci-deployer` | builds, pushes, deploys and validates images (preflight gate) |
| `oci-debugger` | diagnoses runtime 5xx on deployed functions |

All three are non-interactive executors (`tools:` minimal, `model: sonnet`, no `Agent`/plan-mode).

## Instructions

17 path-scoped instruction files (`java-functions-*`, `java-environment-validation`,
`deployment-preflight-checks`) applied to Java sources, `pom.xml`, `func.yaml`, `Dockerfile`.

## Worked examples (from the reference PoC)

Blueprints cite real code from `workspace/poc-oci-serverless/` — `services/func-event-producer`,
`func-evt-consumer-*`, `func-api-facade`, `api-handler`, `libs/obs-commons`, and the
`services/.templates` scaffold. The PoC application code is **not** packaged; it remains the live
example repository.

## Dependencies

- `../factory-core`
