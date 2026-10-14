# Best Practices Analysis: developing-camel-quarkus-rest-v3-40

**Date**: 2026-10-14
**File**: `packages/camel-quarkus-skills/.apm/skills/developing-camel-quarkus-rest-v3-40/SKILL.md`
**Lines**: 107 (confirmed; hybrid target 100-200, hard limit 500)
**Judged against**: `.claude/rules/skill-structure.md` ("Hybrid knowledge skills") and `TEMPLATE.KNOWLEDGE-SKILL.HYBRID.md`
**Scope of check**: presence and consistency only. No URL was re-fetched.
**Score**: **81/100** (rubric: start at 100; HIGH -4, MEDIUM -1.5, LOW -0.5)

---

## Summary

- Official criteria met: 8/8 (B is N/A)
- Team conventions met: 6/7 (D2 partial)
- HIGH: 2, MEDIUM: 6, LOW: 4

Strongest Ask First table (medium tags on nearly every row) but the most "versionless page" exposure: REST DSL manual pages and unpinned `quarkus.io/guides/...` URLs feed Always Do and Never Do. This is exactly the failure class of the core pilot.

## Official Criteria

| Criterion | Status | Notes |
|---|---|---|
| A1 Frontmatter | ✅ | name = folder; `Use when`; under 1536 (regex check) |
| A2 Conciseness | ✅ | 107 lines |
| A3 Progressive disclosure | ✅ | 11 blueprint links, all files exist; anchors checked resolve |
| A4 Content | ✅ | |
| A5 Workflows | ✅ | N/A |
| A6 Paths | ✅ | |
| B Scripts | N/A | |
| C Evaluation | ✅ | 4 scenarios. Not executed |

## Team Conventions

| Criterion | Status | Notes |
|---|---|---|
| D1 | ✅ | |
| D2 | ⚠️ | H1, H2 |
| D3 | ✅ | rows tagged medium where uncertain |
| D4 | ✅ | |
| D5 | ✅ | |
| D6 | ✅ | |
| D7 | ✅ | |

## Hybrid-format checks requested

| Check | Result |
|---|---|
| Flat claims have source or tag | ⚠️ M1 (servlet row), M5 |
| Version Context / Quick Reference rows sourced | ✅ all rows; :95 "none (representative)" |
| Always/Never only High per the register | 🚫 H1, H2 |
| `@ApplicationScoped` never "mandatory" | ✅ SKILL.md:75 "needed only for `@Inject`/`@ConfigProperty`"; eval scenario 1 `must_not` at :19 |
| Every medium/unverified item in the register | ⚠️ M6 |
| SKILL.md not stronger than blueprints | 🚫 H1; blueprint stronger than register in M3 |

---

## Recommendations by Priority

### HIGH

**H1. Always Do #4 states a default the skill tags medium everywhere else** (SKILL.md:49 vs :87; always-do-patterns.md:65; register:50)
- :49 says "`missingOperation` defaults to `fail`" with no tag. Quick Reference :87 tags it medium ("page shows no version"); always-do-patterns.md:65 says "the `missingOperation` pin is medium"; register:50 lists "`missingOperation` defaults (versionless page)".
- Fix: Always Do keeps only the manual-backed claim (a missing `direct:<operationId>` fails startup, OpenAPI manual), and drops the default clause; the default stays in Quick Reference with its tag.

**H2. CORS default is High in Never Do, medium in Ask First and the register** (SKILL.md:72 vs :59, :88; never-do-patterns.md:23; validation-and-cors.md:33; register:50)
- Never Do row 2 treats "`enableCORS(true)` default origin `*`" as a High prohibition. Ask First :59 tags the same default medium ("as tagged in the research"); register:50 lists "CORS comparison" as medium; never-do-patterns.md:23 resolves it by saying "the prohibition is tagged high" without recording why; Quick Reference :88 has no tag.
- Fix: pick one. If the binding manual (an unversioned page, see M4) is accepted as High for this default, remove the medium tag from :59 and register:50 and say why. If not, move row 2 to Ask First. The ✅ (`quarkus.http.cors.*` with explicit origins) is fine either way.

### MEDIUM

- **M1. Ask First "Alternate transport" has no source, no tag, and no register entry** (SKILL.md:63) `camel-quarkus-servlet` + `component("servlet")` appears only here (grep confirmed: nothing in blueprints or register). Add a source and a tag, or delete.
- **M2. Unpinned Quarkus pages feed Always/Never and Quick Reference** (SKILL.md:71-72, :89-90, :93, :106) `https://quarkus.io/guides/http-reference`, `.../security-cors`, `.../getting-started-testing` are "latest", not `quarkus.io/version/3.40/guides/...`. Only :93 is tagged. Re-point to the 3.40 pages (the platform-http skill uses them) or tag every such row medium.
- **M3. Blueprint asserts a runtime effect the register says not to assert** (never-do-patterns.md:7; register:25; platform-http register:40) "The effect is that TLS is silently not applied" is stated as fact in the same paragraph that calls the port behaviour unverified; the sibling register lists the runtime result of `SSLContextParameters` on platform-http as unverified. SKILL.md:71 is correctly silent. Remove "silently ... not applied" or tag it.
- **M4. Unversioned manual pages behind High claims** (SKILL.md:21, :48, :83-84; always-do-patterns.md:42) Version Context says the REST DSL manual is unversioned and medium "where version-sensitive", yet Always Do #3 and Quick Reference rows (`inlineRoutes` since 4.5, response codes, `skipBindingOnErrorCode`) cite it untagged. List which defaults are treated as not version-sensitive and why, or tag them.
- **M5. TLS protocol default implied for the REST server** (validation-and-cors.md:50; migration-guide.md:9) "`quarkus.tls.protocols` default `TLSv1.3` since Camel Quarkus 3.40.0" appears in a REST server security checklist without the caveat that the bridging change is only confirmed for Camel clients (platform-http tls-and-security.md:34 treats the inbound effect as unverified). Add the caveat or remove it from the checklist.
- **M6. Register gap** (SKILL.md:21, :18) "REST DSL manual pages unversioned (treated as 4.22.x)" and "Quarkus platform 3.40.1 pinned by the `main`-branch example pom" are tagged or implied medium but are not in register:50. Add both. (The file skill already flags `main`-branch examples as "not the 3.40.x tag".)

### LOW

- **L1** (rest-dsl-configuration.md:81 vs platform-http SKILL.md:49) Authenticated-user header is medium here and High in the platform-http skill.
- **L2** (SKILL.md:93 vs platform-http SKILL.md:96) Test port 8081 is medium here and unverified there.
- **L3** (never-do-patterns.md:39) "The route does not match" goes beyond "Vert.x rejects"; soften.
- **L4** (SKILL.md:95) "none (representative)"; use "page not recorded".

## Conclusions

Good coverage and honest Ask First. Fix H1 and H2 (two bullets) and re-point the Quarkus URLs (M2); expected score about 90.
