---
name: integrating-langchain4j-openai-v1-22
description: "Teaches OpenAI (ChatGPT) chat and streaming in plain Java with langchain4j-open-ai 1.22.0: dependency, builders, model IDs, reasoning parameters, timeouts, logging. Use when building or reviewing OpenAiChatModel code on 1.22.0. Not for AiServices, RAG, Spring or Quarkus."
---

# LangChain4j OpenAI integration 1.22.0 (chat and streaming)

> Version lock: every claim applies to **langchain4j-open-ai 1.22.0** only. Research date **2026-10-26**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against a versioned official page.

Scope: `OpenAiChatModel` and `OpenAiStreamingChatModel` in plain Java, built with `langchain4j-open-ai`. The generic `ChatModel` API, the streaming handler, exceptions and retry classes are owned by the skill `developing-langchain4j-core-v1-22`; this skill does not repeat them. AiServices, `@Tool`, memory, RAG, structured output, Spring, Quarkus and Anthropic (sibling skill `integrating-langchain4j-provider-a-v1-22`) are out of scope.

## Version Context

| Item | Value | Source (fetched 2026-10-26) |
|---|---|---|
| langchain4j-open-ai | 1.22.0 stable, GitHub release 2026-10-08, Maven Central 2026-10-07 | https://repo1.maven.org/maven2/dev/langchain4j/langchain4j-open-ai/maven-metadata.xml |
| BOM | `dev.langchain4j:langchain4j-bom:1.22.0`, type pom, scope import | https://docs.langchain4j.dev/get-started |
| JDK | minimum 17 | https://docs.langchain4j.dev/get-started |
| OpenAI API called | Chat Completions, through the module's own REST client | https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-open-ai/src/main/java/dev/langchain4j/model/openai/OpenAiChatModel.java |
| OpenAI model catalog | read 2026-10-26; IDs and statuses change on OpenAI's schedule | https://developers.openai.com/api/docs/models/all |
| Official-SDK module | `langchain4j-open-ai-official` 1.22.0-beta32, beta | https://repo1.maven.org/maven2/dev/langchain4j/langchain4j-open-ai-official/ |

**Version-lifetime risk** (as of 2026-10-26; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- 1.22.0 was released on GitHub 2026-10-08; docs pages are unversioned and may change.
- OpenAI marks models Deprecated or Shut down independently of LangChain4j; re-check the catalog before pinning an ID.
- No successor release was recorded (medium confidence, absence of evidence).

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Builder options and variants](./blueprints/builder-options.md)
- [GPT-6 and reasoning-model rules](./blueprints/gpt-6-and-reasoning.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Declare `langchain4j-open-ai` without a `<version>`** and let the imported `langchain4j-bom:1.22.0` manage it ([get-started](https://docs.langchain4j.dev/get-started)). See [patterns](./blueprints/always-do-patterns.md#1-dependency).
- **Read the API key from an environment variable** such as `System.getenv("OPENAI_API_KEY")` ([OpenAI integration docs](https://docs.langchain4j.dev/integrations/language-models/open-ai)). See [patterns](./blueprints/always-do-patterns.md#7-api-key-from-the-environment).
- **Set `modelName` explicitly with a string ID** copied from the OpenAI model catalog; `modelName(String)` exists next to the enum overload ([OpenAiChatModel at 1.22.0](https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-open-ai/src/main/java/dev/langchain4j/model/openai/OpenAiChatModel.java), [catalog](https://developers.openai.com/api/docs/models/all)). See [patterns](./blueprints/always-do-patterns.md#2-blocking-model).
- **Size `timeout(Duration)` to the workload**: it sets both connect and read timeout, and the defaults are 15 s connect and 60 s read ([OpenAiChatModel at 1.22.0](https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-open-ai/src/main/java/dev/langchain4j/model/openai/OpenAiChatModel.java)). See [patterns](./blueprints/always-do-patterns.md#4-timeouts-and-retries).
- **Cap output with `maxCompletionTokens`**; the builder sends it as `max_completion_tokens` ([OpenAiUtils at 1.22.0](https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-open-ai/src/main/java/dev/langchain4j/model/openai/internal/OpenAiUtils.java)). See [GPT-6 rules](./blueprints/gpt-6-and-reasoning.md#output-limit).
- **Omit `temperature`, `topP` and `topLogprobs` on GPT-6 models when reasoning effort is not `none`** ([Using GPT-6 guide](https://developers.openai.com/api/docs/guides/latest-model)). See [GPT-6 rules](./blueprints/gpt-6-and-reasoning.md#sampling-parameters).
- **Implement `onError` in the handler passed to `OpenAiStreamingChatModel`**; errors arrive only there ([handler source at 1.22.0](https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/model/chat/response/StreamingChatResponseHandler.java)). See [patterns](./blueprints/always-do-patterns.md#3-streaming-model).
- **Take handler and error classes from skill `developing-langchain4j-core-v1-22`** rather than redefining them here.
- **Leave `logRequests` and `logResponses` at their default `false` in production**; request and response bodies are logged unmasked ([HttpRequestLogger at 1.22.0](https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-http-client/src/main/java/dev/langchain4j/http/client/log/HttpRequestLogger.java)).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Streaming retries | `OpenAiStreamingChatModel` has no `maxRetries` builder option and does not retry (medium confidence); blocking `OpenAiChatModel` retries 2 times by default. Own retry belongs in `onError`, on retriable exceptions only (see core skill). | "Is a failed stream acceptable, or should the caller retry it?" |
| `maxTokens` vs `maxCompletionTokens` | `maxCompletionTokens` suits api.openai.com; `maxTokens` may be the only field some OpenAI-compatible servers accept (medium confidence). | "Which endpoint and model family does this call target?" |
| OpenAI-compatible `baseUrl` | Works by setting `baseUrl` and the provider's model ID; behavior beyond the documented DeepSeek example is (unverified). See [options](./blueprints/builder-options.md#openai-compatible-endpoints). | "Which provider, which base URL, and does it return `reasoning_content`?" |
| `langchain4j-open-ai-official` 1.22.0-beta32 | Beta artifact on the official OpenAI SDK; adds Azure and GitHub Models support (medium confidence). Never the default. Whether the BOM manages its version is (unverified). See [options](./blueprints/builder-options.md#official-sdk-module). | "Is a beta artifact acceptable, and is Azure or GitHub Models a target?" |
| Azure OpenAI | Use the official-SDK module or the separate Azure integration; pointing `langchain4j-open-ai` at Azure by `baseUrl` alone is (unverified). | "Is Azure the target endpoint?" |
| `streamingBufferSize` | `@Experimental` since 1.20.0; overflow ends the stream with `IllegalStateException`; the default value is (unverified). | "Are experimental APIs acceptable here?" |

### Notes (not decisions; see the register)

- Tools on GPT-6: tool calling is out of scope here; on Astra, Sol and Terra it requires the Responses API, and Luna and Sol allow Chat Completions functions only with effort `none` (medium confidence, M2).
- Reasoning effort value: `reasoningEffort(String)` is sent verbatim; accepted values per model, and the default when unset, are (unverified, U5, U6).
- Long reasoning outputs: the 60 s default read timeout may be too short (unverified, U7).
- One model instance across threads: reusing one built model is common, but no doc states thread-safety (unverified, U3).

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Pick a model from `OpenAiChatModelName`; the 1.22.0 enum stops at `GPT_5_1` and lists models the catalog marks Shut down ([enum](https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-open-ai/src/main/java/dev/langchain4j/model/openai/OpenAiChatModelName.java), [catalog](https://developers.openai.com/api/docs/models/all)) | Pass a string ID from the catalog: `.modelName("gpt-6-astra")` |
| Hardcode the API key in source or config files ([docs sample](https://docs.langchain4j.dev/integrations/language-models/open-ai) reads it from the environment) | `.apiKey(System.getenv("OPENAI_API_KEY"))` or a secret store |
| Enable `logRequests(true)` or `logResponses(true)` in production; bodies with prompts and personal data are logged unmasked at INFO ([HttpRequestLogger at 1.22.0](https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-http-client/src/main/java/dev/langchain4j/http/client/log/HttpRequestLogger.java)) | Keep both `false`; enable locally for debugging only |
| Send `temperature` or `topP` to a GPT-6 model while reasoning effort is not `none` ([Using GPT-6 guide](https://developers.openai.com/api/docs/guides/latest-model)) | Omit them, or set `reasoningEffort("none")` first |

Rows with code: [never-do patterns](./blueprints/never-do-patterns.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| Default `baseUrl` | `https://api.openai.com/v1` | https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-open-ai/src/main/java/dev/langchain4j/model/openai/OpenAiChatModel.java |
| Default timeouts | connect 15 s, read 60 s; one `timeout(Duration)` sets both | same page |
| Blocking `maxRetries` default | 2; base delay 500 ms, backoff 1.5, jitter 0.2 | https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/internal/RetryUtils.java |
| Streaming `maxRetries` | no such builder method (medium confidence) | https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-open-ai/src/main/java/dev/langchain4j/model/openai/OpenAiStreamingChatModel.java |
| `logRequests` / `logResponses` | default `false`; logger option takes an SLF4J `Logger` | same OpenAiChatModel page |
| `modelName` check | no build-time check; a missing name surfaces at request time | same OpenAiChatModel page |
| Optional scoping | `organizationId`, `projectId`, `customHeaders`, `customQueryParams` | same OpenAiChatModel page |
| Streaming-only | `accumulateToolCallId` default `true`; `streamingBufferSize` `@Experimental` | https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-open-ai/src/main/java/dev/langchain4j/model/openai/OpenAiStreamingChatModel.java |
| HTTP client | `langchain4j-http-client-jdk` is a runtime dependency; core and http-client are compile scope | https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-open-ai/pom.xml |
| Error mapping and retry classes | 401/403 Authentication, 404 ModelNotFound, 429 RateLimit and others: see skill `developing-langchain4j-core-v1-22` | https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/internal/ExceptionMapper.java |
| Verify commands (run locally) | `mvn -q dependency:tree -Dincludes=dev.langchain4j` (expect `langchain4j-open-ai` 1.22.0), `grep -rn "OpenAiChatModelName\." src/main/java` (expect no match), `grep -rn 'apiKey("sk-' src` (expect no match) | local commands, no external source |

## External Resources

All fetched 2026-10-26.

- [OpenAI integration docs](https://docs.langchain4j.dev/integrations/language-models/open-ai)
- [Get Started](https://docs.langchain4j.dev/get-started)
- [OpenAI model catalog](https://developers.openai.com/api/docs/models/all)
- [Using GPT-6 guide](https://developers.openai.com/api/docs/guides/latest-model)
- [Release 1.22.0](https://github.com/langchain4j/langchain4j/releases/tag/1.22.0)
- [Full bibliography](./blueprints/unverified-and-risks.md#source-bibliography)
