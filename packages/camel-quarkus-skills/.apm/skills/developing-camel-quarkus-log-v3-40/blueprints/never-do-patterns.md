# Never-Do Patterns: Camel Quarkus Log 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Items 1 to 3 are in the SKILL.md Never Do table; items 4 and 5 are medium confidence and are advisory only.

Contents: [1 dumping headers and properties](#1-dumping-headers-and-properties-severity-high) · [2 deprecated MDC switch](#2-deprecated-mdc-switch-severity-high) · [3 legacy MDC keys pattern](#3-legacy-mdc-keys-pattern-severity-moderate) · [4 stream caching off](#4-logging-streaming-bodies-with-stream-caching-disabled-severity-high) · [5 runtime TRACE below min-level](#5-runtime-trace-below-min-level-severity-moderate)

## 1. Dumping headers and properties (severity: high)

`showAll`, `showHeaders` and `showProperties` dump all headers and properties. All default to `false`. Impact: headers or properties that carry tokens or credentials reach the log aggregator; `logMask=true` masks only key-named values, URI passwords and PEM private keys, not arbitrary values.

```java
// ❌ WRONG
.to("log:debug?showAll=true&multiline=true")
// ✅ CORRECT
.to("log:com.acme.audit?showExchangeId=true&showRouteId=true&showBodyType=true&logMask=true&maxChars=500")
```

Source: https://camel.apache.org/components/4.22.x/log-component.html

## 2. Deprecated MDC switch (severity: high)

`useMdcLogging` is deprecated, and the mdc page says not to enable it together with camel-mdc. Impact: duplicate or conflicting MDC handling.

```properties
# ❌ WRONG
camel.main.useMdcLogging=true
quarkus.camel.mdc.enabled=true
# ✅ CORRECT
quarkus.camel.mdc.enabled=true
```

Sources: https://camel.apache.org/components/4.22.x/others/main.html ; https://camel.apache.org/components/4.22.x/others/mdc.html

## 3. Legacy MDC keys pattern (severity: moderate)

`camel.main.mdcLoggingKeysPattern` is deprecated (main page). Per the mdc extension page, header and property propagation uses `quarkus.camel.mdc.custom-exchange-headers` and `custom-exchange-properties`. Do not copy 3.15-era recipes.

```properties
# ❌ WRONG
camel.main.mdcLoggingKeysPattern=myKey*
# ✅ CORRECT
quarkus.camel.mdc.custom-exchange-properties=myKey*
```

Sources: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/mdc.html ; https://camel.apache.org/components/4.22.x/others/main.html

## 4. Logging streaming bodies with stream caching disabled (severity: high)

The Log EIP page says logging a stream-based body "may cause the message body to be empty afterward", and `showStreams` can consume the stream. `camel.main.streamCachingEnabled` defaults to `true`. The stream-caching manual page is ambiguous, so this stays medium confidence.

```properties
# ❌ WRONG (route: from("platform-http:/up").log("${body}").to("file:in"))
camel.main.streamCachingEnabled=false
# ✅ CORRECT
camel.main.streamCachingEnabled=true
```

Sources: https://camel.apache.org/components/4.22.x/eips/log-eip.html ; https://camel.apache.org/components/4.22.x/others/main.html ; https://camel.apache.org/components/4.22.x/log-component.html

## 5. Runtime TRACE below min-level (severity: moderate)

`quarkus.log.min-level` (default `DEBUG`) is build-time; below that floor the log code is optimised away, so TRACE never appears even after changing the level at runtime. Medium confidence because the research read the unversioned "Latest" guide (value page not recorded for the 3.40 selector).

```properties
# ❌ WRONG
quarkus.log.category."org.apache.camel".level=TRACE
# ✅ CORRECT (then rebuild)
quarkus.log.category."org.apache.camel".level=TRACE
quarkus.log.category."org.apache.camel".min-level=TRACE
```

Source: https://quarkus.io/guides/logging
