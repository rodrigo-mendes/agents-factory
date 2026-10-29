# Family rules — quarkus-aws-saas

Inherited: `.claude/skills/building-agent-packages/blueprints/policy/evidence-rule.md`,
`tag-notation-and-registers.md`, `hybrid-format-checklist.md`, and the Quarkus rules in
`workspace/_family_rules_v3.40.md` (Camel Quarkus family).

Domain decisions for this family:

1. Version-locked skills target **Quarkus 3.40.x LTS** only; Quarkus 4 / Quarkiverse 4.0.0.Beta* content is rejected as misinformation.
2. Quarkiverse amazon-services content targets **3.23.x**; any claim tied to another line is tagged or dropped.
3. **JVM + SnapStart vs native** is always presented as an Ask-First / ADR decision, never a default (they are mutually exclusive).
4. Every code example uses `function.zip` produced by the Quarkus build; IaC examples defer to `provisioning-aws-*-v6` (Terraform), never SAM/CDK.
5. Secrets (Stripe keys, LLM API keys) always come from Secrets Manager/SSM; Bedrock uses the Lambda IAM role.
6. Multi-tenant isolation (tenant from token, never from path alone) is a 🚫 when violated.
7. Observability: log JSON with `requestId`/`tenantId`, no PII; metric dimensions bounded (no unbounded tenant cardinality without an ADR).
8. Skills state no facts outside their research file; frontmatter names follow `.claude/rules/skill-frontmatter.md`.

Decisions revealed by the U1 pilot (2026-10-28):

9. A Never Do ✅ alternative may only name options that are High; unverified/medium options go to the Ask-First item it points to.
10. Defaults are stated per key; never group a key whose default is "page not recorded" under a shared default.
11. "Default" means the documented default value of a config key; an image or value that only appears in examples is called "the guide's example".
12. Reference blueprints over 100 lines start with a Contents list; SKILL.md Quick Navigation links the Verification Loop.

Decided in P6 round 1 (2026-10-28):

13. A claim from a partly read page, a tool summary or a main-branch (not tag-pinned) source is High only when a verbatim quote of it is recorded in the research or the skill; otherwise it is (medium confidence). The same claim carries the same tag in every skill of the family.
14. Handoff records use the protocol vocabulary only: report-family outcomes (report, deploy-report, diagnosis-report) `success | partial | failed | needs-input`, verify outcomes `pass | fail`; section names follow the profile's `required_sections`. Agents do not invent their own outcome words.
15. E7 acceptance: `aws-observability` produces (result-NN-observability.md, kind report); `aws-lambda-debugger` mode B verifies (verify-E7.md, kind verify, role debug). The profile's final-gate rule keys on the debug-role verify.
