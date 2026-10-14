---
kind: report
from: "@oci-debugger"
to: "@oci-serverless-architect"
refs: deploy-report.md (cycles 1-7), diagnosis-report-sch-auth.md
capability: event-pubsub
outcome: blocked
createdAt: 2026-07-22T17:39:35Z
---

## VERDICT (viability gate)

**BLOCKED — could not complete live confirmation: the OCI CLI session (profile `poc`) expired
mid-investigation** ("This CLI session has expired"), before I could pull the live
`ErrorsAtSource` trend, `sch service-connector get` lifecycle-details, or `stream-pool get`
endpoint type. Per the work order ("If session 401, report and stop") I stopped the live probe.

But the SOURCE-CODE + HANDOFF evidence already point to a **strong, near-decisive hypothesis (a):
the PRIVATE-endpoint-only Stream Pool is the most likely cause of `ErrorsAtSource`.** This is
flagged as **HIGH-confidence-but-UNCONFIRMED**; the single live check needed to make it
decisive is listed at the bottom. I recommend the architect NOT green-light GraalVM-native
consumer work until that one check is run — the whole SCH fan-out may need a redesign.

## Why hypothesis (a) — private stream pool unreachable by SCH — is the lead

1. **Our pool is PRIVATE-endpoint-only, by module design.**
   `infra/modules/streaming/main.tf` creates `oci_streaming_stream_pool.this` with ONLY a
   `private_endpoint_settings { subnet_id, nsg_ids }` block — no public access. The module
   header even states the intent literally: "✅ Always Do: private endpoint …" and
   "🚫 Never Do: pool público". Live facts from the handoff match: pool
   `...rwntx7gzy7a`, endpoint host `hrwntx7gzy7a.streaming.sa-saopaulo-1.oci.oraclecloud.com`,
   private endpoint IP **10.0.1.131**, reachable only from inside the VCN.

2. **The producer only reaches the stream because it runs INSIDE the VCN.** Cycle 2 had to add
   an NSG self-ingress 443 rule so the producer function (in the functions subnet) could hit the
   Stream Pool PE at 10.0.1.131:443. That confirms the stream's data plane is VCN-internal only.

3. **SCH is an Oracle-managed service running OUTSIDE our VCN.** A Service Connector reads a
   Streaming source over the service's own network path, not from inside the customer VCN and
   not through the customer's private endpoint / NSG. It has no route to 10.0.1.131. A stream
   pool that exposes ONLY a private endpoint therefore has no address the SCH source stage can
   reach → the read fails → **`ErrorsAtSource`**, and the pipeline never advances to the invoke
   stage → **`FunctionInvocationCount` stays 0** (exactly the coordinator's reported symptom).

4. **The timeline is the tell, and it is NOT an IAM verb issue.** The prior report
   (`diagnosis-report-sch-auth.md`) correctly diagnosed the earlier `ErrorsAtTarget` as a missing
   `use fn-function` verb, and IAM already grants `{STREAM_READ, STREAM_CONSUME}` to
   `request.principal.type='serviceconnector'` — with `ErrorsAtSource=0` proving the SCH principal
   was reading fine through cycles 1-6. So the read verb is present; `ErrorsAtSource` is NOT a
   missing-permission problem.
   - **Crucial nuance:** through cycles 1-6, `ErrorsAtSource=0` — SCH was reading the private
     pool. That would seem to CONTRADICT hypothesis (a)… **UNLESS** the reachability changed at
     ~14:41. The coordinator reports `ErrorsAtSource` began climbing immediately after the
     `fn-function` apply. An IAM policy `apply` in this module can only have changed the target
     verb; it does not touch networking. So one of two things is true and the live check must
     disambiguate:
       (a-1) A concurrent/ancillary change around 14:41 (pool recreate, subnet/NSG edit, or a
             stream-pool endpoint flip) broke source reachability — check stream-pool + recent
             work-requests; OR
       (a-2) `ErrorsAtSource` was actually intermittent all along and only became visible/steady
             once `ErrorsAtTarget` stopped masking the connector's error accounting — i.e. the
             private-pool read was always marginal.
   - Either way the productive question the gate asks — "can SCH read a PRIVATE-endpoint-only
     pool?" — remains the pivot, because if the answer is "no", the design is blocked; if "yes,
     it was reading fine until 14:41", then something at 14:41 regressed the source and we chase
     that instead.

## Alternatives NOT yet ruled out (need the live check)

- **(b) IAM / cursor / consumer-group issue** — LOW. IAM stream-read verbs are present and were
  working (ErrorsAtSource=0 for 6 cycles). A cursor/consumer-group fault is possible but would
  not typically start exactly at an IAM-target apply. Rank below (a).
- **(c) Transient** — MUST be excluded by the live trend. If `ErrorsAtSource` is flat/declining
  now and `FunctionInvocationCount` has resumed, it was a blip from the 14:41 apply and the gate
  is GREEN. The coordinator's report of a *climbing* trend argues against transient, but I could
  not confirm it live.

## Fix IF confirmed (a): private pool is the blocker

OCI Streaming pools are effectively **public OR private at creation** — the endpoint type is set
via `private_endpoint_settings` and is **immutable**; you cannot add a public messages endpoint
to an already-private pool in place. Making the stream reachable by the Oracle-managed SCH
service therefore requires a **public (default) Stream Pool** — i.e. DROP the
`private_endpoint_settings` block. In `infra/modules/streaming/main.tf` that is:

    resource "oci_streaming_stream_pool" "this" {
      compartment_id = var.compartment_ocid
      name           = "sp-${var.project_name}-${var.environment}"
      # REMOVE private_endpoint_settings { ... }  -> pool becomes public-endpoint (Oracle-managed reachable)
      kafka_settings { auto_create_topics_enable = false }
      ...
    }

**DATA-LOSS / DESTROY implication (must warn the architect + user):** removing/altering
`private_endpoint_settings` is an **immutable change → destroy+recreate of the Stream Pool AND
the Stream inside it** (partitions/retention are also immutable, same module warning). That
**drops all buffered events** and rotates `stream_id` / `stream_pool_id` OCIDs — every consumer
of those OCIDs (producer config, both SCH sources, IAM if resource-scoped) must be re-pointed.
For a POC with no durable data this is acceptable, but it is NOT an in-place edit.

## Is "both Functions + SCH" VIABLE with our current private stream?

- If (a) confirmed: **NOT viable as-is.** The Oracle-managed SCH cannot source from a
  private-endpoint-only pool. Minimal change to make it viable = **recreate the Stream Pool as
  public** (destroy/recreate, POC-acceptable) and re-point producer + both SCH sources. The
  SCH→function *target* auth is already fixed (`fn-function` + `fn-invocation`), so once the
  source is reachable, fan-out should complete.
- If (a-2)/(b): viable; fix the specific regression (source reachability change at 14:41, or
  cursor/group) without a pool recreate.
- If (c): already viable; just noise from the apply.

## Classification

**infra (networking/streaming endpoint reachability)** — NOT code, NOT function memory/cold-start
(that whole thread was superseded), NOT the target IAM verb (already fixed). This gates the
architecture, so routed to `@oci-serverless-architect`.

## THE ONE LIVE CHECK that makes this decisive (run after re-auth)

`oci session authenticate --profile poc` (region sa-saopaulo-1), then:

1. **Stream-pool endpoint type** (the crux):
   `oci streaming admin stream-pool get --stream-pool-id ocid1.streampool.oc1.sa-saopaulo-1.amaaaaaa543c4nya7apf46snztt2ne4kz3ldzpwfx43hg6gghrwntx7gzy7a --auth security_token`
   → look at `private-endpoint-settings` (present ⇒ private-only ⇒ hypothesis (a) confirmed) and
   `endpoint-fqdn`. A private-only pool has NO public messages endpoint the SCH can reach.
2. **Confirm the trend is real, not transient** (last ~2h, per connectorId `...3mmwluvjpt` notify /
   `...tuoccrobef` audit):
   `oci monitoring metric-data summarize-metrics-data` namespace `oci_service_connector_hub`,
   queries `ErrorsAtSource[1m].sum()`, `ErrorsAtTarget[1m].sum()`, `MessagesFromSource[1m].sum()`,
   `FunctionInvocationCount[1m].sum()`. Expect: ErrorsAtSource climbing, MessagesFromSource≈0,
   FunctionInvocationCount=0 ⇒ source-stage failure confirmed.
3. **Lifecycle detail / error surface:**
   `oci sch service-connector get --service-connector-id <notify|audit> --auth security_token
   --query 'data.{state:"lifecycle-state",details:"lifecycle-details",source:source}'` — read
   `lifecycle-details` for an explicit source-read error string.
4. **What changed at ~14:41** (disambiguate a-1 vs a-2): check stream-pool + stream
   work-requests / audit events around 14:41 for any pool/subnet/endpoint mutation coincident
   with the IAM apply.

## Next action

**Hand off:** `@oci-serverless-architect` — VIABILITY GATE is OPEN pending ONE live check
(stream-pool endpoint type, step 1 above). If the pool is private-endpoint-only (highly likely
per module source), the SCH→function fan-out design is BLOCKED on the source side and requires a
**public Stream Pool recreate** (destroy/recreate, data-loss, OCID rotation) or an alternative
source path — decide before investing in GraalVM-native consumer work. Context: this file +
diagnosis-report-sch-auth.md + deploy-report.md.

## Session / blockers

- **Session expired mid-run** (profile `poc`); a `region list` succeeded at the very start of
  this session, then every subsequent OCI call returned "This CLI session has expired". Re-auth
  is interactive → could not proceed. No state changed (read-only task; no writes attempted).
- All non-live evidence (module source, immutability of `private_endpoint_settings`, cycle
  timeline, IAM verb history) stands independent of the session and is captured above.
