# Inventory: Camel Quarkus 3.40.x (Phase A, version inventory)

Checked on 2026-10-14. Only official sources were used. Where a page shows no date of its own, it is marked "(no page date, fetched 2026-10-14)".

## 1. Release, versions, LTS

- **Latest Camel Quarkus: 3.40.0**, released 2026-09-28 and marked LTS = Yes. Source: https://camel.apache.org/releases/ (fetched 2026-10-14).
- **Docs index (3.40.x):** Camel 4.22.1, Quarkus 3.40.1, GraalVM 25.0.4.1. The "LTS Until" column is blank. Source: https://camel.apache.org/camel-quarkus/latest/ (no page date).
- **Java:** the release note says "This version supports Java 17 and 21." Java 25 is not listed. Source: https://camel.apache.org/releases/q-3.40.0/ (no page date).
- **Maven Central:** camel-quarkus-junit 3.40.0 was published 2026-09-24 (https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-junit/).
- **LTS evidence for 3.40:**
  - camel.apache.org/releases marks 3.40.0 as LTS.
  - Quarkus 3.40 is LTS ("supported for 12 months"), announced 2026-09-30 at https://quarkus.io/blog/quarkus-3-40-released/. That post lists Camel Quarkus 3.40.0 in the platform.
  - No camel.apache.org blog announcement for 3.40.0 was found. The guessed URL /blog/2026/09/camel-quarkus-3.40.0/ returns 404.
- **3.33.0 LTS:** "We are pleased to announce the 3.33.0 LTS release of Apache Camel Quarkus" (Camel 4.18.0 LTS, Quarkus 3.33.0 LTS), 2026-03-25. Source: https://camel.apache.org/blog/2026/03/camel-quarkus-3.33.0/
- **Support policy:**
  - Quarkus states: "LTS releases are published every 6 months and maintained for 12 months with critical bug fixes and security patches." Quarkus 3.40 is maintained until 2027-09-30 and Quarkus 3.33 until 2027-03-25. Source: https://quarkus.io/releases (fetched 2026-10-14).
  - No Camel Quarkus–specific support policy or end date was found on camel.apache.org: UNVERIFIED. Assuming the same dates as the Quarkus LTS lines is an inference.
- **GraalVM/Mandrel:** the minimum is 25.0 from Quarkus 3.36 onward. JVM mode supports "JDKs from 17 to 25". Source: https://quarkus.io/blog/mandrel-25-minimum-version/ (2026-05-29).

## 2. Units

| Unit | artifactId | Status | Doc | Changes since 3.15 |
|---|---|---|---|---|
| core | camel-quarkus-core | exists, Stable | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/core.html | 3.40: `quarkus.camel.native.reflection.serialization-enabled` now has 3 states; `false` blocks registrations. TLS registry: quarkus.tls protocols/ciphers are enforced on Camel SSL contexts (default TLSv1.3 only, JSSE names only) |
| rest | camel-quarkus-rest | exists, Stable | .../extensions/rest.html | none in the guides |
| platform-http | camel-quarkus-platform-http | exists, Stable | .../extensions/platform-http.html | none in the guides (TLS registry change can affect HTTPS) |
| http | camel-quarkus-http | exists, Stable | .../extensions/http.html | none in the guides (TLS registry change can affect SSLContextParameters) |
| file | camel-quarkus-file | exists, Stable | .../extensions/file.html | none |
| jaxb | camel-quarkus-jaxb | exists, Stable | .../extensions/jaxb.html | none |
| xslt | camel-quarkus-xslt | exists, Stable | .../extensions/xslt.html | 3.40: external entities/DTDs are not resolved; `document()` is denied without a URIResolver; `quarkus.camel.xslt.features` also applies at runtime; the XSLT factory becomes the JAXP default |
| bean | camel-quarkus-bean | exists, Stable | .../extensions/bean.html | none |
| log | camel-quarkus-log | exists, Stable | .../extensions/log.html | none |
| junit5 | camel-quarkus-junit (renamed) | RENAMED in 3.31 | https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html | 3.31: renamed to camel-quarkus-junit; packages `org.apache.camel.test.junit5` -> `junit6`. 3.36: AdviceWith auto-starts routes, `adviceRoute()`, auto-cleanup. CONTRADICTION: the 3.31 guide says junit5 would be removed in 3.34, but camel-quarkus-junit5 3.40.0 is on Central (2026-09-24) |
| ArC | quarkus-arc | exists | https://quarkus.io/guides/cdi-reference | ArC = CDI 4.1. The artifactId is not stated on that page, but quarkus-arc 3.40.0/3.40.1 is on Central |
| Quarkus REST | quarkus-rest | exists | https://quarkus.io/guides/rest | Guide title: "Quarkus REST (formerly RESTEasy Reactive)" |
| Quarkus JUnit | quarkus-junit | exists (renamed from quarkus-junit5) | https://quarkus.io/guides/getting-started-testing | The guide uses quarkus-junit and links to the JUnit 6.1.2 docs. quarkus-junit5 3.40.1 is still on Central. The rename version is UNVERIFIED |

The extension list comes from https://camel.apache.org/camel-quarkus/3.40.x/reference/index.html (no page date).

Migration guides read:
- index: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/index.html
- per version: 3.17.0, 3.18.0, 3.23.0, 3.26.0, 3.27.0, 3.31.0, 3.33.0, 3.35.0, 3.36.0, 3.38.0, 3.39.0, 3.40.0 (each at `/3.40.x/migration-guide/<v>.html`). None of them has a page date.

The other guides touch only extensions outside the 13 units: AWS2, Kamelets+yaml-dsl, Jolokia, Hazelcast/OptaPlanner, LangChain4j, Groovy-xml, CXF WS-Security, CassandraQL, LDAP, JTA and Avro.

## 3. Quarkus 4

- 4.0.0.Beta1 was announced 2026-10-01. The final release is targeted for "end of November" (year implied 2026). Minimum Java is 21. Jackson 3 is included ("everything has changed except for the annotations"). Source: https://quarkus.io/blog/quarkus-4-0-0-beta1-released/
- quarkus-arc 4.0.0.Beta1 is on Central, dated 2026-09-30.
- Camel Quarkus on Quarkus 4: no release or date was found. UNVERIFIED.

## 4. Java baseline

- Camel Quarkus 3.40: Java 17 and 21 (https://camel.apache.org/releases/q-3.40.0/).
- Camel 4.22.0 is LTS and supports Java 17, 21 and 25 (https://camel.apache.org/releases/release-4.22.0/), so Java 17 is still supported.

## UNVERIFIED

- Camel Quarkus–specific LTS policy and end dates for 3.40 and 3.33.
- A camel.apache.org blog announcement for 3.40.0.
- Camel Quarkus on Quarkus 4 (existence or date).
- The Quarkus version that renamed quarkus-junit5 to quarkus-junit.
- Whether camel-quarkus-junit5 3.40.0 is a relocation POM or a deprecated alias.
- Java 25 support in Camel Quarkus 3.40.
