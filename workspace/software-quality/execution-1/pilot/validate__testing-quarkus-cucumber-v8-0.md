# Validation: testing-quarkus-cucumber-v8-0 (pilot U1)

Date 2026-11-01. Target: packages/quality/quarkus-acceptance-testing/.apm/skills/testing-quarkus-cucumber-v8-0/ (source only).
Spec: skill-best-practices-validator. Also checked: hybrid-format-checklist.md, _family_facts.md (F1-F12), _family_rules.md (1-10), SPIKE_RESULTS.md.
Approval: relay of G1 ("Approve", 2026-10-31); not a new approval.

## Score: 90.0 / 100  (0 HIGH, 3 MEDIUM, 5 LOW; 100 - 0 - 7.5 - 2.5)

Verdict: passes. No blocking findings.

## Measured facts (line counts via Grep count)
SKILL.md 103 (target 100-200). Blueprints: always-do 48, never-do 70, runner-patterns 123, steps-and-state 109, migration-guide 48, evaluation-scenarios 67, unverified-and-risks 82 (all <= 160).
Description about 246 chars (< 300), quoted, has "Use when". name == folder, version suffix -v8-0. Frontmatter holds only name + description.
No absolute paths, `.github/`, or relative dates found (grep). All internal links and anchors resolve by heading inspection. evaluation-scenarios has 6 (canonical, edge, rejection, 2 traps, check). unverified-and-risks has the `Version-lifetime risk` and `Source Bibliography` headings. Three tiers are present and populated.
Not run: scripts/verify_skill.py (no shell tool in this session). The caller must run it.

## Findings

### MEDIUM
1. **Rule 1 / A4: mis-sourced or unsourced claim** (SKILL.md:16; migration-guide.md:42). The Version Context row says "Quarkus 3.40 is tested on 17 and 21" and cites Cucumber release-notes/v8.0.0.md. That page only supports F2 (Cucumber needs Java 17). The Quarkus Java range is not in F2 or F5. The migration matrix then states "Max 21" as a bound. Fix: split the row so Java 17 cites release notes and the Quarkus Java range cites the Quarkus page, or tag it (medium confidence)/(unverified). Drop "Max 21" if it cannot be sourced.
2. **Family rule 7 vs default B1** (SKILL.md:44-47; unverified-and-risks.md:38). Rule 7 says Cucumber runs through the JUnit Platform engine (`@Suite`) and `cucumber-junit` is never used. B1 (default) runs the Cucumber CLI `Main.run` inside a Jupiter `@QuarkusIntegrationTest`. The register says the "intent" is kept, but the literal rule is not. Rule 10 defers the path decision to G2. Fix: add an amendment to rule 7 (B1 = documented exception, B2 = engine) or have the orchestrator record the exception at G2. The skill text can stay.
3. **Rules 1 and 3: Always/Never Do evidence** (SKILL.md:59, 60, 77, 82). Always Do bullets 9 and 10 cite the engine README for things it does not state. The `@R`/`@change` tags come from F11 (a factory convention). The non-zero testcase count is derived from F6/F3. Never Do rows 1 and 6 give B1 as the alternative, but B1 is medium confidence, and rule 3 requires High-confidence alternatives. Fix: cite F11 for the tags and the Quarkus/engine pages for the count, or tag them (medium confidence). Reword the two alternatives so the High-confidence one (B2 `@Suite`) comes first.

### LOW
4. **Family fact consistency, F4** (SKILL.md:79; never-do-patterns.md:30). F4 says use `cucumber-jakarta-cdi` after `cucumber-cdi2` removal. The SKILL.md Never Do row gives only `cucumber-picocontainer`. The migration guide does mention jakarta-cdi. Fix: add "(or `cucumber-jakarta-cdi` for a separate CDI SE container)". Also, `openejb` and `deltaspike` are not in F4; they come from the CHANGELOG, so cite it.
5. **Untested versions and extras in the pom fragment** (runner-patterns.md:12, 31, 39, 62-65). The spike used Failsafe/Surefire 3.5.4. The fragment pins 3.6.1, and "current plugin line" has no URL. It also adds `cucumber-picocontainer` and the Failsafe `java.util.logging.manager` and `maven.home` properties, which the spike did not use. Fix: tag these (medium confidence) or run a spike. The Surefire plugin also reuses the property `failsafe-plugin.version`, so rename it to `surefire-failsafe.version`.
6. **Unsourced Jackson version** (migration-guide.md:46). "2.21.8 (Quarkus BOM)" has no tag, and the BOM read was partial (register L1, I1). Fix: add (unverified) or remove the number.
7. **Tag format, rule 2** (SKILL.md:94). "representative command (unverified output)" is not a plain `(unverified)` tag, and its Source cell is not a URL. Fix: write `n/a (unverified)`.
8. **Quick Reference evidence for B1** (SKILL.md:44-47 vs SPIKE_RESULTS.md:7, 11). The spike evidence (Quarkus 3.40.1, Cucumber 8.0.4, tests=1 failures=0) is only in the register and runner-patterns. A one-line pointer to M1 in the guardrails header would make the medium tag traceable. Optional.

## Consistency with family facts (checked)
F1 (8.0.4, 8.0.0, 7.34.9), F2, F3 (6.1.3 via BOM, `@Suite`, `junit-platform-suite`), F5 (`quarkus-junit`, 3.31 rename, LTS 2026-09-30), F6, F7 (1.3.0, 7.21.1, #32/#278/#298/PR #310/#119, spike), F8 (WireMock 3.x, 1.8.1) all match. F9, F10 and F12 are not claimed here, and F11 is used correctly. Rules 4, 5, 8 and 9 are satisfied. B1 behavior matches the spike (2 scenarios, tests=1, RestAssured port auto-configured). Rules 1, 3 and 7 are the exceptions above.

## Priority order for fixes
MEDIUM 1, 3, 2, then LOW 4-7.
