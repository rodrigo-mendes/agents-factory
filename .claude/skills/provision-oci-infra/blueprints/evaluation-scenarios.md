# Evaluation Scenarios — provision-oci-infra

These scenarios verify that the `oci-terraform` agent is invoked correctly and that the skill
routes to the right provisioning sub-skill for each service scope.

---

## Scenario 1: Single-service provisioning (Functions)

**Input:**
```
/provision-oci-infra api-handler functions
```

**Expected agent behavior:**
- Agent `oci-terraform` is forked (not answered inline).
- P0 loads `provisioning-oci-functions/SKILL.md`.
- P1 scans existing `.tf` files for provider version and existing `oci_functions_application` resources.
- P3 presents a plan listing the `oci_functions_application` + `oci_functions_function` resources to create, naming convention, and any `⚠️ Ask First` items (e.g., provisioned concurrency, shape selection).
- P4 generates module code under `infra/modules/function-app/` only after explicit user approval.
- P5 runs `terraform fmt -check` and `terraform validate`; writes `docs/handoff/api-handler/report-terraform-infra.md`.

**Pass criteria:**
- Output `.tf` files contain `provider "oci"` with source `oracle/oci` (never `hashicorp/oci`).
- No hardcoded OCIDs in generated code.
- All variables have `type`, `description`, and `validation` blocks.

---

## Scenario 2: Multi-service provisioning (API Gateway + IAM)

**Input:**
```
/provision-oci-infra event-pubsub streaming connector-hub
```

**Expected agent behavior:**
- Agent `oci-terraform` is forked.
- P0 loads `provisioning-oci-streaming/SKILL.md` and `provisioning-oci-connector-hub/SKILL.md`.
- P2 extracts layer-order constraint: IAM must be provisioned before connector activation.
- P3 presents a two-layer plan: Layer 1 = `oci_streaming_stream_pool` + `oci_streaming_stream`; Layer 2 = `oci_sch_service_connector` with `depends_on = [var.iam_dependencies]`.
- P4 generates `prevent_destroy = true` on `oci_streaming_stream` (Never Do pattern).

**Pass criteria:**
- Generated stream module includes `lifecycle { prevent_destroy = true }` on the stream resource.
- Connector module includes `depends_on` referencing IAM outputs.

---

## Scenario 3: Validation catches hardcoded OCID

**Input:** User provides `.tf` code containing `compartment_id = "ocid1.compartment.oc1..aaaaaa..."`.

**Expected agent behavior:**
- P5 check flags `🚫 Never Do: hardcoded OCIDs` from the loaded skill.
- Agent rejects the code and requests the user to parametrize via `var.compartment_ocid`.
- Corrected code uses `validation { condition = can(regex("^ocid1\\.", var.compartment_ocid)) }`.

**Pass criteria:**
- Agent does not write a `.tf` file with a hardcoded OCID.
- Correction suggestion includes the `can(regex(...))` validation pattern.

---

## Scenario 4: Full-stack provisioning triggers P3 approval gate

**Input:**
```
/provision-oci-infra serverless-poc full-stack
```

**Expected agent behavior:**
- P0 loads `provisioning-oci-serverless-stack/SKILL.md`.
- P3 presents a complete plan across all layers (Networking → IAM → Functions → API Gateway → Streaming → Events → Observability).
- Agent halts at P3 and explicitly requests user approval before any file is written.
- P4 only executes after the user types an affirmative response.

**Pass criteria:**
- No `.tf` files generated before user approval at P3.
- Generated files cover all 7 service layers with cross-module output references (no duplicated variables between modules).
