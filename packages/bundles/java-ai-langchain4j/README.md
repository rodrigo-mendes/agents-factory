# java-ai-langchain4j

Java AI with LangChain4j: plain-Java chat and streaming on LangChain4j 1.22 (OpenAI, Anthropic) and quarkus-langchain4j on Lambda.

**Who it is for:** Java developers who add chat and streaming with LangChain4j or quarkus-langchain4j.

## Contents

<!-- BEGIN GENERATED:contents -->
**Packages included:** [`langchain4j`](../../java/libs/langchain4j/README.md), [`quarkus-langchain4j`](../../java/quarkus/quarkus-langchain4j/README.md)
**Also installed as dependencies:** [`factory-core`](../../factory/factory-core/README.md), [`quarkus-aws`](../../java/quarkus/quarkus-aws/README.md), [`quarkus-core`](../../java/quarkus/quarkus-core/README.md), [`handoff-core`](../../delivery/protocol/handoff-core/README.md), [`aws-skills`](../../cloud/provider/aws/aws-skills/README.md), [`clean-code-quarkus`](../../java/clean-code/clean-code-quarkus/README.md), [`openspec-core`](../../delivery/specs/openspec-core/README.md)

| Type | Entry point or agent | Package |
|---|---|---|
| agent | [`langchain4j-integrator`](../../java/libs/langchain4j/.apm/agents/langchain4j-integrator.agent.md) | `langchain4j` |
| agent | [`langchain4j-reviewer`](../../java/quarkus/quarkus-langchain4j/.apm/agents/langchain4j-reviewer.agent.md) | `quarkus-langchain4j` |
| agent | [`quarkus-code-reviewer`](../../java/quarkus/quarkus-aws/.apm/agents/quarkus-code-reviewer.agent.md) | `quarkus-aws` |
| agent | [`quarkus-lambda-integrator`](../../java/quarkus/quarkus-aws/.apm/agents/quarkus-lambda-integrator.agent.md) | `quarkus-aws` |
| command | [`/syncing-spec-from-code`](../../delivery/protocol/handoff-core/README.md#syncing-spec-from-code) | `handoff-core` |
| agent | [`spec-synchronizer`](../../delivery/protocol/handoff-core/.apm/agents/spec-synchronizer.agent.md) | `handoff-core` |

Plus 61 knowledge skills that Claude loads by description. Each package manual lists them.
<!-- END GENERATED:contents -->

## Installation

From the folder of the project that should receive the bundle:

```bash
apm install <path-to-agents-factory>/packages/bundles/java-ai-langchain4j --target claude
```

Add `--dry-run` to preview. APM installs the packages listed above and their dependencies into `.claude/`.

To produce the folder and zip that are sold or shared, export the bundle from this repository:

```bash
python scripts/export-bundle.py java-ai-langchain4j           # dry run
python scripts/export-bundle.py java-ai-langchain4j --apply   # writes dist/java-ai-langchain4j/ and the zip
```

The export holds the `.claude/` folder and a `docs/` folder with the usage manuals of the packages it
includes.

## Quick Start

This bundle has no commands. Ask Claude in plain language; the skills load by description.

```text
Add a StreamingChatModel wrapper for OpenAI with a StreamingChatResponseHandler in this Maven module.
Review our Anthropic ChatModel builder for hardcoded keys and request logging.
```

## Documentation

The usage manuals cover installation, quick start, usage scenarios, a command or skill reference,
agents and limits:

- [`langchain4j`](../../java/libs/langchain4j/README.md): usage manual.
- [`quarkus-langchain4j`](../../java/quarkus/quarkus-langchain4j/README.md): usage manual.

See also the [package catalog](../../../docs/packages/README.md) and the
[entry points](../../../docs/entry-points/README.md).
