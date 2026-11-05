# Authoring commands

These commands create new factory artifacts: skills, subagents, methodology skills and whole agent
packages. Each one reads a source (usually a research file) and writes files, so check the output
before you commit it.

## Commands

| Command | Use it to | Argument hint |
|---|---|---|
| [`/skill-creator`](../../packages/factory/artifact-authoring/README.md#skill-creator) | Create a skill from a research file. | `<path to research file>` |
| [`/agent-creator`](../../packages/factory/artifact-authoring/README.md#agent-creator) | Create a subagent for a domain role. | `<domain-role> [advisory\|orchestrator]` |
| [`/methodologies-skill-generator`](../../packages/factory/artifact-authoring/README.md#methodologies-skill-generator) | Research and create a methodology skill in one step. | `<methodology>` |
| [`/architecture-approaches-skill-generator`](../../packages/factory/artifact-authoring/README.md#architecture-approaches-skill-generator) | Research and create an architecture-approach skill in one step. | `<approach>` |
| [`/building-agent-packages`](../../packages/factory/agent-package-builder/README.md#building-agent-packages) | Orchestrate a full package: research, skills, agent, rules, quality loop and commit plan. Runs inline. | (none; it asks) |

## Examples

Turn a research file into a skill:

```
/skill-creator workspace/research_FastAPI_v0.115.md
```

Create an advisory subagent:

```
/agent-creator terraform-reviewer advisory
```

Create a methodology skill without a separate research step:

```
/methodologies-skill-generator TDD
```

Build a full package, step by step, with your approval at each gate:

```
/building-agent-packages
```

## Which one to use

- You already have a research file: `/skill-creator`.
- You need a new agent and no skill: `/agent-creator`.
- You want a methodology or an approach and have no research yet: the `-generator` commands.
- You want the whole chain from a brief to a committed package: `/building-agent-packages`.

## Rules to remember

- `/skill-creator` stops if the research file is missing or unreadable. It never writes from memory.
- If the research file has no complexity field, the skill asks you how many tiers to use before it
  writes anything.
- The generated files are only source. After you add them under `packages/`, regenerate `.claude/`
  (see [Maintaining the docs](../reference/maintaining-docs.md)).

## Next steps

1. Validate the skill: `/skill-best-practices-validator .claude/skills/`.
2. Check its behavior: `/evaluating-skill-scenarios <skill-name>` (see [harness-quality](harness-quality.md)).

## Related

- Package: [`artifact-authoring`](../../packages/factory/artifact-authoring/README.md).
- Agent: `artifact-author` ([subagents](../agents/README.md)).
- Orchestrator package: [`agent-package-builder`](../../packages/factory/agent-package-builder/README.md).
- Terraform rule compiler: [`/terraform-instructions-compiler`](terraform.md).
