# Unverified Register, Risks and Bibliography

Research date 2026-10-28. Back to [SKILL.md](../SKILL.md). The research reports a quality score of 84%, a deep run using all 3 iterations, and 7 triangulated Always-Do inputs. Research ids are kept (U, G, S, L, C); the research ids U2 and U3 are the same facts as G2 and G3 and are listed once, under irresolvable items. Research ids I1 to I8 (internal sources) are renamed N1 to N8 here, so that I1 to I3 can name irresolvable items.

## Contents

- [Version-lifetime risk](#version-lifetime-risk)
- [Unverified items](#unverified-items)
- [Irresolvable items](#irresolvable-items)
- [Medium-confidence items](#medium-confidence-items)
- [Coverage limits](#coverage-limits)
- [Contradictions](#contradictions)
- [Tag to register mapping](#tag-to-register-mapping)
- [Source Bibliography](#source-bibliography)

## Version-lifetime risk

- stripe-java 34.0.0 is the only stable 34.x; Maven `<release>` is pre-release 34.1.0-beta.1 (lastUpdated 2026-10-21) (High; https://repo1.maven.org/maven2/com/stripe/stripe-java/maven-metadata.xml). A 35.x line needs a new skill.
- Quarkus 3.40 LTS is community-maintained until 2027-09-30; the 3.40 docs are new (High; https://quarkus.io/releases). Quarkus 4.0.0 is "Upcoming" with no date, Beta1 was published 2026-10-01 and the final release is "planned for the end of November" (High; https://quarkus.io/blog/quarkus-4-0-0-beta1-released/); Quarkus 4 content is rejected.
- `quarkus-amazon-lambda-http` and `-rest` are preview, so backward compatibility is not guaranteed (High; https://quarkus.io/version/3.40/guides/aws-lambda-http).
- Stripe now recommends Thin events for new destinations, and the event notification handlers page still shows a public-preview banner (C3); re-check [webhooks](https://docs.stripe.com/webhooks) before relying on handler APIs.

## Unverified items

6 unverified items (do not assert them).

| ID | Item | Impact and workaround |
|---|---|---|
| U1 | End-to-end effect of the HTTP handler's comma split on a single-valued `@RestHeader String`, and whether the dev-mode mock event server takes the same path (inference from handler source plus Jakarta javadoc) | Keep `getHeaderString` regardless; keep the signature test in the Verification Loop |
| U4 | Whether `StripeClient.build()` performs network I/O (assumed none; `LiveStripeResponseGetter` internals not read) | Do not call Stripe before the snapshot; measure before priming |
| U6 | Maximum Stripe event payload size against the SQS 1 MiB limit | Ask the payload expectation; fall back to the event id (D6) |
| U7 | Lambda host clock synchronisation (NTP) relative to the 300 s tolerance | Never set tolerance 0; monitor signature failures |
| U8 | Exception type `constructEvent` throws for a malformed non-JSON body | Catch `SignatureVerificationException` only for the documented case; test the malformed case |
| U10 | Which DNS TTL wins, Stripe README 60 or AWS SnapStart 0 (named "unverified" in research Q5 and C2 without an id; id assigned here) | Cite both, Ask First D3 |

## Irresolvable items

3 irresolvable items (documentation cannot settle them; they are absence-of-evidence claims and the skill text tags them (medium confidence, absence of evidence)).

| ID | Research id | Item | Reason and workaround |
|---|---|---|---|
| I1 | G1 | Stripe publishes no numeric webhook response timeout | Stripe webhooks page, manage-webhook page and support page checked; third-party figures rejected by the source hierarchy. Keep verify plus one SQS send; watch "(Timed out) ERR" deliveries in Workbench |
| I2 | G2 | No Stripe statement that a `StripeClient` instance is thread-safe | README, Javadoc and source checked; only the `withStripeContext` wording exists. Low impact on default Lambda (one request per environment); do not share mutable `RequestOptions` builders |
| I3 | G3 | When API Gateway HTTP API sets `isBase64Encoded` for a JSON POST is not documented | The payload 2.0 page shows the field without a rule. No correctness impact because Quarkus decodes both paths; use the `byte[]` entity |

## Medium-confidence items

16 medium-confidence items.

| ID | Item | Why medium |
|---|---|---|
| M1 | Secret rotation under SnapStart needs a new published version, and the update must fit the 24-hour old-secret window (research U5) | Config source loads once and the snapshot freezes the value (internal source N7); the combination is an inference |
| M2 | AWS SDK v2 class `ConditionalCheckFailedException` for the failed condition (research U9) | The DynamoDB page states the message only |
| M3 | Timeout budget formula and any example values | Design choice; the inputs are High |
| M4 | Dedupe items kept at least 30 days | Inferred from the 3, 15 and 30 day windows |
| M5 | A Lambda or API Gateway request id adds nothing over the SDK default key | Inference from retry behaviour |
| M6 | Customer metadata is writable by any holder of a key or Dashboard access | Inference; the tenant rule itself is family rule 6 |
| M7 | Illustrative code, the assembled example, the `putMetadata` builder name | Not compiled or run |
| M8 | Retry jitter (`ThreadLocalRandom`) state could repeat across restored environments | Inference, jitter only |
| M9 | Quarkiverse 3.23.0 running on Quarkus patch 3.40.1.1 | The parent POM says 3.40.0; the patch pairing is not stated |
| M10 | Completeness of a hand-maintained native reflection workaround | Community reports only |
| M11 | Fit of the webhook versus EventBridge transport to this architecture | Stripe facts are High; the fit is a judgement |
| M12 | Capping the SQS consumer with reserved concurrency to protect Stripe rate limits | Inference |
| M13 | stripe-java 34.0.0 release date (2026-10-01), default API version `2026-09-30.endive` and the empty `getObject()` on an API-version mismatch | Taken from the neighbour skills `developing-stripe-java-core-v34` and `handling-stripe-webhooks-v34`, which cite the stripe-java releases page, the master-branch CHANGELOG and the EventDataObjectDeserializer Javadoc; not re-fetched here (L5), main-branch source with no verbatim quote recorded (family rule 13) |
| M14 | stripe-java documents no GraalVM support (absence of evidence) | The README, the issues and the source tree were read; a statement could exist on a page not read (L3) |
| M15 | The 3.40.1.1 HTTP handler splits header values on "," and the REST handler copies `multiValueHeaders` as-is | Handler source read through a summarising tool (as in the neighbour skill `developing-quarkus-amazon-lambda-http-v3-40`, register M10); no verbatim quote recorded |
| M16 | SDK retry backoff: `Thread.sleep`, base 500 ms doubling to 5 s, jitter 0.75 to 1.0 | `HttpClient.java` (S13) was read only in a targeted way through a summarising tool; no verbatim quote recorded (family rule 13) |

## Coverage limits

6 coverage limits (parts of pages not read, or read through summarisation).

| ID | Limit |
|---|---|
| L1 | S9, S10, S17, S18 and S20 were read as tool summaries with short verbatim quotes (all read 2026-10-28); the community report of a silent native failure (issue thread S17, 2026-09-30) is tagged (medium confidence, L1) |
| L2 | S31 and S32 were read from the jakartaee/rest main branch, not the 3.1 tag used by Quarkus 3.40; search reports identical wording across versions. The javadoc claims (first value of a non-collection `@HeaderParam`, `getHeaderString` joining with ",") carry (medium confidence, L2) wherever they appear (family rule 13) |
| L3 | HTTP 404 for github.com/stripe/stripe-java/tree/v34.0.0/src/main/resources (absence of `META-INF/native-image` not confirmed), the Jakarta REST 3.1 spec page and the Jakarta EE 11 `HeaderParam` apidocs page |
| L4 | `code.yawk.at` failed DNS resolution |
| L5 | The stripe-java CHANGELOG and the pages cited by neighbour skills (S35, S36: Quarkiverse Secrets Manager page, Lambda with SQS, EventDataObjectDeserializer Javadoc, the `developing-quarkus-arc-v3-40` testing and CDI guides) were not re-fetched; those facts come from internal sources N1 to N3 and carry (medium confidence, L5) or (medium confidence, M13) |
| L6 | The stripe.dev blog on Secrets Manager rotation (linked from S3) was not read |

## Contradictions

5 contradictions (research C1 to C5); no family fact was contradicted by a page read.

| ID | Statement A | Statement B | Handling |
|---|---|---|---|
| C1 | Internal skill `handling-stripe-webhooks-v34` and S2: on AWS API Gateway plus Lambda, capture `rawBody` with a Body Mapping Template | Quarkus HTTP and REST extensions use Lambda proxy integrations where API Gateway "maps the entire client request to the input event" (S24) and Quarkus passes the decoded body (S21, S22) | Not a factual conflict; the advice does not apply to Quarkus proxy integrations; this skill uses `byte[]`. Report to the stripe-java package owner; the stripe-java skills are not edited here |
| C2 | Stripe README: `networkaddress.cache.ttl` 60 (S9, also in `developing-stripe-java-core-v34`) | AWS SnapStart: avoid the Java DNS cache, set 0 (S26) | Ask First D3, cite both |
| C3 | S2 banner: event notification handlers "available in public preview" | Same page's version table and the internal skill: Java GA since v33.4.0 | Keep the GA statement and note the banner; the URL cited by the internal skill now serves "Manage webhook endpoints" |
| C4 | Internal skill `developing-stripe-java-core-v34` lists pre-releases 34.1.0-alpha.1, beta.1, alpha.2 | Maven metadata lists alpha.1 to alpha.4 and beta.1; `<release>` is 34.1.0-beta.1 (S16) | Update only; 34.0.0 is the only stable, pin it |
| C5 | `StripeClientBuilder.build()` Javadoc: "Constructs a StripeResponseGetterOptions" | Code returns `new StripeClient(...)` (S12) | Cosmetic; no action |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) failure of `@RestHeader String` and mock-server path | ask-first D9; always-do 5; verification Verification Loop; evaluation 1 | U1 |
| (unverified) `build()` network I/O | SKILL.md Ask First D4; ask-first D4 | U4 |
| (unverified) event size against 1 MiB | SKILL.md Ask First D6; ask-first D6 | U6 |
| (unverified) host clock synchronisation | never-do N7 | U7 |
| (unverified) exception for a non-JSON body | webhook-pipeline, Webhook resource notes | U8 |
| (unverified) which DNS TTL wins | SKILL.md Ask First D3; ask-first D3; evaluation 2 | U10 |
| (medium confidence, absence of evidence) no numeric webhook timeout | SKILL.md Quick Reference; always-do 6 | I1 |
| (medium confidence, absence of evidence) `StripeClient` thread-safety | always-do 1 | I2 |
| (medium confidence, absence of evidence) HTTP API `isBase64Encoded` rule | always-do 4 | I3 |
| (medium confidence, absence of evidence) no GraalVM support documented | SKILL.md Ask First D2; ask-first D2; migration-notes Compatibility | M14 |
| (medium confidence) rotation and 24-hour window | SKILL.md Ask First D4; ask-first D4; migration-notes step 5 | M1 |
| (medium confidence) exception class name | always-do 7 | M2 |
| (medium confidence) budget formula | SKILL.md Ask First D1; always-do 3; never-do N4; ask-first D1 | M3 |
| (medium confidence) 30-day retention | always-do 7 | M4 |
| (medium confidence) request-id reasoning | SKILL.md Ask First D10; ask-first D10; always-do 8; evaluation 4 | M5 |
| (medium confidence) metadata writable | SKILL.md Ask First D10; ask-first D10; always-do 9 | M6 |
| (medium confidence) illustrative code, `putMetadata` name | always-do, never-do, webhook-pipeline, verification-and-production headers; webhook-pipeline Tenant mapping | M7 |
| (medium confidence) jitter state | ask-first D4 | M8 |
| (medium confidence) Quarkiverse 3.23.0 on 3.40.1.1 | SKILL.md Version Context; migration-notes Compatibility | M9 |
| (medium confidence) native workaround completeness | ask-first D2; evaluation 6 | M10 |
| (medium confidence) fit of the transport options | ask-first D5 | M11 |
| (medium confidence) reserved concurrency cap | webhook-pipeline SQS consumer; verification-and-production Production readiness | M12 |
| (medium confidence, M15) HTTP handler comma split | SKILL.md Ask First D9; ask-first D9; always-do 5; verification-and-production Gateway integration; evaluation 1 | M15 |
| (medium confidence, L2) Jakarta javadoc on the `main` branch | SKILL.md Ask First D9; always-do 5; ask-first D9 | L2 |
| (medium confidence, L1) community report of a silent native failure | ask-first D2 | L1 |
| (medium confidence, M13) release date, API version, empty `getObject()` | SKILL.md Version Context; webhook-pipeline Webhook resource notes; migration-notes | M13 |
| (medium confidence, M16) SDK retry backoff numbers | SKILL.md Quick Reference; always-do 3; ask-first D1 | M16 |
| (medium confidence, L5) neighbour-cited pages not re-fetched | always-do 1 (scope choice), 2, 7 | L5 |
| gateway timeouts: no tag; sourced to S33 and S34 (REST and HTTP API quotas pages) | SKILL.md Never Do, Quick Reference, External Resources; always-do 3; never-do N4; ask-first D1 | S33, S34 |
| contradiction C1 (Body Mapping Template) | always-do 4; verification-and-production Gateway integration | C1 |
| contradiction C2 (DNS TTL) | ask-first D3 | C2 |
| contradiction C4 (Maven release tag) | webhook-pipeline Dependencies; migration-notes | C4 |

## Source Bibliography

The full table is in [source-bibliography.md](./source-bibliography.md).
