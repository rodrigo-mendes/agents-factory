# File Consumer and Producer: Camel Quarkus 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). All option defaults come from https://camel.apache.org/components/4.22.x/file-component.html unless another URL is given.

Contents: [Consumer lifecycle](#consumer-lifecycle) · [Atomic writes](#atomic-writes) · [Idempotency](#idempotency) · [File language](#file-language) · [Performance](#performance-and-batching)

## Consumer lifecycle

```java
// Camel Quarkus 3.40.x: discovered RouteBuilder, no CDI annotation needed (no @Inject/@ConfigProperty)
public class FileIngestRoute extends org.apache.camel.builder.RouteBuilder {
    @Override
    public void configure() {
        errorHandler(deadLetterChannel("file:/data/dlq").maximumRedeliveries(3));

        from("file:/data/in"
             + "?antInclude=**/*.xml&recursive=true"            // recursive default false
             + "&readLock=changed&readLockMinAge=1000"
             + "&move=archive/${file:name}&moveFailed=error/${file:name}"
             + "&maxMessagesPerPoll=100&sortBy=file:modified"
             + "&bridgeErrorHandler=true")                      // default false
            .routeId("file-ingest")
            .log("Got ${file:name} (${file:size} bytes)")
            .to("direct:process");
    }
}
```

Defaults (high confidence, file component page):

| Option | Default |
|---|---|
| `initialDelay` / `delay` | `1000` ms / `500` ms |
| `autoCreate` | `true` |
| `recursive` | `false` |
| `include` / `exclude` | case-insensitive regexes; `antExclude` overrides `antInclude` |
| `bufferSize` | `131072` bytes |
| `bridgeErrorHandler` | `false`: the default consumer `ExceptionHandler` logs and ignores polling exceptions |
| `maxMessagesPerPoll` | no limit |

- The consumed body "will be a `File` object". The runtime type `GenericFile<File>` is (unverified).
- `onCompletionExceptionHandler` logs commit/rollback failures at WARN.
- `directoryName` must not contain `${ }` placeholders; dynamic names go in `fileName` or the `CamelFileName` header.

## Atomic writes

With `tempPrefix`/`tempFileName` the file "is written under the temporary name, then renamed". `doneFileName` makes the consumer wait for a done file and makes the producer write one. Neither has a default. `fileExist` defaults to `Override` (values: Override, Append, Fail, Ignore, Move, TryRename). The `CamelFileName` and `CamelFileNameProduced` headers are confirmed on the same page.

```java
// Camel Quarkus 3.40.x: producer side
from("direct:export")
    .setHeader(org.apache.camel.Exchange.FILE_NAME, simple("orders-${date:now:yyyyMMddHHmmss}.xml"))
    .to("file:/data/out?tempPrefix=.inprogress-&fileExist=Fail&doneFileName=${file:name}.done");
```

## Idempotency

`idempotent` defaults to `false`. Without an `idempotentRepository`, Camel uses "a memory based LRUCache that holds 1000 entries", which is lost on restart. `idempotentKey` defaults to the absolute file path; `idempotentEager` defaults to `true`.

```java
// Camel Quarkus 3.40.x: repository bean named "fileRepo" (for example a JDBC or Infinispan repository)
from("file:/data/in?idempotent=true&idempotentRepository=#fileRepo"
     + "&idempotentKey=${file:name}-${file:size}&move=done/${file:name}")
    .to("direct:process");
```

## File language

Source: https://camel.apache.org/components/4.22.x/languages/file-language.html (high confidence).

| Group | Variables |
|---|---|
| Names | `file:name`, `file:name.ext`, `file:name.noext`, `file:onlyname`, `file:onlyname.noext` |
| Paths | `file:ext`, `file:parent`, `file:path`, `file:absolute`, `file:absolute.path` |
| Size and time | `file:length` / `file:size` (Long), `file:modified` (Date) |
| Dates | `date:<command>:<pattern>` |

`file:absolute*` and `date:file:` are consumer-only.

## Performance and batching

- Polling cadence: `delay` 500 ms, `initialDelay` 1000 ms.
- In Camel 4.22 use `preSort` (String: `name|modified|size|-name|-modified|-size|true`) (medium confidence); the 4.22 upgrade guide was only partly read ([guide](https://camel.apache.org/manual/camel-4x-upgrade-guide-4_22.html)). The research pairs it with an eager max-messages-per-poll option, but that option name and the 4.13 behaviour change are (unverified): check the real name in the 4.13 upgrade guide.
- The in-progress repository is FIFO since 4.19 ([guide](https://camel.apache.org/manual/camel-4x-upgrade-guide-4_19.html)).
- `readLockLoggingLevel` appears in the official test; its default was not recorded (unverified).
