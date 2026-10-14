# Migration: junit5 Rename (3.31) and Test Changes (3.36)

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). The old names below are the migration baseline only (3.15 conventions).

## Breaking changes 3.15 to 3.40

| Version | Change | Source |
|---|---|---|
| 3.31 | `camel-quarkus-junit5` renamed `camel-quarkus-junit`; `org.apache.camel.test.junit5` to `org.apache.camel.test.junit6`; `org.apache.camel:camel-test-junit5` to `camel-test-junit6` | https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html |
| 3.36 | Non-advised routes auto-start (no `startRouteDefinitions()`); new `adviceRoute()`; advice cleaned up between test methods | https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.36.0.html |
| 3.15 | `isUseAdviceWith()` deprecated | https://raw.githubusercontent.com/apache/camel-quarkus/3.40.0/test-framework/camel-quarkus-junit/src/main/java/org/apache/camel/quarkus/test/CamelQuarkusTestSupport.java |

The 3.31 guide said the old artifact is kept "until Camel Quarkus 3.34.0 is released". Maven Central has no `camel-quarkus-junit5` 3.34.x, but 3.35.0, 3.36.0, 3.38.0, 3.39.0 and 3.40.0 exist (listing https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-junit5/; 3.40.0 dated 2026-09-24). The 3.40.0 artifact is a "(Deprecated)" stub that depends on `camel-quarkus-junit`, with no `relocation` element (https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-junit5/3.40.0/camel-quarkus-junit5-3.40.0.pom). When it will be removed is (unverified).

The Quarkus 3.40 testing guide names `quarkus-junit` and never mentions `quarkus-junit5` (https://quarkus.io/version/3.40/guides/getting-started-testing).

## Upgrade steps

1. Replace `camel-quarkus-junit5` with `camel-quarkus-junit` (test scope).
2. Change imports (representative):
   `sed -i 's/org.apache.camel.test.junit5/org.apache.camel.test.junit6/g' $(grep -rl 'org.apache.camel.test.junit5' src/test)`
3. Delete `startRouteDefinitions()` calls that follow AdviceWith; move per-test advice to `adviceRoute()`.
4. Remove `isUseAdviceWith()` overrides.
5. Run `mvn verify` (JVM tests), then `mvn verify -Dnative` (integration tests).

## Verification

```bash
mvn dependency:tree -Dincludes=org.apache.camel.quarkus:camel-quarkus-junit*
# Expected: camel-quarkus-junit:3.40.x:test ; no camel-quarkus-junit5
grep -rn "org.apache.camel.test.junit5\|startRouteDefinitions\|isUseAdviceWith" src/test
# Expected: no output
```

## Compatibility matrix

| Dependency | Version | Source |
|---|---|---|
| Camel | 4.22.1 (4.22.x) | https://camel.apache.org/camel-quarkus/latest/ |
| Quarkus (`quarkus-junit`) | 3.40.1 (3.40.x) | https://camel.apache.org/camel-quarkus/latest/ |
| `camel-test-junit6` | managed by the BOM | https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-junit/3.40.0/camel-quarkus-junit-3.40.0.pom |
| GraalVM (native ITs) | 25.0.4.1 | https://camel.apache.org/camel-quarkus/latest/ |
