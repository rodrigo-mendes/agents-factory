# Migration Guide to 3.40 — camel-quarkus-http

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Sources: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html and https://camel.apache.org/releases/q-3.40.0/

## HTTP-relevant changes by version

| Version | Change | Source |
|---|---|---|
| CQ 3.36.0 | `camel-quarkus-tls-registry` added (GitHub #8603) | https://github.com/apache/camel-quarkus/releases |
| CQ 3.39.0 | Native-mode Jolokia refuses an HTTPS origin over a plain HTTP agent. Not camel-http. | https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.39.0.html |
| CQ 3.40.0 | TLS registry protocols, ciphers and key-exchange groups enforced on bridged beans; default TLSv1.3 only; unknown or OpenSSL names fail (fix #9113; PR #9114) | https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html |
| Camel 4.18 | gzip responses decompressed twice with HttpClient 5.6+; fixed by stripping stale `Content-Encoding`/`Content-Length`/`Content-MD5` headers (medium confidence; page partially read, L1) | https://camel.apache.org/manual/camel-4x-upgrade-guide-4_18.html |
| Camel 4.21 | `ObjectInputFilter` on the `transferException` / `allowJavaSerializedObject` path, new `deserializationFilter` option (medium confidence; page partially read, L1) | https://camel.apache.org/manual/camel-4x-upgrade-guide-4_21.html |
| Camel 4.19, 4.20, 4.22 | No camel-http producer change found | https://camel.apache.org/manual/camel-4x-upgrade-guide-4_22.html (and 4_19, 4_20) |

Testing: `camel-quarkus-junit5` was renamed `camel-quarkus-junit` since 3.31 (High; https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html). Details and test style live in the skill `developing-camel-quarkus-junit-v3-40`; BOM and core topics in `developing-camel-quarkus-core-v3-40`.

## Upgrade steps

1. Bump `quarkus.platform.version` to 3.40.1 (BOM rules: core skill).
2. Grep for `quarkus.tls.` and check every protocol and cipher name against JSSE names.
3. List the HTTPS partners without TLS 1.3 and add named buckets for them.
4. Replace any `camel-quarkus-resilience4j` with `camel-quarkus-microprofile-fault-tolerance`.
5. Re-check `okStatusCodeRange`, the timeouts and `allowJavaSerializedObject`.

```bash
# Representative; adapt to your environment
grep -rn "quarkus.tls" src/main/resources/application.properties
./mvnw dependency:tree | grep httpclient5   # resolves the HttpClient 5 version, which is (unverified) from documentation
# Expected: BUILD SUCCESS; no "SSL context" creation errors at startup (log output unverified)
```

## Compatibility matrix

| Dependency | Value | Source |
|---|---|---|
| Camel Quarkus | 3.40.0 to 3.40.x; http 3.40.0 on Central 2026-09-24 | https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-http/ |
| Camel | 4.22.x | https://camel.apache.org/camel-quarkus/latest/ |
| Apache HttpClient | 5.6.3 in the Camel 4.22.x parent POM; Quarkus-resolved version (unverified) | https://github.com/apache/camel/blob/camel-4.22.x/parent/pom.xml |
| Java | 17 and 21 | https://camel.apache.org/releases/q-3.40.0/ |
| camel-quarkus-tls-registry | 3.36.0 to 3.40.x, Experimental | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/tls-registry.html |
