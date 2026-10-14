---
kind: report
from: "@oci-debugger"
to: "@oci-terraform"
refs: deploy-report.md (cycles 1-6), diagnosis-report.md
capability: event-pubsub
outcome: success
createdAt: 2026-07-22T14:34:01Z
---

## Symptom

Both Service Connectors (`sch-event-audit-dev`, `sch-event-notify-dev`) are ACTIVE and read
the stream fine (`ErrorsAtSource = 0`), but `ErrorsAtTarget` increments exactly once every
~5 min on BOTH connectors, unbroken. Consumer functions emit ZERO logs for SCH deliveries.
A direct `oci fn function invoke` of the SAME image SUCCEEDS (~6s warm-ish, 974ms app init).

## Root cause — AUTHORIZATION denial (missing `fn-function` verb), NOT cold start / image pull

The Service Connector Hub service principal lacked the `use fn-function` IAM permission on the
target compartment. OCI Connector Hub requires **TWO** statements for a Functions target:

  - `use fn-function`   — resolve/read the target function (GetFunction)
  - `use fn-invocation` — actually invoke it

The project's streaming policy had ONLY `use fn-invocation`. Without `fn-function` the
serviceconnector principal cannot resolve the function, so the invoke is **denied at the
authorization layer BEFORE the Functions invoke pipeline is entered** — no container, no
`Received` line, no app log, just a fast reject counted as `ErrorsAtTarget`. Direct invoke
works because the user (SecurityToken) principal has full permissions.

This is a FAST auth reject, decisively NOT the ~60s image-pull/cold-provision timeout that
cycles 3-4 theorized (that theory is disproven — see Evidence).

## Evidence (decisive: auth fast-fail vs 60s pull/timeout)

1. **Invoke-logging was ALREADY ENABLED** (`category: invoke`, `is-enabled: true`) on BOTH
   consumer apps — so "zero logs" is NOT a logging-config gap. The platform invoke log
   captures the full lifecycle incl. platform `Received`/`Served` lines (verified: a direct
   invoke at 13:25 logged `Received function invocation request` [containerId n/a] ->
   COLD_START 974ms -> AUDIT event -> `Served ... in 6.257 seconds`).
2. **The SCH invocations produce ZERO invoke-log entries.** Window 13:29-13:45 recorded
   **4 ErrorsAtTarget** (audit: 13:29, 13:34, 13:39, 13:44) with **0 invoke-log rows** — not
   even a `Received function invocation request`. Notify identical: 0 rows across 13:00-13:45
   while ErrorsAtTarget kept climbing.
   => This is the AUTH signature. A 60s image-pull/cold timeout WOULD show `Received` + 60s +
   a `444 Client request aborted` (exactly what cycle-4's DIRECT invoke on a fresh host
   showed). The SCH invocations show NOTHING before the reject => denied before the pipeline
   => authorization failure, not a timeout.
3. **ErrorsAtTarget cadence = 1 per ~5-min SCH poll cycle** (13:04,09,14,19,24,29,34,39,44),
   one clean error per cycle — no retry-burst / no delayed-by-60s pattern.
4. **No `LatencyAtTarget` metric is emitted at all** (only ErrorsAtSource/ErrorsAtTarget
   exist for the connector) — no invocation ever produced a measurable target round-trip,
   consistent with pre-invoke rejection.
5. **SCH wiring is correct** (ruling out contract/payload): audit SCH source=streaming,
   cursor=TRIM_HORIZON, target kind=functions -> `...4gsk4nyx7a` (correct), batch 60s/128kb,
   lifecycle ACTIVE, `lifecycle-details` empty. The ConnectorHub-shaped batch works on direct
   invoke, so hypothesis 3 (payload contract) is ruled out.
6. **Image size is a red herring for this failure.** Yes the image is 2.28 GB and a fresh-host
   cold provision is ~60s — but that path is never reached; the invoke is rejected at auth
   first. Image-slim is NOT required to unblock fan-out.

## Answers to the coordinator's 3 questions

1. **Auth vs 60s pull?** AUTH, decisively. Failed SCH invokes are FAST rejects with ZERO
   invoke-log entries (no `Received`, no container, no 444) — the opposite of the 60s
   pull/timeout signature (which logs `Received` -> 60s -> 444). Invoke-logging was NOT
   disabled — it was already ON; the "zero logs" is because the request never reached the
   Functions pipeline (auth-denied upstream).
2. **Is the compartment-scoped `where {request.principal.type='serviceconnector'}` form
   sufficient?** YES for this tenancy/setup. Proof: the SIBLING statement
   `Allow any-user to {STREAM_READ, STREAM_CONSUME} ... where all {request.principal.type=
   'serviceconnector'}` uses the exact same principal-type condition and WORKS
   (ErrorsAtSource=0 — the SCH reads the stream). So the principal-type match resolves the
   serviceconnector correctly; the ONLY missing piece is the `fn-function` VERB. A
   `request.principal.compartment.id` condition is NOT needed (the working stream-read
   statement doesn't use one either). Keep the form; just add the verb.
3. **Evidence it's NOT auth?** None found. All evidence points to auth. Image size stays OUT
   of scope for this blocker.

## Exact fix (already staged by coordinator — VERIFIED correct)

`infra/modules/iam/main.tf`, streaming policy statements list, ADD (present at lines 96-97):

    "Allow any-user to use fn-function   in compartment ${var.compartment_name} where all {request.principal.type='serviceconnector'}",
    "Allow any-user to use fn-invocation in compartment ${var.compartment_name} where all {request.principal.type='serviceconnector'}",

The `fn-function` line is the new/required one; `fn-invocation` already existed. The staged
edit matches this exactly. No other change needed. (Note: the local
`provisioning-oci-connector-hub` skill's verb table at
`blueprints/never-do-patterns.md:163` lists only `use fn-invocation` for Functions targets —
that skill is INCOMPLETE and should be corrected to require BOTH `fn-function` +
`fn-invocation`, matching OCI's official overview.htm.)

## Classification

**infra / IAM policy** — a missing verb in the streaming policy module. NOT code, NOT image
size, NOT network, NOT cold start. Solvable while KEEPING the SCH->Function pattern (no
architecture change, no async decouple needed).

## Related: revert provisioned_concurrency

PC=10 (20 warm 1024MB containers) was added chasing the cold-start theory, which is now
disproven as the cause of ErrorsAtTarget. Once the fn-function policy lands and fan-out is
green, PC can safely revert to 0 (a parallel agent was already reverting it). Warm containers
did NOT and could not fix an auth denial — consistent with cycle-6's observation that PC=10
still failed.

## Next action

**Hand off:** `@oci-terraform` — apply the staged `infra/modules/iam/main.tf` fn-function
statement (`terraform apply`, expect the streaming policy to update in place; IAM policy
propagation is usually seconds but can take up to ~1 min). Then confirm fan-out:
`ErrorsAtTarget` goes FLAT on both connectors AND both consumer invoke logs show the next
event_id (audit "AUDIT event"; notify httpbin forward). If ErrorsAtTarget persists >2 min
after apply, re-check for IAM propagation delay before reopening. Context: this file.

## Session / blockers

- Session valid through the ~16:01 window; all live OCI calls completed, no 401.
- No fix applied by me (diagnosis only). The fn-function edit was staged by the coordinator
  and is verified correct in `infra/modules/iam/main.tf` lines 96-97.
