# Unverified Register, Risks and Bibliography

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). The research file reports a quality score of 87%, a deep run that used all 3 iterations, and 3 irresolvable items (here U1-U3, filed under unverified because the text tag is (unverified)). This register lists 18 unverified items (U1-U18), 0 other irresolvable items, 8 medium-confidence items (M1-M8) and 1 coverage limit (L1).

## Version-lifetime risk

- Quarkus 4.0.0.Beta1 was published 2026-10-01; the final release is "planned for the end of November" and the highlights list Java 21 as the new base version (https://quarkus.io/blog/quarkus-4-0-0-beta1-released/, high). Whether Quarkus 4 brings Jackson 3 was not verified for this skill (unverified, U15).
- As of 2026-10-14 no Camel Quarkus build on Quarkus 4 is known; the Beta1 post does not mention Camel Quarkus (medium confidence, absence of evidence, M8). Plan a migration with no known date and do not assume Quarkus 4 compatibility.
- Quarkus 3.40 was released 2026-09-30 as an LTS and is community-maintained until 2027-09-30 (https://quarkus.io/releases, high).
- The Camel Quarkus-specific support end date for 3.40 is not published (unverified, U4; not resolvable from documentation): the "LTS Until" column is blank on https://camel.apache.org/camel-quarkus/latest/. Applying the Quarkus date to Camel Quarkus is an inference.
- Camel Quarkus 3.40.0 was released 2026-09-28 (https://camel.apache.org/releases/). Patch releases are expected and docs may still change.

## Unverified items (do not assert)

| ID | Item | Impact | Workaround |
|---|---|---|---|
| U1 | `xslt-saxon` behaviour under the 3.40 hardening (entities, `document()`, JAXP default); the migration guide is silent; not resolvable from documentation | Saxon users may assume protections that apply only to Xalan | Treat Saxon as unhardened; keep `secureProcessing=true`; custom `URIResolver`; check the 3.40.0 release notes or extension source |
| U2 | Which `quarkus.camel.xslt.*` properties are build-time (the tool did not render the markers; not resolvable from documentation, and the skill does not assert a build-time split) | Changing `sources`/`features` at runtime may have no effect | Treat all as build-time and rebuild; open the extension page in a browser |
| U3 | Camel 4.22.x `ACCESS_EXTERNAL_*` security section absent from the component page rendering; not resolvable from documentation | Unclear Camel-side defaults on JVM with a non-Camel-Quarkus factory | Rely on the restrictions the extension enforces; check the Camel 4.22 upgrade guide |
| U4 | Camel Quarkus-specific LTS end date for 3.40; not resolvable from documentation | Support planning | Quarkus 3.40 date as an inference only |
| U5 | Exact Xalan-J patch version, the "XSLT 1.0 engine" claim, and "Xalan-J 2.7.x predates JAXP 1.5" | Feature expectations | Test stylesheets; do not rely on version numbers |
| U6 | Whether the unescaped `"http://..."` features key parses correctly | Feature may silently not apply | Use the escaped form shown on the extension page |
| U7 | JAXB integration details for 3.40 | Marshalling before `xslt:` | Test; see the jaxb skill |
| U8 | `bean:` / `ref:` template URIs in native mode | Native build failures | Prefer `classpath:` |
| U9 | `output=file` in a native executable | Large-output routes | Test in native |
| U10 | XSLT-specific changes in the migration baseline range other than the 3.40.0 guide | Missed breaking changes | Read the intermediate migration guides |
| U11 | Exception type that wraps a failed transformation (`TransformerException` assumed) | `onException` matching | Log the real type in a test |
| U12 | An XSLT example in the examples repository; the `integration-tests/xslt` path | No reference project | Build from this skill's samples |
| U13 | The extension page's native limitation spelled `xsl:messaging` (feature name not re-checked) | Native `xsl:message` use | Test in native |
| U14 | Property spelling `camel.component.xslt.allow-template-from-header` for 3.40 | Config typo | Use the endpoint option `allowTemplateFromHeader` per the component page |
| U15 | Whether Quarkus 4 brings Jackson 3 (not verified for this skill) | Version-lifetime planning | Do not assume; check the Quarkus 4 release notes |
| U16 | Log output of the representative `./mvnw` commands (expected results are illustrative) | Wrong expectations in CI | Run and read the real output |
| U17 | Native behaviour of the Xalan extension functions beyond the three documented preconditions | Native build or runtime failures | Test in native |
| U18 | Inference that the `.xsl` files need not be in the application archive once they are listed in `sources` | Missing stylesheet at runtime if the inference is wrong | Keep the `.xsl` files on the classpath |

## Medium-confidence items

| ID | Item |
|---|---|
| M1 | Header stripping before `xslt:` (the untrusted-sender warning is only on the 4.23 docs page) |
| M2 | Choosing Saxon vs Xalan, and the Saxon option defaults (`useJsonBody`, `allowStAX`, `secureProcessing`, `saxonExtensionFunctions`) |
| M3 | Extension-function setup conditions other than secure processing (a separate jar, reflection registration). That disabling secure processing permits Xalan extension functions is High everywhere (versioned 3.40.0 migration guide). Evidence-rule reason: High needs a versioned page read by the researcher, and these two conditions are not quoted from one in the research; the page-level coverage limit is recorded separately in L1 |
| M4 | Native behaviour of runtime-loaded dynamic templates |
| M5 | `document()` access options (custom `uriResolver`) |
| M6 | Saxon JVM/native-since versions from the unversioned `latest` alias page |
| M7 | No XSLT-specific testing guidance exists on the extension page |
| M8 | No Camel Quarkus build on Quarkus 4 is known (absence of evidence) |

## Coverage limits

| ID | Item |
|---|---|
| L1 | The fetch tool returned page summaries, not full text: the hardening claims in `security-hardening-3-40.md` and the Always/Never Do claims that cite the extension page and the 3.40.0 migration guide rest on summarised page text. Confirm exact wording on the live pages before quoting. |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (medium confidence, `latest` alias) | SKILL.md Version Context, Saxon row; native-mode.md | M6 |
| Xalan-J patch version (unverified) | SKILL.md Version Context, `camel-quarkus-xslt` row (the engine itself is not tagged) | U5 |
| (unverified) Saxon coverage | SKILL.md Version Context and Ask First (Xalan vs Saxon) | U1 |
| (medium confidence, absence of evidence) | SKILL.md Version-lifetime risk; evaluation-scenarios.md | M8 |
| (unverified) Camel Quarkus end date, not resolvable from documentation | SKILL.md Version-lifetime risk | U4 |
| (unverified) Jackson 3 on Quarkus 4 | SKILL.md Version-lifetime risk; this register | U15 |
| (unverified) Build-time property split | SKILL.md Ask First and Quick Reference; always-do-patterns.md; native-mode.md | U2 |
| (unverified) inference that `.xsl` files need not be in the archive | always-do-patterns.md section 1 | U18 |
| (medium confidence) Header hygiene | SKILL.md Ask First; security-hardening-3-40.md; integration-examples.md; never-do-patterns.md item 5 | M1 |
| (medium confidence) Xalan vs Saxon | SKILL.md Ask First | M2 |
| (medium confidence) Saxon defaults and Saxon error properties | SKILL.md Quick Reference; integration-examples.md (error properties) | M2 |
| (medium confidence) extension-function setup conditions other than secure processing (separate jar, reflection registration) | SKILL.md Ask First; extension-functions.md | M3 |
| (unverified) no XSLT example located in the examples repository | integration-examples.md | U12 |
| (no tag in text) property spelling `camel.component.xslt.allow-template-from-header`; the skill states only the endpoint option `allowTemplateFromHeader` | SKILL.md Ask First (dynamic templates row) | U14 |
| (medium confidence) dynamic templates, native behaviour | SKILL.md Ask First | M4 |
| (medium confidence) `document()` access | SKILL.md Ask First | M5 |
| (unverified) native file output | SKILL.md Ask First; integration-examples.md | U9 |
| (unverified) `bean:` / `ref:` template URIs in native | SKILL.md Ask First; integration-examples.md; native-mode.md | U8 |
| (unverified) `xsl:messaging` feature name | native-mode.md | U13 |
| (log output: unverified) | SKILL.md Quick Reference, representative commands | U16 |
| (unverified) Xalan-J 2.7.x predates JAXP 1.5 | never-do-patterns.md item 3 | U5 |
| (unverified) unescaped features key | never-do-patterns.md item 6 (heading and text) | U6 |
| (unverified) native behaviour of extension functions | extension-functions.md | U17 |
| (medium confidence) no XSLT-specific testing guidance | native-mode.md; integration-examples.md | M7 |
| (unverified) JAXB integration | integration-examples.md | U7 |
| (unverified) exception type of a failed transformation | integration-examples.md | U11 |
| (unverified) Saxon coverage; other XSLT changes 3.15 to 3.40 | migration-guide.md | U1; U10 |
| (unverified) Xalan-J patch version | migration-guide.md | U5 |
| (unverified) `ACCESS_EXTERNAL_*` defaults | security-hardening-3-40.md | U3 |
| (medium confidence) Saxon `saxonExtensionFunctions` | extension-functions.md | M2 |

## Source Bibliography

All fetched 2026-10-14. camel.apache.org pages have no page date and are the current stable 3.40.x / 4.22.x docs. The fetch tool returned summaries (see L1). No community sources were used.

- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html
- https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/cdi.html (via the family facts)
- https://camel.apache.org/releases/q-3.40.0/ (Java 17 and 21)
- https://camel.apache.org/camel-quarkus/latest/ (platform versions; blank "LTS Until")
- https://camel.apache.org/camel-quarkus/latest/reference/extensions/xslt-saxon.html (`latest` alias)
- https://camel.apache.org/components/4.22.x/xslt-component.html
- https://camel.apache.org/components/4.22.x/xslt-saxon-component.html
- https://camel.apache.org/releases/ (Camel Quarkus 3.40.0 LTS 2026-09-28)
- https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-xslt/ (3.40.0, 2026-09-24)
- https://quarkus.io/releases ; https://quarkus.io/blog/quarkus-4-0-0-beta1-released/
- Contrast only, not the target version: https://camel.apache.org/components/next/xslt-component.html (Camel 4.23)
- https://github.com/apache/camel-quarkus-examples (no XSLT example located)
