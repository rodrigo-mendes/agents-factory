# Evaluation Scenarios — develop-java-function

## Scenario 1 (Canonical): Create a new API Gateway function

**Input**: "Create a new function called `func-order-status` that receives a GET request with a store_id query param, reads from OCI Vault for a secret, and returns JSON"

**Expected agent behavior**:
- P0: Classifies as API Gateway handler; identifies integrations: Vault (SDK) + REST response
- Loads `developing-oci-functions-java/SKILL.md` and `invoking-rest-apis-from-oci-functions/SKILL.md`
- P1: Checks existing `services/*/pom.xml` for FDK/SDK versions; checks `.templates/`
- P3: Proposes class structure, handler signature, pom.xml deps, func.yaml config keys
- Waits for user approval before P4
- P4: Generates Java class extending `APIGatewayFunction`, `@FnConfiguration` with initError pattern, ResourcePrincipal auth
- P5: Runs `mvn compile`, checks CMD in Dockerfile, checks httpclient-jersey in pom.xml

**Pass criteria**: Generated code has initError catch, Dockerfile CMD matches func.yaml cmd, no credentials in func.yaml.

---

## Scenario 2 (Integration): Add event publishing to an existing function

**Input**: "Add OCI Streaming publish capability to `func-api-facade` — emit a DomainEvent after each successful object storage write"

**Expected agent behavior**:
- P0: Classifies as existing function modification; identifies integration: `publishing-events-from-oci-functions`
- Loads `publishing-events-from-oci-functions/SKILL.md` and `developing-oci-functions-java/SKILL.md`
- P1: Reads existing `services/func-api-facade/pom.xml` and handler class
- P3: Proposes StreamPublisher field, configure() changes, new pom.xml dependency
- P4: Adds `StreamPublisher` field, initializes in `configure()`, calls after putObject, wraps in try-catch
- P5: Verifies no unbounded buffering; checks SDK timeout budget

**Pass criteria**: StreamPublisher initialized in configure() not in handler(); publish errors map to 503 not 500; event key = event_type.

---

## Scenario 3 (Edge): Refactor a god-class handler

**Input**: "The `RestProxyFunction` is 600 lines. Refactor it using Extract Method and package decomposition"

**Expected agent behavior**:
- P0: Identifies as refactor request; loads `refactoring-oci-java/SKILL.md`
- P1: Scans existing class structure, identifies responsibilities (routing, auth, HTTP, transform)
- P3: Proposes extracted classes: `BrxServicesClient`, `OAuth2TokenProvider`, `StoreMapper`, etc.
- P4: Extracts to sub-packages; handler delegates only; no logic duplication
- P5: Runs `mvn compile` and `mvn test`; verifies all existing tests still pass

**Pass criteria**: Handler class < 200 lines after refactor; each extracted class has single responsibility; no new public API changes.

---

## Scenario 4 (Misuse): Request for Terraform changes

**Input**: "Create the OCI Application and subnet in Terraform for my new function"

**Expected agent behavior**:
- Identifies this as infrastructure provisioning, NOT Java development
- States clearly: "This is outside my scope — use `/provision-oci-infra` or `@oci-terraform` for Terraform"
- Does NOT attempt to write Terraform code

**Pass criteria**: Agent declines, routes to correct command, generates no Terraform.
