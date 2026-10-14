You are working in an OCI serverless project that uses **OCI Functions (Java FDK v1.1.x, Java 17)** and **Terraform (required_version >= 1.5, OCI Provider `oracle/oci` >= 6.0, < 9.0)**. (Constraints match `infra/environments/*/versions.tf` and `infra/modules/*/versions.tf`; tested with Terraform 1.11 / provider 8.x.)

## Project Conventions

- **OCI Provider source**: Always use `oracle/oci` (never `hashicorp/oci`)
- **OCID format**: All OCI resource IDs follow `ocid1.<resource_type>.<realm>.<region>.<unique_id>`
- **Tagging**: Apply `freeform_tags` to all Terraform resources using `local.common_tags`
- **Compartment isolation**: Use OCI compartment hierarchy for blast radius isolation
- **Resource Principal auth**: Functions authenticate to OCI services via Resource Principal (never user credentials)
- **Multi-function support**: Infrastructure supports multiple functions per Application via `var.functions` list and per-route targeting via `var.route_backends`

## Available Agents (Subagents)

This project has specialized subagents in `.claude/agents/`. Delegate domain-specific work to them:

- **`oci-terraform`** — Terraform provisioning of OCI infrastructure
- **`oci-functions-java`** — Java function development with FDK
- **`oci-serverless-architect`** — Architecture design and review (advisory)
- **`oci-serverless-stack`** — End-to-end function + infra creation (supports concurrent parallel delegation to `oci-functions-java` in `services/` and `oci-terraform` in `infra/`)
- **`oci-observability`** — Observability infra + design: APM & tracing, Logging, Monitoring alarms, Connector Hub, Management/APM Dashboards, live validation
- **`oci-deployer`** — Build, push, deploy, and validate functions on existing infra
- **`oci-debugger`** — Diagnose runtime issues in deployed functions (502/503/504)

## Agent Routing (Quick Reference)

Slash commands below are files in `.claude/commands/*.md` that run the listed subagent (`context: fork`, `background: false`). The fork targets (knowledge-skills they read) live in `.claude/skills/`.

| Need | Agent + Command |
|------|---------------|
| New function (Java only) | `oci-functions-java` + `/add-oci-function` |
| New function (infra only) | `oci-terraform` + `/add-functions-infra` |
| New function (end-to-end) | `oci-serverless-stack` + `/add-serverless-stack` |
| Add function to existing app | `oci-serverless-stack` + `/add-function-to-app` |
| Execute a pattern spec | `oci-serverless-stack` + `/execute-pattern` |
| **Scaffold new function (template)** | `oci-functions-java` (skill: `scaffolding-oci-function`) |
| **Deploy new version** | `oci-deployer` + `/deploy-function` |
| **Debug runtime error (502/503/504)** | `oci-debugger` + `/debug-function` |
| Object Storage infra | `oci-terraform` + `/add-object-storage-infra` |
| Logging infra | `oci-observability` + `/add-logging` |
| Connector Hub pipeline | `oci-observability` + `/add-connector-hub` |
| APM infrastructure | `oci-observability` + `/add-apm-infrastructure` |
| **APM/custom dashboards infra** | `oci-observability` + `/add-apm-dashboards` |
| Terraform project governance | `oci-terraform` + `/engineer-terraform-project` |
| Object Storage design | `oci-serverless-architect` + `/design-object-storage` |
| Logging/Observability design | `oci-observability` + `/design-logging` |
| Connector Hub design | `oci-observability` + `/design-connector-hub` |
| APM/Tracing design | `oci-observability` + `/design-apm-observability` |
| **APM dashboard design** | `oci-observability` + `/design-apm-dashboards` |
| Monitoring alarms | `oci-observability` + `/design-monitoring-alarms` |
| Full observability (3 pillars) | `oci-serverless-architect` + `/design-function-observability` |
| Function structured logging | `oci-functions-java` + `/add-function-logging` |
| Function custom metrics | `oci-functions-java` + `/add-function-metrics` |
| Function distributed tracing | `oci-functions-java` + `/add-function-tracing` |
| Function unit tests (Java) | `oci-functions-java` + `/add-function-tests` |
| Terraform project testing | `oci-terraform` + `/add-terraform-tests` |
| Function observability block | `oci-functions-java` + `/add-function-observability` |
| Architecture review | `oci-serverless-architect` + `/design-serverless-architecture` |
| Audit infra prerequisites | `oci-serverless-architect` + `/audit-infra-prerequisites` |
| **Validate observability live (4 pillars)** | skill: `validating-oci-observability` (bundled scripts under `.claude/skills/validating-oci-observability/scripts/`) |
| **Integrate with Oracle RMS/MFCS via webhook** | skill: `integrating-oracle-rms-webhooks` (webhook config, envelope EVENT/PAYLOAD, enrich by-id, OAuth IDCS; bundled scripts under `.claude/skills/integrating-oracle-rms-webhooks/scripts/`) |
| **Event-driven pub/sub architecture design** | `oci-serverless-architect` (skill: `designing-oci-event-driven-pubsub` — producer/consumer patterns, fan-out, SCH cold-start, idempotency, distributed tracing through stream) |
| **Event-driven pub/sub infra (Streaming + SCH + Functions)** | `oci-terraform` (skill: `provisioning-oci-event-driven-pubsub` — PUBLIC pool, for_each SCH fan-out, IAM 4 verbs, prevent_destroy, batch tuning) |

See `@.claude/AGENTS.md` for the full catalog of commands organized by category.

**Agent handoff:** all agent-to-agent handoffs pass through structured records in `docs/handoff/<capability>/` (work-orders forward, reports backward) — never lossy prose. Each agent reads existing records on intake and writes one on exit. Source of truth: `@docs/handoff/README.md`.

## Key Scripts

- **`scripts/preflight.sh`** — Pre-build validation (CMD, HTTP provider, credentials, Docker). Run before every build.
- **`scripts/oci-cleanup.sh`** — Tear down provisioned OCI resources.
- **`.claude/skills/validating-oci-observability/scripts/`** — Live observability validation (**5 pillars**) via OCI CLI, bundled in the `validating-oci-observability` skill. Entry point `validate-observability.sh`; also `check-{logs,metrics,traces,alarms}.sh`, `check-dashboards.sh` (**5th pillar — Management Dashboard render-readiness: widget-template/dataSource-type/regionName + ingestion cross-check**), `smoke-invoke.sh`, `trigger-alarm-test.sh` (alarm→FIRING→email), `deploy-and-validate.sh` (build+push+apply+validate runbook). Scripts resolve the repo root via `git`, so they run from any cwd.
- **`scripts/generate-dashboard-traffic.sh`** — Populate the Management Dashboards (Operations Overview, Upstream Dependencies, Route Analytics) with live API-Gateway traffic before validating. Reuses `services/func-rr-rest-proxy/scripts/simulate-webhook.sh`; runs waves (health, webhook OK/207/400, EVENT) over ~6-8 min. Env: `ROUNDS`, `SLEEP`, `API_BASE_URL` (resolved via `terraform output api_base_url`).
- **`.claude/skills/integrating-oracle-rms-webhooks/scripts/`** — RMS/MFCS webhook integration tools, bundled in the `integrating-oracle-rms-webhooks` skill: `rms-token.sh` (OAuth2 token), `rms-get.sh` (foundation by-id/delta, any entity), `register-webhook.sh` (register/list/disable on `webhooks/manage`), `simulate-webhook.sh` (POST EVENT/PAYLOAD envelope to a listener). Shared `lib-rms.sh`; resolve repo root via `git`.
- **`services/.templates/`** — `Dockerfile.template` and `func.yaml.template` for new functions.

## Build & Run

**Java Functions** (run inside each `services/<function>/`):
- `mvn compile` — compile the function (Java 17, Amazon Corretto)
- `mvn test` — run unit tests
- `mvn package` — build the deployable artifact

**Terraform** (run inside `infra/environments/dev` or `infra/environments/prod`):
- `terraform fmt -check` — verify formatting
- `terraform validate` — validate configuration
- `terraform plan` / `terraform apply` — preview / apply changes

**Deploy pipeline:**
- `scripts/preflight.sh` — run before every build (CMD, HTTP provider, secrets, Docker checks)
- Build & push the function image to OCIR, then update the image reference in `terraform.tfvars` and `terraform apply`
- Prefer the `/deploy-function` command (`oci-deployer`) for the full build → push → deploy → smoke-test lifecycle
