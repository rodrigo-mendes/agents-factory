# Validation: developing-camel-quarkus-core-v3-40

Date: 2026-10-14. Validator: quality-validator (skill-best-practices-validator rubric A1-A6, B, C, D1-D7).
Target: packages/camel-quarkus-skills/.apm/skills/developing-camel-quarkus-core-v3-40/ (SKILL.md 108 lines + 8 blueprints).
Limits: external URLs were not fetched (no network tool), so source content is not independently re-verified. Only internal consistency and presence of sources were checked.

## Overall score: 84/100 (no CRITICAL, 0 blocking, 3 HIGH, 4 MEDIUM, 3 LOW)

## Official criteria (A-C)

| Criterion | Status | Evidence |
|---|---|---|
| A1 frontmatter | PASS | name 34 chars kebab; description about 235 chars (<300 and <1536), third person, quoted (contains `:`), WHAT + "Use when" + "Not for Quarkus 4" |
| A2 conciseness | PASS | 108 lines (<500, and even <150 of the template) |
| A3 progressive disclosure | WARN | Links are one level deep. Blueprints >100 lines (integration-examples.md, always-do-patterns.md roughly 100+) have no TOC (LOW) |
| A4 content | WARN | Heavy absolute dates and "16 days old at research time" (SKILL.md:9,16,23-26) are time-sensitive; mitigated by the version lock, but they rot (MEDIUM) |
| A5 workflows | PASS | Upgrade steps in migration-guide.md, Verification in native-mode.md |
| A6 paths | PASS | Relative, forward slashes |
| B scripts | N/A | No scripts |
| C testing | PASS | 4 scenarios (canonical, edge, misuse, trap) >= 3 |

## Team conventions (D)

| Criterion | Status | Evidence |
|---|---|---|
| D1 naming | PASS | name = folder, gerund-noun, version suffix consistent with Version Absolutism |
| D2 three tiers | PASS | All three present and populated (SKILL.md:44-77) |
| D3 version context | PASS | SKILL.md:12-26 |
| D4 verification loop | WARN | Only "representative" commands (SKILL.md:90, native-mode.md Verification); acknowledged as unverified |
| D5 anti-patterns | PASS | never-do-patterns.md has WRONG/CORRECT pairs; SKILL.md table has Instead column |
| D6 links | PASS | See checks below |
| D7 external resources | PASS | SKILL.md:92-108 |

## Requested checks

1. Sources and dates per claim: PARTIAL. Dates exist globally ("All fetched 2026-10-14", line 94), and every blueprint section carries Source URLs. But SKILL.md body (Version Context, Always/Never Do, Quick Reference) has zero inline URLs. See defects D-1, D-2, D-3.
2. `@ApplicationScoped` mandatory on RouteBuilder: PASS. No file claims it. SKILL.md:47 and :71, always-do-patterns.md:37 and never-do-patterns.md:34 say the opposite. evaluation-scenarios.md:17-18 tests exactly this. Caveat: the "not needed / boot-time cost" claim relies on cdi.html, which I could not fetch. Re-verify once before copying (see D-6).
3. Links and anchors: PASS. All 9 blueprint files linked from SKILL.md exist. Anchors resolve against headings: #blueprints--guardrails, #quick-reference, #external-resources, always-do-patterns#1-bom-import, #2-routebuilder-discovery, #3-named-beans, integration-examples#testing and #error-handling, unverified-and-risks#source-bibliography. Back-links `../SKILL.md` and `./native-mode.md` resolve. External URLs: not fetched.
4. Guardrails without unverified claims: FAIL (partial). Several are stated flat though the skill's own register classes them as medium-confidence or unverified (D-1).
5. Description: PASS (about 235 chars, "Use when" present).

## Defects

| ID | Sev | Criterion | Location | Problem | Fix |
|---|---|---|---|---|---|
| D-1 | HIGH | D6/Executable Truth, check 4 | SKILL.md:72 (setter injection), :74 (startRouteDefinitions / adviceRoute) | Both are flat 🚫 rules, but unverified-and-risks.md:39 lists `@EndpointInject`/`@Produce` setter limitation and `adviceRoute()` as medium-confidence. The guardrail does not say so. | Add "(medium confidence)" in-line, or move to Ask First / blueprint only. Line 74 even says "signature unverified" inside a Never-Do instruction. |
| D-2 | HIGH | Executable Truth | SKILL.md:16-20 (Version Context table) | Java 17/21, Maven 3.8.2/3.9.16, Mandrel 25 "since Quarkus 3.36", 3.40.0 date: no URL per row. The Mandrel and Maven sources are only in the bibliography (or absent: no Maven source is listed at all). | Add a Source column with URL + date. Find or drop the Maven claim. |
| D-3 | HIGH | Executable Truth | SKILL.md:83-90 (Quick Reference) | PT3S shutdown, direct timeout=30000/failIfNoConsumers, health default, TLSv1.3 default, expression-extraction default: no source. Some are likely from core.html / direct.html but the link is not stated. | Add a Source column (core.html, direct.html, migration 3.40.0). |
| D-4 | MEDIUM | D2 / consistency | SKILL.md:71 vs never-do-patterns.md:32 | Removing `@ApplicationScoped` is a boot-time optimization (severity "medium" in the blueprint) yet appears under 🚫 Never Do, beside correctness failures. It overstates the rule and contradicts Always Do line 47 ("only when needed"). | Move to Always Do only (already there) or reword as "Avoid ... unless injection is needed". |
| D-5 | MEDIUM | A4 | SKILL.md:9,23-26 | Relative time ("16 days old", "As of 2026-10-14") and Quarkus 4 GA forecast date go stale. | Keep one dated "Version-lifetime risk" block in unverified-and-risks.md; SKILL.md links to it. |
| D-6 | MEDIUM | check 2 | cdi.html claim | The key `@ApplicationScoped` claim was not re-fetched in this audit. | One manual check of cdi.html before replicating the pattern. |
| D-7 | MEDIUM | Executable Truth | SKILL.md:25 | "Maintained to 2027-09-30 per quarkus.io" is stated, then called an inference for Camel Quarkus. Wording is self-contradicting. | Say: "Quarkus (not Camel Quarkus) LTS to 2027-09-30; CQ end date unverified." |
| D-8 | LOW | A3 | integration-examples.md, always-do-patterns.md | Files >100 lines without a TOC. | Add short TOC (or split). |
| D-9 | LOW | style | SKILL.md:8-10 | Meta line "Knowledge skill (hybrid)..." and "Research date" are authoring notes, not agent-useful. | Remove "hybrid" wording; keep version lock. |
| D-10 | LOW | skill-structure | SKILL.md:12-26 | Version Context sits before Quick Navigation. Rule only requires guardrails after Quick Navigation, which is satisfied. | None required; note for consistency. |

## Hybrid-related findings (not defects)

- H-1: TEMPLATE.KNOWLEDGE-SKILL.md says "<150 lines, NO blueprints; if larger convert to action command". This skill is 108 lines, so the size trigger does not fire. The deviation is the blueprints/ dir, not length.
- H-2: skill-structure.md mandates blueprints/evaluation-scenarios.md only for fork skills. Having it on a knowledge skill is allowed and desirable (C1); not a violation.
- H-3: The template uses top-level `## Always Do / Consider First / Never Do`; this skill nests them as `###` under `## Blueprints & Guardrails` and renames to "Ask First", using tables. Matches action-skill convention, diverges from the knowledge template.
- H-4: Template has `## Overview`; this one has Version Context + Quick Navigation instead. Quick Navigation is required by skill-structure.md for action skills; here it is harmless and useful.
- H-5: Heavy unverified/bibliography blueprint (unverified-and-risks.md) is outside both templates; it is what makes anti-hallucination auditable. Keep.
- H-6: Risk of the hybrid: auto-invocable skills load SKILL.md whole on trigger, then blueprints on demand. Splitting guardrail detail away from the summary (never-do 🚫 in SKILL.md vs full text in blueprint) means qualifiers (confidence, source) get lost in the summary, which is exactly D-1/D-2/D-3.

## Recommendation: can the other 12 skills copy this structure?

Yes, conditionally. Do not copy as is.
1. First fix D-1, D-2, D-3 here; otherwise 12 skills inherit sourceless summaries.
2. Formalize the hybrid: add TEMPLATE.KNOWLEDGE-HYBRID-SKILL.md (or amend the knowledge template and skill-structure.md) so the pattern is a convention, not an exception. Otherwise every validator run will flag all 12.
3. Rule for summaries: any flat claim in SKILL.md needs an inline source or a "(medium confidence)/(unverified)" tag.
4. Use hybrid only where content exceeds about 100 lines of SKILL.md; for small skills the plain template still applies.
5. Keep the unverified-register blueprint and 3+ scenarios per skill.
