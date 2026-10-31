# P6 round 4 VALIDATE, group A (independent pass)

Spec: skill-best-practices-validator (A1-A6, B, C, D1-D7) plus family rules 1-15 (and the inherited Camel rules 11, 12, 17-19), evidence-rule, tag-notation, hybrid-format-checklist, cross-skill tag consistency.
Rubric: 100 - 6 HIGH - 2.5 MEDIUM - 0.5 LOW. Read-only; no skill edited.

## Score table

| Skill | HIGH | MEDIUM | LOW | Score |
|---|---|---|---|---|
| developing-quarkus-amazon-lambda-v3-40 | 0 | 0 | 3 | 98.5 |
| developing-quarkus-amazon-lambda-http-v3-40 | 3 | 3 | 5 | 72.0 |
| securing-quarkus-lambda-cognito-v3-40 | 0 | 1 | 5 | 95.0 |
| integrating-quarkus-amazon-data-v3-40 | 2 | 0 | 5 | 85.5 |
| testing-quarkus-amazon-lambda-v3-40 | 2 | 3 | 2 | 79.5 |

## Mechanical checks (all PASS unless listed in findings)

- Frontmatter: only `name` + `description`; name equals folder; each description is quoted, has "Use when", is under 300 chars (estimated about 250-285), and has no reserved words.
- SKILL.md length: 111 / 118 / 109 / 121 / 102 lines (target 100-200). Largest blueprint is 159 lines (lambda always-do-patterns.md), within the 160 limit.
- Every skill has always-do, never-do, topic blueprints, unverified-and-risks and evaluation-scenarios (6 scenarios each). Quick Navigation links the Verification Loop in all five.
- Contents list is present in every blueprint over 100 lines (family rule 12).
- Links and anchors: every relative link and anchor in the 5 SKILL.md files and blueprints was resolved by hand. None is broken. All sibling skill names exist under `.claude/skills/`.
- Register header counts match the rows (grep: 19 / 27 / 24 / 25 / 23 rows, equal to the declared U+I+M+L(+G)).
- Quick Reference Source columns hold absolute URLs or "page not recorded" (Camel rule 11).
- No absolute local paths, `.github/` or relative dates.
- Family rules 1-8: no violation found (3.40 only, 3.23.x only, JVM/SnapStart/native always Ask First, Terraform deferral, tenant from token, observability bounded).
- Facts checked against the family facts and research files: no wrong fact found. The Beta1 / "end of November" claim in the lambda skill is in the Camel family facts (orchestrator-verified) but not in the lambda research file; it is cited as a family fact, so I do not count it.

---

## 1. developing-quarkus-amazon-lambda-v3-40 (98.5)

No HIGH, no MEDIUM.

- LOW. Rule 13 / evidence-rule. `SKILL.md:93-94`, `blueprints/snapstart.md:26-29`, `blueprints/packaging-and-artifact-contract.md:70`. Evidence: "`enabled` default `true`", "`preload-classes` ... (these 4 default `true`)" are untagged. Register L2 says all-config was read through a summarising tool and "other wording is a paraphrase". No verbatim quote of the default rows is recorded. Fix: tag (medium confidence) or record the verbatim row text.
- LOW. Hybrid rule (every flat claim has a URL or a tag). `SKILL.md:61`, `SKILL.md:64-68`. Evidence: Ask First rows carry High AWS facts ("published versions only, no provisioned concurrency, EFS...", "timeout default 3 s, max 900 s") with no inline URL. Fix: add the AWS URL or point to the Quick Reference row.
- LOW. Evidence-rule (absence claims). `blueprints/packaging-and-artifact-contract.md:79`. Evidence: "Funqy: the 3.40 guide body neither mentions nor recommends it" is untagged. Fix: add (medium confidence, absence of evidence).

## 2. developing-quarkus-amazon-lambda-http-v3-40 (72.0)

### HIGH

- HIGH-1. Evidence-rule (Never Do alternative must be High). `SKILL.md:81`, `blueprints/never-do-patterns.md:72-79`.
  Evidence: row `Let Quarkus REST bind them (@QueryParam List<String>) ([AWS](...http-api-develop-integrations-lambda.html))`. F5 says the handler rebuilds the request from `rawPath` + `rawQueryString` "(medium confidence, L4)".
  The AWS page only supports the "2.0 combines duplicates with commas" half. That Quarkus REST then binds the values rests on the summarised source (M10). The ✅ is not High and its citation does not support it.
  Fix: move the ✅ to an Ask First / blueprint item tagged (medium confidence); keep the Never Do only on the AWS sentence, or drop the Quarkus-REST alternative from the row.
- HIGH-2. Evidence-rule (Always Do = one High claim, High source). `SKILL.md:56`, `blueprints/always-do-patterns.md:116-118`.
  Evidence: "Set an explicit `Content-Type` on every response ([guide])". The justification (a missing `Content-Type` counts as binary) is "(medium confidence: source read through a summarising tool, L4)" (M10). `ask-first-decisions.md:90` says the practice "does not depend on either" medium claim, but no High source is given for it.
  Fix: demote to Ask First C10 (already there), or cite a High source for the practice.
- HIGH-3. Family rule 12 (inherited) and tag-notation ("IDs are exactly U1, I1, M1, L1"). `blueprints/unverified-and-risks.md:3`, `:48-54`, `:85-87`, `:104`.
  Evidence: "Source conflicts" section with id `G1`, "Supporting evidence" with `G2`; mapping row `(unverified) guide vs source on REST response encoding | ... | G1`; header "Research ids (... G1, G2) are kept unchanged".
  The text tag is (unverified) but the register class is not U. A non-standard class and ids.
  Fix: fold G1 into a U-id (e.g. U12, "guide vs source on REST response encoding, cite both") and G2 into the M1 row note; remove the two sections.

### MEDIUM

- MEDIUM-1. Evidence-rule (flat claim without URL or tag; same-claim-same-tag). `SKILL.md:90`.
  Evidence: "Cognito caveat: the Principal path `...claims.cognito:username` matches ID tokens, not access tokens (access tokens carry `username`); identify users and tenants by `sub`."
  No URL and no tag. The family fact and the cognito skill (K2, U11) tag the Quarkus behaviour with an access token (unverified).
  Fix: add the Cognito access-token URL and "(Quarkus behaviour with an access token is (unverified))".
- MEDIUM-2. Evidence-rule / rule 13 (tool-summarised source needs a tag). `blueprints/request-and-response-mapping.md:3`, `:13-32`, `:40`, `:48`.
  Evidence: header says "every statement here is a paraphrase of source" (L4). Only the comma-split line is tagged. "dispatch exception -> 500 {"message":"Internal Server Error"}", "non-numeric X-Forwarded-Port ... yields a 500", "Set-Cookie -> cookies[]" are flat.
  The `Tag to register mapping` M10 row does not list this file (register lines 91-115).
  Fix: tag the lifecycle block (medium confidence) and add the file to the M10 row.
- MEDIUM-3. Rule 13 (partly read page). `blueprints/build-output-and-artifact-contract.md:23`, `SKILL.md:101`.
  Evidence: `mock-event-server.enabled` default `true` untagged. Register L2 (line 80): all-config "keys were found only in characters 0 to 100,000" of a page read through a summariser. The four `lambda-http.*` defaults from the same page are tagged medium.
  Fix: tag the `enabled` default (medium confidence) or record a verbatim quote.

### LOW

- LOW. A6 / rule 11 source column. `SKILL.md:97` ("both extensions" cites only the HTTP `sam.jvm.yaml`); `SKILL.md:102` (REST 29 s cites only the HTTP quotas page). Fix: add the REST template and REST quota URLs.
- LOW. Evidence-rule (no caveats in an Always Do bullet). `SKILL.md:51` ("(with Quarkus REST)"). Move to Ask First C2.
- LOW. Tag consistency. `blueprints/evaluation-scenarios.md:113`: "(null at runtime)" is a must_pass fact resting on M10 and is untagged. Add (medium confidence).
- LOW. Interpretation stated as fact. `blueprints/build-output-and-artifact-contract.md:25` "(documentation typo)". Remove or tag.
- LOW. Hybrid rule (URL for flat claims in Ask First). `SKILL.md:62-71`: High AWS facts (30 s, 10 MB / 6 MB, feature split) have no inline URL.

## 3. securing-quarkus-lambda-cognito-v3-40 (95.0)

No HIGH.

### MEDIUM

- MEDIUM-1. Cross-skill tag consistency. `SKILL.md:49`, `blueprints/always-do-patterns.md:37`.
  Evidence: Always Do bullet: "Know that the guide's Principal name is `cognito:username`, not `sub`, and that this matches ID tokens only."
  The same register (U11), K2 (`ask-first-decisions.md:36`) and option-a:16 tag "Quarkus behaviour with an access token" (unverified); the bullet is flat. The bullet also carries three claims and an advice sentence (not one High claim).
  Fix: reduce the bullet to one High claim ("`cognito:username` is an ID-token claim; access tokens carry `username`"), and keep the Quarkus-behaviour sentence in Ask First K2 with its (unverified) tag.

### LOW

- LOW. Rule 11 / hybrid rule (exact page per default). `SKILL.md:20`: "default `false` (medium confidence)" is cited to the aws-lambda-http guide; the default comes from all-config (see `SKILL.md:88`). Use the all-config URL.
- LOW. Always Do vs Ask First. `SKILL.md:48`, `:50`, `:51`: bullets 1, 3, 4 presuppose Option A (`enable-security`), but K1 (`SKILL.md:62`) leaves A / B / C open and Option B has no `enable-security`. Add "when Option A is chosen" to the bullets or move them under K1.
- LOW. Undefined label. `blueprints/multi-tenant-isolation.md:19` "**A8.**" is not defined in this skill (A8 is the data skill's LeadingKeys pattern). Rename.
- LOW. Format. `blueprints/multi-tenant-isolation.md:64-65`: no blank line before `## Checklist`.
- LOW. Camel rule 19 wording. `blueprints/never-do-patterns.md:3` and headings use "(critical)"; the family wording is low|moderate|high. The intent (no bare "medium") is met.

## 4. integrating-quarkus-amazon-data-v3-40 (85.5)

### HIGH

- HIGH-1. Evidence-rule (Never Do = High rows only). `SKILL.md:81`, `blueprints/never-do-patterns.md:30-40`, register `M3` (line 55) and mapping row (line 104).
  Evidence: row "Pin the credentials type to access-key environment variables (`env-variable`) on a function that uses or may use SnapStart". F2 admits "the mapping of the Quarkiverse value `env-variable` to the SDK `EnvironmentVariableCredentialsProvider` is inferred from the value name (medium confidence, M3)".
  The ❌ premise is the inferred mapping; the SKILL.md row carries no tag.
  Fix: either record a Quarkiverse page quote that defines `env-variable`, or rewrite the row on the High AWS sentence only ("do not rely on access-key environment variables under SnapStart") and put the `env-variable` mapping in Ask First C2 with the (medium confidence) tag.
- HIGH-2. Family rule 13 (tool-summarised / partly read source is High only with a verbatim quote). `SKILL.md:101-105`, `blueprints/limits-and-production-readiness.md:17`, `:38`, `:48`, register L1 (line 69).
  Evidence: Quick Reference rows `connection-timeout` / `socket-timeout` = `2S` / `30S`, `max-concurrency` = `50`, `telemetry.enabled` = `false`, `path-style-access` = `false`, `create-table-schemas` = `true` are untagged. L1 says the pages were "read through a fetch tool that summarises and caps quotes at 125 characters; config defaults were extracted from those summaries". The research gives no verbatim quote for these rows (its only mention is a single line).
  The family facts verify only the client-type, credentials and endpoint-override defaults.
  Fix: tag these rows (medium confidence), or record the verbatim page row. This is the same treatment the HTTP skill gives the `lambda-http.*` defaults.

### LOW

- LOW. Hybrid rule (no caveats in Always Do). `SKILL.md:58-59`: A8 and A9 bullets end with "Applying it to a tenant id: Ask First C4"; A9 has a bare "([IAM policy variables](...))" tail. Move the pointer out of the bullet.
- LOW. Tag consistency. `blueprints/unverified-and-risks.md:18` says "High for the release" while `SKILL.md:17` and M9 tag the same date (medium confidence). Align.
- LOW. Hybrid rule (URL for Ask First facts). `SKILL.md:66-74`: quoted facts (CRT "is not done by default", presigner, Dev Services contradiction) have no inline URL.
- LOW. Format. `blueprints/dev-services.md:22-23`: no blank line before `## Provider and images`.
- LOW. Camel rule 19 wording. `blueprints/never-do-patterns.md:3` "(severity: critical)".

## 5. testing-quarkus-amazon-lambda-v3-40 (79.5)

### HIGH

- HIGH-1. Evidence-rule / skill-structure.md ("every flat claim in SKILL.md carries an inline URL or a tag"; Always Do = one inline URL). `SKILL.md:47-52`.
  Evidence: Always Do bullets 2-7 have no inline URL at all ("Declare `quarkus-junit` and `rest-assured` in test scope. See [patterns]..."). Only bullet 1 (line 46) has a source link. The other four skills link a source in every bullet.
  Fix: add the guide / Dev Services / testing-guide URL to each bullet.
- HIGH-2. Evidence-rule (Never Do / Always Do High only) and tier consistency. `SKILL.md:48`, `:70`, `blueprints/never-do-patterns.md:50-62`, `blueprints/unverified-and-risks.md:56` (M9).
  Evidence: Never Do row "Use a port key other than `quarkus.lambda.mock-event-server.*`" and Always Do "Configure the mock server **only** through `quarkus.lambda.mock-event-server.*`" are untagged. The same skill tags the supporting fact at `SKILL.md:61`: the short keys "exist, are not deprecated and are not read by the start-up (medium confidence, M9, from source at tag 3.40.1.1)". F3's own impact: "the guide gives no behaviour for them". The High basis is only an absence of guide text.
  Fix: reword the Never Do to the High statement ("the guide documents only `mock-event-server.*`; use those"), without implying the short keys are wrong; move the "exclusive / not read" claim to Ask First with (medium confidence).

### MEDIUM

- MEDIUM-1. Evidence-rule / rule 13 (summarised source without tags). `blueprints/mock-event-server.md:7-11`, `:22`.
  Evidence: header says the source was "summarised by the fetch tool (L3)", yet the lifecycle steps are flat: "A handler error returns status **500**", "If the server closes, the caller gets 503", "The start is logged at debug level only", "`setMaxWorkerExecuteTime(60)` is a worker limit". Only the 500 is tagged elsewhere (M10); the mapping row for this file lists M10, M8, U1, U2 only.
  Fix: tag steps 1-5 (medium confidence) and extend the mapping rows.
- MEDIUM-2. Rule 13 (partly read page). `SKILL.md:81`, `blueprints/always-do-patterns.md:89-91`, `:102`, register L2 (line 68).
  Evidence: `mock-event-server.enabled` default `true` untagged, while all-config was read "0 to 100,000 of 232,437" via a summariser and the four `lambda-http.*` defaults from the same read are tagged medium (M12).
  Fix: tag (medium confidence) or record the verbatim row.
- MEDIUM-3. Always Do vs Ask First (family rule 3 pattern; rule 9). `SKILL.md:52` vs `SKILL.md:58`; `blueprints/always-do-patterns.md:120-127`.
  Evidence: Always Do "Let Dev Services start the AWS stack in tests: keep `endpoint-override` out of the test profile" presupposes option A of Ask First row 1 ("Dev Services container vs `@InjectMock` vs `endpoint-override`"). It also rests on the 3.23.x pairing (M7, medium) and on unverified IT / sharing behaviour (U6, U7).
  Fix: remove it from Always Do (keep the High fact "endpoint-override disables Dev Services" as a one-claim bullet) and leave the choice in C1.

### LOW

- LOW. Rule 9. `SKILL.md:69`: the ✅ in the "Call real AWS from unit tests" row names Dev Services (pairing medium) and `@InjectMock` without pointing to Ask First C1 (F2 does).
- LOW. Provenance. `blueprints/unverified-and-risks.md:51`, `:67` cite "family rule 18" / "family rule 17"; these exist only in the Camel `workspace/_family_rules_v3.40.md`, not in the quarkus-aws-saas rules 1-15. Name the file.

---

## Cross-skill consistency (same fact, same tag)

| Fact | Lambda | HTTP | Cognito | Data | Testing | Family facts | Result |
|---|---|---|---|---|---|---|---|
| `lambda-http.*` defaults | n/a | medium | medium | n/a | medium | medium | consistent |
| `mock-event-server.enabled` default `true` | untagged | untagged | n/a | n/a | untagged | not listed | consistently untagged (see rule-13 findings) |
| short `dev-port`/`test-port` keys | medium (M7) | n/a | n/a | n/a | medium (M9) but High in Never Do | medium | testing Never Do inconsistent (HIGH-2) |
| 3.23.x paired with Quarkus 3.40.1.1 | n/a | n/a | n/a | medium | medium | medium | consistent |
| Dev Services sharing contradiction | n/a | n/a | n/a | unverified (U10) | unverified (U6) | cite both | consistent |
| Cognito `cognito:username` vs access token | n/a | flat | Quarkus behaviour (unverified), Always Do flat | n/a | flat | High claims, behaviour (unverified) | HTTP:90 and Cognito:49 inconsistent |
| SnapStart restore limit 2 s vs 10 s | both quotes, (unverified) | n/a | n/a | n/a | n/a | same | consistent |
| Preview status of `-http` / `-rest` | n/a | High | High | n/a | n/a | High | consistent |
| Maven 3.9.16 | medium (M8) | medium (M5) | n/a | n/a | n/a | n/a | consistent (research tags it High in one file; the skills are more conservative, acceptable) |

## Priority fix list

1. HTTP HIGH-1, HIGH-2, HIGH-3 (tier and register structure).
2. Testing HIGH-1 (missing inline URLs, mechanical) and HIGH-2 (Never Do / Always Do tier for the short port keys).
3. Data HIGH-1 (env-variable mapping) and HIGH-2 (summarised defaults).
4. The rule-13 `enabled` default and the summarised-source tagging (HTTP MEDIUM-2/3, Testing MEDIUM-1/2): decide once whether `enabled` and the all-config defaults are tagged medium family-wide.
