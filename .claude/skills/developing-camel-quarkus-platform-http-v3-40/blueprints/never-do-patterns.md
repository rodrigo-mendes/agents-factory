# Never-Do Patterns — Camel Quarkus Platform HTTP 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). High-confidence patterns only; items with lower confidence (such as `muteException=false`, or the global `quarkus.tls.protocols` question) are in [integration examples](./integration-examples.md#error-handling), [TLS and security](./tls-and-security.md#legacy-peers) and the [register](./unverified-and-risks.md).

## 1. Configuring platform-http HTTPS with SSLContextParameters (severity: high)

Not supported ([extension page](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html)). What happens at runtime is not documented; treat any resulting HTTP-only server as a likely outcome (unverified).

```java
// ❌ WRONG
getContext().setSSLContextParameters(scp); // expecting platform-http to serve HTTPS
```
```properties
# ✅ CORRECT (Quarkus 3.40: property per the HTTP reference; <name> is your registry entry)
quarkus.http.tls-configuration-name=<name>
# plus the quarkus.tls.<name>.* entry; see tls-and-security.md
```

## 2. Unrestricted upload endpoint (severity: high)

Without `httpMethodRestrict` every method is served, and without `fileNameExtWhitelist` any file type is accepted ([extension page](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html)).

```java
// ❌ WRONG
from("platform-http:/upload").to("file:target/in");
// ✅ CORRECT
from("platform-http:/upload?httpMethodRestrict=POST&fileNameExtWhitelist=pdf").to("file:target/in");
```

## 3. Leaving insecure-requests enabled when HTTPS is configured (severity: moderate)

The default `enabled` keeps plain HTTP served alongside HTTPS ([HTTP reference](https://quarkus.io/version/3.40/guides/http-reference)).

```properties
# ❌ WRONG
quarkus.http.tls-configuration-name=<name>
# ✅ CORRECT
quarkus.http.tls-configuration-name=<name>
quarkus.http.insecure-requests=redirect
```

## 4. @ApplicationScoped on a route with no injection (severity: low)

Needed only for `@Inject` or `@ConfigProperty`; it adds a boot-time penalty ([CDI guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html), verified by the orchestrator 2026-10-14).

```java
// ❌ WRONG (no injection used)
@ApplicationScoped
public class R extends RouteBuilder { public void configure() { from("platform-http:/a?httpMethodRestrict=GET").setBody(constant("ok")); } }
// ✅ CORRECT
public class R extends RouteBuilder { public void configure() { from("platform-http:/a?httpMethodRestrict=GET").setBody(constant("ok")); } }
```
