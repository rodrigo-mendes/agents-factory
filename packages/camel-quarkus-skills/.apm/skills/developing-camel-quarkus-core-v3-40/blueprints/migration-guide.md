# Migration Guide 3.15 to 3.40 — Camel Quarkus

Research date 2026-10-14. Confidence: high for the per-version rows; the Maven and Java 25 cells and the Quarkus 4 cell carry their own tags. Source: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/index.html plus per-version guides (no page dates). Back to [SKILL.md](../SKILL.md).

## Breaking changes (core-relevant)

| Version | Change |
|---|---|
| 3.31 | `camel-quarkus-junit5` renamed to `camel-quarkus-junit`; `org.apache.camel.test.junit5` to `junit6`; `camel-test-junit5` to `camel-test-junit6` |
| 3.33 | Deprecated `quarkus.camel.jolokia.register-management-endpoint` removed |
| 3.35 | `camel-quarkus-groovy-xml` merged into `camel-quarkus-groovy` |
| 3.36 | AdviceWith auto-starts un-advised routes, adds the `adviceRoute()` helper and cleans up advice automatically. Quarkus 3.36 raises the Mandrel/GraalVM minimum to 25.0. |
| 3.38 | `quarkus-cxf-rt-ws-security` removed from `camel-quarkus-cxf-soap` |
| 3.39 | Jolokia locked down in prod (binds to localhost, origin filtering). Cassandra health check disabled by default. |
| 3.40 | `serialization-enabled` has three states (unset, true, false). TLS registry protocols, ciphers and key-exchange groups are bridged (TLSv1.3 default). XSLT restricted (external entities, `document()`). Avro trusted packages required. LDAP `security-authentication` no longer defaults to `none`. JTA rollback and resume failures are raised. LangChain4j and AI-tool modules reorganised. |

The index has no migration guides for 3.34.x or 3.37.x.

## Upgrade steps

1. Bump `quarkus.platform.version` to `3.40.1`.
2. Run `quarkus update` (Quarkus 3.40 blog). From 3.33 LTS, apply the migration guides 3.34 to 3.40. From 3.39, no changes are needed.
3. Replace junit5 artifacts and imports with junit/junit6.
4. Audit any `serialization-enabled=false` and any `quarkus.tls.*` settings.
5. Make sure native builders use Mandrel/GraalVM 25.

## Compatibility matrix

| Dependency | Min | Max | Notes |
|---|---|---|---|
| Java (CQ 3.40) | 17 | 21 | "This version supports Java 17 and 21" (https://camel.apache.org/releases/q-3.40.0/). Java 25 for CQ is (unverified) (Quarkus JVM mode supports 17 to 25) |
| Camel | 4.22.1 | 4.22.x | docs index |
| Quarkus | 3.40.1 | 3.40.x | Quarkus 4 not supported: no Camel Quarkus build on Quarkus 4 is known (medium confidence, absence of evidence) |
| GraalVM/Mandrel | 25.0 | none | docs index lists 25.0.4.1 |
| Maven | 3.8.2 | none | 3.9.16 recommended (unverified; page not recorded) |

Sources: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/{3.31.0,3.33.0,3.35.0,3.36.0,3.38.0,3.39.0,3.40.0}.html ; https://quarkus.io/blog/quarkus-3-40-released/ (2026-09-30) ; https://quarkus.io/blog/mandrel-25-minimum-version/ (2026-05-29)
