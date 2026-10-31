---
name: java-functions-skills
description: "Skill and command routing guide for OCI Functions Java. Use when determining which skill or command to invoke for a given development task."
paths:
  - "**/src/main/java/**/*.java"
  - "**/func.yaml"
  - "**/pom.xml"
---
## ⚠️ Check Commands First!

Before loading skills directly, check if a command exists for the user's request:

| User Intent | Command (agent) |
|---|---|
| Create or change a function (handler, API Gateway backend, event handler, event publishing, REST client, Object Storage, tests, instrumentation) | `/develop-java-function` (`@oci-functions-java`) |
| Provision or change OCI infrastructure for a function | `/provision-oci-infra` (`@oci-terraform`) |
| Full stack (function + infra + API Gateway route) | `/provision-oci-serverless-stack` (`@oci-serverless-stack`) |
| Deploy a function version | `/deploy-oci-function` (`@oci-deployer`) |
| Diagnose a deployed function | `/debug-oci-function` (`@oci-debugger`) |
| Design, provision or validate observability infrastructure | `/observe-oci-workload` (`@oci-observability`) |
| Architecture design/review | `/design-oci-architecture` (`@oci-serverless-architect`) |
| Tear down a test compartment | `/cleaning-up-oci-resources` (dry-run only by the agent) |

**If a command matches** → Recommend it to the user. Commands provide guided workflows with context collection.

**If no command matches** → Proceed with skill loading below.

---

## Skill Directory Mapping

Use this table to identify which skill(s) to load based on trigger keywords in the user's request:

### Java Function Development Skills

| Keyword Triggers | Skill File | Focus Area |
|---|---|---|
| function, handler, FDK, new function, entry point | `developing-oci-functions-java/SKILL.md` | FDK lifecycle, handler patterns, hot function model |
| refactor, clean code, SOLID, extract method, legibilidade, readability, decompose, god class | `refactoring-oci-java/SKILL.md` | Behavior-preserving refactor: Extract Method, package decomposition, DRY, records, facade |
| event handler, typed events, fn-events, APIGatewayFunction, ConnectorHubFunction, NotificationFunction | `implementing-oci-functions-events/SKILL.md` | Typed event abstractions, request/response helpers |
| object storage, file, bucket, upload, download, InputStream | `integrating-oci-functions-objectstorage/SKILL.md` | Object Storage read/write, InputStream lifecycle, OOM prevention |
| REST client, invoke api, http call, OAuth2, external service | `invoking-rest-apis-from-oci-functions/SKILL.md` | HttpClient, OAuth2 Client Credentials, timeout budget |
| rms, oracle rms, merchandising, mfcs, webhook, merchintegrations, foundation/item, rest proxy | `integrating-oracle-rms-webhooks/SKILL.md` | RMS/MFCS webhook: config webhooks/manage, envelope EVENT/PAYLOAD, enrich by-id, OAuth2 IDCS |
| publish event, send notification, emit, streaming, queue, monitoring | `publishing-events-from-oci-functions/SKILL.md` | OCI Streaming, Notifications, Queue, Monitoring publishing |
| test, unit test, FnTestingRule, mock, testing, fn-events-testing, APIGatewayTestFeature | `testing-oci-functions-java/SKILL.md` | FnTestingRule, OCI SDK mocking, hot function test patterns, fn-events testing |
| logging, log4j, logback, slf4j, structured logging, MDC | `logging-oci-java-functions/SKILL.md` | Java logging framework selection, OCI Logging integration, log ingestion |
| metrics, custom metrics, PostMetricData, monitoring client | `monitoring-oci-java-functions/SKILL.md` | Custom metric ingestion, OCI Monitoring API, oci_faas alarms |
| observability, three pillars, full observability, tracing | `observing-oci-java-functions/SKILL.md` | Umbrella: logging + metrics + tracing orchestration |

### Architecture & Design Skills

| Keyword Triggers | Skill File | Focus Area |
|---|---|---|
| architecture, multi-function design, serverless patterns | `architecting-oci-serverless/SKILL.md` | Reference architecture, composition patterns |
| api gateway design, api architecture, routes | `designing-oci-api-gateway/SKILL.md` | API design, auth strategy, rate limiting |
| security design, vault architecture, secrets management | `designing-oci-vault-security/SKILL.md` | Vault patterns, secret rotation, encryption |
| observability architecture, monitoring strategy | `observing-oci-java-functions/SKILL.md` | Full observability design (logging + metrics + tracing) |

---

## Mandatory Cross-Cutting Rules

These rules apply **regardless** of which specific skill is loaded:

### ✅ Always Do

1. **Resource Principal authentication** — never hardcode credentials, API keys, or user auth
2. **InputStream lifecycle** — always close in finally block; never buffer entire stream in memory
3. **SDK client caching** — initialize in `@FnConfiguration`, reuse across invocations (hot function model)
4. **Timeout budget management** — reserve 10-15% for cleanup; fail gracefully before FDK timeout
5. **Structured error responses** — return proper HTTP status codes via API Gateway response helpers
6. **func.yaml configuration** — declare memory, timeout, and config keys explicitly

### 🚫 Never Do

1. **Never store state between invocations** — functions may cold-start at any time
2. **Never use Thread.sleep()** — waste of execution budget in serverless context
3. **Never catch generic Exception without re-classifying** — use BmcException hierarchy
4. **Never log sensitive data** — no OCIDs of secrets, no credentials, no PII in logs
5. **Never use unbounded collections** — always paginate or set explicit size limits

---

## Multi-Skill Composition

When a request requires multiple skills, load them in this order:

1. **Base**: `developing-oci-functions-java/SKILL.md` (always loaded first)
2. **Event type**: `implementing-oci-functions-events/SKILL.md` (if typed event handling needed)
3. **Integration**: One or more of: object-storage, rest-apis, publishing-events
4. **Design context**: Architecture skills (if designing new function responsibilities)
5. **Testing**: `testing-oci-functions-java/SKILL.md` (if writing or discussing tests)

### Composition Pattern
```
P0: Load base skill → classify function type → load event skill → load integration skills
P2: Merge ✅/🚫 rules from all loaded skills (most restrictive wins on conflicts)
P4: Generate code applying all patterns in composition order
```

---

## Version Compliance

| Component | Required Version | Notes |
|---|---|---|
| Java | 17 | Minimum for OCI Functions |
| FDK (com.fnproject.fn) | 1.0.186+ | Hot function model support |
| fn-events | 1.1.x | Typed event abstractions |
| OCI SDK (com.oracle.oci.sdk) | 3.86+ | Resource Principal v2.2 |
| Maven | 3.8+ | Build tool |

---

## Agent Hand-offs

For requests outside Java function scope (user-mediated: tell the user the command to run):
- **Terraform provisioning** → Hand off: run `/provision-oci-infra` (`@oci-terraform`)
- **Observability infra/design** (APM, logging, alarms, connector-hub, dashboards) → Hand off: run `/observe-oci-workload` (`@oci-observability`)
- **Architecture review** → Hand off: run `/design-oci-architecture` (`@oci-serverless-architect`)
- **Full stack (Java + Terraform)** → Hand off: run `/provision-oci-serverless-stack` (`@oci-serverless-stack`)
- **Function testing** → follow the `java-functions-testing` rule for `**/src/test/java/**/*.java`
