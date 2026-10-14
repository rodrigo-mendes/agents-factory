# Security Hardening in Camel Quarkus 3.40 (XSLT)

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Source for all four changes: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html (section "XSLT extension changes"), re-confirmed on https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html. Scope: the `camel-quarkus-xslt` (Xalan-J) extension. Saxon coverage is (unverified).

## The four changes (high confidence)

| # | Change | Consequence |
|---|---|---|
| 1 | Input documents are parsed without resolving external entities or loading external DTDs; a `SAXSource` with a caller-supplied `XMLReader` is passed through unchanged | `String`, `byte[]` and `InputStream` bodies were already parsed safely by Camel; the change mainly affects `Source` bodies and direct factory calls |
| 2 | `document()` fetches are denied unless a `URIResolver` resolves them; the restriction persists through `reset()` and `setURIResolver(null)` | Routes are unaffected because camel-xslt installs its own resolver on every transformer it uses. `xsl:import` and `xsl:include` are not restricted |
| 3 | `quarkus.camel.xslt.features` applies to every template, including those loaded at runtime; an unsupported feature fails endpoint creation | Review existing feature entries; an unsupported feature now fails endpoint creation. Disabling secure processing logs a startup warning |
| 4 | The Xalan-J factory is registered as the JAXP default | `TransformerFactory.newInstance()` anywhere in the app, including Tika and XML Security extension code paths, gets these restrictions |

## What this means for code

- Direct `TransformerFactory` code using `document()` must set its own `URIResolver`; prefer an allow-list implementation (the allow-list design itself is application code, not a documented API).
- `ACCESS_EXTERNAL_DTD` and `ACCESS_EXTERNAL_STYLESHEET` cannot be set via `setAttribute` on this factory; it throws. The extension enforces the restrictions itself.
- Disabling secure processing is the only documented way to enable Xalan extension functions; see [extension functions](./extension-functions.md).

## Not part of 3.40

The Camel 4.23 behaviour (runtime refusal of `http:`, `https:`, `ftp:` and `file:` in `document()`) is documented only on the `next` docs page (https://camel.apache.org/components/next/xslt-component.html) for the unreleased 4.23. It is absent from the 4.22.x page (https://camel.apache.org/components/4.22.x/xslt-component.html). Do not attribute it to 3.40.

## Header-to-parameter exposure (medium confidence)

By default all headers and variables become XSLT parameters; a parameter is used only if declared as a top-level `<xsl:param>` (4.22.x component page). Stripping headers before `xslt:` limits what a caller can inject. The explicit warning about untrusted senders and `document()` is on the 4.23 page only, so treat the SSRF framing as advisory for 3.40.

```java
from("platform-http:/transform")
    .removeHeaders("*", "myParam")
    .to("xslt:classpath:xslt/transform.xsl");
```

## Security checklist (derived from the above)

1. Secure processing on; `quarkus.camel.xslt.features` unset.
2. `allowTemplateFromHeader=false` (component default).
3. Strip untrusted headers before `xslt:` (medium confidence).
4. `document()` only through a deliberate `URIResolver`.
5. No reliance on DTDs or external entities in inputs.
6. Remember the JAXP-default side effect on Tika and XML Security.

Open items: Camel 4.22.x `ACCESS_EXTERNAL_*` defaults for non-Camel-Quarkus factories and Saxon coverage are in the [register](./unverified-and-risks.md).
