# Migration Guide: 3.15 Baseline to 3.40

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). "3.15" is used here only as the baseline of an older project. Entries marked via the core research were not re-fetched.

## Bean-relevant changes

- No bean-specific entries were found in the 3.31 to 3.40 migration guides (medium confidence, via the core research; https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/index.html).
- Testing: `camel-quarkus-junit5` was renamed `camel-quarkus-junit` since 3.31; test imports move from `org.apache.camel.test.junit5` to `org.apache.camel.test.junit6` (High, https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html). The release that removes the deprecated `camel-quarkus-junit5` stub is (unverified); prefer `camel-quarkus-junit`. Stub and Camel test details: skill `developing-camel-quarkus-junit-v3-40`.
- `@InjectMock` needs `quarkus-junit-mockito` (medium confidence; https://quarkus.io/guides/getting-started-testing).
- 3.40: `serialization-enabled` has three states; relevant only for `Serializable` payloads in native mode (medium confidence, via the core research; https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html).
- Camel 4.x: type+value parameter qualifiers (`int.class 123`) (medium confidence; https://camel.apache.org/manual/bean-binding.html).
- Naming: `@Identifier` is documented next to `@Named` (https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html).

## Upgrade steps

1. Set `quarkus.platform.version=3.40.1`, import `quarkus-bom` and `quarkus-camel-bom` (medium confidence, via the core research; https://camel.apache.org/camel-quarkus/3.40.x/user-guide/dependency-management.html).
2. Run `quarkus update` and apply the migration guides.
3. Audit `@Identifier`-only beans referenced only from routes and add `@Unremovable` (ArC removal of such a bean is (unverified); see [register](./unverified-and-risks.md)).
4. Replace `camel-quarkus-junit5` test artifacts and the `junit5` imports.
5. Run `mvn verify -Dnative` (representative) to catch missing reflection registration.

## Compatibility matrix

| Dependency | Min | Max | Source |
|---|---|---|---|
| camel-quarkus-bean | 3.40.0 | 3.40.x | https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-bean/ (uploaded 2026-09-24) |
| Camel | 4.22.1 | 4.22.x | https://camel.apache.org/camel-quarkus/latest/ |
| Quarkus | 3.40.1 | 3.40.x | https://camel.apache.org/camel-quarkus/latest/ |
| GraalVM | 25.0.4.1 | 25.0.4.1 | https://camel.apache.org/camel-quarkus/latest/ |
| Java | 17 | 21 | https://camel.apache.org/releases/q-3.40.0/ ("This version supports Java 17 and 21") |
