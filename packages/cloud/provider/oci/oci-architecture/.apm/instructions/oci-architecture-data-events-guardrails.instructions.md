---
name: oci-architecture-data-events-guardrails
description: "OCI Object Storage and event-driven pub/sub architecture guardrails (rules OCI-R55 to OCI-R64, R72, R82 to R85, R89 to R92, R104 to R106, R111 to R115). Use when editing or reviewing OCI Terraform for buckets, Streaming, Service Connector Hub or architecture handoff work-orders."
applyTo: "**/oci/**/*.tf,**/*oci*/**/*.tf,docs/handoff/**"
---

# OCI Architecture Guardrails — Object Storage and Event-Driven Pub/Sub

Technical facts live in the architecture skills of the `oci-architecture` package. This rule states
what to check and where to look; it does not duplicate skill bodies. Tags `(unverified)` and
`(medium confidence)` from a skill apply here too. Rule IDs come from the OCI family rules
(Architecture Rules section). Platform, gateway, networking and Vault rules are in
`oci-architecture-guardrails`.

Skill abbreviations: **OBJ** `designing-oci-object-storage`,
**PUB** `designing-oci-event-driven-pubsub`, **SRV** `architecting-oci-serverless`.

## Always

- **OCI-R55** — Explicit `access_type = "NoPublicAccess"` on every bucket. (OBJ)
- **OCI-R56** — Lifecycle policy with an ABORT rule for multipart uploads; previous-version rule on versioned buckets. (OBJ)
- **OCI-R57** — `object_events_enabled` + OCI Events for pipelines; consumers tolerate at-least-once. (OBJ)
- **OCI-R58** — PUBLIC stream pool whenever Service Connector Hub is the source. (PUB)
- **OCI-R59** — Standard message envelope (`event_id`, `event_type`, `payload`). (PUB)
- **OCI-R60** — `event_type` as the partition key. (PUB)
- **OCI-R61** — Idempotent consumers keyed by `event_id`. (PUB)
- **OCI-R62** — One Service Connector per consumer. (PUB)
- **OCI-R63** — SCH-target functions: timeout 300 and memory at least 1024 MB. (PUB)
- **OCI-R64** — Monitor `ErrorsAtSource` and `ErrorsAtTarget` separately. (PUB)

## Ask First

Resolve each as `[Decision] → Recommendation`, or return a numbered question if the request does
not settle it. Options and trade-offs are in the named skill.

- **OCI-R104** — Storage tier; immutable after bucket creation. (OBJ)
- **OCI-R105** — Data protection: versioning / retention rules / replication; locked retention cannot be shortened. (OBJ)
- **OCI-R106** — Access pattern: dynamic group, user policy, PAR, CDN over private bucket, public bucket. (OBJ)
- **OCI-R111** — Consumer variant: REST, database, event chain, custom. (PUB)
- **OCI-R112** — Stream pool type; immutable after creation. (PUB)
- **OCI-R113** — SCH cold-start mitigation (needs tolerable latency and budget). (PUB)
- **OCI-R114** — Cursor strategy `LATEST` vs `TRIM_HORIZON`. (PUB)
- **OCI-R115** — Fan-out topology: N connectors, stream hub, in-VCN Kafka group. (PUB)

## Never

- **OCI-R72** — SCH to Function targets designed without the cold-start ceiling in mind. (SRV, PUB)
- **OCI-R82** — Pre-Authenticated Requests with excessive scope or far-future expiry. (OBJ)
- **OCI-R83** — Versioned bucket without a lifecycle rule on previous versions. (OBJ)
- **OCI-R84** — Object Storage as session state or message queue. (OBJ)
- **OCI-R85** — Public bucket for non-public data. (OBJ)
- **OCI-R89** — Private-endpoint-only stream pool with SCH as source. (PUB)
- **OCI-R90** — One SCH connector routed to several functions. (PUB)
- **OCI-R91** — HTTP headers for trace propagation across the stream boundary. (PUB)
- **OCI-R92** — SCH Functions target granted only `fn-invocation` (also needs `fn-function`). (PUB)

For each violation found in a review, name the rule ID and the governing skill, and prefer the
correct approach stated in that skill over ad-hoc fixes.
