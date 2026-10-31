---
name: developing-camel-quarkus-log-v3-40
description: "Guides Camel Quarkus 3.40.x logging (Camel 4.22): camel-quarkus-log, Log EIP, camel-quarkus-mdc, masking, Quarkus log config. Use when routes log, mask data or correlate with MDC. Not for Quarkus 4, other versions or non-Camel logging."
---

# Developing with Camel Quarkus Log 3.40.x

> Version lock: every claim applies to **Camel Quarkus 3.40.x** (Camel 4.22.x component docs, Quarkus 3.40.x) only. Research date **2026-10-14**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against a versioned official page; treat them as hypotheses.
> Core topics (BOMs, CDI, route discovery, testing harness) belong to the sibling skill `developing-camel-quarkus-core-v3-40`.

## Version Context

| Item | Value | Source (fetched 2026-10-14) |
|---|---|---|
| Camel Quarkus | 3.40.0 released 2026-09-28 and marked LTS (no LTS-until date is given) | https://camel.apache.org/releases/ |
| Camel, Quarkus, GraalVM | Camel 4.22.1, Quarkus 3.40.1, GraalVM 25.0.4.1 | https://camel.apache.org/camel-quarkus/latest/ |
| Java | 17 and 21 ("This version supports Java 17 and 21."; the page names no Camel or Quarkus version) | https://camel.apache.org/releases/q-3.40.0/ |
| Camel 4.22.1 release | 2026-09-17, marked LTS | https://camel.apache.org/releases/ |
| `camel-quarkus-log` | Log component (`log:`), producer only; JVM and native since 0.0.1; no extension options of its own | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/log.html |
| `camel-quarkus-mdc` | JVM and native since 3.29.0; replaces the deprecated `camel.main.useMdcLogging` | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/mdc.html |
| `camel-mdc` (Camel) | Available since Camel 4.15 | https://camel.apache.org/components/4.22.x/others/mdc.html |
| Quarkus 3.40 | Released 2026-09-30 as an LTS, community-maintained until 2027-09-30 | https://quarkus.io/releases |

**Version-lifetime risk** (as of 2026-10-14; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- Quarkus 4.0.0.Beta1 was published 2026-10-01, the final release is "planned for the end of November" and the highlights list Java 21 as the new base version ([source](https://quarkus.io/blog/quarkus-4-0-0-beta1-released/)). No Camel Quarkus build on Quarkus 4 is known (medium confidence, absence of evidence). Do not mix Quarkus 4 artifacts.
- 2027-09-30 is the Quarkus 3.40 LTS maintenance end ([source](https://quarkus.io/releases)). The Camel Quarkus-specific end date is not published (unverified).

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Log component and EIP options](./blueprints/log-component-options.md)
- [MDC correlation](./blueprints/mdc.md)
- [Masking and security](./blueprints/masking-and-security.md)
- [Quarkus logging integration](./blueprints/quarkus-logging.md)
- [Migration guide from 3.15](./blueprints/migration-guide.md)
- [Integration examples and testing](./blueprints/integration-examples.md)
- [Unverified and irresolvable register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Use the Log EIP (`.log(...)`) for human messages.** The EIP is "much lighter and meant for logging human logs" ([log EIP](https://camel.apache.org/components/4.22.x/eips/log-eip.html)). See [patterns](./blueprints/always-do-patterns.md#1-eip-versus-component).
- **Use the `log:` component when you need control over what is printed.** It offers `show*` options, `maxChars`, `style` and `multiline` ([log component](https://camel.apache.org/components/4.22.x/log-component.html)). See [options](./blueprints/log-component-options.md).
- **Add `logMask=true` to a `log:` endpoint that may print secrets.** `logMask` defaults to `false` on the endpoint ([log component](https://camel.apache.org/components/4.22.x/log-component.html)). See [patterns](./blueprints/always-do-patterns.md#2-endpoint-masking) and [masking](./blueprints/masking-and-security.md).
- **Use `camel-quarkus-mdc` with `quarkus.camel.mdc.enabled=true` for correlation ids**, because `camel.main.useMdcLogging` is deprecated ([main](https://camel.apache.org/components/4.22.x/others/main.html)). See [patterns](./blueprints/always-do-patterns.md#3-camel-quarkus-mdc) and [MDC](./blueprints/mdc.md).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Free-form body PII (for example card numbers) | `logMask=true` does not cover arbitrary body content: the default formatter masks key-named values, URI userinfo passwords and PEM private-key blocks, and certificates and public keys are not masked ([log EIP](https://camel.apache.org/components/4.22.x/eips/log-eip.html)); a custom `MaskingFormatter` bean bound as `CamelCustomLogMask` can (medium confidence for the wiring), see [masking](./blueprints/masking-and-security.md), or keep the body out of the log line | "Can bodies carry PII that has no key name?" |
| Quarkus category levels and TRACE (medium confidence, read on the unversioned "Latest" guide) | `quarkus.log.category."org.apache.camel".level` for Camel verbosity; `quarkus.log.min-level` (default `DEBUG`) is build-time, so TRACE also needs `quarkus.log.category."<name>".min-level=TRACE` and a rebuild ([guide](https://quarkus.io/guides/logging)) | "Do you need TRACE in a built or native artifact?" |
| Context-wide masking (medium confidence) | `camel.main.logMask=true` also covers the Log EIP, but Camel Quarkus docs confirm `camel.main.*` only for some families (the `durationMax*` family) vs endpoint `logMask=true` per URI | "Should masking be global, and can I verify `camel.main.logMask` in a test?" |
| Streaming bodies (medium confidence, unversioned ambiguous manual page) | Keep `camel.main.streamCachingEnabled=true` (default per [main](https://camel.apache.org/components/4.22.x/others/main.html)) vs disable it; logging a stream body "may cause the message body to be empty afterward" | "Do routes log stream-based bodies (files, HTTP)?" |
| Text vs JSON console (medium confidence, JSON claims from the Quarkus 3.40 guide, coverage not recorded) | Text pattern with `%X{...}` (readable) vs `quarkus-logging-json` (`default`/`ecs`/`gcp`; format and colour settings ignored) ([guide](https://quarkus.io/version/3.40/guides/logging)) | "Which log backend or format does the platform ingest?" |
| Per-message vs throughput logging | One line per exchange vs `groupSize` or `groupInterval` (no message content) ([log component](https://camel.apache.org/components/4.22.x/log-component.html)) | "How many messages per second, and is content needed?" |
| Custom `ExchangeFormatter` | Global bean named `logFormatter` or `camel.component.log.exchange-formatter` ([configuration guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/configuration.html)) vs several `LogComponent` beans per endpoint ([log component](https://camel.apache.org/components/4.22.x/log-component.html)) | "Is one format enough for all log endpoints?" |
| Log EIP logger name (medium confidence) | Route id (default) vs `logName` vs `camel.main.logName` vs source `file:line` (`sourceLocationEnabled`, default `false`) | "Does operations filter by route id or by class/package?" |
| Log EIP language (unverified) | The EIP page says it logs "only ... Simple language", yet `logLanguage` exists; see [register](./blueprints/unverified-and-risks.md) | "Do you need a non-Simple language in `.log(...)`?" |
| MDC on async threads (unverified) | camel-mdc vs Quarkus Vert.x MDC propagation on Camel async threads is not documented | "Which threads must carry the MDC, and can we test it?" |
| Asserting log text in tests (unverified) | Replace the log endpoint with `mock:` and assert routing vs capture log output (no official CQ 3.40.x API found) | "Is checking the log text itself required?" |
| Native-mode beans (medium confidence) | Beans resolved only by registry name may need reflection registration | "Does the native build run with custom formatter or mask beans?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Use `showAll`, `showHeaders` or `showProperties` in production without masking; they dump all headers and properties ([source](https://camel.apache.org/components/4.22.x/log-component.html)) | Select fields: `showExchangeId`, `showRouteId`, `showBodyType`, plus `logMask=true` and a small `maxChars` |
| Set `camel.main.useMdcLogging=true`, or combine it with camel-mdc; it is deprecated and the mdc page says not to combine ([main](https://camel.apache.org/components/4.22.x/others/main.html), [mdc](https://camel.apache.org/components/4.22.x/others/mdc.html)) | `quarkus.camel.mdc.enabled=true` only |
| Use `camel.main.mdcLoggingKeysPattern`; it is deprecated ([main](https://camel.apache.org/components/4.22.x/others/main.html)) | Per the mdc extension page, `quarkus.camel.mdc.custom-exchange-headers` / `custom-exchange-properties` ([mdc ext](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/mdc.html)) |

Full ❌/✅ code: [never-do patterns](./blueprints/never-do-patterns.md). Unconfirmed items: [register](./blueprints/unverified-and-risks.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| Log component `level` / `maxChars` | `INFO` / `10000` | https://camel.apache.org/components/4.22.x/log-component.html |
| `showBody` / `showBodyType` | `true` / `true` | https://camel.apache.org/components/4.22.x/log-component.html |
| `showAll` / `showHeaders` / `showProperties` / `multiline` | `false` / `false` / `false` / `false` | https://camel.apache.org/components/4.22.x/log-component.html |
| `style` / `groupActiveOnly` | `Default` / `true` | https://camel.apache.org/components/4.22.x/log-component.html |
| Endpoint `logMask` | `false`; masks key-named values, URI passwords, PEM private keys only | https://camel.apache.org/components/4.22.x/log-component.html ; https://camel.apache.org/components/4.22.x/eips/log-eip.html |
| Log EIP `loggingLevel` / `logName` | `INFO` / route id | https://camel.apache.org/components/4.22.x/eips/log-eip.html |
| `camel.main.logMask` | `false` (CQ support for this key: medium confidence) | https://camel.apache.org/components/4.22.x/others/main.html |
| `camel.main.useMdcLogging` | `false`, deprecated | https://camel.apache.org/components/4.22.x/others/main.html |
| `camel.main.streamCachingEnabled` | `true` | https://camel.apache.org/components/4.22.x/others/main.html |
| `camel.main.logExhaustedMessageBody` / `sourceLocationEnabled` / `useBreadcrumb` | `false` / `false` / `false` | https://camel.apache.org/components/4.22.x/others/main.html |
| `quarkus.camel.mdc.enabled` | `false` | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/mdc.html |
| Default MDC keys (each only if present) | `camel.breadcrumbId`, `camel.exchangeId`, `camel.messageId`, `camel.correlationId`, `camel.routeId`, `camel.contextId`, `camel.threadId` | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/mdc.html |
| `quarkus.log.level` / `quarkus.log.min-level` | `INFO` / `DEBUG` (min-level is build-time) (medium confidence, read on the unversioned "Latest" guide) | page not recorded |
| JSON `mdc.flat-fields` / `pretty-print` | `false` / `false` (medium confidence, JSON claims from the Quarkus 3.40 guide, coverage not recorded) | https://quarkus.io/version/3.40/guides/logging |
| Representative commands | `mvn quarkus:dev`, `mvn verify -Dnative`, `grep -rn "showAll=true\|useMdcLogging" src/` | page not recorded |

## External Resources

All fetched 2026-10-14. camel.apache.org pages carry no page date and are the current stable 3.40.x / 4.22.x docs.

- Log extension: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/log.html
- MDC extension: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/mdc.html
- Log component (4.22.x): https://camel.apache.org/components/4.22.x/log-component.html
- Log EIP (4.22.x): https://camel.apache.org/components/4.22.x/eips/log-eip.html
- Main properties (4.22.x): https://camel.apache.org/components/4.22.x/others/main.html
- Quarkus logging guide (3.40): https://quarkus.io/version/3.40/guides/logging
- Releases: https://camel.apache.org/releases/ ; Java support: https://camel.apache.org/releases/q-3.40.0/
- Quarkus LTS policy: https://quarkus.io/releases
- Full bibliography: [unverified and risks](./blueprints/unverified-and-risks.md#source-bibliography)
