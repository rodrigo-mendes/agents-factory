# Validation 2 (final) - developing-camel-quarkus-http-v3-40

Validator: skill-best-practices-validator (hybrid knowledge skill rubric). Date 2026-10-14.
Target: packages/camel-quarkus-skills/.apm/skills/developing-camel-quarkus-http-v3-40/ (SKILL.md 107 lines, 7 blueprints plus evaluation-scenarios).
Scoring: 100 minus 4 per HIGH, 1.5 per MEDIUM, 0.5 per LOW. URLs were not fetched; presence and consistency only.

**Score: 84 / 100** (2 HIGH, 4 MEDIUM, 4 LOW)

Note on process: the P3 "Report Plan" approval gate could not be obtained from the user inside this run; reports were written to the paths the invoking agent specified.

## Official criteria (A-C)

| ID | Status | Evidence |
|---|---|---|
| A1 | PASS | name = folder, third person, "Use when", "Not for" |
| A2 | PASS | 107 lines |
| A3 | PASS | one level; all blueprint links exist |
| A4 | PASS | |
| A5 | PASS (n/a) | |
| A6 | PASS | |
| B | n/a | |
| C | PASS | 5 scenarios (4 types plus an Ask First scenario); scenario 1 must_not has @ApplicationScoped (evaluation-scenarios.md:23) |

## Team criteria (D1-D7)

| ID | Status | Evidence |
|---|---|---|
| D1 | PASS | |
| D2 | WARN | H1, H2 |
| D3 | PASS | every row has a Source |
| D4 | n/a | |
| D5 | PASS | medium anti-patterns have side-by-side code in never-do-patterns.md |
| D6 | PASS | |
| D7 | PASS | |

## Checks requested by the caller

| # | Check | Result |
|---|---|---|
| 1 | High-only Always/Never Do, High alternatives, one claim per bullet | FAIL (H1, H2, M2). Never Do contains no medium rows (the model for the family) |
| 2 | Source column | PASS (Version Context 14-22, Quick Reference 84-95; "page not recorded" at :95); one weak row (L1) |
| 3 | Shared facts match tags | PASS. SKILL.md:25-27, :17-18, register :18-21 reproduce the family-facts tags; TLS rows (:49, :90) are High as in the family facts |
| 4 | Register counts and mapping table | PASS. Unverified table has 10 rows and the heading says 10; irresolvable has 3; mapping table covers High, medium, unverified, inferred, do not assert, contradiction (every tag used in SKILL.md). Header wording is ambiguous (L2) |
| 5 | Not stronger than blueprint | PARTIAL (M1) |
| 6 | @ApplicationScoped | PASS. always-do-patterns.md:38 and integration-examples.md:15 say "no @ApplicationScoped"; no sample has the annotation; no "mandatory" wording |
| 7 | Links and anchors | PASS. `#1-dependency-and-native-ssl`, `#bridging-quarkustls-to-camel`, `#3400-behaviour-change`, `#handling-httpoperationfailedexception`, `#circuit-breaker-with-fallback`, `#medium-confidence-anti-patterns`, `#the-5-settings-that-are-not-bridged`, `#unverified-items-10`, `#medium-confidence-items`, `#contradiction-recorded`, contents anchors in never-do/always-do resolve |
| 8 | Scenarios | PASS |

## Recommendations by priority

### HIGH

- **H1 (check 1, D2)** SKILL.md:73 Never Do row 2: the alternative "Set verification on the endpoint and handle revocation outside the bridge" is not High. blueprints/tls-and-security.md:42 and never-do-patterns.md:40 both say the endpoint-level options (`hostnameVerificationPolicy`, `x509HostnameVerifier`) are medium confidence and "not in the Never Do alternative", yet the SKILL.md alternative still tells the reader to set verification on the endpoint, citing the tls-registry page, which does not state it (the options come from the http-component page). The blueprint's WRONG/CORRECT code (never-do-patterns.md:36-38) shows a CORRECT sample that sets no verification at all. Fix: alternative = "Do not rely on `quarkus.tls.*` for revocation or hostname checks; the bridge ignores them (tls-registry page)", and move "set the endpoint options" to Ask First (medium).
- **H2 (check 1)** SKILL.md:50-51 Always Do bullets 4 and 5 are not single High claims. Bullet 4 mixes an instruction with "(package unverified)" and rests on behaviour the blueprint marks medium (when the exception is thrown depends on `throwExceptionOnFailure` / `okStatusCodeRange`, always-do-patterns.md:58) and an unversioned manual page for `onException`. Bullet 5 has two claims (use `camel-quarkus-microprofile-fault-tolerance`; do not assert its defaults, which are unverified) and links the breaker defaults caveat. Fix: bullet 5 = "Use `camel-quarkus-microprofile-fault-tolerance` for `circuitBreaker()` (Stable, extension page)"; move the defaults warning to Ask First; move bullet 4 to Ask First or reduce it to the High statement from the http-component page that `HttpOperationFailedException` is thrown for non-OK statuses (still medium; so Ask First is the right home).

### MEDIUM

- **M1 (check 5)** SKILL.md:47 "do not set `quarkus.ssl.native=true`" is stronger than blueprints/always-do-patterns.md:16, which only says the extension "enables SSL in native mode automatically"; the SKILL itself calls the plain-`camel-http` difference inferred (line 66). Fix: "The extension enables SSL in native mode automatically; no extra setting is documented as needed".
- **M2 (check 1)** SKILL.md:48 Always Do bullet 2 has two claims (reference the bean explicitly; bridging is not applied to an endpoint on its own). Split or keep one.
- **M3 (check 1/5)** SKILL.md:72 and blueprints/never-do-patterns.md:19 use `quarkus.tls.protocols=TLSv1.3,TLSv1.2,TLSv1` as the "unknown protocol names" sample, but those are valid JSSE names; only the OpenSSL cipher line illustrates the failure. Use a truly unknown name (for example `TLSv9`) or keep only the cipher line.
- **M4 (cross-skill, check 3)** blueprints/fault-tolerance-and-errors.md:26 and register line 40 class the Dead Letter Channel default (6 redeliveries / 1 s) as **unverified**; core classes the same fact as medium (SKILL.md:59 of core). Pick one.

### LOW

- **L1** SKILL.md:16 Version Context row: the source is a Maven directory listing, but "JVM and native since 1.0.0" comes from the extension page; add that URL.
- **L2** blueprints/unverified-and-risks.md:3 "9 plus 1 = 10 unverified" does not say whether the 3 irresolvable items are among the 9; the unverified table lists 10 and irresolvable lists 3 (13 distinct entries).
- **L3** SKILL.md:57 and Quick Reference header (line 80) treat single-page component defaults as medium; platform-http and file treat the same kind of source as High (see cross-skill list).
- **L4** blueprints/integration-examples.md:89 test sample still extends `CamelQuarkusTestSupport` with no import line; fine, but add the "package unverified" comment present in line 74 to the class itself.

## Conclusions

Strong register (best mapping table of the four) and a Never Do table that is nearly clean. Two HIGH defects remain: one non-High alternative with a misattributed citation, and two Always Do bullets that are not single High claims.
