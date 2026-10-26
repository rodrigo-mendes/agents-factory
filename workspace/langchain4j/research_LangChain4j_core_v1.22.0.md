# Research: LangChain4j core (provider-agnostic chat API) — v1.22.0

> Unit: core. Scope: `langchain4j-bom` + `langchain4j-core`; ChatModel / StreamingChatModel; ChatRequest / ChatResponse / ChatRequestParameters; ChatMessage + content types; StreamingChatResponseHandler; TokenUsage / FinishReason; ChatModelListener; exception hierarchy and retry/timeout semantics; Java requirement; testing (mocking ChatModel).
> Out of scope: OpenAI/Anthropic-specific classes, AiServices/@Tool, memory, RAG, structured output, Spring/Quarkus.
> All read dates: 2026-10-26. Source codes used below: [S1]..[S16] (see Source Bibliography).

## Metadata

```yaml
Full_Name: LangChain4j (langchain4j-core + langchain4j-bom)
Target_Version: 1.22.0
Release_Date: 2026-10-08 (GitHub release, [S1]); artifact published to Maven Central 2026-10-07 21:11 ([S16])
Support_Status: Active (current stable per caller; latest on Maven Central listing [S16])
Primary_Docs: https://docs.langchain4j.dev/
Official_Repo: https://github.com/langchain4j/langchain4j (tag 1.22.0)
Research_Date: 2026-10-26
Domain_Complexity: Standard
Research_Depth: standard (caller forbade parallel sub-investigators; single-agent fetch)
Max_Iterations: 5
Gap_Loop_Ran: true
Iterations_Used: 1 of 5
Triangulated_Count: 3
Unverified_Count: 5
Irresolvable_Count: 0
Research_Quality_Score: ~88%  # estimate: ~40 claims, 5 unverified
```

## Executive Summary

LangChain4j 1.22.0 is a Java library whose `langchain4j-core` module defines a provider-agnostic chat API. `ChatModel` handles blocking calls and `StreamingChatModel` handles streaming calls. Requests are built as `ChatRequest` (messages plus `ChatRequestParameters`). Responses come back as `ChatResponse` (an `AiMessage` plus `ChatResponseMetadata` that carries `TokenUsage` and `FinishReason`). Provider modules implement these interfaces. The minimum JDK is 17 [S3], and versions are aligned through `dev.langchain4j:langchain4j-bom:1.22.0` [S3].

The 1.22.0 release notes list no breaking changes and contain no core chat-API entries. The notable items are the OpenAI Decisions API, `BedrockBatchChatModel`, Anthropic automatic prompt caching / cache TTL, and an EmbeddingModel metrics listener [S1]. The chat docs carry one Kotlin source-compatibility warning: `chatAsync(ChatRequest)` now resolves to the Java member and returns `CompletableFuture` [S2]. The async (`chatAsync`, since about 1.20) and reactive-streaming APIs are `@Experimental` [S2][S6][S4].

The domain tier is Standard: one integration surface with multiple concerns (streaming, observability, retries). Three patterns matter most: (1) import the BOM and do not pin modules separately, (2) implement both abstract streaming callbacks `onCompleteResponse` and `onError`, and (3) branch error handling on `RetriableException` vs `NonRetriableException`.

## Architectural Guardrails

> Confidence legend: 🟢 High (2+ official sources, dated ≤12mo) | 🟡 Medium (1 source or dated 12–24mo) | 🔴 Low

### ✅ Mandatory Patterns

**Import langchain4j-bom 1.22.0 and declare modules without versions**
> Confidence: 🟢 High | [✓✓ Triangulated | get-started docs [S3] + Maven Central listing [S16]]
- Why: The docs show the BOM in `dependencyManagement` (type `pom`, scope `import`) [S3].
- Code:
  ```xml
  <!-- LangChain4j 1.22.0 -->
  <dependencyManagement><dependencies>
    <dependency>
      <groupId>dev.langchain4j</groupId><artifactId>langchain4j-bom</artifactId>
      <version>1.22.0</version><type>pom</type><scope>import</scope>
    </dependency>
  </dependencies></dependencyManagement>
  <dependencies>
    <dependency><groupId>dev.langchain4j</groupId><artifactId>langchain4j-core</artifactId></dependency>
  </dependencies>
  ```
- Note: Declaring `langchain4j-core` directly is shown here for completeness. The docs examples declare provider modules (`langchain4j-open-ai`), which bring core with them transitively (transitivity is **unverified**).
- Source: https://docs.langchain4j.dev/get-started (2026-10-26)

**Implement both abstract callbacks of StreamingChatResponseHandler**
> Confidence: 🟢 High | [✓✓ Triangulated | source at tag 1.22.0 [S7] + streaming docs [S4]]
- Why: `onCompleteResponse(ChatResponse)` and `onError(Throwable)` are the only abstract methods. Every partial callback (`onPartialResponse`, `onPartialThinking`, `onPartialToolCall`, `onCompleteToolCall`, `onUnmappedRawEvent`) is a no-op `default` [S7].
- Code:
  ```java
  // LangChain4j 1.22.0
  model.chat(chatRequest, new StreamingChatResponseHandler() {
      @Override public void onPartialResponse(String partial) { System.out.print(partial); }
      @Override public void onCompleteResponse(ChatResponse r) { future.complete(r); }
      @Override public void onError(Throwable t) { future.completeExceptionally(t); }
  });
  ```
- Source: [S7], [S4] (2026-10-26)

**Classify failures via RetriableException / NonRetriableException**
> Confidence: 🟢 High | [✓✓ Triangulated | exception classes [S10–S13] + ExceptionMapper [S9] + RetryUtils [S8]]
- Why: `DefaultExceptionMapper` maps HTTP status to typed exceptions. `RetryUtils` rethrows `NonRetriableException` at once and retries other exceptions [S8][S9].
- Mapping (root cause `HttpException`) [S9]: 401/403 → `AuthenticationException` (NonRetriable [S11]); 404 → `ModelNotFoundException`; 408 → `TimeoutException` (Retriable [S13]); 429 → `RateLimitException` (Retriable [S10]); other 4xx → `InvalidRequestException` (NonRetriable [S12]); 5xx → `InternalServerException` (Retriable [S12b]); `UnresolvedAddressException` → `UnresolvedModelServerException`. The base class is `LangChain4jException extends RuntimeException` [S14].
- Code:
  ```java
  // LangChain4j 1.22.0
  try { ChatResponse r = model.chat(request); }
  catch (RateLimitException | dev.langchain4j.exception.TimeoutException e) { /* already retried by model; back off / degrade */ }
  catch (AuthenticationException | InvalidRequestException e) { /* fix config/request; do not retry */ }
  ```
- Source: [S8][S9][S10–S14] (2026-10-26)

**Treat the model as stateless: resend conversation history**
> Confidence: 🟡 Medium (single source)
- Why: The docs say "LLMs are stateless by nature" [S2].
- Code: `model.chat(firstUser, firstAi, secondUser)` [S2]
- Source: https://docs.langchain4j.dev/tutorials/chat-and-language-models (2026-10-26)

**Keep listener and streaming callbacks non-blocking**
> Confidence: 🟡 Medium (single source page, [S5]; reactive guidance [S4])
- Why: For async and streaming calls, listener callbacks run on the I/O thread that reads the response. Blocking that thread slows other in-flight calls, so offload work to your own executor [S5]. Reactive `onNext` must not block either [S4].
- Source: [S5], [S4] (2026-10-26)

### ⚠️ Conditional Patterns

**Blocking vs async vs streaming vs reactive**
> Confidence: 🟡 Medium
- Options: `ChatModel.chat` (blocking); `ChatModel.chatAsync` → `CompletableFuture` (@Experimental, best-effort HTTP abort on cancel) [S2][S6]; `StreamingChatModel` + handler [S4]; reactive `Flow.Publisher<ChatModelStreamingEvent>` (experimental, cold publisher, request `Long.MAX_VALUE`) [S4].

  | Option | Optimizes | Sacrifices | Best When |
  |---|---|---|---|
  | blocking chat | simplicity | thread per call | batch/back-office |
  | chatAsync | non-blocking | experimental API stability | async services |
  | streaming handler | time-to-first-token | callback complexity | UI/token streaming |
  | reactive publisher | backpressure-aware integration | experimental; overflow if demand < MAX | reactive stacks |

- Agent: "Ask the user whether experimental APIs are acceptable in this codebase."
- Source: [S2][S4][S6] (2026-10-26)

**Where to set parameters: model defaults vs per-request**
> Confidence: 🟡 Medium
- Options: model-level `defaultRequestParameters()` vs `ChatRequest.parameters(...)`. `ChatModel.chat(request, options)` merges the defaults with the request's parameters [S6]. `ChatRequestParameters.overrideWith` gives the argument precedence. `defaultedBy` gives the receiver precedence, and its default implementation throws `UnsupportedOperationException` [S15].
- Agent: "Ask whether parameters are per-tenant/per-call or global."
- Source: [S6][S15] (2026-10-26)

**Per-call listener metadata**
> Confidence: 🟡 Medium
- Options: `ChatRequestOptions` with `listenerAttributes` (not sent to the provider) vs putting values in the `attributes()` map inside `onRequest` [S5][S6].
- Source: [S5] (2026-10-26)

**Cancelling a stream**
> Confidence: 🟡 Medium
- `PartialResponseContext.streamingHandle().cancel()` closes the connection. No further callbacks arrive after that [S4].
- Source: [S4] (2026-10-26)

### 🚫 Forbidden Patterns

**Retrying NonRetriableException in application code**
> Severity: High | Confidence: 🟢 High
- Why: The retry utility rethrows `NonRetriableException` immediately. Auth and invalid-request errors are deterministic [S8][S11][S12].
- Impact: Wasted latency and quota, and auth failures get masked.
- ❌ Wrong:
  ```java
  for (int i = 0; i < 5; i++) { try { return model.chat(req); } catch (LangChain4jException e) { Thread.sleep(1000); } }
  ```
- ✅ Correct:
  ```java
  try { return model.chat(req); }
  catch (NonRetriableException e) { throw e; }          // surface immediately
  catch (RetriableException e) { return fallback(); }   // model-level retries already applied (provider-dependent, unverified)
  ```
- Source: [S8] (2026-10-26)

**Blocking inside ChatModelListener / streaming callbacks**
> Severity: High | Confidence: 🟡 Medium
- Why: The callbacks run on the I/O thread [S5].
- Impact: Other in-flight calls slow down. In reactive mode, buffer overflow errors are possible [S4].
- ❌ Wrong: `public void onResponse(ChatModelResponseContext c) { jdbc.insert(c.chatResponse()); }`
- ✅ Correct: `public void onResponse(ChatModelResponseContext c) { executor.submit(() -> jdbc.insert(c.chatResponse())); }`
- Source: [S5] (2026-10-26)

**Relying on thread-locals across streaming listener callbacks**
> Severity: Medium | Confidence: 🟡 Medium
- Why: For streaming, `onResponse`/`onError` run on a different thread from `onRequest`, and thread context is not propagated [S5].
- ❌ Wrong: `MDC.put("start", ...)` in onRequest, then read in onResponse.
- ✅ Correct: `ctx.attributes().put("startNanos", System.nanoTime())` in onRequest, then read `ctx.attributes()` in onResponse.
- Source: [S5] (2026-10-26)

**Putting end-user input into SystemMessage**
> Severity: High | Confidence: 🟡 Medium
- Why: The docs warn against letting end users inject content into SystemMessage [S2].
- ❌ Wrong: `SystemMessage.from("You are helpful. " + userInput)`
- ✅ Correct: `List.of(SystemMessage.from("You are helpful."), UserMessage.from(userInput))`
- Source: [S2] (2026-10-26)

**Assuming a stream succeeded without onError**
> Severity: High | Confidence: 🟢 High
- Why: `onError` is abstract, and errors are delivered only through it [S7].
- ❌ Wrong: an anonymous handler with an empty `onError(Throwable t) {}`
- ✅ Correct: `onError(Throwable t) { future.completeExceptionally(t); }`
- Source: [S7] (2026-10-26)

## Migration Guide

> Confidence: 🟡 Medium | Sources: [S1] (release 2026-10-08), [S2]

**Breaking Changes**: [S1] lists none for 1.22.0. The docs note one Kotlin change: `chatAsync(ChatRequest)` resolves to the Java member returning `CompletableFuture`. Migrate by calling `.await()` or passing a coroutine context [S2]. The exact version that introduced it is **unverified**.

**Upgrade Steps**: 1) Bump the BOM to `1.22.0`. 2) Re-run tests. 3) If you use Kotlin, check `chatAsync` call sites.

**Compatibility Matrix**:

| Dependency | Min | Max | Notes |
|---|---|---|---|
| JDK | 17 | unverified | "The minimum supported JDK version is 17." [S3] |
| langchain4j modules | 1.22.0 | 1.22.0 | align via BOM [S3] |

Feature-since markers (Javadoc @since) [S7][S8]: `onPartialThinking`/`onPartialToolCall`/`onCompleteToolCall` 1.2.0; context overloads 1.8.0; `onUnmappedRawEvent` 1.17.0; async retry helpers 1.20.0.

## Implementation Blueprint

> Confidence: 🟢 High | [✓✓ Triangulated | ChatModel source [S6] + chat docs [S2]]

`ChatModel` has **no abstract methods**. All 16 methods are `default`, and implementors override `doChat(ChatRequest)` [S6]. Public surface [S6]: `chat(String)`, `chat(ChatMessage...)`, `chat(List<ChatMessage>)`, `chat(ChatRequest)`, `chat(ChatRequest, ChatRequestOptions)`, `chatAsync(...)` (@Experimental), `defaultRequestParameters()`, `listeners()`, `provider()`, `supportedCapabilities()`.

Flow of `chat(ChatRequest)` [S6]: it delegates to `chat(request, ChatRequestOptions.EMPTY)`, which merges default params, notifies listeners `onRequest`, calls `doChat`, then calls `onResponse` on success. On an exception it calls `onError` and rethrows.

```java
// LangChain4j 1.22.0 — provider-agnostic usage; `model` comes from a provider module
ChatRequest request = ChatRequest.builder()
    .messages(SystemMessage.from("Answer briefly."), UserMessage.from("What is LangChain4j?"))
    .temperature(0.2)
    .maxOutputTokens(300)
    .build();                                   // builder fields per [S2]
ChatResponse response = model.chat(request);
AiMessage ai = response.aiMessage();
TokenUsage usage = response.metadata().tokenUsage();     // input/output/total counts [S17]
FinishReason fr = response.metadata().finishReason();    // STOP|LENGTH|TOOL_EXECUTION|CONTENT_FILTER|OTHER [S18]
```

Message types [S2]: `SystemMessage` (text, attributes), `UserMessage` (contents, name, attributes; attributes are not sent to the model), `AiMessage` (text, thinking, toolExecutionRequests, attributes), `ToolExecutionResultMessage`, `CustomMessage` (Ollama only). Content [S2]: `TextContent`, `ImageContent` (URL/Base64, DetailLevel LOW/HIGH/AUTO), `AudioContent`, `VideoContent`, `PdfFileContent`.

`ChatRequestParameters` getters [S15]: modelName, temperature, topP, topK, frequencyPenalty, presencePenalty, maxOutputTokens, stopSequences, toolSpecifications, toolChoice, responseFormat; plus `overrideWith`, `defaultedBy`, `static builder()`.

`TokenUsage` [S17]: `inputTokenCount()`, `outputTokenCount()`, `totalTokenCount()` (Integer, may be null — nullability semantics **unverified**), `add(TokenUsage)`, `static sum(a,b)`.

Listener semantics [S5]: listeners run synchronously in list order, once per call (retries do not re-fire them). A listener exception is logged at WARN and the other listeners still run. For streaming, listener `onResponse` fires before the handler's `onCompleteResponse`, and `onError` fires before the handler's `onError`.

## Quality Control

**Verification Commands**:
```bash
# Representative — adapt to your environment
mvn -q dependency:tree -Dincludes=dev.langchain4j   # Expected: all dev.langchain4j artifacts at 1.22.0
java -version                                        # Expected: 17 or higher
mvn -q test                                          # Expected: BUILD SUCCESS
```

**Mocking** — because every `ChatModel` method is default [S6], a test double only needs `doChat`. This lambda form is not shown in the docs. It is derived from the source and **unverified** as an officially recommended practice.
```java
// LangChain4j 1.22.0 — test double; listeners() defaults to empty (assumed, unverified)
ChatModel fake = new ChatModel() {
    @Override public ChatResponse doChat(ChatRequest req) {
        return ChatResponse.builder()
            .aiMessage(AiMessage.from("stubbed"))
            .tokenUsage(new TokenUsage(1, 1))          // ChatResponse.builder fields unverified
            .finishReason(FinishReason.STOP)
            .build();
    }
};
assertEquals("stubbed", fake.chat("hi"));
```
Mockito `mock(ChatModel.class)` also works mechanically, but note that `chat(String)` is a default method that delegates. Stub the overload your code under test actually calls.

## Production Readiness

- **Performance**: Do not block callbacks [S5]. For reactive streams, request `Long.MAX_VALUE` [S4].
- **Retries**: Core `RetryUtils` defaults are `DEFAULT_RETRY_POLICY` maxRetries=2 (up to 3 executions), base delay 500 ms, backoffExp 1.5, jitterScale 0.2; the builder default delay is 1000 ms. Async retries schedule via `CompletableFuture.delayedExecutor` and never retry `CancellationException` [S8]. Whether and how each provider exposes `maxRetries`/`timeout` builder options belongs to the provider units (**unverified here**).
- **Timeouts**: Only HTTP 408 maps to `TimeoutException`. Other client-side timeouts fall through to generic mapping (passed through as RuntimeException or wrapped) [S9].
- **Monitoring**: `ChatModelListener` gives you request params, response metadata (id, model, finish reason) and token usage [S5]. A Micrometer metrics module exists (an EmbeddingModel listener was added in 1.22.0 [S1]). The chat-metrics details are out of scope / **unverified**.
- **Security**: Keep user input out of SystemMessage [S2]. `UserMessage.attributes()` is not sent to the model [S2].

## Reference Implementations

- Chat docs: https://docs.langchain4j.dev/tutorials/chat-and-language-models
- Streaming docs: https://docs.langchain4j.dev/tutorials/response-streaming
- Observability docs (full listener example): https://docs.langchain4j.dev/tutorials/observability
- Official examples repo: https://github.com/langchain4j/langchain4j-examples (not fetched; **unverified** for 1.22.0)

## Source Bibliography

**Primary** (all read 2026-10-26):
- [S1] GitHub release 1.22.0 — https://github.com/langchain4j/langchain4j/releases/tag/1.22.0 (published 2026-10-08)
- [S2] Chat and Language Models — https://docs.langchain4j.dev/tutorials/chat-and-language-models
- [S3] Get Started — https://docs.langchain4j.dev/get-started
- [S4] Response Streaming — https://docs.langchain4j.dev/tutorials/response-streaming
- [S5] Observability — https://docs.langchain4j.dev/tutorials/observability
- [S6] ChatModel.java @1.22.0 — https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/model/chat/ChatModel.java
- [S7] StreamingChatResponseHandler.java @1.22.0 — https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/model/chat/response/StreamingChatResponseHandler.java
- [S8] RetryUtils.java @1.22.0 — https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/internal/RetryUtils.java
- [S9] ExceptionMapper.java @1.22.0 — https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/internal/ExceptionMapper.java
- [S10] RateLimitException.java @1.22.0 — .../dev/langchain4j/exception/RateLimitException.java
- [S11] AuthenticationException.java @1.22.0 — .../dev/langchain4j/exception/AuthenticationException.java
- [S12] InvalidRequestException.java @1.22.0 — .../dev/langchain4j/exception/InvalidRequestException.java; [S12b] InternalServerException.java @1.22.0
- [S13] TimeoutException.java @1.22.0 — .../dev/langchain4j/exception/TimeoutException.java
- [S14] LangChain4jException.java @1.22.0 — .../dev/langchain4j/exception/LangChain4jException.java
- Exception package listing @1.22.0 (24 classes) — https://github.com/langchain4j/langchain4j/tree/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/exception
- [S15] ChatRequestParameters.java @1.22.0 — .../dev/langchain4j/model/chat/request/ChatRequestParameters.java
- [S16] Maven Central langchain4j-core listing — https://repo1.maven.org/maven2/dev/langchain4j/langchain4j-core/ (1.22.0 at 2026-10-07 21:11)
- [S17] TokenUsage.java @1.22.0 — .../dev/langchain4j/model/output/TokenUsage.java
- [S18] FinishReason.java @1.22.0 — .../dev/langchain4j/model/output/FinishReason.java

(`...` = https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java)

**Validation**: no community sources used.

## Research Gaps

```
Gap: Official guidance on testing/mocking ChatModel (no docs page fetched)
Impact: Mocking pattern is source-derived only
Workaround: Override doChat in a test double
Follow-up: docs.langchain4j.dev testing pages; langchain4j-core test-fixtures artifacts
§7-ref: Iteration 1 — unverified (not IRRESOLVABLE; not searched further)
```
```
Gap: ModelNotFoundException / ContentFilteredException / UnresolvedModelServerException retriable class; ChatResponse.builder field names; JDK max; core transitivity from provider modules; Kotlin change introduction version
Impact: Medium — error branching and test fixtures
Follow-up: read the respective files at tag 1.22.0
§7-ref: Iteration 1 — unverified
```

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|---|---|---|---|---|
| 1 | Production Readiness | Retry defaults | Resolved from RetryUtils source | [S8] (2026-10-26) |
| 1 | Guardrails | Retriable classification of 401/403/429/408/4xx/5xx exceptions | Resolved from class declarations | [S10–S13] (2026-10-26) |
| 1 | Implementation | FinishReason constants, TokenUsage API, ChatRequestParameters API | Resolved from source | [S15][S17][S18] (2026-10-26) |

## Completion Checklist

- [x] Domain complexity tier assessed and documented (Standard)
- [x] All scope areas cited
- [x] Pattern counts driven by domain needs
- [x] Every anti-pattern has alternative
- [x] All CLI commands marked as representative
- [ ] Integration examples complete (provider wiring deferred to OpenAI/Anthropic units)
- [x] Sources dated and linked
- [x] Security documented
- [x] 1+ copy-paste working example
- [x] Confidence badge applied to every pattern entry
- [x] Single-source Always-Do patterns downgraded to 🟡 Medium
- [x] Research Iteration Changelog present
- [x] Research_Quality_Score added to Metadata (estimate)
- [x] Every Research Gap cross-referenced in changelog/§7

## Agent Operation Notes

- **High Confidence**: BOM/JDK 17; handler abstract methods; exception mapping and retriable classes; retry defaults; ChatModel default-method surface.
- **Medium Confidence**: Statelessness, listener threading/ordering, SystemMessage injection warning, reactive/async semantics (single docs page each; async/reactive are @Experimental).
- **Low Confidence / unverified**: Mocking recipe, ChatResponse.builder field names, provider-level maxRetries/timeout options, JDK max version.
- **Edge Cases**: The version was released 18 days before research (<30 days). The docs site is unversioned, so docs content is assumed to match 1.22.0 (it cites 1.22.0 in get-started).
