---
name: developing-langchain4j-core-v1-22
description: "Teaches provider-agnostic chat and streaming in plain Java with LangChain4j 1.22.0 (BOM, ChatModel, StreamingChatModel, errors and retry, test doubles). Use when writing or reviewing Java LLM chat code on 1.22.0. Not for AiServices, RAG, Spring or Quarkus."
---

# LangChain4j core 1.22.0 (chat and streaming)

> Version lock: every claim applies to **LangChain4j 1.22.0** only. Research date **2026-10-26**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against a versioned official page.

Scope: provider-agnostic `ChatModel` / `StreamingChatModel` in plain Java. This skill takes a `ChatModel` or `StreamingChatModel` as given: a runnable call needs a provider model built per `integrating-langchain4j-openai-v1-22` or `integrating-langchain4j-provider-a-v1-22`. Provider specifics live in the sibling skills `integrating-langchain4j-openai-v1-22` and `integrating-langchain4j-provider-a-v1-22`. AiServices, `@Tool`, memory, RAG, structured output, Spring and Quarkus are out of scope for this skill.

## Version Context

| Item | Value | Source (fetched 2026-10-26) |
|---|---|---|
| LangChain4j | 1.22.0, GitHub release 2026-10-08, Maven Central 2026-10-07, latest stable | https://github.com/langchain4j/langchain4j/releases/tag/1.22.0 |
| BOM | `dev.langchain4j:langchain4j-bom:1.22.0`, type pom, scope import; some BOM modules still use `1.22.0-beta32` | https://docs.langchain4j.dev/get-started |
| JDK | minimum 17; maximum (unverified) | https://docs.langchain4j.dev/get-started |
| Provider modules | `langchain4j-open-ai` and `langchain4j-anthropic` are 1.22.0 (stable) | https://repo1.maven.org/maven2/dev/langchain4j/langchain4j-open-ai/maven-metadata.xml |
| Breaking changes in 1.22.0 | none listed; one Kotlin note for `chatAsync` (medium confidence) | https://github.com/langchain4j/langchain4j/releases/tag/1.22.0 |

**Version-lifetime risk** (as of 2026-10-26; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- No successor release or end-of-support date was recorded for 1.22.0.
- The docs site is unversioned: pages were read on 2026-10-26 and are assumed to match 1.22.0 (medium confidence).

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Streaming, listeners and async](./blueprints/streaming-and-listeners.md)
- [Errors and retry](./blueprints/errors-and-retry.md)
- [Testing with a ChatModel test double](./blueprints/testing.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Import the BOM** `dev.langchain4j:langchain4j-bom:1.22.0` (type `pom`, scope `import`) in `dependencyManagement` ([get-started](https://docs.langchain4j.dev/get-started)). See [patterns](./blueprints/always-do-patterns.md#1-import-the-bom).
- **Declare provider modules without a `<version>`** so the BOM aligns them ([get-started](https://docs.langchain4j.dev/get-started)). See [patterns](./blueprints/always-do-patterns.md#2-declare-modules-without-versions).
- **Run on JDK 17 or higher**; 17 is the minimum supported JDK ([get-started](https://docs.langchain4j.dev/get-started)).
- **Rely on the provider module to bring `langchain4j-core`**: it is a compile-scope dependency of the provider poms ([open-ai pom at 1.22.0](https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-open-ai/pom.xml)).
- **Implement both abstract callbacks `onCompleteResponse` and `onError`** of `StreamingChatResponseHandler`; every partial callback is a no-op default ([source at 1.22.0](https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/model/chat/response/StreamingChatResponseHandler.java)). See [streaming](./blueprints/streaming-and-listeners.md#streaming-handler).
- **Branch error handling on `NonRetriableException` vs `RetriableException`** for the classes read at 1.22.0: `RetryUtils` rethrows `NonRetriableException` at once ([RetryUtils at 1.22.0](https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/internal/RetryUtils.java)). See [errors](./blueprints/errors-and-retry.md#classify-and-branch).
- **End error handling with a `catch (LangChain4jException e)` fallback**, because the retry class of `InvalidRequestException` and `ContentFilteredException` is (unverified), see U7. See [errors](./blueprints/errors-and-retry.md#classify-and-branch).
- **Use `ChatRequestParameters.overrideWith(other)` when the argument must win** over the receiver ([source at 1.22.0](https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/model/chat/request/ChatRequestParameters.java)).
- **Read usage from `response.metadata().tokenUsage()`** (`inputTokenCount`, `outputTokenCount`, `totalTokenCount`) ([TokenUsage at 1.22.0](https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/model/output/TokenUsage.java)).
- **Read API keys from environment variables or a secret store** (the official docs sample uses `System.getenv("OPENAI_API_KEY")`: https://docs.langchain4j.dev/integrations/language-models/open-ai). See [patterns](./blueprints/always-do-patterns.md#5-read-keys-from-the-environment).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Async or reactive APIs | `chatAsync` and the reactive `Flow.Publisher` are `@Experimental` (medium confidence); blocking `chat` and the streaming handler are not. Experimental APIs can change between releases. | "Are experimental APIs acceptable in this codebase?" |
| Parameters: model default vs per request | Model-level `defaultRequestParameters()` vs `ChatRequest.parameters(...)`; `chat(request, options)` merges them. Per-request suits per-tenant values, model-level suits global values. | "Are these parameters per tenant or per call, or global?" |
| Per-call listener metadata | `ChatRequestOptions` `listenerAttributes` (not sent to the provider) vs writing into `attributes()` inside `onRequest` (medium confidence). | "Does the metadata need to exist before the first listener runs?" |
| Cancelling a stream | `PartialResponseContext.streamingHandle().cancel()` closes the connection and stops callbacks (medium confidence). | "Should abandoned streams be cancelled?" |
| Resending conversation history | The model is stateless: resend earlier messages with each call (medium confidence); memory is out of scope here. | "Who owns the history, the caller or another component?" |
| User text near a `SystemMessage` | The docs warn against injecting end-user content into `SystemMessage` (medium confidence). | "Does any end-user text reach the system prompt?" |
| Slow work inside listeners or callbacks | Listener and streaming callbacks run on the I/O thread; offload to an executor (medium confidence). | "Does the listener do I/O, such as a database write?" |
| ChatModel test double | Hand-written subclass overriding `doChat` (unverified as an official practice); no official recipe exists for 1.22.0 (medium confidence). | "Use a hand-written double or a Mockito mock?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Retry a `NonRetriableException` in a loop; `RetryUtils` rethrows it immediately ([RetryUtils at 1.22.0](https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/internal/RetryUtils.java)) | Catch `NonRetriableException`, surface it, and fix the configuration or request |
| Leave `onError` empty in a streaming handler; errors arrive only there ([source at 1.22.0](https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/model/chat/response/StreamingChatResponseHandler.java)) | Complete the future exceptionally: `onError(Throwable t) { future.completeExceptionally(t); }` |
| Pin a provider module `<version>` next to the BOM ([get-started](https://docs.langchain4j.dev/get-started)) | Omit the version and let `langchain4j-bom:1.22.0` manage it |
| Hardcode an API key in source or config files (the official docs sample reads it with `System.getenv`: https://docs.langchain4j.dev/integrations/language-models/open-ai) | Read it with `System.getenv("...")` or from a secret store |
| Enable `logRequests` or `logResponses` in production; secret headers are masked but the body is logged unmasked at INFO ([HttpRequestLogger at 1.22.0](https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-http-client/src/main/java/dev/langchain4j/http/client/log/HttpRequestLogger.java)) | Keep them off in production; enable only in local debugging |

Rows with code: [never-do patterns](./blueprints/never-do-patterns.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| Status mapping | 5xx InternalServer, 401/403 Authentication, 404 ModelNotFound, 408 Timeout, 429 RateLimit, other 4xx InvalidRequest, UnresolvedAddress to UnresolvedModelServer | https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/internal/ExceptionMapper.java |
| Default retry | maxRetries 2 (up to 3 executions), delay 500 ms, backoff 1.5, jitter 0.2 | https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/internal/RetryUtils.java |
| `ChatModel` | no abstract methods; 16 default methods; implementors override `doChat(ChatRequest)` | https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/model/chat/ChatModel.java |
| `FinishReason` | STOP, LENGTH, TOOL_EXECUTION, CONTENT_FILTER, OTHER | https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/model/output/FinishReason.java |
| Streaming handler | abstract: `onCompleteResponse`, `onError`; defaults: `onPartialResponse`, `onPartialThinking`, `onPartialToolCall`, `onCompleteToolCall`, `onUnmappedRawEvent` | https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/model/chat/response/StreamingChatResponseHandler.java |
| Verify | `mvn -q dependency:tree -Dincludes=dev.langchain4j` (all at 1.22.0 except beta modules), `java -version` (17+), `mvn -q test` (log output unverified) | page not recorded |

## External Resources

All fetched 2026-10-26.

- [Get Started](https://docs.langchain4j.dev/get-started)
- [Chat and Language Models](https://docs.langchain4j.dev/tutorials/chat-and-language-models)
- [Response Streaming](https://docs.langchain4j.dev/tutorials/response-streaming)
- [Observability](https://docs.langchain4j.dev/tutorials/observability)
- [Release 1.22.0](https://github.com/langchain4j/langchain4j/releases/tag/1.22.0)
- [Full bibliography](./blueprints/unverified-and-risks.md#source-bibliography)
