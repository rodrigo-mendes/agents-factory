# Migration Guide: Quarkus ArC (3.15 baseline to 3.40)

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). "3.15" appears only here, as the baseline of earlier conventions.

## Contents

- [3.39 to 3.40](#339-to-340)
- [Convention changes against the 3.15 baseline](#convention-changes-against-the-315-baseline)
- [Upgrade steps](#upgrade-steps)
- [Compatibility matrix](#compatibility-matrix)
- [Not reviewed](#not-reviewed)

## 3.39 to 3.40

The official 3.40 migration guide says "Quarkus 3.40 LTS is the direct continuation of 3.39 so we don't expect any changes requiring manual intervention in 3.40". This is high confidence for 3.39 to 3.40 only.

Source: https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.40

## Convention changes against the 3.15 baseline

These are differences in the 3.40 documentation, not documented breaking changes.

1. `@Named("primary")` qualifier becomes `@Identifier("primary")` (recommendation, https://quarkus.io/version/3.40/guides/cdi-reference).
2. Test artifacts are `quarkus-junit` and `quarkus-junit-mockito`; `quarkus-junit5*` is absent from the 3.40 testing guide (https://quarkus.io/version/3.40/guides/getting-started-testing).
3. Camel test artifact `camel-quarkus-junit5` becomes `camel-quarkus-junit` (High; https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html). Details: skills `developing-camel-quarkus-junit-v3-40` and `developing-quarkus-junit-v3-40`.
4. `@QuarkusComponentTest` was not verified for 3.40 and is not carried forward (unverified, U7).

## Upgrade steps

1. Bump the Quarkus platform BOM to 3.40.x; the Camel Quarkus 3.40.x BOM uses Quarkus 3.40.1 (https://camel.apache.org/camel-quarkus/latest/).
2. Prefer `@Identifier` over general-purpose `@Named`. Add `@Unremovable` to beans looked up only by name (workaround for U1/U2).
3. Rename the test dependencies as in changes 2 and 3.
4. Run `./mvnw quarkus:dev` and inspect `/q/arc/removed-beans` (representative; page not recorded).

## Compatibility matrix

| Dependency | Value | Source |
|---|---|---|
| Jakarta CDI | 4.1 (Lite) | https://quarkus.io/version/3.40/guides/cdi-reference |
| Camel Quarkus | 3.40.x on Quarkus 3.40.1, Camel 4.22.1 | https://camel.apache.org/camel-quarkus/latest/ |
| jandex-maven-plugin | 3.6.0 (documented) | https://quarkus.io/version/3.40/guides/cdi-reference |
| Gradle Jandex plugin | 2.3.0 (documented) | https://quarkus.io/version/3.40/guides/cdi-reference |
| Java baseline | unverified for 3.40 (U3); Quarkus 4 moves to Java 21 | https://quarkus.io/blog/quarkus-4-0-0-beta1-released/ |

## Not reviewed

ArC items in the Quarkus migration guides from 3.16 to 3.39 were not reviewed in this research (unverified, U6). A project moving from an older release should read those guides.
