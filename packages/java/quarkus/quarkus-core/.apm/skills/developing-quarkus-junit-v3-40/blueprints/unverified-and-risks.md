# Unverified Register, Risks and Bibliography

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). The research reports a quality score of 87% (46 tracked claims) and a deep run that used all 3 iterations. Family facts verified by the orchestrator on 2026-10-14 keep the tags of the family facts file.

Header counts: 6 unverified (U1-U6), 3 irresolvable (I1-I3), 10 medium-confidence (M1-M10), 3 coverage limits (L1-L3).

## Contents

- [Version-lifetime risk](#version-lifetime-risk)
- [Unverified items](#unverified-items)
- [Irresolvable items](#irresolvable-items)
- [Medium-confidence items](#medium-confidence-items)
- [Coverage limits](#coverage-limits)
- [Tag to register mapping](#tag-to-register-mapping)
- [Source Bibliography](#source-bibliography)

## Version-lifetime risk

- Quarkus 4.0.0.Beta1 was published 2026-10-01; the final release is "planned for the end of November"; the highlights list Java 21 as the new base version (High; https://quarkus.io/blog/quarkus-4-0-0-beta1-released/). As of 2026-10-14 no Camel Quarkus build on Quarkus 4 is known and the post does not mention Camel Quarkus (medium confidence, absence of evidence; M6).
- Quarkus 3.40 was released 2026-09-30 as an LTS and is community-maintained until 2027-09-30 (High; https://quarkus.io/releases).
- The Camel Quarkus-specific support end date for 3.40 is not published (unverified, U5). Applying the Quarkus date to Camel Quarkus is an inference.
- The `-junit5` relocation POMs are expected to be at risk in Quarkus 4 (inference, M7); no removal date is documented (I2). Do not mix Quarkus 4 test patterns into this skill.

## Unverified items

6 items. Do not assert any of them.

| ID | Item | Impact and workaround |
|---|---|---|
| U1 | Whether Dev Services restart or are reused when the application restarts on a profile change (the Dev Services page only says they are reused while their configuration is unchanged) | Cost or state leaks between profiles; verify in your build |
| U2 | REST Assured version managed by the Quarkus 3.40.1 BOM (not in the portion read) | Check `mvn dependency:tree` |
| U3 | When the `camel-quarkus-junit5` stub will be removed (the 3.31 guide said "until Camel Quarkus 3.34.0 is released"; the 3.40.0 stub exists, High, see `developing-camel-quarkus-junit-v3-40`) | Use `camel-quarkus-junit` |
| U4 | Concrete Surefire version (the guide uses the placeholder `${surefire-plugin.version}`) | Take the version from your project generator or the BOM of your build |
| U5 | Camel Quarkus-specific support end date for 3.40 (the "LTS Until" column is blank); not resolvable from documentation | Support planning; do not infer from the Quarkus date |
| U6 | Maven and GraalVM versions for Quarkus 3.40 (no page recorded in the research) | Check the project's build and the Quarkus 3.40 guides |

## Irresolvable items

3 items the research could not resolve.

| ID | Item | Impact and workaround |
|---|---|---|
| I1 | Support for JUnit Jupiter parallel test execution with `@QuarkusTest` | May break the shared app/profile lifecycle; run sequentially, parallelize per module or fork, use `@QuarkusTestResource(parallel = true)` for resource startup |
| I2 | How long the `quarkus-junit5` (and other `-junit5`) relocation POMs are kept | Builds on old names break on removal; migrate now |
| I3 | JaCoCo default report directory: the page states both `target/jacoco-report` and `target/jacoco-reports` | CI upload paths may be wrong; set `quarkus.jacoco.report-location` |

## Medium-confidence items

10 items.

| ID | Item | Why medium |
|---|---|---|
| M1 | Group tests by profile; a different `@TestProfile` restarts Quarkus (research AD-4) | Single partly-read source (testing guide, L1) |
| M2 | Separate `@QuarkusTest` and `@QuarkusIntegrationTest` executions; integration tests run in the `prod` profile by default (AD-5) | Single partly-read source (L1) |
| M3 | `@TestHTTPResource` / `@TestHTTPEndpoint` / `HttpServer` for the test URL (AD-6) | Two sources with different claims; the leftover "High" badge in the research is not carried over. The 3.31 wiki names `ConfigProvider`/`SmallRyeConfig` and `HttpServer`, not `@TestHTTPResource`/`@TestHTTPEndpoint` (High, absence on that page) |
| M4 | `@WithTestResource` / `@QuarkusTestResource` scoping, global by default; `@QuarkusTestResource` not deprecated on the 3.40 page (CP-2) | Partly-read guide, absence of evidence |
| M5 | A `@QuarkusIntegrationTest` class can extend a `@QuarkusTest` class | Rests on a main-branch example |
| M6 | No Camel Quarkus build on Quarkus 4 is known | Absence of evidence |
| M7 | `-junit5` relocations at risk in Quarkus 4 | Inference |
| M8 | Quarkus quickstarts (main branch) as examples | Unversioned repository; no claim in the skill relies on it |
| M9 | NP-5: different profiles/resources on `@Nested` classes; `@Mock` beans in `src/main` | Rated High in the research without quoted evidence; kept out of SKILL.md |
| M10 | Pairing `quarkus.https.test-port` (removed in 3.31, High) -> `quarkus.http.test-ssl-port` as its replacement | Inferred from the sentence order of the 3.31 migration wiki (family facts); kept out of the High tiers |

## Coverage limits

3 items (pages read only partly).

| ID | Page | Limit |
|---|---|---|
| L1 | https://quarkus.io/version/3.40/guides/getting-started-testing | Read to 100,000 of 108,136 characters; claims beyond that point are unchecked (the AOT/JDK 25+ row is tagged accordingly) |
| L2 | https://quarkus.io/version/3.40/guides/dev-services | First 100k characters read; anything beyond is medium |
| L3 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1/bom/application/pom.xml | First 100k characters read; properties beyond are unknown (see U2) |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified, U1) Dev Services across profile restarts | SKILL.md Ask First; profiles-and-resources | U1 |
| (unverified, U2) REST Assured version | SKILL.md Quick Reference; always-do-patterns; migration; integration-examples | U2 |
| (unverified, U3) `camel-quarkus-junit5` stub removal date | SKILL.md Quick Reference; migration | U3 |
| (unverified, U4) Surefire version | SKILL.md Ask First; always-do-patterns | U4 |
| (unverified, U5) Camel Quarkus end date | SKILL.md Version-lifetime; this file | U5 |
| (unverified, U6) Maven / GraalVM | SKILL.md Version Context | U6 |
| (unverified, I1) parallel execution; "(unverified)" in scenario 2 | SKILL.md Ask First; profiles-and-resources; evaluation-scenarios | I1 |
| (unverified, I2) relocation retention | SKILL.md Version-lifetime; never-do; migration | I2 |
| (unverified, I3) JaCoCo report directory; "(unverified)" in scenario 2 | SKILL.md Quick Reference; test-types; evaluation-scenarios | I3 |
| (medium confidence) profile grouping | SKILL.md Ask First; test-types; profiles-and-resources | M1 |
| (medium confidence) separate executions, `prod` default | SKILL.md Ask First and Quick Reference; test-types; profiles-and-resources | M2 |
| (medium confidence) test URL, (medium confidence, M3) | SKILL.md Ask First; never-do; profiles-and-resources; migration; integration-examples; evaluation-scenarios; test-types (sample comment) | M3 |
| (medium confidence, M10) https.test-port to http.test-ssl-port pairing | SKILL.md Ask First and Never Do note; migration; evaluation-scenarios | M10 |
| (medium confidence) test resource scope, not deprecated | SKILL.md Ask First; profiles-and-resources | M4 |
| (medium confidence, M5) IT extends QuarkusTest | test-types | M5 |
| (medium confidence, absence of evidence; M6) Quarkus 4 and Camel Quarkus | this file | M6 |
| (inference, medium confidence, M7) relocation risk in Quarkus 4 | migration; this file | M7 |
| (medium confidence, M9) NP-5 kept out | never-do-patterns | M9 |
| (coverage limit, L1) / (medium confidence, L1) | SKILL.md Version Context and Quick Reference; migration | L1 |
| (coverage limit L2) Dev Services | SKILL.md Ask First; profiles-and-resources | L2 |
| (coverage limit, L3) BOM | SKILL.md Version Context; migration | L3 |

M8 (quickstarts) is listed in the bibliography only; no claim in the skill relies on it.

## Source Bibliography

All fetched 2026-10-14. camel.apache.org pages carry no page date and are the current stable 3.40.x docs. No community sources were used as evidence (an OpenRewrite `quarkus331/JUnitRelocations` recipe page appeared in search results; it is not an official Quarkus source).

- https://quarkus.io/version/3.40/guides/getting-started-testing (read to 100,000 of 108,136 characters; L1)
- https://quarkus.io/version/3.40/guides/command-mode-reference (testing section)
- https://quarkus.io/version/3.40/guides/continuous-testing
- https://quarkus.io/version/3.40/guides/tests-with-coverage
- https://quarkus.io/version/3.40/guides/dev-services (first 100k characters read; L2)
- https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31 (official Quarkus migration wiki, unversioned page about a specific version)
- https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1/bom/application/pom.xml (tag 3.40.1; first 100k characters read; L3)
- https://repo1.maven.org/maven2/io/quarkus/quarkus-junit5/3.40.1/quarkus-junit5-3.40.1.pom (relocation POM)
- https://repo1.maven.org/maven2/io/quarkus/quarkus-junit5/maven-metadata.xml (versions up to 4.0.0.Beta1)
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html
- https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html
- https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-junit5/3.40.0/camel-quarkus-junit5-3.40.0.pom (orchestrator-fetched 2026-10-14, High)
- https://camel.apache.org/camel-quarkus/latest/
- https://camel.apache.org/releases/
- https://camel.apache.org/releases/q-3.40.0/
- https://quarkus.io/releases
- https://quarkus.io/blog/quarkus-4-0-0-beta1-released/ (2026-10-01)
- https://github.com/quarkusio/quarkus (repository, tag 3.40.1) ; https://github.com/quarkusio/quarkus-quickstarts (main branch, medium)
