---
name: langchain4j-code-standards
description: "LangChain4j 1.22.0 code standards for plain-Java chat and streaming (ChatModel / StreamingChatModel) with OpenAI and Anthropic: secrets, logging, model IDs, errors, thinking and reasoning parameters. Use when editing or reviewing Java files that import dev.langchain4j."
paths:
  - "**/src/main/java/**/*.java"
  - "**/src/test/java/**/*.java"
---

# LangChain4j code standards (1.22.0)

Technical facts live in the three knowledge skills named below. This rule states what to check
and where to look; it does not duplicate skill bodies. Tags `(unverified)` and
`(medium confidence)` from a skill apply here too.

Activation: a glob cannot test file content, so the pattern covers Maven main and test Java
sources only. Apply this rule **only when the file imports `dev.langchain4j`**; otherwise ignore it.

Scope: chat and streaming in plain Java (`ChatModel`, `StreamingChatModel`). AiServices, `@Tool`,
chat memory, RAG, structured output and Spring/Quarkus integration are out of scope: say so and do
not route to any skill.

## Skills

| Need | Skill |
|---|---|
| Core API, streaming and listeners, errors and retry, testing | `developing-langchain4j-core-v1-22` |
| OpenAI model construction, reasoning models | `integrating-langchain4j-openai-v1-22` |
| Anthropic model construction, thinking and effort, caching | `integrating-langchain4j-provider-a-v1-22` |

Provider skills own model construction (builders); the core skill takes a
`ChatModel`/`StreamingChatModel` as given.

## Always

- Read API keys from environment variables or a secret store
  (`integrating-langchain4j-openai-v1-22`, `integrating-langchain4j-provider-a-v1-22`).
- Pass model IDs as strings taken from the current official provider catalog, not from the OpenAI
  model-name enum (`integrating-langchain4j-openai-v1-22`).
- End error-handling code with a `catch (LangChain4jException e)` fallback after the specific
  exception types (`developing-langchain4j-core-v1-22`).
- Anthropic on Claude 5.x: use `thinkingType("adaptive")`; pass effort through
  `customParameters` (`integrating-langchain4j-provider-a-v1-22`).
- GPT-6 reasoning models: omit `temperature`, `top_p` and `top_logprobs` when reasoning effort is not `none`, and
  prefer `maxCompletionTokens` for output limits (`integrating-langchain4j-openai-v1-22`).
- Tests: use a hand-written `ChatModel` test double instead of a real provider call
  (unverified as an official practice; `developing-langchain4j-core-v1-22`).

## Ask First

- Async or reactive APIs marked `@Experimental` (`developing-langchain4j-core-v1-22`).
- The `langchain4j-open-ai-official` module (beta): never the default
  (`integrating-langchain4j-openai-v1-22`).
- `maxTokens` vs `maxCompletionTokens` on OpenAI: prefer `maxCompletionTokens` on GPT-6
  (unverified that `max_tokens` is rejected); OpenAI-compatible servers may need `maxTokens`
  (medium confidence), so ask which endpoint is targeted (`integrating-langchain4j-openai-v1-22`).
- Anything a loaded skill marks as an Ask-First decision: do not resolve it without consulting that
  skill.

## Never

- Hardcode an API key in source, tests or committed config.
- Enable `logRequests` or `logResponses` in production: request and response bodies (prompts, PII)
  are logged unmasked (`integrating-langchain4j-openai-v1-22`, `integrating-langchain4j-provider-a-v1-22`).
- Use `thinkingType("enabled")` with `thinkingBudgetTokens` on Claude 5.x: use `"adaptive"` instead
  (`integrating-langchain4j-provider-a-v1-22`).
- Set `temperature`/`top_p`/`top_logprobs` on a GPT-6 reasoning model with effort other than `none`
  (`integrating-langchain4j-openai-v1-22`).
- Retry `NonRetriableException` subclasses by hand: the default policy rethrows them immediately
  (`developing-langchain4j-core-v1-22`).

## Verify

- Grep for `logRequests(true)` and `logResponses(true)`: any match outside a dev profile is a violation.
- Grep for string literals starting with a provider key prefix, and for `apiKey("` with a literal.
- Grep for `thinkingBudgetTokens` and `OpenAiChatModelName`: review each match against the skills.
- Run `./mvnw clean compile` and `test` (or `mvn` without a wrapper) after any change.
