# Architecture Audit — terraform-engineer + aws-terraform (P6 round 1)

Date: 2026-10-23 · Auditor: architecture-auditor (3 lenses run sequentially, no fan-out by caller instruction)
Target: `packages/terraform/.apm/agents/terraform-engineer.agent.md`, `packages/terraform/.apm/skills/provision-aws-terraform/`, `packages/aws-terraform/.apm/{instructions,skills}/`, both `apm.yml`.

## Scores

| Lens | Score | HIGH | MEDIUM | LOW |
|---|---|---|---|---|
| 1 Scope hierarchy | 7.0 | 1 | 2 | 1 |
| 2 Invocation flow | 8.0 | 0 | 2 | 2 |
| 3 Engine mechanics | 7.5 | 1 | 2 | 1 |
| **Overall** | **7.5 — PASS WITH CHANGES** | 2 | 6 | 4 |

Objective checks (P5): 26 skill dirs `provisioning-aws-*-v6` (ls); 26 rows in agent table (lines 62-87) and command table (lines 32-57) — match; 3 instruction files, all with `applyTo`; all 26 SKILL.md 123-209 lines (< 500); description lengths 247-313 chars (sum ~7.3k chars); every SKILL.md carries `(unverified)` tags (4-14 each); `.claude/skills/` currently contains 0 `provisioning-aws-*` (not yet regenerated).

## Lens 1 — Scope hierarchy (7.0)

- **HIGH S1** `packages/terraform/apm.yml:11` — the researcher/author package `terraform` (research + `terraform-instructions-compiler`, depends on `research-core`, `artifact-authoring`) now depends on the runtime knowledge package `aws-terraform`. No cycle (aws-terraform → factory-core only), but the dependency direction mixes the factory layer (produces artifacts) with the consumer layer (executes them): installing the Terraform research tools now drags 26 AWS skills + 3 `**/*.tf` rules into every consumer, and a consumer of the executor drags research-core + artifact-authoring. Other executors live in their own package (`camel-quarkus-integrator`, `stripe-java`). Remediation: move `terraform-engineer` + `provision-aws-terraform` into `packages/aws-terraform` (or a new `aws-terraform-engineer` package depending on `aws-terraform`), revert `terraform/apm.yml` to v1.1 deps, and add the new package to root `apm.yml`.
- **MEDIUM S2** `aws-terraform/.apm/instructions/*.instructions.md` — `applyTo: "**/*.tf,**/*.tfvars,**/*.hcl"` is used by two rules with near-identical globs; `project-config` (line 4) should be scoped to `versions.tf`, `backend*.tf`, `providers.tf`, `.terraform.lock.hcl` as its description says; `skills-management` (`**/*.tf`) fires on every .tf read. Also `**/*.hcl` matches non-Terraform HCL (Packer, Nomad). Narrow globs.
- **MEDIUM S3** `CLAUDE.md` routing/structure tables and counts (51 commands, 21 agents, 79 skills, 8 rules, 13 packages) do not list `terraform-engineer`, `/provision-aws-terraform`, `aws-terraform`. Update after regenerating `.claude/`.
- **LOW S4** Naming compliant: knowledge skills `provisioning-aws-<svc>-v6` (gerund-noun), command `provision-aws-terraform` (action-noun), agent `terraform-engineer` (domain-role). Minor: agent is AWS-only but name is cloud-neutral; consider `aws-terraform-engineer` to avoid collision with a future OCI/other executor (workspace has `oci-terraform` packages).

## Lens 2 — Invocation flow (8.0)

Chain: `/provision-aws-terraform` (`context: fork`, `agent: terraform-engineer`, `disable-model-invocation: true`, SKILL.md:5-7) → agent (non-interactive, returns questions, workflow 1-7) → reads `.claude/skills/provisioning-aws-<svc>-v6/SKILL.md` (agent:37). Complete, acyclic, depth 1, no Agent tool → no nested spawning. `model: sonnet` declared (agent:14). Report format with DONE/NEEDS-INPUT/PARTIAL is a clear handoff.

- **MEDIUM F1** agent:13 `Bash` is unbounded at the tool level; the allowlist (agent:46-50) and Never-Do (agent:107-109) are prompt-only. Recommend a `PreToolUse` hook or settings permission rules (`Bash(terraform fmt*)`, `Bash(terraform init -backend=false*)`, `Bash(terraform validate*)`, `Bash(terraform test*)`, deny `terraform apply|destroy|import|state *`, `aws *`). Also `terraform test` with `command = plan` and a real (non-mock) provider would hit credentials — require `mock_provider` explicitly or deny when AWS env credentials are present.
- **MEDIUM F2** agent:28,44 — Write/Edit not bounded to the target path; add an explicit Never-Do "write outside the given target directory" (camel/stripe executors have the same gap, so fix in all three).
- **LOW F3** agent:48 `terraform init -backend=false` needs registry network access; agent already handles "cannot run" — fine; mention `-input=false` and `TF_IN_AUTOMATION` to avoid prompts.
- **LOW F4** The 26-row routing table is duplicated in agent and command (two maintenance points; drift risk). Keep it in the agent only and link from the command, or generate both.

## Lens 3 — Engine mechanics (7.5)

- **HIGH E1** None of the 26 knowledge skills sets `disable-model-invocation` or `user-invocable: false`, and all are auto-invocable: ~7.3k chars of near-identical descriptions ("Provisions AWS X with Terraform (hashicorp/aws 6.x, Terraform ~> 1.16)...") are listed in every session of any project installing the package, including the factory repo itself (via `terraform` dependency, see S1). CLAUDE.md asks auto-listed descriptions to be short and specific. The agent loads skills by explicit `Read` path, so auto-invocation is not required for the executor. Remediation: either (a) keep auto-invocation but cut each description to ≤ ~160 chars with the service noun first ("S3 buckets in Terraform aws 6.x: ..."), dropping the repeated version boilerplate, or (b) set `disable-model-invocation: true` on the 26 skills if only the executor should use them (then they cost nothing in context). Decide explicitly (Ask First for the package owner).
- **MEDIUM E2** "Not for" disambiguation is present in all 26 but inconsistent (some cite sibling skill names, some only service names; SAM lists `-api-gateway-v6` shorthand). Collision risk pairs: lambda/sam, waf/shield, cloudwatch/xray, secrets-manager/parameter-store, cloudfront/acm/route53. Normalize to "Not for <svc> (provisioning-aws-<svc>-v6)".
- **MEDIUM E3** Version-lock text varies: `hashicorp/aws 6.x, Terraform ~> 1.16` vs `aws 6.x, TF ~> 1.16` vs `~> 1.16` (dynamodb, organizations, shield, step-functions, acm, s3, waf, cost-management descriptions). Suffix `-v6` is consistent in all 26 names. Normalize wording.
- **LOW E4** Safety and anti-hallucination mechanics are good: agent Never-Do (apply/destroy/import/state/plan with creds), "facts only from skills", `(unverified)`/`(medium confidence)` surfaced not used (agent:22-24, 99, 113), Ask-First returned as questions (agent:40-41); skills carry dated sources and `unverified-and-risks.md` blueprints. Minor: agent:97-98 hard-codes `~> 6.69` — a second copy of a skill fact, contrary to its own "no second mapping of facts" (agent:39); reference "the constraint the skill prescribes" instead.

## Consensus matrix

| Finding | Scope | Flow | Engine | Confidence |
|---|---|---|---|---|
| S1 package placement / dependency direction | X | | X (context bloat in factory) | High |
| E1 auto-listing cost of 26 descriptions | X | | X | High |
| F1 Bash unbounded | | X | X (safety) | High |
| S2 broad applyTo | X | | X | High |
| F4/E4 duplicated facts/tables | | X | X | High |
| F2, S3, S4, E2, E3, F3 | single lens | | | Medium |

## Prioritized remediation

1. (S1) Move executor + command out of `packages/terraform` into an AWS executor package; revert `terraform/apm.yml` deps.
2. (E1) Decide auto-invocation policy; shorten descriptions or set `disable-model-invocation: true` on the 26 skills.
3. (F1/F2) Add permission rules/hook bounding Bash to the 4 offline commands and Write/Edit to the target dir.
4. (S2) Narrow `applyTo` globs per instruction.
5. (E2/E3) Normalize "Not for" and version wording across 26 descriptions.
6. (F4/E4) Single source for routing table and version constraints.
7. (S3) Run `apm install --target claude`, then update CLAUDE.md counts/tables.
