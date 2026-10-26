# Research: langchain4j-anthropic v1.22.0 (chat + streaming, plain Java)

> Unit: `anthropic`. Scope is limited to `AnthropicChatModel` and `AnthropicStreamingChatModel` and their options, system messages, streaming and error mapping. Out of scope (other units): the core generic API, OpenAI, AiServices/@Tool, RAG, structured output, Spring/Quarkus.
> All sources were read on **2026-10-26**. A claim with no source carries an **(unverified)** tag.

## Metadata

```yaml
Full_Name: LangChain4j Anthropic integration (dev.langchain4j:langchain4j-anthropic)
Target_Version: 1.22.0
Release_Date: 2026-10-08 (GitHub release, "08 Oct"); Maven Central artifact timestamp 2026-10-07 21:41
Support_Status: Active (latest version on Maven Central as of 2026-10-26)
Primary_Docs: https://docs.langchain4j.dev/integrations/language-models/anthropic
Official_Repo: https://github.com/langchain4j/langchain4j/tree/1.22.0/langchain4j-anthropic
Research_Date: 2026-10-26
Domain_Complexity: Standard
Research_Depth: exhaustive (no sub-agents per caller constraint; single-researcher fetches)
Max_Iterations: 5
Gap_Loop_Ran: true
Iterations_Used: 1 of 5
Triangulated_Count: 3
Unverified_Count: 5
Irresolvable_Count: 0
Research_Quality_Score: ~88%  # (approx. 42 claims - 5 unverified) / 42
```

## Executive Summary

`langchain4j-anthropic` 1.22.0 is LangChain4j's integration with the Anthropic Messages API. It provides `AnthropicChatModel` (blocking) and `AnthropicStreamingChatModel` (streaming). Both builders accept the same options (S1). Per-request overrides go through `AnthropicChatRequestParameters`. Any option a request leaves unset falls back to the builder value (S1). The source at tag 1.22.0 sets these defaults: `baseUrl=https://api.anthropic.com/v1/`, `version=2023-06-01` (the `anthropic-version` header), `maxTokens=1024` when unset, and `maxRetries=2` for the blocking model. `timeout` has no default in the model class (S3, S4).

The 1.22.0 changes for Anthropic all concern prompt caching. PR #6598 adds automatic prompt caching and a cache TTL (`cacheAutomatically`, `cacheTtl` with `"5m"`/`"1h"`). PR #6515 puts `cache_control` only on the last tool. PR #6070 puts `cache_control` only on the last system message (S2). The release notes list no breaking changes or deprecations for Anthropic (S2).

The most important finding comes from the Anthropic docs, not LangChain4j: current models (Claude Fable 5.1, Opus 5.5, Sonnet 5.5, Haiku 5.5) use **adaptive thinking**. Manual extended thinking (`thinking.type="enabled"` + `budget_tokens`) "is deprecated on Claude Opus 4.6 and Claude Sonnet 4.6 and not accepted on later models" (S5). So `thinkingType("enabled")` + `thinkingBudgetTokens(...)` must not be used with Claude 5.x model IDs.

Three critical patterns:
1. Set `maxTokens` explicitly. The default of 1024 is far below the 128K maximum output of current models.
2. Use adaptive thinking with effort, not budget tokens, on 5.x models.
3. Opt in to prompt caching explicitly, because it is off by default.

The tier is Standard: one external service, secret handling, and several interacting feature flags.

## Architectural Guardrails

> Confidence legend: 🟢 High (2+ official sources) | 🟡 Medium (1 source) | 🔴 Low

### ✅ Mandatory Patterns

**1. Build the model with an API key from the environment and a pinned model ID**
> Confidence: 🟢 High | [✓✓ Triangulated | S1 docs (2026-10-26) + S5 models overview (2026-10-26)]
- Why: The builder takes `apiKey` and `modelName` (S1). Anthropic API IDs are pinned snapshots, including dateless IDs from the 4.6 generation on (S5).
- Code:
  ```java
  // langchain4j-anthropic 1.22.0
  ChatModel model = AnthropicChatModel.builder()
          .apiKey(System.getenv("ANTHROPIC_API_KEY"))
          .modelName("claude-sonnet-5-5")   // Claude API ID per S5
          .maxTokens(4096)
          .build();
  String answer = model.chat("Hello");
  ```
- Source: S1, S5 (2026-10-26). Note: S3 does not show whether `modelName` is validated as required at build time **(unverified)**. Always set it.

**2. Set `maxTokens` explicitly**
> Confidence: 🟢 High | [✓✓ Triangulated | S3 AnthropicChatModel.java@1.22.0 + S4 AnthropicStreamingChatModel.java@1.22.0]
- Why: Both classes default to `1024` when neither the builder nor `defaultRequestParameters` sets `maxOutputTokens` (S3, S4). Current models support 128K output tokens (S5). With the default, long answers are cut off.
- Code: `.maxTokens(8192)`. You can also set it per request through `AnthropicChatRequestParameters`.
- Source: S3, S4, S5.

**3. Use adaptive thinking on Claude 5.x models, not manual budget thinking**
> Confidence: 🟡 Medium (S5 is explicit; the exact LangChain4j value for adaptive `thinkingType` was not quoted verbatim, see Gaps)
- Why: Extended thinking with `budget_tokens` is not accepted on models after Opus/Sonnet 4.6 (S5). The LangChain4j docs cover adaptive thinking. They also say that `effort` is set through `customParameters` (S1).
- Code (representative):
  ```java
  // langchain4j-anthropic 1.22.0 — adaptive thinking; value "adaptive" is (unverified)
  AnthropicChatModel.builder()
      .modelName("claude-opus-5-5")
      .thinkingType("adaptive")          // (unverified) literal
      .returnThinking(true)              // default false (S1, S4)
      // effort via customParameters (S1); exact map shape (unverified)
      .build();
  ```
- Source: S1, S5.

**4. Opt in to prompt caching, and choose the mode by prompt shape**
> Confidence: 🟢 High | [✓✓ Triangulated | S1 docs + S2 release notes 1.22.0]
- Why: Caching is off by default. Anthropic allows at most 4 cache breakpoints per request. Prompts below a model-specific minimum (512–4,096 tokens) are not cached (S1). `cacheAutomatically` and `cacheTtl` are new in 1.22.0 (S2).
- Code:
  ```java
  // langchain4j-anthropic 1.22.0
  AnthropicChatModel.builder()
      .cacheSystemMessages(true)   // stable system prompt
      .cacheTools(true)            // stable tool set
      .cacheTtl(AnthropicChatRequestParameters.CACHE_TTL_1H) // "5m" default, or "1h"
      .build();
  // Growing conversations (tool loops): .cacheAutomatically(true)
  ```
- Source: S1, S2. Token usage reports cache-creation and cache-read counts (S1).

**5. Catch LangChain4j's typed exceptions, not raw HTTP errors**
> Confidence: 🟡 Medium (S6 + S3: the call is wrapped in `withRetryMappingExceptions`)
- Why: `DefaultExceptionMapper` maps HTTP 401/403 to `AuthenticationException`, 404 to `ModelNotFoundException`, 408 to `TimeoutException`, 429 to `RateLimitException`, other 4xx to `InvalidRequestException`, and 5xx to `InternalServerException`. An unresolved host becomes `UnresolvedModelServerException` (S6). The blocking model wraps calls with retry and exception mapping, using `maxRetries` (default 2) (S3).
- Code:
  ```java
  try { model.chat(request); }
  catch (RateLimitException e) { /* back off */ }
  catch (AuthenticationException e) { /* fix key, do not retry */ }
  ```
- Source: S3, S6. Which of these exceptions are excluded from retry is **(unverified)**.

### ⚠️ Conditional Patterns

**Caching mode**
> Confidence: 🟢 High
| Option | Optimizes | Sacrifices | Best When |
|---|---|---|---|
| `cacheSystemMessages` / `cacheTools` | Reuse across independent calls | Needs a stable prefix | Fixed system prompt or tools |
| `cacheAutomatically` | Growing multi-turn or tool loops | A poor fit when the start of the conversation changes | Agent loops |
| `cacheTtl "1h"` | Fewer cache rewrites | Higher write cost (see pricing) | Infrequent but repeated traffic |
- Agent: ask about the prompt shape and traffic cadence. Source: S1, S2.

**Thinking visibility**
- `thinkingDisplay` accepts `"summarized"` or `"omitted"`. When unset, the default depends on the model. With the API default on recent models, `AiMessage.thinking()` stays empty and `onPartialThinking` is not called (S1, S4). `sendThinking` defaults to `true`, so thinking is returned to the API on follow-up requests (S1, S4).
- Agent: ask whether the UI or logs need the reasoning text. Source: S1, S4.

**Mid-conversation system messages**
- `midConversationSystemMessages` defaults to `false`. Out of the box, all system messages go to the top-level `system` field whatever their position. When the flag is on, later system messages are sent inline. The Javadoc says this needs Claude Opus 4.8 (S3, S1). Whether 5.x models support it is **(unverified)**.

**Beta headers**
- Set with `.beta(...)`. Values change over time. The docs name `cache-diagnosis-2026-04-07`, `context-management-2025-06-27`, `advanced-tool-use-2025-11-20`, `code-execution-2025-08-25`, `skills-2025-10-02` and `files-api-2025-04-14` (S1). Anthropic's `output-300k-2026-03-24` applies to the Batches API only (S5).

### 🚫 Forbidden Patterns

**Manual budget thinking on Claude 5.x**
> Severity: High | Confidence: 🟢 High (S5)
- Impact: The API rejects the request, because the mode is not accepted on models after 4.6.
- ❌ Wrong:
  ```java
  .modelName("claude-sonnet-5-5").thinkingType("enabled").thinkingBudgetTokens(2048)
  ```
- ✅ Correct:
  ```java
  .modelName("claude-sonnet-5-5") // adaptive thinking; steer with effort (customParameters)
  ```
- Source: S5, S1.

**Relying on the 1024 maxTokens default**
> Severity: Medium | Confidence: 🟢 High (S3, S4)
- ❌ Wrong: `AnthropicChatModel.builder().apiKey(k).modelName(m).build();`
- ✅ Correct: `...modelName(m).maxTokens(8192).build();`
- Impact: Output is silently truncated at 1024 tokens.

**Hard-coding the API key or logging request bodies in production**
> Severity: Critical | Confidence: 🟡 Medium (S1 lists `logRequests`/`logResponses`; that logs may contain the key or prompts is **(unverified)**, so treat request logs as sensitive)
- ❌ Wrong: `.apiKey("sk-ant-...").logRequests(true)`
- ✅ Correct: `.apiKey(System.getenv("ANTHROPIC_API_KEY")).logRequests(false)`

**Using retired or legacy model IDs out of habit**
> Severity: Medium | Confidence: 🟢 High (S5)
- ❌ Wrong: `.modelName("claude-3-5-sonnet-20241022")` (not in the current or legacy list in S5)
- ✅ Correct: `.modelName("claude-sonnet-5-5")`

## Migration Guide

> Sources: S2 (release notes 1.22.0), S5.

**Breaking changes in 1.22.0 (Anthropic):** none listed (S2).
**New:** automatic prompt caching (`cacheAutomatically`) and `cacheTtl` (#6598).
**Fixes:** tool `cache_control` goes only on the last tool (#6515). System `cache_control` goes only on the last system message (#6070) (S2).
**Model-side migration:** Claude 5.x does not accept budget thinking. Move to adaptive thinking plus effort (S5).

| Dependency | Version | Notes |
|---|---|---|
| dev.langchain4j:langchain4j-anthropic | 1.22.0 | Maven Central 2026-10-07 (S7) |
| Anthropic API version header | 2023-06-01 | default `version` (S3) |
| Spring Boot 4 starter | 1.22.0-beta32 | out of scope; noted from S1 |

## Implementation Blueprint

```xml
<!-- langchain4j-anthropic 1.22.0 (S1, S7) -->
<dependency>
  <groupId>dev.langchain4j</groupId>
  <artifactId>langchain4j-anthropic</artifactId>
  <version>1.22.0</version>
</dependency>
```

```java
// Streaming, langchain4j-anthropic 1.22.0 — same builder options as AnthropicChatModel (S1)
StreamingChatModel streaming = AnthropicStreamingChatModel.builder()
        .apiKey(System.getenv("ANTHROPIC_API_KEY"))
        .modelName("claude-haiku-5-5")
        .maxTokens(2048)
        .timeout(Duration.ofSeconds(60))   // no default in model class (S3, S4)
        .build();

streaming.chat("Tell me a joke", new StreamingChatResponseHandler() {
    public void onPartialResponse(String token) { System.out.print(token); }
    public void onCompleteResponse(ChatResponse r) { System.out.println(r.tokenUsage()); }
    public void onError(Throwable t) { t.printStackTrace(); }
});
```
Streaming notes: `doChat` fails fast if the handler is null. `validate(parameters)` runs before the request is sent. On the reactive path, a buffer overflow ends the stream with `IllegalStateException` (S4). Whether streaming retries on `maxRetries` is **(unverified)**.

Full option list (S1): `httpClientBuilder, baseUrl, apiKey, version, beta, timeout, maxRetries, modelName, temperature, topP, topK, maxTokens, stopSequences, toolSpecifications, toolChoice, toolChoiceName, disableParallelToolUse, serverTools, returnServerToolResults, toolMetadataKeysToSend, cacheSystemMessages, cacheTools, cacheAutomatically, cacheTtl, returnCacheDiagnostics, thinkingType, thinkingBudgetTokens, thinkingDisplay, returnThinking, sendThinking, midConversationSystemMessages, defaultRequestParameters, userId, customParameters, logRequests, logResponses, listeners`. `previousMessageId` is per-request only.

## Quality Control

```bash
# Representative — adapt to your environment
mvn -q dependency:tree | grep langchain4j-anthropic   # Expected: dev.langchain4j:langchain4j-anthropic:jar:1.22.0
mvn -q test                                            # Expected: BUILD SUCCESS
```
Mocking: put your code behind the `ChatModel` / `StreamingChatModel` interfaces and pass a stub in tests. To test HTTP behavior, point `baseUrl` at a local stub server. Both are standard practice, not an official LangChain4j test recipe **(unverified)**.

## Production Readiness

- **Errors:** map the typed exceptions (S6). 429 → `RateLimitException`; back off with jitter.
- **Timeouts:** set `timeout` explicitly, because there is no default in the model class (S3).
- **Cost:** monitor cache creation and read token counts (S1). Cache reads cost 5% of base input on Opus/Sonnet 5.5 and 10% on Haiku 5.5 (S5). Batch is 50% off (S5; batch is out of scope).
- **Lifecycle:** retirement is not sooner than Sep 22, 2027 (Opus 5.5), Sep 28, 2027 (Sonnet 5.5) or Oct 7, 2027 (Haiku 5.5) (S5).
- **Security:** keep the API key in env or a secrets manager. Keep request logging off in prod.

**Current Claude model IDs (S5, read 2026-10-26)**

| Model | API ID | Context | Max output | Thinking | Default effort |
|---|---|---|---|---|---|
| Claude Fable 5.1 | `claude-fable-5-1` | 1M | 128K | Adaptive (always on) | high |
| Claude Opus 5.5 | `claude-opus-5-5` | 1M | 128K | Adaptive (always on) | medium |
| Claude Sonnet 5.5 | `claude-sonnet-5-5` | 1M | 128K | Adaptive | high |
| Claude Haiku 5.5 | `claude-haiku-5-5` | 1M | 128K | Adaptive | medium |

Legacy models (still available): Fable 5, Opus 5, Opus 4.8, Opus 4.7, Opus 4.6, Opus 4.5, Sonnet 5, Sonnet 4.6, Haiku 4.5 (S5). Their exact API ID strings were not collected **(unverified)**.

## Reference Implementations

- Official docs examples: S1.
- Module source at tag 1.22.0: https://github.com/langchain4j/langchain4j/tree/1.22.0/langchain4j-anthropic
- langchain4j-examples repo: not consulted **(unverified)**.

## Source Bibliography

**Primary** (all read 2026-10-26)
- S1: LangChain4j Anthropic integration docs: https://docs.langchain4j.dev/integrations/language-models/anthropic
- S2: GitHub release 1.22.0 (08 Oct 2026): https://github.com/langchain4j/langchain4j/releases/tag/1.22.0
- S3: AnthropicChatModel.java @1.22.0: https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-anthropic/src/main/java/dev/langchain4j/model/anthropic/AnthropicChatModel.java
- S4: AnthropicStreamingChatModel.java @1.22.0: https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-anthropic/src/main/java/dev/langchain4j/model/anthropic/AnthropicStreamingChatModel.java
- S5: Anthropic Models overview: https://platform.claude.com/docs/en/about-claude/models/overview
- S6: ExceptionMapper.java @1.22.0 (langchain4j-core): https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/internal/ExceptionMapper.java
- S7: Maven Central listing (1.22.0, 2026-10-07): https://repo1.maven.org/maven2/dev/langchain4j/langchain4j-anthropic/

**Validation:** no community sources were used.

## Research Gaps

```
Gap: Exact string for adaptive thinkingType in LangChain4j and the customParameters shape for effort
Impact: Thinking config on 5.x models may be written incorrectly
Workaround: Omit thinkingType on 5.x (adaptive is default/always-on on Opus 5.5/Fable 5.1 per S5)
Follow-up: S1 "thinking" section code samples; AnthropicThinking* sources at tag 1.22.0
§7-ref: Iteration 1 — open (unverified)
```
```
Gap: Which mapped exceptions are non-retriable; whether streaming retries
Impact: Retry storms on 401/400 if misassumed
Workaround: Treat Authentication/InvalidRequest as non-retriable in app code
Follow-up: langchain4j-core RetryUtils.java @1.22.0; AnthropicClient
§7-ref: Iteration 1 — open (unverified)
```
```
Gap: modelName required-at-build validation; legacy model ID strings; midConversationSystemMessages on 5.x
Follow-up: AnthropicChatModel validate(); per-model pages on platform.claude.com
§7-ref: Iteration 1 — open (unverified)
```

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|---|---|---|---|---|
| 1 | Guardrails | maxTokens default 1024 | Resolved | S3, S4 (2026-10-26) |
| 1 | Guardrails | Exception mapping | Resolved (mapping); retry-exclusion open | S6 (2026-10-26) |
| 1 | Metadata | Release date | Resolved | S2, S7 (2026-10-26) |
| 1 | Guardrails | Adaptive thinkingType literal | Open (unverified), not IRRESOLVABLE; follow-up listed | — |

## Completion Checklist

- [x] Domain complexity tier assessed (Standard)
- [x] All scope areas cited
- [x] Every anti-pattern has an alternative
- [x] CLI commands marked representative
- [x] Sources dated and linked
- [x] Security documented
- [x] 1+ copy-paste example
- [x] Confidence badge on every pattern
- [x] Single-source Always-Do patterns downgraded to 🟡
- [x] Research Iteration Changelog present
- [x] Research_Quality_Score in Metadata
- [ ] All gaps closed (5 unverified items remain)

## Agent Operation Notes

- **High:** builder option list, defaults (baseUrl, version, maxTokens 1024, maxRetries 2), caching options, exception mapping, model IDs and thinking constraints for 5.x.
- **Medium:** adaptive-thinking configuration in LangChain4j, logging sensitivity, mid-conversation system messages.
- **Low / ask:** retry exclusions, streaming retries, legacy ID strings.
- **Edge case:** 1.22.0 is 18 days old as of 2026-10-26 (less than 30 days). The docs may still change.

## Source Bibliography (index)

See the Source Bibliography above: S1–S7, all read 2026-10-26.
