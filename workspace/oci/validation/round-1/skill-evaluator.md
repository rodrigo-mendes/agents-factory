# Static evaluation: design-oci-architecture (round 1)

Mode: static, no agents spawned. Inputs: evaluation-scenarios.md (9 scenarios), oci-serverless-architect.agent.md (A), router SKILL.md (R), the 6 routed skills' SKILL.md (S, mostly via keyword search; only the pubsub SKILL.md was read in full).
Overall: 2 PASS, 6 AT-RISK, 1 FAIL (untestable). 2 HIGH, 4 MEDIUM, 3 LOW findings.

## Verdicts

| # | Scenario | Verdict | Driving lines |
|---|---|---|---|
| 1 | Full-stack design | AT-RISK | A:26-29, A:48-49 (NEEDS-INPUT vs full design); A:115 |
| 2 | Security review, plaintext DB_PASSWORD | AT-RISK | A:48-49, A:115-121 |
| 3 | Multi-function gateway routes | AT-RISK | A:6-7 ("states no OCI facts"), A:26-29 |
| 4 | Misuse: also write Terraform | PASS (conditional on slug) | A:22-24, A:118-121, A:127-128, A:146-148 |
| 5 | Incomplete request -> NEEDS-INPUT | PASS | A:26-29, A:48-49, A:195-202 |
| 6 | Object Storage routing | AT-RISK | A:106 omits R82/R83; A:44-45, A:182-188 |
| 7 | Pub/sub routing | AT-RISK | A:102, A:108 (R62 missing); A:80; S pubsub:168-172, :230 |
| 8 | Unverified item | FAIL (untestable) | A:18-19, A:110-111 |
| 9 | Handoff commands and write scope | AT-RISK | A:115, A:118-121, A:144-148 |

## Per-scenario notes

1. The query gives no capability slug, environment, consumers or latency SLA. A:48-49 (P0.4) says missing slug/environment returns NEEDS-INPUT and stops. A compliant response therefore plausibly returns questions, so "triggers the full P0-P6 workflow", the architecture overview and the IAM/JWT/rate-limit/CORS items would not appear. The must_not (no .tf/.java) is safe via A:22-24. The pubsub SKILL cannot supply the JWT/CLIENT_IP facts. Some facts in the api-gateway SKILL.md match JWKS/CLIENT_IP/ANONYMOUS (6 hits), so those items are reachable if the agent proceeds. Whether it proceeds is nondeterministic.
2. Same slug problem (A:48-49). A:115 restricts P6 to COMPLETE designs, but the expected behavior needs work-orders to @oci-functions-java and @oci-terraform. The agent names commands (/develop-java-function, /provision-oci-infra), not those agents. "Reads the secret at runtime via ResourcePrincipalAuthenticationDetailsProvider" depends on the vault SKILL.md, which was not verified to contain it. "Scan of .tf files and func.yaml" works (A:53-57) but there may be no such files in the run directory.
3. The expected behavior states concrete facts: shared /v1/ prefix, deployment-level JWT, ANONYMOUS webhook with signature validation, per-route rate limits. A keyword search of the api-gateway skill folder found none of /v1/, webhook, signature, or "per-route". A:6-7 forbids facts not in a skill, so a compliant agent may omit them or say they are unverified. The last item ("Asks whether a second deployment is needed") contradicts the non-interactive contract (A:26-29): it must be a numbered question with NEEDS-INPUT, and then no design is delivered.
4. Compliant behavior follows A:22-24 and the P6 table (A:127-128) and the hand-off text (A:146-148). The scenario never names a capability slug, so P0.4 may force NEEDS-INPUT. Expected item 4 says "/provision-oci-infra ... with the handoff context", which matches A:146-148. "@oci-terraform" in item 3 does not match the agent text, which only uses commands (see Finding 9).
5. A:26-29 and A:195-202 give exactly "numbered questions", "Status: NEEDS-INPUT", no files and no own OCI facts. PASS. Minor: the first bullet "classifies the domain at P0" may be undemonstrable when the query reveals no domain.
6. A:106 lists only R84/R85 for Object Storage; R82 (PAR) and R83 (versioned bucket, no lifecycle) appear only in oci-architecture-data-events-guardrails.instructions.md:48-49. A:93-94 only says the rule text "lives in" the instructions and never tells the agent to Read them; the agent has Read, Glob and Grep (A:13), but nothing makes it open them. The object-storage SKILL.md covers PAR (SKILL.md:57,64,139) but carries no R-IDs of its own (keyword search for R82/R83/R85 hit the instructions file, not the skill). Reaching "OCI-R82" by ID is therefore not guaranteed. The "[Decision] -> Recommendation" format is covered (A:67-70).
7. R89/R90/R92/R72 are listed (A:102, A:108). R62 is missing from A:93-111 (only in the instructions file, line 27). The pubsub SKILL.md covers the private-pool failure (SKILL.md:16,168,230), one-SCH-per-consumer (:104,:149), cold-start ceiling (:122-134) and fn-function (:172,:245). SKILL.md:230 says "recreate as PUBLIC", but the word "immutable" is not in this SKILL.md; the consequence the scenario expects may sit in a blueprint (never-do-patterns.md had one hit). CRITICAL -> LOW ordering is at A:80.
8. Untestable. The 6 SKILL.md files contain no "(unverified)" or "(medium confidence)" tags (search hit only the agent, the instructions, and this scenario file). The query asks the agent to review a design "where a loaded skill marks one fact as unverified". There is nothing to preserve. The expected behavior "lists every such item, with its skill name" cannot be demonstrated. The scenario also has no concrete design to review.
9. The slug func-orders is given, but no design content exists in the query. A:115 requires a COMPLETE design; "The design ... is final" gives no components, so the agent may return NEEDS-INPUT or write generic work-orders. The write-scope, draft status, createdAt, commands and removed-commands items are all driven by A:118-121, A:130-148 and pass if work-orders are written. The agent cites a work-order schema from the coordinating-oci-handoffs skill (A:119) that is not among the 6 routed skills and an optional template docs/handoff/_templates/work-order.md (A:119). Stream A also says dependsOn syntax is `none | [stream-a, stream-b]` (A:139); stream-c needs it. Unverifiable offline.

## Findings

HIGH
- H1. evaluation-scenarios.md:3-18, 21-37, 39-55 vs oci-serverless-architect.agent.md:48-49,115. Scenarios 1, 2 and 3 expect a full design/ADR from a query that lacks a capability slug, environment, and consumers, while the agent contract returns NEEDS-INPUT when such context is missing. Fix: either make the queries self-sufficient (add "capability func-stores, dev environment, consumers: web SPA, IdP: IAM Identity Domains") or add an expected_behavior alternative that accepts NEEDS-INPUT; separately relax A:48 so the slug is only required for P6 (A:117).
- H2. evaluation-scenarios.md:120-133 (Scenario 8). Untestable: no skill in the package carries an (unverified)/(medium confidence) tag, and the query has no design content. Fix: add a real tag to one skill fact (or name the specific skill + fact the scenario depends on), include a concrete API Gateway + Vault design in the query, and quote the exact tagged text in expected_behavior.

MEDIUM
- M1. oci-serverless-architect.agent.md:93-111 vs evaluation-scenarios.md:97,113. R82, R83 and R62 are asserted by scenarios 6 and 7 but are missing from the P5 list (R85/R84 and R72/R89/R90/R92 are present). Fix: add `OCI-R62`, `OCI-R82`, `OCI-R83` to the A:95-109 list, and add an explicit step "Read `instructions/oci-architecture-data-events-guardrails.instructions.md` for rule text" in P5.
- M2. evaluation-scenarios.md:46-52 (Scenario 3) states facts (/v1/, deployment-level JWT, ANONYMOUS webhook with signature check, per-route rate limits) not found in the api-gateway skill folder, while the agent may state no facts of its own (A:6-7,207). Fix: add these patterns to designing-oci-api-gateway blueprints, or reword the expected items to "per the designing-oci-api-gateway skill" and drop the ones the skill does not contain. The final item (question about a second deployment) must say "returns it as a numbered question (NEEDS-INPUT)" or be dropped.
- M3. evaluation-scenarios.md:141-147 (Scenario 9). "The design is final" without content. Fix: add a short design summary (components, slug func-orders, scope infra + java) to the query, so A:115 is satisfied.
- M4. design-oci-architecture/SKILL.md:27-34 scopes table lists only 4 scopes (full-stack, api-surface, security-model, network-topology); Scenarios 6/7 route to object-storage and event-driven pub/sub domains, which the agent supports (A:42-43) but the router does not document. Fix: add `object-storage` and `event-driven` rows to the scopes table, and update argument-hint (SKILL.md:4).

LOW
- L1. evaluation-scenarios.md:34,66 mention `@oci-functions-java` / `@oci-terraform` delegation; the agent speaks of commands `/develop-java-function` / `/provision-oci-infra` and work-order `to:` (A:127-128, A:134). Fix: reword to "work-orders targeting /develop-java-function and /provision-oci-infra".
- L2. evaluation-scenarios.md:13 "read repos" is unclear (probably "read repos in OCIR"; "virtual-network-family" is plausible but its source skill is not shown). Fix: reword and cite the skill that holds the IAM statement.
- L3. design-oci-architecture/SKILL.md:3 description says handoff "for @oci-serverless-stack" while A:127-128 says commands /provision-oci-infra and /develop-java-function; SKILL.md:18 says "ASCII component diagrams" while A:86 prefers Mermaid. Fix: align the wording.

## Format and JSON validity

- All 9 JSON blocks parse (balanced braces, quoted strings, no trailing commas). The `skills` array has 1 entry except in scenarios 6 and 7 (2 entries); consistent with the intent.
- Format is consistent across the 9 scenarios (title, json block with skills/query/expected_behavior). None has `success_criteria.must_pass[]` / `must_not[]`, which the skill-evaluator agent expects (P2); negatives are embedded as "Does NOT" bullets (scenarios 1, 2, 4, 5, 6, 7, 9). Not verified against sibling skills' scenario files; if siblings use success_criteria, add it here (LOW).
- Scenario 8 is a meta-query (instructions about a loaded skill rather than a user need), which is not a realistic user request.
- Scenario title prefixes mix "Canonical", "Edge", "Misuse", "Routing", "Handoff"; fine (>=3 scenarios satisfied).

## Caveats

Static judgment only. Blueprints for the 6 skills were not read except by keyword search, so some facts attributed to "not in the skill" may live in blueprints files the search patterns did not match; searches of SKILL.md files for R-IDs and tags returned nothing for several expected terms.
