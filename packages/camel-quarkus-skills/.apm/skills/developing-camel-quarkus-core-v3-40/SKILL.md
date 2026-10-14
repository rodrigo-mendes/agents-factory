---
name: developing-camel-quarkus-core-v3-40
description: "Guides Camel Quarkus 3.40.x (Camel 4.22, Quarkus 3.40 LTS) core: BOM, routes, CDI beans, native, TLS. Use when a project uses camel-quarkus-core or camel-quarkus-* 3.40 artifacts or migrates older Camel Quarkus. Not for Quarkus 4."
---

# Developing with Camel Quarkus Core 3.40.x

> Version lock: every claim applies to **Camel Quarkus 3.40.x** only. Research date **2026-10-14**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against a versioned official page; treat them as hypotheses. Tags map to ids in the [register](./blueprints/unverified-and-risks.md#tag-to-register-mapping).

## Version Context

| Item | Value | Source (fetched 2026-10-14) |
|---|---|---|
| Camel Quarkus | 3.40.x (3.40.0 released 2026-09-28, LTS) | https://camel.apache.org/releases/ |
| Camel / Quarkus / GraalVM | 4.22.1 / 3.40.1 / 25.0.4.1 | https://camel.apache.org/camel-quarkus/latest/ |
| Java | 17 and 21; Java 25 for Camel Quarkus: (unverified) | https://camel.apache.org/releases/q-3.40.0/ |
| Native builder | Mandrel/GraalVM 25.0+ (minimum since Quarkus 3.36) | https://quarkus.io/blog/mandrel-25-minimum-version/ (2026-05-29) |
| Maven | 3.8.2 minimum, 3.9.16 recommended (unverified) | page not recorded |

**Version-lifetime risk** (as of 2026-10-14; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- Quarkus 4.0.0.Beta1 was published 2026-10-01, GA is planned for the end of November, and Java 21 is the new base ([source](https://quarkus.io/blog/quarkus-4-0-0-beta1-released/)).
- No Camel Quarkus build on Quarkus 4 is known; the Beta1 post does not mention Camel Quarkus (medium confidence, absence of evidence). Do not mix Quarkus 4 artifacts.
- The maintenance end date of 2027-09-30 is the Quarkus 3.40 LTS date ([source](https://quarkus.io/releases)). The Camel Quarkus-specific end date is (unverified) ("LTS Until" column blank); applying the Quarkus date to Camel Quarkus is an inference.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Migration guide 3.15 to 3.40](./blueprints/migration-guide.md)
- [Native mode](./blueprints/native-mode.md)
- [TLS and security](./blueprints/tls-and-security.md)
- [Integration examples, testing, endpoints](./blueprints/integration-examples.md)
- [Unverified and irresolvable register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Import `quarkus-bom` and `quarkus-camel-bom` with the same `quarkus.platform.version`** (3.40.1), as the [dependency management guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/dependency-management.html) requires. See [patterns](./blueprints/always-do-patterns.md#1-bom-import).
- **Add `@ApplicationScoped` to a RouteBuilder only when it needs `@Inject` or `@ConfigProperty`** ([CDI guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html)). See [patterns](./blueprints/always-do-patterns.md#2-routebuilder-discovery).
- **Rely on automatic RouteBuilder discovery**: route classes are found without extra annotations ([CDI guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html)). See [patterns](./blueprints/always-do-patterns.md#2-routebuilder-discovery).
- **Name beans that routes look up by name with `@Named`**: ArC does not remove them ([CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference)). The naming choice is under Ask First. See [patterns](./blueprints/always-do-patterns.md#3-named-beans).
- **List reflection classes and resources explicitly for native mode** (`quarkus.camel.native.reflection.include-patterns`, `quarkus.native.resources.includes`), because dynamic reflection is unavailable by default ([native mode guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html)). See [native mode](./blueprints/native-mode.md).
- **Use `camel-quarkus-junit` (test scope) with `@QuarkusTest`**: it is the only test artifact in the [3.40 testing guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html). Test-support signatures live in `developing-camel-quarkus-junit-v3-40`. See [integration examples](./blueprints/integration-examples.md#testing).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| BOM choice | Platform `quarkus-camel-bom` (default, aligned) vs `camel-quarkus-bom` (newer CQ, "may not be perfectly aligned") | "Do you need a Camel Quarkus version newer than the platform?" If no, use the platform BOM. |
| `serialization-enabled` | unset (default) / `true` (Cassandra, Infinispan aggregation repositories) / `false` (breaks jms, jolt, management, netty, sjms, sjms2, sql) | "Does the app use jms/sjms/sql/netty/jolt/management?" |
| TLS scope | Default TLSv1.3 vs global widening (`quarkus.tls.protocols`); inbound platform-http impact (unverified); vs a named TLS configuration for one legacy endpoint ([3.40.0 guide](https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html)) | "Which downstream endpoints lack TLS 1.3?" Prefer the named configuration. |
| HTTP surface | `rest()` DSL on platform-http vs Quarkus REST resource with injected `ProducerTemplate`. The second option is shown in the official examples repo (main branch, `quarkus-rest-json`, `OrderResource.java`) (medium confidence); coexistence with platform-http on one server is (unverified). | "Is the HTTP API or the integration the primary concern?" |
| Runtime catalog (medium confidence) | Defaults vs `quarkus.camel.runtime-catalog.*=false` (smaller native image, no catalog tooling) | "Does image size matter more than runtime introspection?" |
| Error handling (medium confidence; manual pages are unversioned) | Default `onException` does not redeliver; `handled(true)` hides the exception from the caller; dead letter channel default redelivery count and delay (unverified) | "Should callers see the failure? Is the flow async?" See [examples](./blueprints/integration-examples.md#error-handling). |
| Component customization (medium confidence) | Observe `ComponentAddEvent` (recommended by the bootstrap guide) vs producing your own component instance (skips Quarkus customization). The event's package is (unverified). | Resolve the import with the IDE and confirm. |
| Bean naming | `@Named` (unremovable per the [Quarkus CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference)) vs `@io.smallrye.common.annotation.Identifier` (lookup from Camel routes is documented on the [Camel Quarkus CDI page](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html); the CDI reference prefers it over `@Named` unless an external language needs the name). ArC removal of an `@Identifier`-only bean is (unverified). | Prefer `@Identifier` plus `@Unremovable`; use `@Named` only if an external language needs the name. |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Set `quarkus.camel.native.reflection.serialization-enabled=false` with jms, sjms, sjms2, sql, netty, jolt or management present. In 3.40 it blocks every serialization registration, and only a warning is logged ([3.40.0 guide](https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html)). | Leave it unset (3.40 default). |
| Use OpenSSL-style or unknown protocol/cipher names in `quarkus.tls.*`. Since 3.40.0 they fail SSL context creation ([3.40.0 guide](https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html)). | Use JSSE protocol and cipher names (`TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256`) ([3.40.0 guide](https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html)). |
| Add `@ApplicationScoped` to a `RouteBuilder` that needs neither `@Inject` nor `@ConfigProperty`; it adds boot-time cost ([CDI guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html)). | Plain `extends RouteBuilder`; it is discovered automatically. |
| Rely on dynamic reflection or unlisted classpath resources in native mode ([native mode guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html)). | Declare patterns and `quarkus.native.resources.includes`. |

Full examples, patterns that are not High, and the `camel-quarkus-junit5` stub note: [never-do patterns](./blueprints/never-do-patterns.md). Camel test rules: `developing-camel-quarkus-junit-v3-40`.

## Quick Reference

Sources fetched 2026-10-14. Where the research did not record the exact page, the row says `page not recorded`.

| Aspect | Value | Source |
|---|---|---|
| Bootstrap | `quarkus.camel.bootstrap.enabled=true` (default); the CamelContext follows the Quarkus lifecycle | https://camel.apache.org/camel-quarkus/3.40.x/user-guide/bootstrap.html |
| Shutdown | `quarkus.camel.main.shutdown.timeout`, default `PT3S` | page not recorded |
| Health | `camel-quarkus-microprofile-health`; `quarkus.camel.health.enabled=true` by default (build time) | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/microprofile-health.html |
| Expression extraction | `quarkus.camel.expression.extraction-enabled=true` (default) | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/core.html |
| `direct:` | Synchronous, same CamelContext, `timeout=30000`, `failIfNoConsumers=true` | https://camel.apache.org/components/4.22.x/direct-component.html |
| Default TLS | TLSv1.3 only on bridged Camel SSL contexts | https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html |
| Native tests | `@QuarkusIntegrationTest` | page not recorded |
| Representative commands | `mvn quarkus:dev`, `mvn test`, `mvn verify -Dnative` (representative; log output unverified) | page not recorded |

## External Resources

All fetched 2026-10-14. camel.apache.org pages carry no page date and are the current stable 3.40.x docs.

- Docs index: https://camel.apache.org/camel-quarkus/3.40.x/
- Releases: https://camel.apache.org/releases/ (3.40.0, 2026-09-28, LTS)
- Dependency management: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/dependency-management.html
- CDI: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html
- Native mode: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html
- Core reference: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/core.html
- Testing: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html
- Migration guides: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/index.html
- Quarkus 3.40 release: https://quarkus.io/blog/quarkus-3-40-released/ (2026-09-30)
- Quarkus 4.0.0.Beta1: https://quarkus.io/blog/quarkus-4-0-0-beta1-released/ (2026-10-01)
- Quarkus LTS policy: https://quarkus.io/releases
- Platform BOM: https://repo1.maven.org/maven2/io/quarkus/platform/quarkus-camel-bom/ (3.40.1, 2026-09-30)
- Full bibliography: [unverified and risks](./blueprints/unverified-and-risks.md#source-bibliography)
