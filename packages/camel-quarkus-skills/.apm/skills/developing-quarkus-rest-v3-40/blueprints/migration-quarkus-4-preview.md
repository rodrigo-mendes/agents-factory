# Migration and Quarkus 4 Preview: Quarkus REST 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). "3.15" appears only as a migration baseline.

## Contents

- [Naming from the 3.15 baseline to 3.40](#naming-from-the-315-baseline-to-340)
- [Deprecated in 3.40](#deprecated-in-340)
- [Quarkus 4 preview, not for 3.40](#quarkus-4-preview-not-for-340)
- [Upgrade steps](#upgrade-steps)
- [Compatibility](#compatibility)

## Naming from the 3.15 baseline to 3.40

| Area | 3.40 name | Source |
|---|---|---|
| Server | `quarkus-rest` (successor of RESTEasy Reactive). Whether legacy `quarkus-resteasy-reactive*` names still exist as aliases is (unverified) (register U5) | https://quarkus.io/version/3.40/guides/rest |
| Client | `quarkus-rest-client`, `quarkus-rest-client-jackson`; never `quarkus-resteasy-client` with Quarkus REST | https://quarkus.io/version/3.40/guides/rest |
| Testing | `quarkus-junit` (no `quarkus-junit5` in the 3.40 guide); Camel tests use `camel-quarkus-junit` | https://quarkus.io/version/3.40/guides/getting-started-testing ; https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html |
| Config prefixes | `quarkus.rest.*` and `quarkus.rest-client.*` | https://quarkus.io/version/3.40/guides/rest |

## Deprecated in 3.40

The proxy settings and `multipart.max-chunk-size` listed in [REST client](./rest-client.md#deprecated-settings) are deprecated in the 3.40 reference (High; https://quarkus.io/version/3.40/guides/rest-client).

## Quarkus 4 preview, not for 3.40

High (https://quarkus.io/blog/quarkus-4-0-0-beta1-released/): Beta1 was published 2026-10-01; final release "planned for the end of November"; Java 21 is the new base; for Jackson 3 "everything has changed except for the annotations".

Medium confidence (Quarkus 4 migration wiki, unversioned, https://github.com/quarkusio/quarkus/wiki/Migration-Guide-4.0; register M7). Do NOT apply to 3.40:

- Packages move from `com.fasterxml.jackson.databind` to `tools.jackson.databind`; annotations keep `com.fasterxml.jackson.annotation`.
- Quarkus produces a `JsonMapper` bean; `ObjectMapperCustomizer` is renamed `JsonMapperBuilderCustomizer`.
- Endpoints may no longer return REST Client `Response` or `RestResponse`.
- `SseEventSink.close()` throws `IOException`.
- RESTEasy 7 and partial Jakarta REST 4.
- The deprecated client proxy settings are removed in favour of `proxy-configuration-name` and `max-chunk-size`.

No Camel Quarkus build on Quarkus 4 is known (medium confidence, absence of evidence; register M8).

## Upgrade steps

Representative, from the research:

1. Replace `quarkus-resteasy*` artifacts with `quarkus-rest*` equivalents.
2. Replace `quarkus-junit5` with `quarkus-junit` and `camel-quarkus-junit5` with `camel-quarkus-junit`.
3. Move proxy settings to `quarkus.rest-client."key".proxy-configuration-name`.
4. Move REST client TLS to `tls-configuration-name` plus `quarkus.tls.<name>.*`.
5. `./mvnw quarkus:update`: tooling hint, command not verified on a 3.40 page.

## Compatibility

| Dependency | Value | Source |
|---|---|---|
| Java (virtual threads) | 21 or later | https://quarkus.io/version/3.40/guides/virtual-threads |
| Camel Quarkus | 3.40.x with Quarkus 3.40.1 and Camel 4.22.1 | https://camel.apache.org/camel-quarkus/latest/ |
| Jackson | 2.x; exact version (unverified) (register U3); Jackson 3 only in Quarkus 4 | page not recorded |
| OpenAPI document | 3.1.0 default | https://quarkus.io/version/3.40/guides/openapi-swaggerui |
