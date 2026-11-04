# Quality validation, oci-architecture, P6 round 1

Scope: oci-serverless-architect agent, 2 instructions, design-oci-architecture skill + evaluation-scenarios, README.
Reference: packages/aws-architect/. Rules: skill-frontmatter, rules-frontmatter, naming-conventions.

## Verified OK
- Frontmatter of design-oci-architecture is valid (name matches folder, "Use when", context: fork + disable-model-invocation + agent paired, argument-hint quoted).
- The 6 routed skills have SKILL.md under packages/oci-architecture/.apm/skills/. Both handoff commands exist (provision-oci-infra in oci-terraform, develop-java-function in oci-functions-java).
- No workspace/ paths in the agent or the instructions. Each rule cites an ID and its source skill abbreviation, with no skill-body duplication.
- Rule-ID coverage: the two instructions together cover R34-R115 with no gap and no overlap. Always R34-R64 (31), Never R65-R92 (28), Ask First R93-R115 (23). This matches README and _family_rules_v2026.md. Always/Never/Ask-First classification and skill attributions match the family file for the rows checked.
- Agent: no own-facts clause, tag preservation, NEEDS-INPUT contract (writes no files), and Status line are all present. tools: Read, Grep, Glob, Write is consistent with the "write only docs/handoff/<capability>/" claim in the agent text.
- Evaluation scenarios cover the canonical, edge, misuse, routing, NEEDS-INPUT, tag and handoff cases.

## HIGH
None.

## MEDIUM

M1. Work-order schema diverges from the shared template.
- oci-serverless-architect.agent.md:118-121 and 130-143 point to `docs/handoff/_templates/work-order.md`. That file does not exist; the real template is `packages/oci-core/.apm/skills/coordinating-oci-handoffs/assets/work-order.template.md`.
- The agent's frontmatter adds `command:` and uses `status: draft`; the template has no `command` and uses `status: pending`.
- Fix: replace the path with the skill's `assets/work-order.template.md`. Either use `status: pending` or document `draft` in coordinating-oci-handoffs. Confirm oci-serverless-stack does not branch on `status: pending`.

M2. Typical workflow in README conflicts with the agent's handoff.
- README.md:72-82 sends users to `/provision-oci-serverless-stack`. Agent lines 146-148 and evaluation scenarios 4 and 9 send them to `/provision-oci-infra` and `/develop-java-function`.
- The two paths are not reconciled. oci-serverless-stack.agent.md:194 ends with `/deploy-function`.
- Fix: in README, state both paths (stack orchestrator vs direct commands). Optionally have the agent mention `/provision-oci-serverless-stack` as the combined option.

M3. P5 points to the wrong instruction for part of the rule text.
- Agent lines 93-109: "the rule text lives in the `oci-architecture-guardrails` instructions". R72 and R84-R92 live in `oci-architecture-data-events-guardrails`.
- Fix: say "in the two `oci-architecture-*guardrails` instructions".

M4. Evaluation scenarios do not cover all 6 routed skills.
- Only object-storage (scenario 6) and pubsub (scenario 7) get routing scenarios. networking, vault and api-gateway are used incidentally. Skill-routing behaviour is the agent's core claim.
- Fix: add a routing scenario for `designing-oci-networking` (R78/R79/R80) and one for `designing-oci-vault-security` (R86-R88).

## LOW

L1. SKILL.md:18 says "ASCII component diagrams". Agent lines 85-86 and 216 say "Mermaid preferred, ASCII acceptable". Align SKILL.md.

L2. SKILL.md:29-34 Scopes table lists only 4 scopes (full-stack, api-surface, security-model, network-topology). The agent also handles Object Storage and event-driven pub/sub. Add `object-storage` and `event-driven` rows, or state that other domains are inferred from free text.

L3. Evaluation scenarios 2 (line 34) and 4 (line 66) use legacy agent handles `@oci-functions-java` / `@oci-terraform` for delegation. Scenario 9 and the agent use the commands. Use the commands (`/develop-java-function`, `/provision-oci-infra`) for consistency.

L4. Scenario 8 (line 124) has a vague query: "a loaded skill marks one of the facts as (unverified)". It is not reproducible against a concrete skill. Name a concrete skill and the tagged fact.

L5. oci-architecture-guardrails.instructions.md:9-13 and the data-events file say "OCI family rules (Architecture Rules section)" without the source file. The aws-architect baseline cites `workspace/aws/_family_rules_v2026.md` as provenance. The no-workspace-path requirement is met, but README.md:58 is the only provenance pointer. Acceptable; optionally add "provenance: see package README".

L6. The `applyTo:` key is used in the instructions, matching aws-architect. It is the APM instructions schema, which compiles to `paths:` in `.claude/rules/`. Confirm the generated rule has `paths:` after `apm install` (rules-frontmatter requires it).

L7. Write is scoped to docs/handoff/<capability>/ by prompt only. aws-architect has no Write. This is acceptable but unenforced. Document it as a known limitation in README Agent Constraints, or add a PreToolUse path guard.

## Counts verified
grep of family rules R34-R115: Always 31, Never 28, Ask First 23 match README.md:59-60.
