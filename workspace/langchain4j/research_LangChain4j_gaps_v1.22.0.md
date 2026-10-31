# Research Gaps — LangChain4j 1.22.0 (core, open-ai, anthropic, open-ai-official 1.22.0-beta32)

> Mode: gap-closing, depth=standard. All sources read on **2026-10-26**.
> Amends (does not replace): `research_LangChain4j_core_v1.22.0.md` (CORE), `research_LangChain4j_openai_v1.22.0.md` (OPENAI), `research_LangChain4j_anthropic_v1.22.0.md` (ANTHROPIC).
> Approval: relay of user approval of 2026-10-26 recorded in `PIPELINE_STATE.md#approvals`.
> Caveat: docs.langchain4j.dev pages are unversioned (they track the current release, 1.22.0 at read time). GitHub source was read at tag `1.22.0`.

## Gap Resolution Table

| # | Item | Resolution | Source | Status | Amends |
|---|------|-----------|--------|--------|--------|
| 1 | gpt-6.* on Chat Completions vs Responses only | **Chat Completions is supported.** The model pages for gpt-6-astra and gpt-6-luna list `v1/chat/completions`, `v1/responses` and `v1/batch`. The gpt-6.1-sol page also lists Chat Completions. The "Using GPT-6" guide says: "GPT-6 Astra, GPT-6.1 Sol, and GPT-6.1 Terra support Chat Completions, but tool calling requires Responses." GPT-6 Sol and GPT-6 Luna allow function calling on Chat Completions only with `reasoning_effort: "none"`. **Impact:** `OpenAiChatModel` with tools against gpt-6-astra, gpt-6.1-sol or gpt-6.1-terra will not work. Use the Responses API or another model. | S1, S2, S3, S4 | VERIFIED (gpt-6.1-terra only through the guide, its model page was not opened) | OPENAI |
| 2 | Reasoning models: max_tokens / temperature | **`max_tokens` is deprecated** in favor of `max_completion_tokens` and "is not compatible with o-series models". `max_completion_tokens` counts both visible and reasoning tokens. For GPT-6: "When reasoning effort is not `none`, remove `temperature`, `top_p`, and `top_logprobs`." Chat Completions also needs `logprobs` removed. **Use `maxCompletionTokens`** and leave out `temperature` unless effort is `none`. | S5 (quote taken from the search snippet; the page returned 404 on direct fetch), S2 | VERIFIED for temperature (GPT-6). max_tokens: VERIFIED for o-series wording only; a GPT-6-specific statement about rejection of `max_tokens` was not found | OPENAI |
| 3 | Anthropic adaptive thinking + effort | **LangChain4j:** `.thinkingType("adaptive")`, optionally `.thinkingDisplay("summarized"\|"omitted")`. There is no `effort` builder method. Effort goes through `.customParameters(Map.of("output_config", Map.of("effort", "max")))`. In the `AnthropicChatModel` source at 1.22.0, `thinkingType` is a plain `String`, and `toThinking(type, budgetTokens, display)` builds the object only when the type or budget is set. **Anthropic API:** `"thinking": {"type": "adaptive"}`. Effort sits at top level, `"output_config": {"effort": "low\|medium\|high\|xhigh\|max"}`, and "not inside the `thinking` object". The default is `high` on most models and `medium` on Opus 5.5 and Haiku 5.5. Level availability differs by model. `"enabled"` + `budget_tokens` is deprecated on 4.6+ models. | S6, S7, S8, S9 | VERIFIED | ANTHROPIC |
| 4 | modelName required at build time? | **No build-time check in either constructor.** Both use `.modelName(getOrDefault(builder.modelName, commonParameters.modelName()))` with no `ensureNotBlank`. A missing name would surface at request time, either from request validation or from the API. Whether `OpenAiUtils.validate(...)` checks modelName per request was not read. | S7, S10 | VERIFIED (no build-time check); request-time validation UNVERIFIED | ANTHROPIC, OPENAI |
| 5 | RetryUtils behavior | `withRetryMappingExceptions(action, maxRetries)` maps exceptions through `ExceptionMapper.DEFAULT` and then uses `DEFAULT_RETRY_POLICY`. That means a **500 ms** base delay, backoffExp 1.5 and jitter 0.2. The builder's 1000 ms is only the `Builder` field default, and `DEFAULT_RETRY_POLICY` overrides it. `NonRetriableException` is rethrown immediately. **Not retried:** `ModelNotFoundException` (HTTP 404) and `UnresolvedModelServerException` (UnresolvedAddressException) both extend `NonRetriableException`. `ContentFilteredException` extends `InvalidRequestException`. Whether `InvalidRequestException` is non-retriable was not read, but it is likely, since 4xx maps to it. Mapping: 5xx→InternalServer, 401/403→Authentication, 404→ModelNotFound, 408→Timeout, 429→RateLimit, other 4xx→InvalidRequest. **Streaming:** `AnthropicStreamingChatModel` has no `maxRetries` and no `withRetry` call, so it does not retry. Blocking `doChat` and async `doChatAsync` (Anthropic and OpenAI) both retry, defaulting to maxRetries=2. | S11, S12, S13, S14, S15, S7, S10, S16 | VERIFIED (InvalidRequestException hierarchy UNVERIFIED; OpenAI streaming model file not re-read, so the earlier "no retries" claim in OPENAI still rests on the first round) | CORE, OPENAI, ANTHROPIC |
| 6 | Provider modules bring core transitively? | **Yes.** In both pom.xml files at 1.22.0, `langchain4j-core` and `langchain4j-http-client` are compile scope (no scope element), and `langchain4j-http-client-jdk` is runtime scope. | S17, S18 | VERIFIED | CORE |
| 7 | API key masked in logRequests? | **Yes, headers are masked.** `HttpRequestLogger` masks any header whose lowercase name contains a secret keyword. `authorization` and `x-api-key`/`api-key` match. Values of 7+ characters show the first 5 and last 2 characters (`abcde...yz`), and shorter values show `...`. **The request body is logged unmasked,** so prompts and PII still appear in logs. Logging goes to an SLF4J `org.slf4j.Logger` at INFO. The `logger(Logger)` builder option takes an `org.slf4j.Logger` in both models. | S19, S7, S10 | VERIFIED | OPENAI, ANTHROPIC |
| 8 | midConversationSystemMessages on Claude 5.x | **Model-dependent.** It is supported on Fable 5.1, Mythos 5.1, Fable 5, Mythos 5, Opus 5.5, Opus 5, Sonnet 5.5, Haiku 5.5 and Opus 4.8, and needs no beta header. Anthropic states it "is not available on Claude Sonnet 5". Opus 4.7 rejects it with a 400 error, per a search-snippet summary. Placement rules (from the LangChain4j docs): the system message must follow a user turn, cannot sit between tool_use and tool_result, and cannot repeat consecutively. Invalid placement returns a 400. | S20, S6 | VERIFIED (Opus 4.7 statement from the search summary only) | ANTHROPIC |
| 9 | Official testing guidance for ChatModel | **No dedicated official testing recipe for ChatModel was found.** The official AI Services tutorial says an AI Service "is an interface" and can be mocked in unit tests and integration-tested in isolation. The Anthropic docs page cites `AnthropicChatModelTest` and `AnthropicStreamingChatModelTest` as references. The provider poms use `me.kpavlov.aimocks:ai-mocks-openai-jvm` / `ai-mocks-anthropic-jvm` as their own test dependencies, which is how the project tests itself and not documented user guidance. `dev.langchain4j:langchain4j-test:1.22.0-beta32` exists on Maven Central (2026-10-07), but at tag 1.22.0 it contains only `dev/langchain4j/test/guardrail` (guardrail assertions). The LLM-judge and `ChatRequestAssert` utilities (PR #6819) were merged on 2026-10-23, **after** 1.22.0, so they are not part of the target version. | S21, S6, S17, S18, S22, S23, S24 | VERIFIED (absence of an official recipe = what the docs show; langchain4j-examples at 1.22.0 was not opened, so UNVERIFIED for examples) | CORE, OPENAI, ANTHROPIC |
| 10 | langchain4j-open-ai-official 1.22.0-beta32 | Maven: `dev.langchain4j:langchain4j-open-ai-official:1.22.0-beta32`, published 2026-10-07. Classes: `OpenAiOfficialChatModel` and `OpenAiOfficialStreamingChatModel`, both built with `builder()`. Key options: `baseUrl` (default `https://api.openai.com/v1`), `apiKey`, `modelName`, `isAzure(true)` and `isGitHubModels(true)`. **Azure is detected automatically** when `baseUrl` ends with `openai.azure.com`. With no API key, it uses passwordless auth, which needs the `azure-identity` dependency. The Responses API section is marked experimental. Azure deployment name and credential builder options are not on the page. | S25, S26 | VERIFIED (Azure deployment/credential options UNVERIFIED) | OPENAI (Ask-First: Azure / official SDK option) |

## Remaining UNVERIFIED (carried forward)

- Whether `OpenAiUtils.validate(...)` rejects a null `modelName` at request time. Tried: OpenAiChatModel.java@1.22.0. Not tried: OpenAiUtils.java.
- Whether `InvalidRequestException` (and so `ContentFilteredException`) extends `NonRetriableException`. Not fetched.
- A GPT-6-specific statement that `max_tokens` is rejected. Only the generic o-series deprecation wording was found (S5).
- gpt-6.1-terra model page (covered only by guide S2).
- langchain4j-examples at 1.22.0 (not opened in this round).
- open-ai-official Azure deployment/credential builder methods.

## Research Iteration Changelog

| Iteration | Date | Items resolved | Notes |
|---|---|---|---|
| Gap round 1 | 2026-10-26 | 1, 2 (partial), 3, 4 (partial), 5 (mostly), 6, 7, 8, 9, 10 (mostly) | No sub-agents. Direct WebFetch/WebSearch. |

## Source Bibliography

| ID | URL | Read |
|---|---|---|
| S1 | https://developers.openai.com/api/docs/models/gpt-6-astra | 2026-10-26 |
| S2 | https://developers.openai.com/api/docs/guides/latest-model | 2026-10-26 |
| S3 | https://developers.openai.com/api/docs/models/gpt-6-luna | 2026-10-26 |
| S4 | https://developers.openai.com/api/docs/models/gpt-6.1-sol (via search result summary) | 2026-10-26 |
| S5 | https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create (search snippet; direct fetch 404) | 2026-10-26 |
| S6 | https://docs.langchain4j.dev/integrations/language-models/anthropic | 2026-10-26 |
| S7 | https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-anthropic/src/main/java/dev/langchain4j/model/anthropic/AnthropicChatModel.java | 2026-10-26 |
| S8 | https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost (served for /adaptive-thinking) | 2026-10-26 |
| S9 | https://platform.claude.com/docs/en/build-with-claude/effort (via search summary) | 2026-10-26 |
| S10 | https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-open-ai/src/main/java/dev/langchain4j/model/openai/OpenAiChatModel.java | 2026-10-26 |
| S11 | https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/internal/RetryUtils.java | 2026-10-26 |
| S12 | https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/internal/ExceptionMapper.java | 2026-10-26 |
| S13 | https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/exception/ModelNotFoundException.java | 2026-10-26 |
| S14 | https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/exception/UnresolvedModelServerException.java | 2026-10-26 |
| S15 | https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/exception/ContentFilteredException.java | 2026-10-26 |
| S16 | https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-anthropic/src/main/java/dev/langchain4j/model/anthropic/AnthropicStreamingChatModel.java | 2026-10-26 |
| S17 | https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-anthropic/pom.xml | 2026-10-26 |
| S18 | https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-open-ai/pom.xml | 2026-10-26 |
| S19 | https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-http-client/src/main/java/dev/langchain4j/http/client/log/HttpRequestLogger.java | 2026-10-26 |
| S20 | https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages | 2026-10-26 |
| S21 | https://docs.langchain4j.dev/tutorials/ai-services/ (via search snippet) | 2026-10-26 |
| S22 | https://repo1.maven.org/maven2/dev/langchain4j/langchain4j-test/ | 2026-10-26 |
| S23 | https://github.com/langchain4j/langchain4j/tree/1.22.0/langchain4j-test/src/main/java/dev/langchain4j | 2026-10-26 |
| S24 | https://github.com/langchain4j/langchain4j/pull/6819 | 2026-10-26 |
| S25 | https://docs.langchain4j.dev/integrations/language-models/open-ai-official | 2026-10-26 |
| S26 | https://repo1.maven.org/maven2/dev/langchain4j/langchain4j-open-ai-official/ | 2026-10-26 |
