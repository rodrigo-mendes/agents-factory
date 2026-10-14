# Masking and Security

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md).

## What is masked (high confidence)

`logMask` defaults to `false` on the endpoint (https://camel.apache.org/components/4.22.x/log-component.html). The default `DefaultMaskingFormatter` masks key-named values, URI userinfo passwords and PEM private-key blocks. Certificates and public keys are not masked (https://camel.apache.org/components/4.22.x/eips/log-eip.html). Free-form body content with no key name (for example a bare card number inside a JSON string) is not covered by the default formatter; use the custom mask below or keep the body out of the log line.

```java
.to("log:com.acme.orders?showExchangeId=true&logMask=true")
```

## Context-wide masking (medium confidence)

`camel.main.logMask` defaults to `false` and also covers the Log EIP (main and log EIP pages). Camel Quarkus docs confirm `camel.main.*` only for some families (the `durationMax*` family, via camel-quarkus-core: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/command-mode.html). That `logMask` behaves the same way is an inference. Verify with a route that logs a masked value before relying on it.

```properties
camel.main.logMask=true
```

## Custom mask (medium confidence for the wiring)

A formatter must implement `org.apache.camel.spi.MaskingFormatter` and be bound as `CamelCustomLogMask` (medium confidence for the wiring). `@ApplicationScoped` is on this CDI bean, not on a route. The Quarkus CDI reference says to prefer `@io.smallrye.common.annotation.Identifier` over `@Named` except when an external language needs the bean name (https://quarkus.io/version/3.40/guides/cdi-reference). Camel's name lookup with `@Identifier` is documented: "As an alternative to @Named, you may also use io.smallrye.common.annotation.Identifier to name and identify a bean" (high confidence, https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html). Whether ArC removes an `@Identifier`-only bean is (unverified); use `@Unremovable`, or keep `@Named` as this sample does, which is unremovable.

```java
@ApplicationScoped
@Named("CamelCustomLogMask")
public class PanMask implements org.apache.camel.spi.MaskingFormatter {
    public String format(String source) { return source.replaceAll("\\b\\d{12,19}\\b", "****"); }
}
```

Native mode: beans used only through registry lookup may need reflection registration (medium confidence; see core skill).

## Other leak controls

- Keep `camel.main.logExhaustedMessageBody` at its default `false` unless masked (https://camel.apache.org/components/4.22.x/others/main.html).
- JSON logging `excluded-keys` can drop sensitive MDC fields (medium confidence, Quarkus 3.40 guide coverage not recorded: https://quarkus.io/version/3.40/guides/logging).
- Do not use `showAll`, `showHeaders` or `showProperties` in production without masking; see [never-do](./never-do-patterns.md#1-dumping-headers-and-properties-severity-high).
- Audit command (representative): `grep -rn "showAll=true\|useMdcLogging" src/` should return no matches.
