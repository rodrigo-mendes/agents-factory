# Native Mode for File Routes: Camel Quarkus 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). General native rules (reflection, Jandex, `@RegisterForReflection`) are in the core skill.

## Support matrix

| Extension | JVM / native | Source |
|---|---|---|
| `camel-quarkus-file` | both, since 0.4.0 | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/file.html |
| `camel-quarkus-file-watch` | both, since 1.0.0 | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/file-watch.html |
| `camel-quarkus-ftp` | both, since 1.0.0 | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/ftp.html |
| `camel-quarkus-mina-sftp` | both, since 3.33.0 | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/mina-sftp.html |
| `camel-quarkus-file-cluster-service` | both, since 3.10.0 | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/file-cluster-service.html |

## Charsets (conditional)

"By default, not all Charsets are available in native mode." Set `quarkus.native.add-all-charsets=true` only when an `UnsupportedCharsetException` appears; the File consumer already defaults to `UTF-8`.

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| Default | Image size | Non-default charsets missing | UTF-8 only |
| `add-all-charsets=true` | Any `charset=` works | Larger native image | `charset=ISO-8859-1` etc. in native |

Sources: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html ; https://camel.apache.org/components/4.22.x/file-component.html

## Classpath resources

Anything loaded from the classpath at runtime needs `quarkus.native.resources.includes` (comma-separated Ant globs). XSLT sources are compiled instead, through `quarkus.camel.xslt.sources`. Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html

```properties
# Camel Quarkus 3.40.x: application.properties
quarkus.native.resources.includes = templates/*
quarkus.camel.xslt.sources = xslt/order.xsl
```

## Other native notes

- XSLT: only `classpath:` URIs work in native; `file:` and `http:` URIs, `<xsl:messaging>` and `XsltSaxonAggregationStrategy` are JVM-only ([xslt](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html)).
- JAXB: POJOs created by a custom `ObjectFactory` without JAXB annotations must be registered for reflection ([jaxb](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/jaxb.html)).
- file-watch on macOS: native mode uses `java.nio.file.WatchService`, possibly slower ([file-watch](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/file-watch.html)).
- SSH library used by `camel-quarkus-ftp` in native: (unverified).
- Native tests (`@QuarkusIntegrationTest`) run out of process; test through the network or by observing the file system ([testing guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html)).
- `mvn verify -Dnative` is a representative command; its log output was not recorded (log output unverified).
