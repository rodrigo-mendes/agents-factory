# Evaluation Scenarios — designing-oci-event-driven-pubsub

Scenarios used to validate that this skill produces correct architectural guidance for OCI event-driven pub/sub patterns.

---

## Scenario 1 — Greenfield pub/sub design for dual consumers

**Query**

Design a pub/sub architecture where an API receives order events and two downstream systems need to react: one sends a notification via REST, another writes an audit record to a database. We want both consumers to receive every event.

**Expected behavior**

- Recommends API Gateway → func-event-producer → OCI Streaming (PUBLIC pool) → 2 separate `oci_sch_service_connector` → func-evt-consumer-notify + func-evt-consumer-audit
- Specifies PUBLIC stream pool because SCH is the source — explicitly states that a PRIVATE-endpoint-only pool makes SCH's `ErrorsAtSource` increment and consumers never fire
- Specifies two separate SCH connector resources (not one connector with two targets, which is not a valid SCH schema)
- Includes standard message envelope with `event_id` (idempotency), `event_type` (partition key), `correlation_id` (tracing), `timestamp`
- Recommends `event_type` as the `PutMessages` key for partition-level ordering
- Specifies consumer function memory >= 1024 MB and timeout = 300 s to allow SCH sync cold-start to complete
- Lists all four required IAM verbs: `stream-push` (producer DG), `STREAM_READ` + `STREAM_CONSUME` (serviceconnector), `fn-function` (serviceconnector), `fn-invocation` (serviceconnector)
- Points to pattern docs `docs/patterns/02-event-driven/02-event-driven-pub-sub.md`, `02a`, `02b` for implementation detail
- Identifies the two consumer variants: 02a REST consumer (notify) and 02b database consumer (audit)

---

## Scenario 2 — Diagnosing ErrorsAtTarget with zero function log entries

**Query**

Our SCH connector is ACTIVE and we can see ErrorsAtSource = 0 after deploying, but ErrorsAtTarget is incrementing every 5 minutes and we see ZERO function log entries, not even 'Received'. What is the architecture issue?

**Expected behavior**

- Identifies the symptom: `ErrorsAtTarget` incrementing + zero function logs (no 'Received') = fast authorization rejection BEFORE the Functions invoke pipeline
- Distinguishes this from cold-start ceiling: cold-start shows 'Received' + ~60 s + 444 abort; auth reject shows NOTHING in function logs
- Diagnoses missing `use fn-function` IAM verb — SCH requires BOTH `fn-function` (resolve/GetFunction) AND `fn-invocation` (invoke); `fn-function` alone being missing produces fast deny before any container is started
- Prescribes adding `Allow any-user to use fn-function in compartment X where all {request.principal.type=serviceconnector}`
- Notes that `fn-invocation` alone was present (`ErrorsAtSource=0` proves the stream-read verbs work), and that the `serviceconnector` principal-type condition is correct
- References `diagnosis-report-sch-auth.md` and `infra/modules/iam/main.tf` lines 92–93 as evidence
- Does NOT suggest checking memory, timeout, image size, or network (those are cold-start concerns, not auth-reject concerns)

---

## Scenario 3 — SCH cold-start ceiling: 444 abort after 60 s despite memory increase

**Query**

We deployed consumer functions with memory=256MB, timeout=60s. SCH ErrorsAtTarget increments every 5 minutes, function logs show 'Received function invocation request' then 60 seconds of silence then '444 - Client request aborted'. We raised memory to 1024MB but the problem persists. What is the architectural decision we need to make?

**Expected behavior**

- Correctly identifies this as the SCH cold-start ceiling: ~60 s of platform container provisioning + JVM pre-main class-loading before application code runs
- Distinguishes from auth reject: 'Received' IS present (so the invoke pipeline was entered, auth OK); the 60 s then 444 = SCH sync deadline exceeded during cold provisioning
- Explains that memory bump (256 → 1024 MB) raises CPU allocation but does NOT eliminate the ~60 s pre-main gap — it is platform + JVM class-loading outside application control
- Presents the four escapes:
  1. `timeout=300s` + `memory=1024MB` let cold-provision complete within deadline (cheapest; confirmed working in cycle 10)
  2. Provisioned Concurrency eliminates cold start but minimum = 10 containers per function (not 1)
  3. GraalVM native image brings cold-start to ~2–5 s
  4. Async decouple via ONS/Queue removes sync deadline
- Flags the PC minimum-10 caveat: `count=1` is rejected with `400 InvalidParameter: Count must be a multiple of 10`
- Recommends raising `timeout` to 300 s alongside the existing 1024 MB as the cheapest first fix
- References `diagnosis-report.md` (55 s pre-main gap evidence) and `deploy-report.md` (cycle 10 confirmation)
