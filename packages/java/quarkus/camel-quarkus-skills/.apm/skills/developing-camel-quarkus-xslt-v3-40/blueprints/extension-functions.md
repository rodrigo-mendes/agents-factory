# Xalan Extension Functions (Camel Quarkus 3.40.x)

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Confidence: that disabling secure processing permits Xalan extension functions is High, as in SKILL.md (versioned page: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html). The other setup conditions (separate jar, reflection registration) are (medium confidence), see M3 in the register (evidence rule: not quoted from a versioned page read by the researcher; source page https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html). This is an Ask First topic.

## Preconditions

Extension functions work only if all three hold (conditions 2 and 3 are (medium confidence)):

1. Secure processing is disabled for the application.
2. The functions live in a **separate jar** (not the application module itself).
3. They are registered for reflection at native build time.

Disabling secure processing is a security trade-off: since 3.40 the feature map applies to every template, including runtime-loaded ones, and a startup warning is logged (https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html). Only do this when every template is trusted.

## Configuration (from the extension page)

```java
// Camel Quarkus 3.40.x
import io.quarkus.runtime.annotations.RegisterForReflection;

@RegisterForReflection(targets = { my.Functions.class })
public class FunctionsConfiguration { }
```

```properties
quarkus.camel.xslt.features."http\://javax.xml.XMLConstants/feature/secure-processing"=false
```

`@RegisterForReflection` is a Quarkus annotation; the import is added here for completeness and is not shown on the page. This class needs no `@ApplicationScoped`.

## Ask before doing it

- Are all stylesheets shipped by the team, with no runtime or header-supplied templates?
- Can the functions be packaged in a separate jar?
- Is a native build required? (Test it; the native behaviour of the functions beyond the three preconditions is (unverified).)

## Saxon alternative

`camel-quarkus-xslt-saxon` has its own `saxonExtensionFunctions` option (https://camel.apache.org/components/4.22.x/xslt-saxon-component.html, medium confidence). Its interaction with the 3.40 hardening is unverified.
