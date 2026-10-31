# Log Component and Log EIP Options

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Only defaults recorded in the research are listed; for any other option, read the page (default: page not recorded).

## Extension

`camel-quarkus-log` (groupId `org.apache.camel.quarkus`) packages the Camel Log component (`log:loggerName`, producer only). JVM and native since 0.0.1; the extension page has no configuration of its own and defers to the Camel 4.22.x component page. Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/log.html

## Log component (`log:`)

| Option | Default | Notes |
|---|---|---|
| `level` | `INFO` | Level of the line written |
| `maxChars` | `10000` | Caps each line |
| `showBody` / `showBodyType` | `true` / `true` | |
| `showAll` / `showHeaders` / `showProperties` | `false` / `false` / `false` | See [masking](./masking-and-security.md) |
| `multiline` | `false` | |
| `style` | `Default` | |
| `logMask` | `false` | Endpoint-level masking switch |
| `groupActiveOnly` | `true` | Throughput logging |
| `showStreams`, `showFuture` | page not recorded | `showStreams` can consume the stream; `showFuture` blocks until the Future completes |
| `lazyStartProducer` | page not recorded | Delays the first message |

Options named by the research, with defaults not recorded: `showExchangeId`, `showRouteId`, `showRouteGroup`, `showVariables`, `showCachedStreams`, `sourceLocationLoggerName`, `plain`, `groupSize`, `groupInterval`, `groupDelay`.

Throughput logging: set `groupSize`, or `groupInterval` with `groupDelay`. It prints statistics per group and no message content.

```java
from("timer:bulk?period=10").to("log:com.acme.bulk?groupInterval=10000&groupDelay=5000");
```

Source: https://camel.apache.org/components/4.22.x/log-component.html

## Custom formatter

- Property form (verbatim example from the CQ 3.40.x configuration guide):

```properties
camel.component.log.exchange-formatter = #class:org.apache.camel.support.processor.DefaultExchangeFormatter
camel.component.log.exchange-formatter.show-exchange-pattern = false
camel.component.log.exchange-formatter.show-body-type = false
```

- Bean form: a bean named `logFormatter` is auto-detected and applies to every Log endpoint. For per-endpoint formatters use several `LogComponent` beans.

Sources: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/configuration.html ; https://camel.apache.org/components/4.22.x/log-component.html

## Log EIP (`.log(...)`)

- Defaults: `loggingLevel=INFO`, `logName` = route id.
- Logger name choices (medium confidence): `logName` per EIP; global `camel.main.logName`; `CamelLogEipName` via `camel.main.globalOptions`; source `file:line` when `camel.main.sourceLocationEnabled=true` (default `false`).
- Language: the page says the EIP logs "only ... Simple language", yet `logLanguage` / `camel.main.logLanguage` exist. (unverified); see the [register](./unverified-and-risks.md).

Sources: https://camel.apache.org/components/4.22.x/eips/log-eip.html ; https://camel.apache.org/components/4.22.x/others/main.html
