---
name: integrating-langchain4j-provider-a-v1-22
description: "Teaches Anthropic chat and streaming in plain Java with langchain4j-anthropic 1.22.0 (builders, defaults, maxTokens, adaptive thinking, effort, prompt caching). Use when building or reviewing AnthropicChatModel code on 1.22.0. Not for AiServices, RAG, Spring, Quarkus or OpenAI."
---

# langchain4j-anthropic 1.22.0 (Claude chat and streaming)

> Version lock: every claim applies to **langchain4j-anthropic 1.22.0** only. Research date **2026-10-26**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against a versioned official page.

Scope: building and configuring `AnthropicChatModel` and `AnthropicStreamingChatModel` in plain Java. The generic `ChatModel` API, streaming handler, listeners, errors and retry are in `developing-langchain4j-core-v1-22`; this skill does not repeat them. AiServices, `@Tool`, memory, RAG, structured output, Spring and Quarkus are out of scope. OpenAI models are covered by the sibling `integrating-langchain4j-openai-v1-22`.

## Version Context

| Item | Value | Source (fetched 2026-10-26) |
|---|---|---|
| langchain4j-anthropic | 1.22.0, GitHub release 2026-10-08, Maven Central 2026-10-07, latest stable, no breaking Anthropic changes listed | https://github.com/langchain4j/langchain4j/releases/tag/1.22.0 |
| New in 1.22.0 | `cacheAutomatically`, `cacheTtl`; `cache_control` only on the last tool and the last system message | https://github.com/langchain4j/langchain4j/releases/tag/1.22.0 |
| BOM | `dev.langchain4j:langchain4j-bom:1.22.0`, type pom, scope import | https://docs.langchain4j.dev/get-started |
| JDK | minimum 17 | https://docs.langchain4j.dev/get-started |
| Anthropic API version header | default `2023-06-01` | https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-anthropic/src/main/java/dev/langchain4j/model/anthropic/AnthropicChatModel.java |
| Claude models | `claude-fable-5-1`, `claude-opus-5-5`, `claude-sonnet-5-5`, `claude-haiku-5-5` | https://platform.claude.com/docs/en/about-claude/models/overview |

**Version-lifetime risk** (as of 2026-10-26; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- Claude model retirement is not sooner than 2027-09-22 (Opus 5.5), 2027-09-28 (Sonnet 5.5) and 2027-10-07 (Haiku 5.5); no retirement date was recorded for Fable 5.1.
- The LangChain4j docs site is unversioned and assumed to match 1.22.0 (medium confidence).

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Builder options and defaults](./blueprints/builder-options.md)
- [Adaptive thinking and effort](./blueprints/thinking-and-effort.md)
- [Prompt caching and system messages](./blueprints/caching-and-system-messages.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Import the BOM** `dev.langchain4j:langchain4j-bom:1.22.0` and declare `langchain4j-anthropic` without a `<version>` ([get-started](https://docs.langchain4j.dev/get-started)). See [patterns](./blueprints/always-do-patterns.md#1-dependency-bom-and-module).
- **Set `maxTokens` explicitly**: both models default to 1024 when neither the builder nor `defaultRequestParameters` sets it ([AnthropicChatModel at 1.22.0](https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-anthropic/src/main/java/dev/langchain4j/model/anthropic/AnthropicChatModel.java)). See [patterns](./blueprints/always-do-patterns.md#2-blocking-model).
- **Set `timeout` explicitly**: the model class defines no default ([AnthropicChatModel at 1.22.0](https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-anthropic/src/main/java/dev/langchain4j/model/anthropic/AnthropicChatModel.java)).
- **Pass `apiKey` from `System.getenv` or a secret store**; the builder takes it as `apiKey(...)` ([Anthropic integration docs](https://docs.langchain4j.dev/integrations/language-models/anthropic)).
- **Pass `modelName` as a string from the current Anthropic catalog**, for example `claude-sonnet-5-5` ([models overview](https://platform.claude.com/docs/en/about-claude/models/overview)).
- **Use `thinkingType("adaptive")` on Claude 5.x models** ([adaptive thinking](https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost)). See [thinking](./blueprints/thinking-and-effort.md#adaptive-thinking).
- **Set effort through `customParameters(Map.of("output_config", Map.of("effort", ...)))`**; the builder has no `effort` method ([AnthropicChatModel at 1.22.0](https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-anthropic/src/main/java/dev/langchain4j/model/anthropic/AnthropicChatModel.java)). See [thinking](./blueprints/thinking-and-effort.md#effort).
- **Keep `logRequests` and `logResponses` off in production**: the body is logged unmasked at INFO ([HttpRequestLogger at 1.22.0](https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-http-client/src/main/java/dev/langchain4j/http/client/log/HttpRequestLogger.java)).
- **Handle model errors with the branching in the core skill** `developing-langchain4j-core-v1-22`.
- **Know that the blocking model retries up to `maxRetries` (default 2) before throwing**, so an outer retry loop adds attempts ([AnthropicChatModel at 1.22.0](https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-anthropic/src/main/java/dev/langchain4j/model/anthropic/AnthropicChatModel.java)).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Prompt caching mode | `cacheSystemMessages` / `cacheTools` for a stable prefix vs `cacheAutomatically` for growing conversations; TTL `5m` (default) vs `1h`. Anthropic allows at most 4 breakpoints per request and has a model-specific minimum prompt size (medium confidence). See [caching](./blueprints/caching-and-system-messages.md#choosing-a-mode). | "Is the prompt prefix stable, or does the conversation grow? How often is it repeated?" |
| Visible reasoning text | `thinkingDisplay("summarized")` + `returnThinking(true)` shows reasoning; when unset, recent models may return empty thinking (medium confidence). `sendThinking` defaults to true. | "Does the UI or the log need the reasoning text?" |
| Effort level | `low`, `medium`, `high`, `xhigh`, `max` exist (medium confidence); availability per model is (unverified). Defaults: high on Fable 5.1 and Sonnet 5.5, medium on Opus 5.5 and Haiku 5.5. | "Latency and cost, or answer quality, first?" |
| Mid-conversation system messages | `midConversationSystemMessages(true)` sends later system messages inline; supported on Fable 5.1, Opus 5.5, Sonnet 5.5 and Haiku 5.5, not on Sonnet 5. Placement rules are (medium confidence). | "Do system messages arrive after the first user turn, and which model is used?" |
| Streaming and retry | The streaming model has no `maxRetries` and does not retry (medium confidence); add retry in your code only within the caller's timeout budget. | "Should a failed stream be retried by the application?" |
| Beta headers | `.beta(...)` values change over time (medium confidence). | "Which beta feature is needed, and is it still listed by Anthropic?" |

### Notes (not decisions; see the register)

- Missing `modelName`: no build-time check exists in either constructor; request-time validation is (unverified, U1).
- Test double: use the hand-written double from the core skill (unverified as an official practice, U4); a local stub server on `baseUrl` is also possible (unverified as an official practice, U4).
- Error classes: the retry class of `InvalidRequestException` is (unverified, U2); end handlers with a `LangChain4jException` catch.

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| `thinkingType("enabled")` + `thinkingBudgetTokens(...)` on Claude 5.x; the mode is not accepted on models after Sonnet 4.6 ([thinking page](https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost)) | `thinkingType("adaptive")` and steer with effort |
| Rely on the 1024 `maxTokens` default; long answers are cut off ([AnthropicChatModel at 1.22.0](https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-anthropic/src/main/java/dev/langchain4j/model/anthropic/AnthropicChatModel.java)) | `.maxTokens(4096)` or higher, sized to the task |
| Hardcode `sk-ant-...` in source ([Anthropic integration docs](https://docs.langchain4j.dev/integrations/language-models/anthropic) pass the key via `apiKey(...)` from the environment) | `System.getenv("ANTHROPIC_API_KEY")` or a secret store |
| Enable `logRequests` or `logResponses` in production; prompts and personal data are logged unmasked ([HttpRequestLogger at 1.22.0](https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-http-client/src/main/java/dev/langchain4j/http/client/log/HttpRequestLogger.java)) | Keep both off; enable only in local debugging |
| Put `effort` inside the `thinking` object; Anthropic places it at top level in `output_config` ([effort docs](https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost)) | `customParameters(Map.of("output_config", Map.of("effort", "high")))` |
| Use retired-looking IDs such as `claude-3-5-sonnet-20241022`; not in the current or legacy catalog ([models overview](https://platform.claude.com/docs/en/about-claude/models/overview)) | `claude-sonnet-5-5` or another current ID |
| Enable `midConversationSystemMessages` with Claude Sonnet 5; Anthropic states it is not available there ([mid-conversation docs](https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages)) | Leave the default `false`, or use Sonnet 5.5 |
| Pin a `<version>` on `langchain4j-anthropic` next to the BOM ([get-started](https://docs.langchain4j.dev/get-started)) | Omit it and let `langchain4j-bom:1.22.0` manage it |

Rows with code: [never-do patterns](./blueprints/never-do-patterns.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| `baseUrl` default | `https://api.anthropic.com/v1/` | https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-anthropic/src/main/java/dev/langchain4j/model/anthropic/AnthropicChatModel.java |
| `version` default | `2023-06-01` (`anthropic-version` header) | same page |
| `maxTokens` default | 1024 when unset | same page |
| `maxRetries` default | 2, blocking model only | same page |
| `timeout` default | none in the model class | same page |
| `returnThinking` / `sendThinking` | false / true | https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-anthropic/src/main/java/dev/langchain4j/model/anthropic/AnthropicStreamingChatModel.java |
| Claude 5.x context / max output | 1M tokens / 128K tokens | https://platform.claude.com/docs/en/about-claude/models/overview |
| Verify command (run locally) | `mvn -q dependency:tree -Dincludes=dev.langchain4j` shows `langchain4j-anthropic:jar:1.22.0` (log output unverified) | local command, no external source |

## External Resources

All fetched 2026-10-26.

- [Anthropic integration docs](https://docs.langchain4j.dev/integrations/language-models/anthropic)
- [Get Started](https://docs.langchain4j.dev/get-started)
- [Release 1.22.0](https://github.com/langchain4j/langchain4j/releases/tag/1.22.0)
- [Anthropic models overview](https://platform.claude.com/docs/en/about-claude/models/overview)
- [Full bibliography](./blueprints/unverified-and-risks.md#source-bibliography)
