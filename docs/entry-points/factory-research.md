# Research commands

Use these commands to collect version-pinned, source-checked knowledge about a technology, a cloud,
a methodology or a business domain. The output is a research file that you then turn into a skill
with [`/skill-creator`](factory-authoring.md).

For self-hosted platforms (databases, brokers, gateways) use [platform-software](platform-software.md)
instead. It has its own, more specific commands.

## Before you start

- A research run is slow and uses a lot of web sources. Start with the default depth and raise it
  only if the first result is thin.
- The agent builds a plan first and waits for your approval before it writes anything. Read the plan
  and reply to approve it.
- None of these commands has an output-path parameter. The agent writes the file where its own rules
  say, and the platform commands' skills name `workspace/docs/`, which the agent's rules contradict.
  Read the path the run reports at the end, and move the file where you want it. This is an open
  inconsistency in the sources, listed in the package manual.

## Commands

| Command | Use it to | Argument hint |
|---|---|---|
| [`/researching-technical-frameworks`](../../packages/factory/researching-frameworks/README.md#researching-technical-frameworks) | Research a library or framework at one exact version. | `<tech> <version> [depth] [iterations]` |
| [`/cloud-architecture-researcher`](../../packages/factory/researching-frameworks/README.md#cloud-architecture-researcher) | Research a cloud provider's architecture guidance. | `<cloud-provider> [depth] [iterations]` |
| [`/architecture-methodology-researcher`](../../packages/factory/researching-frameworks/README.md#architecture-methodology-researcher) | Research an architecture method or notation (for example C4). | `<methodology> [depth] [iterations]` |
| [`/requirements-methodology-researcher`](../../packages/factory/researching-frameworks/README.md#requirements-methodology-researcher) | Research a requirements method (for example user stories). | `<methodology> [depth] [iterations]` |
| [`/business-domain-researcher`](../../packages/factory/researching-frameworks/README.md#business-domain-researcher) | Research a business domain (for example supply chain). | `<business-domain> [depth] [iterations]` |

Depth and iterations are optional. The default is `exhaustive` with 5 iterations.

## Examples

Research a framework at a pinned version:

```
/researching-technical-frameworks FastAPI 0.115 depth=deep iterations=3
```

Research a cloud provider:

```
/cloud-architecture-researcher AWS depth=deep iterations=3
```

Research a methodology:

```
/architecture-methodology-researcher C4 depth=deep iterations=3
```

## What you get

- A file named `research_<topic>_v<version>.md`. It has the sections, sources and dates defined by
  the output-format blueprint of the skill that ran.
- Anything the agent could not confirm is tagged *unverified* in that file. Treat those tags as open
  questions.

## Next steps

1. Read the research file and check the *unverified* items.
2. Turn it into a skill: `/skill-creator workspace/research_FastAPI_v0.115.md`.
3. Validate the result: `/skill-best-practices-validator .claude/skills/`.

## Not for

- Self-hosted platforms: use [platform-software](platform-software.md).
- Writing a skill from a research file: use [factory-authoring](factory-authoring.md).
- Terraform providers: use the Terraform researchers in [terraform](terraform.md).

## Related

- Package: [`researching-frameworks`](../../packages/factory/researching-frameworks/README.md),
  [`research-core`](../../packages/factory/research-core/README.md).
- Agent: `framework-researcher` ([subagents](../agents/README.md)).
