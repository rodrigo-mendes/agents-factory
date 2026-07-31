# Glossary

Terms of the Agents Factory framework.

---

## General Terms

| Term | Definition |
|-------|-----------|
| **Agent / Agente** | Artifact (`.agent.md` in Copilot, `.claude/agents/*.md` in CC) that defines an orchestrator with the P0-P5 workflow. Loads skills and generates/reviews code. |
| **Agent Router Pattern** | Separation pattern: entry-point → agent (orchestration) → skills (knowledge) → rules/instructions (config). See [Conventions](convencoes.md#agent-router-pattern). |
| **Advisory Agent** | Type of agent that produces designs, ADRs and delegation plans but does NOT generate code. P4 = "Deliver", not "Implement". |
| **Always Do (✅)** | Tier 1 of the three-tier: mandatory pattern that the agent executes automatically without asking. Must have functional code. |
| **Ask First (⚠️)** | Tier 2 of the three-tier: architectural decision that requires user approval before proceeding. Requires a trade-off table. |
| **Blueprint** | Auxiliary file in `blueprints/` that expands skill patterns with complete code. Allows SKILL.md < 500 lines. |
| **Compiler** | Prompt/skill that transforms a research document into an operational artifact (SKILL.md or .instructions.md). |
| **Consensus Audit** | Audit that runs 3 lenses in parallel (scope + flow + engine) and prioritizes findings by agreement: 3/3 🔴, 2/3 🟡, 1/3 🟢. |
| **Cross-domain** | Implementation that involves multiple technical domains (e.g. Java + Terraform) with mutual dependencies. Requires an Orchestrator Agent. |
| **Dead-end** | Component that is referenced but does not exist, or incomplete invocation chain (e.g. `agent: x` but `.claude/agents/x.md` does not exist). |
| **Delegation** | When an advisory agent instructs the user to use another agent for implementation. |
| **Entry-point** | `.prompt.md` (Copilot) or skill command `context: fork` (CC) — user entry-point for a flow. |
| **Fan-out depth** | Number of levels of nested sub-agents. The standard for this project is 1: command → sub-agent → output. |
| **Generator** | Synonym for Compiler. Skill that generates artifacts from research. |
| **G0→G4** | Responsibility hierarchy of a Claude Code project: G0 CLAUDE.md → G1 agents → G2 rules → G3 skills-fork → G4 meta-skills. CC equivalent of Copilot's L0→L4. |
| **Implementation Agent** | Type of agent that follows the full P0-P5 and generates/modifies code. |
| **Instruction** | Artifact `.instructions.md` (Copilot) with project-wide configuration (setup, standards, routing). CC equivalent: `.claude/rules/*.md`. |
| **L0→L4** | Responsibility hierarchy of a GitHub Copilot project: L0 settings → L1 instructions → L2 skills → L3 agents → L4 prompts. |
| **Meta-skill** | Self-invocable skill (without `context: fork` and without `disable-model-invocation`) that defines base framework patterns. Loaded by the sub-agent in P0. E.g. `researching-technical-frameworks`. |
| **Never Do (🚫)** | Tier 3 of the three-tier: anti-pattern that the agent automatically blocks, offering an inline alternative and impact. |
| **Orchestrator Agent** | Type of agent that coordinates implementation across multiple domains with dependency ordering. |
| **Orphan** | Component that exists in the project but is not referenced by any other component. |
| **P0-P5** | Mandatory 6-phase workflow: P0 Verify Docs → P1 Analyze → P2 Consult → P3 Propose → P4 Implement → P5 Validate. |
| **Progressive Disclosure** | Principle of presenting basic information first, advanced details later. SKILL.md ≤ 500 lines; overflow to `blueprints/`. |
| **Prompt** | Artifact `.prompt.md` (Copilot) that serves as the user entry-point. CC equivalent: skill command with `context: fork`. |
| **Reachability** | Property of a component being reachable through the invocation chain from some entry-point. |
| **Researcher** | Skill/prompt that researches technology/methodology following `researching-technical-frameworks`. Produces `research_<Tech>_v<Version>.md`. |
| **Rule** | Artifact `.claude/rules/*.md` with `paths:` field that is automatically injected when the corresponding files are in context. CC equivalent of `.instructions.md`. |
| **Routing Table** | File `{domain}-skills.md` in `.claude/rules/` (CC) or `.skills.instructions.md` (Copilot) — maps keywords → skills to load. |
| **Scaffolding** | Generation of file structure from templates (e.g. `skill-creator` generates SKILL.md + blueprints from research). |
| **Skill** | Artifact `SKILL.md` with versioned knowledge base and three-tier patterns (✅⚠️🚫). |
| **Source Hierarchy** | Hierarchy of accepted sources: official/registry > official blog > official examples > community <12 months > reject the rest. |
| **Subagente** | Agent defined in `.claude/agents/` that receives a fork from a skill command via `context: fork`. Runs in an isolated context. |
| **Template** | File `TEMPLATE.*.md` in `.claude/templates/` or `.github/templates/` — template for creating new artifacts. |
| **Three-Tier** | Guardrail architecture in 3 layers: ✅ Always Do, ⚠️ Ask First, 🚫 Never Do. Mandatory in every SKILL.md. |
| **Validator** | Skill that verifies artifact quality against defined standards. Never modifies files by default. |
| **Version Absolutism** | Principle: one skill = one specific version. Old versions = misinformation. Separate research files per version. |

---

## YAML Terms — Claude Code

| YAML Field | Context | Description |
|-----------|----------|-----------|
| `context: fork` | Skills command (G3) | Instructs the CC engine to spawn an isolated sub-agent when this skill is invoked |
| `disable-model-invocation: true` | Skills command (G3) | Prevents auto-listing of the skill in the context budget. Mandatory in all 24 operational commands |
| `allowed-tools:` | Skills (`.claude/skills/`) | List of tools available to the skill. Never use `tools:` in a skill |
| `tools:` | Sub-agents (`.claude/agents/`) | List of tools available to the sub-agent. Never use `allowed-tools:` in an agent |
| `paths:` | Rules (`.claude/rules/`) | File glob that automatically activates the rule when the corresponding files are in context |
| `agent:` | Skills command (G3) | Name of the sub-agent to invoke in the fork (e.g. `agent: framework-researcher`) |
| `argument-hint:` | Skills command (G3) | Input suggestion displayed to the user when the command is invoked |
