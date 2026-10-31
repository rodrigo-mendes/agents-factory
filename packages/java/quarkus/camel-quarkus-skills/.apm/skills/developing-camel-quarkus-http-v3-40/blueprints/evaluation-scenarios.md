# Evaluation Scenarios — developing-camel-quarkus-http-v3-40

Five scenarios: canonical, edge, misuse, anti-pattern trap and Ask First decision. The `skill-evaluator` agent runs these.

---

## Scenario 1 — Canonical Path

**Type**: Standard successful invocation

```yaml
id: 1
name: canonical-https-call-with-tls-and-breaker
query: "In a Camel Quarkus 3.40 app, call https://partner.example.com/api from a route with our own truststore, a circuit breaker and a fallback."
must_pass:
  - "Uses camel-quarkus-http plus camel-quarkus-tls-registry and a named quarkus.tls.<name> bucket referenced as sslContextParameters=#<name>"
  - "Uses camel-quarkus-microprofile-fault-tolerance for circuitBreaker() with onFallback"
  - "Handles HttpOperationFailedException and notes its Java package is unverified (resolve with the IDE)"
  - "Uses a plain RouteBuilder without @ApplicationScoped because no injection is needed"
  - "Notes that bridged endpoints offer TLSv1.3 only by default"
must_not:
  - "Add camel-quarkus-resilience4j"
  - "State that @ApplicationScoped is mandatory on a RouteBuilder"
  - "Set quarkus.ssl.native=true as a requirement"
```

---

## Scenario 2 — Edge Case

**Type**: Ambiguous or unverified territory the skill must handle gracefully

```yaml
id: 2
name: edge-unverified-defaults-and-status-range
query: "What are the faultToleranceConfiguration defaults, which HttpClient 5 version will I get, and is a 150 status a success?"
must_pass:
  - "States the faultToleranceConfiguration defaults are unverified and recommends setting every option explicitly and testing the timeout path"
  - "States the Quarkus-resolved HttpClient 5 version is unverified (parent POM pins 5.6.3) and suggests dependency:tree"
  - "Reports the documented contradiction (prose 100..299 vs okStatusCodeRange default 200-299) and recommends setting the range explicitly"
must_not:
  - "Assert fault-tolerance defaults or an HttpClient version as fact"
  - "Pick one status range as definitive"
```

---

## Scenario 3 — Misuse Rejection

**Type**: Request outside this skill's scope

```yaml
id: 3
name: misuse-server-side-or-quarkus-4
query: "Expose an HTTP endpoint with camel-quarkus-http as a server, or set this up on Quarkus 4.0 Beta."
must_pass:
  - "States in one sentence that the skill covers the camel-quarkus-http client/producer on 3.40.x only, not platform-http (server) or Quarkus 4"
  - "Notes that no Camel Quarkus build on Quarkus 4 is known as of 2026-10-14 (medium confidence, absence of evidence), and suggests researching the target first"
must_not:
  - "Present producer-only guidance as a server setup"
  - "Fabricate a Camel Quarkus 4 artifact or BOM"
```

---

## Scenario 4 — Anti-Pattern Trap

**Type**: Request with a Never Do violation embedded

```yaml
id: 4
name: trap-openssl-ciphers-and-revocation
query: "Set quarkus.tls.cipher-suites=ECDHE-RSA-AES128-GCM-SHA256 and quarkus.tls.partner.certificate-revocation-list so Camel checks revoked certs, and add camel-quarkus-resilience4j."
must_pass:
  - "Rejects OpenSSL-style cipher names: since 3.40.0 unknown names fail SSL context creation; proposes JSSE names (TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256)"
  - "Explains certificate-revocation-list is not bridged to Camel (with hostname-verification-algorithm, key-store.sni, alpn, pqc-enforcement-policy) and revocation must be handled outside the bridge"
  - "States camel-quarkus-resilience4j is not listed in the 3.40.x extension index and recommends camel-quarkus-microprofile-fault-tolerance"
must_not:
  - "Apply the settings as requested without warning"
  - "Claim the bridge checks revocation"
```

---

## Scenario 5 — Ask First Decision (legacy TLS and proxy)

**Type**: Request with an Ask First decision embedded

```yaml
id: 5
name: trap-global-tls-widening-and-proxy-headers
query: "One partner only speaks TLS 1.2, so set quarkus.tls.protocols=TLSv1.3,TLSv1.2 globally. Also forward platform-http:/proxy straight to https://backend.example.com."
must_pass:
  - "Asks which endpoints lack TLS 1.3 and recommends a named bucket quarkus.tls.<name>.protocols over global widening"
  - "Flags that inbound CamelHttp* headers can leak into the producer and suggests bridgeEndpoint=true&skipControlHeaders=true, tagged medium confidence"
must_not:
  - "Widen TLS globally without asking"
  - "Present the proxy-header advice as high confidence"
```
