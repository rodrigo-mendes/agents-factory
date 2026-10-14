# Validation 2 (final) - developing-camel-quarkus-platform-http-v3-40

Validator: skill-best-practices-validator (hybrid knowledge skill rubric). Date 2026-10-14.
Target: packages/camel-quarkus-skills/.apm/skills/developing-camel-quarkus-platform-http-v3-40/ (SKILL.md 112 lines, 8 blueprints).
Scoring: 100 minus 4 per HIGH, 1.5 per MEDIUM, 0.5 per LOW. URLs were not fetched; presence and consistency only.

**Score: 92 / 100** (0 HIGH, 4 MEDIUM, 4 LOW)

Note on process: the P3 "Report Plan" approval gate could not be obtained from the user inside this run; reports were written to the paths the invoking agent specified.

## Official criteria (A-C)

| ID | Status | Evidence |
|---|---|---|
| A1 | PASS | name = folder, third-person description with "Use when" and "Not for" |
| A2 | PASS | 112 lines |
| A3 | PASS | one level; all linked blueprints exist (8 files) |
| A4 | PASS | defaults carry a source per row |
| A5 | PASS (n/a) | knowledge skill |
| A6 | PASS | relative paths only |
| B | n/a | no scripts |
| C | PASS | 4 scenarios, one per type; scenario 1 must_not has the @ApplicationScoped item (evaluation-scenarios.md:23) |

## Team criteria (D1-D7)

| ID | Status | Evidence |
|---|---|---|
| D1 | PASS | |
| D2 | PASS | all tiers populated; no medium claim inside Always/Never Do |
| D3 | PASS | every Version Context row has a Source ("page not recorded" at SKILL.md:21) |
| D4 | n/a | |
| D5 | WARN | Never Do row 5 (SKILL.md:76) has prose only in blueprints/never-do-patterns.md:54-56, no side-by-side code (LOW) |
| D6 | PASS | |
| D7 | PASS | |

## Checks requested by the caller

| # | Check | Result |
|---|---|---|
| 1 | High-only Always/Never Do, High alternatives, one claim per bullet | PASS with one weakness (M1). Never Do alternatives (SKILL.md:72-76) all cite High pages |
| 2 | Source column on every row | PASS. Version Context 15-21, Quick Reference 84-100 all have an exact URL or "page not recorded" |
| 3 | Shared facts match family-facts tags | PASS. SKILL.md:17, :18, :24-26, register :27-29, migration-guide.md:16 and :30 reproduce the tags exactly (High, Medium absence of evidence, Unverified end date, Unverified inbound bridging) |
| 4 | Register counts and mapping table | PASS on counts (15 = 3 irresolvable + 12 other, matching lists; medium list has 5 bullets); mapping table present but see M2 |
| 5 | No claim stronger in SKILL.md than blueprint | PASS (spot-checked every Always/Never/Quick Reference row against its blueprint) |
| 6 | @ApplicationScoped | PASS. Only uses: SKILL.md:51 and :75 (conditional/anti-pattern); always-do-patterns.md:62 has `@ConfigProperty`; never-do-patterns.md:48 is a labelled WRONG example; integration-examples.md:47 and always-do-patterns.md:10 say "no injection, so no @ApplicationScoped". No "mandatory" wording anywhere |
| 7 | Links and anchors | PASS. `#1-declare-the-endpoint-and-restrict-methods`, `#4-close-plain-http-when-https-is-configured`, `#5-read-the-authenticated-identity-from-the-documented-header`, `#quarkus-body-properties`, `#does-the-340-bridging-affect-the-inbound-server`, `#https-configuration`, `#legacy-peers`, `#authentication-and-identity`, `#error-handling`, `#version-lifetime-risk`, `#source-bibliography`, `#tag-to-register-mapping`, `#irresolvable-items-do-not-assert` resolve |
| 8 | Scenarios | PASS (canonical, edge, misuse, trap) |

## Recommendations by priority

### MEDIUM

- **M1 (check 1)** SKILL.md:48 Always Do bullet 3 packs three claims (use the TLS registry; `SSLContextParameters` unsupported; property names from a second page). Fix: split, or keep the single High claim "serve HTTPS through the Quarkus TLS registry" and move the unsupported-`SSLContextParameters` statement to the Never Do row it already has (line 72).
- **M2 (check 4)** blueprints/unverified-and-risks.md:18 mapping row 1 lists "ports, `body.*` defaults" under "Other unverified items", but those entries are in the Irresolvable table (lines 36-37; row 2 of the mapping also lists them). The medium row (line 20) names seven topics against "5" entries (they are bundled into five bullets). Fix: remove ports and `body.*` from row 1; either say "7 topics in 5 entries" or split the bullets.
- **M3 (cross-skill)** SKILL.md:21 and register line 51 mark Java, Maven and GraalVM requirements "unverified / not researched", while the sibling skills record Java 17 and 21 for Camel Quarkus 3.40 from https://camel.apache.org/releases/q-3.40.0/ (core, http, file). Fix: add the same Java row with that source (it is not extension-specific, so it is a shared fact), keep Maven as unverified.
- **M4 (check 1/5)** SKILL.md:76 (Never Do "Assume Quarkus 4 compatibility") states only the High Java 21 fact, but the implied harm rests on the Medium absence-of-evidence fact; blueprints/never-do-patterns.md:54-56 does not mention the Medium tag and has no code. Fix: add "(no Camel Quarkus build on Quarkus 4 is known; medium confidence, absence of evidence)" to the blueprint, or move the row to Ask First.

### LOW

- **L1** blueprints/unverified-and-risks.md:3 admits the 12 "other" entries "are not individually traced to the research file"; consider recording which were added by the fix passes.
- **L2** blueprints/evaluation-scenarios.md:78 says unknown protocol names "fail startup"; the guide (and SKILL.md:65) say they "fail SSL context creation". Use the guide wording.
- **L3** blueprints/migration-guide.md:17 cites the migration index as "medium confidence: not re-fetched"; the register Medium list (lines 56-61) has no matching entry.
- **L4** SKILL.md:75 (Never Do row 4, severity "low" in the blueprint) duplicates Always Do bullet 6 (line 51); fine, but core rates the same rule "medium".

## Conclusions

Closest to the template of the four. The defect classes from round 1 are resolved. Remaining items are register bookkeeping and one multi-claim bullet. The explicit decision that global TLS widening is Ask First, not Never Do (blueprints/tls-and-security.md:39, never-do-patterns.md:3), is the correct reading of the family facts and contradicts core (see the cross-skill list in the hand-back).
