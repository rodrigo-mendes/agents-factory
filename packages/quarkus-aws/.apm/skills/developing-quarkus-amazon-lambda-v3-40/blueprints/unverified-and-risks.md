# Unverified Register, Risks and Bibliography

Research date 2026-10-28. Back to [SKILL.md](../SKILL.md). The research reports a quality score of 87%, a deep run using all 3 iterations, and 4 triangulated claims. Family facts verified by the orchestrator on 2026-10-28 keep the tags of the family facts file.

## Contents

- [Version-lifetime risk](#version-lifetime-risk)
- [Unverified items](#unverified-items)
- [Irresolvable items](#irresolvable-items)
- [Medium-confidence items](#medium-confidence-items)
- [Coverage limits](#coverage-limits)
- [Resolved items](#resolved-items)
- [Tag to register mapping](#tag-to-register-mapping)
- [Source Bibliography](#source-bibliography)

## Version-lifetime risk

- Quarkus 3.40 was released 2026-09-30 as an LTS and is community-maintained until 2027-09-30; latest patch 3.40.1.1 (2026-10-19) (High; https://quarkus.io/releases). The 3.40 documentation is new and may still change.
- Quarkus 4.0.0 is "Upcoming" with no date on the releases page (High). Quarkus 4 and Quarkiverse 4.0.0.Beta* content is rejected for this skill; the 3.40 patterns are not asserted for Quarkus 4.
- AWS runtimes: `provided.al2` deprecated 2026-07-31, `java17` (AL2) deprecates 2027-06-30, AL2 end of life 2026-06-30, AL2023 runtimes (`java17.al2023`, `java21`, `java25`, `provided.al2023`) deprecate 2029-06-30 (High; https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html). Re-check the table before pinning a runtime.
- The SnapStart restore limit conflict (2 s vs 10 s) can change if either source is updated (U10).

## Unverified items

9 unverified items (do not assert them; ids are kept stable, U4 moved to M7).

| ID | Item | Impact and workaround |
|---|---|---|
| U1 | Lambda handler setting for the native (OS-only) function; the guide does not state it | Do not invent a value; ask which value the tooling expects |
| U2 | Quarkus 3.40 support of Java 25 at runtime (`java25`) | Propose `java21` first (medium confidence); `java25` is named only in Ask First C2 and the runtime table, never in a recommendation |
| U3 | Whether `org.crac` must be added explicitly for the SnapStart CRaC example (not a declared dependency of `quarkus-core` 3.40.1.1) | Compile the example; add the dependency only if the build requires it |
| U5 | Failure mode of a native function without `DISABLE_SIGNAL_HANDLERS=true` | Always set the variable |
| U6 | Exact behaviour when SnapStart is configured on an OS-only runtime (rejected vs ignored) | Avoid the combination |
| U7 | Use of `aws-lambda-java-events` classes (SQSEvent, SNSEvent, S3Event, ScheduledEvent) as `RequestHandler` input types; the 3.40 guide does not cover them | Do not present them as documented; ask for the event source |
| U8 | Whether the default 3-second timeout suffices for a JVM Quarkus cold first invocation; the standard init-phase limit was not read | Ask for measured duration |
| U9 | Absence of breaking changes for `quarkus-amazon-lambda` between 3.33 and 3.40 (wiki migration guides not read) | Read the Quarkus migration wiki pages before an upgrade |
| U10 | Which SnapStart restore limit applies: Quarkus guide "Restoration is limited to 2 seconds" or AWS 10 seconds (`SnapStartTimeoutException`); both quotes are High | Cite both, keep `afterRestore` work minimal |

## Irresolvable items

0 irresolvable items. Facts that documentation cannot resolve are listed once under unverified items.

## Medium-confidence items

11 medium-confidence items.

| ID | Item | Why medium |
|---|---|---|
| M1 | Pairing native Quarkus with `provided.al2023` | The guide does not name the runtime; AWS lists `provided.al2023` as the only OS-only runtime, so the pairing is an inference |
| M2 | Method bodies and illustrative code (handlers, `ProcessingService`, stream copy, CRaC hook bodies, uniqueness adaptation) | Class shapes come from the guides; bodies are not from a page |
| M3 | A CDI bean instance as the strong reference for the CRaC `Resource` | Inference from the Quarkus example and the AWS `WeakReference` statement |
| M4 | `java21` as the first candidate to propose (not a documented default) | Aligned with the jdk-21 builder images; no page recommends it for Lambda |
| M5 | Archetype command-line flags beyond the coordinates | The tool returned the coordinates, not the full command line |
| M6 | Typed vs stream handler selection criteria; the peak-JIT trade-off of the tiered compilation flag | Inference; the guide only recommends the flag |
| M7 | `quarkus.lambda.dev-port` / `test-port` are not deprecated (own config class, defaults 8080/8081), but the mock-server start-up code reads only `quarkus.lambda.mock-event-server.dev-port` / `test-port` (family fact; moved from U4) | Read from source code at tag 3.40.1.1 through a summarising tool, not a guide statement: https://github.com/quarkusio/quarkus/tree/3.40.1.1/extensions/amazon-lambda |
| M8 | Maven 3.9.16 build prerequisite | Tool paraphrase of the guide, not a verbatim quote (same tag as the HTTP skill) |
| M9 | Config defaults read from the all-config page through a summarising tool (L2): `quarkus.lambda.mock-event-server.enabled` `true`; `quarkus.snapstart.preload-classes`, `generate-application-class-list`, `initialize-classes`, `full-warmup` `true` (same tag as the HTTP and testing skills) | No verbatim quote of the default rows is recorded (family rule 13) |
| M10 | The 3.40 aws-lambda guide body neither mentions nor recommends Funqy (it appears only as a navigation link) | Absence of evidence in a page read through a summarising tool (L2) |
| M11 | Native build-host RAM of 4-8 GB from the table of the native guide | Page read to 100,000 of 101,875 characters (L1) and no verbatim quote of the table row is recorded (family rule 13) |

## Coverage limits

2 coverage limits (parts of pages not read, or read through summarisation).

| ID | Limit |
|---|---|
| L1 | https://quarkus.io/version/3.40/guides/building-native-image was read only to 100,000 of 101,875 characters |
| L2 | All pages were read through a summarising fetch tool; quoted sentences were returned verbatim, other wording is a paraphrase by the tool |

## Resolved items

A research gap (GraalVM for JDK 21 vs the GraalVM 25.0.4.1 of the Camel Quarkus docs) was resolved by the orchestrator on 2026-10-28: "GraalVM for JDK 21 is required" is a minimum, not a contradiction; 25.0.4.1 is the tested version of the Camel Quarkus line. The skill presents it that way and does not list it as unverified. Source: https://quarkus.io/version/3.40/guides/building-native-image (read to 100,000 of 101,875 characters, L1).

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (medium confidence) native on `provided.al2023` pairing | SKILL.md Ask First; ask-first-decisions C1; packaging contract table; migration-notes | M1 |
| (medium confidence) illustrative method bodies | always-do-patterns 2, 6, 7; packaging handler lifecycle | M2 |
| (medium confidence) CDI bean as strong reference | always-do-patterns 7 | M3 |
| (medium confidence) `java21` first candidate | SKILL.md Ask First; ask-first-decisions C2; U2 workaround | M4 |
| (medium confidence) archetype flags | packaging "Create the project" | M5 |
| (medium confidence) typed vs stream criteria, tiered compilation trade-off | SKILL.md Ask First; ask-first-decisions C3 and C5 | M6 |
| (unverified) Java 25 with Quarkus 3.40 | SKILL.md Version Context and Ask First; ask-first-decisions C2; migration-notes | U2 |
| (unverified) native handler setting | SKILL.md Ask First; ask-first-decisions C7; packaging contract table | U1 |
| (unverified) `org.crac` explicit dependency | always-do-patterns 7; migration-notes | U3 |
| (medium confidence) `dev-port` / `test-port` are not deprecated; start-up code reads only `mock-event-server.*` | packaging dev mode; migration-notes | M7 |
| (medium confidence) Maven 3.9.16 | SKILL.md Version Context; migration-notes matrix | M8 |
| (medium confidence) `mock-event-server.enabled` and SnapStart switch defaults `true` | SKILL.md Quick Reference; always-do-patterns; snapstart.md; ask-first-decisions C3; packaging dev mode | M9 |
| (medium confidence, absence of evidence) Funqy not in the guide body | packaging and artifact contract | M10 |
| (medium confidence, M11) native build-host RAM 4-8 GB | ask-first-decisions C1 | M11 |
| (unverified) failure mode without `DISABLE_SIGNAL_HANDLERS` | never-do-patterns F7 | U5 |
| (unverified) SnapStart on an OS-only runtime, rejected vs ignored | never-do-patterns F3; snapstart.md | U6 |
| (unverified) AWS event classes as handler input | SKILL.md Ask First; ask-first-decisions C7 | U7 |
| (unverified) 3 s timeout for a JVM cold first call | SKILL.md Ask First; ask-first-decisions C4 | U8 |
| (unverified) no other breaking changes 3.33 to 3.40 | migration-notes | U9 |
| (unverified) which restore limit applies | SKILL.md Ask First; ask-first-decisions C6; snapstart.md | U10 |
| (unverified) and (medium confidence) tags inside scenario expectations | evaluation-scenarios | U1, U6, U7, U8, U10, M1, M3 |

## Source Bibliography

All read 2026-10-28.

**Quarkus 3.40 and registry**

| # | URL | Coverage | Used for |
|---|---|---|---|
| S1 | https://quarkus.io/version/3.40/guides/aws-lambda | full per tool, 3 passes | handler rules, build outputs, native, env var, mock server, X-Ray, container images |
| S2 | https://quarkus.io/version/3.40/guides/aws-lambda-snapstart | full per tool, 2 passes | SnapStart properties, preload file, CRaC priming, 2-second claim, tiered compilation |
| S3 | https://quarkus.io/version/3.40/guides/all-config | all 232,437 characters in 3 windows; only `quarkus.lambda.*` and `quarkus.snapstart.*` extracted | env var names, defaults, `enable` deprecation, `full-warmup` |
| S4 | https://quarkus.io/version/3.40/guides/building-native-image | 100,000 of 101,875 characters (L1) | GraalVM for JDK 21, builder image, container build |
| S5 | https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda/3.40.1.1/quarkus-amazon-lambda-3.40.1.1.pom | full | artifact existence, name, description, dependencies |
| S6 | https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda-common/3.40.1.1/quarkus-amazon-lambda-common-3.40.1.1.pom | full | transitive `aws-lambda-java-core` and `-events` |
| S7 | https://repo1.maven.org/maven2/io/quarkus/quarkus-core/3.40.1.1/quarkus-core-3.40.1.1.pom | full | `org.crac:crac` is not a declared dependency |

**AWS Lambda Developer Guide**

| # | URL | Used for |
|---|---|---|
| S8 | https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html | runtime identifiers and deprecation dates |
| S9 | https://docs.aws.amazon.com/lambda/latest/dg/runtimes-provided.html | OS-only runtime, GraalVM Native Image use case |
| S10 | https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html | supported runtimes, limitations, regions, pricing, compatibility |
| S11 | https://docs.aws.amazon.com/lambda/latest/dg/snapstart-activate.html | activation, states, 14-day deletion, credentials |
| S12 | https://docs.aws.amazon.com/lambda/latest/dg/snapstart-runtime-hooks.html | hook purposes (index page) |
| S13 | https://docs.aws.amazon.com/lambda/latest/dg/snapstart-runtime-hooks-java.html | CRaC elements, order, 10-second restore limit, `WeakReference` |
| S14 | https://docs.aws.amazon.com/lambda/latest/dg/snapstart-uniqueness.html | uniqueness, CSPRNG, scanner |
| S15 | https://docs.aws.amazon.com/lambda/latest/dg/configuration-memory.html | memory range, default, vCPU ratio |
| S16 | https://docs.aws.amazon.com/lambda/latest/dg/configuration-timeout.html | timeout default and maximum |

**Family facts (orchestrator-verified)**: https://quarkus.io/releases ; https://quarkus.io/blog/quarkus-4-0-0-beta1-released/ ; https://camel.apache.org/camel-quarkus/latest/ (GraalVM 25.0.4.1 of the Camel Quarkus line); https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31 (`quarkus-junit5` rename). Community sources: none used. The extension source repository (https://github.com/quarkusio/quarkus) and the scanner repository https://github.com/aws/aws-lambda-snapstart-java-rules were not fetched (page not recorded).
