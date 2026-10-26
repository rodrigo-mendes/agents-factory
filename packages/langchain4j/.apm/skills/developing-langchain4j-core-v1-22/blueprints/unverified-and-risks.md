# Unverified Register, Risks and Bibliography

Research date 2026-10-26. Back to [SKILL.md](../SKILL.md). This register lists **13 unverified items (U1-U13), 0 irresolvable items, 12 medium-confidence items (M1-M12), 2 coverage limits (L1-L2)**. A later source read (2026-10-26) resolved provider transitivity, retry defaults and the retry classes of `ModelNotFoundException` and `UnresolvedModelServerException`; it left the `InvalidRequestException` hierarchy open (U7), where an earlier source read had listed that class as non-retriable.

## Contents

- [Tag to register mapping](#tag-to-register-mapping)
- [Version-lifetime risk](#version-lifetime-risk)
- [Unverified items](#unverified-items)
- [Irresolvable items](#irresolvable-items)
- [Medium-confidence items](#medium-confidence-items)
- [Coverage limits](#coverage-limits)
- [Source Bibliography](#source-bibliography)

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| maximum (unverified) | SKILL.md Version Context | U4 |
| whether the counts can be null is (unverified) | always-do-patterns.md | U1 |
| (unverified) builder field names and constructor | testing.md | U2 |
| Default `listeners()` being empty is (unverified) | testing.md | U3 |
| The version that introduced this is (unverified) | streaming-and-listeners.md | U5 |
| (unverified as an official practice) | SKILL.md Ask First; testing.md | U6 |
| retry class (unverified), see U7 | errors-and-retry.md; SKILL.md Always Do | U7 |
| package and base class (unverified), see U13 | errors-and-retry.md | U13 |
| provider options and policy is (unverified) here | errors-and-retry.md | U8, U10 |
| (log output unverified) | SKILL.md Quick Reference | U9 |
| No streaming double was researched: (unverified) | testing.md | U11 |
| AI Service can be mocked (unverified: search snippet) | testing.md | U12 |
| (medium confidence) resend history | SKILL.md Ask First | M1 |
| (medium confidence) offload to an executor | SKILL.md Ask First; streaming-and-listeners.md | M2 |
| (medium confidence) thread context, `ctx.attributes()` | streaming-and-listeners.md; never-do-patterns.md | M3 |
| (medium confidence) end-user text in SystemMessage | SKILL.md Ask First; never-do-patterns.md | M4 |
| (medium confidence) `@Experimental` async and reactive; Kotlin note; reactive overflow below `Long.MAX_VALUE` | SKILL.md Version Context and Ask First; streaming-and-listeners.md | M5 |
| (medium confidence) cancel a stream | SKILL.md Ask First; streaming-and-listeners.md | M6 |
| (medium confidence) streaming does not retry | streaming-and-listeners.md; errors-and-retry.md | M7 |
| (medium confidence) no official ChatModel recipe (absence of evidence) | SKILL.md Ask First; testing.md | M8 |
| (medium confidence) listener ordering, once per call, WARN on error | streaming-and-listeners.md | M9 |
| (medium confidence) builder shortcuts, message and content types | always-do-patterns.md | M10 |
| (medium confidence) `listenerAttributes` vs `attributes()` | SKILL.md Ask First | M11 |
| (medium confidence, derived from source) Mockito mock of ChatModel | testing.md | M12 |
| assumed to match 1.22.0 (medium confidence) | SKILL.md Version-lifetime risk | L1 |
| only the classes named in errors-and-retry.md were read | errors-and-retry.md (exception package) | L2 |
| (medium confidence, absence of evidence) | unverified-and-risks.md Version-lifetime risk (no successor release bullet) | none (version-lifetime note, not a register item) |
| High (shared version facts) | Version Context | https://docs.langchain4j.dev/get-started and https://github.com/langchain4j/langchain4j/releases/tag/1.22.0 |

## Version-lifetime risk

- LangChain4j 1.22.0 was released on GitHub 2026-10-08 and published to Maven Central 2026-10-07 (researched 2026-10-26), so docs may still change (High, https://github.com/langchain4j/langchain4j/releases/tag/1.22.0).
- No successor release and no end-of-support date for 1.22.0 were recorded at research time; plan upgrades by bumping the BOM and re-running tests (medium confidence, absence of evidence).
- The BOM still contains modules versioned `1.22.0-beta32`; beta modules may change shape between releases (High, https://docs.langchain4j.dev/get-started).
- Async (`chatAsync`) and reactive streaming APIs are `@Experimental` and can change without a major version (medium confidence).
- The docs site is unversioned; content read on 2026-10-26 is assumed to match 1.22.0 (see L1).

## Unverified items

- U1. Whether `TokenUsage` counts (Integer) can be null.
- U2. `ChatResponse.builder()` field names and the `TokenUsage(int, int)` constructor used in the test double.
- U3. That `ChatModel.listeners()` defaults to an empty list.
- U4. Maximum supported JDK version.
- U5. Version that introduced the Kotlin `chatAsync` resolution change.
- U6. A hand-written `doChat` test double as an officially recommended practice.
- U7. Whether `InvalidRequestException`, and so `ContentFilteredException`, extends `NonRetriableException` (the class source was not read; an earlier source read listed it as non-retriable).
- U8. Provider-level `maxRetries` and timeout builder options (belong to the provider sibling skills).
- U9. Log output of the representative commands `mvn -q dependency:tree`, `java -version`, `mvn -q test`.
- U10. That every provider implementation applies the core retry policy to blocking calls (confirmed in a later source read only for Anthropic and OpenAI blocking and async calls).
- U11. A `StreamingChatModel` test double.
- U12. That an AI Service interface can be mocked (from a search snippet of https://docs.langchain4j.dev/tutorials/ai-services/; page not read).
- U13. Package and base class of `RetriableException` and `NonRetriableException` (the sources read do not give them).

## Irresolvable items

None.

## Medium-confidence items

- M1. The model is stateless; resend history (chat docs page, unversioned).
- M2. Listener and streaming callbacks run on the I/O thread; slow work should be offloaded (observability docs page).
- M3. For streaming, listener callbacks run on different threads and thread context is not propagated.
- M4. Docs warning against end-user content in `SystemMessage`.
- M5. `chatAsync` and reactive publisher semantics (including overflow when demand is below `Long.MAX_VALUE`) and the `@Experimental` status; Kotlin note.
- M6. Stream cancellation via `streamingHandle().cancel()`.
- M7. Streaming models do not retry (Anthropic streaming source read, OpenAI streaming file not re-read).
- M8. No official ChatModel testing recipe for 1.22.0; `langchain4j-test` holds only guardrail assertions at 1.22.0 (absence of evidence; the `langchain4j-examples` repo at 1.22.0 was not opened).
- M9. Listener ordering, once-per-call firing, WARN logging of listener exceptions.
- M10. `ChatRequest.builder()` shortcut setters, message types and content types (chat docs page).
- M11. `ChatRequestOptions` `listenerAttributes` vs `attributes()` in `onRequest`.
- M12. `mock(ChatModel.class)` works mechanically, but `chat(String)` is a default method that delegates (derived from source, no official recipe).

## Coverage limits

- L1. `docs.langchain4j.dev` pages (get-started, chat, streaming, observability) are unversioned and track the current release; they were read on 2026-10-26 and assumed to match 1.22.0. Source files were read at tag 1.22.0.
- L2. The `dev.langchain4j.exception` package has 24 classes at 1.22.0; only the classes named in [errors and retry](./errors-and-retry.md) were read.

## Source Bibliography

All fetched 2026-10-26. No community sources were used. Raw base: `https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/`.

- https://github.com/langchain4j/langchain4j/releases/tag/1.22.0 (published 2026-10-08)
- https://docs.langchain4j.dev/get-started
- https://docs.langchain4j.dev/tutorials/chat-and-language-models
- https://docs.langchain4j.dev/tutorials/response-streaming
- https://docs.langchain4j.dev/tutorials/observability
- https://docs.langchain4j.dev/tutorials/ai-services/ (search snippet only)
- Raw base + `model/chat/ChatModel.java`
- Raw base + `model/chat/response/StreamingChatResponseHandler.java`
- Raw base + `model/chat/request/ChatRequestParameters.java`
- Raw base + `model/output/TokenUsage.java` and `model/output/FinishReason.java`
- Raw base + `internal/RetryUtils.java` and `internal/ExceptionMapper.java`
- Raw base + `exception/{LangChain4jException,RateLimitException,AuthenticationException,InvalidRequestException,InternalServerException,TimeoutException,ModelNotFoundException,UnresolvedModelServerException,ContentFilteredException}.java`
- https://github.com/langchain4j/langchain4j/tree/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/exception (24 classes)
- https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-open-ai/pom.xml and https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-anthropic/pom.xml
- https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-anthropic/src/main/java/dev/langchain4j/model/anthropic/AnthropicStreamingChatModel.java
- https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-http-client/src/main/java/dev/langchain4j/http/client/log/HttpRequestLogger.java
- https://repo1.maven.org/maven2/dev/langchain4j/langchain4j-core/ (1.22.0 at 2026-10-07)
- https://docs.langchain4j.dev/integrations/language-models/open-ai (sample reads the API key with `System.getenv`)
- https://repo1.maven.org/maven2/dev/langchain4j/langchain4j-open-ai/maven-metadata.xml
- https://repo1.maven.org/maven2/dev/langchain4j/langchain4j-test/ and https://github.com/langchain4j/langchain4j/pull/6819
