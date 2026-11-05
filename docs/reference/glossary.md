# Glossary

Terms used across the documentation, in alphabetical order.

| Term | Meaning |
|---|---|
| **ADR** | Architecture decision record. A short file that records one decision, the alternatives and the sources. |
| **Advisory agent** | A subagent that produces designs, decision records and plans, but no code. |
| **Always do / Ask first / Never do** | The three tiers (✅ ⚠️ 🚫) used in every skill. See [Conventions](conventions.md#three-tiers). |
| **APM** | The package manager that builds `.claude/` from `packages/`. You run `apm install --target claude`. |
| **Ask first** | A decision that needs your approval before the agent goes on. |
| **Asset** | A file kept in a skill's `assets/` folder, such as a template. |
| **Blueprint** | A file in a skill's `blueprints/` folder that holds the long detail so `SKILL.md` stays short. |
| **Bundle** | A sales meta-package. It has only an `apm.yml` that lists packages. It is not counted as a package. |
| **Command** | A skill you start with `/name`. It runs in a fresh context and routes to one subagent. |
| **Compiler** | A command that turns a research file into a skill or rules. |
| **Consensus audit** | An audit that runs three lenses in parallel and ranks findings by how many lenses agree. |
| **Dead end** | A reference that points to something that does not exist, such as `agent: x` with no `x` file. |
| **Drift** | A difference between the spec and the code. A script detects it and the flow turns it into a spec-delta. |
| **Entry point** | Something you start yourself: a command or an inline orchestrator. |
| **Fan-out depth** | How many levels of subagents start other subagents. The standard here is 1. |
| **Fork** | Running a command in a separate context (`context: fork`). |
| **Frontmatter** | The header at the top of a skill, subagent or rule file. See the [cheatsheet](frontmatter-cheatsheet.md). |
| **Gate** | A point where the flow stops and waits for your decision. |
| **Handoff record** | A file one agent writes for another: a work-order, a result, a review or a verify record. |
| **Hybrid knowledge skill** | A knowledge skill with a short `SKILL.md` and a `blueprints/` folder. |
| **Inline orchestrator** | An entry point that runs in your session, asks you questions and starts workers. |
| **Knowledge skill** | A skill Claude loads when your request matches its description. You do not type a command. |
| **Needs-input** | The outcome of a non-interactive worker that lacks information. It returns numbered questions instead of guessing. |
| **Non-interactive** | A subagent that cannot ask you questions. It returns questions to its caller. |
| **OpenSpec** | The specification format and tool used for specs and changes. The factory pins version 1.15. |
| **Orchestrator** | An agent or skill that coordinates other workers and holds the workflow and gates. |
| **Orphan** | A component that nothing else references. |
| **P0 to P5** | The six-phase workflow: verify docs, analyze, consult, propose, implement, validate. |
| **Progressive disclosure** | Showing the basics first and the detail on demand. `SKILL.md` stays under 500 lines. |
| **Reachability** | Whether a component can be reached through an invocation chain from some entry point. |
| **Research file** | The output of a research command: `research_<topic>_v<version>.md`, with sources and *unverified* tags. |
| **Review record** | A handoff record in which a reviewer judges one task. |
| **Rule** | A file with a `paths:` list. It joins the context when Claude works on a matching file. |
| **Routing table** | A rule that maps keywords to the skill to load. |
| **Scenario** | One test case in a skill's `evaluation-scenarios.md`, with a query, must-pass and must-not criteria. |
| **Skill** | A folder with a `SKILL.md`. It is a command, an inline orchestrator or a knowledge skill. |
| **Source hierarchy** | The order of accepted sources: official first, then blog, examples, verified community. |
| **Spec-delta** | A proposed change to a spec, written when code drifted from it. |
| **Subagent** | A worker defined in `.claude/agents/` with its own tools and model. |
| **Tracker** | The optional GitHub Project that mirrors an OpenSpec change. Off by default. |
| **Unverified** | A tag on a claim with no dated official source. |
| **Validator** | A command that checks an artifact against the conventions. It reports and does not change files. |
| **Verify record** | A handoff record in which a verifier passes or fails a phase. |
| **Version absolutism** | One skill is one version. A new version is a new skill. |
| **Version lock** | A skill's pin to an exact version, written in its name, such as `-v3-40`. |
| **Work-order** | A handoff record that tells a worker exactly what to do and what to read. |

## Copilot terms

These apply only when you audit another project that targets GitHub Copilot, using the
`audit-architecture-*` and `copilot-compatibility-review` commands:

| Term | Meaning |
|---|---|
| **L0 to L4** | The Copilot hierarchy: settings, instructions, skills, agents, prompts. |
| **G0 to G4** | The Claude Code hierarchy: `CLAUDE.md`, agents, rules, command skills, meta-skills. |
| **`.instructions.md`** | The Copilot file that rules replace in Claude Code. |
