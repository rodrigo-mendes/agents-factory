# Best Practices Analysis: developing-camel-quarkus-file-v3-40

**Date**: 2026-10-14
**File**: `packages/camel-quarkus-skills/.apm/skills/developing-camel-quarkus-file-v3-40/SKILL.md`
**Lines**: 114 (confirmed; hybrid target 100-200, hard limit 500)
**Judged against**: `.claude/rules/skill-structure.md` ("Hybrid knowledge skills") and `TEMPLATE.KNOWLEDGE-SKILL.HYBRID.md`
**Scope of check**: presence and consistency only. No URL was re-fetched.
**Score**: **86/100** (rubric: start at 100; HIGH -4, MEDIUM -1.5, LOW -0.5)

---

## Summary

- Official criteria met: 8/8 (B is N/A)
- Team conventions met: 6/7 (D5 partial)
- HIGH: 1, MEDIUM: 5, LOW: 5

All five Always Do bullets are High and sourced. Medium items are well tagged in Ask First (atomic writes, idempotency, large files, dynamic paths, jail, cluster defaults) and mirrored in the register. The single HIGH is a Never Do row whose evidence the register itself calls medium.

## Official Criteria

| Criterion | Status | Notes |
|---|---|---|
| A1 Frontmatter | ✅ | name = folder; `Use when`; under 1536 (regex check) |
| A2 Conciseness | ✅ | 114 lines |
| A3 Progressive disclosure | ✅ | 10 blueprint links, all files exist; anchors checked resolve |
| A4 Content | ✅ | |
| A5 Workflows | ✅ | N/A |
| A6 Paths | ✅ | |
| B Scripts | N/A | |
| C Evaluation | ✅ | 4 scenarios. Not executed |

## Team Conventions

| Criterion | Status | Notes |
|---|---|---|
| D1 | ✅ | |
| D2 | ✅ | Always Do has no medium content |
| D3 | ✅ | |
| D4 | ✅ | `mvn test`, `mvn verify -Dnative`, log output flagged unverified |
| D5 | ⚠️ | Never Do rows 2 and 6 (H1, M1) |
| D6 | ✅ | |
| D7 | ✅ | |

## Hybrid-format checks requested

| Check | Result |
|---|---|
| Flat claims have source or tag | ⚠️ M3, M4 |
| Version Context / Quick Reference rows sourced | ✅ all rows (`page not recorded` on :100) |
| Always/Never only High per the register | 🚫 H1; ⚠️ M1 |
| `@ApplicationScoped` never "mandatory" | ✅ not asserted; plain RouteBuilder in all code. But eval scenarios lack a `must_not` (L5) |
| Every medium/unverified item in the register | ✅ (L2 wording only) |
| SKILL.md not stronger than blueprints | ⚠️ M2 (provenance), otherwise consistent |

---

## Recommendations by Priority

### HIGH

**H1. Never Do row 6 (forceWrites / boolean preSort) rests on a page the register calls partly read and medium** (SKILL.md:77; register:28, :35; migration-guide.md:18; never-do-patterns.md:84-95)
- Register:28 says "Parts of the 4.21 and 4.22 upgrade guides were only partly read; entries from them are medium confidence". migration-guide.md:18 marks the same 4.22 entries "partly read" yet "high (preSort, forceWrites)". Register:35 (the medium list) names 4.21 but not 4.22. The three places disagree.
- never-do-patterns.md:92 puts `eagerMaxMessagesPerPoll=true` in the ✅ example while register:17 and migration-guide.md:14 say its name is unverified.
- Fix: either (a) state in the register that the specific forceWrites/preSort entries were read in full and fix register:28, or (b) tag the row medium and move it to Ask First. In both cases remove `eagerMaxMessagesPerPoll` from the ✅ example (use `preSort=modified` alone).

### MEDIUM

- **M1. Never Do row 2 ✅ column leans on medium material** (SKILL.md:73; never-do-patterns.md:22, :28) The alternative `idempotent-changed` + shared `idempotentRepository` is the medium "Idempotency (single page)" pattern (SKILL.md:58) or the cluster singleton (:61, medium defaults). Tag it. The blueprint also adds "files can be processed twice" beyond the page quote ("should be avoided"); label it an inference.
- **M2. Quarkus 4 GA claim provenance** (SKILL.md:24; register:7) SKILL.md states it High with a link, but register:7 says "per the core research". Sibling skills tag the same fact medium ("carried, not re-fetched"). If it was carried, add the medium tag in both files; if fetched, delete "per the core research".
- **M3. Polling vs events row is untagged and unsourced** (SKILL.md:62; file-watch-and-cluster.md:28-31) "file-watch: ... no move/readLock lifecycle" is an inference from absent options. Add a source (file-watch component page) or tag medium and register it.
- **M4. Never Do row 7 has no source or tag** (SKILL.md:78) Same boilerplate as platform-http row 6. Cite the version-lifetime register or delete.
- **M5. Unverified option name used as workaround** (migration-guide.md:33, file-consumer-producer.md:83, register:17) "Set `eagerMaxMessagesPerPoll` explicitly" is advice built on a name the register says is unverified. Reword as "check the real option name in the 4.13 upgrade guide".

### LOW

- **L1** (register:3, :19-31) "9 unverified" in the header vs 11 listed plus 3 irresolvable; reconcile.
- **L2** (register:29 vs remote-ftp-sftp.md:29) Register says "20000 per the File page"; the blueprint says "the File page says the FTP default is 20000". Clarify that the file consumer default (10000, Quick Reference :87) is not in conflict.
- **L3** (SKILL.md:100, integration-examples.md:68-75) `mvn` vs `./mvnw` used elsewhere in the family; pick one.
- **L4** (never-do-patterns.md:109) severity string "high, medium confidence" for item 8 and "inferred" labels are good; add the same marker to the item 2 sentence in M1.
- **L5** (evaluation-scenarios.md:19-24) Scenario 1 has `must_pass` for plain RouteBuilder but no `must_not` for "states `@ApplicationScoped` is mandatory", unlike platform-http, http and rest.

## Conclusions

Cleanest Always Do tier of the four. Resolving H1 and M1-M4 would put it near 94.
