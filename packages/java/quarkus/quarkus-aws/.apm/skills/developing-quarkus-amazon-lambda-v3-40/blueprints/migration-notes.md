# Migration Notes

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. No Quarkus 3.40 migration note specific to `quarkus-amazon-lambda` was found on the pages read; the Quarkus wiki migration guides for 3.32 to 3.40 were not read in full, so the absence of other breaking changes is (unverified).

## Deprecations relevant to this skill

| Item | Change | Source |
|---|---|---|
| `quarkus.snapstart.enable` | deprecated since 3.26; use `quarkus.snapstart.enabled`. The 3.40 SnapStart guide still shows the old name, so prefer the reference | https://quarkus.io/version/3.40/guides/all-config |
| `quarkus-junit5` | renamed `quarkus-junit` in Quarkus 3.31; the 3.40 aws-lambda guide's Gradle sample already uses `testImplementation 'io.quarkus:quarkus-junit'`. Test detail: skill `developing-quarkus-junit-v3-40` | https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31 |
| `provided.al2`, `provided` | deprecated 2026-07-31 and 2024-01-08; move to `provided.al2023` for OS-only runtimes | https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html |
| `java17` (AL2) | deprecation 2027-06-30; move to `java17.al2023` or `java21` (`java25` only after Ask First C2). AL2 reaches end of life 2026-06-30 | https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html |
| `quarkus.lambda.dev-port`, `quarkus.lambda.test-port` | both these and `quarkus.lambda.mock-event-server.*` appear in the 3.40 reference; the former pair is not deprecated, but the mock-server start-up code reads only the `mock-event-server.*` names (medium confidence, from source at tag 3.40.1.1). Use the `mock-event-server.*` names | https://quarkus.io/version/3.40/guides/all-config |

## Upgrade steps (representative)

1. Set the Quarkus platform BOM to 3.40.1.1 (archetype `io.quarkus:quarkus-amazon-lambda-archetype:3.40.1.1`).
2. Replace `quarkus.snapstart.enable` with `quarkus.snapstart.enabled` where present.
3. Replace `quarkus-junit5` with `quarkus-junit`.
4. Move runtimes to `java21` or `java17.al2023` (JVM; `java25` only after Ask First C2), or `provided.al2023` for native (pairing: medium confidence).
5. Rebuild and redeploy `function.zip`. With SnapStart, publish a new version: a snapshot belongs to a published version. A version not invoked for 14 days goes `Inactive`; before rolling back to an old version, wait for it to be `Active` again (`SnapStartNotReadyException` in the meantime) ([AWS](https://docs.aws.amazon.com/lambda/latest/dg/snapstart-activate.html)).

## Compatibility matrix

| Dependency | Min | Max | Notes |
|---|---|---|---|
| JDK (build) | 17 | page not recorded | guide prerequisite "JDK 17+" |
| Maven | 3.9.16 as listed | n/a | guide prerequisite, tool paraphrase (medium confidence) |
| GraalVM or Mandrel (native) | "GraalVM for JDK 21 is required" | n/a | a minimum (family fact, native guide read to 100,000 of 101,875 characters); Mandrel recommended |
| `aws-lambda-java-core`, `aws-lambda-java-events` | managed by the Quarkus BOM | n/a | transitive through `quarkus-amazon-lambda-common` 3.40.1.1; versions page not recorded |
| `org.crac` | page not recorded | n/a | not a declared dependency of `quarkus-core` 3.40.1.1; whether to add it explicitly is (unverified); AWS shows `org.crac:crac:1.4.0` |
| Lambda Java runtime | `java17.al2023` | `java25` | Java 25 with Quarkus 3.40 is (unverified) |
| Lambda OS-only runtime | `provided.al2023` | n/a | the only supported OS-only runtime; Quarkus pairing is medium confidence |

## Quarkus 4

Out of scope. Quarkus 4.0.0 is "Upcoming" with no date on https://quarkus.io/releases (High). The Quarkiverse 4.0.0.Beta* line is rejected as misinformation for this skill. Pin 3.40.x.
