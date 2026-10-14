# Migration Guide to Platform HTTP 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md).

## Breaking changes relevant to platform-http

| Change | Detail | Source |
|---|---|---|
| No platform-http item | The 3.40.0 guide has no entry for platform-http | https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html |
| TLS registry bridging | Protocols, ciphers and key-exchange groups are applied to Camel SSL contexts built from registered beans; default TLSv1.3 only; unknown names fail; a configured cipher list overrides Camel's exclusion filters; `certificate-revocation-list`, `hostname-verification-algorithm`, `key-store.sni`, `alpn`, `pqc-enforcement-policy` still not bridged | https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html |
| Inbound server impact | (unverified); the guide is silent. See [Does the 3.40 bridging affect the inbound server](./tls-and-security.md#does-the-340-bridging-affect-the-inbound-server). | page not recorded |
| Upload body and headers | Since Camel 4.10 a single upload is in the body with `CamelFileName`, `CamelFileContentType`, `CamelFileLength`; several uploads set `CamelAttachmentsSize` | https://camel.apache.org/components/4.22.x/platform-http-component.html |

## Upgrade steps

1. Set `quarkus.platform.version=3.40.1`: Camel Quarkus 3.40.x uses Quarkus 3.40.1 (High, https://camel.apache.org/camel-quarkus/latest/).
2. Run `quarkus update`, then apply each Camel Quarkus migration guide between your version and 3.40 (index: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/index.html, not re-fetched) (medium confidence).
3. Re-test uploads: check the body and the `CamelFile*` headers rather than relying on attachment-only access.
4. Audit the `quarkus.tls.*` names (JSSE names, not OpenSSL).
5. Test inbound HTTPS with a TLSv1.2 client (see [Does the 3.40 bridging affect the inbound server](./tls-and-security.md#does-the-340-bridging-affect-the-inbound-server)) and compare with the pre-upgrade result.
6. Re-check the real URLs if `quarkus.http.root-path` is set; its effect on Camel routes is (unverified).

## Compatibility

| Dependency | Version | Source |
|---|---|---|
| Java | 17 and 21 (High) | https://camel.apache.org/releases/q-3.40.0/ |
| Camel | 4.22.x (component docs) | https://camel.apache.org/components/4.22.x/platform-http-component.html |
| Quarkus | 3.40.x | https://quarkus.io/version/3.40/guides/http-reference |
| `quarkus-vertx-http` | managed by the platform BOM | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html |
| Quarkus 4 | no Camel Quarkus build known as of 2026-10-14 (medium confidence, absence of evidence; the Beta1 post does not mention Camel Quarkus) | see [version-lifetime risk](./unverified-and-risks.md#version-lifetime-risk) |

## Dependency

```xml
<!-- Camel Quarkus 3.40.x; version managed by the Quarkus platform BOM -->
<dependency>
  <groupId>org.apache.camel.quarkus</groupId>
  <artifactId>camel-quarkus-platform-http</artifactId>
</dependency>
```

Native mode is supported since 0.3.0; for non-default character encodings see the charsets section of the native-mode guide ([extension page](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html)).
