# Research: LangChain4j OpenAI integration (`langchain4j-open-ai`) v1.22.0, plain Java chat and streaming

> Unit: `openai`. Version-locked to **langchain4j-open-ai 1.22.0** (GitHub release dated 08 Oct; Maven Central `lastUpdated` 2026-10-07T21:48:29Z).
> Scope: `OpenAiChatModel`, `OpenAiStreamingChatModel`, their builders, `OpenAiChatRequestParameters`, the model-name enum compared with string IDs, streaming behavior, exception and retry mapping, OpenAI-compatible endpoints, a short note on Azure, and the separate `langchain4j-open-ai-official` module.
> Out of scope: the core generic API (separate unit), Anthropic, AiServices/@Tool, RAG, embeddings, images, structured output, Spring and Quarkus.
> All sources were read on **2026-10-26**. Claims without a source are tagged **(unverified)**.

## Metadata

```yaml
Full_Name: LangChain4j OpenAI integration (dev.langchain4j:langchain4j-open-ai)
Target_Version: 1.22.0
Release_Date: 2026-10-08 (GitHub release page shows "08 Oct"; Maven Central metadata lastUpdated 20261007214829)
Support_Status: Active (latest + release on Maven Central as of 2026-10-26)
Primary_Docs: https://docs.langchain4j.dev/integrations/language-models/open-ai
Official_Repo: https://github.com/langchain4j/langchain4j/tree/1.22.0/langchain4j-open-ai
Research_Date: 2026-10-26
Domain_Complexity: Standard (multi-option client, auth secret, retry/error semantics, provider-compat variants)
Research_Depth: exhaustive (sub-agent fan-out disabled by caller constraint; single-researcher fetches)
Max_Iterations: 5
Gap_Loop_Ran: true
Iterations_Used: 2 of 5
Triangulated_Count: 3
Unverified_Count: 5
Irresolvable_Count: 1
Research_Quality_Score: 88%   # approx: ~50 claims, 5 unverified, 1 irresolvable
```

## Executive Summary

`langchain4j-open-ai` 1.22.0 is LangChain4j's own Java client for the OpenAI Chat Completions REST API. The docs describe it as "a custom Java implementation of the OpenAI REST API". In plain Java it uses the JDK `java.net.http.HttpClient` by default. It provides `OpenAiChatModel` (blocking) and `OpenAiStreamingChatModel` (token streaming through a handler callback or a `Flow.Publisher`). Both are configured with Lombok-free fluent builders. The default base URL is `https://api.openai.com/v1`. The default timeouts are 15 s connect and 60 s read, and one `timeout(Duration)` call overrides both. The blocking model retries up to `maxRetries` = 2 by default. The streaming builder has **no** `maxRetries` option. Sources: `OpenAiChatModel.java`, `OpenAiStreamingChatModel.java` and `OpenAiUtils.java` at tag 1.22.0.

The release notes for 1.22.0 list only one OpenAI change: "Add OpenAI Decisions API support: OpenAiDecisionModel and OpenAiOfficialDecisionModel" (#6611). They list no breaking changes for the OpenAI modules. The most important version-specific finding is that the **`OpenAiChatModelName` enum in 1.22.0 is stale**. It stops at `GPT_5_1` and contains many IDs that OpenAI's model catalog (read 2026-10-26) marks **Shut down** (for example `gpt-3.5-turbo`, `gpt-4`, `gpt-4-turbo`, `o1`, `o3-mini`, `o4-mini`, `gpt-4.1-nano`) or **Deprecated** (`gpt-4o`, `gpt-4o-mini`, `gpt-4.1`, `gpt-5`, `gpt-5-mini`, `gpt-5.1`, `o3`). It contains none of the current flagship IDs (`gpt-6-astra`, `gpt-6.1-sol`, `gpt-6.1-terra`, `gpt-6-luna`).

There is also a separate module, `langchain4j-open-ai-official` (version `1.22.0-beta32`, so beta), built on the official `openai-java` SDK. It supports OpenAI, Microsoft Foundry/Azure (`isAzure`, passwordless auth), GitHub Models and compatible endpoints. Three patterns are critical: (1) pass model IDs as **strings** checked against the OpenAI catalog, not enum constants; (2) set an explicit `timeout`, and remember that only the blocking model retries; (3) load `apiKey` from the environment or a secret store, and keep `logRequests`/`logResponses` off in production. The domain was rated **Standard** because there is one service, but with secrets, retry and error semantics, and compatible-endpoint variants.

## Architectural Guardrails

> Confidence legend: 🟢 High (2+ official sources, dated ≤12mo) | 🟡 Medium (1 source or dated 12–24mo) | 🔴 Low (community source or dated >24mo — verify before use)

### ✅ Mandatory Patterns

**A1. Build the blocking model with an explicit API key from the environment and an explicit model ID string**
> Confidence: 🟢 High | [✓✓ Triangulated | docs open-ai page (2026-10-26) + OpenAiChatModel.java@1.22.0 (2026-10-26)]
- Why: `apiKey` and `modelName` are the mandatory settings (the docs list `api-key` and `model-name` as mandatory). `modelName(String)` exists next to `modelName(OpenAiChatModelName)`.
- Code (langchain4j-open-ai 1.22.0):
  ```java
  // langchain4j-open-ai 1.22.0
  ChatModel model = OpenAiChatModel.builder()
          .apiKey(System.getenv("OPENAI_API_KEY"))
          .modelName("gpt-6.1-sol")          // string ID; check it against the OpenAI catalog
          .build();
  String answer = model.chat("Hello");
  ```
- Source: https://docs.langchain4j.dev/integrations/language-models/open-ai (2026-10-26); https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-open-ai/src/main/java/dev/langchain4j/model/openai/OpenAiChatModel.java (2026-10-26). Model ID: https://developers.openai.com/api/docs/models (2026-10-26).
- Note **(unverified)**: the catalog does not say whether `gpt-6.*` models are served on Chat Completions (`/v1/chat/completions`), which `OpenAiChatModel` calls, or only on the Responses API. Confirm with a smoke call.

**A2. Set an explicit timeout sized to the workload and know the defaults**
> Confidence: 🟢 High | [✓✓ Triangulated | OpenAiChatModel.java + OpenAiStreamingChatModel.java @1.22.0]
- Why: the defaults are connect 15 s and read 60 s. `timeout(Duration)` sets **both** connect and read, so there is no separate read timeout on the builder. Reasoning models with long outputs can exceed 60 s **(unverified, typical behavior)**.
- Code:
  ```java
  // langchain4j-open-ai 1.22.0
  OpenAiChatModel model = OpenAiChatModel.builder()
          .apiKey(System.getenv("OPENAI_API_KEY"))
          .modelName("gpt-6.1-sol")
          .timeout(Duration.ofSeconds(120))   // applies to connect AND read
          .maxRetries(2)                      // default is 2; blocking model only
          .build();
  ```
- Source: OpenAiChatModel.java and OpenAiStreamingChatModel.java @1.22.0 (2026-10-26).

**A3. Handle typed LangChain4j exceptions, not HTTP codes**
> Confidence: 🟢 High | [✓✓ Triangulated | ExceptionMapper.java + RetryUtils.java + exception classes @1.22.0]
- Why: HTTP failures are mapped by `ExceptionMapper` as follows. 5xx → `InternalServerException`. 401/403 → `AuthenticationException` (extends `NonRetriableException`). 404 → `ModelNotFoundException`. 408 → `TimeoutException` (extends `RetriableException`). 429 → `RateLimitException` (extends `RetriableException`). Other 4xx → `InvalidRequestException`. DNS failure (`UnresolvedAddressException`) → `UnresolvedModelServerException`. Anything else is passed through if it is a `RuntimeException`, otherwise wrapped in `LangChain4jException`. `RetryUtils` rethrows `NonRetriableException` at once and retries all other exceptions.
- Code:
  ```java
  // langchain4j-open-ai 1.22.0 (exceptions in dev.langchain4j.exception)
  try {
      ChatResponse r = model.chat(ChatRequest.builder()
              .messages(UserMessage.from("Hi")).build());
  } catch (AuthenticationException e) {   // 401/403: fix the key or project, do not retry
      ...
  } catch (ModelNotFoundException e) {    // 404: wrong or retired model ID
      ...
  } catch (RateLimitException e) {        // 429: already retried maxRetries times
      ...
  } catch (InvalidRequestException e) {   // other 4xx: bad parameter for this model
      ...
  } catch (LangChain4jException e) {      // base type
      ...
  }
  ```
- Source: https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/internal/ExceptionMapper.java ; .../internal/RetryUtils.java ; .../exception/AuthenticationException.java, RateLimitException.java, TimeoutException.java (all 2026-10-26).
- Note: an empty `choices` array also raises `InternalServerException("Chat completion failed: no choices returned in response")` (OpenAiChatModel.java@1.22.0).

**A4. Streaming: always implement `onError` and do not expect automatic retries**
> Confidence: 🟡 Medium (single source: OpenAiStreamingChatModel.java@1.22.0)
- Why: the streaming builder has no `maxRetries`. On the callback path, failures are mapped through `ExceptionMapper.DEFAULT.mapException(throwable)` and passed to `handler.onError(...)`. Partial tool calls are assembled internally and emitted through `onCompleteToolCall`. Thinking tokens go to `onPartialThinking()` when `returnThinking(true)` is set.
- Code:
  ```java
  // langchain4j-open-ai 1.22.0
  StreamingChatModel streaming = OpenAiStreamingChatModel.builder()
          .apiKey(System.getenv("OPENAI_API_KEY"))
          .modelName("gpt-6.1-sol")
          .timeout(Duration.ofSeconds(120))
          .build();

  streaming.chat("Tell me a joke", new StreamingChatResponseHandler() {
      @Override public void onPartialResponse(String token) { System.out.print(token); }
      @Override public void onCompleteResponse(ChatResponse response) { /* done */ }
      @Override public void onError(Throwable error) { /* mapped LangChain4jException; retry yourself if wanted */ }
  });
  ```
- Source: https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-open-ai/src/main/java/dev/langchain4j/model/openai/OpenAiStreamingChatModel.java (2026-10-26). The exact `StreamingChatResponseHandler` method set belongs to the core unit **(cross-check there)**.

**A5. Put shared defaults in `defaultRequestParameters(OpenAiChatRequestParameters)` and override per request**
> Confidence: 🟡 Medium (docs + source agree, but the inherited builder methods were not seen directly)
- Why: `OpenAiChatRequestParameters.Builder` adds `maxCompletionTokens`, `logitBias`, `parallelToolCalls`, `seed`, `user`, `store`, `metadata`, `serviceTier`, `promptCacheKey`/`promptCacheOptions` (@since 1.21.0), `reasoningEffort`, `logprobs`, `topLogprobs`, `customParameters`, `modelName(OpenAiChatModelName)` and `overrideWith`. The docs say per-request values override defaults (stated for the Responses variant; the same merge is implied for Chat Completions by `overrideWith`).
- Code:
  ```java
  // langchain4j-open-ai 1.22.0
  OpenAiChatModel model = OpenAiChatModel.builder()
          .apiKey(System.getenv("OPENAI_API_KEY"))
          .defaultRequestParameters(OpenAiChatRequestParameters.builder()
                  .modelName("gpt-6.1-sol")
                  .maxCompletionTokens(2000)
                  .reasoningEffort("low")        // sent verbatim, no validation
                  .build())
          .build();
  ```
- Source: OpenAiChatRequestParameters.java@1.22.0; docs open-ai page; OpenAiUtils.java@1.22.0 (`.reasoningEffort(parameters.reasoningEffort())` sent as-is) (2026-10-26).

### ⚠️ Conditional Patterns

**C1. `maxTokens` or `maxCompletionTokens`**
> Confidence: 🟡 Medium
- Options: `maxTokens(Integer)` is sent as `max_tokens`, populated from `maxOutputTokens`. `maxCompletionTokens(Integer)` is sent as `max_completion_tokens`. Both are sent as given, with no conversion between them (OpenAiUtils.java@1.22.0).
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |---|---|---|---|
  | `maxCompletionTokens` | Correct for OpenAI reasoning-class models | Some compatible servers may ignore it **(unverified)** | api.openai.com with current models |
  | `maxTokens` | Wide compatibility with OpenAI-compatible servers | Rejected by OpenAI reasoning models **(unverified, OpenAI API reference not read)** | Older or compatible endpoints |

- Agent: "Ask the user which endpoint and model family they target before choosing."
- Source: OpenAiUtils.java@1.22.0 (2026-10-26).

**C2. `langchain4j-open-ai` (1.22.0, GA) or `langchain4j-open-ai-official` (1.22.0-beta32)**
> Confidence: 🟡 Medium
- Options: A) `langchain4j-open-ai`: the custom REST client (`OpenAiChatModel`), GA. B) `langchain4j-open-ai-official`: wraps the official `openai-java` SDK (`OpenAiOfficialChatModel`, `OpenAiOfficialResponsesChatModel`). Its version string is beta. It adds `isAzure(boolean)` (auto-detected when `baseUrl` ends with `openai.azure.com`; passwordless auth with `azure-identity` and the "Cognitive Services OpenAI User" role when no key is set), `isGitHubModels(boolean)` (default base URL `https://models.inference.ai.azure.com`, reads `GITHUB_TOKEN`), Responses API and Batch models.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |---|---|---|---|
  | open-ai (GA) | Stable version, few dependencies (JDK HttpClient), Chat Completions | No built-in Azure auth | Plain OpenAI or compatible endpoints with a GA requirement |
  | open-ai-official (beta) | Official SDK, Azure/Foundry/GitHub Models, Responses API | Beta version string; pulls in openai-java | Need Azure passwordless auth, GitHub Models, or the Responses API |

- Agent: "Ask whether a beta artifact is acceptable and whether Azure/Foundry or GitHub Models is a target." The docs state **no explicit recommendation**.
- Source: https://docs.langchain4j.dev/integrations/language-models/open-ai-official (2026-10-26); open-ai page (2026-10-26).

**C3. OpenAI-compatible endpoint (non-OpenAI provider)**
> Confidence: 🟡 Medium
- Options: set `baseUrl(...)` and the provider's model ID. The official example is DeepSeek: `baseUrl("https://api.deepseek.com/v1")`, `modelName("deepseek-reasoner")`, `returnThinking(true)`, which returns `reasoning_content` in `AiMessage.thinking()`. `sendThinking(true[, fieldName])` sends thinking back. The default field name is `reasoning_content`. In streaming, `accumulateToolCallId(false)` is for APIs that repeat the full tool-call ID in every chunk.
- Tradeoffs: compatibility varies by provider. `returnThinking` is documented as intended for DeepSeek.
- Agent: "Ask for the provider, its base URL and whether it returns reasoning_content."
- Source: docs open-ai page; OpenAiStreamingChatModel.java@1.22.0 (2026-10-26). The dedicated "OpenAI-Compatible" docs page URL guessed (`/open-ai-compatible`) returned 404, so its content was not read (see Gaps).

**C4. Azure OpenAI (note only)**
> Confidence: 🟡 Medium
- Options: (a) `langchain4j-open-ai-official` with `isAzure`; (b) the separate Azure OpenAI integration, which "uses the Azure SDK from Microsoft", for a Microsoft-centric stack with advanced Azure auth. Pointing `langchain4j-open-ai` at Azure by `baseUrl` alone is **(unverified)**, because Azure uses `api-key` headers and an `api-version` query parameter. `customHeaders`/`customQueryParams` exist on the builder, but no official doc confirms this use.
- Source: docs open-ai and open-ai-official pages (2026-10-26).

**C5. Request/response logging**
> Confidence: 🟡 Medium
- Options: `logRequests(true)`/`logResponses(true)` (default false), with an optional `logger(org.slf4j.Logger)` (type assumed slf4j **(unverified)**). Turn them on for debugging only.
- Source: OpenAiChatModel.java@1.22.0 (2026-10-26). Whether the API key is masked in logs is **(unverified)**.

### 🚫 Forbidden Patterns

**N1. Choosing a model from `OpenAiChatModelName` without checking the OpenAI catalog**
> Severity: High
> Confidence: 🟢 High (enum source + OpenAI catalog, both read 2026-10-26)
- Why: the 1.22.0 enum ends at `GPT_5_1`. Many of its constants are **Shut down** in OpenAI's catalog: `gpt-3.5-turbo`, `gpt-4`, `gpt-4-turbo`, `o1`, `o3-mini`, `o4-mini`, `gpt-4.1-nano`. Many others are **Deprecated**: `gpt-4o`, `gpt-4o-mini`, `gpt-4.1`, `gpt-4.1-mini`, `gpt-5`, `gpt-5-mini`, `gpt-5-nano`, `gpt-5.1`, `o3`.
- Impact: a shut-down model probably fails with 404 → `ModelNotFoundException` or 400 → `InvalidRequestException`. The exact status is **(unverified)**.
- ❌ Wrong:
  ```java
  OpenAiChatModel.builder().apiKey(key).modelName(OpenAiChatModelName.O4_MINI).build(); // shut down
  ```
- ✅ Correct:
  ```java
  OpenAiChatModel.builder().apiKey(key).modelName("gpt-6.1-sol").build(); // current catalog ID, 2026-10-26
  ```
- Source: OpenAiChatModelName.java@1.22.0; https://developers.openai.com/api/docs/models/all (2026-10-26).

**N2. Hardcoding the API key**
> Severity: Critical
> Confidence: 🟡 Medium (general secret hygiene; the docs examples use variables or env)
- ❌ Wrong: `.apiKey("sk-proj-abc...")`
- ✅ Correct: `.apiKey(System.getenv("OPENAI_API_KEY"))`, or a secret manager.
- Impact: the key leaks through VCS or logs.
- Source: docs open-ai-official sample uses `System.getenv("OPENAI_API_KEY")` (2026-10-26).

**N3. Expecting `maxRetries` on the streaming model, or retrying after an `AuthenticationException`**
> Severity: Medium
> Confidence: 🟢 High (source)
- ❌ Wrong:
  ```java
  OpenAiStreamingChatModel.builder().maxRetries(3)  // does not compile in 1.22.0: no such method
  ```
- ✅ Correct:
  ```java
  // retry in your own onError for RetriableException subtypes only
  if (error instanceof RetriableException) scheduleRetry(); else fail(error);
  ```
- Impact: compile error, or wasted calls on 401/403.
- Source: OpenAiStreamingChatModel.java, RetryUtils.java, AuthenticationException.java @1.22.0 (2026-10-26).

**N4. Leaving `logRequests`/`logResponses` on in production**
> Severity: High
> Confidence: 🟡 Medium
- ❌ Wrong: `.logRequests(true).logResponses(true)` in production builds.
- ✅ Correct: `.logRequests(Boolean.getBoolean("llm.debug"))`, off by default.
- Impact: prompts and completions (possibly PII) are written to logs. Masking of the key is **(unverified)**.
- Source: OpenAiChatModel.java@1.22.0 defaults false (2026-10-26).

**N5. Mixing the `-official` beta artifact version with the GA line, or treating them as the same classes**
> Severity: Medium
> Confidence: 🟡 Medium
- ❌ Wrong: `langchain4j-open-ai-official:1.22.0`, and expecting `OpenAiChatModel` inside it.
- ✅ Correct: `langchain4j-open-ai-official:1.22.0-beta32` → `OpenAiOfficialChatModel`; or `langchain4j-open-ai:1.22.0` → `OpenAiChatModel`.
- Source: docs open-ai and open-ai-official pages (2026-10-26).

## Migration Guide

> Confidence: 🟡 Medium | Source: https://github.com/langchain4j/langchain4j/releases/tag/1.22.0 (2026-10-26)

**Breaking Changes**: none listed for the OpenAI modules in 1.22.0. The new feature is `OpenAiDecisionModel` / `OpenAiOfficialDecisionModel` (Decisions API, #6611, outside this unit's scope). From the source: `promptCacheKey`/`promptCacheOptions` @since 1.21.0, and `streamingBufferSize` @since 1.20.0 (`@Experimental`; overflow ends the stream with `IllegalStateException`). No `@Deprecated` methods exist in either model class.

**Upgrade Steps**:
1. Bump `dev.langchain4j:langchain4j-open-ai` to `1.22.0` (aligning with the core version is covered by the core unit).
2. Replace enum model constants with catalog string IDs (N1).
3. Re-run smoke tests with the new model IDs (A1 note).

**Compatibility Matrix**:

| Dependency | Version | Notes |
|---|---|---|
| langchain4j-open-ai | 1.22.0 | GA; latest on Maven Central (2026-10-26) |
| langchain4j-open-ai-official | 1.22.0-beta32 | beta |
| Java | (unverified) | minimum JDK not read in this unit; see core unit |

## Implementation Blueprint

> Confidence: 🟢 High | [✓✓ docs + source]

**Dependency**:
```xml
<!-- langchain4j-open-ai 1.22.0 -->
<dependency>
  <groupId>dev.langchain4j</groupId>
  <artifactId>langchain4j-open-ai</artifactId>
  <version>1.22.0</version>
</dependency>
```

**Full builder surface (OpenAiChatModel, 1.22.0)**: `httpClientBuilder`, `baseUrl` (default `https://api.openai.com/v1`), `apiKey`, `organizationId`, `projectId`, `timeout` (default connect 15 s/read 60 s), `maxRetries` (default 2), `logRequests`/`logResponses` (default false), `logger`, `customHeaders(Map | Supplier<Map>)`, `customQueryParams`, `customParameters`, `listeners`, `defaultRequestParameters`, `modelName(String | OpenAiChatModelName)`, `temperature`, `topP`, `stop`, `maxTokens`, `maxCompletionTokens`, `presencePenalty`, `frequencyPenalty`, `logitBias`, `seed`, `user`, `store`, `metadata`, `serviceTier`, `reasoningEffort` (String, sent verbatim), `logprobs`, `topLogprobs`, `parallelToolCalls`, `promptCacheKey`, `promptCacheOptions`, `responseFormat`, `supportedCapabilities`, `strictJsonSchema`/`strictTools` (default false), `returnThinking` (default false), `sendThinking(Boolean[, String])` (default false, `reasoning_content`), `useInputImageFormat` (default false). User-Agent default `langchain4j-openai`.

**Streaming-only additions**: `accumulateToolCallId` (default true), `streamingBufferSize` (@Experimental, default constant value not shown). There is **no** `maxRetries`.

**Lifecycle**:
```java
// langchain4j-open-ai 1.22.0. Build once and reuse (the model holds an HTTP client).
OpenAiChatModel model = OpenAiChatModel.builder()
        .apiKey(System.getenv("OPENAI_API_KEY"))
        .projectId(System.getenv("OPENAI_PROJECT_ID"))   // optional
        .modelName("gpt-6.1-sol")
        .temperature(0.2)          // some reasoning models may reject temperature (unverified)
        .maxCompletionTokens(1000)
        .timeout(Duration.ofSeconds(90))
        .build();
ChatResponse r = model.chat(ChatRequest.builder().messages(UserMessage.from("Hi")).build());
System.out.println(r.aiMessage().text());
```
Thread-safety and reuse of a single instance: **(unverified)**. This is probably safe because the client is immutable, but no doc states it.

## Quality Control

```bash
# Representative — adapt to your environment
mvn -q dependency:tree -Dincludes=dev.langchain4j:langchain4j-open-ai   # expect 1.22.0
grep -rn "OpenAiChatModelName\." src/main/java                        # expect no matches (N1)
grep -rn 'apiKey("sk-' src/                                            # expect no matches (N2)
```
**Mocking**: point `baseUrl` at a local stub server (for example WireMock) that returns Chat Completions JSON, or mock the `ChatModel` interface. The docs do not show this pattern, so it is **(unverified)**.

## Production Readiness

- **Performance**: default read timeout is 60 s; size it per model. The streaming buffer is configurable (experimental).
- **Resilience**: the blocking model uses up to 2 retries. Backoff starts at about 500 ms base with a ×1.5 exponent and 20% jitter (DEFAULT_RETRY_POLICY). Note that the model uses `withRetryMappingExceptions(..., maxRetries)`; whether that call uses the 500 ms or 1000 ms base delay is not confirmed **(unverified)**. Streaming has no retries.
- **Monitoring**: `listeners(ChatModelListener...)` provides request/response/error hooks (the listener API belongs to the core unit).
- **Security**: key from the environment or a secret store; logging off; `organizationId`/`projectId` for scoping; `customHeaders(Supplier)` for rotating proxy tokens (documented for the Responses model; present on the `OpenAiChatModel` builder too).

## Reference Implementations

- Official docs: https://docs.langchain4j.dev/integrations/language-models/open-ai
- Official docs (SDK-based): https://docs.langchain4j.dev/integrations/language-models/open-ai-official
- Source @1.22.0: https://github.com/langchain4j/langchain4j/tree/1.22.0/langchain4j-open-ai
- Examples repo (langchain4j-examples): not read **(unverified)**

## Source Bibliography

**Primary** (all read 2026-10-26):
- LangChain4j docs, OpenAI: https://docs.langchain4j.dev/integrations/language-models/open-ai
- LangChain4j docs, OpenAI Official SDK: https://docs.langchain4j.dev/integrations/language-models/open-ai-official
- Release 1.22.0 (dated 08 Oct): https://github.com/langchain4j/langchain4j/releases/tag/1.22.0
- Maven Central metadata (latest/release 1.22.0, lastUpdated 2026-10-07): https://repo1.maven.org/maven2/dev/langchain4j/langchain4j-open-ai/maven-metadata.xml
- OpenAI models (redirected from platform.openai.com/docs/models): https://developers.openai.com/api/docs/models and https://developers.openai.com/api/docs/models/all

**Source code @ tag 1.22.0** (read 2026-10-26):
- https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-open-ai/src/main/java/dev/langchain4j/model/openai/OpenAiChatModel.java
- https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-open-ai/src/main/java/dev/langchain4j/model/openai/OpenAiStreamingChatModel.java
- https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-open-ai/src/main/java/dev/langchain4j/model/openai/OpenAiChatModelName.java
- https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-open-ai/src/main/java/dev/langchain4j/model/openai/OpenAiChatRequestParameters.java
- https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-open-ai/src/main/java/dev/langchain4j/model/openai/internal/OpenAiUtils.java
- https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/internal/ExceptionMapper.java
- https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/internal/RetryUtils.java
- https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/exception/AuthenticationException.java
- https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/exception/RateLimitException.java
- https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/exception/TimeoutException.java

**Validation**: no community sources used.

## Research Gaps

```
Gap: Whether gpt-6.* catalog models are available on Chat Completions (vs Responses-only)
Impact: OpenAiChatModel may fail for current flagship IDs
Workaround: smoke-test; fall back to gpt-5.5 / gpt-5.4 (catalog, not marked deprecated) or use the Responses model
Follow-up: per-model pages under developers.openai.com/api/docs/models/<id>
§7-ref: Iteration 2 — IRRESOLVABLE (within this run)

Gap: OpenAI-compatible docs page content (URL /open-ai-compatible returned 404)
Impact: provider caveats beyond DeepSeek not captured
Follow-up: docs sidebar link to "OpenAI-Compatible Language Models"

Gap: max_tokens rejection for reasoning models; temperature support per model; log key masking; thread-safety; minimum JDK
Impact: medium; tagged (unverified) inline
Follow-up: OpenAI API reference (chat/create); core unit research
```

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|---|---|---|---|---|
| 1 | Guardrails | Current model IDs (platform.openai.com 301) | Resolved by following the redirect | https://developers.openai.com/api/docs/models/all (2026-10-26) |
| 1 | Guardrails | Retriable vs non-retriable exceptions | Resolved | AuthenticationException/RateLimitException/TimeoutException.java @1.22.0 (2026-10-26) |
| 2 | Guardrails | gpt-6.* on Chat Completions | ⚠️ IRRESOLVABLE — catalog does not state endpoint support; human smoke test required | — |
| 2 | Guardrails | OpenAI-compatible page | Unresolved — guessed URL 404 | — |

## Completion Checklist

- [x] Domain complexity tier assessed and documented (Standard)
- [x] All scope areas cited
- [x] Pattern counts driven by domain needs
- [x] Every anti-pattern has an alternative
- [x] All CLI commands marked representative
- [x] Integration examples complete (OpenAI, compatible endpoints, Azure note)
- [x] Sources dated and linked
- [x] Security documented
- [x] 1+ copy-paste working example (A1; model ID requires smoke test)
- [x] Confidence badge applied to every pattern entry
- [x] Single-source Always-Do patterns downgraded to 🟡 (A4, A5)
- [x] Research Iteration Changelog present
- [x] Research_Quality_Score in Metadata
- [x] Gaps cross-referenced

## Agent Operation Notes

- **High Confidence**: builder option names and defaults, exception mapping, retry semantics, enum contents, artifact coordinates (A1–A3, N1, N3).
- **Medium Confidence**: streaming error flow details, request-parameter merge, the official-module choice, compatible endpoints, the Azure note.
- **Low / ask human**: whether current flagship model IDs work on Chat Completions (IRRESOLVABLE); Azure via plain `langchain4j-open-ai`.
- **Edge cases**: 1.22.0 was released 18 days before the research date (<30 days), so the docs may still change.
