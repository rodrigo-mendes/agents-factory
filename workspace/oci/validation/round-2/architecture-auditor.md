# Architecture audit round 2 - oci-architecture (single lens)

A = packages/oci-architecture/.apm/agents/oci-serverless-architect.agent.md
R = .apm/skills/design-oci-architecture/SKILL.md
S = .apm/skills/design-oci-architecture/blueprints/evaluation-scenarios.md
README = packages/oci-architecture/README.md
(.claude/ regeneration and the 6 knowledge skills' content are ignored, per brief.)

## Round-1 findings

| Finding | Status | Evidence |
|---|---|---|
| ARCH H1 stale `_templates` path, coordinating-oci-handoffs not loaded | RESOLVED | A:123-127 loads `coordinating-oci-handoffs`, uses `assets/work-order.template.md` + `blueprints/handoff-protocol.md`; `_templates` gone. Both files exist in packages/oci-core. |
| ARCH H2 `status: draft` outside protocol enum | RESOLVED | A:145 and A:150 use `pending`. handoff-protocol.md:56 and :337 define pending, in-progress, completed. oci-serverless-stack.agent.md:153,169 only sets `completed`, so there is no branching on `draft`/`pending`. |
| ARCH H3 conflicting handoff paths | RESOLVED | One-path wording is consistent in A:153-157, R:3 and R:19, README:69-72 and :84-89, S Scenarios 4 and 9. All say run ONE path (stack one-shot OR per-stream), never both. |
| ARCH M4 write scope prompt-only, no slug sanitisation | RESOLVED (documented limit) | A:119-122 sanitises `[a-z0-9-]+` and rejects `/`, `\`, `..`. README:74-75 states the scope is prompt-enforced. |
| ARCH M6 router scopes incomplete | RESOLVED | R:4 argument-hint and R:29-36 list all 6 scopes. |
| ARCH M7 ASCII vs Mermaid, `@oci-serverless-stack` wording | RESOLVED | R:18 "Mermaid preferred, ASCII fallback". R:3 now names the commands. |
| ARCH M8 slug ask-path | RESOLVED | R:4 `[capability-slug]`, R:38, A:49 and A:119-121. |
| ARCH 9 createdAt `<pending>` | RESOLVED | A:127 explains it (no Bash). S Scenario 9 covers it. |
| ARCH L10 hardcoded `infra/modules/*` in P1 | OPEN (LOW) | A:53 and A:60-61 are unchanged. |
| ARCH L11 A should cite both instruction files | RESOLVED | A:93-94 names both instructions. |
| ARCH 12 applyTo -> paths | Deferred to P8 | Both instructions have `applyTo` at line 4. Check the generated `.claude/rules/*` has `paths:`. |
| ARCH 13 oci-terraform / oci-functions-java not in apm.yml deps | OPEN (informational) | README:92-103 unchanged. I did not re-read apm.yml. Only matters for the stack path. |
| QV M1 template path / `command:` / `draft` | RESOLVED | Frontmatter at A:136-148 has no `command`; the command is in the body (A:149); status is `pending`. |
| QV M2 README workflow conflict | RESOLVED | README:84-89 offers (a) one-shot or (b) per-stream, never both. |
| QV M3 P5 points to the wrong instruction | RESOLVED | A:93-94 names both instructions. |
| QV M4 routing scenarios for networking / vault | OPEN (LOW) | Only Scenarios 6 and 7 are routing scenarios. S:120-133 touches api-gateway and vault, but only as a no-tags check. |
| QV L1/L2/L3 Mermaid, scopes, legacy `@` handles | RESOLVED | R:18, R:29-36. S Scenarios 2 and 4 use `to:` fields and commands. |
| QV L4 vague Scenario 8 | RESOLVED | S:120-133 is now concrete. It names the two skills and asserts none are tagged. I grepped designing-oci-api-gateway and designing-oci-vault-security: 0 occurrences of `(unverified)` / `(medium confidence)`. The scenario holds. |
| QV L5/L6 provenance, applyTo | L5 unchanged and acceptable; L6 deferred to P8 | - |
| QV L7 write scope undocumented | RESOLVED | README:74-75. |
| SE H1 Scenarios 1-3 lacked slug/env/consumers vs NEEDS-INPUT | RESOLVED | The S queries at lines 8, 26, 44, 62 supply slug, environment and consumers. A:48-49 now requires the slug only for P6. |
| SE H2 / L4 Scenario 8 untestable | RESOLVED | See QV L4. |
| SE M1 R82/R83/R62 missing from P5 | RESOLVED | A:96 (R62), A:107 (R82/R83). Both IDs exist in the data-events instructions (R62 at :27, R82 at :48, R83 at :49). R72, R89-R92 are also listed. |
| SE M2 Scenario 3 facts not in the skill | RESOLVED (mostly) | S:47-52 now cites the skill and the poc-worked-examples blueprint, and drops the second-deployment question. The api-gateway skill folder has 22 hits for `/v1/`, webhook, per-route and signature. |
| SE M3 Scenario 9 had no design content | RESOLVED | S:140 includes a design summary. |
| SE M4 router scopes | RESOLVED | See ARCH M6. |
| SE L1 legacy handles | RESOLVED | See QV L1. |
| SE L2 "read repos" | OPEN (cosmetic) | S:13 is unchanged. The IAM statement has no cited skill. |
| SE L3 SKILL.md wording | RESOLVED | See ARCH M7. |
| SE "scenarios lack must_pass / must_not" | OPEN (LOW) | S uses `expected_behavior` only, with "Does NOT" bullets. Check what sibling skills use. |
| Scenario 7 "immutable" consequence | RESOLVED | The word is in designing-oci-event-driven-pubsub/blueprints/ask-first-decisions.md:40 and never-do-patterns.md:31. |

## Checks on the new contradictions

- pending vs coordinating-oci-handoffs: consistent. `status: pending` is the protocol's initial value.
- One-path wording: consistent across A, R, README and S (Scenarios 4 and 9).
- Slug rule: consistent. R:38 and README:73 say `[a-z0-9-]+`; A:119-122 adds the sanitisation. No conflict.
- R62, R82 and R83 exist in the data-events instructions (lines 27, 48, 49). The README split at README:50-51 is correct.
- Scenarios JSON: all 9 blocks are well formed (balanced, quoted, no trailing commas). S1-S9 supply a slug, environment and consumers, so none collide with the NEEDS-INPUT rule. S5 intentionally triggers it.

## New findings

### MEDIUM
N1. A:117-121 vs A:26-29: status semantics for "design without slug". A:117 says P6 runs only on `Status: COMPLETE` with no open questions. A:120-121 says a design without a slug "still gets a design" plus a slug question and `NEEDS-INPUT for the handoff`. A:26-29 says NEEDS-INPUT means "stop, write no files", which reads as withholding the design. A caller cannot tell whether the design is delivered. No scenario covers a design request without a slug.
Fix: in A:26-29, add "except when only the capability slug is missing: deliver P0-P5, then end with `Status: NEEDS-INPUT` and the slug question; write no work-orders". Add Scenario 10 (a valid design query with no slug; expect a design and a slug question, no files).

### LOW
N2. A:141 `to: "<target agent>"` is undefined, while S Scenario 2 line 34 and Scenario 4 line 66 expect it to name the executor agents. The P6 table (A:130-134) has only commands.
Fix: in the table, map stream-a to `@oci-functions-java` and stream-b/c to `@oci-terraform`, or state "to: = the agent behind the command".

N3. A:144 gives `dependsOn: none | [stream-a, stream-b]` without saying which stream takes which value.
Fix: add "stream-a, stream-b: `none`; stream-c: `[stream-a, stream-b]`".

N4. A:93-94 says the rule text "lives in" the instructions but never tells the agent to Read them. S Scenario 6 relies on OCI-R82/R83, and the object-storage skill has no R-IDs of its own.
Fix: in P5 add "Read both instruction files by Glob (`**/oci-architecture-*guardrails.instructions.md`) when citing a rule ID; if absent, cite the skill rule only".

N5. Not re-verified: README:101-103 says `provisioning-oci-*` skills live in `oci-core`. I did not check this, so the claim is not confirmed.

## Verdict
No HIGH findings. 1 MEDIUM (N1) and 4 LOW findings are new, and 3 LOW findings from round 1 remain open (P1 module paths, no routing scenarios for networking and vault, no `must_pass` / `must_not`). Every round-1 HIGH and MEDIUM is RESOLVED.
