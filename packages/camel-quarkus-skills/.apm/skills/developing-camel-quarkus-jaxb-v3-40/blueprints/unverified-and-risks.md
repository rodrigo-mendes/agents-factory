# Unverified Register, Risks and Bibliography

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md).

Contents: [Counts](#counts) · [Version-lifetime risk](#version-lifetime-risk) · [Irresolvable items](#irresolvable-items-do-not-assert) · [Unverified items](#unverified-items) · [Medium-confidence items](#medium-confidence-items) · [Tag to register mapping](#tag-to-register-mapping) · [Source Bibliography](#source-bibliography)

## Counts

**13 unverified, 1 irresolvable, 12 medium-confidence** items are listed below (no coverage limits). Reconciliation with the research file: its metadata says 6 unverified and 3 irresolvable, but its body names more. This register uses the real list: 10 unverified items from the research body (U1-U10), plus 3 added by this skill (U11-U13). The Camel Quarkus-specific LTS end date is tagged `(unverified)` in the text, so it is U13 (not resolvable from documentation). The `prettyPrint` contradiction is the only irresolvable item (I1; tagged `(unverified)` in the text). "No Camel Quarkus build on Quarkus 4 is known" is filed once, as M9 (medium, absence of evidence, per the family facts).

## Version-lifetime risk

- Quarkus 4.0.0.Beta1 was published 2026-10-01; the final release is "planned for the end of November"; the highlights list Java 21 as the new base version ([blog](https://quarkus.io/blog/quarkus-4-0-0-beta1-released/)). It also ports Jackson to 3 ([release notes](https://github.com/quarkusio/quarkus/releases/tag/4.0.0.Beta1)). As of 2026-10-14 no Camel Quarkus build on Quarkus 4 is known (medium confidence, absence of evidence; the Beta1 post does not mention Camel Quarkus). Plan a migration with no known date.
- Assessment for this extension: `camel-quarkus-jaxb` has no Jackson dependency in its 3.40.0 POM (medium confidence, the research's reading of [Maven Central](https://central.sonatype.com/artifact/org.apache.camel.quarkus/camel-quarkus-jaxb/3.40.0)); the Jackson 3 move affects `camel-quarkus-jacksonxml`; the [Quarkus 4.0 migration guide](https://github.com/quarkusio/quarkus/wiki/Migration-Guide-4.0) (fetched 2026-10-14) lists no JAXB entries (medium confidence, absence of evidence; the wiki page is unversioned). Java 21 is a baseline bump and does not change the JAXB API itself (inference).
- Quarkus 3.40 was released 2026-09-30 as an LTS and is community-maintained until 2027-09-30 ([source](https://quarkus.io/releases)). The Camel Quarkus-specific end date is (unverified): the "LTS Until" column is blank on https://camel.apache.org/camel-quarkus/latest/, and applying the Quarkus date is an inference.
- Camel Quarkus 3.40.0 was released 2026-09-28 and is marked LTS ([releases](https://camel.apache.org/releases/)); it was less than a month old at the research date, so expect patch releases.

## Irresolvable items (do not assert)

| ID | Item | Impact | Workaround |
|---|---|---|---|
| I1 | `prettyPrint` default: options table says `true`, prose says "by default false" (tagged `(unverified)` in the text; not resolvable from documentation) | Output format differs from expectation | Set `prettyPrint` explicitly; check the field initialiser in `JaxbDataFormat` or the model class in camel-core-model 4.22.x |

## Unverified items

| ID | Item | Where it matters |
|---|---|---|
| U1 | JAXB-spec rule that a package `contextPath` needs an `ObjectFactory` or `jaxb.index` (`JAXBContext.newInstance(String)` contract not fetched) | contextPath choice |
| U2 | Name of the `JaxbDataFormat` setter that injects an external `JAXBContext` | Camel vs Quarkus context |
| U3 | Accepted values of `accessExternalSchemaProtocols` (`all`, `file`, `http` follow `XMLConstants` semantics) | Opening schema protocols |
| U4 | `xtokenize` (xml-jaxp / stax) working in native mode | Large XML in native |
| U5 | `XMLInputFactory` external-entity settings on unmarshal (come from Camel's StAX type converter) | Untrusted XML |
| U6 | Property name `quarkus.native.resources.includes` for including XSDs in a native image | Schema in native |
| U7 | `camel-quarkus-jacksonxml` options (the 4.22.x jacksonXml page URL returned 404) | JAXB vs jacksonxml |
| U8 | Jakarta XML Binding API version in the BOM | Version Context |
| U9 | Which Camel release added `accessExternalSchemaProtocols`, `contentTypeHeader`, `jaxbProviderProperties` | Migration |
| U10 | That each inline `.jaxb(...)` definition creates its own context (performance advice in the research body) | Named beans vs inline |
| U11 | (skill-added) ArC removal of an `@Identifier`-only bean (the Quarkus CDI reference does not say; `@Unremovable` is a suggestion). Camel lookup of `@Identifier` beans is High (Camel Quarkus CDI page) and is not part of this item | Bean name Ask First row |
| U12 | (skill-added, family fact) Release in which the deprecated `camel-quarkus-junit5` stub will be removed (3.40.0 still publishes it, High, see [Never Do 3](./never-do-patterns.md); the 3.31 guide said "until 3.34.0 is released"); prefer `camel-quarkus-junit` | Never Do row 3 |
| U13 | (skill-added, family fact) Camel Quarkus-specific support end date for 3.40: not resolvable from documentation (the "LTS Until" column is blank on https://camel.apache.org/camel-quarkus/latest/; applying the Quarkus date 2027-09-30 is an inference only) | Version Context, support planning |

## Medium-confidence items

| ID | Item |
|---|---|
| M1 | `camel-quarkus-support-jaxb` depends on `quarkus-jaxb` (search summary of the Central page) |
| M2 | Marshal/unmarshal failures surface as `IOException` (single source: 4.22.x source code) |
| M3 | Split with `xtokenize` + `streaming()` then JAXB unmarshal (Split EIP page; combination not an official example) |
| M4 | `file:`/`http:` schema or model resources not portable in native (only XSLT is documented) |
| M5 | Manually adding `com.sun.xml.bind` / a second JAXB runtime is harmful (POM exclusion, single source) |
| M6 | Integration-test-driven testing shape |
| M7 | `@RegisterForReflection` on already-annotated classes is redundant and harmless (inferred from Quarkus `JaxbProcessor` source code, not documented behaviour) |
| M8 | `camel-quarkus-jaxb` has no Jackson dependency (the research's reading of the 3.40.0 POM) |
| M9 | No Camel Quarkus build on Quarkus 4 is known (absence of evidence) |
| M10 | The 3.40.0 XSLT hardening also affects code that marshals JAXB to a `Source` and transforms it directly (the research's reading) |
| M11 | The Quarkus 4.0 migration guide lists no JAXB entries (absence of evidence; unversioned wiki page, so the claim cannot be pinned to a release) |
| M12 | Source-code readings whose URLs are branch heads, not tags (`blob/3.40`, `blob/3.40.x`, `blob/camel-4.22.x`): JAXBContext lifetime, `quarkus.jaxb.*` defaults, build-time class discovery, REST DSL binding, default schema security behaviour |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| "JAXB spec rule ... unverified" | SKILL.md Ask First (contextPath row); always-do-patterns.md; integration-examples.md | U1 |
| "setter name is unverified" | SKILL.md Ask First (Camel-built vs Quarkus context); evaluation-scenarios.md:38 (scenario 2) | U2 |
| "accepted values are unverified" | SKILL.md Ask First; schema-security.md; always-do-patterns.md; never-do-patterns.md:104 | U3 |
| "`xtokenize` in native unverified" | SKILL.md Ask First (Large XML); native-mode-and-contexts.md | U4 |
| "XMLInputFactory ... not verified" | schema-security.md | U5 |
| "include property name is unverified" | SKILL.md Ask First; never-do-patterns.md D; native-mode-and-contexts.md; schema-security.md | U6 |
| "jacksonxml options unverified" | SKILL.md Ask First; integration-examples.md; migration-guide.md; evaluation-scenarios.md:57 (scenario 3) | U7 |
| "Jakarta XML Binding API version unverified" | SKILL.md Version Context; migration-guide.md | U8 |
| "which Camel release added each option unverified" | migration-guide.md; evaluation-scenarios.md:39 (scenario 2) | U9 |
| "each inline definition creates its own context unverified" | always-do-patterns.md | U10 |
| "ArC removal of `@Identifier`-only bean unverified" | SKILL.md Ask First (Bean name) | U11 |
| "`camel-quarkus-junit5` stub removal release unverified" | never-do-patterns.md 3 | U12 |
| "Camel Quarkus-specific end date unverified" | SKILL.md Version-lifetime risk; evaluation-scenarios.md:42 (scenario 2) | U13 |
| "`prettyPrint` contradictory (unverified)" | SKILL.md Ask First and Quick Reference; evaluation-scenarios.md:37 (scenario 2) | I1 |
| "quarkus-jaxb via support-jaxb (medium confidence)" | SKILL.md Version Context; native-mode-and-contexts.md | M1 |
| "`IOException` (medium confidence)" | SKILL.md Ask First (Wrong-type bodies, Error handling); native-mode-and-contexts.md; never-do-patterns.md B | M2 |
| "Large XML (medium confidence)" | SKILL.md Ask First; native-mode-and-contexts.md | M3 |
| "`classpath:` only in native (medium confidence)" | SKILL.md Ask First; schema-security.md; never-do-patterns.md D | M4 |
| "second JAXB runtime (medium confidence)" | always-do-patterns.md; never-do-patterns.md A | M5 |
| "testing shape (medium confidence)" | integration-examples.md | M6 |
| "redundant @RegisterForReflection (medium confidence)" | never-do-patterns.md F; migration-guide.md; always-do-patterns.md:79; evaluation-scenarios.md:94 | M7 |
| "no Jackson dependency (medium confidence)" | SKILL.md Version-lifetime risk; migration-guide.md | M8 |
| "no Camel Quarkus build on Quarkus 4 (medium confidence)" | SKILL.md Version-lifetime risk; migration-guide.md; evaluation-scenarios.md | M9 |
| "XSLT hardening applies to JAXB-to-Source (medium confidence)" | migration-guide.md; schema-security.md (Related XSLT hardening) | M10 |
| "Quarkus 4.0 migration guide lists no JAXB entries (medium confidence, absence of evidence)" | SKILL.md Version-lifetime risk; migration-guide.md (Quarkus 4 outlook); this file (Version-lifetime risk) | M11 |
| "branch-head source code (medium confidence)" | SKILL.md Quick Reference (JAXBContext lifetime, `quarkus.jaxb.*`, build-time class discovery, REST DSL XML binding); native-mode-and-contexts.md (source-code reading); schema-security.md (Default security behaviour) | M12 |

## Source Bibliography

All fetched 2026-10-14. camel.apache.org pages have no page date and are the versioned 3.40.x / 4.22.x docs. No community sources were used. The research used tool summaries for some pages, so confirm exact wording on the live page before quoting.

Documentation pages:
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/jaxb.html
- https://camel.apache.org/components/4.22.x/dataformats/jaxb-dataformat.html
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html
- https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html
- https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/jacksonxml.html
- https://camel.apache.org/components/4.22.x/eips/split-eip.html
- https://camel.apache.org/camel-quarkus/latest/
- https://camel.apache.org/releases/ and https://camel.apache.org/releases/q-3.40.0/
- https://quarkus.io/releases ; https://quarkus.io/version/3.40/guides/cdi-reference
- https://quarkus.io/blog/quarkus-4-0-0-beta1-released/ ; https://github.com/quarkusio/quarkus/releases/tag/4.0.0.Beta1 ; https://github.com/quarkusio/quarkus/wiki/Migration-Guide-4.0

Registry pages:
- https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-junit5/3.40.0/camel-quarkus-junit5-3.40.0.pom (fetched 2026-10-14 by the orchestrator)
- https://central.sonatype.com/artifact/org.apache.camel.quarkus/camel-quarkus-jaxb/3.40.0
- https://central.sonatype.com/artifact/org.apache.camel.quarkus/camel-quarkus-support-jaxb/3.40.0/jar

Source code (branch heads, not tags; not documentation pages; medium confidence, M12):
- https://github.com/apache/camel/blob/camel-4.22.x/components/camel-jaxb/src/main/java/org/apache/camel/converter/jaxb/JaxbDataFormat.java
- https://github.com/apache/camel-quarkus/blob/3.40.x/extensions/jaxb/deployment/src/main/java/org/apache/camel/quarkus/component/jaxb/deployment/JaxbProcessor.java
- https://github.com/apache/camel-quarkus/blob/3.40.x/extensions/jaxb/runtime/src/main/java/org/apache/camel/quarkus/component/jaxb/JaxbRecorder.java
- https://github.com/apache/camel-quarkus/blob/3.40.x/extensions-support/jaxb/deployment/src/main/java/org/apache/camel/quarkus/support/jaxb/deployment/JaxbProcessor.java
- https://github.com/apache/camel-quarkus/blob/3.40.x/integration-tests/jaxb/src/main/java/org/apache/camel/quarkus/component/jaxb/it/JaxbProducers.java
- https://github.com/apache/camel-quarkus/blob/3.40.x/integration-tests/jaxb/src/main/java/org/apache/camel/quarkus/component/jaxb/it/JaxbRoute.java
- https://github.com/quarkusio/quarkus/blob/3.40/extensions/jaxb/deployment/src/main/java/io/quarkus/jaxb/deployment/JaxbProcessor.java
- https://github.com/quarkusio/quarkus/blob/3.40/extensions/jaxb/runtime/src/main/java/io/quarkus/jaxb/runtime/JaxbConfig.java
- https://github.com/quarkusio/quarkus/blob/3.40/extensions/jaxb/runtime/src/main/java/io/quarkus/jaxb/runtime/JaxbContextProducer.java

Not usable (404 at research time): https://quarkus.io/guides/jaxb, https://quarkus.io/guides/xml, https://camel.apache.org/components/4.22.x/dataformats/jacksonXml-dataformat.html
