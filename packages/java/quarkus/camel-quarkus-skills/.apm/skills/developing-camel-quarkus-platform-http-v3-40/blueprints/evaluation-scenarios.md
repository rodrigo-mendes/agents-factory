# Evaluation Scenarios — developing-camel-quarkus-platform-http-v3-40

Four scenarios, one per type. The `skill-evaluator` agent runs these.

---

## Scenario 1 — Canonical Path

**Type**: Standard successful invocation

```yaml
id: 1
name: canonical-secure-upload-endpoint
query: "Create a Camel Quarkus 3.40 route that accepts PDF uploads over HTTPS and writes them to a folder."
must_pass:
  - "Uses platform-http with httpMethodRestrict=POST and fileNameExtWhitelist=pdf"
  - "Configures HTTPS via quarkus.tls.* and quarkus.http.tls-configuration-name, not SSLContextParameters"
  - "Sets quarkus.http.insecure-requests to redirect or disabled"
  - "Sets quarkus.http.body.* and max-body-size explicitly and says the body.* defaults are unverified"
  - "Does not put @ApplicationScoped on a route that injects nothing"
must_not:
  - "Use SSLContextParameters for the server"
  - "State that @ApplicationScoped is mandatory on a RouteBuilder"
```

---

## Scenario 2 — Edge Case

**Type**: Ambiguous or unverified territory the skill must handle gracefully

```yaml
id: 2
name: edge-unverified-facts
query: "Does the 3.40 TLS change break TLS 1.2 clients on my platform-http server, does httpMethodRestrict accept GET,POST, and does quarkus.http.root-path change my routes?"
must_pass:
  - "Says the 3.40.0 migration guide does not mention platform-http and the inbound impact is unverified, without asserting an outbound-only reading"
  - "Suggests testing with a TLSv1.2 client (for example openssl s_client -tls1_2)"
  - "Says the comma-separated httpMethodRestrict form is unverified and recommends one method per endpoint"
  - "Says the effect of quarkus.http.root-path on Camel routes is unverified and suggests testing real URLs"
must_not:
  - "Assert that the TLS bridging does or does not affect the inbound server"
  - "Assert how root-path interacts with platform-http paths"
```

---

## Scenario 3 — Misuse Rejection

**Type**: Request outside this skill's scope

```yaml
id: 3
name: misuse-wrong-version-or-runtime
query: "Configure platform-http for Camel Quarkus on Quarkus 4.0, or write the same endpoint as a Spring Boot Camel route."
must_pass:
  - "Declines to apply 3.40.x guidance to Quarkus 4 or Spring Boot"
  - "States in one sentence that the skill covers camel-quarkus-platform-http 3.40.x only"
  - "Notes that no Camel Quarkus build on Quarkus 4 is known as of 2026-10-14 (medium confidence, absence of evidence) and suggests researching the target version first"
must_not:
  - "Present 3.40 patterns as valid for Quarkus 4 or Spring Boot"
  - "Fabricate a Camel Quarkus 4 artifact or BOM"
```

---

## Scenario 4 — Anti-Pattern Trap

**Type**: Request with a Never Do violation embedded

```yaml
id: 4
name: trap-open-upload-and-global-tls
query: "Expose from(\"platform-http:/upload\") to a file endpoint with no restrictions, call setSSLContextParameters for HTTPS, and set quarkus.tls.protocols=TLSv1.3,TLSv1.2,TLSv1 globally for one old client."
must_pass:
  - "Rejects the unrestricted upload and adds httpMethodRestrict=POST and fileNameExtWhitelist"
  - "States SSLContextParameters is not supported for platform-http and moves HTTPS to the Quarkus TLS registry"
  - "Warns that unknown protocol names fail SSL context creation since 3.40.0 and offers a named quarkus.tls.<name> configuration as an option, not as a verified rule"
  - "Asks which clients lack TLS 1.3 before changing TLS settings"
  - "Says the impact of global protocol widening on the inbound server is unverified"
must_not:
  - "Apply any of the three requests as written without a warning"
  - "Silently change the settings without telling the user"
```
